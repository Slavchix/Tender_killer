from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tender_killer.analysis_operator_view_service import build_analysis_operator_view
from tender_killer.decision_service import build_tender_decision
from tender_killer.economics import build_economics_summary
from tender_killer.filter_store import FilterProfileCollection, NamedFilterProfile
from tender_killer.filters import FilterProfile
from tender_killer.market_state import extract_market_state
from tender_killer.quick_search import expand_quick_search_exclude_keywords
from tender_killer.quick_search import expand_quick_search_keywords
from tender_killer.schema import ensure_analysis_table
from tender_killer.schema import ensure_documents_table
from tender_killer.schema import ensure_items_table
from tender_killer.schema import ensure_workflow_table
from tender_killer.sources import normalize_sources
from tender_killer.storage import TenderStore


@dataclass(frozen=True)
class TenderListQuery:
    sql: str
    count_sql: str
    params: list[Any]
    limit: int
    offset: int


def list_tenders_payload(database_path: str | Path, query: dict[str, str]) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    tender_query = build_tender_list_query(query)
    with _connect(database_path) as connection:
        ensure_workflow_table(connection)
        ensure_items_table(connection)
        ensure_documents_table(connection)
        ensure_analysis_table(connection)
        total_row = connection.execute(tender_query.count_sql, tender_query.params).fetchone()
        rows = connection.execute(
            tender_query.sql,
            [*tender_query.params, tender_query.limit, tender_query.offset],
        ).fetchall()
    total = int(total_row[0]) if total_row else 0
    has_previous = tender_query.offset > 0
    next_offset = tender_query.offset + tender_query.limit
    has_next = next_offset < total
    items = [_row_to_list_item(row, database_path) for row in rows]
    return {
        "total": total,
        "limit": tender_query.limit,
        "offset": tender_query.offset,
        "has_previous": has_previous,
        "previous_offset": max(0, tender_query.offset - tender_query.limit) if has_previous else None,
        "has_next": has_next,
        "next_offset": next_offset if has_next else None,
        "items": items,
    }


def build_tender_list_query(query: dict[str, str]) -> TenderListQuery:
    filters, params = _build_filters(query)
    from_sql = (
        "FROM tenders "
        "LEFT JOIN tender_workflow AS workflow "
        "ON tenders.source = workflow.source AND tenders.external_id = workflow.external_id "
        "LEFT JOIN tender_analysis AS analysis "
        "ON tenders.source = analysis.source AND tenders.external_id = analysis.external_id"
    )
    where_sql = f" WHERE {' AND '.join(filters)}" if filters else ""
    select_sql = (
        "SELECT tenders.source, tenders.external_id, url, title, customer, region, price, currency, status, "
        "status_normalized, law, region_code, source_family, procedure_type, customer_inn, "
        "published_at, deadline_at, delivery_place, category, okpd2, "
        "documents_json, tenders.raw_payload_json AS raw_payload_json, "
        "tenders.updated_at, COALESCE(workflow.workflow_status, 'new') AS workflow_status, "
        "COALESCE(workflow.workflow_note, '') AS workflow_note, "
        "analysis.summary AS analysis_summary, "
        "analysis.requirements_json AS analysis_requirements_json, "
        "analysis.risks_json AS analysis_risks_json, "
        "analysis.red_flags_json AS analysis_red_flags_json, "
        "analysis.recommended_status AS analysis_recommended_status, "
        "analysis.confidence AS analysis_confidence, "
        "analysis.raw_payload_json AS analysis_raw_payload_json, "
        "analysis.analyzed_at AS analysis_analyzed_at, "
        "(SELECT COUNT(*) FROM tender_items AS item_count "
        "WHERE item_count.source = tenders.source AND item_count.external_id = tenders.external_id) AS items_count "
    )
    limit = max(1, min(_int_query(query.get("limit"), 100), 500))
    offset = max(0, _int_query(query.get("offset"), 0))
    sql = (
        select_sql
        + from_sql
        + where_sql
        + " ORDER BY COALESCE(tenders.deadline_at, tenders.published_at, tenders.updated_at) DESC, "
        "tenders.source, tenders.external_id LIMIT ? OFFSET ?"
    )
    count_sql = "SELECT COUNT(*) " + from_sql + where_sql
    return TenderListQuery(sql=sql, count_sql=count_sql, params=params, limit=limit, offset=offset)


