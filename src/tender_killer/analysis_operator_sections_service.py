from __future__ import annotations

from typing import Any

from tender_killer.analysis_document_state_service import build_document_items as _document_items
from tender_killer.analysis_operator_item_service import dedupe_operator_items as _dedupe_items
from tender_killer.analysis_operator_item_service import operator_item_is_visible as _is_operator_visible_item
from tender_killer.analysis_types import OperatorItem
from tender_killer.analysis_types import OperatorSection


BLOCKER_CATEGORIES = {"legal", "national_regime"}
DECISION_RISK_CATEGORIES = BLOCKER_CATEGORIES | {"security", "penalty", "restriction"}
DOCUMENT_CATEGORIES = {"documents", "standards", "qualification", "subject"}
FULFILLMENT_CATEGORIES = {"contract", "delivery"}
ACCEPTANCE_PAYMENT_CATEGORIES = {"acceptance", "financial", "payment"}

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


def build_major_sections(
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


def operator_item_is_analysis_item(item: OperatorItem) -> bool:
    return item.get("type") not in {"document", "document_summary"}


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


def _section_count(items: list[OperatorItem]) -> int:
    return sum(1 for item in items if operator_item_is_analysis_item(item))


def _sort_items(items: list[OperatorItem]) -> list[OperatorItem]:
    return sorted(items, key=lambda item: (-_int_metric(item.get("priority"), 0), str(item.get("label") or "")))


def _int_metric(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback
