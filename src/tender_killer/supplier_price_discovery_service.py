from __future__ import annotations

import os
import json
import re
from pathlib import Path
from typing import Any
from typing import Callable
from urllib.parse import unquote
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.parse import urldefrag

import httpx
from bs4 import BeautifulSoup

from tender_killer import supplier_browser_fetcher
from tender_killer.product_profile_service import ensure_product_profiles
from tender_killer.price_candidate_service import stage_tender_price_candidates
from tender_killer.storage import TenderStore
from tender_killer.supplier_catalog_presets import SUPPLIER_CATALOG_PRESETS
from tender_killer.supplier_catalog_health_service import http_error_kind
from tender_killer.supplier_catalog_health_service import response_body_preview
from tender_killer.supplier_discovery_service import stage_profile_supplier_candidates
from tender_killer.supplier_product_matcher import supplier_product_name_matches_query
from tender_killer.supplier_search_service import build_supplier_search_queries
from tender_killer.supplier_search_service import prepare_profile_supplier_search


SCHEMA_ORG_PRODUCT_PROVIDER = "schema_org_product"
CATALOG_SEARCH_LINK_KIND = "catalog_search"
MANUAL_PRODUCT_LINK_KIND = "manual_product_url"
BUILT_IN_CATALOG_PROVIDERS = tuple(str(preset["provider"]) for preset in SUPPLIER_CATALOG_PRESETS)
BUILT_IN_CATALOG_PROVIDER_SET = {provider.casefold() for provider in BUILT_IN_CATALOG_PROVIDERS}
SEARCH_ENGINE_HOSTS = ("google.", "yandex.")
FetchText = Callable[[str], str]
ProgressCallback = Callable[[dict[str, Any]], None]
VISIBLE_PRICE_RE = re.compile(r"(?<!\d)(\d[\d\s\u00a0\u202f]*(?:[,.]\d{1,2})?)\s*(?:₽|руб\.?)", re.IGNORECASE)
NUMBER_SPACE_RE = re.compile(r"[\s\u00a0\u202f]+")
CATALOG_TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)
CATALOG_QUERY_STOP_WORDS = {
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
NO_SUPPLIER_CANDIDATES_MESSAGE = "\u041d\u043e\u0432\u044b\u0445 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u043e\u0432 \u043f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u043e\u0432 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043e."
PREPARE_SUPPLIER_SEARCH_MESSAGE = "\u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u043f\u043e\u0434\u0433\u043e\u0442\u043e\u0432\u044c \u043f\u043e\u0438\u0441\u043a \u043f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u043e\u0432."
DEFAULT_TENDER_PRICE_DISCOVERY_MAX_POSITIONS = 50
DEFAULT_CATALOG_MAX_PRODUCT_PAGES = 1
DEFAULT_PUBLIC_FETCH_TIMEOUT_SECONDS = 5.0


def _positive_env_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return value if value > 0 else default


def _positive_env_float(name: str, default: float) -> float:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        value = float(raw_value)
    except ValueError:
        return default
    return value if value > 0 else default


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
            if _is_builtin_catalog_search_link(link):
                diagnostics["links_skipped"] += 1
                continue
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


class ProviderCatalogCollector:
    def __init__(self, catalog_provider: str, fetch_text: FetchText | None = None, max_product_pages: int = 5) -> None:
        self.catalog_provider = str(catalog_provider).casefold()
        self.provider = f"catalog_{self.catalog_provider}"
        self.fetch_text = fetch_text or (lambda url: _fetch_catalog_text(url, self.catalog_provider))
        self.max_product_pages = max(0, int(max_product_pages))

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
            if not url or not _is_catalog_search_link_for_provider(link, self.catalog_provider):
                diagnostics["links_skipped"] += 1
                continue
            if not _is_public_product_page_url(url):
                diagnostics["links_skipped"] += 1
                continue
            try:
                html = self.fetch_text(url)
            except httpx.HTTPError as exc:
                diagnostics["errors"].append(str(exc))
                continue
            diagnostics["pages_fetched"] += 1

            page_candidates = self._schema_candidates(html, url, query_text, source_kind)
            diagnostics["candidates_found"] += len(page_candidates)
            candidates.extend(page_candidates)

            fetched_urls = {url.casefold()}
            candidate_urls = {
                candidate_url.casefold()
                for candidate in page_candidates
                if (candidate_url := _text(candidate.get("url")))
            }
            followed_pages = 0
            for product_url in _catalog_product_page_urls(html, url):
                if followed_pages >= self.max_product_pages:
                    break
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
                followed_pages += 1
                diagnostics["pages_fetched"] += 1
                product_candidates = self._schema_candidates(product_html, product_url, query_text, source_kind)
                diagnostics["candidates_found"] += len(product_candidates)
                candidates.extend(product_candidates)
        return {"candidates": candidates, "diagnostics": diagnostics}

    def _schema_candidates(
        self,
        html: str,
        source_url: str,
        query_text: str,
        source_kind: str,
    ) -> list[dict[str, Any]]:
        if self.catalog_provider == "officemag":
            candidates = _officemag_visible_candidates(html, source_url, query_text, source_kind)
            if candidates:
                return candidates
        candidates = _schema_org_candidates(
            html,
            source_url,
            query_text,
            source_kind,
            provider=self.catalog_provider,
            note_prefix=f"{_catalog_provider_label(self.catalog_provider)} catalog offer",
        )
        if candidates:
            return candidates
        return _provider_visible_offer_candidates(
            html,
            source_url,
            query_text,
            source_kind,
            self.catalog_provider,
        )


def default_price_collectors(fetch_text: FetchText | None = None) -> list[Any]:
    max_product_pages = _positive_env_int(
        "TENDER_KILLER_PRICE_DISCOVERY_MAX_PRODUCT_PAGES",
        DEFAULT_CATALOG_MAX_PRODUCT_PAGES,
    )
    return [
        *[
            ProviderCatalogCollector(provider, fetch_text=fetch_text, max_product_pages=max_product_pages)
            for provider in BUILT_IN_CATALOG_PROVIDERS
        ],
        SchemaOrgProductCollector(fetch_text=fetch_text),
    ]


def run_profile_supplier_price_discovery(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    collectors: list[Any] | None = None,
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = ensure_product_profiles(database_path, source, external_id)

    target = _find_profile(profiles, position_index)
    if target is None:
        raise KeyError(f"Product profile position {position_index} not found.")

    raw_payload = dict(target.get("raw_payload") or {})
    queries = _refreshed_supplier_search_queries(target, raw_payload)
    if not queries:
        raise ValueError("Сначала подготовь поиск поставщиков.")
    supplier_search = dict(raw_payload.get("supplier_search") or {})
    supplier_search["status"] = supplier_search.get("status") or "ready"
    supplier_search["queries"] = queries
    raw_payload["supplier_search"] = supplier_search
    target["raw_payload"] = raw_payload
    store.upsert_product_profiles(source, external_id, profiles)

    existing_keys = _existing_candidate_keys(raw_payload)
    price_collectors = default_price_collectors() if collectors is None else collectors
    return _run_supplier_discovery_with_queries(
        database_path,
        store,
        source,
        external_id,
        profiles,
        target,
        queries,
        price_collectors,
        existing_keys,
    )


def run_tender_supplier_price_discovery(
    database_path: str | Path,
    source: str,
    external_id: str,
    collectors: list[Any] | None = None,
    max_positions: int | None = None,
    progress_callback: ProgressCallback | None = None,
) -> dict[str, Any]:
    profiles = ensure_product_profiles(database_path, source, external_id)
    searchable_profiles = [profile for profile in profiles if int(profile.get("position_index") or 0) > 0]
    price_collectors = default_price_collectors() if collectors is None else collectors
    position_limit = (
        max(1, int(max_positions))
        if max_positions is not None
        else _positive_env_int(
            "TENDER_KILLER_PRICE_DISCOVERY_MAX_POSITIONS",
            DEFAULT_TENDER_PRICE_DISCOVERY_MAX_POSITIONS,
        )
    )
    positions: list[dict[str, Any]] = []
    prepared_count = 0
    no_candidates_count = 0
    error_count = 0
    searched_count = 0
    if progress_callback is not None:
        progress_callback(
            {
                "status": "running",
                "total_profiles": len(profiles),
                "searched_count": 0,
                "limited_count": len(searchable_profiles),
                "partial": bool(searchable_profiles),
                "positions": [],
            }
        )

    for profile in searchable_profiles:
        position_index = int(profile.get("position_index") or 0)
        if searched_count >= position_limit:
            positions.append({"position_index": position_index, "status": "deferred", "staged_count": 0})
            if progress_callback is not None:
                progress_callback(
                    {
                        "total_profiles": len(profiles),
                        "searched_count": searched_count,
                        "limited_count": max(0, len(searchable_profiles) - searched_count),
                        "partial": True,
                        "positions": positions,
                    }
                )
            continue
        prepare_profile_supplier_search(database_path, source, external_id, position_index)
        prepared_count += 1
        searched_count += 1
        if progress_callback is not None:
            progress_callback(
                {
                    "total_profiles": len(profiles),
                    "searched_count": searched_count,
                    "limited_count": max(0, len(searchable_profiles) - searched_count),
                    "partial": searched_count < len(searchable_profiles),
                    "positions": [
                        *positions,
                        {"position_index": position_index, "status": "searching", "staged_count": 0},
                    ],
                }
            )
        try:
            result = run_profile_supplier_price_discovery(
                database_path,
                source,
                external_id,
                position_index,
                collectors=price_collectors,
            )
        except ValueError as exc:
            no_candidates_count += 1
            positions.append(
                {
                    "position_index": position_index,
                    "status": "no_candidates",
                    "staged_count": 0,
                    "error": _supplier_discovery_error_message(exc),
                }
            )
            if progress_callback is not None:
                progress_callback(
                    {
                        "total_profiles": len(profiles),
                        "searched_count": searched_count,
                        "limited_count": max(0, len(searchable_profiles) - searched_count),
                        "partial": searched_count < len(searchable_profiles),
                        "positions": positions,
                    }
                )
            continue
        except KeyError as exc:
            error_count += 1
            positions.append(
                {
                    "position_index": position_index,
                    "status": "error",
                    "staged_count": 0,
                    "error": str(exc),
                }
            )
            if progress_callback is not None:
                progress_callback(
                    {
                        "total_profiles": len(profiles),
                        "searched_count": searched_count,
                        "limited_count": max(0, len(searchable_profiles) - searched_count),
                        "partial": searched_count < len(searchable_profiles),
                        "positions": positions,
                    }
                )
            continue
        staged_count = int(result.get("staged_count") or 0)
        positions.append(
            {
                "position_index": position_index,
                "status": "staged" if staged_count else "no_candidates",
                "staged_count": staged_count,
            }
        )
        if progress_callback is not None:
            progress_callback(
                {
                    "total_profiles": len(profiles),
                    "searched_count": searched_count,
                    "limited_count": max(0, len(searchable_profiles) - searched_count),
                    "partial": searched_count < len(searchable_profiles),
                    "positions": positions,
                }
            )

    normalized_stage = stage_tender_price_candidates(database_path, source, external_id)
    updated_profiles = ensure_product_profiles(database_path, source, external_id)
    diagnostics_by_provider = _tender_discovery_diagnostics(updated_profiles)
    result = {
        "ok": True,
        "total_profiles": len(profiles),
        "prepared_count": prepared_count,
        "searched_count": searched_count,
        "limited_count": max(0, len(searchable_profiles) - searched_count),
        "partial": searched_count < len(searchable_profiles),
        "staged_count": normalized_stage["staged_count"],
        "ready_count": normalized_stage["ready_count"],
        "review_count": normalized_stage["review_count"],
        "blocked_count": normalized_stage["blocked_count"],
        "no_candidates_count": no_candidates_count,
        "error_count": error_count,
        "positions": positions,
        "diagnostics_by_provider": diagnostics_by_provider,
    }
    if progress_callback is not None:
        progress_callback(result)
    return result


def run_profile_supplier_url_discovery(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    data: dict[str, Any],
    collectors: list[Any] | None = None,
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = ensure_product_profiles(database_path, source, external_id)

    target = _find_profile(profiles, position_index)
    if target is None:
        raise KeyError(f"Product profile position {position_index} not found.")

    url = _text(data.get("url"))
    if not url or not _is_public_product_page_url(url):
        raise ValueError("Укажи публичную ссылку на страницу товара поставщика.")

    query_text = _text(data.get("source_query")) or _text(target.get("normalized_name")) or _text(target.get("product_name")) or url
    provider = _text(data.get("provider")) or _provider_from_url(url)
    link = {
        "label": _text(data.get("label")) or "Manual supplier URL",
        "url": url,
        "link_kind": MANUAL_PRODUCT_LINK_KIND,
    }
    if provider:
        link["provider"] = provider
    queries = [
        {
            "query": query_text,
            "kind": MANUAL_PRODUCT_LINK_KIND,
            "priority": 1,
            "quick_links": [link],
        }
    ]
    raw_payload = dict(target.get("raw_payload") or {})
    existing_keys = _existing_candidate_keys(raw_payload)
    price_collectors = default_price_collectors() if collectors is None else collectors
    return _run_supplier_discovery_with_queries(
        database_path,
        store,
        source,
        external_id,
        profiles,
        target,
        queries,
        price_collectors,
        existing_keys,
    )


def _run_supplier_discovery_with_queries(
    database_path: str | Path,
    store: TenderStore,
    source: str,
    external_id: str,
    profiles: list[dict[str, Any]],
    target: dict[str, Any],
    queries: list[dict[str, Any]],
    price_collectors: list[Any],
    existing_keys: set[tuple[str, str]],
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    diagnostics_by_provider: dict[str, dict[str, Any]] = {}
    for query in queries:
        for collector in price_collectors:
            result = collector.collect_with_diagnostics(query)
            accepted_candidates: list[dict[str, Any]] = []
            rejected_by_intent = 0
            for candidate in result["candidates"]:
                if not _candidate_matches_profile_intent(target, candidate):
                    rejected_by_intent += 1
                    continue
                key = _candidate_key(candidate)
                if key in existing_keys:
                    continue
                existing_keys.add(key)
                accepted_candidates.append(_candidate_with_profile_match(candidate))
            diagnostics = _with_intent_rejection_diagnostics(result["diagnostics"], rejected_by_intent)
            if _diagnostics_has_signal(diagnostics):
                _merge_diagnostics(diagnostics_by_provider, diagnostics)
            candidates.extend(accepted_candidates)
    if not candidates:
        if diagnostics_by_provider:
            _record_supplier_discovery_diagnostics(
                store,
                source,
                external_id,
                profiles,
                target,
                list(diagnostics_by_provider.values()),
            )
        raise ValueError(NO_SUPPLIER_CANDIDATES_MESSAGE)

    return stage_profile_supplier_candidates(
        database_path,
        source,
        external_id,
        int(target.get("position_index") or 0),
        candidates,
        collector_diagnostics=list(diagnostics_by_provider.values()),
    )


def _candidate_matches_profile_intent(profile: dict[str, Any], candidate: dict[str, Any]) -> bool:
    product_name = _text(candidate.get("name") or candidate.get("product_name"))
    profile_text = _profile_intent_text(profile, candidate)
    if not product_name or not profile_text:
        return True
    return _catalog_product_name_matches_query(product_name, profile_text)


def _profile_intent_text(profile: dict[str, Any], candidate: dict[str, Any]) -> str:
    parts: list[str] = []
    for field in ("product_name", "normalized_name"):
        value = _text(profile.get(field))
        if value:
            parts.append(value)
    for phrase in _text_items(profile.get("search_phrases")):
        parts.append(phrase)
    source_query = _text(candidate.get("source_query"))
    if source_query:
        parts.append(source_query)
    return " ".join(parts)


def _candidate_with_profile_match(candidate: dict[str, Any]) -> dict[str, Any]:
    updated = dict(candidate)
    reasons = _text_items(candidate.get("match_reasons"))
    if "profile_intent_match" not in reasons:
        reasons.append("profile_intent_match")
    updated["match_reasons"] = reasons
    return updated


def _with_intent_rejection_diagnostics(diagnostics: dict[str, Any], rejected_count: int) -> dict[str, Any]:
    if rejected_count <= 0:
        return diagnostics
    updated = dict(diagnostics)
    updated["candidates_rejected_by_intent"] = int(updated.get("candidates_rejected_by_intent") or 0) + rejected_count
    return updated


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


def _refreshed_supplier_search_queries(profile: dict[str, Any], raw_payload: dict[str, Any]) -> list[dict[str, Any]]:
    existing_queries = _supplier_search_queries(raw_payload.get("supplier_search"))
    fresh_queries = build_supplier_search_queries(profile)
    if not existing_queries:
        return fresh_queries
    return _unique_supplier_search_queries([*existing_queries, *fresh_queries])


def _unique_supplier_search_queries(queries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for query in queries:
        query_text = _text(query.get("query"))
        if not query_text:
            continue
        key = query_text.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(dict(query))
    return unique


def _record_supplier_discovery_diagnostics(
    store: TenderStore,
    source: str,
    external_id: str,
    profiles: list[dict[str, Any]],
    target: dict[str, Any],
    collector_diagnostics: list[dict[str, Any]],
) -> None:
    raw_payload = dict(target.get("raw_payload") or {})
    discovery = dict(raw_payload.get("supplier_discovery") or {})
    candidates = _dict_items(discovery.get("candidates"))
    discovery["status"] = discovery.get("status") or "no_candidates"
    if not candidates:
        discovery["status"] = "no_candidates"
    discovery["collector_diagnostics"] = collector_diagnostics
    discovery["candidates"] = candidates
    raw_payload["supplier_discovery"] = discovery
    target["raw_payload"] = raw_payload
    store.upsert_product_profiles(source, external_id, profiles)


def _tender_discovery_diagnostics(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    diagnostics_by_provider: dict[str, dict[str, Any]] = {}
    for profile in profiles:
        raw_payload = profile.get("raw_payload") if isinstance(profile.get("raw_payload"), dict) else {}
        discovery = raw_payload.get("supplier_discovery") if isinstance(raw_payload.get("supplier_discovery"), dict) else {}
        diagnostics = discovery.get("collector_diagnostics") if isinstance(discovery.get("collector_diagnostics"), list) else []
        for item in diagnostics:
            if isinstance(item, dict) and _diagnostics_has_signal(item):
                _merge_diagnostics(diagnostics_by_provider, item)
    return list(diagnostics_by_provider.values())


def _supplier_discovery_error_message(exc: ValueError) -> str:
    message = str(exc)
    lowered = message.casefold()
    if NO_SUPPLIER_CANDIDATES_MESSAGE.casefold() in lowered or "new candidates" in lowered:
        return NO_SUPPLIER_CANDIDATES_MESSAGE
    if PREPARE_SUPPLIER_SEARCH_MESSAGE.casefold() in lowered or "prepare" in lowered:
        return PREPARE_SUPPLIER_SEARCH_MESSAGE
    return message


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
    for field in (
        "queries_seen",
        "links_seen",
        "links_skipped",
        "pages_fetched",
        "candidates_found",
        "candidates_rejected_by_intent",
    ):
        value = int(item.get(field) or 0)
        if field not in target and value == 0:
            continue
        target[field] = int(target.get(field) or 0) + value
    target["errors"].extend([str(error) for error in item.get("errors") or []])


def _diagnostics_has_signal(item: dict[str, Any]) -> bool:
    return bool(
        item.get("pages_fetched")
        or item.get("candidates_found")
        or item.get("candidates_rejected_by_intent")
        or item.get("errors")
    )


def _quick_links(query: dict[str, Any]) -> list[dict[str, Any]]:
    links = query.get("quick_links")
    if not isinstance(links, list):
        return []
    return [dict(link) for link in links if isinstance(link, dict) and _text(link.get("url"))]


def _schema_org_candidates(
    html: str,
    source_url: str,
    query_text: str,
    source_kind: str,
    *,
    provider: str = SCHEMA_ORG_PRODUCT_PROVIDER,
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


def _catalog_product_page_urls(html: str, source_url: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for product_url in _schema_product_page_urls(html, source_url):
        _append_unique_url(urls, seen, product_url)
    for product_url in _same_site_anchor_urls(html, source_url):
        _append_unique_url(urls, seen, product_url)
    return urls


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
    for item in soup.select("li.listItem"):
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
    if not _catalog_product_name_matches_query(product_name, query_text):
        return None
    price_breaks = _officemag_price_breaks(scope)
    prices = [item["price"] for item in price_breaks]
    if price := _officemag_primary_price(scope):
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


def _officemag_product_name(scope: BeautifulSoup) -> str | None:
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
    price_node = scope.select_one('.Product__price[itemprop="price"][content]')
    if price_node:
        return _number(price_node.get("content"))
    sum_node = scope.select_one(".js-productSum[data-price]")
    if sum_node:
        return _number(sum_node.get("data-price"))
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


def _catalog_product_name_matches_query(product_name: str, query_text: str) -> bool:
    return supplier_product_name_matches_query(query_text, product_name)


def _catalog_token_stems(text: str, *, remove_stop_words: bool) -> set[str]:
    stems: set[str] = set()
    for token in CATALOG_TOKEN_RE.findall(str(text or "").casefold()):
        if token.isdigit() or len(token) < 4:
            continue
        if remove_stop_words and token in CATALOG_QUERY_STOP_WORDS:
            continue
        stems.add(token[:5])
    return stems


def _positive_number(value: Any) -> int | None:
    number = _number(value)
    if number is None or number <= 0:
        return None
    return int(number)


def _format_decimal(value: Any) -> str:
    number = _number(value)
    if number is None:
        return ""
    return f"{number:.2f}".rstrip("0").rstrip(".")


def _is_provider_product_detail_url(provider: str, url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.casefold()
    provider_key = provider.casefold()
    if provider_key == "officemag":
        return "/catalog/goods/" in path
    if provider_key == "komus":
        return "/p/" in path
    if provider_key == "petrovich":
        return path.startswith("/product/")
    if provider_key == "vseinstrumenti":
        return "/product/" in path
    return False


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
        timeout=_positive_env_float(
            "TENDER_KILLER_PRICE_DISCOVERY_HTTP_TIMEOUT_SECONDS",
            DEFAULT_PUBLIC_FETCH_TIMEOUT_SECONDS,
        ),
        trust_env=False,
        headers={"User-Agent": "TenderKiller/0.1 public price discovery"},
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        kind = http_error_kind(int(response.status_code))
        preview = response_body_preview(response.text)
        message = f"{kind} HTTP {response.status_code} from {url}"
        if preview:
            message = f"{message}: {preview}"
        raise httpx.HTTPStatusError(message, request=exc.request, response=exc.response) from exc
    return response.text


def _fetch_catalog_text(url: str, provider: str) -> str:
    try:
        return _fetch_public_text(url)
    except httpx.HTTPError as exc:
        if not supplier_browser_fetcher.is_enabled_for_provider(provider):
            raise
        try:
            return supplier_browser_fetcher.fetch_text(url, provider=provider)
        except supplier_browser_fetcher.BrowserFetchError as browser_exc:
            raise httpx.HTTPError(f"{exc}; browser_fetch_error: {browser_exc}") from browser_exc


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


def _is_builtin_catalog_search_link(link: dict[str, Any]) -> bool:
    provider = _text(link.get("provider"))
    return (
        _text(link.get("link_kind")) in {CATALOG_SEARCH_LINK_KIND, MANUAL_PRODUCT_LINK_KIND}
        and provider is not None
        and provider.casefold() in BUILT_IN_CATALOG_PROVIDER_SET
    )


def _is_catalog_search_link_for_provider(link: dict[str, Any], provider: str) -> bool:
    link_provider = _text(link.get("provider"))
    return (
        _text(link.get("link_kind")) in {CATALOG_SEARCH_LINK_KIND, MANUAL_PRODUCT_LINK_KIND}
        and link_provider is not None
        and link_provider.casefold() == provider.casefold()
    )


def _provider_from_url(url: str) -> str | None:
    host = urlparse(url).netloc.casefold()
    if "officemag.ru" in host:
        return "officemag"
    if "komus.ru" in host:
        return "komus"
    if "petrovich.ru" in host:
        return "petrovich"
    if "vseinstrumenti.ru" in host:
        return "vseinstrumenti"
    return None


def _catalog_provider_label(provider: str) -> str:
    labels = {
        "officemag": "OfficeMag",
        "komus": "Komus",
        "petrovich": "Petrovich",
        "vseinstrumenti": "Vseinstrumenti",
    }
    return labels.get(provider.casefold(), provider.replace("_", " ").title())


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


def _text_items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = _text(item)
        if text:
            items.append(text)
    return items


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
        number = float(NUMBER_SPACE_RE.sub("", str(value)).replace(",", "."))
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None
