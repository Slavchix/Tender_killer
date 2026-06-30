from __future__ import annotations

from pathlib import Path
from typing import Any

from tender_killer.economics_service import accept_profile_auto_economics as accept_profile_auto_economics_inputs
from tender_killer.economics_service import update_profile_auto_economics as update_profile_auto_economics_inputs
from tender_killer.economics_service import update_profile_economics as update_profile_economics_inputs
from tender_killer.economics_service import update_profile_economics_assumptions as update_profile_economics_assumptions_inputs
from tender_killer.price_book_feed_service import stage_tender_price_book_feed
from tender_killer.price_book_feed_service import stage_tender_price_book_feed_file
from tender_killer.price_candidate_staging import stage_tender_price_candidates
from tender_killer.price_candidate_workflows import apply_tender_auto_prices
from tender_killer.price_candidate_workflows import confirm_ready_price_candidates
from tender_killer.price_candidate_workflows import review_profile_price_candidate
from tender_killer.price_memory_service import stage_price_memory_candidates
from tender_killer.supplier_catalog_preset_service import update_profile_supplier_catalog_presets
from tender_killer.supplier_discovery_service import import_profile_supplier_candidate
from tender_killer.supplier_discovery_service import stage_profile_supplier_candidates
from tender_killer.supplier_option_service import add_profile_supplier_option
from tender_killer.supplier_option_service import apply_best_profile_supplier_option
from tender_killer.supplier_option_service import apply_best_profile_supplier_options
from tender_killer.supplier_option_service import select_profile_supplier_option
from tender_killer.supplier_price_discovery_workflows import run_profile_supplier_price_discovery
from tender_killer.supplier_price_discovery_workflows import run_profile_supplier_url_discovery
from tender_killer.supplier_search_service import prepare_profile_supplier_search
from tender_killer.tender_detail_service import get_tender_payload


def update_product_profile_economics(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    data: dict[str, Any],
) -> dict[str, Any]:
    update_profile_economics_inputs(database_path, source, external_id, position_index, data)
    return get_tender_payload(database_path, source, external_id)


def update_product_profile_economics_assumptions(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    data: dict[str, Any],
) -> dict[str, Any]:
    update_profile_economics_assumptions_inputs(database_path, source, external_id, position_index, data)
    return get_tender_payload(database_path, source, external_id)


def update_product_profile_auto_economics(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
) -> dict[str, Any]:
    detail = get_tender_payload(database_path, source, external_id)
    update_profile_auto_economics_inputs(
        database_path,
        source,
        external_id,
        position_index,
        detail.get("document_records") or [],
    )
    return get_tender_payload(database_path, source, external_id)


def accept_product_profile_auto_economics(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
) -> dict[str, Any]:
    accept_profile_auto_economics_inputs(database_path, source, external_id, position_index)
    return get_tender_payload(database_path, source, external_id)


def add_product_profile_supplier_option(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    data: dict[str, Any],
) -> dict[str, Any]:
    add_profile_supplier_option(database_path, source, external_id, position_index, data)
    return get_tender_payload(database_path, source, external_id)


def select_product_profile_supplier_option(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    option_index: int,
) -> dict[str, Any]:
    select_profile_supplier_option(database_path, source, external_id, position_index, option_index)
    return get_tender_payload(database_path, source, external_id)


def select_best_product_profile_supplier_option(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
) -> dict[str, Any]:
    apply_best_profile_supplier_option(database_path, source, external_id, position_index)
    return get_tender_payload(database_path, source, external_id)


def select_best_product_profile_supplier_options(
    database_path: str | Path,
    source: str,
    external_id: str,
) -> dict[str, Any]:
    selection = apply_best_profile_supplier_options(database_path, source, external_id)
    payload = get_tender_payload(database_path, source, external_id)
    payload["supplier_selection"] = selection
    return payload


def prepare_product_profile_supplier_search(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
) -> dict[str, Any]:
    prepare_profile_supplier_search(
        database_path,
        source,
        external_id,
        position_index,
        resolve_best_product_link=True,
    )
    return get_tender_payload(database_path, source, external_id)


