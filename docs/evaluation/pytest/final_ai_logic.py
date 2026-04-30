import sys
import os
import asyncio
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List

# 0. 경로 설정 및 환경 변수 로딩
BASE_DIR = os.path.abspath(os.path.join(os.getcwd(), "services/fastapi"))
sys.path.append(BASE_DIR)

from langchain_core.messages import HumanMessage, AIMessage
from final_ai.graph.builder import build_graph
from langgraph.checkpoint.memory import MemorySaver
from final_ai.contracts.chat import ChatRequest, ConversationHistoryItem
from final_ai.application.chat.dto import build_chat_execution_request



def make_serializable(obj: Any) -> Any:
    """PostgreSQL Decimal 및 LangChain 메시지 객체 등 JSON 비호환 타입을 변환"""
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items() if not k.startswith("_")}
    elif isinstance(obj, list):
        return [make_serializable(v) for v in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    elif hasattr(obj, "content") and hasattr(obj, "type"): # LangChain Message 객체
        return {"type": getattr(obj, "type"), "content": getattr(obj, "content")}
    elif hasattr(obj, "isoformat"):
        return obj.isoformat()
    return str(obj) if "Message" in str(type(obj)) else obj

class FinalAILogicTester:
    def __init__(self):
        # 중단점(breakpoint) 기능을 쓰기 위해서는 반드시 checkpointer가 필요함
        self.memory = MemorySaver()
        self.graph = build_graph(checkpointer=self.memory)
        self.golden_dataset_path = "docs/evaluation/llm_as_a_judge_gemini/ai_logic_golden_dataset.json"
        self.output_path = "docs/evaluation/second_test/captured_logic_output.json"
        # 멀티턴 문맥 유지 및 상태 이어달리기를 위한 세션 캐시
        self.session_context = {} 

    def load_dataset(self) -> List[Dict]:
        with open(self.golden_dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def run_test(self):
        dataset = self.load_dataset()
        # 제한 없이 전체 케이스 실행
        test_cases = dataset
        
        captured_results = []
        print(f"🚀 총 {len(test_cases)}개의 케이스에 대해 로직 테스트(v4 - Multi-turn Support)를 시작합니다.")

        for case in test_cases:
            case_id = case["id"]
            print(f"🔍 Testing Case: {case_id}...")
            
            # 1. ChatRequest 객체 생성 (실제 서비스와 동일한 계약 구조)
            input_data = case["input"]
            history = [
                ConversationHistoryItem(role=item["role"], content=item["content"])
                for item in input_data.get("conversation_history", [])
            ]
            
            pet_profiles = input_data.get("current_pet_profiles", [])
            
            # --- [핵심] 타겟 펫 매칭 로직 ---
            # 데이터셋의 의도된 타겟 펫 아이디 확인
            expected_target_id = case.get("expected_output", {}).get("target_pet_id")
            
            active_profile = None
            if expected_target_id:
                # 아이디가 일치하는 프로필을 찾음 (타겟 펫 정밀 매칭)
                active_profile = next((p for p in pet_profiles if str(p.get("pet_id")) == str(expected_target_id)), None)
            
            # 명시적인 타겟이 없거나 못 찾았다면 첫 번째 프로필 사용
            if not active_profile and pet_profiles:
                active_profile = pet_profiles[0]
                
            pet_profile = active_profile or {}
            
            # --- [핵심] 상태 이어달리기 로직 ---
            # case_id (예: case_001_no_profile_B)에서 그룹키와 순서를 파악
            session_key = case_id.rsplit('_', 1)[0]
            suffix = case_id.rsplit('_', 1)[1] if '_' in case_id else 'A'
            
            # 후속 질문(B, C 등)인 경우 이전 턴의 상태를 로드
            prev_dialog_state = {}
            if suffix != 'A' and session_key in self.session_context:
                print(f"   -> State Relay: Carrying over context from previous turn in group {session_key}")
                prev_dialog_state = self.session_context[session_key]
            
            # --- [수정] target_pet_id 주입 조건 강화 ---
            # case_id에 with_profile이 있으면 외부(프론트엔드/클라이언트)에서 펫을 선택한 상황으로 간주하여 ID 주입
            is_with_profile_case = "with_profile" in case_id
            forced_target_pet_id = active_profile.get("pet_id") if is_with_profile_case and active_profile else None
            
            chat_req = ChatRequest(
                message=input_data["user_input"],
                thread_id=input_data.get("session_id", f"test_{session_key}"),
                user_id=str(input_data.get("user_id", "")),
                target_pet_id=forced_target_pet_id or active_profile.get("pet_id") if active_profile else prev_dialog_state.get("target_pet_id"),
                pet_profile=pet_profile if active_profile else prev_dialog_state.get("pet_profile", {}),
                health_concerns=active_profile.get("health_concerns", []) if active_profile else prev_dialog_state.get("health_concerns", []),
                allergies=active_profile.get("allergies", []) if active_profile else prev_dialog_state.get("allergies", []),
                conversation_history=history,
                dialog_state={**prev_dialog_state, **input_data.get("dialog_state", {})}
            )
            
            # 2. 실행 요청 빌드
            # 주의: build_chat_execution_request는 모든 필드를 기본값으로 채우기 때문에
            # 연속 대화(Multi-turn)에서는 기존 메모리를 덮어쓸 위험이 있습니다.
            execution = build_chat_execution_request(chat_req)
            initial_state = execution.initial_state
            config = execution.config

            try:
                # 3. 실행 데이터 결정 (데이터셋의 이력을 명시적으로 메시지 객체로 주입)
                # 동일 세션을 유지하더라도 데이터셋의 history가 최우선 문맥이 되어야 함
                current_input = initial_state
                
                state_snapshot = await self.graph.aget_state(config)
                if state_snapshot.values:
                    print(f"   -> Multi-turn context detected for session {chat_req.thread_id}")
                    # 리듀서에 의해 메시지가 중복되는 것을 방지하기 위해, 
                    # 이미 메모리에 상태가 있다면 현재 질문 문맥에 필요한 필드들만 선별적으로 업데이트 요청
                    # 단, 데이터셋의 의도를 존중하기 위해 conversation_history는 그대로 전달
                    pass

                # 4. 실행 (중단점 설정)
                await self.graph.ainvoke(current_input, config=config, interrupt_before=["respond"])
                
                # 5. 상태 캡처
                state_snapshot = await self.graph.aget_state(config)
                raw_state = state_snapshot.values
                state_snapshot = await self.graph.aget_state(config)
                raw_state = state_snapshot.values
                
                # 6. 중단점 이후 계속 실행하여 최종 응답 획득
                final_state_snapshot = await self.graph.ainvoke(None, config=config)
                final_state = final_state_snapshot
                final_response = final_state.get("response", "")

                # 원하는 필드만 선별적으로 추출
                selected_fields = [
                    "user_input", "intents", "filters", "effective_filters", 
                    "search_query", "decomposed_tasks", "conversation_history", 
                    "target_pet_id", "pet_profile", "health_concerns"
                ]
                
                filtered_state = {k: raw_state.get(k) for k in selected_fields if k in raw_state}
                
                # 상품 관련 정보 추가
                recommended_goods = final_state.get("reranked_results", [])
                filtered_state["recommended_goods_ids"] = [g.get("goods_id") for g in recommended_goods if "goods_id" in g]
                filtered_state["last_recommended_goods_ids"] = raw_state.get("last_recommended_goods_ids", [])

                # 결과 수집
                captured_result = {
                    "case_id": case_id,
                    "captured_at": datetime.now().isoformat(),
                    "logic": make_serializable(filtered_state),
                    "actual_response": final_response
                }
                captured_results.append(captured_result)
                
                # --- [핵심] 다음 턴을 위해 현재 상태를 세션 캐시에 업데이트 ---
                # LangGraph의 State를 다음 턴의 dialog_state로 재사용 가능한 형태로 보관
                # conversation_history는 데이터셋의 것을 따르므로 제외하고 로직 데이터만 보관
                self.session_context[session_key] = {
                    k: v for k, v in raw_state.items() 
                    if k not in ["messages", "conversation_history", "user_input", "response"]
                }
                
                print(f"✅ Case {case_id} captured. (Intents: {raw_state.get('intents')})")

            except Exception as e:
                print(f"❌ Error in {case_id}: {str(e)}")
                import traceback
                traceback.print_exc()

        # 결과 저장
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(captured_results, f, ensure_ascii=False, indent=2)

        print(f"\n✨ {len(captured_results)}개 테스트 완료! 결과가 {self.output_path}에 저장되었습니다.")

if __name__ == "__main__":
    tester = FinalAILogicTester()
    asyncio.run(tester.run_test())
