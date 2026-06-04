from __future__ import annotations

import re
from typing import Any


SUPPLIER_CATALOG_PRESETS: tuple[dict[str, Any], ...] = (
    {
        "preset_id": "officemag_office_supplies",
        "label": "OfficeMag",
        "provider": "officemag",
        "url_template": "https://www.officemag.ru/search/?q={query}",
        "match_keywords": (
            "office",
            "paper",
            "stationery",
            "бумаг",
            "канцел",
            "офис",
            "папк",
            "скоросшив",
            "регистратор",
            "файл",
            "картридж",
            "тонер",
            "принтер",
            "мфу",
            "оргтехник",
            "расходн",
            "чернил",
        ),
        "match_okpd2_prefixes": ("17.12", "28.23"),
    },
    {
        "preset_id": "komus_office_supplies",
        "label": "Komus",
        "provider": "komus",
        "url_template": "https://www.komus.ru/search/?text={query}",
        "match_keywords": (
            "office",
            "paper",
            "stationery",
            "бумаг",
            "канцел",
            "офис",
            "папк",
            "скоросшив",
            "регистратор",
            "файл",
            "картридж",
            "тонер",
            "принтер",
            "мфу",
            "оргтехник",
            "расходн",
            "чернил",
        ),
        "match_okpd2_prefixes": ("17.12", "28.23"),
    },
    {
        "preset_id": "petrovich_building_materials",
        "label": "Petrovich",
        "provider": "petrovich",
        "url_template": "https://petrovich.ru/search/?q={query}",
        "match_keywords": (
            "building",
            "cement",
            "concrete",
            "цемент",
            "бетон",
            "строител",
            "сухая смесь",
            "сухие смеси",
            "смес",
            "штукатур",
            "шпатлев",
            "гипс",
            "кирпич",
            "плитк",
            "краск",
            "грунтов",
            "герметик",
            "пескобетон",
        ),
        "match_okpd2_prefixes": ("08.12", "23.5", "23.6", "23.7", "23.9"),
    },
    {
        "preset_id": "vseinstrumenti_building_materials",
        "label": "Vseinstrumenti",
        "provider": "vseinstrumenti",
        "url_template": "https://www.vseinstrumenti.ru/search/?q={query}",
        "match_keywords": (
            "tool",
            "tools",
            "instrument",
            "building",
            "cement",
            "concrete",
            "инструмент",
            "дрел",
            "шуруповерт",
            "перфоратор",
            "пил",
            "болгарк",
            "шлиф",
            "сверл",
            "ключ",
            "молот",
            "насос",
            "компрессор",
            "станок",
            "свароч",
            "генератор",
            "триммер",
            "цемент",
            "бетон",
            "строител",
            "сухая смесь",
            "сухие смеси",
            "смес",
            "штукатур",
            "шпатлев",
            "пескобетон",
        ),
        "match_okpd2_prefixes": ("08.12", "23.5", "23.6", "23.7", "23.9", "25.73", "28.24"),
    },
)

TOKEN_RE = re.compile(r"[0-9a-zа-яё]+", re.IGNORECASE)


def supplier_catalog_preset_ids() -> set[str]:
    return {str(preset["preset_id"]) for preset in SUPPLIER_CATALOG_PRESETS}


def normalize_supplier_catalog_preset_ids(value: Any) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError("supplier catalog preset ids must be a list or null")
    valid_ids = supplier_catalog_preset_ids()
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        preset_id = _text(item)
        if not preset_id or preset_id not in valid_ids or preset_id in seen:
            continue
        seen.add(preset_id)
        normalized.append(preset_id)
    return normalized


def supplier_catalog_presets_for_profile(profile: dict[str, Any]) -> list[dict[str, str]]:
    raw_payload = profile.get("raw_payload") if isinstance(profile.get("raw_payload"), dict) else {}
    preset_ids = raw_payload.get("supplier_catalog_preset_ids")
    if isinstance(preset_ids, list):
        return _presets_by_ids(preset_ids)

    profile_text = _profile_text(profile)
    profile_tokens = _profile_tokens(profile_text)
    okpd2_codes = _profile_okpd2_codes(profile)
    return [
        _public_preset(preset)
        for preset in SUPPLIER_CATALOG_PRESETS
        if _matches_profile(preset, profile_text, profile_tokens, okpd2_codes)
    ]


def _presets_by_ids(preset_ids: list[Any]) -> list[dict[str, str]]:
    presets_by_id = {str(preset["preset_id"]): preset for preset in SUPPLIER_CATALOG_PRESETS}
    selected: list[dict[str, str]] = []
    seen: set[str] = set()
    for preset_id in preset_ids:
        key = str(preset_id)
        if key in seen or key not in presets_by_id:
            continue
        seen.add(key)
        selected.append(_public_preset(presets_by_id[key]))
    return selected


def _matches_profile(
    preset: dict[str, Any],
    profile_text: str,
    profile_tokens: list[str],
    okpd2_codes: list[str],
) -> bool:
    if _matches_okpd2_prefix(preset, okpd2_codes):
        return True
    keywords = preset.get("match_keywords") or preset.get("match_terms") or ()
    return any(_matches_keyword(str(keyword), profile_text, profile_tokens) for keyword in keywords)


def _matches_okpd2_prefix(preset: dict[str, Any], okpd2_codes: list[str]) -> bool:
    prefixes = tuple(str(prefix).casefold().strip() for prefix in preset.get("match_okpd2_prefixes") or ())
    if not prefixes:
        return False
    return any(code.startswith(prefix) for code in okpd2_codes for prefix in prefixes)


def _matches_keyword(keyword: str, profile_text: str, profile_tokens: list[str]) -> bool:
    normalized = " ".join(_profile_tokens(keyword))
    if not normalized:
        return False
    if " " in normalized:
        return normalized in " ".join(profile_tokens)
    return any(token == normalized or token.startswith(normalized) for token in profile_tokens)


def _public_preset(preset: dict[str, Any]) -> dict[str, str]:
    return {
        "preset_id": str(preset["preset_id"]),
        "label": str(preset["label"]),
        "provider": str(preset["provider"]),
        "url_template": str(preset["url_template"]),
    }


def _profile_text(profile: dict[str, Any]) -> str:
    parts: list[str] = []
    for field in (
        "product_name",
        "normalized_name",
        "category",
        "okpd2",
        "classifier_code",
        "classifier_type",
        "details",
    ):
        if text := _text(profile.get(field)):
            parts.append(text)
    search_phrases = profile.get("search_phrases") if isinstance(profile.get("search_phrases"), list) else []
    for phrase in search_phrases:
        if text := _text(phrase):
            parts.append(text)
    return " ".join(parts).casefold()


def _profile_tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(str(text or "").casefold())


def _profile_okpd2_codes(profile: dict[str, Any]) -> list[str]:
    codes: list[str] = []
    for field in ("okpd2", "classifier_code"):
        if text := _text(profile.get(field)):
            codes.append(text.casefold().strip())
    return codes


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
