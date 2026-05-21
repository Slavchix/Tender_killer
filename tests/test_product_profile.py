from __future__ import annotations

from tender_killer.product_profile import build_product_profiles


def test_build_product_profiles_from_structured_items_and_text():
    tender = {
        "title": "Поставка бумаги офисной",
        "category": "Канцелярские товары",
        "okpd2": "17.12",
        "items": [
            {
                "name": "Бумага офисная А4",
                "details": "Белизна не менее 146 CIE, плотность 80 г/м2",
                "quantity": 100,
                "unit": "пачка",
                "okpd2": "17.12.14.110",
                "classifier_code": "17.12.14.110",
                "classifier_type": "ОКПД2",
            }
        ],
        "document_records": [
            {
                "text_content": "Товар должен соответствовать ГОСТ. Требуется сертификат соответствия. Формат А4."
            }
        ],
    }

    profiles = build_product_profiles(tender)

    assert len(profiles) == 1
    profile = profiles[0]
    assert profile["product_name"] == "Бумага офисная А4"
    assert profile["category"] == "Канцелярские товары"
    assert profile["okpd2"] == "17.12.14.110"
    assert profile["classifier_code"] == "17.12.14.110"
    assert profile["classifier_type"] == "ОКПД2"
    assert profile["quantity"] == 100
    assert profile["unit"] == "пачка"
    assert "Белизна не менее 146 CIE, плотность 80 г/м2" in profile["required_characteristics"]
    assert "ГОСТ" in profile["required_characteristics"]
    assert "сертификат соответствия" in profile["required_characteristics"]
    assert "Бумага офисная А4" in profile["search_phrases"]
    assert "Бумага офисная А4 17.12.14.110" in profile["search_phrases"]


def test_build_product_profiles_falls_back_to_card_subject_without_items():
    tender = {
        "title": "Поставка садовых инструментов и комплектующих",
        "category": "Хозяйственные товары",
        "okpd2": "25.73.10",
        "price": 191156.0,
        "items": [],
        "document_records": [],
    }

    profiles = build_product_profiles(tender)

    assert len(profiles) == 1
    profile = profiles[0]
    assert profile["position_index"] == 1
    assert profile["product_name"] == "Поставка садовых инструментов и комплектующих"
    assert profile["category"] == "Хозяйственные товары"
    assert profile["okpd2"] == "25.73.10"
    assert profile["classifier_code"] == "25.73.10"
    assert profile["classifier_type"] == "ОКПД2"
    assert profile["source"] == "card"
    assert profile["profile_status"] == "needs_review"
    assert profile["confidence"] < 0.7
    assert profile["raw_payload"] == {}
    assert profile["evidence"] == [
        {
            "field": "product_name",
            "source": "tender.title",
            "value": "Поставка садовых инструментов и комплектующих",
        },
        {"field": "classifier", "source": "tender.okpd2", "value": "25.73.10"},
    ]


