from __future__ import annotations

from typing import Any


EXPECTED_CHECKS: tuple[dict[str, Any], ...] = (
    {
        "id": "delivery_deadline",
        "label": "Срок поставки",
        "category": "delivery",
        "hint": "Нужно найти срок поставки или выполнения работ.",
        "markers": ("delivery_deadline", "срок постав", "срок выполн", "delivery deadline", "srok postav"),
    },
    {
        "id": "payment_terms",
        "label": "Оплата",
        "category": "financial",
        "hint": "Нужно найти порядок оплаты, отсрочку, аванс или условие оплаты после приемки.",
        "markers": ("payment_terms", "оплат", "аванс", "payment", "oplata"),
    },
    {
        "id": "contract_security",
        "label": "Обеспечение исполнения контракта",
        "category": "financial",
        "hint": "Нужно найти размер обеспечения исполнения или условие независимой гарантии.",
        "markers": (
            "contract_security",
            "обеспечение исполнения",
            "независимая гарант",
            "contract security",
            "obespechenie ispolneniya",
        ),
    },
    {
        "id": "acceptance_documents",
        "label": "Приемка и закрывающие документы",
        "category": "acceptance",
        "hint": "Нужно найти порядок приемки, акт, УПД или срок устранения замечаний.",
        "markers": ("acceptance_documents", "приемк", "приёмк", "акт", "упд", "acceptance"),
    },
)


def build_missing_checks(analysis: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(analysis, dict):
        return []
    haystack = _analysis_haystack(analysis)
    missing: list[dict[str, Any]] = []
    for definition in EXPECTED_CHECKS:
        if _contains_any(haystack, definition["markers"]):
            continue
        missing.append(
            {
                "id": definition["id"],
                "label": definition["label"],
                "category": definition["category"],
                "status": "missing",
                "severity": "medium",
                "hint": definition["hint"],
            }
        )
    return missing


def missing_checklist_items(missing_checks: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in missing_checks or []:
        if not isinstance(item, dict) or item.get("status") != "missing":
            continue
        label = str(item.get("label") or "").strip()
        hint = str(item.get("hint") or "").strip()
        missing_id = str(item.get("id") or "").strip()
        if not label or not missing_id:
            continue
        items.append(
            {
                "type": "missing_check",
                "missing_check_id": missing_id,
                "label": f"Не найдено: {label}",
                "category": item.get("category") or "general",
                "severity": item.get("severity") or "medium",
                "evidence": hint or f"В прочитанных документах не найдено условие: {label}.",
                "status": "missing",
            }
        )
    return items


def _analysis_haystack(analysis: dict[str, Any]) -> str:
    values: list[str] = []
    for key in ("summary", "requirements", "risks", "red_flags"):
        values.extend(_strings_from_value(analysis.get(key)))
    for key in ("checklist", "execution_terms", "evidence_items"):
        for item in analysis.get(key) or []:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "missing_check":
                continue
            values.extend(_strings_from_value(item))
    return " ".join(values).casefold()


def _strings_from_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        strings: list[str] = []
        for nested in value.values():
            strings.extend(_strings_from_value(nested))
        return strings
    if isinstance(value, list):
        strings: list[str] = []
        for nested in value:
            strings.extend(_strings_from_value(nested))
        return strings
    return [str(value)]


def _contains_any(haystack: str, markers: tuple[str, ...]) -> bool:
    return any(marker.casefold() in haystack for marker in markers)
