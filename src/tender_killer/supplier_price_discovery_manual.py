from __future__ import annotations

from typing import Any

from tender_killer.supplier_price_discovery_diagnostics import MANUAL_PRODUCT_LINK_KIND
from tender_killer.supplier_price_discovery_queries import _quick_links
from tender_killer.supplier_price_discovery_utils import _candidate_key
from tender_killer.supplier_price_discovery_utils import _catalog_provider_label
from tender_killer.supplier_price_discovery_utils import _dict_items
from tender_killer.supplier_price_discovery_utils import _provider_from_url
from tender_killer.supplier_price_discovery_utils import _text


def _manual_product_link_review_candidates(
    profile: dict[str, Any],
    queries: list[dict[str, Any]],
    existing_keys: set[tuple[str, str]],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for query in queries:
        if _text(query.get("kind")) != MANUAL_PRODUCT_LINK_KIND:
            continue
        source_query = _text(query.get("query")) or _text(profile.get("normalized_name")) or _text(profile.get("product_name")) or ""
        for link in _quick_links(query):
            if _text(link.get("link_kind")) != MANUAL_PRODUCT_LINK_KIND:
                continue
            url = _text(link.get("url"))
            if not url:
                continue
            provider = _text(link.get("provider")) or _provider_from_url(url) or "manual_supplier_url"
            candidate = {
                "name": _text(profile.get("product_name")) or source_query or _text(link.get("label")) or "Manual supplier URL",
                "url": url,
                "source_url": url,
                "provider": provider,
                "supplier_name": _catalog_provider_label(provider),
                "source_query": source_query,
                "source_kind": MANUAL_PRODUCT_LINK_KIND,
                "confidence": "needs_review",
                "confidence_reasons": ["manual_product_url", "price_not_read"],
                "match_reasons": ["manual_product_url"],
                "note": "Manual URL saved; price was not read automatically.",
                "manual_price_required": True,
            }
            key = _candidate_key(candidate)
            if key in existing_keys:
                continue
            existing_keys.add(key)
            candidates.append(candidate)
    return candidates


def _existing_candidate_keys(raw_payload: dict[str, Any]) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    discovery = raw_payload.get("supplier_discovery")
    if isinstance(discovery, dict):
        for candidate in _dict_items(discovery.get("candidates")):
            keys.add(_candidate_key(candidate))
    for option in _dict_items(raw_payload.get("supplier_options")):
        keys.add(_candidate_key(option))
    return keys
