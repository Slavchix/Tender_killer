from __future__ import annotations

import json
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from tender_killer.supplier_price_discovery_utils import _append_unique_url
from tender_killer.supplier_price_discovery_utils import _number
from tender_killer.supplier_price_discovery_utils import _text


def _schema_org_candidates(
    html: str,
    source_url: str,
    query_text: str,
    source_kind: str,
    *,
    provider: str = "schema_org_product",
    note_prefix: str = "Schema.org product offer",
) -> list[dict[str, Any]]:
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
                    "note": f"{note_prefix} from {source_url}.",
                    "provider": provider,
                }
                if currency := _schema_offer_currency(offer):
                    candidate["currency"] = currency
                if vat_mode := _schema_offer_vat_mode(offer):
                    candidate["vat_mode"] = vat_mode
                if delivery_note := _schema_delivery_note(offer):
                    candidate["delivery_note"] = delivery_note
                if brand := _schema_brand_name(product):
                    candidate["brand"] = brand
                image_urls = _schema_image_urls(product)
                if image_urls:
                    candidate["image_url"] = image_urls[0]
                    candidate["image_urls"] = image_urls
                if product_attributes := _schema_product_attributes(product):
                    candidate["product_attributes"] = product_attributes
                candidates.append(candidate)
    return candidates


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


def _schema_brand_name(product: dict[str, Any]) -> str | None:
    brand = product.get("brand")
    if isinstance(brand, dict):
        return _text(brand.get("name")) or _text(brand.get("alternateName"))
    if isinstance(brand, list):
        for item in brand:
            if isinstance(item, dict):
                if name := _text(item.get("name")) or _text(item.get("alternateName")):
                    return name
            elif name := _text(item):
                return name
        return None
    return _text(brand)


def _schema_image_urls(product: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    def append(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                append(item)
            return
        if isinstance(value, dict):
            append(value.get("url") or value.get("contentUrl"))
            return
        url = _text(value)
        if not url:
            return
        key = url.casefold()
        if key in seen:
            return
        seen.add(key)
        urls.append(url)

    append(product.get("image"))
    return urls


def _schema_product_attributes(product: dict[str, Any]) -> list[dict[str, str]]:
    raw_properties = product.get("additionalProperty")
    properties = raw_properties if isinstance(raw_properties, list) else [raw_properties]
    attributes: list[dict[str, str]] = []
    for item in properties:
        if not isinstance(item, dict):
            continue
        name = _text(item.get("name"))
        value = _schema_property_text(item.get("value"))
        if not name or not value:
            continue
        attributes.append({"name": name, "value": value})
    return attributes


def _schema_property_text(value: Any) -> str | None:
    if isinstance(value, dict):
        return _text(value.get("value")) or _text(value.get("name"))
    if isinstance(value, list):
        parts = [_schema_property_text(item) for item in value]
        joined = ", ".join(part for part in parts if part)
        return joined or None
    return _text(value)


def _schema_availability(value: Any) -> str:
    availability = str(value or "").casefold()
    if "instock" in availability:
        return "in_stock"
    if "outofstock" in availability or "soldout" in availability:
        return "not_available"
    if "preorder" in availability or "backorder" in availability:
        return "on_request"
    return "unknown"
