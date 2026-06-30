from __future__ import annotations

import re
from typing import Any

from tender_killer.analysis_fact_builder_service import build_fact as _fact
from tender_killer.analysis_fact_metadata_service import impact as _impact
from tender_killer.analysis_fact_metadata_service import semantic_key as _semantic_key
from tender_killer.analysis_fact_metadata_service import structured_metadata as _structured_metadata
from tender_killer.analysis_fact_source_service import document_source as _document_source
from tender_killer.analysis_text_index_service import document_roles_from_text_index
from tender_killer.analysis_text_index_service import infer_document_role
from tender_killer.analysis_types import AnalysisFact
from tender_killer.analysis_types import AnalysisFactsContract


BLOCKER_CATEGORIES = {"legal", "national_regime"}
PRICE_FACTOR_CATEGORIES = {"acceptance", "contract", "delivery", "financial", "payment", "standards"}
SUPPLIER_DOCUMENT_CATEGORIES = {"documents", "standards"}


def build_analysis_facts(
    analysis: dict[str, Any] | None,
    documents: list[dict[str, Any]] | None = None,
) -> AnalysisFactsContract:
    """Build the compact fact layer used by UI, economics, reports, and future agents."""
    document_rows = documents or []
    if not isinstance(analysis, dict):
        return {"version": 1, "items": [], "metrics": _metrics([])}

    items: list[AnalysisFact] = []
    document_roles = _document_roles(analysis, document_rows)
    document_contexts = _document_contexts(analysis)
    summary = _text(analysis.get("summary"))
    if summary:
        items.append(
            _fact(
                kind="subject",
                label="Предмет",
                value=summary,
                category="subject",
                severity="medium",
                confidence=analysis.get("confidence"),
                rule_id="summary",
            )
        )

    for item in _dict_items(analysis.get("execution_terms")):
        items.append(_execution_term_fact(item, analysis, document_rows, document_roles, document_contexts))

    for item in _dict_items(analysis.get("checklist")):
        items.append(_checklist_fact(item, analysis, document_rows, document_roles, document_contexts))

    items = _dedupe_items(items)
    return {"version": 1, "items": items, "metrics": _metrics(items)}


def _checklist_fact(
    item: dict[str, Any],
    analysis: dict[str, Any],
    documents: list[dict[str, Any]],
    document_roles: dict[str, str],
    document_contexts: dict[str, dict[str, Any]],
) -> AnalysisFact:
    label = _text(item.get("label")) or "Условие"
    category = _text(item.get("category")) or "general"
    severity = _text(item.get("severity")) or "medium"
    fragment = _text(item.get("evidence") or item.get("value"))
    is_blocker = severity == "high" or category in BLOCKER_CATEGORIES
    is_price_factor = category in PRICE_FACTOR_CATEGORIES and not is_blocker
    kind = "blocker" if is_blocker else "supplier_document" if category in SUPPLIER_DOCUMENT_CATEGORIES else "requirement"
    source = _document_source(item, fragment, documents)
    document_name = _text(source.get("document_name"))
    structured = _structured_metadata(
        label=label,
        category=category,
        term_type="checklist",
        text=fragment or label,
        document_name=document_name,
        document_roles=document_roles,
        document_contexts=document_contexts,
    )
    return _fact(
        kind=kind,
        label=label,
        value=fragment or label,
        category=category,
        severity=severity,
        confidence=analysis.get("confidence"),
        rule_id=f"checklist:{label}",
        fragment=fragment,
        document_name=document_name,
        source_page=source.get("source_page"),
        source_label=source.get("source_label", ""),
        source_context=source.get("source_context", ""),
        is_blocker=is_blocker,
        is_price_factor=is_price_factor,
        impact=_impact(category, severity),
        metadata=structured,
        semantic_key=_semantic_key(label, category),
    )


def _execution_term_fact(
    item: dict[str, Any],
    analysis: dict[str, Any],
    documents: list[dict[str, Any]],
    document_roles: dict[str, str],
    document_contexts: dict[str, dict[str, Any]],
) -> AnalysisFact:
    label = _text(item.get("label")) or "Условие исполнения"
    category = _text(item.get("category")) or "general"
    severity = _text(item.get("severity")) or "medium"
    fragment = _text(item.get("evidence") or item.get("value"))
    term_type = _text(item.get("type")) or _slug(label)
    is_blocker = severity == "high" and category in {"financial", "legal", "national_regime"}
    is_price_factor = category in PRICE_FACTOR_CATEGORIES
    source = _document_source(item, fragment, documents)
    document_name = _text(source.get("document_name"))
    value = _text(item.get("value")) or fragment or label
    structured = _structured_metadata(
        label=label,
        category=category,
        term_type=term_type,
        text=" ".join(part for part in (value, fragment) if part),
        document_name=document_name,
        document_roles=document_roles,
        document_contexts=document_contexts,
    )
    return _fact(
        kind="blocker" if is_blocker else "execution_term",
        label=label,
        value=value,
        category=category,
        severity=severity,
        confidence=analysis.get("confidence"),
        rule_id=f"execution_term:{term_type}",
        fragment=fragment,
        document_name=document_name,
        source_page=source.get("source_page"),
        source_label=source.get("source_label", ""),
        source_context=source.get("source_context", ""),
        is_blocker=is_blocker,
        is_price_factor=is_price_factor,
        impact=_impact(category, severity),
        metadata=structured,
        semantic_key=_semantic_key(label, category),
    )