def test_build_product_profiles_returns_persistent_shape_for_extinguisher_with_koz2_and_okpd2():
    tender = {
        "source": "moscow",
        "external_id": "123-abc",
        "title": "Поставка огнетушителей",
        "category": "Пожарная безопасность",
        "items": [
            {
                "position_index": 3,
                "name": "Огнетушитель порошковый ОП-5",
                "details": "Масса заряда не менее 5 кг",
                "quantity": 12,
                "unit": "шт",
                "unit_price": 1500.0,
                "total_price": 18000.0,
                "okpd2": "28.29.22.110",
                "classifier_code": "01.02.03.04.05",
                "classifier_type": "koz2",
            }
        ],
        "document_records": [
            {
                "text_content": (
                    "Товар должен соответствовать ГОСТ Р 51057-2001, ТР ТС 032/2013. "
                    "Требуется сертификат соответствия, декларация соответствия, СГР. "
                    "Страна происхождения - Россия, допускается российский товар."
                )
            }
        ],
    }

    profile = build_product_profiles(tender)[0]

    assert set(profile) == {
        "tender_source",
        "tender_external_id",
        "position_index",
        "product_name",
        "normalized_name",
        "details",
        "category",
        "okpd2",
        "quantity",
        "unit",
        "unit_price",
        "total_price",
        "classifier_code",
        "classifier_type",
        "classifiers",
        "required_characteristics",
        "standards",
        "cert_documents",
        "brand_model",
        "origin_country_requirements",
        "search_phrases",
        "stop_words",
        "evidence",
        "profile_status",
        "confidence",
        "source",
        "raw_payload",
    }
    assert profile["tender_source"] == "moscow"
    assert profile["tender_external_id"] == "123-abc"
    assert profile["position_index"] == 3
    assert profile["product_name"] == "Огнетушитель порошковый ОП-5"
    assert profile["normalized_name"] == "огнетушитель порошковый оп-5"
    assert profile["details"] == "Масса заряда не менее 5 кг"
    assert profile["quantity"] == 12
    assert profile["unit"] == "шт"
    assert profile["unit_price"] == 1500.0
    assert profile["total_price"] == 18000.0
    assert profile["classifier_code"] == "01.02.03.04.05"
    assert profile["classifier_type"] == "koz2"
    assert profile["classifiers"] == [
        {"type": "koz2", "code": "01.02.03.04.05", "source": "tender_item"},
        {"type": "okpd2", "code": "28.29.22.110", "source": "tender_item"},
    ]
    assert "Масса заряда не менее 5 кг" in profile["required_characteristics"]
    assert "ГОСТ Р 51057-2001" in profile["standards"]
    assert "ТР ТС 032/2013" in profile["standards"]
    assert "сертификат соответствия" in profile["cert_documents"]
    assert "декларация соответствия" in profile["cert_documents"]
    assert "СГР" in profile["cert_documents"]
    assert "страна происхождения" in profile["origin_country_requirements"]
    assert "российский товар" in profile["origin_country_requirements"]
    assert profile["brand_model"] == []
    assert profile["profile_status"] == "ready"
    assert profile["confidence"] >= 0.7
    assert profile["source"] == "item"
    assert profile["raw_payload"] == {}
    assert {
        "field": "product_name",
        "source": "tender_item.name",
        "value": "Огнетушитель порошковый ОП-5",
    } in profile["evidence"]
    assert {"field": "classifier", "source": "tender_item.classifier_code", "value": "01.02.03.04.05"} in profile["evidence"]
    assert {"field": "details", "source": "tender_item.details", "value": "Масса заряда не менее 5 кг"} in profile["evidence"]
    assert {
        "field": "document_requirement",
        "source": "document_1",
        "value": "Товар должен соответствовать ГОСТ Р 51057-2001, ТР ТС 032/2013.",
    } in profile["evidence"]
    assert profile["search_phrases"] == [
        "Огнетушитель порошковый ОП-5",
        "Масса заряда не менее 5 кг",
        "Огнетушитель порошковый ОП-5 28.29.22.110",
        "Огнетушитель порошковый ОП-5 01.02.03.04.05",
    ]


def test_build_product_profiles_returns_one_profile_per_item_for_large_tender():
    tender = {
        "source": "mosreg",
        "external_id": "bulk-40",
        "title": "Поставка товаров",
        "items": [
            {
                "name": f"Товар {index}",
                "details": f"Характеристика {index}",
                "quantity": index,
                "unit": "шт",
                "okpd2": f"10.20.30.{index:03d}",
            }
            for index in range(1, 41)
        ],
    }

    profiles = build_product_profiles(tender)

    assert len(profiles) == 40
    assert [profile["position_index"] for profile in profiles] == list(range(1, 41))
    assert [profile["product_name"] for profile in profiles] == [f"Товар {index}" for index in range(1, 41)]


def test_build_product_profiles_traces_classifier_source_from_item_okpd2_when_classifier_code_absent():
    tender = {
        "title": "Поставка товара",
        "okpd2": "99.99.99",
        "items": [
            {
                "name": "Картридж",
                "okpd2": "28.23.25.000",
            }
        ],
    }

    profile = build_product_profiles(tender)[0]

    assert {"field": "classifier", "source": "tender_item.okpd2", "value": "28.23.25.000"} in profile["evidence"]


