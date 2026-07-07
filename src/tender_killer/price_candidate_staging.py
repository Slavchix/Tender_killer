from __future__ import annotations

from pathlib import Path
from typing import Any

from tender_killer.price_candidate_normalization import normalize_price_candidate
from tender_killer.price_candidate_profiles import ensure_profiles_with_item_fallback
from tender_killer.price_candidate_quality import evaluate_price_candidate_quality
from tender_killer.price_candidate_sources import profile_candidate_sources
from tender_killer.storage import TenderStore


def stage_tender_price_candidates(
    database_path: str | Path,
    source: str,
    external_id: str,
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = ensure_profiles_with_item_fallback(database_path, source, external_id)
    staged_count = 0
    ready_count = 0
    review_count = 0
    blocked_count = 0
    skipped_no_candidate_source_count = 0
    positions: list[dict[str, Any]] = []

    for profile in profiles:
        position_index = int(profile.get("position_index") or 0)
        candidates = profile_candidate_sources(profile)
        if not candidates:
            skipped_no_candidate_source_count += 1
            positions.append({"position_index": position_index, "staged_count": 0, "status": "no_candidate_source"})
            continue

        normalized_candidates = [normalize_price_candidate(profile, candidate) for candidate in candidates]
        saved_candidates = store.upsert_price_candidates(
            source,
            external_id,
            position_index,
            normalized_candidates,
            origin="auto_stage",
        )
        staged_count += len(saved_candidates)

        status_counts = {"ready": 0, "review": 0, "blocked": 0}
        for candidate in saved_candidates:
            status = str(evaluate_price_candidate_quality(profile, candidate).get("quality_status") or "review")
            if status in status_counts:
                status_counts[status] += 1
        ready_count += status_counts["ready"]
        review_count += status_counts["review"]
        blocked_count += status_counts["blocked"]
        positions.append(
            {
                "position_index": position_index,
                "staged_count": len(saved_candidates),
                "ready_count": status_counts["ready"],
                "review_count": status_counts["review"],
                "blocked_count": status_counts["blocked"],
            }
        )

    return {
        "ok": True,
        "total_profiles": len(profiles),
        "profiles_with_candidates_count": len(profiles) - skipped_no_candidate_source_count,
        "staged_count": staged_count,
        "ready_count": ready_count,
        "review_count": review_count,
        "blocked_count": blocked_count,
        "skipped_no_candidate_source_count": skipped_no_candidate_source_count,
        "positions": positions,
    }
