import os
import json
import sys
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from typing import Any, Dict, List

# 환경 변수 로드
load_dotenv()

# 경로 설정
ROOT = Path(__file__).resolve().parents[3]
FASTAPI_ROOT = ROOT / "services" / "fastapi"
if str(FASTAPI_ROOT) not in sys.path:
    sys.path.insert(0, str(FASTAPI_ROOT))

# RAGAS 및 관련 모듈 임포트
try:
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
    from datasets import Dataset
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    print("⚠️ Ragas or datasets library not installed. RAGAS evaluation will be skipped.")
    evaluate = None

# AI 로직 임포트
try:
    from final_ai.graph.builder import graph
    from final_ai.graph.state import ChatState
except ImportError as e:
    print(f"❌ Failed to import AI modules: {e}")
    sys.exit(1)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("IntegrationValidator")

CORE_PET_FIELDS = {"species", "breed", "name", "age", "gender"}

def filter_core_values(data: Any, core_keys: set = None) -> Any:
    """객체에서 핵심 비즈니스 값만 남기고 필터링합니다."""
    if isinstance(data, dict):
        if core_keys:
            return {k: v for k, v in data.items() if k in core_keys}
        return data
    if isinstance(data, list):
        return [filter_core_values(i, core_keys) for i in data]
    return data

def compare_deep(actual: Any, expected: Any) -> bool:
    """깊은 비교를 수행합니다."""
    if type(actual) != type(expected):
        return False
    if isinstance(actual, dict):
        for k, v in expected.items():
            if k not in actual or not compare_deep(actual[k], v):
                return False
        return True
    if isinstance(actual, list):
        if len(actual) != len(expected):
            return False
        return all(compare_deep(a, e) for a, e in zip(actual, expected))
    return actual == expected

def build_context_string(expected_output: Dict) -> str:
    """골든 데이터의 설정값들을 RAGAS용 컨텍스트 문자열로 변환합니다."""
    filters = expected_output.get("filters", {})
    profile = expected_output.get("pet_profile", {})
    
    context_parts = []
    if profile:
        p_str = f"펫 정보: 이름={profile.get('name')}, 종={profile.get('species')}, 품종={profile.get('breed')}"
        context_parts.append(p_str)
    
    if filters:
        f_str = f"적용 필터: 카테고리={filters.get('category')}, 하위카테고리={filters.get('subcategory')}, 검색어={expected_output.get('search_query')}"
        context_parts.append(f_str)
        
    return " | ".join(context_parts) if context_parts else "기본 컨텍스트"

