from __future__ import annotations

from typing import Any
from typing import Callable

import httpx

from tender_killer import supplier_browser_fetcher
from tender_killer.supplier_lemanapro_parser import _lemanapro_plp_candidates
from tender_killer.supplier_lemanapro_parser import _lemanapro_visible_catalog_candidates
from tender_killer.supplier_officemag_parser import _officemag_visible_candidates
from tender_killer.supplier_price_discovery_catalog_pages import _catalog_fallback_page_urls
from tender_killer.supplier_price_discovery_catalog_pages import _catalog_product_page_urls
from tender_killer.supplier_price_discovery_diagnostics import _catalog_access_block_reason_from_body
from tender_killer.supplier_price_discovery_diagnostics import _catalog_access_block_reason_from_error
from tender_killer.supplier_price_discovery_diagnostics import _catalog_body_has_provider_product_signal
from tender_killer.supplier_price_discovery_diagnostics import _collector_diagnostics
from tender_killer.supplier_price_discovery_diagnostics import _fetch_action_for_link
from tender_killer.supplier_price_discovery_diagnostics import _mark_catalog_access_blocked
from tender_killer.supplier_price_discovery_diagnostics import _mark_policy_skipped
from tender_killer.supplier_price_discovery_diagnostics import _skip_remaining_links
from tender_killer.supplier_price_discovery_matching import _add_rejected_by_intent
from tender_killer.supplier_price_discovery_matching import _provider_catalog_candidates_matching_query
from tender_killer.supplier_price_discovery_queries import _is_builtin_catalog_search_link
from tender_killer.supplier_price_discovery_queries import _is_catalog_search_link_for_provider
from tender_killer.supplier_price_discovery_queries import _quick_links
from tender_killer.supplier_price_discovery_utils import _catalog_provider_label
from tender_killer.supplier_price_discovery_utils import _fetch_catalog_text
from tender_killer.supplier_price_discovery_utils import _fetch_public_text
from tender_killer.supplier_price_discovery_utils import _is_provider_product_detail_url
from tender_killer.supplier_price_discovery_utils import _is_public_product_page_url
from tender_killer.supplier_price_discovery_utils import _is_same_public_site
from tender_killer.supplier_price_discovery_utils import _provider_from_url
from tender_killer.supplier_price_discovery_utils import _text
from tender_killer.supplier_price_discovery_utils import _unique_candidates
from tender_killer.supplier_provider_policy import ACTION_BROWSER_FETCH
from tender_killer.supplier_provider_policy import ACTION_PRODUCT_PAGE_FETCH
from tender_killer.supplier_provider_policy import supplier_fetch_decision
from tender_killer.supplier_schema_org_parser import _schema_org_candidates
from tender_killer.supplier_schema_org_parser import _schema_product_page_urls
from tender_killer.supplier_visible_offer_parser import _provider_visible_offer_candidates


SCHEMA_ORG_PRODUCT_PROVIDER = "schema_org_product"
FetchText = Callable[[str], str]


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
