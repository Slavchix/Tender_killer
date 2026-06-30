from __future__ import annotations

import re
from typing import Any

from tender_killer.analysis_interpretation_service import build_fact_interpretation
from tender_killer.analysis_operator_evidence_service import build_operator_confidence_level as _operator_confidence_level
from tender_killer.analysis_operator_evidence_service import build_operator_evidence_quality as _operator_evidence_quality
from tender_killer.analysis_operator_evidence_service import build_operator_source_binding as _operator_source_binding
from tender_killer.analysis_operator_evidence_service import operator_evidence_summary as _operator_evidence_summary
from tender_killer.analysis_operator_evidence_service import operator_evidence_text as _operator_evidence_text
from tender_killer.analysis_operator_evidence_service import operator_source_context as _operator_source_context
from tender_killer.analysis_operator_evidence_service import source_label as _source_label
from tender_killer.analysis_operator_evidence_service import source_page as _source_page
from tender_killer.analysis_operator_item_quality_service import dedupe_operator_items
from tender_killer.analysis_operator_item_quality_service import operator_item_is_visible
from tender_killer.analysis_operator_item_quality_service import operator_item_quality
from tender_killer.analysis_operator_item_taxonomy_service import BLOCKER_CATEGORIES
from tender_killer.analysis_operator_item_taxonomy_service import PRICE_FACTOR_CATEGORIES
from tender_killer.analysis_operator_item_taxonomy_service import canonical_label
from tender_killer.analysis_operator_item_taxonomy_service import canonical_label as _canonical_label
from tender_killer.analysis_operator_item_taxonomy_service import fallback_kind
from tender_killer.analysis_operator_item_taxonomy_service import fallback_kind as _fallback_kind
from tender_killer.analysis_operator_item_taxonomy_service import operator_group as _operator_group
from tender_killer.analysis_operator_item_taxonomy_service import price_impact as _price_impact
from tender_killer.analysis_operator_item_taxonomy_service import priority as _priority
from tender_killer.analysis_operator_item_wording_service import description_is_only_label
from tender_killer.analysis_operator_item_wording_service import operator_action as _operator_action
from tender_killer.analysis_operator_item_wording_service import operator_check as _operator_check
from tender_killer.analysis_operator_item_wording_service import operator_description as _operator_description
from tender_killer.analysis_operator_item_wording_service import operator_display_tier as _operator_display_tier
from tender_killer.analysis_operator_item_wording_service import operator_impact as _operator_impact
from tender_killer.analysis_operator_item_wording_service import operator_summary as _operator_summary
from tender_killer.analysis_operator_item_wording_service import operator_weak_reason as _operator_weak_reason
from tender_killer.analysis_types import OperatorItem


__all__ = [
    "build_operator_item",
    "canonical_label",
    "dedupe_operator_items",
    "description_is_only_label",
    "fallback_kind",
    "operator_item_is_visible",
    "operator_item_quality",
]


def build_operator_item(raw_item: dict[str, Any], index: int) -> OperatorItem:
    kind = str(raw_item.get("kind") or raw_item.get("type") or _fallback_kind(raw_item))
    raw_label = _text(raw_item.get("label")) or f"Факт {index + 1}"
    category = _text(raw_item.get("category")) or "general"
    severity = _text(raw_item.get("severity")) or "medium"
    source = _text(raw_item.get("document_name") or raw_item.get("source"))
    conflict_flags = _text_list(raw_item.get("conflict_flags"))
    expected_missing = bool(raw_item.get("expected_missing"))
    needs_review = bool(raw_item.get("needs_review")) or source == "Документ не привязан" or bool(conflict_flags) or expected_missing
    is_blocker = (
        bool(raw_item.get("is_blocker"))
        or kind in {"blocker", "red_flag"}
        or category in BLOCKER_CATEGORIES
        or (severity == "high" and kind not in {"document", "subject"})
    )
    label = _canonical_label(raw_label, category)
    is_price_factor = bool(raw_item.get("is_price_factor")) or (category in PRICE_FACTOR_CATEGORIES and kind != "subject")
    value = _text(raw_item.get("value")) or _text(raw_item.get("description")) or _text(raw_item.get("fragment"))
    fragment = _text(raw_item.get("fragment") or raw_item.get("evidence"))
    source_page = _source_page(raw_item.get("source_page"))
    source_label = _text(raw_item.get("source_label")) or _source_label(source, source_page)
    impact = _operator_impact(
        category=category,
        severity=severity,
        is_blocker=is_blocker,
        label=label,
        kind=kind,
        raw_impact=_text(raw_item.get("impact")),
    )
    evidence_text = _operator_evidence_text(label=label, value=value, fragment=fragment)
    source_context = _operator_source_context(
        raw_context=_text(raw_item.get("source_context")),
        source=source,
        evidence_text=evidence_text,
        impact=impact,
    )
    evidence_summary = _operator_evidence_summary(
        source_label=source_label,
        evidence_text=evidence_text,
        impact=impact,
    )
    source_binding = _operator_source_binding(
        raw_item=raw_item,
        source=source,
        source_label=source_label,
        source_context=source_context,
        fragment=fragment,
        needs_review=needs_review,
    )
    confidence_level = _operator_confidence_level(
        raw_item,
        source_binding,
        fragment=fragment,
        source_context=source_context,
    )
    evidence_quality = _operator_evidence_quality(
        source_binding=source_binding,
        confidence_level=confidence_level,
        conflict_flags=conflict_flags,
        expected_missing=expected_missing,
    )
    operator_action = _operator_action(
        kind,
        category,
        is_blocker,
        needs_review,
        label=label,
        raw_action=_text(raw_item.get("operator_action")),
    )
    price_impact = _text(raw_item.get("price_impact")) or _price_impact(category, label=label)
    display_tier = "expected_missing" if expected_missing else _operator_display_tier(
        source_binding=source_binding,
        confidence_level=confidence_level,
        is_blocker=is_blocker,
        needs_review=needs_review,
    )
    description = _operator_description(
        label=label,
        raw_description=_text(raw_item.get("description")),
        value=value,
        fragment=fragment,
        category=category,
        kind=kind,
        is_blocker=is_blocker,
    )
    interpretation = build_fact_interpretation(
        {
            **raw_item,
            "label": label,
            "value": value,
            "description": description,
            "category": category,
            "fragment": fragment,
            "source_context": source_context,
            "evidence_summary": evidence_summary,
            "operator_action": operator_action,
            "source_label": source_label,
        }
    )
    if expected_missing:
        interpretation = {
            "found": "",
            "meaning": "Точная формулировка в извлеченном тексте не найдена.",
            "impact": "Условие нужно подтвердить перед расчетом и решением об участии.",
            "action": f"Точная формулировка по условию «{label}» не найдена: найти ее в документах или подтвердить, что ее нет.",
            "confidence": "missing",
        }

    return {
        "id": _text(raw_item.get("id")) or f"{kind}:{_slug(label)}",
        "type": _text(raw_item.get("type")) or kind,
        "kind": kind,
        "label": label,
        "value": value,
        "description": description,
        "operator_summary": _operator_summary(
            label=label,
            description=description,
            impact=impact,
            is_blocker=is_blocker,
            needs_review=needs_review,
            source_binding=source_binding,
            confidence_level=confidence_level,
        ),
        "operator_check": _operator_check(
            label=label,
            action=operator_action,
            needs_review=needs_review,
            conflict_flags=conflict_flags,
            expected_missing=expected_missing,
        ),
        "interpretation": interpretation,
        "conflict_flags": conflict_flags,
        "expected_missing": expected_missing,
        "display_tier": display_tier,
        "weak_reason": _operator_weak_reason(
            display_tier=display_tier,
            source_binding=source_binding,
            confidence_level=confidence_level,
            needs_review=needs_review,
        ),
        "category": category,
        "severity": severity,
        "source": source,
        "document_name": source,
        "source_page": source_page,
        "source_label": source_label,
        "source_context": source_context,
        "evidence_summary": evidence_summary,
        "fragment": fragment,
        "source_binding": source_binding,
        "confidence_level": confidence_level,
        "evidence_quality": evidence_quality,
        "impact": impact,
        "document_role": _text(raw_item.get("document_role")),
        "context_document_role": _text(raw_item.get("context_document_role")),
        "context_document_role_confidence": _text(raw_item.get("context_document_role_confidence")),
        "context_source_priority": _text_list(raw_item.get("context_source_priority")),
        "context_topics": _text_list(raw_item.get("context_topics")),
        "context_mismatch_flags": _text_list(raw_item.get("context_mismatch_flags")),
        "context_text_quality": _text(raw_item.get("context_text_quality")),
        "context_source_authority": _text(raw_item.get("context_source_authority")),
        "context_source_reason": _text(raw_item.get("context_source_reason")),
        "document_stage": _text(raw_item.get("document_stage")),
        "amount_percent": raw_item.get("amount_percent"),
        "amount_type": _text(raw_item.get("amount_type")),
        "days": raw_item.get("days"),
        "deadline_type": _text(raw_item.get("deadline_type")),
        "responsible_party": _text(raw_item.get("responsible_party")),
        "operator_group": _text(raw_item.get("operator_group")) or _operator_group(kind, category, is_blocker, needs_review),
        "operator_action": operator_action,
        "price_impact": price_impact,
        "priority": _int_metric(raw_item.get("priority"), _priority(kind, category, severity, is_blocker, needs_review)),
        "rule_id": _text(raw_item.get("rule_id")),
        "is_blocker": is_blocker,
        "is_price_factor": is_price_factor,
        "needs_review": needs_review,
    }


def _text_list(value: Any) -> list[str]:
    values = value if isinstance(value, list) else [value]
    return [_text(item) for item in values if _text(item)]


def _int_metric(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _slug(value: str) -> str:
    normalized = re.sub(r"\s+", "-", value.strip().casefold())
    normalized = re.sub(r"[^0-9a-zа-яё_-]+", "", normalized)
    return normalized or "item"


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()
