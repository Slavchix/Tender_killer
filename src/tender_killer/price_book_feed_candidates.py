from __future__ import annotations

from typing import Any


def candidate_from_feed_row(
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
