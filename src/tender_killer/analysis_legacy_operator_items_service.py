from __future__ import annotations

from typing import Any

from tender_killer.analysis_operator_item_service import build_operator_item
from tender_killer.analysis_operator_item_service import dedupe_operator_items
from tender_killer.analysis_operator_item_service import fallback_kind
from tender_killer.analysis_types import OperatorItem


def build_legacy_operator_items(analysis: dict[str, Any]) -> list[OperatorItem]:
    items: list[OperatorItem] = []
    checklist = _checklist_items(analysis.get("checklist"))
    checklist_by_label = {item["label"]: item for item in checklist}

    summary = _text(analysis.get("summary"))
    if summary:
        items.append(
            build_operator_item(
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
        items.append(build_operator_item(item, len(items)))

    for term in _execution_terms(analysis.get("execution_terms")):
        items.append(build_operator_item({**term, "kind": "execution_term"}, len(items)))

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

    return dedupe_operator_items(items)


def _legacy_label_item(
    label: str,
    source: dict[str, Any],
    kind: str,
    *,
    is_blocker: bool = False,
    severity: str | None = None,
) -> OperatorItem:
    return build_operator_item(
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


def _checklist_items(value: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for raw_item in value if isinstance(value, list) else []:
        if not isinstance(raw_item, dict) or not raw_item.get("label"):
            continue
        items.append(
            {
                **raw_item,
                "kind": raw_item.get("kind") or fallback_kind(raw_item),
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


def _text_list(value: Any) -> list[str]:
    values = value if isinstance(value, list) else [value]
    return [_text(item) for item in values if _text(item)]


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()
