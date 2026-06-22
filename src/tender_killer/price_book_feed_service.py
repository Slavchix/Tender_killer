from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from tender_killer.price_candidate_service import normalize_price_candidate
from tender_killer.product_profile_service import ensure_product_profiles
from tender_killer.storage import TenderStore


TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)
STOP_WORDS = {
    "and",
    "for",
    "the",
    "item",
    "product",
    "goods",
    "товар",
    "товары",
    "для",
}


def stage_tender_price_book_feed(
    database_path: str | Path,
    source: str,
    external_id: str,
    rows: list[dict[str, Any]],
    *,
    feed_name: str = "price book",
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = ensure_product_profiles(database_path, source, external_id)
    profiles_by_position = {
        int(profile.get("position_index") or 0): profile
        for profile in profiles
        if int(profile.get("position_index") or 0) > 0
    }

    staged_count = 0
    matched_count = 0
    skipped_count = 0
    position_counts: dict[int, int] = {}

    for row_index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            skipped_count += 1
            continue
        match = _match_feed_row(row, profiles, profiles_by_position)
        if match is None:
            skipped_count += 1
            continue
        profile, match_reason = match
        candidate = _candidate_from_feed_row(row, profile, feed_name=feed_name, row_index=row_index, match_reason=match_reason)
        if not candidate:
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
            skipped_count += 1
            continue
        matched_count += 1
        staged_count += len(saved)
        position = int(profile["position_index"])
        position_counts[position] = position_counts.get(position, 0) + len(saved)

    return {
        "ok": True,
        "feed_name": feed_name,
        "rows_count": len(rows),
        "matched_count": matched_count,
        "staged_count": staged_count,
        "skipped_count": skipped_count,
        "positions": [
            {"position_index": position, "staged_count": count}
            for position, count in sorted(position_counts.items())
        ],
    }


def _match_feed_row(
    row: dict[str, Any],
    profiles: list[dict[str, Any]],
    profiles_by_position: dict[int, dict[str, Any]],
) -> tuple[dict[str, Any], str] | None:
    position = _integer(row.get("position_index") or row.get("position") or row.get("pos"))
    if position and position in profiles_by_position:
        return profiles_by_position[position], "position_index"

    row_tokens = _tokens(
        row.get("product_name"),
        row.get("name"),
        row.get("item_name"),
        row.get("description"),
        row.get("sku"),
        row.get("article"),
    )
    if not row_tokens:
        return None

    best_profile: dict[str, Any] | None = None
    best_score = 0
    for profile in profiles:
        profile_tokens = _tokens(profile.get("product_name"), profile.get("normalized_name"), profile.get("details"))
        if not profile_tokens:
            continue
        score = len(row_tokens & profile_tokens)
        if score > best_score:
            best_score = score
            best_profile = profile

    if best_profile is None:
        return None
    threshold = 2 if len(row_tokens) >= 2 else 1
    return (best_profile, "name_match") if best_score >= threshold else None


def _candidate_from_feed_row(
    row: dict[str, Any],
    profile: dict[str, Any],
    *,
    feed_name: str,
    row_index: int,
    match_reason: str,
) -> dict[str, Any]:
    unit_price = _number(row.get("unit_price") or row.get("price"))
    if unit_price is None or unit_price <= 0:
        return {}
    supplier_name = _text(row.get("supplier_name") or row.get("supplier") or row.get("vendor"))
    provider = _text(row.get("provider") or supplier_name or feed_name)
    product_name = _text(row.get("product_name") or row.get("name") or row.get("item_name")) or _text(profile.get("product_name"))
    raw_payload = {
        **row,
        "feed_name": feed_name,
        "row_index": row_index,
        "source_kind": "price_book_feed",
    }
    candidate = {
        "provider": provider,
        "supplier_name": supplier_name,
        "product_name": product_name,
        "name": product_name,
        "source_url": row.get("source_url") or row.get("url"),
        "source_query": row.get("source_query") or row.get("product_name") or row.get("name") or profile.get("product_name"),
        "source_kind": "price_book_feed",
        "unit_price": unit_price,
        "currency": row.get("currency") or "RUB",
        "vat_mode": row.get("vat_mode"),
        "vat_rate_percent": row.get("vat_rate_percent"),
        "availability": row.get("availability"),
        "delivery_note": row.get("delivery_note"),
        "delivery_cost": row.get("delivery_cost"),
        "unit": row.get("unit") or row.get("uom") or profile.get("unit"),
        "pack_quantity": row.get("pack_quantity") or row.get("quantity_per_pack"),
        "stock_quantity": row.get("stock_quantity") or row.get("stock"),
        "preorder_quantity": row.get("preorder_quantity"),
        "minimum_order_quantity": row.get("minimum_order_quantity") or row.get("min_order_quantity"),
        "minimum_order_amount": row.get("minimum_order_amount") or row.get("min_order_amount"),
        "price_breaks": row.get("price_breaks"),
        "confidence": row.get("confidence") or "high",
        "confidence_reasons": ["price_book_feed", match_reason],
        "match_reasons": ["price_book_feed", match_reason],
        "feed_name": feed_name,
        "sku": row.get("sku") or row.get("article"),
        "valid_until": row.get("valid_until"),
        "raw_payload": raw_payload,
    }
    return {key: value for key, value in candidate.items() if value not in (None, "")}


def _tokens(*values: Any) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        for token in TOKEN_RE.findall(str(value or "").casefold()):
            if len(token) > 1 and token not in STOP_WORDS:
                tokens.add(token)
    return tokens


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


def _integer(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
