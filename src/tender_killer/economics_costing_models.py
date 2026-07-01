from __future__ import annotations

from dataclasses import dataclass


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
