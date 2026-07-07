from __future__ import annotations

from pathlib import Path
from typing import Any

from tender_killer.config import Settings
from tender_killer.filter_store import FilterProfileCollection
from tender_killer.filter_store import FilterProfileStore
from tender_killer.filters import MultiProfileTenderFilter
from tender_killer.pipeline import PipelineStats
from tender_killer.pipeline import TenderPipeline
from tender_killer.sources import build_adapters_for_collection
from tender_killer.storage import TenderStore
from tender_killer.telegram import TelegramNotifier
from tender_killer.tender_query_service import build_search_collection


def run_search_payload(settings: Settings, runner=None, filters_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    collection = build_search_collection(filters_payload) if filters_payload else None
    stats = runner(settings, collection) if runner else _run_search_from_settings(settings, collection)
    return {
        "ok": True,
        "notifications_enabled": bool(settings.telegram_bot_token and settings.telegram_chat_id),
        "stats": _stats_payload(stats),
    }


def _run_search_from_settings(settings: Settings, collection: FilterProfileCollection | None = None) -> PipelineStats:
    if collection is None:
        filter_path = settings.filter_profile_path or Path("filters.json")
        filter_store = FilterProfileStore(filter_path)
        collection = filter_store.load_collection()
    pipeline = TenderPipeline(
        adapters=build_adapters_for_collection(collection, settings),
        store=TenderStore(settings.database_path),
        material_filter=MultiProfileTenderFilter(collection),
        notifier=TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id, dry_run=settings.dry_run),
        notify_mode="new_only",
        source_overlap_minutes=settings.source_incremental_overlap_minutes,
    )
    return pipeline.run()


def _stats_payload(stats: PipelineStats) -> dict[str, Any]:
    return {
        "fetched": stats.fetched,
        "saved": stats.saved,
        "matched": stats.matched,
        "matched_new": stats.matched_new,
        "matched_existing": stats.matched_existing,
        "notified": stats.notified,
        "failed_sources": stats.failed_sources,
        "failed_source_names": list(stats.failed_source_names),
        "failed_source_errors": list(stats.failed_source_errors),
        "source_counts": _count_rows(stats.source_counts),
        "law_counts": _count_rows(stats.law_counts),
        "region_counts": _count_rows(stats.region_counts),
    }


def _count_rows(rows: tuple[tuple[str, int], ...]) -> list[dict[str, Any]]:
    return [{"value": value, "count": count} for value, count in rows]
