from __future__ import annotations

from pathlib import Path
from typing import Any

from tender_killer.api_response import ApiResponse
from tender_killer.api_routes import parse_product_profile_auto_economics_accept_path
from tender_killer.api_routes import parse_product_profile_auto_economics_path
from tender_killer.api_routes import parse_product_profile_economics_assumptions_path
from tender_killer.api_routes import parse_product_profile_economics_path
from tender_killer.api_routes import parse_product_profile_price_candidate_review_path
from tender_killer.api_routes import parse_product_profile_supplier_catalog_presets_path
from tender_killer.api_routes import parse_product_profile_supplier_discovery_candidate_import_path
from tender_killer.api_routes import parse_product_profile_supplier_discovery_candidates_path
from tender_killer.api_routes import parse_product_profile_supplier_discovery_run_path
from tender_killer.api_routes import parse_product_profile_supplier_discovery_url_path
from tender_killer.api_routes import parse_product_profile_supplier_option_best_select_path
from tender_killer.api_routes import parse_product_profile_supplier_option_select_path
from tender_killer.api_routes import parse_product_profile_supplier_options_path
from tender_killer.api_routes import parse_product_profile_supplier_search_prepare_path
from tender_killer.api_routes import parse_tender_path
from tender_killer.economics_service import accept_profile_auto_economics as accept_profile_auto_economics_inputs
from tender_killer.economics_service import update_profile_auto_economics as update_profile_auto_economics_inputs
from tender_killer.economics_service import update_profile_economics as update_profile_economics_inputs
from tender_killer.economics_service import update_profile_economics_assumptions as update_profile_economics_assumptions_inputs
from tender_killer.price_book_feed_service import stage_tender_price_book_feed
from tender_killer.price_book_feed_service import stage_tender_price_book_feed_file
from tender_killer.price_candidate_service import apply_tender_auto_prices
from tender_killer.price_candidate_service import confirm_ready_price_candidates
from tender_killer.price_candidate_service import review_profile_price_candidate
from tender_killer.price_candidate_service import stage_tender_price_candidates
from tender_killer.price_memory_service import stage_price_memory_candidates
from tender_killer.supplier_catalog_preset_service import update_profile_supplier_catalog_presets
from tender_killer.supplier_discovery_service import import_profile_supplier_candidate
from tender_killer.supplier_discovery_service import stage_profile_supplier_candidates
from tender_killer.supplier_option_service import add_profile_supplier_option
from tender_killer.supplier_option_service import apply_best_profile_supplier_option
from tender_killer.supplier_option_service import apply_best_profile_supplier_options
from tender_killer.supplier_option_service import select_profile_supplier_option
from tender_killer.supplier_price_discovery_service import run_profile_supplier_price_discovery
from tender_killer.supplier_price_discovery_service import run_profile_supplier_url_discovery
from tender_killer.supplier_search_service import prepare_profile_supplier_search
from tender_killer.tender_detail_service import get_tender_payload


