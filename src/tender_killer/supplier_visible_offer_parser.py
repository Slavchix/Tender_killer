from __future__ import annotations

import re
from typing import Any
from urllib.parse import urldefrag
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from tender_killer.supplier_price_discovery_utils import _append_unique_url
from tender_killer.supplier_price_discovery_utils import _catalog_provider_label
from tender_killer.supplier_price_discovery_utils import _is_provider_product_detail_url
from tender_killer.supplier_price_discovery_utils import _is_public_product_page_url
from tender_killer.supplier_price_discovery_utils import _is_same_public_site
from tender_killer.supplier_price_discovery_utils import _number
from tender_killer.supplier_price_discovery_utils import _text


VISIBLE_PRICE_RE = re.compile(r"(?<!\d)(\d[\d\s\u00a0\u202f]*(?:[,.]\d{1,2})?)\s*(?:₽|руб\.?)", re.IGNORECASE)


def _provider_visible_offer_candidates(
    html: str,
    source_url: str,
    query_text: str,
    source_kind: str,
    provider: str,
) -> list[dict[str, Any]]:
    if not _is_provider_product_detail_url(provider, source_url):
        return []
    soup = BeautifulSoup(html, "html.parser")
    product_name = _visible_product_name(soup)
    if not product_name:
        return []
    lines = _visible_text_lines(soup)
    price = _visible_offer_price(lines, product_name)
    if price is None:
        return []
    return [
        {
            "name": product_name,
            "url": source_url,
            "unit_price": price,
            "currency": "RUB",
            "availability": _visible_availability(lines),
            "status": "candidate",
            "source_query": query_text,
            "source_kind": source_kind,
            "note": f"{_catalog_provider_label(provider)} catalog visible offer from {source_url}.",
            "provider": provider,
        }
    ]


def _same_site_anchor_urls(html: str, source_url: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    soup = BeautifulSoup(html, "html.parser")
    source_key = source_url.casefold()
    for anchor in soup.find_all("a", href=True):
        href = _text(anchor.get("href"))
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        url = urldefrag(urljoin(source_url, href))[0]
        if not _is_public_product_page_url(url) or not _is_same_public_site(source_url, url):
            continue
        if url.casefold() == source_key:
            continue
        _append_unique_url(urls, seen, url)
    return urls


def _visible_product_name(soup: BeautifulSoup) -> str | None:
    heading = soup.find("h1")
    if not heading:
        return None
    return _text(heading.get_text(" ", strip=True))


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
