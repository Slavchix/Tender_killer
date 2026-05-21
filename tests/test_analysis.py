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


def test_analyze_tender_texts_handles_empty_text_cautiously():
    result = analyze_tender_texts(["", "   "])

    assert result.status == "needs_review"
    assert result.confidence == 0.1
    assert result.summary == "Текст документов не извлечен или пустой."
    assert result.red_flags == ["нет текста для анализа"]
