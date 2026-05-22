from __future__ import annotations

from pathlib import Path
from typing import Any

from tender_killer.storage import TenderStore


SUPPLIER_OPTION_TEXT_FIELDS = ("name", "url", "availability", "status", "note")
SUPPLIER_OPTION_NUMBER_FIELDS = ("unit_price",)


def add_profile_supplier_option(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    data: dict[str, Any],
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = store.get_product_profiles(source, external_id)
    if not profiles:
        raise KeyError(f"Product profiles for {source}/{external_id} not found.")

    target = None
    for profile in profiles:
        if int(profile.get("position_index") or 0) == position_index:
            target = profile
            break
    if target is None:
        raise KeyError(f"Product profile position {position_index} not found.")

    option = _supplier_option(data)
    if not option:
        raise ValueError("Supplier option is empty.")

    raw_payload = dict(target.get("raw_payload") or {})
    supplier_options = _supplier_options(raw_payload.get("supplier_options"))
    supplier_options.append(option)
    raw_payload["supplier_options"] = supplier_options
    target["raw_payload"] = raw_payload

    store.upsert_product_profiles(source, external_id, profiles)
    return {"ok": True}


def _supplier_option(data: dict[str, Any]) -> dict[str, Any]:
    option: dict[str, Any] = {}
    for field in SUPPLIER_OPTION_TEXT_FIELDS:
        value = _text(data.get(field))
        if value:
            option[field] = value
    for field in SUPPLIER_OPTION_NUMBER_FIELDS:
        number = _number(data.get(field))
        if number is not None:
            option[field] = number
    has_candidate_signal = any(option.get(field) for field in ("name", "url", "note")) or "unit_price" in option
    if not has_candidate_signal:
        return {}
    return option


def _supplier_options(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


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
