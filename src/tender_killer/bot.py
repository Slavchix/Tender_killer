from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters as tg_filters

from tender_killer.config import Settings
from tender_killer.filter_store import FilterProfileCollection, FilterProfileStore, NamedFilterProfile
from tender_killer.filters import FilterProfile, MultiProfileTenderFilter
from tender_killer.pipeline import TenderPipeline, PipelineStats
from tender_killer.sources import SOURCE_LABELS, build_adapters_for_collection, normalize_sources
from tender_killer.storage import TenderStore
from tender_killer.telegram import TelegramNotifier

LOGGER = logging.getLogger(__name__)

MENU = ReplyKeyboardMarkup(
    [
        ["Настроить поиск", "Профили"],
        ["Запустить поиск", "Тест поиска"],
        ["Редактировать профиль", "Вкл/выкл профиль"],
        ["Статус источников"],
    ],
    resize_keyboard=True,
)

PROFILE_FIELDS = {
    "Закон": "law",
    "Этап закупки": "stage",
    "Регион": "region",
    "Цена": "price",
    "ОКПД2": "okpd2",
    "Площадки": "sources",
    "Ключевые слова": "keywords",
    "Стоп-слова": "exclude",
    "Только активные": "active",
}

FIELD_EXAMPLES = {
    "law": "44-ФЗ",
    "stage": "Подача заявок",
    "region": "Москва, Московская область",
    "price": "10000 500000",
    "okpd2": "17.12, 27.32.13",
    "sources": "moscow, mosreg",
    "keywords": "бумага, канцтовары",
    "exclude": "услуги, ремонт",
    "active": "on",
}

PROFILE_TEMPLATES = {
    "Бумага/канцелярия": {
        "keywords": ("бумаг", "канцеляр", "папк", "ручк", "карандаш", "тетрад", "файл"),
        "exclude_keywords": ("услуги", "обслуживание", "ремонт"),
        "okpd2": ("17.12", "17.23"),
    },
    "Хозтовары": {
        "keywords": ("хозтовар", "моющ", "чистящ", "салфет", "мыло", "перчат", "инвентар"),
        "exclude_keywords": ("услуги", "обслуживание", "ремонт"),
        "okpd2": (),
    },
    "Картриджи/оргтехника": {
        "keywords": ("картридж", "тонер", "принтер", "мфу", "оргтехник"),
        "exclude_keywords": ("услуги", "заправка", "ремонт", "обслуживание"),
        "okpd2": (),
    },
    "Электрика": {
        "keywords": ("кабель", "провод", "электр", "светильник", "ламп"),
        "exclude_keywords": ("услуги", "монтаж", "ремонт", "обслуживание"),
        "okpd2": ("27",),
    },
    "Сантехника": {
        "keywords": ("сантех", "труб", "кран", "смесител", "сифон"),
        "exclude_keywords": ("услуги", "монтаж", "ремонт", "обслуживание"),
        "okpd2": (),
    },
    "Стройматериалы": {
        "keywords": ("стройматериал", "цемент", "смесь", "краск", "лак", "крепеж", "саморез"),
        "exclude_keywords": ("услуги", "работы", "ремонт", "монтаж"),
        "okpd2": (),
    },
}

STAGE_PRESETS = {
    "Подача заявок": (("прием предложений", "прием заявок", "active"), True),
    "Работа комиссии": (("работа комиссии", "рассмотрение", "комиссия"), False),
    "Закупка отменена": (("отмен", "cancel"), False),
    "Закупка завершена": (("заверш", "проведена", "completed", "closed"), False),
    "Все этапы": ((), False),
}


def parse_csv_args(text: str) -> tuple[str, ...]:
    values = []
    for part in text.replace(";", ",").split(","):
        value = part.strip()
        if value:
            values.append(value)
    return tuple(values)


def apply_filter_command(store: FilterProfileStore, command: str, args: str) -> FilterProfile:
    command = command.lower()
    if command == "law":
        return store.update(laws=parse_csv_args(args))
    if command == "stage":
        statuses, only_active = _parse_stage_args(args)
        return store.update(statuses=statuses, only_active=only_active)
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


def apply_profile_edit(store: FilterProfileStore, profile_id: str, field: str, args: str) -> NamedFilterProfile:
    field = field.lower()
    if field in {"law", "laws", "закон"}:
        return store.update_profile(profile_id, laws=parse_csv_args(args))
    if field in {"stage", "status", "statuses", "этап"}:
        statuses, only_active = _parse_stage_args(args)
        return store.update_profile(profile_id, statuses=statuses, only_active=only_active)
    if field in {"region", "regions", "регион"}:
        return store.update_profile(profile_id, regions=parse_csv_args(args))
    if field in {"price", "цена"}:
        min_price, max_price = _parse_price_args(args)
        return store.update_profile(profile_id, min_price=min_price, max_price=max_price)
    if field in {"okpd2", "окпд2"}:
        return store.update_profile(profile_id, okpd2=parse_csv_args(args))
    if field in {"sources", "площадки"}:
        return store.update_profile(profile_id, sources=normalize_sources(parse_csv_args(args)))
    if field in {"keywords", "ключевые"}:
        return store.update_profile(profile_id, keywords=parse_csv_args(args))
    if field in {"exclude", "exclude_keywords", "стоп"}:
        return store.update_profile(profile_id, exclude_keywords=parse_csv_args(args))
    if field in {"active", "only_active", "активные"}:
        return store.update_profile(profile_id, only_active=_parse_bool(args))
    raise ValueError("Поле не найдено. Доступно: law, stage, region, price, okpd2, sources, keywords, exclude, active.")


def create_profile_from_template(store: FilterProfileStore, template_name: str) -> NamedFilterProfile:
    if template_name not in PROFILE_TEMPLATES:
        raise ValueError("Шаблон не найден.")
    template = PROFILE_TEMPLATES[template_name]
    return store.add_profile(
        template_name,
        keywords=template["keywords"],
        exclude_keywords=template["exclude_keywords"],
        okpd2=template["okpd2"],
        regions=("Московская область",),
        sources=("mosreg",),
        laws=("44-ФЗ",),
        statuses=STAGE_PRESETS["Подача заявок"][0],
        only_active=True,
        min_price=None,
        max_price=None,
    )


def format_filter_profile(profile: FilterProfile) -> str:
    source_labels = [SOURCE_LABELS[source] for source in normalize_sources(profile.sources)]
    return "\n".join(
        [
            "Текущие фильтры",
            "",
            f"Закон: {_format_list(profile.laws)}",
            f"Этап: {_format_list(profile.statuses)}",
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
        "Готов настраивать поиск закупок. Нажми «Настроить поиск» или запусти /search.",
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


async def profiles_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, format_profiles(_store(context).load_collection()))


async def profile_new_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    name = " ".join(context.args).strip()
    if not name:
        context.user_data["awaiting"] = "profile_new_name"
        await _reply(update, "Введите название нового профиля, например: Бумага")
        return
    profile = _store(context).add_profile(name)
    await _reply(update, f"Профиль создан: {profile.name} [{profile.id}]\n\n{format_profiles(_store(context).load_collection())}")


async def profile_edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 1:
        await _reply(update, "Формат: /profile_edit <id> <field> <value>")
        return
    profile_id = context.args[0]
    if len(context.args) == 1:
        context.user_data["editing_profile_id"] = profile_id
        await _reply(update, "Выберите поле: region, price, okpd2, sources, keywords, exclude, active")
        return
    if len(context.args) < 3:
        await _reply(update, "Формат: /profile_edit <id> <field> <value>")
        return
    try:
        profile = apply_profile_edit(_store(context), profile_id, context.args[1], " ".join(context.args[2:]))
    except ValueError as exc:
        await _reply(update, str(exc))
        return
    await _reply(update, f"Профиль обновлен: {profile.name}\n\n{format_profiles(_store(context).load_collection())}")


async def profile_toggle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 2:
        await _reply(update, "Формат: /profile_toggle <id> on|off")
        return
    try:
        collection = _store(context).set_profile_enabled(context.args[0], _parse_bool(context.args[1]))
    except ValueError as exc:
        await _reply(update, str(exc))
        return
    await _reply(update, format_profiles(collection))


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat:
        return
    await _reply(update, "Запускаю поиск по текущим фильтрам.")
    settings: Settings = context.application.bot_data["settings"]
    store = _store(context)
    stats = await asyncio.to_thread(_run_search, settings, store, str(update.effective_chat.id))
    context.application.bot_data["last_stats"] = stats
    await _reply(update, format_search_summary(stats))


async def test_search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat:
        return
    await _reply(update, "Запускаю тест поиска: подходящие карточки будут показаны даже если уже приходили.")
    settings: Settings = context.application.bot_data["settings"]
    store = _store(context)
    stats = await asyncio.to_thread(_run_search, settings, store, str(update.effective_chat.id), "preview")
    context.application.bot_data["last_stats"] = stats
    await _reply(update, format_test_search_summary(stats))


async def sources_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, format_sources_status(context.application.bot_data.get("last_stats")))


