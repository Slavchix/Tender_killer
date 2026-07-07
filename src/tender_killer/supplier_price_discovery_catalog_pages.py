from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from tender_killer.supplier_officemag_parser import _officemag_hidden_product_page_urls
from tender_killer.supplier_price_discovery_utils import _append_unique_url
from tender_killer.supplier_price_discovery_utils import _text
from tender_killer.supplier_schema_org_parser import _schema_product_page_urls
from tender_killer.supplier_visible_offer_parser import _same_site_anchor_urls


def _catalog_product_page_urls(html: str, source_url: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for product_url in _officemag_hidden_product_page_urls(html, source_url):
        _append_unique_url(urls, seen, product_url)
    for product_url in _schema_product_page_urls(html, source_url):
        _append_unique_url(urls, seen, product_url)
    for product_url in _same_site_anchor_urls(html, source_url):
        _append_unique_url(urls, seen, product_url)
    return urls


def _catalog_fallback_page_urls(html: str, source_url: str, provider: str) -> list[str]:
    provider_key = provider.casefold()
    if provider_key != "officemag":
        return []
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    seen: set[str] = set()
    for node in soup.select('input[name="SECTION"][value]'):
        section = _text(node.get("value"))
        if not section or not section.isdigit() or int(section) <= 0:
            continue
        _append_unique_url(urls, seen, urljoin(source_url, f"/catalog/{section}/"))
    return urls
