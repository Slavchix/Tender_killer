from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import unquote


@dataclass(frozen=True)
class TenderPath:
    source: str
    external_id: str


@dataclass(frozen=True)
class ProductProfileEconomicsPath:
    source: str
    external_id: str
    position_index: int


@dataclass(frozen=True)
class ProductProfileSupplierOptionsPath:
    source: str
    external_id: str
    position_index: int


@dataclass(frozen=True)
class ProductProfileSupplierOptionSelectPath:
    source: str
    external_id: str
    position_index: int
    option_index: int


@dataclass(frozen=True)
class ProductProfileSupplierDiscoveryCandidatePath:
    source: str
    external_id: str
    position_index: int
    candidate_index: int


@dataclass(frozen=True)
class ProductProfilePriceCandidateReviewPath:
    source: str
    external_id: str
    position_index: int
    candidate_id: int
    action: str


def parse_tender_path(path: str, suffix: str = "") -> TenderPath | None:
    parts = path.split("/")
    suffix_parts = [part for part in suffix.split("/") if part]
    expected_length = 5 + len(suffix_parts)
    if len(parts) != expected_length:
        return None
    if parts[:3] != ["", "api", "tenders"]:
        return None
    if suffix_parts and parts[5:] != suffix_parts:
        return None
    if not parts[3] or not parts[4]:
        return None
    return TenderPath(source=unquote(parts[3]), external_id=unquote(parts[4]))


def parse_product_profile_economics_path(path: str) -> ProductProfileEconomicsPath | None:
    parts = path.split("/")
    if len(parts) != 8 or parts[:3] != ["", "api", "tenders"]:
        return None
    if parts[5] != "product-profiles" or parts[7] != "economics":
        return None
    if not parts[3] or not parts[4]:
        return None
    try:
        position_index = int(parts[6])
    except ValueError:
        return None
    if position_index <= 0:
        return None
    return ProductProfileEconomicsPath(
        source=unquote(parts[3]),
        external_id=unquote(parts[4]),
        position_index=position_index,
    )


def parse_product_profile_economics_assumptions_path(path: str) -> ProductProfileEconomicsPath | None:
    parts = path.split("/")
    if len(parts) != 9 or parts[:3] != ["", "api", "tenders"]:
        return None
    if parts[5] != "product-profiles" or parts[7] != "economics" or parts[8] != "assumptions":
        return None
    if not parts[3] or not parts[4]:
        return None
    try:
        position_index = int(parts[6])
    except ValueError:
        return None
    if position_index <= 0:
        return None
    return ProductProfileEconomicsPath(
        source=unquote(parts[3]),
        external_id=unquote(parts[4]),
        position_index=position_index,
    )


def parse_product_profile_auto_economics_path(path: str) -> ProductProfileEconomicsPath | None:
    parts = path.split("/")
    if len(parts) != 9 or parts[:3] != ["", "api", "tenders"]:
        return None
    if parts[5] != "product-profiles" or parts[7] != "economics" or parts[8] != "auto-estimate":
        return None
    if not parts[3] or not parts[4]:
        return None
    try:
        position_index = int(parts[6])
    except ValueError:
        return None
    if position_index <= 0:
        return None
    return ProductProfileEconomicsPath(
        source=unquote(parts[3]),
        external_id=unquote(parts[4]),
        position_index=position_index,
    )


def parse_product_profile_auto_economics_accept_path(path: str) -> ProductProfileEconomicsPath | None:
    parts = path.split("/")
    if len(parts) != 10 or parts[:3] != ["", "api", "tenders"]:
        return None
    if parts[5] != "product-profiles" or parts[7] != "economics" or parts[8] != "auto-estimate" or parts[9] != "accept":
        return None
    if not parts[3] or not parts[4]:
        return None
    try:
        position_index = int(parts[6])
    except ValueError:
        return None
    if position_index <= 0:
        return None
    return ProductProfileEconomicsPath(
        source=unquote(parts[3]),
        external_id=unquote(parts[4]),
        position_index=position_index,
    )


def parse_product_profile_supplier_options_path(path: str) -> ProductProfileSupplierOptionsPath | None:
    parts = path.split("/")
    if len(parts) != 8 or parts[:3] != ["", "api", "tenders"]:
        return None
    if parts[5] != "product-profiles" or parts[7] != "supplier-options":
        return None
    if not parts[3] or not parts[4]:
        return None
    try:
        position_index = int(parts[6])
    except ValueError:
        return None
    if position_index <= 0:
        return None
    return ProductProfileSupplierOptionsPath(
        source=unquote(parts[3]),
        external_id=unquote(parts[4]),
        position_index=position_index,
    )


def parse_product_profile_supplier_search_prepare_path(path: str) -> ProductProfileSupplierOptionsPath | None:
    parts = path.split("/")
    if len(parts) != 9 or parts[:3] != ["", "api", "tenders"]:
        return None
    if parts[5] != "product-profiles" or parts[7] != "supplier-search" or parts[8] != "prepare":
        return None
    if not parts[3] or not parts[4]:
        return None
    try:
        position_index = int(parts[6])
    except ValueError:
        return None
    if position_index <= 0:
        return None
    return ProductProfileSupplierOptionsPath(
        source=unquote(parts[3]),
        external_id=unquote(parts[4]),
        position_index=position_index,
    )


def parse_product_profile_supplier_catalog_presets_path(path: str) -> ProductProfileSupplierOptionsPath | None:
    parts = path.split("/")
    if len(parts) != 8 or parts[:3] != ["", "api", "tenders"]:
        return None
    if parts[5] != "product-profiles" or parts[7] != "supplier-catalog-presets":
        return None
    if not parts[3] or not parts[4]:
        return None
    try:
        position_index = int(parts[6])
    except ValueError:
        return None
    if position_index <= 0:
        return None
    return ProductProfileSupplierOptionsPath(
        source=unquote(parts[3]),
        external_id=unquote(parts[4]),
        position_index=position_index,
    )


