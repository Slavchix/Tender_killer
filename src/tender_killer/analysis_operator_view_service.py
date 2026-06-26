from __future__ import annotations

from typing import Any

from tender_killer.analysis_document_state_service import build_document_state as _document_state
from tender_killer.analysis_operator_condition_service import prepare_operator_condition_items
from tender_killer.analysis_operator_context_service import build_context_operator_items
from tender_killer.analysis_operator_fact_source_service import build_operator_fact_source
from tender_killer.analysis_operator_sections_service import build_major_sections as _major_sections
from tender_killer.analysis_operator_view_assembler_service import assemble_operator_view
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

    fact_source = build_operator_fact_source(analysis)
    facts = list(fact_source["items"])
    facts.extend(build_context_operator_items(analysis.get("context_pack")))
    facts = prepare_operator_condition_items(facts, analysis, document_rows)
    sections = _major_sections(facts, document_rows)
    return assemble_operator_view(
        analysis=analysis,
        sections=sections,
        document_state=document_state,
        status=str(analysis.get("status") or "needs_review"),
        fact_metrics=fact_source.get("metrics"),
    )
