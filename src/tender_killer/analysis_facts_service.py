from __future__ import annotations

import re
from typing import Any


BLOCKER_CATEGORIES = {"legal", "national_regime"}
PRICE_FACTOR_CATEGORIES = {"acceptance", "contract", "delivery", "financial", "payment", "standards"}
SUPPLIER_DOCUMENT_CATEGORIES = {"documents", "standards"}


def build_analysis_facts(
    analysis: dict[str, Any] | None,
    documents: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the compact fact layer used by UI, economics, reports, and future agents."""
    document_rows = documents or []
    if not isinstance(analysis, dict):
        return {"version": 1, "items": [], "metrics": _metrics([])}

    items: list[dict[str, Any]] = []
    summary = _text(analysis.get("summary"))
    if summary:
        items.append(
            _fact(
                kind="subject",
                label="Предмет",
                value=summary,
                category="subject",
                severity="medium",
                confidence=analysis.get("confidence"),
                rule_id="summary",
            )
        )

    for item in _dict_items(analysis.get("execution_terms")):
        items.append(_execution_term_fact(item, analysis, document_rows))

    for item in _dict_items(analysis.get("checklist")):
        items.append(_checklist_fact(item, analysis, document_rows))

    items = _dedupe_items(items)
    return {"version": 1, "items": items, "metrics": _metrics(items)}


def _checklist_fact(
    item: dict[str, Any],
    analysis: dict[str, Any],
    documents: list[dict[str, Any]],
) -> dict[str, Any]:
    label = _text(item.get("label")) or "Условие"
    category = _text(item.get("category")) or "general"
    severity = _text(item.get("severity")) or "medium"
    fragment = _text(item.get("evidence") or item.get("value"))
    is_blocker = severity == "high" or category in BLOCKER_CATEGORIES
    is_price_factor = category in PRICE_FACTOR_CATEGORIES and not is_blocker
    kind = "blocker" if is_blocker else "supplier_document" if category in SUPPLIER_DOCUMENT_CATEGORIES else "requirement"
    return _fact(
        kind=kind,
        label=label,
        value=fragment or label,
        category=category,
        severity=severity,
        confidence=analysis.get("confidence"),
        rule_id=f"checklist:{label}",
        fragment=fragment,
        document_name=_resolve_document_name(item, fragment, documents),
        is_blocker=is_blocker,
        is_price_factor=is_price_factor,
        impact=_impact(category, severity),
    )


def _execution_term_fact(
    item: dict[str, Any],
    analysis: dict[str, Any],
    documents: list[dict[str, Any]],
) -> dict[str, Any]:
    label = _text(item.get("label")) or "Условие исполнения"
    category = _text(item.get("category")) or "general"
    severity = _text(item.get("severity")) or "medium"
    fragment = _text(item.get("evidence") or item.get("value"))
    term_type = _text(item.get("type")) or _slug(label)
    is_blocker = severity == "high" and category in {"financial", "legal", "national_regime"}
    is_price_factor = category in PRICE_FACTOR_CATEGORIES
    return _fact(
        kind="blocker" if is_blocker else "execution_term",
        label=label,
        value=_text(item.get("value")) or fragment or label,
        category=category,
        severity=severity,
        confidence=analysis.get("confidence"),
        rule_id=f"execution_term:{term_type}",
        fragment=fragment,
        document_name=_resolve_document_name(item, fragment, documents),
        is_blocker=is_blocker,
        is_price_factor=is_price_factor,
        impact=_impact(category, severity),
    )


def _fact(
    *,
    kind: str,
    label: str,
    value: str,
    category: str,
    severity: str,
    confidence: Any,
    rule_id: str,
    fragment: str = "",
    document_name: str = "",
    is_blocker: bool = False,
    is_price_factor: bool = False,
    impact: str = "",
) -> dict[str, Any]:
    bound_document = _text(document_name)
    needs_review = bool(fragment and not bound_document)
    if needs_review:
        bound_document = "Документ не привязан"
    return {
        "id": f"{kind}:{_slug(label)}",
        "kind": kind,
        "label": label,
        "value": value,
        "category": category,
        "severity": severity,
        "confidence": _confidence(confidence),
        "rule_id": rule_id,
        "document_name": bound_document,
        "source": bound_document,
        "fragment": fragment,
        "is_blocker": is_blocker,
        "is_price_factor": is_price_factor,
        "needs_review": needs_review,
        "impact": impact,
    }


def _resolve_document_name(item: dict[str, Any], fragment: str, documents: list[dict[str, Any]]) -> str:
    explicit = _text(item.get("document_name") or item.get("source"))
    if explicit:
        return explicit
    needle = _normalized_text(fragment)
    if not needle:
        return ""
    for document in documents:
        haystack = _normalized_text(document.get("text_content"))
        if needle in haystack:
            return _text(document.get("name") or document.get("url"))
    return ""


def _metrics(items: list[dict[str, Any]]) -> dict[str, int]:
    actionable = [item for item in items if item.get("kind") != "subject"]
    return {
        "total": len(items),
        "blockers": sum(1 for item in actionable if item.get("is_blocker")),
        "price_factors": sum(1 for item in actionable if item.get("is_price_factor")),
        "unbound": sum(1 for item in actionable if item.get("needs_review")),
    }


def _dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, Any]] = []
    for item in items:
        if item.get("kind") == "subject":
            unique.append(item)
            continue
        key = (_dedupe_text(item.get("fragment") or item.get("value")), _text(item.get("category")))
        if key[0] and key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _impact(category: str, severity: str) -> str:
    if severity == "high" and category in BLOCKER_CATEGORIES:
        return "Проверить до участия: может повлиять на возможность участия."
    if severity == "high":
        return "Проверить до участия и заложить в решение или экономику."
    if category in SUPPLIER_DOCUMENT_CATEGORIES:
        return "Проверить наличие документа у поставщика или подготовить подтверждение."
    if category in PRICE_FACTOR_CATEGORIES:
        return "Учесть в сроках, резерве, стоп-цене или договорной подготовке."
    return "Проверить перед принятием решения."


def _dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _confidence(value: Any) -> float | None:
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _normalized_text(value: Any) -> str:
    return re.sub(r"\s+", " ", _text(value)).strip().casefold()


def _dedupe_text(value: Any) -> str:
    text = re.sub(r"[^\wа-яА-ЯёЁ]+", " ", _text(value), flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip().casefold()


def _slug(value: str) -> str:
    normalized = re.sub(r"\s+", "-", value.strip().casefold())
    normalized = re.sub(r"[^0-9a-zа-яё_-]+", "", normalized)
    return normalized or "fact"


def _text(value: Any) -> str:
    if value in (None, ""):
        return ""
    return str(value).strip()
