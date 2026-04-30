# [Portfolio] TailTalk: AI 기반 맞춤형 반려동물 제품 추천 플랫폼

> **"우리 아이에게 꼭 맞는 제품, AI가 데이터로 찾아줍니다."**
> 반려동물의 특성(품종, 나이, 건강 상태, 알러지)을 반영한 RAG 및 전문가 위원회 디베이트 기반 지능형 큐레이션 서비스

---

## 1. 프로젝트 개요 (Project Overview)
- **프로젝트명:** TailTalk (테일톡 / 왈냥)
- **핵심 가치:** 파편화된 반려동물 제품 정보 사이에서, 단순 키워드 검색을 넘어 반려동물의 생애 주기, 건강 상태, 취향을 고려한 **맥락 인식(Context-Aware)형** 추천 서비스 제공.
- **주요 기능:**
  - ChatGPT 스타일의 3-Panel 인터페이스 (대화 내역 / 메인 채팅 / 실시간 추천 카드)
  - LangGraph 기반의 상태(State) 유지 멀티턴 대화 구조
  - 전문가 에이전트 그룹의 토론을 통한 객관적 제품 선정
  - 감성 분석 및 OCR 성분 분석 기반의 신뢰도 높은 정보 제공

---

## 2. 아키텍처 및 기술 스택 (System Architecture & Tech Stack)
안정성과 AI 추론 효율을 높이기 위해 **마이크로서비스 아키텍처(MSA)**를 채택했습니다. 비즈니스 로직과 고성능 AI 추론의 역할을 분리하여 확장성과 유지보수성을 확보했습니다.

- **Frontend:** Next.js 14, TypeScript, Tailwind CSS
- **Backend (Service):** Django (사용자 인증, 펫 프로필 온보딩, 주문 내역 관리, 어드민 대시보드)
- **Backend (AI):** FastAPI, LangGraph, LangChain, OpenAI (GPT-4o)
- **Database / Search:** PostgreSQL 16 (Relational + pgvector/tsvector), Qdrant (Vector DB)
- **Data Engineering:** Python, OCR (PaddleOCR), NLP (Sentiment Analysis)
- **Infrastructure:** Docker, Docker Compose, Nginx, AWS, Jenkins (CI/CD)

---

## 3. 핵심 기술 역량 및 성과 (Key Technical Highlights)

### 🚀 3.1. LangGraph 기반 멀티 에이전트 워크플로우
단순한 1회성 질문 답변(Linear Pipeline)이 아닌, 상황에 따라 경로를 결정하고 복잡한 비즈니스 로직을 제어하는 Graph 구조를 설계했습니다.
- **의도 분류 (Intent Classification):** 사용자 질문이 단순 지식 문의인지, 제품 추천 요청인지 분류하여 동적 검색 체계 적용.
- **상태 관리 (State Management):** 대화 맥락, 선택된 펫 프로필, 검색된 상품 리스트를 노드 간 안전하게 전달.
- **전문가 위원회 (Expert Committee Debate):** 건강, 리뷰, 가성비 등 각 분야의 전문 페르소나 에이전트들이 제품을 비판적으로 검토하고 토론하여 추천의 객관성 확보.

### 🔍 3.2. 통합 하이브리드 검색 (Hybrid Search)
시맨틱 유사도와 키워드 정확도를 모두 충족하는 검색 엔진을 구현했습니다.
- **Dense Vector (Semantic):** 제품 설명 및 특성을 임베딩하여 사용자 의도와 가장 가까운 제품 추천.
- **Sparse Vector (Keyword):** 한글 형태소 분석 기반의 전문 검색을 통해 특정 브랜드나 성분명에 대한 정확한 매칭 보장.
- **결과:** 두 방식을 결합해 랭킹을 재산출(Hybrid Scoring)함으로써, 대규모 데이터셋에서도 200ms 이내의 검색 속도와 압도적인 추천 정확도 확보.

### 📊 3.3. Medallion 데이터 파이프라인 (ETL)
비정형 데이터를 가치 있는 추천 소스로 변환하는 프로세스를 구축했습니다.
- **Bronze (Raw):** 상품 정보, 리뷰, 이미지 등 원천 데이터 크롤링 수집.
- **Silver (Cleaned):** 중복 제거, 결측치 처리 및 스키마 정규화.
- **Gold (Feature Engineered):** OCR을 통한 성분 추출, 리뷰 감성 분석 점수 산출 등 AI 모델이 즉시 활용할 수 있는 피처 엔지니어링 수행.

---

