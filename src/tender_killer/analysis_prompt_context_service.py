from __future__ import annotations

from typing import Any

from tender_killer.analysis_context_pack_service import build_analysis_context_pack
from tender_killer.analysis_evidence_service import build_analysis_evidence_items
from tender_killer.analysis_facts_service import build_analysis_facts
from tender_killer.analysis_questions_service import build_analysis_ai_questions
from tender_killer.analysis_text_index_service import build_analysis_text_index


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
    fact_items = [_prompt_fact(item) for item in _dict_items(analysis_facts.get("items"))[:MAX_PROMPT_FACT_ITEMS]]
    prompt_documents = _prompt_documents(text_index)
    agent_contract = _agent_contract(analysis_payload, analysis_facts)
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
        },
        "task": {
            "goal": (
                "Review tender requirements, risks, economics-impacting conditions, "
                "and missing checks using the supplied document chunks, evidence, and facts."
            ),
            "output_rules": [
                "Do not invent requirements not supported by document chunks or bound evidence.",
                "When changing a fact, keep document_name/source_page/source_context or mark it needs_review.",
                "Preserve existing fact ids where the meaning has not changed.",
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


def _analysis_facts(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> dict[str, Any]:
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


def _prompt_fact(item: dict[str, Any]) -> dict[str, Any]:
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


def _agent_contract(analysis: dict[str, Any], analysis_facts: dict[str, Any]) -> dict[str, Any]:
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
