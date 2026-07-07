from __future__ import annotations

from pathlib import Path
from typing import Any

from tender_killer.storage import TenderStore
from tender_killer.supplier_candidate_contract import normalize_supplier_candidate
from tender_killer.supplier_discovery_service import stage_profile_supplier_candidates
from tender_killer.supplier_price_discovery_collector_state import _collector_catalog_provider
from tender_killer.supplier_price_discovery_collector_state import _collector_is_access_blocked
from tender_killer.supplier_price_discovery_collector_state import _collector_provider_name
from tender_killer.supplier_price_discovery_collector_state import _mark_collector_access_blocked
from tender_killer.supplier_price_discovery_collector_state import _set_collector_policy_context
from tender_killer.supplier_price_discovery_diagnostics import NO_SUPPLIER_CANDIDATES_MESSAGE
from tender_killer.supplier_price_discovery_diagnostics import _blocked_collector_diagnostics
from tender_killer.supplier_price_discovery_diagnostics import _diagnostics_has_signal
from tender_killer.supplier_price_discovery_diagnostics import _diagnostics_is_access_blocked
from tender_killer.supplier_price_discovery_diagnostics import _increment_reason_counts
from tender_killer.supplier_price_discovery_diagnostics import _merge_diagnostics
from tender_killer.supplier_price_discovery_diagnostics import _record_supplier_discovery_diagnostics
from tender_killer.supplier_price_discovery_diagnostics import _with_intent_rejection_diagnostics
from tender_killer.supplier_price_discovery_limits import _candidate_limit_diagnostics
from tender_killer.supplier_price_discovery_limits import _limit_supplier_candidates_for_profile
from tender_killer.supplier_price_discovery_manual import _manual_product_link_review_candidates
from tender_killer.supplier_price_discovery_matching import _candidate_matches_profile_intent
from tender_killer.supplier_price_discovery_matching import _candidate_profile_intent_rejection_reasons
from tender_killer.supplier_price_discovery_matching import _candidate_with_profile_match
from tender_killer.supplier_price_discovery_routing import _relevant_price_collectors_for_queries
from tender_killer.supplier_price_discovery_utils import _candidate_key
from tender_killer.supplier_price_discovery_utils import _text


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
