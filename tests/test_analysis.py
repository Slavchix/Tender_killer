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
