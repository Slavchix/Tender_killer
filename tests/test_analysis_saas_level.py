from __future__ import annotations

import json
import sqlite3
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from tender_killer.api_handlers import handle_post_request
from tender_killer.analysis_operator_view_service import build_analysis_operator_view
from tender_killer.analysis_playbook_service import build_analysis_playbooks
from tender_killer.models import Tender
from tender_killer.models import TenderDocument
from tender_killer.reports import build_tender_report_docx
from tender_killer.storage import TenderStore
from tender_killer.tender_detail_service import get_tender_payload


WEB_API_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "api.js"
USE_TENDER_DOCUMENT_ANALYSIS_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "useTenderDocumentAnalysis.js"
)
TENDER_ANALYSIS_TAB_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderAnalysisTab.jsx"
STYLES_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "styles.css"
STYLES_ANALYSIS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "styles.analysis.css"
STYLES_ECONOMICS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "styles.economics.css"


def read_styles_source() -> str:
    return "\n".join(
        (
            STYLES_SOURCE.read_text(encoding="utf-8"),
            STYLES_ANALYSIS_SOURCE.read_text(encoding="utf-8"),
            STYLES_ECONOMICS_SOURCE.read_text(encoding="utf-8"),
        )
    )


def test_operator_view_exposes_tz_workflow_questions_and_playbooks():
    view = build_analysis_operator_view(
        {
            "summary": "Office paper supply.",
            "status": "needs_review",
            "tz_workflow": {
                "responsible": "Anna",
                "deadline": "2026-06-30",
                "comment": "Check contract version before bid.",
                "journal": [
                    {
                        "action": "comment",
                        "actor": "Anna",
                        "comment": "Initial review started.",
                        "changed_at": "2026-06-22T10:00:00",
                    }
                ],
            },
            "analysis_facts": {
                "version": 1,
                "items": [
                    {
                        "id": "fact:advance-positive",
                        "kind": "execution_term",
                        "label": "Advance payment",
                        "value": "Advance payment 30% of contract price.",
                        "category": "financial",
                        "severity": "medium",
                        "document_name": "Contract.docx",
                        "source_label": "Contract.docx p. 2",
                        "fragment": "Advance payment 30% of contract price.",
                        "conflict_flags": ["Advance is also absent in another document."],
                    },
                    {
                        "id": "fact:payment-documents",
                        "kind": "execution_term",
                        "label": "Payment documents",
                        "value": "Payment requires UPD and signed acceptance act.",
                        "category": "payment",
                        "severity": "medium",
                        "document_name": "Contract.docx",
                        "source_label": "Contract.docx p. 5",
                        "fragment": "Payment requires UPD and signed acceptance act.",
                    },
                    {
                        "id": "fact:acceptance",
                        "kind": "execution_term",
                        "label": "Acceptance procedure",
                        "value": "Customer signs acceptance act within 5 business days.",
                        "category": "acceptance",
                        "severity": "medium",
                        "document_name": "Terms.docx",
                        "source_label": "Terms.docx p. 4",
                        "fragment": "Customer signs acceptance act within 5 business days.",
                    },
                    {
                        "id": "fact:national-regime",
                        "kind": "blocker",
                        "label": "National regime",
                        "value": "Country of origin must be declared in the bid.",
                        "category": "national_regime",
                        "severity": "high",
                        "document_name": "Spec.docx",
                        "source_label": "Spec.docx p. 7",
                        "fragment": "Country of origin must be declared in the bid.",
                        "is_blocker": True,
                    },
                ],
            },
        },
        [{"name": "Contract.docx", "local_path": "Contract.docx", "text_status": "ok"}],
    )

    workflow = view["tz_workflow"]
    assert workflow["version"] == 1
    assert workflow["status"] == "has_blockers"
    assert workflow["responsible"] == "Anna"
    assert workflow["deadline"] == "2026-06-30"
    assert workflow["comment"] == "Check contract version before bid."
    assert workflow["journal"][0]["comment"] == "Initial review started."
    assert [status["id"] for status in workflow["statuses"]] == [
        "documents_not_downloaded",
        "text_extracted",
        "analysis_ready",
        "operator_verified",
        "has_blockers",
    ]

    questions = {item["id"]: item for item in view["ai_questions"]["items"]}
    assert set(questions) == {"advance", "payment_documents", "participation_blockers", "acceptance_source"}
    assert questions["advance"]["answer_status"] == "found"
    assert questions["advance"]["sources"][0]["fact_id"] == "fact:advance-positive"
    assert questions["advance"]["sources"][0]["fragment"] == "Advance payment 30% of contract price."
    assert questions["payment_documents"]["sources"][0]["source_label"] == "Contract.docx p. 5"
    assert questions["participation_blockers"]["sources"][0]["fact_id"] == "fact:national-regime"
    assert questions["acceptance_source"]["sources"][0]["fragment"] == "Customer signs acceptance act within 5 business days."

    playbooks = {item["id"]: item for item in view["playbooks"]["items"]}
    assert {"contradictions", "clarification_request", "skip_procurement", "supplier_dangerous_terms"} <= set(playbooks)
    assert playbooks["contradictions"]["severity"] == "high"
    assert "fact:advance-positive" in playbooks["contradictions"]["source_fact_ids"]
    assert playbooks["clarification_request"]["when_to_use"]
    assert playbooks["skip_procurement"]["skip_conditions"]
    assert playbooks["supplier_dangerous_terms"]["dangerous_for_supplier"]

    drilldowns = {item["id"]: item for item in view["evidence_drilldowns"]["items"]}
    assert drilldowns["fact:advance-positive"]["title"] == "Advance payment"
    assert drilldowns["fact:advance-positive"]["source_label"] == "Contract.docx p. 2"
    assert drilldowns["fact:advance-positive"]["fragment"] == "Advance payment 30% of contract price."
    assert drilldowns["fact:advance-positive"]["evidence_quality"]["level"] == "conflict"
    assert drilldowns["fact:national-regime"]["related_fact_ids"] == ["fact:national-regime"]
    assert view["evidence_drilldowns"]["by_fact_id"]["fact:payment-documents"] == "fact:payment-documents"


