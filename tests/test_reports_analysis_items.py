from __future__ import annotations

from tender_killer.reports_analysis_items import item_source_text
from tender_killer.reports_analysis_items import operator_feedback_text
from tender_killer.reports_analysis_items import report_item_action
from tender_killer.reports_analysis_items import report_item_found
from tender_killer.reports_analysis_items import report_item_impact
from tender_killer.reports_analysis_items import report_item_meaning


def test_report_analysis_item_uses_structured_interpretation_and_operator_feedback():
    item = {
        "label": "Оплата",
        "value": "legacy value",
        "description": "legacy description",
        "impact": "legacy impact",
        "operator_action": "legacy action",
        "source_label": "Проект контракта.docx",
        "fragment": "Оплата производится в течение 15 рабочих дней.",
        "feedback_label": "неверно",
        "feedback_comment": "в контракте срок 10 дней",
        "interpretation": {
            "found": "Оплата 15 рабочих дней",
            "meaning": "Платеж после приемки",
            "impact": "Нужен запас оборотки",
            "action": "Сверить срок оплаты с ПИК",
        },
    }

    assert report_item_found(item) == "Оплата 15 рабочих дней"
    assert report_item_meaning(item) == "Платеж после приемки"
    assert report_item_impact(item) == "Нужен запас оборотки"
    assert operator_feedback_text(item) == "неверно: в контракте срок 10 дней"
    assert report_item_action(item) == "Сверить срок оплаты с ПИК Оператор: неверно: в контракте срок 10 дней"
    assert item_source_text(item) == "Проект контракта.docx: Оплата производится в течение 15 рабочих дней."
