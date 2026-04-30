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



# 🚑 [Portfolio] SafeDrug: AI 에이전트 기반 의약품 안전 가이드 서비스

## 1. 프로젝트 개요 (Overview)

**SafeDrug**는 미국 등 해외를 방문 중인 한국인이 낯선 환경에서 겪는 증상을 분석하고, 개인별 메디컬 프로필과 실시간 한국(DUR) 및 미국(OpenFDA) 의약품 데이터를 결합하여 **가장 안전한 현지 약품 구매 및 복용 가이드**를 제공하는 **Agentic RAG 기반 지능형 서비스**입니다.
단순 검색을 넘어 AI 에이전트가 데이터의 정합성을 판단하고, 병용 금기 및 주의사항을 능동적으로 체크하여 언어 장벽과 정보 부족으로 인한 의약품 오남용 문제를 해결합니다.

---

## 2. 👨‍💻 주요 역할 및 기여도 (My Role & Contributions)

본 프로젝트에서 저는 **AI 에이전트의 지능 설계**, **시스템 성능 최적화**, **데이터 파이프라인 구축**을 담당하며 아래의 핵심 과업을 수행했습니다.

1. **AI 추천 로직 및 프롬프트 고도화**:
   - **CoT(Chain of Thought)** 기법을 적용하여 복잡한 증상에 대한 추론 정밀도 향상.
   - Prompt Injection 방어를 위한 보안 레이어 및 Strict JSON 출력 보장 로직 설계.
2. **에이전트 워크플로우 설계**:
   - 사용자의 구어체 질문을 표준 의학 용어로 변환하고 의도를 분류하는 파이프라인 구축.
   - DUR 데이터와 유저 프로필을 대조하여 성분을 분류(추천/주의/금기)하는 판단 로직 개발.
3. **응답 속도 최적화**:
   - **ASGI 전환 및 비동기(Async) 프로그래밍**을 도입하여 다중 API 호출 병목 현상 해결.
   - `asyncio.gather`를 활용한 병렬 데이터 수집으로 전체 응답 시간 약 40~50% 단축.

---

## 3. 🛠 핵심 기술 스택 (Tech Stack)

| Category               | Technologies                              | Role                                                    |
| :--------------------- | :---------------------------------------- | :------------------------------------------------------ |
| **Backend**      | Python, Django (ASGI), FastAPI            | 비동기 기반 웹 인터페이스 및 서비스 통합 서버           |
| **Orchestrator** | LangGraph, LangChain                      | 에이전틱 워크플로우 제어 및 상태(State) 관리            |
| **AI/LLM**       | OpenAI GPT-4o-mini                        | 의도 분류(Classifier), 정보 추출 및 최종 답변 생성      |
| **Database**     | Supabase (PostgreSQL / Vector), MySQL     | 유저 프로필 및 의료 데이터 저장 (RLS 보안 적용)         |
| **Data Source**  | KR DUR (공공데이터포털), e약은요, OpenFDA | 글로벌/국내 의약품 및 금기 정보 실시간 검색             |
| **DevOps**       | GitHub Actions, Git                       | CI/CD, 자동화 워크플로우(PR/Commit), 정기 데이터 동기화 |

---

## 4. 🏗 핵심 아키텍처 및 엔지니어링 (Architecture & Engineering)

### 4.1 LangGraph Multi-Agent Workflow

복잡한 의료 상담 프로세스를 상태 기반(State-based) 워크플로우로 구조화하여 유연성과 확장성을 확보했습니다.

- **지능형 의도 분류 (`classify_node`)**: 자연어 분석을 통해 `증상 기반 추천`, `제품 상세 정보`, `일반 의료 상담`으로 경로를 자동 분기. 불필요한 API 호출을 줄여 응답 정확도를 95% 이상으로 향상.
- **Multi-Source 데이터 통합 엔진 (`retrieve_nodes`)**: 국내(e약은요)와 해외(OpenFDA) API를 통합하고 실시간 DUR 조회를 통해 상호작용 검증.
- **상태 관리 (`AgentState`)**: 대화 컨텍스트를 유지하여 이전 답변에 기반한 후속 질문 처리.

### 4.2 Data Engineering & DevOps

- **데이터 파이프라인**: 5만여 건의 DUR 데이터를 수집/정제하는 `DurUnifiedCollector` 구현 및 KCD9 코드 매핑을 통한 질병-성분-제품 관계형 모델 설계.
- **AI-Driven DevOps**: 맞춤형 GitHub 스킬(`auto-pr`, `auto-commit`)을 적용하여 Semantic Commit 및 PR 본문 작성 자동화, `project-board-sync.yml`로 투명한 진행 관리.

---

## 5. 💡 기술적 도전 및 해결 전략 (Troubleshooting & Challenges)

프로젝트의 핵심은 **"AI의 편리함을 유지하면서 의료적 안전성을 확보하는 것"**이었습니다. 여러 기술적 난제를 다음과 같이 해결했습니다.

### 🔥 Case 1: LLM의 의료 정보 환각(Hallucination) 방지 (Strict RAG & Chain of Safety)

