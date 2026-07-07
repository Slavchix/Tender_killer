from __future__ import annotations

import re
from typing import Any

from tender_killer.analysis_fact_source_service import evidence_sources as _evidence_sources
from tender_killer.analysis_fact_source_service import page_number as _page_number
from tender_killer.analysis_fact_source_service import source_label as _source_label
from tender_killer.analysis_types import AnalysisFact
from tender_killer.analysis_types import EvidenceQuality
from tender_killer.analysis_types import SourceBinding


BLOCKER_CATEGORIES = {"legal", "national_regime"}
PRICE_FACTOR_CATEGORIES = {"acceptance", "contract", "delivery", "financial", "payment", "standards"}
SUPPLIER_DOCUMENT_CATEGORIES = {"documents", "standards"}


def build_fact(
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
    semantic_key: str = "",
) -> AnalysisFact:
    bound_document = _text(document_name)
    page_number = _page_number(source_page)
    needs_review = bool(fragment and not bound_document)
    if needs_review:
        bound_document = "Документ не привязан"
    display_source_label = _text(source_label) or (bound_document if needs_review else _source_label(bound_document, page_number))
    operator = _operator_metadata(kind, category, severity, is_blocker, is_price_factor, needs_review)
    source_binding = _source_binding(
        document_name=bound_document,
        source_label=display_source_label,
        source_context=source_context,
        fragment=fragment,
        needs_review=needs_review,
    )
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
        "source_binding": source_binding,
        "confidence_level": _confidence_level(
            confidence=_confidence(confidence),
            source_binding_level=source_binding["level"],
            has_fragment=bool(fragment),
            has_context=bool(_text(source_context)),
        ),
        "is_blocker": is_blocker,
        "is_price_factor": is_price_factor,
        "needs_review": needs_review,
        "impact": impact,
        "semantic_key": semantic_key,
        "related_labels": [label],
        "evidence_sources": _evidence_sources(bound_document, display_source_label, fragment),
        **_clean_metadata(metadata),
        **operator,
    }


def _source_binding(
    *,
    document_name: str,
    source_label: str,
    source_context: str,
    fragment: str,
    needs_review: bool,
) -> SourceBinding:
    if needs_review:
        return {
            "level": "unbound",
            "label": "нужна ручная проверка",
            "detail": "Факт не удалось надежно связать с документом.",
            "document_name": document_name,
            "source_label": source_label,
        }
    if document_name and fragment:
        return {
            "level": "explicit",
            "label": "источник подтвержден",
            "detail": "Факт найден в документе и связан с фрагментом текста.",
            "document_name": document_name,
            "source_label": source_label,
        }
    if document_name or source_context:
        return {
            "level": "context",
            "label": "источник по контексту",
            "detail": "Факт связан с документом или контекстом, но требует быстрой сверки формулировки.",
            "document_name": document_name,
            "source_label": source_label,
        }
    return {
        "level": "inferred",
        "label": "вывод без источника",
        "detail": "Факт получен из анализа без точной документальной привязки.",
        "document_name": document_name,
        "source_label": source_label,
    }


def _clean_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not metadata:
        return {}
    return {key: value for key, value in metadata.items() if value not in (None, "")}


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


def _confidence(value: Any) -> float | None:
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _confidence_level(
    *,
    confidence: float | None,
    source_binding_level: str,
    has_fragment: bool,
    has_context: bool,
) -> EvidenceQuality:
    if source_binding_level == "unbound":
        return {
            "level": "low",
            "label": "уверенность низкая",
            "detail": "Нет надежной привязки к документу, нужна ручная проверка.",
        }
    if source_binding_level == "explicit" and has_fragment and has_context:
        return {
            "level": "high",
            "label": "уверенность высокая",
            "detail": "Есть документ, фрагмент и контекст источника.",
        }
    if confidence is not None and confidence >= 0.85 and source_binding_level == "explicit":
        return {
            "level": "high",
            "label": "уверенность высокая",
            "detail": "Есть документальная привязка и высокая общая уверенность анализа.",
        }
    if source_binding_level in {"explicit", "context"}:
        return {
            "level": "medium",
            "label": "уверенность средняя",
            "detail": "Есть источник или контекст, но формулировку стоит сверить вручную.",
        }
    return {
        "level": "low",
        "label": "уверенность низкая",
        "detail": "Вывод сделан без точного источника.",
    }


def _slug(value: str) -> str:
    normalized = re.sub(r"\s+", "-", value.strip().casefold())
    normalized = re.sub(r"[^0-9a-zа-яё_-]+", "", normalized)
    return normalized or "fact"


def _text(value: Any) -> str:
    if value in (None, ""):
        return ""
    return str(value).strip()
