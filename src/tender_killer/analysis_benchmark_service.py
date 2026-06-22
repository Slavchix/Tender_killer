from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tender_killer.analysis import analyze_tender_texts
from tender_killer.analysis_facts_service import build_analysis_facts
from tender_killer.analysis_operator_view_service import build_analysis_operator_view
from tender_killer.analysis_source_service import attach_document_sources


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
DEFAULT_TZ_BENCHMARK_CASES_PATH = Path(__file__).resolve().parent / "analysis_benchmark_cases" / "tz_benchmark_cases.json"


def load_tz_benchmark_cases(path: str | Path | None = None) -> list[dict[str, Any]]:
    """Load manually labeled TZ benchmark cases used as the product quality corpus."""
    fixture_path = Path(path) if path is not None else DEFAULT_TZ_BENCHMARK_CASES_PATH
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    raw_cases = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(raw_cases, list):
        raise ValueError("TZ benchmark fixture must contain a list of cases.")
    return [_normalize_case(case, index) for index, case in enumerate(raw_cases)]


def run_tz_benchmark_suite(cases: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Run the labeled TZ benchmark through the same fact/operator layers as product analysis."""
    raw_cases = load_tz_benchmark_cases() if cases is None else cases
    benchmark_cases = [_normalize_case(case, index) for index, case in enumerate(raw_cases)]
    scores = [
        score_tz_benchmark_case(case, _analysis_payload_for_case(case))
        for case in benchmark_cases
    ]
    return {
        "version": 1,
        "scores": scores,
        "summary": _suite_summary(scores),
    }


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

    matched_labels = _matched_text_values(expected_labels, found_labels)
    missed_labels = _missed_text_values(expected_labels, found_labels)
    false_positive_labels = _false_positive_text_values(
        found=found_labels,
        expected=expected_labels,
        absent=absent_labels,
        allowed_found=[*found_conflicts, *found_expected_missing],
    )
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


def _analysis_payload_for_case(case: dict[str, Any]) -> dict[str, Any]:
    documents = [
        {
            "name": f"{case['name']}-{index + 1}.txt",
            "document_type": "tz",
            "text_status": "ok",
            "text_content": text,
        }
        for index, text in enumerate(case["texts"])
    ]
    combined = analyze_tender_texts([document["text_content"] for document in documents]).to_dict()
    per_document = [
        analyze_tender_texts([document["text_content"]]).to_dict()
        for document in documents
    ]
    payload = {
        **combined,
        "requirements": _merge_unique(
            [*combined.get("requirements", []), *[item for result in per_document for item in result.get("requirements", [])]]
        ),
        "risks": _merge_unique([*combined.get("risks", []), *[item for result in per_document for item in result.get("risks", [])]]),
        "red_flags": _merge_unique(
            [*combined.get("red_flags", []), *[item for result in per_document for item in result.get("red_flags", [])]]
        ),
        "checklist": _merge_dict_items(
            [*combined.get("checklist", []), *[item for result in per_document for item in result.get("checklist", [])]],
            keys=("label", "evidence"),
        ),
        "execution_terms": _merge_dict_items(
            [
                *combined.get("execution_terms", []),
                *[item for result in per_document for item in result.get("execution_terms", [])],
            ],
            keys=("type", "value", "evidence"),
        ),
    }
    attach_document_sources(payload, documents)
    payload["analysis_facts"] = build_analysis_facts(payload, documents)
    payload["operator_view"] = build_analysis_operator_view(payload, documents)
    return payload


def _suite_summary(scores: list[dict[str, Any]]) -> dict[str, Any]:
    summary = summarize_tz_benchmark_scores(scores)
    case_count = int(summary["cases"])
    case_count_gap = max(0, TZ_BENCHMARK_TARGET_CASE_COUNT["min"] - case_count)
    category_scores = _category_scores(scores)
    fact_quality = _fact_quality(scores)
    required_categories_passed = not summary["missing_categories"]
    target_count_passed = (
        TZ_BENCHMARK_TARGET_CASE_COUNT["min"]
        <= case_count
        <= TZ_BENCHMARK_TARGET_CASE_COUNT["max"]
    )
    hallucination_passed = fact_quality["hallucinated"] == 0
    recall_passed = float(summary["average_recall"]) >= 0.85
    return {
        **summary,
        "case_count_gap": case_count_gap,
        "coverage_status": "target_reached" if target_count_passed and required_categories_passed else "needs_more_cases",
        "category_scores": category_scores,
        "fact_quality": fact_quality,
        "quality_gates": {
            "target_case_count": {
                "passed": target_count_passed,
                "actual": case_count,
                "target": dict(TZ_BENCHMARK_TARGET_CASE_COUNT),
            },
            "required_categories": {
                "passed": required_categories_passed,
                "missing": summary["missing_categories"],
            },
            "minimum_recall": {
                "passed": recall_passed,
                "actual": summary["average_recall"],
                "target": 0.85,
            },
            "no_hallucinated_labels": {
                "passed": hallucination_passed,
                "actual": fact_quality["hallucinated"],
                "target": 0,
            },
        },
    }


def _category_scores(scores: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for score in scores:
        grouped.setdefault(str(score.get("category") or "uncategorized"), []).append(score)
    return {
        category: {
            "cases": len(items),
            "average_recall": _average(score.get("recall") for score in items),
            "average_precision": _average(score.get("precision") for score in items),
            "missed": sum(_missed_count(score) for score in items),
            "hallucinated": sum(len(score.get("false_positive_labels") or []) for score in items),
            "conflicts_caught": sum(len(score.get("matched_conflicts") or []) for score in items),
            "conflicts_missed": sum(len(score.get("missed_conflicts") or []) for score in items),
        }
        for category, items in sorted(grouped.items())
    }


def _fact_quality(scores: list[dict[str, Any]]) -> dict[str, Any]:
    found = sum(_matched_count(score) for score in scores)
    missed = sum(_missed_count(score) for score in scores)
    hallucinated = sum(len(score.get("false_positive_labels") or []) for score in scores)
    return {
        "found": found,
        "missed": missed,
        "hallucinated": hallucinated,
        "conflicts_caught": sum(len(score.get("matched_conflicts") or []) for score in scores),
        "conflicts_missed": sum(len(score.get("missed_conflicts") or []) for score in scores),
        "expected_missing_caught": sum(len(score.get("matched_expected_missing") or []) for score in scores),
        "expected_missing_missed": sum(len(score.get("missed_expected_missing") or []) for score in scores),
        "missed_labels": _unique_score_values(scores, "missed_labels"),
        "missed_terms": _unique_score_values(scores, "missed_terms"),
        "hallucinated_labels": _unique_score_values(scores, "false_positive_labels"),
    }


def _matched_count(score: dict[str, Any]) -> int:
    return sum(
        len(score.get(key) or [])
        for key in (
            "matched_labels",
            "matched_terms",
            "matched_conflicts",
            "matched_expected_missing",
        )
    )


def _missed_count(score: dict[str, Any]) -> int:
    return sum(
        len(score.get(key) or [])
        for key in (
            "missed_labels",
            "missed_terms",
            "missed_conflicts",
            "missed_expected_missing",
        )
    )


def _unique_score_values(scores: list[dict[str, Any]], key: str) -> list[str]:
    values = {
        _text(value)
        for score in scores
        for value in score.get(key) or []
        if _text(value)
    }
    return _sorted(values)


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
        if item.get("kind") == "subject":
            continue
        label = _text(item.get("label"))
        if label:
            labels.add(label)
    for item in _operator_items(analysis):
        if item.get("expected_missing"):
            continue
        if item.get("kind") == "subject" or item.get("type") == "document_summary":
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


def _normalize_case(case: Any, index: int) -> dict[str, Any]:
    if not isinstance(case, dict):
        raise ValueError(f"TZ benchmark case #{index + 1} must be an object.")
    name = _text(case.get("name"))
    if not name:
        raise ValueError(f"TZ benchmark case #{index + 1} must have name.")
    category = _text(case.get("category"))
    if category not in REQUIRED_TZ_BENCHMARK_CATEGORIES:
        raise ValueError(f"TZ benchmark case {name!r} has unsupported category {category!r}.")
    texts = _text_list(case.get("texts"))
    if not texts:
        raise ValueError(f"TZ benchmark case {name!r} must have non-empty texts.")
    return {
        "name": name,
        "category": category,
        "texts": texts,
        "expected_labels": _text_list(case.get("expected_labels")),
        "expected_terms": _text_list(case.get("expected_terms")),
        "expected_conflicts": _text_list(case.get("expected_conflicts")),
        "expected_missing": _text_list(case.get("expected_missing")),
        "absent_labels": _text_list(case.get("absent_labels")),
    }


def _text_list(value: Any) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple, set)):
        return []
    return [_text(item) for item in value if _text(item)]


def _matched_text_values(expected: set[str], found: set[str]) -> list[str]:
    found_keys = {_text_key(value) for value in found}
    return _sorted({value for value in expected if _text_key(value) in found_keys})


def _missed_text_values(expected: set[str], found: set[str]) -> list[str]:
    found_keys = {_text_key(value) for value in found}
    return _sorted({value for value in expected if _text_key(value) not in found_keys})


def _false_positive_text_values(
    *,
    found: set[str],
    expected: set[str],
    absent: set[str],
    allowed_found: list[str],
) -> list[str]:
    expected_keys = {_text_key(value) for value in expected}
    absent_keys = {_text_key(value) for value in absent}
    allowed_keys = expected_keys | {_text_key(value) for value in allowed_found}
    return _sorted(
        {
            value
            for value in found
            if _text_key(value) in absent_keys or _text_key(value) not in allowed_keys
        }
    )


def _text_key(value: Any) -> str:
    normalized = _text(value).casefold().replace("ё", "е")
    normalized = re.sub(r"[^0-9a-zа-я]+", " ", normalized, flags=re.IGNORECASE)
    tokens = [token for token in normalized.split() if token not in {"и", "или"}]
    return " ".join(tokens)


def _merge_unique(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = _text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _merge_dict_items(values: list[Any], *, keys: tuple[str, ...]) -> list[dict[str, Any]]:
    seen: set[tuple[str, ...]] = set()
    result: list[dict[str, Any]] = []
    for value in values:
        if not isinstance(value, dict):
            continue
        marker = tuple(_text(value.get(key)) for key in keys)
        if not any(marker) or marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result


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