def test_playbooks_use_readable_russian_operator_text():
    playbooks = build_analysis_playbooks(
        [
            {
                "id": "fact:advance-positive",
                "label": "Аванс",
                "severity": "medium",
                "conflict_flags": ["Есть взаимоисключающие условия по авансу."],
                "needs_review": True,
            },
            {
                "id": "fact:docs-missing",
                "label": "приемка и закрывающие документы",
                "expected_missing": True,
            },
        ],
        {"unbound_facts": 1},
    )

    titles = [item["title"] for item in playbooks["items"]]
    assert "Противоречия в документах" in titles
    assert "Когда писать запрос разъяснений" in titles
    assert all("Рџ" not in title for title in titles)
    clarification = next(item for item in playbooks["items"] if item["id"] == "clarification_request")
    assert "Сформулировать вопрос коротко" in clarification["what_to_do"][0]
    assert "РЎ" not in " ".join(clarification["what_to_do"])


def test_analysis_workflow_endpoint_persists_owner_deadline_comment_and_journal(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3668200",
            url="https://example.test/tender/3668200",
            title="Office paper",
            customer="School",
            document_records=[
                TenderDocument(
                    name="Contract.docx",
                    url="https://example.test/contract.docx",
                    local_path="Contract.docx",
                    text_status="ok",
                )
            ],
        )
    )
    with sqlite3.connect(store.database_path) as connection:
        connection.execute(
            """
            UPDATE tender_documents
            SET text_content = ?, text_extracted_at = ?
            WHERE source = ? AND external_id = ? AND url = ?
            """,
            (
                "Payment requires UPD and signed acceptance act.",
                "2026-06-22T09:00:00",
                "mosreg_market",
                "3668200",
                "https://example.test/contract.docx",
            ),
        )
        connection.execute(
            """
            INSERT INTO tender_analysis (
                source, external_id, summary, requirements_json, risks_json,
                red_flags_json, recommended_status, confidence, raw_payload_json, analyzed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "mosreg_market",
                "3668200",
                "Office paper",
                "[]",
                "[]",
                "[]",
                "needs_review",
                0.8,
                json.dumps(
                    {
                        "summary": "Office paper",
                        "analysis_facts": {"version": 1, "items": []},
                    },
                    ensure_ascii=False,
                ),
                "2026-06-22T10:00:00",
            ),
        )

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/analysis/workflow",
        {
            "status": "operator_verified",
            "responsible": "Anna",
            "deadline": "2026-06-30",
            "comment": "Facts verified.",
            "actor": "Anna",
        },
    )

    assert response.status == 200
    workflow = response.payload["analysis"]["operator_view"]["tz_workflow"]
    assert workflow["status"] == "operator_verified"
    assert workflow["responsible"] == "Anna"
    assert workflow["deadline"] == "2026-06-30"
    assert workflow["comment"] == "Facts verified."
    assert workflow["journal"][-1]["action"] == "workflow_update"
    assert workflow["journal"][-1]["actor"] == "Anna"

    detail = get_tender_payload(store.database_path, "mosreg_market", "3668200")
    assert detail["analysis"]["operator_view"]["tz_workflow"]["comment"] == "Facts verified."


def test_frontend_exposes_tz_saas_workflow_questions_and_playbooks():
    api_source = WEB_API_SOURCE.read_text(encoding="utf-8")
    hook_source = USE_TENDER_DOCUMENT_ANALYSIS_SOURCE.read_text(encoding="utf-8")
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    styles_source = read_styles_source()

    assert "export function saveAnalysisWorkflow" in api_source
    assert "/analysis/workflow" in api_source
    assert "saveAnalysisWorkflow" in hook_source
    assert "saveTzWorkflow" in hook_source
    assert "savingAnalysisWorkflow" in hook_source
    assert "AnalysisWorkflowPanel" in analysis_source
    assert "AnalysisQuestionsPanel" in analysis_source
    assert "AnalysisPlaybooksPanel" in analysis_source
    assert "AnalysisEvidenceDrilldownPanel" in analysis_source
    assert "selectedEvidence" in analysis_source
    assert "onEvidenceSelect" in analysis_source
    assert "operator_view?.evidence_drilldowns" in analysis_source
    assert "operator_view?.tz_workflow" in analysis_source
    assert "operator_view?.condition_groups" in analysis_source
    assert "AnalysisConditionGroupsPanel" in analysis_source
    assert "conditionGroupStatusLabel" in analysis_source
    assert "operator_view?.ai_questions" in analysis_source
    assert "operator_view?.playbooks" in analysis_source
    assert "analysis-workflow-panel" in styles_source
    assert "analysis-condition-groups" in styles_source
    assert "analysis-condition-card" in styles_source
    assert "analysis-questions-grid" in styles_source
    assert "analysis-playbook-list" in styles_source
    assert "analysis-evidence-drilldown" in styles_source


def test_word_report_renders_tz_workflow_questions_and_playbooks():
    content = build_tender_report_docx(
        {
            "source": "mosreg_market",
            "external_id": "3668200",
            "title": "Office paper",
            "customer": "School",
            "document_records": [],
            "analysis": {
                "summary": "Office paper",
                "status": "needs_review",
                "confidence": 0.8,
                "operator_view": {
                    "version": 3,
                    "tz_workflow": {
                        "version": 1,
                        "status": "operator_verified",
                        "responsible": "Anna",
                        "deadline": "2026-06-30",
                        "comment": "Facts verified.",
                        "journal": [{"action": "workflow_update", "actor": "Anna", "comment": "Facts verified."}],
                    },
                    "ai_questions": {
                        "version": 1,
                        "items": [
                            {
                                "id": "advance",
                                "question": "Is advance present?",
                                "answer": "Advance payment 30%.",
                                "answer_status": "found",
                                "sources": [
                                    {
                                        "fact_id": "fact:advance",
                                        "source_label": "Contract.docx p. 2",
                                        "fragment": "Advance payment 30%.",
                                    }
                                ],
                            }
                        ],
                    },
                    "playbooks": {
                        "version": 1,
                        "items": [
                            {
                                "id": "clarification_request",
                                "title": "Clarification before bid",
                                "severity": "medium",
                                "what_to_do": ["Send request before price approval."],
                                "when_to_use": ["Source wording affects bid decision."],
                                "source_fact_ids": ["fact:advance"],
                            }
                        ],
                    },
                    "decision_brief": {"title": "Check terms", "summary": "Manual review", "reasons": []},
                    "action_plan": [],
                    "major_blocks": [
                        {"id": "decision_risks", "title": "Decision", "items": []},
                        {"id": "product_compliance", "title": "Product", "items": []},
                        {"id": "fulfillment_terms", "title": "Fulfillment", "items": []},
                        {"id": "acceptance_payment", "title": "Payment", "items": []},
                    ],
                },
            },
        }
    )

    document_xml = _document_xml(content)

    assert "Anna" in document_xml
    assert "Facts verified." in document_xml
    assert "Is advance present?" in document_xml
    assert "Advance payment 30%." in document_xml
    assert "Clarification before bid" in document_xml
    assert "Send request before price approval." in document_xml
    assert "Контрольные вопросы ТЗ" in document_xml
    assert "Плейбуки оператора" in document_xml
    assert "AI-вопросы" not in document_xml
    assert "Tender playbooks" not in document_xml


def _document_xml(content: bytes) -> str:
    with ZipFile(BytesIO(content)) as archive:
        return archive.read("word/document.xml").decode("utf-8")
