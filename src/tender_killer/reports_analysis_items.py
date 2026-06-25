from __future__ import annotations

from typing import Any


def report_item_meaning(item: dict[str, Any]) -> str:
    interpretation = item.get("interpretation")
    if isinstance(interpretation, dict) and interpretation.get("meaning"):
        return _value(interpretation.get("meaning"), "")
    return _value(
        item.get("operator_summary")
        or item.get("description")
        or item.get("impact")
        or item.get("value")
        or item.get("fragment"),
        "",
    )


def report_item_found(item: dict[str, Any]) -> str:
    interpretation = item.get("interpretation")
    if isinstance(interpretation, dict) and interpretation.get("found"):
        return _value(interpretation.get("found"), "")
    return _value(item.get("value") or item.get("fragment") or item.get("source_context"), "")


def report_item_impact(item: dict[str, Any]) -> str:
    interpretation = item.get("interpretation")
    if isinstance(interpretation, dict) and interpretation.get("impact"):
        return _value(interpretation.get("impact"), "")
    return _value(item.get("impact") or item.get("operator_summary") or item.get("description"), "")


def report_item_action(item: dict[str, Any]) -> str:
    interpretation = item.get("interpretation")
    feedback = operator_feedback_text(item)
    action = ""
    if isinstance(interpretation, dict) and interpretation.get("action"):
        action = _value(interpretation.get("action"), "")
    else:
        action = _value(item.get("operator_check") or item.get("operator_action") or item.get("next_step"), "")
    if feedback and action:
        return f"{action} Оператор: {feedback}"
    if feedback:
        return f"Оператор: {feedback}"
    return action


def operator_feedback_text(item: dict[str, Any]) -> str:
    label = _value(item.get("feedback_label"), "").strip()
    comment = _value(item.get("feedback_comment"), "").strip()
    if label and comment:
        return f"{label}: {comment}"
    return label or comment


def item_source_text(item: dict[str, Any]) -> str:
    source = _value(item.get("source_label") or item.get("document_name") or item.get("source"), "")
    fragment = short_text(item.get("fragment") or item.get("source_context"), 180)
    if source and fragment:
        return f"{source}: {fragment}"
    return source or fragment


def short_text(value: Any, limit: int) -> str:
    text = _value(value, "").replace("\n", " ").strip()
    while "  " in text:
        text = text.replace("  ", " ")
    if len(text) <= limit:
        return text
    return f"{text[: max(0, limit - 1)].rstrip()}…"


def _value(value: Any, fallback: str = "не указано") -> str:
    if value is None or value == "":
        return fallback
    return str(value)
