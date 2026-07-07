from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from tender_killer.schema import ensure_analysis_table
from tender_killer.schema import ensure_documents_table
from tender_killer.schema import ensure_items_table
from tender_killer.schema import ensure_source_runs_table
from tender_killer.schema import ensure_workflow_table
from tender_killer.storage import TenderStore


DATABASE_VIEW_TABLES = (
    "tenders",
    "tender_items",
    "tender_documents",
    "tender_analysis",
    "tender_workflow",
    "product_profiles",
    "source_runs",
)


def list_database_tables_payload(database_path: str | Path) -> dict[str, Any]:
    TenderStore(database_path).initialize()
    with _connect(database_path) as connection:
        _ensure_database_view_tables(connection)
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
        _ensure_database_view_tables(connection)
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


def _ensure_database_view_tables(connection: sqlite3.Connection) -> None:
    ensure_workflow_table(connection)
    ensure_items_table(connection)
    ensure_documents_table(connection)
    ensure_analysis_table(connection)
    ensure_source_runs_table(connection)


def _connect(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


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


def _int_query(value: str | None, default: int) -> int:
    try:
        return int(value) if value else default
    except ValueError:
        return default
