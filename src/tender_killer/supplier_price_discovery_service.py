from __future__ import annotations

import httpx

from tender_killer.supplier_officemag_parser import _officemag_product_scopes
from tender_killer.supplier_officemag_parser import _officemag_visible_candidates
from tender_killer.supplier_price_discovery_collectors import ProviderCatalogCollector
from tender_killer.supplier_price_discovery_collectors import SCHEMA_ORG_PRODUCT_PROVIDER
from tender_killer.supplier_price_discovery_collectors import SchemaOrgProductCollector
from tender_killer.supplier_price_discovery_diagnostics import MANUAL_PRODUCT_LINK_KIND
from tender_killer.supplier_price_discovery_diagnostics import NO_SUPPLIER_CANDIDATES_MESSAGE
from tender_killer.supplier_price_discovery_limits import DEFAULT_BULK_DISCOVERY_CANDIDATE_LIMIT
from tender_killer.supplier_price_discovery_limits import DEFAULT_BULK_DISCOVERY_PROFILE_THRESHOLD
from tender_killer.supplier_price_discovery_limits import DEFAULT_SINGLE_DISCOVERY_CANDIDATE_LIMIT
from tender_killer.supplier_price_discovery_matching import _candidate_matches_profile_intent
from tender_killer.supplier_price_discovery_matching import _provider_catalog_candidates_matching_query
from tender_killer.supplier_price_discovery_policy import _manual_required_tender_discovery_result
from tender_killer.supplier_price_discovery_policy import tender_price_discovery_policy_for_tender
from tender_killer.supplier_price_discovery_queries import _refreshed_supplier_search_queries
from tender_killer.supplier_price_discovery_routing import DEFAULT_CATALOG_MAX_PRODUCT_PAGES
from tender_killer.supplier_price_discovery_routing import _relevant_price_collectors_for_queries
from tender_killer.supplier_price_discovery_routing import default_price_collectors
from tender_killer.supplier_price_discovery_utils import _append_unique_url
from tender_killer.supplier_price_discovery_utils import _catalog_token_stems
from tender_killer.supplier_price_discovery_utils import _fetch_public_text
from tender_killer.supplier_price_discovery_workflows import DEFAULT_TENDER_PRICE_DISCOVERY_MAX_POSITIONS
from tender_killer.supplier_price_discovery_workflows import ProgressCallback
from tender_killer.supplier_price_discovery_workflows import run_profile_supplier_price_discovery
from tender_killer.supplier_price_discovery_workflows import run_profile_supplier_url_discovery
from tender_killer.supplier_price_discovery_workflows import run_tender_supplier_price_discovery


_LEGACY_CATALOG_QUERY_STOP_WORDS = {
    "для",
    "товар",
    "товара",
    "товары",
    "работа",
    "работы",
    "услуга",
    "услуги",
    "офисной",
    "офисная",
    "техники",
    "техника",
    "office",
    "for",
    "the",
}


# Compatibility facade: tests and existing API code still import these names here.
__all__ = [
    "DEFAULT_BULK_DISCOVERY_CANDIDATE_LIMIT",
    "DEFAULT_BULK_DISCOVERY_PROFILE_THRESHOLD",
    "DEFAULT_CATALOG_MAX_PRODUCT_PAGES",
    "DEFAULT_SINGLE_DISCOVERY_CANDIDATE_LIMIT",
    "DEFAULT_TENDER_PRICE_DISCOVERY_MAX_POSITIONS",
    "MANUAL_PRODUCT_LINK_KIND",
    "NO_SUPPLIER_CANDIDATES_MESSAGE",
    "ProgressCallback",
    "ProviderCatalogCollector",
    "SCHEMA_ORG_PRODUCT_PROVIDER",
    "SchemaOrgProductCollector",
    "_LEGACY_CATALOG_QUERY_STOP_WORDS",
    "_append_unique_url",
    "_candidate_matches_profile_intent",
    "_catalog_token_stems",
    "_fetch_public_text",
    "_manual_required_tender_discovery_result",
    "_officemag_product_scopes",
    "_officemag_visible_candidates",
    "_provider_catalog_candidates_matching_query",
    "_refreshed_supplier_search_queries",
    "_relevant_price_collectors_for_queries",
    "default_price_collectors",
    "httpx",
    "run_profile_supplier_price_discovery",
    "run_profile_supplier_url_discovery",
    "run_tender_supplier_price_discovery",
    "tender_price_discovery_policy_for_tender",
]
