from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_path: Path
    telegram_bot_token: str | None
    telegram_chat_id: str | None
    dry_run: bool
    moscow_url: str
    mosreg_url: str
    filter_profile_path: Path | None
    request_timeout_seconds: float
    bot_auto_search_minutes: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_path=Path(os.getenv("TENDER_KILLER_DB", "data/tenders.sqlite")),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
            dry_run=os.getenv("TENDER_KILLER_DRY_RUN", "0") == "1",
            moscow_url=os.getenv(
                "TENDER_KILLER_MOSCOW_URL",
                "https://old.zakupki.mos.ru/api/Cssp/Purchase/Query",
            ),
            mosreg_url=os.getenv(
                "TENDER_KILLER_MOSREG_URL",
                "https://api.market.mosreg.ru/api/Trade/GetTradesForParticipantOrAnonymous",
            ),
            filter_profile_path=(
                Path(filter_path) if (filter_path := os.getenv("TENDER_KILLER_FILTERS")) else None
            ),
            request_timeout_seconds=float(os.getenv("TENDER_KILLER_TIMEOUT", "20")),
            bot_auto_search_minutes=int(os.getenv("TENDER_KILLER_AUTO_SEARCH_MINUTES", "0")),
        )
