from __future__ import annotations

from typing import Any

from tender_killer.analysis_context_pack_service import build_analysis_context_pack
from tender_killer.analysis_evidence_service import build_analysis_evidence_items
from tender_killer.analysis_facts_service import build_analysis_facts
from tender_killer.analysis_questions_service import build_analysis_ai_questions
from tender_killer.analysis_text_index_service import build_analysis_text_index
from tender_killer.analysis_types import AnalysisFact
from tender_killer.analysis_types import AnalysisFactsContract


MAX_PROMPT_DOCUMENT_CHUNKS = 36
MAX_PROMPT_EVIDENCE_ITEMS = 40
MAX_PROMPT_FACT_ITEMS = 60


def build_analysis_prompt_context(
    analysis: dict[str, Any] | None,
    documents: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a document-bound context contract for a future analysis agent."""
    analysis_payload = analysis if isinstance(analysis, dict) else {}
    document_rows = documents or []
    text_index = _text_index(analysis_payload, document_rows)
    context_pack = _context_pack(analysis_payload, document_rows)
    evidence_items = _evidence_items(analysis_payload, document_rows)
    analysis_facts = _analysis_facts(analysis_payload, document_rows)
    condition_groups = _condition_groups(analysis_payload)
    condition_diff = _condition_diff(analysis_payload)
    agent_review_plan = _agent_review_plan(condition_groups, condition_diff)
    fact_items = [_prompt_fact(item) for item in _dict_items(analysis_facts.get("items"))[:MAX_PROMPT_FACT_ITEMS]]
    prompt_documents = _prompt_documents(text_index)
    agent_contract = _agent_contract(analysis_payload, analysis_facts, agent_review_plan)
    return {
        "version": 1,
        "mode": "document_aware_agent_prompt",
        "source_contract": {
            "use_only_supplied_context": True,
            "preserve_document_bindings": True,
            "required_binding_fields": ["document_name", "source_page", "source_label", "source_context"],
            "facts_schema": "analysis.analysis_facts.version=1",
            "evidence_schema": "analysis.evidence_items",
            "context_schema": "analysis.context_pack.version=1",
            "condition_schema": "analysis.operator_view.condition_groups.version=1",
            "condition_diff_schema": "analysis.analysis_history.changes.condition_diff.version=2",
            "review_plan_schema": "analysis.agent_review_plan.version=1",
        },
        "task": {
            "goal": (
                "Review tender requirements, risks, economics-impacting conditions, "
                "and missing checks using the supplied document chunks, evidence, facts, "
                "condition groups, and review plan."
            ),
            "output_rules": [
                "Do not invent requirements not supported by document chunks or bound evidence.",
                "When changing a fact, keep document_name/source_page/source_context or mark it needs_review.",
                "Preserve existing fact ids where the meaning has not changed.",
                "Process agent_review_plan items before proposing broad fact changes.",
            ],
        },
        "agent_contract": agent_contract,
        "tender": {
            "summary": _text(analysis_payload.get("summary")),
            "status": _text(analysis_payload.get("status") or analysis_payload.get("recommended_status")),
            "confidence": analysis_payload.get("confidence"),
        },
        "documents": prompt_documents,
        "context_pack": _prompt_context_pack(context_pack),
        "condition_groups": condition_groups,
        "condition_diff": condition_diff,
        "agent_review_plan": agent_review_plan,
        "evidence_items": [_prompt_evidence(item) for item in evidence_items[:MAX_PROMPT_EVIDENCE_ITEMS]],
        "analysis_facts": {
            "version": 1,
            "metrics": analysis_facts.get("metrics") if isinstance(analysis_facts.get("metrics"), dict) else {},
            "items": fact_items,
        },
        "metrics": {
            "documents": len(prompt_documents),
            "document_chunks": sum(len(document.get("chunks") or []) for document in prompt_documents),
            "context_documents": len(_dict_items(context_pack.get("documents"))),
            "evidence_items": min(len(evidence_items), MAX_PROMPT_EVIDENCE_ITEMS),
            "facts": len(fact_items),
            "agent_questions": len(agent_contract.get("questions") or []),
            "condition_groups": len(condition_groups.get("items") or []),
            "condition_diff_items": len(condition_diff.get("items") or []),
            "agent_review_items": len(agent_review_plan.get("items") or []),
        },
    }


def _text_index(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> dict[str, Any]:
    value = analysis.get("text_index") or analysis.get("analysis_text_index")
    if isinstance(value, dict) and value.get("version") == 1:
        return value
    return build_analysis_text_index(documents)


def _context_pack(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> dict[str, Any]:
    value = analysis.get("context_pack") or analysis.get("analysis_context_pack")
    if isinstance(value, dict) and value.get("version") == 1:
        return value
    return build_analysis_context_pack(
        documents,
        tender=analysis if isinstance(analysis, dict) else {},
        items=_dict_items(analysis.get("items")),
    )


def _prompt_context_pack(context_pack: dict[str, Any]) -> dict[str, Any]:
    documents: list[dict[str, Any]] = []
    for document in _dict_items(context_pack.get("documents")):
        documents.append(
            {
                "id": _text(document.get("id")),
                "name": _text(document.get("name")),
                "document_role": _text(document.get("document_role")),
                "document_role_confidence": _text(document.get("document_role_confidence")),
                "source_priority": _text_list(document.get("source_priority")),
                "text_quality": document.get("text_quality") if isinstance(document.get("text_quality"), dict) else {},
                "duplicate_group_id": _text(document.get("duplicate_group_id")),
                "revision_group_id": _text(document.get("revision_group_id")),
                "mismatch_flags": _text_list(document.get("mismatch_flags")),
                "tender_identity_match": (
                    document.get("tender_identity_match")
                    if isinstance(document.get("tender_identity_match"), dict)
                    else {}
                ),
                "section_taxonomy": _prompt_section_taxonomy(document.get("section_taxonomy")),
            }
        )
    return {
        "version": 1,
        "mode": _text(context_pack.get("mode")) or "deterministic_document_context",
        "metrics": context_pack.get("metrics") if isinstance(context_pack.get("metrics"), dict) else {},
        "mismatch_flags": _text_list(context_pack.get("mismatch_flags")),
        "expected_missing_reasons": _text_list(context_pack.get("expected_missing_reasons")),
        "topic_coverage": context_pack.get("topic_coverage") if isinstance(context_pack.get("topic_coverage"), dict) else {},
        "documents": documents,
    }


def _condition_groups(analysis: dict[str, Any]) -> dict[str, Any]:
    operator_view = analysis.get("operator_view")
    if isinstance(operator_view, dict):
        condition_groups = operator_view.get("condition_groups")
        if isinstance(condition_groups, dict):
            return _prompt_condition_groups(condition_groups)
    tz_passport = analysis.get("tz_passport")
    if isinstance(tz_passport, dict):
        condition_groups = tz_passport.get("condition_groups")
        if isinstance(condition_groups, dict):
            return _prompt_condition_groups(condition_groups)
    return {"version": 1, "items": [], "metrics": {}}


def _prompt_condition_groups(condition_groups: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": 1,
        "metrics": condition_groups.get("metrics") if isinstance(condition_groups.get("metrics"), dict) else {},
        "items": [_prompt_condition_group(item) for item in _dict_items(condition_groups.get("items"))],
    }


def _prompt_condition_group(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "family": _text(item.get("family")),
        "label": _text(item.get("label")),
        "status": _text(item.get("status")),
        "source_status": _text(item.get("source_status")),
        "value": _text(item.get("value") or item.get("summary")),
        "sources": _text_list(item.get("sources")),
        "primary_fact_id": _text(item.get("primary_fact_id")),
        "related_fact_ids": _text_list(item.get("related_fact_ids")),
        "operator_action": _text(item.get("operator_action") or item.get("resolution")),
        "manual_review_reason": _text(item.get("manual_review_reason")),
    }


def _condition_diff(analysis: dict[str, Any]) -> dict[str, Any]:
    direct = analysis.get("condition_diff")
    if isinstance(direct, dict):
        return _prompt_condition_diff(direct)
    for history_row in _dict_items(analysis.get("analysis_history")):
        changes = history_row.get("changes")
        if not isinstance(changes, dict):
            continue
        condition_diff = changes.get("condition_diff")
        if isinstance(condition_diff, dict):
            return _prompt_condition_diff(condition_diff)
    return {"version": 2, "metrics": {"added": 0, "removed": 0, "changed": 0}, "items": [], "highlights": []}


def _prompt_condition_diff(condition_diff: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": 2,
        "metrics": condition_diff.get("metrics") if isinstance(condition_diff.get("metrics"), dict) else {},
        "items": [_prompt_condition_change(item) for item in _dict_items(condition_diff.get("items"))],
        "highlights": _prompt_condition_diff_highlights(condition_diff.get("highlights")),
        "action_plan_changed": bool(condition_diff.get("action_plan_changed")),
    }


def _prompt_condition_change(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "family": _text(item.get("family")),
        "label": _text(item.get("label")),
        "change_type": _text(item.get("change_type")),
        "status_before": _text(item.get("status_before")),
        "status_after": _text(item.get("status_after")),
        "value_before": _text(item.get("before") or item.get("value_before")),
        "value_after": _text(item.get("after") or item.get("value_after")),
        "sources_before": _text_list(item.get("sources_before")),
        "sources_after": _text_list(item.get("sources_after")),
        "changed_fields": _text_list(item.get("changed_fields")),
    }


def _prompt_condition_diff_highlights(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        items = [item for item in value.values() if isinstance(item, dict)]
    else:
        items = _dict_items(value)
    return [_prompt_condition_change(item) for item in items]


def _agent_review_plan(condition_groups: dict[str, Any], condition_diff: dict[str, Any]) -> dict[str, Any]:
    diff_by_family = {
        _text(item.get("family")): item
        for item in _dict_items(condition_diff.get("items"))
        if _text(item.get("family"))
    }
    items: list[dict[str, Any]] = []
    for group in _dict_items(condition_groups.get("items")):
        review_item = _agent_review_plan_item(group, diff_by_family.get(_text(group.get("family"))))
        if review_item:
            items.append(review_item)
    items.sort(key=lambda item: (item["priority"], item["family"]))
    return {
        "version": 1,
        "mode": "condition_first_review",
        "items": items,
        "metrics": {
            "total": len(items),
            "conflicts": sum(1 for item in items if item.get("operation") == "mark_conflict"),
            "changed": sum(1 for item in items if item.get("review_reason") == "condition_changed"),
            "expected_missing": sum(1 for item in items if item.get("operation") == "mark_expected_missing"),
            "manual_review": sum(1 for item in items if item.get("operation") == "mark_manual_review"),
        },
    }


def _agent_review_plan_item(group: dict[str, Any], diff: dict[str, Any] | None) -> dict[str, Any] | None:
    family = _text(group.get("family"))
    if not family:
        return None
    status = _text(group.get("status"))
    source_status = _text(group.get("source_status"))
    operation, reason, priority = _review_operation(status, source_status, diff)
    if not operation:
        return None
    diff_payload = _prompt_condition_change(diff) if isinstance(diff, dict) else {}
    return {
        "id": f"condition-review:{family}",
        "family": family,
        "label": _text(group.get("label")),
        "priority": priority,
        "operation": operation,
        "review_reason": reason,
        "instruction": _review_instruction(reason),
        "condition_status": status,
        "source_status": source_status,
        "current_value": _text(group.get("value") or group.get("summary")),
        "sources": _text_list(group.get("sources")),
        "primary_fact_id": _text(group.get("primary_fact_id")),
        "related_fact_ids": _text_list(group.get("related_fact_ids")),
        "operator_action": _text(group.get("operator_action") or group.get("resolution")),
        "changed_fields": _text_list(diff_payload.get("changed_fields")),
        "diff": diff_payload,
    }


def _review_operation(
    status: str,
    source_status: str,
    diff: dict[str, Any] | None,
) -> tuple[str, str, int]:
    if status == "conflict":
        return ("mark_conflict", "condition_conflict", 10)
    if isinstance(diff, dict) and _text(diff.get("change_type")):
        return ("revise", "condition_changed", 20)
    if status == "expected_missing":
        return ("mark_expected_missing", "condition_expected_missing", 30)
    if status == "manual_review" or source_status in {"missing", "weak_source", "unbound", "conflicting_sources"}:
        return ("mark_manual_review", "condition_manual_review", 40)
    return ("", "", 0)


def _review_instruction(reason: str) -> str:
    instructions = {
        "condition_conflict": (
            "Compare the cited sources for the same condition and keep manual review "
            "unless one current authoritative source clearly resolves the conflict."
        ),
        "condition_changed": (
            "Re-check the changed condition against the latest cited source and update "
            "only the condition value/status that changed."
        ),
        "condition_expected_missing": (
            "Look for a cited source in the supplied context; if none exists, keep the "
            "condition as expected_missing instead of inventing a fact."
        ),
        "condition_manual_review": (
            "Keep the condition in manual review until a stronger source confirms or "
            "rejects it."
        ),
    }
    return instructions.get(reason, "Review the condition using only supplied sources.")


def _prompt_section_taxonomy(value: Any) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for section in _dict_items(value):
        sections.append(
            {
                "topic": _text(section.get("topic")),
                "confidence": _text(section.get("confidence")),
                "evidence": _text(section.get("evidence")),
                "markers": _text_list(section.get("markers")),
            }
        )
    return sections


def _evidence_items(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    value = analysis.get("evidence_items")
    if isinstance(value, list) and _items_have_source_binding(value):
        return [dict(item) for item in value if isinstance(item, dict)]
    return build_analysis_evidence_items(analysis, documents)


def _analysis_facts(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> AnalysisFactsContract:
    value = analysis.get("analysis_facts")
    if isinstance(value, dict) and value.get("version") == 1 and isinstance(value.get("items"), list):
        return value
    return build_analysis_facts(analysis, documents)


def _prompt_documents(text_index: dict[str, Any]) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    remaining_chunks = MAX_PROMPT_DOCUMENT_CHUNKS
    for document in _dict_items(text_index.get("documents")):
        chunks = _dict_items(document.get("chunks"))
        selected_chunks = [_prompt_chunk(chunk) for chunk in chunks[:remaining_chunks]]
        remaining_chunks = max(0, remaining_chunks - len(selected_chunks))
        documents.append(
            {
                "name": _text(document.get("name")),
                "document_type": _text(document.get("document_type")),
                "document_role": _text(document.get("document_role")),
                "quality": document.get("quality") if isinstance(document.get("quality"), dict) else {},
                "sections": _dict_items(document.get("sections"))[:20],
                "chunks": selected_chunks,
            }
        )
        if remaining_chunks <= 0:
            break
    return documents


def _prompt_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _text(chunk.get("id")),
        "page": chunk.get("page"),
        "section": _text(chunk.get("section")),
        "kind": _text(chunk.get("kind")),
        "text": _text(chunk.get("text")),
    }


def _prompt_evidence(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _text(item.get("id")),
        "label": _text(item.get("label")),
        "category": _text(item.get("category")),
        "severity": _text(item.get("severity")),
        "document_name": _text(item.get("document_name") or item.get("source")),
        "source_page": item.get("source_page"),
        "source_label": _text(item.get("source_label")),
        "source_context": _text(item.get("source_context")),
        "fragment": _text(item.get("fragment") or item.get("evidence") or item.get("value")),
        "impact": _text(item.get("impact")),
    }


def _prompt_fact(item: AnalysisFact) -> dict[str, Any]:
    binding = _source_binding(item)
    return {
        "id": _text(item.get("id")),
        "kind": _text(item.get("kind")),
        "label": _text(item.get("label")),
        "value": _text(item.get("value")),
        "category": _text(item.get("category")),
        "severity": _text(item.get("severity")),
        "is_blocker": bool(item.get("is_blocker")),
        "is_price_factor": bool(item.get("is_price_factor")),
        "needs_review": bool(item.get("needs_review")),
        "conflict_flags": _text_list(item.get("conflict_flags")),
        "expected_missing": bool(item.get("expected_missing")),
        "impact": _text(item.get("impact")),
        "source_binding": binding,
        "evidence_sources": [_source_binding(source) for source in _dict_items(item.get("evidence_sources"))[:8]],
        "metadata": item.get("metadata") if isinstance(item.get("metadata"), dict) else {},
    }


def _agent_contract(
    analysis: dict[str, Any],
    analysis_facts: AnalysisFactsContract,
    agent_review_plan: dict[str, Any],
) -> dict[str, Any]:
    fact_items = _dict_items(analysis_facts.get("items"))
    questions = _agent_questions(analysis, fact_items)
    return {
        "version": 1,
        "guardrails": {
            "answer_only_from_sources": True,
            "unknown_when_no_source": True,
            "preserve_fact_ids": True,
            "no_bid_submission_or_legal_action": True,
        },
        "output_schema": {
            "type": "object",
            "fields": [
                "decision",
                "answers",
                "facts_patch",
                "condition_review",
                "conflicts",
                "expected_missing",
                "manual_review",
            ],
            "citation_fields": ["document_name", "source_page", "source_label", "source_context", "fragment"],
        },
        "fact_patch_policy": {
            "allowed_operations": ["keep", "revise", "mark_not_supported", "mark_manual_review"],
            "requires_source_for_revise": True,
            "mark_manual_review_when_source_missing": True,
        },
        "condition_patch_policy": {
            "allowed_operations": ["keep", "revise", "mark_conflict", "mark_expected_missing", "mark_manual_review"],
            "requires_condition_source": True,
            "preserve_condition_family": True,
            "use_condition_diff_for_document_updates": True,
        },
        "condition_review_plan": {
            "schema": "analysis.agent_review_plan.version=1",
            "mode": _text(agent_review_plan.get("mode")) or "condition_first_review",
            "review_order": ["condition_conflict", "condition_changed", "condition_expected_missing", "condition_manual_review"],
            "items": len(agent_review_plan.get("items") or []),
        },
        "questions": questions,
        "manual_review_triggers": _manual_review_triggers(fact_items, questions),
    }


def _agent_questions(analysis: dict[str, Any], fact_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    operator_view = analysis.get("operator_view")
    if isinstance(operator_view, dict):
        ai_questions = operator_view.get("ai_questions")
        if isinstance(ai_questions, dict) and isinstance(ai_questions.get("items"), list):
            return [_agent_question(item) for item in _dict_items(ai_questions.get("items"))]
    return [_agent_question(item) for item in _dict_items(build_analysis_ai_questions(fact_items).get("items"))]


def _agent_question(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _text(item.get("id")),
        "question": _text(item.get("question")),
        "answer": _text(item.get("answer")),
        "answer_status": _text(item.get("answer_status")) or "unknown",
        "sources": [_agent_question_source(source) for source in _dict_items(item.get("sources"))[:3]],
    }


def _agent_question_source(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "fact_id": _text(item.get("fact_id")),
        "label": _text(item.get("label")),
        "document_name": _text(item.get("document_name")),
        "source_page": item.get("source_page"),
        "source_label": _text(item.get("source_label")),
        "source_context": _text(item.get("source_context")),
        "fragment": _text(item.get("fragment")),
    }


def _manual_review_triggers(fact_items: list[dict[str, Any]], questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    triggers: list[dict[str, Any]] = []
    for item in fact_items:
        fact_id = _text(item.get("id"))
        label = _text(item.get("label"))
        if item.get("conflict_flags"):
            triggers.append(
                {
                    "type": "conflict",
                    "fact_id": fact_id,
                    "label": label,
                    "reason": "; ".join(_text_list(item.get("conflict_flags"))),
                }
            )
        if item.get("needs_review"):
            triggers.append(
                {
                    "type": "needs_review",
                    "fact_id": fact_id,
                    "label": label,
                    "reason": "Fact is marked for manual operator review.",
                }
            )
        if not _source_binding_has_citation(_source_binding(item)) and _text(item.get("kind")) != "subject":
            triggers.append(
                {
                    "type": "missing_source",
                    "fact_id": fact_id,
                    "label": label,
                    "reason": "Fact has no document/page/context binding.",
                }
            )
    for question in questions:
        if question.get("answer_status") == "not_found":
            triggers.append(
                {
                    "type": "unanswered_question",
                    "question_id": _text(question.get("id")),
                    "label": _text(question.get("question")),
                    "reason": "Agent must answer unknown unless it finds a cited source in supplied context.",
                }
            )
    return _dedupe_triggers(triggers)


def _source_binding_has_citation(binding: dict[str, Any]) -> bool:
    return bool(
        _text(binding.get("document_name"))
        and (
            binding.get("source_page") not in (None, "")
            or _text(binding.get("source_label"))
            or _text(binding.get("source_context"))
            or _text(binding.get("fragment"))
        )
    )


def _source_binding(item: dict[str, Any]) -> dict[str, Any]:
    binding = item.get("source_binding") if isinstance(item.get("source_binding"), dict) else {}
    return {
        "document_name": _text(binding.get("document_name") or item.get("document_name") or item.get("source")),
        "source_page": binding.get("source_page", item.get("source_page")),
        "source_label": _text(binding.get("source_label") or item.get("source_label")),
        "source_context": _text(binding.get("source_context") or item.get("source_context")),
        "fragment": _text(binding.get("fragment") or item.get("fragment") or item.get("evidence") or item.get("value")),
    }


def _items_have_source_binding(items: list[Any]) -> bool:
    return any(
        isinstance(item, dict)
        and bool(
            item.get("source_context")
            or item.get("source_label")
            or item.get("source_page") not in (None, "")
            or item.get("document_name")
        )
        for item in items
    )


def _dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _text_list(value: Any) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple, set)):
        return []
    return [_text(item) for item in value if _text(item)]


def _dedupe_triggers(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        key = (_text(item.get("type")), _text(item.get("fact_id") or item.get("question_id")), _text(item.get("reason")))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _text(value: Any) -> str:
    if value in (None, ""):
        return ""
    return str(value).strip()
