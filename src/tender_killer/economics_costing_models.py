from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PositionCostContext:
    profile: dict[str, Any]
    economics: dict[str, Any]
    assumptions: dict[str, Any]
    price_source: dict[str, Any]
    cost_model: str


@dataclass(frozen=True)
class LandedCostTotals:
    base_cost: float | None
    vat_mode: str
    vat_rate_percent: float | None
    vat_cost: float
    risk_reserve_percent: float
    position_risk_reserve: float
    estimated_total_cost: float | None
    target_margin_percent: float | None
    target_price: float | None
