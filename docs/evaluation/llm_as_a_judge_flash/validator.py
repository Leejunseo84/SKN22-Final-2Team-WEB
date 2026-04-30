import os
import json
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("LLMJudgeValidator")

print("DEBUG: Script started")
# 경로 설정
ROOT = Path(__file__).resolve().parents[3]
print(f"DEBUG: ROOT is {ROOT}")
FASTAPI_ROOT = ROOT / "services" / "fastapi"
print(f"DEBUG: FASTAPI_ROOT is {FASTAPI_ROOT}")
if str(FASTAPI_ROOT) not in sys.path:
    sys.path.insert(0, str(FASTAPI_ROOT))
    print("DEBUG: Added FASTAPI_ROOT to sys.path")

print("DEBUG: Importing modules...")
# AI 로직 및 Judge 임포트
try:
    from final_ai.graph.builder import graph
    from final_ai.contracts.chat import ChatRequest, ConversationHistoryItem
    from final_ai.application.chat.dto import build_chat_execution_request
    from llm_judge import LLMJudge
    print("DEBUG: Modules imported successfully")
except ImportError as e:
    print(f"DEBUG: ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"DEBUG: General Exception during import: {e}")
    sys.exit(1)

# 설정
DATASET_PATH = ROOT / "docs/evaluation/ragas_dataset/ai_logic_golden_dataset.jsonl"
REPORT_PATH = ROOT / "docs/evaluation/llm_as_a_judge_flash/validation_report.md"
CORE_FIELDS = {"species", "breed", "name", "age", "gender"}

def compare_filters(actual: Dict, expected: Dict) -> bool:
    """필터 데이터를 유연하게 비교합니다. (None, [], {} 등 빈 값 허용)"""
    if not actual and not expected:
        return True
    
    # 비교할 키 집합 (핵심 필터 위주)
    actual_dict = actual if isinstance(actual, dict) else {}
    expected_dict = expected if isinstance(expected, dict) else {}
    keys = set(actual_dict.keys()) | set(expected_dict.keys())
    
    for k in keys:
        v_act = actual_dict.get(k)
        v_exp = expected_dict.get(k)
        
        # 둘 다 비어있는 경우 (None, [], {}, "")
        if not v_act and not v_exp:
            continue
            
        # 하나만 비어있는 경우
        if not v_act or not v_exp:
            return False
            
        if not compare_deep(v_act, v_exp):
            return False
            
    return True

def compare_deep(actual: Any, expected: Any) -> bool:
    """깊은 비교를 수행하며 리스트 순서는 무시합니다."""
    # 빈 값끼리는 동일 처리 (None, [], {})
    if not actual and not expected:
        return True
    
    if type(actual) != type(expected) and not (actual is None or expected is None):
        return False
        
    if isinstance(actual, dict):
        if not expected: return not actual
        for k, v in expected.items():
            if k not in actual or not compare_deep(actual[k], v):
                return False
        return True
        
    if isinstance(actual, list):
        if not expected: return not actual
        if len(actual) != len(expected):
            return False
        # 리스트의 경우 순서와 상관없이 요소들이 매칭되는지 확인
        return all(any(compare_deep(a, e) for a in actual) for e in expected)
        
    return actual == expected

def calculate_product_metrics(actual_ids: List[str], expected_ids: List[str]) -> Dict[str, float]:
    """Recall과 Precision을 계산합니다."""
    if not expected_ids:
        return {"recall": 1.0, "precision": 1.0 if not actual_ids else 0.0}
    
    actual_set = set(actual_ids)
    expected_set = set(expected_ids)
    intersection = actual_set.intersection(expected_set)
    
    recall = len(intersection) / len(expected_set)
    precision = len(intersection) / len(actual_set) if actual_set else 0.0
    
    return {"recall": recall, "precision": precision}

async def run_validation():
    if not DATASET_PATH.exists():
        logger.error(f"❌ Dataset not found at {DATASET_PATH}")
        return

    judge = LLMJudge()
    results = []
    
    current_session_id = None
    result_state = {} # 이전 턴의 결과 상태 저장용

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        case_lines = f.readlines()

    logger.info(f"🚀 Starting LLM-as-a-Judge Validation for {len(case_lines)} cases...")

    for i, line in enumerate(case_lines):
        case = json.loads(line)
        case_id = case.get("id")
        session_id = case.get("session_id", "default")
        user_input = case["input"].get("user_input")
        expected = case.get("expected_output", {})
        
        # 세션 초기화 및 상태 유지
        if session_id != current_session_id:
            current_session_id = session_id
            last_dialog_state = {}
            last_history = []
        else:
            # 이전 턴의 상태 계승 (result_state 자체가 이전 턴의 전체 상태임)
            last_dialog_state = result_state
            last_history = result_state.get("conversation_history", [])

        try:
            # ChatRequest 및 DTO 변환 (생산 환경과 동일)
            # 데이터셋에 히스토리가 명시되어 있으면 그것을 우선, 없으면 누적된 히스토리 사용
            dataset_history = case["input"].get("conversation_history")
            if dataset_history is not None:
                history_raw = dataset_history
            else:
                history_raw = last_history

            history_items = []
            for h in history_raw:
                role = h.get("role")
                content = h.get("content")
                if role and content:
                    history_items.append(ConversationHistoryItem(role=role, content=content))

            chat_req = ChatRequest(
                message=user_input,
                thread_id=session_id,
                pet_profile=case["input"].get("pet_profile"),
                health_concerns=case["input"].get("health_concerns", []),
                allergies=case["input"].get("allergies", []),
                food_preferences=case["input"].get("food_preferences", []),
                target_pet_id=case["input"].get("target_pet_id"),
                conversation_history=history_items,
                dialog_state=last_dialog_state # 이전 상태 주입
            )

            # 생산용 execution request 생성 (여기서 정규화 및 메시지 객체 변환 실행됨)
            exec_req = build_chat_execution_request(chat_req)
            
            # AI 로직 실행
            result_state = graph.invoke(exec_req.initial_state, config=exec_req.config)

            # 1. 확정적 검증 (Deterministic)
            intent_match = compare_deep(result_state.get("intents"), expected.get("intents"))
            filter_match = compare_filters(result_state.get("filters", {}), expected.get("filters", {}))
            task_match = compare_deep(result_state.get("decomposed_tasks"), expected.get("decomposed_tasks"))
            
            # 상품 메트릭
            actual_product_ids = [p.get("goods_id") for p in result_state.get("product_cards", [])]
            expected_product_ids = [p.get("goods_id") for p in expected.get("golden_products", [])]
            p_metrics = calculate_product_metrics(actual_product_ids, expected_product_ids)

            # 2. LLM Judge 검증
            # 쿼리 의도 검증
            query_result = judge.judge_query(user_input, expected.get("search_query", ""), result_state.get("search_query", ""))
            
            # 응답 품질 검증
            resp_result = judge.judge_response(user_input, expected.get("expected_response_contains", []), result_state.get("response", ""))

            # 종합 판정 (임계값 설정 가능)
            # 필터 매칭 조건을 논리적 매칭으로 다소 완화하거나 별도 가중치 부여 가능
            passed = intent_match and query_result["score"] >= 0.8 and p_metrics["recall"] >= 0.5

            results.append({
                "id": case_id,
                "passed": passed,
                "metrics": {
                    "intent": intent_match,
                    "filter": filter_match,
                    "task": task_match,
                    "recall": p_metrics["recall"],
                    "precision": p_metrics["precision"],
                    "query_score": query_result["score"],
                    "response_score": resp_result["score"]
                },
                "reasoning": f"Query: {query_result['reasoning']} | Response: {resp_result['reasoning']}",
                "error": None
            })
            logger.info(f"✅ Case {case_id} processed. Passed: {passed}")

        except Exception as e:
            logger.error(f"❌ Error in case {case_id}: {e}")
            results.append({"id": case_id, "passed": False, "error": str(e)})

    # 리포트 생성
    generate_report(results)

def generate_report(results: List[Dict]):
    total = len(results)
    passed_count = sum(1 for r in results if r.get("passed", False))
    avg_recall = sum(r.get("metrics", {}).get("recall", 0) for r in results) / total if total > 0 else 0
    avg_query_score = sum(r.get("metrics", {}).get("query_score", 0) for r in results) / total if total > 0 else 0

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# 🚀 LLM-as-a-Judge AI 검증 리포트 (Flash)\n\n")
        f.write(f"**생성 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 1. 종합 요약\n")
        f.write(f"- **총 테스트 케이스**: {total}\n")
        f.write(f"- **성공(PASS)**: {passed_count}\n")
        f.write(f"- **실패(FAIL)**: {total - passed_count}\n")
        f.write(f"- **통과율**: { (passed_count/total*100):.1f}%\n")
        f.write(f"- **평균 상품 재현율(Recall)**: {avg_recall:.2f}\n")
        f.write(f"- **평균 쿼리 의도 점수**: {avg_query_score:.2f}\n\n")

        f.write("## 2. 상세 결과 리스트\n")
        f.write("| ID | 상태(I/F/T) | Recall | Precision | Query 점수 | 총평 |\n")
        f.write("| --- | --- | --- | --- | --- | --- |\n")
        for r in results:
            if r.get("error"):
                f.write(f"| {r['id']} | ERROR | - | - | - | {r['error']} |\n")
                continue
            
            m = r["metrics"]
            st = f"{'✅' if m['intent'] else '❌'}/{'✅' if m['filter'] else '❌'}/{'✅' if m['task'] else '❌'}"
            overall = "**PASS**" if r["passed"] else "FAIL"
            f.write(f"| {r['id']} | {st} | {m['recall']:.2f} | {m['precision']:.2f} | {m['query_score']:.2f} | {overall} |\n")

        f.write("\n## 3. 주요 실패 사유 및 상세 분석 (LLM Reasoning)\n")
        for r in results:
            if not r.get("passed") and not r.get("error"):
                f.write(f"### ❌ Case {r['id']}\n")
                f.write(f"- **Reasoning**: {r.get('reasoning', 'N/A')}\n\n")

    logger.info(f"📊 Report generated at {REPORT_PATH}")

if __name__ == "__main__":
    asyncio.run(run_validation())
