from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urldefrag
from urllib.parse import urljoin
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from tender_killer.supplier_price_discovery_utils import NUMBER_SPACE_RE
from tender_killer.supplier_price_discovery_utils import _append_unique_url
from tender_killer.supplier_price_discovery_utils import _catalog_product_name_matches_query
from tender_killer.supplier_price_discovery_utils import _format_decimal
from tender_killer.supplier_price_discovery_utils import _is_provider_product_detail_url
from tender_killer.supplier_price_discovery_utils import _number
from tender_killer.supplier_price_discovery_utils import _positive_number
from tender_killer.supplier_price_discovery_utils import _text


VISIBLE_PRICE_RE = re.compile(r"(?<!\d)(\d[\d\s\u00a0\u202f]*(?:[,.]\d{1,2})?)\s*(?:₽|руб\.?)", re.IGNORECASE)


def _officemag_hidden_product_page_urls(html: str, source_url: str) -> list[str]:
    if "officemag.ru" not in urlparse(source_url).netloc.casefold():
        return []
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    seen: set[str] = set()
    for node in soup.select(".js-listXmlIDs[value]"):
        for product_code in re.findall(r"(?<!\d)\d{5,8}(?!\d)", str(node.get("value") or "")):
            _append_unique_url(urls, seen, urljoin(source_url, f"/catalog/goods/{product_code}/"))
    return urls


def _officemag_visible_candidates(
    html: str,
    source_url: str,
    query_text: str,
    source_kind: str,
) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    if _is_provider_product_detail_url("officemag", source_url):
        candidate = _officemag_candidate_from_scope(
            soup,
            source_url,
            query_text,
            source_kind,
            note=f"OfficeMag catalog visible offer from {source_url}.",
        )
        return [candidate] if candidate else []

    candidates: list[dict[str, Any]] = []
    for item in _officemag_product_scopes(soup):
        product_url = _officemag_product_url(item, source_url)
        if not product_url:
            continue
        candidate = _officemag_candidate_from_scope(
            item,
            product_url,
            query_text,
            source_kind,
            note=f"OfficeMag catalog search result from {source_url}.",
        )
        if candidate:
            candidates.append(candidate)
    return candidates


def _officemag_product_scopes(soup: BeautifulSoup) -> list[Any]:
    scopes: list[Any] = []
    seen: set[int] = set()
    for item in soup.select("li.listItem, .js-productListItem"):
        key = id(item)
        if key in seen:
            continue
        seen.add(key)
        scopes.append(item)
    return scopes


def _officemag_candidate_from_scope(
    scope: BeautifulSoup,
    product_url: str,
    query_text: str,
    source_kind: str,
    *,
    note: str,
) -> dict[str, Any] | None:
    product_name = _officemag_product_name(scope)
    if not product_name:
        return None
    product_code = _officemag_product_code(scope, product_url)
    query_codes = _officemag_query_product_codes(query_text)
    code_matched = bool(product_code and product_code in query_codes)
    if query_codes and product_code and not code_matched:
        return None
    if not code_matched and not _catalog_product_name_matches_query(product_name, query_text):
        return None
    price_breaks = _officemag_price_breaks(scope)
    prices = [item["price"] for item in price_breaks]
    if price := _officemag_primary_price(scope):
        prices.append(price)
    if price := _officemag_ga_product_price(scope, product_code):
        prices.append(price)
    if not prices:
        lines = _visible_text_lines(scope)
        visible_price = _visible_offer_price(lines, product_name)
        if visible_price is not None:
            prices.append(visible_price)
    if not prices:
        return None

    delivery_note = _officemag_delivery_note(scope, price_breaks)
    stock_quantity = _officemag_stock_quantity(scope)
    preorder_quantity = _officemag_preorder_quantity(scope)
    min_party = _officemag_min_party(scope)
    pack_size = _officemag_pack_size(scope)
    candidate = {
        "name": product_name,
        "url": product_url,
        "unit_price": min(prices),
        "currency": "RUB",
        "availability": _officemag_availability(scope),
        "status": "candidate",
        "source_query": query_text,
        "source_kind": source_kind,
        "note": note,
        "provider": "officemag",
    }
    if price_breaks:
        candidate["price_breaks"] = price_breaks
    if code_matched and product_code:
        candidate["product_code"] = product_code
    if stock_quantity is not None:
        candidate["stock_quantity"] = stock_quantity
    if preorder_quantity is not None:
        candidate["preorder_quantity"] = preorder_quantity
    if min_party is not None:
        candidate["minimum_order_quantity"] = min_party
    if pack_size is not None:
        candidate["pack_quantity"] = pack_size
    if delivery_note:
        candidate["delivery_note"] = delivery_note
    return candidate


