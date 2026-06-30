from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from tender_killer.product_profile_service import ensure_product_profiles


def ensure_profiles_with_item_fallback(
    database_path: str | Path,
    source: str,
    external_id: str,
) -> list[dict[str, Any]]:
    profiles = ensure_product_profiles(database_path, source, external_id)
    item_fallbacks = _tender_items_by_position(database_path, source, external_id)
    if not item_fallbacks:
        return profiles
    return [
        _profile_with_item_fallback(profile, item_fallbacks.get(int(profile.get("position_index") or 0)))
        for profile in profiles
    ]


def find_profile(profiles: list[dict[str, Any]], position_index: int) -> dict[str, Any]:
    for profile in profiles:
        if int(profile.get("position_index") or 0) == int(position_index):
            return profile
    raise KeyError(f"Product profile position {position_index} not found.")


def _tender_items_by_position(
    database_path: str | Path,
    source: str,
    external_id: str,
) -> dict[int, dict[str, Any]]:
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT position_index, quantity, unit
            FROM tender_items
            WHERE source = ? AND external_id = ?
            ORDER BY position_index
            """,
            (source, external_id),
        ).fetchall()
    return {
        int(row["position_index"]): dict(row)
        for row in rows
        if int(row["position_index"] or 0) > 0
    }


def _profile_with_item_fallback(profile: dict[str, Any], item: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(item, dict):
        return profile
    enriched = dict(profile)
    for key in ("quantity", "unit"):
        if enriched.get(key) in (None, "") and item.get(key) not in (None, ""):
            enriched[key] = item.get(key)
    return enriched
