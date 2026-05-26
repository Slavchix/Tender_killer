from __future__ import annotations

from typing import Any


SUPPLIER_CATALOG_PRESETS: tuple[dict[str, Any], ...] = (
    {
        "preset_id": "officemag_office_supplies",
        "label": "OfficeMag",
        "provider": "officemag",
        "url_template": "https://www.officemag.ru/search/?q={query}",
        "match_terms": ("office", "paper", "stationery", "бумага", "канцел", "офис", "17.12"),
    },
    {
        "preset_id": "komus_office_supplies",
        "label": "Komus",
        "provider": "komus",
        "url_template": "https://www.komus.ru/search/?text={query}",
        "match_terms": ("office", "paper", "stationery", "бумага", "канцел", "офис", "17.12"),
    },
    {
        "preset_id": "petrovich_building_materials",
        "label": "Petrovich",
        "provider": "petrovich",
        "url_template": "https://petrovich.ru/search/?q={query}",
        "match_terms": ("building", "cement", "concrete", "цемент", "бетон", "строит", "строй", "смес"),
    },
    {
        "preset_id": "vseinstrumenti_building_materials",
        "label": "Vseinstrumenti",
        "provider": "vseinstrumenti",
        "url_template": "https://www.vseinstrumenti.ru/search/?q={query}",
        "match_terms": ("building", "cement", "tool", "цемент", "инструмент", "строит", "строй", "смес"),
    },
)


def supplier_catalog_presets_for_profile(profile: dict[str, Any]) -> list[dict[str, str]]:
    raw_payload = profile.get("raw_payload") if isinstance(profile.get("raw_payload"), dict) else {}
    preset_ids = raw_payload.get("supplier_catalog_preset_ids")
    if isinstance(preset_ids, list):
        return _presets_by_ids(preset_ids)

    profile_text = _profile_text(profile)
    return [
        _public_preset(preset)
        for preset in SUPPLIER_CATALOG_PRESETS
        if _matches_profile(preset, profile_text)
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


def _matches_profile(preset: dict[str, Any], profile_text: str) -> bool:
    return any(str(term).casefold() in profile_text for term in preset.get("match_terms") or ())


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


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
