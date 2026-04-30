# [Portfolio] TailTalk: AI 기반 반려동물 맞춤형 제품 추천 플랫폼 (Technical Deep Dive)

> **복합 질문 처리(Query Decomposition)와 하이브리드 검색 기반의 고정밀 AI 추천 시스템**

---

## 1. 프로젝트 개요 (Project Overview)
- **서비스명**: TailTalk (테일톡)
- **핵심 가치**: 개별 반려동물 프로필에 최적화된 상품을 추천하는 전문가 위원회 기반 AI 시스템.
- **아키텍처**: MSA (Next.js, Django, FastAPI) + PostgreSQL (Unified Search).

---

## 2. 핵심 기술적 성과 (Key Technical Achievements)

### 🚀 2.1. Query Decomposition (복합 질문 해결)
유저의 파편화된 요구사항을 정밀하게 처리하기 위해 **질문 분해(Decomposition)** 로직을 구현했습니다.
- **Problem**: "우리 강아지 사료랑 고양이 간식 추천해줘"와 같은 다중 목적 질문에 대해 단일 검색 쿼리가 실패하는 현상.
- **Solution**: LangGraph 내 `decomposition` 노드를 배치하여 질문을 `[강아지 사료 검색, 고양이 간식 검색]`과 같은 독립 태스크로 분리.
- **Result**: 복합 요청에 대해서도 누락 없는 상품 추천 및 각 태스크별 최적화된 필터 적용 가능.

### 🔍 2.2. PostgreSQL 통합 하이브리드 검색
- **Semantic Search**: `pgvector`를 활용하여 제품 설명의 맥락적 의미 파악 및 추천.
- **Exact Match**: `tsvector`를 이용한 한글 형태소 분석 기반 검색으로 브랜드/성분명의 정확한 매칭 보장.
- **Efficiency**: 별도의 벡터 DB(Qdrant 등) 없이 단일 DB로 구축하여 인프라 비용 절감 및 데이터 동기화 이슈 해결.

---

## 3. 핵심 트러블슈팅 사례 (Troubleshooting)

### ✅ 3.1. 프로필 전환 시 알러지 정보 간섭 (Context Carry-over)
- **Issue**: 대화 중 대상을 바꿨을 때 이전 펫의 알러지 성분이 필터링에 남아 오추천이 발생하는 심각한 결함 발견.
- **Debug & Fix**: 
  - `ChatState` 내의 `target_pet_id`가 변경될 때마다 관련 컨텍스트 정보를 명시적으로 플러시(Flush)하는 로직 도입.
  - 시스템 프롬프트에 **"이전 정보가 아닌 현재 선택된 펫 프로필만 참조할 것"**이라는 강한 제약 조건 추가.
- **Success**: 멀티 펫 환경에서도 완벽한 정보 격리(Context Isolation) 달성.

### ✅ 3.2. 검색 정밀도 최적화 (하우스, 캣닢 사례)
- **Issue**: 특정 키워드 검색 시 관련성이 낮은 제품이 상위에 노출되는 현상.
- **Debug & Fix**:
  - `category_boost` 로직을 도입하여 키워드에 따라 관련 카테고리 가중치를 동적으로 상향.
  - 형태소 분석기 특성에 따른 매칭 오류를 잡기 위해 유의어 사전(Synonym) 확장 적용.
- **Success**: 니치한 카테고리 키워드에 대해서도 Top-5 검색 정확도 비약적 상승.

### ✅ 3.3. 데이터 일관성 및 UI 아티팩트 해결
- **Issue**: 크롤링 데이터의 유니코드 불일치로 인한 검색 실패 및 텍스트 깨짐 현상.
- **Debug & Fix**: 데이터 파이프라인의 `Silver` 단계에서 **NFKC 정규화**를 필수 프로세스로 추가하여 데이터 포맷 통일.
- **Success**: 검색 성공률 및 UI 텍스트 출력 품질 안정화.

---

## 4. 품질 관리 프로세스 (Quality Assurance)

### 🛡️ Golden Dataset & AI Evaluation
- **Dataset**: 90여 개의 시나리오별 정답 셋 구축.
- **Process**: 코드 수정 시마다 자동 평가 하네스를 실행하여 **Logic Precision, Retrieval F1** 지표 측정.
- **Refinement**: 실패 사례를 로그로 추적하여 프롬프트와 로직을 반복적으로 튜닝하는 **피드백 루프(Feedback Loop)** 완성.

---

## 5. 결론 및 회고
TailTalk 프로젝트를 통해 단순한 AI 연동을 넘어 **'어떻게 하면 실제 사용자 질문의 복잡성을 이해하고(Decomposition), 데이터의 신뢰성을 확보하며(Evaluation), 정밀한 검색 결과(Hybrid Search)를 줄 것인가'**에 대한 기술적 해답을 찾는 과정을 경험했습니다.
