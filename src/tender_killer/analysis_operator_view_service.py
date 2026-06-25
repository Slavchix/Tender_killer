from __future__ import annotations

import re
from typing import Any

from tender_killer.analysis_action_plan_service import build_analysis_action_plan
from tender_killer.analysis_condition_groups_service import build_condition_groups
from tender_killer.analysis_document_state_service import build_document_state as _document_state
from tender_killer.analysis_evidence_drilldown_service import build_evidence_drilldowns
from tender_killer.analysis_legacy_operator_items_service import build_legacy_operator_items as _legacy_fact_items
from tender_killer.analysis_operator_condition_service import prepare_operator_condition_items
from tender_killer.analysis_operator_item_service import build_operator_item as _operator_item
from tender_killer.analysis_operator_sections_service import MAJOR_SECTION_DEFINITIONS
from tender_killer.analysis_operator_sections_service import MAJOR_SECTION_IDS
from tender_killer.analysis_operator_sections_service import build_major_sections as _major_sections
from tender_killer.analysis_operator_sections_service import operator_item_is_analysis_item as _is_analysis_item
from tender_killer.analysis_playbook_service import build_analysis_playbooks
from tender_killer.analysis_questions_service import build_analysis_ai_questions
from tender_killer.analysis_types import AnalysisFactsContract
from tender_killer.analysis_types import OperatorItem
from tender_killer.analysis_types import OperatorSection
from tender_killer.analysis_types import OperatorView
from tender_killer.analysis_types import OperatorViewMetrics
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
    facts.extend(_context_pack_items(analysis.get("context_pack")))
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


def _analysis_facts(value: Any) -> AnalysisFactsContract | None:
    if isinstance(value, dict) and value.get("version") == 1:
        return value
    return None


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
