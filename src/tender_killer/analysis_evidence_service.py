from __future__ import annotations

from typing import Any

from tender_killer.analysis_source_service import document_source_for_fragment


def build_analysis_evidence_items(
    analysis: dict[str, Any] | None,
    documents: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    checklist = analysis.get("checklist") if isinstance(analysis, dict) else []
    if not isinstance(checklist, list):
        return []

    document_rows = documents or []
    items: list[dict[str, str]] = []
    for index, item in enumerate(checklist):
        if not isinstance(item, dict) or not item.get("evidence"):
            continue
        label = _text(item.get("label"), "Фрагмент документа")
        category = _text(item.get("category"), "general")
        severity = _text(item.get("severity"), "medium")
        fragment = _text(item.get("evidence"), "")
        source = _evidence_source(item, fragment, document_rows)
        evidence_item = {
            "id": f"{label}-{index}",
            "label": label,
            "category": category,
            "severity": severity,
            "type_label": evidence_type_label(category),
            "importance_label": evidence_importance_label(severity),
            "document_name": source["document_name"],
            "fragment": fragment,
            "impact": evidence_impact_label(item),
        }
        if source.get("source_page") not in (None, ""):
            evidence_item["source_page"] = source["source_page"]
        if source.get("source_label"):
            evidence_item["source_label"] = source["source_label"]
        if source.get("source_context"):
            evidence_item["source_context"] = source["source_context"]
        items.append(evidence_item)
    return items


def evidence_type_label(category: Any) -> str:
    return {
        "documents": "Документы",
        "delivery": "Сроки и поставка",
        "acceptance": "Приемка",
        "standards": "ГОСТ/ТУ",
        "contract": "Контракт",
        "financial": "Финансы",
        "national_regime": "Нацрежим",
        "legal": "Юридическое",
    }.get(str(category or ""), "Условие")


def evidence_importance_label(severity: Any) -> str:
    return {
        "high": "важно",
        "medium": "проверить",
        "low": "к сведению",
    }.get(str(severity or ""), "проверить")


def evidence_impact_label(item: dict[str, Any]) -> str:
    if item.get("severity") == "high":
        return "Может повлиять на решение, цену или возможность участия."
    return {
        "documents": "Проверьте, какие документы нужно приложить или получить у поставщика.",
        "delivery": "Сверьте сроки с доступностью товара и логистикой.",
        "acceptance": "Учтите порядок приемки при оценке исполнения.",
        "standards": "Сверьте соответствие товара стандартам до расчета экономики.",
        "contract": "Учтите условие в рисках исполнения и договорной подготовке.",
        "financial": "Учтите в стоп-цене, резерве и решении по участию.",
        "national_regime": "Проверьте ограничения происхождения и реестровые требования.",
        "legal": "Проверьте допуски, лицензии или ограничения до участия.",
    }.get(str(item.get("category") or ""), "Проверьте фрагмент перед принятием решения.")


def resolve_evidence_document_name(item: dict[str, Any], documents: list[dict[str, Any]]) -> str:
    if item.get("document_name"):
        return _text(item.get("document_name"), "Документ")
    if item.get("source"):
        return _text(item.get("source"), "Документ")

    ready_documents = [document for document in documents if document.get("text_status") == "ok"]
    if len(ready_documents) == 1:
        return _text(ready_documents[0].get("name") or ready_documents[0].get("url"), "Документ")
    return "Документ не привязан"


def _evidence_source(item: dict[str, Any], fragment: str, documents: list[dict[str, Any]]) -> dict[str, Any]:
    explicit = {
        "document_name": resolve_evidence_document_name(item, documents),
        "source_page": item.get("source_page"),
        "source_label": _text(item.get("source_label"), ""),
        "source_context": _text(item.get("source_context"), ""),
    }
    if explicit["source_label"] or explicit["source_context"] or explicit["source_page"] not in (None, ""):
        return explicit

    matched = document_source_for_fragment(fragment, documents)
    if matched:
        return {
            "document_name": _text(matched.get("document_name"), explicit["document_name"]),
            "source_page": matched.get("source_page"),
            "source_label": _text(matched.get("source_label"), ""),
            "source_context": _text(matched.get("source_context"), ""),
        }
    return explicit


def _text(value: Any, fallback: str) -> str:
    if value in (None, ""):
        return fallback
    return str(value)
