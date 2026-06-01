from __future__ import annotations

from typing import Any


DOCUMENT_CATEGORIES = {"documents", "standards"}
BLOCKER_CATEGORIES = {"legal", "national_regime"}
PRICE_FACTOR_CATEGORIES = {"acceptance", "contract", "delivery", "financial", "payment", "standards"}


def build_analysis_tz_passport(
    analysis: dict[str, Any] | None,
    documents: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a compact operator passport from the saved analysis contract."""
    document_rows = documents or []
    if not isinstance(analysis, dict):
        return _pending_passport(document_rows)

    checklist = _checklist_items(analysis.get("checklist"))
    execution_terms = _execution_terms(analysis.get("execution_terms"))
    summary = _text(analysis.get("summary")) or "Предмет закупки не определен."

    subject_items = [
        {
            "id": "subject:summary",
            "type": "summary",
            "label": "Кратко",
            "value": summary,
            "category": "subject",
            "severity": "medium",
            "source": "",
            "impact": "",
        }
    ]
    supplier_documents = [
        _item_from_checklist(item, "supplier_document")
        for item in checklist
        if item["category"] in DOCUMENT_CATEGORIES
    ]
    execution_items = [_item_from_execution_term(item) for item in execution_terms]
    blocker_items = _unique_items(
        [
            *[
                _item_from_checklist(item, "blocker")
                for item in checklist
                if item["severity"] == "high" or item["category"] in BLOCKER_CATEGORIES
            ],
            *[
                _item_from_execution_term(item, item_type="blocker")
                for item in execution_terms
                if item["severity"] == "high"
            ],
        ]
    )
    price_factor_items = _unique_items(
        [
            *[
                _item_from_execution_term(item, item_type="price_factor")
                for item in execution_terms
                if item["category"] in PRICE_FACTOR_CATEGORIES
            ],
            *[
                _item_from_checklist(item, "price_factor")
                for item in checklist
                if item["category"] in PRICE_FACTOR_CATEGORIES
            ],
        ]
    )

    return {
        "version": 1,
        "status": _text(analysis.get("status")) or "needs_review",
        "title": summary,
        "confidence": analysis.get("confidence"),
        "sections": [
            _section("subject", "Предмет", subject_items, "Предмет закупки пока не найден."),
            _section("execution", "Исполнение", execution_items, "Сроки, оплата и гарантия пока не найдены."),
            _section(
                "supplier_documents",
                "Документы и соответствие",
                supplier_documents,
                "Отдельные документы поставщика пока не найдены.",
            ),
            _section(
                "blockers",
                "Блокеры",
                blocker_items,
                "Критичные ограничения пока не найдены.",
                tone="danger" if blocker_items else "ok",
            ),
            _section(
                "price_factors",
                "Влияние на цену",
                price_factor_items,
                "Условия, влияющие на цену, пока не найдены.",
            ),
        ],
    }


def _pending_passport(documents: list[dict[str, Any]]) -> dict[str, Any]:
    ready_count = sum(1 for document in documents if document.get("text_status") == "ok")
    total_count = len(documents)
    return {
        "version": 1,
        "status": "pending",
        "title": "Паспорт ТЗ появится после анализа.",
        "confidence": None,
        "sections": [
            _section(
                "subject",
                "Предмет",
                [],
                f"Сначала подготовьте анализ: текст извлечен у {ready_count} из {total_count} документов.",
                tone="pending",
            ),
            _section("execution", "Исполнение", [], "Анализ ТЗ еще не запускался.", tone="pending"),
            _section(
                "supplier_documents",
                "Документы и соответствие",
                [],
                "Анализ ТЗ еще не запускался.",
                tone="pending",
            ),
            _section("blockers", "Блокеры", [], "Анализ ТЗ еще не запускался.", tone="pending"),
            _section("price_factors", "Влияние на цену", [], "Анализ ТЗ еще не запускался.", tone="pending"),
        ],
    }


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


def _item_from_execution_term(
    item: dict[str, Any],
    item_type: str = "execution_term",
) -> dict[str, Any]:
    label = _text(item.get("label")) or "Условие"
    value = _text(item.get("value")) or _text(item.get("evidence"))
    return {
        "id": f"{item_type}:{item.get('type') or label}",
        "type": item_type,
        "label": label,
        "value": value,
        "category": _text(item.get("category")) or "general",
        "severity": _text(item.get("severity")) or "medium",
        "source": _text(item.get("document_name")) or _text(item.get("source")),
        "impact": _execution_impact(item),
    }


def _item_from_checklist(item: dict[str, Any], item_type: str) -> dict[str, Any]:
    label = _text(item.get("label")) or "Условие"
    return {
        "id": f"{item_type}:{label}",
        "type": item_type,
        "label": label,
        "value": _text(item.get("evidence")),
        "category": _text(item.get("category")) or "general",
        "severity": _text(item.get("severity")) or "medium",
        "source": _text(item.get("document_name")) or _text(item.get("source")),
        "impact": _checklist_impact(item),
    }


def _execution_impact(item: dict[str, Any]) -> str:
    category = _text(item.get("category"))
    severity = _text(item.get("severity"))
    if severity == "high":
        return "Проверить перед участием и заложить в экономику."
    if category in {"delivery", "financial", "payment"}:
        return "Заложить в сроки, резерв или стоп-цену."
    if category == "contract":
        return "Проверить гарантийные обязательства."
    return ""


def _checklist_impact(item: dict[str, Any]) -> str:
    category = _text(item.get("category"))
    severity = _text(item.get("severity"))
    if severity == "high":
        return "Может повлиять на возможность участия."
    if category in DOCUMENT_CATEGORIES:
        return "Проверить наличие у поставщика или подготовить документ."
    if category in PRICE_FACTOR_CATEGORIES:
        return "Учесть в расчете экономики."
    return ""


def _checklist_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [_normalized_item(item) for item in value if isinstance(item, dict)]


def _execution_terms(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [_normalized_item(item) for item in value if isinstance(item, dict)]


def _normalized_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        **item,
        "label": _text(item.get("label")),
        "category": _text(item.get("category")) or "general",
        "severity": _text(item.get("severity")) or "medium",
        "document_name": _text(item.get("document_name")),
        "source": _text(item.get("source")),
    }


def _unique_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, Any]] = []
    for item in items:
        key = (str(item.get("label") or ""), str(item.get("source") or ""))
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()
