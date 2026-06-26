from __future__ import annotations

from typing import Any

from tender_killer.analysis_document_state_service import build_document_state as _document_state
from tender_killer.analysis_legacy_operator_items_service import build_legacy_operator_items as _legacy_fact_items
from tender_killer.analysis_operator_condition_service import prepare_operator_condition_items
from tender_killer.analysis_operator_context_service import build_context_operator_items
from tender_killer.analysis_operator_item_service import build_operator_item as _operator_item
from tender_killer.analysis_operator_sections_service import build_major_sections as _major_sections
from tender_killer.analysis_operator_view_assembler_service import assemble_operator_view
from tender_killer.analysis_types import AnalysisFactsContract
from tender_killer.analysis_types import OperatorItem
from tender_killer.analysis_types import OperatorView


def build_analysis_operator_view(
    analysis: dict[str, Any] | None,
    documents: list[dict[str, Any]] | None = None,
) -> OperatorView:
    """Build the stable four-block operator-facing Analysis/TZ contract."""
    document_rows = documents or []
    document_state = _document_state(document_rows)

    if not isinstance(analysis, dict):
        sections = _major_sections([], document_rows, pending=True)
        return assemble_operator_view(
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
    return assemble_operator_view(
        analysis=analysis,
        sections=sections,
        document_state=document_state,
        status=str(analysis.get("status") or "needs_review"),
        fact_metrics=facts_contract.get("metrics") if facts_contract else None,
    )


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