def _document_roles(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> dict[str, str]:
    roles = document_roles_from_text_index(analysis.get("text_index"))
    for document in documents:
        name = _text(document.get("name") or document.get("url"))
        if name:
            roles.setdefault(name, infer_document_role(document))
    return roles


def _document_contexts(analysis: dict[str, Any]) -> dict[str, dict[str, Any]]:
    context_pack = analysis.get("context_pack")
    if not isinstance(context_pack, dict) or context_pack.get("version") != 1:
        return {}
    contexts: dict[str, dict[str, Any]] = {}
    for document in context_pack.get("documents") if isinstance(context_pack.get("documents"), list) else []:
        if not isinstance(document, dict):
            continue
        name = _text(document.get("name"))
        if name:
            contexts[name] = document
    return contexts


def _metrics(items: list[dict[str, Any]]) -> dict[str, int]:
    actionable = [item for item in items if item.get("kind") != "subject"]
    return {
        "total": len(items),
        "blockers": sum(1 for item in actionable if item.get("is_blocker")),
        "price_factors": sum(1 for item in actionable if item.get("is_price_factor")),
        "unbound": sum(1 for item in actionable if item.get("needs_review")),
    }


def _dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: list[tuple[str, str, str]] = []
    semantic_seen: dict[tuple[str, str], dict[str, Any]] = {}
    unique: list[dict[str, Any]] = []
    for item in items:
        if item.get("kind") == "subject":
            unique.append(item)
            continue
        semantic_key = _text(item.get("semantic_key"))
        label_key = _dedupe_text(item.get("label"))
        fragment_key = _dedupe_text(item.get("fragment") or item.get("value"))
        category_key = _text(item.get("category"))
        if semantic_key:
            semantic_seen_key = (semantic_key, category_key)
            existing = semantic_seen.get(semantic_seen_key)
            if existing is not None:
                _merge_fact(existing, item)
                continue
            semantic_seen[semantic_seen_key] = item
        if _seen_equivalent_fact(seen, label_key, fragment_key, category_key):
            continue
        seen.append((label_key, fragment_key, category_key))
        unique.append(item)
    return unique


def _merge_fact(target: dict[str, Any], duplicate: dict[str, Any]) -> None:
    target["related_labels"] = _unique_texts(
        [
            *target.get("related_labels", []),
            duplicate.get("label"),
            *duplicate.get("related_labels", []),
        ]
    )
    target["evidence_sources"] = _unique_sources(
        [
            *target.get("evidence_sources", []),
            *duplicate.get("evidence_sources", []),
        ]
    )
    if not target.get("source") and duplicate.get("source"):
        for key in ("document_name", "source", "source_page", "source_label", "source_context", "fragment"):
            target[key] = duplicate.get(key)
    if duplicate.get("severity") == "high":
        target["severity"] = "high"
    target["is_blocker"] = bool(target.get("is_blocker") or duplicate.get("is_blocker"))
    target["is_price_factor"] = bool(target.get("is_price_factor") or duplicate.get("is_price_factor"))
    target["needs_review"] = bool(target.get("needs_review") or duplicate.get("needs_review"))
    target["priority"] = max(int(target.get("priority") or 0), int(duplicate.get("priority") or 0))


def _unique_texts(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = _text(value)
        key = _dedupe_text(text)
        if not text or key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _unique_sources(values: list[Any]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    result: list[dict[str, Any]] = []
    for value in values:
        if not isinstance(value, dict):
            continue
        source = {
            "document_name": _text(value.get("document_name")),
            "source_label": _text(value.get("source_label")),
            "fragment": _text(value.get("fragment")),
        }
        key = (source["document_name"], source["source_label"], source["fragment"])
        if not source["fragment"] or key in seen:
            continue
        seen.add(key)
        result.append(source)
    return result


def _seen_equivalent_fact(
    seen: list[tuple[str, str, str]],
    label: str,
    fragment: str,
    category: str,
) -> bool:
    for seen_label, seen_fragment, seen_category in seen:
        if not fragment or fragment != seen_fragment or category != seen_category:
            continue
        if label == seen_label or label in seen_label or seen_label in label:
            return True
    return False


def _dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _normalized_text(value: Any) -> str:
    return re.sub(r"\s+", " ", _text(value)).strip().casefold()


def _dedupe_text(value: Any) -> str:
    text = re.sub(r"[^\wа-яА-ЯёЁ]+", " ", _text(value), flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip().casefold()


def _slug(value: str) -> str:
    normalized = re.sub(r"\s+", "-", value.strip().casefold())
    normalized = re.sub(r"[^0-9a-zа-яё_-]+", "", normalized)
    return normalized or "fact"


def _text(value: Any) -> str:
    if value in (None, ""):
        return ""
    return str(value).strip()
