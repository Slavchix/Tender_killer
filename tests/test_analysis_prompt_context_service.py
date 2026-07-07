from __future__ import annotations

import json
import sqlite3

from tender_killer.analysis_prompt_context_service import build_analysis_prompt_context
from tender_killer.analysis_service import analyze_tender_payload
from tender_killer.tender_detail_service import get_tender_payload
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
    assert context["context_pack"]["version"] == 1
    assert context["context_pack"]["documents"][0]["document_role"] == "technical_spec"
    assert "certificates_closing_docs" in {
        section["topic"] for section in context["context_pack"]["documents"][0]["section_taxonomy"]
    }


def test_build_analysis_prompt_context_reuses_current_context_pack() -> None:
    analysis = {
        "summary": "Supply of office paper.",
        "context_pack": {
            "version": 1,
            "mode": "deterministic_document_context",
            "documents": [
                {
                    "id": "document:1",
                    "name": "pik.zip",
                    "document_role": "pik_obligations_payment",
                    "source_priority": ["payment_terms", "acceptance_documents"],
                    "section_taxonomy": [{"topic": "payment_terms", "evidence": "Оплата 100%."}],
                }
            ],
            "metrics": {"documents": 1},
        },
    }

    context = build_analysis_prompt_context(analysis, [])

    assert context["context_pack"]["documents"][0]["name"] == "pik.zip"
    assert context["context_pack"]["documents"][0]["source_priority"] == [
        "payment_terms",
        "acceptance_documents",
    ]


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


def test_build_analysis_prompt_context_includes_source_bound_agent_contract() -> None:
    analysis = {
        "summary": "Supply with advance contradiction.",
        "confidence": 0.78,
        "analysis_facts": {
            "version": 1,
            "metrics": {"items": 2},
            "items": [
                {
                    "id": "fact:advance-positive",
                    "kind": "execution_term",
                    "label": "Advance",
                    "value": "Advance payment 30% is required.",
                    "category": "financial",
                    "severity": "medium",
                    "document_name": "contract.docx",
                    "source_page": 3,
                    "source_label": "contract.docx / p. 3",
                    "source_context": "Advance payment is 30% of the contract price.",
                    "fragment": "Advance payment is 30% of the contract price.",
                    "conflict_flags": ["Documents contain mutually exclusive advance payment terms."],
                    "needs_review": True,
                },
                {
                    "id": "fact:payment-docs",
                    "kind": "requirement",
                    "label": "Closing documents",
                    "value": "Payment after closing documents.",
                    "category": "acceptance",
                    "severity": "medium",
                    "document_name": "tz.docx",
                    "source_page": 2,
                    "source_label": "tz.docx / p. 2",
                    "source_context": "Supplier provides closing documents after delivery.",
                    "fragment": "Supplier provides closing documents after delivery.",
                },
            ],
        },
    }
    documents = [
        {
            "name": "contract.docx",
            "document_type": "contract",
            "text_status": "ok",
            "text_content": "Advance payment is 30% of the contract price.",
        },
        {
            "name": "tz.docx",
            "document_type": "technical specification",
            "text_status": "ok",
            "text_content": "Supplier provides closing documents after delivery.",
        },
    ]

    context = build_analysis_prompt_context(analysis, documents)
    contract = context["agent_contract"]

    assert contract["version"] == 1
    assert contract["guardrails"]["answer_only_from_sources"] is True
    assert contract["guardrails"]["unknown_when_no_source"] is True
    assert contract["output_schema"]["fields"] == [
        "decision",
        "answers",
        "facts_patch",
        "condition_review",
        "conflicts",
        "expected_missing",
        "manual_review",
    ]
    assert contract["fact_patch_policy"]["allowed_operations"] == [
        "keep",
        "revise",
        "mark_not_supported",
        "mark_manual_review",
    ]

    questions = {item["id"]: item for item in contract["questions"]}
    assert {"advance", "payment_documents", "participation_blockers", "acceptance_source"} <= set(questions)
    assert questions["advance"]["answer_status"] == "found"
    assert questions["advance"]["sources"][0]["fact_id"] == "fact:advance-positive"
    assert questions["advance"]["sources"][0]["source_label"] == "contract.docx / p. 3"
    assert questions["participation_blockers"]["answer_status"] == "found"
    assert contract["manual_review_triggers"]
    assert context["metrics"]["agent_questions"] == 4


