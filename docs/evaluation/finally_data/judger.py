import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 골든 데이터셋 경로를 result 폴더 내의 ids_only 파일로 변경
GOLDEN_PATH = os.path.join(BASE_DIR, "result", "ai_logic_golden_dataset_ids_only.json")
ACTUAL_PATH = os.path.join(BASE_DIR, "result", "captured_logic_output.json")
REPORT_PATH = os.path.join(BASE_DIR, "result", "evaluation_report.md")

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_logic_score(golden: Dict, actual: Dict) -> Dict:
    """인텐트, 필터, 펫 ID 등 논리적 정합성 평가"""
    expected = golden.get("expected_output", {})
    logic = actual.get("logic", {})
    
    # 1. Intents Match (Set comparison)
    exp_intents = set(expected.get("intents", []))
    act_intents = set(logic.get("intents", []))
    intent_score = 1.0 if exp_intents == act_intents else 0.5 if exp_intents & act_intents else 0.0
    
    # 2. Filters Match (Key-Value comparison)
    exp_filters = expected.get("filters", {})
    act_filters = logic.get("filters", {})
    
    filter_match_count = 0
    filter_keys = set(exp_filters.keys()) | set(act_filters.keys())
    for k in filter_keys:
        if str(exp_filters.get(k)).strip() == str(act_filters.get(k)).strip():
            filter_match_count += 1
    
    filter_dist = filter_match_count / len(filter_keys) if filter_keys else 1.0
    
    # 3. Target Pet ID Match
    exp_pet_id = str(expected.get("target_pet_id") or "None")
    act_pet_id = str(logic.get("target_pet_id") or "None")
    pet_id_match = (exp_pet_id == act_pet_id)
    
    overall_logic = (intent_score * 0.4) + (filter_dist * 0.4) + (1.0 if pet_id_match else 0.0) * 0.2
    
    return {
        "intent_match": intent_score,
        "filter_score": filter_dist,
        "pet_id_match": pet_id_match,
        "overall": overall_logic
    }

def calculate_retrieval_score(golden: Dict, actual: Dict) -> Dict:
    """상품 추천 정합성 평가 (Top 5 ID 비교)"""
    # ai_logic_golden_dataset_ids_only.json은 golden_products가 ID 리스트임
    exp_ids = golden.get("expected_output", {}).get("golden_products", [])
    if not isinstance(exp_ids, list):
        exp_ids = []
    
    # 상위 5개만 추출
    exp_ids = exp_ids[:5]
    
    # 로직 데이터셋에서 last_recommended_goods_ids 사용
    act_ids = actual.get("logic", {}).get("last_recommended_goods_ids", [])
    if not isinstance(act_ids, list):
        act_ids = []
    
    # 실제 응답에서도 상위 5개만 추출
    act_ids = act_ids[:5]
    
    if not exp_ids:
        return {"recall": 1.0, "precision": 1.0, "f1": 1.0}
    
    # 순서와 상관없이 ID 일치 여부 비교
    intersection = set(exp_ids) & set(act_ids)
    recall = len(intersection) / len(exp_ids)
    precision = len(intersection) / len(act_ids) if act_ids else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "recall": recall,
        "precision": precision,
        "f1": f1
    }

def calculate_keyword_match_score(golden: Dict, actual: Dict) -> Dict:
    """골든 데이터의 키워드가 실제 응답에 포함되어 있는지 판별"""
    expected_keywords = golden.get("expected_output", {}).get("expected_response_contains", [])
    actual_response = actual.get("actual_response", "")
    
    pet_profiles = golden.get("input", {}).get("current_pet_profiles", [])
    target_pet_id = golden.get("expected_output", {}).get("target_pet_id")
    
    if target_pet_id and pet_profiles:
        for p in pet_profiles:
            if p.get("pet_id") == target_pet_id:
                pet_name = p.get("name")
                if pet_name and pet_name not in expected_keywords:
                    expected_keywords.append(pet_name)
                break

    if not expected_keywords:
        return {"score": 1.0, "matches": [], "missing": []}
        
    matches = [k for k in expected_keywords if k in actual_response]
    missing = [k for k in expected_keywords if k not in actual_response]
    score = len(matches) / len(expected_keywords)
    
    return {
        "score": score,
        "matches": matches,
        "missing": missing,
        "reasoning": f"매칭된 키워드: {', '.join(matches)} | 누락된 키워드: {', '.join(missing)}"
    }

