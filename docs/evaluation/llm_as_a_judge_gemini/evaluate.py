import json
import os
import sys
import asyncio
from pathlib import Path
from typing import Any, Dict, List
import re

# final_ai 모듈을 불러오기 위해 경로 추가
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(BASE_DIR / "services" / "fastapi"))

from final_ai.graph.builder import build_graph
from final_ai.graph.state import ChatState
from langgraph.checkpoint.memory import MemorySaver
from final_ai.contracts.chat import ChatRequest, ConversationHistoryItem
from final_ai.application.chat.dto import build_chat_execution_request

# OpenAI를 활용한 평가를 위한 모듈
from openai import AsyncOpenAI

# API 키 설정 (환경 변수에서 로드)
client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
MODEL_NAME = "gpt-4o-mini"

class GPTJudge:
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        self.checkpointer = MemorySaver()
        self.graph = build_graph(checkpointer=self.checkpointer)
        self.results = []
        # 멀티턴 문맥 유지 및 상태 이어달리기를 위한 세션 캐시
        self.session_context = {} 

    def load_dataset(self) -> List[Dict]:
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []

    def get_base_id(self, case_id: str) -> str:
        """id에서 멀티턴 접미사(_A, _B, _C 등)를 제거한 기본 시나리오 ID를 반환합니다."""
        return re.sub(r'_[A-Z]$', '', case_id)

    def group_by_session(self, dataset: List[Dict]) -> Dict[str, List[Dict]]:
        sessions = {}
        for case in dataset:
            session_id = case.get("input", {}).get("session_id", "default")
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(case)
        
        for sid in sessions:
            sessions[sid].sort(key=lambda x: x["id"])
        return sessions

    def check_logic_fields(self, actual_state: Dict, expected_output: Dict) -> Dict:
        fields_to_check = [
            "intents", "search_query", "allergies", "conversation_history",
            "decomposed_tasks", "filters", "health_concerns", "target_pet_id"
        ]
        comparison = {}
        for field in fields_to_check:
            actual = actual_state.get(field)
            expected = expected_output.get(field)
            
            is_match = False
            # Rule: 빈 리스트([])와 None(null)은 동일하게 취급
            if (actual == [] or actual is None) and (expected == [] or expected is None):
                is_match = True
            elif isinstance(actual, list) and isinstance(expected, list):
                is_match = set(map(str, actual)) == set(map(str, expected))
            elif isinstance(actual, dict) and isinstance(expected, dict):
                is_match = all(actual.get(k) == expected.get(k) for k in expected)
            else:
                is_match = str(actual) == str(expected) if (actual is not None and expected is not None) else actual == expected
            
            comparison[field] = {"actual": actual, "expected": expected, "match": is_match}
        return comparison

    def check_response_keywords(self, response: str, keywords: List[str]) -> Dict:
        if not keywords:
            return {"passed": True, "missing": []}
        norm_response = response.replace(" ", "").lower()
        missing = [k for k in keywords if k.replace(" ", "").lower() not in norm_response]
        return {"passed": len(missing) == 0, "missing": missing}

    def check_products(self, actual_products: List[Dict], expected_products: List[Dict]) -> Dict:
        if not expected_products:
            return {"passed": True, "match_count": 0, "matches": []}
        actual_ids = {str(p.get("goods_id")) for p in actual_products if p.get("goods_id")}
        expected_ids = {str(p.get("goods_id")) for p in expected_products if p.get("goods_id")}
        matches = actual_ids.intersection(expected_ids)
        return {"passed": len(matches) >= 3, "match_count": len(matches), "matches": list(matches)}

    async def evaluate_with_gpt(self, case_id: str, prompt_content: str) -> str:
        try:
            response = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "당신은 AI 챗봇의 로직과 답변 품질을 평가하는 전문 판독관입니다. 한국어로 답변하세요."},
                    {"role": "user", "content": prompt_content}
                ],
                temperature=0
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    def generate_markdown_report(self, results: List[Dict], output_path: Path):
        total = len(results)
        passed = sum(1 for r in results if "PASS" in r["gpt_decision"][:10].upper())
        failed = total - passed
        
        md = [
            "# 🐾 TailTalk AI 로직 평가 리포트 (LLM-as-a-Judge)",
            f"\n## 📊 요약",
            f"- **총 테스트 케이스**: {total}",
            f"- **성공 (PASS)**: {passed}",
            f"- **실패 (FAIL)**: {failed}",
            f"- **성공률**: {(passed/total)*100:.1f}%" if total > 0 else "- **성공률**: 0%",
            "\n## 📝 상세 결과",
            "| ID | 결과 | 로직 일치 | 키워드 | 상품 일치 | 세션(Thread) |",
            "| :--- | :---: | :---: | :---: | :---: | :--- |"
        ]
        
        for r in results:
            decision = "✅ PASS" if "PASS" in r["gpt_decision"][:10].upper() else "❌ FAIL"
            logic_icon = "✔️" if all(f["match"] for f in r["logic_check"].values()) else "⚠️"
            keyword_icon = "✔️" if r["keyword_check"]["passed"] else "❌"
            product_icon = f"{r['product_check']['match_count']}개" if r["product_check"]["passed"] else f"⚠️ {r['product_check']['match_count']}개"
            
            md.append(f"| {r['id']} | {decision} | {logic_icon} | {keyword_icon} | {product_icon} | `{r['thread_id']}` |")
        
        md.append("\n## 🔍 케이스별 상세 판정 이유")
        for r in results:
            md.append(f"\n### 🔹 {r['id']}")
            md.append(f"- **Thread**: `{r['thread_id']}`")
            md.append(f"- **GPT Judge 판정**:\n\n{r['gpt_decision']}")
            md.append("\n---\n")
            
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md))

    async def run_evaluation(self):
        dataset = self.load_dataset()
        # 세션별 그룹화는 그대로 유지하되, 내부 실행 로직을 고도화
        sessions = self.group_by_session(dataset)

        for session_id, cases in sessions.items():
            for case in cases:
                case_id = case["id"]
                # case_id (예: case_001_no_profile_B)에서 그룹키와 순서를 파악
                session_key = case_id.rsplit('_', 1)[0]
                suffix = case_id.rsplit('_', 1)[1] if '_' in case_id else 'A'
                
                eval_thread_id = f"{session_id}_{session_key}"
                config = {"configurable": {"thread_id": eval_thread_id}}
                
                print(f"Evaluating Case: {case_id} (Thread: {eval_thread_id})")
                
                input_data = case["input"]
                user_input = input_data["user_input"]
                expected_output = case.get("expected_output", {})
                
                # 1. 펫 프로필 매칭 (정밀 주입)
                pet_profiles = input_data.get("current_pet_profiles", [])
                expected_target_id = expected_output.get("target_pet_id")
                
                active_profile = None
                if expected_target_id:
                    active_profile = next((p for p in pet_profiles if str(p.get("pet_id")) == str(expected_target_id)), None)
                
                if not active_profile and pet_profiles:
                    active_profile = pet_profiles[0]
                
                pet_profile = active_profile or {}

                # 2. 상태 이어달리기 (State Relay) 로직 적용
                prev_dialog_state = {}
                if suffix != 'A' and session_key in self.session_context:
                    print(f"   -> State Relay: Carrying over context from previous turn in group {session_key}")
                    prev_dialog_state = self.session_context[session_key]

                # 3. ChatRequest 및 실행 요청 빌드 (표준화)
                history = [
                    ConversationHistoryItem(role=item["role"], content=item["content"])
                    for item in input_data.get("conversation_history", [])
                ]
                
                # --- [수정] target_pet_id 주입 조건 강화 ---
                # case_id에 with_profile이 있으면 외부(프론트엔드/클라이언트)에서 펫을 선택한 상황으로 간주하여 ID 주입
                is_with_profile_case = "with_profile" in case_id
                forced_target_pet_id = active_profile.get("pet_id") if is_with_profile_case and active_profile else None

                chat_req = ChatRequest(
                    message=user_input,
                    thread_id=eval_thread_id,
                    user_id=str(input_data.get("user_id", "default_user")),
                    target_pet_id=forced_target_pet_id or active_profile.get("pet_id") if active_profile else prev_dialog_state.get("target_pet_id"),
                    pet_profile=pet_profile if active_profile else prev_dialog_state.get("pet_profile", {}),
                    health_concerns=active_profile.get("health_concerns", []) if active_profile else prev_dialog_state.get("health_concerns", []),
                    allergies=active_profile.get("allergies", []) if active_profile else prev_dialog_state.get("allergies", []),
                    conversation_history=history,
                    dialog_state={**prev_dialog_state, **input_data.get("dialog_state", {})}
                )
                
                execution = build_chat_execution_request(chat_req)
                initial_state = execution.initial_state
                
                respond_input_state = {}

                # 4. 실행 및 캡처 (respond 노드 이전 상태 캡처를 위해 astream 사용)
                async for event in self.graph.astream(initial_state, config=config, stream_mode="values"):
                    if "response" not in event or not event["response"]:
                        respond_input_state = event

                # 최종 상태 및 응답 획득
                final_state_snapshot = await self.graph.aget_state(config)
                final_raw_state = final_state_snapshot.values
                actual_response = final_raw_state.get("response", "")
                actual_products = final_raw_state.get("reranked_results", [])

                # 5. 상태 캐시 업데이트 (다음 턴을 위함)
                self.session_context[session_key] = {
                    k: v for k, v in respond_input_state.items() 
                    if k not in ["messages", "conversation_history", "user_input", "response"]
                }

                logic_check = self.check_logic_fields(respond_input_state, expected_output)
                keyword_check = self.check_response_keywords(actual_response, expected_output.get("expected_response_contains", []))
                product_check = self.check_products(actual_products, expected_output.get("golden_products", []))

                judge_prompt = f"""
                평가 ID: {case['id']}
                사용자 입력: {user_input}
                
                [검증 데이터]
                1. 로직 필드 8종 (빈 리스트/null 동일 취급):
                {json.dumps(logic_check, ensure_ascii=False, indent=2)}
                
                2. 응답 키워드 포함:
                {json.dumps(keyword_check, ensure_ascii=False, indent=2)}
                
                3. 상품 일치 (3개 이상 시 PASS):
                {json.dumps(product_check, ensure_ascii=False, indent=2)}
                
                [AI 실제 답변]
                {actual_response}
                
                판정 가이드:
                - 시나리오 변경 시 이전 문맥이 섞이지 않았는가?
                - AI가 새로운 입력에서 의도와 필터를 정확히 추출했는가?
                - 답변이 자연스럽고 요구사항을 충족하는가?
                
                최종 판정은 PASS 혹은 FAIL로 시작하고 논리적으로 설명하세요.
                """
                
                gpt_decision = await self.evaluate_with_gpt(case['id'], judge_prompt)
                print(f"Decision: {'PASS' if 'PASS' in gpt_decision[:10].upper() else 'FAIL'}")

                self.results.append({
                    "id": case["id"],
                    "session_id": session_id,
                    "thread_id": eval_thread_id,
                    "logic_check": logic_check,
                    "keyword_check": keyword_check,
                    "product_check": product_check,
                    "gpt_decision": gpt_decision,
                    "actual_response": actual_response
                })

        # JSON 리포트 저장
        report_dir = BASE_DIR / "docs" / "evaluation" / "llm_as_a_judge_gemini"
        json_path = report_dir / "evaluation_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
            
        # Markdown 리포트 생성
        md_path = report_dir / "evaluation_report.md"
        self.generate_markdown_report(self.results, md_path)
        
        print(f"Evaluation complete.")
        print(f"- JSON Report: {json_path}")
        print(f"- MD Report: {md_path}")

if __name__ == "__main__":
    dataset_path = str(BASE_DIR / "docs" / "evaluation" / "llm_as_a_judge_gemini" / "ai_logic_golden_dataset.json")
    judge = GPTJudge(dataset_path)
    asyncio.run(judge.run_evaluation())
