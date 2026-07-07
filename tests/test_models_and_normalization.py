import pytest

from tender_killer.adapters.base import AdapterError
from tender_killer.adapters.moscow import MoscowSupplierPortalAdapter
from tender_killer.adapters.mosreg import MosregMarketAdapter
from tender_killer.models import Tender


def test_moscow_adapter_normalizes_json_payload():
    payload = {
        "id": 123,
        "name": "Поставка бумаги офисной",
        "customerName": "ГБУ Школа",
        "price": 42000,
        "status": "Прием заявок",
        "endDate": "2026-05-20T10:00:00+03:00",
        "deliveryAddress": "г. Москва, ул. Тестовая, 1",
        "url": "/tender/123",
        "okpd2": "17.12.14",
    }

    tender = MoscowSupplierPortalAdapter().normalize_payload(payload)

    assert isinstance(tender, Tender)
    assert tender.source == "moscow_supplier_portal"
    assert tender.external_id == "123"
    assert tender.title == "Поставка бумаги офисной"
    assert tender.customer == "ГБУ Школа"
    assert tender.price == 42000
    assert tender.okpd2 == "17.12.14"


def test_moscow_adapter_normalizes_enriched_detail_items_and_documents():
    payload = {
        "auctionId": 10205109,
        "number": "10205109",
        "name": "ТОВАРЫ СТРОИТЕЛЬНЫЕ",
        "stateName": "Активная",
        "__detail": {
            "id": 10205109,
            "name": "ТОВАРЫ СТРОИТЕЛЬНЫЕ",
            "federalLawName": "44-ФЗ",
            "customer": {"name": "Школа"},
            "startCost": 86330.0,
            "state": {"name": "Активная"},
            "endDate": "19.05.2026 17:26:05",
            "deliveries": [{"deliveryPlace": "г Москва, Малый Козловский переулок, 3"}],
            "items": [
                {
                    "name": "Краска акриловая",
                    "currentValue": 50.0,
                    "costPerUnit": 1567.0,
                    "okeiName": "шт",
                    "okpdName": "Краски на основе акриловых полимеров",
                    "productionDirectoryName": "Краски",
                }
            ],
            "files": [{"id": 275311511, "name": "Проект контракта.pdf"}],
        },
    }

    tender = MoscowSupplierPortalAdapter().normalize_payload(payload)

    assert tender.customer == "Школа"
    assert tender.price == 86330.0
    assert tender.delivery_place == "г Москва, Малый Козловский переулок, 3"
    assert tender.documents[0].startswith("https://zakupki.mos.ru/newapi/api/FileStorage/Download?id=275311511")
    assert "%D0%9F%D1%80%D0%BE%D0%B5%D0%BA%D1%82" in tender.documents[0]
    assert len(tender.items) == 1
    assert tender.items[0].name == "Краска акриловая"
    assert tender.items[0].details == "Краски"
    assert tender.items[0].quantity == 50.0
    assert tender.items[0].unit == "шт"
    assert tender.items[0].unit_price == 1567.0
    assert tender.items[0].total_price == 78350.0
    assert tender.items[0].okpd2 == "Краски на основе акриловых полимеров"


def test_adapter_extracts_json_with_utf8_bom():
    payloads = MoscowSupplierPortalAdapter().extract_payloads(
        '\ufeff{"items":[{"id":123,"name":"Поставка бумаги"}]}'
    )

    assert payloads == [{"id": 123, "name": "Поставка бумаги"}]


def test_moscow_adapter_rejects_payload_without_detail_link():
    with pytest.raises(AdapterError):
        MoscowSupplierPortalAdapter().normalize_payload(
            {"id": 123, "name": "Paper supply"}
        )


def test_mosreg_adapter_rejects_payload_without_detail_link():
    with pytest.raises(AdapterError):
        MosregMarketAdapter().normalize_payload(
            {"purchaseNumber": "MO-77", "subject": "Cable supply"}
        )


def test_mosreg_adapter_normalizes_json_payload():
    payload = {
        "Id": 3668200,
        "TradeName": "Поставка хозяйственных товаров",
        "CustomerFullName": "Администрация",
        "InitialPrice": "150000.50",
        "TradeStateName": "Прием предложений",
        "FillingApplicationEndDate": "2026-05-21T12:30:00+03:00",
        "CategoryName": "Хозтовары",
    }

    tender = MosregMarketAdapter().normalize_payload(payload)

    assert tender.source == "mosreg_market"
    assert tender.external_id == "3668200"
    assert tender.title == "Поставка хозяйственных товаров"
    assert tender.customer == "Администрация"
    assert tender.price == 150000.50
    assert tender.status == "Прием предложений"
    assert tender.url == "https://market.mosreg.ru/Trade/ViewTrade/3668200"
    assert tender.documents == ["https://api.market.mosreg.ru/api/Trade/3668200/GetTradeDocuments"]


