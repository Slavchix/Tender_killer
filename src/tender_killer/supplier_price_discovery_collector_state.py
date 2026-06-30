from __future__ import annotations

from typing import Any

from tender_killer.supplier_price_discovery_utils import _text


def _collector_catalog_provider(collector: Any) -> str | None:
    catalog_provider = _text(getattr(collector, "catalog_provider", None))
    if catalog_provider:
        return catalog_provider.casefold()
    provider = _text(getattr(collector, "provider", None))
    if provider and provider.casefold().startswith("catalog_"):
        return provider.casefold().removeprefix("catalog_")
    return None


def _collector_provider_name(collector: Any) -> str:
    return _text(getattr(collector, "provider", None)) or collector.__class__.__name__


def _collector_is_access_blocked(collector: Any) -> bool:
    return bool(getattr(collector, "_tender_killer_access_blocked", False))


def _set_collector_policy_context(collectors: list[Any], tender_position_count: int) -> None:
    for collector in collectors:
        try:
            setattr(collector, "tender_position_count", tender_position_count)
        except Exception:
            continue


def _mark_collector_access_blocked(collector: Any) -> None:
    try:
        setattr(collector, "_tender_killer_access_blocked", True)
    except Exception:
        return
