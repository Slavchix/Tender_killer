from __future__ import annotations

from typing import Any


FEEDBACK_LABELS: dict[str, str] = {
    "confirmed": "подтверждено",
    "important": "важно",
    "not_risk": "не риск",
    "ignored": "игнорировать",
}


def normalize_feedback_state(value: Any) -> str:
    state = str(value or "").strip().casefold()
    return state if state in FEEDBACK_LABELS else ""


def apply_analysis_feedback(analysis: dict[str, Any]) -> None:
    feedback = analysis.get("analysis_feedback")
    if not isinstance(feedback, dict):
        raw_payload = analysis.get("raw_payload")
        feedback = raw_payload.get("analysis_feedback") if isinstance(raw_payload, dict) else {}
    if not isinstance(feedback, dict) or not feedback:
        return
    _apply_to_items(analysis.get("checklist"), feedback)
    _apply_to_items(analysis.get("evidence_items"), feedback)
    analysis_facts = analysis.get("analysis_facts")
    if isinstance(analysis_facts, dict):
        _apply_to_items(analysis_facts.get("items"), feedback)
        _refresh_fact_metrics(analysis_facts)
    operator_view = analysis.get("operator_view")
    if isinstance(operator_view, dict):
        for section_key in ("sections", "major_blocks"):
            for section in operator_view.get(section_key) or []:
                if isinstance(section, dict):
                    _apply_to_items(section.get("items"), feedback)


def _apply_to_items(items: Any, feedback: dict[str, Any]) -> None:
    if not isinstance(items, list):
        return
    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("id") or "").strip()
        if not item_id:
            continue
        feedback_item = feedback.get(item_id)
        if not isinstance(feedback_item, dict):
            continue
        _apply_feedback_to_item(item, normalize_feedback_state(feedback_item.get("state")))


def _apply_feedback_to_item(item: dict[str, Any], state: str) -> None:
    if not state:
        return
    item["feedback_state"] = state
    item["feedback_label"] = FEEDBACK_LABELS[state]
    if state == "confirmed":
        item["status"] = "confirmed"
        return
    if state == "important":
        item["status"] = "important"
        item["priority"] = max(int(item.get("priority") or 0), 100)
        return
    if state == "not_risk":
        item["status"] = "not_risk"
        item["is_blocker"] = False
        if item.get("severity") == "high":
            item["severity"] = "medium"
        return
    if state == "ignored":
        item["status"] = "ignored"
        item["is_blocker"] = False
        item["is_price_factor"] = False
        item["priority"] = 0


def _refresh_fact_metrics(analysis_facts: dict[str, Any]) -> None:
    items = analysis_facts.get("items")
    if not isinstance(items, list):
        return
    actionable = [
        item
        for item in items
        if isinstance(item, dict)
        and item.get("kind") != "subject"
        and item.get("feedback_state") != "ignored"
    ]
    analysis_facts["metrics"] = {
        "total": len(items),
        "blockers": sum(1 for item in actionable if item.get("is_blocker")),
        "price_factors": sum(1 for item in actionable if item.get("is_price_factor")),
        "unbound": sum(1 for item in actionable if item.get("needs_review")),
    }
