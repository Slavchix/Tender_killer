from __future__ import annotations

import argparse
import logging

from tender_killer.adapters import MoscowSupplierPortalAdapter, MosregMarketAdapter
from tender_killer.config import Settings
from tender_killer.filters import FilterProfile, TenderFilter
from tender_killer.pipeline import TenderPipeline
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
    moscow_url = args.moscow_url or settings.moscow_url
    mosreg_url = args.mosreg_url or settings.mosreg_url
    filter_path = args.filters or settings.filter_profile_path
    filter_profile = (
        FilterProfile.from_json_file(filter_path)
        if filter_path
        else FilterProfile.default()
    )

    pipeline = TenderPipeline(
        adapters=[
            MoscowSupplierPortalAdapter(moscow_url, settings.request_timeout_seconds),
            MosregMarketAdapter(mosreg_url, settings.request_timeout_seconds),
        ],
        store=TenderStore(database_path),
        material_filter=TenderFilter(filter_profile),
        notifier=TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id, dry_run=dry_run),
    )
    stats = pipeline.run()
    print(
        "Fetched={fetched} Saved={saved} Matched={matched} "
        "Notified={notified} FailedSources={failed_sources}".format(**stats.__dict__)
    )


if __name__ == "__main__":
    main()
