from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class PriceCandidate(TypedDict, total=False):
    id: int
    provider: str
    product_name: str
    supplier_name: str
    source_url: str
    source_query: str
    source_kind: str
    unit_price: float
    currency: str
    unit: str
    vat_mode: str
    vat_rate_percent: float
    availability: str
    delivery_note: str
    delivery_cost: float
    delivery_rate_percent: float
    delivery_cost_per_unit: float
    confidence: str
    confidence_reasons: list[str]
    match_reasons: list[str]
    review_status: str
    quality_status: str
    auto_eligible: bool
    quality_flags: list["PriceCandidateQualityFlag"]
    price_breaks: list[dict[str, float]]
    selected_price_break: dict[str, float]
    price_break_selection_quantity: float
    pack_quantity: float
    stock_quantity: float
    preorder_quantity: float
    minimum_order_quantity: float
    minimum_order_amount: float
    raw_payload: dict[str, Any]
    pricing_passport: "PriceCandidatePassport"


class PriceCandidateQualityFlag(TypedDict):
    id: str
    severity: str
    label: str
    detail: str


class PriceCandidateQuality(TypedDict):
    quality_status: str
    auto_eligible: bool
    quality_flags: list[PriceCandidateQualityFlag]


class PriceCandidatePassportRule(TypedDict, total=False):
    enabled: bool
    provider: str
    vat_mode: str
    delivery_rate_percent: float | None
    delivery_cost_per_unit: float | None
    operator_note: str


class PriceCandidatePassportReuse(TypedDict, total=False):
    source: str
    external_id: str
    position_index: int
    unit_match: bool
    pack_quantity: float | None
    freshness_status: str
    operator_note: str


class PriceCandidatePassportStep(TypedDict):
    id: str
    label: str
    status: str


class PriceCandidatePassport(TypedDict):
    provider: Any
    supplier_name: Any
    product_name: Any
    source_url: Any
    source_kind: Any
    source_label: str
    observed_at: Any
    freshness_label: str
    match_confidence: Any
    match_reasons: list[str]
    unit_pack_label: str
    vat_label: str
    delivery_label: str
    evidence_url: Any
    evidence_label: str
    unit_price: float | None
    total_price: float | None
    quantity: float | None
    unit: Any
    currency: Any
    availability: Any
    vat_mode: Any
    delivery_note: str | None
    stock_quantity: float | None
    preorder_quantity: float | None
    pack_quantity: float | None
    minimum_order_quantity: float | None
    quality_status: str
    auto_eligible: bool
    confidence: Any
    positive_checks: list[str]
    review_checks: list[str]
    block_checks: list[str]
    funnel_steps: list[PriceCandidatePassportStep]
    next_action: str
    summary: str
    vat_note: NotRequired[Any]
    trusted_supplier_rule: NotRequired[PriceCandidatePassportRule]
    rule_label: NotRequired[str]
    reuse: NotRequired[PriceCandidatePassportReuse]
