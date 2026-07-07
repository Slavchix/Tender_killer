from __future__ import annotations

import math
import re
from typing import Any


UNAVAILABLE_VALUES = {"not_available", "unavailable", "out_of_stock", "sold_out"}
UNKNOWN_VALUES = {"", "unknown", "none", "null", "n/a", "not_specified", "неизвестно", "не указано"}
VAT_INCLUDED_VALUES = {"vat_included", "included", "with_vat", "nds_included", "ндс_включен"}
VAT_REVIEW_VALUES = {"vat_excluded", "excluded", "without_vat", "no_vat", "nds_excluded", "без_ндс"}
PICKUP_ONLY_MARKERS = ("pickup", "self pickup", "self-pickup", "самовывоз")
DELIVERY_INCLUDED_MARKERS = ("delivery included", "доставка включена", "с доставкой")
TRUSTED_SUPPLIER_VAT_NOTE = "НДС проверить: по умолчанию считаем цену поставщика с НДС."
TRUSTED_SUPPLIER_DELIVERY_RATE_PERCENT = 3.0
TRUSTED_SUPPLIER_MARKERS = (
    "officemag",
    "komus",
    "petrovich",
    "vseinstrumenti",
    "vseinstrument",
    "lemanapro",
    "lemana",
    "офисмаг",
    "комус",
    "петрович",
    "всеинструменты",
    "лемана",
)
PACK_QUANTITY_FIELDS = (
    "pack_quantity",
    "quantity_per_pack",
    "package_quantity",
    "items_per_pack",
    "items_in_pack",
)
MIN_ORDER_QUANTITY_FIELDS = ("minimum_order_quantity", "min_order_quantity", "minimum_quantity", "min_quantity")
MIN_ORDER_AMOUNT_FIELDS = ("minimum_order_amount", "min_order_amount")
SUPPLIER_STOCK_FIELDS = ("stock_quantity", "available_quantity", "stock")
SUPPLIER_PREORDER_FIELDS = ("preorder_quantity", "backorder_quantity", "on_order_quantity")


def raw_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    payload = candidate.get("raw_payload")
    return dict(payload) if isinstance(payload, dict) else {}


def first_number(candidate: dict[str, Any], raw_payload: dict[str, Any], fields: tuple[str, ...]) -> float | None:
    for field in fields:
        value = candidate.get(field)
        if value in (None, ""):
            value = raw_payload.get(field)
        number = number_or_none(value)
        if number is not None:
            return number
    return None


def price_breaks(value: Any) -> list[dict[str, float]]:
    if not isinstance(value, list):
        return []
    breaks: list[dict[str, float]] = []
    seen: set[tuple[float, float]] = set()
    for item in value:
        if not isinstance(item, dict):
            continue
        count = number_or_none(item.get("count") or item.get("quantity") or item.get("min_quantity"))
        price = number_or_none(item.get("price") or item.get("unit_price"))
        if count is None or count <= 0 or price is None or price <= 0:
            continue
        key = (float(count), float(price))
        if key in seen:
            continue
        seen.add(key)
        breaks.append({"count": float(count), "price": float(price)})
    return sorted(breaks, key=lambda item: (item["count"], item["price"]))


def price_break_selection_quantity(
    profile_quantity: float | None,
    profile_unit: str,
    candidate_unit: str,
    pack_quantity: float | None,
) -> float | None:
    if profile_quantity is None or profile_quantity <= 0:
        return None
    if is_pack_unit(candidate_unit) and is_piece_unit(profile_unit) and pack_quantity and pack_quantity > 0:
        return float(math.ceil(profile_quantity / pack_quantity))
    return float(profile_quantity)


def select_price_break(price_breaks: list[dict[str, float]], selection_quantity: float | None) -> dict[str, float] | None:
    if not price_breaks:
        return None
    if selection_quantity is None or selection_quantity <= 0:
        return min(price_breaks, key=lambda item: item["price"])
    eligible = [item for item in price_breaks if item["count"] <= selection_quantity]
    if eligible:
        return max(eligible, key=lambda item: (item["count"], -item["price"]))
    return min(price_breaks, key=lambda item: item["count"])


