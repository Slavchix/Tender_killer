from __future__ import annotations

import json
import sqlite3
import hashlib
from typing import Any

from tender_killer.analysis_feedback import FEEDBACK_LABELS
from tender_killer.analysis_feedback import normalize_feedback_state
from tender_killer.schema import ensure_analysis_history_table


CONDITION_LABELS: dict[str, str] = {
    "payment": "условия оплаты",
    "advance": "аванс",
    "delivery_deadline": "срок поставки",
    "delivery_place": "место поставки",
    "closing_documents": "приемка и закрывающие документы",
    "bid_security": "обеспечение заявки",
    "contract_security": "обеспечение контракта",
    "warranty": "гарантия",
    "penalty": "штрафы и пени",
    "national_regime": "национальный режим",
    "certificate_documents": "сертификаты и декларации",
    "license_sro": "лицензии или СРО",
    "packaging_marking": "упаковка и маркировка",
    "termination": "условия расторжения",
    "participant_restrictions": "ограничения по участникам",
    "retentions": "удержания",
}

CONDITION_DIFF_HIGHLIGHT_FAMILIES = {
    "payment",
    "advance",
    "delivery_deadline",
    "delivery_place",
    "closing_documents",
    "bid_security",
    "contract_security",
    "retentions",
    "penalty",
    "termination",
}


def record_analysis_history(
    connection: sqlite3.Connection,
    *,
    source: str,
    external_id: str,
    analysis: dict[str, Any],
    analyzed_at: str,
) -> dict[str, Any]:
    ensure_analysis_history_table(connection)
    previous = connection.execute(
        """
        SELECT id, run_number, snapshot_json
        FROM tender_analysis_history
        WHERE source = ? AND external_id = ?
        ORDER BY run_number DESC
        LIMIT 1
        """,
        (source, external_id),
    ).fetchone()
    previous_snapshot = _json_object(previous["snapshot_json"]) if previous else {}
    previous_id = int(previous["id"]) if previous else None
    run_number = int(previous["run_number"]) + 1 if previous else 1
    changes = build_analysis_change_summary(
        previous_snapshot,
        analysis,
        previous_run_id=previous_id,
    )
    cursor = connection.execute(
        """
        INSERT INTO tender_analysis_history (
            source, external_id, run_number, analyzed_at, status,
            confidence, summary, snapshot_json, changes_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source,
            external_id,
            run_number,
            analyzed_at,
            str(analysis.get("status") or "needs_review"),
            _float_value(analysis.get("confidence")),
            str(analysis.get("summary") or ""),
            json.dumps(analysis, ensure_ascii=False),
            json.dumps(changes, ensure_ascii=False),
        ),
    )
    return {
        "id": int(cursor.lastrowid),
        "run_number": run_number,
        "analyzed_at": analyzed_at,
        "changes": changes,
    }


def list_analysis_history(
    connection: sqlite3.Connection,
    *,
    source: str,
    external_id: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    ensure_analysis_history_table(connection)
    rows = connection.execute(
        """
        SELECT id, run_number, analyzed_at, status, confidence, summary, changes_json
        FROM tender_analysis_history
        WHERE source = ? AND external_id = ?
        ORDER BY run_number DESC
        LIMIT ?
        """,
        (source, external_id, limit),
    ).fetchall()
    return [
        {
            "id": int(row["id"]),
            "run_number": int(row["run_number"]),
            "analyzed_at": row["analyzed_at"],
            "status": row["status"],
            "confidence": float(row["confidence"]),
            "summary": row["summary"],
            "changes": _json_object(row["changes_json"]),
        }
        for row in rows
    ]


def build_analysis_change_summary(
    previous: dict[str, Any],
    current: dict[str, Any],
    *,
    previous_run_id: int | None = None,
) -> dict[str, Any]:
    previous_facts = _facts_by_id(previous)
    current_facts = _facts_by_id(current)
    previous_ids = set(previous_facts)
    current_ids = set(current_facts)
    added = [_fact_label(current_facts[item_id]) for item_id in sorted(current_ids - previous_ids)]
    removed = [_fact_label(previous_facts[item_id]) for item_id in sorted(previous_ids - current_ids)]
    changed = [
        _fact_label(current_facts[item_id])
        for item_id in sorted(previous_ids & current_ids)
        if _fact_signature(previous_facts[item_id]) != _fact_signature(current_facts[item_id])
    ]
    feedback = current.get("analysis_feedback")
    feedback_count = len(feedback) if isinstance(feedback, dict) else 0
    documents = _document_changes(previous.get("documents_snapshot"), current.get("documents_snapshot"))
    condition_diff = _condition_diff(previous, current, documents)
    condition_changes = condition_diff["items"]
    return {
        "previous_run_id": previous_run_id,
        "added_count": len(added),
        "removed_count": len(removed),
        "changed_count": len(changed),
        "feedback_count": feedback_count,
        "added": added[:10],
        "removed": removed[:10],
        "changed": changed[:10],
        "feedback": _feedback_labels(feedback, current_facts)[:10],
        "documents": documents,
        "condition_changes": condition_changes[:10],
        "condition_diff": {
            **condition_diff,
            "items": condition_changes[:10],
        },
        "summary": _change_summary_text(
            previous_run_id=previous_run_id,
            added_count=len(added),
            removed_count=len(removed),
            changed_count=len(changed),
        ),
    }


def _facts_by_id(analysis: dict[str, Any]) -> dict[str, dict[str, Any]]:
    facts = analysis.get("analysis_facts")
    items = facts.get("items") if isinstance(facts, dict) else []
    result: dict[str, dict[str, Any]] = {}
    if not isinstance(items, list):
        return result
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("id") or f"fact:{index}")
        result[item_id] = item
    return result


def build_analysis_documents_snapshot(documents: list[dict[str, Any]]) -> list[dict[str, str]]:
    snapshot: list[dict[str, str]] = []
    for index, document in enumerate(documents):
        if not isinstance(document, dict):
            continue
        name = str(document.get("name") or f"Документ {index + 1}").strip()
        url = str(document.get("url") or "").strip()
        source_document_id = str(document.get("source_document_id") or "").strip()
        key = url or source_document_id or name or f"document:{index}"
        text_status = str(document.get("text_status") or "").strip()
        document_type = str(document.get("document_type") or "").strip()
        text_content = str(document.get("text_content") or "")
        digest_source = "\n".join((name, url, source_document_id, document_type, text_status, _normalized_text(text_content)))
        snapshot.append(
            {
                "key": key,
                "name": name,
                "url": url,
                "document_type": document_type,
                "text_status": text_status,
                "text_hash": hashlib.sha1(digest_source.encode("utf-8")).hexdigest(),
            }
        )
    return snapshot


def _fact_label(item: dict[str, Any]) -> str:
    return str(item.get("label") or item.get("kind") or item.get("id") or "пункт анализа")


def _fact_signature(item: dict[str, Any]) -> tuple[str, ...]:
    fields = (
        "label",
        "value",
        "description",
        "operator_action",
        "source_label",
        "fragment",
        "severity",
        "needs_review",
        "feedback_state",
    )
    return tuple(str(item.get(field) or "") for field in fields)


def _feedback_labels(feedback: Any, facts_by_id: dict[str, dict[str, Any]]) -> list[str]:
    if not isinstance(feedback, dict):
        return []
    rows: list[str] = []
    for fact_id, payload in feedback.items():
        if not isinstance(payload, dict):
            continue
        state = str(payload.get("state") or "").strip()
        state = normalize_feedback_state(state)
        if not state:
            continue
        fact = facts_by_id.get(str(fact_id), {})
        label = _fact_label(fact) if fact else str(fact_id)
        comment = str(payload.get("comment") or "").strip()
        suffix = f" — {comment}" if comment else ""
        rows.append(f"{label}: {_feedback_state_label(state)}{suffix}")
    return rows


def _feedback_state_label(state: str) -> str:
    normalized = normalize_feedback_state(state)
    return FEEDBACK_LABELS.get(normalized, state)


def _document_changes(previous: Any, current: Any) -> dict[str, list[str]]:
    previous_by_key = _documents_by_key(previous)
    current_by_key = _documents_by_key(current)
    previous_keys = set(previous_by_key)
    current_keys = set(current_by_key)
    changed = [
        _document_label(current_by_key[key])
        for key in sorted(previous_keys & current_keys)
        if _document_signature(previous_by_key[key]) != _document_signature(current_by_key[key])
    ]
    return {
        "added": [_document_label(current_by_key[key]) for key in sorted(current_keys - previous_keys)],
        "removed": [_document_label(previous_by_key[key]) for key in sorted(previous_keys - current_keys)],
        "changed": changed,
    }


def _documents_by_key(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or item.get("url") or item.get("source_document_id") or item.get("name") or f"document:{index}")
        result[key] = item
    return result


def _document_label(item: dict[str, Any]) -> str:
    return str(item.get("name") or item.get("url") or item.get("key") or "документ")


def _document_signature(item: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(item.get("text_hash") or ""),
        str(item.get("document_type") or ""),
        str(item.get("text_status") or ""),
        str(item.get("url") or ""),
    )


def _condition_diff(
    previous: dict[str, Any],
    current: dict[str, Any],
    documents: dict[str, list[str]],
) -> dict[str, Any]:
    previous_by_family = _condition_groups_by_family(previous)
    current_by_family = _condition_groups_by_family(current)
    if not previous_by_family and not current_by_family:
        previous_by_family = _fact_conditions_by_family(_facts_by_id(previous).values())
        current_by_family = _fact_conditions_by_family(_facts_by_id(current).values())
    families = sorted(set(previous_by_family) | set(current_by_family))
    changes: list[dict[str, Any]] = []
    for family in families:
        previous_group = previous_by_family.get(family)
        current_group = current_by_family.get(family)
        if _condition_group_signature(previous_group) == _condition_group_signature(current_group):
            continue
        if previous_group and current_group:
            change_type = "changed"
        elif current_group:
            change_type = "added"
        else:
            change_type = "removed"
        before = previous_group.get("summary", "") if previous_group else ""
        after = current_group.get("summary", "") if current_group else ""
        changes.append(
            {
                "family": family,
                "label": (current_group or previous_group or {}).get("label") or CONDITION_LABELS.get(family, family),
                "change_type": change_type,
                "before": before,
                "after": after,
                "status_before": previous_group.get("status", "") if previous_group else "",
                "status_after": current_group.get("status", "") if current_group else "",
                "source_status_before": previous_group.get("source_status", "") if previous_group else "",
                "source_status_after": current_group.get("source_status", "") if current_group else "",
                "sources_before": previous_group.get("sources", []) if previous_group else [],
                "sources_after": current_group.get("sources", []) if current_group else [],
                "operator_action_before": previous_group.get("operator_action", "") if previous_group else "",
                "operator_action_after": current_group.get("operator_action", "") if current_group else "",
                "changed_fields": _condition_changed_fields(previous_group, current_group),
            }
        )
    metrics = {
        "added": sum(1 for item in changes if item["change_type"] == "added"),
        "removed": sum(1 for item in changes if item["change_type"] == "removed"),
        "changed": sum(1 for item in changes if item["change_type"] == "changed"),
    }
    highlights = {
        item["family"]: item
        for item in changes
        if item.get("family") in CONDITION_DIFF_HIGHLIGHT_FAMILIES
    }
    return {
        "version": 2,
        "items": changes,
        "metrics": metrics,
        "highlights": highlights,
        "documents": documents,
        "action_plan_changed": _action_plan_signature(previous) != _action_plan_signature(current),
    }


def _condition_groups_by_family(analysis: dict[str, Any]) -> dict[str, dict[str, Any]]:
    operator_view = analysis.get("operator_view") if isinstance(analysis, dict) else None
    condition_groups = operator_view.get("condition_groups") if isinstance(operator_view, dict) else None
    items = condition_groups.get("items") if isinstance(condition_groups, dict) else None
    if not isinstance(items, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        family = str(item.get("family") or "").strip()
        if not family:
            continue
        result[family] = {
            "family": family,
            "label": str(item.get("label") or CONDITION_LABELS.get(family, family)),
            "status": str(item.get("status") or ""),
            "source_status": str(item.get("source_status") or ""),
            "summary": str(item.get("summary") or ""),
            "sources": _string_list(item.get("sources")),
            "operator_action": str(item.get("operator_action") or item.get("resolution") or ""),
            "primary_fact_id": str(item.get("primary_fact_id") or ""),
            "related_fact_ids": _string_list(item.get("related_fact_ids")),
        }
    return result


def _condition_group_signature(group: dict[str, Any] | None) -> tuple[Any, ...]:
    if not group:
        return ()
    return (
        group.get("summary", ""),
        group.get("status", ""),
        group.get("source_status", ""),
        tuple(group.get("sources") or []),
        group.get("operator_action", ""),
        group.get("primary_fact_id", ""),
        tuple(group.get("related_fact_ids") or []),
    )


def _condition_changed_fields(previous: dict[str, Any] | None, current: dict[str, Any] | None) -> list[str]:
    fields = (
        ("summary", "summary"),
        ("status", "status"),
        ("source_status", "source_status"),
        ("sources", "sources"),
        ("operator_action", "operator_action"),
        ("primary_fact_id", "primary_fact_id"),
        ("related_fact_ids", "related_fact_ids"),
    )
    changed: list[str] = []
    previous = previous or {}
    current = current or {}
    for field_name, payload_key in fields:
        if previous.get(payload_key) != current.get(payload_key):
            changed.append(field_name)
    return changed


def _action_plan_signature(analysis: dict[str, Any]) -> tuple[tuple[str, str, str], ...]:
    operator_view = analysis.get("operator_view") if isinstance(analysis, dict) else None
    action_plan = operator_view.get("action_plan") if isinstance(operator_view, dict) else None
    if not isinstance(action_plan, list):
        return ()
    rows: list[tuple[str, str, str]] = []
    for item in action_plan:
        if not isinstance(item, dict):
            continue
        rows.append(
            (
                str(item.get("id") or ""),
                str(item.get("status") or ""),
                str(item.get("next_step") or ""),
            )
        )
    return tuple(rows)


def _fact_conditions_by_family(items: Any) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        family = _condition_family(item)
        if not family:
            continue
        text = _condition_text(item)
        if text:
            result[family] = {
                "family": family,
                "label": CONDITION_LABELS.get(family, family),
                "status": str(item.get("status") or ""),
                "source_status": "",
                "summary": text,
                "sources": _string_list(item.get("source_label") or item.get("document_name") or item.get("source")),
                "operator_action": str(item.get("operator_action") or ""),
                "primary_fact_id": str(item.get("id") or ""),
                "related_fact_ids": _string_list(item.get("id")),
            }
    return result


def _condition_family(item: dict[str, Any]) -> str:
    category = str(item.get("category") or "").strip().casefold()
    text = _normalized_text(
        " ".join(
            str(item.get(key) or "")
            for key in ("id", "label", "category", "value", "description", "fragment", "source_context", "operator_summary")
        )
    )
    if any(marker in text for marker in ("удерж", "неустоек из суммы", "неустойку из суммы", "из суммы оплаты")):
        return "retentions"
    if "оплат" in text:
        return "payment"
    if "аванс" in text:
        return "advance"
    if category == "delivery" or any(marker in text for marker in ("срок постав", "срок исполн", "поставка в течение")):
        return "delivery_deadline"
    if any(marker in text for marker in ("acceptance", "приемк", "приёмк", "упд", "закрывающ", "накладн", "акт прием", "акт приём")):
        return "closing_documents"
    if "обеспеч" in text and "заяв" in text:
        return "bid_security"
    if "contract-security" in text or "contract_security" in text:
        return "contract_security"
    if "обеспеч" in text and any(marker in text for marker in ("контракт", "исполн")):
        return "contract_security"
    if any(marker in text for marker in ("штраф", "пен", "неустой")):
        return "penalty"
    if category == "national_regime" or any(marker in text for marker in ("национальн", "страна происхожд", "1875")):
        return "national_regime"
    if any(marker in text for marker in ("сертифик", "деклараци", "паспорт качества", "регистрацион")):
        return "certificate_documents"
    return ""


def _condition_text(item: dict[str, Any]) -> str:
    for key in ("value", "fragment", "source_context", "operator_summary", "description", "label"):
        text = str(item.get(key) or "").strip()
        if text:
            return text
    return ""


def _normalized_text(value: Any) -> str:
    return " ".join(str(value or "").split()).casefold()


def _string_list(values: Any) -> list[str]:
    if isinstance(values, list):
        source = values
    elif values in (None, ""):
        source = []
    else:
        source = [values]
    result: list[str] = []
    seen: set[str] = set()
    for value in source:
        text = str(value or "").strip()
        key = _normalized_text(text)
        if not text or key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _change_summary_text(
    *,
    previous_run_id: int | None,
    added_count: int,
    removed_count: int,
    changed_count: int,
) -> str:
    if previous_run_id is None:
        return f"Первый анализ: найдено {added_count} пунктов."
    if not any((added_count, removed_count, changed_count)):
        return "Изменений после пересчета не найдено."
    return f"Добавлено {added_count}, удалено {removed_count}, изменено {changed_count}."


def _json_object(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
