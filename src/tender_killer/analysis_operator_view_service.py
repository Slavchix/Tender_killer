from __future__ import annotations

import re
from typing import Any


BLOCKER_CATEGORIES = {"legal", "national_regime"}
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
) -> dict[str, Any]:
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
    sections: list[dict[str, Any]],
    document_state: dict[str, Any],
    status: str,
    fact_metrics: Any = None,
) -> dict[str, Any]:
    items = [item for section in sections for item in section["items"] if _is_analysis_item(item)]
    decision = _decision_brief(analysis, sections, status)
    action_plan = _action_plan(sections, document_state)
    metrics = _metrics(items, sections, document_state, fact_metrics)
    return {
        "version": 3,
        "document_state": document_state,
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


def _major_sections(
    facts: list[dict[str, Any]],
    documents: list[dict[str, Any]],
    *,
    pending: bool = False,
) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {section_id: [] for section_id in MAJOR_SECTION_IDS}
    for item in facts:
        if not _is_operator_visible_item(item):
            continue
        buckets[_major_section_for_item(item)].append(item)

    buckets["product_compliance"].extend(_document_items(documents))
    sections: list[dict[str, Any]] = []
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


def _major_section_for_item(item: dict[str, Any]) -> str:
    kind = str(item.get("kind") or item.get("type") or "")
    category = str(item.get("category") or "")
    if item.get("is_blocker") or kind in {"blocker", "red_flag", "risk"}:
        return "decision_risks"
    if category in BLOCKER_CATEGORIES:
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
    sections: list[dict[str, Any]],
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


def _action_plan(
    sections: list[dict[str, Any]],
    document_state: dict[str, Any],
) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    for section in sections:
        items = [item for item in section["items"] if _is_analysis_item(item)]
        section_id = section["id"]
        focus_item = items[0] if items else None
        status = "ok"
        if section_id == "decision_risks" and items:
            status = "manual_review"
        elif items:
            status = "needs_review"
        elif section_id == "product_compliance" and document_state.get("status") != "ready":
            status = str(document_state.get("status") or "pending")

        plan.append(
            {
                "id": section_id,
                "title": _action_title(section_id),
                "status": status,
                "next_step": _action_next_step(section_id, document_state, focus_item),
                "items": [_action_item_label(item) for item in items[:3]],
            }
        )
    return plan[:4]


def _action_title(section_id: str) -> str:
    return {
        "decision_risks": "Проверить итог и риски",
        "product_compliance": "Сверить товар и документы",
        "fulfillment_terms": "Разобрать поставку и исполнение",
        "acceptance_payment": "Проверить приемку и оплату",
    }[section_id]


def _action_next_step(section_id: str, document_state: dict[str, Any], focus_item: dict[str, Any] | None = None) -> str:
    if focus_item:
        action = _text(focus_item.get("operator_action") or focus_item.get("impact"))
        if action:
            return action
    if section_id == "decision_risks":
        return "Снять блокеры и ручные проверки до расчета."
    if section_id == "product_compliance":
        if document_state.get("status") != "ready":
            return str(document_state.get("next_step") or "Подготовить документы для анализа.")
        return "Проверить характеристики товара и подтверждающие документы."
    if section_id == "fulfillment_terms":
        return "Заложить сроки, логистику и договорные обязанности."
    return "Сверить порядок приемки, закрывающие документы и денежные условия."


def _action_item_label(item: dict[str, Any]) -> str:
    label = _text(item.get("label"))
    source = _text(item.get("source_label") or item.get("document_name") or item.get("source"))
    if label and source:
        return f"{label} · {source}"
    return label or source


def _metrics(
    items: list[dict[str, Any]],
    sections: list[dict[str, Any]],
    document_state: dict[str, Any],
    fact_metrics: Any,
) -> dict[str, Any]:
    source_metrics = fact_metrics if isinstance(fact_metrics, dict) else {}
    return {
        "major_blocks": len(sections),
        "facts": len(items),
        "requirements": sum(1 for item in items if item.get("kind") in {"requirement", "supplier_document"}),
        "risks": len([item for item in items if item.get("kind") in {"risk", "red_flag", "blocker"} or item.get("is_blocker")]),
        "blockers": sum(1 for item in items if item.get("is_blocker")),
        "needs_review": sum(1 for item in items if item.get("needs_review")),
        "price_factors": sum(1 for item in items if item.get("is_price_factor")),
        "execution_terms": sum(1 for item in items if item.get("kind") == "execution_term"),
        "documents_ready": document_state["text_ready"],
        "documents_total": document_state["total"],
        "unbound_facts": _int_metric(source_metrics.get("unbound"), sum(1 for item in items if item.get("needs_review"))),
    }


def _fact_items(value: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index, raw_item in enumerate(value if isinstance(value, list) else []):
        if isinstance(raw_item, dict) and raw_item.get("label"):
            items.append(_operator_item(raw_item, index))
    return _dedupe_items(items)


def _legacy_fact_items(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    checklist = _checklist_items(analysis.get("checklist"))
    checklist_by_label = {item["label"]: item for item in checklist}

    summary = _text(analysis.get("summary"))
    if summary:
        items.append(
            _operator_item(
                {
                    "kind": "subject",
                    "label": "Предмет",
                    "value": summary,
                    "category": "subject",
                    "severity": "medium",
                },
                len(items),
            )
        )

    for item in checklist:
        items.append(_operator_item(item, len(items)))

    for term in _execution_terms(analysis.get("execution_terms")):
        items.append(_operator_item({**term, "kind": "execution_term"}, len(items)))

    known_labels = {item.get("label") for item in items}
    for label in _text_list(analysis.get("red_flags")):
        if label in known_labels:
            continue
        source = checklist_by_label.get(label, {})
        items.append(_legacy_label_item(label, source, "red_flag", is_blocker=True, severity="high"))

    for label in _text_list(analysis.get("risks")):
        if label in known_labels:
            continue
        source = checklist_by_label.get(label, {})
        items.append(_legacy_label_item(label, source, "risk"))

    for label in _text_list(analysis.get("requirements")):
        if label in known_labels:
            continue
        items.append(_legacy_label_item(label, checklist_by_label.get(label, {}), "requirement"))

    return _dedupe_items(items)


def _legacy_label_item(
    label: str,
    source: dict[str, Any],
    kind: str,
    *,
    is_blocker: bool = False,
    severity: str | None = None,
) -> dict[str, Any]:
    return _operator_item(
        {
            **source,
            "kind": kind,
            "label": label,
            "value": source.get("evidence") or source.get("value") or label,
            "category": source.get("category") or ("general" if kind != "red_flag" else "legal"),
            "severity": severity or source.get("severity") or "medium",
            "is_blocker": is_blocker or source.get("is_blocker"),
        },
        0,
    )


def _operator_item(raw_item: dict[str, Any], index: int) -> dict[str, Any]:
    kind = str(raw_item.get("kind") or raw_item.get("type") or _fallback_kind(raw_item))
    raw_label = _text(raw_item.get("label")) or f"Факт {index + 1}"
    category = _text(raw_item.get("category")) or "general"
    severity = _text(raw_item.get("severity")) or "medium"
    source = _text(raw_item.get("document_name") or raw_item.get("source"))
    needs_review = bool(raw_item.get("needs_review")) or source == "Документ не привязан"
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

    return {
        "id": _text(raw_item.get("id")) or f"{kind}:{_slug(label)}",
        "type": _text(raw_item.get("type")) or kind,
        "kind": kind,
        "label": label,
        "value": value,
        "description": _operator_description(
            label=label,
            raw_description=_text(raw_item.get("description")),
            value=value,
            fragment=fragment,
            category=category,
            kind=kind,
            is_blocker=is_blocker,
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
        "confidence_level": _operator_confidence_level(
            raw_item,
            source_binding,
            fragment=fragment,
            source_context=source_context,
        ),
        "impact": impact,
        "document_role": _text(raw_item.get("document_role")),
        "document_stage": _text(raw_item.get("document_stage")),
        "amount_percent": raw_item.get("amount_percent"),
        "amount_type": _text(raw_item.get("amount_type")),
        "days": raw_item.get("days"),
        "deadline_type": _text(raw_item.get("deadline_type")),
        "responsible_party": _text(raw_item.get("responsible_party")),
        "operator_group": _text(raw_item.get("operator_group")) or _operator_group(kind, category, is_blocker, needs_review),
        "operator_action": _operator_action(
            kind,
            category,
            is_blocker,
            needs_review,
            label=label,
            raw_action=_text(raw_item.get("operator_action")),
        ),
        "price_impact": _text(raw_item.get("price_impact")) or _price_impact(category, label=label),
        "priority": _int_metric(raw_item.get("priority"), _priority(kind, category, severity, is_blocker, needs_review)),
        "rule_id": _text(raw_item.get("rule_id")),
        "is_blocker": is_blocker,
        "is_price_factor": is_price_factor,
        "needs_review": needs_review,
    }


def _operator_source_binding(
    *,
    raw_item: dict[str, Any],
    source: str,
    source_label: str,
    source_context: str,
    fragment: str,
    needs_review: bool,
) -> dict[str, str]:
    raw_binding = raw_item.get("source_binding")
    if isinstance(raw_binding, dict) and raw_binding.get("level"):
        return {
            "level": _text(raw_binding.get("level")),
            "label": _text(raw_binding.get("label")),
            "detail": _text(raw_binding.get("detail")),
            "document_name": _text(raw_binding.get("document_name")) or source,
            "source_label": _text(raw_binding.get("source_label")) or source_label,
        }
    if needs_review:
        return {
            "level": "unbound",
            "label": "нужна ручная проверка",
            "detail": "Факт не удалось надежно связать с документом.",
            "document_name": source,
            "source_label": source_label,
        }
    if source and fragment:
        return {
            "level": "explicit",
            "label": "источник подтвержден",
            "detail": "Факт найден в документе и связан с фрагментом текста.",
            "document_name": source,
            "source_label": source_label,
        }
    if source or source_context:
        return {
            "level": "context",
            "label": "источник по контексту",
            "detail": "Факт связан с документом или контекстом, но требует быстрой сверки формулировки.",
            "document_name": source,
            "source_label": source_label,
        }
    return {
        "level": "inferred",
        "label": "вывод без источника",
        "detail": "Факт получен из анализа без точной документальной привязки.",
        "document_name": source,
        "source_label": source_label,
    }


def _operator_confidence_level(
    raw_item: dict[str, Any],
    source_binding: dict[str, str],
    *,
    fragment: str,
    source_context: str,
) -> dict[str, str]:
    raw_level = raw_item.get("confidence_level")
    if isinstance(raw_level, dict) and raw_level.get("level"):
        return {
            "level": _text(raw_level.get("level")),
            "label": _text(raw_level.get("label")),
            "detail": _text(raw_level.get("detail")),
        }
    level = source_binding.get("level")
    if level == "unbound":
        return {
            "level": "low",
            "label": "уверенность низкая",
            "detail": "Нет надежной привязки к документу, нужна ручная проверка.",
        }
    if level == "explicit" and fragment and source_context:
        return {
            "level": "high",
            "label": "уверенность высокая",
            "detail": "Есть документ, фрагмент и контекст источника.",
        }
    if level in {"explicit", "context"}:
        return {
            "level": "medium",
            "label": "уверенность средняя",
            "detail": "Есть источник или контекст, но формулировку стоит сверить вручную.",
        }
    return {
        "level": "low",
        "label": "уверенность низкая",
        "detail": "Вывод сделан без точного источника.",
    }


def _operator_evidence_text(*, label: str, value: str, fragment: str) -> str:
    for candidate in (fragment, value):
        if candidate and not _description_is_only_label(candidate, label):
            return candidate
    return ""


def _operator_source_context(
    *,
    raw_context: str,
    source: str,
    evidence_text: str,
    impact: str,
) -> str:
    if raw_context:
        return raw_context
    if not source or not evidence_text or not impact:
        return ""
    return f"Почему важно: {_compact_text(impact, 190)}"


def _operator_evidence_summary(*, source_label: str, evidence_text: str, impact: str) -> str:
    parts = []
    if source_label:
        parts.append(source_label)
    if evidence_text:
        parts.append(_compact_text(evidence_text, 180))
    if impact:
        parts.append(f"вывод: {_compact_text(impact, 180)}")
    return " · ".join(parts)


def _document_items(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not documents:
        return []
    document_state = _document_state(documents)
    document_labels = [
        _text(document.get("name") or document.get("url")) or f"Документ {index + 1}"
        for index, document in enumerate(documents)
    ]
    return [
        {
            "id": "documents:summary",
            "type": "document_summary",
            "kind": "document_summary",
            "label": "Документы для анализа",
            "value": "",
            "description": _document_summary_description(document_state),
            "category": "documents",
            "severity": "medium" if document_state["attention"] == 0 else "high",
            "status": document_state["status"],
            "source": "",
            "document_name": "",
            "source_page": None,
            "source_label": "",
            "source_context": "",
            "fragment": "",
            "impact": "",
            "operator_group": "document",
            "operator_action": document_state["next_step"],
            "price_impact": "none",
            "priority": 5,
            "rule_id": "",
            "is_blocker": False,
            "is_price_factor": False,
            "needs_review": document_state["status"] != "ready",
            "documents": document_labels[:8],
        }
    ]


def _document_state(documents: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(documents)
    downloaded = sum(1 for document in documents if document.get("local_path"))
    text_ready = sum(1 for document in documents if document.get("text_status") == "ok")
    missing_download = sum(1 for document in documents if not document.get("local_path"))
    missing_text = total - text_ready
    if total == 0:
        status = "no_documents"
        summary = "Документы по закупке пока не найдены."
        next_step = "Обновить карточку закупки или открыть источник."
    elif text_ready == total:
        status = "ready"
        summary = "Текст извлечен по всем документам."
        next_step = "Переходить к проверке четырех блоков анализа."
    elif downloaded == 0:
        status = "needs_download"
        summary = "Документы нужно скачать перед анализом."
        next_step = "Скачать документы и извлечь текст."
    else:
        status = "needs_text"
        summary = "Текст извлечен не по всем документам."
        next_step = "Извлечь текст и проверить проблемные файлы."
    return {
        "status": status,
        "summary": summary,
        "next_step": next_step,
        "total": total,
        "downloaded": downloaded,
        "text_ready": text_ready,
        "attention": missing_text,
        "missing_download": missing_download,
        "missing_text": missing_text,
    }


def _document_description(status: str) -> str:
    if status == "ok":
        return "Текст извлечен и готов для анализа."
    if status == "pending":
        return "Документ еще нужно скачать или извлечь текст."
    return "Документ требует внимания перед анализом."


def _document_summary_description(document_state: dict[str, Any]) -> str:
    total = document_state["total"]
    suffix = "файл" if total == 1 else "файла" if total in {2, 3, 4} else "файлов"
    return (
        f"{total} {suffix}: {document_state['downloaded']} скачано, "
        f"{document_state['text_ready']} с извлеченным текстом, {document_state['attention']} требуют внимания."
    )


def _section_tone(section_id: str, items: list[dict[str, Any]], *, pending: bool) -> str:
    if pending:
        return "pending"
    if section_id == "decision_risks" and items:
        return "danger"
    if any(item.get("needs_review") for item in items):
        return "review"
    if not items:
        return "ok" if section_id == "decision_risks" else "default"
    return "review"


def _fallback_kind(item: dict[str, Any]) -> str:
    category = _text(item.get("category"))
    severity = _text(item.get("severity"))
    if severity == "high" or category in BLOCKER_CATEGORIES:
        return "blocker"
    if category in DOCUMENT_CATEGORIES:
        return "supplier_document"
    if category in FULFILLMENT_CATEGORIES | ACCEPTANCE_PAYMENT_CATEGORIES:
        return "execution_term"
    return "requirement"


def _operator_impact(
    *,
    category: str,
    severity: str,
    is_blocker: bool,
    label: str,
    kind: str,
    raw_impact: str,
) -> str:
    fallback = _fallback_impact(category, severity, is_blocker, label=label, kind=kind)
    if fallback and (not raw_impact or _impact_is_generic(raw_impact)):
        return fallback
    return raw_impact or fallback


def _fallback_impact(
    category: str,
    severity: str,
    is_blocker: bool,
    *,
    label: str = "",
    kind: str = "",
) -> str:
    family = _semantic_family(label, category)
    if family == "national_regime":
        return "Проверить допуск товара и заявки: страна происхождения, реестр и подтверждения могут привести к отклонению."
    if family == "license_sro":
        return "Проверить право участника выполнять работы: без лицензии или СРО заявку могут отклонить."
    if family == "contract_security":
        return "Учесть нагрузку на оборотку: обеспечение или гарантия замораживает деньги и влияет на решение об участии."
    if family == "short_delivery":
        return "Проверить наличие товара и срочную логистику: короткий срок может увеличить расходы или стать стоп-фактором."
    if family == "closing_documents":
        return "Подготовить закрывающие документы для приемки: ошибки в УПД, актах или накладных задержат оплату."
    if family == "montage_launch":
        return "Заложить работы, выезд специалистов, акты и возможные дополнительные расходы на монтаж или пусконаладку."
    if family == "certificate_documents":
        return "Проверить документы соответствия у поставщика: без сертификатов или деклараций возможна проблема с приемкой."
    if family == "warranty":
        return "Заложить резерв на гарантийные обязательства, замену брака и возможные выезды после поставки."
    if is_blocker or severity == "high":
        return "Проверить допустимость участия до расчета."
    if category in DOCUMENT_CATEGORIES:
        return "Проверить наличие подтверждающих документов."
    if category in FULFILLMENT_CATEGORIES:
        return "Учесть в сроках, логистике и договорной подготовке."
    if category in ACCEPTANCE_PAYMENT_CATEGORIES:
        return "Учесть в закрывающих документах и денежном цикле."
    return ""


def _impact_is_generic(impact: str) -> bool:
    text = _dedupe_text(impact)
    generic_markers = (
        "может повлиять на возможность участия",
        "заложить в решение или экономику",
        "учесть в сроках",
        "проверить наличие документа",
        "проверить перед принятием решения",
        "проверить допустимость участия до расчета",
    )
    return any(marker in text for marker in generic_markers)


def _operator_group(kind: str, category: str, is_blocker: bool, needs_review: bool) -> str:
    if needs_review:
        return "manual_review"
    if is_blocker:
        return "blocker"
    if category in ACCEPTANCE_PAYMENT_CATEGORIES:
        return "acceptance_payment"
    if category in FULFILLMENT_CATEGORIES or kind == "execution_term":
        return "execution"
    if kind in {"subject", "supplier_document", "requirement"}:
        return "prepare"
    return "review"


def _operator_action(
    kind: str,
    category: str,
    is_blocker: bool,
    needs_review: bool,
    *,
    label: str = "",
    raw_action: str = "",
) -> str:
    family = _semantic_family(label, category)
    if family == "national_regime":
        return "Проверить страну происхождения, применимый нацрежим и подтверждающие документы до участия."
    if family == "license_sro":
        return "Проверить, действительно ли нужна лицензия или СРО, и есть ли подтверждение у участника."
    if family == "contract_security":
        return "Учесть обеспечение в деньгах или гарантии и проверить возможность участия."
    if family == "short_delivery":
        return "Проверить наличие товара, реалистичность срока и заложить срочную логистику до расчета цены."
    if family == "closing_documents":
        return "Подготовить УПД, накладные или акты и проверить, без каких документов заказчик не примет и не оплатит поставку."
    if family == "montage_launch":
        return "Проверить, входят ли монтаж, пусконаладка или обучение в поставку, и заложить выезд специалистов."
    if family == "certificate_documents":
        return "Запросить у поставщика сертификаты, декларации или паспорта качества до подачи заявки."
    if family == "warranty":
        return "Проверить гарантийный срок, правила замены брака и резерв на гарантийные обязательства."
    if raw_action and raw_action not in {"Проверить до участия.", "Проверить допустимость участия до расчета."}:
        return raw_action
    if needs_review:
        return "Проверить источник факта вручную."
    if is_blocker:
        return "Проверить допустимость участия до расчета."
    if kind == "subject":
        return "Сверить предмет закупки."
    if category in DOCUMENT_CATEGORIES:
        return "Подготовить или проверить подтверждающие документы."
    if category == "delivery":
        return "Проверить срок, место и логистику поставки."
    if category == "contract":
        return "Проверить договорные обязанности и гарантию."
    if category == "acceptance":
        return "Проверить порядок приемки и закрывающие документы."
    if category in {"financial", "payment"}:
        return "Проверить оплату, аванс, обеспечение и денежный цикл."
    return "Проверить условие перед решением."


def _price_impact(category: str, *, label: str = "") -> str:
    family = _semantic_family(label, category)
    if family in {"short_delivery", "montage_launch"}:
        return "logistics"
    if family in {"closing_documents", "contract_security"}:
        return "working_capital"
    if family == "certificate_documents":
        return "documents"
    if family == "warranty":
        return "reserve"
    if category == "delivery":
        return "logistics"
    if category in {"financial", "payment", "acceptance"}:
        return "working_capital"
    if category == "documents":
        return "documents"
    if category == "contract":
        return "reserve"
    if category in {"legal", "national_regime", "standards"}:
        return "compliance"
    return "none"


def _priority(kind: str, category: str, severity: str, is_blocker: bool, needs_review: bool) -> int:
    if needs_review:
        return 95
    if is_blocker:
        return 90 if severity == "high" else 80
    if category in ACCEPTANCE_PAYMENT_CATEGORIES:
        return 65
    if category in FULFILLMENT_CATEGORIES:
        return 60
    if kind in {"supplier_document", "requirement"}:
        return 50
    if kind == "subject":
        return 20
    return 40


def _analysis_facts(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict) and value.get("version") == 1:
        return value
    return None


def _checklist_items(value: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for raw_item in value if isinstance(value, list) else []:
        if not isinstance(raw_item, dict) or not raw_item.get("label"):
            continue
        items.append(
            {
                **raw_item,
                "kind": raw_item.get("kind") or _fallback_kind(raw_item),
                "label": _text(raw_item.get("label")),
                "value": _text(raw_item.get("value") or raw_item.get("evidence")),
                "category": _text(raw_item.get("category")) or "general",
                "severity": _text(raw_item.get("severity")) or "medium",
                "fragment": _text(raw_item.get("fragment") or raw_item.get("evidence")),
            }
        )
    return items


def _execution_terms(value: Any) -> list[dict[str, Any]]:
    terms: list[dict[str, Any]] = []
    for raw_term in value if isinstance(value, list) else []:
        if not isinstance(raw_term, dict) or not raw_term.get("label"):
            continue
        terms.append(
            {
                **raw_term,
                "kind": "execution_term",
                "type": _text(raw_term.get("type") or "execution_term"),
                "label": _text(raw_term.get("label")),
                "value": _text(raw_term.get("value") or raw_term.get("evidence")),
                "category": _text(raw_term.get("category")) or "general",
                "severity": _text(raw_term.get("severity")) or "medium",
                "fragment": _text(raw_term.get("fragment") or raw_term.get("evidence")),
            }
        )
    return terms


def _dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    ordered_keys: list[tuple[str, str, str]] = []
    for item in items:
        if not _is_operator_visible_item(item):
            continue
        key = _dedupe_key(item)
        current = best_by_key.get(key)
        if current is None:
            best_by_key[key] = item
            ordered_keys.append(key)
            continue
        if _operator_item_quality(item) > _operator_item_quality(current):
            best_by_key[key] = item
    return [best_by_key[key] for key in ordered_keys]


def _dedupe_key(item: dict[str, Any]) -> tuple[str, str, str]:
    kind = _text(item.get("kind") or item.get("type"))
    if kind in {"document", "document_summary", "subject"}:
        return (kind, _dedupe_text(item.get("id") or item.get("label")), "")
    family = _semantic_family(_text(item.get("label")), _text(item.get("category")))
    if family:
        return ("semantic", family, "")
    return (
        kind,
        _dedupe_text(item.get("label")),
        "" if _operator_item_quality(item) <= 0 else _dedupe_text(item.get("fragment") or item.get("value")),
    )


def _is_operator_visible_item(item: dict[str, Any]) -> bool:
    kind = _text(item.get("kind") or item.get("type"))
    if kind == "document_summary":
        return True
    if kind == "document":
        return False
    if kind == "subject":
        return bool(_specific_text(item, allow_description=True))
    return _operator_item_quality(item) > 0


def _operator_item_quality(item: dict[str, Any]) -> int:
    label = _text(item.get("label"))
    score = 0
    source_context = _text(item.get("source_context"))
    fragment = _text(item.get("fragment"))
    specific = _specific_text(item)
    if source_context:
        score += 90
    if fragment and _item_text_is_relevant(item, fragment):
        score += 80
    if _has_real_source(item) and (not fragment or _item_text_is_relevant(item, fragment) or source_context):
        score += 45
    if specific and _item_text_is_relevant(item, specific):
        score += 35
    if score and _text(item.get("rule_id")):
        score += 5
    if not score and label:
        return 0
    return score + min(_int_metric(item.get("priority"), 0), 100)


def _specific_text(item: dict[str, Any], *, allow_description: bool = False) -> str:
    label = _text(item.get("label"))
    fields = ["value"]
    if allow_description:
        fields.append("description")
    for field in fields:
        text = _text(item.get(field))
        if text and not _description_is_only_label(text, label):
            return text
    return ""


def _has_real_source(item: dict[str, Any]) -> bool:
    source = _text(item.get("source_label") or item.get("source") or item.get("document_name"))
    if not source:
        return False
    return _dedupe_text(source) != _dedupe_text("Документ не привязан")


def _item_text_is_relevant(item: dict[str, Any], value: str) -> bool:
    text = _dedupe_text(value)
    if not text:
        return False
    label = _text(item.get("label"))
    category = _text(item.get("category"))
    family = _semantic_family(label, category)
    if family == "national_regime":
        return any(marker in text for marker in ("национальн", "страна происхожд", "страну происхожд", "страны происхожд", "1875"))
    if family == "license_sro":
        return any(marker in text for marker in ("сро", "лиценз", "саморегулируем"))
    if family == "contract_security":
        return any(marker in text for marker in ("обеспечение исполнения", "независим", "гарант"))
    tokens = _meaningful_label_tokens(label)
    if not tokens:
        return True
    if "/" in label or len(tokens) == 1:
        return any(token in text for token in tokens)
    return all(token in text for token in tokens)


def _meaningful_label_tokens(label: str) -> list[str]:
    tokens = _dedupe_text(label).split()
    return [token for token in tokens if len(token) >= 4]


def _canonical_label(label: str, category: str) -> str:
    family = _semantic_family(label, category)
    if family == "national_regime":
        return "национальный режим/страна происхождения"
    if family == "license_sro":
        return "лицензия/СРО"
    if family == "contract_security":
        return "обеспечение исполнения контракта"
    return label


def _operator_description(
    *,
    label: str,
    raw_description: str,
    value: str,
    fragment: str,
    category: str,
    kind: str,
    is_blocker: bool,
) -> str:
    family = _semantic_family(label, category)
    if family == "national_regime":
        return (
            "Это проверка применимости национального режима: страна происхождения, реестровые записи "
            "и подтверждающие документы могут влиять на допуск заявки."
        )
    if family == "license_sro":
        return (
            "Это квалификационное ограничение: если лицензия или членство в СРО действительно требуется, "
            "участник без подтверждения может получить отклонение заявки."
        )
    if family == "contract_security":
        return (
            "Это денежная нагрузка на исполнение: обеспечение или независимая гарантия влияет на оборотку, "
            "резерв и решение об участии."
        )
    if family == "short_delivery":
        return (
            "Это риск физического исполнения: короткий срок поставки требует наличия товара на складе, "
            "быстрой логистики и подтверждения, что срок реально выполнить без срыва контракта."
        )
    if family == "closing_documents":
        return (
            "Это условие приемки и оплаты: УПД, накладные, счета-фактуры или акты должны совпасть с требованиями "
            "заказчика, иначе поставку могут не принять или задержать оплату."
        )
    if family == "montage_launch":
        return (
            "Это не просто поставка товара: монтаж, пусконаладка, ввод в эксплуатацию или обучение требуют "
            "специалистов, допуска на объект, актов и дополнительного времени."
        )
    if family == "certificate_documents":
        return (
            "Это подтверждение соответствия товара: сертификаты, декларации, паспорта качества или другие документы "
            "нужно получить у поставщика до заявки или до приемки."
        )
    if family == "warranty":
        return (
            "Это обязательства после поставки: гарантийный срок, замена брака и порядок ремонта могут потребовать "
            "резерва, документов и готовности обслуживать товар после приемки."
        )
    if category == "documents":
        return "Нужно понять, какой подтверждающий документ требуется и кто сможет его предоставить к заявке или поставке."
    if category == "standards":
        return "Это требование к характеристикам или соответствию товара; его нужно сверить с фактическим предложением."
    if category == "delivery":
        return "Это влияет на логистику, сроки поставки и возможные расходы исполнения."
    if category == "acceptance":
        return "Это влияет на приемку, закрывающие документы и момент, когда поставку признают исполненной."
    if category in {"financial", "payment"}:
        return "Это влияет на денежный цикл: оплату, аванс, удержания, обеспечение или резервы."
    if raw_description and not _description_is_only_label(raw_description, label):
        return raw_description
    if value and not _description_is_only_label(value, label) and value != fragment:
        return value
    if is_blocker:
        return "Условие может повлиять на допуск к участию, его нужно проверить до расчета."
    if kind == "subject":
        return value or "Краткое описание предмета закупки."
    return "Условие нужно сверить с документами закупки и учесть перед решением."


def _description_is_only_label(description: str, label: str) -> bool:
    return _dedupe_text(description) == _dedupe_text(label)


def _semantic_family(label: str, category: str) -> str:
    text = _dedupe_text(label)
    if category == "national_regime" or any(marker in text for marker in ("национальн", "страна происхожд", "страны происхожд", "1875")):
        return "national_regime"
    if category == "legal" and any(marker in text for marker in ("сро", "лиценз", "саморегулируем")):
        return "license_sro"
    if category == "financial" and any(marker in text for marker in ("обеспечение исполнения", "независим", "гарант")):
        return "contract_security"
    if any(marker in text for marker in ("монтаж", "пусконалад", "ввод в эксплуатац", "обучение", "инструктаж")):
        return "montage_launch"
    if category in {"documents", "standards"} and any(
        marker in text
        for marker in (
            "сертифик",
            "деклараци",
            "паспорт качества",
            "паспорт издел",
            "сгр",
            "регистрационное удостоверение",
            "удостоверение качества",
        )
    ):
        return "certificate_documents"
    if category in ACCEPTANCE_PAYMENT_CATEGORIES | {"documents"} and any(
        marker in text
        for marker in (
            "упд",
            "закрывающ",
            "накладн",
            "счет-фактур",
            "счёт-фактур",
            "акт прием",
            "акт приём",
            "акт выполн",
            "документы о приемке",
            "документы о приёмке",
        )
    ):
        return "closing_documents"
    if category == "delivery" and any(
        marker in text
        for marker in (
            "короткий срок",
            "срок поставки",
            "срок исполн",
            "поставка в течение",
            "в течение 1",
            "в течение 2",
            "в течение 3",
            "1 день",
            "2 дня",
            "3 дня",
        )
    ):
        return "short_delivery"
    if category in {"contract", "documents"} and any(marker in text for marker in ("гарантийн", "гарантия", "замена брака", "ремонт")):
        return "warranty"
    return ""


def _section_count(items: list[dict[str, Any]]) -> int:
    return sum(1 for item in items if _is_analysis_item(item))


def _is_analysis_item(item: dict[str, Any]) -> bool:
    return item.get("type") not in {"document", "document_summary"}


def _sort_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(items, key=lambda item: (-_int_metric(item.get("priority"), 0), str(item.get("label") or "")))


def _text_list(value: Any) -> list[str]:
    values = value if isinstance(value, list) else [value]
    return [_text(item) for item in values if _text(item)]


def _source_label(source: str, page: int | None) -> str:
    if not source:
        return ""
    if page is None:
        return source
    return f"{source} · стр. {page}"


def _source_page(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        page = int(value)
    except (TypeError, ValueError):
        return None
    return page if page > 0 else None


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
