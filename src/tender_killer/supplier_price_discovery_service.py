from __future__ import annotations

import os
import json
import re
from pathlib import Path
from typing import Any
from typing import Callable
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.parse import urldefrag

import httpx
from bs4 import BeautifulSoup

from tender_killer import supplier_browser_fetcher
from tender_killer.product_profile_service import ensure_product_profiles
from tender_killer.price_candidate_service import stage_tender_price_candidates
from tender_killer.storage import TenderStore
from tender_killer.supplier_candidate_contract import normalize_supplier_candidate
from tender_killer.supplier_catalog_fetcher import fetch_catalog_text
from tender_killer.supplier_catalog_fetcher import fetch_public_text
from tender_killer.supplier_catalog_presets import SUPPLIER_CATALOG_PRESETS
from tender_killer.supplier_catalog_presets import supplier_catalog_providers_for_profile
from tender_killer.supplier_discovery_service import stage_profile_supplier_candidates
from tender_killer.supplier_provider_policy import ACTION_BROWSER_FETCH
from tender_killer.supplier_provider_policy import ACTION_PRODUCT_PAGE_FETCH
from tender_killer.supplier_provider_policy import ACTION_PUBLIC_SEARCH_FETCH
from tender_killer.supplier_provider_policy import SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT
from tender_killer.supplier_provider_policy import supplier_fetch_decision
from tender_killer.supplier_product_matcher import supplier_product_name_match_reasons
from tender_killer.supplier_product_matcher import supplier_product_name_mismatch_reasons
from tender_killer.supplier_product_matcher import supplier_product_name_matches_query
from tender_killer.supplier_search_service import build_supplier_search_queries
from tender_killer.supplier_search_service import prepare_profile_supplier_search


SCHEMA_ORG_PRODUCT_PROVIDER = "schema_org_product"
CATALOG_SEARCH_LINK_KIND = "catalog_search"
MANUAL_PRODUCT_LINK_KIND = "manual_product_url"
ACCESS_BLOCKED_ERROR_KIND = "access_blocked"
BUILT_IN_CATALOG_PROVIDERS = tuple(str(preset["provider"]) for preset in SUPPLIER_CATALOG_PRESETS)
BUILT_IN_CATALOG_PROVIDER_SET = {provider.casefold() for provider in BUILT_IN_CATALOG_PROVIDERS}
ACCESS_BLOCKED_STATUS_CODES = {401, 403, 429, 503}
SEARCH_ENGINE_HOSTS = ("google.", "yandex.")
MAX_INTENT_REJECTION_SAMPLES = 5
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
DEFAULT_CATALOG_MAX_PRODUCT_PAGES = 5
DEFAULT_BULK_DISCOVERY_PROFILE_THRESHOLD = 3
DEFAULT_BULK_DISCOVERY_CANDIDATE_LIMIT = 5
DEFAULT_SINGLE_DISCOVERY_CANDIDATE_LIMIT = 12


def _positive_env_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return value if value > 0 else default


