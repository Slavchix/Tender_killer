from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Callable

import httpx

from tender_killer import supplier_browser_fetcher
from tender_killer.product_profile_service import ensure_product_profiles
from tender_killer.price_candidate_service import stage_tender_price_candidates
from tender_killer.storage import TenderStore
from tender_killer.supplier_candidate_contract import normalize_supplier_candidate
from tender_killer.supplier_catalog_presets import supplier_catalog_providers_for_profile
from tender_killer.supplier_discovery_service import stage_profile_supplier_candidates
from tender_killer.supplier_lemanapro_parser import _lemanapro_plp_candidates
from tender_killer.supplier_lemanapro_parser import _lemanapro_visible_catalog_candidates
from tender_killer.supplier_officemag_parser import _officemag_product_scopes
from tender_killer.supplier_officemag_parser import _officemag_visible_candidates
from tender_killer.supplier_price_discovery_catalog_pages import _catalog_fallback_page_urls
from tender_killer.supplier_price_discovery_catalog_pages import _catalog_product_page_urls
from tender_killer.supplier_price_discovery_utils import _append_unique_url
from tender_killer.supplier_price_discovery_utils import _candidate_key
from tender_killer.supplier_price_discovery_utils import _catalog_provider_label
from tender_killer.supplier_price_discovery_utils import _catalog_token_stems
from tender_killer.supplier_price_discovery_utils import _dict_items
from tender_killer.supplier_price_discovery_utils import _fetch_catalog_text
from tender_killer.supplier_price_discovery_utils import _fetch_public_text
from tender_killer.supplier_price_discovery_utils import _is_provider_product_detail_url
from tender_killer.supplier_price_discovery_utils import _is_public_product_page_url
from tender_killer.supplier_price_discovery_utils import _is_same_public_site
from tender_killer.supplier_price_discovery_utils import _positive_env_int
from tender_killer.supplier_price_discovery_utils import _positive_number
from tender_killer.supplier_price_discovery_utils import _provider_from_url
from tender_killer.supplier_price_discovery_utils import _text
from tender_killer.supplier_price_discovery_utils import _unique_candidates
from tender_killer.supplier_provider_policy import ACTION_BROWSER_FETCH
from tender_killer.supplier_provider_policy import ACTION_PRODUCT_PAGE_FETCH
from tender_killer.supplier_provider_policy import SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT
from tender_killer.supplier_provider_policy import supplier_fetch_decision
from tender_killer.supplier_price_discovery_diagnostics import MANUAL_PRODUCT_LINK_KIND
from tender_killer.supplier_price_discovery_diagnostics import NO_SUPPLIER_CANDIDATES_MESSAGE
from tender_killer.supplier_price_discovery_diagnostics import _blocked_collector_diagnostics
from tender_killer.supplier_price_discovery_diagnostics import _catalog_access_block_reason_from_body
from tender_killer.supplier_price_discovery_diagnostics import _catalog_access_block_reason_from_error
from tender_killer.supplier_price_discovery_diagnostics import _catalog_body_has_provider_product_signal
from tender_killer.supplier_price_discovery_diagnostics import _collector_diagnostics
from tender_killer.supplier_price_discovery_diagnostics import _diagnostics_has_signal
from tender_killer.supplier_price_discovery_diagnostics import _diagnostics_is_access_blocked
from tender_killer.supplier_price_discovery_diagnostics import _fetch_action_for_link
from tender_killer.supplier_price_discovery_diagnostics import _increment_reason_counts
from tender_killer.supplier_price_discovery_diagnostics import _mark_catalog_access_blocked
from tender_killer.supplier_price_discovery_diagnostics import _mark_policy_skipped
from tender_killer.supplier_price_discovery_diagnostics import _merge_diagnostics
from tender_killer.supplier_price_discovery_diagnostics import _record_supplier_discovery_diagnostics
from tender_killer.supplier_price_discovery_diagnostics import _skipped_collector_diagnostics
from tender_killer.supplier_price_discovery_diagnostics import _skip_remaining_links
from tender_killer.supplier_price_discovery_diagnostics import _supplier_discovery_error_message
from tender_killer.supplier_price_discovery_diagnostics import _tender_discovery_diagnostics
from tender_killer.supplier_price_discovery_diagnostics import _with_intent_rejection_diagnostics
from tender_killer.supplier_price_discovery_matching import _add_rejected_by_intent
from tender_killer.supplier_price_discovery_matching import _attribute_unit_hint
from tender_killer.supplier_price_discovery_matching import _candidate_brand_match_reasons
from tender_killer.supplier_price_discovery_matching import _candidate_intent_text
from tender_killer.supplier_price_discovery_matching import _candidate_matches_profile_intent
from tender_killer.supplier_price_discovery_matching import _candidate_profile_intent_rejection_reasons
from tender_killer.supplier_price_discovery_matching import _candidate_with_profile_match
from tender_killer.supplier_price_discovery_matching import _intent_rejection_sample
from tender_killer.supplier_price_discovery_matching import _profile_intent_text
from tender_killer.supplier_price_discovery_matching import _provider_catalog_candidates_matching_query
from tender_killer.supplier_price_discovery_matching import _rank_tokens
from tender_killer.supplier_price_discovery_matching import _supplier_candidate_rank_key
from tender_killer.supplier_price_discovery_matching import _supplier_candidate_relevance_score
from tender_killer.supplier_price_discovery_queries import BUILT_IN_CATALOG_PROVIDERS
from tender_killer.supplier_price_discovery_queries import _catalog_providers_for_queries
from tender_killer.supplier_price_discovery_queries import _is_builtin_catalog_search_link
from tender_killer.supplier_price_discovery_queries import _is_catalog_search_link_for_provider
from tender_killer.supplier_price_discovery_queries import _manual_product_catalog_providers_for_queries
from tender_killer.supplier_price_discovery_queries import _quick_links
from tender_killer.supplier_price_discovery_queries import _refreshed_supplier_search_queries
from tender_killer.supplier_price_discovery_queries import _supplier_search_queries
from tender_killer.supplier_schema_org_parser import _schema_org_candidates
from tender_killer.supplier_schema_org_parser import _schema_product_page_urls
from tender_killer.supplier_search_service import prepare_profile_supplier_search
from tender_killer.supplier_visible_offer_parser import _provider_visible_offer_candidates


