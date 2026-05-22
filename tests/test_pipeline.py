from datetime import UTC, datetime

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


class CheckpointAdapter:
    source = "checkpoint"

    def __init__(self, tenders):
        self.tenders = tenders
        self.published_from = None
        self.seen_published_from = None

    def fetch(self):
        self.seen_published_from = self.published_from
        return self.tenders


class SpyNotifier:
    def __init__(self):
        self.messages = []
        self.reply_markups = []

    def send(self, text, reply_markup=None):
        self.messages.append(text)
        self.reply_markups.append(reply_markup)
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
    assert stats.failed_source_errors == ("failing: source unavailable",)
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


def test_pipeline_new_only_notification_mode_skips_existing_unnotified_tenders(tmp_path):
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
    store.initialize()
    store.upsert_tender(tender)
    notifier = SpyNotifier()
    pipeline = TenderPipeline(
        adapters=[StaticAdapter([tender])],
        store=store,
        material_filter=MaterialFilter(),
        notifier=notifier,
        notify_mode="new_only",
    )

    stats = pipeline.run()

    assert stats.saved == 0
    assert stats.matched == 1
    assert stats.notified == 0
    assert notifier.messages == []


def test_pipeline_new_only_notification_mode_sends_new_tenders(tmp_path):
    tender = Tender(
        source="static",
        external_id="1",
        url="https://example.test/1",
        title="Поставка бумаги",
        customer="ГБУ",
        region="Москва",
        status="active",
    )
    notifier = SpyNotifier()
    pipeline = TenderPipeline(
        adapters=[StaticAdapter([tender])],
        store=TenderStore(tmp_path / "db.sqlite"),
        material_filter=MaterialFilter(),
        notifier=notifier,
        notify_mode="new_only",
    )

    stats = pipeline.run()

    assert stats.saved == 1
    assert stats.matched == 1
    assert stats.notified == 1
    assert len(notifier.messages) == 1
    assert notifier.reply_markups[0]["inline_keyboard"][0][0]["text"] == "Открыть источник"


def test_pipeline_stats_tracks_matched_breakdowns(tmp_path):
    existing = Tender(
        source="mosreg_market",
        external_id="existing",
        url="https://example.test/existing",
        title="Поставка кабеля",
        customer="ГБУ",
        region="Московская область",
        status="active",
        raw_payload={"law": "223-ФЗ"},
    )
    fresh = Tender(
        source="moscow_supplier_portal",
        external_id="fresh",
        url="https://example.test/fresh",
        title="Поставка бумаги",
        customer="ГБУ",
        region="Москва",
        status="active",
        raw_payload={"law": "44-ФЗ"},
    )
    store = TenderStore(tmp_path / "db.sqlite")
    store.initialize()
    store.upsert_tender(existing)
    pipeline = TenderPipeline(
        adapters=[StaticAdapter([existing, fresh])],
        store=store,
        material_filter=MaterialFilter(("поставка",)),
        notifier=SpyNotifier(),
    )

    stats = pipeline.run()

    assert stats.fetched == 2
    assert stats.saved == 1
    assert stats.matched == 2
    assert stats.matched_new == 1
    assert stats.matched_existing == 1
    assert stats.source_counts == (("moscow_supplier_portal", 1), ("mosreg_market", 1))
    assert stats.law_counts == (("223-ФЗ", 1), ("44-ФЗ", 1))
    assert stats.region_counts == (("Москва", 1), ("Московская область", 1))


def test_pipeline_preview_resends_matched_tenders_without_marking_notifications(tmp_path):
    tender = Tender(
        source="static",
        external_id="1",
        url="https://example.test/1",
        title="Поставка бумаги",
        customer="ГБУ",
        region="Москва",
        status="active",
    )
    store = TenderStore(tmp_path / "tenders.sqlite")
    notifier = SpyNotifier()
    pipeline = TenderPipeline(
        adapters=[StaticAdapter([tender])],
        store=store,
        material_filter=MaterialFilter(("бумага",)),
        notifier=notifier,
        notify_mode="preview",
    )

    first = pipeline.run()
    second = pipeline.run()

    assert first.notified == 1
    assert second.notified == 1
    assert len(notifier.messages) == 2


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


