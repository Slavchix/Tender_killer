from __future__ import annotations

import re
from dataclasses import dataclass

from tender_killer.filter_store import FilterProfileCollection, FilterProfileStore, NamedFilterProfile
from tender_killer.filters import FilterProfile


QUICK_SEARCH_PROFILE_ID = "quick-entry"
QUICK_SEARCH_PROFILE_NAME = "Быстрый вход"
QUICK_SEARCH_RUN_BUTTON = "Запустить быстрый поиск"

ACTIVE_STATUSES = ("прием предложений", "прием заявок", "active")


@dataclass(frozen=True)
class QuickSearchDraft:
    original_text: str
    title: str
    profile: FilterProfile


def parse_quick_search_text(text: str) -> QuickSearchDraft:
    original_text = " ".join(text.split())
    working = original_text

    laws = _extract_laws(working)
    working = _remove_laws(working)

    okpd2 = _extract_okpd2(working)
    working = _remove_okpd2(working)

    min_price, max_price, working = _extract_price(working)
    regions = _extract_regions(working)
    working = _remove_regions(working)

    keywords = _keywords_from_text(working) or original_text
    profile = FilterProfile(
        keywords=(keywords,),
        exclude_keywords=(),
        regions=regions,
        sources=("moscow", "mosreg"),
        laws=laws,
        statuses=ACTIVE_STATUSES,
        okpd2=okpd2,
        min_price=min_price,
        max_price=max_price,
        only_active=True,
        include_without_price=True,
        include_without_deadline=True,
    )
    return QuickSearchDraft(original_text=original_text, title=keywords[:80], profile=profile)


def save_quick_search_profile(store: FilterProfileStore, draft: QuickSearchDraft) -> NamedFilterProfile:
    collection = store.load_collection()
    named = NamedFilterProfile(
        id=QUICK_SEARCH_PROFILE_ID,
        name=f"{QUICK_SEARCH_PROFILE_NAME}: {draft.title}",
        profile=draft.profile,
    )
    profiles = tuple(
        named if profile.id == QUICK_SEARCH_PROFILE_ID else profile
        for profile in collection.profiles
    )
    if not any(profile.id == QUICK_SEARCH_PROFILE_ID for profile in collection.profiles):
        profiles = (*profiles, named)
    active_ids = list(collection.active_profile_ids)
    if QUICK_SEARCH_PROFILE_ID not in active_ids:
        active_ids.append(QUICK_SEARCH_PROFILE_ID)
    store.save_collection(FilterProfileCollection(profiles=profiles, active_profile_ids=tuple(active_ids)))
    return named


def format_quick_search_confirmation(profile: NamedFilterProfile, draft: QuickSearchDraft) -> str:
    return "\n".join(
        [
            "Быстрый вход сохранен.",
            "",
            f"Профиль: {profile.name} [{profile.id}]",
            f"Запрос: {draft.original_text}",
            f"Ключевые слова: {_format_list(profile.profile.keywords)}",
            f"Регионы: {_format_list(profile.profile.regions)}",
            f"Закон: {_format_list(profile.profile.laws)}",
            f"ОКПД2: {_format_list(profile.profile.okpd2)}",
            f"Цена: {_format_price_range(profile.profile.min_price, profile.profile.max_price)}",
            "",
            f"Нажмите «{QUICK_SEARCH_RUN_BUTTON}», чтобы запустить поиск только по этому быстрому профилю.",
            "Обычные фильтры и сохраненные профили не удалены.",
        ]
    )


def _extract_laws(text: str) -> tuple[str, ...]:
    lower = text.lower()
    laws: list[str] = []
    if re.search(r"\b44\s*[-–—]?\s*фз\b", lower):
        laws.append("44-ФЗ")
    if re.search(r"\b223\s*[-–—]?\s*фз\b", lower):
        laws.append("223-ФЗ")
    return tuple(laws)


