from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urldefrag
from urllib.parse import urljoin
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from tender_killer.supplier_price_discovery_utils import _format_decimal
from tender_killer.supplier_price_discovery_utils import _is_provider_product_detail_url
from tender_killer.supplier_price_discovery_utils import _number
from tender_killer.supplier_price_discovery_utils import _text


VISIBLE_PRICE_RE = re.compile(r"(?<!\d)(\d[\d\s\u00a0\u202f]*(?:[,.]\d{1,2})?)\s*(?:₽|руб\.?)", re.IGNORECASE)


def _lemanapro_plp_candidates(
    html: str,
    source_url: str,
    query_text: str,
    source_kind: str,
) -> list[dict[str, Any]]:
    state = _extract_initial_state(html, "plp")
    products = _lemanapro_product_items(state)
    candidates: list[dict[str, Any]] = []
    for product in products:
        candidate = _lemanapro_candidate_from_product(product, source_url, query_text, source_kind)
        if candidate:
            candidates.append(candidate)
    return candidates


def _lemanapro_visible_catalog_candidates(
    html: str,
    source_url: str,
    query_text: str,
    source_kind: str,
) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[dict[str, Any]] = []
    for anchor in soup.find_all("a", href=True):
        product_url = urldefrag(urljoin(source_url, str(anchor.get("href") or "")))[0]
        if not _is_provider_product_detail_url("lemanapro", product_url):
            continue
        product_name = _text(anchor.get_text(" ", strip=True))
        if not product_name:
            continue
        scope = _lemanapro_visible_card_scope(anchor)
        lines = _visible_text_lines(scope or soup)
        unit_price = _visible_offer_price(lines, product_name)
        if unit_price is None:
            continue
        candidate: dict[str, Any] = {
            "name": product_name,
            "url": product_url,
            "unit_price": unit_price,
            "currency": "RUB",
            "availability": _visible_availability(lines),
            "status": "candidate",
            "source_query": query_text,
            "source_kind": source_kind,
            "note": f"Lemana Pro catalog visible offer from {source_url}.",
            "provider": "lemanapro",
        }
        if product_code := _lemanapro_visible_product_code(lines, product_url):
            candidate["product_code"] = product_code
        candidates.append(candidate)
    return candidates


def _lemanapro_visible_card_scope(anchor: Any) -> Any | None:
    for parent in getattr(anchor, "parents", []):
        name = str(getattr(parent, "name", "") or "").casefold()
        if name in {"body", "html"}:
            break
        text = parent.get_text(" ", strip=True) if hasattr(parent, "get_text") else ""
        if VISIBLE_PRICE_RE.search(text) and parent.find("a", href=re.compile(r"/product/", re.IGNORECASE)):
            return parent
    return getattr(anchor, "parent", None)


def _lemanapro_visible_product_code(lines: list[str], product_url: str) -> str | None:
    text = " ".join(lines)
    if match := re.search(r"\b(?:арт\.?|art\.?)\s*[:№#-]?\s*(\d{5,12})\b", text, re.IGNORECASE):
        return match.group(1)
    if match := re.search(r"-(\d{5,12})/?$", urlparse(product_url).path):
        return match.group(1)
    return None


def _extract_initial_state(html: str, state_name: str) -> Any:
    marker = f'window.INITIAL_STATE["{state_name}"]'
    marker_index = html.find(marker)
    if marker_index < 0:
        return None
    assignment_index = html.find("=", marker_index + len(marker))
    if assignment_index < 0:
        return None
    object_start = html.find("{", assignment_index)
    if object_start < 0:
        return None
    object_text = _balanced_js_object_text(html, object_start)
    return _json(object_text)


