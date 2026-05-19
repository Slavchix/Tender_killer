from tender_killer.filter_store import FilterProfileCollection, NamedFilterProfile
from tender_killer.filters import FilterProfile, MultiProfileTenderFilter
from tender_killer.models import Tender


def tender(**overrides):
    values = {
        "source": "static",
        "external_id": "1",
        "url": "https://example.test/1",
        "title": "Поставка бумаги офисной",
        "customer": "ГБУ",
        "region": "Москва",
        "status": "active",
        "okpd2": "17.12.14",
    }
    values.update(overrides)
    return Tender(**values)


def test_multi_profile_filter_matches_active_profile():
    collection = FilterProfileCollection(
        profiles=(
            NamedFilterProfile(
                id="paper",
                name="Бумага",
                profile=FilterProfile(keywords=("бумага",), okpd2=("17.12",)),
            ),
            NamedFilterProfile(
                id="cable",
                name="Кабель",
                profile=FilterProfile(keywords=("кабель",), okpd2=("27.32",)),
            ),
        ),
        active_profile_ids=("paper",),
    )

    result = MultiProfileTenderFilter(collection).match(tender())

    assert result.matched is True
    assert "profile:Бумага" in result.reasons
    assert "keyword:бумага" in result.reasons


def test_multi_profile_filter_ignores_disabled_profile():
    collection = FilterProfileCollection(
        profiles=(
            NamedFilterProfile(
                id="paper",
                name="Бумага",
                profile=FilterProfile(keywords=("бумага",), okpd2=("17.12",)),
            ),
        ),
        active_profile_ids=(),
    )

    result = MultiProfileTenderFilter(collection).match(tender())

    assert result.matched is False
    assert result.reasons == []
