from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from tender_killer.adapters.base import BaseAdapter
from tender_killer.filters import TenderFilter
from tender_killer.storage import TenderStore
from tender_killer.telegram import TelegramNotifier, build_tender_actions, build_tender_message
from tender_killer.tender_metadata import normalize_law

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineStats:
    fetched: int = 0
    saved: int = 0
    matched: int = 0
    matched_new: int = 0
    matched_existing: int = 0
    notified: int = 0
    failed_sources: int = 0
    failed_source_names: tuple[str, ...] = ()
    failed_source_errors: tuple[str, ...] = ()
    source_counts: tuple[tuple[str, int], ...] = ()
    law_counts: tuple[tuple[str, int], ...] = ()
    region_counts: tuple[tuple[str, int], ...] = ()


class TenderPipeline:
    def __init__(
        self,
        adapters: list[BaseAdapter],
        store: TenderStore,
        material_filter: TenderFilter,
        notifier: TelegramNotifier,
        notify_mode: str = "normal",
        source_overlap_minutes: int = 0,
    ) -> None:
        self.adapters = adapters
        self.store = store
        self.material_filter = material_filter
        self.notifier = notifier
        self.notify_mode = notify_mode
        self.source_overlap_minutes = max(0, int(source_overlap_minutes))

    def run(self) -> PipelineStats:
        self.store.initialize()
        fetched = saved = matched = matched_new = matched_existing = notified = failed_sources = 0
        failed_source_names: list[str] = []
        failed_source_errors: list[str] = []
        source_counts: dict[str, int] = {}
        law_counts: dict[str, int] = {}
        region_counts: dict[str, int] = {}

        for adapter in self.adapters:
            checkpoint = self.store.get_source_checkpoint(adapter.source)
            previous_published_at = checkpoint["last_seen_published_at"]
            if previous_published_at is not None:
                setattr(adapter, "published_from", _with_overlap(previous_published_at, self.source_overlap_minutes))
            try:
                tenders = adapter.fetch()
            except Exception as exc:  # noqa: BLE001 - one source must not break the whole run.
                failed_sources += 1
                failed_source_names.append(adapter.source)
                failed_source_errors.append(f"{adapter.source}: {exc}")
                self.store.record_source_error(adapter.source, str(exc))
                LOGGER.warning("Source %s failed: %s", adapter.source, exc)
                continue

            fetched += len(tenders)
            self.store.record_source_success(
                adapter.source,
                _max_datetime(previous_published_at, _latest_published_at(tenders)),
            )
            fetched_identities = {tender.identity for tender in tenders}
            for tender in tenders:
                result = self.store.upsert_tender(tender)
                if result.created:
                    saved += 1

                filter_result = self.material_filter.match(tender)
                if not filter_result.matched:
                    continue
                matched += 1
                if result.created:
                    matched_new += 1
                else:
                    matched_existing += 1
                _increment_count(source_counts, tender.source)
                _increment_count(law_counts, normalize_law(tender.raw_payload) or "Не указан")
                _increment_count(region_counts, tender.region or "Не указан")

                if self.notify_mode == "new_only" and not result.created:
                    continue
                if self.notify_mode != "preview" and self.store.was_notified(tender):
                    continue
                if self.notifier.send(
                    build_tender_message(tender, filter_result.reasons),
                    reply_markup=build_tender_actions(tender),
                ):
                    if self.notify_mode != "preview":
                        self.store.mark_notified(tender)
                    notified += 1
            self._refresh_saved_active_tenders(adapter, fetched_identities)

        return PipelineStats(
            fetched=fetched,
            saved=saved,
            matched=matched,
            matched_new=matched_new,
            matched_existing=matched_existing,
            notified=notified,
            failed_sources=failed_sources,
            failed_source_names=tuple(failed_source_names),
            failed_source_errors=tuple(failed_source_errors),
            source_counts=_sorted_counts(source_counts),
            law_counts=_sorted_counts(law_counts),
            region_counts=_sorted_counts(region_counts),
        )

    def _refresh_saved_active_tenders(self, adapter: BaseAdapter, fetched_identities: set[tuple[str, str]]) -> None:
        if adapter.source != "moscow_supplier_portal":
            return
        enrich_payload = getattr(adapter, "enrich_payload", None)
        if not callable(enrich_payload):
            return
        for row in self.store.list_active_tender_payloads(adapter.source):
            identity = (str(row["source"]), str(row["external_id"]))
            if identity in fetched_identities:
                continue
            raw_payload = row["raw_payload"]
            if not raw_payload:
                continue
            try:
                refreshed_payload = enrich_payload(raw_payload)
                refreshed_tender = adapter.normalize_payload(refreshed_payload)
            except Exception as exc:  # noqa: BLE001 - a stale card must not break source updates.
                LOGGER.warning("Failed to refresh saved %s tender %s: %s", adapter.source, identity[1], exc)
                continue
            self.store.upsert_tender(refreshed_tender)


def _latest_published_at(tenders: list) -> datetime | None:
    latest: datetime | None = None
    for tender in tenders:
        published_at = getattr(tender, "published_at", None)
        if published_at is None:
            continue
        normalized = _as_aware_utc(published_at)
        if latest is None or normalized > latest:
            latest = normalized
    return latest


def _max_datetime(left: datetime | None, right: datetime | None) -> datetime | None:
    if left is None:
        return right
    if right is None:
        return left
    return left if _as_aware_utc(left) >= _as_aware_utc(right) else right


def _with_overlap(value: datetime, minutes: int) -> datetime:
    normalized = _as_aware_utc(value)
    if minutes <= 0:
        return normalized
    return normalized - timedelta(minutes=minutes)


def _as_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _increment_count(counts: dict[str, int], value: str | None) -> None:
    key = str(value or "").strip() or "Не указан"
    counts[key] = counts.get(key, 0) + 1


def _sorted_counts(counts: dict[str, int]) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold())))
