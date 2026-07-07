from __future__ import annotations

from pathlib import Path
from typing import Any

from tender_killer.price_book_feed_candidates import candidate_from_feed_row
from tender_killer.price_book_feed_io import decode_base64_file
from tender_killer.price_book_feed_io import parse_price_book_feed_file
from tender_killer.price_book_feed_matching import assess_feed_row
from tender_killer.price_book_feed_matching import quality_report
from tender_killer.price_book_feed_matching import stage_mode as normalize_stage_mode
from tender_killer.price_book_feed_matching import stage_mode_allows
from tender_killer.price_candidate_normalization import normalize_price_candidate
from tender_killer.product_profile_service import ensure_product_profiles
from tender_killer.storage import TenderStore


def stage_tender_price_book_feed(
    database_path: str | Path,
    source: str,
    external_id: str,
    rows: list[dict[str, Any]],
    *,
    feed_name: str = "price book",
    stage_mode: str = "all",
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = ensure_product_profiles(database_path, source, external_id)
    stage_mode = normalize_stage_mode(stage_mode)
    profiles_by_position = {
        int(profile.get("position_index") or 0): profile
        for profile in profiles
        if int(profile.get("position_index") or 0) > 0
    }

    staged_count = 0
    matched_count = 0
    skipped_count = 0
    position_counts: dict[int, int] = {}
    quality_rows: list[dict[str, Any]] = []

    for row_index, row in enumerate(rows, start=1):
        assessment = assess_feed_row(row_index, row, profiles, profiles_by_position)
        quality_rows.append(assessment)
        if not assessment["can_stage"]:
            assessment["stage_action"] = "error" if assessment["status"] == "error" else "left_for_review"
            skipped_count += 1
            continue
        if not stage_mode_allows(stage_mode, assessment):
            assessment["stage_action"] = "left_for_review"
            skipped_count += 1
            continue

        profile = assessment["_profile"]
        match_reason = assessment["reason"]
        candidate = candidate_from_feed_row(row, profile, feed_name=feed_name, row_index=row_index, match_reason=match_reason)
        if not candidate:
            assessment["status"] = "error"
            assessment["reason"] = "missing_unit_price"
            assessment["can_stage"] = False
            assessment["stage_action"] = "error"
            skipped_count += 1
            continue
        normalized = normalize_price_candidate(profile, candidate)
        saved = store.upsert_price_candidates(
            source,
            external_id,
            int(profile["position_index"]),
            [normalized],
            origin="price_book_feed",
        )
        if not saved:
            assessment["stage_action"] = "error"
            skipped_count += 1
            continue
        assessment["stage_action"] = "staged"
        matched_count += 1
        staged_count += len(saved)
        position = int(profile["position_index"])
        position_counts[position] = position_counts.get(position, 0) + len(saved)

    return {
        "ok": True,
        "feed_name": feed_name,
        "stage_mode": stage_mode,
        "rows_count": len(rows),
        "matched_count": matched_count,
        "staged_count": staged_count,
        "skipped_count": skipped_count,
        "quality_report": quality_report(quality_rows, stage_mode),
        "positions": [
            {"position_index": position, "staged_count": count}
            for position, count in sorted(position_counts.items())
        ],
    }


def stage_tender_price_book_feed_file(
    database_path: str | Path,
    source: str,
    external_id: str,
    *,
    file_name: str,
    content_base64: str,
    feed_name: str = "price book",
    stage_mode: str = "all",
) -> dict[str, Any]:
    file_bytes = decode_base64_file(content_base64)
    rows, file_import = parse_price_book_feed_file(file_name, file_bytes)
    result = stage_tender_price_book_feed(
        database_path,
        source,
        external_id,
        rows,
        feed_name=feed_name,
        stage_mode=stage_mode,
    )
    result["file_import"] = file_import
    return result


__all__ = [
    "parse_price_book_feed_file",
    "stage_tender_price_book_feed",
    "stage_tender_price_book_feed_file",
]