class SchemaOrgProductCollector:
    provider = SCHEMA_ORG_PRODUCT_PROVIDER

    def __init__(self, fetch_text: FetchText | None = None) -> None:
        self.fetch_text = fetch_text or _fetch_public_text
        self.tender_position_count: int | None = None

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
            link_action = _fetch_action_for_link(link)
            if not url or not _is_public_product_page_url(url):
                diagnostics["links_skipped"] += 1
                continue
            decision = supplier_fetch_decision(
                url,
                provider=_text(link.get("provider")),
                action=link_action,
                tender_position_count=self.tender_position_count,
            )
            if not decision["allowed"]:
                diagnostics["links_skipped"] += 1
                _mark_policy_skipped(diagnostics, decision["reason"])
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
                if not _is_same_public_site(url, product_url):
                    diagnostics["links_skipped"] += 1
                    continue
                decision = supplier_fetch_decision(
                    product_url,
                    provider=_text(link.get("provider")) or _provider_from_url(product_url),
                    action=link_action,
                    tender_position_count=self.tender_position_count,
                )
                if not decision["allowed"]:
                    diagnostics["links_skipped"] += 1
                    _mark_policy_skipped(diagnostics, decision["reason"])
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
        self.fetch_text = fetch_text
        self.max_product_pages = max(0, int(max_product_pages))
        self.tender_position_count: int | None = None

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
        links = _quick_links(query)
        for link_index, link in enumerate(links):
            diagnostics["links_seen"] += 1
            url = _text(link.get("url"))
            if not url or not _is_catalog_search_link_for_provider(link, self.catalog_provider):
                diagnostics["links_skipped"] += 1
                continue
            link_action = _fetch_action_for_link(link)
            if not self._allow_fetch_url(url, link_action, diagnostics):
                diagnostics["links_skipped"] += 1
                continue
            try:
                html = self._fetch_link_text(url, link_action)
            except httpx.HTTPError as exc:
                if _catalog_access_block_reason_from_error(exc):
                    _mark_catalog_access_blocked(diagnostics, url, error=exc)
                    _skip_remaining_links(diagnostics, links, link_index)
                    break
                diagnostics["errors"].append(str(exc))
                continue
            if self._access_block_reason_from_body(html):
                _mark_catalog_access_blocked(diagnostics, url)
                _skip_remaining_links(diagnostics, links, link_index)
                break
            diagnostics["pages_fetched"] += 1

            raw_page_candidates = self._schema_candidates(html, url, query_text, source_kind)
            page_candidates, rejected_count, rejection_samples = _provider_catalog_candidates_matching_query(
                raw_page_candidates,
                query_text,
            )
            _add_rejected_by_intent(diagnostics, rejected_count, rejection_samples)
            diagnostics["candidates_found"] += len(page_candidates)
            candidates.extend(page_candidates)

            fetched_urls = {url.casefold()}
            candidate_urls = {
                candidate_url.casefold()
                for candidate in page_candidates
                if (candidate_url := _text(candidate.get("url")))
            }
            product_source_pages = [(html, url)]
            blocked = False
            if not page_candidates:
                for fallback_url in _catalog_fallback_page_urls(html, url, self.catalog_provider):
                    fallback_url_key = fallback_url.casefold()
                    if fallback_url_key in fetched_urls:
                        continue
                    if not self._allow_fetch_url(fallback_url, link_action, diagnostics):
                        diagnostics["links_skipped"] += 1
                        continue
                    try:
                        fallback_html = self._fetch_link_text(fallback_url, link_action)
                    except httpx.HTTPError as exc:
                        if _catalog_access_block_reason_from_error(exc):
                            _mark_catalog_access_blocked(diagnostics, fallback_url, error=exc)
                            _skip_remaining_links(diagnostics, links, link_index)
                            blocked = True
                            break
                        diagnostics["errors"].append(str(exc))
                        continue
                    if self._access_block_reason_from_body(fallback_html):
                        _mark_catalog_access_blocked(diagnostics, fallback_url)
                        _skip_remaining_links(diagnostics, links, link_index)
                        blocked = True
                        break
                    fetched_urls.add(fallback_url_key)
                    product_source_pages.append((fallback_html, fallback_url))
                    diagnostics["pages_fetched"] += 1
                    raw_fallback_candidates = self._schema_candidates(
                        fallback_html,
                        fallback_url,
                        query_text,
                        source_kind,
                    )
                    fallback_candidates, rejected_count, rejection_samples = _provider_catalog_candidates_matching_query(
                        raw_fallback_candidates,
                        query_text,
                    )
                    _add_rejected_by_intent(diagnostics, rejected_count, rejection_samples)
                    diagnostics["candidates_found"] += len(fallback_candidates)
                    candidates.extend(fallback_candidates)
                    candidate_urls.update(
                        candidate_url.casefold()
                        for candidate in fallback_candidates
                        if (candidate_url := _text(candidate.get("url")))
                    )
            if blocked:
                break
            followed_pages = 0
            for source_html, source_page_url in product_source_pages:
                for product_url in _catalog_product_page_urls(source_html, source_page_url):
                    if followed_pages >= self.max_product_pages:
                        break
                    product_url_key = product_url.casefold()
                    if product_url_key in fetched_urls or product_url_key in candidate_urls:
                        continue
                    if not _is_provider_product_detail_url(self.catalog_provider, product_url):
                        diagnostics["links_skipped"] += 1
                        continue
                    if not _is_same_public_site(url, product_url):
                        diagnostics["links_skipped"] += 1
                        continue
                    if not self._allow_fetch_url(product_url, link_action, diagnostics):
                        diagnostics["links_skipped"] += 1
                        continue
                    try:
                        product_html = self._fetch_link_text(product_url, link_action)
                    except httpx.HTTPError as exc:
                        if _catalog_access_block_reason_from_error(exc):
                            _mark_catalog_access_blocked(diagnostics, product_url, error=exc)
                            _skip_remaining_links(diagnostics, links, link_index)
                            blocked = True
                            break
                        diagnostics["errors"].append(str(exc))
                        continue
                    if self._access_block_reason_from_body(product_html):
                        _mark_catalog_access_blocked(diagnostics, product_url)
                        _skip_remaining_links(diagnostics, links, link_index)
                        blocked = True
                        break
                    fetched_urls.add(product_url_key)
                    followed_pages += 1
                    diagnostics["pages_fetched"] += 1
                    raw_product_candidates = self._schema_candidates(product_html, product_url, query_text, source_kind)
                    product_candidates, rejected_count, rejection_samples = _provider_catalog_candidates_matching_query(
                        raw_product_candidates,
                        query_text,
                    )
                    _add_rejected_by_intent(diagnostics, rejected_count, rejection_samples)
                    diagnostics["candidates_found"] += len(product_candidates)
                    candidates.extend(product_candidates)
                if blocked:
                    break
                if followed_pages >= self.max_product_pages:
                    break
            if blocked:
                break
        return {"candidates": candidates, "diagnostics": diagnostics}

    def _fetch_link_text(self, url: str, action: str) -> str:
        if self.fetch_text is not None:
            return self.fetch_text(url)
        browser_decision = supplier_fetch_decision(
            url,
            provider=self.catalog_provider,
            action=ACTION_BROWSER_FETCH,
            tender_position_count=self.tender_position_count,
        )
        allow_browser_fetch = bool(browser_decision["allowed"])
        html = _fetch_catalog_text(
            url,
            self.catalog_provider,
            allow_browser_fetch=allow_browser_fetch,
        )
        if allow_browser_fetch and _catalog_access_block_reason_from_body(html):
            try:
                return supplier_browser_fetcher.fetch_text(url, provider=self.catalog_provider)
            except supplier_browser_fetcher.BrowserFetchError as exc:
                raise httpx.HTTPError(f"access_blocked body from {url}; browser_fetch_error: {exc}") from exc
        return html

    def _access_block_reason_from_body(self, html: str) -> str | None:
        reason = _catalog_access_block_reason_from_body(html)
        if not reason:
            return None
        if _catalog_body_has_provider_product_signal(self.catalog_provider, html):
            return None
        return reason

    def _allow_fetch_url(self, url: str, action: str, diagnostics: dict[str, Any]) -> bool:
        decision = supplier_fetch_decision(
            url,
            provider=self.catalog_provider,
            action=action,
            tender_position_count=self.tender_position_count,
        )
        if decision["allowed"]:
            return True
        _mark_policy_skipped(diagnostics, decision["reason"])
        return False

    def _schema_candidates(
        self,
        html: str,
        source_url: str,
        query_text: str,
        source_kind: str,
    ) -> list[dict[str, Any]]:
        if self.catalog_provider == "lemanapro":
            candidates = _lemanapro_plp_candidates(html, source_url, query_text, source_kind)
            candidates.extend(_lemanapro_visible_catalog_candidates(html, source_url, query_text, source_kind))
            if candidates:
                return _unique_candidates(candidates)
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
    candidate_limit: int | None = None,
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
        candidate_limit=candidate_limit,
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
    manual_required = _manual_required_tender_discovery_result(profiles, searchable_profiles)
    if manual_required is not None:
        if progress_callback is not None:
            progress_callback(manual_required)
        return manual_required
    price_collectors = default_price_collectors() if collectors is None else collectors
    position_limit = (
        max(1, int(max_positions))
        if max_positions is not None
        else _positive_env_int(
            "TENDER_KILLER_PRICE_DISCOVERY_MAX_POSITIONS",
            DEFAULT_TENDER_PRICE_DISCOVERY_MAX_POSITIONS,
        )
    )
    candidate_limit = _candidate_limit_for_profile_count(len(searchable_profiles))
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
                candidate_limit=candidate_limit,
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
    provider = _text(data.get("provider")) or _provider_from_url(url or "")
    if not url or not _is_public_product_page_url(url):
        raise ValueError("Укажи публичную ссылку на страницу товара поставщика.")

    decision = supplier_fetch_decision(
        url,
        provider=provider,
        action=ACTION_PRODUCT_PAGE_FETCH,
        tender_position_count=len(profiles),
    )
    if not decision["allowed"]:
        raise ValueError(f"unsafe supplier URL: {decision['reason']}")

    query_text = _text(data.get("source_query")) or _text(target.get("normalized_name")) or _text(target.get("product_name")) or url
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
        candidate_limit=_candidate_limit_for_single_profile(),
    )


