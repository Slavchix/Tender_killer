from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tender_killer.models import ProductProfile, Tender, TenderDocument
from tender_killer.market_state import extract_market_state
from tender_killer.normalization import parse_datetime
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
            self._record_price_snapshot(connection, tender, "nmc", tender.price)
            market_state = extract_market_state(
                {
                    "source": tender.source,
                    "external_id": tender.external_id,
                    "price": tender.price,
                    "raw_payload": tender.raw_payload,
                }
            )
            self._record_price_snapshot(connection, tender, "current_offer", market_state.get("current_offer_price"))
            self._replace_items(connection, tender)
            self._replace_documents(connection, tender)
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

    def get_source_checkpoint(self, source: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT source, last_success_at, last_seen_published_at,
                       last_error_at, last_error, updated_at
                FROM source_runs
                WHERE source = ?
                """,
                (source,),
            ).fetchone()
        if row is None:
            return {
                "source": source,
                "last_success_at": None,
                "last_seen_published_at": None,
                "last_error_at": None,
                "last_error": None,
                "updated_at": None,
            }
        return _deserialize_source_checkpoint(row)

    def record_source_success(self, source: str, last_seen_published_at: datetime | None = None) -> None:
        now = datetime.now(UTC).isoformat(timespec="seconds")
        seen_value = last_seen_published_at.isoformat() if last_seen_published_at else None
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO source_runs (
                    source, last_success_at, last_seen_published_at,
                    last_error_at, last_error, updated_at
                )
                VALUES (?, ?, ?, NULL, NULL, ?)
                ON CONFLICT(source) DO UPDATE SET
                    last_success_at = excluded.last_success_at,
                    last_seen_published_at = COALESCE(excluded.last_seen_published_at, source_runs.last_seen_published_at),
                    last_error_at = NULL,
                    last_error = NULL,
                    updated_at = excluded.updated_at
                """,
                (source, now, seen_value, now),
            )

    def record_source_error(self, source: str, error: str) -> None:
        now = datetime.now(UTC).isoformat(timespec="seconds")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO source_runs (
                    source, last_success_at, last_seen_published_at,
                    last_error_at, last_error, updated_at
                )
                VALUES (?, NULL, NULL, ?, ?, ?)
                ON CONFLICT(source) DO UPDATE SET
                    last_error_at = excluded.last_error_at,
                    last_error = excluded.last_error,
                    updated_at = excluded.updated_at
                """,
                (source, now, error, now),
            )

    def list_active_tender_payloads(self, source: str, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT source, external_id, raw_payload_json
                FROM tenders
                WHERE source = ? AND status_normalized = 'active'
                ORDER BY COALESCE(deadline_at, updated_at) ASC, external_id ASC
                LIMIT ?
                """,
                (source, max(1, int(limit))),
            ).fetchall()
        return [
            {
                "source": row["source"],
                "external_id": row["external_id"],
                "raw_payload": _json_object(row["raw_payload_json"]),
            }
            for row in rows
        ]

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
                    "DELETE FROM price_candidates WHERE tender_source = ? AND tender_external_id = ?",
                    (source, external_id),
                )
                connection.execute(
                    "DELETE FROM product_profiles WHERE tender_source = ? AND tender_external_id = ?",
                    (source, external_id),
                )
                return
            positions = [row["position_index"] for row in rows]
            placeholders = ", ".join(["?"] * len(positions))
            connection.execute(
                f"""
                DELETE FROM price_candidates
                WHERE tender_source = ? AND tender_external_id = ?
                    AND position_index NOT IN ({placeholders})
                """,
                [source, external_id, *positions],
            )
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
                    fulfillment_requirements_json, brand_model_json, origin_country_requirements_json,
                    search_phrases_json, stop_words_json, evidence_json, profile_status,
                    confidence, source, raw_payload_json
                )
                VALUES (
                    :tender_source, :tender_external_id, :position_index, :product_name,
                    :normalized_name, :details, :category, :quantity, :unit, :unit_price,
                    :total_price, :okpd2, :classifier_code, :classifier_type, :classifiers_json,
                    :required_characteristics_json, :standards_json, :cert_documents_json,
                    :fulfillment_requirements_json, :brand_model_json, :origin_country_requirements_json,
                    :search_phrases_json, :stop_words_json, :evidence_json, :profile_status,
                    :confidence, :source, :raw_payload_json
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
                    fulfillment_requirements_json = excluded.fulfillment_requirements_json,
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
                    fulfillment_requirements_json, brand_model_json, origin_country_requirements_json,
                    search_phrases_json, stop_words_json, evidence_json, profile_status,
                    confidence, source, raw_payload_json
                FROM product_profiles
                WHERE tender_source = ? AND tender_external_id = ?
                ORDER BY position_index
                """,
                (source, external_id),
            ).fetchall()
            candidate_rows = connection.execute(
                """
                SELECT
                    id, tender_source, tender_external_id, position_index, origin, fingerprint,
                    provider, product_name, supplier_name, source_url, source_query, source_kind,
                    unit_price, currency, vat_mode, availability, offer_status, review_status,
                    confidence, confidence_reasons_json, match_reasons_json, supplier_option_index,
                    observed_at, reviewed_at, raw_payload_json, created_at, updated_at
                FROM price_candidates
                WHERE tender_source = ? AND tender_external_id = ?
                ORDER BY position_index, id
                """,
                (source, external_id),
            ).fetchall()
        profiles = [_deserialize_product_profile(row) for row in rows]
        candidates_by_position: dict[int, list[dict[str, Any]]] = {}
        for row in candidate_rows:
            candidate = _deserialize_price_candidate(row)
            candidates_by_position.setdefault(int(candidate["position_index"]), []).append(candidate)
        for profile in profiles:
            profile["price_candidates"] = candidates_by_position.get(int(profile.get("position_index") or 0), [])
        return profiles

    def upsert_price_candidates(
        self,
        source: str,
        external_id: str,
        position_index: int,
        candidates: list[dict[str, Any]],
        *,
        origin: str,
    ) -> list[dict[str, Any]]:
        rows = [
            _serialize_price_candidate(source, external_id, position_index, candidate, origin=origin)
            for candidate in candidates
        ]
        rows = [row for row in rows if row]
        if not rows:
            return []
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO price_candidates (
                    tender_source, tender_external_id, position_index, origin, fingerprint,
                    provider, product_name, supplier_name, source_url, source_query, source_kind,
                    unit_price, currency, vat_mode, availability, offer_status, review_status,
                    confidence, confidence_reasons_json, match_reasons_json, supplier_option_index,
                    raw_payload_json
                )
                VALUES (
                    :tender_source, :tender_external_id, :position_index, :origin, :fingerprint,
                    :provider, :product_name, :supplier_name, :source_url, :source_query, :source_kind,
                    :unit_price, :currency, :vat_mode, :availability, :offer_status, :review_status,
                    :confidence, :confidence_reasons_json, :match_reasons_json, :supplier_option_index,
                    :raw_payload_json
                )
                ON CONFLICT(tender_source, tender_external_id, position_index, fingerprint) DO UPDATE SET
                    origin = excluded.origin,
                    provider = excluded.provider,
                    product_name = excluded.product_name,
                    supplier_name = excluded.supplier_name,
                    source_url = excluded.source_url,
                    source_query = excluded.source_query,
                    source_kind = excluded.source_kind,
                    unit_price = excluded.unit_price,
                    currency = excluded.currency,
                    vat_mode = excluded.vat_mode,
                    availability = excluded.availability,
                    offer_status = excluded.offer_status,
                    review_status = CASE
                        WHEN price_candidates.review_status IN ('confirmed', 'imported', 'rejected')
                            THEN price_candidates.review_status
                        ELSE excluded.review_status
                    END,
                    confidence = excluded.confidence,
                    confidence_reasons_json = excluded.confidence_reasons_json,
                    match_reasons_json = excluded.match_reasons_json,
                    raw_payload_json = excluded.raw_payload_json,
                    observed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                """,
                rows,
            )
            fingerprints = [row["fingerprint"] for row in rows]
            placeholders = ", ".join(["?"] * len(fingerprints))
            saved_rows = connection.execute(
                f"""
                SELECT
                    id, tender_source, tender_external_id, position_index, origin, fingerprint,
                    provider, product_name, supplier_name, source_url, source_query, source_kind,
                    unit_price, currency, vat_mode, availability, offer_status, review_status,
                    confidence, confidence_reasons_json, match_reasons_json, supplier_option_index,
                    observed_at, reviewed_at, raw_payload_json, created_at, updated_at
                FROM price_candidates
                WHERE tender_source = ? AND tender_external_id = ? AND position_index = ?
                    AND fingerprint IN ({placeholders})
                """,
                [source, external_id, int(position_index), *fingerprints],
            ).fetchall()
        saved_by_fingerprint = {
            str(row["fingerprint"]): _deserialize_price_candidate(row)
            for row in saved_rows
        }
        return [saved_by_fingerprint[row["fingerprint"]] for row in rows if row["fingerprint"] in saved_by_fingerprint]

    def list_price_candidates(
        self,
        source: str,
        external_id: str,
        position_index: int | None = None,
    ) -> list[dict[str, Any]]:
        params: list[Any] = [source, external_id]
        position_filter = ""
        if position_index is not None:
            position_filter = " AND position_index = ?"
            params.append(int(position_index))
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    id, tender_source, tender_external_id, position_index, origin, fingerprint,
                    provider, product_name, supplier_name, source_url, source_query, source_kind,
                    unit_price, currency, vat_mode, availability, offer_status, review_status,
                    confidence, confidence_reasons_json, match_reasons_json, supplier_option_index,
                    observed_at, reviewed_at, raw_payload_json, created_at, updated_at
                FROM price_candidates
                WHERE tender_source = ? AND tender_external_id = ?{position_filter}
                ORDER BY position_index, id
                """,
                params,
            ).fetchall()
        return [_deserialize_price_candidate(row) for row in rows]

    def update_price_candidate_review(
        self,
        source: str,
        external_id: str,
        position_index: int,
        candidate: dict[str, Any],
        *,
        review_status: str,
        supplier_option_index: int | None = None,
    ) -> None:
        row = _serialize_price_candidate(source, external_id, position_index, candidate, origin="supplier_discovery")
        if not row:
            return
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE price_candidates
                SET review_status = ?,
                    supplier_option_index = ?,
                    reviewed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE tender_source = ? AND tender_external_id = ? AND position_index = ? AND fingerprint = ?
                """,
                (
                    _price_candidate_review_status(review_status),
                    supplier_option_index,
                    source,
                    external_id,
                    int(position_index),
                    row["fingerprint"],
                ),
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _record_price_snapshot(
        self,
        connection: sqlite3.Connection,
        tender: Tender,
        price_kind: str,
        price: float | None,
    ) -> None:
        if price is None:
            return
        latest = connection.execute(
            """
            SELECT price
            FROM tender_price_snapshots
            WHERE source = ? AND external_id = ? AND price_kind = ?
            ORDER BY observed_at DESC, id DESC
            LIMIT 1
            """,
            (tender.source, tender.external_id, price_kind),
        ).fetchone()
        if latest is not None and float(latest["price"]) == float(price):
            return
        connection.execute(
            """
            INSERT INTO tender_price_snapshots (
                source, external_id, price_kind, price, currency, raw_payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                tender.source,
                tender.external_id,
                price_kind,
                float(price),
                tender.currency or "RUB",
                json.dumps(tender.raw_payload, ensure_ascii=False),
            ),
        )

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


def _deserialize_source_checkpoint(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "source": row["source"],
        "last_success_at": parse_datetime(row["last_success_at"]),
        "last_seen_published_at": parse_datetime(row["last_seen_published_at"]),
        "last_error_at": parse_datetime(row["last_error_at"]),
        "last_error": row["last_error"],
        "updated_at": parse_datetime(row["updated_at"]),
    }


def _json_object(value: Any) -> dict[str, Any]:
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


_PRODUCT_PROFILE_JSON_FIELDS = (
    "classifiers",
    "required_characteristics",
    "standards",
    "cert_documents",
    "fulfillment_requirements",
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


def _serialize_price_candidate(
    source: str,
    external_id: str,
    position_index: int,
    candidate: dict[str, Any],
    *,
    origin: str,
) -> dict[str, Any]:
    row = {
        "tender_source": source,
        "tender_external_id": external_id,
        "position_index": int(position_index),
        "origin": _token(origin) or "manual",
        "provider": _token(candidate.get("provider")),
        "product_name": _text(candidate.get("product_name")) or _text(candidate.get("name")),
        "supplier_name": _text(candidate.get("supplier_name")),
        "source_url": _text(candidate.get("source_url")) or _text(candidate.get("url")),
        "source_query": _text(candidate.get("source_query")),
        "source_kind": _text(candidate.get("source_kind")),
        "unit_price": _number(candidate.get("unit_price")),
        "currency": _currency(candidate.get("currency")),
        "vat_mode": _token(candidate.get("vat_mode")),
        "availability": _token(candidate.get("availability")),
        "offer_status": _token(candidate.get("offer_status")) or _token(candidate.get("status")),
        "review_status": _price_candidate_review_status(candidate.get("review_status")),
        "confidence": _token(candidate.get("confidence")),
        "confidence_reasons_json": json.dumps(_json_list(candidate.get("confidence_reasons")), ensure_ascii=False),
        "match_reasons_json": json.dumps(_json_list(candidate.get("match_reasons")), ensure_ascii=False),
        "supplier_option_index": _integer(candidate.get("supplier_option_index")),
        "raw_payload_json": json.dumps(_normalized_price_candidate_payload(candidate), ensure_ascii=False),
    }
    if not any(row.get(field) for field in ("product_name", "source_url", "supplier_name")) and row["unit_price"] is None:
        return {}
    row["fingerprint"] = _price_candidate_fingerprint(row)
    return row


def _deserialize_price_candidate(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "tender_source": row["tender_source"],
        "tender_external_id": row["tender_external_id"],
        "position_index": int(row["position_index"]),
        "origin": row["origin"],
        "fingerprint": row["fingerprint"],
        "provider": row["provider"],
        "product_name": row["product_name"],
        "supplier_name": row["supplier_name"],
        "source_url": row["source_url"],
        "source_query": row["source_query"],
        "source_kind": row["source_kind"],
        "unit_price": row["unit_price"],
        "currency": row["currency"],
        "vat_mode": row["vat_mode"],
        "availability": row["availability"],
        "offer_status": row["offer_status"],
        "review_status": row["review_status"],
        "confidence": row["confidence"],
        "confidence_reasons": _json_list(row["confidence_reasons_json"]),
        "match_reasons": _json_list(row["match_reasons_json"]),
        "supplier_option_index": row["supplier_option_index"],
        "observed_at": row["observed_at"],
        "reviewed_at": row["reviewed_at"],
        "raw_payload": _json_object(row["raw_payload_json"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _normalized_price_candidate_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    payload = {str(key): value for key, value in candidate.items()}
    if name := _text(candidate.get("name")):
        payload["name"] = name
    if product_name := _text(candidate.get("product_name")):
        payload["product_name"] = product_name
    if url := _text(candidate.get("url")):
        payload["url"] = url
    if source_url := _text(candidate.get("source_url")):
        payload["source_url"] = source_url
    if unit_price := _number(candidate.get("unit_price")):
        payload["unit_price"] = unit_price
    if provider := _token(candidate.get("provider")):
        payload["provider"] = provider
    return payload


def _price_candidate_fingerprint(row: dict[str, Any]) -> str:
    provider = str(row.get("provider") or "").casefold()
    source_url = str(row.get("source_url") or "").strip().casefold()
    if source_url:
        basis = ["url", provider, source_url]
    else:
        basis = [
            "text",
            provider,
            str(row.get("source_query") or "").casefold(),
            str(row.get("product_name") or "").casefold(),
            str(row.get("unit_price") or ""),
        ]
    return hashlib.sha256("\x1f".join(basis).encode("utf-8")).hexdigest()


def _price_candidate_review_status(value: Any) -> str:
    token = _token(value)
    return token if token in {"pending", "confirmed", "imported", "rejected"} else "pending"


def _currency(value: Any) -> str:
    text = _text(value)
    if not text:
        return "RUB"
    currency = text.upper()
    return "RUB" if currency in {"RUB", "RUR", "РУБ", "РУБ."} else currency


def _json_list(value: Any) -> list[Any]:
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return []
        return decoded if isinstance(decoded, list) else []
    return value if isinstance(value, list) else []


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _token(value: Any) -> str | None:
    text = _text(value)
    if not text:
        return None
    token = "".join(character if character.isalnum() else "_" for character in text.casefold()).strip("_")
    while "__" in token:
        token = token.replace("__", "_")
    return token or None


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _integer(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
