from __future__ import annotations

import re
from typing import Any


TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)
STAGE_MODES = {"all", "confident", "review", "errors"}
STOP_WORDS = {
    "and",
    "for",
    "the",
    "item",
    "product",
    "goods",
    "товар",
    "товары",
    "для",
}


def assess_feed_row(
    row_index: int,
    row: Any,
    profiles: list[dict[str, Any]],
    profiles_by_position: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(row, dict):
        return _quality_row(row_index, "error", "invalid_row")
    unit_price = _number(row.get("unit_price") or row.get("price"))
    if unit_price is None or unit_price <= 0:
        return _quality_row(row_index, "error", "missing_unit_price", row=row)
    match = _match_feed_row(row, profiles, profiles_by_position)
    if match is None:
        return _quality_row(row_index, "review", "no_matching_position", row=row)
    profile, match_reason = match
    status = "exact_position" if match_reason == "position_index" else "name_match"
    return _quality_row(row_index, status, match_reason, row=row, profile=profile, can_stage=True)


def quality_report(rows: list[dict[str, Any]], stage_mode: str) -> dict[str, Any]:
    public_rows = [_public_quality_row(row) for row in rows]
    summary = {
        "rows_count": len(rows),
        "exact_position_count": sum(1 for row in rows if row["status"] == "exact_position"),
        "name_match_count": sum(1 for row in rows if row["status"] == "name_match"),
        "review_count": sum(1 for row in rows if row["status"] == "review"),
        "error_count": sum(1 for row in rows if row["status"] == "error"),
        "stageable_count": sum(1 for row in rows if row.get("can_stage")),
        "selected_count": sum(1 for row in rows if row.get("can_stage") and stage_mode_allows(stage_mode, row)),
    }
    return {
        "stage_mode": stage_mode,
        "summary": summary,
        "rows": public_rows,
    }


def stage_mode(value: Any) -> str:
    text = str(value or "all").strip().casefold()
    return text if text in STAGE_MODES else "all"


def stage_mode_allows(stage_mode: str, row: dict[str, Any]) -> bool:
    if stage_mode == "errors":
        return False
    if stage_mode == "confident":
        return row.get("status") == "exact_position"
    if stage_mode == "review":
        return row.get("status") == "name_match"
    return row.get("status") in {"exact_position", "name_match"}


def _quality_row(
    row_index: int,
    status: str,
    reason: str,
    *,
    row: dict[str, Any] | None = None,
    profile: dict[str, Any] | None = None,
    can_stage: bool = False,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "row_index": row_index,
        "status": status,
        "reason": reason,
        "can_stage": can_stage,
        "stage_action": "pending",
    }
    if row:
        result["product_name"] = _text(row.get("product_name") or row.get("name") or row.get("item_name") or row.get("description"))
        result["unit_price"] = _number(row.get("unit_price") or row.get("price"))
        result["supplier_name"] = _text(row.get("supplier_name") or row.get("supplier") or row.get("vendor"))
    if profile:
        result["_profile"] = profile
        result["position_index"] = int(profile.get("position_index") or 0)
        result["matched_product_name"] = _text(profile.get("product_name"))
    return result


def _public_quality_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "_profile"}


def _match_feed_row(
    row: dict[str, Any],
    profiles: list[dict[str, Any]],
    profiles_by_position: dict[int, dict[str, Any]],
) -> tuple[dict[str, Any], str] | None:
    position = _integer(row.get("position_index") or row.get("position") or row.get("pos"))
    if position and position in profiles_by_position:
        return profiles_by_position[position], "position_index"

    row_tokens = _tokens(
        row.get("product_name"),
        row.get("name"),
        row.get("item_name"),
        row.get("description"),
        row.get("sku"),
        row.get("article"),
    )
    if not row_tokens:
        return None

    best_profile: dict[str, Any] | None = None
    best_score = 0
    for profile in profiles:
        profile_tokens = _tokens(profile.get("product_name"), profile.get("normalized_name"), profile.get("details"))
        if not profile_tokens:
            continue
        score = len(row_tokens & profile_tokens)
        if score > best_score:
            best_score = score
            best_profile = profile

    if best_profile is None:
        return None
    threshold = 2 if len(row_tokens) >= 2 else 1
    return (best_profile, "name_match") if best_score >= threshold else None


def _tokens(*values: Any) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        for token in TOKEN_RE.findall(str(value or "").casefold()):
            if len(token) > 1 and token not in STOP_WORDS:
                tokens.add(token)
    return tokens


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _integer(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