def tender_price_discovery_policy_for_tender(
    database_path: str | Path,
    source: str,
    external_id: str,
) -> dict[str, Any]:
    profiles = ensure_product_profiles(database_path, source, external_id)
    searchable_profiles = [profile for profile in profiles if int(profile.get("position_index") or 0) > 0]
    manual_required = _manual_required_tender_discovery_result(profiles, searchable_profiles)
    if manual_required is not None:
        return manual_required
    return {
        "ok": True,
        "status": "active_discovery_allowed",
        "reason": "small_tender_review_only",
        "total_profiles": len(searchable_profiles),
        "max_active_positions": SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT,
    }


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
    candidate_limit: int | None = None,
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    diagnostics_by_provider: dict[str, dict[str, Any]] = {}
    price_collectors = _relevant_price_collectors_for_queries(
        queries,
        price_collectors,
        diagnostics_by_provider,
        profile=target,
    )
    _set_collector_policy_context(price_collectors, len(profiles))
    blocked_providers: set[str] = set()
    for query in queries:
        for collector in price_collectors:
            provider_name = _collector_provider_name(collector)
            if provider_name in blocked_providers or _collector_is_access_blocked(collector):
                _merge_diagnostics(
                    diagnostics_by_provider,
                    _blocked_collector_diagnostics(provider_name),
                )
                continue
            result = collector.collect_with_diagnostics(query)
            accepted_candidates: list[dict[str, Any]] = []
            rejected_by_intent = 0
            rejection_reasons: dict[str, int] = {}
            for candidate in result["candidates"]:
                if not _candidate_matches_profile_intent(target, candidate):
                    rejected_by_intent += 1
                    _increment_reason_counts(
                        rejection_reasons,
                        _candidate_profile_intent_rejection_reasons(target, candidate),
                    )
                    continue
                key = _candidate_key(candidate)
                if key in existing_keys:
                    continue
                existing_keys.add(key)
                normalized_candidate = normalize_supplier_candidate(
                    candidate,
                    provider=_collector_catalog_provider(collector) or _collector_provider_name(collector),
                    source_query=_text(query.get("query")) or "",
                    source_kind=_text(query.get("kind")) or "",
                )
                accepted_candidates.append(_candidate_with_profile_match(target, normalized_candidate))
            diagnostics = _with_intent_rejection_diagnostics(
                result["diagnostics"],
                rejected_by_intent,
                rejection_reasons,
            )
            if _diagnostics_has_signal(diagnostics):
                _merge_diagnostics(diagnostics_by_provider, diagnostics)
            if _diagnostics_is_access_blocked(diagnostics):
                blocked_providers.add(provider_name)
                _mark_collector_access_blocked(collector)
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

    limited_candidates = _limit_supplier_candidates_for_profile(target, candidates, candidate_limit)
    if len(limited_candidates) < len(candidates):
        _merge_diagnostics(
            diagnostics_by_provider,
            _candidate_limit_diagnostics(
                candidate_limit,
                collected_count=len(candidates),
                staged_count=len(limited_candidates),
            ),
        )

    return stage_profile_supplier_candidates(
        database_path,
        source,
        external_id,
        int(target.get("position_index") or 0),
        limited_candidates,
        collector_diagnostics=list(diagnostics_by_provider.values()),
    )