def _remove_laws(text: str) -> str:
    return re.sub(r"\b(?:44|223)\s*[-–—]?\s*фз\b", " ", text, flags=re.IGNORECASE)


def _extract_okpd2(text: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(re.findall(r"\b\d{2}(?:\.\d{1,3})+\b", text)))


def _remove_okpd2(text: str) -> str:
    return re.sub(r"\b\d{2}(?:\.\d{1,3})+\b", " ", text)


def _extract_regions(text: str) -> tuple[str, ...]:
    lower = text.lower()
    regions: list[str] = []
    has_moscow_region = bool(
        re.search(r"\bмо\b", lower)
        or "московск" in lower
        or "подмосков" in lower
    )
    has_moscow = bool(re.search(r"\bмоскв[аеуы]?\b", lower) or "мск" in lower)
    if has_moscow and "Москва" not in regions:
        regions.append("Москва")
    if has_moscow_region and "Московская область" not in regions:
        regions.append("Московская область")
    return tuple(regions)


def _remove_regions(text: str) -> str:
    patterns = (
        r"\bмоскв[аеуы]?\b",
        r"\bмск\b",
        r"\bмо\b",
        r"\bмосковск\w*\s+област\w*\b",
        r"\bподмосков\w*\b",
    )
    result = text
    for pattern in patterns:
        result = re.sub(pattern, " ", result, flags=re.IGNORECASE)
    return result


def _extract_price(text: str) -> tuple[float | None, float | None, str]:
    range_pattern = re.compile(
        r"\bот\s+(?P<min>\d[\d\s.,]*)(?:\s*(?P<min_unit>тыс\.?|тысяч|млн\.?|миллион\w*))?"
        r"\s+(?:до|-)\s+(?P<max>\d[\d\s.,]*)(?:\s*(?P<max_unit>тыс\.?|тысяч|млн\.?|миллион\w*))?",
        flags=re.IGNORECASE,
    )
    if match := range_pattern.search(text):
        return (
            _parse_money(match.group("min"), match.group("min_unit")),
            _parse_money(match.group("max"), match.group("max_unit")),
            text[: match.start()] + " " + text[match.end() :],
        )

    max_pattern = re.compile(
        r"\bдо\s+(?P<max>\d[\d\s.,]*)(?:\s*(?P<max_unit>тыс\.?|тысяч|млн\.?|миллион\w*))?",
        flags=re.IGNORECASE,
    )
    if match := max_pattern.search(text):
        return (
            None,
            _parse_money(match.group("max"), match.group("max_unit")),
            text[: match.start()] + " " + text[match.end() :],
        )
    return None, None, text


def _parse_money(value: str, unit: str | None) -> float:
    number = float(value.replace(" ", "").replace(",", "."))
    normalized_unit = (unit or "").lower().replace(".", "")
    if normalized_unit.startswith("тыс"):
        number *= 1_000
    if normalized_unit.startswith("млн") or normalized_unit.startswith("миллион"):
        number *= 1_000_000
    return number


def _keywords_from_text(text: str) -> str:
    words = re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9-]+", text)
    stop_words = {
        "в",
        "во",
        "и",
        "или",
        "по",
        "для",
        "на",
        "с",
        "со",
        "только",
        "закупки",
        "закупка",
        "тендеры",
        "тендер",
        "поставка",
        "поставки",
        "нужны",
        "ищу",
    }
    cleaned = [word for word in words if word.lower() not in stop_words]
    return " ".join(cleaned).strip()


def _format_list(values: tuple[str, ...]) -> str:
    return ", ".join(values) if values else "не задано"


def _format_price_range(min_price: float | None, max_price: float | None) -> str:
    left = _format_number(min_price) if min_price is not None else "любая"
    right = _format_number(max_price) if max_price is not None else "любая"
    return f"{left} - {right}"


def _format_number(value: float) -> str:
    return f"{value:,.0f}".replace(",", " ")
