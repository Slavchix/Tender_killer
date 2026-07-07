from __future__ import annotations

from pathlib import Path
from typing import Any

from tender_killer.product_profile import build_product_profiles
from tender_killer.storage import TenderStore


PRODUCT_PROFILE_SUMMARY_STATUSES = ("draft", "needs_review", "ready", "searching", "matched", "priced", "rejected")
PRESERVED_RAW_PAYLOAD_KEYS = (
    "economics",
    "economics_assumptions",
    "economics_auto",
    "economics_acceptance",
    "economics_price_source",
    "selected_supplier_option",
    "supplier_options",
    "supplier_search",
    "supplier_catalog_preset_ids",
    "supplier_catalogs",
    "supplier_discovery",
)
PRESERVED_PROFILE_STATUSES = {"searching", "matched", "priced", "rejected"}


def product_profile_summary(profiles: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"total": len(profiles), **{status: 0 for status in PRODUCT_PROFILE_SUMMARY_STATUSES}}
    for profile in profiles:
        status = str(profile.get("profile_status") or "")
        if status in PRODUCT_PROFILE_SUMMARY_STATUSES:
            summary[status] += 1
    return summary


def build_profiles(tender_payload: dict[str, Any]) -> list[dict[str, Any]]:
    return build_product_profiles(tender_payload)


def ensure_product_profiles(
    database_path: str | Path,
    source: str,
    external_id: str,
    tender_payload: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = store.get_product_profiles(source, external_id)
    if profiles:
        return profiles

    if tender_payload is None:
        from tender_killer.tender_detail_service import get_tender_payload

        tender_payload = get_tender_payload(database_path, source, external_id, include_product_profiles=False)
    result = rebuild_product_profiles(database_path, source, external_id, tender_payload)
    return result["product_profiles"]


def rebuild_product_profiles(
    database_path: str | Path,
    source: str,
    external_id: str,
    tender_payload: dict[str, Any],
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    existing_profiles = {
        int(profile.get("position_index") or 0): profile
        for profile in store.get_product_profiles(source, external_id)
    }
    profiles = [
        _merge_saved_profile_state(profile, existing_profiles.get(int(profile.get("position_index") or 0)))
        for profile in build_profiles(tender_payload)
    ]
    store.upsert_product_profiles(source, external_id, profiles)
    saved_profiles = store.get_product_profiles(source, external_id)
    return {
        "ok": True,
        "summary": product_profile_summary(saved_profiles),
        "product_profiles": saved_profiles,
    }


def _merge_saved_profile_state(profile: dict[str, Any], saved_profile: dict[str, Any] | None) -> dict[str, Any]:
    if not saved_profile:
        return profile
    saved_raw = saved_profile.get("raw_payload") if isinstance(saved_profile.get("raw_payload"), dict) else {}
    preserved_raw = {
        key: saved_raw[key]
        for key in PRESERVED_RAW_PAYLOAD_KEYS
        if key in saved_raw
    }
    saved_status = str(saved_profile.get("profile_status") or "")
    if not preserved_raw and saved_status not in PRESERVED_PROFILE_STATUSES:
        return profile

    merged = dict(profile)
    raw_payload = dict(merged.get("raw_payload") or {})
    raw_payload.update(preserved_raw)
    merged["raw_payload"] = raw_payload
    if saved_status in PRESERVED_PROFILE_STATUSES:
        merged["profile_status"] = saved_status
    return merged
