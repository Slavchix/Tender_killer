from __future__ import annotations

from typing import Any

from tender_killer.analysis_condition_groups_service import EXPECTED_TZ_CHECKS
from tender_killer.analysis_condition_groups_service import condition_family_and_measure as _condition_family_and_measure
from tender_killer.analysis_condition_groups_service import condition_family_and_polarity as _condition_family_and_polarity
from tender_killer.analysis_condition_groups_service import conflict_evidence_quality as _conflict_evidence_quality
from tender_killer.analysis_condition_groups_service import expected_families as _expected_families
from tender_killer.analysis_document_state_service import build_document_state as _document_state
from tender_killer.analysis_operator_item_service import build_operator_item as _operator_item
from tender_killer.analysis_types import OperatorItem


def prepare_operator_condition_items(
    items: list[OperatorItem],
    analysis: dict[str, Any],
    documents: list[dict[str, Any]],
) -> list[OperatorItem]:
    return _add_expected_missing_checks(_annotate_conflicts(items), analysis, documents)


def _annotate_conflicts(items: list[OperatorItem]) -> list[OperatorItem]:
    polarity_by_family: dict[str, set[str]] = {}
    measure_by_family: dict[str, set[str]] = {}
    for item in items:
        family, polarity = _condition_family_and_polarity(item)
        if family and polarity:
            polarity_by_family.setdefault(family, set()).add(polarity)
        measure_family, measure = _condition_family_and_measure(item)
        if measure_family and measure:
            measure_by_family.setdefault(measure_family, set()).add(measure)

    polarity_conflicts = {
        family
        for family, polarities in polarity_by_family.items()
        if "positive" in polarities and "negative" in polarities
    }
    measure_conflicts = {family for family, measures in measure_by_family.items() if len(measures) > 1}
    conflicted = polarity_conflicts | measure_conflicts
    if not conflicted:
        return items

    annotated: list[OperatorItem] = []
    for item in items:
        family, polarity = _condition_family_and_polarity(item)
        measure_family, measure = _condition_family_and_measure(item)
        flags: list[str] = []
        if family in polarity_conflicts and polarity:
            flags.append(
                "В документах есть взаимоисключающие формулировки: условие одновременно найдено как применимое и как отсутствующее."
            )
        if measure_family in measure_conflicts and measure:
            flags.append("В документах есть разные числовые значения одного условия; нужно выбрать применимую редакцию.")
        if not flags:
            annotated.append(item)
            continue
        updated = {
            **item,
            "needs_review": True,
            "conflict_flags": flags,
            "evidence_quality": _conflict_evidence_quality(flags),
            "operator_check": f"Разобрать противоречие по условию «{item['label']}»: {'; '.join(flags)}",
        }
        annotated.append(updated)
    return annotated


def _add_expected_missing_checks(
    items: list[OperatorItem],
    analysis: dict[str, Any],
    documents: list[dict[str, Any]],
) -> list[OperatorItem]:
    if not documents or _document_state(documents).get("text_ready", 0) == 0:
        return items
    present: set[str] = set()
    for item in items:
        present.update(_expected_families(item))
    additions: list[OperatorItem] = []
    for spec in EXPECTED_TZ_CHECKS:
        family = spec["family"]
        if family in present:
            continue
        additions.append(
            _operator_item(
                {
                    "id": f"expected:{family}",
                    "kind": "expected_check",
                    "label": spec["label"],
                    "category": spec["category"],
                    "severity": "medium",
                    "source": "Ожидаемая проверка",
                    "operator_action": spec["action"],
                    "expected_missing": True,
                    "needs_review": True,
                    "priority": 30,
                },
                len(items) + len(additions),
            )
        )
    return [*items, *additions]
