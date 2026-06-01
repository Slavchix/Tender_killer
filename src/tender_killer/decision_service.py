from __future__ import annotations

from typing import Any


def build_tender_decision(tender: dict[str, Any]) -> dict[str, Any]:
    """Build one operator-facing decision from tender detail payload parts."""

    economics = _dict(tender.get("economics"))
    analysis = _dict(tender.get("analysis"))
    market_state = _dict(tender.get("market_state") or economics.get("market_state"))
    documents = _list_of_dicts(tender.get("document_records"))
    profiles = _list_of_dicts(tender.get("product_profiles"))
    participation = _dict(economics.get("participation_decision"))
    metrics = _decision_metrics(economics, market_state, documents, profiles)

    missing_costs = _text_list(economics.get("missing_cost_inputs"))
    red_flags = _text_list(analysis.get("red_flags"))
    risks = _text_list(analysis.get("risks"))
    requirements = _text_list(analysis.get("requirements"))
    operator_decision = _operator_decision(analysis)
    operator_blockers = _operator_section_labels(analysis, "blockers")
    passport_blockers = _passport_section_labels(analysis, "blockers")
    passport_price_factors = _passport_section_labels(analysis, "price_factors")
    analysis_blockers = _compact_reasons([*red_flags, *passport_blockers, *operator_blockers])
    operator_reasons = _operator_decision_reasons(operator_decision)
    passport_reasons = _compact_reasons([*passport_blockers, *passport_price_factors])
    economics_status = str(economics.get("status") or "")
    participation_status = str(participation.get("status") or "")

    if economics_status in {"needs_price", "needs_costs"} or participation_status in {"needs_price", "needs_costs"} or missing_costs:
        blockers = missing_costs or ["товарные позиции"]
        return _decision(
            status="missing_prices",
            label="Не хватает цен",
            tone="pending",
            summary="Нужно добавить закупочную себестоимость по позициям, чтобы принять решение по участию.",
            next_step="Добавить себестоимость",
            reasons=["Экономика не рассчитана без закупочных цен.", *_document_reasons(metrics)],
            blockers=blockers,
            limit_price=None,
            metrics=metrics,
        )

    if participation_status == "do_not_bid":
        return _decision(
            status="skip",
            label="Пропустить",
            tone="danger",
            summary=_text(participation.get("recommendation"), "Экономика указывает на убыточное участие."),
            next_step="Не участвовать",
            reasons=_compact_reasons([participation.get("recommendation"), *operator_reasons, *passport_reasons, *analysis_blockers, *risks]),
            blockers=_compact_reasons([participation.get("label"), *analysis_blockers]),
            limit_price=participation.get("limit_price"),
            metrics=metrics,
        )

    if analysis_blockers:
        return _decision(
            status="needs_review",
            label="Проверить ТЗ",
            tone="warning",
            summary=_text(
                operator_decision.get("summary"),
                "В документах есть условия, которые могут повлиять на возможность участия или цену.",
            ),
            next_step=_text(operator_decision.get("next_step"), "Проверить анализ"),
            reasons=_compact_reasons([*operator_reasons, *passport_reasons, *analysis_blockers, *risks, *requirements]),
            blockers=analysis_blockers,
            limit_price=participation.get("limit_price"),
            metrics=metrics,
        )

    if participation_status in {"guarded_bid", "low_margin"}:
        return _decision(
            status="with_limit",
            label=_text(participation.get("label"), "Только с лимитом"),
            tone="warning",
            summary=_text(participation.get("recommendation"), "Участвовать можно только с жестким ценовым лимитом."),
            next_step="Проверить лимит ставки",
            reasons=_compact_reasons([participation.get("recommendation"), *operator_reasons, *passport_reasons, *risks, *requirements]),
            blockers=risks,
            limit_price=participation.get("limit_price"),
            metrics=metrics,
        )

    if participation_status == "can_bid" and not risks:
        return _decision(
            status="interesting",
            label="Интересно",
            tone="success",
            summary=_text(participation.get("recommendation"), "Экономика выглядит пригодной для участия."),
            next_step="Проверить поставщика и документы",
            reasons=_compact_reasons([participation.get("recommendation"), *operator_reasons, *passport_reasons, *requirements]),
            blockers=[],
            limit_price=participation.get("limit_price"),
            metrics=metrics,
        )

    return _decision(
        status="needs_review",
        label="Нужна проверка",
        tone="warning",
        summary=_text(economics.get("recommendation"), "Нужно сверить экономику, документы и условия поставки."),
        next_step="Проверить карточку",
        reasons=_compact_reasons([economics.get("recommendation"), *operator_reasons, *passport_reasons, *risks, *requirements, *_document_reasons(metrics)]),
        blockers=risks,
        limit_price=participation.get("limit_price"),
        metrics=metrics,
    )


