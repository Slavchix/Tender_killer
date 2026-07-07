from __future__ import annotations

from tender_killer.analysis_operator_evidence_service import build_operator_confidence_level
from tender_killer.analysis_operator_evidence_service import build_operator_evidence_quality
from tender_killer.analysis_operator_evidence_service import build_operator_source_binding
from tender_killer.analysis_operator_evidence_service import operator_evidence_text


def test_build_operator_source_binding_marks_unbound_fact_for_manual_review():
    binding = build_operator_source_binding(
        raw_item={},
        source="Документ не привязан",
        source_label="Документ не привязан",
        source_context="",
        fragment="Аванс предусмотрен.",
        needs_review=True,
    )
    confidence = build_operator_confidence_level(
        {},
        binding,
        fragment="Аванс предусмотрен.",
        source_context="",
    )
    quality = build_operator_evidence_quality(
        source_binding=binding,
        confidence_level=confidence,
        conflict_flags=[],
        expected_missing=False,
    )

    assert binding["level"] == "unbound"
    assert confidence["level"] == "low"
    assert quality["level"] == "inferred"


def test_operator_evidence_text_ignores_label_only_values():
    assert operator_evidence_text(label="Оплата", value="Оплата", fragment="") == ""
    assert (
        operator_evidence_text(
            label="Оплата",
            value="Оплата",
            fragment="Оплата в течение 7 рабочих дней.",
        )
        == "Оплата в течение 7 рабочих дней."
    )
