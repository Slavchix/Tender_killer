from __future__ import annotations

from typing import Any
from typing import Callable

from tender_killer.supplier_catalog_presets import supplier_catalog_providers_for_profile
from tender_killer.supplier_price_discovery_collector_state import _collector_catalog_provider
from tender_killer.supplier_price_discovery_collector_state import _collector_provider_name
from tender_killer.supplier_price_discovery_collectors import ProviderCatalogCollector
from tender_killer.supplier_price_discovery_collectors import SchemaOrgProductCollector
from tender_killer.supplier_price_discovery_diagnostics import _merge_diagnostics
from tender_killer.supplier_price_discovery_diagnostics import _skipped_collector_diagnostics
from tender_killer.supplier_price_discovery_queries import BUILT_IN_CATALOG_PROVIDERS
from tender_killer.supplier_price_discovery_queries import _catalog_providers_for_queries
from tender_killer.supplier_price_discovery_queries import _manual_product_catalog_providers_for_queries
from tender_killer.supplier_price_discovery_utils import _positive_env_int


FetchText = Callable[[str], str]
DEFAULT_CATALOG_MAX_PRODUCT_PAGES = 5


def default_price_collectors(fetch_text: FetchText | None = None) -> list[Any]:
    max_product_pages = _positive_env_int(
        "TENDER_KILLER_PRICE_DISCOVERY_MAX_PRODUCT_PAGES",
        DEFAULT_CATALOG_MAX_PRODUCT_PAGES,
    )
    return [
        *[
            ProviderCatalogCollector(provider, fetch_text=fetch_text, max_product_pages=max_product_pages)
            for provider in BUILT_IN_CATALOG_PROVIDERS
        ],
        SchemaOrgProductCollector(fetch_text=fetch_text),
    ]


def _relevant_price_collectors_for_queries(
    queries: list[dict[str, Any]],
    price_collectors: list[Any],
    diagnostics_by_provider: dict[str, dict[str, Any]],
    profile: dict[str, Any] | None = None,
) -> list[Any]:
    query_catalog_providers = _catalog_providers_for_queries(queries)
    allowed_catalog_providers = query_catalog_providers
    if profile is not None:
        profile_catalog_providers = supplier_catalog_providers_for_profile(profile)
        if profile_catalog_providers:
            allowed_catalog_providers = set(profile_catalog_providers)
            allowed_catalog_providers.update(_manual_product_catalog_providers_for_queries(queries))
    relevant_collectors: list[Any] = []
    for collector in price_collectors:
        catalog_provider = _collector_catalog_provider(collector)
        if catalog_provider is not None and catalog_provider not in allowed_catalog_providers:
            _merge_diagnostics(
                diagnostics_by_provider,
                _skipped_collector_diagnostics(
                    _collector_provider_name(collector),
                    "not_relevant_for_profile",
                ),
            )
            continue
        relevant_collectors.append(collector)
    return relevant_collectors
