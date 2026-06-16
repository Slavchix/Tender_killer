from __future__ import annotations

from tender_killer.analysis_interpretation_service import build_fact_interpretation


def test_build_fact_interpretation_explains_advance_without_inventing():
    interpretation = build_fact_interpretation(
        {
            "label": "Аванс",
            "category": "financial",
            "value": "Авансирование не предусмотрено.",
            "fragment": "Авансирование не предусмотрено. Оплата после приемки товара.",
            "source_label": "Контракт.docx · стр. 5",
        }
    )

    assert interpretation["found"] == "Авансирование не предусмотрено."
    assert "авансом" in interpretation["meaning"].casefold()
    assert "оборот" in interpretation["impact"].casefold()
    assert "срок оплаты" in interpretation["action"].casefold()
    assert interpretation["confidence"] == "value"


def test_build_fact_interpretation_reports_missing_exact_value_honestly():
    interpretation = build_fact_interpretation(
        {
            "label": "Оплата",
            "category": "payment",
            "description": "Это влияет на денежный цикл: оплату, аванс, удержания, обеспечение или резервы.",
        }
    )

    assert interpretation["found"] == ""
    assert interpretation["meaning"] == "Точная формулировка в извлеченном тексте не найдена."
    assert interpretation["confidence"] == "missing"
def test_build_fact_interpretation_normalizes_payment_sentence_from_fragment():
    interpretation = build_fact_interpretation(
        {
            "label": "Оплата",
            "category": "payment",
            "fragment": "7.3. Оплата производится в течение 7 рабочих дней с даты подписания УПД.",
        }
    )

    assert interpretation["found"] == "Оплата производится в течение 7 рабочих дней с даты подписания УПД."
    assert "7 рабочих дней" in interpretation["meaning"]
    assert "УПД" in interpretation["action"]
    assert interpretation["confidence"] == "fragment"


def test_build_fact_interpretation_explains_contract_security_percent():
    interpretation = build_fact_interpretation(
        {
            "label": "Обеспечение исполнения контракта",
            "category": "financial",
            "value": "Размер обеспечения исполнения контракта составляет 5 % начальной цены контракта.",
        }
    )

    assert interpretation["found"] == "Размер обеспечения исполнения контракта составляет 5% начальной цены контракта."
    assert "5%" in interpretation["meaning"]
    assert "банковская гарантия" in interpretation["impact"].casefold()
    assert "срок возврата" in interpretation["action"].casefold()


def test_build_fact_interpretation_explains_vat_condition():
    interpretation = build_fact_interpretation(
        {
            "label": "НДС",
            "category": "financial",
            "value": "Цена контракта включает НДС 20%.",
        }
    )

    assert interpretation["found"] == "Цена контракта включает НДС 20%."
    assert "НДС 20%" in interpretation["meaning"]
    assert "себестоимость" in interpretation["impact"].casefold()
    assert "ставку ндс" in interpretation["action"].casefold()


def test_build_fact_interpretation_explains_closing_documents():
    interpretation = build_fact_interpretation(
        {
            "label": "Закрывающие документы",
            "category": "acceptance",
            "value": "Поставщик предоставляет УПД и акт приема-передачи товара.",
        }
    )

    assert interpretation["found"] == "Поставщик предоставляет УПД и акт приема-передачи товара."
    assert "УПД" in interpretation["meaning"]
    assert "оплаты" in interpretation["impact"].casefold()
    assert "закрывающие документы" in interpretation["action"].casefold()


def test_build_fact_interpretation_explains_service_scope():
    interpretation = build_fact_interpretation(
        {
            "label": "Монтаж/пусконаладка",
            "category": "delivery",
            "value": "Поставщик выполняет монтаж, пусконаладку и ввод оборудования в эксплуатацию.",
        }
    )

    assert interpretation["found"] == "Поставщик выполняет монтаж, пусконаладку и ввод оборудования в эксплуатацию."
    assert "пусконалад" in interpretation["meaning"].casefold()
    assert "дополнительные расходы" in interpretation["impact"].casefold()
    assert "специалист" in interpretation["action"].casefold()