def _officemag_product_url(scope: BeautifulSoup, source_url: str) -> str | None:
    for anchor in scope.find_all("a", href=True):
        href = _text(anchor.get("href"))
        if href and "/catalog/goods/" in href.casefold():
            return urldefrag(urljoin(source_url, href))[0]
    return None


def _officemag_product_code(scope: BeautifulSoup, product_url: str) -> str | None:
    url_match = re.search(r"/catalog/goods/(\d{5,8})(?:/|$)", urlparse(product_url).path)
    if url_match:
        return url_match.group(1)
    for node in scope.select(".code"):
        code = _first_product_code(_officemag_scope_text(node))
        if code:
            return code
    return _first_product_code(_officemag_scope_text(scope))


def _officemag_query_product_codes(query_text: str) -> set[str]:
    return set(re.findall(r"(?<!\d)\d{5,8}(?!\d)", str(query_text or "")))


def _first_product_code(text: str) -> str | None:
    match = re.search(r"(?<!\d)\d{5,8}(?!\d)", text)
    return match.group(0) if match else None


def _officemag_product_name(scope: BeautifulSoup) -> str | None:
    for selector in (".ProductHead__name", "[itemprop='name']"):
        for node in scope.select(selector):
            text = _clean_officemag_text(str(node.get("content") or "") or node.get_text(" ", strip=True))
            if text:
                return text
    heading = scope.find("h1")
    if heading:
        return _clean_officemag_text(heading.get_text(" ", strip=True))
    for anchor in scope.find_all("a", href=True):
        href = _text(anchor.get("href"))
        if not href or "/catalog/goods/" not in href.casefold():
            continue
        text = _clean_officemag_text(anchor.get_text(" ", strip=True))
        if text:
            return text
    image = scope.find("img", alt=True)
    if image:
        return _clean_officemag_text(str(image.get("alt") or ""))
    return None


def _clean_officemag_text(value: str) -> str | None:
    text = BeautifulSoup(value.replace("<wbr/>", ""), "html.parser").get_text(" ", strip=True)
    text = text.replace("«", '"').replace("»", '"').replace("\xa0", " ")
    text = " ".join(text.split())
    text = text.replace("/ ", "/").replace(" /", "/")
    text = re.sub(r'\s+"', ' "', text)
    text = re.sub(r'"([^"]*?)\s+"', r'"\1"', text)
    text = re.sub(r'"\s+', '" ', text)
    return _text(text)


def _officemag_price_breaks(scope: BeautifulSoup) -> list[dict[str, Any]]:
    breaks: list[dict[str, Any]] = []
    seen: set[tuple[int, float]] = set()
    for item in scope.select(".ProductSpecial__item[data-price]"):
        price = _number(item.get("data-price"))
        count = _positive_number(item.get("data-count"))
        if price is None or count is None:
            continue
        key = (count, price)
        if key in seen:
            continue
        seen.add(key)
        breaks.append({"count": count, "price": price})
    return sorted(breaks, key=lambda item: int(item["count"]))


def _officemag_primary_price(scope: BeautifulSoup) -> float | None:
    price_node = scope.select_one('.Product__price[content], [itemprop="price"][content]')
    if price_node:
        return _number(price_node.get("content"))
    sum_node = scope.select_one(".js-productSum[data-price]")
    if sum_node:
        return _number(sum_node.get("data-price"))
    return None


def _officemag_ga_product_price(scope: BeautifulSoup, product_code: str | None) -> float | None:
    if not product_code:
        return None
    for node in scope.find_all(attrs={"data-ga-object": True}):
        payload = node.get("data-ga-object")
        if not isinstance(payload, str) or product_code not in payload:
            continue
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if price := _officemag_ga_price_for_product(data, product_code):
            return price
    return None


