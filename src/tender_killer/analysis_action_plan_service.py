from __future__ import annotations

from typing import Any

from tender_killer.analysis_condition_groups_service import unique_condition_texts


def build_analysis_action_plan(
    sections: list[dict[str, Any]],
    document_state: dict[str, Any],
    condition_groups: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    groups = condition_groups.get("items") if isinstance(condition_groups, dict) else []
    group_items = [group for group in groups if isinstance(group, dict)]
    for section in sections:
        items = [item for item in section["items"] if _is_analysis_item(item)]
        section_id = section["id"]
        section_groups = _action_condition_groups_for_section(section, group_items)
        focus_group = section_groups[0] if section_groups else None
        focus_item = None if focus_group else (items[0] if items else None)
        status = _action_status(section_id, document_state, items, section_groups)

        plan.append(
            {
                "id": section_id,
                "title": _action_title(section_id),
                "status": status,
                "next_step": _action_next_step(section_id, document_state, focus_item, focus_group),
                "items": (
                    [_action_group_label(group) for group in section_groups[:3]]
                    if section_groups
                    else [_action_item_label(item) for item in items[:3]]
                ),
                "condition_fact_ids": _action_condition_fact_ids(section_groups),
                "source": "condition_groups" if section_groups else "facts",
            }
        )
    return plan[:4]


def _action_condition_groups_for_section(section: dict[str, Any], groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    section_items = [
        item
        for item in section.get("items") or []
        if isinstance(item, dict)
    ]
    items_by_id = {_text(item.get("id")): item for item in section_items if _text(item.get("id"))}
    section_fact_ids = {
        fact_id
        for fact_id in items_by_id
    }
    matched = [
        group
        for group in groups
        if any(fact_id in section_fact_ids for fact_id in group.get("related_fact_ids") or [])
    ]
    return sorted(matched, key=lambda group: _action_group_priority(group, items_by_id))


def _action_group_priority(group: dict[str, Any], items_by_id: dict[str, dict[str, Any]]) -> tuple[int, int, str]:
    status_order = {
        "conflict": 0,
        "manual_review": 2,
        "confirmed": 3,
        "expected_missing": 4,
    }
    if _action_group_has_blocker(group, items_by_id):
        status_rank = 1
    else:
        status_rank = status_order.get(_text(group.get("status")), 9)
    source_order = {
        "conflicting_sources": 0,
        "missing": 1,
        "needs_source_review": 2,
        "inferred": 3,
        "explicit_source": 4,
        "primary_source": 5,
    }
    return (
        status_rank,
        source_order.get(_text(group.get("source_status")), 9),
        _text(group.get("label")).casefold(),
    )


def _action_group_has_blocker(group: dict[str, Any], items_by_id: dict[str, dict[str, Any]]) -> bool:
    for fact_id in group.get("related_fact_ids") or []:
        item = items_by_id.get(_text(fact_id))
        if not item or item.get("expected_missing"):
            continue
        kind = _text(item.get("type") or item.get("kind"))
        severity = _text(item.get("severity")).casefold()
        if item.get("is_blocker") or kind in {"red_flag", "blocker", "risk"} or severity in {"high", "critical"}:
            return True
    return False


def _action_status(
    section_id: str,
    document_state: dict[str, Any],
    items: list[dict[str, Any]],
    groups: list[dict[str, Any]],
) -> str:
    group_statuses = {_text(group.get("status")) for group in groups}
    if group_statuses.intersection({"conflict", "expected_missing", "manual_review"}):
        return "manual_review"
    if groups:
        return "ok" if group_statuses == {"confirmed"} else "needs_review"
    if section_id == "decision_risks" and items:
        return "manual_review"
    if items:
        return "needs_review"
    if section_id == "product_compliance" and document_state.get("status") != "ready":
        return str(document_state.get("status") or "pending")
    return "ok"


def _action_title(section_id: str) -> str:
    return {
        "decision_risks": "Проверить итог и риски",
        "product_compliance": "Сверить товар и документы",
        "fulfillment_terms": "Разобрать поставку и исполнение",
        "acceptance_payment": "Проверить приемку и оплату",
    }[section_id]


def _action_next_step(
    section_id: str,
    document_state: dict[str, Any],
    focus_item: dict[str, Any] | None = None,
    focus_group: dict[str, Any] | None = None,
) -> str:
    if focus_group:
        action = _text(focus_group.get("operator_action") or focus_group.get("resolution"))
        if action:
            return action
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


def _action_group_label(group: dict[str, Any]) -> str:
    label = _text(group.get("label") or group.get("family"))
    status = _action_group_status_label(_text(group.get("status")))
    if label and status:
        return f"{label} · {status}"
    return label or status


def _action_group_status_label(status: str) -> str:
    return {
        "confirmed": "подтверждено",
        "conflict": "противоречие",
        "expected_missing": "не найдено",
        "manual_review": "ручная проверка",
    }.get(status, status)


def _action_condition_fact_ids(groups: list[dict[str, Any]]) -> list[str]:
    return unique_condition_texts(
        fact_id
        for group in groups
        for fact_id in (group.get("related_fact_ids") or [])
    )


def _is_analysis_item(item: dict[str, Any]) -> bool:
    return item.get("type") not in {"document", "document_summary"}


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()
