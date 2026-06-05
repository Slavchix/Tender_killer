from __future__ import annotations

import json
import sqlite3
from typing import Any

from tender_killer.schema import ensure_analysis_history_table


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
    return {
        "previous_run_id": previous_run_id,
        "added_count": len(added),
        "removed_count": len(removed),
        "changed_count": len(changed),
        "feedback_count": feedback_count,
        "added": added[:10],
        "removed": removed[:10],
        "changed": changed[:10],
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
