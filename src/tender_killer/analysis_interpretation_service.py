from __future__ import annotations

import re
from typing import Any


def build_fact_interpretation(item: dict[str, Any]) -> dict[str, str]:
    label = _text(item.get("label")) or "Условие"
    category = _text(item.get("category"))
    found, confidence = _found_text(item, label)
    family = _family(label, category, found)
    if not found:
        return {
            "found": "",
            "meaning": "Точная формулировка в извлеченном тексте не найдена.",
            "impact": "Нельзя считать условие подтвержденным без проверки источника.",
            "action": _text(item.get("operator_action")) or "Проверить точную формулировку в документах.",
            "confidence": "missing",
        }

    meaning, impact, action = _interpret_family(
        family=family,
        found=found,
        fallback_action=_text(item.get("operator_action")),
    )
    return {
        "found": found,
        "meaning": meaning,
        "impact": impact,
        "action": action,
        "confidence": confidence,
    }


def _found_text(item: dict[str, Any], label: str) -> tuple[str, str]:
    for field, confidence in (
        ("value", "value"),
        ("fragment", "fragment"),
        ("source_context", "context"),
        ("evidence_summary", "context"),
    ):
        value = _text(item.get(field))
        if _specific_text(label, value):
            return _normalize_found_text(value), confidence
    return "", "missing"


def _specific_text(label: str, value: str) -> bool:
    normalized_value = _normalized(value)
    normalized_label = _normalized(label)
    if not normalized_value or normalized_value == normalized_label:
        return False
    if len(normalized_value) < 8 and not re.search(r"\d", normalized_value) and "нет" not in normalized_value:
        return False
    generic_prefixes = (
        "это влияет",
        "это условие",
        "нужно понять",
        "условие нужно",
        "проверить",
        "найден возможный признак",
        "практический смысл",
    )
    return not normalized_value.startswith(generic_prefixes)


def _family(label: str, category: str, found: str) -> str:
    text = _normalized(f"{label} {category} {found}")
    if "ндс" in text or "налог на добавлен" in text:
        return "vat"
    if "аванс" in text:
        return "advance"
    if "оплат" in text or category == "payment":
        return "payment"
    if any(marker in text for marker in ("упд", "акт приема", "акт приёма", "накладн", "закрывающ")):
        return "closing_documents"
    if any(marker in text for marker in ("монтаж", "пусконалад", "ввод в эксплуатац", "разгруз")):
        return "service_scope"
    if "обеспеч" in text or "гарант" in text:
        return "security"
    if "срок" in text or "поставк" in text or category == "delivery":
        return "delivery"
    if "прием" in text or "приём" in text or category == "acceptance":
        return "acceptance"
    if any(marker in text for marker in ("сертификат", "декларац", "паспорт качества")):
        return "certificate"
    if "гаранти" in text:
        return "warranty"
    if "националь" in text or "страна происхожд" in text:
        return "national_regime"
    if "сро" in text or "лиценз" in text:
        return "license"
    if category in {"financial", "payment"}:
        return "payment"
    return "general"


