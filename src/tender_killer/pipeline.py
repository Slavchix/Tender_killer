from __future__ import annotations

import logging
from dataclasses import dataclass

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
    ) -> None:
        self.adapters = adapters
        self.store = store
        self.material_filter = material_filter
        self.notifier = notifier

    def run(self) -> PipelineStats:
        self.store.initialize()
        fetched = saved = matched = notified = failed_sources = 0
        failed_source_names: list[str] = []
        failed_source_errors: list[str] = []

        for adapter in self.adapters:
            try:
                tenders = adapter.fetch()
            except Exception as exc:  # noqa: BLE001 - one source must not break the whole run.
                failed_sources += 1
                failed_source_names.append(adapter.source)
                failed_source_errors.append(f"{adapter.source}: {exc}")
                LOGGER.warning("Source %s failed: %s", adapter.source, exc)
                continue

            fetched += len(tenders)
            for tender in tenders:
                result = self.store.upsert_tender(tender)
                if result.created:
                    saved += 1

                filter_result = self.material_filter.match(tender)
                if not filter_result.matched:
                    continue
                matched += 1

                if self.store.was_notified(tender):
                    continue
                if self.notifier.send(build_tender_message(tender, filter_result.reasons)):
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
