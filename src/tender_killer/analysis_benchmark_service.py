from __future__ import annotations

from typing import Any


REQUIRED_TZ_BENCHMARK_CATEGORIES: tuple[str, ...] = (
    "small_supply",
    "cartridges_paper",
    "construction_materials",
    "services",
    "advance_payment",
    "no_advance",
    "conflicting_documents",
    "poor_ocr",
    "multiple_revisions",
)

TZ_BENCHMARK_TARGET_CASE_COUNT = {"min": 20, "max": 30}


def score_tz_benchmark_case(case: dict[str, Any], analysis: Any) -> dict[str, Any]:
    """Score one manually labeled TZ benchmark case against an analysis payload."""
    payload = _analysis_dict(analysis)
    expected_labels = _text_set(case.get("expected_labels"))
    expected_terms = _text_set(case.get("expected_terms"))
    expected_conflicts = _text_set(case.get("expected_conflicts"))
    expected_missing = _text_set(case.get("expected_missing"))
    absent_labels = _text_set(case.get("absent_labels"))

    found_labels = _found_labels(payload)
    found_terms = _found_terms(payload)
    found_conflicts = _found_conflicts(payload)
    found_expected_missing = _found_expected_missing(payload)

    matched_labels = _sorted(expected_labels & found_labels)
    missed_labels = _sorted(expected_labels - found_labels)
    false_positive_labels = _sorted((found_labels & absent_labels) | (found_labels - expected_labels - found_conflicts - found_expected_missing))
    matched_terms = _sorted(expected_terms & found_terms)
    missed_terms = _sorted(expected_terms - found_terms)
    matched_conflicts = _sorted(expected_conflicts & found_conflicts)
    missed_conflicts = _sorted(expected_conflicts - found_conflicts)
    matched_expected_missing = _sorted(expected_missing & found_expected_missing)
    missed_expected_missing = _sorted(expected_missing - found_expected_missing)

    expected_total = len(expected_labels) + len(expected_terms) + len(expected_conflicts) + len(expected_missing)
    matched_total = len(matched_labels) + len(matched_terms) + len(matched_conflicts) + len(matched_expected_missing)
    precision_denominator = len(matched_labels) + len(false_positive_labels)

    return {
        "name": str(case.get("name") or ""),
        "category": str(case.get("category") or "uncategorized"),
        "matched_labels": matched_labels,
        "missed_labels": missed_labels,
        "false_positive_labels": false_positive_labels,
        "matched_terms": matched_terms,
        "missed_terms": missed_terms,
        "matched_conflicts": matched_conflicts,
        "missed_conflicts": missed_conflicts,
        "matched_expected_missing": matched_expected_missing,
        "missed_expected_missing": missed_expected_missing,
        "recall": _ratio(matched_total, expected_total),
        "precision": _ratio(len(matched_labels), precision_denominator),
        "manual_review_required": bool(
            matched_conflicts
            or missed_conflicts
            or matched_expected_missing
            or missed_expected_missing
            or missed_labels
            or missed_terms
        ),
    }


def summarize_tz_benchmark_scores(scores: list[dict[str, Any]]) -> dict[str, Any]:
    categories = sorted({str(score.get("category") or "uncategorized") for score in scores})
    return {
        "target_case_count": dict(TZ_BENCHMARK_TARGET_CASE_COUNT),
        "cases": len(scores),
        "categories": categories,
        "missing_categories": [category for category in REQUIRED_TZ_BENCHMARK_CATEGORIES if category not in categories],
        "average_recall": _average(score.get("recall") for score in scores),
        "average_precision": _average(score.get("precision") for score in scores),
        "manual_review_cases": sum(1 for score in scores if score.get("manual_review_required")),
    }


def _analysis_dict(analysis: Any) -> dict[str, Any]:
    if isinstance(analysis, dict):
        return analysis
    to_dict = getattr(analysis, "to_dict", None)
    if callable(to_dict):
        result = to_dict()
        return result if isinstance(result, dict) else {}
    return {}


def _found_labels(analysis: dict[str, Any]) -> set[str]:
    labels = set()
    for key in ("requirements", "risks", "red_flags"):
        labels.update(_text_set(analysis.get(key)))
    for item in _analysis_facts(analysis):
        if item.get("expected_missing"):
            continue
        label = _text(item.get("label"))
        if label:
            labels.add(label)
    for item in _operator_items(analysis):
        if item.get("expected_missing"):
            continue
        label = _text(item.get("label"))
        if label:
            labels.add(label)
    for term in analysis.get("execution_terms") or []:
        if isinstance(term, dict):
            label = _text(term.get("label"))
            if label:
                labels.add(label)
    return labels


def _found_terms(analysis: dict[str, Any]) -> set[str]:
    terms = set()
    for term in analysis.get("execution_terms") or []:
        if isinstance(term, dict):
            term_type = _text(term.get("type"))
            if term_type:
                terms.add(term_type)
    for item in [*_analysis_facts(analysis), *_operator_items(analysis)]:
        term_type = _text(item.get("type"))
        if item.get("kind") == "execution_term" and term_type:
            terms.add(term_type)
    return terms


def _found_conflicts(analysis: dict[str, Any]) -> set[str]:
    return {
        label
        for item in [*_analysis_facts(analysis), *_operator_items(analysis)]
        if item.get("conflict_flags") and (label := _text(item.get("label")))
    }


def _found_expected_missing(analysis: dict[str, Any]) -> set[str]:
    return {
        label
        for item in [*_analysis_facts(analysis), *_operator_items(analysis)]
        if item.get("expected_missing") and (label := _text(item.get("label")))
    }


def _analysis_facts(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    facts = analysis.get("analysis_facts")
    items = facts.get("items") if isinstance(facts, dict) else []
    return [item for item in items if isinstance(item, dict)]


def _operator_items(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    operator_view = analysis.get("operator_view")
    if not isinstance(operator_view, dict):
        return []
    sections = operator_view.get("major_blocks") or operator_view.get("sections") or []
    items: list[dict[str, Any]] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        items.extend(item for item in section.get("items") or [] if isinstance(item, dict))
    return items


def _text_set(value: Any) -> set[str]:
    if not isinstance(value, (list, tuple, set)):
        return set()
    return {_text(item) for item in value if _text(item)}


def _sorted(values: set[str]) -> list[str]:
    return sorted(values, key=str.casefold)


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 1.0
    return round(numerator / denominator, 4)


def _average(values: Any) -> float:
    numbers = []
    for value in values:
        try:
            numbers.append(float(value))
        except (TypeError, ValueError):
            continue
    if not numbers:
        return 1.0
    return round(sum(numbers) / len(numbers), 4)


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()