def _officemag_ga_price_for_product(value: Any, product_code: str) -> float | None:
    if isinstance(value, dict):
        item_id = _text(value.get("item_id"))
        if item_id == product_code:
            return _number(value.get("price")) or _number(value.get("value"))
        for key in ("items", "data"):
            if price := _officemag_ga_price_for_product(value.get(key), product_code):
                return price
        return None
    if isinstance(value, list):
        for item in value:
            if price := _officemag_ga_price_for_product(item, product_code):
                return price
    return None


def _officemag_availability(scope: BeautifulSoup) -> str:
    text = _officemag_scope_text(scope).casefold()
    if "наличие на складе" in text or "на складе" in text or "в корзину" in text:
        return "in_stock"
    if "нет в наличии" in text or "недоступен" in text:
        return "not_available"
    return "unknown"


def _officemag_delivery_note(scope: BeautifulSoup, price_breaks: list[dict[str, Any]]) -> str | None:
    parts: list[str] = []
    for item in price_breaks:
        parts.append(f"цена от {item['count']} шт. {_format_decimal(item['price'])} RUB")
    text = _officemag_scope_text(scope)
    stock = _officemag_quantity_after(text, r"(?:Наличие на складе|На складе)\b")
    preorder = _officemag_quantity_after(text, r"Под заказ\b")
    min_party = _officemag_min_party(scope)
    pack_size = _officemag_pack_size(scope)
    if not parts and not stock and not preorder and min_party is None and pack_size is None:
        return None
    if stock:
        parts.append(f"склад {stock}")
    if preorder:
        parts.append(f"под заказ {preorder}")
    if min_party is not None:
        parts.append(f"мин. партия {min_party}")
    if pack_size is not None:
        parts.append(f"в упаковке {pack_size}")
    return f"OfficeMag: {'; '.join(parts)}." if parts else None


def _officemag_scope_text(scope: BeautifulSoup) -> str:
    return " ".join(scope.get_text(" ", strip=True).replace("\xa0", " ").split())


def _officemag_stock_quantity(scope: BeautifulSoup) -> int | None:
    text = _officemag_scope_text(scope)
    return _officemag_quantity_number_after(text, r"(?:Наличие на складе|На складе)\b")


def _officemag_preorder_quantity(scope: BeautifulSoup) -> int | None:
    text = _officemag_scope_text(scope)
    return _officemag_quantity_number_after(text, r"Под заказ\b")


def _officemag_min_party(scope: BeautifulSoup) -> int | None:
    text = _officemag_scope_text(scope)
    for node in scope.select(".ProductState--stepCount .ProductState"):
        node_text = _officemag_scope_text(node)
        if "Мин. партия" not in node_text:
            continue
        match = re.search(r":\s*(\d+)\b", node_text)
        if match:
            return int(match.group(1))
    return _officemag_int_after(text, r"Мин\.\s*партия")


def _officemag_pack_size(scope: BeautifulSoup) -> int | None:
    text = _officemag_scope_text(scope)
    return _officemag_int_after(text, r"В упаковке")


def _officemag_quantity_after(text: str, marker_pattern: str) -> str | None:
    match = re.search(rf"{marker_pattern}.{{0,80}}?([+]?\d[\d\s\u00a0\u202f]*\s*шт\.?)", text, re.IGNORECASE)
    if not match:
        return None
    return " ".join(match.group(1).replace("\xa0", " ").replace("\u202f", " ").split())


def _officemag_quantity_number_after(text: str, marker_pattern: str) -> int | None:
    quantity = _officemag_quantity_after(text, marker_pattern)
    if not quantity:
        return None
    match = re.search(r"\d[\d\s\u00a0\u202f]*", quantity)
    if not match:
        return None
    return int(NUMBER_SPACE_RE.sub("", match.group(0)))


def _officemag_int_after(text: str, marker_pattern: str) -> int | None:
    match = re.search(rf"{marker_pattern}\s*:?\s*(\d+)", text, re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


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
