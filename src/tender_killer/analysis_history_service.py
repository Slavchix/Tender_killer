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
    "closing_documents": "приемка и закрывающие документы",
    "bid_security": "обеспечение заявки",
    "contract_security": "обеспечение контракта",
    "penalty": "штрафы и пени",
    "national_regime": "национальный режим",
    "certificate_documents": "сертификаты и декларации",
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
    condition_changes = _condition_changes(previous_facts, current_facts)
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


def _condition_changes(
    previous_facts: dict[str, dict[str, Any]],
    current_facts: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    previous_by_family = _conditions_by_family(previous_facts.values())
    current_by_family = _conditions_by_family(current_facts.values())
    families = sorted(set(previous_by_family) | set(current_by_family))
    changes: list[dict[str, str]] = []
    for family in families:
        previous_text = previous_by_family.get(family, "")
        current_text = current_by_family.get(family, "")
        if previous_text == current_text:
            continue
        if previous_text and current_text:
            change_type = "changed"
        elif current_text:
            change_type = "added"
        else:
            change_type = "removed"
        changes.append(
            {
                "family": family,
                "label": CONDITION_LABELS.get(family, family),
                "change_type": change_type,
                "before": previous_text,
                "after": current_text,
            }
        )
    return changes


def _conditions_by_family(items: Any) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        family = _condition_family(item)
        if not family:
            continue
        text = _condition_text(item)
        if text:
            result[family] = text
    return result


def _condition_family(item: dict[str, Any]) -> str:
    category = str(item.get("category") or "").strip().casefold()
    text = _normalized_text(
        " ".join(
            str(item.get(key) or "")
            for key in ("id", "label", "category", "value", "description", "fragment", "source_context", "operator_summary")
        )
    )
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