def test_mosreg_adapter_normalizes_items_from_trade_payload():
    payload = {
        "Id": 3668200,
        "TradeName": "Поставка товаров для организации проведения ГИА.",
        "TradeObjects": [
            {
                "ProductName": "Файл-вкладыш",
                "DetailedName": 'Папка-вкладыш Berlingo "Mirror", A4',
                "Quantity": "800,0000000000",
                "UnitName": "Штука",
                "UnitPrice": "2,0000",
                "TotalPrice": "1600,00",
                "Koz2Value": "11.05.01.01.02.01.017",
                "ClassificatorType": "КОЗ-2",
            }
        ],
    }

    tender = MosregMarketAdapter().normalize_payload(payload)

    assert len(tender.items) == 1
    assert tender.items[0].name == "Файл-вкладыш"
    assert tender.items[0].details == 'Папка-вкладыш Berlingo "Mirror", A4'
    assert tender.items[0].quantity == 800.0
    assert tender.items[0].unit == "Штука"
    assert tender.items[0].unit_price == 2.0
    assert tender.items[0].total_price == 1600.0
    assert tender.items[0].okpd2 == "11.05.01.01.02.01.017"
    assert tender.items[0].classifier_code == "11.05.01.01.02.01.017"
    assert tender.items[0].classifier_type == "КОЗ-2"


def test_mosreg_adapter_normalizes_items_from_trade_html_card():
    payload = {
        "Id": 3666760,
        "TradeName": "Поставка зачетных книжек",
        "__html": """
        <div class="informationAboutCustomer__resultBlock objectPurchase">
          <div class="outputResults__oneResult">
            <p class="outputResults__oneResult-top"><b>№</b>1</p>
            <div class="outputResults__oneResult-leftPart leftPart">
              <p class="leftPart__parag"><span class="grayText">Наименование товара, работ, услуг:</span> Бланк из бумаги или картона</p>
              <p class="leftPart__parag"><span class="grayText">Детализированное наименование:</span> Поставка зачетных книжек</p>
              <p class="leftPart__parag"><span class="grayText">Код классификатор:</span><span>11.105.01.02.08.01.008</span></p>
              <p class="leftPart__parag"><span class="grayText">Тип классификатор:</span><span>КОЗ-2</span></p>
            </div>
            <div class="outputResults__oneResult-centerPart centerPart">
              <p class="centerPart__contentResult-parag"><span class="grayText">Единицы измерения:</span> Штука</p>
              <p class="centerPart__contentResult-parag"><span class="grayText">Количество:</span> 700,00000000000</p>
            </div>
            <div class="outputResults__oneResult-rightPart rightPart">
              <p class="rightPart__contentResult-parag"><span class="grayText">Стоимость единицы продукции ( в т.ч. НДС при наличии):</span> 150,91000</p>
              <p class="rightPart__contentResult-parag"><span class="grayText">Стоимость поставленого товара, выполненых работ, оказываемых услуг ( в т.ч. НДС при наличии):</span> 105637,00</p>
            </div>
          </div>
        </div>
        """,
    }

    tender = MosregMarketAdapter().normalize_payload(payload)

    assert len(tender.items) == 1
    assert tender.items[0].name == "Бланк из бумаги или картона"
    assert tender.items[0].details == "Поставка зачетных книжек"
    assert tender.items[0].quantity == 700.0
    assert tender.items[0].unit == "Штука"
    assert tender.items[0].unit_price == 150.91
    assert tender.items[0].total_price == 105637.0
    assert tender.items[0].classifier_code == "11.105.01.02.08.01.008"
    assert tender.items[0].classifier_type == "КОЗ-2"


def test_mosreg_adapter_uses_real_document_urls_from_enriched_payload():
    payload = {
        "Id": 3668200,
        "TradeName": "Поставка товаров",
        "__documents": [
            {
                "FileName": "Техническое задание.docx",
                "Url": "https://easuz.mosreg.ru/file/docx",
            }
        ],
    }

    tender = MosregMarketAdapter().normalize_payload(payload)

    assert tender.documents == ["https://easuz.mosreg.ru/file/docx"]
    assert tender.raw_payload["__documents"][0]["FileName"] == "Техническое задание.docx"


def test_production_adapters_do_not_extract_navigation_html_as_tenders():
    html = """
    <html>
      <body>
        <a href="/">Электронный магазин Московской области</a>
        <a href="/about">О магазине</a>
      </body>
    </html>
    """

    assert MosregMarketAdapter().extract_payloads(html) == []
    assert MoscowSupplierPortalAdapter().extract_payloads(html) == []


def test_mosreg_adapter_rejects_homepage_payload():
    with pytest.raises(AdapterError):
        MosregMarketAdapter().normalize_payload(
            {
                "purchaseNumber": "MO-77",
                "subject": "Электронный магазин Московской области",
                "href": "/",
            }
        )
