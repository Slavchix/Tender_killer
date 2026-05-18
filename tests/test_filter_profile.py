import json

from tender_killer.filters import FilterProfile, TenderFilter
from tender_killer.models import Tender


def tender(**overrides):
    values = {
        "source": "moscow",
        "external_id": "1",
        "url": "https://example.test/1",
        "title": "Поставка бумаги офисной",
        "customer": "ГБУ",
        "region": "Москва",
        "price": 50_000,
        "currency": "RUB",
        "status": "active",
        "delivery_place": "Москва",
        "category": "Канцелярия",
        "okpd2": "17.12.14",
    }
    values.update(overrides)
    return Tender(**values)


def test_filter_profile_uses_custom_keywords():
    profile = FilterProfile(keywords=("бумага",), exclude_keywords=())

    result = TenderFilter(profile).match(tender())

    assert result.matched is True
    assert result.reasons == ["keyword:бумага"]


def test_filter_profile_rejects_excluded_keywords():
    profile = FilterProfile(keywords=("бумага",), exclude_keywords=("услуги",))

    result = TenderFilter(profile).match(tender(title="Услуги по поставке бумаги"))

    assert result.matched is False
    assert result.reasons == ["excluded:услуги"]


def test_filter_profile_applies_price_range():
    profile = FilterProfile(keywords=("бумага",), min_price=100_000, max_price=200_000)

    result = TenderFilter(profile).match(tender(price=50_000))

    assert result.matched is False
    assert result.reasons == ["price_below_min"]


def test_filter_profile_applies_region_allowlist():
    profile = FilterProfile(keywords=("бумага",), regions=("Московская область",))

    result = TenderFilter(profile).match(tender(region="Москва", delivery_place="Москва"))

    assert result.matched is False
    assert result.reasons == ["region_not_allowed"]


def test_filter_profile_loads_from_json_file(tmp_path):
    path = tmp_path / "filters.json"
    path.write_text(
        json.dumps(
            {
                "keywords": ["кабель", "крепеж"],
                "exclude_keywords": ["услуги"],
                "regions": ["Москва"],
                "min_price": 10_000,
                "max_price": 500_000,
                "statuses": ["active"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    profile = FilterProfile.from_json_file(path)

    assert profile.keywords == ("кабель", "крепеж")
    assert profile.exclude_keywords == ("услуги",)
    assert profile.regions == ("Москва",)
    assert profile.min_price == 10_000
    assert profile.max_price == 500_000
    assert profile.statuses == ("active",)

