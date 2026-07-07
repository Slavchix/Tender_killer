from __future__ import annotations

from typing import Any

from tender_killer.price_candidate_common import (
    PACK_QUANTITY_FIELDS,
    SUPPLIER_PREORDER_FIELDS,
    SUPPLIER_STOCK_FIELDS,
    UNKNOWN_VALUES,
    VAT_INCLUDED_VALUES,
    VAT_REVIEW_VALUES,
    dedupe_strings,
    delivery_needs_supplier_default,
    first_number,
    format_number,
    is_pack_unit,
    is_piece_unit,
    normalize_availability,
    number_or_none,
    price_break_selection_quantity,
    price_breaks,
    raw_payload,
    select_price_break,
    string_list,
    token,
    trusted_supplier_pricing_defaults,
)


def normalize_price_candidate(profile: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    normalized = {**candidate}
    payload = raw_payload(candidate)
    profile_quantity = number_or_none(profile.get("quantity"))
    profile_unit = token(profile.get("unit"))
    candidate_unit = token(candidate.get("unit") or payload.get("unit") or payload.get("uom"))
    pack_quantity = first_number(candidate, payload, PACK_QUANTITY_FIELDS)
    breaks = price_breaks(candidate.get("price_breaks") or payload.get("price_breaks"))
    break_quantity = price_break_selection_quantity(profile_quantity, profile_unit, candidate_unit, pack_quantity)
    selected_break = select_price_break(breaks, break_quantity)
    original_unit_price = number_or_none(candidate.get("unit_price") or payload.get("unit_price"))
    if selected_break:
        original_unit_price = number_or_none(selected_break.get("price"))
    if original_unit_price is None:
        original_unit_price = 0.0
    unit_price = original_unit_price
    match_reasons = string_list(candidate.get("match_reasons"))
    normalization: dict[str, Any] = {
        "original_unit_price": original_unit_price,
        "source": candidate.get("source_kind") or payload.get("source_kind"),
    }

    if breaks:
        normalized["price_breaks"] = breaks
        payload["price_breaks"] = breaks
    if selected_break:
        normalized["selected_price_break"] = selected_break
        payload["selected_price_break"] = selected_break
        normalization["selected_price_break"] = selected_break
        match_reasons.append("price_break_selected")
    if break_quantity is not None:
        normalized["price_break_selection_quantity"] = break_quantity
        payload["price_break_selection_quantity"] = break_quantity
        normalization["price_break_selection_quantity"] = break_quantity

    if is_pack_unit(candidate_unit) and is_piece_unit(profile_unit) and pack_quantity and pack_quantity > 0:
        unit_price = unit_price / pack_quantity
        normalized["unit"] = profile.get("unit")
        normalization["pack_quantity"] = pack_quantity
        match_reasons.append("pack_quantity_normalized")
    elif candidate.get("unit") not in (None, ""):
        normalized["unit"] = candidate.get("unit")
    elif profile.get("unit") not in (None, ""):
        normalized["unit"] = profile.get("unit")

    vat_mode = token(candidate.get("vat_mode") or payload.get("vat_mode"))
    vat_rate = number_or_none(candidate.get("vat_rate_percent") or payload.get("vat_rate_percent"))
    supplier_defaults = trusted_supplier_pricing_defaults(candidate, payload)
    if vat_mode in VAT_REVIEW_VALUES and vat_rate and vat_rate > 0:
        unit_price = unit_price * (1 + vat_rate / 100)
        normalized["vat_mode"] = "vat_included"
        normalized["vat_rate_percent"] = vat_rate
        normalization["vat_rate_percent"] = vat_rate
        match_reasons.append("vat_normalized")
    elif vat_mode in VAT_REVIEW_VALUES and supplier_defaults:
        normalized["vat_mode"] = "vat_included"
        normalized["vat_note"] = supplier_defaults["vat_note"]
        normalization["supplier_default_vat_note"] = supplier_defaults["vat_note"]
        match_reasons.append("supplier_default_vat_included")
    elif vat_mode in UNKNOWN_VALUES and supplier_defaults:
        normalized["vat_mode"] = "vat_included"
        normalized["vat_note"] = supplier_defaults["vat_note"]
        normalization["supplier_default_vat_note"] = supplier_defaults["vat_note"]
        match_reasons.append("supplier_default_vat_included")
    elif vat_mode:
        normalized["vat_mode"] = "vat_included" if vat_mode in VAT_INCLUDED_VALUES else vat_mode
        if vat_rate is not None:
            normalized["vat_rate_percent"] = vat_rate

    availability = normalize_availability(candidate.get("availability") or payload.get("availability"))
    if availability:
        normalized["availability"] = availability
    stock_quantity = first_number(candidate, payload, SUPPLIER_STOCK_FIELDS)
    if stock_quantity is not None:
        normalized["stock_quantity"] = stock_quantity
    preorder_quantity = first_number(candidate, payload, SUPPLIER_PREORDER_FIELDS)
    if preorder_quantity is not None:
        normalized["preorder_quantity"] = preorder_quantity

    delivery_note = str(candidate.get("delivery_note") or payload.get("delivery_note") or "").strip()
    delivery_token = delivery_note.casefold()
    if not delivery_note and number_or_none(candidate.get("delivery_cost") or payload.get("delivery_cost")) == 0:
        delivery_note = "Delivery included"
        delivery_token = delivery_note.casefold()
    elif supplier_defaults and delivery_needs_supplier_default(delivery_token):
        delivery_rate = number_or_none(candidate.get("delivery_rate_percent") or payload.get("delivery_rate_percent"))
        if delivery_rate is None or delivery_rate <= 0:
            delivery_rate = supplier_defaults["delivery_rate_percent"]
        delivery_cost_per_unit = unit_price * delivery_rate / 100
        unit_price += delivery_cost_per_unit
        normalized["delivery_rate_percent"] = delivery_rate
        normalized["delivery_cost_per_unit"] = round(delivery_cost_per_unit, 2)
        delivery_note = f"Delivery included by supplier default ({format_number(delivery_rate)}%)"
        normalization["supplier_default_delivery_rate_percent"] = delivery_rate
        normalization["supplier_default_delivery_cost_per_unit"] = round(delivery_cost_per_unit, 2)
        match_reasons.append("supplier_default_delivery")
    if delivery_note:
        normalized["delivery_note"] = delivery_note

    normalized["unit_price"] = round(unit_price, 2)
    normalized["currency"] = str(candidate.get("currency") or payload.get("currency") or "RUB").strip().upper() or "RUB"
    normalized["confidence"] = str(candidate.get("confidence") or payload.get("confidence") or "high").strip().casefold()
    if candidate.get("provider") not in (None, ""):
        normalized["provider"] = candidate.get("provider")
    if candidate.get("source_url") in (None, "") and candidate.get("url"):
        normalized["source_url"] = candidate.get("url")
    if candidate.get("product_name") in (None, "") and candidate.get("name"):
        normalized["product_name"] = candidate.get("name")

    normalization["normalized_unit_price"] = normalized["unit_price"]
    payload.update(
        {
            "original_unit_price": original_unit_price,
            "normalized_unit_price": normalized["unit_price"],
            "normalization": {key: value for key, value in normalization.items() if value not in (None, "")},
        }
    )
    normalized["original_unit_price"] = original_unit_price
    normalized["normalized_unit_price"] = normalized["unit_price"]
    normalized["normalization"] = payload["normalization"]
    normalized["raw_payload"] = payload
    normalized["match_reasons"] = dedupe_strings(match_reasons)
    return normalized
