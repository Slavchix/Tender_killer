from __future__ import annotations

from typing import Any

from tender_killer.analysis_evidence_service import build_analysis_evidence_items
from tender_killer.analysis_facts_service import build_analysis_facts
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
    evidence_items = _evidence_items(analysis_payload, document_rows)
    analysis_facts = _analysis_facts(analysis_payload, document_rows)
    fact_items = [_prompt_fact(item) for item in _dict_items(analysis_facts.get("items"))[:MAX_PROMPT_FACT_ITEMS]]
    prompt_documents = _prompt_documents(text_index)
    return {
        "version": 1,
        "mode": "document_aware_agent_prompt",
        "source_contract": {
            "use_only_supplied_context": True,
            "preserve_document_bindings": True,
            "required_binding_fields": ["document_name", "source_page", "source_label", "source_context"],
            "facts_schema": "analysis.analysis_facts.version=1",
            "evidence_schema": "analysis.evidence_items",
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
        "tender": {
            "summary": _text(analysis_payload.get("summary")),
            "status": _text(analysis_payload.get("status") or analysis_payload.get("recommended_status")),
            "confidence": analysis_payload.get("confidence"),
        },
        "documents": prompt_documents,
        "evidence_items": [_prompt_evidence(item) for item in evidence_items[:MAX_PROMPT_EVIDENCE_ITEMS]],
        "analysis_facts": {
            "version": 1,
            "metrics": analysis_facts.get("metrics") if isinstance(analysis_facts.get("metrics"), dict) else {},
            "items": fact_items,
        },
        "metrics": {
            "documents": len(prompt_documents),
            "document_chunks": sum(len(document.get("chunks") or []) for document in prompt_documents),
            "evidence_items": min(len(evidence_items), MAX_PROMPT_EVIDENCE_ITEMS),
            "facts": len(fact_items),
        },
    }


def _text_index(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> dict[str, Any]:
    value = analysis.get("text_index") or analysis.get("analysis_text_index")
    if isinstance(value, dict) and value.get("version") == 1:
        return value
    return build_analysis_text_index(documents)


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
        "impact": _text(item.get("impact")),
        "source_binding": binding,
        "evidence_sources": [_source_binding(source) for source in _dict_items(item.get("evidence_sources"))[:8]],
        "metadata": item.get("metadata") if isinstance(item.get("metadata"), dict) else {},
    }


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


def _text(value: Any) -> str:
    if value in (None, ""):
        return ""
    return str(value).strip()