def _relevant_price_collectors_for_queries(
    queries: list[dict[str, Any]],
    price_collectors: list[Any],
    diagnostics_by_provider: dict[str, dict[str, Any]],
    profile: dict[str, Any] | None = None,
) -> list[Any]:
    query_catalog_providers = _catalog_providers_for_queries(queries)
    allowed_catalog_providers = query_catalog_providers
    if profile is not None:
        profile_catalog_providers = supplier_catalog_providers_for_profile(profile)
        if profile_catalog_providers:
            allowed_catalog_providers = set(profile_catalog_providers)
            allowed_catalog_providers.update(_manual_product_catalog_providers_for_queries(queries))
    relevant_collectors: list[Any] = []
    for collector in price_collectors:
        catalog_provider = _collector_catalog_provider(collector)
        if catalog_provider is not None and catalog_provider not in allowed_catalog_providers:
            _merge_diagnostics(
                diagnostics_by_provider,
                _skipped_collector_diagnostics(
                    _collector_provider_name(collector),
                    "not_relevant_for_profile",
                ),
            )
            continue
        relevant_collectors.append(collector)
    return relevant_collectors


def _catalog_providers_for_queries(queries: list[dict[str, Any]]) -> set[str]:
    providers: set[str] = set()
    for query in queries:
        for link in _quick_links(query):
            link_kind = _text(link.get("link_kind"))
            provider = _text(link.get("provider"))
            if link_kind in {CATALOG_SEARCH_LINK_KIND, MANUAL_PRODUCT_LINK_KIND} and provider:
                providers.add(provider.casefold())
    return providers


def _manual_product_catalog_providers_for_queries(queries: list[dict[str, Any]]) -> set[str]:
    providers: set[str] = set()
    for query in queries:
        for link in _quick_links(query):
            link_kind = _text(link.get("link_kind"))
            provider = _text(link.get("provider"))
            if link_kind == MANUAL_PRODUCT_LINK_KIND and provider:
                providers.add(provider.casefold())
    return providers


def _candidate_limit_for_single_profile() -> int:
    return _positive_env_int(
        "TENDER_KILLER_PRICE_DISCOVERY_SINGLE_CANDIDATES_PER_POSITION",
        DEFAULT_SINGLE_DISCOVERY_CANDIDATE_LIMIT,
    )


