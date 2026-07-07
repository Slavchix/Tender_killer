from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from tender_killer.normalization import parse_datetime
from tender_killer.schema import ensure_source_runs_table
from tender_killer.storage import TenderStore


SOURCE_STATUS_LABELS = {
    "moscow_supplier_portal": "Москва: zakupki.mos.ru",
    "mosreg_market": "МО: market.mosreg.ru",
}


def list_source_runs_payload(database_path: str | Path) -> dict[str, Any]:
    TenderStore(database_path).initialize()
    with _connect(database_path) as connection:
        ensure_source_runs_table(connection)
        rows = connection.execute(
            """
            SELECT source, last_success_at, last_seen_published_at,
                   last_error_at, last_error, updated_at
            FROM source_runs
            ORDER BY source
            """
        ).fetchall()

    sources = {source: _empty_source(source) for source in SOURCE_STATUS_LABELS}
    for row in rows:
        payload = _source_run_row_to_payload(row)
        sources[payload["source"]] = payload

    ordered_sources = [
        sources[source]
        for source in [*SOURCE_STATUS_LABELS, *sorted(set(sources) - set(SOURCE_STATUS_LABELS))]
    ]
    return {"sources": ordered_sources}


def _empty_source(source: str) -> dict[str, Any]:
    return {
        "source": source,
        "label": SOURCE_STATUS_LABELS.get(source, source),
        "last_success_at": None,
        "last_seen_published_at": None,
        "last_error_at": None,
        "last_error": None,
        "updated_at": None,
    }


def _source_run_row_to_payload(row: sqlite3.Row) -> dict[str, Any]:
    source = str(row["source"])
    return {
        "source": source,
        "label": SOURCE_STATUS_LABELS.get(source, source),
        "last_success_at": _iso(row["last_success_at"]),
        "last_seen_published_at": _iso(row["last_seen_published_at"]),
        "last_error_at": _iso(row["last_error_at"]),
        "last_error": row["last_error"],
        "updated_at": _iso(row["updated_at"]),
    }


def _iso(value: Any) -> str | None:
    parsed = parse_datetime(value)
    if isinstance(parsed, datetime):
        return parsed.isoformat()
    return None


def _connect(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection
