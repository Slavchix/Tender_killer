from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any

from tender_killer.models import ProductProfile, Tender, TenderDocument
from tender_killer.schema import initialize_schema
from tender_killer.tender_metadata import normalize_customer_inn
from tender_killer.tender_metadata import normalize_law
from tender_killer.tender_metadata import normalize_procedure_type
from tender_killer.tender_metadata import normalize_region_code
from tender_killer.tender_metadata import normalize_source_family
from tender_killer.tender_metadata import normalize_status


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
            initialize_schema(connection)

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
                    status, status_normalized, published_at, deadline_at, delivery_place,
                    law, region_code, source_family, procedure_type, customer_inn, category, okpd2,
                    documents_json, raw_payload_json
                )
                VALUES (
                    :source, :external_id, :url, :title, :customer, :region, :price, :currency,
                    :status, :status_normalized, :published_at, :deadline_at, :delivery_place,
                    :law, :region_code, :source_family, :procedure_type, :customer_inn, :category, :okpd2,
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
                    status_normalized = excluded.status_normalized,
                    published_at = excluded.published_at,
                    deadline_at = excluded.deadline_at,
                    delivery_place = excluded.delivery_place,
                    law = excluded.law,
                    region_code = excluded.region_code,
                    source_family = excluded.source_family,
                    procedure_type = excluded.procedure_type,
                    customer_inn = excluded.customer_inn,
                    category = excluded.category,
                    okpd2 = excluded.okpd2,
                    documents_json = excluded.documents_json,
                    raw_payload_json = excluded.raw_payload_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                payload,
            )
            self._replace_items(connection, tender)
            self._replace_documents(connection, tender)
            connection.execute(
                "DELETE FROM product_profiles WHERE tender_source = ? AND tender_external_id = ?",
                tender.identity,
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

    def upsert_product_profiles(
        self,
        source: str,
        external_id: str,
        profiles: list[ProductProfile | dict[str, Any]],
    ) -> None:
        rows = [_serialize_product_profile(source, external_id, profile) for profile in profiles]
        with self._connect() as connection:
            if not rows:
                connection.execute(
                    "DELETE FROM product_profiles WHERE tender_source = ? AND tender_external_id = ?",
                    (source, external_id),
                )
                return
            positions = [row["position_index"] for row in rows]
            placeholders = ", ".join(["?"] * len(positions))
            connection.execute(
                f"""
                DELETE FROM product_profiles
                WHERE tender_source = ? AND tender_external_id = ?
                    AND position_index NOT IN ({placeholders})
                """,
                [source, external_id, *positions],
            )
            connection.executemany(
                """
                INSERT INTO product_profiles (
                    tender_source, tender_external_id, position_index, product_name,
                    normalized_name, details, category, quantity, unit, unit_price,
                    total_price, okpd2, classifier_code, classifier_type, classifiers_json,
                    required_characteristics_json, standards_json, cert_documents_json,
                    brand_model_json, origin_country_requirements_json, search_phrases_json,
                    stop_words_json, evidence_json, profile_status, confidence, source,
                    raw_payload_json
                )
                VALUES (
                    :tender_source, :tender_external_id, :position_index, :product_name,
                    :normalized_name, :details, :category, :quantity, :unit, :unit_price,
                    :total_price, :okpd2, :classifier_code, :classifier_type, :classifiers_json,
                    :required_characteristics_json, :standards_json, :cert_documents_json,
                    :brand_model_json, :origin_country_requirements_json, :search_phrases_json,
                    :stop_words_json, :evidence_json, :profile_status, :confidence, :source,
                    :raw_payload_json
                )
                ON CONFLICT(tender_source, tender_external_id, position_index) DO UPDATE SET
                    product_name = excluded.product_name,
                    normalized_name = excluded.normalized_name,
                    details = excluded.details,
                    category = excluded.category,
                    quantity = excluded.quantity,
                    unit = excluded.unit,
                    unit_price = excluded.unit_price,
                    total_price = excluded.total_price,
                    okpd2 = excluded.okpd2,
                    classifier_code = excluded.classifier_code,
                    classifier_type = excluded.classifier_type,
                    classifiers_json = excluded.classifiers_json,
                    required_characteristics_json = excluded.required_characteristics_json,
                    standards_json = excluded.standards_json,
                    cert_documents_json = excluded.cert_documents_json,
                    brand_model_json = excluded.brand_model_json,
                    origin_country_requirements_json = excluded.origin_country_requirements_json,
                    search_phrases_json = excluded.search_phrases_json,
                    stop_words_json = excluded.stop_words_json,
                    evidence_json = excluded.evidence_json,
                    profile_status = excluded.profile_status,
                    confidence = excluded.confidence,
                    source = excluded.source,
                    raw_payload_json = excluded.raw_payload_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                rows,
            )

    def get_product_profiles(self, source: str, external_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    tender_source, tender_external_id, position_index, product_name,
                    normalized_name, details, category, quantity, unit, unit_price,
                    total_price, okpd2, classifier_code, classifier_type, classifiers_json,
                    required_characteristics_json, standards_json, cert_documents_json,
                    brand_model_json, origin_country_requirements_json, search_phrases_json,
                    stop_words_json, evidence_json, profile_status, confidence, source,
                    raw_payload_json
                FROM product_profiles
                WHERE tender_source = ? AND tender_external_id = ?
                ORDER BY position_index
                """,
                (source, external_id),
            ).fetchall()
        return [_deserialize_product_profile(row) for row in rows]

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
            "status_normalized": normalize_status(tender.status),
            "published_at": tender.published_at.isoformat() if tender.published_at else None,
            "deadline_at": tender.deadline_at.isoformat() if tender.deadline_at else None,
            "delivery_place": tender.delivery_place,
            "law": normalize_law(tender.raw_payload),
            "region_code": normalize_region_code(tender.region, tender.source),
            "source_family": normalize_source_family(tender.source),
            "procedure_type": normalize_procedure_type(tender.source, tender.raw_payload),
            "customer_inn": normalize_customer_inn(tender.raw_payload),
            "category": tender.category,
            "okpd2": tender.okpd2,
            "documents_json": json.dumps(tender.documents, ensure_ascii=False),
            "raw_payload_json": json.dumps(tender.raw_payload, ensure_ascii=False),
        }

    def _replace_items(self, connection: sqlite3.Connection, tender: Tender) -> None:
        connection.execute(
            "DELETE FROM tender_items WHERE source = ? AND external_id = ?",
            tender.identity,
        )
        rows = [
            {
                "source": tender.source,
                "external_id": tender.external_id,
                "position_index": index,
                "name": item.name,
                "details": item.details,
                "quantity": item.quantity,
                "unit": item.unit,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "okpd2": item.okpd2,
                "classifier_code": item.classifier_code,
                "classifier_type": item.classifier_type,
                "raw_payload_json": json.dumps(item.raw_payload, ensure_ascii=False),
            }
            for index, item in enumerate(tender.items, start=1)
        ]
        if not rows:
            return
        connection.executemany(
            """
            INSERT INTO tender_items (
                source, external_id, position_index, name, details, quantity, unit,
                unit_price, total_price, okpd2, classifier_code, classifier_type, raw_payload_json
            )
            VALUES (
                :source, :external_id, :position_index, :name, :details, :quantity, :unit,
                :unit_price, :total_price, :okpd2, :classifier_code, :classifier_type, :raw_payload_json
            )
            """,
            rows,
        )

    def _replace_documents(self, connection: sqlite3.Connection, tender: Tender) -> None:
        documents = _document_records_for_tender(tender)
        if not documents:
            connection.execute(
                "DELETE FROM tender_documents WHERE source = ? AND external_id = ?",
                tender.identity,
            )
            return
        urls = [document.url for document in documents]
        placeholders = ", ".join(["?"] * len(urls))
        connection.execute(
            f"DELETE FROM tender_documents WHERE source = ? AND external_id = ? AND url NOT IN ({placeholders})",
            [tender.source, tender.external_id, *urls],
        )
        rows = [
            {
                "source": tender.source,
                "external_id": tender.external_id,
                "document_index": index,
                "name": document.name,
                "document_type": document.document_type,
                "url": document.url,
                "source_document_id": document.source_document_id,
                "local_path": document.local_path,
                "downloaded_at": document.downloaded_at.isoformat() if document.downloaded_at else None,
                "text_status": document.text_status or "pending",
                "raw_payload_json": json.dumps(document.raw_payload, ensure_ascii=False),
            }
            for index, document in enumerate(documents, start=1)
        ]
        connection.executemany(
            """
            INSERT INTO tender_documents (
                source, external_id, document_index, name, document_type, url,
                source_document_id, local_path, downloaded_at, text_status, raw_payload_json
            )
            VALUES (
                :source, :external_id, :document_index, :name, :document_type, :url,
                :source_document_id, :local_path, :downloaded_at, :text_status, :raw_payload_json
            )
            ON CONFLICT(source, external_id, url) DO UPDATE SET
                document_index = excluded.document_index,
                name = excluded.name,
                document_type = excluded.document_type,
                source_document_id = excluded.source_document_id,
                local_path = COALESCE(tender_documents.local_path, excluded.local_path),
                downloaded_at = COALESCE(tender_documents.downloaded_at, excluded.downloaded_at),
                text_status = CASE
                    WHEN tender_documents.local_path IS NOT NULL THEN tender_documents.text_status
                    ELSE excluded.text_status
                END,
                raw_payload_json = excluded.raw_payload_json
            """,
            rows,
        )


