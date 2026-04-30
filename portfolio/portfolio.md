# [Portfolio] TailTalk: AI 기반 반려동물 맞춤형 제품 추천 플랫폼

> **반려동물 개별 맞춤형 케어를 위한 전문가 위원회 디베이트 기반 RAG 시스템**

---

## 1. 프로젝트 개요 (Project Overview)

- **서비스명**: TailTalk (테일톡)
- **핵심 가치**: 단순 키워드 검색을 넘어, 반려동물의 생애 주기, 건강 상태, 취향을 고려한 **맥락 인식(Context-Aware)형** AI 추천 서비스 제공.
- **주요 기능**:
  - ChatGPT 스타일의 3패널 UI (채팅 히스토리, 대화창, 실시간 추천 상품 패널).
  - LangGraph 기반의 복잡한 추천 워크플로우 제어.
  - 전문가 에이전트 그룹의 토론을 통한 최종 제품 선정.
  - 데이터 신뢰성 확보를 위한 Medallion 아키텍처 데이터 파이프라인.

---

## 2. 아키텍처 (System Architecture)

TailTalk은 유연성과 확장성을 위해 마이크로서비스 아키텍처(MSA)를 채택했습니다.

- **Frontend**: Next.js 14, Tailwind CSS (반응형 3패널 인터페이스)
- **Main Database**: PostgreSQL 16 (Relation Data + Vector Search)
- **AI Engine**: FastAPI, LangGraph, OpenAI (GPT-4o)
- **Search System**: PostgreSQL (pgvector for Similarity, tsvector for Keyword)
- **Infrastructure**: Docker, Nginx, AWS, Jenkins (CI/CD)

---

## 3. 핵심 기술 및 성과 (Key Technical Highlights)

### 🚀 3.1. LangGraph 기반 멀티 에이전트 워크플로우
단순한 ChatBot을 넘어, 복잡한 비즈니스 로직을 상태(State) 기반으로 제어합니다.
- **Intent Classification**: 사용자 질문의 의도를 분석하여 RAG 검색 여부 결정.
- **State Management**: 대화 맥락, 선택된 반려동물 프로필, 검색된 상품 리스트를 노드 간 안전하게 전달.
- **Expert Committee Debate**: 건강/리뷰/가성비 등 각 분야의 전문 페르소나 에이전트들이 제품을 검토하고 비판하는 토론 과정을 통해 추천의 객관성 확보.

### 🔍 3.2. PostgreSQL 기반 하이브리드 검색 (Unified DB)
별도의 벡터 DB 없이 PostgreSQL 하나로 키워드와 유사도 검색을 통합하여 인프라 복잡도를 낮추고 데이터 일관성을 확보했습니다.
- **Semantic Search (pgvector)**: 제품 설명 및 특성을 임베딩하여 사용자 의도와 가장 가까운 제품을 벡터 유사도 기반으로 검색.
- **Keyword Search (tsvector)**: 한글 형태소 분석을 통한 전문 검색(Full-Text Search)을 적용하여 특정 브랜드나 성분명에 대한 정확한 매칭 제공.
- **Hybrid Scoring**: 두 검색 방식을 결합하여 랭킹을 재산출함으로써 검색 품질 최적화.

### 📊 3.3. Medallion 데이터 파이프라인 (ETL)
비정형 데이터를 가치 있는 추천 소스로 변환하는 프로세스를 구축했습니다.
- **Bronze (Raw)**: 크롤링을 통한 원천 데이터 수집.
- **Silver (Cleaned)**: 중복 제거, 결측치 처리 및 정규화.
- **Gold (Feature Engineered)**: 성분 OCR 분석, 리뷰 감성 분석(Sentiment Analysis)을 통한 제품 스코어링 적용.

---

## 4. 품질 관리 및 평가 (Evaluation & Quality Control)

**"데이터로 증명하는 AI 성능"**을 위해 프로덕션 급 평가 체계를 구축했습니다.

- **Golden Dataset**: 실제 추천 시나리오 90개 이상의 정답셋(Target Pet, Filters, Expected Products) 구축.
- **LLM-as-a-Judge**: GPT-4o를 평가자로 활용하여 AI 응답의 논리적 타당성 검증.
- **Automated Evaluation Harness**:
  - **Logic Precision**: 의도 분류 및 내부 로직 실행의 정확도 측정.
  - **Retrieval F1 Score**: 추천된 제품이 정답셋과 얼마나 일치하는지 측정.
  - **Keyword Match**: 필수 포함 키워드 및 금지어 필터링 검증.