def test_build_analysis_prompt_context_includes_condition_groups_and_diff() -> None:
    analysis = {
        "summary": "Поставка бумаги.",
        "operator_view": {
            "condition_groups": {
                "version": 1,
                "items": [
                    {
                        "family": "payment",
                        "label": "условия оплаты",
                        "status": "confirmed",
                        "source_status": "primary_source",
                        "value": "Оплата в течение 15 рабочих дней после УПД.",
                        "sources": ["ПИК.docx · стр. 4", "Контракт.docx · стр. 7"],
                        "primary_fact_id": "fact:payment",
                        "related_fact_ids": ["fact:payment", "fact:closing-docs"],
                        "operator_action": "Проверить УПД и срок оплаты.",
                    },
                    {
                        "family": "advance",
                        "label": "аванс",
                        "status": "expected_missing",
                        "source_status": "missing",
                        "value": "",
                        "sources": [],
                        "operator_action": "Проверить, предусмотрен ли аванс.",
                    },
                ],
            }
        },
        "analysis_history": [
            {
                "changes": {
                    "condition_diff": {
                        "version": 2,
                        "metrics": {"added": 1, "removed": 0, "changed": 1},
                        "items": [
                            {
                                "family": "payment",
                                "label": "условия оплаты",
                                "change_type": "changed",
                                "status_before": "manual_review",
                                "status_after": "confirmed",
                                "sources_before": ["Контракт.docx · стр. 7"],
                                "sources_after": ["ПИК.docx · стр. 4", "Контракт.docx · стр. 7"],
                                "changed_fields": ["status", "sources"],
                            }
                        ],
                        "highlights": {
                            "payment": {
                                "family": "payment",
                                "label": "условия оплаты",
                                "change_type": "changed",
                            }
                        },
                        "action_plan_changed": True,
                    }
                }
            }
        ],
        "analysis_facts": {
            "version": 1,
            "items": [
                {
                    "id": "fact:payment",
                    "kind": "execution_term",
                    "label": "Оплата",
                    "value": "Оплата в течение 15 рабочих дней после УПД.",
                    "category": "payment",
                    "document_name": "ПИК.docx",
                    "source_label": "ПИК.docx · стр. 4",
                    "fragment": "Оплата в течение 15 рабочих дней после УПД.",
                }
            ],
        },
    }

    context = build_analysis_prompt_context(analysis, [])

    assert context["source_contract"]["condition_schema"] == "analysis.operator_view.condition_groups.version=1"
    assert context["condition_groups"]["version"] == 1
    assert context["condition_groups"]["items"][0]["family"] == "payment"
    assert context["condition_groups"]["items"][0]["sources"] == ["ПИК.docx · стр. 4", "Контракт.docx · стр. 7"]
    assert context["condition_diff"]["version"] == 2
    assert context["condition_diff"]["metrics"] == {"added": 1, "removed": 0, "changed": 1}
    assert context["condition_diff"]["highlights"][0]["family"] == "payment"
    assert context["agent_contract"]["condition_patch_policy"]["requires_condition_source"] is True
    assert context["metrics"]["condition_groups"] == 2
    assert context["metrics"]["condition_diff_items"] == 1


