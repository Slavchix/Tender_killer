from __future__ import annotations

import sqlite3

from tender_killer.analysis_facts_service import build_analysis_facts
from tender_killer.analysis_service import analyze_tender_payload
from tender_killer.api_handlers import handle_post_request
from tender_killer.models import Tender
from tender_killer.models import TenderDocument
from tender_killer.storage import TenderStore
from tender_killer.tender_detail_service import get_tender_payload


def test_analysis_facts_merge_semantic_duplicates_with_sources():
    documents = [
        {
            "name": "requirements.docx",
            "text_status": "ok",
            "text_content": "Zayavka dolzhna soderzhat stranu proiskhozhdeniya tovara.",
        },
        {
            "name": "spec.docx",
            "text_status": "ok",
            "text_content": "Primenyaetsya nacionalnyy rezhim po postanovleniyu 1875.",
        },
    ]
    analysis = {
        "confidence": 0.9,
        "checklist": [
            {
                "label": "strana proiskhozhdeniya",
                "category": "national_regime",
                "severity": "high",
                "evidence": "Zayavka dolzhna soderzhat stranu proiskhozhdeniya tovara.",
            },
            {
                "label": "nacionalnyy rezhim",
                "category": "national_regime",
                "severity": "high",
                "evidence": "Primenyaetsya nacionalnyy rezhim po postanovleniyu 1875.",
            },
        ],
    }

    facts = build_analysis_facts(analysis, documents)
    national_regime_items = [
        item for item in facts["items"] if item.get("semantic_key") == "national_regime"
    ]

    assert len(national_regime_items) == 1
    item = national_regime_items[0]
    assert item["related_labels"] == ["strana proiskhozhdeniya", "nacionalnyy rezhim"]
    assert [
        (source["document_name"], source["fragment"])
        for source in item["evidence_sources"]
    ] == [
        ("requirements.docx", "Zayavka dolzhna soderzhat stranu proiskhozhdeniya tovara."),
        ("spec.docx", "Primenyaetsya nacionalnyy rezhim po postanovleniyu 1875."),
    ]


def test_analyze_tender_payload_lists_missing_expected_checks(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3680003",
            url="https://market.mosreg.ru/Trade/ViewTrade/3680003",
            title="Missing checks tender",
            document_records=[
                TenderDocument(
                    url="https://example.test/spec.docx",
                    name="spec.docx",
                    document_type="technical specification",
                ),
            ],
        )
    )
    with sqlite3.connect(store.database_path) as connection:
        connection.execute(
            """
            UPDATE tender_documents
            SET text_status = ?, text_content = ?, text_extracted_at = ?
            WHERE source = ? AND external_id = ? AND url = ?
            """,
            (
                "ok",
                "Technical specification: supply of office paper. Supplier provides certificate.",
                "2026-06-04T12:00:00",
                "mosreg_market",
                "3680003",
                "https://example.test/spec.docx",
            ),
        )

    payload = analyze_tender_payload(store.database_path, "mosreg_market", "3680003")
    analysis = payload["analysis"]
    missing = {item["id"]: item for item in analysis["missing_checks"]}
    checklist_missing = [
        item for item in analysis["checklist"] if item.get("type") == "missing_check"
    ]

    assert {"delivery_deadline", "payment_terms", "contract_security", "acceptance_documents"} <= set(missing)
    assert missing["delivery_deadline"]["status"] == "missing"
    assert missing["payment_terms"]["category"] == "financial"
    assert any(item["missing_check_id"] == "payment_terms" for item in checklist_missing)
    assert all(item["severity"] == "medium" for item in checklist_missing)


def test_analysis_feedback_endpoint_persists_operator_mark(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3668200",
            url="https://market.mosreg.ru/Trade/ViewTrade/3668200",
            title="Paper tender",
            document_records=[
                TenderDocument(
                    url="https://example.test/tz.docx",
                    name="tz.docx",
                    document_type="technical specification",
                ),
            ],
        )
    )
    with sqlite3.connect(store.database_path) as connection:
        connection.execute(
            """
            UPDATE tender_documents
            SET text_status = ?, text_content = ?, text_extracted_at = ?
            WHERE source = ? AND external_id = ? AND url = ?
            """,
            (
                "ok",
                "Technical specification: paper supply. Certificate required. National regime 1875 applies.",
                "2026-06-04T12:00:00",
                "mosreg_market",
                "3668200",
                "https://example.test/tz.docx",
            ),
        )
    analysis_payload = analyze_tender_payload(store.database_path, "mosreg_market", "3668200")
    fact = next(
        item
        for item in analysis_payload["analysis"]["analysis_facts"]["items"]
        if item.get("kind") != "subject"
    )

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/analysis/feedback",
        {"fact_id": fact["id"], "state": "not_risk"},
    )

    assert response.status == 200
    analysis = response.payload["analysis"]
    assert analysis["analysis_feedback"][fact["id"]]["state"] == "not_risk"
    updated_fact = next(item for item in analysis["analysis_facts"]["items"] if item["id"] == fact["id"])
    assert updated_fact["feedback_state"] == "not_risk"
    assert updated_fact["feedback_label"] == "не риск"
    assert updated_fact["is_blocker"] is False
    detail = get_tender_payload(store.database_path, "mosreg_market", "3668200")
    assert detail["analysis"]["analysis_feedback"][fact["id"]]["state"] == "not_risk"


def test_analysis_history_tracks_reanalysis_changes(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3680100",
            url="https://market.mosreg.ru/Trade/ViewTrade/3680100",
            title="History tender",
            document_records=[
                TenderDocument(
                    url="https://example.test/tz.docx",
                    name="tz.docx",
                    document_type="technical specification",
                ),
            ],
        )
    )
    with sqlite3.connect(store.database_path) as connection:
        connection.execute(
            """
            UPDATE tender_documents
            SET text_status = ?, text_content = ?, text_extracted_at = ?
            WHERE source = ? AND external_id = ? AND url = ?
            """,
            (
                "ok",
                "Техническое задание: поставка офисной бумаги. Поставщик предоставляет сертификат.",
                "2026-06-04T12:00:00",
                "mosreg_market",
                "3680100",
                "https://example.test/tz.docx",
            ),
        )
    first_payload = analyze_tender_payload(store.database_path, "mosreg_market", "3680100")
    first_history = first_payload["analysis"]["analysis_history"]

    assert first_history[0]["run_number"] == 1
    assert first_history[0]["changes"]["previous_run_id"] is None

    with sqlite3.connect(store.database_path) as connection:
        connection.execute(
            """
            UPDATE tender_documents
            SET text_content = ?, text_extracted_at = ?
            WHERE source = ? AND external_id = ? AND url = ?
            """,
            (
                "Техническое задание: поставка офисной бумаги. Поставщик предоставляет сертификат. "
                "Срок поставки 2 рабочих дня. Обеспечение исполнения контракта 5 процентов.",
                "2026-06-04T12:30:00",
                "mosreg_market",
                "3680100",
                "https://example.test/tz.docx",
            ),
        )
    second_payload = analyze_tender_payload(store.database_path, "mosreg_market", "3680100")
    latest_history = second_payload["analysis"]["analysis_history"][0]

    assert latest_history["run_number"] == 2
    assert latest_history["changes"]["previous_run_id"] == first_history[0]["id"]
    assert latest_history["changes"]["added_count"] >= 1
    assert latest_history["changes"]["summary"].startswith("Добавлено")
    assert latest_history["changes"]["feedback_count"] == 0
