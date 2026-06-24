from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile

from tender_killer.reports import build_tender_report_docx


def test_build_tender_report_docx_includes_product_profile_summary_for_many_profiles():
    payload = {
        "title": "Тестовая закупка материалов",
        "product_profile_summary": {
            "total": 40,
            "ready": 35,
            "needs_review": 5,
            "matched": 30,
            "priced": 25,
            "rejected": 2,
        },
        "product_profiles": [
            {
                "position_index": index,
                "product_name": f"Материал {index}",
                "profile_status": "ready",
                "category": "Материалы",
                "quantity": index,
                "unit": "шт",
                "search_phrases": [f"Материал {index}"],
            }
            for index in range(1, 41)
        ],
    }

    content = build_tender_report_docx(payload)
    document_xml = _document_xml(content)

    assert "Сводка товарных профилей" in document_xml
    assert "Товарные профили" in document_xml
    assert "Готовы к поиску" in document_xml
    assert "Требуют проверки" in document_xml
    assert "Товарный профиль для поиска" not in document_xml
    assert "Поисковые фразы" not in document_xml
    assert "Стоп-слова для товарного поиска" not in document_xml
    assert "Материал 40" not in document_xml


def test_build_tender_report_docx_contains_key_sections():
    payload = {
        "source": "mosreg_market",
        "external_id": "3668200",
        "url": "https://market.mosreg.ru/Trade/ViewTrade/3668200",
        "title": "Поставка огнетушителей",
        "customer": "Школа",
        "region": "Московская область",
        "price": 38064.0,
        "status": "Прием предложений",
        "deadline_at": "2026-05-29T11:50:00",
        "items": [
            {
                "position_index": 1,
                "name": "Огнетушитель порошковый",
                "quantity": 5,
                "unit": "шт",
                "unit_price": 7612.8,
                "total_price": 38064.0,
                "okpd2": "28.29.22.110",
                "classifier_code": "28.29.22.110",
                "classifier_type": "КОЗ-2",
            }
        ],
        "document_records": [
            {
                "name": "Техническое задание.docx",
                "document_type": "Описание объекта закупки",
                "text_status": "ok",
                "text_content": "Поставщик предоставляет сертификат соответствия. Срок поставки 3 дня.",
            }
        ],
        "analysis": {
            "summary": "поставка огнетушителей",
            "requirements": ["сертификат/декларация", "срок поставки"],
            "risks": ["короткий срок поставки"],
            "red_flags": ["национальный режим/страна происхождения"],
            "checklist": [
                {
                    "label": "сертификат/декларация",
                    "category": "documents",
                    "severity": "medium",
                    "evidence": "Поставщик предоставляет сертификат соответствия.",
                },
                {
                    "label": "короткий срок поставки",
                    "category": "delivery",
                    "severity": "high",
                    "evidence": "Срок поставки 3 дня.",
                },
            ],
            "status": "needs_review",
            "confidence": 0.84,
        },
        "economics": {
            "status": "interesting",
            "recommendation": "Маржа выглядит интересной, но требует проверки поставщика и условий исполнения.",
            "revenue": 38064.0,
            "supplier_cost": 25000.0,
            "risk_reserve_rate_percent": 3.5,
            "risk_reserve": 1332.24,
            "estimated_total_cost": 26332.24,
            "gross_margin": 11731.76,
            "margin_percent": 30.82,
            "missing_cost_inputs": [],
            "risk_types": ["delivery", "warranty", "acceptance"],
            "items": [
                {
                    "product_name": "Огнетушитель порошковый",
                    "quantity": 5,
                    "unit": "шт",
                    "unit_cost": 5000.0,
                    "total_cost": 25000.0,
                    "extra_costs": 0.0,
                }
            ],
        },
        "product_profiles": [
            {
                "position_index": 1,
                "product_name": "Огнетушитель порошковый",
                "category": "Противопожарные товары",
                "okpd2": "28.29.22.110",
                "classifier_code": "28.29.22.110",
                "classifier_type": "КОЗ-2",
                "quantity": 5,
                "unit": "шт",
                "required_characteristics": ["сертификат соответствия"],
                "evidence": [
                    {
                        "field": "document_requirement",
                        "source": "Техническое задание.docx",
                        "value": "Поставщик предоставляет сертификат соответствия.",
                    }
                ],
                "search_phrases": ["Огнетушитель порошковый", "Огнетушитель порошковый 28.29.22.110"],
                "stop_words": ["б/у"],
                "source": "item",
            }
        ],
    }

    content = build_tender_report_docx(payload)
    document_xml = _document_xml(content)

    assert "Паспорт закупки" in document_xml
    assert "Поставка огнетушителей" in document_xml
    assert "28.29.22.110" in document_xml
    assert "Товарный профиль для поиска" not in document_xml
    assert "КОЗ-2" in document_xml
    assert "Огнетушитель порошковый 28.29.22.110" not in document_xml
    assert "сертификат/декларация" in document_xml
    assert "Проверочный список" not in document_xml
    assert "Operator analysis sections" not in document_xml
    assert "Приложение: фрагменты извлеченного текста" not in document_xml
    assert "Поставщик предоставляет сертификат соответствия." in document_xml
    assert "короткий срок поставки" in document_xml
    assert "Экономика" in document_xml
    assert "Маржа" in document_xml
    assert "30.82%" in document_xml
    assert "Маржа выглядит интересной" in document_xml
    assert "<w:tbl>" in document_xml
    assert "Краткое решение" in document_xml
    assert "Документы" in document_xml
    assert "Анализ ТЗ: 4 блока" in document_xml
    assert "Выжимка ТЗ" not in document_xml
    assert "Требования" not in document_xml
    assert "Подтверждения из ТЗ" not in document_xml


