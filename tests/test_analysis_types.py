from __future__ import annotations

from tender_killer.analysis_types import AnalysisFact
from tender_killer.analysis_types import AnalysisFactsContract
from tender_killer.analysis_types import ConditionGroup
from tender_killer.analysis_types import OperatorItem
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

    condition_fields = set(ConditionGroup.__annotations__)
    assert {"family", "status", "primary_fact_id", "related_fact_ids", "operator_action"}.issubset(
        condition_fields
    )

    assert {"major_blocks", "condition_groups", "decision_brief", "metrics"}.issubset(
        set(OperatorView.__annotations__)
    )