def run_evaluation():
    golden_data = load_json(GOLDEN_PATH)
    actual_data = load_json(ACTUAL_PATH)
    
    actual_map = {item["case_id"]: item for item in actual_data}
    
    results = []
    
    print(f"Starting evaluation for {len(golden_data)} cases using ID-only golden dataset...")
    
    for g_item in golden_data:
        case_id = g_item["id"]
        a_item = actual_map.get(case_id)
        
        if not a_item:
            print(f"Warning: Case {case_id} not found in logic output.")
            continue
            
        logic_res = calculate_logic_score(g_item, a_item)
        retrieval_res = calculate_retrieval_score(g_item, a_item)
        keyword_res = calculate_keyword_match_score(g_item, a_item)
        
        # 가중치: Logic(40%), Retrieval(30%), KeywordMatch(30%)
        total_score = (logic_res["overall"] * 0.4) + (retrieval_res["f1"] * 0.3) + (keyword_res["score"] * 0.3)
        
        results.append({
            "case_id": case_id,
            "user_input": g_item["input"]["user_input"],
            "scores": {
                "logic": logic_res,
                "retrieval": retrieval_res,
                "keyword": keyword_res,
                "total": total_score
            }
        })
        print(f"Processed {case_id}: Total Score {total_score:.2f}")

    generate_markdown_report(results)
    
    with open(os.path.join(BASE_DIR, "evaluation_results_v2.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def generate_markdown_report(results: List[Dict]):
    total = len(results)
    if total == 0: return
    
    avg_logic = sum(r["scores"]["logic"]["overall"] for r in results) / total
    avg_retrieval_f1 = sum(r["scores"]["retrieval"]["f1"] for r in results) / total
    avg_retrieval_recall = sum(r["scores"]["retrieval"]["recall"] for r in results) / total
    avg_retrieval_precision = sum(r["scores"]["retrieval"]["precision"] for r in results) / total
    avg_keyword = sum(r["scores"]["keyword"]["score"] for r in results) / total
    avg_total = sum(r["scores"]["total"] for r in results) / total
    
    report = f"""# TailTalk AI Logic Evaluation Report (V2)
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Golden Dataset: `ai_logic_golden_dataset_ids_only.json`
Comparison Target: `last_recommended_goods_ids`

## 📊 Overall Performance Summary
| Metric | Average Score | Status |
| :--- | :--- | :--- |
| **Total Accuracy** | **{avg_total*100:.1f}%** | {'✅ PASS' if avg_total > 0.85 else '⚠️ REVIEW'} |
| Logic Precision | {avg_logic*100:.1f}% | - |
| **Retrieval (F1 Score)** | **{avg_retrieval_f1*100:.1f}%** | - |
| Retrieval (Recall) | {avg_retrieval_recall*100:.1f}% | - |
| Retrieval (Precision) | {avg_retrieval_precision*100:.1f}% | - |
| Keyword Match | {avg_keyword*100:.1f}% | - |

## 📝 결과 분석 가이드
- **Total Accuracy**: Logic, Retrieval, Keyword 점수를 종합(4:3:3)한 최종 점수입니다. 85% 이상 시 통과(PASS)로 간주합니다.
- **Logic Precision**: 인텐트 분류(Intent), 검색 필터 추출(Filter), 타겟 펫 식별(Pet ID)의 정확도입니다. 모델의 의도 파악 능력을 나타냅니다.
- **Retrieval (F1/Recall/Precision)**: 골든 데이터셋의 상품 ID와 실제 모델이 추천한 `last_recommended_goods_ids`의 일치율입니다. 추천 엔진의 정확성을 평가합니다.
- **Keyword Match**: 시스템 응답 메시지에 필수 키워드(펫 이름, 카테고리 등)가 포함되었는지 확인합니다. 사용자에게 정보가 제대로 전달되었는지 평가하는 지표입니다.

---

## 🔍 Detailed Analysis

"""
    # 점수 낮은 순으로 정렬된 리스트 준비
    sorted_res = sorted(results, key=lambda x: x["scores"]["total"])
    
    report += "### ❌ Low Scoring Cases (Top 5)\n"
    for r in sorted_res[:5]:
        report += f"""
#### [{r['case_id']}] {r['user_input']}
- **Total Score**: `{r['scores']['total']:.2f}`
- **Reasoning**: {r['scores']['keyword']['reasoning']}
- **Retrieval F1**: `{r['scores']['retrieval']['f1']:.2f}` (Matched: {int(r['scores']['retrieval']['recall']*5)}/5)
"""

    report += """
---
*End of Report*
"""
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report generated at {REPORT_PATH}")

if __name__ == "__main__":
    run_evaluation()