SCHEMA_ORG_PRODUCT_PROVIDER = "schema_org_product"
FetchText = Callable[[str], str]
ProgressCallback = Callable[[dict[str, Any]], None]
_LEGACY_CATALOG_QUERY_STOP_WORDS = {
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
DEFAULT_TENDER_PRICE_DISCOVERY_MAX_POSITIONS = 50
DEFAULT_CATALOG_MAX_PRODUCT_PAGES = 5
DEFAULT_BULK_DISCOVERY_PROFILE_THRESHOLD = 3
DEFAULT_BULK_DISCOVERY_CANDIDATE_LIMIT = 5
DEFAULT_SINGLE_DISCOVERY_CANDIDATE_LIMIT = 12


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
        browser_position_count = 1 if action == ACTION_PRODUCT_PAGE_FETCH else self.tender_position_count
        browser_decision = supplier_fetch_decision(
            url,
            provider=self.catalog_provider,
            action=ACTION_BROWSER_FETCH,
            tender_position_count=browser_position_count,
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
        manual_link_candidates = _manual_product_link_review_candidates(target, queries, existing_keys)
        if manual_link_candidates:
            return stage_profile_supplier_candidates(
                database_path,
                source,
                external_id,
                int(target.get("position_index") or 0),
                manual_link_candidates,
                collector_diagnostics=list(diagnostics_by_provider.values()),
            )
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


def _find_profile(profiles: list[dict[str, Any]], position_index: int) -> dict[str, Any] | None:
    for profile in profiles:
        if int(profile.get("position_index") or 0) == position_index:
            return profile
    return None


def _existing_candidate_keys(raw_payload: dict[str, Any]) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    discovery = raw_payload.get("supplier_discovery")
    if isinstance(discovery, dict):
        for candidate in _dict_items(discovery.get("candidates")):
            keys.add(_candidate_key(candidate))
    for option in _dict_items(raw_payload.get("supplier_options")):
        keys.add(_candidate_key(option))
    return keys
