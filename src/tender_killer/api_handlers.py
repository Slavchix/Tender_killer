from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from tender_killer.analysis_feedback_service import update_analysis_feedback
from tender_killer.analysis_service import analyze_tender_payload
from tender_killer.analysis_workflow_service import update_analysis_workflow
from tender_killer.api_economics_handlers import accept_product_profile_auto_economics
from tender_killer.api_economics_handlers import add_product_profile_supplier_option
from tender_killer.api_economics_handlers import apply_tender_auto_prices_request
from tender_killer.api_economics_handlers import confirm_ready_tender_price_candidates
from tender_killer.api_economics_handlers import handle_economics_post_request
from tender_killer.api_economics_handlers import import_product_profile_supplier_candidate
from tender_killer.api_economics_handlers import prepare_product_profile_supplier_search
from tender_killer.api_economics_handlers import review_product_profile_price_candidate
from tender_killer.api_economics_handlers import run_product_profile_supplier_discovery
from tender_killer.api_economics_handlers import run_product_profile_supplier_url_discovery
from tender_killer.api_economics_handlers import select_best_product_profile_supplier_option
from tender_killer.api_economics_handlers import select_best_product_profile_supplier_options
from tender_killer.api_economics_handlers import select_product_profile_supplier_option
from tender_killer.api_economics_handlers import stage_product_profile_supplier_candidates
from tender_killer.api_economics_handlers import stage_tender_price_book_feed_file_request
from tender_killer.api_economics_handlers import stage_tender_price_book_feed_request
from tender_killer.api_economics_handlers import stage_tender_price_candidate_sources
from tender_killer.api_economics_handlers import update_product_profile_auto_economics
from tender_killer.api_economics_handlers import update_product_profile_economics
from tender_killer.api_economics_handlers import update_product_profile_economics_assumptions
from tender_killer.api_economics_handlers import update_product_profile_supplier_catalog_presets
from tender_killer.api_response import ApiResponse
from tender_killer.api_routes import parse_database_table_path
from tender_killer.api_routes import parse_tender_path
from tender_killer.config import Settings
from tender_killer.dashboard_queue_service import build_dashboard_queues_payload
from tender_killer.database_view_service import get_database_table_payload
from tender_killer.database_view_service import list_database_tables_payload
from tender_killer.document_service import download_tender_documents_payload
from tender_killer.document_service import extract_tender_document_text_payload
from tender_killer.market_state_import_service import import_tender_market_state
from tender_killer.notification_service import send_tender_notification_payload
from tender_killer.price_discovery_job_service import get_tender_price_discovery_job
from tender_killer.price_discovery_job_service import start_tender_price_discovery_job
from tender_killer.price_memory_service import archive_price_memory_entry
from tender_killer.price_memory_service import list_price_memory_payload
from tender_killer.product_profile_service import rebuild_product_profiles as rebuild_product_profiles_from_payload
from tender_killer.report_service import build_tender_report_response as build_tender_report_download_response
from tender_killer.search_service import run_search_payload
from tender_killer.source_run_service import list_source_runs_payload
from tender_killer.supplier_catalog_health_service import get_cached_supplier_catalog_health_payload
from tender_killer.tender_detail_service import get_tender_payload
from tender_killer.tender_detail_service import refresh_tender_detail_payload
from tender_killer.tender_query_service import list_tenders_payload
from tender_killer.workflow_service import save_tender_workflow


SettingsFactory = Callable[[], Settings]
SearchRunner = Any

API_CAPABILITIES: tuple[str, ...] = (
    "supplier_search_prepare",
    "supplier_catalog_presets",
    "supplier_catalog_health",
    "supplier_discovery_url",
    "web_auto_search",
    "market_state_import",
    "dashboard_queues",
    "price_candidate_review",
    "price_candidate_bulk_review",
    "price_candidate_auto_stage",
    "price_memory_manage",
    "price_memory_stage",
    "price_auto_apply",
    "price_book_feed",
    "price_discovery_run",
    "price_discovery_jobs",
    "analysis_workflow",
)


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


def run_tender_price_discovery(database_path: str | Path, source: str, external_id: str) -> dict[str, Any]:
    discovery_run = start_tender_price_discovery_job(database_path, source, external_id)
    payload = get_tender_payload(database_path, source, external_id)
    payload["price_discovery_job"] = discovery_run
    payload["price_discovery_run"] = discovery_run
    return payload


def get_price_discovery_job_payload(database_path: str | Path, job_id: str) -> dict[str, Any]:
    job = get_tender_price_discovery_job(job_id, database_path)
    payload: dict[str, Any] = {"ok": True, "price_discovery_job": job}
    source = str(job.get("source") or "")
    external_id = str(job.get("external_id") or "")
    if source and external_id:
        payload["tender"] = get_tender_payload(database_path, source, external_id)
    return payload


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
    if path == "/api/supplier-catalogs/health":
        return ApiResponse(
            get_cached_supplier_catalog_health_payload(
                database_path,
                live=_truthy_query_value(query.get("live")),
            )
        )
    if path == "/api/dashboard/queues":
        return ApiResponse(build_dashboard_queues_payload(database_path, query))
    if path == "/api/price-memory":
        return ApiResponse(
            list_price_memory_payload(
                database_path,
                limit=_integer_query_value(query.get("limit"), default=50),
            )
        )
    if path.startswith("/api/price-discovery/jobs/"):
        job_id = path.removeprefix("/api/price-discovery/jobs/").strip("/")
        if not job_id or "/" in job_id:
            return ApiResponse({"error": "invalid price discovery job path"}, status=400)
        try:
            return ApiResponse(get_price_discovery_job_payload(database_path, job_id))
        except KeyError as exc:
            return ApiResponse({"error": str(exc)}, status=404)
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
        return ApiResponse({"ok": True, "capabilities": list(API_CAPABILITIES)})
    return ApiResponse({"error": "not found"}, status=404)