---

## 5. 핵심 문제 해결 사례 (Troubleshooting & Optimization)

### ✅ 5.1. Query Decomposition을 통한 복합 질문 처리
- **문제점**: 유저가 "우리 강아지 사료랑 고양이 간식 같이 추천해줘"와 같이 여러 요구사항을 한 번에 말할 경우, 단일 검색 쿼리로는 정확한 결과를 내기 어려움.
- **해결책**: LangGraph 워크플로우에 `Query Decomposition` 단계를 추가. LLM이 복합 질문을 독립적인 하위 태스크(예: 태스크 1-강아지 사료, 태스크 2-고양이 간식)로 분해하도록 설계.
- **성과**: 각 태스크별로 최적화된 검색 파라미터를 생성하여 병렬/순차적으로 처리한 후 결과를 병합함으로써 복합 질문에 대한 응답 정확도를 80% 이상 향상.

### ✅ 5.2. 프로필 전환 시 데이터 간섭(Allergy Leakage) 해결
- **문제점**: 멀티 펫 환경에서 '강아지'에서 '고양이'로 대화 대상을 바꿨음에도, 이전 강아지의 알러지 정보가 고양이 추천 로직에 남아있는 현상 발생.
- **해결책**:
  - `ChatState` 내 `target_pet_id` 변경 시 관련 필터를 강제 초기화하는 로직 구현.
  - 시스템 프롬프트에 `Context Isolation` 규칙을 추가하여 응답 생성 시 현재 선택된 펫의 프로필만 참조하도록 엄격히 제한.
- **성과**: 사용자별 멀티 펫 컨텍스트의 독립성을 확보하여 오추천 사례를 근절.

### ✅ 5.3. 특정 키워드(하우스, 캣닢 등) 검색 정밀도 최적화
- **문제점**: "하우스" 검색 시 일반적인 용품과 섞이거나, "캣닢" 검색 시 연관 없는 장난감이 상위에 노출되는 정밀도 이슈.
- **해결책**:
  - 특정 카테고리 키워드에 대해 `Synonym Expansion` 및 `Category-Specific Boost` 로직 적용.
  - `pgvector` 유사도 점수와 `tsvector` 가중치 배율을 키워드 특성에 맞게 동적으로 조정.
- **성과**: 니치(Niche)한 카테고리에 대한 검색 결과의 Top-5 관련성을 크게 개선.

### ✅ 5.4. 데이터 정규화 및 UI 아티팩트 제거
- **문제점**: 크롤링된 데이터 내 특수문자나 유니코드(NFKC/NFD) 불일치로 인해 UI에서 텍스트가 깨지거나 검색 매칭이 실패하는 문제.
- **해결책**: 데이터 수집 파이프라인(Silver 단계)에 `NFKC 정규화` 및 정규식 기반의 클렌징 로직을 도입하여 데이터 일관성 확보.
- **성과**: 검색 매칭 성공률을 높이고 사용자에게 깨끗한 UI 텍스트 제공.

### ✅ 5.5. Golden Dataset 기반의 프롬프트 엔지니어링 루프
- **문제점**: AI 응답 형식이 일관되지 않거나, 필수 정보를 누락하는 현상이 간헐적으로 발생.
- **해결책**: 90여 개의 테스트 케이스를 담은 **Golden Dataset**을 구축하고 자동 평가 하네스를 실행. 실패한 케이스의 로그를 분석하여 프롬프트를 반복적으로 수정(Iterative Refinement)하는 프로세스 정립.
- **성과**: 응답의 일관성 및 지시 사항 준수율을 비약적으로 높여 프로덕션 급 품질 달성.

---

## 6. 회고 및 성장 (Lessons Learned)

- AI 서비스 구축 시 모델의 성능만큼이나 **데이터의 정제 수준(Gold Data)**과 **평가 자동화(Evaluation)**가 프로덕션 퀄리티를 결정짓는 핵심임을 깨달았습니다.
- MSA 구조에서 서비스 간 통신과 상태 공유의 중요성을 경험하며, 효율적인 API 설계 역량을 길렀습니다.