def test_build_tender_report_docx_renders_analysis_decision_and_evidence():
    payload = {
        "source": "mosreg_market",
        "external_id": "3668200",
        "title": "Поставка огнетушителей",
        "document_records": [
            {
                "name": "ТЗ.docx",
                "text_status": "ok",
                "text_content": "Поставщик предоставляет сертификат. Срок поставки 3 дня.",
            }
        ],
        "analysis": {
            "summary": "поставка огнетушителей",
            "requirements": ["сертификат/декларация"],
            "risks": ["короткий срок поставки"],
            "red_flags": [],
            "status": "needs_review",
            "confidence": 0.78,
            "checklist": [
                {
                    "label": "сертификат/декларация",
                    "category": "documents",
                    "severity": "medium",
                    "evidence": "Поставщик предоставляет сертификат.",
                    "source": "ТЗ.docx",
                },
                {
                    "label": "короткий срок поставки",
                    "category": "delivery",
                    "severity": "high",
                    "evidence": "Срок поставки 3 дня.",
                    "source": "ТЗ.docx",
                },
            ],
        },
    }

    content = build_tender_report_docx(payload)
    document_xml = _document_xml(content)

    assert "Решение по анализу ТЗ" in document_xml
    assert "Нужна ручная проверка" in document_xml
    assert "Ключевые причины" in document_xml
    assert "Риск: короткий срок поставки" in document_xml
    assert "Требование: сертификат/декларация" in document_xml
    assert "Доказательства из документов" not in document_xml
    assert "Проверочный список" not in document_xml
    assert "Тип условия" not in document_xml
    assert "Важность" not in document_xml
    assert "Документ" in document_xml
    assert "Влияние" in document_xml
    assert "Документы" in document_xml
    assert "ТЗ.docx" in document_xml
    assert "Срок поставки 3 дня." in document_xml
    assert "Проверить наличие товара, реалистичность срока и заложить срочную логистику до расчета цены." in document_xml
    assert "Анализ ТЗ: 4 блока" in document_xml
    assert "Блок" in document_xml
    assert "Что означает" in document_xml
    assert "Что сделать" in document_xml
    assert "Выжимка ТЗ" not in document_xml
    assert "Приложение: фрагменты извлеченного текста" not in document_xml