async def auto_search_loop(application: Application) -> None:
    settings: Settings = application.bot_data["settings"]
    store: FilterProfileStore = application.bot_data["filter_store"]
    interval_seconds = max(settings.bot_auto_search_minutes, 1) * 60
    while True:
        await asyncio.sleep(interval_seconds)
        if not settings.telegram_chat_id:
            LOGGER.info("Skipping auto search: TELEGRAM_CHAT_ID is not set.")
            continue
        stats = await asyncio.to_thread(_run_search, settings, store, settings.telegram_chat_id)
        application.bot_data["last_stats"] = stats
        summary = format_search_summary(stats)
        if settings.dry_run:
            print(summary)
        else:
            await application.bot.send_message(
                chat_id=settings.telegram_chat_id,
                text=summary,
                disable_web_page_preview=True,
            )


async def text_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    awaiting = context.user_data.get("awaiting")
    if awaiting == "profile_new_name":
        context.user_data.pop("awaiting", None)
        profile = _store(context).add_profile(text)
        await _reply(update, f"Профиль создан: {profile.name} [{profile.id}]")
        return
    if awaiting == "wizard_price":
        context.user_data.pop("awaiting", None)
        profile_id = context.user_data.get("wizard_profile_id")
        if not profile_id:
            await _reply(update, "Профиль мастера не найден. Нажми «Настроить поиск» заново.")
            return
        try:
            profile = apply_profile_edit(_store(context), profile_id, "price", text)
        except ValueError as exc:
            await _reply(update, str(exc))
            return
        context.user_data["wizard_profile_id"] = profile.id
        await _reply(update, "Укажи ОКПД2 или нажми «Пропустить ОКПД2».", reply_markup=_wizard_okpd2_keyboard())
        return
    if awaiting == "wizard_okpd2":
        context.user_data.pop("awaiting", None)
        profile_id = context.user_data.get("wizard_profile_id")
        if not profile_id:
            await _reply(update, "Профиль мастера не найден. Нажми «Настроить поиск» заново.")
            return
        try:
            profile = apply_profile_edit(_store(context), profile_id, "okpd2", text)
        except ValueError as exc:
            await _reply(update, str(exc))
            return
        await _finish_wizard(update, context, profile)
        return
    if awaiting == "profile_edit_value":
        context.user_data.pop("awaiting", None)
        profile_id = context.user_data.pop("editing_profile_id", "")
        field = context.user_data.pop("editing_profile_field", "")
        try:
            profile = apply_profile_edit(_store(context), profile_id, field, text)
        except ValueError as exc:
            await _reply(update, str(exc))
            return
        await _reply(update, f"Профиль обновлен: {profile.name}\n\n{format_profile_details(profile)}")
        return

    if text == "Настроить поиск":
        context.user_data["wizard_step"] = "template"
        await _reply(update, "Выбери шаблон поиска.", reply_markup=_template_keyboard())
    elif text.startswith("Шаблон: "):
        template_name = text.removeprefix("Шаблон: ").strip()
        try:
            profile = create_profile_from_template(_store(context), template_name)
        except ValueError as exc:
            await _reply(update, str(exc))
            return
        context.user_data["wizard_profile_id"] = profile.id
        await _reply(update, "Выбери закон.", reply_markup=_law_keyboard())
    elif text in {"44-ФЗ", "223-ФЗ", "44-ФЗ + 223-ФЗ"} and context.user_data.get("wizard_profile_id"):
        profile_id = context.user_data["wizard_profile_id"]
        laws = ("44-ФЗ", "223-ФЗ") if text == "44-ФЗ + 223-ФЗ" else (text,)
        profile = _store(context).update_profile(profile_id, laws=laws)
        context.user_data["wizard_profile_id"] = profile.id
        await _reply(update, "Выбери этап закупки.", reply_markup=_stage_keyboard())
    elif text in STAGE_PRESETS and context.user_data.get("wizard_profile_id"):
        profile_id = context.user_data["wizard_profile_id"]
        profile = apply_profile_edit(_store(context), profile_id, "stage", text)
        context.user_data["wizard_profile_id"] = profile.id
        await _reply(update, "Выбери регион.", reply_markup=_region_keyboard())
    elif text in {"Москва", "Московская область", "Москва + МО"} and context.user_data.get("wizard_profile_id"):
        profile_id = context.user_data["wizard_profile_id"]
        regions = ("Москва", "Московская область") if text == "Москва + МО" else (text,)
        profile = _store(context).update_profile(profile_id, regions=regions)
        context.user_data["wizard_profile_id"] = profile.id
        await _reply(update, "Укажи диапазон цены в формате `10000 500000` или нажми «Любая цена».", reply_markup=_price_keyboard())
    elif text == "Любая цена" and context.user_data.get("wizard_profile_id"):
        profile_id = context.user_data["wizard_profile_id"]
        profile = _store(context).update_profile(profile_id, min_price=None, max_price=None)
        context.user_data["wizard_profile_id"] = profile.id
        await _reply(update, "Укажи ОКПД2 или нажми «Пропустить ОКПД2».", reply_markup=_wizard_okpd2_keyboard())
    elif text == "Ввести цену" and context.user_data.get("wizard_profile_id"):
        context.user_data["awaiting"] = "wizard_price"
        await _reply(update, "Введи цену от-до, например: 10000 500000")
    elif text == "Пропустить ОКПД2" and context.user_data.get("wizard_profile_id"):
        profile = _store(context).update_profile(context.user_data["wizard_profile_id"], okpd2=())
        await _finish_wizard(update, context, profile)
    elif text == "Ввести ОКПД2" and context.user_data.get("wizard_profile_id"):
        context.user_data["awaiting"] = "wizard_okpd2"
        await _reply(update, "Введи ОКПД2 через запятую, например: 17.12, 27.32.13")
    elif text == "Профили":
        await profiles_command(update, context)
    elif text == "Создать профиль":
        context.user_data["awaiting"] = "profile_new_name"
        await _reply(update, "Введите название нового профиля, например: Бумага")
    elif text == "Редактировать профиль":
        collection = _store(context).load_collection()
        await _reply(
            update,
            "Выберите профиль для редактирования.",
            reply_markup=_profile_action_keyboard(collection, "Редактировать"),
        )
    elif text == "Вкл/выкл профиль":
        collection = _store(context).load_collection()
        await _reply(
            update,
            "Выберите профиль, который нужно включить или выключить.",
            reply_markup=_profile_action_keyboard(collection, "Вкл/выкл"),
        )
    elif text == "Запустить поиск":
        await search_command(update, context)
    elif text == "Тест поиска":
        await test_search_command(update, context)
    elif text == "Статус источников":
        await sources_status_command(update, context)
    elif text.startswith("Редактировать "):
        profile_id = text.removeprefix("Редактировать ").strip()
        context.user_data["editing_profile_id"] = profile_id
        await _reply(
            update,
            "Выберите поле, которое хотите изменить.",
            reply_markup=_profile_field_keyboard(),
        )
    elif text.startswith("Вкл/выкл "):
        profile_id = text.removeprefix("Вкл/выкл ").strip()
        store = _store(context)
        collection = store.load_collection()
        enabled = profile_id not in set(collection.active_profile_ids)
        try:
            collection = store.set_profile_enabled(profile_id, enabled)
        except ValueError as exc:
            await _reply(update, str(exc))
            return
        await _reply(update, format_profiles(collection))
    elif text in PROFILE_FIELDS and context.user_data.get("editing_profile_id"):
        field = PROFILE_FIELDS[text]
        context.user_data["editing_profile_field"] = field
        context.user_data["awaiting"] = "profile_edit_value"
        await _reply(update, f"Введите значение для поля `{text}`.\nПример: {FIELD_EXAMPLES[field]}")
    else:
        await _reply(update, "Не понял команду. Открой /profiles или /filters.")


def format_search_summary(stats: PipelineStats) -> str:
    lines = [
        "Готово: Fetched={fetched} Saved={saved} Matched={matched} "
        "Notified={notified} FailedSources={failed_sources}".format(**stats.__dict__)
    ]
    if stats.failed_source_names:
        lines.append(f"Упали источники: {', '.join(stats.failed_source_names)}")
    if stats.failed_source_errors:
        lines.append("Ошибки:")
        lines.extend(stats.failed_source_errors)
    return "\n".join(lines)


def format_test_search_summary(stats: PipelineStats) -> str:
    return "\n".join(
        [
            "Тест поиска: Fetched={fetched} Saved={saved} Matched={matched} "
            "Sent={notified} FailedSources={failed_sources}".format(**stats.__dict__),
            "В этом режиме подходящие карточки отправлены повторно и не помечены как новые уведомления.",
        ]
    )


def format_profiles(collection: FilterProfileCollection) -> str:
    lines = ["Профили поиска", ""]
    active = set(collection.active_profile_ids)
    for profile in collection.profiles:
        marker = "on" if profile.id in active else "off"
        lines.append(f"{marker} {profile.name} [{profile.id}]")
        lines.append(f"  {format_profile_details(profile)}")
    return "\n".join(lines)


def format_profile_details(profile: NamedFilterProfile) -> str:
    source_labels = [SOURCE_LABELS[source] for source in normalize_sources(profile.profile.sources)]
    return "\n".join(
        [
            f"Закон: {_format_list(profile.profile.laws)}",
            f"Этап: {_format_list(profile.profile.statuses)}",
            f"Регионы: {_format_list(profile.profile.regions)}",
            f"Цена: {_format_price_range(profile.profile.min_price, profile.profile.max_price)}",
            f"ОКПД2: {_format_list(profile.profile.okpd2)}",
            f"Площадки: {'; '.join(source_labels)}",
            f"Только активные: {'да' if profile.profile.only_active else 'нет'}",
            f"Ключевые слова: {_format_list(profile.profile.keywords)}",
            f"Стоп-слова: {_format_list(profile.profile.exclude_keywords)}",
        ]
    )


