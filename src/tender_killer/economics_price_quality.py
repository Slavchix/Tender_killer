from __future__ import annotations

from typing import Any

from .economics_costing import _round_percent


def _price_quality_summary(profiles: list[dict[str, Any]], items: list[dict[str, Any]]) -> dict[str, Any]:
    positions_total = len(profiles)
    positions_priced = sum(1 for item in items if item.get("total_cost") is not None)
    candidates_total = 0
    candidates_ready = 0
    candidates_review = 0
    candidates_blocked = 0
    candidates_unknown = 0
    candidates_confirmed = 0
    candidates_auto_eligible = 0
    review_flags: dict[str, dict[str, Any]] = {}
    block_flags: dict[str, dict[str, Any]] = {}

    for profile in profiles:
        candidates = profile.get("price_candidates") if isinstance(profile.get("price_candidates"), list) else []
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            candidates_total += 1
            review_status = str(candidate.get("review_status") or "").strip().casefold()
            if review_status == "confirmed":
                candidates_confirmed += 1
                candidates_ready += 1
                if candidate.get("auto_eligible") is True:
                    candidates_auto_eligible += 1
                continue
            status = str(candidate.get("quality_status") or "").strip().casefold()
            if status == "ready":
                candidates_ready += 1
            elif status == "review":
                candidates_review += 1
            elif status == "blocked":
                candidates_blocked += 1
            else:
                candidates_unknown += 1
            if candidate.get("auto_eligible") is True:
                candidates_auto_eligible += 1
            for flag in candidate.get("quality_flags") or []:
                if not isinstance(flag, dict) or not flag.get("id"):
                    continue
                severity = str(flag.get("severity") or "").strip().casefold()
                if severity == "review":
                    _count_price_quality_flag(review_flags, flag)
                elif severity == "block":
                    _count_price_quality_flag(block_flags, flag)

    positions_missing = max(0, positions_total - positions_priced)
    return {
        "positions_total": positions_total,
        "positions_priced": positions_priced,
        "positions_missing": positions_missing,
        "price_coverage_percent": _round_percent((positions_priced / positions_total) * 100) if positions_total else 0.0,
        "candidates_total": candidates_total,
        "candidates_ready": candidates_ready,
        "candidates_review": candidates_review,
        "candidates_blocked": candidates_blocked,
        "candidates_unknown": candidates_unknown,
        "candidates_confirmed": candidates_confirmed,
        "candidates_auto_eligible": candidates_auto_eligible,
        "review_flags": _price_quality_flags(review_flags),
        "block_flags": _price_quality_flags(block_flags),
        "summary": _price_quality_summary_text(
            positions_priced,
            positions_total,
            candidates_ready,
            candidates_review,
            candidates_blocked,
        ),
    }


def _count_price_quality_flag(target: dict[str, dict[str, Any]], flag: dict[str, Any]) -> None:
    flag_id = str(flag.get("id") or "").strip()
    if not flag_id:
        return
    item = target.setdefault(
        flag_id,
        {"id": flag_id, "label": str(flag.get("label") or flag_id), "count": 0},
    )
    item["count"] += 1


def _price_quality_flags(flags: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"id": item["id"], "label": item["label"], "count": item["count"]}
        for item in sorted(flags.values(), key=lambda value: (-int(value["count"]), str(value["id"])))
    ]


def _price_quality_summary_text(
    positions_priced: int,
    positions_total: int,
    candidates_ready: int,
    candidates_review: int,
    candidates_blocked: int,
) -> str:
    return (
        f"Цены есть по {positions_priced}/{positions_total} позиций. "
        f"Кандидаты: {candidates_ready} готово, {candidates_review} проверить, {candidates_blocked} блок."
    )