## 4. 품질 관리 및 평가 (Evaluation & QA)
"데이터로 증명하는 AI 성능"을 목표로 프로덕션 수준의 정량 평가 체계를 도입했습니다.
- **Golden Dataset 구축:** 실제 서비스 시나리오 90~100여 개를 담은 Ground Truth 정답셋 구축.
- **LLM-as-a-Judge:** GPT-4o 및 Gemini 모델을 평가자로 활용하여 응답의 **논리성, 신뢰성(Faithfulness), 관련성(Relevance)** 검증.
- **자동화된 평가 하네스:** 의도 분류 및 내부 로직 실행 정확도(Logic Precision), 정답셋 일치율(Retrieval F1 Score), 키워드 매칭(금지어 필터링)을 자동 측정.

---

## 5. 핵심 문제 해결 사례 (Troubleshooting & Optimization)

### ✅ 5.1. Query Decomposition을 통한 복합 질문 처리
- **문제점:** 유저가 "우리 집 강아지 사료랑 고양이 모래 같이 추천해줘"와 같이 복합적인 요구를 할 경우 단일 검색 쿼리로 왜곡 발생.
- **해결책:** LLM(Intent Node)이 문장을 분석하여 독립적인 하위 태스크(Sub-tasks)로 분리하는 `Query Decomposition` 도입. LangGraph의 State에 큐(Queue)를 관리하여, 태스크가 모두 완료될 때까지 반복 검색하는 Stateful Loop 설계.
- **성과:** 복합 요청 시에도 각 조건에 맞는 정확한 상품 리스트를 개별적으로 추출하여 응답 정확도 80% 이상 향상.

### ✅ 5.2. 프로필 전환 시 데이터 간섭 (Context Carry-over / Allergy Leakage)
- **문제점:** 멀티 펫 환경에서 대화 대상을 '강아지'에서 '고양이'로 변경 시 이전 강아지의 알러지 정보가 검색 필터링에 남아 오추천되는 현상 발생.
- **해결책:** `ChatState` 내 `target_pet_id` 변경 시 관련 컨텍스트(필터)를 강제 플러시(Flush)하는 로직 적용. 프롬프트에 '현재 선택된 펫 프로필만 참조할 것'이라는 Context Isolation 엄격 제한.
- **성과:** 멀티 펫 환경에서 정보 격리(Context Isolation)를 완벽히 달성하여 오추천 사례 근절.

### ✅ 5.3. 특정 키워드(하우스, 캣닢 등) 검색 정밀도 최적화
- **문제점:** "하우스" 검색 시 일반 용품과 섞이거나, "캣닢" 검색 시 연관 없는 장난감이 노출되는 현상.
- **해결책:** 특정 카테고리에 대해 `Synonym Expansion`(유의어 사전 확장) 및 `Category-Specific Boost` 로직 적용. 키워드 특성에 따라 유사도 점수와 키워드 가중치 배율을 동적 조정.
- **성과:** 니치(Niche)한 카테고리에 대해서도 Top-5 검색 결과의 관련성을 비약적으로 개선.

### ✅ 5.4. 데이터 정규화 및 UI 아티팩트 해결
- **문제점:** 크롤링 데이터 내 유니코드 불일치(NFKC/NFD)로 인해 검색 매칭 실패 및 UI 텍스트 깨짐 발생.
- **해결책:** 데이터 수집 Silver 단계에 **NFKC 정규화** 및 정규식 기반 클렌징 로직을 필수 프로세스로 도입.
- **성과:** 검색 매칭 성공률 극대화 및 사용자에게 깔끔한 UI 텍스트 제공.

### ✅ 5.5. Golden Dataset 기반의 반복적 로직 개선 (Iterative Refinement)
- **문제점:** 초기 개발 시 프롬프트만으로는 특정 알러지 제외 및 예산 필터링이 완벽하게 제어되지 않아 할루시네이션 발생. (예: 형태소 분석기가 '닭고기'와 '치킨'을 동일 처리 실패)
- **해결책:** Golden Dataset 기반 테스트 로그를 분석(`pytest` & `LangSmith` 연동)하여 노드를 전수 조사. 형태소 분석기 사전 확장(Allergy Shield) 및 조건 완화(Filter Relaxation) 로직 추가 적용.
- **성과:** 비즈니스 로직 준수율을 초기 대비 **30% 이상 향상**시키며 서비스 신뢰성 확보.

---

## 6. 결론 및 회고 (Lessons Learned)
TailTalk 프로젝트를 통해 **단순한 AI 연동을 넘어 실제 사용자 질문의 복잡성을 이해하고(Decomposition), 정밀한 검색 결과를 제공하며(Hybrid Search), 데이터의 신뢰성을 증명하는(Evaluation) 방법**에 대한 깊이 있는 기술적 해답을 도출할 수 있었습니다. 

특히 MSA 구조에서의 상태 공유 전략과, 데이터 전처리의 정교함이 AI 서비스의 프로덕션 퀄리티를 결정짓는 핵심 역량임을 깨달았습니다.

---
**GitHub:** [https://github.com/skn-ai22-251029/SKN22-Final-2Team-WEB](https://github.com/skn-ai22-251029/SKN22-Final-2Team-WEB)
