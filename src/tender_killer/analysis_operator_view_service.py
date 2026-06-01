from __future__ import annotations

from typing import Any

from tender_killer.analysis_evidence_service import build_analysis_evidence_items


PRICE_FACTOR_CATEGORIES = {"acceptance", "contract", "delivery", "financial", "payment", "standards"}
BLOCKER_CATEGORIES = {"legal", "national_regime"}


def build_analysis_operator_view(
    analysis: dict[str, Any] | None,
    documents: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the stable operator-facing analysis contract consumed by UI/report layers."""
    document_rows = documents or []
    if not isinstance(analysis, dict):
        return _pending_view(document_rows)

    checklist = _checklist_items(analysis.get("checklist"))
    requirements = _text_list(analysis.get("requirements"))
    risks = _text_list(analysis.get("risks"))
    red_flags = _text_list(analysis.get("red_flags"))
    execution_terms = _execution_terms(analysis.get("execution_terms"))
    evidence_items = _evidence_items(analysis, document_rows)
    blockers = _blocker_items(red_flags, checklist)
    requirement_items = [_item_from_label(label, checklist, "requirement") for label in requirements]
    execution_term_items = [_execution_term_item(term, index) for index, term in enumerate(execution_terms)]
    price_factor_items = [
        _item_from_checklist(item, "price_factor")
        for item in checklist
        if item["category"] in PRICE_FACTOR_CATEGORIES
    ]
    document_items = [_document_item(document, index) for index, document in enumerate(document_rows)]

    return {
        "version": 2,
        "decision_brief": _decision_brief(
            analysis=analysis,
            blockers=blockers,
            requirements=requirement_items,
            risks=risks,
        ),
        "metrics": {
            "requirements": len(requirement_items),
            "risks": len(risks) + len(red_flags),
            "blockers": len(blockers),
            "checklist": len(checklist),
            "execution_terms": len(execution_term_items),
            "evidence": len(evidence_items),
            "documents_ready": sum(1 for document in document_rows if document.get("text_status") == "ok"),
            "documents_total": len(document_rows),
        },
        "sections": [
            _section(
                "blockers",
                "Блокеры",
                blockers,
                "Критичных блокеров в ТЗ не найдено.",
                tone="danger" if blockers else "ok",
            ),
            _section(
                "requirements",
                "Требования",
                requirement_items,
                "Явные требования пока не найдены.",
            ),
            _section(
                "execution_terms",
                "Условия исполнения",
                execution_term_items,
                "Сроки, оплата, гарантия и обеспечение пока не найдены.",
            ),
            _section(
                "price_factors",
                "Влияние на цену",
                price_factor_items,
                "Условий, которые прямо влияют на цену, пока не найдено.",
            ),
            _section(
                "documents",
                "Документы",
                document_items,
                "Документы по закупке пока не загружены.",
            ),
            _section(
                "evidence",
                "Доказательства",
                [_evidence_item(item, index) for index, item in enumerate(evidence_items)],
                "Фрагменты из документов появятся после анализа.",
            ),
        ],
    }


def _pending_view(documents: list[dict[str, Any]]) -> dict[str, Any]:
    document_items = [_document_item(document, index) for index, document in enumerate(documents)]
    return {
        "version": 2,
        "decision_brief": {
            "status": "pending",
            "tone": "pending",
            "title": "Нужен анализ ТЗ",
            "summary": "Сначала извлеките текст документов и запустите анализ.",
            "next_step": "Извлечь текст и запустить анализ ТЗ",
            "confidence": None,
            "primary_section": "documents",
            "reasons": [],
        },
        "metrics": {
            "requirements": 0,
            "risks": 0,
            "blockers": 0,
            "checklist": 0,
            "execution_terms": 0,
            "evidence": 0,
            "documents_ready": sum(1 for document in documents if document.get("text_status") == "ok"),
            "documents_total": len(documents),
        },
        "sections": [
            _section("blockers", "Блокеры", [], "Критичных блокеров в ТЗ не найдено.", tone="pending"),
            _section("requirements", "Требования", [], "Анализ ТЗ еще не запускался.", tone="pending"),
            _section("execution_terms", "Условия исполнения", [], "Анализ ТЗ еще не запускался.", tone="pending"),
            _section("price_factors", "Влияние на цену", [], "Анализ ТЗ еще не запускался.", tone="pending"),
            _section("documents", "Документы", document_items, "Документы по закупке пока не загружены.", tone="pending"),
            _section("evidence", "Доказательства", [], "Фрагменты из документов появятся после анализа.", tone="pending"),
        ],
    }


def _decision_brief(
    *,
    analysis: dict[str, Any],
    blockers: list[dict[str, Any]],
    requirements: list[dict[str, Any]],
    risks: list[str],
) -> dict[str, Any]:
    confidence = _number_or_none(analysis.get("confidence"))
    if blockers:
        return {
            "status": "manual_review",
            "tone": "danger",
            "title": "Нужна ручная проверка",
            "summary": "В ТЗ есть условия, которые могут повлиять на участие, цену или документы.",
            "next_step": "Разобрать блокеры и заложить их в экономику",
            "confidence": confidence,
            "primary_section": "blockers",
            "reasons": [item["label"] for item in blockers[:3]],
        }

    if risks or requirements:
        return {
            "status": "needs_review",
            "tone": "review",
            "title": "Проверить условия",
            "summary": "Критичных блокеров не видно, но требования и риски нужно сверить перед расчетом.",
            "next_step": "Проверить требования и влияние на цену",
            "confidence": confidence,
            "primary_section": "requirements",
            "reasons": [*risks[:2], *[item["label"] for item in requirements[:2]]][:3],
        }

    return {
        "status": "ok",
        "tone": "ok",
        "title": "Критичных рисков не видно",
        "summary": "Анализ не нашел явных блокеров; можно переходить к экономике.",
        "next_step": "Проверить экономику и поставщиков",
        "confidence": confidence,
        "primary_section": "price_factors",
        "reasons": _text_list([analysis.get("summary")])[:1],
    }


def _blocker_items(red_flags: list[str], checklist: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = [_item_from_label(label, checklist, "red_flag", severity="high") for label in red_flags]
    items.extend(
        _item_from_checklist(item, "blocker")
        for item in checklist
        if item["severity"] == "high" or item["category"] in BLOCKER_CATEGORIES
    )
    return _unique_items(items)


def _section(
    section_id: str,
    title: str,
    items: list[dict[str, Any]],
    empty: str,
    *,
    tone: str = "default",
) -> dict[str, Any]:
    return {
        "id": section_id,
        "title": title,
        "count": len(items),
        "tone": tone,
        "empty": empty,
        "items": items,
    }


def _item_from_label(
    label: str,
    checklist: list[dict[str, Any]],
    item_type: str,
    *,
    severity: str | None = None,
) -> dict[str, Any]:
    source = next((item for item in checklist if item["label"] == label), None)
    if source:
        return _item_from_checklist(source, item_type, severity=severity)
    return {
        "id": f"{item_type}:{label}",
        "type": item_type,
        "label": label,
        "category": "general",
        "severity": severity or "medium",
        "description": "",
        "source": "",
        "impact": "",
    }


def _item_from_checklist(
    item: dict[str, Any],
    item_type: str,
    *,
    severity: str | None = None,
) -> dict[str, Any]:
    label = item["label"]
    return {
        "id": f"{item_type}:{label}",
        "type": item_type,
        "label": label,
        "category": item["category"],
        "severity": severity or item["severity"],
        "description": item.get("evidence", ""),
        "source": item.get("document_name") or item.get("source") or "",
        "impact": item.get("impact") or "",
    }


def _document_item(document: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(document.get("text_status") or "pending")
    label = str(document.get("name") or document.get("url") or f"Документ {index + 1}")
    return {
        "id": f"document:{index + 1}",
        "type": "document",
        "label": label,
        "category": str(document.get("document_type") or "document"),
        "severity": "medium" if status == "ok" else "high",
        "status": "ok" if status == "ok" else "attention",
        "description": _document_description(status),
        "source": str(document.get("url") or ""),
        "impact": "",
    }


def _evidence_item(item: dict[str, Any], index: int) -> dict[str, Any]:
    label = str(item.get("label") or f"Фрагмент {index + 1}")
    return {
        "id": str(item.get("id") or f"evidence:{index + 1}"),
        "type": "evidence",
        "label": label,
        "category": str(item.get("category") or "general"),
        "severity": str(item.get("severity") or "medium"),
        "description": str(item.get("fragment") or ""),
        "source": str(item.get("document_name") or ""),
        "impact": str(item.get("impact") or ""),
    }


def _execution_term_item(term: dict[str, Any], index: int) -> dict[str, Any]:
    label = str(term.get("label") or f"Условие {index + 1}")
    value = str(term.get("value") or term.get("evidence") or "")
    return {
        "id": f"execution_term:{term.get('type') or index + 1}",
        "type": "execution_term",
        "label": label,
        "category": str(term.get("category") or "general"),
        "severity": str(term.get("severity") or "medium"),
        "description": value,
        "source": str(term.get("source") or ""),
        "impact": _execution_term_impact(term),
    }


def _execution_term_impact(term: dict[str, Any]) -> str:
    category = str(term.get("category") or "")
    severity = str(term.get("severity") or "")
    if severity == "high":
        return "Заложить в экономику и проверить допустимость участия."
    if category in {"delivery", "financial", "payment"}:
        return "Заложить срок или денежное условие в расчет цены."
    if category == "contract":
        return "Проверить гарантийные обязательства и документы поставщика."
    return ""


def _document_description(status: str) -> str:
    if status == "ok":
        return "Текст извлечен и готов для анализа."
    if status == "pending":
        return "Документ еще нужно скачать или извлечь текст."
    return "Документ требует внимания перед анализом."


def _checklist_items(value: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for raw_item in value if isinstance(value, list) else []:
        if not isinstance(raw_item, dict) or not raw_item.get("label"):
            continue
        items.append(
            {
                **raw_item,
                "label": str(raw_item.get("label") or ""),
                "category": str(raw_item.get("category") or "general"),
                "severity": str(raw_item.get("severity") or "medium"),
                "evidence": str(raw_item.get("evidence") or ""),
            }
        )
    return items


def _evidence_items(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence_items = analysis.get("evidence_items")
    if isinstance(evidence_items, list):
        return [item for item in evidence_items if isinstance(item, dict)]
    return build_analysis_evidence_items(analysis, documents)


def _execution_terms(value: Any) -> list[dict[str, Any]]:
    terms: list[dict[str, Any]] = []
    for raw_term in value if isinstance(value, list) else []:
        if not isinstance(raw_term, dict) or not raw_term.get("label"):
            continue
        terms.append(
            {
                **raw_term,
                "type": str(raw_term.get("type") or ""),
                "label": str(raw_term.get("label") or ""),
                "value": str(raw_term.get("value") or raw_term.get("evidence") or ""),
                "category": str(raw_term.get("category") or "general"),
                "severity": str(raw_term.get("severity") or "medium"),
                "evidence": str(raw_term.get("evidence") or ""),
            }
        )
    return terms


def _text_list(value: Any) -> list[str]:
    values = value if isinstance(value, list) else [value]
    return [str(item).strip() for item in values if item not in (None, "") and str(item).strip()]


def _unique_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in items:
        key = item["label"]
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _number_or_none(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number
