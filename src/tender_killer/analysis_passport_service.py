from __future__ import annotations

from typing import Any

from tender_killer.analysis_condition_groups_service import EXPECTED_TZ_CHECKS
from tender_killer.analysis_operator_sections_service import MAJOR_SECTION_IDS
from tender_killer.analysis_operator_view_service import build_analysis_operator_view


def build_analysis_tz_passport(
    analysis: dict[str, Any] | None,
    documents: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a compact TZ passport from the same four-block Analysis contract."""
    operator_view = build_analysis_operator_view(analysis, documents)
    decision = operator_view.get("decision_brief") if isinstance(operator_view.get("decision_brief"), dict) else {}
    sections = [_passport_section(section) for section in operator_view.get("sections", []) if section.get("id") in MAJOR_SECTION_IDS]
    document_state = operator_view.get("document_state") if isinstance(operator_view.get("document_state"), dict) else {}
    condition_groups = operator_view.get("condition_groups") if isinstance(operator_view.get("condition_groups"), dict) else {}
    items = [item for section in sections for item in section.get("items", []) if _is_passport_fact_item(item)]
    subject = _passport_subject(items, analysis)
    documents_summary = _passport_documents(document_state)
    key_conditions = _unique_texts(
        item["label"]
        for item in items
        if not item.get("expected_missing")
        and not item.get("conflict_flags")
        and not _is_red_flag(item)
        and item.get("type") != "subject"
    )[:8]
    red_flags = _unique_texts(item["label"] for item in items if _is_red_flag(item))[:8]
    conflicts = _unique_texts(item["label"] for item in items if item.get("conflict_flags"))[:8]
    expected_missing = _ordered_expected_missing(items)[:8]
    verdict = _passport_verdict(
        document_state=document_state,
        items=items,
        red_flags=red_flags,
        conflicts=conflicts,
        expected_missing=expected_missing,
    )
    return {
        "version": 2,
        "status": str(decision.get("status") or "pending"),
        "title": str(decision.get("title") or "Паспорт ТЗ появится после анализа."),
        "summary": str(decision.get("summary") or ""),
        "confidence": decision.get("confidence"),
        "subject": subject,
        "documents": documents_summary,
        "key_conditions": key_conditions,
        "red_flags": red_flags,
        "conflicts": conflicts,
        "expected_missing": expected_missing,
        "condition_groups": condition_groups,
        "verdict": verdict,
        "summary_block": {
            "subject": subject,
            "documents": documents_summary["label"],
            "key_conditions": key_conditions,
            "red_flags": red_flags,
            "conflicts": conflicts,
            "expected_missing": expected_missing,
            "condition_groups": _passport_condition_group_labels(condition_groups),
            "verdict": verdict["label"],
        },
        "sections": sections,
    }


def _passport_section(section: dict[str, Any]) -> dict[str, Any]:
    items = [_passport_item(item) for item in section.get("items", []) if isinstance(item, dict)]
    return {
        "id": str(section.get("id") or ""),
        "title": str(section.get("title") or ""),
        "count": len(items),
        "tone": str(section.get("tone") or "default"),
        "empty": str(section.get("empty") or ""),
        "items": items,
    }


def _passport_item(item: dict[str, Any]) -> dict[str, Any]:
    kind = str(item.get("kind") or item.get("type") or "fact")
    label = str(item.get("label") or "Условие")
    if kind == "subject":
        label = "Кратко"
    return {
        "id": str(item.get("id") or label),
        "type": kind,
        "label": label,
        "value": str(item.get("value") or item.get("description") or item.get("fragment") or ""),
        "category": str(item.get("category") or "general"),
        "severity": str(item.get("severity") or "medium"),
        "source": str(item.get("source_label") or item.get("source") or ""),
        "impact": str(item.get("impact") or item.get("operator_action") or ""),
        "needs_review": bool(item.get("needs_review")),
        "is_blocker": bool(item.get("is_blocker")),
        "conflict_flags": [str(flag) for flag in item.get("conflict_flags") or [] if str(flag).strip()],
        "expected_missing": bool(item.get("expected_missing")),
    }


def _is_passport_fact_item(item: dict[str, Any]) -> bool:
    return item.get("type") not in {"document", "document_summary"}


def _passport_subject(items: list[dict[str, Any]], analysis: dict[str, Any] | None) -> str:
    for item in items:
        if item.get("type") == "subject" and str(item.get("value") or "").strip():
            return str(item["value"]).strip()
    if isinstance(analysis, dict) and str(analysis.get("summary") or "").strip():
        return str(analysis["summary"]).strip()
    return "предмет не определен"


def _passport_documents(document_state: dict[str, Any]) -> dict[str, Any]:
    status = str(document_state.get("status") or "no_documents")
    total = _int_value(document_state.get("total"))
    ready = _int_value(document_state.get("text_ready"))
    if status == "ready":
        label = "документы готовы"
    elif total == 0:
        label = "документы не найдены"
    else:
        label = "документы не готовы"
    return {
        "status": status,
        "label": label,
        "ready": ready,
        "total": total,
        "summary": str(document_state.get("summary") or ""),
        "next_step": str(document_state.get("next_step") or ""),
    }


def _passport_verdict(
    *,
    document_state: dict[str, Any],
    items: list[dict[str, Any]],
    red_flags: list[str],
    conflicts: list[str],
    expected_missing: list[str],
) -> dict[str, str]:
    has_high_blocker = any(
        item.get("is_blocker") and str(item.get("severity") or "").casefold() == "high"
        for item in items
        if not item.get("expected_missing")
    )
    if has_high_blocker or red_flags:
        return {"code": "high_risk", "label": "высокий риск"}
    has_manual_review = (
        str(document_state.get("status") or "") != "ready"
        or bool(conflicts)
        or bool(expected_missing)
        or any(item.get("needs_review") for item in items)
    )
    if has_manual_review:
        return {"code": "manual_review", "label": "нужна ручная проверка"}
    return {"code": "can_read_further", "label": "можно читать дальше"}


def _is_red_flag(item: dict[str, Any]) -> bool:
    return (
        str(item.get("type") or item.get("kind") or "") in {"red_flag", "blocker", "risk"}
        or bool(item.get("is_blocker"))
        or str(item.get("severity") or "").casefold() == "high"
    ) and not item.get("expected_missing")


def _unique_texts(values: Any) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        key = text.casefold()
        if not text or key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _ordered_expected_missing(items: list[dict[str, Any]]) -> list[str]:
    labels = _unique_texts(item["label"] for item in items if item.get("expected_missing"))
    order = {spec["label"].casefold(): index for index, spec in enumerate(EXPECTED_TZ_CHECKS)}
    return sorted(labels, key=lambda label: (order.get(label.casefold(), 999), label.casefold()))


def _passport_condition_group_labels(condition_groups: dict[str, Any]) -> list[str]:
    groups = condition_groups.get("items") if isinstance(condition_groups, dict) else []
    labels: list[str] = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        label = _passport_condition_group_label(group)
        if label:
            labels.append(label)
    return labels[:8]


def _passport_condition_group_label(group: dict[str, Any]) -> str:
    label = str(group.get("label") or group.get("family") or "").strip()
    status = _passport_condition_status(str(group.get("status") or "").strip())
    if label and status:
        return f"{label} · {status}"
    return label or status


def _passport_condition_status(status: str) -> str:
    return {
        "confirmed": "подтверждено",
        "conflict": "противоречие",
        "expected_missing": "не найдено",
        "manual_review": "ручная проверка",
    }.get(status, status)


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
