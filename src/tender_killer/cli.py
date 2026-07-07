from __future__ import annotations

import argparse
import logging
from dataclasses import replace

from tender_killer.config import Settings
from tender_killer.filter_store import FilterProfileCollection, FilterProfileStore, NamedFilterProfile
from tender_killer.filters import FilterProfile, MultiProfileTenderFilter
from tender_killer.pipeline import TenderPipeline
from tender_killer.sources import build_adapters_for_collection
from tender_killer.storage import TenderStore
from tender_killer.telegram import TelegramNotifier


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tender-killer")
    parser.add_argument("--dry-run", action="store_true", help="Print Telegram messages instead of sending them.")
    parser.add_argument("--moscow-url", help="Override Moscow supplier portal URL.")
    parser.add_argument("--mosreg-url", help="Override Moscow Oblast market URL.")
    parser.add_argument("--db", help="Override SQLite database path.")
    parser.add_argument("--filters", help="Path to JSON filter profile.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logs.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    settings = Settings.from_env()

    database_path = args.db or settings.database_path
    dry_run = args.dry_run or settings.dry_run
    settings = replace(
        settings,
        moscow_url=args.moscow_url or settings.moscow_url,
        mosreg_url=args.mosreg_url or settings.mosreg_url,
    )
    filter_path = args.filters or settings.filter_profile_path
    filter_collection = (
        FilterProfileStore(filter_path).load_collection()
        if filter_path
        else FilterProfileCollection(
            profiles=(NamedFilterProfile("default", "Default", FilterProfile.default()),),
            active_profile_ids=("default",),
        )
    )

    pipeline = TenderPipeline(
        adapters=build_adapters_for_collection(filter_collection, settings),
        store=TenderStore(database_path),
        material_filter=MultiProfileTenderFilter(filter_collection),
        notifier=TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id, dry_run=dry_run),
        source_overlap_minutes=settings.source_incremental_overlap_minutes,
    )
    stats = pipeline.run()
    print(
        "Fetched={fetched} Saved={saved} Matched={matched} "
        "Notified={notified} FailedSources={failed_sources}".format(**stats.__dict__)
    )


if __name__ == "__main__":
    main()
