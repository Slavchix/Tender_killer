from __future__ import annotations

from pathlib import Path
from typing import Any

from tender_killer.product_profile import build_product_profiles
from tender_killer.storage import TenderStore


PRODUCT_PROFILE_SUMMARY_STATUSES = ("draft", "needs_review", "ready", "searching", "matched", "priced", "rejected")


def product_profile_summary(profiles: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"total": len(profiles), **{status: 0 for status in PRODUCT_PROFILE_SUMMARY_STATUSES}}
    for profile in profiles:
        status = str(profile.get("profile_status") or "")
        if status in PRODUCT_PROFILE_SUMMARY_STATUSES:
            summary[status] += 1
    return summary


def build_profiles(tender_payload: dict[str, Any]) -> list[dict[str, Any]]:
    return build_product_profiles(tender_payload)


def rebuild_product_profiles(
    database_path: str | Path,
    source: str,
    external_id: str,
    tender_payload: dict[str, Any],
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = build_profiles(tender_payload)
    store.upsert_product_profiles(source, external_id, profiles)
    saved_profiles = store.get_product_profiles(source, external_id)
    return {
        "ok": True,
        "summary": product_profile_summary(saved_profiles),
        "product_profiles": saved_profiles,
    }