def parse_product_profile_supplier_discovery_candidates_path(path: str) -> ProductProfileSupplierOptionsPath | None:
    parts = path.split("/")
    if len(parts) != 9 or parts[:3] != ["", "api", "tenders"]:
        return None
    if parts[5] != "product-profiles" or parts[7] != "supplier-discovery" or parts[8] != "candidates":
        return None
    if not parts[3] or not parts[4]:
        return None
    try:
        position_index = int(parts[6])
    except ValueError:
        return None
    if position_index <= 0:
        return None
    return ProductProfileSupplierOptionsPath(
        source=unquote(parts[3]),
        external_id=unquote(parts[4]),
        position_index=position_index,
    )


def parse_product_profile_supplier_discovery_run_path(path: str) -> ProductProfileSupplierOptionsPath | None:
    parts = path.split("/")
    if len(parts) != 9 or parts[:3] != ["", "api", "tenders"]:
        return None
    if parts[5] != "product-profiles" or parts[7] != "supplier-discovery" or parts[8] != "run":
        return None
    if not parts[3] or not parts[4]:
        return None
    try:
        position_index = int(parts[6])
    except ValueError:
        return None
    if position_index <= 0:
        return None
    return ProductProfileSupplierOptionsPath(
        source=unquote(parts[3]),
        external_id=unquote(parts[4]),
        position_index=position_index,
    )


def parse_product_profile_supplier_discovery_url_path(path: str) -> ProductProfileSupplierOptionsPath | None:
    parts = path.split("/")
    if len(parts) != 9 or parts[:3] != ["", "api", "tenders"]:
        return None
    if parts[5] != "product-profiles" or parts[7] != "supplier-discovery" or parts[8] != "url":
        return None
    if not parts[3] or not parts[4]:
        return None
    try:
        position_index = int(parts[6])
    except ValueError:
        return None
    if position_index <= 0:
        return None
    return ProductProfileSupplierOptionsPath(
        source=unquote(parts[3]),
        external_id=unquote(parts[4]),
        position_index=position_index,
    )


def parse_product_profile_supplier_discovery_candidate_import_path(
    path: str,
) -> ProductProfileSupplierDiscoveryCandidatePath | None:
    parts = path.split("/")
    if len(parts) != 11 or parts[:3] != ["", "api", "tenders"]:
        return None
    if (
        parts[5] != "product-profiles"
        or parts[7] != "supplier-discovery"
        or parts[8] != "candidates"
        or parts[10] != "import"
    ):
        return None
    if not parts[3] or not parts[4]:
        return None
    try:
        position_index = int(parts[6])
        candidate_index = int(parts[9])
    except ValueError:
        return None
    if position_index <= 0 or candidate_index < 0:
        return None
    return ProductProfileSupplierDiscoveryCandidatePath(
        source=unquote(parts[3]),
        external_id=unquote(parts[4]),
        position_index=position_index,
        candidate_index=candidate_index,
    )


def parse_product_profile_price_candidate_review_path(
    path: str,
) -> ProductProfilePriceCandidateReviewPath | None:
    parts = path.split("/")
    if len(parts) != 10 or parts[:3] != ["", "api", "tenders"]:
        return None
    if parts[5] != "product-profiles" or parts[7] != "price-candidates":
        return None
    if parts[9] not in {"confirm", "reject"}:
        return None
    if not parts[3] or not parts[4]:
        return None
    try:
        position_index = int(parts[6])
        candidate_id = int(parts[8])
    except ValueError:
        return None
    if position_index <= 0 or candidate_id <= 0:
        return None
    return ProductProfilePriceCandidateReviewPath(
        source=unquote(parts[3]),
        external_id=unquote(parts[4]),
        position_index=position_index,
        candidate_id=candidate_id,
        action=parts[9],
    )


def parse_product_profile_supplier_option_select_path(path: str) -> ProductProfileSupplierOptionSelectPath | None:
    parts = path.split("/")
    if len(parts) != 10 or parts[:3] != ["", "api", "tenders"]:
        return None
    if parts[5] != "product-profiles" or parts[7] != "supplier-options" or parts[9] != "select":
        return None
    if not parts[3] or not parts[4]:
        return None
    try:
        position_index = int(parts[6])
        option_index = int(parts[8])
    except ValueError:
        return None
    if position_index <= 0 or option_index < 0:
        return None
    return ProductProfileSupplierOptionSelectPath(
        source=unquote(parts[3]),
        external_id=unquote(parts[4]),
        position_index=position_index,
        option_index=option_index,
    )


def parse_product_profile_supplier_option_best_select_path(path: str) -> ProductProfileSupplierOptionsPath | None:
    parts = path.split("/")
    if len(parts) != 10 or parts[:3] != ["", "api", "tenders"]:
        return None
    if parts[5] != "product-profiles" or parts[7] != "supplier-options" or parts[8] != "best" or parts[9] != "select":
        return None
    if not parts[3] or not parts[4]:
        return None
    try:
        position_index = int(parts[6])
    except ValueError:
        return None
    if position_index <= 0:
        return None
    return ProductProfileSupplierOptionsPath(
        source=unquote(parts[3]),
        external_id=unquote(parts[4]),
        position_index=position_index,
    )


def parse_database_table_path(path: str) -> str | None:
    parts = path.split("/")
    if len(parts) != 5 or parts[:4] != ["", "api", "db", "tables"] or not parts[4]:
        return None
    return unquote(parts[4])