def _decision(
    *,
    status: str,
    label: str,
    tone: str,
    summary: str,
    next_step: str,
    reasons: list[str],
    blockers: list[str],
    limit_price: Any,
    metrics: dict[str, Any],
) -> dict[str, Any]:
    return {
        "status": status,
        "label": label,
        "tone": tone,
        "summary": summary,
        "next_step": next_step,
        "reasons": _compact_reasons(reasons)[:5],
        "blockers": _compact_reasons(blockers)[:5],
        "limit_price": limit_price,
        "metrics": metrics,
    }


def _decision_metrics(
    economics: dict[str, Any],
    market_state: dict[str, Any],
    documents: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
) -> dict[str, Any]:
    documents_ready = sum(1 for document in documents if document.get("text_status") == "ok")
    positions_priced = sum(
        1
        for profile in profiles
        if profile.get("profile_status") == "priced"
        or bool(_dict(profile.get("raw_payload")).get("economics"))
    )
    return {
        "nmc_price": _first_value(economics.get("nmc_price"), market_state.get("nmc_price")),
        "current_offer_price": _first_value(market_state.get("current_offer_price"), economics.get("revenue") if economics.get("revenue_kind") == "current_offer" else None),
        "bid_count": market_state.get("bid_count"),
        "participant_count": market_state.get("participant_count"),
        "margin_percent": economics.get("margin_percent"),
        "documents_ready": documents_ready,
        "documents_total": len(documents),
        "positions_total": len(profiles),
        "positions_priced": positions_priced,
    }


def _document_reasons(metrics: dict[str, Any]) -> list[str]:
    total = metrics.get("documents_total") or 0
    ready = metrics.get("documents_ready") or 0
    if total and ready < total:
        return [f"Текст документов извлечен не полностью: {ready} из {total}."]
    return []


def _operator_decision(analysis: dict[str, Any]) -> dict[str, Any]:
    operator_view = _dict(analysis.get("operator_view"))
    if operator_view.get("version") != 2:
        return {}
    return _dict(operator_view.get("decision_brief"))


def _operator_decision_reasons(decision: dict[str, Any]) -> list[str]:
    return _text_list(decision.get("reasons"))


def _operator_section_labels(analysis: dict[str, Any], section_id: str) -> list[str]:
    operator_view = _dict(analysis.get("operator_view"))
    if operator_view.get("version") != 2:
        return []
    sections = operator_view.get("sections")
    if not isinstance(sections, list):
        return []

    labels: list[str] = []
    for section in sections:
        if not isinstance(section, dict) or section.get("id") != section_id:
            continue
        items = section.get("items")
        if not isinstance(items, list):
            return []
        for item in items:
            if isinstance(item, dict):
                labels.append(_text(item.get("label"), ""))
            else:
                labels.append(_text(item, ""))
        return _compact_reasons(labels)
    return []


def _passport_section_labels(analysis: dict[str, Any], section_id: str) -> list[str]:
    passport = _dict(analysis.get("tz_passport"))
    if passport.get("version") != 1:
        return []
    sections = passport.get("sections")
    if not isinstance(sections, list):
        return []

    labels: list[str] = []
    for section in sections:
        if not isinstance(section, dict) or section.get("id") != section_id:
            continue
        items = section.get("items")
        if not isinstance(items, list):
            return []
        for item in items:
            if isinstance(item, dict):
                labels.append(_text(item.get("label"), ""))
            else:
                labels.append(_text(item, ""))
        return _compact_reasons(labels)
    return []


def _compact_reasons(values: list[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = _text(value, "").strip()
        if text and text not in result:
            result.append(text)
    return result


def _text_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return _compact_reasons(values)


def _list_of_dicts(values: Any) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, dict)]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _text(value: Any, fallback: str) -> str:
    if value in (None, ""):
        return fallback
    return str(value)


def _first_value(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None
