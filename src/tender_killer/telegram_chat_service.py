from __future__ import annotations

import sqlite3
from pathlib import Path

from tender_killer.schema import initialize_schema

TELEGRAM_LAST_CHAT_KEY = "telegram.last_chat_id"


def remember_telegram_chat(database_path: str | Path, chat_id: str | int | None) -> None:
    value = str(chat_id or "").strip()
    if not value:
        return
    with _connect(database_path) as connection:
        initialize_schema(connection)
        connection.execute(
            """
            INSERT INTO app_state (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (TELEGRAM_LAST_CHAT_KEY, value),
        )


def get_remembered_telegram_chat_id(database_path: str | Path) -> str | None:
    with _connect(database_path) as connection:
        initialize_schema(connection)
        row = connection.execute(
            "SELECT value FROM app_state WHERE key = ?",
            (TELEGRAM_LAST_CHAT_KEY,),
        ).fetchone()
    if row is None:
        return None
    return str(row["value"] or "").strip() or None


def _connect(database_path: str | Path) -> sqlite3.Connection:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection
