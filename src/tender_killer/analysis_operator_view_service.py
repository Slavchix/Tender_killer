from __future__ import annotations

from typing import Any

from tender_killer.analysis_action_plan_service import build_analysis_action_plan
from tender_killer.analysis_condition_groups_service import build_condition_groups
from tender_killer.analysis_document_state_service import build_document_state as _document_state
from tender_killer.analysis_evidence_drilldown_service import build_evidence_drilldowns
from tender_killer.analysis_legacy_operator_items_service import build_legacy_operator_items as _legacy_fact_items
from tender_killer.analysis_operator_condition_service import prepare_operator_condition_items
from tender_killer.analysis_operator_context_service import build_context_operator_items
from tender_killer.analysis_operator_item_service import build_operator_item as _operator_item
from tender_killer.analysis_operator_sections_service import MAJOR_SECTION_DEFINITIONS
from tender_killer.analysis_operator_sections_service import MAJOR_SECTION_IDS
from tender_killer.analysis_operator_sections_service import build_major_sections as _major_sections
from tender_killer.analysis_operator_sections_service import operator_item_is_analysis_item as _is_analysis_item
from tender_killer.analysis_operator_summary_service import build_operator_decision_brief
from tender_killer.analysis_operator_summary_service import build_operator_view_metrics
from tender_killer.analysis_playbook_service import build_analysis_playbooks
from tender_killer.analysis_questions_service import build_analysis_ai_questions
from tender_killer.analysis_types import AnalysisFactsContract
from tender_killer.analysis_types import OperatorItem
from tender_killer.analysis_types import OperatorSection
from tender_killer.analysis_types import OperatorView
from tender_killer.analysis_workflow_service import build_analysis_tz_workflow


def build_analysis_operator_view(
    analysis: dict[str, Any] | None,
    documents: list[dict[str, Any]] | None = None,
) -> OperatorView:
    """Build the stable four-block operator-facing Analysis/TZ contract."""
    document_rows = documents or []
    document_state = _document_state(document_rows)

    if not isinstance(analysis, dict):
        sections = _major_sections([], document_rows, pending=True)
        return _view(
            analysis={},
            sections=sections,
            document_state=document_state,
            status="pending",
        )

    facts_contract = _analysis_facts(analysis.get("analysis_facts"))
    facts = _fact_items(facts_contract.get("items")) if facts_contract else _legacy_fact_items(analysis)
    facts.extend(build_context_operator_items(analysis.get("context_pack")))
    facts = prepare_operator_condition_items(facts, analysis, document_rows)
    sections = _major_sections(facts, document_rows)
    return _view(
        analysis=analysis,
        sections=sections,
        document_state=document_state,
        status=str(analysis.get("status") or "needs_review"),
        fact_metrics=facts_contract.get("metrics") if facts_contract else None,
    )


def _view(
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


def _fact_items(value: Any) -> list[OperatorItem]:
    items: list[OperatorItem] = []
    for index, raw_item in enumerate(value if isinstance(value, list) else []):
        if isinstance(raw_item, dict) and raw_item.get("label"):
            items.append(_operator_item(raw_item, index))
    return items


def _analysis_facts(value: Any) -> AnalysisFactsContract | None:
    if isinstance(value, dict) and value.get("version") == 1:
        return value
    return None
