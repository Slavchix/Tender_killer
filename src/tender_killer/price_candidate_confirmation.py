from __future__ import annotations

import re
from typing import Any

from tender_killer.price_candidate_common import (
    MIN_ORDER_QUANTITY_FIELDS,
    PACK_QUANTITY_FIELDS,
    SUPPLIER_PREORDER_FIELDS,
    SUPPLIER_STOCK_FIELDS,
    copy_price_break_fields as _copy_price_break_fields,
    first_number as _first_number,
    number_or_none as _number,
    raw_payload as _raw_payload,
    token as _token,
    units_compatible as _units_compatible,
)
from tender_killer.price_candidate_quality import evaluate_price_candidate_quality


PRICE_MATCH_TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)
PRICE_MATCH_STOP_WORDS = {
    "для",
    "товар",
    "товара",
    "товары",
    "работа",
    "работы",
    "услуга",
    "услуги",
    "офисной",
    "офисная",
    "техники",
    "техника",
    "office",
    "for",
    "the",
}


def apply_confirmed_candidate(
    profile: dict[str, Any],
    candidate: dict[str, Any],
    *,
    selection: str = "manual_confirmed",
) -> int | None:
    unit_price = _number(candidate.get("unit_price"))
    if unit_price is None:
        raise ValueError("Price candidate has no unit price.")

    raw_payload = dict(profile.get("raw_payload") or {})
    supplier_options = _supplier_options(raw_payload.get("supplier_options"))
    option = _supplier_option_from_candidate(candidate)
    option_index = _matching_supplier_option_index(supplier_options, option)
    if option_index is None:
        supplier_options.append(option)
        option_index = len(supplier_options) - 1

    for index, supplier_option in enumerate(supplier_options):
        if index == option_index:
            supplier_option["status"] = "selected"
        elif supplier_option.get("status") == "selected":
            supplier_option["status"] = "candidate"

    economics = dict(raw_payload.get("economics") or {})
    economics["unit_cost"] = unit_price
    raw_payload["economics"] = economics
    raw_payload["supplier_options"] = supplier_options
    raw_payload["selected_supplier_option_index"] = option_index
    quality = evaluate_price_candidate_quality(profile, candidate)
    raw_payload["economics_price_source"] = _economics_price_source(candidate, unit_price, quality, selection=selection)
    profile["raw_payload"] = raw_payload
    profile["profile_status"] = "priced"
    return option_index


def propagate_confirmed_candidate_to_matching_profiles(
    profiles: list[dict[str, Any]],
    source_profile: dict[str, Any],
    candidate: dict[str, Any],
) -> list[dict[str, int | None]]:
    source_index = int(source_profile.get("position_index") or 0)
    source_key = _profile_price_reuse_key(source_profile)
    source_unit = _token(source_profile.get("unit"))
    if not source_key or not source_unit:
        return []

    propagated: list[dict[str, int | None]] = []
    for profile in profiles:
        position_index = int(profile.get("position_index") or 0)
        if position_index == source_index or profile_has_positive_cost(profile):
            continue
        if _profile_price_reuse_key(profile) != source_key:
            continue
        target_unit = _token(profile.get("unit"))
        if not target_unit or not _units_compatible(source_unit, target_unit):
            continue
        option_index = apply_confirmed_candidate(profile, candidate, selection="reused_from_position")
        raw_payload = dict(profile.get("raw_payload") or {})
        price_source = dict(raw_payload.get("economics_price_source") or {})
        price_source["reused_from_position_index"] = source_index
        raw_payload["economics_price_source"] = price_source
        profile["raw_payload"] = raw_payload
        propagated.append({"position_index": position_index, "supplier_option_index": option_index})
    return propagated


def profile_has_positive_cost(profile: dict[str, Any]) -> bool:
    raw_payload = profile.get("raw_payload")
    if not isinstance(raw_payload, dict):
        return False
    economics = raw_payload.get("economics")
    if not isinstance(economics, dict):
        return False
    unit_cost = _number(economics.get("unit_cost"))
    total_cost = _number(economics.get("total_cost"))
    return bool((unit_cost is not None and unit_cost > 0) or (total_cost is not None and total_cost > 0))


