from tender_killer.models import Tender
from tender_killer.telegram import build_tender_message


def test_build_tender_message_contains_decision_fields():
    tender = Tender(
        source="moscow_supplier_portal",
        external_id="1",
        url="https://example.test/1",
        title="Поставка бумаги офисной",
        customer="ГБУ Школа",
        region="Москва",
        price=42000,
        currency="RUB",
        status="active",
        delivery_place="Москва",
    )

    message = build_tender_message(tender, ["бумага", "канцелярия"])

    assert "Поставка бумаги офисной" in message
    assert "ГБУ Школа" in message
    assert "42 000.00 RUB" in message
    assert "бумага, канцелярия" in message
    assert "https://example.test/1" in message

