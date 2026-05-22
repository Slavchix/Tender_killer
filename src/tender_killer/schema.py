from __future__ import annotations

import sqlite3


def initialize_schema(connection: sqlite3.Connection) -> None:
    ensure_tenders_table(connection)
    ensure_notifications_table(connection)
    ensure_items_table(connection)
    ensure_workflow_table(connection)
    ensure_documents_table(connection)
    ensure_analysis_table(connection)
    ensure_product_profiles_table(connection)
    ensure_source_runs_table(connection)
    ensure_app_state_table(connection)


def ensure_tenders_table(connection: sqlite3.Connection) -> None:
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
            status_normalized TEXT,
            published_at TEXT,
            deadline_at TEXT,
            delivery_place TEXT,
            law TEXT,
            region_code TEXT,
            source_family TEXT,
            procedure_type TEXT,
            customer_inn TEXT,
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
    ensure_tender_normalized_columns(connection)


def ensure_notifications_table(connection: sqlite3.Connection) -> None:
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


def ensure_items_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tender_items (
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            position_index INTEGER NOT NULL,
            name TEXT NOT NULL,
            details TEXT,
            quantity REAL,
            unit TEXT,
            unit_price REAL,
            total_price REAL,
            okpd2 TEXT,
            classifier_code TEXT,
            classifier_type TEXT,
            raw_payload_json TEXT NOT NULL,
            PRIMARY KEY (source, external_id, position_index),
            FOREIGN KEY (source, external_id) REFERENCES tenders(source, external_id)
                ON DELETE CASCADE
        )
        """
    )
    ensure_item_classifier_columns(connection)


def ensure_workflow_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tender_workflow (
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            workflow_status TEXT NOT NULL DEFAULT 'new',
            workflow_note TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (source, external_id)
        )
        """
    )


def ensure_documents_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tender_documents (
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            document_index INTEGER NOT NULL,
            name TEXT,
            document_type TEXT,
            url TEXT NOT NULL,
            source_document_id TEXT,
            local_path TEXT,
            downloaded_at TEXT,
            text_status TEXT NOT NULL DEFAULT 'pending',
            text_content TEXT,
            text_extracted_at TEXT,
            text_error TEXT,
            raw_payload_json TEXT NOT NULL,
            PRIMARY KEY (source, external_id, url),
            FOREIGN KEY (source, external_id) REFERENCES tenders(source, external_id)
                ON DELETE CASCADE
        )
        """
    )
    ensure_document_text_columns(connection)


def ensure_analysis_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tender_analysis (
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            summary TEXT NOT NULL,
            requirements_json TEXT NOT NULL,
            risks_json TEXT NOT NULL,
            red_flags_json TEXT NOT NULL,
            recommended_status TEXT NOT NULL,
            confidence REAL NOT NULL,
            raw_payload_json TEXT NOT NULL,
            analyzed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (source, external_id),
            FOREIGN KEY (source, external_id) REFERENCES tenders(source, external_id)
                ON DELETE CASCADE
        )
        """
    )


