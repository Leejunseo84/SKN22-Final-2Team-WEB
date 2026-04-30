import sys
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 및 FastAPI 경로 추가
ROOT_DIR = Path("/home/playdata/SKN22-Final-2Team-WEB")
FASTAPI_DIR = ROOT_DIR / "services" / "fastapi"
sys.path.append(str(FASTAPI_DIR))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")

try:
    from final_ai.graph.builder import graph
    from final_ai.infrastructure.llm.openai_client import llm, LLM_MODEL
    from final_ai.contracts.filters import normalize_search_filters
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

class HybridEvaluator:
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        self.results = []
        # 멀티턴 상태 저장을 위한 메모리
        self.session_memory = {}
        self.output_dir = Path("/home/playdata/SKN22-Final-2Team-WEB/docs/evaluation/llm_as_a_judge_gemini")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.report_path = self.output_dir / f"validation_report_enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        # 의미상 동일한 카테고리/펫타입 매핑 (유연한 검증용)
        self.semantic_map = {
            "패드": ["배변용품", "배변패드", "위생용품"],
            "의류": ["옷", "패션"],
            "강아지": ["dog", "견"],
            "고양이": ["cat", "묘"]
        }

    def normalize_value(self, val):
        if val is None: return None
        if isinstance(val, list): return [str(v).strip().lower() for v in val]
        return str(val).strip().lower()

    def check_semantic_match(self, expected, actual):
        exp = self.normalize_value(expected)
        act = self.normalize_value(actual)
        if exp == act: return True
        if exp in self.semantic_map:
            return act in self.semantic_map[exp]
        return False

    def validate_deterministic(self, actual_state, expected, inp):
        """개선된 확정적 검증: 필터, 큐, 펫 전환, 완화 정책 동시 확인"""
        # 1. Intents
        actual_intents = set(actual_state.get("intents") or [])
        expected_intents = set(expected.get("intents") or [])
        intent_match = actual_intents == expected_intents
        
        # 2. Filters (현재 필터 vs 예상 필터)
        act_filters = normalize_search_filters(actual_state.get("filters", {}))
        exp_filters = normalize_search_filters(expected.get("filters", {}))
        
        # 3. 작업 큐 확인 (Decomposed Tasks)
        new_tasks = actual_state.get("new_decomposed_tasks") or []
        queue_categories = [self.normalize_value(t.get("category")) for t in new_tasks]
        queue_pet_types = [self.normalize_value(t.get("pet_type")) for t in new_tasks]

        filter_errors = []
        # 카테고리 체크 (Semantic Match + Queue Check)
        exp_cat = exp_filters.get("category")
        act_cat = act_filters.get("category")
        cat_match = self.check_semantic_match(exp_cat, act_cat)
        captured_in_queue = any(self.check_semantic_match(exp_cat, q_cat) for q_cat in queue_categories)
        
        if exp_cat and not (cat_match or captured_in_queue):
            filter_errors.append(f"category: exp({exp_cat}) vs act({act_cat}) or queue{queue_categories}")

        # 펫 타입 체크
        exp_pet = exp_filters.get("pet_type")
        act_pet = act_filters.get("pet_type")
        pet_match = self.check_semantic_match(exp_pet, act_pet)
        pet_in_queue = any(self.check_semantic_match(exp_pet, q_pet) for q_pet in queue_pet_types)
        
        if exp_pet and not (pet_match or pet_in_queue):
            filter_errors.append(f"pet_type: exp({exp_pet}) vs act({act_pet}) or queue{queue_pet_types}")

        # 4. Pet Identity (Target Pet ID 체크)
        exp_target_id = expected.get("target_pet_id")
        act_target_id = actual_state.get("target_pet_id")
        pet_id_match = True
        if exp_target_id and str(exp_target_id) != str(act_target_id):
            pet_id_match = False
            filter_errors.append(f"pet_id: exp({exp_target_id}) vs act({act_target_id})")

        # 5. Relaxation Policy (완화 정책 작동 여부)
        # 결과가 0개여야 하는데 필터 완화로 결과가 나왔는지 혹은 relaxation_count가 증가했는지
        relaxation_count = actual_state.get("relaxation_count", 0)
        product_count = len(actual_state.get("product_cards", []))
        relaxation_worked = True
        if expected.get("expect_relaxation") and relaxation_count == 0 and product_count == 0:
            relaxation_worked = False
            filter_errors.append("relaxation: expected but not triggered")

        # 6. Product Overlap (단순 ID 비교)
        actual_ids = {str(p.get("goods_id")) for p in actual_state.get("product_cards", [])}
        golden_ids = {str(p.get("goods_id")) for p in expected.get("golden_products", [])}
        overlap_score = len(actual_ids & golden_ids) / len(golden_ids) if golden_ids else (1.0 if not actual_ids else 0.0)

        # 7. Keywords
        response_text = actual_state.get("response", "")
        keywords = expected.get("expected_response_contains", [])
        missing_keywords = [w for w in keywords if w not in response_text]

        return {
            "intent_passed": intent_match,
            "filter_passed": len(filter_errors) == 0,
            "filter_errors": filter_errors,
            "overlap_score": overlap_score,
            "keyword_passed": len(missing_keywords) == 0,
            "missing_keywords": missing_keywords,
            "captured_in_queue": captured_in_queue,
            "pet_id_match": pet_id_match,
            "relaxation_worked": relaxation_worked
        }

    async def get_llm_judge_score(self, user_input, actual_query, expected_query, response, expected_contains, actual_products):
        product_info = "\n".join([f"- {p.get('name')} ({p.get('category')})" for p in actual_products[:5]])
        
        prompt = f"""
        당신은 반려동물 쇼핑 AI 'TailTalk'의 시니어 품질 평가관입니다.
        단순히 텍스트 일치만 보는 게 아니라, 시스템의 '추천 품질'과 '맥락 유지'를 엄격히 평가하세요.

        [평가 대상]
        1. 유저 질문: {user_input}
        2. 생성된 검색어: {actual_query} (골든 쿼리: {expected_query})
        3. 추천된 상품들:
        {product_info}
        4. 최종 응답: {response}
        5. 필수 포함 키워드: {expected_contains}

        [평가 기준]
        1. 검색 의도 및 상품 적합성 (0.0 ~ 1.0점):
           - 단순히 키워드가 아니라, 유저가 요청한 펫의 종/나이/건강고민에 맞는 상품이 추천되었는가?
           - 검색 쿼리가 DB에서 관련 상품을 뽑기에 충분히 전문적인가?

        2. 응답 품질 및 페르소나 (1 ~ 5점):
           - 3패널 규칙(사이드바/채팅/상품판)을 존수하며 전문가답고 친절한가?
           - 이전 대화 맥락(펫 이름, 종 등)을 자연스럽게 반영했는가?
           - 필수 키워드가 자연스럽게 녹아있는가?

        JSON 형식으로만 응답하세요: {{"query_score": 1.0, "response_score": 5, "reason": "..."}}
        """
        try:
            res = llm.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0
            )
            return json.loads(res.choices[0].message.content)
        except:
            return {"query_score": 0, "response_score": 0, "reason": "LLM Judge Error"}

    async def run_eval(self):
        # JSON 배열 또는 JSONL 모두 지원하도록 수정
        try:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content.startswith("["):
                    cases = json.loads(content)
                else:
                    cases = [json.loads(line) for line in content.splitlines() if line.strip()]
        except Exception as e:
            print(f"❌ 데이터셋 로딩 실패: {e}")
            return

        print(f"📋 TailTalk 지능형 검증 엔진 가동 (총 {len(cases)}개 케이스)...")
        
        from unittest.mock import patch

        for i, case in enumerate(cases):
            inp = case["input"]
            exp = case["expected_output"]
            sid = inp.get("session_id", "test-session")
            
            # 펫 프로필 정보 준비
            registered_pets = inp.get("current_pet_profiles", [])
            # [보정] 실제 repository가 반환하는 중첩 구조로 래핑
            def wrap_full_profile(pet_data):
                if not pet_data: return {}
                return {
                    "pet_id": pet_data.get("pet_id"),
                    "pet_profile": {
                        "name": pet_data.get("name"),
                        "species": pet_data.get("species"),
                        "breed": pet_data.get("breed"),
                        "age": pet_data.get("age"),
                        "gender": pet_data.get("gender"),
                        "weight": pet_data.get("weight")
                    },
                    "health_concerns": pet_data.get("health_concerns", []),
                    "allergies": pet_data.get("allergies", []),
                    "food_preferences": pet_data.get("food_preferences", [])
                }

            pet_profile_map = {str(p.get("pet_id")): wrap_full_profile(p) for p in registered_pets if p.get("pet_id")}
            
            # 이전 턴의 상태
            prev_turn_state = self.session_memory.get(sid, {})
            target_pet_id = inp.get("target_pet_id") or prev_turn_state.get("target_pet_id")
            
            # [개선] target_pet_id가 지정된 경우 해당 프로필을 초기 상태에 주입
            current_pet_info = pet_profile_map.get(str(target_pet_id), {}).get("pet_profile") if target_pet_id else prev_turn_state.get("pet_profile")

            initial_state = {
                "user_input": inp["user_input"],
                "conversation_history": inp.get("conversation_history", []),
                "user_id": inp.get("user_id", 10),
                "thread_id": sid,
                "target_pet_id": target_pet_id,
                "pet_profile": current_pet_info,
                "filters": prev_turn_state.get("filters", {}),
                "decomposed_tasks": prev_turn_state.get("decomposed_tasks", []),
                "intents": prev_turn_state.get("intents", []),
                "last_recommended_goods_ids": prev_turn_state.get("last_recommended_goods_ids", []),
                "messages": [],
                "product_cards": [],
                "search_query": "",
                "relaxation_count": 0
            }
            
            try:
                # [수정] side_effect 함수가 래핑된 구조를 반환하도록 patch 설정
                with patch("final_ai.domain.intent.service.get_user_pets", return_value=registered_pets), \
                     patch("final_ai.domain.intent.service.get_pet_full_profile", side_effect=lambda pid: pet_profile_map.get(str(pid), {})), \
                     patch("final_ai.application.chat.context.get_pet_full_profile", side_effect=lambda pid: pet_profile_map.get(str(pid), {})):
                    
                    final_state = graph.invoke(initial_state, config={"configurable": {"thread_id": sid}})
                
                # 상태 저장
                self.session_memory[sid] = {
                    "filters": final_state.get("filters"),
                    "pet_profile": final_state.get("pet_profile"),
                    "decomposed_tasks": final_state.get("decomposed_tasks"),
                    "intents": final_state.get("intents"),
                    "last_recommended_goods_ids": final_state.get("last_recommended_goods_ids"),
                    "target_pet_id": final_state.get("target_pet_id")
                }

                # 정밀 검증
                det_res = self.validate_deterministic(final_state, exp, inp)
                judge_res = await self.get_llm_judge_score(
                    inp["user_input"], 
                    final_state.get("search_query"), 
                    exp.get("search_query"), 
                    final_state.get("response"), 
                    exp.get("expected_response_contains"),
                    final_state.get("product_cards", [])
                )
                
                self.results.append({
                    "id": case.get("id", f"case_{i}"), 
                    "description": case.get("description", ""),
                    "input": inp["user_input"],
                    "det": det_res, 
                    "judge": judge_res,
                    "actual_response": final_state.get("response")
                })
                print(f"[{i+1}/{len(cases)}] ✅ {case.get('id')} 완료 (Det: {'✅' if det_res['filter_passed'] else '❌'}, Score: {judge_res['response_score']}/5)")
            except Exception as e:
                import traceback
                print(f"[{i+1}/{len(cases)}] ❌ {case.get('id')} 에러: {e}")
                traceback.print_exc()

        self.generate_report()

    def generate_report(self):
        total = len(self.results)
        if not total: return
        
        avg_overlap = sum(r['det']['overlap_score'] for r in self.results) / total
        avg_judge = sum(r['judge']['response_score'] for r in self.results) / total
        det_pass_rate = sum(1 for r in self.results if r['det']['filter_passed']) / total
        
        md = f"# TailTalk Intelligent Logic Validation Report\n"
        md += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        md += f"**Core Enhancements:** Semantic Matching, Task Queue Tracking, Pet Identity Sync, Relaxation Policy Validation.\n\n"
        
        md += "## Summary\n"
        md += f"- Total Cases: {total}\n"
        md += f"- Deterministic Pass Rate (Filters/Queue/PetID): {det_pass_rate:.2%}\n"
        md += f"- Avg. Product Overlap: {avg_overlap:.2%}\n"
        md += f"- Avg. Response Quality: {avg_judge:.2f} / 5.0\n\n"
        
        md += "## Detailed Results\n"
        for r in self.results:
            d = r['det']
            j = r['judge']
            md += f"### [{r['id']}] {r['description']}\n"
            md += f"- **Input:** {r['input']}\n"
            md += f"- **Status:** Intent({'✅' if d['intent_passed'] else '❌'}), Filter({'✅' if d['filter_passed'] else '❌'}), PetID({'✅' if d['pet_id_match'] else '❌'}), Relaxation({'✅' if d['relaxation_worked'] else 'N/A'})\n"
            
            if d['captured_in_queue']:
                md += f"  - *Note: Intent captured in task queue (Future Action OK).*\n"
            if d['filter_errors']:
                md += f"  - Validation Errors: `{', '.join(d['filter_errors'])}`\n"
            
            md += f"- **Overlap Score:** {d['overlap_score']:.2%}\n"
            md += f"- **LLM Judge:** Query({j['query_score']:.1f}), Response({j['response_score']}점)\n"
            md += f"- **Judge Reason:** {j['reason']}\n\n"
            md += "---\n"

        with open(self.report_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"\n📑 지능형 리포트 생성 완료: {self.report_path}")

if __name__ == "__main__":
    DATA_PATH = "/home/playdata/SKN22-Final-2Team-WEB/docs/evaluation/ai_logic_golden_dataset.json"
    evaluator = HybridEvaluator(DATA_PATH)
    asyncio.run(evaluator.run_eval())