def test_pipeline_passes_source_checkpoint_to_incremental_adapter_and_records_success(tmp_path):
    store = TenderStore(tmp_path / "db.sqlite")
    store.initialize()
    previous_checkpoint = datetime(2026, 5, 20, 10, 30, tzinfo=UTC)
    next_checkpoint = datetime(2026, 5, 21, 9, 15, tzinfo=UTC)
    store.record_source_success("checkpoint", last_seen_published_at=previous_checkpoint)
    adapter = CheckpointAdapter(
        [
            Tender(
                source="checkpoint",
                external_id="2",
                url="https://example.test/2",
                title="Incremental tender",
                status="active",
                published_at=next_checkpoint,
            )
        ]
    )
    pipeline = TenderPipeline(
        adapters=[adapter],
        store=store,
        material_filter=MaterialFilter(),
        notifier=SpyNotifier(),
    )

    stats = pipeline.run()
    checkpoint = store.get_source_checkpoint("checkpoint")

    assert adapter.seen_published_from == previous_checkpoint
    assert stats.fetched == 1
    assert checkpoint["last_seen_published_at"] == next_checkpoint
    assert checkpoint["last_error"] is None


def test_pipeline_applies_source_checkpoint_overlap_for_incremental_fetch(tmp_path):
    store = TenderStore(tmp_path / "db.sqlite")
    store.initialize()
    previous_checkpoint = datetime(2026, 5, 22, 10, 30, tzinfo=UTC)
    expected_fetch_from = datetime(2026, 5, 22, 9, 0, tzinfo=UTC)
    store.record_source_success("checkpoint", last_seen_published_at=previous_checkpoint)
    adapter = CheckpointAdapter([])
    pipeline = TenderPipeline(
        adapters=[adapter],
        store=store,
        material_filter=MaterialFilter(),
        notifier=SpyNotifier(),
        source_overlap_minutes=90,
    )

    pipeline.run()
    checkpoint = store.get_source_checkpoint("checkpoint")

    assert adapter.seen_published_from == expected_fetch_from
    assert checkpoint["last_seen_published_at"] == previous_checkpoint


def test_pipeline_records_source_errors_for_diagnostics(tmp_path):
    store = TenderStore(tmp_path / "db.sqlite")
    pipeline = TenderPipeline(
        adapters=[FailingAdapter()],
        store=store,
        material_filter=MaterialFilter(),
        notifier=SpyNotifier(),
    )

    stats = pipeline.run()
    checkpoint = store.get_source_checkpoint("failing")

    assert stats.failed_sources == 1
    assert checkpoint["last_error"] == "source unavailable"
    assert checkpoint["last_error_at"] is not None


def test_pipeline_does_not_move_source_checkpoint_backwards(tmp_path):
    store = TenderStore(tmp_path / "db.sqlite")
    store.initialize()
    previous_checkpoint = datetime(2026, 5, 22, 10, 30, tzinfo=UTC)
    older_publication = datetime(2026, 5, 21, 9, 15, tzinfo=UTC)
    store.record_source_success("checkpoint", last_seen_published_at=previous_checkpoint)
    adapter = CheckpointAdapter(
        [
            Tender(
                source="checkpoint",
                external_id="older",
                url="https://example.test/older",
                title="Older tender",
                status="active",
                published_at=older_publication,
            )
        ]
    )
    pipeline = TenderPipeline(
        adapters=[adapter],
        store=store,
        material_filter=MaterialFilter(),
        notifier=SpyNotifier(),
    )

    pipeline.run()
    checkpoint = store.get_source_checkpoint("checkpoint")

    assert checkpoint["last_seen_published_at"] == previous_checkpoint