def test_build_analysis_prompt_context_builds_agent_review_plan_from_conditions() -> None:
    analysis = {
        "summary": "Supply with condition issues.",
        "operator_view": {
            "condition_groups": {
                "version": 1,
                "items": [
                    {
                        "family": "advance",
                        "label": "Advance",
                        "status": "conflict",
                        "source_status": "conflicting_sources",
                        "value": "Advance both present and absent.",
                        "sources": ["contract.docx / p. 3", "terms.docx / p. 5"],
                        "primary_fact_id": "fact:advance-positive",
                        "related_fact_ids": ["fact:advance-positive", "fact:advance-negative"],
                        "operator_action": "Resolve advance contradiction.",
                    },
                    {
                        "family": "payment",
                        "label": "Payment terms",
                        "status": "confirmed",
                        "source_status": "primary_source",
                        "value": "Payment within 15 business days after UPD.",
                        "sources": ["payment.docx / p. 2"],
                        "primary_fact_id": "fact:payment",
                        "related_fact_ids": ["fact:payment"],
                        "operator_action": "Check payment trigger.",
                    },
                    {
                        "family": "closing_documents",
                        "label": "Closing documents",
                        "status": "expected_missing",
                        "source_status": "missing",
                        "value": "",
                        "sources": [],
                        "primary_fact_id": "missing:closing-documents",
                        "related_fact_ids": ["missing:closing-documents"],
                        "operator_action": "Find acceptance and closing documents.",
                    },
                    {
                        "family": "license_sro",
                        "label": "License/SRO",
                        "status": "manual_review",
                        "source_status": "weak_source",
                        "value": "License may be required.",
                        "sources": ["summary.html"],
                        "primary_fact_id": "fact:license",
                        "related_fact_ids": ["fact:license"],
                        "operator_action": "Check participant requirements.",
                    },
                ],
            }
        },
        "analysis_history": [
            {
                "changes": {
                    "condition_diff": {
                        "version": 2,
                        "metrics": {"added": 0, "removed": 0, "changed": 1},
                        "items": [
                            {
                                "family": "payment",
                                "label": "Payment terms",
                                "change_type": "changed",
                                "status_before": "manual_review",
                                "status_after": "confirmed",
                                "value_before": "Payment within 30 days.",
                                "value_after": "Payment within 15 business days after UPD.",
                                "sources_after": ["payment.docx / p. 2"],
                                "changed_fields": ["status", "value", "sources"],
                            }
                        ],
                    }
                }
            }
        ],
        "analysis_facts": {"version": 1, "items": []},
    }

    context = build_analysis_prompt_context(analysis, [])

    review_plan = context["agent_review_plan"]
    assert review_plan["version"] == 1
    assert review_plan["mode"] == "condition_first_review"
    assert review_plan["metrics"] == {
        "total": 4,
        "conflicts": 1,
        "changed": 1,
        "expected_missing": 1,
        "manual_review": 1,
    }
    operations = {item["family"]: item["operation"] for item in review_plan["items"]}
    assert operations == {
        "advance": "mark_conflict",
        "payment": "revise",
        "closing_documents": "mark_expected_missing",
        "license_sro": "mark_manual_review",
    }
    assert review_plan["items"][0]["family"] == "advance"
    assert review_plan["items"][0]["related_fact_ids"] == ["fact:advance-positive", "fact:advance-negative"]
    assert review_plan["items"][1]["family"] == "payment"
    assert review_plan["items"][1]["diff"]["change_type"] == "changed"
    assert review_plan["items"][1]["changed_fields"] == ["status", "value", "sources"]
    assert context["source_contract"]["review_plan_schema"] == "analysis.agent_review_plan.version=1"
    assert context["agent_contract"]["condition_review_plan"]["schema"] == "analysis.agent_review_plan.version=1"
    assert context["metrics"]["agent_review_items"] == 4


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
    assert payload["analysis"]["context_pack"]["version"] == 1
    assert context["context_pack"]["version"] == 1
    assert context["context_pack"]["documents"][0]["document_role"] == "technical_spec"
    assert context["evidence_items"]
    assert context["analysis_facts"]["items"]
    assert all(
        item.get("source_binding")
        for item in context["analysis_facts"]["items"]
        if item.get("kind") != "subject"
    )
    with sqlite3.connect(store.database_path) as connection:
        raw_payload_json = connection.execute(
            """
            SELECT raw_payload_json
            FROM tender_analysis
            WHERE source = ? AND external_id = ?
            """,
            ("mosreg_market", "agent-context-1"),
        ).fetchone()[0]
    assert '"agent_prompt_context"' in raw_payload_json
    assert '"agent_contract"' in raw_payload_json


def test_get_tender_payload_rebuilds_stale_agent_prompt_context(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="agent-context-stale",
            url="https://market.mosreg.ru/Trade/ViewTrade/agent-context-stale",
            title="Agent stale context tender",
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
                "agent-context-stale",
                "https://example.test/terms.pdf",
            ),
        )

    analyze_tender_payload(store.database_path, "mosreg_market", "agent-context-stale")
    with sqlite3.connect(store.database_path) as connection:
        raw_payload_json = connection.execute(
            """
            SELECT raw_payload_json
            FROM tender_analysis
            WHERE source = ? AND external_id = ?
            """,
            ("mosreg_market", "agent-context-stale"),
        ).fetchone()[0]
        raw_payload = json.loads(raw_payload_json)
        raw_payload["agent_prompt_context"] = {
            "version": 1,
            "mode": "document_aware_agent_prompt",
            "agent_contract": {"version": 1},
            "context_pack": {"version": 1, "documents": []},
        }
        connection.execute(
            """
            UPDATE tender_analysis
            SET raw_payload_json = ?
            WHERE source = ? AND external_id = ?
            """,
            (
                json.dumps(raw_payload, ensure_ascii=False),
                "mosreg_market",
                "agent-context-stale",
            ),
        )

    detail = get_tender_payload(store.database_path, "mosreg_market", "agent-context-stale")
    context = detail["analysis"]["agent_prompt_context"]

    assert context["agent_contract"]["guardrails"]["answer_only_from_sources"] is True
    assert context["agent_contract"]["questions"]
    assert context["agent_review_plan"]["version"] == 1