def test_build_tender_report_docx_uses_operator_analysis_contract():
    payload = {
        "source": "moscow_supplier_portal",
        "external_id": "Auction10212588",
        "title": "Climbing equipment",
        "document_records": [{"name": "TZ.docx", "text_status": "ok"}],
        "analysis": {
            "summary": "legacy summary",
            "operator_view": {
                "version": 2,
                "decision_brief": {
                    "title": "Operator decision",
                    "summary": "Use the operator-ready analysis contract.",
                    "reasons": ["delivery in 3 days", "certificate package"],
                },
                "sections": [
                    {
                        "id": "blockers",
                        "title": "Blockers",
                        "items": [
                            {
                                "label": "contract security",
                                "category": "financial",
                                "severity": "high",
                                "description": "Bank guarantee may be required.",
                                "source": "Contract.pdf",
                                "impact": "cash gap",
                            }
                        ],
                    },
                    {
                        "id": "price_factors",
                        "title": "Price factors",
                        "items": [
                            {
                                "label": "delivery in 3 days",
                                "category": "delivery",
                                "severity": "high",
                                "description": "Rush logistics.",
                                "source": "TZ.docx",
                                "impact": "add delivery reserve",
                            }
                        ],
                    },
                ],
            },
        },
    }

    content = build_tender_report_docx(payload)
    document_xml = _document_xml(content)

    assert "Operator decision" in document_xml
    assert "Use the operator-ready analysis contract." in document_xml
    assert "Operator analysis sections" not in document_xml
    assert "Price factors" not in document_xml
    assert "delivery in 3 days" in document_xml
    assert "add delivery reserve" not in document_xml
    assert "contract security" not in document_xml


def test_build_tender_report_docx_renders_styled_four_block_analysis():
    payload = {
        "source": "mosreg_market",
        "external_id": "3675299",
        "title": "Поставка оборудования",
        "document_records": [
            {"name": "ТЗ.docx", "local_path": "data/tz.docx", "text_status": "ok", "text_content": "text"},
            {"name": "Контракт.pdf", "local_path": "data/contract.pdf", "text_status": "empty"},
        ],
        "analysis": {
            "summary": "Поставка оборудования.",
            "operator_view": {
                "version": 2,
                "decision_brief": {
                    "title": "Нужна ручная проверка",
                    "summary": "Есть блокеры и условия для экономики.",
                    "reasons": ["национальный режим", "Срок поставки"],
                },
                "document_state": {
                    "status": "needs_text",
                    "summary": "Текст извлечен не по всем документам.",
                    "next_step": "Извлечь текст и проверить проблемные файлы.",
                    "total": 2,
                    "downloaded": 2,
                    "text_ready": 1,
                    "attention": 1,
                    "missing_download": 0,
                    "missing_text": 1,
                },
                "action_plan": [
                    {
                        "id": "decision_risks",
                        "title": "Проверить риски участия",
                        "status": "manual_review",
                        "next_step": "Проверить допустимость участия до расчета.",
                        "items": ["национальный режим"],
                    },
                    {
                        "id": "fulfillment_terms",
                        "title": "Проверить поставку и исполнение",
                        "status": "needs_price_review",
                        "next_step": "Учесть в сроках, резерве и стоп-цене.",
                        "items": ["Срок поставки"],
                    },
                ],
                "major_blocks": [
                    {
                        "id": "decision_risks",
                        "title": "Итог и риски",
                        "items": [
                            {
                                "label": "национальный режим",
                                "description": "Нужно подтвердить страну происхождения.",
                                "operator_action": "Проверить допустимость участия до расчета.",
                                "source_label": "ТЗ.docx · стр. 2",
                                "fragment": "Заявка должна содержать страну происхождения товара.",
                                "priority": 1,
                            }
                        ],
                    },
                    {
                        "id": "product_compliance",
                        "title": "Товар и документы",
                        "items": [
                            {
                                "label": f"сертификат {index}",
                                "description": f"Подтверждающий документ {index}.",
                                "operator_action": "Запросить у поставщика.",
                                "source_label": "ТЗ.docx",
                                "fragment": f"Фрагмент про сертификат {index}.",
                                "priority": index,
                            }
                            for index in range(1, 9)
                        ],
                    },
                    {
                        "id": "fulfillment_terms",
                        "title": "Поставка и исполнение",
                        "items": [
                            {
                                "label": "срок поставки",
                                "description": "Поставка в короткий срок.",
                                "operator_action": "Заложить логистический резерв.",
                                "source_label": "Контракт.pdf",
                                "fragment": "Срок поставки 3 дня.",
                                "priority": 2,
                            }
                        ],
                    },
                    {
                        "id": "acceptance_payment",
                        "title": "Приемка, документы и оплата",
                        "items": [
                            {
                                "label": "УПД",
                                "description": "Передать закрывающие документы.",
                                "operator_action": "Подготовить УПД к приемке.",
                                "source_label": "Контракт.pdf",
                                "fragment": "Оплата после подписания УПД.",
                                "priority": 3,
                            }
                        ],
                    },
                ],
                "sections": [],
            },
        },
    }

    content = build_tender_report_docx(payload)
    document_xml = _document_xml(content)
    styles_xml = _styles_xml(content)

    assert "Анализ ТЗ: 4 блока" in document_xml
    assert "Итог и риски" in document_xml
    assert "Товар и документы" in document_xml
    assert "Поставка и исполнение" in document_xml
    assert "Приемка, документы и оплата" in document_xml
    assert "сертификат 1" in document_xml
    assert "сертификат 7" in document_xml
    assert "сертификат 8" not in document_xml
    assert "и еще 1 пункт — см. в интерфейсе" in document_xml
    assert "Проверить допустимость участия до расчета." in document_xml
    assert "Заложить логистический резерв." in document_xml
    assert "Подготовить УПД к приемке." in document_xml
    assert "План проверки ТЗ" not in document_xml
    assert "Состояние документов" not in document_xml
    assert '<w:shd w:fill="E6F4EA"' in document_xml
    assert 'w:color w:val="1F4D3A"' in styles_xml
    assert "Очень длинный извлеченный текст" not in document_xml


