from __future__ import annotations

import sqlite3

from tender_killer.schema import initialize_schema


def test_initialize_schema_creates_core_tables_and_columns():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    initialize_schema(connection)

    tables = {
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    }
    assert {
        "tenders",
        "notifications",
        "tender_items",
        "tender_workflow",
        "tender_documents",
        "tender_analysis",
        "product_profiles",
        "tender_price_snapshots",
        "app_state",
    }.issubset(tables)
    assert {"classifier_code", "classifier_type"}.issubset(_columns(connection, "tender_items"))
    assert {"text_content", "text_extracted_at", "text_error"}.issubset(_columns(connection, "tender_documents"))
    assert {"search_phrases_json", "evidence_json", "raw_payload_json"}.issubset(
        _columns(connection, "product_profiles")
    )


def test_schema_creates_tender_price_snapshots_table(tmp_path):
    database_path = tmp_path / "db.sqlite"
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        initialize_schema(connection)
        columns = _columns(connection, "tender_price_snapshots")

    assert {
        "id",
        "source",
        "external_id",
        "price_kind",
        "price",
        "currency",
        "observed_at",
        "raw_payload_json",
    }.issubset(columns)


def test_schema_creates_price_book_entries_table(tmp_path):
    database_path = tmp_path / "db.sqlite"
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        initialize_schema(connection)
        columns = _columns(connection, "price_book_entries")

    assert {
        "id",
        "fingerprint",
        "provider",
        "product_name",
        "tokens_json",
        "unit",
        "unit_price",
        "source_tender_source",
        "source_tender_external_id",
        "source_position_index",
        "source_candidate_id",
        "quality_status",
        "pricing_passport_json",
    }.issubset(columns)


def test_initialize_schema_migrates_legacy_minimal_tables():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE tender_items (
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            position_index INTEGER NOT NULL,
            name TEXT NOT NULL,
            raw_payload_json TEXT NOT NULL,
            PRIMARY KEY (source, external_id, position_index)
        );
        CREATE TABLE tender_documents (
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            document_index INTEGER NOT NULL,
            url TEXT NOT NULL,
            raw_payload_json TEXT NOT NULL,
            PRIMARY KEY (source, external_id, url)
        );
        CREATE TABLE product_profiles (
            tender_source TEXT NOT NULL,
            tender_external_id TEXT NOT NULL,
            position_index INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            PRIMARY KEY (tender_source, tender_external_id, position_index)
        );
        """
    )

    initialize_schema(connection)

    assert {"classifier_code", "classifier_type"}.issubset(_columns(connection, "tender_items"))
    assert {"text_content", "text_extracted_at", "text_error"}.issubset(_columns(connection, "tender_documents"))
    assert {"normalized_name", "classifiers_json", "profile_status", "raw_payload_json"}.issubset(
        _columns(connection, "product_profiles")
    )


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {str(row["name"]) for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}
