# TailTalk AI Logic Evaluation Report (V2 - Second Test)
Generated on: 2026-04-21 11:50:54
Golden Dataset: `ai_logic_golden_dataset.json` (Gemini version)
Comparison Target: `docs/evaluation/second_test/captured_logic_output.json`

## 📊 Overall Performance Summary
| Metric | Average Score | Status |
| :--- | :--- | :--- |
| **Total Accuracy** | **56.4%** | ⚠️ REVIEW |
| Logic Precision | 73.5% | - |
| **Retrieval (F1 Score)** | **40.4%** | - |
| Retrieval (Recall) | 40.4% | - |
| Retrieval (Precision) | 40.4% | - |
| Keyword Match | 49.6% | - |

## 📝 결과 분석 가이드
- **Total Accuracy**: Logic(40%), Retrieval(30%), Keyword(30%) 종합 점수입니다. (통과 기준: 85%)
- **Logic Precision**: Intent, Filter, Pet ID 연계 성능입니다.
- **Retrieval (F1)**: 추천 상품 ID 일치도입니다.
- **Keyword Match**: 응답 내 필수 단어 포함 여부입니다.

---

## 🔍 Detailed Analysis
### ❌ Low Scoring Cases (Top 10)

#### [case_007_with_profile] 요즘 바나나한테 필요한 인기 있는 모래 좀 보여줘
- **Total Score**: `0.21`
- **Reasoning**: 매칭된 키워드: 추천 | 누락된 키워드: 바나나, 인기, 모래
- **Retrieval F1**: `0.00`

#### [case_005_with_profile_B] 응 사과 꺼 보여줘
- **Total Score**: `0.21`
- **Reasoning**: 매칭된 키워드:  | 누락된 키워드: 사과, 간식, 추천, 여기, 그다음, 포도, 보여줄까요
- **Retrieval F1**: `0.00`

#### [case_004_with_profile] 우리 바나나 체중, 피부 관리를 위한 사료 추천해줘
- **Total Score**: `0.22`
- **Reasoning**: 매칭된 키워드:  | 누락된 키워드: 바나나, 체중, 피부, 사료, 추천
- **Retrieval F1**: `0.00`

#### [case_011_with_profile] 사료 추천해줘
- **Total Score**: `0.26`
- **Reasoning**: 매칭된 키워드: 사료 | 누락된 키워드: 초코, 알러지, 닭고기, 제외
- **Retrieval F1**: `0.00`

#### [case_013_with_profile] 그중에서 제일 저렴한 거로 알려줘
- **Total Score**: `0.28`
- **Reasoning**: 매칭된 키워드:  | 누락된 키워드: 제일 저렴한, 가격 낮은 순, 추천, 바나나
- **Retrieval F1**: `0.00`

#### [case_008_with_profile_A] 초코 사료랑 간식이랑 용품 다 보여줘
- **Total Score**: `0.31`
- **Reasoning**: 매칭된 키워드: 사료, 추천 | 누락된 키워드: 초코, 그다음, 간식, 보여줄까요
- **Retrieval F1**: `0.00`

#### [case_008_with_profile_B] 응 간식도 보여줘
- **Total Score**: `0.31`
- **Reasoning**: 매칭된 키워드: 간식, 추천 | 누락된 키워드: 초코, 마지막으로, 용품, 보여줄까요
- **Retrieval F1**: `0.00`

#### [case_013_no_profile] 제일 싼 고양이 모래 보여줘
- **Total Score**: `0.32`
- **Reasoning**: 매칭된 키워드: 추천 | 누락된 키워드: 최저가, 가장 저렴한, 모래
- **Retrieval F1**: `0.00`

#### [case_005_with_profile_A] 우리 애들 사료랑 간식 추천해줘
- **Total Score**: `0.34`
- **Reasoning**: 매칭된 키워드: 사료, 추천, 바나나 | 누락된 키워드: 초코, 그다음, 간식, 보여줄까요
- **Retrieval F1**: `0.00`

#### [case_005_with_profile_B] 응 바나나 꺼 보여줘
- **Total Score**: `0.35`
- **Reasoning**: 매칭된 키워드:  | 누락된 키워드: 바나나, 간식, 추천, 여기
- **Retrieval F1**: `0.00`

---
*End of Report*