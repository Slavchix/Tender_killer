from tender_killer.config import Settings
from tender_killer.filter_store import FilterProfileCollection, NamedFilterProfile
from tender_killer.filters import FilterProfile
from tender_killer.adapters.base import AdapterError
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
    )


def test_build_adapters_uses_selected_sources(tmp_path):
    adapters = build_adapters(FilterProfile(keywords=(), sources=("mosreg",)), settings(tmp_path))

    assert [adapter.source for adapter in adapters] == ["mosreg_market"]
    assert adapters[0].url == "https://mosreg.test/api"


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


def test_moscow_adapter_treats_known_entity_endpoint_error_as_empty(monkeypatch):
    adapter = MoscowSupplierPortalAdapter("https://zakupki.mos.ru/custom")

    def fail_fetch_text(url):
        raise AdapterError(f"{url}: HTTP 400 Bad Request. {{\"message\":\"Не указан идентификатор КС.\"}}")

    monkeypatch.setattr(adapter, "fetch_text", fail_fetch_text)

    assert adapter.fetch() == []


def test_moscow_adapter_skips_default_placeholder_endpoint(monkeypatch):
    adapter = MoscowSupplierPortalAdapter()

    def fail_fetch_text(url):
        raise AssertionError("default placeholder endpoint should not be requested")

    monkeypatch.setattr(adapter, "fetch_text", fail_fetch_text)

    assert adapter.fetch() == []


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

    tenders = adapter.fetch()

    assert len(tenders) == 1
    assert tenders[0].external_id == "3668200"
    assert tenders[0].url == "https://market.mosreg.ru/Trade/ViewTrade/3668200"
