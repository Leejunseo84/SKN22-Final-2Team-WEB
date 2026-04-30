from __future__ import annotations

import argparse
import json
import sys
from contextlib import ExitStack
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
FASTAPI_ROOT = ROOT / "services" / "fastapi"
if str(FASTAPI_ROOT) not in sys.path:
    sys.path.insert(0, str(FASTAPI_ROOT))

from final_ai.application.chat.dto import build_chat_execution_request
from final_ai.contracts.chat import ChatRequest
from final_ai.contracts.filters import normalize_search_exclusions, normalize_search_filters
from final_ai.domain.intent.service import classify_intent
from final_ai.domain.recommendation.constants import MAX_FILTER_RELAXATION_COUNT
from final_ai.domain.recommendation.profile_service import build_profile_state
from final_ai.domain.recommendation.query_service import build_search_query_state
from final_ai.domain.recommendation.rerank_service import rerank_search_results
from final_ai.domain.recommendation.search_service import execute_search_state
from final_ai.domain.response.compose_service import build_response_state
from final_ai.graph.builder import route_intent

from adapter import (
    build_pet_profiles_lookup,
    build_registered_pets,
    build_seed_dialog_state,
    choose_active_pet,
    extract_golden_goods_ids,
    load_eval_cases,
    normalize_expected_filters,
    species_to_korean,
)
from judge import (
    judge_response_with_llm,
    judge_search_query_with_llm,
    keyword_contains_all,
    token_intent_similarity,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default=str(ROOT / "docs/evaluation/ragas_dataset/ai_logic_golden_dataset.jsonl"),
    )
    parser.add_argument(
        "--report-json",
        default=str(ROOT / "docs/evaluation/llm_as_a_judge_codex/report.json"),
    )
    parser.add_argument(
        "--report-md",
        default=str(ROOT / "docs/evaluation/llm_as_a_judge_codex/report.md"),
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--with-llm-judge", action="store_true")
    parser.add_argument("--with-system-response", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cases = load_eval_cases(args.input)
    if args.limit > 0:
        cases = cases[: args.limit]

    session_dialog_state: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []

    for case in cases:
        session_id = str(case.input.get("session_id") or "default")
        prior_dialog_state = session_dialog_state.get(session_id, {})
        current_pet_profiles = list(case.input.get("current_pet_profiles") or [])
        active_pet = choose_active_pet(current_pet_profiles)
        dialog_state = build_seed_dialog_state(prior_dialog_state, active_pet=active_pet)

        request = ChatRequest(
            message=str(case.input.get("user_input") or ""),
            thread_id=session_id,
            request_id=case.input.get("request_id"),
            user_id=str(case.input.get("user_id")) if case.input.get("user_id") is not None else None,
            target_pet_id=dialog_state.get("target_pet_id"),
            pet_profile=None,
            health_concerns=[],
            allergies=[],
            food_preferences=[],
            conversation_history=list(case.input.get("conversation_history") or []),
            dialog_state=dialog_state,
        )

        case_result = run_case(
            case=case,
            request=request,
            current_pet_profiles=current_pet_profiles,
            with_llm_judge=bool(args.with_llm_judge),
            with_system_response=bool(args.with_system_response),
        )
        results.append(case_result)
        report = build_report(results)
        Path(args.report_json).write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        Path(args.report_md).write_text(render_markdown(report), encoding="utf-8")

        if case_result.get("state", {}).get("dialog_state_for_next_turn") is not None:
            session_dialog_state[session_id] = dict(case_result["state"]["dialog_state_for_next_turn"])

    report = build_report(results)
    Path(args.report_json).write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    Path(args.report_md).write_text(render_markdown(report), encoding="utf-8")

    print(f"cases={report['summary']['total_cases']} passed={report['summary']['passed_cases']} failed={report['summary']['failed_cases']}")
    print(f"report_json={args.report_json}")
    print(f"report_md={args.report_md}")
    return 0


def run_case(
    *,
    case,
    request: ChatRequest,
    current_pet_profiles: list[dict[str, Any]],
    with_llm_judge: bool,
    with_system_response: bool,
) -> dict[str, Any]:
    registered_pets = build_registered_pets(current_pet_profiles)
    pet_profiles_lookup = build_pet_profiles_lookup(current_pet_profiles)
    expected = dict(case.expected_output or {})
    expected_filters = normalize_expected_filters(expected)

    initial_state = {}
    extracted_updates = {}
    final_state = {}
    route = None
    response_text = None
    error = None

    try:
        with _patch_pet_sources(registered_pets, pet_profiles_lookup):
            execution = build_chat_execution_request(request)
            initial_state = dict(execution.initial_state)
            extracted_updates = classify_intent(dict(initial_state))
            state = dict(initial_state)
            state.update(extracted_updates)
            route = _normalize_route(route_intent(state))

            if route != "clarify" and _has_recommend_intent(state):
                state.update(build_profile_state(state))
                for _ in range(MAX_FILTER_RELAXATION_COUNT + 1):
                    state.update(build_search_query_state(state))
                    state.update(execute_search_state(state))
                    state.update(rerank_search_results(state))
                    if not state.get("recommend_retry_pending"):
                        break

            if with_system_response:
                state.update(build_response_state(state))
                response_text = state.get("response")

            final_state = state
    except Exception as exc:
        error = str(exc)

    deterministic = evaluate_case_deterministically(
        case=case,
        request=request,
        expected_filters=expected_filters,
        route=route,
        final_state=final_state,
        response_text=response_text,
        error=error,
    )

    llm_judges = {}
    if with_llm_judge and not error:
        llm_judges["search_query"] = judge_search_query_with_llm(
            expected.get("search_query"),
            final_state.get("search_query"),
        )
        if response_text:
            llm_judges["response"] = judge_response_with_llm(
                user_input=request.message,
                response=response_text,
                expected_keywords=list(expected.get("expected_response_contains") or []),
            )
        else:
            llm_judges["response"] = {"status": "skipped", "reason": "system response not generated"}

    next_dialog_state = build_next_dialog_state(final_state)
    return {
        "case_id": case.case_id,
        "description": case.description,
        "request": {
            "session_id": request.thread_id,
            "user_id": request.user_id,
            "request_id": request.request_id,
            "user_input": request.message,
        },
        "state": {
            "initial_state": summarize_state(initial_state),
            "extracted_updates": summarize_state(extracted_updates),
            "final_state": summarize_state(final_state),
            "route": route,
            "dialog_state_for_next_turn": next_dialog_state,
        },
        "deterministic": deterministic,
        "llm_judges": llm_judges,
        "error": error,
    }


def evaluate_case_deterministically(
    *,
    case,
    request: ChatRequest,
    expected_filters: dict[str, Any],
    route: str | list[str] | None,
    final_state: dict[str, Any],
    response_text: str | None,
    error: str | None,
) -> dict[str, Any]:
    expected = dict(case.expected_output or {})
    final_slots = extract_comparable_slots(final_state)
    retrieved_goods_ids = _goods_ids(final_state.get("search_results"))
    reranked_goods_ids = _goods_ids(final_state.get("reranked_results"))
    golden_goods_ids = extract_golden_goods_ids(expected)

    expected_intents = set(expected.get("intents") or [])
    actual_intents = set(final_state.get("intents") or [])

    filter_failures = []
    for key, expected_value in expected_filters.items():
        actual_value = final_slots.get(key)
        if not _loosely_equal(actual_value, expected_value):
            filter_failures.append(
                {
                    "field": key,
                    "expected": expected_value,
                    "actual": actual_value,
                }
            )

    decomposed_expected = list(expected.get("decomposed_tasks") or [])
    decomposed_actual = list(final_state.get("decomposed_tasks") or [])

    keyword_expected = list(expected.get("expected_response_contains") or [])
    keyword_match, missing_keywords = keyword_contains_all(response_text or "", keyword_expected)

    query_token_eval = token_intent_similarity(
        expected.get("search_query"),
        final_state.get("search_query"),
    )

    deterministic_checks = {
        "session_match": request.thread_id == str(case.input.get("session_id") or "default"),
        "intent_match": actual_intents == expected_intents if expected_intents else True,
        "target_pet_id_match": (
            final_state.get("target_pet_id") == expected.get("target_pet_id")
            if "target_pet_id" in expected
            else True
        ),
        "requires_clarification_match": (
            (route == "clarify") == bool(expected.get("requires_clarification"))
            if "requires_clarification" in expected
            else True
        ),
        "filter_subset_match": not filter_failures,
        "decomposed_tasks_match": _compare_decomposed_tasks(decomposed_actual, decomposed_expected),
        "search_query_exact_match": _normalize(expected.get("search_query")) == _normalize(final_state.get("search_query")),
        "response_keywords_match": keyword_match if response_text is not None else None,
    }

    overlap_retrieved = overlap_metrics(retrieved_goods_ids, golden_goods_ids)
    overlap_reranked = overlap_metrics(reranked_goods_ids, golden_goods_ids)

    return {
        "checks": deterministic_checks,
        "expected": {
            "intents": sorted(expected_intents),
            "filters": expected_filters,
            "decomposed_tasks": decomposed_expected,
            "search_query": expected.get("search_query"),
            "golden_goods_ids": golden_goods_ids,
            "expected_response_contains": keyword_expected,
        },
        "actual": {
            "intents": sorted(actual_intents),
            "slots": final_slots,
            "decomposed_tasks": decomposed_actual,
            "search_query": final_state.get("search_query"),
            "route": route,
            "retrieved_goods_ids": retrieved_goods_ids,
            "reranked_goods_ids": reranked_goods_ids,
            "response": response_text,
        },
        "search_query_token_eval": query_token_eval,
        "response_keyword_missing": missing_keywords,
        "filter_failures": filter_failures,
        "retrieved_overlap": overlap_retrieved,
        "reranked_overlap": overlap_reranked,
        "error": error,
        "passed": error is None
        and all(value is True or value is None for value in deterministic_checks.values()),
    }


def summarize_state(state: dict[str, Any]) -> dict[str, Any]:
    if not state:
        return {}
    return {
        "target_pet_id": state.get("target_pet_id"),
        "pet_profile": state.get("pet_profile"),
        "health_concerns": list(state.get("health_concerns") or []),
        "allergies": list(state.get("allergies") or []),
        "intents": list(state.get("intents") or []),
        "filters": normalize_search_filters(state.get("filters")),
        "exclusions": normalize_search_exclusions(state.get("exclusions")),
        "decomposed_tasks": list(state.get("decomposed_tasks") or []),
        "pending_requests": list(state.get("pending_requests") or []),
        "search_query": state.get("search_query"),
        "filter_relaxation_count": state.get("filter_relaxation_count"),
        "recommend_retry_pending": state.get("recommend_retry_pending"),
        "search_results_count": len(state.get("search_results") or []),
        "reranked_results_count": len(state.get("reranked_results") or []),
        "last_recommended_goods_ids": list(state.get("last_recommended_goods_ids") or []),
        "is_result_refinement": bool(state.get("is_result_refinement")),
        "refinement_sort": state.get("refinement_sort"),
        "response": state.get("response"),
    }


def build_next_dialog_state(state: dict[str, Any]) -> dict[str, Any] | None:
    if not state:
        return None
    keys = (
        "user_id",
        "target_pet_id",
        "pet_profile",
        "health_concerns",
        "allergies",
        "food_preferences",
        "intents",
        "filters",
        "exclusions",
        "decomposed_tasks",
        "pending_requests",
        "clarification_count",
        "filter_relaxation_count",
        "recommend_retry_pending",
        "is_result_refinement",
        "refinement_sort",
        "last_recommended_goods_ids",
        "allowed_goods_ids",
        "is_pet_override",
        "pet_mismatch",
    )
    next_state: dict[str, Any] = {}
    for key in keys:
        if key == "filters":
            next_state[key] = normalize_search_filters(state.get(key))
        elif key == "exclusions":
            next_state[key] = normalize_search_exclusions(state.get(key))
        elif isinstance(state.get(key), list):
            next_state[key] = list(state.get(key) or [])
        elif isinstance(state.get(key), dict):
            next_state[key] = dict(state.get(key) or {})
        else:
            next_state[key] = state.get(key)
    return next_state


def extract_comparable_slots(state: dict[str, Any]) -> dict[str, Any]:
    pet_profile = dict(state.get("pet_profile") or {})
    filters = normalize_search_filters(state.get("filters"))
    exclusions = normalize_search_exclusions(state.get("exclusions"))
    slots: dict[str, Any] = dict(filters)

    pet_type = slots.get("pet_type") or species_to_korean(pet_profile.get("species"))
    if pet_type:
        slots["pet_type"] = pet_type
    if pet_profile.get("name"):
        slots["pet_name"] = pet_profile.get("name")
    if pet_profile.get("breed"):
        slots["breed"] = pet_profile.get("breed")
    if state.get("health_concerns"):
        slots["health_concerns"] = list(state.get("health_concerns") or [])
    if state.get("allergies"):
        slots["allergies"] = list(state.get("allergies") or [])
    if exclusions.get("brands"):
        slots["exclude_brands"] = list(exclusions.get("brands") or [])
    if state.get("refinement_sort"):
        slots["sort"] = _normalize_sort_value(state.get("refinement_sort"))
    return slots


def overlap_metrics(system_goods_ids: list[str], golden_goods_ids: list[str]) -> dict[str, Any]:
    system = {str(item) for item in system_goods_ids if item}
    golden = {str(item) for item in golden_goods_ids if item}
    intersection = sorted(system & golden)
    recall = (len(intersection) / len(golden) * 100.0) if golden else None
    precision = (len(intersection) / len(system) * 100.0) if system else None
    return {
        "intersection_goods_ids": intersection,
        "golden_count": len(golden),
        "system_count": len(system),
        "overlap_percent": round(recall, 2) if recall is not None else None,
        "precision_percent": round(precision, 2) if precision is not None else None,
    }


def build_report(results: list[dict[str, Any]]) -> dict[str, Any]:
    passed = sum(1 for result in results if result.get("deterministic", {}).get("passed"))
    failed = len(results) - passed
    return {
        "summary": {
            "total_cases": len(results),
            "passed_cases": passed,
            "failed_cases": failed,
        },
        "results": results,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Codex Evaluation Report",
        "",
        "## Summary",
        f"- total_cases: {report['summary']['total_cases']}",
        f"- passed_cases: {report['summary']['passed_cases']}",
        f"- failed_cases: {report['summary']['failed_cases']}",
        "",
        "## Cases",
        "| case_id | passed | route | search_query | reranked_overlap | error |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for result in report.get("results", []):
        deterministic = result.get("deterministic", {})
        actual = deterministic.get("actual", {})
        reranked_overlap = deterministic.get("reranked_overlap", {}).get("overlap_percent")
        lines.append(
            "| {case_id} | {passed} | {route} | {query} | {overlap} | {error} |".format(
                case_id=result.get("case_id"),
                passed="PASS" if deterministic.get("passed") else "FAIL",
                route=actual.get("route"),
                query=(actual.get("search_query") or "").replace("|", "/"),
                overlap=reranked_overlap,
                error=(result.get("error") or "").replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def _normalize_route(value: Any) -> str | list[str] | None:
    if value is None:
        return None
    if isinstance(value, list):
        nodes: list[str] = []
        for item in value:
            node = getattr(item, "node", None)
            nodes.append(str(node) if node is not None else str(item))
        return nodes
    return str(value)


def _patch_pet_sources(registered_pets: list[dict[str, Any]], pet_profiles_lookup: dict[str, dict[str, Any]]):
    def _get_user_pets(_user_id):
        return [dict(pet) for pet in registered_pets]

    def _get_pet_full_profile(pet_id):
        return dict(pet_profiles_lookup.get(str(pet_id), {}))

    def _fetch_pet_for_user(_user_id, target_pet_id=None, auto_latest=True):
        if target_pet_id:
            full = pet_profiles_lookup.get(str(target_pet_id))
            if not full:
                return None
            return _pet_row_from_full_profile(full)
        if auto_latest and registered_pets:
            active = next((pet for pet in registered_pets if pet.get("active")), registered_pets[-1])
            full = pet_profiles_lookup.get(str(active.get("pet_id")))
            if full:
                return _pet_row_from_full_profile(full)
        return None

    def _fetch_pet_preferences(pet_id):
        full = pet_profiles_lookup.get(str(pet_id), {})
        return {
            "health_concerns": list(full.get("health_concerns") or []),
            "allergies": list(full.get("allergies") or []),
            "food_preferences": list(full.get("food_preferences") or []),
        }

    stack = ExitStack()
    stack.enter_context(patch("final_ai.domain.intent.service.get_user_pets", side_effect=_get_user_pets))
    stack.enter_context(patch("final_ai.domain.intent.service.get_pet_full_profile", side_effect=_get_pet_full_profile))
    stack.enter_context(
        patch("final_ai.domain.recommendation.profile_service.fetch_pet_for_user", side_effect=_fetch_pet_for_user)
    )
    stack.enter_context(
        patch("final_ai.domain.recommendation.profile_service.fetch_pet_preferences", side_effect=_fetch_pet_preferences)
    )
    return stack


def _pet_row_from_full_profile(full: dict[str, Any]) -> dict[str, Any]:
    pet_profile = dict(full.get("pet_profile") or {})
    age = str(pet_profile.get("age") or "0세 0개월")
    age_years, age_months = _extract_age(age)
    return {
        "pet_id": full.get("pet_id"),
        "name": pet_profile.get("name"),
        "species": pet_profile.get("species"),
        "breed": pet_profile.get("breed"),
        "age_years": age_years,
        "age_months": age_months,
        "weight_kg": 0,
        "gender": pet_profile.get("gender") or "",
        "budget_range": None,
    }


def _extract_age(value: str) -> tuple[int, int]:
    import re

    years_match = re.search(r"(\d+)\s*세", value)
    months_match = re.search(r"(\d+)\s*개월", value)
    years = int(years_match.group(1)) if years_match else 0
    months = int(months_match.group(1)) if months_match else 0
    return years, months


def _has_recommend_intent(state: dict[str, Any]) -> bool:
    intents = state.get("intents") or []
    return "recommend" in intents or "popularity" in intents


def _goods_ids(products: Any) -> list[str]:
    goods_ids: list[str] = []
    for product in products or []:
        goods_id = product.get("goods_id")
        if goods_id is not None:
            goods_ids.append(str(goods_id))
    return goods_ids


def _compare_decomposed_tasks(actual: list[dict[str, Any]], expected: list[dict[str, Any]]) -> bool:
    if not expected:
        return actual == [] or actual is None
    if len(actual) != len(expected):
        return False
    for actual_task, expected_task in zip(actual, expected):
        for key, expected_value in expected_task.items():
            if not _loosely_equal(actual_task.get(key), expected_value):
                return False
    return True


def _loosely_equal(actual: Any, expected: Any) -> bool:
    if isinstance(expected, list):
        actual_list = list(actual or [])
        return sorted(_normalize(item) for item in actual_list) == sorted(_normalize(item) for item in expected)
    return _normalize(actual) == _normalize(expected)


def _normalize(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip().lower()


def _normalize_sort_value(value: Any) -> str | None:
    raw = _normalize(value)
    if raw in {"price_low", "price_asc", "lowest_price"}:
        return "price_asc"
    if raw in {"price_high", "price_desc"}:
        return "price_desc"
    return str(value) if value is not None else None


if __name__ == "__main__":
    raise SystemExit(main())
