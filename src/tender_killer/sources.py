from __future__ import annotations

from tender_killer.adapters import MoscowSupplierPortalAdapter, MosregMarketAdapter
from tender_killer.adapters.base import BaseAdapter
from tender_killer.config import Settings
from tender_killer.filter_store import FilterProfileCollection
from tender_killer.filters import FilterProfile


SOURCE_ALIASES = {
    "moscow": "moscow",
    "msk": "moscow",
    "zakupki.mos.ru": "moscow",
    "moscow_supplier_portal": "moscow",
    "mosreg": "mosreg",
    "mo": "mosreg",
    "market.mosreg.ru": "mosreg",
    "mosreg_market": "mosreg",
}

SOURCE_LABELS = {
    "moscow": "Москва: zakupki.mos.ru",
    "mosreg": "МО: market.mosreg.ru",
}


def normalize_sources(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        key = SOURCE_ALIASES.get(value.strip().lower())
        if key and key not in normalized:
            normalized.append(key)
    return tuple(normalized) or ("moscow", "mosreg")


def build_adapters(profile: FilterProfile, settings: Settings) -> list[BaseAdapter]:
    sources = normalize_sources(profile.sources)
    return _build_adapters_for_sources(sources, settings)


def build_adapters_for_collection(collection: FilterProfileCollection, settings: Settings) -> list[BaseAdapter]:
    raw_sources: list[str] = []
    active_profiles = collection.active_profiles()
    if not active_profiles:
        return []
    for named_profile in active_profiles:
        raw_sources.extend(named_profile.profile.sources)
    sources = normalize_sources(raw_sources)
    return _build_adapters_for_sources(sources, settings)


def _build_adapters_for_sources(sources: tuple[str, ...], settings: Settings) -> list[BaseAdapter]:
    adapters: list[BaseAdapter] = []
    if "moscow" in sources:
        adapters.append(MoscowSupplierPortalAdapter(settings.moscow_url, settings.request_timeout_seconds))
    if "mosreg" in sources:
        adapters.append(MosregMarketAdapter(settings.mosreg_url, settings.request_timeout_seconds))
    return adapters
