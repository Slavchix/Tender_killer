from __future__ import annotations

import re
from typing import Any

from tender_killer.analysis_condition_groups_service import condition_source_hierarchy_score
from tender_killer.analysis_condition_groups_service import normalized_condition_family
from tender_killer.analysis_condition_groups_service import semantic_family
from tender_killer.analysis_interpretation_service import build_fact_interpretation
from tender_killer.analysis_operator_evidence_service import build_operator_confidence_level as _operator_confidence_level
from tender_killer.analysis_operator_evidence_service import build_operator_evidence_quality as _operator_evidence_quality
from tender_killer.analysis_operator_evidence_service import build_operator_source_binding as _operator_source_binding
from tender_killer.analysis_operator_evidence_service import operator_evidence_summary as _operator_evidence_summary
from tender_killer.analysis_operator_evidence_service import operator_evidence_text as _operator_evidence_text
from tender_killer.analysis_operator_evidence_service import operator_source_context as _operator_source_context
from tender_killer.analysis_operator_evidence_service import source_label as _source_label
from tender_killer.analysis_operator_evidence_service import source_page as _source_page
from tender_killer.analysis_types import OperatorItem


BLOCKER_CATEGORIES = {"legal", "national_regime"}
DOCUMENT_CATEGORIES = {"documents", "standards", "qualification", "subject"}
FULFILLMENT_CATEGORIES = {"contract", "delivery"}
ACCEPTANCE_PAYMENT_CATEGORIES = {"acceptance", "financial", "payment"}
PRICE_FACTOR_CATEGORIES = ACCEPTANCE_PAYMENT_CATEGORIES | FULFILLMENT_CATEGORIES | {"standards"}


