from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from tender_killer.adapters import MoscowSupplierPortalAdapter
from tender_killer.adapters import MosregMarketAdapter
from tender_killer.document_service import document_row_to_payload
from tender_killer.economics import build_economics_summary
from tender_killer.market_state import extract_market_state
from tender_killer.price_tracking import latest_price_change
from tender_killer.product_profile_service import build_profiles
from tender_killer.product_profile_service import product_profile_summary
from tender_killer.product_profile_service import rebuild_product_profiles as rebuild_product_profiles_from_payload
from tender_killer.schema import ensure_documents_table
from tender_killer.schema import ensure_items_table
from tender_killer.schema import ensure_workflow_table
from tender_killer.storage import TenderStore


def refresh_tender_detail_payload(
    database_path: str | Path,
    source: str,
    external_id: str,
    adapter: Any | None = None,
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    current = get_tender_payload(database_path, source, external_id, include_product_profiles=False)
    raw_payload = _raw_payload_from_tender(current)
    _seed_detail_identifier(raw_payload, source, external_id)
    detail_adapter = adapter or _detail_adapter_for_source(source)
    enriched_payload = detail_adapter.enrich_payload(raw_payload)
    if enriched_payload == raw_payload or not _has_detail_markers(enriched_payload):
        detail = get_tender_payload(database_path, source, external_id)
        return {
            "ok": True,
            "refreshed": False,
            "summary": _detail_refresh_summary(detail),
            "tender": detail,
            "message": "Detail data did not change or source did not return detail payload.",
        }

    refreshed_tender = detail_adapter.normalize_payload(enriched_payload)
    if refreshed_tender.source != source or refreshed_tender.external_id != external_id:
        raise ValueError("Detail adapter returned another tender identity.")
    store.upsert_tender(refreshed_tender)
    profiles_result = rebuild_product_profiles_from_payload(
        database_path,
        source,
        external_id,
        get_tender_payload(database_path, source, external_id, include_product_profiles=False),
    )
    detail = get_tender_payload(database_path, source, external_id)
    return {
        "ok": True,
        "refreshed": True,
        "summary": {
            **_detail_refresh_summary(detail),
            "product_profiles_count": profiles_result["summary"]["total"],
        },
        "tender": detail,
    }


def get_tender_payload(
    database_path: str | Path,
    source: str,
    external_id: str,
    include_product_profiles: bool = True,
) -> dict[str, Any]:
    with _connect(database_path) as connection:
        ensure_workflow_table(connection)
        ensure_items_table(connection)
        ensure_documents_table(connection)
        row = connection.execute(
            """
            SELECT tenders.source, tenders.external_id, url, title, customer, region, price, currency, status,
                   status_normalized, law, region_code, published_at, deadline_at, delivery_place, category, okpd2,
                   source_family, procedure_type, customer_inn,
                   documents_json, raw_payload_json, created_at, tenders.updated_at,
                   COALESCE(workflow.workflow_status, 'new') AS workflow_status,
                   COALESCE(workflow.workflow_note, '') AS workflow_note
            FROM tenders
            LEFT JOIN tender_workflow AS workflow
            ON tenders.source = workflow.source AND tenders.external_id = workflow.external_id
            WHERE tenders.source = ? AND tenders.external_id = ?
            """,
            (source, external_id),
        ).fetchone()
        item_rows = connection.execute(
            """
            SELECT position_index, name, details, quantity, unit, unit_price, total_price,
                   okpd2, classifier_code, classifier_type, raw_payload_json
            FROM tender_items
            WHERE source = ? AND external_id = ?
            ORDER BY position_index
            """,
            (source, external_id),
        ).fetchall()
        document_rows = connection.execute(
            """
            SELECT document_index, name, document_type, url, source_document_id,
                   local_path, downloaded_at, text_status, text_content,
                   text_extracted_at, text_error, raw_payload_json
            FROM tender_documents
            WHERE source = ? AND external_id = ?
            ORDER BY document_index
            """,
            (source, external_id),
        ).fetchall()
        analysis_row = connection.execute(
            """
            SELECT summary, requirements_json, risks_json, red_flags_json,
                   recommended_status, confidence, raw_payload_json, analyzed_at
            FROM tender_analysis
            WHERE source = ? AND external_id = ?
            """,
            (source, external_id),
        ).fetchone()
    if row is None:
        raise KeyError(f"Tender {source}/{external_id} not found.")
    payload = dict(row)
    payload["documents"] = _json_list(payload.pop("documents_json"))
    payload["items"] = [_item_row_to_payload(item_row) for item_row in item_rows]
    payload["document_records"] = [document_row_to_payload(document_row) for document_row in document_rows]
    payload["analysis"] = _analysis_row_to_payload(analysis_row) if analysis_row else None
    if include_product_profiles:
        store = TenderStore(database_path)
        store.initialize()
        product_profiles = store.get_product_profiles(source, external_id)
        if not product_profiles:
            product_profiles = build_profiles(payload)
    else:
        product_profiles = []
    payload["product_profiles"] = product_profiles
    payload["product_profile_summary"] = product_profile_summary(product_profiles)
    payload["market_state"] = extract_market_state(payload)
    payload["economics"] = build_economics_summary(payload)
    payload["price_change"] = latest_price_change(
        database_path, source, external_id, "current_offer"
    ) or latest_price_change(database_path, source, external_id, "nmc")
    return payload


def _raw_payload_from_tender(tender: dict[str, Any]) -> dict[str, Any]:
    raw_payload = tender.get("raw_payload_json")
    if isinstance(raw_payload, str):
        try:
            data = json.loads(raw_payload)
        except json.JSONDecodeError:
            data = {}
    elif isinstance(raw_payload, dict):
        data = raw_payload
    else:
        data = {}
    return dict(data) if isinstance(data, dict) else {}


def _seed_detail_identifier(payload: dict[str, Any], source: str, external_id: str) -> None:
    if source == "moscow_supplier_portal":
        payload.setdefault("auctionId", external_id)
        payload.setdefault("number", external_id)
    elif source == "mosreg_market":
        payload.setdefault("Id", external_id)


def _detail_adapter_for_source(source: str):
    if source == "moscow_supplier_portal":
        return MoscowSupplierPortalAdapter(enrich_details=True)
    if source == "mosreg_market":
        return MosregMarketAdapter(enrich_documents=True, enrich_html=True)
    raise ValueError(f"Unsupported source for detail refresh: {source}")


def _has_detail_markers(payload: dict[str, Any]) -> bool:
    return "__detail" in payload or "__documents" in payload or "__html" in payload


def _detail_refresh_summary(tender: dict[str, Any]) -> dict[str, int]:
    return {
        "items_count": len(tender.get("items") or []),
        "documents_count": len(tender.get("document_records") or []),
        "product_profiles_count": len(tender.get("product_profiles") or []),
    }


def _connect(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def _item_row_to_payload(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    raw_payload_json = payload.pop("raw_payload_json", None)
    payload["raw_payload"] = _json_object(raw_payload_json)
    return payload


def _analysis_row_to_payload(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["requirements"] = _json_list(payload.pop("requirements_json"))
    payload["risks"] = _json_list(payload.pop("risks_json"))
    payload["red_flags"] = _json_list(payload.pop("red_flags_json"))
    payload["raw_payload"] = _json_object(payload.pop("raw_payload_json"))
    payload["checklist"] = payload["raw_payload"].get("checklist", [])
    payload["status"] = payload.pop("recommended_status")
    return payload


def _json_list(value: str | None) -> list[Any]:
    if not value:
        return []
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _json_object(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}
