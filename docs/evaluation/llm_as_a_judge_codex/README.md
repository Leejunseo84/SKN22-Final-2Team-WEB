## Codex Evaluator

`services/fastapi/final_ai` 코드는 수정하지 않고, 기존 하네스와 도메인 로직을 재사용해 `docs/evaluation/ragas_dataset/ai_logic_golden_dataset.jsonl`을 평가하는 스크립트 모음입니다.

### 구성

- `adapter.py`
  - 골든 JSONL을 로컬 evaluator 입력으로 변환
  - `current_pet_profiles`, `conversation_history`, 세션별 `dialog_state`를 실제 서비스 초기 state와 비슷하게 매핑
- `judge.py`
  - 검색 쿼리 의도와 응답 품질에 대한 optional LLM judge
  - API/네트워크가 없으면 자동으로 skip
- `run_eval.py`
  - `ChatRequest -> initial_state -> intent -> profile/query/search/rerank` 순서로 실행
  - deterministic 결과와 optional LLM judge 결과를 JSON/Markdown 리포트로 저장

### 기본 실행

```bash
python3 docs/evaluation/llm_as_a_judge_codex/run_eval.py
```

### 옵션

```bash
python3 docs/evaluation/llm_as_a_judge_codex/run_eval.py \
  --with-llm-judge \
  --with-system-response
```

### 출력

- `docs/evaluation/llm_as_a_judge_codex/report.json`
- `docs/evaluation/llm_as_a_judge_codex/report.md`

### 주의

- 추천 검색은 실제 `final_ai` 검색/리랭크 로직을 호출하므로 DB 연결 상태에 영향을 받습니다.
- `classify_intent`, `build_response_state`, LLM judge는 OpenAI API 사용 가능 여부에 영향을 받습니다.
- API/DB가 없으면 가능한 범위까지만 실행하고, 실패 원인을 케이스별로 리포트합니다.
