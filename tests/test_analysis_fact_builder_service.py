from __future__ import annotations

import importlib
import importlib.util


def _fact_builder_service():
    spec = importlib.util.find_spec("tender_killer.analysis_fact_builder_service")
    assert spec is not None
    return importlib.import_module("tender_killer.analysis_fact_builder_service")


def test_build_fact_creates_document_bound_operator_fact():
    service = _fact_builder_service()

    fact = service.build_fact(
        kind="requirement",
        label="license",
        value="Need license.",
        category="legal",
        severity="high",
        confidence=0.91,
        rule_id="checklist:license",
        fragment="Need license.",
        document_name="tz.docx",
        source_page=2,
        source_context="Need license.",
        is_blocker=True,
        is_price_factor=False,
        impact="Check before bid.",
        metadata={"days": None, "document_stage": "bid"},
        semantic_key="license_sro",
    )

    assert fact["id"] == "requirement:license"
    assert fact["confidence"] == 0.91
    assert fact["document_name"] == "tz.docx"
    assert fact["source_page"] == 2
    assert fact["source_label"] == "tz.docx · стр. 2"
    assert fact["source_binding"]["level"] == "explicit"
    assert fact["confidence_level"]["level"] == "high"
    assert fact["operator_group"] == "blocker"
    assert fact["price_impact"] == "compliance"
    assert fact["priority"] == 90
    assert fact["document_stage"] == "bid"
    assert "days" not in fact
    assert fact["evidence_sources"] == [
        {
            "document_name": "tz.docx",
            "source_label": "tz.docx · стр. 2",
            "fragment": "Need license.",
        }
    ]


def test_build_fact_marks_fragment_without_document_as_manual_review():
    service = _fact_builder_service()

    fact = service.build_fact(
        kind="execution_term",
        label="payment",
        value="Payment after acceptance.",
        category="payment",
        severity="medium",
        confidence="0.7",
        rule_id="execution_term:payment",
        fragment="Payment after acceptance.",
        is_price_factor=True,
    )

    assert fact["document_name"] == "Документ не привязан"
    assert fact["needs_review"] is True
    assert fact["source_binding"]["level"] == "unbound"
    assert fact["confidence_level"]["level"] == "low"
    assert fact["operator_group"] == "manual_review"
    assert fact["priority"] == 95