def update_product_profile_supplier_catalog_presets(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    data: dict[str, Any],
) -> dict[str, Any]:
    update_profile_supplier_catalog_presets(database_path, source, external_id, position_index, data)
    return get_tender_payload(database_path, source, external_id)


def stage_product_profile_supplier_candidates(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    data: dict[str, Any],
) -> dict[str, Any]:
    candidates = data.get("candidates") if isinstance(data.get("candidates"), list) else []
    stage_profile_supplier_candidates(database_path, source, external_id, position_index, candidates)
    return get_tender_payload(database_path, source, external_id)


def run_product_profile_supplier_discovery(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
) -> dict[str, Any]:
    run_profile_supplier_price_discovery(database_path, source, external_id, position_index)
    return get_tender_payload(database_path, source, external_id)


def run_product_profile_supplier_url_discovery(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    data: dict[str, Any],
) -> dict[str, Any]:
    run_profile_supplier_url_discovery(database_path, source, external_id, position_index, data)
    return get_tender_payload(database_path, source, external_id)


def import_product_profile_supplier_candidate(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    candidate_index: int,
) -> dict[str, Any]:
    import_profile_supplier_candidate(database_path, source, external_id, position_index, candidate_index)
    return get_tender_payload(database_path, source, external_id)


def review_product_profile_price_candidate(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    candidate_id: int,
    action: str,
) -> dict[str, Any]:
    review_status = "confirmed" if action == "confirm" else "rejected"
    review = review_profile_price_candidate(
        database_path,
        source,
        external_id,
        position_index,
        candidate_id,
        review_status=review_status,
    )
    payload = get_tender_payload(database_path, source, external_id)
    payload["price_candidate_review"] = review
    return payload


def confirm_ready_tender_price_candidates(database_path: str | Path, source: str, external_id: str) -> dict[str, Any]:
    review = confirm_ready_price_candidates(database_path, source, external_id)
    payload = get_tender_payload(database_path, source, external_id)
    payload["price_candidate_bulk_review"] = review
    return payload


def stage_tender_price_candidate_sources(database_path: str | Path, source: str, external_id: str) -> dict[str, Any]:
    memory_stage = stage_price_memory_candidates(database_path, source, external_id)
    stage = stage_tender_price_candidates(database_path, source, external_id)
    payload = get_tender_payload(database_path, source, external_id)
    payload["price_memory_stage"] = memory_stage
    payload["price_candidate_stage"] = stage
    return payload


def apply_tender_auto_prices_request(database_path: str | Path, source: str, external_id: str) -> dict[str, Any]:
    auto_apply = apply_tender_auto_prices(database_path, source, external_id)
    payload = get_tender_payload(database_path, source, external_id)
    payload["price_auto_apply"] = auto_apply
    return payload


def stage_tender_price_book_feed_request(
    database_path: str | Path,
    source: str,
    external_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    rows = data.get("rows") if isinstance(data.get("rows"), list) else []
    feed_name = str(data.get("feed_name") or data.get("name") or "price book").strip() or "price book"
    stage_mode = str(data.get("stage_mode") or "all").strip() or "all"
    feed = stage_tender_price_book_feed(database_path, source, external_id, rows, feed_name=feed_name, stage_mode=stage_mode)
    payload = get_tender_payload(database_path, source, external_id)
    payload["price_book_feed"] = feed
    return payload


def stage_tender_price_book_feed_file_request(
    database_path: str | Path,
    source: str,
    external_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    feed_name = str(data.get("feed_name") or data.get("name") or "price book").strip() or "price book"
    file_name = str(data.get("file_name") or data.get("filename") or "price-book.csv").strip() or "price-book.csv"
    content_base64 = str(data.get("content_base64") or data.get("file_base64") or "").strip()
    stage_mode = str(data.get("stage_mode") or "all").strip() or "all"
    feed = stage_tender_price_book_feed_file(
        database_path,
        source,
        external_id,
        file_name=file_name,
        content_base64=content_base64,
        feed_name=feed_name,
        stage_mode=stage_mode,
    )
    payload = get_tender_payload(database_path, source, external_id)
    payload["price_book_feed"] = feed
    return payload
