from __future__ import annotations

from pathlib import Path
from typing import Any

from tender_killer.storage import TenderStore
from tender_killer.supplier_catalog_presets import normalize_supplier_catalog_preset_ids


def update_profile_supplier_catalog_presets(
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

    target = _find_profile(profiles, position_index)
    if target is None:
        raise KeyError(f"Product profile position {position_index} not found.")

    preset_ids = normalize_supplier_catalog_preset_ids(data.get("preset_ids"))
    raw_payload = dict(target.get("raw_payload") or {})
    raw_payload.pop("supplier_search", None)
    if preset_ids is None:
        raw_payload.pop("supplier_catalog_preset_ids", None)
    else:
        raw_payload["supplier_catalog_preset_ids"] = preset_ids
    target["raw_payload"] = raw_payload

    store.upsert_product_profiles(source, external_id, profiles)
    return {
        "ok": True,
        "position_index": position_index,
        "preset_ids": preset_ids,
    }


def _find_profile(profiles: list[dict[str, Any]], position_index: int) -> dict[str, Any] | None:
    for profile in profiles:
        if int(profile.get("position_index") or 0) == position_index:
            return profile
    return None
