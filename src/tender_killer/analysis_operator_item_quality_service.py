from __future__ import annotations

import re
from typing import Any

from tender_killer.analysis_condition_groups_service import condition_source_hierarchy_score
from tender_killer.analysis_condition_groups_service import normalized_condition_family
from tender_killer.analysis_condition_groups_service import semantic_family
from tender_killer.analysis_types import OperatorItem


def dedupe_operator_items(items: list[OperatorItem]) -> list[OperatorItem]:
    best_by_key: dict[tuple[str, str, str], OperatorItem] = {}
    ordered_keys: list[tuple[str, str, str]] = []
    for item in items:
        if not _is_operator_visible_item(item):
            continue
        key = _dedupe_key(item)
        current = best_by_key.get(key)
        if current is None:
            best_by_key[key] = item
            ordered_keys.append(key)
            continue
        if _operator_item_quality(item) > _operator_item_quality(current):
            best_by_key[key] = item
    return [best_by_key[key] for key in ordered_keys]


def operator_item_is_visible(item: OperatorItem) -> bool:
    return _is_operator_visible_item(item)


def operator_item_quality(item: OperatorItem) -> int:
    return _operator_item_quality(item)


def _dedupe_key(item: OperatorItem) -> tuple[str, str, str]:
    kind = _text(item.get("kind") or item.get("type"))
    if kind in {"document", "document_summary", "subject"}:
        return (kind, _dedupe_text(item.get("id") or item.get("label")), "")
    label = _text(item.get("label"))
    category = _text(item.get("category"))
    family = semantic_family(label, category)
    if item.get("conflict_flags"):
        return ("conflict", family or _dedupe_text(label), _dedupe_text(item.get("fragment") or item.get("value") or item.get("source_context")))
    if family:
        return ("semantic", family, "")
    return (
        kind,
        _dedupe_text(label),
        "" if _operator_item_quality(item) <= 0 else _dedupe_text(item.get("fragment") or item.get("value")),
    )


def _is_operator_visible_item(item: OperatorItem) -> bool:
    kind = _text(item.get("kind") or item.get("type"))
    if kind == "document_summary":
        return True
    if kind == "document":
        return False
    if kind == "subject":
        return bool(_specific_text(item, allow_description=True))
    return _operator_item_quality(item) > 0


def _operator_item_quality(item: OperatorItem) -> int:
    label = _text(item.get("label"))
    category = _text(item.get("category"))
    score = 0
    source_context = _text(item.get("source_context"))
    fragment = _text(item.get("fragment"))
    specific = _specific_text(item)
    if source_context:
        score += 90
    if fragment and _item_text_is_relevant(item, fragment):
        score += 80
    if _has_real_source(item) and (not fragment or _item_text_is_relevant(item, fragment) or source_context):
        score += 45
    if specific and _item_text_is_relevant(item, specific):
        score += 35
    if score and _text(item.get("rule_id")):
        score += 5
    if not score and label:
        return 0
    family = semantic_family(label, category)
    if family:
        score += condition_source_hierarchy_score(item, normalized_condition_family(family))
    return score + min(_int_metric(item.get("priority"), 0), 100)


def _specific_text(item: OperatorItem, *, allow_description: bool = False) -> str:
    label = _text(item.get("label"))
    fields = ["value"]
    if allow_description:
        fields.append("description")
    for field in fields:
        text = _text(item.get(field))
        if text and not _description_is_only_label(text, label):
            return text
    return ""


def _has_real_source(item: OperatorItem) -> bool:
    source = _text(item.get("source_label") or item.get("source") or item.get("document_name"))
    if not source:
        return False
    return _dedupe_text(source) != _dedupe_text("Документ не привязан")


def _item_text_is_relevant(item: OperatorItem, value: str) -> bool:
    text = _dedupe_text(value)
    if not text:
        return False
    label = _text(item.get("label"))
    category = _text(item.get("category"))
    family = semantic_family(label, category)
    if family == "national_regime":
        return any(
            marker in text
            for marker in ("национальн", "страна происхожд", "страну происхожд", "страны происхожд", "1875")
        )
    if family == "license_sro":
        return any(marker in text for marker in ("сро", "лиценз", "саморегулируем"))
    if family == "contract_security":
        return any(marker in text for marker in ("обеспечение исполнения", "независим", "гарант"))
    tokens = _meaningful_label_tokens(label)
    if not tokens:
        return True
    if "/" in label or len(tokens) == 1:
        return any(token in text for token in tokens)
    return all(token in text for token in tokens)


def _meaningful_label_tokens(label: str) -> list[str]:
    tokens = _dedupe_text(label).split()
    return [token for token in tokens if len(token) >= 4]


def _description_is_only_label(description: str, label: str) -> bool:
    return _dedupe_text(description) == _dedupe_text(label)


def _int_metric(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _dedupe_text(value: Any) -> str:
    return re.sub(r"\s+", " ", _text(value)).strip().casefold()


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()
