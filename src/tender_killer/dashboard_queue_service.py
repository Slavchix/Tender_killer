from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from tender_killer.normalization import parse_datetime
from tender_killer.normalization import parse_float
from tender_killer.tender_query_service import list_tenders_payload


MAX_DASHBOARD_QUEUE_ITEMS = 5000
PAGE_SIZE = 500


def build_dashboard_queues_payload(database_path: str | Path, query: dict[str, str]) -> dict[str, Any]:
    tenders, total = _load_dashboard_tenders(database_path, query)
    queues = [
        _decision_queue(
            "missing_prices",
            "Не хватает цен",
            "Закупки, где решение упирается в незаполненную себестоимость.",
            tenders,
            lambda tender: _decision_status(tender) == "missing_prices",
        ),
        _decision_queue(
            "needs_review",
            "Проверить ТЗ",
            "Есть условия из анализа документов, которые надо проверить до решения.",
            tenders,
            lambda tender: _decision_status(tender) == "needs_review",
        ),
        _decision_queue(
            "customer_review",
            "Проверить заказчика",
            "История заказчика, ЕИС-связка или повторные закупки требуют ручной проверки.",
            tenders,
            _customer_needs_review,
        ),
        _decision_queue(
            "with_limit",
            "Только с лимитом",
            "Экономика допускает участие только при жестком ценовом лимите.",
            tenders,
            lambda tender: _decision_status(tender) == "with_limit",
        ),
        _decision_queue(
            "interesting",
            "Интересно",
            "Расчет и анализ выглядят пригодными для участия.",
            tenders,
            lambda tender: _decision_status(tender) == "interesting",
        ),
        _decision_queue(
            "documents_review",
            "Документы",
            "Документы есть, но текст извлечен не полностью.",
            tenders,
            _documents_need_review,
        ),
        _decision_queue(
            "urgent_deadline",
            "Скоро дедлайн",
            "До окончания приема осталось меньше 24 часов.",
            tenders,
            _deadline_within_24_hours,
        ),
    ]
    return {
        "ok": True,
        "summary": {
            "total": total,
            "scanned": len(tenders),
            "decisions": sum(1 for tender in tenders if tender.get("decision")),
            "current_offers": sum(1 for tender in tenders if _has_current_offer(tender)),
            "customer_reviews": sum(1 for tender in tenders if _customer_needs_review(tender)),
            "no_participants": sum(
                1 for tender in tenders if tender.get("market_state", {}).get("status") == "no_participants"
            ),
        },
        "queues": queues,
    }


def _load_dashboard_tenders(database_path: str | Path, query: dict[str, str]) -> tuple[list[dict[str, Any]], int]:
    base_query = {
        key: value
        for key, value in dict(query or {}).items()
        if key not in {"limit", "offset"}
    }
    base_query.setdefault("status", "active")
    items: list[dict[str, Any]] = []
    total = 0
    offset = 0
    while len(items) < MAX_DASHBOARD_QUEUE_ITEMS:
        page = list_tenders_payload(
            database_path,
            {**base_query, "limit": str(PAGE_SIZE), "offset": str(offset)},
        )
        total = int(page.get("total") or total)
        page_items = page.get("items") or []
        items.extend(page_items)
        if not page.get("has_next") or not page_items:
            break
        offset = int(page.get("next_offset") or (offset + PAGE_SIZE))
    return items[:MAX_DASHBOARD_QUEUE_ITEMS], total


def _decision_queue(
    queue_id: str,
    label: str,
    description: str,
    tenders: list[dict[str, Any]],
    predicate: Any,
) -> dict[str, Any]:
    matches = [tender for tender in tenders if predicate(tender)]
    return {
        "id": queue_id,
        "label": label,
        "description": description,
        "count": len(matches),
        "items": [_queue_item(tender) for tender in matches[:5]],
    }


def _queue_item(tender: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": tender.get("source"),
        "external_id": tender.get("external_id"),
        "title": tender.get("title"),
        "customer": tender.get("customer"),
        "deadline_at": tender.get("deadline_at"),
        "price": tender.get("price"),
        "workflow_status": tender.get("workflow_status"),
        "market_state": tender.get("market_state"),
        "decision": tender.get("decision"),
        "eis_reference": tender.get("eis_reference"),
        "customer_risk_profile": tender.get("customer_risk_profile"),
    }


def _decision_status(tender: dict[str, Any]) -> str:
    decision = tender.get("decision")
    if not isinstance(decision, dict):
        return ""
    return str(decision.get("status") or "")


def _documents_need_review(tender: dict[str, Any]) -> bool:
    decision = tender.get("decision") or {}
    metrics = decision.get("metrics") if isinstance(decision, dict) else {}
    if not isinstance(metrics, dict):
        return False
    total = int(metrics.get("documents_total") or 0)
    ready = int(metrics.get("documents_ready") or 0)
    return total > 0 and ready < total


def _customer_needs_review(tender: dict[str, Any]) -> bool:
    profile = tender.get("customer_risk_profile")
    if not isinstance(profile, dict):
        return False
    if profile.get("level") == "high" or profile.get("status") == "needs_customer_identity":
        return True
    factors = profile.get("factors")
    if not isinstance(factors, list):
        return False
    important_ids = {
        "repeated_no_participants",
        "customer_complaints",
        "terminated_contracts",
        "payment_delay",
        "missing_customer_identity",
    }
    return any(isinstance(factor, dict) and factor.get("id") in important_ids for factor in factors)


def _deadline_within_24_hours(tender: dict[str, Any]) -> bool:
    deadline = parse_datetime(tender.get("deadline_at"))
    if deadline is None:
        return False
    if deadline.tzinfo is None:
        now = datetime.now()
    else:
        now = datetime.now(UTC).astimezone(deadline.tzinfo)
    return now <= deadline <= now + timedelta(hours=24)


def _has_current_offer(tender: dict[str, Any]) -> bool:
    market_state = tender.get("market_state")
    if not isinstance(market_state, dict):
        return False
    price = parse_float(market_state.get("current_offer_price"))
    return price is not None and price > 0