def build_operator_item(raw_item: dict[str, Any], index: int) -> OperatorItem:
    kind = str(raw_item.get("kind") or raw_item.get("type") or _fallback_kind(raw_item))
    raw_label = _text(raw_item.get("label")) or f"Факт {index + 1}"
    category = _text(raw_item.get("category")) or "general"
    severity = _text(raw_item.get("severity")) or "medium"
    source = _text(raw_item.get("document_name") or raw_item.get("source"))
    conflict_flags = _text_list(raw_item.get("conflict_flags"))
    expected_missing = bool(raw_item.get("expected_missing"))
    needs_review = bool(raw_item.get("needs_review")) or source == "Документ не привязан" or bool(conflict_flags) or expected_missing
    is_blocker = (
        bool(raw_item.get("is_blocker"))
        or kind in {"blocker", "red_flag"}
        or category in BLOCKER_CATEGORIES
        or (severity == "high" and kind not in {"document", "subject"})
    )
    label = _canonical_label(raw_label, category)
    is_price_factor = bool(raw_item.get("is_price_factor")) or (category in PRICE_FACTOR_CATEGORIES and kind != "subject")
    value = _text(raw_item.get("value")) or _text(raw_item.get("description")) or _text(raw_item.get("fragment"))
    fragment = _text(raw_item.get("fragment") or raw_item.get("evidence"))
    source_page = _source_page(raw_item.get("source_page"))
    source_label = _text(raw_item.get("source_label")) or _source_label(source, source_page)
    impact = _operator_impact(
        category=category,
        severity=severity,
        is_blocker=is_blocker,
        label=label,
        kind=kind,
        raw_impact=_text(raw_item.get("impact")),
    )
    evidence_text = _operator_evidence_text(label=label, value=value, fragment=fragment)
    source_context = _operator_source_context(
        raw_context=_text(raw_item.get("source_context")),
        source=source,
        evidence_text=evidence_text,
        impact=impact,
    )
    evidence_summary = _operator_evidence_summary(
        source_label=source_label,
        evidence_text=evidence_text,
        impact=impact,
    )
    source_binding = _operator_source_binding(
        raw_item=raw_item,
        source=source,
        source_label=source_label,
        source_context=source_context,
        fragment=fragment,
        needs_review=needs_review,
    )
    confidence_level = _operator_confidence_level(
        raw_item,
        source_binding,
        fragment=fragment,
        source_context=source_context,
    )
    evidence_quality = _operator_evidence_quality(
        source_binding=source_binding,
        confidence_level=confidence_level,
        conflict_flags=conflict_flags,
        expected_missing=expected_missing,
    )
    operator_action = _operator_action(
        kind,
        category,
        is_blocker,
        needs_review,
        label=label,
        raw_action=_text(raw_item.get("operator_action")),
    )
    price_impact = _text(raw_item.get("price_impact")) or _price_impact(category, label=label)
    display_tier = "expected_missing" if expected_missing else _operator_display_tier(
        source_binding=source_binding,
        confidence_level=confidence_level,
        is_blocker=is_blocker,
        needs_review=needs_review,
    )
    description = _operator_description(
        label=label,
        raw_description=_text(raw_item.get("description")),
        value=value,
        fragment=fragment,
        category=category,
        kind=kind,
        is_blocker=is_blocker,
    )
    interpretation = build_fact_interpretation(
        {
            **raw_item,
            "label": label,
            "value": value,
            "description": description,
            "category": category,
            "fragment": fragment,
            "source_context": source_context,
            "evidence_summary": evidence_summary,
            "operator_action": operator_action,
            "source_label": source_label,
        }
    )
    if expected_missing:
        interpretation = {
            "found": "",
            "meaning": "Точная формулировка в извлеченном тексте не найдена.",
            "impact": "Условие нужно подтвердить перед расчетом и решением об участии.",
            "action": f"Точная формулировка по условию «{label}» не найдена: найти ее в документах или подтвердить, что ее нет.",
            "confidence": "missing",
        }

    return {
        "id": _text(raw_item.get("id")) or f"{kind}:{_slug(label)}",
        "type": _text(raw_item.get("type")) or kind,
        "kind": kind,
        "label": label,
        "value": value,
        "description": description,
        "operator_summary": _operator_summary(
            label=label,
            description=description,
            impact=impact,
            is_blocker=is_blocker,
            needs_review=needs_review,
            source_binding=source_binding,
            confidence_level=confidence_level,
        ),
        "operator_check": _operator_check(
            label=label,
            action=operator_action,
            needs_review=needs_review,
            conflict_flags=conflict_flags,
            expected_missing=expected_missing,
        ),
        "interpretation": interpretation,
        "conflict_flags": conflict_flags,
        "expected_missing": expected_missing,
        "display_tier": display_tier,
        "weak_reason": _operator_weak_reason(
            display_tier=display_tier,
            source_binding=source_binding,
            confidence_level=confidence_level,
            needs_review=needs_review,
        ),
        "category": category,
        "severity": severity,
        "source": source,
        "document_name": source,
        "source_page": source_page,
        "source_label": source_label,
        "source_context": source_context,
        "evidence_summary": evidence_summary,
        "fragment": fragment,
        "source_binding": source_binding,
        "confidence_level": confidence_level,
        "evidence_quality": evidence_quality,
        "impact": impact,
        "document_role": _text(raw_item.get("document_role")),
        "context_document_role": _text(raw_item.get("context_document_role")),
        "context_document_role_confidence": _text(raw_item.get("context_document_role_confidence")),
        "context_source_priority": _text_list(raw_item.get("context_source_priority")),
        "context_topics": _text_list(raw_item.get("context_topics")),
        "context_mismatch_flags": _text_list(raw_item.get("context_mismatch_flags")),
        "context_text_quality": _text(raw_item.get("context_text_quality")),
        "context_source_authority": _text(raw_item.get("context_source_authority")),
        "context_source_reason": _text(raw_item.get("context_source_reason")),
        "document_stage": _text(raw_item.get("document_stage")),
        "amount_percent": raw_item.get("amount_percent"),
        "amount_type": _text(raw_item.get("amount_type")),
        "days": raw_item.get("days"),
        "deadline_type": _text(raw_item.get("deadline_type")),
        "responsible_party": _text(raw_item.get("responsible_party")),
        "operator_group": _text(raw_item.get("operator_group")) or _operator_group(kind, category, is_blocker, needs_review),
        "operator_action": operator_action,
        "price_impact": price_impact,
        "priority": _int_metric(raw_item.get("priority"), _priority(kind, category, severity, is_blocker, needs_review)),
        "rule_id": _text(raw_item.get("rule_id")),
        "is_blocker": is_blocker,
        "is_price_factor": is_price_factor,
        "needs_review": needs_review,
    }


