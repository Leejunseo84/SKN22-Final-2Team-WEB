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
BASE_DIR = "/home/playdata/SKN22-Final-2Team-WEB"
# captured_logic_output.json과 ID가 매칭되는 Gemini 골든 데이터셋으로 변경
GOLDEN_PATH = os.path.join(BASE_DIR, "docs/evaluation/llm_as_a_judge_gemini/ai_logic_golden_dataset.json")
ACTUAL_PATH = os.path.join(BASE_DIR, "docs/evaluation/second_test/captured_logic_output.json")
TARGET_DIR = os.path.join(BASE_DIR, "docs/evaluation/second_test")
REPORT_PATH = os.path.join(TARGET_DIR, "evaluation_report_v2.md")
RESULTS_JSON_PATH = os.path.join(TARGET_DIR, "evaluation_results_v2.json")

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
    # Gemini 골든 데이터셋은 golden_products가 객체 리스트일 수 있음
    exp_products = golden.get("expected_output", {}).get("golden_products", [])
    if not isinstance(exp_products, list):
        exp_products = []
        
    exp_ids = []
    for p in exp_products:
        if isinstance(p, dict):
            exp_ids.append(str(p.get("goods_id", "")))
        else:
            exp_ids.append(str(p))
            
    exp_ids = [i for i in exp_ids if i][:5]
    
    act_ids = actual.get("logic", {}).get("last_recommended_goods_ids", [])
    if not isinstance(act_ids, list):
        act_ids = []
    act_ids = [str(i) for i in act_ids][:5]
    
    if not exp_ids:
        return {"recall": 1.0, "precision": 1.0, "f1": 1.0}
    
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
    if not os.path.exists(GOLDEN_PATH):
        print(f"Error: Golden dataset not found at {GOLDEN_PATH}")
        return
    if not os.path.exists(ACTUAL_PATH):
        print(f"Error: Actual output not found at {ACTUAL_PATH}")
        return

    golden_data = load_json(GOLDEN_PATH)
    actual_data = load_json(ACTUAL_PATH)
    
    actual_map = {item["case_id"]: item for item in actual_data}
    results = []
    
    print(f"Starting evaluation (V2) for {len(golden_data)} cases matching Gemini Dataset IDs...")
    
    for g_item in golden_data:
        case_id = g_item["id"]
        a_item = actual_map.get(case_id)
        
        if not a_item:
            # 매칭되지 않는 케이스 건너뜀 (이미 매칭 확인됨)
            continue
            
        logic_res = calculate_logic_score(g_item, a_item)
        retrieval_res = calculate_retrieval_score(g_item, a_item)
        keyword_res = calculate_keyword_match_score(g_item, a_item)
        
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

    if not results:
        print("No matches found between Golden Dataset and Actual Output IDs.")
        return

    generate_markdown_report(results)
    
    with open(RESULTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Evaluation complete. Matched {len(results)} cases.")

def generate_markdown_report(results: List[Dict]):
    total = len(results)
    if total == 0: return
    
    avg_logic = sum(r["scores"]["logic"]["overall"] for r in results) / total
    avg_retrieval_f1 = sum(r["scores"]["retrieval"]["f1"] for r in results) / total
    avg_retrieval_recall = sum(r["scores"]["retrieval"]["recall"] for r in results) / total
    avg_retrieval_precision = sum(r["scores"]["retrieval"]["precision"] for r in results) / total
    avg_keyword = sum(r["scores"]["keyword"]["score"] for r in results) / total
    avg_total = sum(r["scores"]["total"] for r in results) / total
    
    report = f"""# TailTalk AI Logic Evaluation Report (V2 - Second Test)
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Golden Dataset: `ai_logic_golden_dataset.json` (Gemini version)
Comparison Target: `docs/evaluation/second_test/captured_logic_output.json`

## 📊 Overall Performance Summary
| Metric | Average Score | Status |
| :--- | :--- | :--- |
| **Total Accuracy** | **{avg_total*100:.1f}%** | {'✅ PASS' if avg_total >= 0.85 else '⚠️ REVIEW'} |
| Logic Precision | {avg_logic*100:.1f}% | - |
| **Retrieval (F1 Score)** | **{avg_retrieval_f1*100:.1f}%** | - |
| Retrieval (Recall) | {avg_retrieval_recall*100:.1f}% | - |
| Retrieval (Precision) | {avg_retrieval_precision*100:.1f}% | - |
| Keyword Match | {avg_keyword*100:.1f}% | - |

## 📝 결과 분석 가이드
- **Total Accuracy**: Logic(40%), Retrieval(30%), Keyword(30%) 종합 점수입니다. (통과 기준: 85%)
- **Logic Precision**: Intent, Filter, Pet ID 연계 성능입니다.
- **Retrieval (F1)**: 추천 상품 ID 일치도입니다.
- **Keyword Match**: 응답 내 필수 단어 포함 여부입니다.

---

## 🔍 Detailed Analysis
"""
    sorted_res = sorted(results, key=lambda x: x["scores"]["total"])
    
    report += "### ❌ Low Scoring Cases (Top 10)\n"
    for r in sorted_res[:10]:
        report += f"""
#### [{r['case_id']}] {r['user_input']}
- **Total Score**: `{r['scores']['total']:.2f}`
- **Reasoning**: {r['scores']['keyword'].get('reasoning', 'N/A')}
- **Retrieval F1**: `{r['scores']['retrieval']['f1']:.2f}`
"""

    report += "\n---\n*End of Report*"
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report generated at {REPORT_PATH}")

if __name__ == "__main__":
    run_evaluation()