def _document_records_for_tender(tender: Tender) -> list[TenderDocument]:
    if tender.document_records:
        return tender.document_records
    return [TenderDocument(url=url) for url in tender.documents]


_PRODUCT_PROFILE_JSON_FIELDS = (
    "classifiers",
    "required_characteristics",
    "standards",
    "cert_documents",
    "brand_model",
    "origin_country_requirements",
    "search_phrases",
    "stop_words",
    "evidence",
    "raw_payload",
)


def _serialize_product_profile(
    source: str,
    external_id: str,
    profile: ProductProfile | dict[str, Any],
) -> dict[str, Any]:
    values = asdict(profile) if is_dataclass(profile) else dict(profile)
    values["tender_source"] = source
    values["tender_external_id"] = external_id
    row = {
        "tender_source": values["tender_source"],
        "tender_external_id": values["tender_external_id"],
        "position_index": int(values["position_index"]),
        "product_name": values["product_name"],
        "normalized_name": values.get("normalized_name"),
        "details": values.get("details"),
        "category": values.get("category"),
        "quantity": values.get("quantity"),
        "unit": values.get("unit"),
        "unit_price": values.get("unit_price"),
        "total_price": values.get("total_price"),
        "okpd2": values.get("okpd2"),
        "classifier_code": values.get("classifier_code"),
        "classifier_type": values.get("classifier_type"),
        "profile_status": values.get("profile_status") or "needs_review",
        "confidence": values.get("confidence"),
        "source": values.get("source"),
    }
    for field_name in _PRODUCT_PROFILE_JSON_FIELDS:
        row[f"{field_name}_json"] = json.dumps(values.get(field_name) or _empty_json_value(field_name), ensure_ascii=False)
    return row


def _deserialize_product_profile(row: sqlite3.Row) -> dict[str, Any]:
    profile = {
        "tender_source": row["tender_source"],
        "tender_external_id": row["tender_external_id"],
        "position_index": row["position_index"],
        "product_name": row["product_name"],
        "normalized_name": row["normalized_name"],
        "details": row["details"],
        "category": row["category"],
        "quantity": row["quantity"],
        "unit": row["unit"],
        "unit_price": row["unit_price"],
        "total_price": row["total_price"],
        "okpd2": row["okpd2"],
        "classifier_code": row["classifier_code"],
        "classifier_type": row["classifier_type"],
        "profile_status": row["profile_status"],
        "confidence": row["confidence"],
        "source": row["source"],
    }
    for field_name in _PRODUCT_PROFILE_JSON_FIELDS:
        profile[field_name] = json.loads(row[f"{field_name}_json"])
    return profile


def _empty_json_value(field_name: str) -> list[Any] | dict[str, Any]:
    if field_name == "raw_payload":
        return {}
    return []