def dedupe_operator_items(items: list[OperatorItem]) -> list[OperatorItem]:
    best_by_key: dict[tuple[str, str, str], OperatorItem] = {}
    ordered_keys: list[tuple[str, str, str]] = []
    for item in items:
        if not _is_operator_visible_item(item):
            continue
        key = _dedupe_key(item)
        current = best_by_key.get(key)
        if current is None:
            best_by_key[key] = item
            ordered_keys.append(key)
            continue
        if _operator_item_quality(item) > _operator_item_quality(current):
            best_by_key[key] = item
    return [best_by_key[key] for key in ordered_keys]


def fallback_kind(item: dict[str, Any]) -> str:
    return _fallback_kind(item)


def canonical_label(label: str, category: str) -> str:
    return _canonical_label(label, category)


def description_is_only_label(description: str, label: str) -> bool:
    return _description_is_only_label(description, label)


def operator_item_is_visible(item: OperatorItem) -> bool:
    return _is_operator_visible_item(item)


def operator_item_quality(item: OperatorItem) -> int:
    return _operator_item_quality(item)


def _fallback_kind(item: dict[str, Any]) -> str:
    category = _text(item.get("category"))
    severity = _text(item.get("severity"))
    if severity == "high" or category in BLOCKER_CATEGORIES:
        return "blocker"
    if category in DOCUMENT_CATEGORIES:
        return "supplier_document"
    if category in FULFILLMENT_CATEGORIES | ACCEPTANCE_PAYMENT_CATEGORIES:
        return "execution_term"
    return "requirement"


def _operator_impact(
    *,
    category: str,
    severity: str,
    is_blocker: bool,
    label: str,
    kind: str,
    raw_impact: str,
) -> str:
    fallback = _fallback_impact(category, severity, is_blocker, label=label, kind=kind)
    if fallback and (not raw_impact or _impact_is_generic(raw_impact)):
        return fallback
    return raw_impact or fallback


def _fallback_impact(
    category: str,
    severity: str,
    is_blocker: bool,
    *,
    label: str = "",
    kind: str = "",
) -> str:
    family = semantic_family(label, category)
    if family == "national_regime":
        return "Проверить допуск товара и заявки: страна происхождения, реестр и подтверждения могут привести к отклонению."
    if family == "license_sro":
        return "Проверить право участника выполнять работы: без лицензии или СРО заявку могут отклонить."
    if family == "contract_security":
        return "Учесть нагрузку на оборотку: обеспечение или гарантия замораживает деньги и влияет на решение об участии."
    if family == "short_delivery":
        return "Проверить наличие товара и срочную логистику: короткий срок может увеличить расходы или стать стоп-фактором."
    if family == "closing_documents":
        return "Подготовить закрывающие документы для приемки: ошибки в УПД, актах или накладных задержат оплату."
    if family == "montage_launch":
        return "Заложить работы, выезд специалистов, акты и возможные дополнительные расходы на монтаж или пусконаладку."
    if family == "certificate_documents":
        return "Проверить документы соответствия у поставщика: без сертификатов или деклараций возможна проблема с приемкой."
    if family == "warranty":
        return "Заложить резерв на гарантийные обязательства, замену брака и возможные выезды после поставки."
    if is_blocker or severity == "high":
        return "Проверить допустимость участия до расчета."
    if category in DOCUMENT_CATEGORIES:
        return "Проверить наличие подтверждающих документов."
    if category in FULFILLMENT_CATEGORIES:
        return "Учесть в сроках, логистике и договорной подготовке."
    if category in ACCEPTANCE_PAYMENT_CATEGORIES:
        return "Учесть в закрывающих документах и денежном цикле."
    return ""


def _impact_is_generic(impact: str) -> bool:
    text = _dedupe_text(impact)
    generic_markers = (
        "может повлиять на возможность участия",
        "заложить в решение или экономику",
        "учесть в сроках",
        "проверить наличие документа",
        "проверить перед принятием решения",
        "проверить допустимость участия до расчета",
    )
    return any(marker in text for marker in generic_markers)


