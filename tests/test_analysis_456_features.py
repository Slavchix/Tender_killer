from __future__ import annotations

import sqlite3

from tender_killer.analysis_facts_service import build_analysis_facts
from tender_killer.analysis_history_service import build_analysis_change_summary
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
    assert analysis["analysis_feedback"][fact["id"]]["state"] == "incorrect"
    updated_fact = next(item for item in analysis["analysis_facts"]["items"] if item["id"] == fact["id"])
    assert updated_fact["feedback_state"] == "incorrect"
    assert updated_fact["feedback_label"] == "неверно"
    assert updated_fact["is_blocker"] is False
    detail = get_tender_payload(store.database_path, "mosreg_market", "3668200")
    assert detail["analysis"]["analysis_feedback"][fact["id"]]["state"] == "incorrect"


def test_analysis_feedback_endpoint_persists_saas_state_comment_and_history(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3668201",
            url="https://market.mosreg.ru/Trade/ViewTrade/3668201",
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
                "Техническое задание: поставка бумаги. Требуется сертификат. Применяется национальный режим 1875.",
                "2026-06-04T12:00:00",
                "mosreg_market",
                "3668201",
                "https://example.test/tz.docx",
            ),
        )
    analysis_payload = analyze_tender_payload(store.database_path, "mosreg_market", "3668201")
    fact = next(
        item
        for item in analysis_payload["analysis"]["analysis_facts"]["items"]
        if item.get("kind") != "subject"
    )

    first_response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668201/analysis/feedback",
        {
            "fact_id": fact["id"],
            "state": "needs_manual_review",
            "comment": "Нужно сверить формулировку с проектом контракта.",
        },
    )
    second_response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668201/analysis/feedback",
        {
            "fact_id": fact["id"],
            "state": "correct",
            "comment": "Проверено по ТЗ, требование действительно есть.",
        },
    )

    assert first_response.status == 200
    assert second_response.status == 200
    feedback = second_response.payload["analysis"]["analysis_feedback"][fact["id"]]
    assert feedback["state"] == "correct"
    assert feedback["comment"] == "Проверено по ТЗ, требование действительно есть."
    assert [entry["to_state"] for entry in feedback["history"]] == ["needs_manual_review", "correct"]
    assert feedback["history"][0]["comment"] == "Нужно сверить формулировку с проектом контракта."
    assert feedback["history"][1]["from_state"] == "needs_manual_review"
    updated_fact = next(
        item
        for item in second_response.payload["analysis"]["analysis_facts"]["items"]
        if item["id"] == fact["id"]
    )
    assert updated_fact["feedback_state"] == "correct"
    assert updated_fact["feedback_label"] == "верно"
    assert updated_fact["feedback_comment"] == "Проверено по ТЗ, требование действительно есть."
    assert updated_fact["feedback_history"] == feedback["history"]


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


def test_analysis_history_summarizes_operator_feedback_labels():
    current = {
        "analysis_facts": {
            "version": 1,
            "items": [
                {"id": "fact:certificate", "label": "сертификат/декларация"},
                {"id": "fact:delivery", "label": "срок поставки"},
            ],
        },
        "analysis_feedback": {
            "fact:certificate": {"state": "confirmed"},
            "fact:delivery": {"state": "ignored"},
        },
    }

    changes = build_analysis_change_summary({}, current)

    assert changes["feedback_count"] == 2
    assert changes["feedback"] == [
        "сертификат/декларация: верно",
        "срок поставки: не относится к заявке",
    ]


def test_analysis_history_summarizes_saas_feedback_labels_with_comments():
    current = {
        "analysis_facts": {
            "version": 1,
            "items": [
                {"id": "fact:certificate", "label": "сертификат/декларация"},
                {"id": "fact:delivery", "label": "срок поставки"},
            ],
        },
        "analysis_feedback": {
            "fact:certificate": {"state": "correct", "comment": "Проверено по ТЗ."},
            "fact:delivery": {"state": "needs_manual_review", "comment": "Срок есть только в проекте контракта."},
        },
    }

    changes = build_analysis_change_summary({}, current)

    assert changes["feedback_count"] == 2
    assert changes["feedback"] == [
        "сертификат/декларация: верно — Проверено по ТЗ.",
        "срок поставки: требует ручной проверки — Срок есть только в проекте контракта.",
    ]


