from __future__ import annotations

import re
from typing import Any

from tender_killer.analysis_types import ConditionGroup
from tender_killer.analysis_types import ConditionGroupsContract
from tender_killer.analysis_types import OperatorItem


ACCEPTANCE_PAYMENT_CATEGORIES = {"acceptance", "financial", "payment"}

EXPECTED_TZ_CHECKS: tuple[dict[str, str], ...] = (
    {
        "family": "payment",
        "label": "условия оплаты",
        "category": "payment",
        "action": "Проверить срок оплаты, дату начала отсчета и документы для оплаты.",
    },
    {
        "family": "advance",
        "label": "аванс",
        "category": "financial",
        "action": "Проверить, предусмотрен ли аванс, его размер и условия выплаты.",
    },
    {
        "family": "retentions",
        "label": "удержания из оплаты",
        "category": "financial",
        "action": "Проверить удержания, неустойки из суммы оплаты и их влияние на денежный цикл.",
    },
    {
        "family": "closing_documents",
        "label": "приемка и закрывающие документы",
        "category": "acceptance",
        "action": "Проверить порядок приемки, УПД, акты, накладные и условия запуска оплаты.",
    },
    {
        "family": "delivery_deadline",
        "label": "срок поставки",
        "category": "delivery",
        "action": "Проверить срок поставки и дату начала отсчета срока.",
    },
    {
        "family": "delivery_place",
        "label": "место поставки",
        "category": "delivery",
        "action": "Проверить адрес, регион и условия передачи товара заказчику.",
    },
    {
        "family": "bid_security",
        "label": "обеспечение заявки",
        "category": "security",
        "action": "Проверить размер, форму и срок действия обеспечения заявки.",
    },
    {
        "family": "contract_security",
        "label": "обеспечение контракта",
        "category": "security",
        "action": "Проверить размер, форму и срок действия обеспечения исполнения контракта.",
    },
    {
        "family": "warranty",
        "label": "гарантия",
        "category": "contract",
        "action": "Проверить гарантийный срок, порядок замены брака и документы по гарантии.",
    },
    {
        "family": "penalty",
        "label": "штрафы и пени",
        "category": "penalty",
        "action": "Проверить штрафы, пени и риск санкций за просрочку или ненадлежащее исполнение.",
    },
    {
        "family": "national_regime",
        "label": "национальный режим",
        "category": "national_regime",
        "action": "Проверить ограничения, запреты, преимущества и подтверждение страны происхождения.",
    },
    {
        "family": "certificate_documents",
        "label": "сертификаты и декларации",
        "category": "documents",
        "action": "Проверить сертификаты, декларации, паспорта качества и регистрационные документы.",
    },
    {
        "family": "license_sro",
        "label": "лицензии или СРО",
        "category": "qualification",
        "action": "Проверить, требуется ли лицензия, СРО или иное квалификационное подтверждение.",
    },
    {
        "family": "packaging_marking",
        "label": "упаковка и маркировка",
        "category": "standards",
        "action": "Проверить требования к упаковке, маркировке, ярлыкам и сопроводительным знакам.",
    },
    {
        "family": "termination",
        "label": "условия расторжения",
        "category": "contract",
        "action": "Проверить основания расторжения, односторонний отказ и последствия для поставщика.",
    },
    {
        "family": "participant_restrictions",
        "label": "ограничения по участникам",
        "category": "restriction",
        "action": "Проверить СМП, преимущества, запреты, ограничения допуска и специальные требования к участнику.",
    },
)