def format_sources_status(stats: PipelineStats | None) -> str:
    if stats is None:
        return "Статус источников\n\nЗапусков еще не было."
    lines = [
        "Статус источников",
        "",
        "Последний запуск: Fetched={fetched} Saved={saved} Matched={matched} "
        "Notified={notified} FailedSources={failed_sources}".format(**stats.__dict__),
    ]
    if stats.failed_source_errors:
        lines.append("")
        lines.append("Ошибки:")
        lines.extend(stats.failed_source_errors)
    return "\n".join(lines)


async def _update_filter(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str, args: str) -> None:
    try:
        profile = apply_filter_command(_store(context), command, args)
    except ValueError as exc:
        await _reply(update, str(exc))
        return
    await _reply(update, format_filter_profile(profile))


async def _finish_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE, profile: NamedFilterProfile) -> None:
    context.user_data.pop("wizard_profile_id", None)
    context.user_data.pop("wizard_step", None)
    await _reply(
        update,
        f"Профиль настроен: {profile.name} [{profile.id}]\n\n{format_profile_details(profile)}",
    )


def _run_search(
    settings: Settings,
    store: FilterProfileStore,
    chat_id: str,
    notify_mode: str = "normal",
) -> PipelineStats:
    collection = store.load_collection()
    pipeline = TenderPipeline(
        adapters=build_adapters_for_collection(collection, settings),
        store=TenderStore(settings.database_path),
        material_filter=MultiProfileTenderFilter(collection),
        notifier=TelegramNotifier(settings.telegram_bot_token, chat_id, dry_run=settings.dry_run),
        notify_mode=notify_mode,
    )
    return pipeline.run()