def ensure_product_profiles_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS product_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tender_source TEXT NOT NULL,
            tender_external_id TEXT NOT NULL,
            position_index INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            normalized_name TEXT,
            details TEXT,
            category TEXT,
            quantity REAL,
            unit TEXT,
            unit_price REAL,
            total_price REAL,
            okpd2 TEXT,
            classifier_code TEXT,
            classifier_type TEXT,
            classifiers_json TEXT NOT NULL,
            required_characteristics_json TEXT NOT NULL,
            standards_json TEXT NOT NULL,
            cert_documents_json TEXT NOT NULL,
            fulfillment_requirements_json TEXT NOT NULL,
            brand_model_json TEXT NOT NULL,
            origin_country_requirements_json TEXT NOT NULL,
            search_phrases_json TEXT NOT NULL,
            stop_words_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            profile_status TEXT NOT NULL,
            confidence REAL,
            source TEXT,
            raw_payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(tender_source, tender_external_id, position_index)
        )
        """
    )
    ensure_product_profile_columns(connection)


def ensure_source_runs_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS source_runs (
            source TEXT NOT NULL PRIMARY KEY,
            last_success_at TEXT,
            last_seen_published_at TEXT,
            last_error_at TEXT,
            last_error TEXT,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    ensure_source_run_columns(connection)


def ensure_app_state_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT NOT NULL PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def ensure_document_text_columns(connection: sqlite3.Connection) -> None:
    columns = _columns(connection, "tender_documents")
    for column, definition in {
        "text_content": "TEXT",
        "text_extracted_at": "TEXT",
        "text_error": "TEXT",
    }.items():
        if column not in columns:
            connection.execute(f"ALTER TABLE tender_documents ADD COLUMN {column} {definition}")


def ensure_item_classifier_columns(connection: sqlite3.Connection) -> None:
    columns = _columns(connection, "tender_items")
    for column in ("classifier_code", "classifier_type"):
        if column not in columns:
            connection.execute(f"ALTER TABLE tender_items ADD COLUMN {column} TEXT")


def ensure_product_profile_columns(connection: sqlite3.Connection) -> None:
    columns = _columns(connection, "product_profiles")
    definitions = {
        "id": "INTEGER",
        "normalized_name": "TEXT",
        "details": "TEXT",
        "category": "TEXT",
        "quantity": "REAL",
        "unit": "TEXT",
        "unit_price": "REAL",
        "total_price": "REAL",
        "okpd2": "TEXT",
        "classifier_code": "TEXT",
        "classifier_type": "TEXT",
        "classifiers_json": "TEXT NOT NULL DEFAULT '[]'",
        "required_characteristics_json": "TEXT NOT NULL DEFAULT '[]'",
        "standards_json": "TEXT NOT NULL DEFAULT '[]'",
        "cert_documents_json": "TEXT NOT NULL DEFAULT '[]'",
        "fulfillment_requirements_json": "TEXT NOT NULL DEFAULT '[]'",
        "brand_model_json": "TEXT NOT NULL DEFAULT '[]'",
        "origin_country_requirements_json": "TEXT NOT NULL DEFAULT '[]'",
        "search_phrases_json": "TEXT NOT NULL DEFAULT '[]'",
        "stop_words_json": "TEXT NOT NULL DEFAULT '[]'",
        "evidence_json": "TEXT NOT NULL DEFAULT '[]'",
        "profile_status": "TEXT NOT NULL DEFAULT 'draft'",
        "confidence": "REAL NOT NULL DEFAULT 0",
        "source": "TEXT NOT NULL DEFAULT 'item'",
        "raw_payload_json": "TEXT NOT NULL DEFAULT '{}'",
        "created_at": "TEXT NOT NULL DEFAULT ''",
        "updated_at": "TEXT NOT NULL DEFAULT ''",
    }
    for column, definition in definitions.items():
        if column not in columns:
            connection.execute(f"ALTER TABLE product_profiles ADD COLUMN {column} {definition}")


def ensure_tender_normalized_columns(connection: sqlite3.Connection) -> None:
    columns = _columns(connection, "tenders")
    definitions = {
        "law": "TEXT",
        "status_normalized": "TEXT",
        "region_code": "TEXT",
        "source_family": "TEXT",
        "procedure_type": "TEXT",
        "customer_inn": "TEXT",
    }
    for column, definition in definitions.items():
        if column not in columns:
            connection.execute(f"ALTER TABLE tenders ADD COLUMN {column} {definition}")


def ensure_source_run_columns(connection: sqlite3.Connection) -> None:
    columns = _columns(connection, "source_runs")
    definitions = {
        "last_success_at": "TEXT",
        "last_seen_published_at": "TEXT",
        "last_error_at": "TEXT",
        "last_error": "TEXT",
        "updated_at": "TEXT NOT NULL DEFAULT ''",
    }
    for column, definition in definitions.items():
        if column not in columns:
            connection.execute(f"ALTER TABLE source_runs ADD COLUMN {column} {definition}")


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {str(row["name"]) for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}
