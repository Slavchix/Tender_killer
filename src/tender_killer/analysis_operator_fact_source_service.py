from __future__ import annotations

from typing import Any

from tender_killer.analysis_legacy_operator_items_service import build_legacy_operator_items
from tender_killer.analysis_operator_item_service import build_operator_item as _operator_item
from tender_killer.analysis_types import AnalysisFactsContract
from tender_killer.analysis_types import OperatorItem


def build_operator_fact_source(analysis: dict[str, Any]) -> dict[str, Any]:
    facts_contract = _analysis_facts(analysis.get("analysis_facts"))
    if facts_contract:
        return {
            "source": "analysis_facts",
            "items": _fact_items(facts_contract.get("items")),
            "metrics": facts_contract.get("metrics"),
        }
    return {
        "source": "legacy",
        "items": build_legacy_operator_items(analysis),
        "metrics": None,
    }


def _fact_items(value: Any) -> list[OperatorItem]:
    items: list[OperatorItem] = []
    for index, raw_item in enumerate(value if isinstance(value, list) else []):
        if isinstance(raw_item, dict) and raw_item.get("label"):
            items.append(_operator_item(raw_item, index))
    return items


def _analysis_facts(value: Any) -> AnalysisFactsContract | None:
    if isinstance(value, dict) and value.get("version") == 1:
        return value
    return None
