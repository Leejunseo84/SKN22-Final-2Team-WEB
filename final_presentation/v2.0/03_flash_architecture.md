# 03. 시스템 아키텍처: 고성능 통합 AI 솔루션

## 3.1 기술 스택 (Tech Stack)
* **Frontend**: Django Templates (HTML/CSS/JavaScript)
* **Services Backend**: Django (User Management, Pet Profiles, Order System)
* **AI Backend**: FastAPI (LangGraph Orchestration, RAG Pipeline)
* **Database**: **PostgreSQL 16** (Unified DB: Relational + Vector Extension)
* **Infra**: Nginx, Docker, Docker Compose

## 3.2 서버 구성 및 데이터 흐름
1. **Request Hub (Nginx)**: 브라우저의 요청을 경로에 따라 Django 또는 FastAPI로 분기
2. **Business Core (Django)**: 사용자 인증, 펫 정보 관리 및 정형화된 데이터의 CRUD 담당
3. **AI Logic (FastAPI)**: 대화 맥락 유지, 하이브리드 검색 수행 및 최적의 답변 생성

## 3.3 아키텍처 혁신 포인트
* **Unified DB Strategy**: 벡터 검색용 외부 DB를 별도로 두지 않고, PostgreSQL의 `pgvector` 확장을 사용하여 RDB와 Vector 데이터를 통합 관리합니다. 
    * **장점**: 데이터 동기화 비용 제로, 인프라 운영 복잡성 최소화, 가용성 증대
* **Micro-Service Pattern**: 사용자 관리와 AI 추천 로직을 서비스 단위로 분리하여 각 도메인에 최적화된 프레임워크(Django/FastAPI) 선택
