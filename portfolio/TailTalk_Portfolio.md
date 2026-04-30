# [Portfolio] TailTalk: AI 기반 맞춤형 반려동물 제품 추천 플랫폼

> **"우리 아이에게 꼭 맞는 제품, AI가 데이터로 찾아줍니다."**
> 반려동물의 특성(품종, 나이, 건강 상태)을 반영한 RAG 기반 지능형 큐레이션 서비스

---

## 1. Project Overview
- **프로젝트명:** TailTalk (왈냥)
- **핵심 가치:** 파편화된 반려동물 제품 정보 사이에서 사용자의 반려동물 프로필에 최적화된 제품을 제안하고 관리하는 AI 비서 서비스.
- **주요 기능:** 
  - 3-Panel 인터페이스 (대화 내역 / 메인 채팅 / 실시간 추천 카드)
  - 반려동물 맞춤형 RAG 기반 상담 및 추천
  - 감성 분석 및 OCR 성분 분석 데이터 기반의 신뢰도 높은 정보 제공

---

## 2. Tech Stack
- **Frontend:** Next.js, TypeScript, Tailwind CSS
- **Backend (Service):** Django (Auth, Pet Profile, Order Management)
- **Backend (AI):** FastAPI, LangGraph, LangChain
- **Database:** PostgreSQL (Relational), Qdrant (Vector DB)
- **Infrastructure:** Docker, Nginx, AWS (Elastic Beanstalk)
- **AI/ML:** OpenAI (GPT-4o), Gemini (Evaluation), OCR (PaddleOCR)

---

## 3. System Architecture
TailTalk은 서비스 안정성과 AI 추론 효율을 위해 **멀티 서비스 아키텍처**를 채택했습니다.
- **Django:** 유저 계정, 반려동물 프로필, 주문 시스템 등 전통적인 비즈니스 로직 담당.
- **FastAPI:** 비동기 처리가 필수적인 AI 챗봇 흐름(LangGraph) 및 벡터 검색 전담.
- **Nginx:** 단일 진입점을 통해 서비스 라우팅 및 보안 계층 형성.

---

## 4. Key Engineering Points

### 4.1. LangGraph 기반 Stateful AI Chatflow
단순한 1회성 질문 답변이 아닌, 사용자의 의도를 분석하고 상태를 유지하는 멀티턴 대화 구조를 설계했습니다.
- **Intent Classification:** 사용자 질문이 단순 지식 문의인지, 제품 추천 요청인지 분류.
- **Dynamic Retrieval:** 의도에 따라 지식 기반(RAG) 검색 또는 상품 DB 검색을 동적으로 선택.
- **Response Synthesis:** 검색된 정보와 반려동물 프로필을 결합하여 개인화된 응답 생성.

### 4.2. 하이브리드 검색 (Hybrid Search) 엔진
정확한 제품 매칭을 위해 Qdrant를 활용한 하이브리드 검색을 구현했습니다.
- **Dense Vector:** 시맨틱 의미 기반의 유사 상품 추천.
- **Sparse Vector:** 상품명, 브랜드 등 키워드 중심의 정확한 매칭.
- **결과:** 키워드 중심 검색 대비 사용자 만족도 및 추천 정확도 향상.

### 4.3. Medallion 데이터 파이프라인
데이터의 품질이 AI 성능을 결정한다는 원칙하에 3단계 데이터 정제 과정을 구축했습니다.
- **Bronze:** 원천 데이터(상품 정보, 리뷰, 이미지) 크롤링 및 수집.
- **Silver:** 중복 제거, 스키마 표준화 및 정규화.
- **Gold:** OCR을 통한 성분 추출, 리뷰 감성 분석 점수(Sentiment Score) 산출 등 피처 엔지니어링 수행.

---

## 5. Quality Assurance & Evaluation
AI 모델의 신뢰성을 확보하기 위해 정량적인 평가 지표를 도입했습니다.
- **Golden Dataset 구축:** 실제 서비스 시나리오를 바탕으로 한 100개 이상의 Ground Truth 데이터셋 생성.
- **LLM-as-a-Judge:** Gemini 모델을 활용하여 AI 응답의 **신뢰성(Faithfulness)**, **관련성(Relevance)**을 자동 평가하는 시스템 구축.
- **Iteration:** 평가 결과를 바탕으로 프롬프트 엔지니어링 및 검색 로직을 지속적으로 고도화.

---

## 6. Achievements & Lessons
- **기술적 성과:** 
  - LangGraph 도입을 통해 대화 이탈률 감소 및 복잡한 추천 시나리오 해결.
  - 벡터 DB(Qdrant) 최적화로 대규모 상품 데이터셋에서도 200ms 이내의 검색 속도 유지.
- **협업 경험:** 
  - Django와 FastAPI 간의 API 통신 규격 정의 및 데이터 동기화 이슈 해결.
  - 데이터 엔지니어링 팀과 AI 팀 간의 Gold 데이터 피드백 루프 형성.

---
**GitHub:** [https://github.com/skn-ai22-251029/SKN22-Final-2Team-WEB](https://github.com/skn-ai22-251029/SKN22-Final-2Team-WEB)
