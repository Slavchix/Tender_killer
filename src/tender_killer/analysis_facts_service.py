from __future__ import annotations

import re
from typing import Any

from tender_killer.analysis_source_service import document_source_for_fragment
from tender_killer.analysis_text_index_service import document_roles_from_text_index
from tender_killer.analysis_text_index_service import infer_document_role


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
    document_roles = _document_roles(analysis, document_rows)
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
        items.append(_execution_term_fact(item, analysis, document_rows, document_roles))

    for item in _dict_items(analysis.get("checklist")):
        items.append(_checklist_fact(item, analysis, document_rows, document_roles))

    items = _dedupe_items(items)
    return {"version": 1, "items": items, "metrics": _metrics(items)}


def _checklist_fact(
    item: dict[str, Any],
    analysis: dict[str, Any],
    documents: list[dict[str, Any]],
    document_roles: dict[str, str],
) -> dict[str, Any]:
    label = _text(item.get("label")) or "Условие"
    category = _text(item.get("category")) or "general"
    severity = _text(item.get("severity")) or "medium"
    fragment = _text(item.get("evidence") or item.get("value"))
    is_blocker = severity == "high" or category in BLOCKER_CATEGORIES
    is_price_factor = category in PRICE_FACTOR_CATEGORIES and not is_blocker
    kind = "blocker" if is_blocker else "supplier_document" if category in SUPPLIER_DOCUMENT_CATEGORIES else "requirement"
    source = _document_source(item, fragment, documents)
    document_name = _text(source.get("document_name"))
    structured = _structured_metadata(
        label=label,
        category=category,
        term_type="checklist",
        text=fragment or label,
        document_name=document_name,
        document_roles=document_roles,
    )
    return _fact(
        kind=kind,
        label=label,
        value=fragment or label,
        category=category,
        severity=severity,
        confidence=analysis.get("confidence"),
        rule_id=f"checklist:{label}",
        fragment=fragment,
        document_name=document_name,
        source_page=source.get("source_page"),
        source_label=source.get("source_label", ""),
        source_context=source.get("source_context", ""),
        is_blocker=is_blocker,
        is_price_factor=is_price_factor,
        impact=_impact(category, severity),
        metadata=structured,
    )


def _execution_term_fact(
    item: dict[str, Any],
    analysis: dict[str, Any],
    documents: list[dict[str, Any]],
    document_roles: dict[str, str],
) -> dict[str, Any]:
    label = _text(item.get("label")) or "Условие исполнения"
    category = _text(item.get("category")) or "general"
    severity = _text(item.get("severity")) or "medium"
    fragment = _text(item.get("evidence") or item.get("value"))
    term_type = _text(item.get("type")) or _slug(label)
    is_blocker = severity == "high" and category in {"financial", "legal", "national_regime"}
    is_price_factor = category in PRICE_FACTOR_CATEGORIES
    source = _document_source(item, fragment, documents)
    document_name = _text(source.get("document_name"))
    value = _text(item.get("value")) or fragment or label
    structured = _structured_metadata(
        label=label,
        category=category,
        term_type=term_type,
        text=" ".join(part for part in (value, fragment) if part),
        document_name=document_name,
        document_roles=document_roles,
    )
    return _fact(
        kind="blocker" if is_blocker else "execution_term",
        label=label,
        value=value,
        category=category,
        severity=severity,
        confidence=analysis.get("confidence"),
        rule_id=f"execution_term:{term_type}",
        fragment=fragment,
        document_name=document_name,
        source_page=source.get("source_page"),
        source_label=source.get("source_label", ""),
        source_context=source.get("source_context", ""),
        is_blocker=is_blocker,
        is_price_factor=is_price_factor,
        impact=_impact(category, severity),
        metadata=structured,
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
    source_page: Any = None,
    source_label: str = "",
    source_context: str = "",
    is_blocker: bool = False,
    is_price_factor: bool = False,
    impact: str = "",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    bound_document = _text(document_name)
    page_number = _page_number(source_page)
    needs_review = bool(fragment and not bound_document)
    if needs_review:
        bound_document = "Документ не привязан"
    display_source_label = _text(source_label) or (bound_document if needs_review else _source_label(bound_document, page_number))
    operator = _operator_metadata(kind, category, severity, is_blocker, is_price_factor, needs_review)
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
        "source_page": page_number,
        "source_label": display_source_label,
        "source_context": _text(source_context),
        "fragment": fragment,
        "is_blocker": is_blocker,
        "is_price_factor": is_price_factor,
        "needs_review": needs_review,
        "impact": impact,
        **_clean_metadata(metadata),
        **operator,
    }


