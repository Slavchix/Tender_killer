from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tender_killer.models import Tender


@dataclass(frozen=True)
class SaveResult:
    created: bool
    updated: bool


class TenderStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tenders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    customer TEXT,
                    region TEXT,
                    price REAL,
                    currency TEXT NOT NULL,
                    status TEXT,
                    published_at TEXT,
                    deadline_at TEXT,
                    delivery_place TEXT,
                    category TEXT,
                    okpd2 TEXT,
                    documents_json TEXT NOT NULL,
                    raw_payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source, external_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS notifications (
                    source TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    notified_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (source, external_id)
                )
                """
            )

    def upsert_tender(self, tender: Tender) -> SaveResult:
        payload = self._serialize(tender)
        with self._connect() as connection:
            existed = (
                connection.execute(
                    "SELECT 1 FROM tenders WHERE source = ? AND external_id = ?",
                    tender.identity,
                ).fetchone()
                is not None
            )
            connection.execute(
                """
                INSERT INTO tenders (
                    source, external_id, url, title, customer, region, price, currency,
                    status, published_at, deadline_at, delivery_place, category, okpd2,
                    documents_json, raw_payload_json
                )
                VALUES (
                    :source, :external_id, :url, :title, :customer, :region, :price, :currency,
                    :status, :published_at, :deadline_at, :delivery_place, :category, :okpd2,
                    :documents_json, :raw_payload_json
                )
                ON CONFLICT(source, external_id) DO UPDATE SET
                    url = excluded.url,
                    title = excluded.title,
                    customer = excluded.customer,
                    region = excluded.region,
                    price = excluded.price,
                    currency = excluded.currency,
                    status = excluded.status,
                    published_at = excluded.published_at,
                    deadline_at = excluded.deadline_at,
                    delivery_place = excluded.delivery_place,
                    category = excluded.category,
                    okpd2 = excluded.okpd2,
                    documents_json = excluded.documents_json,
                    raw_payload_json = excluded.raw_payload_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                payload,
            )
            return SaveResult(created=not existed, updated=existed)

    def was_notified(self, tender: Tender) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM notifications WHERE source = ? AND external_id = ?",
                tender.identity,
            ).fetchone()
        return row is not None

    def mark_notified(self, tender: Tender) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO notifications (source, external_id)
                VALUES (?, ?)
                """,
                tender.identity,
            )

    def count_tenders(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) FROM tenders").fetchone()
        return int(row[0])

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _serialize(self, tender: Tender) -> dict[str, Any]:
        return {
            "source": tender.source,
            "external_id": tender.external_id,
            "url": tender.url,
            "title": tender.title,
            "customer": tender.customer,
            "region": tender.region,
            "price": tender.price,
            "currency": tender.currency,
            "status": tender.status,
            "published_at": tender.published_at.isoformat() if tender.published_at else None,
            "deadline_at": tender.deadline_at.isoformat() if tender.deadline_at else None,
            "delivery_place": tender.delivery_place,
            "category": tender.category,
            "okpd2": tender.okpd2,
            "documents_json": json.dumps(tender.documents, ensure_ascii=False),
            "raw_payload_json": json.dumps(tender.raw_payload, ensure_ascii=False),
        }