def test_build_product_profiles_links_document_requirements_to_item_profile():
    tender = {
        "source": "mosreg_market",
        "external_id": "3666760",
        "title": "Поставка зачетных книжек для нужд колледжа",
        "items": [
            {
                "position_index": 1,
                "name": "Бланк из бумаги или картона",
                "details": "Поставка зачетных книжек",
                "quantity": 700,
                "unit": "Штука",
                "classifier_code": "11.105.01.02.08.01.008",
                "classifier_type": "КОЗ-2",
            }
        ],
        "document_records": [
            {
                "name": "Техническое задание.docx",
                "text_content": (
                    "Поставка зачетных книжек осуществляется партиями по заявке заказчика. "
                    "Бланк из бумаги или картона должен соответствовать требованиям качества. "
                    "Поставщик предоставляет сертификат или декларацию соответствия."
                ),
            }
        ],
    }

    profile = build_product_profiles(tender)[0]

    assert "Бланк из бумаги или картона должен соответствовать требованиям качества." in profile["required_characteristics"]
    assert {
        "field": "document_requirement",
        "source": "Техническое задание.docx",
        "value": "Бланк из бумаги или картона должен соответствовать требованиям качества.",
    } in profile["evidence"]


def test_build_product_profiles_extracts_concrete_tz_requirements_without_llm():
    tender = {
        "source": "mosreg_market",
        "external_id": "paper-1",
        "title": "Поставка бумаги офисной",
        "items": [
            {
                "position_index": 1,
                "name": "Бумага офисная А4",
                "details": "Бумага офисная белая",
                "quantity": 100,
                "unit": "пачка",
                "classifier_code": "17.12.14.110",
                "classifier_type": "ОКПД2",
            }
        ],
        "document_records": [
            {
                "name": "Описание объекта закупки.docx",
                "text_content": (
                    "Бумага офисная А4 должна иметь формат А4, плотность не менее 80 г/м2, "
                    "белизну не менее 146 CIE, количество листов в пачке не менее 500. "
                    "Товар должен быть новым, не бывшим в употреблении. "
                    "Поставщик предоставляет декларацию соответствия и паспорт качества."
                ),
            }
        ],
    }

    profile = build_product_profiles(tender)[0]

    assert "формат А4" in profile["required_characteristics"]
    assert "плотность не менее 80 г/м2" in profile["required_characteristics"]
    assert "белизну не менее 146 CIE" in profile["required_characteristics"]
    assert "количество листов в пачке не менее 500" in profile["required_characteristics"]
    assert "новый товар" in profile["required_characteristics"]
    assert "декларация соответствия" in profile["cert_documents"]
    assert "паспорт качества" in profile["cert_documents"]
    assert {
        "field": "document_requirement",
        "source": "Описание объекта закупки.docx",
        "value": (
            "Бумага офисная А4 должна иметь формат А4, плотность не менее 80 г/м2, "
            "белизну не менее 146 CIE, количество листов в пачке не менее 500."
        ),
    } in profile["evidence"]


def test_build_product_profiles_extracts_national_regime_and_registry_requirements():
    tender = {
        "title": "Поставка мебели",
        "items": [{"name": "Стол письменный", "details": "Стол офисный", "quantity": 10, "unit": "шт"}],
        "document_records": [
            {
                "name": "Требования к закупке.docx",
                "text_content": (
                    "При исполнении контракта применяется национальный режим по постановлению 1875. "
                    "Участник указывает страну происхождения товара. "
                    "Товар должен быть включен в реестр российской промышленной продукции."
                ),
            }
        ],
    }

    profile = build_product_profiles(tender)[0]

    assert "национальный режим / ПП 1875" in profile["origin_country_requirements"]
    assert "страна происхождения товара" in profile["origin_country_requirements"]
    assert "реестр российской промышленной продукции" in profile["origin_country_requirements"]