def test_analysis_history_detects_document_and_key_condition_changes():
    previous = {
        "documents_snapshot": [
            {"key": "tz", "name": "ТЗ.docx", "text_hash": "old-tz"},
            {"key": "old", "name": "Старый проект.docx", "text_hash": "old-project"},
        ],
        "analysis_facts": {
            "version": 1,
            "items": [
                {
                    "id": "fact:payment",
                    "label": "Оплата",
                    "category": "payment",
                    "value": "Оплата в течение 7 рабочих дней.",
                },
                {
                    "id": "fact:contract-security",
                    "label": "Обеспечение исполнения контракта",
                    "category": "financial",
                    "value": "Обеспечение исполнения контракта 5%.",
                },
            ],
        },
    }
    current = {
        "documents_snapshot": [
            {"key": "tz", "name": "ТЗ.docx", "text_hash": "new-tz"},
            {"key": "new", "name": "Новый проект.docx", "text_hash": "new-project"},
        ],
        "analysis_facts": {
            "version": 1,
            "items": [
                {
                    "id": "fact:payment",
                    "label": "Оплата",
                    "category": "payment",
                    "value": "Оплата в течение 15 рабочих дней.",
                },
                {
                    "id": "fact:contract-security",
                    "label": "Обеспечение исполнения контракта",
                    "category": "financial",
                    "value": "Обеспечение исполнения контракта 10%.",
                },
                {
                    "id": "fact:acceptance",
                    "label": "Приемка и УПД",
                    "category": "acceptance",
                    "value": "Закрывающие документы: УПД.",
                },
            ],
        },
    }

    changes = build_analysis_change_summary(previous, current, previous_run_id=7)

    assert changes["documents"] == {
        "added": ["Новый проект.docx"],
        "removed": ["Старый проект.docx"],
        "changed": ["ТЗ.docx"],
    }
    assert {
        (item["family"], item["label"], item["change_type"])
        for item in changes["condition_changes"]
    } >= {
        ("payment", "условия оплаты", "changed"),
        ("contract_security", "обеспечение контракта", "changed"),
        ("closing_documents", "приемка и закрывающие документы", "added"),
    }
    payment = next(item for item in changes["condition_changes"] if item["family"] == "payment")
    assert payment["before"] == "Оплата в течение 7 рабочих дней."
    assert payment["after"] == "Оплата в течение 15 рабочих дней."


def test_analysis_history_builds_condition_diff_v2_from_condition_groups():
    previous = {
        "documents_snapshot": [
            {"key": "contract", "name": "Проект контракта.docx", "text_hash": "old-contract"},
        ],
        "operator_view": {
            "condition_groups": {
                "version": 1,
                "items": [
                    {
                        "family": "payment",
                        "label": "условия оплаты",
                        "status": "confirmed",
                        "source_status": "explicit_source",
                        "summary": "Оплата в течение 7 рабочих дней.",
                        "sources": ["Проект контракта.docx · стр. 8"],
                        "operator_action": "Сверить оплату с проектом контракта.",
                    },
                    {
                        "family": "contract_security",
                        "label": "обеспечение контракта",
                        "status": "confirmed",
                        "source_status": "explicit_source",
                        "summary": "Обеспечение исполнения контракта 5%.",
                        "sources": ["Проект контракта.docx · стр. 12"],
                        "operator_action": "Учесть обеспечение в оборотке.",
                    },
                ],
            },
            "action_plan": [
                {"id": "acceptance_payment", "next_step": "Сверить оплату с проектом контракта."},
            ],
        },
    }
    current = {
        "documents_snapshot": [
            {"key": "contract", "name": "Проект контракта.docx", "text_hash": "new-contract"},
        ],
        "operator_view": {
            "condition_groups": {
                "version": 1,
                "items": [
                    {
                        "family": "payment",
                        "label": "условия оплаты",
                        "status": "manual_review",
                        "source_status": "primary_source",
                        "summary": "Оплата в течение 15 рабочих дней после подписания УПД.",
                        "sources": ["ПИК.zip · стр. 4"],
                        "operator_action": "Проверить оплату по ПИК.",
                    },
                    {
                        "family": "contract_security",
                        "label": "обеспечение контракта",
                        "status": "confirmed",
                        "source_status": "primary_source",
                        "summary": "Обеспечение исполнения контракта 10%.",
                        "sources": ["Проект контракта.docx · стр. 12"],
                        "operator_action": "Учесть обеспечение в оборотке.",
                    },
                    {
                        "family": "closing_documents",
                        "label": "приемка и закрывающие документы",
                        "status": "confirmed",
                        "source_status": "primary_source",
                        "summary": "Закрывающий документ: УПД.",
                        "sources": ["ПИК.zip · стр. 5"],
                        "operator_action": "Подготовить УПД к приемке.",
                    },
                ],
            },
            "action_plan": [
                {"id": "acceptance_payment", "next_step": "Проверить оплату по ПИК."},
            ],
        },
    }

    changes = build_analysis_change_summary(previous, current, previous_run_id=9)
    payment = next(item for item in changes["condition_changes"] if item["family"] == "payment")
    diff = changes["condition_diff"]

    assert diff["version"] == 2
    assert diff["metrics"] == {"added": 1, "removed": 0, "changed": 2}
    assert diff["action_plan_changed"] is True
    assert diff["documents"] == {"added": [], "removed": [], "changed": ["Проект контракта.docx"]}
    assert payment["change_type"] == "changed"
    assert payment["before"] == "Оплата в течение 7 рабочих дней."
    assert payment["after"] == "Оплата в течение 15 рабочих дней после подписания УПД."
    assert payment["status_before"] == "confirmed"
    assert payment["status_after"] == "manual_review"
    assert payment["sources_before"] == ["Проект контракта.docx · стр. 8"]
    assert payment["sources_after"] == ["ПИК.zip · стр. 4"]
    assert set(payment["changed_fields"]) >= {"summary", "status", "source_status", "sources", "operator_action"}
    assert diff["highlights"]["payment"]["change_type"] == "changed"
    assert diff["highlights"]["closing_documents"]["change_type"] == "added"
    assert diff["highlights"]["contract_security"]["change_type"] == "changed"
