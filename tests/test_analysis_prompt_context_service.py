from __future__ import annotations

import sqlite3

from tender_killer.analysis_prompt_context_service import build_analysis_prompt_context
from tender_killer.analysis_service import analyze_tender_payload
from tender_killer.models import Tender
from tender_killer.models import TenderDocument
from tender_killer.storage import TenderStore


def test_build_analysis_prompt_context_preserves_document_bound_evidence_and_facts() -> None:
    analysis = {
        "summary": "Supply of office paper.",
        "confidence": 0.82,
        "checklist": [
            {
                "label": "Certificate",
                "category": "documents",
                "severity": "medium",
                "evidence": "Supplier must provide certificate before acceptance.",
            }
        ],
        "evidence_items": [
            {
                "id": "cert-1",
                "label": "Certificate",
                "category": "documents",
                "severity": "medium",
                "document_name": "terms.pdf",
                "source_page": 2,
                "source_label": "terms.pdf / p. 2",
                "source_context": "Page two. Supplier must provide certificate before acceptance.",
                "fragment": "Supplier must provide certificate before acceptance.",
            }
        ],
        "analysis_facts": {
            "version": 1,
            "metrics": {"items": 1},
            "items": [
                {
                    "id": "supplier_document:certificate",
                    "kind": "supplier_document",
                    "label": "Certificate",
                    "value": "Certificate is required.",
                    "category": "documents",
                    "severity": "medium",
                    "document_name": "terms.pdf",
                    "source_page": 2,
                    "source_label": "terms.pdf / p. 2",
                    "source_context": "Page two. Supplier must provide certificate before acceptance.",
                    "source_binding": {
                        "document_name": "terms.pdf",
                        "source_page": 2,
                        "source_label": "terms.pdf / p. 2",
                        "source_context": "Page two. Supplier must provide certificate before acceptance.",
                    },
                }
            ],
        },
    }
    documents = [
        {
            "name": "terms.pdf",
            "document_type": "technical specification",
            "text_status": "ok",
            "text_content": (
                "Page one has general conditions.\f"
                "Page two. Supplier must provide certificate before acceptance."
            ),
        }
    ]

    context = build_analysis_prompt_context(analysis, documents)

    assert context["version"] == 1
    assert context["mode"] == "document_aware_agent_prompt"
    assert context["source_contract"]["preserve_document_bindings"] is True
    assert context["documents"][0]["name"] == "terms.pdf"
    assert context["documents"][0]["chunks"][1]["page"] == 2
    assert context["evidence_items"][0]["document_name"] == "terms.pdf"
    assert context["evidence_items"][0]["source_page"] == 2
    assert context["analysis_facts"]["items"][0]["source_binding"]["document_name"] == "terms.pdf"
    assert context["analysis_facts"]["items"][0]["source_binding"]["source_page"] == 2


def test_build_analysis_prompt_context_derives_missing_evidence_from_documents() -> None:
    analysis = {
        "summary": "Supply of office paper.",
        "confidence": 0.7,
        "checklist": [
            {
                "label": "Delivery",
                "category": "delivery",
                "severity": "high",
                "evidence": "Delivery must be completed within 3 days.",
            }
        ],
    }
    documents = [
        {
            "name": "contract.pdf",
            "document_type": "contract",
            "text_status": "ok",
            "text_content": "Contract terms.\fDelivery must be completed within 3 days.",
        }
    ]

    context = build_analysis_prompt_context(analysis, documents)

    assert context["metrics"]["documents"] == 1
    assert context["metrics"]["evidence_items"] == 1
    assert context["metrics"]["facts"] >= 1
    assert context["evidence_items"][0]["document_name"] == "contract.pdf"
    assert context["evidence_items"][0]["source_page"] == 2
    bound_fact = next(item for item in context["analysis_facts"]["items"] if item.get("kind") != "subject")
    assert bound_fact["source_binding"]["document_name"] == "contract.pdf"


def test_analyze_tender_payload_exposes_agent_prompt_context_with_bindings(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="agent-context-1",
            url="https://market.mosreg.ru/Trade/ViewTrade/agent-context-1",
            title="Agent context tender",
            document_records=[
                TenderDocument(
                    url="https://example.test/terms.pdf",
                    name="terms.pdf",
                    document_type="technical specification",
                )
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
                "Technical specification: office paper.\fSupplier must provide certificate before acceptance.",
                "2026-06-10T09:00:00",
                "mosreg_market",
                "agent-context-1",
                "https://example.test/terms.pdf",
            ),
        )

    payload = analyze_tender_payload(store.database_path, "mosreg_market", "agent-context-1")
    context = payload["analysis"]["agent_prompt_context"]

    assert context["mode"] == "document_aware_agent_prompt"
    assert context["documents"][0]["name"] == "terms.pdf"
    assert context["evidence_items"]
    assert context["analysis_facts"]["items"]
    assert all(
        item.get("source_binding")
        for item in context["analysis_facts"]["items"]
        if item.get("kind") != "subject"
    )
