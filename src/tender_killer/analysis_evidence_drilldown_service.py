from __future__ import annotations

from typing import Any


def build_evidence_drilldowns(items: list[dict[str, Any]]) -> dict[str, Any]:
    drilldown_items: list[dict[str, Any]] = []
    by_fact_id: dict[str, str] = {}
    seen: set[str] = set()
    for item in items:
        fact_id = _text(item.get("id"))
        if not fact_id or fact_id in seen:
            continue
        entry = _evidence_drilldown_item(item, fact_id)
        if entry is None:
            continue
        seen.add(fact_id)
        by_fact_id[fact_id] = entry["id"]
        item["evidence_drilldown_id"] = entry["id"]
        drilldown_items.append(entry)
    return {
        "version": 1,
        "items": drilldown_items,
        "by_fact_id": by_fact_id,
    }


def _evidence_drilldown_item(item: dict[str, Any], fact_id: str) -> dict[str, Any] | None:
    source_label = _text(item.get("source_label") or item.get("document_name") or item.get("source"))
    fragment = _text(item.get("fragment"))
    source_context = _text(item.get("source_context"))
    evidence_summary = _text(item.get("evidence_summary"))
    evidence_quality = item.get("evidence_quality") if isinstance(item.get("evidence_quality"), dict) else {}
    source_binding = item.get("source_binding") if isinstance(item.get("source_binding"), dict) else {}
    confidence_level = item.get("confidence_level") if isinstance(item.get("confidence_level"), dict) else {}
    if not any((source_label, fragment, source_context, evidence_summary, evidence_quality, source_binding)):
        return None
    return {
        "id": fact_id,
        "kind": _text(item.get("kind") or item.get("type")),
        "title": _text(item.get("label")) or fact_id,
        "value": _text(item.get("value")),
        "category": _text(item.get("category")),
        "severity": _text(item.get("severity")),
        "source_label": source_label,
        "document_name": _text(item.get("document_name") or item.get("source")),
        "source_page": item.get("source_page"),
        "fragment": fragment,
        "source_context": source_context,
        "evidence_summary": evidence_summary,
        "source_binding": source_binding,
        "confidence_level": confidence_level,
        "evidence_quality": evidence_quality,
        "related_fact_ids": [fact_id],
    }


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()
