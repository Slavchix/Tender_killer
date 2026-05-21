from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import httpx

from tender_killer.analysis import analyze_tender_texts
from tender_killer.config import Settings
from tender_killer.documents import DocumentTextExtractor
from tender_killer.filter_store import FilterProfileCollection, FilterProfileStore, NamedFilterProfile
from tender_killer.filters import FilterProfile, MultiProfileTenderFilter
from tender_killer.models import Tender
from tender_killer.models import TenderDocument
from tender_killer.normalization import parse_datetime
from tender_killer.pipeline import PipelineStats, TenderPipeline
from tender_killer.product_profile import build_product_profiles
from tender_killer.reports import build_tender_report_docx, report_filename
from tender_killer.sources import build_adapters_for_collection, normalize_sources
from tender_killer.storage import TenderStore
from tender_killer.telegram import TelegramNotifier, build_tender_message


WORKFLOW_STATUSES = frozenset(("new", "opened", "interesting", "in_progress", "skipped", "archive"))
PRODUCT_PROFILE_SUMMARY_STATUSES = ("draft", "needs_review", "ready", "searching", "matched", "priced", "rejected")
DATABASE_VIEW_TABLES = (
    "tenders",
    "tender_items",
    "tender_documents",
    "tender_analysis",
    "tender_workflow",
    "product_profiles",
)


def list_database_tables_payload(database_path: str | Path) -> dict[str, Any]:
    TenderStore(database_path).initialize()
    with _connect(database_path) as connection:
        _ensure_workflow_table(connection)
        _ensure_items_table(connection)
        _ensure_documents_table(connection)
        _ensure_analysis_table(connection)
        tables = [{"name": table, "rows": _table_count(connection, table)} for table in DATABASE_VIEW_TABLES]
    return {"tables": tables}


