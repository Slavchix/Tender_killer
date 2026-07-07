from __future__ import annotations

from typing import get_type_hints

from tender_killer.analysis_types import AnalysisFact
from tender_killer.analysis_types import AnalysisFactsContract
from tender_killer.analysis_types import ConditionGroup
from tender_killer.analysis_types import OperatorItem
from tender_killer.analysis_types import OperatorSection
from tender_killer.analysis_types import OperatorView


def test_analysis_types_define_cross_layer_contracts():
    assert AnalysisFactsContract.__required_keys__ == frozenset({"version", "items", "metrics"})

    fact_fields = set(AnalysisFact.__annotations__)
    assert {
        "id",
        "kind",
        "label",
        "category",
        "source_binding",
        "confidence_level",
        "evidence_quality",
        "operator_action",
        "price_impact",
        "priority",
        "feedback_state",
        "feedback_label",
        "feedback_comment",
        "feedback_history",
    }.issubset(fact_fields)

    operator_fields = set(OperatorItem.__annotations__)
    assert {"interpretation", "display_tier", "weak_reason", "needs_review"}.issubset(operator_fields)
    assert OperatorItem is not AnalysisFact

    condition_fields = set(ConditionGroup.__annotations__)
    assert {"family", "status", "primary_fact_id", "related_fact_ids", "operator_action"}.issubset(
        condition_fields
    )

    assert {"major_blocks", "condition_groups", "decision_brief", "metrics"}.issubset(
        set(OperatorView.__annotations__)
    )


def test_operator_view_contract_uses_operator_specific_items_and_required_keys():
    assert get_type_hints(OperatorSection)["items"] == list[OperatorItem]
    assert OperatorView.__required_keys__ == frozenset(
        {
            "version",
            "document_state",
            "tz_workflow",
            "ai_questions",
            "playbooks",
            "evidence_drilldowns",
            "condition_groups",
            "decision_brief",
            "action_plan",
            "metrics",
            "major_blocks",
            "sections",
        }
    )
    assert {"operator_summary", "operator_check", "source_binding", "evidence_quality"}.issubset(
        set(OperatorItem.__annotations__)
    )