def test_build_tender_report_docx_includes_operator_feedback_mark_and_comment():
    payload = {
        "source": "mosreg_market",
        "external_id": "3668200",
        "title": "Поставка бумаги",
        "document_records": [{"name": "ТЗ.docx", "text_status": "ok"}],
        "analysis": {
            "summary": "Нужна проверка ТЗ.",
            "status": "needs_review",
            "confidence": 0.7,
            "operator_view": {
                "version": 3,
                "major_blocks": [
                    {
                        "id": "decision_risks",
                        "title": "Итог и риски",
                        "items": [
                            {
                                "id": "fact:national",
                                "label": "национальный режим/страна происхождения",
                                "operator_summary": "Может повлиять на допуск заявки.",
                                "operator_check": "Проверить страну происхождения.",
                                "source_label": "ТЗ.docx · стр. 2",
                                "fragment": "Участник указывает страну происхождения.",
                                "feedback_state": "needs_manual_review",
                                "feedback_label": "требует ручной проверки",
                                "feedback_comment": "Нужно сверить с последней редакцией извещения.",
                                "priority": 100,
                            }
                        ],
                    },
                    {"id": "product_compliance", "title": "Товар и документы", "items": []},
                    {"id": "fulfillment_terms", "title": "Поставка и исполнение", "items": []},
                    {"id": "acceptance_payment", "title": "Приемка, документы и оплата", "items": []},
                ],
            },
        },
    }

    content = build_tender_report_docx(payload)
    document_xml = _document_xml(content)

    assert "Оператор" in document_xml
    assert "требует ручной проверки" in document_xml
    assert "Нужно сверить с последней редакцией извещения." in document_xml


