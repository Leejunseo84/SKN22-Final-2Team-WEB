# 05. AI 엔진: LangGraph 기반 멀티 에이전틱 워크플로우

## 5.1 LangGraph 오케스트레이션
TailTalk의 추천 엔진은 단순한 질문-답변(Linear) 구조가 아닌, 상태(State)와 의도에 따라 동적으로 움직이는 **Agentic Workflow**입니다.
* **Intent Node**: 자연어 분석을 통해 사용자 의도(정보 질의, 상품 추천 등) 분류 및 검색 필터링 매개변수 추출
* **Profile Node**: 선택된 펫의 알러지, 품종, 생애주기 정보를 검색 컨텍스트에 긴밀하게 주입
* **RAG Flow**: 실시간 검색 데이터와 LLM의 지식을 결합하여 정확하고 설득력 있는 개인화 응답 생성

## 5.2 PostgreSQL 통합 하이브리드 검색 (Unified Hybrid Search)
데이터베이스 한 곳에서 모든 검색 요구사항을 처리하는 고효율 엔진을 구축하였습니다.
1. **Semantic Search (pgvector)**: "관절에 좋은 영양제"와 같이 질문의 의미를 파악하는 벡터 유사도 검색
2. **Keyword Search (TSVector)**: "오리젠", "치킨맛" 등 고유 명사와 키워드에 충실한 정밀 검색
3. **RRF (Reciprocal Rank Fusion)**: 벡터 순위와 키워드 순위를 수학적으로 결합하여 검색 결과의 신뢰도를 극대화

## 5.3 지능형 추천 세이프가드 (Safeguards)
* **Allergy Shield**: 펫 프로필의 알러지 성분이 포함된 상품은 추천 목록에서 강제로 제외
* **Age-Aware Filtering**: 퍼피/성견/시니어 등 연령대에 맞지 않는 부적합 사료 필터링
* **Filter Relaxation**: 사용자의 조건이 너무 까다로워 검색 결과가 없을 경우, "브랜드"나 "세부 조건"을 단계적으로 완화하여 최선의 대안 제시
