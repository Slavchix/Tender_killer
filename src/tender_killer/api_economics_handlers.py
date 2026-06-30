from __future__ import annotations

from pathlib import Path
from typing import Any

from tender_killer.api_economics_actions import accept_product_profile_auto_economics
from tender_killer.api_economics_actions import add_product_profile_supplier_option
from tender_killer.api_economics_actions import apply_tender_auto_prices_request
from tender_killer.api_economics_actions import confirm_ready_tender_price_candidates
from tender_killer.api_economics_actions import import_product_profile_supplier_candidate
from tender_killer.api_economics_actions import prepare_product_profile_supplier_search
from tender_killer.api_economics_actions import review_product_profile_price_candidate
from tender_killer.api_economics_actions import run_product_profile_supplier_discovery
from tender_killer.api_economics_actions import run_product_profile_supplier_url_discovery
from tender_killer.api_economics_actions import select_best_product_profile_supplier_option
from tender_killer.api_economics_actions import select_best_product_profile_supplier_options
from tender_killer.api_economics_actions import select_product_profile_supplier_option
from tender_killer.api_economics_actions import stage_product_profile_supplier_candidates
from tender_killer.api_economics_actions import stage_tender_price_book_feed_file_request
from tender_killer.api_economics_actions import stage_tender_price_book_feed_request
from tender_killer.api_economics_actions import stage_tender_price_candidate_sources
from tender_killer.api_economics_actions import update_product_profile_auto_economics
from tender_killer.api_economics_actions import update_product_profile_economics
from tender_killer.api_economics_actions import update_product_profile_economics_assumptions
from tender_killer.api_economics_actions import update_product_profile_supplier_catalog_presets
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
        return ApiResponse(update_product_profile_economics(database_path, route.source, route.external_id, route.position_index, body))
    if path.startswith("/api/tenders/") and path.endswith("/economics/assumptions"):
        route = parse_product_profile_economics_assumptions_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile economics assumptions path"}, status=400)
        return ApiResponse(update_product_profile_economics_assumptions(database_path, route.source, route.external_id, route.position_index, body))
    if path.startswith("/api/tenders/") and path.endswith("/auto-estimate"):
        route = parse_product_profile_auto_economics_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile auto economics path"}, status=400)
        return ApiResponse(update_product_profile_auto_economics(database_path, route.source, route.external_id, route.position_index))
    if path.startswith("/api/tenders/") and path.endswith("/auto-estimate/accept"):
        route = parse_product_profile_auto_economics_accept_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile auto economics accept path"}, status=400)
        return ApiResponse(accept_product_profile_auto_economics(database_path, route.source, route.external_id, route.position_index))
    if path.startswith("/api/tenders/") and path.endswith("/supplier-options"):
        route = parse_product_profile_supplier_options_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile supplier options path"}, status=400)
        return ApiResponse(add_product_profile_supplier_option(database_path, route.source, route.external_id, route.position_index, body))
    if path.startswith("/api/tenders/") and path.endswith("/supplier-options/best/select"):
        route = parse_product_profile_supplier_option_best_select_path(path)
        if route is None:
            tender_route = parse_tender_path(path, suffix="product-profiles/supplier-options/best/select")
            if tender_route is None:
                return ApiResponse({"error": "invalid product profile supplier option best select path"}, status=400)
            return ApiResponse(select_best_product_profile_supplier_options(database_path, tender_route.source, tender_route.external_id))
        return ApiResponse(select_best_product_profile_supplier_option(database_path, route.source, route.external_id, route.position_index))
    if path.startswith("/api/tenders/") and path.endswith("/select"):
        route = parse_product_profile_supplier_option_select_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile supplier option select path"}, status=400)
        return ApiResponse(select_product_profile_supplier_option(database_path, route.source, route.external_id, route.position_index, route.option_index))
    if path.startswith("/api/tenders/") and path.endswith("/supplier-search/prepare"):
        route = parse_product_profile_supplier_search_prepare_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile supplier search prepare path"}, status=400)
        return ApiResponse(prepare_product_profile_supplier_search(database_path, route.source, route.external_id, route.position_index))
    if path.startswith("/api/tenders/") and path.endswith("/supplier-catalog-presets"):
        route = parse_product_profile_supplier_catalog_presets_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile supplier catalog presets path"}, status=400)
        return ApiResponse(update_product_profile_supplier_catalog_presets(database_path, route.source, route.external_id, route.position_index, body))
    if path.startswith("/api/tenders/") and path.endswith("/supplier-discovery/candidates"):
        route = parse_product_profile_supplier_discovery_candidates_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile supplier discovery candidates path"}, status=400)
        return ApiResponse(stage_product_profile_supplier_candidates(database_path, route.source, route.external_id, route.position_index, body))
    if path.startswith("/api/tenders/") and path.endswith("/supplier-discovery/run"):
        route = parse_product_profile_supplier_discovery_run_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile supplier discovery run path"}, status=400)
        try:
            return ApiResponse(run_product_profile_supplier_discovery(database_path, route.source, route.external_id, route.position_index))
        except ValueError as exc:
            payload = get_tender_payload(database_path, route.source, route.external_id)
            payload["error"] = str(exc)
            return ApiResponse(payload, status=400)
    if path.startswith("/api/tenders/") and path.endswith("/supplier-discovery/url"):
        route = parse_product_profile_supplier_discovery_url_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile supplier discovery url path"}, status=400)
        try:
            return ApiResponse(run_product_profile_supplier_url_discovery(database_path, route.source, route.external_id, route.position_index, body))
        except ValueError as exc:
            payload = get_tender_payload(database_path, route.source, route.external_id)
            payload["error"] = str(exc)
            return ApiResponse(payload, status=400)
    if path.startswith("/api/tenders/") and path.endswith("/import"):
        route = parse_product_profile_supplier_discovery_candidate_import_path(path)
        if route is None:
            return ApiResponse({"error": "invalid product profile supplier discovery candidate import path"}, status=400)
        return ApiResponse(import_product_profile_supplier_candidate(database_path, route.source, route.external_id, route.position_index, route.candidate_index))
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
            return ApiResponse(review_product_profile_price_candidate(database_path, route.source, route.external_id, route.position_index, route.candidate_id, route.action))
        except ValueError as exc:
            return ApiResponse({"error": str(exc)}, status=400)
        except KeyError as exc:
            return ApiResponse({"error": str(exc)}, status=404)
    return None


__all__ = [
    "accept_product_profile_auto_economics",
    "add_product_profile_supplier_option",
    "apply_tender_auto_prices_request",
    "confirm_ready_tender_price_candidates",
    "handle_economics_post_request",
    "import_product_profile_supplier_candidate",
    "prepare_product_profile_supplier_search",
    "review_product_profile_price_candidate",
    "run_product_profile_supplier_discovery",
    "run_product_profile_supplier_url_discovery",
    "select_best_product_profile_supplier_option",
    "select_best_product_profile_supplier_options",
    "select_product_profile_supplier_option",
    "stage_product_profile_supplier_candidates",
    "stage_tender_price_book_feed_file_request",
    "stage_tender_price_book_feed_request",
    "stage_tender_price_candidate_sources",
    "update_product_profile_auto_economics",
    "update_product_profile_economics",
    "update_product_profile_economics_assumptions",
    "update_product_profile_supplier_catalog_presets",
]