def test_build_tender_report_docx_renders_participation_map():
    payload = {
        "source": "mosreg_market",
        "external_id": "3677777",
        "url": "https://market.mosreg.ru/Trade/ViewTrade/3677777",
        "title": "Поставка бумаги",
        "customer": "Комитет закупок",
        "price": 49015,
        "deadline_at": "2026-06-29T14:37:00",
        "document_records": [
            {"name": "ТЗ.docx", "document_type": "Описание объекта закупки", "text_status": "ok"},
            {"name": "Контракт.docx", "document_type": "Проект контракта", "text_status": "ok"},
        ],
        "analysis": {
            "status": "needs_review",
            "confidence": 0.95,
            "operator_view": {
                "version": 3,
                "decision_brief": {
                    "title": "Нужна ручная проверка",
                    "summary": "В ТЗ есть условия, которые влияют на участие и цену.",
                    "reasons": ["лицензия/СРО", "национальный режим"],
                },
                "action_plan": [
                    {
                        "title": "Проверить итоги и риски",
                        "next_step": "Снять блокеры до расчета.",
                        "items": ["лицензия/СРО", "национальный режим"],
                    }
                ],
                "major_blocks": [
                    {
                        "id": "decision_risks",
                        "title": "Итог и риски",
                        "items": [
                            {
                                "label": "лицензия/СРО",
                                "operator_summary": "Квалификационное условие может заблокировать заявку без подтверждения.",
                                "operator_check": "Проверить наличие лицензии или СРО у участника.",
                                "description": "Проверить, действительно ли требуется лицензия.",
                                "operator_action": "Проверить до участия.",
                                "source_label": "ТЗ.docx · стр. 2",
                                "fragment": "Требуется лицензия.",
                                "source_binding": {"label": "источник подтвержден"},
                                "confidence_level": {"label": "уверенность высокая"},
                                "context_source_authority": "primary_for_topic",
                                "context_source_reason": "technical_spec covers participant_requirements",
                                "context_document_role": "technical_spec",
                                "context_source_priority": ["participant_requirements"],
                                "weak_reason": "Нужна ручная проверка формулировки.",
                                "priority": 1,
                            }
                        ],
                    },
                    {
                        "id": "product_compliance",
                        "title": "Товар и документы",
                        "items": [
                            {
                                "label": "сертификат/декларация",
                                "operator_summary": "Нужно заранее получить документы соответствия у поставщика.",
                                "operator_check": "Запросить сертификаты до подачи заявки.",
                                "description": "Подготовить подтверждающие документы.",
                                "operator_action": "Запросить документы у поставщика.",
                                "source_label": "ТЗ.docx · стр. 4",
                                "fragment": "Поставщик предоставляет сертификат.",
                                "source_binding": {"label": "источник подтвержден"},
                                "confidence_level": {"label": "уверенность высокая"},
                                "priority": 2,
                            }
                        ],
                    },
                    {"id": "fulfillment_terms", "title": "Поставка и исполнение", "items": []},
                    {"id": "acceptance_payment", "title": "Приемка, документы и оплата", "items": []},
                ],
            },
            "analysis_history": [
                {
                    "run_number": 2,
                    "analyzed_at": "2026-06-04T12:30:00",
                    "changes": {
                        "summary": "Добавлено 1, удалено 0, изменено 1.",
                        "added": ["сертификат/декларация"],
                        "changed": ["лицензия/СРО"],
                        "removed": [],
                        "feedback": ["лицензия/СРО: подтверждено"],
                    },
                }
            ],
        },
    }

    content = build_tender_report_docx(payload)
    document_xml = _document_xml(content)

    assert "КАРТА УЧАСТИЯ" in document_xml
    assert "Краткое решение" in document_xml
    assert "Таблица рисков" in document_xml
    assert "Чеклист участия" in document_xml
    assert "Источники" in document_xml
    assert "Приложения" in document_xml
    assert "Нужна ручная проверка" in document_xml
    assert "лицензия/СРО" in document_xml
    assert "Квалификационное условие может заблокировать заявку" in document_xml
    assert "Проверить наличие лицензии или СРО" in document_xml
    assert "История анализа" in document_xml
    assert "лицензия/СРО: подтверждено" in document_xml
    assert "ТЗ.docx · стр. 2" in document_xml
    assert "источник подтвержден" in document_xml
    assert "уверенность высокая" in document_xml
    assert "главный источник по теме" in document_xml
    assert "ТЗ" in document_xml
    assert "требования к участнику" in document_xml
    assert "Нужна ручная проверка формулировки" in document_xml


def test_build_tender_report_docx_renders_tz_passport_before_raw_analysis():
    payload = {
        "source": "moscow_supplier_portal",
        "external_id": "Auction10212588",
        "title": "Climbing equipment",
        "document_records": [{"name": "TZ.docx", "text_status": "ok"}],
        "analysis": {
            "summary": "legacy summary",
            "tz_passport": {
                "version": 1,
                "title": "Climbing equipment",
                "status": "needs_review",
                "confidence": 0.75,
                "sections": [
                    {
                        "id": "execution",
                        "title": "Execution",
                        "items": [
                            {
                                "label": "delivery term",
                                "value": "5 working days",
                                "source": "TZ.docx",
                                "impact": "rush logistics",
                            }
                        ],
                    },
                    {
                        "id": "price_factors",
                        "title": "Price factors",
                        "items": [
                            {
                                "label": "contract security",
                                "value": "5%",
                                "source": "Contract.pdf",
                                "impact": "cash reserve",
                            }
                        ],
                    },
                ],
            },
            "operator_view": {
                "version": 2,
                "sections": [
                    {
                        "id": "price_factors",
                        "title": "Operator price factors",
                        "items": [
                            {
                                "label": "operator-only cost factor",
                                "category": "delivery",
                                "severity": "high",
                            }
                        ],
                    }
                ],
            },
        },
    }

    content = build_tender_report_docx(payload)
    document_xml = _document_xml(content)

    assert "Паспорт ТЗ" in document_xml
    assert "Execution" in document_xml
    assert "delivery term" in document_xml
    assert "5 working days" in document_xml
    assert "TZ.docx" in document_xml
    assert "cash reserve" in document_xml
    assert "Operator analysis sections" not in document_xml
    assert "Выжимка ТЗ" not in document_xml
    assert document_xml.index("Паспорт ТЗ") < document_xml.index("Анализ ТЗ: 4 блока")


