from tender_killer.filter_store import FilterProfileStore


def test_filter_profile_store_creates_default_file(tmp_path):
    path = tmp_path / "filters.json"
    store = FilterProfileStore(path)

    profile = store.load()

    assert profile.only_active is True
    assert profile.sources == ("moscow", "mosreg")
    assert path.exists()


def test_filter_profile_store_updates_profile(tmp_path):
    path = tmp_path / "filters.json"
    store = FilterProfileStore(path)

    updated = store.update(
        regions=("Москва",),
        min_price=10_000,
        max_price=500_000,
        okpd2=("17.12", "27.32.13"),
        sources=("moscow",),
        only_active=True,
        keywords=(),
    )
    loaded = store.load()

    assert updated == loaded
    assert loaded.regions == ("Москва",)
    assert loaded.min_price == 10_000
    assert loaded.max_price == 500_000
    assert loaded.okpd2 == ("17.12", "27.32.13")
    assert loaded.sources == ("moscow",)
    assert loaded.keywords == ()

