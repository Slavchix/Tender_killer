import json

from tender_killer.filter_store import FilterProfileStore, NamedFilterProfile


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


def test_filter_profile_store_migrates_legacy_filter_to_default_profile(tmp_path):
    path = tmp_path / "filters.json"
    path.write_text(
        json.dumps(
            {
                "keywords": ["бумага"],
                "regions": ["Москва"],
                "sources": ["moscow"],
                "only_active": True,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    collection = FilterProfileStore(path).load_collection()

    assert collection.active_profile_ids == ("default",)
    assert collection.profiles[0].id == "default"
    assert collection.profiles[0].name == "Default"
    assert collection.profiles[0].profile.keywords == ("бумага",)
    assert collection.profiles[0].profile.regions == ("Москва",)


def test_filter_profile_store_saves_and_loads_multiple_profiles(tmp_path):
    path = tmp_path / "filters.json"
    store = FilterProfileStore(path)
    collection = store.load_collection()

    paper = store.add_profile("Бумага", keywords=("бумага",), okpd2=("17.12",))
    cable = store.add_profile("Кабель", keywords=("кабель",), okpd2=("27.32",))
    store.set_profile_enabled("default", False)
    store.set_profile_enabled(cable.id, False)
    loaded = store.load_collection()

    assert [profile.name for profile in loaded.profiles] == ["Default", "Бумага", "Кабель"]
    assert loaded.active_profile_ids == (paper.id,)
    assert isinstance(loaded.profiles[1], NamedFilterProfile)