def get_database_table_payload(database_path: str | Path, table: str, query: dict[str, str]) -> dict[str, Any]:
    if table not in DATABASE_VIEW_TABLES:
        raise KeyError(f"Table {table} is not allowed.")
    TenderStore(database_path).initialize()
    limit = max(1, min(_int_query(query.get("limit"), 100), 500))
    offset = max(0, _int_query(query.get("offset"), 0))
    search = str(query.get("q") or "").strip()

    with _connect(database_path) as connection:
        _ensure_workflow_table(connection)
        _ensure_items_table(connection)
        _ensure_documents_table(connection)
        _ensure_analysis_table(connection)
        columns = _table_columns(connection, table)
        where_sql = ""
        params: list[Any] = []
        if search and columns:
            where_sql = " WHERE " + " OR ".join([f"CAST({column} AS TEXT) LIKE ?" for column in columns])
            params.extend([f"%{search}%"] * len(columns))
        total = _table_count(connection, table, where_sql, params)
        rows = connection.execute(
            f"SELECT * FROM {table}{where_sql} ORDER BY rowid DESC LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()
    return {
        "table": table,
        "columns": columns,
        "rows": [dict(row) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def list_tenders_payload(database_path: str | Path, query: dict[str, str]) -> dict[str, Any]:
    filters, params = _build_filters(query)
    sql = (
        "SELECT tenders.source, tenders.external_id, url, title, customer, region, price, currency, status, "
        "published_at, deadline_at, delivery_place, category, okpd2, documents_json, raw_payload_json, "
        "tenders.updated_at, COALESCE(workflow.workflow_status, 'new') AS workflow_status, "
        "COALESCE(workflow.workflow_note, '') AS workflow_note, "
        "(SELECT COUNT(*) FROM tender_items AS item_count "
        "WHERE item_count.source = tenders.source AND item_count.external_id = tenders.external_id) AS items_count "
        "FROM tenders "
        "LEFT JOIN tender_workflow AS workflow "
        "ON tenders.source = workflow.source AND tenders.external_id = workflow.external_id"
    )
    if filters:
        sql += " WHERE " + " AND ".join(filters)
    sql += " ORDER BY COALESCE(tenders.deadline_at, tenders.updated_at) DESC LIMIT ?"
    params.append(_int_query(query.get("limit"), 100))

    with _connect(database_path) as connection:
        _ensure_workflow_table(connection)
        _ensure_items_table(connection)
        _ensure_documents_table(connection)
        _ensure_analysis_table(connection)
        rows = connection.execute(sql, params).fetchall()
    items = [_row_to_list_item(row) for row in rows]
    return {"total": len(items), "items": items}


def _product_profile_summary(profiles: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"total": len(profiles), **{status: 0 for status in PRODUCT_PROFILE_SUMMARY_STATUSES}}
    for profile in profiles:
        status = str(profile.get("profile_status") or "")
        if status in PRODUCT_PROFILE_SUMMARY_STATUSES:
            summary[status] += 1
    return summary


def rebuild_product_profiles(database_path: str | Path, source: str, external_id: str) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    tender = get_tender_payload(database_path, source, external_id, include_product_profiles=False)
    profiles = build_product_profiles(tender)
    store.upsert_product_profiles(source, external_id, profiles)
    saved_profiles = store.get_product_profiles(source, external_id)
    return {
        "ok": True,
        "summary": _product_profile_summary(saved_profiles),
        "product_profiles": saved_profiles,
    }


def get_tender_payload(
    database_path: str | Path,
    source: str,
    external_id: str,
    include_product_profiles: bool = True,
) -> dict[str, Any]:
    with _connect(database_path) as connection:
        _ensure_workflow_table(connection)
        _ensure_items_table(connection)
        _ensure_documents_table(connection)
        row = connection.execute(
            """
            SELECT tenders.source, tenders.external_id, url, title, customer, region, price, currency, status,
                   published_at, deadline_at, delivery_place, category, okpd2,
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
    payload["document_records"] = [_document_row_to_payload(document_row) for document_row in document_rows]
    payload["analysis"] = _analysis_row_to_payload(analysis_row) if analysis_row else None
    if include_product_profiles:
        store = TenderStore(database_path)
        store.initialize()
        product_profiles = store.get_product_profiles(source, external_id)
        if not product_profiles:
            product_profiles = build_product_profiles(payload)
    else:
        product_profiles = []
    payload["product_profiles"] = product_profiles
    payload["product_profile_summary"] = _product_profile_summary(product_profiles)
    return payload


def download_tender_documents_payload(
    database_path: str | Path,
    source: str,
    external_id: str,
    documents_dir: str | Path = Path("data/documents"),
    downloader=None,
    document_listing_resolver=None,
) -> dict[str, Any]:
    target_root = Path(documents_dir) / _safe_path_part(source) / _safe_path_part(external_id)
    target_root.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    failed: list[dict[str, str]] = []
    downloader = downloader or _download_file
    document_listing_resolver = document_listing_resolver or _resolve_document_listing

    with _connect(database_path) as connection:
        _ensure_documents_table(connection)
        rows = connection.execute(
            """
            SELECT document_index, name, url
            FROM tender_documents
            WHERE source = ? AND external_id = ?
            ORDER BY document_index
            """,
            (source, external_id),
        ).fetchall()
        if not rows:
            tender_row = connection.execute(
                "SELECT documents_json FROM tenders WHERE source = ? AND external_id = ?",
                (source, external_id),
            ).fetchone()
            if tender_row is None:
                raise KeyError(f"Tender {source}/{external_id} not found.")
            fallback_documents = _json_list(tender_row["documents_json"])
            _insert_fallback_document_rows(connection, source, external_id, fallback_documents)
            rows = connection.execute(
                """
                SELECT document_index, name, url
                FROM tender_documents
                WHERE source = ? AND external_id = ?
                ORDER BY document_index
                """,
                (source, external_id),
            ).fetchall()
        if rows:
            expanded = _expand_document_listing_rows(
                connection,
                source,
                external_id,
                rows,
                document_listing_resolver,
                failed,
            )
            if expanded:
                rows = connection.execute(
                    """
                    SELECT document_index, name, url
                    FROM tender_documents
                    WHERE source = ? AND external_id = ?
                    ORDER BY document_index
                    """,
                    (source, external_id),
                ).fetchall()
        for row in rows:
            filename = _safe_filename(row["name"] or _filename_from_url(row["url"]) or f"document-{row['document_index']}")
            target_path = _unique_target_path(target_root, filename)
            try:
                downloader(row["url"], target_path)
            except Exception as exc:  # noqa: BLE001 - report per-document failure to UI.
                failed.append({"url": row["url"], "error": str(exc)})
                continue
            downloaded += 1
            connection.execute(
                """
                UPDATE tender_documents
                SET name = COALESCE(name, ?), local_path = ?, downloaded_at = ?, text_status = CASE
                    WHEN text_status = 'pending' THEN 'downloaded'
                    ELSE text_status
                END
                WHERE source = ? AND external_id = ? AND url = ?
                """,
                (
                    filename,
                    str(target_path),
                    datetime.now().isoformat(timespec="seconds"),
                    source,
                    external_id,
                    row["url"],
                ),
            )
    detail = get_tender_payload(database_path, source, external_id)
    return {"ok": True, "downloaded": downloaded, "failed": failed, "document_records": detail["document_records"]}


def extract_tender_document_text_payload(
    database_path: str | Path,
    source: str,
    external_id: str,
    extractor: DocumentTextExtractor | None = None,
) -> dict[str, Any]:
    text_extractor = extractor or DocumentTextExtractor()
    extracted_count = 0
    failed: list[dict[str, str]] = []

    with _connect(database_path) as connection:
        _ensure_documents_table(connection)
        exists = connection.execute(
            "SELECT 1 FROM tenders WHERE source = ? AND external_id = ?",
            (source, external_id),
        ).fetchone()
        if exists is None:
            raise KeyError(f"Tender {source}/{external_id} not found.")

        rows = connection.execute(
            """
            SELECT url, local_path
            FROM tender_documents
            WHERE source = ? AND external_id = ?
            ORDER BY document_index
            """,
            (source, external_id),
        ).fetchall()
        for row in rows:
            url = str(row["url"])
            local_path = str(row["local_path"] or "")
            if not local_path or not Path(local_path).exists():
                error = "local file is missing"
                failed.append({"url": url, "error": error})
                connection.execute(
                    """
                    UPDATE tender_documents
                    SET text_status = ?, text_error = ?
                    WHERE source = ? AND external_id = ? AND url = ?
                    """,
                    ("missing_file", error, source, external_id, url),
                )
                continue

            result = text_extractor.extract(local_path)
            text_error = "; ".join(result.warnings)
            connection.execute(
                """
                UPDATE tender_documents
                SET text_status = ?, text_content = ?, text_extracted_at = ?, text_error = ?
                WHERE source = ? AND external_id = ? AND url = ?
                """,
                (
                    result.status,
                    result.text,
                    datetime.now().isoformat(timespec="seconds"),
                    text_error,
                    source,
                    external_id,
                    url,
                ),
            )
            if result.status == "ok":
                extracted_count += 1
            else:
                failed.append({"url": url, "error": text_error or result.status})

    detail = get_tender_payload(database_path, source, external_id)
    return {"ok": True, "extracted": extracted_count, "failed": failed, "document_records": detail["document_records"]}


def analyze_tender_payload(database_path: str | Path, source: str, external_id: str) -> dict[str, Any]:
    with _connect(database_path) as connection:
        _ensure_documents_table(connection)
        _ensure_analysis_table(connection)
        exists = connection.execute(
            "SELECT 1 FROM tenders WHERE source = ? AND external_id = ?",
            (source, external_id),
        ).fetchone()
        if exists is None:
            raise KeyError(f"Tender {source}/{external_id} not found.")
        rows = connection.execute(
            """
            SELECT text_content
            FROM tender_documents
            WHERE source = ? AND external_id = ? AND text_status = 'ok'
            ORDER BY document_index
            """,
            (source, external_id),
        ).fetchall()
        result = analyze_tender_texts([str(row["text_content"] or "") for row in rows])
        raw_payload = result.to_dict()
        connection.execute(
            """
            INSERT INTO tender_analysis (
                source, external_id, summary, requirements_json, risks_json,
                red_flags_json, recommended_status, confidence, raw_payload_json, analyzed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source, external_id) DO UPDATE SET
                summary = excluded.summary,
                requirements_json = excluded.requirements_json,
                risks_json = excluded.risks_json,
                red_flags_json = excluded.red_flags_json,
                recommended_status = excluded.recommended_status,
                confidence = excluded.confidence,
                raw_payload_json = excluded.raw_payload_json,
                analyzed_at = excluded.analyzed_at
            """,
            (
                source,
                external_id,
                result.summary,
                json.dumps(result.requirements, ensure_ascii=False),
                json.dumps(result.risks, ensure_ascii=False),
                json.dumps(result.red_flags, ensure_ascii=False),
                result.status,
                result.confidence,
                json.dumps(raw_payload, ensure_ascii=False),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
    detail = get_tender_payload(database_path, source, external_id)
    return {"ok": True, "analysis": detail["analysis"]}


def build_tender_report_response(database_path: str | Path, source: str, external_id: str) -> dict[str, Any]:
    tender = get_tender_payload(database_path, source, external_id)
    return {
        "body": build_tender_report_docx(tender),
        "filename": report_filename(tender),
        "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }


def update_tender_workflow(
    database_path: str | Path,
    source: str,
    external_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    workflow_status = str(data.get("workflow_status") or "new").strip()
    workflow_note = str(data.get("workflow_note") or "").strip()
    if workflow_status not in WORKFLOW_STATUSES:
        raise ValueError(f"Unknown workflow status: {workflow_status}")
    with _connect(database_path) as connection:
        _ensure_workflow_table(connection)
        exists = connection.execute(
            "SELECT 1 FROM tenders WHERE source = ? AND external_id = ?",
            (source, external_id),
        ).fetchone()
        if exists is None:
            raise KeyError(f"Tender {source}/{external_id} not found.")
        connection.execute(
            """
            INSERT INTO tender_workflow (source, external_id, workflow_status, workflow_note)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(source, external_id) DO UPDATE SET
                workflow_status = excluded.workflow_status,
                workflow_note = excluded.workflow_note,
                updated_at = CURRENT_TIMESTAMP
            """,
            (source, external_id, workflow_status, workflow_note),
        )
    return get_tender_payload(database_path, source, external_id)


def send_tender_notification_payload(
    database_path: str | Path,
    source: str,
    external_id: str,
    settings: Settings,
    notifier: TelegramNotifier | None = None,
) -> dict[str, Any]:
    tender_payload = get_tender_payload(database_path, source, external_id)
    sender = notifier or TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id, dry_run=settings.dry_run)
    tender = _payload_to_tender(tender_payload)
    sent = sender.send(build_tender_message(tender, ["manual:site"]))
    return {"ok": True, "sent": bool(sent)}


def run_search_payload(settings: Settings, runner=None, filters_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    collection = build_search_collection(filters_payload) if filters_payload else None
    stats = runner(settings, collection) if runner else _run_search_from_settings(settings, collection)
    return {
        "ok": True,
        "notifications_enabled": bool(settings.telegram_bot_token and settings.telegram_chat_id),
        "stats": _stats_payload(stats),
    }


def build_search_collection(payload: dict[str, Any] | None) -> FilterProfileCollection:
    data = payload.get("filters", payload) if isinstance(payload, dict) else {}
    data = data if isinstance(data, dict) else {}
    status = str(data.get("status") or "").strip()
    only_active = not status or _is_active_status_query(status)
    statuses = () if only_active else _multi_value_tuple(status)
    keywords = _keywords_from_query(str(data.get("q") or ""))
    profile = FilterProfile(
        keywords=keywords or FilterProfile.DEFAULT_KEYWORDS,
        regions=_region_values(data.get("region")),
        sources=normalize_sources(_multi_value_tuple(data.get("source"))),
        laws=_multi_value_tuple(data.get("law")),
        statuses=statuses,
        okpd2=_multi_value_tuple(data.get("okpd2")),
        min_price=_float_query(data.get("min_price")),
        max_price=_float_query(data.get("max_price")),
        only_active=only_active,
        include_without_price=True,
        include_without_deadline=True,
    )
    return FilterProfileCollection(
        profiles=(NamedFilterProfile(id="site", name="Сайт", profile=profile),),
        active_profile_ids=("site",),
    )


def _run_search_from_settings(settings: Settings, collection: FilterProfileCollection | None = None) -> PipelineStats:
    if collection is None:
        filter_path = settings.filter_profile_path or Path("filters.json")
        filter_store = FilterProfileStore(filter_path)
        collection = filter_store.load_collection()
    pipeline = TenderPipeline(
        adapters=build_adapters_for_collection(collection, settings),
        store=TenderStore(settings.database_path),
        material_filter=MultiProfileTenderFilter(collection),
        notifier=TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id, dry_run=settings.dry_run),
        notify_mode="new_only",
    )
    return pipeline.run()


def _stats_payload(stats: PipelineStats) -> dict[str, Any]:
    return {
        "fetched": stats.fetched,
        "saved": stats.saved,
        "matched": stats.matched,
        "notified": stats.notified,
        "failed_sources": stats.failed_sources,
        "failed_source_names": list(stats.failed_source_names),
        "failed_source_errors": list(stats.failed_source_errors),
    }


def _build_filters(query: dict[str, str]) -> tuple[list[str], list[Any]]:
    filters: list[str] = []
    params: list[Any] = []

    if source_values := _source_query_values(query.get("source")):
        filters.append(_in_clause("tenders.source", source_values))
        params.extend(source_values)
    if region_values := _region_values(query.get("region")):
        region_filters, region_params = _text_like_any("tenders.region", region_values)
        filters.append(region_filters)
        params.extend(region_params)
    if status := query.get("status"):
        if _is_active_status_query(status):
            filters.append(
                "("
                + " OR ".join(
                    [
                        "COALESCE(tenders.status, '') LIKE ?",
                        "COALESCE(tenders.status, '') LIKE ?",
                        "COALESCE(tenders.status, '') LIKE ?",
                        "COALESCE(tenders.status, '') LIKE ?",
                    ]
                )
                + ")"
            )
            params.extend(["%Актив%", "%актив%", "%Прием%", "%Приём%"])
        else:
            status_filters, status_params = _text_like_any("tenders.status", status)
            filters.append(status_filters)
            params.extend(status_params)
    if okpd2_values := _multi_value_tuple(query.get("okpd2")):
        filters.append(
            "("
            + " OR ".join(
                [
                    "COALESCE(tenders.okpd2, '') LIKE ?",
                    (
                        "EXISTS (SELECT 1 FROM tender_items AS okpd_item "
                        "WHERE okpd_item.source = tenders.source "
                        "AND okpd_item.external_id = tenders.external_id "
                        "AND COALESCE(okpd_item.okpd2, '') LIKE ?)"
                    ),
                ]
                * len(okpd2_values)
            )
            + ")"
        )
        for okpd2 in okpd2_values:
            params.extend([f"{okpd2}%", f"{okpd2}%"])
    if law_values := _law_query_values(query.get("law")):
        filters.append("(" + " OR ".join(["LOWER(COALESCE(tenders.raw_payload_json, '')) LIKE ?"] * len(law_values)) + ")")
        params.extend([f"%{law}%" for law in law_values])
    if min_price := _float_query(query.get("min_price")):
        filters.append("tenders.price >= ?")
        params.append(min_price)
    if max_price := _float_query(query.get("max_price")):
        filters.append("tenders.price <= ?")
        params.append(max_price)
    if search := query.get("q"):
        filters.append(
            "(LOWER(tenders.title) LIKE ? OR LOWER(COALESCE(tenders.customer, '')) LIKE ? "
            "OR LOWER(COALESCE(tenders.raw_payload_json, '')) LIKE ?)"
        )
        needle = f"%{search.lower()}%"
        params.extend([needle, needle, needle])
    if workflow_status := query.get("workflow_status"):
        filters.append("COALESCE(workflow.workflow_status, 'new') = ?")
        params.append(workflow_status)
    return filters, params


def _keywords_from_query(value: str) -> tuple[str, ...]:
    parts = re.split(r"[,;\n]+", value)
    return tuple(part.strip() for part in parts if part.strip())


def _multi_value_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple, set)):
        candidates = [str(item) for item in value]
    else:
        candidates = re.split(r"[,;\n]+", str(value or ""))
    return tuple(part.strip() for part in candidates if part and part.strip())


def _region_values(value: Any) -> tuple[str, ...]:
    regions: list[str] = []
    for region in _multi_value_tuple(value):
        normalized = region.casefold().replace("ё", "е")
        if normalized in {"москва + мо", "москва и мо", "москва, мо", "мск + мо"}:
            candidates = ("Москва", "Московская область")
        else:
            candidates = (region,)
        for candidate in candidates:
            if candidate not in regions:
                regions.append(candidate)
    return tuple(regions)


def _source_query_values(value: Any) -> tuple[str, ...]:
    source_map = {
        "moscow": "moscow_supplier_portal",
        "moscow_supplier_portal": "moscow_supplier_portal",
        "mosreg": "mosreg_market",
        "mo": "mosreg_market",
        "mosreg_market": "mosreg_market",
    }
    sources: list[str] = []
    for source in _multi_value_tuple(value):
        normalized = source.strip().casefold()
        mapped = source_map.get(normalized, source)
        if mapped not in sources:
            sources.append(mapped)
    return tuple(sources)


def _in_clause(field: str, values: tuple[str, ...]) -> str:
    placeholders = ", ".join(["?"] * len(values))
    return f"{field} IN ({placeholders})"


def _is_active_status_query(value: str) -> bool:
    normalized = value.strip().casefold().replace("ё", "е")
    return normalized in {"active", "актив", "активные", "прием", "прием заявок", "прием предложений"}


def _text_like_any(field: str, values: str | tuple[str, ...]) -> tuple[str, list[Any]]:
    variants = _text_variants(values)
    clause = "(" + " OR ".join([f"COALESCE({field}, '') LIKE ?" for _ in variants]) + ")"
    return clause, [f"%{variant}%" for variant in variants]


def _text_variants(values: str | tuple[str, ...]) -> tuple[str, ...]:
    variants = []
    for value in (values if isinstance(values, tuple) else (values,)):
        text = value.strip()
        if not text:
            continue
        for candidate in (text, text.casefold(), text.upper(), text[:1].upper() + text[1:].casefold()):
            if candidate and candidate not in variants:
                variants.append(candidate)
    if not variants:
        return ("",)
    return tuple(variants)


def _row_to_list_item(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    documents = _json_list(payload.pop("documents_json"))
    raw_payload_json = payload.pop("raw_payload_json", None)
    payload["documents_count"] = len(documents)
    payload["law"] = _law_label(raw_payload_json)
    return payload


def _payload_to_tender(payload: dict[str, Any]) -> Tender:
    return Tender(
        source=payload["source"],
        external_id=payload["external_id"],
        url=payload["url"],
        title=payload["title"],
        customer=payload.get("customer"),
        region=payload.get("region"),
        price=payload.get("price"),
        currency=payload.get("currency") or "RUB",
        status=payload.get("status"),
        published_at=parse_datetime(payload.get("published_at")),
        deadline_at=parse_datetime(payload.get("deadline_at")),
        delivery_place=payload.get("delivery_place"),
        category=payload.get("category"),
        okpd2=payload.get("okpd2"),
        documents=payload.get("documents") or [],
        document_records=[
            TenderDocument(
                url=document["url"],
                name=document.get("name"),
                document_type=document.get("document_type"),
                source_document_id=document.get("source_document_id"),
                local_path=document.get("local_path"),
                downloaded_at=parse_datetime(document.get("downloaded_at")),
                text_status=document.get("text_status") or "pending",
                raw_payload=document.get("raw_payload") or {},
            )
            for document in payload.get("document_records") or []
            if document.get("url")
        ],
        raw_payload=_json_object(payload.get("raw_payload_json")),
    )


def _json_list(value: str | None) -> list[Any]:
    if not value:
        return []
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _connect(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_workflow_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tender_workflow (
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            workflow_status TEXT NOT NULL DEFAULT 'new',
            workflow_note TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (source, external_id)
        )
        """
    )


def _ensure_items_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tender_items (
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            position_index INTEGER NOT NULL,
            name TEXT NOT NULL,
            details TEXT,
            quantity REAL,
            unit TEXT,
            unit_price REAL,
            total_price REAL,
            okpd2 TEXT,
            classifier_code TEXT,
            classifier_type TEXT,
            raw_payload_json TEXT NOT NULL,
            PRIMARY KEY (source, external_id, position_index)
        )
        """
    )
    _ensure_item_classifier_columns(connection)


def _ensure_item_classifier_columns(connection: sqlite3.Connection) -> None:
    columns = {str(row["name"]) for row in connection.execute("PRAGMA table_info(tender_items)").fetchall()}
    for column in ("classifier_code", "classifier_type"):
        if column not in columns:
            connection.execute(f"ALTER TABLE tender_items ADD COLUMN {column} TEXT")


def _ensure_documents_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tender_documents (
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            document_index INTEGER NOT NULL,
            name TEXT,
            document_type TEXT,
            url TEXT NOT NULL,
            source_document_id TEXT,
            local_path TEXT,
            downloaded_at TEXT,
            text_status TEXT NOT NULL DEFAULT 'pending',
            text_content TEXT,
            text_extracted_at TEXT,
            text_error TEXT,
            raw_payload_json TEXT NOT NULL,
            PRIMARY KEY (source, external_id, url)
        )
        """
    )
    _ensure_document_text_columns(connection)


def _ensure_analysis_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tender_analysis (
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            summary TEXT NOT NULL,
            requirements_json TEXT NOT NULL,
            risks_json TEXT NOT NULL,
            red_flags_json TEXT NOT NULL,
            recommended_status TEXT NOT NULL,
            confidence REAL NOT NULL,
            raw_payload_json TEXT NOT NULL,
            analyzed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (source, external_id)
        )
        """
    )


def _ensure_document_text_columns(connection: sqlite3.Connection) -> None:
    columns = {str(row["name"]) for row in connection.execute("PRAGMA table_info(tender_documents)").fetchall()}
    for column, definition in {
        "text_content": "TEXT",
        "text_extracted_at": "TEXT",
        "text_error": "TEXT",
    }.items():
        if column not in columns:
            connection.execute(f"ALTER TABLE tender_documents ADD COLUMN {column} {definition}")


def _item_row_to_payload(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    raw_payload_json = payload.pop("raw_payload_json", None)
    payload["raw_payload"] = _json_object(raw_payload_json)
    return payload


def _document_row_to_payload(row: sqlite3.Row) -> dict[str, Any]:
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
    payload["status"] = payload.pop("recommended_status")
    return payload


def _insert_fallback_document_rows(
    connection: sqlite3.Connection,
    source: str,
    external_id: str,
    documents: list[Any],
) -> None:
    rows = [
        {
            "source": source,
            "external_id": external_id,
            "document_index": index,
            "name": _filename_from_url(url) or f"document-{index}",
            "document_type": None,
            "url": url,
            "source_document_id": None,
            "raw_payload_json": "{}",
        }
        for index, url in enumerate(documents, start=1)
        if isinstance(url, str) and url
    ]
    if not rows:
        return
    connection.executemany(
        """
        INSERT OR IGNORE INTO tender_documents (
            source, external_id, document_index, name, document_type, url,
            source_document_id, raw_payload_json
        )
        VALUES (
            :source, :external_id, :document_index, :name, :document_type, :url,
            :source_document_id, :raw_payload_json
        )
        """,
        rows,
    )


def _expand_document_listing_rows(
    connection: sqlite3.Connection,
    source: str,
    external_id: str,
    rows: list[sqlite3.Row],
    resolver,
    failed: list[dict[str, str]],
) -> bool:
    expanded_any = False
    for row in rows:
        url = str(row["url"] or "")
        if not _is_document_listing_url(url):
            continue
        try:
            documents = resolver(url)
        except Exception as exc:  # noqa: BLE001 - surface source errors to the UI.
            failed.append({"url": url, "error": str(exc)})
            continue
        records = _document_rows_from_listing(source, external_id, documents)
        if not records:
            continue
        connection.execute(
            "DELETE FROM tender_documents WHERE source = ? AND external_id = ? AND url = ?",
            (source, external_id, url),
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO tender_documents (
                source, external_id, document_index, name, document_type, url,
                source_document_id, raw_payload_json
            )
            VALUES (
                :source, :external_id, :document_index, :name, :document_type, :url,
                :source_document_id, :raw_payload_json
            )
            """,
            records,
        )
        expanded_any = True
    return expanded_any


def _document_rows_from_listing(
    source: str,
    external_id: str,
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, document in enumerate(documents, start=1):
        url = document.get("Url") or document.get("url") or document.get("href") or document.get("downloadUrl")
        if not url:
            continue
        rows.append(
            {
                "source": source,
                "external_id": external_id,
                "document_index": index,
                "name": document.get("FileName") or document.get("UserFileNameFromOuterSystem") or document.get("name"),
                "document_type": document.get("Type") or document.get("type") or document.get("DocumentType"),
                "url": str(url),
                "source_document_id": str(document.get("Id") or document.get("id") or "") or None,
                "raw_payload_json": json.dumps(document, ensure_ascii=False),
            }
        )
    return rows


def _is_document_listing_url(url: str) -> bool:
    return "/GetTradeDocuments" in url


def _resolve_document_listing(url: str) -> list[dict[str, Any]]:
    response = httpx.get(
        url,
        headers={"Accept": "application/json, text/plain, */*", "XXX-TenantId-Header": "2"},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def _json_object(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _table_columns(connection: sqlite3.Connection, table: str) -> list[str]:
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return [str(row["name"]) for row in rows]


def _table_count(
    connection: sqlite3.Connection,
    table: str,
    where_sql: str = "",
    params: list[Any] | None = None,
) -> int:
    row = connection.execute(f"SELECT COUNT(*) FROM {table}{where_sql}", params or []).fetchone()
    return int(row[0]) if row else 0


def _download_file(url: str, target_path: Path) -> None:
    with httpx.stream("GET", url, follow_redirects=True, timeout=60) as response:
        response.raise_for_status()
        with target_path.open("wb") as file:
            for chunk in response.iter_bytes():
                file.write(chunk)


def _safe_path_part(value: str) -> str:
    return re.sub(r"[^A-Za-zА-Яа-я0-9_.-]+", "_", value).strip("._") or "item"


def _safe_filename(value: str) -> str:
    name = Path(value.replace("\\", "/")).name
    safe = re.sub(r"[^A-Za-zА-Яа-я0-9_.() -]+", "_", name).strip()
    return safe or "document"


def _unique_target_path(directory: Path, filename: str) -> Path:
    target = directory / filename
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    index = 2
    while True:
        candidate = directory / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def _filename_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    for key in ("fileName", "name"):
        if key in query and query[key]:
            return query[key][-1]
    name = Path(unquote(parsed.path)).name
    return name or None


def _int_query(value: str | None, default: int) -> int:
    try:
        return int(value) if value else default
    except ValueError:
        return default


def _float_query(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


def _law_query_values(value: Any) -> tuple[str, ...]:
    laws: list[str] = []
    for law in _multi_value_tuple(value):
        digits = re.sub(r"\D+", "", law)
        if "223" in digits:
            normalized = "223"
        elif "44" in digits:
            normalized = "44"
        else:
            normalized = law.lower()
        if normalized not in laws:
            laws.append(normalized)
    return tuple(laws)


def _law_label(raw_payload_json: str | None) -> str | None:
    if not raw_payload_json:
        return None
    digits = re.sub(r"\D+", "", raw_payload_json)
    if "223" in digits:
        return "223-ФЗ"
    if "44" in digits:
        return "44-ФЗ"
    return None


class TenderApiHandler(BaseHTTPRequestHandler):
    database_path: Path

    def do_GET(self) -> None:  # noqa: N802 - stdlib API name.
        parsed = urlparse(self.path)
        query = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
        try:
            if parsed.path == "/api/db/tables":
                self._send_json(list_database_tables_payload(self.database_path))
                return
            if parsed.path.startswith("/api/db/tables/"):
                parts = parsed.path.split("/")
                if len(parts) != 5:
                    self._send_json({"error": "invalid database table path"}, status=400)
                    return
                self._send_json(get_database_table_payload(self.database_path, unquote(parts[4]), query))
                return
            if parsed.path == "/api/tenders":
                self._send_json(list_tenders_payload(self.database_path, query))
                return
            if parsed.path.startswith("/api/tenders/") and parsed.path.endswith("/report.docx"):
                parts = parsed.path.split("/")
                if len(parts) != 6:
                    self._send_json({"error": "invalid report path"}, status=400)
                    return
                source, external_id = unquote(parts[3]), unquote(parts[4])
                self._send_binary(build_tender_report_response(self.database_path, source, external_id))
                return
            if parsed.path.startswith("/api/tenders/") and parsed.path.endswith("/product-profiles"):
                parts = parsed.path.split("/")
                if len(parts) != 6:
                    self._send_json({"error": "invalid product profiles path"}, status=400)
                    return
                source, external_id = unquote(parts[3]), unquote(parts[4])
                detail = get_tender_payload(self.database_path, source, external_id)
                self._send_json(
                    {
                        "ok": True,
                        "summary": detail["product_profile_summary"],
                        "product_profiles": detail["product_profiles"],
                    }
                )
                return
            if parsed.path.startswith("/api/tenders/"):
                parts = parsed.path.split("/")
                if len(parts) != 5:
                    self._send_json({"error": "invalid tender path"}, status=400)
                    return
                source, external_id = parts[3], parts[4]
                self._send_json(get_tender_payload(self.database_path, unquote(source), unquote(external_id)))
                return
            if parsed.path == "/api/health":
                self._send_json({"ok": True})
                return
            self._send_json({"error": "not found"}, status=404)
        except KeyError as exc:
            self._send_json({"error": str(exc)}, status=404)
        except Exception as exc:  # noqa: BLE001 - API must return JSON errors in local dev.
            self._send_json({"error": str(exc)}, status=500)

    def do_POST(self) -> None:  # noqa: N802 - stdlib API name.
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/search":
                self._send_json(run_search_payload(Settings.from_env(), filters_payload=self._read_json_body()))
                return
            if parsed.path.startswith("/api/tenders/") and parsed.path.endswith("/workflow"):
                parts = parsed.path.split("/")
                if len(parts) != 6:
                    self._send_json({"error": "invalid workflow path"}, status=400)
                    return
                source, external_id = unquote(parts[3]), unquote(parts[4])
                payload = self._read_json_body()
                self._send_json(update_tender_workflow(self.database_path, source, external_id, payload))
                return
            if parsed.path.startswith("/api/tenders/") and parsed.path.endswith("/notify"):
                parts = parsed.path.split("/")
                if len(parts) != 6:
                    self._send_json({"error": "invalid notify path"}, status=400)
                    return
                source, external_id = unquote(parts[3]), unquote(parts[4])
                self._send_json(
                    send_tender_notification_payload(
                        self.database_path,
                        source,
                        external_id,
                        Settings.from_env(),
                    )
                )
                return
            if parsed.path.startswith("/api/tenders/") and parsed.path.endswith("/documents/download"):
                parts = parsed.path.split("/")
                if len(parts) != 7:
                    self._send_json({"error": "invalid documents download path"}, status=400)
                    return
                source, external_id = unquote(parts[3]), unquote(parts[4])
                self._send_json(download_tender_documents_payload(self.database_path, source, external_id))
                return
            if parsed.path.startswith("/api/tenders/") and parsed.path.endswith("/documents/extract-text"):
                parts = parsed.path.split("/")
                if len(parts) != 7:
                    self._send_json({"error": "invalid documents extract path"}, status=400)
                    return
                source, external_id = unquote(parts[3]), unquote(parts[4])
                self._send_json(extract_tender_document_text_payload(self.database_path, source, external_id))
                return
            if parsed.path.startswith("/api/tenders/") and parsed.path.endswith("/analysis/run"):
                parts = parsed.path.split("/")
                if len(parts) != 7:
                    self._send_json({"error": "invalid analysis path"}, status=400)
                    return
                source, external_id = unquote(parts[3]), unquote(parts[4])
                self._send_json(analyze_tender_payload(self.database_path, source, external_id))
                return
            if parsed.path.startswith("/api/tenders/") and parsed.path.endswith("/product-profiles/rebuild"):
                parts = parsed.path.split("/")
                if len(parts) != 7:
                    self._send_json({"error": "invalid product profiles rebuild path"}, status=400)
                    return
                source, external_id = unquote(parts[3]), unquote(parts[4])
                self._send_json(rebuild_product_profiles(self.database_path, source, external_id))
                return
            self._send_json({"error": "not found"}, status=404)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=400)
        except KeyError as exc:
            self._send_json({"error": str(exc)}, status=404)
        except Exception as exc:  # noqa: BLE001 - API must return JSON errors in local dev.
            self._send_json({"error": str(exc)}, status=500)

    def do_OPTIONS(self) -> None:  # noqa: N802 - stdlib API name.
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        if length > 65536:
            raise ValueError("Request body is too large.")
        data = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Request body must be a JSON object.")
        return data

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_binary(self, payload: dict[str, Any], status: int = 200) -> None:
        body = payload["body"]
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", payload["content_type"])
        self.send_header("Content-Disposition", f'attachment; filename="{payload["filename"]}"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def run_server(host: str, port: int, database_path: Path) -> None:
    handler = type("ConfiguredTenderApiHandler", (TenderApiHandler,), {"database_path": database_path})
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Tender Killer API: http://{host}:{port}")
    print(f"SQLite: {database_path}")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(prog="tender-killer-api")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db", type=Path)
    args = parser.parse_args()

    settings = Settings.from_env()
    run_server(args.host, args.port, args.db or settings.database_path)


if __name__ == "__main__":
    main()
