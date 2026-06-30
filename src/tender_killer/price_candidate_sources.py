from __future__ import annotations

from typing import Any

from tender_killer.price_candidate_common import (
    MIN_ORDER_AMOUNT_FIELDS,
    MIN_ORDER_QUANTITY_FIELDS,
    PACK_QUANTITY_FIELDS,
    SUPPLIER_PREORDER_FIELDS,
    SUPPLIER_STOCK_FIELDS,
    first_number as _first_number,
    number_or_none as _number,
    price_breaks as _price_breaks,
    string_list as _string_list,
)


def profile_candidate_sources(profile: dict[str, Any]) -> list[dict[str, Any]]:
    raw_payload = profile.get("raw_payload") if isinstance(profile.get("raw_payload"), dict) else {}
    candidates: list[dict[str, Any]] = []
    for option in _supplier_options(raw_payload.get("supplier_options")):
        candidate = _candidate_from_supplier_source(profile, option, source_kind="supplier_options")
        if candidate:
            candidates.append(candidate)

    discovery = raw_payload.get("supplier_discovery") if isinstance(raw_payload.get("supplier_discovery"), dict) else {}
    discovery_candidates = discovery.get("candidates") if isinstance(discovery.get("candidates"), list) else []
    for item in discovery_candidates:
        if not isinstance(item, dict):
            continue
        candidate = _candidate_from_supplier_source(profile, item, source_kind="supplier_discovery")
        if candidate:
            candidates.append(candidate)
    return candidates


def _candidate_from_supplier_source(
    profile: dict[str, Any],
    source_candidate: dict[str, Any],
    *,
    source_kind: str,
) -> dict[str, Any]:
    unit_price = _number(source_candidate.get("unit_price") or source_candidate.get("price"))
    if unit_price is None or unit_price <= 0:
        return {}
    raw_payload = {**source_candidate, "source_kind": source_kind}
    confidence = str(source_candidate.get("confidence") or "").strip().casefold()
    if not confidence:
        confidence = "high" if source_candidate.get("url") or source_candidate.get("source_url") else "medium"
    candidate = {
        "provider": source_candidate.get("provider") or source_candidate.get("catalog") or "manual",
        "product_name": source_candidate.get("product_name") or source_candidate.get("name") or profile.get("product_name"),
        "supplier_name": source_candidate.get("supplier_name"),
        "source_url": source_candidate.get("source_url") or source_candidate.get("url"),
        "source_query": source_candidate.get("source_query"),
        "source_kind": source_kind,
        "unit_price": unit_price,
        "currency": source_candidate.get("currency") or "RUB",
        "vat_mode": source_candidate.get("vat_mode"),
        "vat_rate_percent": source_candidate.get("vat_rate_percent"),
        "availability": source_candidate.get("availability"),
        "delivery_note": source_candidate.get("delivery_note"),
        "delivery_cost": source_candidate.get("delivery_cost"),
        "unit": source_candidate.get("unit") or source_candidate.get("uom") or profile.get("unit"),
        "price_breaks": _price_breaks(source_candidate.get("price_breaks")),
        "pack_quantity": _first_number(source_candidate, raw_payload, PACK_QUANTITY_FIELDS),
        "stock_quantity": _first_number(source_candidate, raw_payload, SUPPLIER_STOCK_FIELDS),
        "preorder_quantity": _first_number(source_candidate, raw_payload, SUPPLIER_PREORDER_FIELDS),
        "minimum_order_quantity": _first_number(source_candidate, raw_payload, MIN_ORDER_QUANTITY_FIELDS),
        "minimum_order_amount": _first_number(source_candidate, raw_payload, MIN_ORDER_AMOUNT_FIELDS),
        "confidence": confidence,
        "confidence_reasons": _string_list(source_candidate.get("confidence_reasons")),
        "match_reasons": _string_list(source_candidate.get("match_reasons")) + [f"from_{source_kind}"],
        "raw_payload": raw_payload,
    }
    return {key: value for key, value in candidate.items() if value not in (None, "")}


def _supplier_options(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]