def handle_economics_post_request(
    database_path: str | Path,
    path: str,
    body: dict[str, Any],
) -> ApiResponse | None:
    if path.startswith("/api/tenders/") and path.endswith("/economics"):
        route = parse_product_profile_economics_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile economics path"}, status=400)
        return ApiResponse(
            update_product_profile_economics(
                database_path,
                route.source,
                route.external_id,
                route.position_index,
                body,
            )
        )
    if path.startswith("/api/tenders/") and path.endswith("/economics/assumptions"):
        route = parse_product_profile_economics_assumptions_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile economics assumptions path"}, status=400)
        return ApiResponse(
            update_product_profile_economics_assumptions(
                database_path,
                route.source,
                route.external_id,
                route.position_index,
                body,
            )
        )
    if path.startswith("/api/tenders/") and path.endswith("/auto-estimate"):
        route = parse_product_profile_auto_economics_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile auto economics path"}, status=400)
        return ApiResponse(
            update_product_profile_auto_economics(
                database_path,
                route.source,
                route.external_id,
                route.position_index,
            )
        )
    if path.startswith("/api/tenders/") and path.endswith("/auto-estimate/accept"):
        route = parse_product_profile_auto_economics_accept_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile auto economics accept path"}, status=400)
        return ApiResponse(
            accept_product_profile_auto_economics(
                database_path,
                route.source,
                route.external_id,
                route.position_index,
            )
        )
    if path.startswith("/api/tenders/") and path.endswith("/supplier-options"):
        route = parse_product_profile_supplier_options_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile supplier options path"}, status=400)
        return ApiResponse(
            add_product_profile_supplier_option(
                database_path,
                route.source,
                route.external_id,
                route.position_index,
                body,
            )
        )
    if path.startswith("/api/tenders/") and path.endswith("/supplier-options/best/select"):
        route = parse_product_profile_supplier_option_best_select_path(path)
        if route is None:
            tender_route = parse_tender_path(path, suffix="product-profiles/supplier-options/best/select")
            if tender_route is None:
                return ApiResponse({"error": "invalid product profile supplier option best select path"}, status=400)
            return ApiResponse(
                select_best_product_profile_supplier_options(
                    database_path,
                    tender_route.source,
                    tender_route.external_id,
                )
            )
        return ApiResponse(
            select_best_product_profile_supplier_option(
                database_path,
                route.source,
                route.external_id,
                route.position_index,
            )
        )
    if path.startswith("/api/tenders/") and path.endswith("/select"):
        route = parse_product_profile_supplier_option_select_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile supplier option select path"}, status=400)
        return ApiResponse(
            select_product_profile_supplier_option(
                database_path,
                route.source,
                route.external_id,
                route.position_index,
                route.option_index,
            )
        )
    if path.startswith("/api/tenders/") and path.endswith("/supplier-search/prepare"):
        route = parse_product_profile_supplier_search_prepare_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile supplier search prepare path"}, status=400)
        return ApiResponse(
            prepare_product_profile_supplier_search(
                database_path,
                route.source,
                route.external_id,
                route.position_index,
            )
        )
    if path.startswith("/api/tenders/") and path.endswith("/supplier-catalog-presets"):
        route = parse_product_profile_supplier_catalog_presets_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile supplier catalog presets path"}, status=400)
        return ApiResponse(
            update_product_profile_supplier_catalog_presets(
                database_path,
                route.source,
                route.external_id,
                route.position_index,
                body,
            )
        )
    if path.startswith("/api/tenders/") and path.endswith("/supplier-discovery/candidates"):
        route = parse_product_profile_supplier_discovery_candidates_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile supplier discovery candidates path"}, status=400)
        return ApiResponse(
            stage_product_profile_supplier_candidates(
                database_path,
                route.source,
                route.external_id,
                route.position_index,
                body,
            )
        )
    if path.startswith("/api/tenders/") and path.endswith("/supplier-discovery/run"):
        route = parse_product_profile_supplier_discovery_run_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile supplier discovery run path"}, status=400)
        try:
            return ApiResponse(
                run_product_profile_supplier_discovery(
                    database_path,
                    route.source,
                    route.external_id,
                    route.position_index,
                )
            )
        except ValueError as exc:
            payload = get_tender_payload(database_path, route.source, route.external_id)
            payload["error"] = str(exc)
            return ApiResponse(payload, status=400)
    if path.startswith("/api/tenders/") and path.endswith("/supplier-discovery/url"):
        route = parse_product_profile_supplier_discovery_url_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile supplier discovery url path"}, status=400)
        try:
            return ApiResponse(
                run_product_profile_supplier_url_discovery(
                    database_path,
                    route.source,
                    route.external_id,
                    route.position_index,
                    body,
                )
            )
        except ValueError as exc:
            payload = get_tender_payload(database_path, route.source, route.external_id)
            payload["error"] = str(exc)
            return ApiResponse(payload, status=400)
    if path.startswith("/api/tenders/") and path.endswith("/import"):
        route = parse_product_profile_supplier_discovery_candidate_import_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile supplier discovery candidate import path"}, status=400)
        return ApiResponse(
            import_product_profile_supplier_candidate(
                database_path,
                route.source,
                route.external_id,
                route.position_index,
                route.candidate_index,
            )
        )
    if path.startswith("/api/tenders/") and path.endswith("/price-candidates/ready/confirm"):
        route = parse_tender_path(path, suffix="price-candidates/ready/confirm")
        if route is None:
            return ApiResponse({"error": "invalid ready price candidate bulk review path"}, status=400)
        return ApiResponse(confirm_ready_tender_price_candidates(database_path, route.source, route.external_id))
    if path.startswith("/api/tenders/") and path.endswith("/price-candidates/stage"):
        route = parse_tender_path(path, suffix="price-candidates/stage")
        if route is None:
            return ApiResponse({"error": "invalid price candidate stage path"}, status=400)
        return ApiResponse(stage_tender_price_candidate_sources(database_path, route.source, route.external_id))
    if path.startswith("/api/tenders/") and path.endswith("/price-candidates/auto-apply"):
        route = parse_tender_path(path, suffix="price-candidates/auto-apply")
        if route is None:
            return ApiResponse({"error": "invalid price auto apply path"}, status=400)
        return ApiResponse(apply_tender_auto_prices_request(database_path, route.source, route.external_id))
    if path.startswith("/api/tenders/") and path.endswith("/price-book/feed"):
        route = parse_tender_path(path, suffix="price-book/feed")
        if route is None:
            return ApiResponse({"error": "invalid price book feed path"}, status=400)
        return ApiResponse(stage_tender_price_book_feed_request(database_path, route.source, route.external_id, body))
    if path.startswith("/api/tenders/") and path.endswith("/price-book/feed/file"):
        route = parse_tender_path(path, suffix="price-book/feed/file")
        if route is None:
            return ApiResponse({"error": "invalid price book feed file path"}, status=400)
        try:
            return ApiResponse(stage_tender_price_book_feed_file_request(database_path, route.source, route.external_id, body))
        except ValueError as exc:
            return ApiResponse({"error": str(exc)}, status=400)
    if path.startswith("/api/tenders/") and (path.endswith("/confirm") or path.endswith("/reject")):
        route = parse_product_profile_price_candidate_review_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile price candidate review path"}, status=400)
        try:
            return ApiResponse(
                review_product_profile_price_candidate(
                    database_path,
                    route.source,
                    route.external_id,
                    route.position_index,
                    route.candidate_id,
                    route.action,
                )
            )
        except ValueError as exc:
            return ApiResponse({"error": str(exc)}, status=400)
        except KeyError as exc:
            return ApiResponse({"error": str(exc)}, status=404)
    return None


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