def _document_roles(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> dict[str, str]:
    roles = document_roles_from_text_index(analysis.get("text_index"))
    for document in documents:
        name = _text(document.get("name") or document.get("url"))
        if name:
            roles.setdefault(name, infer_document_role(document))
    return roles


def _structured_metadata(
    *,
    label: str,
    category: str,
    term_type: str,
    text: str,
    document_name: str,
    document_roles: dict[str, str],
) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    role = _text(document_roles.get(document_name))
    if role:
        metadata["document_role"] = role

    stage = _document_stage(label=label, category=category, text=text)
    if stage:
        metadata["document_stage"] = stage

    amount_percent = _amount_percent(text)
    if amount_percent is not None:
        metadata["amount_percent"] = amount_percent
        amount_type = _amount_type(label=label, category=category, term_type=term_type, text=text)
        if amount_type:
            metadata["amount_type"] = amount_type

    days = _days(text)
    if days is not None:
        metadata["days"] = days
        deadline_type = _deadline_type(label=label, category=category, term_type=term_type, text=text)
        if deadline_type:
            metadata["deadline_type"] = deadline_type

    responsible_party = _responsible_party(text) or ("supplier" if category == "delivery" else "")
    if responsible_party:
        metadata["responsible_party"] = responsible_party

    return metadata


def _clean_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not metadata:
        return {}
    return {key: value for key, value in metadata.items() if value not in (None, "")}


def _amount_percent(text: str) -> int | float | None:
    match = re.search(r"(\d+(?:[,.]\d+)?)\s*(?:%|процент(?:а|ов)?)", text, flags=re.IGNORECASE)
    if not match:
        return None
    raw_value = match.group(1).replace(",", ".")
    value = float(raw_value)
    return int(value) if value.is_integer() else value


def _amount_type(*, label: str, category: str, term_type: str, text: str) -> str:
    combined = _normalized_text(" ".join((label, category, term_type, text)))
    if "обеспечение исполнения" in combined or term_type == "contract_security":
        return "contract_security"
    if "аванс" in combined:
        return "advance"
    if "штраф" in combined or "пени" in combined or "пеня" in combined:
        return "penalty"
    if category in {"financial", "payment"}:
        return "financial_condition"
    return ""


def _days(text: str) -> int | None:
    patterns = (
        r"(?:в течение|не позднее|срок[^.]{0,80}?)(\d{1,3})\s*(?:рабочих|календарных)?\s*дн",
        r"(\d{1,3})\s*(?:рабочих|календарных)?\s*дн",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def _deadline_type(*, label: str, category: str, term_type: str, text: str) -> str:
    combined = _normalized_text(" ".join((label, category, term_type, text)))
    if category == "delivery" or "поставк" in combined or term_type == "delivery_deadline":
        return "delivery"
    if category == "payment" or "оплат" in combined:
        return "payment"
    if category == "acceptance" or "приемк" in combined or "приёмк" in combined:
        return "acceptance"
    if "устран" in combined and "замечан" in combined:
        return "correction"
    return ""


def _responsible_party(text: str) -> str:
    combined = _normalized_text(text)
    if any(marker in combined for marker in ("поставщик", "поставщиком", "исполнитель", "исполнителем")):
        return "supplier"
    if any(marker in combined for marker in ("заказчик", "заказчиком")):
        return "customer"
    return ""


def _document_stage(*, label: str, category: str, text: str) -> str:
    combined = _normalized_text(" ".join((label, category, text)))
    if category in {"national_regime", "legal", "qualification"} or "заявк" in combined or "участ" in combined:
        return "bid"
    if category == "documents":
        if any(marker in combined for marker in ("приемк", "приёмк", "поставк", "товар")):
            return "delivery_or_acceptance"
        return "preparation"
    if category == "delivery" or "поставк" in combined:
        return "delivery"
    if category in {"acceptance", "payment"} or "приемк" in combined or "приёмк" in combined:
        return "acceptance"
    if category in {"financial", "contract"}:
        return "contract_execution"
    return ""


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


def _document_source(item: dict[str, Any], fragment: str, documents: list[dict[str, Any]]) -> dict[str, Any]:
    explicit_document = _text(item.get("document_name") or item.get("source"))
    explicit_source = {
        "document_name": explicit_document,
        "source_page": item.get("source_page"),
        "source_label": _text(item.get("source_label")),
        "source_context": _text(item.get("source_context")),
    }
    if (
        explicit_source["document_name"]
        and (explicit_source["source_page"] not in (None, "") or explicit_source["source_context"])
    ):
        return explicit_source

    matched = document_source_for_fragment(fragment, documents)
    if matched:
        return {
            "document_name": _text(matched.get("document_name")),
            "source_page": matched.get("source_page"),
            "source_label": _text(matched.get("source_label")),
            "source_context": _text(matched.get("source_context")),
        }

    if explicit_document:
        return explicit_source
    return {
        "document_name": _resolve_document_name(item, fragment, documents),
        "source_page": item.get("source_page"),
        "source_label": _text(item.get("source_label")),
        "source_context": _text(item.get("source_context")),
    }


def _page_number(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        page = int(value)
    except (TypeError, ValueError):
        return None
    return page if page > 0 else None


def _source_label(document_name: str, page_number: int | None) -> str:
    if not document_name:
        return ""
    if page_number is None:
        return f"{document_name} · стр. не определена"
    return f"{document_name} · стр. {page_number}"


def _metrics(items: list[dict[str, Any]]) -> dict[str, int]:
    actionable = [item for item in items if item.get("kind") != "subject"]
    return {
        "total": len(items),
        "blockers": sum(1 for item in actionable if item.get("is_blocker")),
        "price_factors": sum(1 for item in actionable if item.get("is_price_factor")),
        "unbound": sum(1 for item in actionable if item.get("needs_review")),
    }


def _dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: list[tuple[str, str, str]] = []
    unique: list[dict[str, Any]] = []
    for item in items:
        if item.get("kind") == "subject":
            unique.append(item)
            continue
        label_key = _dedupe_text(item.get("label"))
        fragment_key = _dedupe_text(item.get("fragment") or item.get("value"))
        category_key = _text(item.get("category"))
        if _seen_equivalent_fact(seen, label_key, fragment_key, category_key):
            continue
        seen.append((label_key, fragment_key, category_key))
        unique.append(item)
    return unique


def _seen_equivalent_fact(
    seen: list[tuple[str, str, str]],
    label: str,
    fragment: str,
    category: str,
) -> bool:
    for seen_label, seen_fragment, seen_category in seen:
        if not fragment or fragment != seen_fragment or category != seen_category:
            continue
        if label == seen_label or label in seen_label or seen_label in label:
            return True
    return False


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


def _operator_metadata(
    kind: str,
    category: str,
    severity: str,
    is_blocker: bool,
    is_price_factor: bool,
    needs_review: bool,
) -> dict[str, Any]:
    if needs_review:
        return {
            "operator_group": "manual_review",
            "operator_action": "Проверить источник факта вручную.",
            "price_impact": _price_impact(category),
            "priority": 95,
        }
    if kind == "subject":
        return {
            "operator_group": "overview",
            "operator_action": "Сверить предмет закупки.",
            "price_impact": "none",
            "priority": 10,
        }
    if is_blocker:
        return {
            "operator_group": "blocker",
            "operator_action": "Проверить допустимость участия до расчета.",
            "price_impact": _price_impact(category),
            "priority": 90 if severity == "high" else 80,
        }
    if kind == "execution_term":
        return {
            "operator_group": "execution",
            "operator_action": _execution_action(category),
            "price_impact": _price_impact(category),
            "priority": 60 if is_price_factor else 45,
        }
    if kind in {"supplier_document", "requirement"}:
        return {
            "operator_group": "prepare",
            "operator_action": _prepare_action(category),
            "price_impact": _price_impact(category),
            "priority": 50 if category in SUPPLIER_DOCUMENT_CATEGORIES else 45,
        }
    if is_price_factor:
        return {
            "operator_group": "price",
            "operator_action": "Заложить условие в экономику.",
            "price_impact": _price_impact(category),
            "priority": 55,
        }
    return {
        "operator_group": "review",
        "operator_action": "Проверить факт перед решением.",
        "price_impact": _price_impact(category),
        "priority": 40,
    }


def _execution_action(category: str) -> str:
    if category == "delivery":
        return "Проверить срок исполнения и заложить логистику."
    if category in {"financial", "payment"}:
        return "Проверить денежные условия и нагрузку на оборотку."
    if category == "acceptance":
        return "Проверить приемку и закрывающие документы."
    if category == "contract":
        return "Проверить договорные обязательства."
    return "Проверить условие исполнения договора."


def _prepare_action(category: str) -> str:
    if category in SUPPLIER_DOCUMENT_CATEGORIES:
        return "Подготовить подтверждающие документы."
    if category in BLOCKER_CATEGORIES:
        return "Проверить требование до участия."
    return "Подготовить ответ по требованию ТЗ."


def _price_impact(category: str) -> str:
    if category == "delivery":
        return "logistics"
    if category in {"financial", "payment", "acceptance"}:
        return "working_capital"
    if category == "documents":
        return "documents"
    if category == "contract":
        return "reserve"
    if category in {"legal", "national_regime", "standards"}:
        return "compliance"
    return "none"


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
