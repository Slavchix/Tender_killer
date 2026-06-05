from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from tender_killer.analysis import analyze_tender_texts
from tender_killer.analysis_document_context import annotate_document_roles
from tender_killer.analysis_document_context import build_document_coverage
from tender_killer.analysis_document_context import document_roles_summary
from tender_killer.analysis_evidence_service import build_analysis_evidence_items
from tender_killer.analysis_facts_service import build_analysis_facts
from tender_killer.analysis_missing_checks import build_missing_checks
from tender_killer.analysis_missing_checks import missing_checklist_items
from tender_killer.analysis_operator_view_service import build_analysis_operator_view
from tender_killer.analysis_passport_service import build_analysis_tz_passport
from tender_killer.analysis_source_service import attach_document_sources
from tender_killer.analysis_text_index_service import build_analysis_text_index
from tender_killer.schema import ensure_analysis_table
from tender_killer.schema import ensure_documents_table
from tender_killer.tender_detail_service import get_tender_payload


def analyze_tender_payload(database_path: str | Path, source: str, external_id: str) -> dict[str, Any]:
    with _connect(database_path) as connection:
        ensure_documents_table(connection)
        ensure_analysis_table(connection)
        exists = connection.execute(
            "SELECT 1 FROM tenders WHERE source = ? AND external_id = ?",
            (source, external_id),
        ).fetchone()
        if exists is None:
            raise KeyError(f"Tender {source}/{external_id} not found.")
        rows = connection.execute(
            """
            SELECT name, url, document_type, text_status, text_content, text_error
            FROM tender_documents
            WHERE source = ? AND external_id = ?
            ORDER BY document_index
            """,
            (source, external_id),
        ).fetchall()
        documents = annotate_document_roles([dict(row) for row in rows])
        ready_documents = [
            document
            for document in documents
            if str(document.get("text_status") or "").strip().casefold() == "ok"
            and str(document.get("text_content") or "").strip()
        ]
        document_coverage = build_document_coverage(documents)
        document_roles = document_roles_summary(documents)
        result = analyze_tender_texts([str(document["text_content"] or "") for document in ready_documents])
        _apply_document_coverage_gate(result, document_coverage)
        raw_payload = result.to_dict()
        missing_checks = build_missing_checks(raw_payload)
        raw_payload["missing_checks"] = missing_checks
        raw_payload["checklist"] = [
            *raw_payload.get("checklist", []),
            *missing_checklist_items(missing_checks),
        ]
        raw_payload["document_coverage"] = document_coverage
        raw_payload["document_roles"] = document_roles
        raw_payload["text_index"] = build_analysis_text_index(documents)
        attach_document_sources(raw_payload, ready_documents)
        raw_payload["analysis_facts"] = build_analysis_facts(raw_payload, documents)
        raw_payload["tz_passport"] = build_analysis_tz_passport(raw_payload, documents)
        raw_payload["evidence_items"] = build_analysis_evidence_items(raw_payload, documents)
        raw_payload["operator_view"] = build_analysis_operator_view(raw_payload, documents)
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


def _apply_document_coverage_gate(result, coverage: dict[str, Any]) -> None:
    if coverage.get("status") == "complete":
        return
    total = int(coverage.get("total") or 0)
    ready = int(coverage.get("ready") or 0)
    summary = str(coverage.get("summary") or "").strip()
    missing_names = [
        str(item.get("name") or "").strip()
        for item in coverage.get("not_ready", [])
        if isinstance(item, dict) and str(item.get("name") or "").strip()
    ]
    label = "Неполный анализ документов" if total else "Документы для анализа не найдены"
    if label not in result.red_flags:
        result.red_flags.insert(0, label)
    evidence = summary
    if missing_names:
        evidence = f"{summary} Проверьте документы: {', '.join(missing_names[:5])}."
    result.checklist.insert(
        0,
        {
            "type": "document_coverage",
            "label": label,
            "category": "documents",
            "severity": "high",
            "evidence": evidence,
        },
    )
    result.confidence = min(result.confidence, 0.55 if ready else 0.25)
    if summary:
        result.summary = f"{summary} Анализ ниже построен только по прочитанным документам."


def _connect(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection
