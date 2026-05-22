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
    source_max_pages: int
    source_incremental_overlap_minutes: int

    @classmethod
    def from_env(cls) -> "Settings":
        dotenv = _dotenv_values()
        return cls(
            database_path=Path(_env("TENDER_KILLER_DB", dotenv, "data/tenders.sqlite")),
            telegram_bot_token=_env("TELEGRAM_BOT_TOKEN", dotenv),
            telegram_chat_id=_env("TELEGRAM_CHAT_ID", dotenv),
            dry_run=_env("TENDER_KILLER_DRY_RUN", dotenv, "0") == "1",
            moscow_url=_env(
                "TENDER_KILLER_MOSCOW_URL",
                dotenv,
                "https://old.zakupki.mos.ru/api/Cssp/Purchase/Query",
            ),
            mosreg_url=_env(
                "TENDER_KILLER_MOSREG_URL",
                dotenv,
                "https://api.market.mosreg.ru/api/Trade/GetTradesForParticipantOrAnonymous",
            ),
            filter_profile_path=(
                Path(filter_path) if (filter_path := _env("TENDER_KILLER_FILTERS", dotenv)) else None
            ),
            request_timeout_seconds=float(_env("TENDER_KILLER_TIMEOUT", dotenv, "20")),
            bot_auto_search_minutes=int(_env("TENDER_KILLER_AUTO_SEARCH_MINUTES", dotenv, "0")),
            source_max_pages=max(1, int(_env("TENDER_KILLER_SOURCE_MAX_PAGES", dotenv, "1"))),
            source_incremental_overlap_minutes=max(0, int(_env("TENDER_KILLER_SOURCE_OVERLAP_MINUTES", dotenv, "60"))),
        )


def _env(name: str, dotenv: dict[str, str], default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is not None:
        return value
    return dotenv.get(name, default)


def _dotenv_values(path: str | Path = ".env") -> dict[str, str]:
    dotenv_path = Path(path)
    if not dotenv_path.exists():
        return {}
    values: dict[str, str] = {}
    for line in dotenv_path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if not key:
            continue
        values[key] = _clean_dotenv_value(value)
    return values


def _clean_dotenv_value(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
        return cleaned[1:-1]
    return cleaned