async def run_validation():
    input_path = ROOT / "docs/evaluation/ragas_dataset/ai_logic_golden_dataset.jsonl"
    report_path = ROOT / "docs/evaluation/ragas_dataset/validation_report.md"
    
    if not input_path.exists():
        logger.error(f"❌ Input file not found: {input_path}")
        return

    results = []
    ragas_data = {
        "question": [],
        "answer": [],
        "contexts": [],
        "ground_truth": []
    }
    
    current_session_id = None
    current_state = None

    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()  # 전체 케이스 실행으로 복구

    logger.info(f"🚀 Starting validation for {len(lines)} cases...")

    for i, line in enumerate(lines):
        case = json.loads(line)
        case_id = case.get("id")
        session_id = case.get("session_id", "default")
        user_input = case["input"].get("user_input")
        expected = case.get("expected_output", {})
        
        # 세션 관리: 새로운 session_id가 나오면 상태 초기화
        if session_id != current_session_id:
            logger.info(f"🔄 New session detected: {session_id}")
            current_session_id = session_id
            current_state = {
                "user_input": user_input,
                "messages": [],
                "conversation_history": [],
                "pet_profile": case["input"].get("pet_profile"),
                "health_concerns": case["input"].get("health_concerns", []),
                "allergies": case["input"].get("allergies", []),
                "food_preferences": case["input"].get("food_preferences", []),
                "target_pet_id": case["input"].get("target_pet_id"),
                "decomposed_tasks": [],
                "pending_requests": [],
            }
        else:
            current_state["user_input"] = user_input
            # 멀티턴의 경우 이전 state가 유지됨

        # 로직 실행
        try:
            config = {"configurable": {"thread_id": session_id}}
            result_state = graph.invoke(current_state, config=config)
            current_state = result_state # 다음 턴을 위해 업데이트
            
            # 1. 상태 검토 (Internal State Matches)
            state_checks = {
                "intents": compare_deep(result_state.get("intents"), expected.get("intents")),
                "filters": compare_deep(result_state.get("filters"), expected.get("filters")),
                "pet_profile": compare_deep(
                    filter_core_values(result_state.get("pet_profile"), CORE_PET_FIELDS),
                    filter_core_values(expected.get("pet_profile"), CORE_PET_FIELDS)
                ),
                "search_query": result_state.get("search_query") == expected.get("search_query")
            }
            
            # 2. 결과 검토 (Output Matches)
            actual_products = [p.get("goods_id") for p in result_state.get("product_cards", [])]
            expected_products = [p.get("goods_id") for p in expected.get("golden_products", [])]
            product_match = actual_products[:len(expected_products)] == expected_products
            
            actual_response = result_state.get("response", "")
            expected_keywords = expected.get("expected_response_contains", [])
            keyword_match = all(kw in actual_response for kw in expected_keywords)
            
            all_passed = all(state_checks.values()) and product_match and keyword_match
            
            results.append({
                "id": case_id,
                "passed": all_passed,
                "checks": state_checks,
                "product_match": product_match,
                "keyword_match": keyword_match,
                "error": None
            })
            
            # RAGAS 데이터 수집
            ragas_data["question"].append(user_input)
            ragas_data["answer"].append(actual_response)
            ragas_data["contexts"].append([build_context_string(expected)])
            ragas_data["ground_truth"].append(", ".join(expected_keywords) if expected_keywords else "N/A")

        except Exception as e:
            logger.error(f"❌ Error in case {case_id}: {e}")
            results.append({"id": case_id, "passed": False, "error": str(e)})

    # RAGAS 평가 수행
    ragas_summary = {}
    if evaluate and ragas_data["question"]:
        try:
            logger.info("📊 Running RAGAS evaluation...")
            dataset = Dataset.from_dict(ragas_data)
            embeddings = OpenAIEmbeddings()
            score = evaluate(dataset, metrics=[faithfulness, answer_relevancy], embeddings=embeddings)
            ragas_summary = score
        except Exception as e:
            logger.error(f"❌ RAGAS evaluation failed: {e}")

    # 리포트 생성
    total = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# AI 시스템 정합성 및 RAGAS 평가 리포트\n\n")
        f.write(f"## 요약\n")
        f.write(f"- **총 테스트 케이스**: {total}\n")
        f.write(f"- **성공**: {passed}\n")
        f.write(f"- **실패**: {total - passed}\n")
        f.write(f"- **성공률**: {(passed/total*100):.1f}%\n\n")
        
        if ragas_summary:
            f.write("## RAGAS 지표\n")
            # Result 객체에서 요약 지표(평균 점수) 추출
            try:
                # Ragas 0.2.1+ Result/EvaluationResult 대응
                # 객체 자체를 순회하거나 dict() 변환이 실패할 경우를 대비하여 명시적으로 필드 확인
                summary_data = {}
                if hasattr(ragas_summary, 'items'):
                    summary_data = dict(ragas_summary.items())
                elif isinstance(ragas_summary, dict):
                    summary_data = ragas_summary
                else:
                    # pydantic 모델이거나 일반 객체인 경우
                    summary_data = {k: v for k, v in vars(ragas_summary).items() if not k.startswith('_') and k != 'scores'}
                
                for k, v in summary_data.items():
                    if isinstance(v, (int, float)):
                        f.write(f"- **{k}**: {v:.4f}\n")
                    else:
                        f.write(f"- **{k}**: {v}\n")
            except Exception as e:
                f.write(f"- 지표 추출 중 오류 발생: {e}\n")
            f.write("\n")
            
        f.write("## 상세 결과\n")
        f.write("| ID | 상태 검증 | 상품 일치 | 키워드 일치 | 결과 |\n")
        f.write("| --- | --- | --- | --- | --- |\n")
        for r in results:
            sc = "✅" if all(r.get("checks", {}).values()) else "❌"
            pm = "✅" if r.get("product_match") else "❌"
            km = "✅" if r.get("keyword_match") else "❌"
            overall = "PASS" if r.get("passed") else "FAIL"
            f.write(f"| {r['id']} | {sc} | {pm} | {km} | **{overall}** |\n")

    logger.info(f"✅ Validation complete. Report saved to {report_path}")

if __name__ == "__main__":
    asyncio.run(run_validation())
