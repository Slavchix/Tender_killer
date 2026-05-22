from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tender_killer.analysis_service import analyze_tender_payload
from tender_killer.api_routes import parse_database_table_path
from tender_killer.api_routes import parse_product_profile_economics_path
from tender_killer.api_routes import parse_product_profile_supplier_options_path
from tender_killer.api_routes import parse_tender_path
from tender_killer.config import Settings
from tender_killer.database_view_service import get_database_table_payload
from tender_killer.database_view_service import list_database_tables_payload
from tender_killer.document_service import download_tender_documents_payload
from tender_killer.document_service import extract_tender_document_text_payload
from tender_killer.economics_service import update_profile_economics as update_profile_economics_inputs
from tender_killer.notification_service import send_tender_notification_payload
from tender_killer.product_profile_service import rebuild_product_profiles as rebuild_product_profiles_from_payload
from tender_killer.report_service import build_tender_report_response as build_tender_report_download_response
from tender_killer.search_service import run_search_payload
from tender_killer.source_run_service import list_source_runs_payload
from tender_killer.supplier_option_service import add_profile_supplier_option
from tender_killer.tender_detail_service import get_tender_payload
from tender_killer.tender_detail_service import refresh_tender_detail_payload
from tender_killer.workflow_service import save_tender_workflow


@dataclass(frozen=True)
class ApiResponse:
    payload: dict[str, Any]
    status: int = 200
    kind: str = "json"


SettingsFactory = Callable[[], Settings]


def rebuild_product_profiles(database_path: str | Path, source: str, external_id: str) -> dict[str, Any]:
    tender = get_tender_payload(database_path, source, external_id, include_product_profiles=False)
    return rebuild_product_profiles_from_payload(database_path, source, external_id, tender)


def build_tender_report_response(database_path: str | Path, source: str, external_id: str) -> dict[str, Any]:
    tender = get_tender_payload(database_path, source, external_id)
    return build_tender_report_download_response(tender)


def update_tender_workflow(
    database_path: str | Path,
    source: str,
    external_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    save_tender_workflow(database_path, source, external_id, data)
    return get_tender_payload(database_path, source, external_id)


def update_product_profile_economics(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    data: dict[str, Any],
) -> dict[str, Any]:
    update_profile_economics_inputs(database_path, source, external_id, position_index, data)
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


def handle_get_request(database_path: str | Path, path: str, query: dict[str, str]) -> ApiResponse:
    if path == "/api/db/tables":
        return ApiResponse(list_database_tables_payload(database_path))
    if path.startswith("/api/db/tables/"):
        table_name = parse_database_table_path(path)
        if table_name is None:
            return ApiResponse({"error": "invalid database table path"}, status=400)
        return ApiResponse(get_database_table_payload(database_path, table_name, query))
    if path == "/api/sources/status":
        return ApiResponse(list_source_runs_payload(database_path))
    if path == "/api/tenders":
        return ApiResponse(list_tenders_payload(database_path, query))
    if path.startswith("/api/tenders/") and path.endswith("/report.docx"):
        route = parse_tender_path(path, suffix="report.docx")
        if route is None:
            return ApiResponse({"error": "invalid report path"}, status=400)
        return ApiResponse(build_tender_report_response(database_path, route.source, route.external_id), kind="binary")
    if path.startswith("/api/tenders/") and path.endswith("/product-profiles"):
        route = parse_tender_path(path, suffix="product-profiles")
        if route is None:
            return ApiResponse({"error": "invalid product profiles path"}, status=400)
        detail = get_tender_payload(database_path, route.source, route.external_id)
        return ApiResponse(
            {
                "ok": True,
                "summary": detail["product_profile_summary"],
                "product_profiles": detail["product_profiles"],
            }
        )
    if path.startswith("/api/tenders/"):
        route = parse_tender_path(path)
        if route is None:
            return ApiResponse({"error": "invalid tender path"}, status=400)
        return ApiResponse(get_tender_payload(database_path, route.source, route.external_id))
    if path == "/api/health":
        return ApiResponse({"ok": True})
    return ApiResponse({"error": "not found"}, status=404)


def handle_post_request(
    database_path: str | Path,
    path: str,
    body: dict[str, Any],
    settings_factory: SettingsFactory = Settings.from_env,
) -> ApiResponse:
    if path == "/api/search":
        return ApiResponse(run_search_payload(settings_factory(), filters_payload=body))
    if path.startswith("/api/tenders/") and path.endswith("/workflow"):
        route = parse_tender_path(path, suffix="workflow")
        if route is None:
            return ApiResponse({"error": "invalid workflow path"}, status=400)
        return ApiResponse(update_tender_workflow(database_path, route.source, route.external_id, body))
    if path.startswith("/api/tenders/") and path.endswith("/notify"):
        route = parse_tender_path(path, suffix="notify")
        if route is None:
            return ApiResponse({"error": "invalid notify path"}, status=400)
        return ApiResponse(
            send_tender_notification_payload(
                database_path,
                route.source,
                route.external_id,
                settings_factory(),
            )
        )
    if path.startswith("/api/tenders/") and path.endswith("/documents/download"):
        route = parse_tender_path(path, suffix="documents/download")
        if route is None:
            return ApiResponse({"error": "invalid documents download path"}, status=400)
        return ApiResponse(download_tender_documents_payload(database_path, route.source, route.external_id))
    if path.startswith("/api/tenders/") and path.endswith("/documents/extract-text"):
        route = parse_tender_path(path, suffix="documents/extract-text")
        if route is None:
            return ApiResponse({"error": "invalid documents extract path"}, status=400)
        return ApiResponse(extract_tender_document_text_payload(database_path, route.source, route.external_id))
    if path.startswith("/api/tenders/") and path.endswith("/analysis/run"):
        route = parse_tender_path(path, suffix="analysis/run")
        if route is None:
            return ApiResponse({"error": "invalid analysis path"}, status=400)
        return ApiResponse(analyze_tender_payload(database_path, route.source, route.external_id))
    if path.startswith("/api/tenders/") and path.endswith("/details/refresh"):
        route = parse_tender_path(path, suffix="details/refresh")
        if route is None:
            return ApiResponse({"error": "invalid detail refresh path"}, status=400)
        return ApiResponse(refresh_tender_detail_payload(database_path, route.source, route.external_id))
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
    if path.startswith("/api/tenders/") and path.endswith("/product-profiles/rebuild"):
        route = parse_tender_path(path, suffix="product-profiles/rebuild")
        if route is None:
            return ApiResponse({"error": "invalid product profiles rebuild path"}, status=400)
        return ApiResponse(rebuild_product_profiles(database_path, route.source, route.external_id))
    return ApiResponse({"error": "not found"}, status=404)
