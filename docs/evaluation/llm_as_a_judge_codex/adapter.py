from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class EvalCase:
    case_id: str
    description: str
    input: dict[str, Any]
    expected_output: dict[str, Any]


def load_eval_cases(path: str | Path) -> list[EvalCase]:
    rows: list[EvalCase] = []
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        payload = json.loads(line)
        rows.append(
            EvalCase(
                case_id=str(payload.get("id")),
                description=str(payload.get("description") or ""),
                input=dict(payload.get("input") or {}),
                expected_output=dict(payload.get("expected_output") or {}),
            )
        )
    return rows


def species_to_profile_value(value: Any) -> str | None:
    if value is None:
        return None
    raw = str(value).strip()
    lowered = raw.lower()
    if lowered in {"dog", "강아지"}:
        return "dog"
    if lowered in {"cat", "고양이"}:
        return "cat"
    return raw or None


def species_to_korean(value: Any) -> str | None:
    if value is None:
        return None
    raw = str(value).strip()
    lowered = raw.lower()
    if lowered in {"dog", "강아지"}:
        return "강아지"
    if lowered in {"cat", "고양이"}:
        return "고양이"
    return raw or None


def build_registered_pets(current_pet_profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pets: list[dict[str, Any]] = []
    for pet in current_pet_profiles or []:
        pets.append(
            {
                "pet_id": str(pet.get("pet_id") or ""),
                "name": pet.get("name"),
                "species": species_to_profile_value(
                    pet.get("species_en") or pet.get("species")
                ),
                "breed": pet.get("breed"),
                "age": pet.get("age")
                or _build_age_text(pet.get("age_years"), pet.get("age_months")),
                "active": bool(pet.get("active", False)),
            }
        )
    return pets


def build_pet_profiles_lookup(current_pet_profiles: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for pet in current_pet_profiles or []:
        pet_id = str(pet.get("pet_id") or "")
        if not pet_id:
            continue
        lookup[pet_id] = {
            "pet_id": pet_id,
            "pet_profile": {
                "name": pet.get("name"),
                "species": species_to_profile_value(
                    pet.get("species_en") or pet.get("species")
                ),
                "breed": pet.get("breed"),
                "age": pet.get("age")
                or _build_age_text(pet.get("age_years"), pet.get("age_months")),
            },
            "health_concerns": list(pet.get("health_concerns") or []),
            "allergies": list(pet.get("allergies") or []),
            "food_preferences": list(pet.get("food_preferences") or []),
        }
    return lookup


def choose_active_pet(current_pet_profiles: list[dict[str, Any]]) -> dict[str, Any] | None:
    active = [pet for pet in current_pet_profiles or [] if pet.get("active")]
    if len(active) == 1:
        return dict(active[0])
    if len(current_pet_profiles or []) == 1:
        return dict((current_pet_profiles or [])[0])
    return None


def build_seed_dialog_state(
    prior_dialog_state: dict[str, Any] | None,
    *,
    active_pet: dict[str, Any] | None,
) -> dict[str, Any]:
    dialog_state = dict(prior_dialog_state or {})
    if active_pet and not dialog_state.get("target_pet_id"):
        dialog_state["target_pet_id"] = str(active_pet.get("pet_id") or "")
    if active_pet and not dialog_state.get("pet_profile"):
        dialog_state["pet_profile"] = {
            "name": active_pet.get("name"),
            "species": species_to_profile_value(
                active_pet.get("species_en") or active_pet.get("species")
            ),
            "breed": active_pet.get("breed"),
            "age": active_pet.get("age")
            or _build_age_text(active_pet.get("age_years"), active_pet.get("age_months")),
        }
    if active_pet and not dialog_state.get("health_concerns"):
        dialog_state["health_concerns"] = list(active_pet.get("health_concerns") or [])
    if active_pet and not dialog_state.get("allergies"):
        dialog_state["allergies"] = list(active_pet.get("allergies") or [])
    if active_pet and not dialog_state.get("food_preferences"):
        dialog_state["food_preferences"] = list(active_pet.get("food_preferences") or [])
    return dialog_state


def normalize_expected_filters(expected_output: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(expected_output.get("filters") or {})
    pet_profile = dict(expected_output.get("pet_profile") or {})
    if "pet_type" not in normalized:
        pet_type = (
            pet_profile.get("pet_type")
            or species_to_korean(pet_profile.get("species"))
        )
        if pet_type:
            normalized["pet_type"] = pet_type
    if "pet_name" not in normalized and pet_profile.get("pet_name"):
        normalized["pet_name"] = pet_profile["pet_name"]
    if "breed" not in normalized and pet_profile.get("breed"):
        normalized["breed"] = pet_profile["breed"]
    if "health_concerns" not in normalized and pet_profile.get("health_concerns"):
        normalized["health_concerns"] = list(pet_profile.get("health_concerns") or [])
    return normalized


def extract_golden_goods_ids(expected_output: dict[str, Any]) -> list[str]:
    goods_ids: list[str] = []
    for product in expected_output.get("golden_products") or []:
        goods_id = product.get("goods_id")
        if goods_id:
            goods_ids.append(str(goods_id))
    return goods_ids


def _build_age_text(age_years: Any, age_months: Any) -> str | None:
    if age_years is None and age_months is None:
        return None
    years = 0 if age_years is None else int(age_years)
    months = 0 if age_months is None else int(age_months)
    return f"{years}세 {months}개월"
