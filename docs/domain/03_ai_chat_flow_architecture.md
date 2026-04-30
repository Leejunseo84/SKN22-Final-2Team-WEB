# AI 채팅 실행 흐름 및 아키텍처 (AI Chat Flow Architecture)

본 문서는 TailTalk AI 서비스의 사용자 입력부터 응답 생성까지의 논리적 흐름과 패키지 구조 내 물리적 파일 매핑을 설명합니다.

---

## 1. 시스템 진입점 (Entry Point)

사용자의 채팅 요청은 다음 순서로 전달됩니다.
1. **Django Proxy**: `services/django/chat/api/views.py`에서 FastAPI로 요청 위임.
2. **FastAPI Router**: `services/fastapi/final_ai/api/routers/chat.py`에서 요청 접수.
3. **Application Service**: `services/fastapi/final_ai/application/chat/service.py`에서 그래프 호출.

---

## 2. 랭그래프 구성 (LangGraph Architecture)

그래프의 뼈대와 노드 간의 연결(Edges)은 아래 파일에서 정의됩니다.
*   **경로**: `services/fastapi/final_ai/graph/builder.py`
*   **상태 정의**: `services/fastapi/final_ai/graph/state.py` (`ChatState` 클래스)

### 그래프 시각화 (추상 정의)
`START` -> `intent` -> `(Conditional Edge)`
- -> `clarify` -> `END`
- -> `general` -> `rag` -> `merge` -> `respond` -> `END`
- -> `profile` -> `query` -> `search` -> `rerank` -> `merge` -> `respond` -> `END`

---

## 3. 노드 상세 및 파일 매핑 (Nodes Mapping)

각 노드는 특정 역할을 수행하며 `domain/` 레이어의 비즈니스 로직을 호출합니다.

| 노드 명 | 역할 | 파일 경로 | 호출 서비스 (Domain) |
| :--- | :--- | :--- | :--- |
| **intent** | 질문 의도 분류 (추천/일반/모호) | `final_ai/graph/nodes/intent_node.py` | `domain/intent/service.py` |
| **clarify** | 정보 부족 시 사용자에게 되묻기 | `final_ai/graph/nodes/clarify_node.py` | `domain/intent/service.py` |
| **general** | 일반적인 대화 및 인사 처리 | `final_ai/graph/nodes/general_node.py` | `domain/response/compose_service.py` |
| **rag** | 지식 베이스(도메인 QA) 정보 조회 | `final_ai/graph/nodes/rag_node.py` | `domain/domain_qa/retrieval_service.py` |
| **profile** | 사용자/반려동물 프로필 컨텍스트 적용 | `final_ai/graph/nodes/profile_node.py` | `domain/profile/service.py` |
| **query** | 검색 최적화 쿼리 생성 | `final_ai/graph/nodes/query_node.py` | `domain/recommendation/search_service.py` |
| **search** | 벡터 DB(Qdrant) 및 상품 검색 | `final_ai/graph/nodes/search_node.py` | `infrastructure/search/hybrid_search.py` |
| **rerank** | 선호도 및 건강 기반 랭킹 최적화 | `final_ai/graph/nodes/rerank_node.py` | `domain/recommendation/rerank_service.py` |
| **merge** | 조회된 정보 통합 및 필터링 | `final_ai/graph/nodes/merge_node.py` | `contracts/chat.py` |
| **respond** | 최종 친절한 응답 문장 생성 | `final_ai/graph/nodes/respond_node.py` | `domain/response/compose_service.py` |

---

## 4. 실행 순서 및 조건부 분기 (Execution Sequence)

1.  **초기화**: `builder.py`의 `chat()` 함수가 `user_input`과 `ChatState`를 초기화하여 그래프를 실행합니다.
2.  **의도 분류 (`intent`)**: 사용자 질문이 `recommend` 인지 `domain_qa` 인지 판단합니다.
3.  **동적 분기 (`route_intent`)**:
    *   질문이 모호하면 `clarify` 노드로 가고 즉시 종료합니다.
    *   `domain_qa` 의도라면 `general` 노드를 거쳐 지식 검색(`rag`)을 수행합니다.
    *   `recommend` 의도라면 `profile` 노드를 시작으로 검색 파이프라인(`query` -> `search` -> `rerank`)을 실행합니다.
4.  **병합 및 응답**: 모든 정보를 `merge` 노드에서 결합한 뒤, `respond` 노드에서 LLM을 사용해 최종 답변을 스트리밍 방식으로 반환합니다.

---

> [!NOTE]
> 모든 노드는 `final_ai/infrastructure/observability/`의 로거를 사용하여 `request_id`별로 추적됩니다. 에러 발생 시 로그에서 전체 흐름 상의 어떤 노드에서 중단되었는지 확인 가능합니다.