def _operator_group(kind: str, category: str, is_blocker: bool, needs_review: bool) -> str:
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


def _operator_action(
    kind: str,
    category: str,
    is_blocker: bool,
    needs_review: bool,
    *,
    label: str = "",
    raw_action: str = "",
) -> str:
    family = semantic_family(label, category)
    if family == "national_regime":
        return "Проверить страну происхождения, применимый нацрежим и подтверждающие документы до участия."
    if family == "license_sro":
        return "Проверить, действительно ли нужна лицензия или СРО, и есть ли подтверждение у участника."
    if family == "contract_security":
        return "Учесть обеспечение в деньгах или гарантии и проверить возможность участия."
    if family == "short_delivery":
        return "Проверить наличие товара, реалистичность срока и заложить срочную логистику до расчета цены."
    if family == "closing_documents":
        return "Подготовить УПД, накладные или акты и проверить, без каких документов заказчик не примет и не оплатит поставку."
    if family == "montage_launch":
        return "Проверить, входят ли монтаж, пусконаладка или обучение в поставку, и заложить выезд специалистов."
    if family == "certificate_documents":
        return "Запросить у поставщика сертификаты, декларации или паспорта качества до подачи заявки."
    if family == "warranty":
        return "Проверить гарантийный срок, правила замены брака и резерв на гарантийные обязательства."
    if raw_action and raw_action not in {"Проверить до участия.", "Проверить допустимость участия до расчета."}:
        return raw_action
    if needs_review:
        return "Проверить источник факта вручную."
    if is_blocker:
        return "Проверить допустимость участия до расчета."
    if kind == "subject":
        return "Сверить предмет закупки."
    if category in DOCUMENT_CATEGORIES:
        return "Подготовить или проверить подтверждающие документы."
    if category == "delivery":
        return "Проверить срок, место и логистику поставки."
    if category == "contract":
        return "Проверить договорные обязанности и гарантию."
    if category == "acceptance":
        return "Проверить порядок приемки и закрывающие документы."
    if category in {"financial", "payment"}:
        return "Проверить оплату, аванс, обеспечение и денежный цикл."
    return "Проверить условие перед решением."


def _operator_display_tier(
    *,
    source_binding: dict[str, str],
    confidence_level: dict[str, str],
    is_blocker: bool,
    needs_review: bool,
) -> str:
    if is_blocker:
        return "primary"
    if needs_review:
        return "weak"
    if source_binding.get("level") in {"unbound", "inferred"}:
        return "weak"
    if confidence_level.get("level") == "low":
        return "weak"
    if source_binding.get("level") == "explicit" and confidence_level.get("level") == "high":
        return "primary"
    return "standard"


def _operator_weak_reason(
    *,
    display_tier: str,
    source_binding: dict[str, str],
    confidence_level: dict[str, str],
    needs_review: bool,
) -> str:
    if display_tier != "weak":
        return ""
    if needs_review or source_binding.get("level") == "unbound":
        return "Факт не привязан к надежному месту в документах; учитывайте его только после ручной проверки источника."
    if source_binding.get("level") == "inferred":
        return "Это вывод из общего контекста, а не прямое требование; проверьте формулировку в документах."
    if confidence_level.get("level") == "low":
        return "Низкая уверенность извлечения; нужна проверка перед расчетом и решением."
    return "Слабое совпадение: проверьте источник перед тем, как считать условие обязательным."


def _operator_summary(
    *,
    label: str,
    description: str,
    impact: str,
    is_blocker: bool,
    needs_review: bool,
    source_binding: dict[str, str],
    confidence_level: dict[str, str],
) -> str:
    binding_level = source_binding.get("level")
    confidence = confidence_level.get("level")
    if is_blocker:
        return f"Это условие может заблокировать участие или изменить решение по тендеру. {description}"
    if needs_review or binding_level in {"unbound", "inferred"} or confidence == "low":
        return f"Найден возможный признак «{label}», но источник слабый. Сначала подтвердите его в документе, затем учитывайте в решении."
    if impact and impact != description:
        return f"{description} Практический смысл: {impact}"
    return description


