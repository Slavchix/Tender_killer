from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from tender_killer.schema import ensure_analysis_table


TZ_WORKFLOW_STATUSES: tuple[dict[str, str], ...] = (
    {"id": "documents_not_downloaded", "label": "документы не скачаны"},
    {"id": "text_extracted", "label": "текст извлечен"},
    {"id": "analysis_ready", "label": "анализ готов"},
    {"id": "operator_verified", "label": "оператор проверил"},
    {"id": "has_blockers", "label": "есть блокеры"},
)
TZ_WORKFLOW_STATUS_IDS = {status["id"] for status in TZ_WORKFLOW_STATUSES}


def build_analysis_tz_workflow(
    analysis: dict[str, Any],
    document_state: dict[str, Any],
    metrics: dict[str, Any],
    *,
    status: str,
) -> dict[str, Any]:
    raw = analysis.get("tz_workflow") if isinstance(analysis, dict) else None
    if not isinstance(raw, dict) and isinstance(analysis.get("raw_payload"), dict):
        raw = analysis["raw_payload"].get("tz_workflow")
    raw = raw if isinstance(raw, dict) else {}
    derived_status = _derive_status(raw, document_state, metrics, analysis, status=status)
    return {
        "version": 1,
        "status": derived_status,
        "status_label": _status_label(derived_status),
        "statuses": _status_steps(derived_status),
        "responsible": _text(raw.get("responsible")),
        "deadline": _text(raw.get("deadline")),
        "comment": _text(raw.get("comment")),
        "comments": _comments(raw),
        "journal": _journal(raw),
    }


def update_analysis_workflow(
    database_path: str | Path,
    source: str,
    external_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    requested_status = _text(data.get("status"))
    if requested_status and requested_status not in TZ_WORKFLOW_STATUS_IDS:
        raise ValueError(f"Unknown analysis workflow status: {requested_status}")

    with _connect(database_path) as connection:
        ensure_analysis_table(connection)
        row = connection.execute(
            """
            SELECT raw_payload_json
            FROM tender_analysis
            WHERE source = ? AND external_id = ?
            """,
            (source, external_id),
        ).fetchone()
        if row is None:
            raise KeyError(f"Analysis for {source}/{external_id} not found.")

        raw_payload = _json_object(row["raw_payload_json"])
        workflow = raw_payload.get("tz_workflow")
        workflow = workflow if isinstance(workflow, dict) else {}
        previous_status = _text(workflow.get("status"))
        updated_at = datetime.now().isoformat(timespec="seconds")
        actor = _text(data.get("actor")) or "operator"
        comment = _text(data.get("comment"))

        for key in ("responsible", "deadline", "comment"):
            if key in data:
                workflow[key] = _text(data.get(key))
        if requested_status:
            workflow["status"] = requested_status

        journal = workflow.get("journal")
        journal = [entry for entry in journal if isinstance(entry, dict)] if isinstance(journal, list) else []
        journal.append(
            {
                "action": "workflow_update",
                "actor": actor,
                "from_status": previous_status,
                "to_status": _text(workflow.get("status")),
                "comment": comment,
                "changed_at": updated_at,
            }
        )
        workflow["journal"] = journal[-20:]
        raw_payload["tz_workflow"] = workflow

        connection.execute(
            """
            UPDATE tender_analysis
            SET raw_payload_json = ?
            WHERE source = ? AND external_id = ?
            """,
            (json.dumps(raw_payload, ensure_ascii=False), source, external_id),
        )

    from tender_killer.tender_detail_service import get_tender_payload

    return get_tender_payload(database_path, source, external_id)


def _derive_status(
    raw: dict[str, Any],
    document_state: dict[str, Any],
    metrics: dict[str, Any],
    analysis: dict[str, Any],
    *,
    status: str,
) -> str:
    raw_status = _text(raw.get("status"))
    blocker_count = int(
        metrics.get("actual_blockers")
        if metrics.get("actual_blockers") is not None
        else metrics.get("blockers") or 0
    )
    conflict_count = int(
        metrics.get("actual_conflicts")
        if metrics.get("actual_conflicts") is not None
        else metrics.get("conflicts") or 0
    )
    if blocker_count > 0 or conflict_count > 0:
        return "has_blockers"
    if raw_status in TZ_WORKFLOW_STATUS_IDS:
        return raw_status
    if document_state.get("total", 0) == 0 or document_state.get("downloaded", 0) == 0:
        return "documents_not_downloaded"
    if int(document_state.get("text_ready") or 0) > 0 and not analysis:
        return "text_extracted"
    if status == "pending":
        return "text_extracted" if int(document_state.get("text_ready") or 0) > 0 else "documents_not_downloaded"
    feedback = analysis.get("analysis_feedback") if isinstance(analysis, dict) else None
    if isinstance(feedback, dict) and feedback:
        states = {
            _text(item.get("state"))
            for item in feedback.values()
            if isinstance(item, dict) and _text(item.get("state"))
        }
        if states and states <= {"correct", "not_applicable", "incorrect"}:
            return "operator_verified"
    return "analysis_ready"


def _status_steps(current_status: str) -> list[dict[str, Any]]:
    try:
        current_index = [status["id"] for status in TZ_WORKFLOW_STATUSES].index(current_status)
    except ValueError:
        current_index = 0
    return [
        {
            **status,
            "done": index < current_index,
            "current": status["id"] == current_status,
        }
        for index, status in enumerate(TZ_WORKFLOW_STATUSES)
    ]


def _status_label(status: str) -> str:
    for item in TZ_WORKFLOW_STATUSES:
        if item["id"] == status:
            return item["label"]
    return status


def _comments(raw: dict[str, Any]) -> list[dict[str, str]]:
    comments = raw.get("comments")
    result = [entry for entry in comments if isinstance(entry, dict)] if isinstance(comments, list) else []
    comment = _text(raw.get("comment"))
    if comment and not any(_text(entry.get("text")) == comment for entry in result):
        result.insert(0, {"text": comment})
    return result[:10]


def _journal(raw: dict[str, Any]) -> list[dict[str, Any]]:
    journal = raw.get("journal")
    return [entry for entry in journal if isinstance(entry, dict)][-20:] if isinstance(journal, list) else []


def _connect(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def _json_object(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()
