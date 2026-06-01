from __future__ import annotations

from tender_killer.analysis import analyze_tender_texts


def test_analyze_tender_texts_extracts_supplier_requirements_and_red_flags():
    result = analyze_tender_texts(
        [
            """
            Техническое задание: поставка офисной бумаги А4.
            Поставщик обязан предоставить сертификат соответствия и декларацию о соответствии.
            Срок поставки товара: в течение 3 рабочих дней с даты заключения контракта.
            Приемка осуществляется через ЕИС.
            Применяется национальный режим и постановление 1875, страна происхождения товара подтверждается документами.
            Обеспечение исполнения контракта: 5 процентов. За просрочку начисляется штраф и пеня.
            """
        ]
    )

    assert result.status == "needs_review"
    assert result.confidence >= 0.7
    assert "поставка офисной бумаги А4" in result.summary
    assert "сертификат/декларация" in result.requirements
    assert "срок поставки" in result.requirements
    assert "приемка через ЕИС" in result.requirements
    assert "национальный режим/страна происхождения" in result.red_flags
    assert "обеспечение исполнения контракта" in result.risks
    assert "штрафы/пени" in result.risks


def test_analyze_tender_texts_builds_actionable_checklist_with_evidence():
    result = analyze_tender_texts(
        [
            """
            Техническое задание: поставка бумаги офисной.
            Бумага должна соответствовать ГОСТ Р 57641-2017.
            Поставщик предоставляет декларацию о соответствии.
            Гарантийный срок на товар не менее 12 месяцев.
            Срок поставки: 5 календарных дней.
            """
        ]
    )

    labels = [item["label"] for item in result.checklist]
    assert "ГОСТ/ТУ" in labels
    assert "сертификат/декларация" in labels
    assert "гарантия" in labels
    assert "срок поставки" in labels

    warranty = next(item for item in result.checklist if item["label"] == "гарантия")
    assert warranty["category"] == "contract"
    assert warranty["severity"] == "medium"
    assert "12 месяцев" in warranty["evidence"]


def test_analyze_tender_texts_ignores_binary_garbage_lines():
    result = analyze_tender_texts(
        [
            "ГОСТ\x00\x02=\x02j\x02Z\x02`\x02^\x02Z\x02g\x02k\x03\x04\x05",
            "Техническое задание: поставка багетного стекла. Срок поставки товара - 5 рабочих дней.",
        ]
    )

    labels = [item["label"] for item in result.checklist]
    assert "ГОСТ/ТУ" not in labels
    assert "лицензия/СРО" not in labels
    assert "срок поставки" in labels
    assert all("\x00" not in item["evidence"] for item in result.checklist)


def test_analyze_tender_texts_normalizes_spacing_before_punctuation():
    result = analyze_tender_texts(
        [
            "Техническое задание: Поставка , монтаж и установка товара. "
            "Срок поставки товара - 5 рабочих дней."
        ]
    )

    assert "Поставка, монтаж" in result.summary


def test_analyze_tender_texts_handles_empty_text_cautiously():
    result = analyze_tender_texts(["", "   "])

    assert result.status == "needs_review"
    assert result.confidence == 0.1
    assert result.summary == "Текст документов не извлечен или пустой."
    assert result.red_flags == ["нет текста для анализа"]


def test_analyze_tender_texts_flags_registry_and_quality_documents():
    result = analyze_tender_texts(
        [
            """
            Предмет контракта: поставка мебели офисной.
            Поставщик предоставляет паспорт качества.
            Товар должен быть включен в реестр российской промышленной продукции.
            Участник указывает страну происхождения товара.
            """
        ]
    )

    assert "паспорт качества" in result.requirements
    assert "реестр российской продукции" in result.red_flags
    assert "национальный режим/страна происхождения" in result.red_flags


def test_analyze_tender_texts_ignores_short_delivery_and_license_noise():
    result = analyze_tender_texts(
        [
            """
            Техническое задание: поставка учебных материалов.
            Срок хранения документов и конфиденциальность действуют в течение 3 лет.
            Пользователь принимает условия лицензионного соглашения производителя.
            """
        ]
    )

    labels = [item["label"] for item in result.checklist]
    assert "короткий срок поставки" not in result.risks
    assert "короткий срок поставки" not in labels
    assert "лицензия/СРО" not in result.red_flags
    assert "лицензия/СРО" not in labels


def test_analyze_tender_texts_extracts_execution_terms_for_operator_view():
    result = analyze_tender_texts(
        [
            """
            Техническое задание: поставка хозяйственных товаров.
            Срок поставки товара: в течение 5 рабочих дней с даты заключения контракта.
            Оплата производится в течение 7 рабочих дней после подписания документа о приемке.
            Авансирование не предусмотрено.
            Гарантийный срок на товар составляет 12 месяцев.
            Обеспечение исполнения контракта составляет 5 процентов от цены контракта.
            За просрочку поставки начисляется пеня.
            """
        ]
    )

    terms = {term["type"]: term for term in result.execution_terms}

    assert "delivery_deadline" in terms
    assert "5 рабочих дней" in terms["delivery_deadline"]["value"]
    assert terms["delivery_deadline"]["category"] == "delivery"

    assert "payment_terms" in terms
    assert "7 рабочих дней" in terms["payment_terms"]["value"]
    assert terms["payment_terms"]["category"] == "financial"

    assert "advance_payment" in terms
    assert "не предусмотрено" in terms["advance_payment"]["value"]

    assert "warranty_period" in terms
    assert "12 месяцев" in terms["warranty_period"]["value"]

    assert "contract_security" in terms
    assert terms["contract_security"]["severity"] == "high"

    assert "penalties" in terms
    assert terms["penalties"]["category"] == "financial"