def _store(context: ContextTypes.DEFAULT_TYPE) -> FilterProfileStore:
    return context.application.bot_data["filter_store"]


async def _reply(update: Update, text: str, reply_markup: ReplyKeyboardMarkup = MENU) -> None:
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, disable_web_page_preview=True)


def _profile_action_keyboard(collection: FilterProfileCollection, action: str) -> ReplyKeyboardMarkup:
    rows = [[f"{action} {profile.id}"] for profile in collection.profiles]
    rows.append(["Профили", "Запустить поиск"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def _profile_field_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["Закон", "Этап закупки"],
            ["Регион", "Цена"],
            ["ОКПД2", "Площадки"],
            ["Ключевые слова", "Стоп-слова"],
            ["Только активные"],
            ["Профили", "Запустить поиск"],
        ],
        resize_keyboard=True,
    )


def _template_keyboard() -> ReplyKeyboardMarkup:
    rows = [[f"Шаблон: {name}"] for name in PROFILE_TEMPLATES]
    rows.append(["Профили", "Запустить поиск"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def _law_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["44-ФЗ", "223-ФЗ"], ["44-ФЗ + 223-ФЗ"], ["Профили", "Запустить поиск"]],
        resize_keyboard=True,
    )


def _stage_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["Подача заявок", "Работа комиссии"],
            ["Закупка отменена", "Закупка завершена"],
            ["Все этапы"],
            ["Профили", "Запустить поиск"],
        ],
        resize_keyboard=True,
    )


def _region_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["Московская область", "Москва"], ["Москва + МО"], ["Профили", "Запустить поиск"]],
        resize_keyboard=True,
    )


def _price_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["Любая цена", "Ввести цену"], ["Профили", "Запустить поиск"]],
        resize_keyboard=True,
    )


def _wizard_okpd2_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["Пропустить ОКПД2", "Ввести ОКПД2"], ["Профили", "Запустить поиск"]],
        resize_keyboard=True,
    )


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


def _parse_stage_args(args: str) -> tuple[tuple[str, ...], bool]:
    value = args.strip()
    if value in STAGE_PRESETS:
        return STAGE_PRESETS[value]
    return parse_csv_args(value), False


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
    application = Application.builder().token(settings.telegram_bot_token).post_init(_post_init).build()
    application.bot_data["settings"] = settings
    application.bot_data["filter_store"] = FilterProfileStore(filter_path)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("filters", filters_command))
    application.add_handler(CommandHandler("region", region_command))
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("okpd2", okpd2_command))
    application.add_handler(CommandHandler("sources", sources_command))
    application.add_handler(CommandHandler("active", active_command))
    application.add_handler(CommandHandler("profiles", profiles_command))
    application.add_handler(CommandHandler("profile_new", profile_new_command))
    application.add_handler(CommandHandler("profile_edit", profile_edit_command))
    application.add_handler(CommandHandler("profile_toggle", profile_toggle_command))
    application.add_handler(CommandHandler("sources_status", sources_status_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("test_search", test_search_command))
    application.add_handler(MessageHandler(tg_filters.TEXT & ~tg_filters.COMMAND, text_menu_handler))
    LOGGER.info("Starting Tender Killer bot with filter profile %s", filter_path)
    application.run_polling()


async def _post_init(application: Application) -> None:
    settings: Settings = application.bot_data["settings"]
    if settings.bot_auto_search_minutes > 0:
        LOGGER.info("Starting auto search loop: every %s minutes.", settings.bot_auto_search_minutes)
        application.create_task(auto_search_loop(application), name="tender-killer-auto-search")


if __name__ == "__main__":
    main()