def test_build_tender_report_docx_renders_backend_decision_reasons():
    payload = {
        "source": "mosreg_market",
        "external_id": "3668201",
        "title": "Поставка бумаги",
        "price": 100000,
        "decision": {
            "label": "Проверить ТЗ",
            "summary": "Экономика выглядит рабочей, но есть условия для проверки.",
            "next_step": "Проверить анализ",
            "reasons": ["Маржа выше целевого уровня.", "Есть короткий срок поставки."],
            "blockers": ["Проверить сертификат/декларацию"],
        },
    }

    content = build_tender_report_docx(payload)
    document_xml = _document_xml(content)

    assert "Решение Tender Killer" in document_xml
    assert "Проверить ТЗ" in document_xml
    assert "Экономика выглядит рабочей" in document_xml
    assert "Следующий шаг" in document_xml
    assert "Причины решения" in document_xml
    assert "Маржа выше целевого уровня." in document_xml
    assert "Блокеры" in document_xml
    assert "Проверить сертификат/декларацию" in document_xml


def test_build_tender_report_docx_renders_customer_eis_and_risk_summary():
    payload = {
        "source": "mosreg_market",
        "external_id": "customer-risk",
        "title": "Paper supply",
        "customer": "School",
        "customer_risk_profile": {
            "level": "high",
            "score": 72,
            "customer": {"name": "School", "inn": "5047152960"},
            "history": {"total": 4},
            "factors": [
                {"severity": "high", "evidence": "Terminated contracts: 3."},
                {"severity": "medium", "evidence": "Local history has tenders without participants."},
            ],
        },
        "eis_reference": {
            "network_fetch_enabled": False,
            "identifiers": {
                "purchase_number": "0373200000126000012",
                "customer_inn": "5047152960",
            },
            "links": [
                {
                    "id": "eis_purchase_search",
                    "label": "EIS purchase search",
                    "url": "https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString=0373200000126000012",
                },
                {
                    "id": "eis_contracts_by_customer",
                    "label": "EIS customer contracts",
                    "url": "https://zakupki.gov.ru/epz/contract/search/results.html?searchString=5047152960",
                },
            ],
        },
    }

    content = build_tender_report_docx(payload)
    document_xml = _document_xml(content)

    assert "Заказчик / ЕИС" in document_xml
    assert "5047152960" in document_xml
    assert "0373200000126000012" in document_xml
    assert "Terminated contracts: 3." in document_xml
    assert "network fetch: off" in document_xml
    assert "EIS purchase search" in document_xml


def test_build_tender_report_docx_falls_back_to_card_subject_when_items_missing():
    payload = {
        "source": "mosreg_market",
        "external_id": "3670000",
        "url": "https://market.mosreg.ru/Trade/ViewTrade/3670000",
        "title": "Поставка садовых инструментов",
        "category": "Хозяйственные товары",
        "okpd2": "25.73.10",
        "price": 191156.0,
        "items": [],
        "document_records": [],
        "analysis": None,
    }

    content = build_tender_report_docx(payload)
    document_xml = _document_xml(content)

    assert "Поставка садовых инструментов" in document_xml
    assert "Хозяйственные товары" in document_xml
    assert "25.73.10" in document_xml
    assert "Позиции пока не найдены" not in document_xml


