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
        "purchaseNumber": "MO-77",
        "subject": "Поставка хозяйственных товаров",
        "customer": {"name": "Администрация"},
        "maxPrice": "150000.50",
        "state": "active",
        "deadline": "2026-05-21T12:30:00+03:00",
        "deliveryPlace": "Московская область",
        "href": "https://market.mosreg.ru/purchase/MO-77",
    }

    tender = MosregMarketAdapter().normalize_payload(payload)

    assert tender.source == "mosreg_market"
    assert tender.external_id == "MO-77"
    assert tender.title == "Поставка хозяйственных товаров"
    assert tender.customer == "Администрация"
    assert tender.price == 150000.50


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