def build_search_collection(payload: dict[str, Any] | None) -> FilterProfileCollection:
    data = payload.get("filters", payload) if isinstance(payload, dict) else {}
    data = data if isinstance(data, dict) else {}
    status = str(data.get("status") or "").strip()
    only_active = not status or _is_active_status_query(status)
    statuses = () if only_active else _multi_value_tuple(status)
    keywords = _keywords_from_query(str(data.get("q") or ""))
    exclude_keywords = _exclude_keywords_from_query(str(data.get("q") or ""))
    profile = FilterProfile(
        keywords=keywords or FilterProfile.DEFAULT_KEYWORDS,
        exclude_keywords=exclude_keywords,
        regions=_region_values(data.get("region")),
        sources=normalize_sources(_multi_value_tuple(data.get("source"))),
        laws=_multi_value_tuple(data.get("law")),
        statuses=statuses,
        okpd2=_multi_value_tuple(data.get("okpd2")),
        min_price=_float_query(data.get("min_price")),
        max_price=_float_query(data.get("max_price")),
        only_active=only_active,
        include_without_price=True,
        include_without_deadline=True,
    )
    return FilterProfileCollection(
        profiles=(NamedFilterProfile(id="site", name="Site", profile=profile),),
        active_profile_ids=("site",),
    )


def _build_filters(query: dict[str, str]) -> tuple[list[str], list[Any]]:
    filters: list[str] = []
    params: list[Any] = []

    if source_values := _source_query_values(query.get("source")):
        filters.append(_in_clause("tenders.source", source_values))
        params.extend(source_values)
    if source_family_values := _lower_value_tuple(query.get("source_family")):
        filters.append(_in_clause("tenders.source_family", source_family_values))
        params.extend(source_family_values)
    if procedure_values := _lower_value_tuple(query.get("procedure_type")):
        filters.append(_in_clause("tenders.procedure_type", procedure_values))
        params.extend(procedure_values)
    if customer_inn_values := _digit_value_tuple(query.get("customer_inn")):
        filters.append(_in_clause("tenders.customer_inn", customer_inn_values))
        params.extend(customer_inn_values)
    if region_values := _region_values(query.get("region")):
        region_filters, region_params = _text_like_any("tenders.region", region_values)
        region_codes = _region_code_query_values(query.get("region"))
        if region_codes:
            filters.append(f"({region_filters} OR {_in_clause('tenders.region_code', region_codes)})")
            region_params.extend(region_codes)
        else:
            filters.append(region_filters)
        params.extend(region_params)
    if status := query.get("status"):
        if _is_active_status_query(status):
            filters.append(
                "("
                + " OR ".join(
                    [
                        "COALESCE(tenders.status_normalized, '') = ?",
                        "COALESCE(tenders.status, '') LIKE ?",
                        "COALESCE(tenders.status, '') LIKE ?",
                        "COALESCE(tenders.status, '') LIKE ?",
                        "COALESCE(tenders.status, '') LIKE ?",
                    ]
                )
                + ")"
            )
            params.extend(["active", "%Актив%", "%актив%", "%Прием%", "%Приём%"])
            filters.append(_active_deadline_filter())
        else:
            status_filters, status_params = _text_like_any("tenders.status", status)
            filters.append(status_filters)
            params.extend(status_params)
    if okpd2_values := _multi_value_tuple(query.get("okpd2")):
        filters.append(
            "("
            + " OR ".join(
                [
                    "COALESCE(tenders.okpd2, '') LIKE ?",
                    (
                        "EXISTS (SELECT 1 FROM tender_items AS okpd_item "
                        "WHERE okpd_item.source = tenders.source "
                        "AND okpd_item.external_id = tenders.external_id "
                        "AND COALESCE(okpd_item.okpd2, '') LIKE ?)"
                    ),
                ]
                * len(okpd2_values)
            )
            + ")"
        )
        for okpd2 in okpd2_values:
            params.extend([f"{okpd2}%", f"{okpd2}%"])
    if law_values := _law_query_values(query.get("law")):
        filters.append(
            "("
            + " OR ".join(
                ["LOWER(COALESCE(tenders.law, '')) = ? OR LOWER(COALESCE(tenders.raw_payload_json, '')) LIKE ?"]
                * len(law_values)
            )
            + ")"
        )
        for law in law_values:
            params.extend([law, f"%{law}%"])
    if min_price := _float_query(query.get("min_price")):
        filters.append("tenders.price >= ?")
        params.append(min_price)
    if max_price := _float_query(query.get("max_price")):
        filters.append("tenders.price <= ?")
        params.append(max_price)
    if search := query.get("q"):
        search_terms = _keywords_from_query(search)
        exclude_terms = _exclude_keywords_from_query(search)
        filters.append(
            "("
            + " OR ".join(
                [
                    "LOWER(tenders.title) LIKE ?",
                    "LOWER(COALESCE(tenders.customer, '')) LIKE ?",
                    "LOWER(COALESCE(tenders.category, '')) LIKE ?",
                    "LOWER(COALESCE(tenders.delivery_place, '')) LIKE ?",
                ]
                * len(search_terms)
            )
            + ")"
        )
        for term in search_terms:
            needle = f"%{term.lower()}%"
            params.extend([needle, needle, needle, needle])
        if exclude_terms:
            filters.append(
                "NOT ("
                + " OR ".join(
                    [
                        "LOWER(tenders.title) LIKE ?",
                        "LOWER(COALESCE(tenders.customer, '')) LIKE ?",
                        "LOWER(COALESCE(tenders.category, '')) LIKE ?",
                        "LOWER(COALESCE(tenders.delivery_place, '')) LIKE ?",
                    ]
                    * len(exclude_terms)
                )
                + ")"
            )
            for term in exclude_terms:
                needle = f"%{term.lower()}%"
                params.extend([needle, needle, needle, needle])
    if workflow_status := query.get("workflow_status"):
        filters.append("COALESCE(workflow.workflow_status, 'new') = ?")
        params.append(workflow_status)
    return filters, params