def test_build_tender_report_docx_keeps_word_report_compact():
    payload = {
        "source": "mosreg_market",
        "external_id": "3675299",
        "title": "Поставка товаров для оборудования медицинских кабинетов ДОУ",
        "price": 238933.0,
        "product_profile_summary": {"total": 39, "ready": 39, "needs_review": 0, "matched": 0, "priced": 0, "rejected": 0},
        "product_profiles": [
            {
                "position_index": index,
                "product_name": f"Позиция {index}",
                "profile_status": "ready",
                "search_phrases": [f"Позиция {index} купить", f"Позиция {index} поставщик"],
                "stop_words": ["б/у", "ремонт"],
            }
            for index in range(1, 40)
        ],
        "document_records": [
            {
                "name": "ТЗ.docx",
                "text_status": "ok",
                "text_content": "Очень длинный извлеченный текст, который должен оставаться на сайте, а не в Word. " * 80,
            }
        ],
        "analysis": {
            "summary": "Поставка оборудования для медицинских кабинетов.",
            "requirements": ["сертификат/декларация", "гарантия"],
            "risks": ["короткий срок поставки"],
            "red_flags": [],
            "status": "needs_review",
            "confidence": 0.8,
        },
        "economics": {
            "status": "missing_prices",
            "revenue": 238933.0,
            "supplier_cost": 0,
            "estimated_total_cost": 0,
            "gross_margin": 0,
            "margin_percent": 0,
            "missing_cost_inputs": [f"Позиция {index}" for index in range(1, 13)],
            "items": [{"product_name": f"Позиция {index}", "quantity": 1, "unit": "шт"} for index in range(1, 40)],
        },
    }

    content = build_tender_report_docx(payload)
    document_xml = _document_xml(content)

    assert "Сводка товарных профилей" in document_xml
    assert "39" in document_xml
    assert "Не хватает цен" in document_xml
    assert "12 позиций" in document_xml
    assert "Позиция 12" not in document_xml
    assert "Товарный профиль для поиска" not in document_xml
    assert "Поисковые фразы" not in document_xml
    assert "Стоп-слова для товарного поиска" not in document_xml
    assert "Позиции расчета" not in document_xml
    assert "Приложение: фрагменты извлеченного текста" not in document_xml
    assert "Очень длинный извлеченный текст" not in document_xml
    assert "Выжимка ТЗ" not in document_xml


def test_build_tender_report_docx_surfaces_financial_model_v1():
    payload = {
        "source": "mosreg_market",
        "external_id": "finance-v1",
        "title": "Поставка бумаги",
        "price": 100000.0,
        "product_profile_summary": {"total": 1, "ready": 1, "needs_review": 0, "matched": 0, "priced": 1, "rejected": 0},
        "product_profiles": [],
        "document_records": [],
        "analysis": None,
        "economics": {
            "status": "interesting",
            "revenue": 100000.0,
            "supplier_cost": 70560.0,
            "risk_reserve": 5360.0,
            "risk_reserve_rate_percent": 7.0,
            "estimated_total_cost": 72560.0,
            "gross_margin": 27440.0,
            "margin_percent": 27.44,
            "stop_price": 90700.0,
            "security_amount": 10000.0,
            "missing_cost_inputs": [],
            "risk_types": ["delivery"],
            "participation_calculation": {
                "label": "Можно заходить",
                "current_price": 100000.0,
                "stop_price": 90700.0,
                "profit": 27440.0,
                "headroom_to_stop_price": 9300.0,
                "risk_reserve": 5360.0,
                "security_amount": 10000.0,
                "reason": "Ставка выше стоп-цены, целевая маржа сохранена.",
            },
            "cost_breakdown": {
                "direct_cost": 50000.0,
                "logistics_cost": 3000.0,
                "documents_cost": 2000.0,
                "other_costs": 1000.0,
                "vat_cost": 11200.0,
                "position_risk_reserve": 3360.0,
                "execution_risk_reserve": 2000.0,
                "cash_required": 82560.0,
            },
        },
    }

    content = build_tender_report_docx(payload)
    document_xml = _document_xml(content)

    assert "Стоп-цена" in document_xml
    assert "90 700" in document_xml
    assert "Расчет участия" in document_xml
    assert "Можно заходить" in document_xml
    assert "Запас до стоп-цены" in document_xml
    assert "9 300" in document_xml
    assert "Разбивка затрат" in document_xml
    assert "Денежная нагрузка" in document_xml
    assert "82 560" in document_xml


def _document_xml(content: bytes) -> str:
    with ZipFile(BytesIO(content)) as archive:
        return archive.read("word/document.xml").decode("utf-8")


def _styles_xml(content: bytes) -> str:
    with ZipFile(BytesIO(content)) as archive:
        return archive.read("word/styles.xml").decode("utf-8")
