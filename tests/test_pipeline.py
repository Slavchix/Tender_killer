from tender_killer.filters import FilterProfile, MaterialFilter, TenderFilter
from tender_killer.models import Tender
from tender_killer.pipeline import TenderPipeline
from tender_killer.storage import TenderStore


class StaticAdapter:
    source = "static"

    def __init__(self, tenders):
        self.tenders = tenders

    def fetch(self):
        return self.tenders


class FailingAdapter:
    source = "failing"

    def fetch(self):
        raise RuntimeError("source unavailable")


class SpyNotifier:
    def __init__(self):
        self.messages = []

    def send(self, text):
        self.messages.append(text)
        return True


def test_pipeline_continues_when_one_source_fails(tmp_path):
    tender = Tender(
        source="static",
        external_id="1",
        url="https://example.test/1",
        title="Поставка кабеля",
        customer="ГБУ",
        region="Москва",
        status="active",
    )
    notifier = SpyNotifier()
    pipeline = TenderPipeline(
        adapters=[FailingAdapter(), StaticAdapter([tender])],
        store=TenderStore(tmp_path / "db.sqlite"),
        material_filter=MaterialFilter(),
        notifier=notifier,
    )

    stats = pipeline.run()

    assert stats.failed_sources == 1
    assert stats.failed_source_names == ("failing",)
    assert stats.fetched == 1
    assert stats.notified == 1
    assert len(notifier.messages) == 1


def test_pipeline_does_not_send_duplicate_notifications(tmp_path):
    tender = Tender(
        source="static",
        external_id="1",
        url="https://example.test/1",
        title="Поставка бумаги",
        customer="ГБУ",
        region="Москва",
        status="active",
    )
    store = TenderStore(tmp_path / "db.sqlite")
    notifier = SpyNotifier()
    pipeline = TenderPipeline(
        adapters=[StaticAdapter([tender])],
        store=store,
        material_filter=MaterialFilter(),
        notifier=notifier,
    )

    first = pipeline.run()
    second = pipeline.run()

    assert first.notified == 1
    assert second.notified == 0
    assert len(notifier.messages) == 1


def test_pipeline_rejects_unknown_activity_with_only_active_filter(tmp_path):
    tender = Tender(
        source="static",
        external_id="1",
        url="https://example.test/1",
        title="Поставка бумаги",
        customer="ГБУ",
        region="Москва",
    )
    notifier = SpyNotifier()
    pipeline = TenderPipeline(
        adapters=[StaticAdapter([tender])],
        store=TenderStore(tmp_path / "db.sqlite"),
        material_filter=TenderFilter(FilterProfile(keywords=("бумага",), only_active=True)),
        notifier=notifier,
    )

    stats = pipeline.run()

    assert stats.matched == 0
    assert stats.notified == 0
    assert notifier.messages == []
