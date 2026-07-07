from __future__ import annotations

from pathlib import Path
from typing import Any

from tender_killer.product_profile_service import ensure_product_profiles
from tender_killer.supplier_provider_policy import SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT


def tender_price_discovery_policy_for_tender(
    database_path: str | Path,
    source: str,
    external_id: str,
) -> dict[str, Any]:
    profiles = ensure_product_profiles(database_path, source, external_id)
    searchable_profiles = [profile for profile in profiles if int(profile.get("position_index") or 0) > 0]
    manual_required = _manual_required_tender_discovery_result(profiles, searchable_profiles)
    if manual_required is not None:
        return manual_required
    return {
        "ok": True,
        "status": "active_discovery_allowed",
        "reason": "small_tender_review_only",
        "total_profiles": len(searchable_profiles),
        "max_active_positions": SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT,
    }


def _manual_required_tender_discovery_result(
    profiles: list[dict[str, Any]],
    searchable_profiles: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if len(searchable_profiles) <= SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT:
        return None
    return {
        "ok": False,
        "status": "manual_required",
        "reason": "large_tender_manual_required",
        "message": "Active supplier price discovery is limited to small tenders. Use quick links/manual URL/feed.",
        "total_profiles": len(searchable_profiles),
        "prepared_count": 0,
        "searched_count": 0,
        "limited_count": len(searchable_profiles),
        "partial": True,
        "staged_count": 0,
        "ready_count": 0,
        "review_count": 0,
        "blocked_count": 0,
        "no_candidates_count": 0,
        "error_count": 0,
        "positions": [
            {
                "position_index": int(profile.get("position_index") or 0),
                "status": "manual_required",
                "staged_count": 0,
            }
            for profile in searchable_profiles
        ],
        "diagnostics_by_provider": [],
    }