def test_build_tender_report_docx_uses_structured_interpretation_in_four_block_table():
    payload = {
        "source": "mosreg_market",
        "external_id": "structured-interpretation",
        "title": "Поставка бумаги",
        "document_records": [{"name": "Контракт.docx", "local_path": "contract.docx", "text_status": "ok"}],
        "analysis": {
            "summary": "Поставка бумаги",
            "analysis_facts": {
                "version": 1,
                "items": [
                    {
                        "kind": "execution_term",
                        "label": "Оплата",
                        "value": "Оплата производится в течение 7 рабочих дней с даты подписания УПД.",
                        "category": "payment",
                        "severity": "medium",
                        "document_name": "Контракт.docx",
                        "fragment": "Оплата производится в течение 7 рабочих дней с даты подписания УПД.",
                    }
                ],
            },
        },
    }

    content = build_tender_report_docx(payload)
    document_xml = _document_xml(content)

    assert "Что найдено" in document_xml
    assert "Что означает" in document_xml
    assert "Влияние" in document_xml
    assert "Что сделать" in document_xml
    assert "Оплата производится в течение 7 рабочих дней с даты подписания УПД." in document_xml
    assert "Оплата привязана к условиям документа" in document_xml
    assert "кассовый разрыв" in document_xml
    assert "Отдельно сверить УПД" in document_xml


def test_build_tender_report_docx_renders_management_tz_brief_v2():
    payload = {
        "source": "mosreg_market",
        "external_id": "brief-v2",
        "url": "https://example.test/tender/brief-v2",
        "title": "Поставка офисной бумаги",
        "document_records": [
            {"name": "ТЗ.docx", "local_path": "tz.docx", "text_status": "ok"},
            {"name": "Проект контракта.docx", "local_path": "contract.docx", "text_status": "ok"},
        ],
        "analysis": {
            "summary": "Поставка офисной бумаги",
            "status": "needs_review",
            "confidence": 0.82,
            "analysis_facts": {
                "version": 1,
                "items": [
                    {
                        "id": "subject:paper",
                        "kind": "subject",
                        "label": "Предмет",
                        "value": "Поставка офисной бумаги",
                        "category": "subject",
                        "document_name": "ТЗ.docx",
                        "fragment": "Поставка офисной бумаги",
                    },
                    {
                        "id": "payment",
                        "kind": "execution_term",
                        "label": "Оплата",
                        "value": "Оплата в течение 15 рабочих дней после поставки товара.",
                        "category": "payment",
                        "document_name": "Проект контракта.docx",
                        "fragment": "Оплата в течение 15 рабочих дней после поставки товара.",
                    },
                    {
                        "id": "advance:no",
                        "kind": "execution_term",
                        "label": "Аванс",
                        "value": "Аванс не предусмотрен.",
                        "category": "financial",
                        "document_name": "ТЗ.docx",
                        "fragment": "Аванс не предусмотрен.",
                    },
                    {
                        "id": "advance:yes",
                        "kind": "execution_term",
                        "label": "Аванс",
                        "value": "Предусмотрен аванс 30 процентов.",
                        "category": "financial",
                        "document_name": "Проект контракта.docx",
                        "fragment": "Предусмотрен аванс 30 процентов.",
                    },
                ],
            },
            "analysis_history": [
                {
                    "id": 2,
                    "run_number": 2,
                    "analyzed_at": "2026-06-22T10:10:00",
                    "changes": {
                        "summary": "Добавлено 1, удалено 0, изменено 1.",
                        "documents": {
                            "added": ["Проект контракта.docx"],
                            "removed": [],
                            "changed": ["ТЗ.docx"],
                        },
                        "condition_changes": [
                            {
                                "family": "payment",
                                "label": "условия оплаты",
                                "change_type": "changed",
                                "before": "Оплата в течение 7 рабочих дней.",
                                "after": "Оплата в течение 15 рабочих дней.",
                            }
                        ],
                    },
                }
            ],
        },
    }

    content = build_tender_report_docx(payload)
    document_xml = _document_xml(content)

    assert "Управленческий brief по ТЗ" in document_xml
    assert "Решение по ТЗ" in document_xml
    assert "Паспорт ТЗ v2" in document_xml
    assert "Документы готовы/не готовы" in document_xml
    assert "Ключевые условия" in document_xml
    assert "Противоречия" in document_xml
    assert "Ожидаемые условия не найдены" in document_xml
    assert "Действия оператора" in document_xml
    assert "Ссылки на источники" in document_xml
    assert "Что изменилось с прошлой версии" in document_xml
    assert "Аванс" in document_xml
    assert "приемка и закрывающие документы" in document_xml
    assert "Проект контракта.docx" in document_xml