def build_condition_groups(items: list[OperatorItem]) -> ConditionGroupsContract:
    grouped: dict[str, list[OperatorItem]] = {}
    for item in items:
        families = _condition_families(item)
        if not families:
            continue
        item["condition_families"] = families
        item["condition_family"] = families[0]
        for family in families:
            grouped.setdefault(family, []).append(item)
    group_items = [_condition_group(family, grouped[family]) for family in _ordered_condition_families(grouped)]
    return {
        "version": 1,
        "items": group_items,
        "metrics": {
            "total": len(group_items),
            "confirmed": sum(1 for group in group_items if group.get("status") == "confirmed"),
            "conflicts": sum(1 for group in group_items if group.get("status") == "conflict"),
            "expected_missing": sum(1 for group in group_items if group.get("status") == "expected_missing"),
            "manual_review": sum(1 for group in group_items if group.get("status") == "manual_review"),
        },
    }


def condition_family_and_polarity(item: dict[str, Any]) -> tuple[str, str]:
    return _condition_family_and_polarity(item)


def condition_family_and_measure(item: dict[str, Any]) -> tuple[str, str]:
    return _condition_family_and_measure(item)


def condition_source_hierarchy_score(item: dict[str, Any], family: str) -> int:
    return _condition_source_hierarchy_score(item, family)


def conflict_evidence_quality(flags: list[str]) -> dict[str, str]:
    return {
        "level": "conflict",
        "label": "противоречие",
        "detail": " ".join(flags),
    }


def expected_families(item: dict[str, Any]) -> set[str]:
    return _expected_families(item)


def normalized_condition_family(family: str) -> str:
    return _normalized_condition_family(family)


def semantic_family(label: str, category: str) -> str:
    return _semantic_family(label, category)


def unique_condition_texts(values: Any) -> list[str]:
    return _unique_condition_texts(values)


def _condition_group(family: str, items: list[OperatorItem]) -> ConditionGroup:
    primary = _primary_condition_item(family, items)
    status = _condition_group_status(items)
    source_status = _condition_source_status(status, primary)
    related_fact_ids = _condition_related_fact_ids(primary, items)
    return {
        "family": family,
        "label": _condition_family_label(family),
        "status": status,
        "source_status": source_status,
        "primary_fact_id": _text(primary.get("id")),
        "related_fact_ids": related_fact_ids,
        "sources": _unique_condition_texts(_condition_item_source(item) for item in items),
        "summary": _condition_group_summary(primary),
        "resolution": _condition_group_resolution(family, status, source_status),
        "operator_action": _condition_group_action(family, status, primary),
    }


def _condition_related_fact_ids(primary: dict[str, Any], items: list[dict[str, Any]]) -> list[str]:
    primary_id = _text(primary.get("id"))
    return _unique_condition_texts(
        [
            primary_id,
            *[_text(item.get("id")) for item in items if _text(item.get("id")) != primary_id],
        ]
    )


def _condition_families(item: dict[str, Any]) -> list[str]:
    families: list[str] = []
    polarity_family, polarity = _condition_family_and_polarity(item)
    if polarity_family and polarity:
        families.append(_normalized_condition_family(polarity_family))
    measure_family, measure = _condition_family_and_measure(item)
    if measure_family and measure:
        families.append(_normalized_condition_family(measure_family))
    families.extend(_normalized_condition_family(family) for family in _expected_families(item))
    semantic_family = _semantic_family(_text(item.get("label")), _text(item.get("category")))
    if semantic_family:
        families.append(_normalized_condition_family(semantic_family))
    return _unique_condition_texts(family for family in families if family)


def _normalized_condition_family(family: str) -> str:
    return {
        "payment_deadline": "payment",
        "acceptance_deadline": "closing_documents",
        "short_delivery": "delivery_deadline",
    }.get(family, family)


def _ordered_condition_families(grouped: dict[str, list[dict[str, Any]]]) -> list[str]:
    order = {spec["family"]: index for index, spec in enumerate(EXPECTED_TZ_CHECKS)}
    return sorted(grouped, key=lambda family: (order.get(family, 10_000), family))


def _condition_family_label(family: str) -> str:
    for spec in EXPECTED_TZ_CHECKS:
        if spec["family"] == family:
            return spec["label"]
    return family.replace("_", " ")


