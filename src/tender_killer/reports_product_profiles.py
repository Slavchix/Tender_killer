from __future__ import annotations

from typing import Any

from tender_killer.product_profile_service import product_profile_summary


REPORT_PRODUCT_PROFILE_SUMMARY_KEYS = ("total", "ready", "needs_review", "matched", "priced", "rejected")


def report_product_profile_summary(tender: dict[str, Any], product_profiles: list[Any]) -> dict[str, int]:
    summary = tender.get("product_profile_summary")
    if isinstance(summary, dict):
        return {key: _int_value(summary.get(key)) for key in REPORT_PRODUCT_PROFILE_SUMMARY_KEYS}

    profile_dicts = [profile for profile in product_profiles if isinstance(profile, dict)]
    counts = product_profile_summary(profile_dicts)
    report_summary = {key: _int_value(counts.get(key)) for key in REPORT_PRODUCT_PROFILE_SUMMARY_KEYS}
    report_summary["total"] = len(product_profiles)
    return report_summary


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
