from datetime import UTC, datetime, timedelta

from tender_killer.filters import MaterialFilter
from tender_killer.models import Tender


def make_tender(**overrides):
    values = {
        "source": "moscow",
        "external_id": "1",
        "url": "https://example.test/tenders/1",
        "title": "Поставка кабеля и крепежа для учреждения",
        "customer": "ГБУ Тест",
        "region": "Москва",
        "price": 100000.0,
        "currency": "RUB",
        "status": "active",
        "published_at": datetime.now(UTC),
        "deadline_at": datetime.now(UTC) + timedelta(days=1),
        "delivery_place": "Москва",
        "category": None,
        "okpd2": None,
        "documents": [],
        "raw_payload": {},
    }
    values.update(overrides)
    return Tender(**values)


def test_material_filter_accepts_broad_material_keywords():
    result = MaterialFilter().match(make_tender())

    assert result.matched is True
    assert "keyword:кабель" in result.reasons
    assert "keyword:крепеж" in result.reasons


def test_material_filter_rejects_unrelated_services():
    result = MaterialFilter().match(
        make_tender(
            title="Оказание услуг по организации праздничного мероприятия",
            category="Услуги",
        )
    )

    assert result.matched is False
    assert result.reasons == []


def test_material_filter_rejects_expired_tenders():
    result = MaterialFilter().match(
        make_tender(deadline_at=datetime.now(UTC) - timedelta(hours=1))
    )

    assert result.matched is False
    assert "deadline_expired" in result.reasons
