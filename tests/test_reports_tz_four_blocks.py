from __future__ import annotations

from tender_killer.reports_tz_four_blocks import analysis_four_block_elements


def test_analysis_four_block_elements_builds_rows_from_operator_view_and_supplemental_checklist():
    operator_view = {
        "major_blocks": [
            {
                "id": "decision_risks",
                "title": "Итог и риски",
                "empty": "Блокеров не найдено.",
                "items": [
                    {
                        "label": "Аванс",
                        "priority": 1,
                        "source_label": "Проект контракта.docx",
                        "fragment": "Предусмотрен аванс 30%.",
                        "feedback_label": "требует ручной проверки",
                        "interpretation": {
                            "found": "Аванс 30%",
                            "meaning": "Условия оплаты противоречат ТЗ",
                            "impact": "Нужно уточнить условия участия",
                            "action": "Проверить аванс до расчета",
                        },
                    }
                ],
            },
            {"id": "product_compliance", "title": "Товар и документы", "empty": "Нет данных.", "items": []},
            {"id": "fulfillment_terms", "title": "Поставка и исполнение", "empty": "Нет данных.", "items": []},
            {"id": "acceptance_payment", "title": "Приемка, документы и оплата", "empty": "Нет данных.", "items": []},
        ]
    }
    analysis = {
        "checklist": [
            {
                "label": "Оплата",
                "category": "payment",
                "severity": "medium",
                "evidence": "Оплата в течение 15 рабочих дней.",
                "document_name": "ПИК.docx",
            }
        ]
    }

    elements = analysis_four_block_elements(operator_view, analysis)

    assert elements[0] == ("p", "Анализ ТЗ: 4 блока", "heading")
    assert elements[1][0] == "table"
    assert elements[1][2] == "analysis"
    rows = elements[1][1]
    assert rows[0] == ["Блок", "Пункт", "Что найдено", "Что означает", "Влияние", "Что сделать", "Источник", "Оператор"]
    assert [
        "Итог и риски",
        "Аванс",
        "Аванс 30%",
        "Условия оплаты противоречат ТЗ",
        "Нужно уточнить условия участия",
        "Проверить аванс до расчета Оператор: требует ручной проверки",
        "Проект контракта.docx: Предусмотрен аванс 30%.",
        "требует ручной проверки",
    ] in rows
    assert any(row[0] == "Приемка, документы и оплата" and row[1] == "Оплата" for row in rows)
