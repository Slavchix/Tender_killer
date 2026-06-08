from __future__ import annotations

import re
from typing import Any


NUMBER_SPACE_RE = re.compile(r"[\s\u00a0\u202f]+")


def normalize_supplier_candidate(
    candidate: dict[str, Any],
    *,
    provider: str = "",
    source_query: str = "",
    source_kind: str = "",
) -> dict[str, Any]:
    normalized = dict(candidate)

    name = _text(normalized.get("name") or normalized.get("product_name"))
    product_name = _text(normalized.get("product_name") or name)
    url = _text(normalized.get("url") or normalized.get("source_url"))
    source_url = _text(normalized.get("source_url") or url)
    if name:
        normalized["name"] = name
    if product_name:
        normalized["product_name"] = product_name
    if url:
        normalized["url"] = url
    if source_url:
        normalized["source_url"] = source_url

    resolved_provider = _token(normalized.get("provider") or provider)
    if resolved_provider:
        normalized["provider"] = resolved_provider
    resolved_source_query = _text(normalized.get("source_query") or source_query)
    if resolved_source_query:
        normalized["source_query"] = resolved_source_query
    resolved_source_kind = _text(normalized.get("source_kind") or source_kind)
    if resolved_source_kind:
        normalized["source_kind"] = resolved_source_kind

    for field in (
        "unit_price",
        "stock_quantity",
        "preorder_quantity",
        "minimum_order_quantity",
        "minimum_order_amount",
        "pack_quantity",
        "vat_rate_percent",
    ):
        number = _number(normalized.get(field))
        if number is not None:
            normalized[field] = number
        elif field in normalized:
            normalized.pop(field, None)

    price_breaks = _price_breaks(normalized.get("price_breaks"))
    if price_breaks:
        normalized["price_breaks"] = price_breaks

    for field in ("match_reasons", "confidence_reasons"):
        items = _string_list(normalized.get(field))
        if items:
            normalized[field] = _dedupe_strings(items)
        elif field in normalized:
            normalized.pop(field, None)

    return normalized


def normalize_supplier_candidates(
    candidates: list[dict[str, Any]],
    *,
    provider: str = "",
    source_query: str = "",
    source_kind: str = "",
) -> list[dict[str, Any]]:
    return [
        normalize_supplier_candidate(
            candidate,
            provider=provider,
            source_query=source_query,
            source_kind=source_kind,
        )
        for candidate in candidates
        if isinstance(candidate, dict)
    ]


def _price_breaks(value: Any) -> list[dict[str, float]]:
    if not isinstance(value, list):
        return []
    price_breaks: list[dict[str, float]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        count = _number(item.get("count") or item.get("quantity") or item.get("min_quantity"))
        price = _number(item.get("price") or item.get("unit_price"))
        if count is None or price is None:
            continue
        price_breaks.append({"count": count, "price": price})
    return sorted(price_breaks, key=lambda item: (item["count"], item["price"]))


def _dedupe_strings(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        key = item.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = _text(item)
        if text:
            items.append(text)
    return items


def _token(value: Any) -> str | None:
    text = _text(value)
    if not text:
        return None
    token = "".join(character if character.isalnum() else "_" for character in text.casefold()).strip("_")
    while "__" in token:
        token = token.replace("__", "_")
    return token or None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(NUMBER_SPACE_RE.sub("", str(value)).replace(",", "."))
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None