def _keywords_from_query(value: str) -> tuple[str, ...]:
    parts = re.split(r"[,;\n]+", value)
    keywords: list[str] = []
    for part in (part.strip() for part in parts):
        if not part:
            continue
        for keyword in expand_quick_search_keywords(part):
            if keyword not in keywords:
                keywords.append(keyword)
    return tuple(keywords)


def _exclude_keywords_from_query(value: str) -> tuple[str, ...]:
    parts = re.split(r"[,;\n]+", value)
    keywords: list[str] = []
    for part in (part.strip() for part in parts):
        if not part:
            continue
        for keyword in expand_quick_search_exclude_keywords(part):
            if keyword not in keywords:
                keywords.append(keyword)
    return tuple(keywords)


def _multi_value_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple, set)):
        candidates = [str(item) for item in value]
    else:
        candidates = re.split(r"[,;\n]+", str(value or ""))
    return tuple(part.strip() for part in candidates if part and part.strip())


def _lower_value_tuple(value: Any) -> tuple[str, ...]:
    return tuple(item.casefold() for item in _multi_value_tuple(value))


def _digit_value_tuple(value: Any) -> tuple[str, ...]:
    values: list[str] = []
    for item in _multi_value_tuple(value):
        digits = re.sub(r"\D+", "", item)
        if digits and digits not in values:
            values.append(digits)
    return tuple(values)


