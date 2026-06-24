from __future__ import annotations

from typing import Any

from tender_killer.supplier_provider_policy import supplier_auto_price_policy


def build_tender_decision(tender: dict[str, Any]) -> dict[str, Any]:
    """Build one operator-facing decision from tender detail payload parts."""

    economics = _dict(tender.get("economics"))
    analysis = _dict(tender.get("analysis"))
    market_state = _dict(tender.get("market_state") or economics.get("market_state"))
    documents = _list_of_dicts(tender.get("document_records"))
    profiles = _list_of_dicts(tender.get("product_profiles"))
    participation = _dict(economics.get("participation_decision"))
    customer_risk = _dict(tender.get("customer_risk_profile"))
    metrics = _decision_metrics(economics, market_state, documents, profiles)
    context = {
        "economics": economics,
        "analysis": analysis,
        "customer_risk": customer_risk,
        "metrics": metrics,
        "participation": participation,
        "operator_decision": _operator_decision(analysis),
    }

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
    customer_risk_reasons = _customer_risk_reasons(customer_risk)
    economics_status = str(economics.get("status") or "")
    participation_status = str(participation.get("status") or "")
    price_quality_reasons = _price_quality_reasons(economics)
    price_quality_blockers = _price_quality_blockers(economics)

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
            context=context,
        )

    if price_quality_reasons or price_quality_blockers:
        return _decision(
            status="needs_review",
            label="Проверить цены",
            tone="warning",
            summary="Цены есть, но перед расчетом заявки нужно проверить качество кандидатов.",
            next_step="Проверить кандидатов цен",
            reasons=_compact_reasons([*price_quality_reasons, participation.get("recommendation"), *_document_reasons(metrics)]),
            blockers=price_quality_blockers or price_quality_reasons,
            limit_price=participation.get("limit_price"),
            metrics=metrics,
            context=context,
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
            context=context,
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
            context=context,
        )

    if customer_risk.get("level") == "high":
        return _decision(
            status="needs_review",
            label="Проверить заказчика",
            tone="warning",
            summary="Профиль заказчика содержит риск-сигналы, которые нужно сверить перед участием.",
            next_step="Проверить историю заказчика в ЕИС",
            reasons=_compact_reasons([*customer_risk_reasons, *operator_reasons, *passport_reasons, *risks, *requirements]),
            blockers=customer_risk_reasons,
            limit_price=participation.get("limit_price"),
            metrics=metrics,
            context=context,
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
            context=context,
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
            context=context,
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
        context=context,
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
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    compact_reasons = _compact_reasons(reasons)[:5]
    compact_blockers = _compact_reasons(blockers)[:5]
    context_payload = context or {}
    return {
        "status": status,
        "label": label,
        "tone": tone,
        "summary": summary,
        "next_step": next_step,
        "reasons": compact_reasons,
        "blockers": compact_blockers,
        "limit_price": limit_price,
        "metrics": metrics,
        "economics_decision": _economics_decision_v2(
            status=status,
            reasons=compact_reasons,
            blockers=compact_blockers,
            limit_price=limit_price,
            metrics=metrics,
            context=context_payload,
        ),
        "reason_tree": _reason_tree(
            label=label,
            summary=summary,
            next_step=next_step,
            reasons=compact_reasons,
            blockers=compact_blockers,
            limit_price=limit_price,
            metrics=metrics,
            context=context_payload,
        ),
    }


def _economics_decision_v2(
    *,
    status: str,
    reasons: list[str],
    blockers: list[str],
    limit_price: Any,
    metrics: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    economics = _dict(context.get("economics"))
    analysis = _dict(context.get("analysis"))
    participation = _dict(context.get("participation"))
    customer_risk = _dict(context.get("customer_risk"))
    safe_bid = _safe_bid(economics, participation, limit_price)
    benchmark = _historical_benchmark(customer_risk, metrics)
    minimum_margin_percent = _first_number(
        economics.get("target_margin_percent"),
        _scenario_margin_percent(economics, "minimum_margin"),
    )
    current_margin_percent = _number(economics.get("margin_percent"))
    discount_buffer = _discount_buffer(metrics, economics, safe_bid)
    risks = _compact_reasons(
        [
            *_text_list(analysis.get("risks")),
            *_text_list(analysis.get("red_flags")),
            *blockers,
        ]
    )
    if benchmark.get("status") == "warning":
        risks.append("Historical benchmark differs from recent customer purchases.")
    compact_risks = _compact_reasons(risks)[:6]
    one_line_explanation = _economics_decision_one_line(
        status=status,
        safe_bid=safe_bid,
        current_margin_percent=current_margin_percent,
        minimum_margin_percent=minimum_margin_percent,
        discount_buffer=discount_buffer,
        blockers=blockers,
        risks=compact_risks,
        reasons=reasons,
    )

    return {
        "version": 2,
        "can_participate": _can_participate(status),
        "safe_bid": safe_bid,
        "minimum_margin_percent": minimum_margin_percent,
        "current_margin_percent": current_margin_percent,
        "discount_buffer": discount_buffer,
        "risks": compact_risks,
        "blockers": blockers,
        "what_blocks_application": blockers,
        "one_line_explanation": one_line_explanation,
        "final_decision_card": _final_decision_card(
            status=status,
            safe_bid=safe_bid,
            current_margin_percent=current_margin_percent,
            minimum_margin_percent=minimum_margin_percent,
            discount_buffer=discount_buffer,
            blockers=blockers,
            risks=compact_risks,
            reasons=reasons,
            one_line_explanation=one_line_explanation,
        ),
        "auto_price_policy": supplier_auto_price_policy(metrics.get("positions_total")),
        "historical_benchmark": benchmark,
        "basis": _compact_reasons([participation.get("recommendation"), *reasons])[:5],
    }


def _final_decision_card(
    *,
    status: str,
    safe_bid: dict[str, Any] | None,
    current_margin_percent: float | None,
    minimum_margin_percent: float | None,
    discount_buffer: dict[str, Any] | None,
    blockers: list[str],
    risks: list[str],
    reasons: list[str],
    one_line_explanation: str,
) -> dict[str, Any]:
    card_status = _final_decision_status(status)
    return {
        "status": card_status,
        "tone": _final_decision_tone(card_status),
        "headline": _final_decision_headline(card_status, safe_bid, one_line_explanation),
        "safe_bid": safe_bid,
        "margin_text": _margin_text(current_margin_percent, minimum_margin_percent),
        "buffer_text": _buffer_text(discount_buffer),
        "primary_reasons": _compact_reasons([*reasons, *risks, *blockers])[:3],
        "blockers": _compact_reasons(blockers)[:3],
        "next_action": _final_decision_next_action(card_status),
    }


def _final_decision_status(status: str) -> str:
    if status == "interesting":
        return "can_bid"
    if status == "with_limit":
        return "can_bid_with_limit"
    if status == "skip":
        return "do_not_bid"
    return "needs_review"


def _final_decision_tone(status: str) -> str:
    if status == "can_bid":
        return "success"
    if status == "can_bid_with_limit":
        return "warning"
    if status == "do_not_bid":
        return "danger"
    return "review"


def _final_decision_headline(status: str, safe_bid: dict[str, Any] | None, fallback: str) -> str:
    amount = _money(safe_bid.get("amount")) if safe_bid else ""
    if status == "can_bid":
        return f"Можно участвовать до {amount}" if amount else "Можно участвовать"
    if status == "can_bid_with_limit":
        return f"Можно участвовать до {amount}" if amount else "Можно участвовать с лимитом"
    if status == "do_not_bid":
        return "Не участвовать"
    return fallback or "Нужна проверка"


def _margin_text(current_margin_percent: float | None, minimum_margin_percent: float | None) -> str:
    parts = []
    if current_margin_percent is not None:
        parts.append(f"маржа {_format_percent(current_margin_percent)}")
    if minimum_margin_percent is not None:
        parts.append(f"минимум {_format_percent(minimum_margin_percent)}")
    return ", ".join(parts)


def _buffer_text(discount_buffer: dict[str, Any] | None) -> str:
    percent = _number(_dict(discount_buffer).get("percent"))
    if percent is None:
        return ""
    return f"запас снижения {_format_percent(percent)}"


def _final_decision_next_action(status: str) -> str:
    if status == "can_bid":
        return "Готовить заявку"
    if status == "can_bid_with_limit":
        return "Проверить лимит и условия перед заявкой"
    if status == "do_not_bid":
        return "Не готовить заявку"
    return "Проверить цены, условия и риски"


def _economics_decision_one_line(
    *,
    status: str,
    safe_bid: dict[str, Any] | None,
    current_margin_percent: float | None,
    minimum_margin_percent: float | None,
    discount_buffer: dict[str, Any] | None,
    blockers: list[str],
    risks: list[str],
    reasons: list[str],
) -> str:
    can_participate = _can_participate(status)
    if can_participate is True:
        limit = _money(safe_bid.get("amount")) if safe_bid else "уточненного лимита"
        details = []
        if current_margin_percent is not None:
            details.append(f"маржа {_format_percent(current_margin_percent)}")
        if minimum_margin_percent is not None:
            details.append(f"минимум {_format_percent(minimum_margin_percent)}")
        buffer_percent = _number(_dict(discount_buffer).get("percent"))
        if buffer_percent is not None:
            details.append(f"запас снижения {_format_percent(buffer_percent)}")
        return f"Можно участвовать до {limit}: {', '.join(details)}." if details else f"Можно участвовать до {limit}."
    if can_participate is False:
        return f"Не участвовать: {_first_reason(blockers, risks, reasons, fallback='экономика не проходит')}."
    return f"Нужна проверка: {_first_reason(blockers, risks, reasons, fallback='подтверди цены, условия и риски')}."


def _first_reason(*groups: list[str], fallback: str) -> str:
    for group in groups:
        for reason in group:
            text = _text(reason, "").strip()
            if text:
                return text
    return fallback


def _can_participate(status: str) -> bool | None:
    if status in {"interesting", "with_limit"}:
        return True
    if status == "skip":
        return False
    return None


def _safe_bid(
    economics: dict[str, Any],
    participation: dict[str, Any],
    limit_price: Any,
) -> dict[str, Any] | None:
    amount = _number(limit_price)
    if amount is None:
        amount = _first_number(
            participation.get("limit_price"),
            economics.get("stop_price"),
            economics.get("target_bid_price"),
            economics.get("minimum_margin_price"),
            economics.get("break_even_price"),
        )
    if amount is None:
        return None
    return {
        "amount": _round_money(amount),
        "source": _safe_bid_source(economics, participation, amount),
    }


def _safe_bid_source(economics: dict[str, Any], participation: dict[str, Any], amount: float) -> str:
    for source in ("stop_price", "target_bid_price", "minimum_margin_price", "break_even_price"):
        if _same_money(amount, economics.get(source)):
            return source
    if _same_money(amount, participation.get("limit_price")):
        return "participation_decision.limit_price"
    return "manual_limit"


def _discount_buffer(
    metrics: dict[str, Any],
    economics: dict[str, Any],
    safe_bid: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not safe_bid:
        return None
    basis_label, basis_amount = _buffer_basis(metrics, economics)
    safe_amount = _number(safe_bid.get("amount"))
    if basis_amount is None or basis_amount <= 0 or safe_amount is None:
        return None
    amount = _round_money(basis_amount - safe_amount)
    return {
        "amount": amount,
        "percent": _round_percent((amount / basis_amount) * 100),
        "basis": basis_label,
    }


def _buffer_basis(metrics: dict[str, Any], economics: dict[str, Any]) -> tuple[str, float | None]:
    current_offer = _number(metrics.get("current_offer_price"))
    if current_offer is not None:
        return "current_offer_price", current_offer
    revenue = _number(economics.get("revenue"))
    if revenue is not None:
        return "revenue", revenue
    return "nmc_price", _number(metrics.get("nmc_price"))


def _historical_benchmark(
    customer_risk: dict[str, Any],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    history = _dict(customer_risk.get("history"))
    recent = _list_of_dicts(history.get("recent"))
    prices = sorted(
        price
        for price in (_number(item.get("price")) for item in recent)
        if price is not None
    )
    if not prices:
        return {
            "status": "no_history",
            "sample_size": 0,
            "note": "Historical benchmark is a control signal only; landed cost remains the decision basis.",
        }

    typical_price = _median(prices)
    current_price = _first_number(metrics.get("current_offer_price"), metrics.get("nmc_price"))
    no_participant_count = sum(
        1
        for item in recent
        if _dict(item.get("market_state")).get("status") == "no_participants"
    )
    if current_price is None or typical_price <= 0:
        delta_percent = None
        status = "info"
    else:
        delta_percent = _round_percent(((current_price - typical_price) / typical_price) * 100)
        status = "warning" if abs(delta_percent) >= 25 else "ok"

    return {
        "status": status,
        "sample_size": len(prices),
        "typical_price": _round_money(typical_price),
        "current_price": _round_money(current_price) if current_price is not None else None,
        "delta_percent": delta_percent,
        "no_participant_count": no_participant_count,
        "note": "Historical benchmark is a control signal only; landed cost remains the decision basis.",
    }


def _scenario_margin_percent(economics: dict[str, Any], scenario_id: str) -> float | None:
    for scenario in _list_of_dicts(economics.get("bid_scenarios")):
        if scenario.get("id") == scenario_id:
            return _number(scenario.get("margin_percent"))
    return None


def _reason_tree(
    *,
    label: str,
    summary: str,
    next_step: str,
    reasons: list[str],
    blockers: list[str],
    limit_price: Any,
    metrics: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    economics = _dict(context.get("economics"))
    analysis = _dict(context.get("analysis"))
    participation = _dict(context.get("participation"))
    operator_decision = _dict(context.get("operator_decision"))
    positive = _positive_decision_reasons(economics, metrics, participation)
    negative = _compact_reasons([*blockers, *_text_list(analysis.get("risks")), *_text_list(analysis.get("requirements"))])[:6]
    actions = _decision_actions(
        next_step=next_step,
        operator_next_step=_text(operator_decision.get("next_step"), ""),
        limit_price=limit_price,
        metrics=metrics,
    )
    return {
        "title": label,
        "summary": summary,
        "positive": positive[:5],
        "negative": negative[:6],
        "context": [reason for reason in reasons if reason not in positive and reason not in negative][:5],
        "actions": actions[:5],
    }


def _positive_decision_reasons(
    economics: dict[str, Any],
    metrics: dict[str, Any],
    participation: dict[str, Any],
) -> list[str]:
    reasons: list[Any] = []
    margin = _number(economics.get("margin_percent"))
    if margin is not None:
        reasons.append(f"Маржа после расходов: {_format_percent(margin)}")
    positions_total = _int_or_none(metrics.get("positions_total"))
    positions_priced = _int_or_none(metrics.get("positions_priced"))
    if positions_total:
        reasons.append(f"Товарные позиции с ценами: {positions_priced or 0}/{positions_total}")
    bid_count = _int_or_none(metrics.get("bid_count"))
    if bid_count is not None:
        reasons.append(f"Ставок участников: {bid_count}")
    recommendation = _text(participation.get("recommendation"), "")
    if recommendation:
        reasons.append(recommendation)
    return _compact_reasons(reasons)


def _decision_actions(
    *,
    next_step: str,
    operator_next_step: str,
    limit_price: Any,
    metrics: dict[str, Any],
) -> list[str]:
    actions = _compact_reasons([operator_next_step, next_step])
    if limit_price not in (None, ""):
        actions.append(f"Не падать ниже {_money(limit_price)}")
    total = _int_or_none(metrics.get("documents_total")) or 0
    ready = _int_or_none(metrics.get("documents_ready")) or 0
    if total and ready < total:
        actions.append(f"Дочитать документы: {ready}/{total}")
    return _compact_reasons(actions)


def _decision_metrics(
    economics: dict[str, Any],
    market_state: dict[str, Any],
    documents: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
) -> dict[str, Any]:
    documents_ready = sum(1 for document in documents if document.get("text_status") == "ok")
    price_quality = _dict(economics.get("price_quality"))
    fallback_positions_priced = sum(
        1
        for profile in profiles
        if profile.get("profile_status") == "priced"
        or bool(_dict(profile.get("raw_payload")).get("economics"))
    )
    positions_total = _first_value(price_quality.get("positions_total"), len(profiles))
    positions_priced = _first_value(price_quality.get("positions_priced"), fallback_positions_priced)
    return {
        "nmc_price": _first_value(economics.get("nmc_price"), market_state.get("nmc_price")),
        "current_offer_price": _first_value(market_state.get("current_offer_price"), economics.get("revenue") if economics.get("revenue_kind") == "current_offer" else None),
        "bid_count": market_state.get("bid_count"),
        "participant_count": market_state.get("participant_count"),
        "margin_percent": economics.get("margin_percent"),
        "documents_ready": documents_ready,
        "documents_total": len(documents),
        "positions_total": positions_total,
        "positions_priced": positions_priced,
        "price_candidates_total": _first_value(price_quality.get("candidates_total"), 0),
        "price_candidates_ready": _first_value(price_quality.get("candidates_ready"), 0),
        "price_candidates_review": _first_value(price_quality.get("candidates_review"), 0),
        "price_candidates_blocked": _first_value(price_quality.get("candidates_blocked"), 0),
    }


def _price_quality_reasons(economics: dict[str, Any]) -> list[str]:
    quality = _dict(economics.get("price_quality"))
    review_count = _int_or_none(quality.get("candidates_review")) or 0
    blocked_count = _int_or_none(quality.get("candidates_blocked")) or 0
    if review_count <= 0 and blocked_count <= 0:
        return []
    reasons = _compact_reasons([
        *_price_quality_flag_labels(quality, "review_flags"),
        *_price_quality_flag_labels(quality, "block_flags"),
    ])
    if reasons:
        return reasons
    if blocked_count > 0:
        return ["Есть заблокированные кандидаты цен"]
    return ["Есть кандидаты цен на проверку"]


def _price_quality_blockers(economics: dict[str, Any]) -> list[str]:
    quality = _dict(economics.get("price_quality"))
    blocked_count = _int_or_none(quality.get("candidates_blocked")) or 0
    review_count = _int_or_none(quality.get("candidates_review")) or 0
    if blocked_count <= 0 and review_count <= 0:
        return []
    if blocked_count <= 0:
        return _price_quality_flag_labels(quality, "review_flags") or ["Есть кандидаты цен на проверку"]
    return _price_quality_flag_labels(quality, "block_flags") or ["Есть заблокированные кандидаты цен"]


def _price_quality_flag_labels(quality: dict[str, Any], key: str) -> list[str]:
    labels: list[Any] = []
    for flag in _list_of_dicts(quality.get(key)):
        labels.append(flag.get("label") or flag.get("id"))
    return _compact_reasons(labels)


def _document_reasons(metrics: dict[str, Any]) -> list[str]:
    total = metrics.get("documents_total") or 0
    ready = metrics.get("documents_ready") or 0
    if total and ready < total:
        return [f"Текст документов извлечен не полностью: {ready} из {total}."]
    return []


def _operator_decision(analysis: dict[str, Any]) -> dict[str, Any]:
    operator_view = _dict(analysis.get("operator_view"))
    if operator_view.get("version") not in {2, 3}:
        return {}
    return _dict(operator_view.get("decision_brief"))


def _operator_decision_reasons(decision: dict[str, Any]) -> list[str]:
    return _text_list(decision.get("reasons"))


def _operator_section_labels(analysis: dict[str, Any], section_id: str) -> list[str]:
    operator_view = _dict(analysis.get("operator_view"))
    if operator_view.get("version") not in {2, 3}:
        return []
    sections = operator_view.get("sections")
    if not isinstance(sections, list):
        return []

    target_ids = {section_id}
    if section_id == "blockers":
        target_ids.add("decision_risks")

    labels: list[str] = []
    for section in sections:
        if not isinstance(section, dict) or section.get("id") not in target_ids:
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


def _customer_risk_reasons(customer_risk: dict[str, Any]) -> list[str]:
    if not customer_risk:
        return []
    factors = customer_risk.get("factors")
    reasons: list[Any] = []
    if isinstance(factors, list):
        for factor in factors:
            if not isinstance(factor, dict):
                continue
            if str(factor.get("severity") or "") not in {"high", "medium"}:
                continue
            reasons.append(factor.get("evidence") or factor.get("id"))
    if not reasons and customer_risk.get("level") == "high":
        reasons.append("Высокий риск-профиль заказчика.")
    return _compact_reasons(reasons)


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


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_number(*values: Any) -> float | None:
    for value in values:
        number = _number(value)
        if number is not None:
            return number
    return None


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _round_money(value: float) -> float:
    return round(float(value), 2)


def _round_percent(value: float) -> float:
    return round(float(value), 2)


def _same_money(left: Any, right: Any) -> bool:
    left_number = _number(left)
    right_number = _number(right)
    if left_number is None or right_number is None:
        return False
    return _round_money(left_number) == _round_money(right_number)


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    middle = len(values) // 2
    if len(values) % 2:
        return values[middle]
    return (values[middle - 1] + values[middle]) / 2


def _format_percent(value: float) -> str:
    return f"{value:.0f}%" if value.is_integer() else f"{value:.2f}%"


def _money(value: Any) -> str:
    number = _number(value)
    if number is None:
        return "не указано"
    return f"{number:,.2f} ₽".replace(",", " ")


def _first_value(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None
