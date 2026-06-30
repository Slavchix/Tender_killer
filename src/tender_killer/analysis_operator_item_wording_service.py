from __future__ import annotations

import re
from typing import Any

from tender_killer.analysis_condition_groups_service import semantic_family
from tender_killer.analysis_operator_item_taxonomy_service import ACCEPTANCE_PAYMENT_CATEGORIES
from tender_killer.analysis_operator_item_taxonomy_service import DOCUMENT_CATEGORIES
from tender_killer.analysis_operator_item_taxonomy_service import FULFILLMENT_CATEGORIES


def operator_impact(
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


def operator_action(
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


def operator_display_tier(
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


def operator_weak_reason(
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


def operator_summary(
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


def operator_check(
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


def operator_description(
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
    if raw_description and not description_is_only_label(raw_description, label):
        return raw_description
    if value and not description_is_only_label(value, label) and value != fragment:
        return value
    if is_blocker:
        return "Условие может повлиять на допуск к участию, его нужно проверить до расчета."
    if kind == "subject":
        return value or "Краткое описание предмета закупки."
    return "Условие нужно сверить с документами закупки и учесть перед решением."


def description_is_only_label(description: str, label: str) -> bool:
    return _dedupe_text(description) == _dedupe_text(label)


def _dedupe_text(value: Any) -> str:
    return re.sub(r"\s+", " ", _text(value)).strip().casefold()


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()
