from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from tender_killer.adapters.base import BaseAdapter
from tender_killer.filters import TenderFilter
from tender_killer.storage import TenderStore
from tender_killer.telegram import TelegramNotifier, build_tender_message

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineStats:
    fetched: int = 0
    saved: int = 0
    matched: int = 0
    notified: int = 0
    failed_sources: int = 0
    failed_source_names: tuple[str, ...] = ()
    failed_source_errors: tuple[str, ...] = ()


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
        fetched = saved = matched = notified = failed_sources = 0
        failed_source_names: list[str] = []
        failed_source_errors: list[str] = []

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
            for tender in tenders:
                result = self.store.upsert_tender(tender)
                if result.created:
                    saved += 1

                filter_result = self.material_filter.match(tender)
                if not filter_result.matched:
                    continue
                matched += 1

                if self.notify_mode == "new_only" and not result.created:
                    continue
                if self.notify_mode != "preview" and self.store.was_notified(tender):
                    continue
                if self.notifier.send(build_tender_message(tender, filter_result.reasons)):
                    if self.notify_mode != "preview":
                        self.store.mark_notified(tender)
                    notified += 1

        return PipelineStats(
            fetched=fetched,
            saved=saved,
            matched=matched,
            notified=notified,
            failed_sources=failed_sources,
            failed_source_names=tuple(failed_source_names),
            failed_source_errors=tuple(failed_source_errors),
        )


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
