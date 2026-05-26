from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from typing import Callable
from urllib.parse import unquote
from urllib.parse import urlparse
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from tender_killer.storage import TenderStore
from tender_killer.supplier_discovery_service import stage_profile_supplier_candidates


SCHEMA_ORG_PRODUCT_PROVIDER = "schema_org_product"
SEARCH_ENGINE_HOSTS = ("google.", "yandex.")
FetchText = Callable[[str], str]


class SchemaOrgProductCollector:
    provider = SCHEMA_ORG_PRODUCT_PROVIDER

    def __init__(self, fetch_text: FetchText | None = None) -> None:
        self.fetch_text = fetch_text or _fetch_public_text

    def collect(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        return self.collect_with_diagnostics(query)["candidates"]

    def collect_with_diagnostics(self, query: dict[str, Any]) -> dict[str, Any]:
        diagnostics = _collector_diagnostics(self.provider)
        query_text = _text(query.get("query"))
        if not query_text:
            return {"candidates": [], "diagnostics": diagnostics}
        diagnostics["queries_seen"] = 1
        source_kind = _text(query.get("kind")) or "supplier_search"
        candidates: list[dict[str, Any]] = []
        for link in _quick_links(query):
            diagnostics["links_seen"] += 1
            url = _text(link.get("url"))
            if not url or not _is_public_product_page_url(url):
                diagnostics["links_skipped"] += 1
                continue
            try:
                html = self.fetch_text(url)
            except httpx.HTTPError as exc:
                diagnostics["errors"].append(str(exc))
                continue
            diagnostics["pages_fetched"] += 1
            page_candidates = _schema_org_candidates(html, url, query_text, source_kind)
            diagnostics["candidates_found"] += len(page_candidates)
            candidates.extend(page_candidates)
            fetched_urls = {url.casefold()}
            candidate_urls = {
                candidate_url.casefold()
                for candidate in page_candidates
                if (candidate_url := _text(candidate.get("url")))
            }
            for product_url in _schema_product_page_urls(html, url):
                product_url_key = product_url.casefold()
                if product_url_key in fetched_urls or product_url_key in candidate_urls:
                    continue
                if not _is_public_product_page_url(product_url) or not _is_same_public_site(url, product_url):
                    diagnostics["links_skipped"] += 1
                    continue
                try:
                    product_html = self.fetch_text(product_url)
                except httpx.HTTPError as exc:
                    diagnostics["errors"].append(str(exc))
                    continue
                fetched_urls.add(product_url_key)
                diagnostics["pages_fetched"] += 1
                product_candidates = _schema_org_candidates(product_html, product_url, query_text, source_kind)
                diagnostics["candidates_found"] += len(product_candidates)
                candidates.extend(product_candidates)
        return {"candidates": candidates, "diagnostics": diagnostics}


def run_profile_supplier_price_discovery(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    collectors: list[SchemaOrgProductCollector] | None = None,
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = store.get_product_profiles(source, external_id)
    if not profiles:
        raise KeyError(f"Product profiles for {source}/{external_id} not found.")

    target = _find_profile(profiles, position_index)
    if target is None:
        raise KeyError(f"Product profile position {position_index} not found.")

    raw_payload = dict(target.get("raw_payload") or {})
    queries = _supplier_search_queries(raw_payload.get("supplier_search"))
    if not queries:
        raise ValueError("Сначала подготовь поиск поставщиков.")

    existing_keys = _existing_candidate_keys(raw_payload)
    price_collectors = collectors or [SchemaOrgProductCollector()]
    candidates: list[dict[str, Any]] = []
    diagnostics_by_provider: dict[str, dict[str, Any]] = {}
    for query in queries:
        for collector in price_collectors:
            result = collector.collect_with_diagnostics(query)
            _merge_diagnostics(diagnostics_by_provider, result["diagnostics"])
            for candidate in result["candidates"]:
                key = _candidate_key(candidate)
                if key in existing_keys:
                    continue
                existing_keys.add(key)
                candidates.append(candidate)
    if not candidates:
        raise ValueError("Новых кандидатов поставщиков не найдено.")

    return stage_profile_supplier_candidates(
        database_path,
        source,
        external_id,
        position_index,
        candidates,
        collector_diagnostics=list(diagnostics_by_provider.values()),
    )


def _find_profile(profiles: list[dict[str, Any]], position_index: int) -> dict[str, Any] | None:
    for profile in profiles:
        if int(profile.get("position_index") or 0) == position_index:
            return profile
    return None


def _supplier_search_queries(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, dict):
        return []
    queries = value.get("queries")
    if not isinstance(queries, list):
        return []
    return [dict(item) for item in queries if isinstance(item, dict)]


def _collector_diagnostics(provider: str) -> dict[str, Any]:
    return {
        "provider": provider,
        "queries_seen": 0,
        "links_seen": 0,
        "links_skipped": 0,
        "pages_fetched": 0,
        "candidates_found": 0,
        "errors": [],
    }


def _merge_diagnostics(current: dict[str, dict[str, Any]], item: dict[str, Any]) -> None:
    provider = str(item.get("provider") or "unknown")
    target = current.setdefault(provider, _collector_diagnostics(provider))
    for field in ("queries_seen", "links_seen", "links_skipped", "pages_fetched", "candidates_found"):
        target[field] += int(item.get(field) or 0)
    target["errors"].extend([str(error) for error in item.get("errors") or []])


def _quick_links(query: dict[str, Any]) -> list[dict[str, Any]]:
    links = query.get("quick_links")
    if not isinstance(links, list):
        return []
    return [dict(link) for link in links if isinstance(link, dict) and _text(link.get("url"))]


def _schema_org_candidates(html: str, source_url: str, query_text: str, source_kind: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        data = _json(script.string or script.get_text())
        for product in _schema_products(data):
            product_name = _text(product.get("name"))
            if not product_name:
                continue
            product_url = _text(product.get("url")) or source_url
            for offer in _schema_offers(product):
                price = _schema_offer_price(offer)
                if price is None:
                    continue
                offer_url = _text(offer.get("url")) or product_url
                candidate = {
                    "name": product_name,
                    "url": offer_url,
                    "unit_price": price,
                    "availability": _schema_availability(offer.get("availability")),
                    "status": "candidate",
                    "source_query": query_text,
                    "source_kind": source_kind,
                    "note": f"Schema.org product offer from {source_url}.",
                    "provider": SCHEMA_ORG_PRODUCT_PROVIDER,
                }
                if currency := _schema_offer_currency(offer):
                    candidate["currency"] = currency
                if vat_mode := _schema_offer_vat_mode(offer):
                    candidate["vat_mode"] = vat_mode
                if delivery_note := _schema_delivery_note(offer):
                    candidate["delivery_note"] = delivery_note
                candidates.append(candidate)
    return candidates


def _json(value: str | None) -> Any:
    text = _text(value)
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _schema_products(value: Any) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    for item in _walk_schema(value):
        if isinstance(item, dict) and _schema_type_matches(item.get("@type"), "Product"):
            products.append(item)
    return products


def _walk_schema(value: Any) -> list[Any]:
    items: list[Any] = []
    if isinstance(value, list):
        for item in value:
            items.extend(_walk_schema(item))
        return items
    if isinstance(value, dict):
        items.append(value)
        for nested in value.values():
            items.extend(_walk_schema(nested))
    return items


def _schema_type_matches(value: Any, expected: str) -> bool:
    if isinstance(value, list):
        return any(_schema_type_matches(item, expected) for item in value)
    return str(value or "").casefold() == expected.casefold()


def _schema_offers(product: dict[str, Any]) -> list[dict[str, Any]]:
    offers = product.get("offers")
    if isinstance(offers, dict):
        return [offers]
    if isinstance(offers, list):
        return [dict(item) for item in offers if isinstance(item, dict)]
    return []


def _schema_offer_price(offer: dict[str, Any]) -> float | None:
    price = _number(offer.get("price") or offer.get("lowPrice"))
    if price is not None:
        return price
    for specification in _schema_price_specifications(offer):
        price = _number(specification.get("price") or specification.get("lowPrice"))
        if price is not None:
            return price
    return None


def _schema_offer_currency(offer: dict[str, Any]) -> str | None:
    currency = _text(offer.get("priceCurrency"))
    if currency:
        return currency.upper()
    for specification in _schema_price_specifications(offer):
        currency = _text(specification.get("priceCurrency"))
        if currency:
            return currency.upper()
    return None


def _schema_offer_vat_mode(offer: dict[str, Any]) -> str | None:
    for specification in _schema_price_specifications(offer):
        value = specification.get("valueAddedTaxIncluded")
        if value is True:
            return "vat_included"
        if value is False:
            return "vat_excluded"
    return None


def _schema_price_specifications(offer: dict[str, Any]) -> list[dict[str, Any]]:
    specifications = offer.get("priceSpecification")
    if isinstance(specifications, dict):
        return [specifications]
    if isinstance(specifications, list):
        return [dict(item) for item in specifications if isinstance(item, dict)]
    return []


def _schema_delivery_note(offer: dict[str, Any]) -> str | None:
    details = offer.get("shippingDetails")
    candidates = [details] if isinstance(details, dict) else details if isinstance(details, list) else []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        note = _text(item.get("description")) or _text(item.get("name"))
        if note:
            return note
    return None


def _schema_product_page_urls(html: str, source_url: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        data = _json(script.string or script.get_text())
        for product in _schema_products(data):
            if product_url := _text(product.get("url")):
                _append_unique_url(urls, seen, urljoin(source_url, product_url))
        for item in _walk_schema(data):
            if isinstance(item, dict) and _schema_type_matches(item.get("@type"), "ListItem"):
                item_value = item.get("item")
                if isinstance(item_value, str):
                    _append_unique_url(urls, seen, urljoin(source_url, item_value))
                if item_url := _text(item.get("url")):
                    _append_unique_url(urls, seen, urljoin(source_url, item_url))
    return urls


def _append_unique_url(urls: list[str], seen: set[str], url: str) -> None:
    key = url.casefold()
    if key in seen:
        return
    seen.add(key)
    urls.append(url)


def _schema_availability(value: Any) -> str:
    availability = str(value or "").casefold()
    if "instock" in availability:
        return "in_stock"
    if "outofstock" in availability or "soldout" in availability:
        return "not_available"
    if "preorder" in availability or "backorder" in availability:
        return "on_request"
    return "unknown"


def _fetch_public_text(url: str) -> str:
    if url.startswith("data:text/html,"):
        return unquote(url.removeprefix("data:text/html,"))
    response = httpx.get(
        url,
        follow_redirects=True,
        timeout=10.0,
        headers={"User-Agent": "TenderKiller/0.1 public price discovery"},
    )
    response.raise_for_status()
    return response.text


def _is_public_product_page_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme == "data":
        return True
    if parsed.scheme not in {"http", "https"}:
        return False
    host = parsed.netloc.casefold()
    return not any(marker in host for marker in SEARCH_ENGINE_HOSTS)


def _is_same_public_site(source_url: str, target_url: str) -> bool:
    source = urlparse(source_url)
    target = urlparse(target_url)
    if source.scheme == "data" or target.scheme == "data":
        return True
    return source.netloc.casefold() == target.netloc.casefold()


def _existing_candidate_keys(raw_payload: dict[str, Any]) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    discovery = raw_payload.get("supplier_discovery")
    if isinstance(discovery, dict):
        for candidate in _dict_items(discovery.get("candidates")):
            keys.add(_candidate_key(candidate))
    for option in _dict_items(raw_payload.get("supplier_options")):
        keys.add(_candidate_key(option))
    return keys


def _dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _candidate_key(candidate: dict[str, Any]) -> tuple[str, str]:
    url = _text(candidate.get("url"))
    source_query = _text(candidate.get("source_query"))
    return (
        (_text(candidate.get("provider")) or "").casefold(),
        (url or source_query or "").casefold(),
    )


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
