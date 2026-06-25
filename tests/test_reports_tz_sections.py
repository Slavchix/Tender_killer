from __future__ import annotations

from tender_killer.reports_tz_sections import analysis_management_brief_elements
from tender_killer.reports_tz_sections import analysis_history_elements
from tender_killer.reports_tz_sections import analysis_saas_elements
from tender_killer.reports_tz_sections import analysis_tz_passport_elements


def test_analysis_tz_passport_elements_builds_passport_tables_from_analysis_contract():
    analysis = {
        "tz_passport": {
            "version": 2,
            "title": "Поставка огнетушителей",
            "status": "needs_review",
            "confidence": 0.82,
            "summary_block": {
                "title": "Поставка огнетушителей",
            },
            "sections": [
                {
                    "id": "payment_acceptance",
                    "title": "Оплата и приемка",
                    "items": [
                        {
                            "label": "Условия оплаты",
                            "value": "100% по факту поставки",
                            "source": "Проект контракта.docx",
                            "impact": "Влияет на оборотку",
                        }
                    ],
                }
            ],
        }
    }

    elements = analysis_tz_passport_elements(analysis, [])

    assert elements[0] == ("p", "Паспорт ТЗ", "heading")
    assert elements[1] == (
        "table",
        [
            ["Предмет", "Поставка огнетушителей"],
            ["Статус", "Нужна проверка"],
            ["Уверенность", "82%"],
        ],
        "",
    )
    assert elements[2] == (
        "table",
        [
            ["Раздел", "Условие", "Значение", "Источник", "Влияние"],
            [
                "Оплата и приемка",
                "Условия оплаты",
                "100% по факту поставки",
                "Проект контракта.docx",
                "Влияет на оборотку",
            ],
        ],
        "",
    )


def test_analysis_management_brief_elements_builds_operator_brief_from_passport_and_view():
    analysis = {
        "tz_passport": {
            "version": 2,
            "title": "Поставка бумаги",
            "subject": "Офисная бумага",
            "summary_block": {"title": "Поставка бумаги"},
            "verdict": {"label": "Нужна ручная проверка"},
            "documents": {"label": "2 готовы, 1 требует текста"},
            "key_conditions": ["оплата 15 дней", "поставка 5 дней"],
            "red_flags": ["аванс противоречит контракту"],
            "conflicts": ["аванс"],
            "expected_missing": ["приемочные документы"],
            "sections": [
                {
                    "id": "payment",
                    "title": "Оплата",
                    "items": [{"label": "Оплата", "value": "15 дней"}],
                }
            ],
        },
        "analysis_history": [
            {
                "changes": {
                    "summary": "Изменились условия оплаты.",
                    "documents": {"added": ["Контракт.docx"], "changed": ["ТЗ.docx"], "removed": []},
                    "condition_changes": [
                        {"label": "условия оплаты", "change_type": "changed"},
                    ],
                }
            }
        ],
    }
    documents = [{"name": "ТЗ.docx", "text_status": "ok", "url": "https://example.test/tz"}]
    operator_view = {
        "action_plan": [
            {
                "title": "Проверить оплату",
                "next_step": "Сверить контракт и ТЗ",
                "status": "manual_review",
            }
        ]
    }

    elements = analysis_management_brief_elements(analysis, documents, operator_view)

    assert elements[0] == ("p", "Управленческий brief по ТЗ", "heading")
    assert elements[1] == (
        "table",
        [
            ["Решение по ТЗ", "Нужна ручная проверка"],
            ["Паспорт ТЗ v2", "Офисная бумага"],
            ["Документы готовы/не готовы", "2 готовы, 1 требует текста"],
            ["Ключевые условия", "оплата 15 дней; поставка 5 дней"],
            ["Красные флаги", "аванс противоречит контракту"],
            ["Противоречия", "аванс"],
            ["Ожидаемые условия не найдены", "приемочные документы"],
        ],
        "analysis",
    )
    assert ("p", "Действия оператора", "heading2") in elements
    assert ("p", "Ссылки на источники", "heading2") in elements
    assert ("p", "Что изменилось с прошлой версии", "heading2") in elements


def test_analysis_saas_elements_builds_workflow_questions_and_playbooks():
    operator_view = {
        "tz_workflow": {
            "status_label": "Есть блокеры",
            "responsible": "operator@example.test",
            "deadline": "2026-06-30",
            "comment": "Проверить до расчета",
            "journal": [
                {"action": "created", "actor": "AI", "comment": "Анализ готов"},
            ],
        },
        "condition_groups": {
            "items": [
                {
                    "label": "условия оплаты",
                    "status": "conflict",
                    "source_status": "conflicting_sources",
                    "sources": ["ТЗ.docx", "Контракт.docx"],
                    "operator_action": "Сверить документы",
                }
            ]
        },
        "ai_questions": {
            "items": [
                {
                    "question": "Есть ли аванс?",
                    "answer": "В документах есть противоречие.",
                    "sources": [
                        {"source_label": "Контракт.docx", "fragment": "Аванс 30%"},
                    ],
                }
            ]
        },
        "playbooks": {
            "items": [
                {
                    "title": "Когда писать запрос разъяснений",
                    "severity": "manual_review",
                    "what_to_do": ["Сформулировать короткий вопрос"],
                    "when_to_use": ["Есть противоречие"],
                }
            ]
        },
    }

    elements = analysis_saas_elements(operator_view)

    assert ("p", "Рабочий статус ТЗ", "heading") in elements
    assert (
        "table",
        [
            ["Статус", "Есть блокеры"],
            ["Ответственный", "operator@example.test"],
            ["Дедлайн", "2026-06-30"],
            ["Комментарий", "Проверить до расчета"],
        ],
        "analysis",
    ) in elements
    assert ("p", "Сводка условий ТЗ", "heading") in elements
    assert ("p", "Контрольные вопросы ТЗ", "heading") in elements
    assert ("p", "Плейбуки оператора", "heading") in elements


def test_analysis_history_elements_summarizes_document_and_condition_changes():
    analysis = {
        "analysis_history": [
            {
                "run_number": 2,
                "analyzed_at": "2026-06-22T10:10:00",
                "changes": {
                    "summary": "Добавлено 1, изменено 2.",
                    "added": ["обеспечение"],
                    "feedback": ["оплата: подтверждено"],
                    "documents": {"added": ["Контракт.docx"], "changed": ["ТЗ.docx"], "removed": []},
                    "condition_changes": [
                        {"label": "условия оплаты"},
                    ],
                },
            }
        ]
    }

    elements = analysis_history_elements(analysis)

    assert elements == [
        ("p", "История анализа", "heading"),
        (
            "table",
            [
                ["Версия", "Когда", "Итог", "Детали"],
                [
                    "2",
                    "2026-06-22T10:10:00",
                    "Добавлено 1, изменено 2.",
                    "добавлено: обеспечение; метки: оплата: подтверждено; документы добавлены: Контракт.docx; документы изменены: ТЗ.docx; условия: условия оплаты",
                ],
            ],
            "analysis",
        ),
    ]
