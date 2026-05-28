import json
import sqlite3

from tender_killer.models import ProductProfile, Tender, TenderDocument, TenderItem
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


def test_store_persists_normalized_tender_filter_fields(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()

    tender = Tender(
        source="mosreg_market",
        external_id="mo-1",
        url="https://example.test/mo-1",
        title="Paper supply",
        region="Moscow Oblast",
        status="Reception of proposals",
        raw_payload={
            "federalLawName": "44-\u0424\u0417",
            "customers": [{"inn": "5047152960"}],
            "tradeType": 1,
        },
    )

    store.upsert_tender(tender)

    with sqlite3.connect(store.database_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT law, status_normalized, region_code, source_family, procedure_type, customer_inn
            FROM tenders
            WHERE source = ? AND external_id = ?
            """,
            tender.identity,
        ).fetchone()

    assert dict(row) == {
        "law": "44-\u0424\u0417",
        "status_normalized": "active",
        "region_code": "50",
        "source_family": "mosreg",
        "procedure_type": "electronic_shop",
        "customer_inn": "5047152960",
    }


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


def test_store_replaces_tender_items_on_upsert(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()

    tender = Tender(
        source="mosreg_market",
        external_id="3668200",
        url="https://market.mosreg.ru/Trade/ViewTrade/3668200",
        title="Поставка папок",
        items=[
            TenderItem(
                name="Папка-вкладыш",
                details='Папка-вкладыш Berlingo "Mirror", A4',
                quantity=800.0,
                unit="Штука",
                unit_price=2.0,
                total_price=1600.0,
                okpd2="11.05.01.01.02.01.017",
                classifier_code="11.05.01.01.02.01.017",
                classifier_type="КОЗ-2",
                raw_payload={"Id": "item-1"},
            )
        ],
    )
    updated = Tender(
        source=tender.source,
        external_id=tender.external_id,
        url=tender.url,
        title=tender.title,
        items=[
            TenderItem(
                name="Папка-регистратор",
                quantity=10.0,
                unit="Штука",
                unit_price=150.0,
                total_price=1500.0,
                raw_payload={"Id": "item-2"},
            )
        ],
    )

    store.upsert_tender(tender)
    store.upsert_tender(updated)

    with sqlite3.connect(store.database_path) as connection:
        rows = connection.execute(
            "SELECT name, quantity, unit, unit_price, total_price, okpd2, classifier_code, classifier_type, raw_payload_json "
            "FROM tender_items WHERE source = ? AND external_id = ?",
            tender.identity,
        ).fetchall()

    assert rows == [("Папка-регистратор", 10.0, "Штука", 150.0, 1500.0, None, None, None, '{"Id": "item-2"}')]
    assert json.loads(rows[0][8]) == {"Id": "item-2"}


def test_store_saves_tender_documents_with_metadata(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()

    tender = Tender(
        source="moscow_supplier_portal",
        external_id="10205109",
        url="https://zakupki.mos.ru/auction/10205109",
        title="ТОВАРЫ СТРОИТЕЛЬНЫЕ",
        document_records=[
            TenderDocument(
                url="https://zakupki.mos.ru/newapi/api/FileStorage/Download?id=1",
                name="Техническое задание.docx",
                document_type="Техническое задание",
                source_document_id="1",
                raw_payload={"id": 1},
            )
        ],
    )

    store.upsert_tender(tender)

    with sqlite3.connect(store.database_path) as connection:
        rows = connection.execute(
            "SELECT name, document_type, url, source_document_id, local_path, text_status, raw_payload_json "
            "FROM tender_documents WHERE source = ? AND external_id = ?",
            tender.identity,
        ).fetchall()

    assert rows == [
        (
            "Техническое задание.docx",
            "Техническое задание",
            "https://zakupki.mos.ru/newapi/api/FileStorage/Download?id=1",
            "1",
            None,
            "pending",
            '{"id": 1}',
        )
    ]


def test_store_upserts_product_profiles_without_duplicates_and_deserializes_json(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()

    first = _product_profile(
        position_index=1,
        product_name="Paper A4",
        classifiers=[{"type": "okpd2", "code": "17.12.14", "source": "item"}],
        required_characteristics=["80 gsm"],
        fulfillment_requirements=[{"type": "delivery", "source": "TZ.docx", "value": "Срок поставки 5 дней"}],
        evidence=[{"field": "product_name", "value": "Paper A4"}],
        raw_payload={"row": 1},
    )
    updated = _product_profile(
        position_index=1,
        product_name="Paper A4 premium",
        classifiers=[{"type": "okpd2", "code": "17.12.14", "source": "updated"}],
        required_characteristics=["90 gsm"],
        fulfillment_requirements=[{"type": "warranty", "source": "TZ.docx", "value": "Гарантия 12 месяцев"}],
        evidence=[{"field": "product_name", "value": "Paper A4 premium"}],
        raw_payload={"row": 2},
    )

    store.upsert_product_profiles("moscow", "abc", [first])
    store.upsert_product_profiles("moscow", "abc", [updated])

    profiles = store.get_product_profiles("moscow", "abc")

    assert len(profiles) == 1
    assert profiles[0]["position_index"] == 1
    assert profiles[0]["product_name"] == "Paper A4 premium"
    assert profiles[0]["classifiers"] == [{"type": "okpd2", "code": "17.12.14", "source": "updated"}]
    assert profiles[0]["required_characteristics"] == ["90 gsm"]
    assert profiles[0]["fulfillment_requirements"] == [{"type": "warranty", "source": "TZ.docx", "value": "Гарантия 12 месяцев"}]
    assert profiles[0]["evidence"] == [{"field": "product_name", "value": "Paper A4 premium"}]
    assert profiles[0]["raw_payload"] == {"row": 2}


def test_store_preserves_product_profile_okpd2_distinct_from_classifier_code(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    profile = _product_profile(
        position_index=1,
        product_name="Extinguisher",
        okpd2="28.29.22.110",
        classifier_code="01.02.03.04.05.006",
        classifier_type="КОЗ-2",
    )

    store.upsert_product_profiles("moscow", "abc", [profile])

    saved = store.get_product_profiles("moscow", "abc")
    assert saved[0]["okpd2"] == "28.29.22.110"
    assert saved[0]["classifier_code"] == "01.02.03.04.05.006"


def test_store_persists_and_reads_back_forty_product_profiles(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    profiles = [_product_profile(position_index=index, product_name=f"Item {index}") for index in range(1, 41)]

    store.upsert_product_profiles("moscow", "bulk", profiles)

    saved = store.get_product_profiles("moscow", "bulk")
    assert len(saved) == 40
    assert [profile["position_index"] for profile in saved] == list(range(1, 41))
    assert saved[39]["product_name"] == "Item 40"


def test_store_empty_product_profile_upsert_deletes_existing_profiles(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_product_profiles(
        "moscow",
        "abc",
        [
            _product_profile(position_index=1, product_name="Paper"),
            _product_profile(position_index=2, product_name="Folder"),
        ],
    )

    store.upsert_product_profiles("moscow", "abc", [])

    assert store.get_product_profiles("moscow", "abc") == []


def test_store_preserves_product_profiles_when_tender_is_refreshed(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="moscow",
            external_id="abc",
            url="https://example.test/abc",
            title="Tender",
            items=[TenderItem(name="Paper")],
        )
    )
    store.upsert_product_profiles("moscow", "abc", [_product_profile(position_index=1, product_name="Paper")])

    store.upsert_tender(
        Tender(
            source="moscow",
            external_id="abc",
            url="https://example.test/abc",
            title="Tender refreshed",
            items=[TenderItem(name="Paper"), TenderItem(name="Folder")],
        )
    )

    profiles = store.get_product_profiles("moscow", "abc")
    assert len(profiles) == 1
    assert profiles[0]["product_name"] == "Paper"


def test_store_migrates_existing_minimal_product_profiles_table(tmp_path):
    database_path = tmp_path / "tenders.sqlite"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE product_profiles (
                tender_source TEXT NOT NULL,
                tender_external_id TEXT NOT NULL,
                position_index INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                UNIQUE(tender_source, tender_external_id, position_index)
            )
            """
        )

    store = TenderStore(database_path)
    store.initialize()
    store.upsert_product_profiles("moscow", "abc", [_product_profile(position_index=1, product_name="Paper")])

    profiles = store.get_product_profiles("moscow", "abc")
    assert profiles[0]["product_name"] == "Paper"
    assert profiles[0]["classifiers"] == []
    assert profiles[0]["fulfillment_requirements"] == []
    assert profiles[0]["raw_payload"] == {}


def _product_profile(
    *,
    position_index: int,
    product_name: str,
    classifiers=None,
    required_characteristics=None,
    fulfillment_requirements=None,
    evidence=None,
    raw_payload=None,
    okpd2="17.12.14",
    classifier_code="17.12.14",
    classifier_type="okpd2",
) -> ProductProfile:
    return ProductProfile(
        tender_source="moscow",
        tender_external_id="abc",
        position_index=position_index,
        product_name=product_name,
        normalized_name=product_name.casefold(),
        details="A test product profile",
        category="office",
        quantity=float(position_index),
        unit="pcs",
        unit_price=10.0,
        total_price=10.0 * position_index,
        okpd2=okpd2,
        classifier_code=classifier_code,
        classifier_type=classifier_type,
        classifiers=classifiers or [],
        required_characteristics=required_characteristics or [],
        standards=["GOST 1"],
        cert_documents=["certificate"],
        fulfillment_requirements=fulfillment_requirements or [],
        brand_model=[],
        origin_country_requirements=["country required"],
        search_phrases=[product_name],
        stop_words=["used"],
        evidence=evidence or [],
        profile_status="ready",
        confidence=0.9,
        source="item",
        raw_payload=raw_payload or {},
    )