def _interpret_family(*, family: str, found: str, fallback_action: str) -> tuple[str, str, str]:
    text = _normalized(found)
    if family == "vat":
        vat_rate = _first_percent(found)
        return (
            f"В цене отдельно зафиксировано условие по НДС{f' {vat_rate}' if vat_rate else ''}.",
            "НДС влияет на себестоимость, налоговый учет и сопоставимость цен поставщиков.",
            fallback_action or "Проверить ставку НДС, включение налога в цену и корректность КП поставщика.",
        )
    if family == "closing_documents":
        docs = _document_names(found)
        return (
            f"Для закрытия поставки нужны документы{f': {docs}' if docs else ''}.",
            "От закрывающих документов зависит приемка, запуск оплаты и отсутствие споров по поставке.",
            fallback_action or "Подготовить закрывающие документы и проверить, кто подписывает УПД, акт или накладную.",
        )
    if family == "service_scope":
        return (
            "В поставку включены дополнительные работы: монтаж, пусконаладка, разгрузка или ввод в эксплуатацию.",
            "Это дополнительные расходы, время специалистов и риск просрочки, если заложить только цену товара.",
            fallback_action or "Проверить, нужны ли специалист, выезд, инструмент, допуск на объект и отдельная стоимость работ.",
        )
    if family == "advance":
        if "не предусмотр" in text or "без аванс" in text:
            return (
                "Авансом расходы поставщика не закрываются; деньги придут после исполнения условий оплаты.",
                "Нужна оборотка на закупку, доставку и период до оплаты.",
                "Проверить срок оплаты и заложить кассовый разрыв.",
            )
        return (
            "В документах есть условие об авансе; часть денег может поступить до полного исполнения.",
            "Аванс снижает потребность в оборотке, но нужно проверить условия его получения.",
            "Проверить размер аванса, основание выплаты и сроки.",
        )
    if family == "payment":
        deadline = _payment_deadline(found)
        meaning = f"Оплата привязана к условиям документа{f' и сроку {deadline}' if deadline else ''}."
        action = fallback_action or "Проверить срок оплаты, документы для оплаты и дату начала отсчета."
        if "упд" in text and "УПД" not in action:
            action = f"{action} Отдельно сверить УПД."
        return (
            meaning,
            "Влияет на кассовый разрыв и срок возврата денег после поставки.",
            action,
        )
    if family == "security":
        percent = _first_percent(found)
        return (
            f"Нужно обеспечить исполнение контракта{f' на {percent}' if percent else ''}.",
            "Деньги или банковская гарантия замораживают лимит и оборотку.",
            fallback_action or "Проверить размер обеспечения, способ внесения и срок возврата.",
        )
    if family == "delivery":
        days = _first_number(text)
        return (
            f"Поставка ограничена сроком{f' около {days} дней' if days else ''}.",
            "Влияет на наличие товара, логистику и риск просрочки.",
            fallback_action or "Проверить склад, маршрут, разгрузку и реалистичность срока.",
        )
    if family == "acceptance":
        return (
            "Условие описывает порядок приемки или подтверждения поставки.",
            "От приемки зависит момент закрытия обязательств и запуск оплаты.",
            fallback_action or "Проверить, какие документы нужны для приемки и оплаты.",
        )
    if family == "certificate":
        return (
            "Потребуются документы соответствия товара.",
            "Без подтверждающих документов заявку или поставку могут не принять.",
            fallback_action or "Запросить сертификаты, декларации или паспорта качества у поставщика.",
        )
    if family == "warranty":
        return (
            "Есть гарантийные обязательства после поставки.",
            "Нужен резерв на замену, ремонт или обслуживание товара.",
            fallback_action or "Проверить срок гарантии и порядок устранения дефектов.",
        )
    if family == "national_regime":
        return (
            "Нужно подтвердить страну происхождения или применимость национального режима.",
            "Ошибки в подтверждении могут привести к отклонению заявки.",
            fallback_action or "Проверить страну происхождения, реестр и подтверждающие документы.",
        )
    if family == "license":
        return (
            "Участнику может потребоваться лицензия, СРО или другой допуск.",
            "Без допуска заявку могут отклонить.",
            fallback_action or "Проверить, относится ли требование к участнику и есть ли подтверждение.",
        )
    return (
        "Условие найдено в документах и требует проверки перед решением.",
        "Влияние зависит от точной формулировки и роли документа.",
        fallback_action or "Сверить условие с документом и учесть перед решением.",
    )


def _compact_sentence(value: str) -> str:
    text = _text(value)
    match = re.search(r"[.!?](\s|$)", text)
    if match and match.start() >= 20:
        text = text[: match.start() + 1]
    if len(text) <= 240:
        return text
    return f"{text[:239].rstrip()}…"


def _normalize_found_text(value: str) -> str:
    text = _compact_sentence(value)
    text = re.sub(r"^\s*(?:п\.|пункт\s*)?\d+(?:\.\d+)*[.)]?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"(\d+(?:[,.]\d+)?)\s+%", r"\1%", text)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def _first_number(text: str) -> str:
    match = re.search(r"\b\d+\b", text)
    return match.group(0) if match else ""


def _first_percent(text: str) -> str:
    match = re.search(r"\b\d+(?:[,.]\d+)?\s*%", text)
    return re.sub(r"\s+", "", match.group(0)).replace(",", ".") if match else ""


def _payment_deadline(text: str) -> str:
    match = re.search(
        r"\b\d+\s+(?:рабочих\s+|календарных\s+)?дн(?:ей|я|ь)\b",
        _normalized(text),
    )
    return match.group(0) if match else ""


def _document_names(text: str) -> str:
    normalized = _normalized(text)
    names: list[str] = []
    for marker, label in (
        ("упд", "УПД"),
        ("акт", "акт"),
        ("накладн", "накладная"),
        ("счет-фактур", "счет-фактура"),
        ("счёт-фактур", "счет-фактура"),
    ):
        if marker in normalized and label not in names:
            names.append(label)
    return ", ".join(names)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\n", " ").strip()


def _normalized(value: Any) -> str:
    return re.sub(r"\s+", " ", _text(value).casefold()).strip()