* **이슈**: LLM이 허구의 약품을 추천하거나 기저질환을 무시하고 위험한 성분을 권장하는 문제 발생.
* **해결**:
  * **강제 검증 노드**: LangGraph 상태 머신에 `[의도 분류] -> [성분 추출] -> [DUR 검증] -> [답변 생성]` 구조를 강제. `증상 추천` 시 반드시 DUR API를 거치도록 엣지(Edge) 설계.
  * **Strict RAG**: 시스템 프롬프트에 제공된 데이터 외부 지식 사용을 금지하여 AI의 자의적 판단 원천 차단.

### 🌐 Case 2: 파편화된 데이터 통합 및 한-영 용어 불일치 해결 (Entity Normalization)

* **이슈**: 한국어 구어체 증상 표현(예: "배가 살살 아파요")과 미국 FDA 영문 의학 용어 간 매칭 실패. 기관별 데이터 명칭 불일치.
* **해결**:
  * **Semantic Mapping Layer**: `SYMPTOM_TO_FDA_TERMS` 매핑 사전 및 LLM을 활용한 Entity Normalization 파이프라인을 최상단에 구축하여 쿼리 정규화.
  * **Unified Pipeline**: 중복을 제거하고 표준 식별자를 기준으로 묶는 통합 데이터 로더 설계로 매핑 성공률 40% 향상.

### ⚡ Case 3: 다단계 API 호출에 따른 응답 지연 최적화 (The Latency Wall)

* **이슈**: 4~5개의 외부 API를 순차 호출하며 응답 시간이 10~15초 이상 소요되어 UX 저하.
* **해결**:
  * **ASGI 전환**: Django WSGI의 스레드 블로킹 문제를 극복하기 위해 ASGI(Uvicorn/FastAPI 레이어) 환경으로 전면 전환.
  * **Async Concurrent Calls**: `asyncio.gather`를 활용해 여러 성분에 대한 DUR 체크 및 FDA 검색을 병렬로 처리.
  * **결과**: 전체 응답 지연 시간을 기존 대비 40~50% 단축.

### 🛡️ Case 4: 민감 의료 데이터 보안 및 프롬프트 방어 (Security First)

* **이슈**: 애플리케이션 버그로 인한 타인 의료 정보 유출 위험 및 악의적인 프롬프트 인젝션(해킹 시도) 위험.
* **해결**:
  * **Supabase RLS 적용**: 데이터베이스 엔진 레벨에서 `auth.uid() = user_id` 조건을 검사하는 Row Level Security를 적용해 원천적 데이터 격리 보장.
  * **Prompt Defense**: 시스템 최상단에 보안 규칙 배치, 무관한 질문 유입 시 즉각적인 `Invalid` 반환 처리 적용.

### 🧠 Case 5: CoT(Chain of Thought)를 통한 추론 정밀도 향상

* **이슈**: 사용자가 여러 증상을 복합적으로 말할 경우 핵심 키워드 추출 실패 및 논리적 오류 발생.
* **해결**: 출력 형식에 `"reason"` 필드를 필수 포함하여 AI가 스스로 분석 근거를 먼저 서술하도록(Step-by-step reasoning) 강제. 다중 증상에서도 정확도 대폭 향상.

### 📝 Case 6: 데이터 인코딩 및 가독성 문제 (Mojibake 자동 정제)

* **이슈**: 구형 공공 API 데이터의 인코딩 충돌로 인한 텍스트 깨짐 현상.
* **해결**: 정규표현식 기반 `_looks_mojibake` 헬퍼 함수를 적용하여 비정상 문자 조합을 탐지하고 자동 정제하는 필터 도입.

---

## 6. 📊 성과 및 핵심 역량 (Key Competencies & Impact)

1. **에이전틱 AI 설계 역량**: LangGraph를 활용해 복잡한 비즈니스 로직과 LLM을 결합한 지능형 시스템 구축 경험.
2. **비동기 시스템 최적화**: Python `async/await` 활용으로 대규모 I/O 바운드 작업의 병목 현상 해결 능력.
3. **데이터 통합 및 품질 관리**: 파편화된 공공데이터의 불일치를 해소하는 데이터 엔지니어링 역량.
4. **보안 및 자동화(DevOps)**: DB 레벨(RLS) 보안 정책 수립 및 AI 기반 CI/CD 자동화 인프라 구성.

---

## 7. 🚀 마무리 및 회고 (Retrospective)

**SafeDrug**는 **"AI의 혁신성"**과 **"엔지니어링적 안정성(의료 도메인의 엄격함)"** 사이의 균형을 에이전틱 아키텍처와 비동기 최적화로 풀어낸 프로젝트입니다. 단순 기능 구현을 넘어, 데이터 수집부터 워크플로우 통제, 보안, 응답성 개선에 이르는 Full-Cycle 문제 해결 과정을 통해 견고한 시스템 아키텍처의 중요성을 깊이 체감할 수 있었습니다. 향후 처방전 OCR 기능과 실시간 약국 재고 연동을 통해 더욱 완성도 높은 의료 생태계를 구축할 계획입니다.