def _balanced_js_object_text(value: str, start_index: int) -> str | None:
    depth = 0
    in_string: str | None = None
    escaped = False
    for index in range(start_index, len(value)):
        char = value[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == in_string:
                in_string = None
            continue
        if char in {'"', "'"}:
            in_string = char
            continue
        if char == "{":
            depth += 1
            continue
        if char == "}":
            depth -= 1
            if depth == 0:
                return value[start_index : index + 1]
    return None


def _json(value: str | None) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None


def _lemanapro_product_items(state: Any) -> list[dict[str, Any]]:
    if not isinstance(state, dict):
        return []
    products = state.get("products")
    if not isinstance(products, dict):
        return []
    data = products.get("data")
    if isinstance(data, list):
        return [dict(item) for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return [dict(item) for item in data.values() if isinstance(item, dict)]
    products_by_ids = products.get("productsByIds")
    if isinstance(products_by_ids, dict):
        return [dict(item) for item in products_by_ids.values() if isinstance(item, dict)]
    return []


def _lemanapro_candidate_from_product(
    product: dict[str, Any],
    source_url: str,
    query_text: str,
    source_kind: str,
) -> dict[str, Any] | None:
    product_name = _text(product.get("displayedName") or product.get("name"))
    price_data = product.get("price") if isinstance(product.get("price"), dict) else {}
    unit_price = _number(price_data.get("main_price"))
    if not product_name or unit_price is None:
        return None
    product_url = _text(product.get("productLink") or product.get("url")) or source_url
    product_url = urldefrag(urljoin(source_url, product_url))[0]
    if not _is_provider_product_detail_url("lemanapro", product_url):
        return None
    currency = (_text(price_data.get("currency")) or "RUB").upper()
    candidate: dict[str, Any] = {
        "name": product_name,
        "url": product_url,
        "unit_price": unit_price,
        "currency": currency,
        "availability": _lemanapro_availability(product),
        "status": "candidate",
        "source_query": query_text,
        "source_kind": source_kind,
        "note": f"Lemana Pro catalog PLP offer from {source_url}.",
        "provider": "lemanapro",
    }
    if product_code := _text(product.get("productId")):
        candidate["product_code"] = product_code
    if brand := _text(product.get("brand")):
        candidate["brand"] = brand
    if image_url := _lemanapro_image_url(product):
        candidate["image_url"] = image_url
    if attributes := _lemanapro_product_attributes(product):
        candidate["product_attributes"] = attributes
    if price_break := _lemanapro_price_break(unit_price):
        candidate["price_breaks"] = [price_break]
    if delivery_note := _lemanapro_delivery_note(price_data, currency):
        candidate["delivery_note"] = delivery_note
    return candidate


def _lemanapro_price_break(unit_price: float) -> dict[str, Any] | None:
    if unit_price is None:
        return None
    return {"count": 1, "price": unit_price}


def _lemanapro_delivery_note(price_data: dict[str, Any], currency: str) -> str | None:
    main_price = _number(price_data.get("main_price"))
    parts: list[str] = []
    if main_price is not None:
        main_uom = _text(price_data.get("main_uom_rus")) or _text(price_data.get("main_uom")) or "unit"
        parts.append(f"цена {_format_decimal(main_price)} {currency}/{main_uom}")
    additional_price = _number(price_data.get("additional_price"))
    if additional_price is not None:
        additional_uom = _text(price_data.get("additional_uom_rus")) or _text(price_data.get("additional_uom")) or "unit"
        parts.append(f"доп. цена {_format_decimal(additional_price)} {currency}/{additional_uom}")
    return f"Lemana Pro: {'; '.join(parts)}." if parts else None


def _lemanapro_availability(product: dict[str, Any]) -> str:
    eligibility = product.get("eligibility")
    if isinstance(eligibility, dict) and any(bool(eligibility.get(key)) for key in (
        "homeDeliveryEligible",
        "storeDeliveryEligible",
        "webEligible",
    )):
        return "in_stock"
    return "in_stock"


def _lemanapro_image_url(product: dict[str, Any]) -> str | None:
    media = product.get("mediaMainPhoto")
    if isinstance(media, dict):
        for key in ("desktop", "tablet", "mobile"):
            if url := _text(media.get(key)):
                return url
    return None


def _lemanapro_product_attributes(product: dict[str, Any]) -> list[dict[str, str]]:
    attributes: list[dict[str, str]] = []
    characteristics = product.get("characteristics")
    if not isinstance(characteristics, list):
        return attributes
    for item in characteristics:
        if not isinstance(item, dict):
            continue
        name = _text(item.get("description") or item.get("name") or item.get("key"))
        value = _text(item.get("value"))
        if name and value:
            attributes.append({"name": name, "value": value})
    return attributes


def _visible_text_lines(soup: BeautifulSoup) -> list[str]:
    return [
        line.strip()
        for line in soup.get_text("\n").splitlines()
        if line.strip()
    ]


def _visible_offer_price(lines: list[str], product_name: str) -> float | None:
    search_lines = _lines_after_product_name(lines, product_name)
    prices: list[float] = []
    for line in search_lines:
        for match in VISIBLE_PRICE_RE.finditer(line):
            price = _number(match.group(1).replace("\u00a0", "").replace("\u202f", ""))
            if price is not None:
                prices.append(price)
    if not prices:
        return None
    return min(prices)


def _lines_after_product_name(lines: list[str], product_name: str) -> list[str]:
    product_key = product_name.casefold()
    for index, line in enumerate(lines):
        if line.casefold() == product_key:
            return lines[index + 1:index + 30]
    return lines[:30]


def _visible_availability(lines: list[str]) -> str:
    text = " ".join(lines).casefold()
    in_stock_markers = (
        "в корзину",
        "наличие",
        "на складе",
        "самовывоз",
        "курьером",
        "доставка",
        "in stock",
    )
    if any(marker in text for marker in in_stock_markers):
        return "in_stock"
    not_available_markers = (
        "нет в наличии",
        "недоступен к заказу",
        "нет товара",
        "out of stock",
        "sold out",
    )
    if any(marker in text for marker in not_available_markers):
        return "not_available"
    return "unknown"
