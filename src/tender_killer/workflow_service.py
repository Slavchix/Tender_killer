from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from tender_killer.schema import ensure_workflow_table
from tender_killer.storage import TenderStore


WORKFLOW_STATUSES = frozenset(("new", "opened", "interesting", "in_progress", "skipped", "archive"))


def save_tender_workflow(
    database_path: str | Path,
    source: str,
    external_id: str,
    data: dict[str, Any],
) -> dict[str, str]:
    workflow_status = str(data.get("workflow_status") or "new").strip()
    workflow_note = str(data.get("workflow_note") or "").strip()
    if workflow_status not in WORKFLOW_STATUSES:
        raise ValueError(f"Unknown workflow status: {workflow_status}")

    TenderStore(database_path).initialize()
    with _connect(database_path) as connection:
        ensure_workflow_table(connection)
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
    return {"workflow_status": workflow_status, "workflow_note": workflow_note}


def _connect(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection
