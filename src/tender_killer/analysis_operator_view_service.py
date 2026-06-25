from __future__ import annotations

import re
from typing import Any

from tender_killer.analysis_action_plan_service import build_analysis_action_plan
from tender_killer.analysis_condition_groups_service import (
    EXPECTED_TZ_CHECKS,
    build_condition_groups,
    condition_family_and_measure as _condition_family_and_measure,
    condition_family_and_polarity as _condition_family_and_polarity,
    conflict_evidence_quality as _conflict_evidence_quality,
    expected_families as _expected_families,
    unique_condition_texts as _unique_condition_texts,
)
from tender_killer.analysis_document_state_service import build_document_items as _document_items
from tender_killer.analysis_document_state_service import build_document_state as _document_state
from tender_killer.analysis_evidence_drilldown_service import build_evidence_drilldowns
from tender_killer.analysis_legacy_operator_items_service import build_legacy_operator_items as _legacy_fact_items
from tender_killer.analysis_operator_item_service import build_operator_item as _operator_item
from tender_killer.analysis_operator_item_service import dedupe_operator_items as _dedupe_items
from tender_killer.analysis_operator_item_service import operator_item_is_visible as _is_operator_visible_item
from tender_killer.analysis_playbook_service import build_analysis_playbooks
from tender_killer.analysis_questions_service import build_analysis_ai_questions
from tender_killer.analysis_types import AnalysisFactsContract
from tender_killer.analysis_types import OperatorItem
from tender_killer.analysis_types import OperatorSection
from tender_killer.analysis_types import OperatorView
from tender_killer.analysis_types import OperatorViewMetrics
from tender_killer.analysis_workflow_service import build_analysis_tz_workflow


BLOCKER_CATEGORIES = {"legal", "national_regime"}
DECISION_RISK_CATEGORIES = BLOCKER_CATEGORIES | {"security", "penalty", "restriction"}
DOCUMENT_CATEGORIES = {"documents", "standards", "qualification", "subject"}
FULFILLMENT_CATEGORIES = {"contract", "delivery"}
ACCEPTANCE_PAYMENT_CATEGORIES = {"acceptance", "financial", "payment"}
PRICE_FACTOR_CATEGORIES = ACCEPTANCE_PAYMENT_CATEGORIES | FULFILLMENT_CATEGORIES | {"standards"}

MAJOR_SECTION_DEFINITIONS: tuple[dict[str, str], ...] = (
    {
        "id": "decision_risks",
        "title": "Итог и риски",
        "empty": "Критичных условий и ручных проверок пока не найдено.",
    },
    {
        "id": "product_compliance",
        "title": "Товар и документы",
        "empty": "Требования к товару и документам пока не найдены.",
    },
    {
        "id": "fulfillment_terms",
        "title": "Поставка и исполнение",
        "empty": "Условия поставки и исполнения пока не найдены.",
    },
    {
        "id": "acceptance_payment",
        "title": "Приемка, документы и оплата",
        "empty": "Условия приемки, закрывающих документов и оплаты пока не найдены.",
    },
)
MAJOR_SECTION_IDS = tuple(section["id"] for section in MAJOR_SECTION_DEFINITIONS)


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
    facts.extend(_context_pack_items(analysis.get("context_pack")))
    facts = _add_expected_missing_checks(_annotate_conflicts(facts), analysis, document_rows)
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
    decision = _decision_brief(analysis, sections, status)
    action_plan = build_analysis_action_plan(sections, document_state, condition_groups)
    metrics = _metrics(items, sections, document_state, fact_metrics)
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


def _context_pack_items(context_pack: Any) -> list[OperatorItem]:
    if not isinstance(context_pack, dict) or context_pack.get("version") != 1:
        return []
    items: list[OperatorItem] = []
    for document in context_pack.get("documents") if isinstance(context_pack.get("documents"), list) else []:
        if not isinstance(document, dict):
            continue
        items.extend(_context_document_items(document))
    return items


def _context_document_items(document: dict[str, Any]) -> list[OperatorItem]:
    result: list[OperatorItem] = []
    name = _text(document.get("name"))
    if "subject_mismatch" in _text_list(document.get("mismatch_flags")):
        subject = document.get("tender_identity_match") if isinstance(document.get("tender_identity_match"), dict) else {}
        subject_info = subject.get("subject") if isinstance(subject.get("subject"), dict) else {}
        tender_title = _text(subject_info.get("tender_title"))
        document_subject = _text(subject_info.get("document_subject"))
        fragment = _context_subject_mismatch_fragment(tender_title, document_subject)
        result.append(
            {
                "id": f"context:{_slug(name)}:subject_mismatch",
                "kind": "risk",
                "type": "risk",
                "label": "Документ не совпадает с карточкой закупки",
                "value": fragment,
                "description": (
                    "В документах найден предмет, который отличается от карточки закупки. "
                    "Такой документ нельзя использовать как подтвержденный источник без ручной проверки."
                ),
                "category": "legal",
                "severity": "high",
                "document_name": name,
                "source": name,
                "source_label": name,
                "fragment": fragment,
                "source_context": fragment,
                "operator_action": "Проверить релевантность документа и не использовать его условия без подтверждения.",
                "price_impact": "manual_review",
                "priority": 98,
                "needs_review": True,
                "is_blocker": True,
                "is_price_factor": False,
            }
        )
    if _text(document.get("document_role")) == "unsupported_primary":
        quality = document.get("text_quality") if isinstance(document.get("text_quality"), dict) else {}
        reason = _text(quality.get("text_error")) or _text(quality.get("status")) or "текст не извлечен"
        result.append(
            {
                "id": f"context:{_slug(name)}:unsupported_primary",
                "kind": "requirement",
                "type": "requirement",
                "label": "Главный документ ТЗ не прочитан",
                "value": reason,
                "description": "Один из главных документов закупки не прочитан, поэтому условия нельзя считать полными.",
                "category": "documents",
                "severity": "medium",
                "document_name": name,
                "source": name,
                "source_label": name,
                "fragment": reason,
                "source_context": reason,
                "operator_action": "Открыть документ вручную или повторить извлечение текста перед решением по заявке.",
                "price_impact": "documents",
                "priority": 82,
                "needs_review": True,
                "expected_missing": True,
                "is_blocker": False,
                "is_price_factor": False,
            }
        )
    return result


def _context_subject_mismatch_fragment(tender_title: str, document_subject: str) -> str:
    if tender_title and document_subject:
        return f"В карточке: {tender_title}. В документе: {document_subject}."
    if document_subject:
        return f"В документе найден другой предмет: {document_subject}."
    return "Документ не совпадает с карточкой закупки."


def _major_sections(
    facts: list[OperatorItem],
    documents: list[dict[str, Any]],
    *,
    pending: bool = False,
) -> list[OperatorSection]:
    buckets: dict[str, list[OperatorItem]] = {section_id: [] for section_id in MAJOR_SECTION_IDS}
    for item in facts:
        if not _is_operator_visible_item(item):
            continue
        buckets[_major_section_for_item(item)].append(item)

    buckets["product_compliance"].extend(_document_items(documents))
    sections: list[OperatorSection] = []
    for definition in MAJOR_SECTION_DEFINITIONS:
        section_id = definition["id"]
        items = _sort_items(_dedupe_items(buckets[section_id]))
        sections.append(
            {
                "id": section_id,
                "title": definition["title"],
                "count": _section_count(items),
                "tone": _section_tone(section_id, items, pending=pending),
                "empty": definition["empty"],
                "items": items,
            }
        )
    return sections


def _major_section_for_item(item: OperatorItem) -> str:
    kind = str(item.get("kind") or item.get("type") or "")
    category = str(item.get("category") or "")
    if item.get("is_blocker") or kind in {"blocker", "red_flag", "risk"}:
        return "decision_risks"
    if category in DECISION_RISK_CATEGORIES:
        return "decision_risks"
    if category in ACCEPTANCE_PAYMENT_CATEGORIES:
        return "acceptance_payment"
    if category in FULFILLMENT_CATEGORIES or kind == "execution_term":
        return "fulfillment_terms"
    if kind == "subject" or category in DOCUMENT_CATEGORIES or kind in {"supplier_document", "requirement"}:
        return "product_compliance"
    return "product_compliance"


def _decision_brief(
    analysis: dict[str, Any],
    sections: list[OperatorSection],
    status: str,
) -> dict[str, Any]:
    section_map = {section["id"]: section for section in sections}
    decision_items = section_map["decision_risks"]["items"]
    blockers = [item for item in decision_items if item.get("is_blocker") or item.get("needs_review")]
    confidence = _number_or_none(analysis.get("confidence"))

    if status == "pending":
        return {
            "status": "pending",
            "tone": "pending",
            "title": "Нужен анализ ТЗ",
            "summary": "Сначала извлеките текст документов и запустите анализ.",
            "next_step": "Извлечь текст и запустить анализ ТЗ",
            "confidence": confidence,
            "primary_section": "decision_risks",
            "reasons": [],
        }

    if blockers:
        primary_item = blockers[0]
        return {
            "status": "manual_review",
            "tone": "danger",
            "title": "Нужна ручная проверка",
            "summary": _decision_summary(primary_item, "В ТЗ есть условия, которые могут повлиять на участие, цену или закрывающие документы."),
            "next_step": _text(primary_item.get("operator_action")) or "Разобрать риски до расчета и решения об участии",
            "confidence": confidence,
            "primary_section": "decision_risks",
            "reasons": [_decision_reason(item) for item in blockers[:3]],
        }

    non_empty_sections = [section for section in sections if section["items"]]
    if non_empty_sections:
        reasons = []
        for section in non_empty_sections:
            reasons.extend(_decision_reason(item) for item in section["items"][:2] if item.get("type") != "document")
        primary_item = next(
            (item for section in non_empty_sections for item in section["items"] if item.get("type") != "document"),
            None,
        )
        return {
            "status": "needs_review",
            "tone": "review",
            "title": "Проверить условия ТЗ",
            "summary": _decision_summary(primary_item, "Критичных блокеров не видно, но условия товара, поставки, приемки и оплаты нужно сверить перед расчетом."),
            "next_step": _text(primary_item.get("operator_action")) if primary_item else "Пройти четыре блока анализа и зафиксировать влияние на заявку",
            "confidence": confidence,
            "primary_section": "product_compliance",
            "reasons": reasons[:3],
        }

    return {
        "status": "ok",
        "tone": "ok",
        "title": "Критичных рисков не видно",
        "summary": "Анализ не нашел явных блокеров; можно переходить к следующему этапу проверки.",
        "next_step": "Сверить экономику и поставщиков",
        "confidence": confidence,
        "primary_section": "decision_risks",
        "reasons": _text_list([analysis.get("summary")])[:1],
    }


def _decision_summary(item: dict[str, Any] | None, fallback: str) -> str:
    if not item:
        return fallback
    label = _text(item.get("label"))
    impact = _text(item.get("impact") or item.get("description"))
    if not label or not impact:
        return fallback
    return f"Сначала проверить: {label}. {_compact_text(impact, 180)}"


def _decision_reason(item: dict[str, Any]) -> str:
    label = _text(item.get("label")) or "условие"
    impact = _text(item.get("impact") or item.get("description") or item.get("operator_action"))
    source = _text(item.get("source_label") or item.get("document_name") or item.get("source"))
    reason = label
    if impact:
        reason = f"{reason} — {_compact_text(impact, 150)}"
    if source:
        reason = f"{reason} ({source})"
    return reason


def _metrics(
    items: list[OperatorItem],
    sections: list[OperatorSection],
    document_state: dict[str, Any],
    fact_metrics: Any,
) -> OperatorViewMetrics:
    source_metrics = fact_metrics if isinstance(fact_metrics, dict) else {}
    actual_items = [item for item in items if not item.get("expected_missing")]
    return {
        "major_blocks": len(sections),
        "facts": len(items),
        "requirements": sum(1 for item in items if item.get("kind") in {"requirement", "supplier_document"}),
        "risks": len([item for item in items if item.get("kind") in {"risk", "red_flag", "blocker"} or item.get("is_blocker")]),
        "blockers": sum(1 for item in items if item.get("is_blocker")),
        "actual_blockers": sum(1 for item in actual_items if item.get("is_blocker")),
        "needs_review": sum(1 for item in items if item.get("needs_review")),
        "price_factors": sum(1 for item in items if item.get("is_price_factor")),
        "execution_terms": sum(1 for item in items if item.get("kind") == "execution_term"),
        "conflicts": sum(1 for item in items if item.get("conflict_flags")),
        "actual_conflicts": sum(1 for item in actual_items if item.get("conflict_flags")),
        "expected_missing": sum(1 for item in items if item.get("expected_missing")),
        "documents_ready": document_state["text_ready"],
        "documents_total": document_state["total"],
        "unbound_facts": _int_metric(source_metrics.get("unbound"), sum(1 for item in items if item.get("needs_review"))),
    }


def _fact_items(value: Any) -> list[OperatorItem]:
    items: list[OperatorItem] = []
    for index, raw_item in enumerate(value if isinstance(value, list) else []):
        if isinstance(raw_item, dict) and raw_item.get("label"):
            items.append(_operator_item(raw_item, index))
    return items


def _annotate_conflicts(items: list[OperatorItem]) -> list[OperatorItem]:
    polarity_by_family: dict[str, set[str]] = {}
    measure_by_family: dict[str, set[str]] = {}
    for item in items:
        family, polarity = _condition_family_and_polarity(item)
        if family and polarity:
            polarity_by_family.setdefault(family, set()).add(polarity)
        measure_family, measure = _condition_family_and_measure(item)
        if measure_family and measure:
            measure_by_family.setdefault(measure_family, set()).add(measure)

    polarity_conflicts = {
        family
        for family, polarities in polarity_by_family.items()
        if "positive" in polarities and "negative" in polarities
    }
    measure_conflicts = {family for family, measures in measure_by_family.items() if len(measures) > 1}
    conflicted = polarity_conflicts | measure_conflicts
    if not conflicted:
        return items

    annotated: list[OperatorItem] = []
    for item in items:
        family, polarity = _condition_family_and_polarity(item)
        measure_family, measure = _condition_family_and_measure(item)
        flags: list[str] = []
        if family in polarity_conflicts and polarity:
            flags.append(
                "В документах есть взаимоисключающие формулировки: условие одновременно найдено как применимое и как отсутствующее."
            )
        if measure_family in measure_conflicts and measure:
            flags.append("В документах есть разные числовые значения одного условия; нужно выбрать применимую редакцию.")
        if not flags:
            annotated.append(item)
            continue
        updated = {
            **item,
            "needs_review": True,
            "conflict_flags": flags,
            "evidence_quality": _conflict_evidence_quality(flags),
            "operator_check": f"Разобрать противоречие по условию «{item['label']}»: {'; '.join(flags)}",
        }
        annotated.append(updated)
    return annotated


def _add_expected_missing_checks(
    items: list[OperatorItem],
    analysis: dict[str, Any],
    documents: list[dict[str, Any]],
) -> list[OperatorItem]:
    if not documents or _document_state(documents).get("text_ready", 0) == 0:
        return items
    present: set[str] = set()
    for item in items:
        present.update(_expected_families(item))
    additions: list[OperatorItem] = []
    for spec in EXPECTED_TZ_CHECKS:
        family = spec["family"]
        if family in present:
            continue
        additions.append(
            _operator_item(
                {
                    "id": f"expected:{family}",
                    "kind": "expected_check",
                    "label": spec["label"],
                    "category": spec["category"],
                    "severity": "medium",
                    "source": "Ожидаемая проверка",
                    "operator_action": spec["action"],
                    "expected_missing": True,
                    "needs_review": True,
                    "priority": 30,
                },
                len(items) + len(additions),
            )
        )
    return [*items, *additions]


def _section_tone(section_id: str, items: list[OperatorItem], *, pending: bool) -> str:
    if pending:
        return "pending"
    if section_id == "decision_risks" and items:
        return "danger"
    if any(item.get("needs_review") for item in items):
        return "review"
    if not items:
        return "ok" if section_id == "decision_risks" else "default"
    return "review"


def _analysis_facts(value: Any) -> AnalysisFactsContract | None:
    if isinstance(value, dict) and value.get("version") == 1:
        return value
    return None


def _section_count(items: list[OperatorItem]) -> int:
    return sum(1 for item in items if _is_analysis_item(item))


def _is_analysis_item(item: OperatorItem) -> bool:
    return item.get("type") not in {"document", "document_summary"}


def _sort_items(items: list[OperatorItem]) -> list[OperatorItem]:
    return sorted(items, key=lambda item: (-_int_metric(item.get("priority"), 0), str(item.get("label") or "")))


def _text_list(value: Any) -> list[str]:
    values = value if isinstance(value, list) else [value]
    return [_text(item) for item in values if _text(item)]


def _number_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_metric(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _dedupe_text(value: Any) -> str:
    return re.sub(r"\s+", " ", _text(value)).strip().casefold()


def _compact_text(value: Any, limit: int) -> str:
    text = re.sub(r"\s+", " ", _text(value)).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip(" .,;:") + "…"


def _slug(value: str) -> str:
    normalized = re.sub(r"\s+", "-", value.strip().casefold())
    normalized = re.sub(r"[^0-9a-zа-яё_-]+", "", normalized)
    return normalized or "item"


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()
