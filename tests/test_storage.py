from tender_killer.models import Tender
from tender_killer.storage import TenderStore


def test_store_deduplicates_by_source_and_external_id(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()

    tender = Tender(
        source="moscow",
        external_id="abc",
        url="https://example.test/abc",
        title="Поставка бумаги",
        customer="ГБУ",
        region="Москва",
        price=10.0,
        currency="RUB",
        status="active",
        documents=["https://example.test/doc.pdf"],
        raw_payload={"id": "abc"},
    )

    first = store.upsert_tender(tender)
    second = store.upsert_tender(tender)

    assert first.created is True
    assert second.created is False
    assert store.count_tenders() == 1


def test_store_tracks_notification_state(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()

    tender = Tender(
        source="mosreg",
        external_id="mo-1",
        url="https://example.test/mo-1",
        title="Поставка крепежа",
        customer="Администрация",
        region="Московская область",
        price=None,
        currency="RUB",
        status="active",
    )
    store.upsert_tender(tender)

    assert store.was_notified(tender) is False
    store.mark_notified(tender)
    assert store.was_notified(tender) is True

