from __future__ import annotations

from typing import Any, TypedDict


class SourceBinding(TypedDict, total=False):
    level: str
    label: str
    detail: str
    document_name: str
    source_label: str


class EvidenceQuality(TypedDict, total=False):
    level: str
    label: str
    detail: str


class FactInterpretation(TypedDict, total=False):
    found: str
    meaning: str
    impact: str
    action: str
    confidence: float | None


class AnalysisFact(TypedDict, total=False):
    id: str
    kind: str
    type: str
    label: str
    value: str
    description: str
    category: str
    severity: str
    confidence: str
    rule_id: str
    document_name: str
    source: str
    source_page: int | None
    source_label: str
    source_context: str
    fragment: str
    source_binding: SourceBinding
    confidence_level: EvidenceQuality
    evidence_quality: EvidenceQuality
    evidence_summary: str
    interpretation: FactInterpretation
    operator_summary: str
    operator_check: str
    operator_group: str
    operator_action: str
    display_tier: str
    weak_reason: str
    impact: str
    price_impact: str
    priority: int
    is_blocker: bool
    is_price_factor: bool
    needs_review: bool
    expected_missing: bool
    conflict_flags: list[str]
    semantic_key: str
    condition_family: str
    condition_families: list[str]
    related_labels: list[str]
    related_fact_ids: list[str]
    evidence_sources: list[dict[str, Any]]
    document_role: str
    context_document_role: str
    context_document_role_confidence: str
    context_source_priority: list[str]
    context_topics: list[str]
    context_mismatch_flags: list[str]
    context_text_quality: str
    context_source_authority: str
    context_source_reason: str
    document_stage: str
    amount_percent: Any
    amount_type: str
    days: Any
    deadline_type: str
    responsible_party: str
    feedback_state: str
    feedback_label: str
    feedback_comment: str
    feedback_history: list[dict[str, Any]]


class AnalysisFactsMetrics(TypedDict, total=False):
    facts: int
    blockers: int
    price_factors: int
    unbound: int
    conflicts: int


class AnalysisFactsContract(TypedDict):
    version: int
    items: list[AnalysisFact]
    metrics: AnalysisFactsMetrics


class ConditionGroup(TypedDict, total=False):
    family: str
    label: str
    status: str
    source_status: str
    primary_fact_id: str
    related_fact_ids: list[str]
    sources: list[str]
    summary: str
    resolution: str
    operator_action: str


class ConditionGroupsMetrics(TypedDict, total=False):
    total: int
    confirmed: int
    conflicts: int
    expected_missing: int
    manual_review: int


class ConditionGroupsContract(TypedDict):
    version: int
    items: list[ConditionGroup]
    metrics: ConditionGroupsMetrics


class OperatorSection(TypedDict, total=False):
    id: str
    title: str
    count: int
    tone: str
    empty: str
    items: list[AnalysisFact]


class DecisionBrief(TypedDict, total=False):
    status: str
    tone: str
    title: str
    summary: str
    next_step: str
    confidence: float | None
    primary_section: str
    reasons: list[str]
    blockers: list[str]
    recommended_actions: list[str]


class OperatorViewMetrics(TypedDict, total=False):
    major_blocks: int
    facts: int
    requirements: int
    risks: int
    blockers: int
    actual_blockers: int
    needs_review: int
    price_factors: int
    execution_terms: int
    conflicts: int
    actual_conflicts: int
    expected_missing: int
    documents_ready: int
    documents_total: int
    unbound_facts: int


class OperatorView(TypedDict, total=False):
    version: int
    document_state: dict[str, Any]
    tz_workflow: dict[str, Any]
    ai_questions: dict[str, Any]
    playbooks: dict[str, Any]
    evidence_drilldowns: dict[str, Any]
    condition_groups: ConditionGroupsContract
    decision_brief: DecisionBrief
    action_plan: list[dict[str, Any]]
    metrics: OperatorViewMetrics
    major_blocks: list[OperatorSection]
    sections: list[OperatorSection]


OperatorItem = AnalysisFact
