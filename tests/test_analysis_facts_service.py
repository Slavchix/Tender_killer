from __future__ import annotations

from tender_killer.analysis import analyze_tender_texts
from tender_killer.analysis_facts_service import build_analysis_facts
from tender_killer.analysis_text_index_service import build_analysis_text_index


def test_build_analysis_facts_binds_each_fact_to_document_evidence():
    documents = [
        {
            "name": "spec.docx",
            "text_status": "ok",
            "text_content": "Техническое задание: поставка мебели. Поставщик обязан предоставить сертификат соответствия.",
        },
        {
            "name": "contract.docx",
            "text_status": "ok",
            "text_content": "Срок поставки товара: в течение 5 рабочих дней. Указывается страна происхождения товара.",
        },
    ]
    analysis = {
        "summary": "поставка мебели",
        "confidence": 0.82,
        "checklist": [
            {
                "label": "сертификат/декларация",
                "category": "documents",
                "severity": "medium",
                "evidence": "Поставщик обязан предоставить сертификат соответствия.",
            },
            {
                "label": "национальный режим/страна происхождения",
                "category": "national_regime",
                "severity": "high",
                "evidence": "Указывается страна происхождения товара.",
            },
        ],
        "execution_terms": [
            {
                "type": "delivery_deadline",
                "label": "Срок поставки",
                "category": "delivery",
                "severity": "medium",
                "value": "Срок поставки товара: в течение 5 рабочих дней.",
                "evidence": "Срок поставки товара: в течение 5 рабочих дней.",
            }
        ],
    }

    facts = build_analysis_facts(analysis, documents)
    items = facts["items"]
    by_label = {item["label"]: item for item in items}

    assert facts["version"] == 1
    assert facts["metrics"] == {"total": 4, "blockers": 1, "price_factors": 1, "unbound": 0}
    assert by_label["Предмет"]["kind"] == "subject"
    assert by_label["Предмет"]["value"] == "поставка мебели"
    assert by_label["сертификат/декларация"]["kind"] == "supplier_document"
    assert by_label["сертификат/декларация"]["document_name"] == "spec.docx"
    assert by_label["сертификат/декларация"]["fragment"] == "Поставщик обязан предоставить сертификат соответствия."
    assert by_label["сертификат/декларация"]["rule_id"] == "checklist:сертификат/декларация"
    assert by_label["сертификат/декларация"]["operator_group"] == "prepare"
    assert by_label["сертификат/декларация"]["operator_action"] == "Подготовить подтверждающие документы."
    assert by_label["сертификат/декларация"]["price_impact"] == "documents"
    assert by_label["сертификат/декларация"]["priority"] == 50
    assert by_label["Срок поставки"]["kind"] == "execution_term"
    assert by_label["Срок поставки"]["document_name"] == "contract.docx"
    assert by_label["Срок поставки"]["is_price_factor"] is True
    assert by_label["Срок поставки"]["operator_group"] == "execution"
    assert by_label["Срок поставки"]["operator_action"] == "Проверить срок исполнения и заложить логистику."
    assert by_label["Срок поставки"]["price_impact"] == "logistics"
    assert by_label["Срок поставки"]["priority"] == 60
    assert by_label["национальный режим/страна происхождения"]["kind"] == "blocker"
    assert by_label["национальный режим/страна происхождения"]["document_name"] == "contract.docx"
    assert by_label["национальный режим/страна происхождения"]["is_blocker"] is True
    assert by_label["национальный режим/страна происхождения"]["operator_group"] == "blocker"
    assert by_label["национальный режим/страна происхождения"]["operator_action"] == "Проверить допустимость участия до расчета."
    assert by_label["национальный режим/страна происхождения"]["price_impact"] == "compliance"
    assert by_label["национальный режим/страна происхождения"]["priority"] == 90
    assert all(item["document_name"] != "Документ не привязан" for item in items if item["kind"] != "subject")


def test_build_analysis_facts_marks_unbound_evidence_for_operator_review():
    facts = build_analysis_facts(
        {
            "summary": "поставка техники",
            "confidence": 0.7,
            "checklist": [
                {
                    "label": "лицензия/СРО",
                    "category": "legal",
                    "severity": "high",
                    "evidence": "Нужна лицензия на выполнение работ.",
                }
            ],
        },
        [{"name": "tz.docx", "text_status": "ok", "text_content": "Документ без такого фрагмента."}],
    )

    license_fact = next(item for item in facts["items"] if item["label"] == "лицензия/СРО")

    assert license_fact["document_name"] == "Документ не привязан"
    assert license_fact["needs_review"] is True
    assert license_fact["operator_group"] == "manual_review"
    assert license_fact["operator_action"] == "Проверить источник факта вручную."
    assert license_fact["priority"] == 95
    assert facts["metrics"]["unbound"] == 1


