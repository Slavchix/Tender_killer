from __future__ import annotations

from typing import Any

from tender_killer.analysis_condition_groups_service import semantic_family


BLOCKER_CATEGORIES = {"legal", "national_regime"}
DOCUMENT_CATEGORIES = {"documents", "standards", "qualification", "subject"}
FULFILLMENT_CATEGORIES = {"contract", "delivery"}
ACCEPTANCE_PAYMENT_CATEGORIES = {"acceptance", "financial", "payment"}
PRICE_FACTOR_CATEGORIES = ACCEPTANCE_PAYMENT_CATEGORIES | FULFILLMENT_CATEGORIES | {"standards"}


def fallback_kind(item: dict[str, Any]) -> str:
    category = _text(item.get("category"))
    severity = _text(item.get("severity"))
    if severity == "high" or category in BLOCKER_CATEGORIES:
        return "blocker"
    if category in DOCUMENT_CATEGORIES:
        return "supplier_document"
    if category in FULFILLMENT_CATEGORIES | ACCEPTANCE_PAYMENT_CATEGORIES:
        return "execution_term"
    return "requirement"


def operator_group(kind: str, category: str, is_blocker: bool, needs_review: bool) -> str:
    if needs_review:
        return "manual_review"
    if is_blocker:
        return "blocker"
    if category in ACCEPTANCE_PAYMENT_CATEGORIES:
        return "acceptance_payment"
    if category in FULFILLMENT_CATEGORIES or kind == "execution_term":
        return "execution"
    if kind in {"subject", "supplier_document", "requirement"}:
        return "prepare"
    return "review"


def price_impact(category: str, *, label: str = "") -> str:
    family = semantic_family(label, category)
    if family in {"short_delivery", "montage_launch"}:
        return "logistics"
    if family in {"closing_documents", "contract_security"}:
        return "working_capital"
    if family == "certificate_documents":
        return "documents"
    if family == "warranty":
        return "reserve"
    if category == "delivery":
        return "logistics"
    if category in {"financial", "payment", "acceptance"}:
        return "working_capital"
    if category == "documents":
        return "documents"
    if category == "contract":
        return "reserve"
    if category in {"legal", "national_regime", "standards"}:
        return "compliance"
    return "none"


def priority(kind: str, category: str, severity: str, is_blocker: bool, needs_review: bool) -> int:
    if needs_review:
        return 95
    if is_blocker:
        return 90 if severity == "high" else 80
    if category in ACCEPTANCE_PAYMENT_CATEGORIES:
        return 65
    if category in FULFILLMENT_CATEGORIES:
        return 60
    if kind in {"supplier_document", "requirement"}:
        return 50
    if kind == "subject":
        return 20
    return 40


def canonical_label(label: str, category: str) -> str:
    family = semantic_family(label, category)
    if family == "national_regime":
        return "национальный режим/страна происхождения"
    if family == "license_sro":
        return "лицензия/СРО"
    if family == "contract_security":
        return "обеспечение исполнения контракта"
    return label


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()
