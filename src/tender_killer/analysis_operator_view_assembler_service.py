from __future__ import annotations

from typing import Any

from tender_killer.analysis_action_plan_service import build_analysis_action_plan
from tender_killer.analysis_condition_groups_service import build_condition_groups
from tender_killer.analysis_evidence_drilldown_service import build_evidence_drilldowns
from tender_killer.analysis_operator_sections_service import operator_item_is_analysis_item as _is_analysis_item
from tender_killer.analysis_operator_summary_service import build_operator_decision_brief
from tender_killer.analysis_operator_summary_service import build_operator_view_metrics
from tender_killer.analysis_playbook_service import build_analysis_playbooks
from tender_killer.analysis_questions_service import build_analysis_ai_questions
from tender_killer.analysis_types import OperatorSection
from tender_killer.analysis_types import OperatorView
from tender_killer.analysis_workflow_service import build_analysis_tz_workflow


def assemble_operator_view(
    *,
    analysis: dict[str, Any],
    sections: list[OperatorSection],
    document_state: dict[str, Any],
    status: str,
    fact_metrics: Any = None,
) -> OperatorView:
    items = [item for section in sections for item in section["items"] if _is_analysis_item(item)]
    condition_groups = build_condition_groups(items)
    decision = build_operator_decision_brief(analysis, sections, status)
    action_plan = build_analysis_action_plan(sections, document_state, condition_groups)
    metrics = build_operator_view_metrics(items, sections, document_state, fact_metrics)
    tz_workflow = build_analysis_tz_workflow(analysis, document_state, metrics, status=status)
    ai_questions = build_analysis_ai_questions(items)
    playbooks = build_analysis_playbooks(items, metrics)
    evidence_drilldowns = build_evidence_drilldowns(items)
    return {
        "version": 3,
        "document_state": document_state,
        "tz_workflow": tz_workflow,
        "ai_questions": ai_questions,
        "playbooks": playbooks,
        "evidence_drilldowns": evidence_drilldowns,
        "condition_groups": condition_groups,
        "decision_brief": {
            **decision,
            "blockers": [item["label"] for item in items if item.get("is_blocker")][:5],
            "recommended_actions": [item["next_step"] for item in action_plan if item.get("next_step")][:4],
        },
        "action_plan": action_plan,
        "metrics": metrics,
        "major_blocks": sections,
        "sections": sections,
    }
