from __future__ import annotations

from pathlib import Path

from tender_killer.analysis_operator_view_service import build_analysis_operator_view


def _section(view: dict, section_id: str) -> dict:
    return next(section for section in view["sections"] if section["id"] == section_id)


def _analysis_items(section: dict) -> list[dict]:
    return [item for item in section["items"] if item.get("type") not in {"document", "document_summary"}]


def test_operator_view_drops_empty_cards_and_keeps_best_semantic_duplicate():
    analysis = {
        "summary": "Поставка бумаги",
        "status": "needs_review",
        "confidence": 0.9,
        "analysis_facts": {
            "version": 1,
            "metrics": {"total": 8, "blockers": 4, "price_factors": 0, "unbound": 0},
            "items": [
                {
                    "kind": "subject",
                    "label": "Предмет",
                    "value": "Поставка бумаги",
                    "category": "subject",
                    "severity": "medium",
                },
                {
                    "kind": "blocker",
                    "label": "национальный режим/страна происхождения",
                    "value": "национальный режим/страна происхождения",
                    "category": "legal",
                    "severity": "high",
                    "is_blocker": True,
                },
                {
                    "kind": "blocker",
                    "label": "страна происхождения товара",
                    "value": "Заявка должна содержать страну происхождения товара.",
                    "category": "national_regime",
                    "severity": "high",
                    "document_name": "Описание объекта закупки.docx",
                    "source_label": "Описание объекта закупки.docx · стр. 2",
                    "source_context": "Заявка должна содержать наименование страны происхождения товара.",
                    "fragment": "Заявка должна содержать наименование страны происхождения товара.",
                    "is_blocker": True,
                },
                {
                    "kind": "blocker",
                    "label": "лицензия/СРО",
                    "value": "лицензия/СРО",
                    "category": "legal",
                    "severity": "high",
                    "is_blocker": True,
                },
                {
                    "kind": "requirement",
                    "label": "членство в СРО",
                    "value": "Участник предоставляет подтверждение членства в СРО.",
                    "category": "legal",
                    "severity": "high",
                    "document_name": "Контракт.docx",
                    "source_label": "Контракт.docx · стр. 4",
                    "source_context": "Участник предоставляет подтверждение членства в СРО.",
                    "fragment": "Участник предоставляет подтверждение членства в СРО.",
                    "is_blocker": True,
                },
                {
                    "kind": "requirement",
                    "label": "сертификат/декларация",
                    "value": "сертификат/декларация",
                    "category": "general",
                    "severity": "medium",
                },
                {
                    "kind": "requirement",
                    "label": "температурный режим хранения",
                    "value": "температурный режим хранения",
                    "category": "general",
                    "severity": "medium",
                },
                {
                    "kind": "requirement",
                    "label": "приемка через ЕИС",
                    "value": "приемка через ЕИС",
                    "category": "general",
                    "severity": "medium",
                },
                {
                    "kind": "requirement",
                    "label": "монтаж/пусконаладка",
                    "value": "Цена контракта является твердой на весь срок исполнения.",
                    "category": "delivery",
                    "severity": "medium",
                    "source_label": "Документ не привязан",
                    "fragment": "Цена контракта является твердой на весь срок исполнения.",
                },
            ],
        },
    }

    view = build_analysis_operator_view(analysis, [])

    decision_items = _analysis_items(_section(view, "decision_risks"))
    product_items = _analysis_items(_section(view, "product_compliance"))
    all_labels = [item["label"] for section in view["sections"] for item in _analysis_items(section)]

    assert [item["label"] for item in decision_items] == [
        "лицензия/СРО",
        "национальный режим/страна происхождения",
    ]
    assert [item["source_label"] for item in decision_items] == [
        "Контракт.docx · стр. 4",
        "Описание объекта закупки.docx · стр. 2",
    ]
    assert [item["label"] for item in product_items] == ["Предмет"]
    assert "сертификат/декларация" not in all_labels
    assert "температурный режим хранения" not in all_labels
    assert "приемка через ЕИС" not in all_labels
    assert "монтаж/пусконаладка" not in all_labels
    assert view["metrics"]["facts"] == 3
    assert _section(view, "decision_risks")["count"] == 2
    assert _section(view, "product_compliance")["count"] == 1


def test_frontend_operator_view_filters_cards_before_counting():
    source = Path("web/src/TenderAnalysisSections.jsx").read_text(encoding="utf-8")

    assert "displayableAnalysisItems(section.items)" in source
    assert "count: analysisItemCount(items)" in source
    assert "function isDisplayableAnalysisItem" in source
    assert "analysisItemQuality(item) > 0" in source
    assert "operator_action" not in source[source.index("function analysisItemQuality") : source.index("function semanticAnalysisItemKey")]
