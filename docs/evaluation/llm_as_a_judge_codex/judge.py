from __future__ import annotations

import os
import re
from typing import Any


def normalize_text(value: Any) -> str:
    if value in (None, ""):
        return ""
    return re.sub(r"\s+", "", str(value)).lower()


def keyword_contains_all(response: str, keywords: list[str]) -> tuple[bool, list[str]]:
    haystack = normalize_text(response)
    missing = [keyword for keyword in keywords if normalize_text(keyword) not in haystack]
    return not missing, missing


def token_intent_similarity(expected_query: str | None, actual_query: str | None) -> dict[str, Any]:
    expected_tokens = _query_tokens(expected_query)
    actual_tokens = _query_tokens(actual_query)
    if not expected_tokens and not actual_tokens:
        return {"passed": True, "score": 1.0, "label": "empty_both"}
    if not expected_tokens or not actual_tokens:
        return {"passed": False, "score": 0.0, "label": "empty_one_side"}
    overlap = len(expected_tokens & actual_tokens)
    union = len(expected_tokens | actual_tokens)
    score = overlap / union if union else 0.0
    return {
        "passed": score >= 0.5,
        "score": round(score, 4),
        "label": "token_jaccard",
        "expected_tokens": sorted(expected_tokens),
        "actual_tokens": sorted(actual_tokens),
    }


def llm_available() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def judge_search_query_with_llm(expected_query: str | None, actual_query: str | None) -> dict[str, Any]:
    if not llm_available():
        return {"status": "skipped", "reason": "OPENAI_API_KEY not set"}

    try:
        from openai import OpenAI

        client = OpenAI(timeout=30, max_retries=0)
        prompt = (
            "두 검색 쿼리가 단어 순서나 조사 차이를 넘어 동일한 검색 의도를 가지는지 판정하라.\n"
            "반드시 JSON으로만 답하라: "
            '{"label":"same_intent|partial|different","score":0.0,"reason":"..."}'
        )
        user = f"golden_query: {expected_query or ''}\nsystem_query: {actual_query or ''}"
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_EVAL_MODEL", "gpt-5-mini"),
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user},
            ],
        )
        return {"status": "ok", **_safe_json_loads(response.choices[0].message.content)}
    except Exception as exc:
        return {"status": "error", "reason": str(exc)}


def judge_response_with_llm(
    *,
    user_input: str,
    response: str,
    expected_keywords: list[str],
) -> dict[str, Any]:
    if not llm_available():
        return {"status": "skipped", "reason": "OPENAI_API_KEY not set"}

    try:
        from openai import OpenAI

        client = OpenAI(timeout=30, max_retries=0)
        prompt = (
            "응답이 키워드를 자연스럽게 포함하고 있는지, 사용자에게 불쾌하지 않고 요청에 맞는지 평가하라.\n"
            "반드시 JSON으로만 답하라: "
            '{"label":"good|partial|bad","score":0.0,"reason":"..."}'
        )
        user = (
            f"user_input: {user_input}\n"
            f"expected_keywords: {expected_keywords}\n"
            f"response: {response}"
        )
        response_obj = client.chat.completions.create(
            model=os.getenv("OPENAI_EVAL_MODEL", "gpt-5-mini"),
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user},
            ],
        )
        return {"status": "ok", **_safe_json_loads(response_obj.choices[0].message.content)}
    except Exception as exc:
        return {"status": "error", "reason": str(exc)}


def _query_tokens(value: str | None) -> set[str]:
    compact = re.sub(r"[^0-9A-Za-z가-힣\s]", " ", str(value or ""))
    return {token.lower() for token in compact.split() if token.strip()}


def _safe_json_loads(value: str) -> dict[str, Any]:
    import json

    try:
        payload = json.loads(value)
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass
    return {"raw": value}