def _operator_check(
    *,
    label: str,
    action: str,
    needs_review: bool,
    conflict_flags: list[str] | None = None,
    expected_missing: bool = False,
) -> str:
    if conflict_flags:
        return f"Разобрать противоречие по условию «{label}»: {'; '.join(conflict_flags)}."
    if expected_missing:
        return f"Точная формулировка по условию «{label}» не найдена: найти ее в документах или подтвердить, что ее нет."
    if needs_review:
        return f"Найти точное место в документе по условию «{label}» и подтвердить, что оно относится к заявке."
    return action


def _price_impact(category: str, *, label: str = "") -> str:
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


def _priority(kind: str, category: str, severity: str, is_blocker: bool, needs_review: bool) -> int:
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


def _canonical_label(label: str, category: str) -> str:
    family = semantic_family(label, category)
    if family == "national_regime":
        return "национальный режим/страна происхождения"
    if family == "license_sro":
        return "лицензия/СРО"
    if family == "contract_security":
        return "обеспечение исполнения контракта"
    return label


def _operator_description(
    *,
    label: str,
    raw_description: str,
    value: str,
    fragment: str,
    category: str,
    kind: str,
    is_blocker: bool,
) -> str:
    family = semantic_family(label, category)
    if family == "national_regime":
        return (
            "Это проверка применимости национального режима: страна происхождения, реестровые записи "
            "и подтверждающие документы могут влиять на допуск заявки."
        )
    if family == "license_sro":
        return (
            "Это квалификационное ограничение: если лицензия или членство в СРО действительно требуется, "
            "участник без подтверждения может получить отклонение заявки."
        )
    if family == "contract_security":
        return (
            "Это денежная нагрузка на исполнение: обеспечение или независимая гарантия влияет на оборотку, "
            "резерв и решение об участии."
        )
    if family == "short_delivery":
        return (
            "Это риск физического исполнения: короткий срок поставки требует наличия товара на складе, "
            "быстрой логистики и подтверждения, что срок реально выполнить без срыва контракта."
        )
    if family == "closing_documents":
        return (
            "Это условие приемки и оплаты: УПД, накладные, счета-фактуры или акты должны совпасть с требованиями "
            "заказчика, иначе поставку могут не принять или задержать оплату."
        )
    if family == "montage_launch":
        return (
            "Это не просто поставка товара: монтаж, пусконаладка, ввод в эксплуатацию или обучение требуют "
            "специалистов, допуска на объект, актов и дополнительного времени."
        )
    if family == "certificate_documents":
        return (
            "Это подтверждение соответствия товара: сертификаты, декларации, паспорта качества или другие документы "
            "нужно получить у поставщика до заявки или до приемки."
        )
    if family == "warranty":
        return (
            "Это обязательства после поставки: гарантийный срок, замена брака и порядок ремонта могут потребовать "
            "резерва, документов и готовности обслуживать товар после приемки."
        )
    if category == "documents":
        return "Нужно понять, какой подтверждающий документ требуется и кто сможет его предоставить к заявке или поставке."
    if category == "standards":
        return "Это требование к характеристикам или соответствию товара; его нужно сверить с фактическим предложением."
    if category == "delivery":
        return "Это влияет на логистику, сроки поставки и возможные расходы исполнения."
    if category == "acceptance":
        return "Это влияет на приемку, закрывающие документы и момент, когда поставку признают исполненной."
    if category in {"financial", "payment"}:
        return "Это влияет на денежный цикл: оплату, аванс, удержания, обеспечение или резервы."
    if raw_description and not _description_is_only_label(raw_description, label):
        return raw_description
    if value and not _description_is_only_label(value, label) and value != fragment:
        return value
    if is_blocker:
        return "Условие может повлиять на допуск к участию, его нужно проверить до расчета."
    if kind == "subject":
        return value or "Краткое описание предмета закупки."
    return "Условие нужно сверить с документами закупки и учесть перед решением."


def _description_is_only_label(description: str, label: str) -> bool:
    return _dedupe_text(description) == _dedupe_text(label)