def test_build_analysis_facts_derives_page_and_context_from_document_text():
    documents = [
        {
            "name": "contract.pdf",
            "text_status": "ok",
            "text_content": (
                "Страница 1. Общие условия поставки.\f"
                "Раздел 2. Подтверждающие документы. "
                "Поставщик обязан предоставить сертификат соответствия. "
                "Проверка сертификата проводится заказчиком при приемке товара."
            ),
        }
    ]
    analysis = {
        "confidence": 0.9,
        "checklist": [
            {
                "label": "сертификат/декларация",
                "category": "documents",
                "severity": "medium",
                "evidence": "Поставщик обязан предоставить сертификат соответствия.",
            }
        ],
    }

    facts = build_analysis_facts(analysis, documents)
    certificate = next(item for item in facts["items"] if item["label"] == "сертификат/декларация")

    assert certificate["document_name"] == "contract.pdf"
    assert certificate["source_page"] == 2
    assert certificate["source_label"] == "contract.pdf · стр. 2"
    assert "Раздел 2. Подтверждающие документы" in certificate["source_context"]
    assert "Проверка сертификата проводится заказчиком" in certificate["source_context"]
    assert certificate["needs_review"] is False
    assert facts["metrics"]["unbound"] == 0


def test_build_analysis_facts_routes_domain_specific_requirements_to_operator_tasks():
    text = """
    Техническое задание: поставка аккумуляторных батарей с монтажом.
    Допускается эквивалент при полной совместимости с имеющимся оборудованием.
    Поставщик выполняет монтаж и пусконаладочные работы.
    У исполнителя должен быть квалифицированный персонал.
    Работы закрываются актом выполненных работ.
    """
    analysis = analyze_tender_texts([text]).to_dict()

    facts = build_analysis_facts(
        analysis,
        [{"name": "tz.docx", "text_status": "ok", "text_content": text}],
    )
    by_label = {item["label"]: item for item in facts["items"]}

    assert by_label["эквивалент"]["operator_group"] == "prepare"
    assert by_label["эквивалент"]["price_impact"] == "compliance"
    assert by_label["совместимость"]["operator_group"] == "prepare"
    assert by_label["совместимость"]["price_impact"] == "compliance"
    assert by_label["монтаж/пусконаладка"]["is_price_factor"] is True
    assert by_label["монтаж/пусконаладка"]["price_impact"] == "logistics"
    assert by_label["квалифицированный персонал"]["operator_group"] == "prepare"
    assert by_label["квалифицированный персонал"]["is_blocker"] is False
    assert by_label["акт выполненных работ"]["price_impact"] == "working_capital"


def test_build_analysis_facts_adds_document_roles_and_typed_fields_from_evidence():
    documents = [
        {
            "name": "Описание объекта закупки.docx",
            "document_type": "Описание объекта закупки",
            "text_status": "ok",
            "text_content": (
                "Поставщик предоставляет сертификат соответствия при поставке товара. "
                "Проверка сертификата проводится заказчиком при приемке."
            ),
        },
        {
            "name": "Проект контракта.docx",
            "document_type": "Проект контракта",
            "text_status": "ok",
            "text_content": (
                "Срок поставки товара: в течение 5 рабочих дней с даты заключения контракта поставщиком. "
                "Обеспечение исполнения контракта составляет 10% от цены контракта."
            ),
        },
    ]
    analysis = {
        "summary": "Поставка бумаги",
        "confidence": 0.91,
        "text_index": build_analysis_text_index(documents),
        "checklist": [
            {
                "label": "сертификат/декларация",
                "category": "documents",
                "severity": "medium",
                "evidence": "Поставщик предоставляет сертификат соответствия при поставке товара.",
            }
        ],
        "execution_terms": [
            {
                "type": "delivery_deadline",
                "label": "Срок поставки",
                "category": "delivery",
                "severity": "medium",
                "value": "Срок поставки товара: в течение 5 рабочих дней с даты заключения контракта поставщиком.",
                "evidence": "Срок поставки товара: в течение 5 рабочих дней с даты заключения контракта поставщиком.",
            },
            {
                "type": "contract_security",
                "label": "Обеспечение исполнения",
                "category": "financial",
                "severity": "high",
                "value": "Обеспечение исполнения контракта составляет 10% от цены контракта.",
                "evidence": "Обеспечение исполнения контракта составляет 10% от цены контракта.",
            },
        ],
    }

    facts = build_analysis_facts(analysis, documents)
    by_label = {item["label"]: item for item in facts["items"]}

    assert by_label["сертификат/декларация"]["document_role"] == "technical_specification"
    assert by_label["сертификат/декларация"]["document_stage"] == "delivery_or_acceptance"
    assert by_label["Срок поставки"]["document_role"] == "contract"
    assert by_label["Срок поставки"]["days"] == 5
    assert by_label["Срок поставки"]["deadline_type"] == "delivery"
    assert by_label["Срок поставки"]["responsible_party"] == "supplier"
    assert by_label["Обеспечение исполнения"]["document_role"] == "contract"
    assert by_label["Обеспечение исполнения"]["amount_percent"] == 10
    assert by_label["Обеспечение исполнения"]["amount_type"] == "contract_security"
