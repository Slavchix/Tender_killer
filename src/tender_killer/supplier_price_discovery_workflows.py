from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Callable

from tender_killer.product_profile_service import ensure_product_profiles
from tender_killer.price_candidate_staging import stage_tender_price_candidates
from tender_killer.storage import TenderStore
from tender_killer.supplier_price_discovery_diagnostics import MANUAL_PRODUCT_LINK_KIND
from tender_killer.supplier_price_discovery_diagnostics import _supplier_discovery_error_message
from tender_killer.supplier_price_discovery_diagnostics import _tender_discovery_diagnostics
from tender_killer.supplier_price_discovery_limits import _candidate_limit_for_profile_count
from tender_killer.supplier_price_discovery_limits import _candidate_limit_for_single_profile
from tender_killer.supplier_price_discovery_manual import _existing_candidate_keys
from tender_killer.supplier_price_discovery_policy import _manual_required_tender_discovery_result
from tender_killer.supplier_price_discovery_queries import _refreshed_supplier_search_queries
from tender_killer.supplier_price_discovery_routing import default_price_collectors
from tender_killer.supplier_price_discovery_runner import _run_supplier_discovery_with_queries
from tender_killer.supplier_price_discovery_utils import _is_public_product_page_url
from tender_killer.supplier_price_discovery_utils import _positive_env_int
from tender_killer.supplier_price_discovery_utils import _provider_from_url
from tender_killer.supplier_price_discovery_utils import _text
from tender_killer.supplier_provider_policy import ACTION_PRODUCT_PAGE_FETCH
from tender_killer.supplier_provider_policy import supplier_fetch_decision
from tender_killer.supplier_search_service import prepare_profile_supplier_search


ProgressCallback = Callable[[dict[str, Any]], None]
DEFAULT_TENDER_PRICE_DISCOVERY_MAX_POSITIONS = 50


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


def _find_profile(profiles: list[dict[str, Any]], position_index: int) -> dict[str, Any] | None:
    for profile in profiles:
        if int(profile.get("position_index") or 0) == position_index:
            return profile
    return None