def _dedupe_key(item: OperatorItem) -> tuple[str, str, str]:
    kind = _text(item.get("kind") or item.get("type"))
    if kind in {"document", "document_summary", "subject"}:
        return (kind, _dedupe_text(item.get("id") or item.get("label")), "")
    label = _text(item.get("label"))
    category = _text(item.get("category"))
    family = semantic_family(label, category)
    if item.get("conflict_flags"):
        return ("conflict", family or _dedupe_text(label), _dedupe_text(item.get("fragment") or item.get("value") or item.get("source_context")))
    if family:
        return ("semantic", family, "")
    return (
        kind,
        _dedupe_text(label),
        "" if _operator_item_quality(item) <= 0 else _dedupe_text(item.get("fragment") or item.get("value")),
    )


def _is_operator_visible_item(item: OperatorItem) -> bool:
    kind = _text(item.get("kind") or item.get("type"))
    if kind == "document_summary":
        return True
    if kind == "document":
        return False
    if kind == "subject":
        return bool(_specific_text(item, allow_description=True))
    return _operator_item_quality(item) > 0


def _operator_item_quality(item: OperatorItem) -> int:
    label = _text(item.get("label"))
    category = _text(item.get("category"))
    score = 0
    source_context = _text(item.get("source_context"))
    fragment = _text(item.get("fragment"))
    specific = _specific_text(item)
    if source_context:
        score += 90
    if fragment and _item_text_is_relevant(item, fragment):
        score += 80
    if _has_real_source(item) and (not fragment or _item_text_is_relevant(item, fragment) or source_context):
        score += 45
    if specific and _item_text_is_relevant(item, specific):
        score += 35
    if score and _text(item.get("rule_id")):
        score += 5
    if not score and label:
        return 0
    family = semantic_family(label, category)
    if family:
        score += condition_source_hierarchy_score(item, normalized_condition_family(family))
    return score + min(_int_metric(item.get("priority"), 0), 100)


def _specific_text(item: OperatorItem, *, allow_description: bool = False) -> str:
    label = _text(item.get("label"))
    fields = ["value"]
    if allow_description:
        fields.append("description")
    for field in fields:
        text = _text(item.get(field))
        if text and not _description_is_only_label(text, label):
            return text
    return ""


def _has_real_source(item: OperatorItem) -> bool:
    source = _text(item.get("source_label") or item.get("source") or item.get("document_name"))
    if not source:
        return False
    return _dedupe_text(source) != _dedupe_text("Документ не привязан")


def _item_text_is_relevant(item: OperatorItem, value: str) -> bool:
    text = _dedupe_text(value)
    if not text:
        return False
    label = _text(item.get("label"))
    category = _text(item.get("category"))
    family = semantic_family(label, category)
    if family == "national_regime":
        return any(marker in text for marker in ("национальн", "страна происхожд", "страну происхожд", "страны происхожд", "1875"))
    if family == "license_sro":
        return any(marker in text for marker in ("сро", "лиценз", "саморегулируем"))
    if family == "contract_security":
        return any(marker in text for marker in ("обеспечение исполнения", "независим", "гарант"))
    tokens = _meaningful_label_tokens(label)
    if not tokens:
        return True
    if "/" in label or len(tokens) == 1:
        return any(token in text for token in tokens)
    return all(token in text for token in tokens)


def _meaningful_label_tokens(label: str) -> list[str]:
    tokens = _dedupe_text(label).split()
    return [token for token in tokens if len(token) >= 4]


def _text_list(value: Any) -> list[str]:
    values = value if isinstance(value, list) else [value]
    return [_text(item) for item in values if _text(item)]


def _int_metric(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _dedupe_text(value: Any) -> str:
    return re.sub(r"\s+", " ", _text(value)).strip().casefold()


def _compact_text(value: Any, limit: int) -> str:
    text = re.sub(r"\s+", " ", _text(value)).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip(" .,;:") + "…"


def _slug(value: str) -> str:
    normalized = re.sub(r"\s+", "-", value.strip().casefold())
    normalized = re.sub(r"[^0-9a-zа-яё_-]+", "", normalized)
    return normalized or "item"


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()
