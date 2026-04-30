# TailTalk AI Logic Evaluation Report (V2)
Generated on: 2026-04-16 12:08:44
Golden Dataset: `ai_logic_golden_dataset_ids_only.json`
Comparison Target: `last_recommended_goods_ids`

## 📊 Overall Performance Summary
| Metric | Average Score | Status |
| :--- | :--- | :--- |
| **Total Accuracy** | **85.2%** | ✅ PASS |
| Logic Precision | 83.8% | - |
| **Retrieval (F1 Score)** | **95.7%** | - |
| Retrieval (Recall) | 95.7% | - |
| Retrieval (Precision) | 95.7% | - |
| Keyword Match | 76.5% | - |

## 📝 결과 분석 가이드
- **Total Accuracy**: Logic, Retrieval, Keyword 점수를 종합(4:3:3)한 최종 점수입니다. 85% 이상 시 통과(PASS)로 간주합니다.
- **Logic Precision**: 인텐트 분류(Intent), 검색 필터 추출(Filter), 타겟 펫 식별(Pet ID)의 정확도입니다. 모델의 의도 파악 능력을 나타냅니다.
- **Retrieval (F1/Recall/Precision)**: 골든 데이터셋의 상품 ID와 실제 모델이 추천한 `last_recommended_goods_ids`의 일치율입니다. 추천 엔진의 정확성을 평가합니다.
- **Keyword Match**: 시스템 응답 메시지에 필수 키워드(펫 이름, 카테고리 등)가 포함되었는지 확인합니다. 사용자에게 정보가 제대로 전달되었는지 평가하는 지표입니다.

---

## 🔍 Detailed Analysis

### ❌ Low Scoring Cases (Top 5)

#### [case_021] 요즘 인기 있는 강아지 옷 보여줘
- **Total Score**: `0.42`
- **Reasoning**: 매칭된 키워드: 추천 | 누락된 키워드: 인기, 강아지, 옷
- **Retrieval F1**: `0.00` (Matched: 0/5)

#### [case_092] 그중에서 제일 저렴한 거로 알려줘
- **Total Score**: `0.49`
- **Reasoning**: 매칭된 키워드:  | 누락된 키워드: 제일 저렴한, 가격 낮은 순, 추천, 사과
- **Retrieval F1**: `1.00` (Matched: 5/5)

#### [case_084] 아니 포도 말고 바나나 꺼 보여줘
- **Total Score**: `0.65`
- **Reasoning**: 매칭된 키워드: 바나나, 상품, 사료 | 누락된 키워드: 고양이, 간식, 용품, 모래, 습식관
- **Retrieval F1**: `1.00` (Matched: 5/5)

#### [case_091] 제일 싼 강아지 패드 보여줘
- **Total Score**: `0.67`
- **Reasoning**: 매칭된 키워드: 추천 | 누락된 키워드: 최저가, 가장 저렴한, 패드
- **Retrieval F1**: `1.00` (Matched: 5/5)

#### [case_069] 요즘 사과한테 필요한 인기 있는 패드 좀 보여줘
- **Total Score**: `0.72`
- **Reasoning**: 매칭된 키워드: 사과, 추천 | 누락된 키워드: 인기, 패드
- **Retrieval F1**: `1.00` (Matched: 5/5)

---
*End of Report*
