from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from tender_killer.analysis import analyze_tender_texts
from tender_killer.analysis_evidence_service import build_analysis_evidence_items
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
            SELECT name, url, text_status, text_content
            FROM tender_documents
            WHERE source = ? AND external_id = ? AND text_status = 'ok'
            ORDER BY document_index
            """,
            (source, external_id),
        ).fetchall()
        documents = [dict(row) for row in rows]
        result = analyze_tender_texts([str(row["text_content"] or "") for row in rows])
        raw_payload = result.to_dict()
        raw_payload["evidence_items"] = build_analysis_evidence_items(raw_payload, documents)
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


def _connect(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection
