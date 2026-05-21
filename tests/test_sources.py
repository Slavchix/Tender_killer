from tender_killer.config import Settings
from tender_killer.filter_store import FilterProfileCollection, NamedFilterProfile
from tender_killer.filters import FilterProfile
from tender_killer.adapters.moscow import MoscowSupplierPortalAdapter
from tender_killer.adapters.mosreg import MosregMarketAdapter
from tender_killer.sources import build_adapters, build_adapters_for_collection


def settings(tmp_path):
    return Settings(
        database_path=tmp_path / "db.sqlite",
        telegram_bot_token=None,
        telegram_chat_id=None,
        dry_run=True,
        moscow_url="https://moscow.test/api",
        mosreg_url="https://mosreg.test/api",
        filter_profile_path=None,
        request_timeout_seconds=7,
        bot_auto_search_minutes=30,
        source_max_pages=4,
        source_incremental_overlap_minutes=60,
    )


def test_build_adapters_uses_selected_sources(tmp_path):
    adapters = build_adapters(FilterProfile(keywords=(), sources=("mosreg",)), settings(tmp_path))

    assert [adapter.source for adapter in adapters] == ["mosreg_market"]
    assert adapters[0].url == "https://mosreg.test/api"
    assert adapters[0].max_pages == 4


def test_build_adapters_uses_all_sources_by_default(tmp_path):
    adapters = build_adapters(FilterProfile.default(), settings(tmp_path))

    assert [adapter.source for adapter in adapters] == ["moscow_supplier_portal", "mosreg_market"]


def test_build_adapters_for_collection_uses_union_of_active_profile_sources(tmp_path):
    collection = FilterProfileCollection(
        profiles=(
            NamedFilterProfile("paper", "Бумага", FilterProfile(keywords=(), sources=("moscow",))),
            NamedFilterProfile("cable", "Кабель", FilterProfile(keywords=(), sources=("mosreg",))),
            NamedFilterProfile("disabled", "Выкл", FilterProfile(keywords=(), sources=("moscow",))),
        ),
        active_profile_ids=("paper", "cable"),
    )

    adapters = build_adapters_for_collection(collection, settings(tmp_path))

    assert [adapter.source for adapter in adapters] == ["moscow_supplier_portal", "mosreg_market"]


def test_build_adapters_for_collection_skips_sources_when_no_active_profiles(tmp_path):
    collection = FilterProfileCollection(
        profiles=(
            NamedFilterProfile("paper", "Бумага", FilterProfile(keywords=(), sources=("moscow",))),
        ),
        active_profile_ids=(),
    )

    adapters = build_adapters_for_collection(collection, settings(tmp_path))

    assert adapters == []


def test_moscow_adapter_fetches_active_auctions_from_purchase_query(monkeypatch):
    adapter = MoscowSupplierPortalAdapter()
    monkeypatch.setattr(
        adapter,
        "_fetch_page",
        lambda skip: {
            "count": 1,
            "items": [
                {
                    "auctionId": 10205128,
                    "number": "10205128",
                    "name": "ДЕКОРАЦИИ",
                    "customers": [
                        {
                            "name": "Государственное бюджетное профессиональное образовательное учреждение города Москвы",
                            "inn": "7708044657",
                        }
                    ],
                    "stateName": "Активная",
                    "stateId": 19000002,
                    "startPrice": 50200.0,
                    "regionName": "г Москва",
                    "beginDate": "19.05.2026 14:40:03",
                    "endDate": "19.05.2026 17:40:03",
                    "federalLawName": "44-ФЗ",
                }
            ],
        },
    )
    monkeypatch.setattr(
        adapter,
        "_fetch_auction_detail",
        lambda auction_id: {
            "id": 10205128,
            "files": [{"id": 275314143, "name": "Краткое описание КС 10205128.docx"}],
            "items": [{"name": "Кисть 70мм", "currentValue": 20, "costPerUnit": 220, "okeiName": "шт"}],
        },
    )

    tenders = adapter.fetch()

    assert len(tenders) == 1
    assert tenders[0].external_id == "10205128"
    assert tenders[0].url == "https://zakupki.mos.ru/auction/10205128"
    assert tenders[0].customer == "Государственное бюджетное профессиональное образовательное учреждение города Москвы"
    assert tenders[0].price == 50200.0
    assert tenders[0].status == "Активная"
    assert tenders[0].deadline_at is not None
    assert tenders[0].documents[0].startswith(
        "https://zakupki.mos.ru/newapi/api/FileStorage/Download?id=275314143"
    )
    assert "%D0%9A%D1%80%D0%B0%D1%82%D0%BA%D0%BE%D0%B5" in tenders[0].documents[0]
    assert tenders[0].items[0].name == "Кисть 70мм"
    assert tenders[0].raw_payload["federalLawName"] == "44-ФЗ"
    assert tenders[0].raw_payload["__detail"]["id"] == 10205128


def test_moscow_purchase_query_payload_requests_active_moscow_auctions():
    query = MoscowSupplierPortalAdapter.purchase_query(skip=0, take=50)

    assert query["filter"]["regionPaths"]["values"] == [".1.504."]
    assert query["filter"]["auctionSpecificFilter"]["stateIdIn"] == [19000002]
    assert query["take"] == 50
    assert query["skip"] == 0


def test_moscow_purchase_query_payload_supports_publication_checkpoint():
    published_from = "2026-05-20T10:30:00+00:00"

    query = MoscowSupplierPortalAdapter.purchase_query(skip=0, take=50, published_from=published_from)

    assert query["filter"]["publicationDateFrom"] == published_from


def test_mosreg_adapter_fetches_active_trades_from_post_endpoint(monkeypatch):
    adapter = MosregMarketAdapter()

    def fetch_page(page):
        assert page == 1
        return {
            "totalpages": 1,
            "invdata": [
                {
                    "Id": 3668200,
                    "TradeName": "Поставка товаров для организации проведения ГИА.",
                    "CustomerFullName": "Школа",
                    "InitialPrice": 599817.0,
                    "TradeStateName": "Прием предложений",
                    "FillingApplicationEndDate": "2026-05-28T14:20:00Z",
                    "PublicationDate": "2026-05-15T05:19:46.733Z",
                    "CategoryName": "Прочее",
                }
            ],
        }

    monkeypatch.setattr(adapter, "_fetch_page", fetch_page)
    monkeypatch.setattr(
        adapter,
        "_fetch_trade_documents",
        lambda trade_id: [{"FileName": "Техническое задание.docx", "Url": "https://example.test/tz.docx"}],
    )

    tenders = adapter.fetch()

    assert len(tenders) == 1
    assert tenders[0].external_id == "3668200"
    assert tenders[0].url == "https://market.mosreg.ru/Trade/ViewTrade/3668200"
    assert tenders[0].documents == ["https://example.test/tz.docx"]
    assert tenders[0].raw_payload["__documents"][0]["FileName"] == "Техническое задание.docx"


def test_mosreg_adapter_paginates_until_configured_limit(monkeypatch):
    adapter = MosregMarketAdapter(max_pages=2, enrich_documents=False)
    seen_pages = []

    def fetch_page(page):
        seen_pages.append(page)
        return {
            "totalpages": 3,
            "invdata": [
                {
                    "Id": 3668200 + page,
                    "TradeName": f"Trade {page}",
                    "PublicationDate": f"2026-05-2{page}T05:19:46Z",
                }
            ],
        }

    monkeypatch.setattr(adapter, "_fetch_page", fetch_page)

    tenders = adapter.fetch()

    assert seen_pages == [1, 2]
    assert [tender.external_id for tender in tenders] == ["3668201", "3668202"]


def test_mosreg_trade_search_payload_supports_publication_checkpoint():
    payload = MosregMarketAdapter.trade_search_payload(
        page=1,
        items_per_page=50,
        published_from="2026-05-20T10:30:00+00:00",
    )

    assert payload["filterDateFrom"] == "2026-05-20T10:30:00+00:00"