def _region_values(value: Any) -> tuple[str, ...]:
    regions: list[str] = []
    for region in _multi_value_tuple(value):
        normalized = region.casefold().replace("\u0451", "\u0435")
        if normalized in {
            "\u043c\u043e\u0441\u043a\u0432\u0430 + \u043c\u043e",
            "\u043c\u043e\u0441\u043a\u0432\u0430 \u0438 \u043c\u043e",
            "\u043c\u043e\u0441\u043a\u0432\u0430, \u043c\u043e",
            "\u043c\u0441\u043a + \u043c\u043e",
        }:
            candidates = (
                "\u041c\u043e\u0441\u043a\u0432\u0430",
                "\u041c\u043e\u0441\u043a\u043e\u0432\u0441\u043a\u0430\u044f \u043e\u0431\u043b\u0430\u0441\u0442\u044c",
            )
        else:
            candidates = (region,)
        for candidate in candidates:
            if candidate not in regions:
                regions.append(candidate)
    return tuple(regions)


def _region_code_query_values(value: Any) -> tuple[str, ...]:
    codes: list[str] = []
    for region in _multi_value_tuple(value):
        normalized = region.casefold().replace("\u0451", "\u0435")
        if normalized in {
            "mo",
            "mosreg",
            "moscow oblast",
            "\u043c\u043e\u0441\u043a\u043e\u0432\u0441\u043a\u0430\u044f \u043e\u0431\u043b\u0430\u0441\u0442\u044c",
            "\u043c\u043e\u0441\u043a\u0432\u0430 + \u043c\u043e",
            "\u043c\u043e\u0441\u043a\u0432\u0430 \u0438 \u043c\u043e",
        }:
            candidates = ("50",)
            if "\u043c\u043e\u0441\u043a\u0432\u0430" in normalized:
                candidates = ("77", "50")
        elif normalized in {"moscow", "msk", "\u043c\u043e\u0441\u043a\u0432\u0430"}:
            candidates = ("77",)
        else:
            candidates = ()
        for candidate in candidates:
            if candidate not in codes:
                codes.append(candidate)
    return tuple(codes)


def _source_query_values(value: Any) -> tuple[str, ...]:
    source_map = {
        "moscow": "moscow_supplier_portal",
        "moscow_supplier_portal": "moscow_supplier_portal",
        "mosreg": "mosreg_market",
        "mo": "mosreg_market",
        "mosreg_market": "mosreg_market",
    }
    sources: list[str] = []
    for source in _multi_value_tuple(value):
        normalized = source.strip().casefold()
        mapped = source_map.get(normalized, source)
        if mapped not in sources:
            sources.append(mapped)
    return tuple(sources)


def _in_clause(field: str, values: tuple[str, ...]) -> str:
    placeholders = ", ".join(["?"] * len(values))
    return f"{field} IN ({placeholders})"


def _is_active_status_query(value: str) -> bool:
    normalized = value.strip().casefold().replace("\u0451", "\u0435")
    return normalized in {
        "active",
        "\u0430\u043a\u0442\u0438\u0432",
        "\u0430\u043a\u0442\u0438\u0432\u043d\u044b\u0435",
        "\u043f\u0440\u0438\u0435\u043c",
        "\u043f\u0440\u0438\u0435\u043c \u0437\u0430\u044f\u0432\u043e\u043a",
        "\u043f\u0440\u0438\u0435\u043c \u043f\u0440\u0435\u0434\u043b\u043e\u0436\u0435\u043d\u0438\u0439",
    }


def _text_like_any(field: str, values: str | tuple[str, ...]) -> tuple[str, list[Any]]:
    variants = _text_variants(values)
    clause = "(" + " OR ".join([f"COALESCE({field}, '') LIKE ?" for _ in variants]) + ")"
    return clause, [f"%{variant}%" for variant in variants]


def _text_variants(values: str | tuple[str, ...]) -> tuple[str, ...]:
    variants = []
    for value in (values if isinstance(values, tuple) else (values,)):
        text = value.strip()
        if not text:
            continue
        for candidate in (text, text.casefold(), text.upper(), text[:1].upper() + text[1:].casefold()):
            if candidate and candidate not in variants:
                variants.append(candidate)
    if not variants:
        return ("",)
    return tuple(variants)