def _truthy_query_value(value: str | None) -> bool:
    return str(value or "").casefold() in {"1", "true", "yes", "on"}


def _integer_query_value(value: str | None, *, default: int) -> int:
    try:
        number = int(str(value or "").strip())
    except ValueError:
        return default
    return max(0, number)


def _price_memory_archive_entry_id(path: str) -> int | None:
    prefix = "/api/price-memory/"
    suffix = "/archive"
    if not path.startswith(prefix) or not path.endswith(suffix):
        return None
    raw_entry_id = path.removeprefix(prefix).removesuffix(suffix).strip("/")
    if not raw_entry_id or "/" in raw_entry_id:
        return None
    try:
        return int(raw_entry_id)
    except ValueError:
        return None


def handle_post_request(
    database_path: str | Path,
    path: str,
    body: dict[str, Any],
    settings_factory: SettingsFactory = Settings.from_env,
    search_runner: SearchRunner | None = None,
) -> ApiResponse:
    if path == "/api/search":
        if search_runner is not None:
            payload = search_runner.run(filters_payload=body, trigger="manual")
            if payload.get("status") == "already_running":
                return ApiResponse({**payload, "error": payload.get("message") or "Search is already running."}, status=409)
            return ApiResponse(payload)
        return ApiResponse(run_search_payload(settings_factory(), filters_payload=body))
    if path.startswith("/api/price-memory/") and path.endswith("/archive"):
        entry_id = _price_memory_archive_entry_id(path)
        if entry_id is None:
            return ApiResponse({"error": "invalid price memory archive path"}, status=400)
        reason = str(body.get("reason") or "").strip() or None
        try:
            return ApiResponse(archive_price_memory_entry(database_path, entry_id, reason=reason))
        except KeyError as exc:
            return ApiResponse({"error": str(exc)}, status=404)
    if path.startswith("/api/tenders/") and path.endswith("/analysis/workflow"):
        route = parse_tender_path(path, suffix="analysis/workflow")
        if route is None:
            return ApiResponse({"error": "invalid analysis workflow path"}, status=400)
        try:
            return ApiResponse(update_analysis_workflow(database_path, route.source, route.external_id, body))
        except ValueError as exc:
            return ApiResponse({"error": str(exc)}, status=400)
        except KeyError as exc:
            return ApiResponse({"error": str(exc)}, status=404)
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
    if path.startswith("/api/tenders/") and path.endswith("/analysis/feedback"):
        route = parse_tender_path(path, suffix="analysis/feedback")
        if route is None:
            return ApiResponse({"error": "invalid analysis feedback path"}, status=400)
        try:
            return ApiResponse(update_analysis_feedback(database_path, route.source, route.external_id, body))
        except ValueError as exc:
            return ApiResponse({"error": str(exc)}, status=400)
        except KeyError as exc:
            return ApiResponse({"error": str(exc)}, status=404)
    if path.startswith("/api/tenders/") and path.endswith("/details/refresh"):
        route = parse_tender_path(path, suffix="details/refresh")
        if route is None:
            return ApiResponse({"error": "invalid detail refresh path"}, status=400)
        return ApiResponse(refresh_tender_detail_payload(database_path, route.source, route.external_id))
    if path.startswith("/api/tenders/") and path.endswith("/market-state/import"):
        route = parse_tender_path(path, suffix="market-state/import")
        if route is None:
            return ApiResponse({"error": "invalid market state import path"}, status=400)
        try:
            return ApiResponse(import_tender_market_state(database_path, route.source, route.external_id, body))
        except ValueError as exc:
            return ApiResponse({"error": str(exc)}, status=400)
        except KeyError as exc:
            return ApiResponse({"error": str(exc)}, status=404)
    economics_response = handle_economics_post_request(database_path, path, body)
    if economics_response is not None:
        return economics_response
    if path.startswith("/api/tenders/") and path.endswith("/price-discovery/run"):
        route = parse_tender_path(path, suffix="price-discovery/run")
        if route is None:
            return ApiResponse({"error": "invalid price discovery run path"}, status=400)
        return ApiResponse(run_tender_price_discovery(database_path, route.source, route.external_id))
    if path.startswith("/api/tenders/") and path.endswith("/product-profiles/rebuild"):
        route = parse_tender_path(path, suffix="product-profiles/rebuild")
        if route is None:
            return ApiResponse({"error": "invalid product profiles rebuild path"}, status=400)
        return ApiResponse(rebuild_product_profiles(database_path, route.source, route.external_id))
    return ApiResponse({"error": "not found"}, status=404)