def _primary_condition_item(family: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    return max(items, key=lambda item: _condition_item_score(item, family))


def _condition_item_score(item: dict[str, Any], family: str = "") -> int:
    authority_score = {
        "primary_for_topic": 500,
        "primary_document": 420,
        "supporting_document": 260,
    }.get(_text(item.get("context_source_authority")), 0)
    binding = item.get("source_binding") if isinstance(item.get("source_binding"), dict) else {}
    binding_score = {
        "explicit": 180,
        "context": 100,
        "inferred": 20,
        "unbound": -100,
    }.get(_text(binding.get("level")), 0)
    if item.get("expected_missing"):
        binding_score -= 500
    if item.get("conflict_flags"):
        binding_score -= 20
    return authority_score + binding_score + _condition_source_hierarchy_score(item, family) + _int_metric(item.get("priority"), 0)


def _condition_source_hierarchy_score(item: dict[str, Any], family: str) -> int:
    role = _condition_source_role(item)
    if not role:
        return 0
    hierarchy = _condition_source_role_hierarchy(family)
    try:
        index = hierarchy.index(role)
    except ValueError:
        return 0
    return max(0, 120 - index * 15)


def _condition_source_role(item: dict[str, Any]) -> str:
    role = _text(item.get("context_document_role") or item.get("document_role"))
    return {
        "technical_specification": "technical_spec",
        "contract": "contract_project",
    }.get(role, role)


def _condition_source_role_hierarchy(family: str) -> tuple[str, ...]:
    if family in {"payment", "advance", "closing_documents"}:
        return (
            "pik_obligations_payment",
            "contract_project",
            "technical_spec",
            "technical_spec_appendix",
            "source_card",
            "participant_requirements",
        )
    if family in {"delivery_deadline", "delivery_place", "packaging_marking", "certificate_documents"}:
        return (
            "technical_spec",
            "technical_spec_appendix",
            "pik_obligations_payment",
            "contract_project",
            "source_card",
        )
    if family in {"contract_security", "penalty", "termination", "warranty", "retentions"}:
        return (
            "contract_project",
            "pik_obligations_payment",
            "technical_spec",
            "technical_spec_appendix",
            "source_card",
        )
    if family in {"bid_security", "participant_restrictions", "license_sro", "national_regime"}:
        return (
            "participant_requirements",
            "source_card",
            "technical_spec",
            "technical_spec_appendix",
            "contract_project",
        )
    return (
        "technical_spec",
        "technical_spec_appendix",
        "contract_project",
        "pik_obligations_payment",
        "participant_requirements",
        "source_card",
    )


def _condition_group_status(items: list[dict[str, Any]]) -> str:
    if any(item.get("conflict_flags") for item in items):
        return "conflict"
    if all(item.get("expected_missing") for item in items):
        return "expected_missing"
    if any(item.get("needs_review") for item in items):
        return "manual_review"
    return "confirmed"


def _condition_source_status(status: str, primary: dict[str, Any]) -> str:
    if status == "conflict":
        return "conflicting_sources"
    if status == "expected_missing":
        return "missing"
    authority = _text(primary.get("context_source_authority"))
    if authority in {"primary_for_topic", "primary_document"}:
        return "primary_source"
    binding = primary.get("source_binding") if isinstance(primary.get("source_binding"), dict) else {}
    if _text(binding.get("level")) == "explicit":
        return "explicit_source"
    if _text(binding.get("level")) in {"context", "unbound"}:
        return "needs_source_review"
    return "inferred"


def _condition_group_summary(primary: dict[str, Any]) -> str:
    interpretation = primary.get("interpretation") if isinstance(primary.get("interpretation"), dict) else {}
    return _text(
        interpretation.get("found")
        or primary.get("value")
        or primary.get("fragment")
        or primary.get("source_context")
        or primary.get("operator_summary")
    )


def _condition_group_resolution(family: str, status: str, source_status: str) -> str:
    label = _condition_family_label(family)
    if status == "conflict":
        return f"Разобрать противоречие по условию «{label}» и выбрать применимую редакцию документа."
    if status == "expected_missing":
        return f"Найти точную формулировку по условию «{label}» или подтвердить, что ее нет в документах."
    if status == "manual_review":
        return f"Проверить формулировку по условию «{label}» вручную перед решением."
    if source_status == "primary_source":
        return f"Считать рабочей формулировку по главному источнику для условия «{label}»."
    if source_status == "explicit_source":
        return f"Есть точная привязка к источнику по условию «{label}»."
    return f"Сверить источник по условию «{label}» перед использованием в решении."


def _condition_group_action(family: str, status: str, primary: dict[str, Any]) -> str:
    if status in {"conflict", "expected_missing", "manual_review"}:
        return _condition_group_resolution(family, status, _condition_source_status(status, primary))
    return _text(primary.get("operator_action")) or _condition_group_resolution(
        family,
        status,
        _condition_source_status(status, primary),
    )


def _condition_item_source(item: dict[str, Any]) -> str:
    return _text(item.get("source_label") or item.get("document_name") or item.get("source"))


def _unique_condition_texts(values: Any) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _text(value)
        if not text:
            continue
        key = _dedupe_text(text)
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _condition_family_and_polarity(item: dict[str, Any]) -> tuple[str, str]:
    text = _dedupe_text(" ".join(_text(item.get(key)) for key in ("label", "value", "fragment", "source_context")))
    if "аванс" in text:
        if "не предусмотр" in text or "без аванс" in text:
            return "advance", "negative"
        if "предусмотр" in text or re.search(r"\b\d+(?:[,.]\d+)?\s*%", text):
            return "advance", "positive"
    if "ндс" in text:
        if "без ндс" in text or "ндс не" in text:
            return "vat", "negative"
        if "включ" in text or re.search(r"\b\d+(?:[,.]\d+)?\s*%", text):
            return "vat", "positive"
    return "", ""


def _condition_family_and_measure(item: dict[str, Any]) -> tuple[str, str]:
    text = _dedupe_text(" ".join(_text(item.get(key)) for key in ("label", "category", "value", "fragment", "source_context")))
    category = _text(item.get("category"))
    percent = _first_percent_measure(text)
    days = _first_day_measure(text)
    if days and (category == "delivery" or any(marker in text for marker in ("срок постав", "срок исполн", "поставка в течение"))):
        return "delivery_deadline", f"days:{days}"
    if days and "оплат" in text:
        return "payment_deadline", f"days:{days}"
    if days and any(marker in text for marker in ("приемк", "приёмк", "прием", "приём")):
        return "acceptance_deadline", f"days:{days}"
    if percent and "обеспеч" in text and "заяв" in text:
        return "bid_security", f"percent:{percent}"
    if percent and "обеспеч" in text and any(marker in text for marker in ("контракт", "исполн")):
        return "contract_security", f"percent:{percent}"
    if percent and "аванс" in text:
        return "advance", f"percent:{percent}"
    return "", ""


def _first_day_measure(text: str) -> str:
    match = re.search(r"\b(\d+(?:[,.]\d+)?)\s*(?:рабоч\w+\s*)?(?:календар\w+\s*)?(?:дн|день|дня|дней)", text)
    return _normalized_measure(match.group(1)) if match else ""


def _first_percent_measure(text: str) -> str:
    match = re.search(r"\b(\d+(?:[,.]\d+)?)\s*%", text)
    return _normalized_measure(match.group(1)) if match else ""


def _normalized_measure(value: str) -> str:
    normalized = value.replace(",", ".")
    number = float(normalized)
    if number.is_integer():
        return str(int(number))
    return str(number)


def _expected_families(item: dict[str, Any]) -> set[str]:
    text = _dedupe_text(" ".join(_text(item.get(key)) for key in ("label", "category", "value", "fragment")))
    category = _text(item.get("category"))
    families: set[str] = set()
    has_retention = any(marker in text for marker in ("удерж", "неустоек из суммы", "неустойку из суммы", "из суммы оплаты"))
    if has_retention:
        families.add("retentions")
    if "оплат" in text and not has_retention:
        families.add("payment")
    if "аванс" in text:
        families.add("advance")
    if any(marker in text for marker in ("упд", "закрывающ", "накладн", "акт прием", "акт приём", "приемк", "приёмк")):
        families.add("closing_documents")
    if category == "delivery" or any(marker in text for marker in ("срок постав", "срок исполн", "поставка в течение")):
        families.add("delivery_deadline")
    if any(marker in text for marker in ("место постав", "адрес постав", "пункт постав", "регион постав")):
        families.add("delivery_place")
    if "обеспеч" in text and "заяв" in text:
        families.add("bid_security")
    if "обеспеч" in text and any(marker in text for marker in ("контракт", "исполн")):
        families.add("contract_security")
    if any(marker in text for marker in ("гарант", "замена брака", "ремонт")):
        families.add("warranty")
    if any(marker in text for marker in ("штраф", "пен", "неустой")):
        families.add("penalty")
    if category == "national_regime" or any(marker in text for marker in ("национальн", "страна происхожд", "страны происхожд", "1875")):
        families.add("national_regime")
    if any(marker in text for marker in ("сертифик", "деклараци", "паспорт качества", "регистрацион", "сгр")):
        families.add("certificate_documents")
    if any(marker in text for marker in ("лиценз", "сро", "саморегулируем")):
        families.add("license_sro")
    if any(marker in text for marker in ("упаков", "маркиров", "ярлык", "этикет")):
        families.add("packaging_marking")
    if any(marker in text for marker in ("расторж", "односторонн", "отказ от исполн")):
        families.add("termination")
    if any(marker in text for marker in ("смп", "сонко", "ограничен", "преимуществ", "участник")):
        families.add("participant_restrictions")
    return families


def _semantic_family(label: str, category: str) -> str:
    text = _dedupe_text(label)
    if category == "national_regime" or any(marker in text for marker in ("национальн", "страна происхожд", "страны происхожд", "1875")):
        return "national_regime"
    if category == "legal" and any(marker in text for marker in ("сро", "лиценз", "саморегулируем")):
        return "license_sro"
    if category in {"financial", "contract", "security"} and (
        any(marker in text for marker in ("обеспечение контракт", "обеспечение исполнения"))
        or ("независим" in text and "гарант" in text)
    ):
        return "contract_security"
    if any(marker in text for marker in ("монтаж", "пусконалад", "ввод в эксплуатац", "обучение", "инструктаж")):
        return "montage_launch"
    if category in {"documents", "standards"} and any(
        marker in text
        for marker in (
            "сертифик",
            "деклараци",
            "паспорт качества",
            "паспорт издел",
            "сгр",
            "регистрационное удостоверение",
            "удостоверение качества",
        )
    ):
        return "certificate_documents"
    if category in ACCEPTANCE_PAYMENT_CATEGORIES | {"documents"} and any(
        marker in text
        for marker in (
            "упд",
            "закрывающ",
            "накладн",
            "счет-фактур",
            "счёт-фактур",
            "акт прием",
            "акт приём",
            "акт выполн",
            "документы о приемке",
            "документы о приёмке",
        )
    ):
        return "closing_documents"
    if category == "delivery" and any(
        marker in text
        for marker in (
            "короткий срок",
            "срок поставки",
            "срок исполн",
            "поставка в течение",
            "в течение 1",
            "в течение 2",
            "в течение 3",
            "1 день",
            "2 дня",
            "3 дня",
        )
    ):
        return "short_delivery"
    if category in {"contract", "documents"} and any(marker in text for marker in ("гарантийн", "гарантия", "замена брака", "ремонт")):
        return "warranty"
    return ""


def _int_metric(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _dedupe_text(value: Any) -> str:
    return re.sub(r"\s+", " ", _text(value)).strip().casefold()


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()
