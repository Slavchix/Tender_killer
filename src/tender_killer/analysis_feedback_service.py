from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from tender_killer.analysis_feedback import normalize_feedback_state
from tender_killer.schema import ensure_analysis_table
from tender_killer.tender_detail_service import get_tender_payload


def update_analysis_feedback(
    database_path: str | Path,
    source: str,
    external_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    fact_id = str(data.get("fact_id") or "").strip()
    if not fact_id:
        raise ValueError("fact_id is required.")
    requested_state = str(data.get("state") or "").strip().casefold()
    state = normalize_feedback_state(requested_state)
    if requested_state not in {"", "clear"} and not state:
        raise ValueError("Unknown analysis feedback state.")

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
        feedback = raw_payload.get("analysis_feedback")
        if not isinstance(feedback, dict):
            feedback = {}
        current_item = feedback.get(fact_id)
        current_item = current_item if isinstance(current_item, dict) else {}
        current_state = normalize_feedback_state(current_item.get("state"))
        current_history = current_item.get("history")
        history = [entry for entry in current_history if isinstance(entry, dict)] if isinstance(current_history, list) else []
        updated_at = datetime.now().isoformat(timespec="seconds")
        comment = str(data.get("comment") or "").strip()
        actor = str(data.get("actor") or "operator").strip() or "operator"
        if state:
            history.append(
                {
                    "from_state": current_state,
                    "to_state": state,
                    "comment": comment,
                    "changed_at": updated_at,
                    "actor": actor,
                }
            )
            feedback[fact_id] = {
                "state": state,
                "comment": comment,
                "updated_at": updated_at,
                "history": history,
            }
        else:
            feedback.pop(fact_id, None)
        raw_payload["analysis_feedback"] = feedback
        connection.execute(
            """
            UPDATE tender_analysis
            SET raw_payload_json = ?
            WHERE source = ? AND external_id = ?
            """,
            (json.dumps(raw_payload, ensure_ascii=False), source, external_id),
        )

    detail = get_tender_payload(database_path, source, external_id)
    return {"ok": True, "analysis": detail["analysis"]}


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