def copy_price_break_fields(target: dict[str, Any], candidate: dict[str, Any], raw_payload: dict[str, Any]) -> None:
    breaks = price_breaks(candidate.get("price_breaks") or raw_payload.get("price_breaks"))
    if breaks:
        target["price_breaks"] = breaks
    selected = candidate.get("selected_price_break") or raw_payload.get("selected_price_break")
    if isinstance(selected, dict):
        selected_break = select_price_break(price_breaks([selected]), number_or_none(selected.get("count")))
        if selected_break:
            target["selected_price_break"] = selected_break
    selection_quantity = number_or_none(candidate.get("price_break_selection_quantity") or raw_payload.get("price_break_selection_quantity"))
    if selection_quantity is not None:
        target["price_break_selection_quantity"] = selection_quantity


def normalize_availability(value: Any) -> str:
    current_token = token(value)
    in_stock_values = {
        "in_stock",
        "available",
        "instock",
        "https://schema.org/instock",
        "в_наличии",
        "на_складе",
    }
    unavailable_values = {
        "not_available",
        "unavailable",
        "out_of_stock",
        "sold_out",
        "https://schema.org/outofstock",
        "нет",
        "нет_в_наличии",
    }
    if current_token in in_stock_values:
        return "in_stock"
    if current_token in unavailable_values:
        return "unavailable"
    if current_token in UNKNOWN_VALUES:
        return "unknown"
    return current_token or "unknown"


def trusted_supplier_pricing_defaults(candidate: dict[str, Any], raw_payload: dict[str, Any]) -> dict[str, Any]:
    if not trusted_supplier_marker(candidate, raw_payload):
        return {}
    return {
        "vat_note": TRUSTED_SUPPLIER_VAT_NOTE,
        "delivery_rate_percent": TRUSTED_SUPPLIER_DELIVERY_RATE_PERCENT,
    }


def trusted_supplier_marker(candidate: dict[str, Any], raw_payload: dict[str, Any]) -> str:
    text = " ".join(
        str(value)
        for value in (
            candidate.get("provider"),
            raw_payload.get("provider"),
            candidate.get("supplier_name"),
            raw_payload.get("supplier_name"),
            candidate.get("source_url"),
            raw_payload.get("source_url"),
            candidate.get("url"),
            raw_payload.get("url"),
            raw_payload.get("catalog"),
        )
        if value not in (None, "")
    ).casefold()
    compact = re.sub(r"[^a-z0-9]+", "", text)
    for marker in TRUSTED_SUPPLIER_MARKERS:
        if marker in text or marker in compact:
            return marker
    return ""


def delivery_needs_supplier_default(delivery_token: str) -> bool:
    if not delivery_token or delivery_token in UNKNOWN_VALUES:
        return True
    if any(marker in delivery_token for marker in PICKUP_ONLY_MARKERS):
        return False
    if any(marker in delivery_token for marker in DELIVERY_INCLUDED_MARKERS):
        return False
    return True


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item not in (None, "")]


def dedupe_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def token(value: Any) -> str:
    return str(value or "").strip().casefold().replace(" ", "_").replace("-", "_")


def is_piece_unit(unit: str) -> bool:
    return unit in {"шт", "штука", "ед", "pcs", "piece", "unit", "item"}


def is_pack_unit(unit: str) -> bool:
    return unit in {"уп", "упак", "упаковка", "pack", "package", "box"}


def units_compatible(profile_unit: str, candidate_unit: str) -> bool:
    unit_groups = [
        {"шт", "штука", "ед", "pcs", "piece", "unit"},
        {"уп", "упак", "упаковка", "pack", "package"},
        {"м", "meter", "metre", "m"},
        {"кг", "kg"},
        {"л", "l", "liter", "litre"},
    ]
    for group in unit_groups:
        if profile_unit in group and candidate_unit in group:
            return True
    return profile_unit == candidate_unit


def number_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def format_number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(round(float(value), 2)).replace(".", ",")


def round_money(value: float) -> float:
    return round(float(value), 2)
