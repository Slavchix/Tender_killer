from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from tender_killer.config import Settings
from tender_killer.filter_store import FilterProfileStore
from tender_killer.filters import FilterProfile, TenderFilter
from tender_killer.pipeline import TenderPipeline, PipelineStats
from tender_killer.sources import SOURCE_LABELS, build_adapters, normalize_sources
from tender_killer.storage import TenderStore
from tender_killer.telegram import TelegramNotifier

LOGGER = logging.getLogger(__name__)

MENU = ReplyKeyboardMarkup(
    [
        ["/filters", "/search"],
        ["/active on", "/active off"],
        ["/sources moscow, mosreg"],
        ["/region Москва, Московская область"],
        ["/price 10000 500000"],
        ["/okpd2 17.12, 27.32.13"],
    ],
    resize_keyboard=True,
)


def parse_csv_args(text: str) -> tuple[str, ...]:
    values = []
    for part in text.replace(";", ",").split(","):
        value = part.strip()
        if value:
            values.append(value)
    return tuple(values)


def apply_filter_command(store: FilterProfileStore, command: str, args: str) -> FilterProfile:
    command = command.lower()
    if command == "region":
        return store.update(regions=parse_csv_args(args))
    if command == "price":
        min_price, max_price = _parse_price_args(args)
        return store.update(min_price=min_price, max_price=max_price)
    if command == "okpd2":
        return store.update(okpd2=parse_csv_args(args))
    if command == "sources":
        return store.update(sources=normalize_sources(parse_csv_args(args)))
    if command == "active":
        return store.update(only_active=_parse_bool(args))
    raise ValueError(f"Unknown filter command: {command}")


def format_filter_profile(profile: FilterProfile) -> str:
    source_labels = [SOURCE_LABELS[source] for source in normalize_sources(profile.sources)]
    return "\n".join(
        [
            "Текущие фильтры",
            "",
            f"Регион: {_format_list(profile.regions)}",
            f"Цена: {_format_price_range(profile.min_price, profile.max_price)}",
            f"ОКПД2: {_format_list(profile.okpd2)}",
            f"Площадки: {'; '.join(source_labels)}",
            f"Только активные: {'да' if profile.only_active else 'нет'}",
            f"Ключевые слова: {_format_list(profile.keywords)}",
            f"Стоп-слова: {_format_list(profile.exclude_keywords)}",
        ]
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(
        update,
        "Готов настраивать поиск закупок. Открой /filters или запусти /search.",
    )


async def filters_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    store = _store(context)
    await _reply(update, format_filter_profile(store.load()))


async def region_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _update_filter(update, context, "region", " ".join(context.args))


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _update_filter(update, context, "price", " ".join(context.args))


async def okpd2_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _update_filter(update, context, "okpd2", " ".join(context.args))


async def sources_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _update_filter(update, context, "sources", " ".join(context.args))


async def active_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _update_filter(update, context, "active", " ".join(context.args))


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat:
        return
    await _reply(update, "Запускаю поиск по текущим фильтрам.")
    settings: Settings = context.application.bot_data["settings"]
    store = _store(context)
    stats = await asyncio.to_thread(_run_search, settings, store, str(update.effective_chat.id))
    await _reply(update, format_search_summary(stats))


def format_search_summary(stats: PipelineStats) -> str:
    lines = [
        "Готово: Fetched={fetched} Saved={saved} Matched={matched} "
        "Notified={notified} FailedSources={failed_sources}".format(**stats.__dict__)
    ]
    if stats.failed_source_names:
        lines.append(f"Упали источники: {', '.join(stats.failed_source_names)}")
    return "\n".join(lines)


async def _update_filter(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str, args: str) -> None:
    try:
        profile = apply_filter_command(_store(context), command, args)
    except ValueError as exc:
        await _reply(update, str(exc))
        return
    await _reply(update, format_filter_profile(profile))


def _run_search(settings: Settings, store: FilterProfileStore, chat_id: str) -> PipelineStats:
    profile = store.load()
    pipeline = TenderPipeline(
        adapters=build_adapters(profile, settings),
        store=TenderStore(settings.database_path),
        material_filter=TenderFilter(profile),
        notifier=TelegramNotifier(settings.telegram_bot_token, chat_id, dry_run=settings.dry_run),
    )
    return pipeline.run()


def _store(context: ContextTypes.DEFAULT_TYPE) -> FilterProfileStore:
    return context.application.bot_data["filter_store"]


async def _reply(update: Update, text: str) -> None:
    if update.message:
        await update.message.reply_text(text, reply_markup=MENU, disable_web_page_preview=True)


def _parse_price_args(args: str) -> tuple[float | None, float | None]:
    values = [part for part in args.replace(",", " ").split() if part]
    if len(values) != 2:
        raise ValueError("Формат: /price 10000 500000")
    return _parse_optional_price(values[0]), _parse_optional_price(values[1])


def _parse_optional_price(value: str) -> float | None:
    if value in {"-", "none", "нет"}:
        return None
    return float(value.replace("_", ""))


def _parse_bool(args: str) -> bool:
    value = args.strip().lower()
    if value in {"on", "1", "true", "yes", "да", "вкл"}:
        return True
    if value in {"off", "0", "false", "no", "нет", "выкл"}:
        return False
    raise ValueError("Формат: /active on или /active off")


def _format_list(values: tuple[str, ...]) -> str:
    return ", ".join(values) if values else "не задано"


def _format_price_range(min_price: float | None, max_price: float | None) -> str:
    left = _format_number(min_price) if min_price is not None else "любая"
    right = _format_number(max_price) if max_price is not None else "любая"
    return f"{left} - {right}"


def _format_number(value: float) -> str:
    return f"{value:,.0f}".replace(",", " ")


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = Settings.from_env()
    if not settings.telegram_bot_token:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN before starting the bot.")
    filter_path = settings.filter_profile_path or Path("filters.json")
    application = Application.builder().token(settings.telegram_bot_token).build()
    application.bot_data["settings"] = settings
    application.bot_data["filter_store"] = FilterProfileStore(filter_path)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("filters", filters_command))
    application.add_handler(CommandHandler("region", region_command))
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("okpd2", okpd2_command))
    application.add_handler(CommandHandler("sources", sources_command))
    application.add_handler(CommandHandler("active", active_command))
    application.add_handler(CommandHandler("search", search_command))
    LOGGER.info("Starting Tender Killer bot with filter profile %s", filter_path)
    application.run_polling()


if __name__ == "__main__":
    main()