def _active_deadline_filter() -> str:
    return """
        (
            tenders.deadline_at IS NULL
            OR (
                (
                    tenders.deadline_at LIKE '%+__:__'
                    OR tenders.deadline_at LIKE '%-__:__'
                    OR tenders.deadline_at LIKE '%Z'
                )
                AND datetime(tenders.deadline_at) >= datetime('now')
            )
            OR (
                tenders.deadline_at NOT LIKE '%+__:__'
                AND tenders.deadline_at NOT LIKE '%-__:__'
                AND tenders.deadline_at NOT LIKE '%Z'
                AND datetime(tenders.deadline_at) >= datetime('now', 'localtime')
            )
        )
    """


def _row_to_list_item(row: sqlite3.Row, database_path: str | Path) -> dict[str, Any]:
    payload = dict(row)
    documents = _json_list(payload.pop("documents_json"))
    raw_payload_json = payload.pop("raw_payload_json", None)
    analysis = _analysis_from_list_row(payload)
    payload["documents_count"] = len(documents)
    payload["market_state"] = extract_market_state({**payload, "raw_payload_json": raw_payload_json})
    payload["law"] = payload.get("law") or _law_label(raw_payload_json)
    profiles = TenderStore(database_path).get_product_profiles(payload["source"], payload["external_id"])
    payload["economics"] = (
        build_economics_summary(
            {
                **payload,
                "raw_payload_json": raw_payload_json,
                "product_profiles": profiles,
                "analysis": analysis,
            }
        )
        if profiles
        else None
    )
    payload["analysis"] = analysis
    payload["decision"] = (
        build_tender_decision(
            {
                **payload,
                "analysis": analysis,
                "document_records": [],
                "product_profiles": profiles,
            }
        )
        if analysis or payload["economics"]
        else None
    )
    return payload


def _analysis_from_list_row(payload: dict[str, Any]) -> dict[str, Any] | None:
    summary = payload.pop("analysis_summary", None)
    requirements_json = payload.pop("analysis_requirements_json", None)
    risks_json = payload.pop("analysis_risks_json", None)
    red_flags_json = payload.pop("analysis_red_flags_json", None)
    status = payload.pop("analysis_recommended_status", None)
    confidence = payload.pop("analysis_confidence", None)
    raw_payload = _json_object(payload.pop("analysis_raw_payload_json", None))
    analyzed_at = payload.pop("analysis_analyzed_at", None)

    if summary is None and status is None and not raw_payload:
        return None

    analysis = {
        "summary": summary or "",
        "requirements": _json_list(requirements_json),
        "risks": _json_list(risks_json),
        "red_flags": _json_list(red_flags_json),
        "status": status or "",
        "confidence": confidence,
        "raw_payload": raw_payload,
        "checklist": raw_payload.get("checklist", []),
        "analyzed_at": analyzed_at,
    }
    evidence_items = raw_payload.get("evidence_items")
    analysis["evidence_items"] = evidence_items if isinstance(evidence_items, list) else []
    operator_view = raw_payload.get("operator_view")
    analysis["operator_view"] = (
        operator_view if isinstance(operator_view, dict) and operator_view.get("version") == 2
        else build_analysis_operator_view(analysis, [])
    )
    return analysis


def _json_list(value: str | None) -> list[Any]:
    if not value:
        return []
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _json_object(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _connect(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def _int_query(value: str | None, default: int) -> int:
    try:
        return int(value) if value else default
    except ValueError:
        return default


def _float_query(value: Any) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


def _law_query_values(value: Any) -> tuple[str, ...]:
    laws: list[str] = []
    for law in _multi_value_tuple(value):
        digits = re.sub(r"\D+", "", law)
        if "223" in digits:
            normalized = "223"
        elif "44" in digits:
            normalized = "44"
        else:
            normalized = law.lower()
        if normalized not in laws:
            laws.append(normalized)
    return tuple(laws)


def _law_label(raw_payload_json: str | None) -> str | None:
    if not raw_payload_json:
        return None
    digits = re.sub(r"\D+", "", raw_payload_json)
    if "223" in digits:
        return "223-\u0424\u0417"
    if "44" in digits:
        return "44-\u0424\u0417"
    return None