def _manual_required_tender_discovery_result(
    profiles: list[dict[str, Any]],
    searchable_profiles: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if len(searchable_profiles) <= SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT:
        return None
    return {
        "ok": False,
        "status": "manual_required",
        "reason": "large_tender_manual_required",
        "message": "Active supplier price discovery is limited to small tenders. Use quick links/manual URL/feed.",
        "total_profiles": len(searchable_profiles),
        "prepared_count": 0,
        "searched_count": 0,
        "limited_count": len(searchable_profiles),
        "partial": True,
        "staged_count": 0,
        "ready_count": 0,
        "review_count": 0,
        "blocked_count": 0,
        "no_candidates_count": 0,
        "error_count": 0,
        "positions": [
            {
                "position_index": int(profile.get("position_index") or 0),
                "status": "manual_required",
                "staged_count": 0,
            }
            for profile in searchable_profiles
        ],
        "diagnostics_by_provider": [],
    }


def _candidate_limit_for_profile_count(profile_count: int) -> int:
    threshold = _positive_env_int(
        "TENDER_KILLER_PRICE_DISCOVERY_BULK_PROFILE_THRESHOLD",
        DEFAULT_BULK_DISCOVERY_PROFILE_THRESHOLD,
    )
    if int(profile_count or 0) > threshold:
        return _positive_env_int(
            "TENDER_KILLER_PRICE_DISCOVERY_BULK_CANDIDATES_PER_POSITION",
            DEFAULT_BULK_DISCOVERY_CANDIDATE_LIMIT,
        )
    return _candidate_limit_for_single_profile()


def _limit_supplier_candidates_for_profile(
    profile: dict[str, Any],
    candidates: list[dict[str, Any]],
    candidate_limit: int | None,
) -> list[dict[str, Any]]:
    if candidate_limit is None or candidate_limit <= 0 or len(candidates) <= candidate_limit:
        return candidates
    ranked = sorted(candidates, key=lambda candidate: _supplier_candidate_rank_key(profile, candidate))
    return ranked[:candidate_limit]


def _supplier_candidate_rank_key(profile: dict[str, Any], candidate: dict[str, Any]) -> tuple[float, float, str]:
    unit_price = _number(candidate.get("unit_price"))
    normalized_price = unit_price if unit_price is not None else float("inf")
    name_key = _text(candidate.get("name") or candidate.get("product_name")) or ""
    return (-_supplier_candidate_relevance_score(profile, candidate), normalized_price, name_key.casefold())


def _supplier_candidate_relevance_score(profile: dict[str, Any], candidate: dict[str, Any]) -> float:
    product_name = _candidate_intent_text(candidate)
    profile_text = _profile_intent_text(profile, candidate)
    score = _number(candidate.get("score")) or 0.0
    if product_name and profile_text and _catalog_product_name_matches_query(product_name, profile_text):
        score += 60
    profile_tokens = _rank_tokens(profile_text)
    candidate_tokens = _rank_tokens(
        " ".join(
            part
            for part in (
                product_name,
                _text(candidate.get("brand")) or "",
                _text(candidate.get("manufacturer")) or "",
                _text(candidate.get("supplier_name")) or "",
            )
            if part
        )
    )
    overlap = profile_tokens.intersection(candidate_tokens)
    score += min(len(overlap), 12) * 4
    brand_tokens = _rank_tokens(_text(candidate.get("brand")) or _text(candidate.get("manufacturer")) or "")
    if brand_tokens and brand_tokens.issubset(profile_tokens.union(candidate_tokens)):
        score += 25
    confidence = (_text(candidate.get("confidence")) or "").casefold()
    score += {"high": 20, "medium": 10, "needs_review": 2, "low": 2}.get(confidence, 0)
    if _number(candidate.get("unit_price")) is not None:
        score += 10
    availability = (_text(candidate.get("availability")) or "").casefold()
    if availability in {"in_stock", "available", "instock"}:
        score += 5
    source_kind = (_text(candidate.get("source_kind")) or "").casefold()
    if source_kind in {"catalog_hint", "normalized_name", "manual_product_url"}:
        score += 8
    if candidate.get("url") or candidate.get("source_url"):
        score += 4
    return score


def _rank_tokens(text: str | None) -> set[str]:
    tokens: set[str] = set()
    for token in CATALOG_TOKEN_RE.findall(str(text or "").casefold()):
        if len(token) < 2 or token in CATALOG_QUERY_STOP_WORDS:
            continue
        tokens.add(token)
    return tokens


def _candidate_limit_diagnostics(candidate_limit: int | None, *, collected_count: int, staged_count: int) -> dict[str, Any]:
    diagnostics = _collector_diagnostics("candidate_limiter")
    diagnostics["run_state"] = "applied"
    diagnostics["candidate_limit"] = int(candidate_limit or 0)
    diagnostics["candidates_seen"] = int(collected_count)
    diagnostics["candidates_limited"] = max(0, int(collected_count) - int(staged_count))
    diagnostics["candidates_staged"] = int(staged_count)
    diagnostics["candidates_found"] = int(collected_count)
    return diagnostics


def _collector_catalog_provider(collector: Any) -> str | None:
    catalog_provider = _text(getattr(collector, "catalog_provider", None))
    if catalog_provider:
        return catalog_provider.casefold()
    provider = _text(getattr(collector, "provider", None))
    if provider and provider.casefold().startswith("catalog_"):
        return provider.casefold().removeprefix("catalog_")
    return None


def _collector_provider_name(collector: Any) -> str:
    return _text(getattr(collector, "provider", None)) or collector.__class__.__name__


def _collector_is_access_blocked(collector: Any) -> bool:
    return bool(getattr(collector, "_tender_killer_access_blocked", False))


def _set_collector_policy_context(collectors: list[Any], tender_position_count: int) -> None:
    for collector in collectors:
        try:
            setattr(collector, "tender_position_count", tender_position_count)
        except Exception:
            continue


def _mark_collector_access_blocked(collector: Any) -> None:
    try:
        setattr(collector, "_tender_killer_access_blocked", True)
    except Exception:
        return


def _candidate_matches_profile_intent(profile: dict[str, Any], candidate: dict[str, Any]) -> bool:
    product_name = _candidate_intent_text(candidate)
    profile_text = _profile_intent_text(profile, candidate)
    if not product_name or not profile_text:
        return True
    return _catalog_product_name_matches_query(product_name, profile_text)


def _candidate_profile_intent_rejection_reasons(profile: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    product_name = _candidate_intent_text(candidate)
    profile_text = _profile_intent_text(profile, candidate)
    if not product_name or not profile_text:
        return []
    return supplier_product_name_mismatch_reasons(profile_text, product_name)


def _profile_intent_text(profile: dict[str, Any], candidate: dict[str, Any]) -> str:
    parts: list[str] = []
    for field in ("product_name", "normalized_name"):
        value = _text(profile.get(field))
        if value:
            parts.append(value)
    for phrase in _text_items(profile.get("search_phrases")):
        parts.append(phrase)
    raw_payload = profile.get("raw_payload") if isinstance(profile.get("raw_payload"), dict) else {}
    for query in _supplier_search_queries(raw_payload.get("supplier_search")):
        if _text(query.get("kind")) == "catalog_hint" and (query_text := _text(query.get("query"))):
            parts.append(query_text)
    source_query = _text(candidate.get("source_query"))
    if source_query:
        parts.append(source_query)
    return " ".join(parts)


def _candidate_with_profile_match(profile: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    updated = dict(candidate)
    reasons = _text_items(candidate.get("match_reasons"))
    reasons.extend(supplier_product_name_match_reasons(_profile_intent_text(profile, candidate), _candidate_intent_text(candidate)))
    reasons.extend(_candidate_brand_match_reasons(candidate))
    if "profile_intent_match" not in reasons:
        reasons.append("profile_intent_match")
    updated["match_reasons"] = _dedupe_text_items(reasons)
    return updated


def _candidate_intent_text(candidate: dict[str, Any]) -> str:
    parts: list[str] = []
    for field in ("name", "product_name", "brand", "manufacturer", "supplier_name", "unit"):
        if text := _text(candidate.get(field)):
            parts.append(text)
    for attribute in _dict_items(candidate.get("product_attributes")):
        name = _text(attribute.get("name"))
        value = _text(attribute.get("value"))
        if not name or not value:
            continue
        parts.append(f"{name} {value}")
        parts.append(f"{value} {name}")
        if unit_hint := _attribute_unit_hint(name):
            if unit_hint not in value.casefold():
                parts.append(f"{value} {unit_hint}")
    return " ".join(parts)


def _candidate_brand_match_reasons(candidate: dict[str, Any]) -> list[str]:
    brand_tokens = _rank_tokens(_text(candidate.get("brand")) or _text(candidate.get("manufacturer")) or "")
    if not brand_tokens:
        return []
    source_tokens = _rank_tokens(_text(candidate.get("source_query")) or "")
    name_tokens = _rank_tokens(_text(candidate.get("name") or candidate.get("product_name")) or "")
    return ["brand_match"] if brand_tokens.intersection(source_tokens.union(name_tokens)) else []


def _attribute_unit_hint(name: str) -> str | None:
    normalized = name.casefold()
    if "kg" in normalized or "\u043a\u0433" in normalized:
        return "kg"
    if "ml" in normalized or "\u043c\u043b" in normalized:
        return "ml"
    if "mm" in normalized or "\u043c\u043c" in normalized:
        return "mm"
    if re.search(r"(?<![a-z])g(?![a-z])", normalized) or "\u0433" in normalized:
        return "g"
    if re.search(r"(?<![a-z])l(?![a-z])", normalized) or "\u043b" in normalized:
        return "l"
    return None


def _provider_catalog_candidates_matching_query(
    candidates: list[dict[str, Any]],
    query_text: str,
) -> tuple[list[dict[str, Any]], int, list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []
    rejected_count = 0
    rejection_samples: list[dict[str, Any]] = []
    for candidate in candidates:
        product_name = _candidate_intent_text(candidate)
        if not product_name or not query_text or _catalog_product_name_matches_query(product_name, query_text):
            accepted.append(candidate)
            continue
        rejected_count += 1
        if len(rejection_samples) < MAX_INTENT_REJECTION_SAMPLES:
            rejection_samples.append(_intent_rejection_sample(candidate, query_text))
    return accepted, rejected_count, rejection_samples


def _add_rejected_by_intent(
    diagnostics: dict[str, Any],
    rejected_count: int,
    rejection_samples: list[dict[str, Any]] | None = None,
) -> None:
    if rejected_count <= 0:
        return
    diagnostics["candidates_rejected_by_intent"] = (
        int(diagnostics.get("candidates_rejected_by_intent") or 0) + rejected_count
    )
    if rejection_samples:
        _extend_intent_rejection_samples(diagnostics, rejection_samples)


def _intent_rejection_sample(candidate: dict[str, Any], query_text: str) -> dict[str, Any]:
    sample = {
        "name": _text(candidate.get("name") or candidate.get("product_name")) or "",
        "url": _text(candidate.get("url")) or "",
        "reasons": supplier_product_name_mismatch_reasons(query_text, _candidate_intent_text(candidate)),
    }
    return {key: value for key, value in sample.items() if value not in ("", [], None)}


def _extend_intent_rejection_samples(target: dict[str, Any], samples: list[dict[str, Any]]) -> None:
    current = [dict(item) for item in target.get("intent_rejection_samples") or [] if isinstance(item, dict)]
    current = current[:MAX_INTENT_REJECTION_SAMPLES]
    seen = {
        (
            (_text(item.get("url")) or "").casefold(),
            (_text(item.get("name")) or "").casefold(),
        )
        for item in current
    }
    for sample in samples:
        if len(current) >= MAX_INTENT_REJECTION_SAMPLES:
            break
        key = (
            (_text(sample.get("url")) or "").casefold(),
            (_text(sample.get("name")) or "").casefold(),
        )
        if key in seen:
            continue
        seen.add(key)
        current.append(dict(sample))
        if len(current) >= MAX_INTENT_REJECTION_SAMPLES:
            break
    if current:
        target["intent_rejection_samples"] = current


def _with_intent_rejection_diagnostics(
    diagnostics: dict[str, Any],
    rejected_count: int,
    rejection_reasons: dict[str, int] | None = None,
) -> dict[str, Any]:
    if rejected_count <= 0:
        return diagnostics
    updated = dict(diagnostics)
    updated["candidates_rejected_by_intent"] = int(updated.get("candidates_rejected_by_intent") or 0) + rejected_count
    if rejection_reasons:
        current_reasons = dict(updated.get("intent_rejection_reasons") or {})
        for reason, count in rejection_reasons.items():
            current_reasons[reason] = int(current_reasons.get(reason) or 0) + int(count)
        updated["intent_rejection_reasons"] = current_reasons
    return updated


def _increment_reason_counts(target: dict[str, int], reasons: list[str]) -> None:
    for reason in reasons:
        target[reason] = int(target.get(reason) or 0) + 1


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
    index_by_key: dict[str, int] = {}
    for query in queries:
        query_text = _text(query.get("query"))
        if not query_text:
            continue
        key = query_text.casefold()
        if key in index_by_key:
            unique[index_by_key[key]] = _merge_supplier_search_query(unique[index_by_key[key]], query)
            continue
        index_by_key[key] = len(unique)
        unique.append(dict(query))
    return unique


def _merge_supplier_search_query(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    merged = dict(left)
    if _has_direct_supplier_quick_link(left):
        return merged
    merged_links = _unique_quick_links([*_quick_links(left), *_quick_links(right)])
    if merged_links:
        merged["quick_links"] = merged_links
    return merged


def _has_direct_supplier_quick_link(query: dict[str, Any]) -> bool:
    for link in _quick_links(query):
        if _text(link.get("link_kind")) == CATALOG_SEARCH_LINK_KIND:
            continue
        url = _text(link.get("url"))
        if url and _is_public_product_page_url(url):
            return True
    return False


def _unique_quick_links(links: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for link in links:
        url = _text(link.get("url"))
        if not url:
            continue
        key = (
            url.casefold(),
            _text(link.get("provider")) or "",
            _text(link.get("link_kind")) or "",
            _text(link.get("preset_id")) or "",
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(dict(link))
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


def _skipped_collector_diagnostics(provider: str, reason: str) -> dict[str, Any]:
    diagnostics = _collector_diagnostics(provider)
    diagnostics["run_state"] = "skipped"
    diagnostics["skip_reason"] = reason
    return diagnostics


def _blocked_collector_diagnostics(provider: str) -> dict[str, Any]:
    diagnostics = _collector_diagnostics(provider)
    diagnostics["run_state"] = "blocked"
    diagnostics["skip_reason"] = ACCESS_BLOCKED_ERROR_KIND
    diagnostics["error_kind"] = ACCESS_BLOCKED_ERROR_KIND
    return diagnostics


def _fetch_action_for_link(link: dict[str, Any]) -> str:
    return ACTION_PRODUCT_PAGE_FETCH if _text(link.get("link_kind")) == MANUAL_PRODUCT_LINK_KIND else ACTION_PUBLIC_SEARCH_FETCH


def _mark_policy_skipped(diagnostics: dict[str, Any], reason: str) -> None:
    diagnostics["run_state"] = "skipped"
    diagnostics["skip_reason"] = reason
    policy_reasons = diagnostics.setdefault("policy_skip_reasons", {})
    policy_reasons[reason] = int(policy_reasons.get(reason) or 0) + 1


def _mark_catalog_access_blocked(
    diagnostics: dict[str, Any],
    url: str,
    *,
    error: BaseException | None = None,
) -> None:
    diagnostics["run_state"] = "blocked"
    diagnostics["skip_reason"] = ACCESS_BLOCKED_ERROR_KIND
    diagnostics["error_kind"] = ACCESS_BLOCKED_ERROR_KIND
    if error is None:
        diagnostics["errors"].append(f"{ACCESS_BLOCKED_ERROR_KIND} body from {url}")
        return
    diagnostics["errors"].append(f"{ACCESS_BLOCKED_ERROR_KIND} error from {url}: {error}")


def _skip_remaining_links(diagnostics: dict[str, Any], links: list[dict[str, Any]], current_index: int) -> None:
    diagnostics["links_skipped"] += max(0, len(links) - int(current_index) - 1)


def _catalog_access_block_reason_from_error(exc: BaseException) -> str | None:
    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if isinstance(status_code, int) and status_code in ACCESS_BLOCKED_STATUS_CODES:
        return ACCESS_BLOCKED_ERROR_KIND
    text = str(exc).casefold()
    if any(
        marker in text
        for marker in (
            ACCESS_BLOCKED_ERROR_KIND,
            "forbidden",
            "captcha",
            "\u043a\u0430\u043f\u0447",
            "browser check",
            "\u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0432\u0430\u0448\u0435\u0433\u043e \u0432\u0435\u0431-\u0431\u0440\u0430\u0443\u0437\u0435\u0440\u0430",
            "\u043f\u0440\u043e\u0439\u0434\u0438\u0442\u0435 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0443",
        )
    ):
        return ACCESS_BLOCKED_ERROR_KIND
    return None


def _catalog_access_block_reason_from_body(body: str) -> str | None:
    text = re.sub(r"\s+", " ", str(body or "")).casefold()
    if not text:
        return None
    if "if you are not a bot" in text:
        return ACCESS_BLOCKED_ERROR_KIND
    if "forbidden" in text and ("origin:" in text or "copy the report" in text):
        return ACCESS_BLOCKED_ERROR_KIND
    if any(
        marker in text
        for marker in (
            "access denied",
            "browser verification",
            "verification required",
            "captcha",
            "\u043a\u0430\u043f\u0447",
            "browser check",
            "\u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0432\u0430\u0448\u0435\u0433\u043e \u0432\u0435\u0431-\u0431\u0440\u0430\u0443\u0437\u0435\u0440\u0430",
            "\u043f\u0440\u043e\u0439\u0434\u0438\u0442\u0435 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0443",
        )
    ):
        return ACCESS_BLOCKED_ERROR_KIND
    return None


def _catalog_body_has_provider_product_signal(provider: str, body: str) -> bool:
    body_text = str(body or "")
    if not body_text.strip():
        return False
    soup = BeautifulSoup(body_text, "html.parser")
    if re.search(r'"@type"\s*:\s*(?:"Product"|\[[^\]]*"Product")', body_text, re.IGNORECASE):
        return True
    provider_key = str(provider or "").casefold()
    if provider_key == "officemag":
        return bool(
            _officemag_product_scopes(soup)
            or soup.select_one(".ProductHead__name, .Product__price, .js-productSum")
        )
    if provider_key == "komus":
        return bool(soup.select_one("a[href*='/p/'], .product-card, [data-qa*='product' i]"))
    if provider_key == "petrovich":
        return bool(soup.select_one("a[href^='/product/'], a[href*='/product/'], .product-card, [data-test*='product' i]"))
    if provider_key in {"vseinstrumenti", "lemanapro"}:
        return bool(soup.select_one("a[href*='/product/'], .product-card, [data-qa*='product' i]"))
    return False


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
    for reason, count in dict(item.get("intent_rejection_reasons") or {}).items():
        target_reasons = target.setdefault("intent_rejection_reasons", {})
        target_reasons[str(reason)] = int(target_reasons.get(str(reason)) or 0) + int(count or 0)
    _extend_intent_rejection_samples(
        target,
        [dict(sample) for sample in item.get("intent_rejection_samples") or [] if isinstance(sample, dict)],
    )
    if run_state := _text(item.get("run_state")):
        target["run_state"] = run_state
    if skip_reason := _text(item.get("skip_reason")):
        target["skip_reason"] = skip_reason
    if error_kind := _text(item.get("error_kind")):
        target["error_kind"] = error_kind
    for field in ("candidate_limit", "candidates_seen", "candidates_limited", "candidates_staged"):
        if field in item:
            target[field] = int(item.get(field) or 0)
    target["errors"].extend([str(error) for error in item.get("errors") or []])


def _diagnostics_is_access_blocked(item: dict[str, Any]) -> bool:
    if _text(item.get("error_kind")) == ACCESS_BLOCKED_ERROR_KIND:
        return True
    if _text(item.get("skip_reason")) == ACCESS_BLOCKED_ERROR_KIND:
        return True
    return any(_catalog_access_block_reason_from_error(RuntimeError(str(error))) for error in item.get("errors") or [])


def _diagnostics_has_signal(item: dict[str, Any]) -> bool:
    return bool(
        item.get("pages_fetched")
        or item.get("candidates_found")
        or item.get("candidates_rejected_by_intent")
        or item.get("run_state") == "skipped"
        or item.get("run_state") == "blocked"
        or item.get("skip_reason")
        or item.get("error_kind")
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
    for product_url in _officemag_hidden_product_page_urls(html, source_url):
        _append_unique_url(urls, seen, product_url)
    for product_url in _schema_product_page_urls(html, source_url):
        _append_unique_url(urls, seen, product_url)
    for product_url in _same_site_anchor_urls(html, source_url):
        _append_unique_url(urls, seen, product_url)
    return urls


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
        return path.startswith("/product/") or path.startswith("/catalog/")
    if provider_key == "vseinstrumenti":
        return "/product/" in path
    if provider_key == "lemanapro":
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
    return fetch_public_text(url)


def _fetch_catalog_text(url: str, provider: str, *, allow_browser_fetch: bool = False) -> str:
    return fetch_catalog_text(url, provider, allow_browser_fetch=allow_browser_fetch)


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
    if "lemanapro.ru" in host:
        return "lemanapro"
    return None


def _catalog_provider_label(provider: str) -> str:
    labels = {
        "officemag": "OfficeMag",
        "komus": "Komus",
        "petrovich": "Petrovich",
        "vseinstrumenti": "Vseinstrumenti",
        "lemanapro": "Lemana Pro",
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


def _dedupe_text_items(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = _text(item)
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _unique_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        url = (_text(candidate.get("url")) or "").casefold()
        name = (_text(candidate.get("name") or candidate.get("product_name")) or "").casefold()
        key = (url, name)
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


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