def _profile_price_reuse_key(profile: dict[str, Any]) -> str:
    name = str(profile.get("normalized_name") or profile.get("product_name") or "").casefold()
    tokens = [token for token in PRICE_MATCH_TOKEN_RE.findall(name) if token and token not in PRICE_MATCH_STOP_WORDS]
    return " ".join(tokens)


def _economics_price_source(
    candidate: dict[str, Any],
    unit_price: float,
    quality: dict[str, Any],
    *,
    selection: str,
) -> dict[str, Any]:
    raw_payload = _raw_payload(candidate)
    source = {
        "source": "price_candidate",
        "selection": selection,
        "candidate_id": int(candidate["id"]),
        "provider": candidate.get("provider"),
        "product_name": candidate.get("product_name"),
        "supplier_name": candidate.get("supplier_name"),
        "source_url": candidate.get("source_url"),
        "source_query": candidate.get("source_query"),
        "source_kind": candidate.get("source_kind"),
        "unit_price": unit_price,
        "currency": candidate.get("currency") or "RUB",
        "review_status": "confirmed",
        "quality_status": quality.get("quality_status"),
        "auto_eligible": bool(quality.get("auto_eligible")),
        "quality_flags": quality.get("quality_flags") or [],
    }
    for field, fields in {
        "stock_quantity": SUPPLIER_STOCK_FIELDS,
        "preorder_quantity": SUPPLIER_PREORDER_FIELDS,
        "minimum_order_quantity": MIN_ORDER_QUANTITY_FIELDS,
        "pack_quantity": PACK_QUANTITY_FIELDS,
    }.items():
        number = _first_number(candidate, raw_payload, fields)
        if number is not None:
            source[field] = number
    price_memory = candidate.get("price_memory") if isinstance(candidate.get("price_memory"), dict) else raw_payload.get("price_memory")
    if isinstance(price_memory, dict):
        source["price_memory"] = price_memory
    _copy_price_break_fields(source, candidate, raw_payload)
    return source


def _supplier_option_from_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    option: dict[str, Any] = {
        "name": candidate.get("supplier_name") or candidate.get("product_name") or "Supplier candidate",
        "unit_price": _number(candidate.get("unit_price")),
        "status": "selected",
    }
    field_map = {
        "source_url": "url",
        "provider": "provider",
        "confidence": "confidence",
        "currency": "currency",
        "vat_mode": "vat_mode",
        "availability": "availability",
        "source_query": "source_query",
        "source_kind": "source_kind",
    }
    for source_key, option_key in field_map.items():
        if candidate.get(source_key) not in (None, ""):
            option[option_key] = candidate[source_key]
    raw_payload = _raw_payload(candidate)
    number_field_map = {
        "stock_quantity": SUPPLIER_STOCK_FIELDS,
        "preorder_quantity": SUPPLIER_PREORDER_FIELDS,
        "minimum_order_quantity": MIN_ORDER_QUANTITY_FIELDS,
        "pack_quantity": PACK_QUANTITY_FIELDS,
    }
    for option_key, source_fields in number_field_map.items():
        number = _first_number(candidate, raw_payload, source_fields)
        if number is not None:
            option[option_key] = number
    _copy_price_break_fields(option, candidate, raw_payload)
    return {key: value for key, value in option.items() if value is not None}


def _matching_supplier_option_index(supplier_options: list[dict[str, Any]], option: dict[str, Any]) -> int | None:
    option_url = str(option.get("url") or "").strip().casefold()
    for index, supplier_option in enumerate(supplier_options):
        supplier_url = str(supplier_option.get("url") or "").strip().casefold()
        if option_url and supplier_url == option_url:
            return index
        same_provider = str(supplier_option.get("provider") or "").casefold() == str(option.get("provider") or "").casefold()
        same_name = str(supplier_option.get("name") or "").casefold() == str(option.get("name") or "").casefold()
        same_price = _number(supplier_option.get("unit_price")) == _number(option.get("unit_price"))
        if same_provider and same_name and same_price:
            return index
    return None


def _supplier_options(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]
