from __future__ import annotations

import re
from typing import Any


BLOCKER_CATEGORIES = {"legal", "national_regime"}
PRICE_FACTOR_CATEGORIES = {"acceptance", "contract", "delivery", "financial", "payment", "standards"}
SUPPLIER_DOCUMENT_CATEGORIES = {"documents", "standards"}


def structured_metadata(
    *,
    label: str,
    category: str,
    term_type: str,
    text: str,
    document_name: str,
    document_roles: dict[str, str],
    document_contexts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    role = _text(document_roles.get(document_name))
    if role:
        metadata["document_role"] = role
    metadata.update(
        _context_metadata(
            document_contexts.get(document_name),
            label=label,
            category=category,
            term_type=term_type,
        )
    )

    stage = _document_stage(label=label, category=category, text=text)
    if stage:
        metadata["document_stage"] = stage

    amount_percent = _amount_percent(text)
    if amount_percent is not None:
        metadata["amount_percent"] = amount_percent
        amount_type = _amount_type(label=label, category=category, term_type=term_type, text=text)
        if amount_type:
            metadata["amount_type"] = amount_type

    days = _days(text)
    if days is not None:
        metadata["days"] = days
        deadline_type = _deadline_type(label=label, category=category, term_type=term_type, text=text)
        if deadline_type:
            metadata["deadline_type"] = deadline_type

    responsible_party = _responsible_party(text) or ("supplier" if category == "delivery" else "")
    if responsible_party:
        metadata["responsible_party"] = responsible_party

    return metadata

def _context_metadata(
    context_document: dict[str, Any] | None,
    *,
    label: str,
    category: str,
    term_type: str,
) -> dict[str, Any]:
    if not isinstance(context_document, dict):
        return {}
    metadata: dict[str, Any] = {}
    role = _text(context_document.get("document_role"))
    if role:
        metadata["context_document_role"] = role
    role_confidence = _text(context_document.get("document_role_confidence"))
    if role_confidence:
        metadata["context_document_role_confidence"] = role_confidence
    source_priority = _unique_texts(context_document.get("source_priority") or [])
    if source_priority:
        metadata["context_source_priority"] = source_priority
    source_authority = _context_source_authority(
        role=role,
        source_priority=source_priority,
        label=label,
        category=category,
        term_type=term_type,
    )
    if source_authority:
        metadata.update(source_authority)
    topics = _context_topics(context_document)
    if topics:
        metadata["context_topics"] = topics
    mismatch_flags = _unique_texts(context_document.get("mismatch_flags") or [])
    if mismatch_flags:
        metadata["context_mismatch_flags"] = mismatch_flags
    text_quality = context_document.get("text_quality") if isinstance(context_document.get("text_quality"), dict) else {}
    text_quality_status = _text(text_quality.get("status"))
    if text_quality_status:
        metadata["context_text_quality"] = text_quality_status
    return metadata

def _context_source_authority(
    *,
    role: str,
    source_priority: list[str],
    label: str,
    category: str,
    term_type: str,
) -> dict[str, str]:
    if not role:
        return {}
    priority = set(source_priority)
    topic_keys = _context_topic_keys(label=label, category=category, term_type=term_type)
    matched_topics = sorted(priority & topic_keys)
    if matched_topics:
        return {
            "context_source_authority": "primary_for_topic",
            "context_source_reason": f"{role} covers {', '.join(matched_topics)}",
        }
    if role in {"contract_project", "pik_obligations_payment", "technical_spec", "technical_spec_appendix"}:
        return {
            "context_source_authority": "primary_document",
            "context_source_reason": f"{role} is a primary tender document",
        }
    if role == "participant_requirements":
        return {
            "context_source_authority": "supporting_document",
            "context_source_reason": "participant_requirements supports admission checks",
        }
    return {
        "context_source_authority": "supporting_document",
        "context_source_reason": f"{role} is a supporting source",
    }

def _context_topic_keys(*, label: str, category: str, term_type: str) -> set[str]:
    combined = _normalized_text(" ".join((label, category, term_type)))
    keys = {_text(term_type), _text(category)} - {""}
    if category == "payment" or "оплат" in combined or "payment" in combined:
        keys.add("payment_terms")
    if "аванс" in combined or "advance" in combined:
        keys.add("advance")
    if category == "acceptance" or "прием" in combined or "приём" in combined:
        keys.update({"acceptance_process", "acceptance_documents"})
    if category == "delivery" or "постав" in combined or "delivery" in combined:
        keys.update({"delivery_schedule", "delivery_place", "logistics_responsibility"})
    if category in {"documents", "standards"} or any(marker in combined for marker in ("сертифик", "деклараци", "паспорт")):
        keys.add("certificates_closing_docs")
    if category in {"financial", "security"} or "обеспеч" in combined or "security" in combined:
        keys.add("contract_security")
    if "обеспеч" in combined and "заяв" in combined:
        keys.add("bid_security")
    if "удерж" in combined or "retention" in combined:
        keys.add("retentions")
    if category == "contract" or "гарант" in combined or "warranty" in combined:
        keys.add("warranty")
    if "расторж" in combined or "односторон" in combined or "termination" in combined:
        keys.add("termination")
    if category == "qualification" or any(marker in combined for marker in ("лиценз", "сро", "участник")):
        keys.add("participant_requirements")
    if any(marker in combined for marker in ("смп", "сонко", "преимуществ", "ограничен")):
        keys.add("participant_restrictions")
    if category == "penalty" or any(marker in combined for marker in ("штраф", "пени", "пеня")):
        keys.add("penalties")
    return keys

def _context_topics(context_document: dict[str, Any]) -> list[str]:
    return _unique_texts(
        _text(section.get("topic"))
        for section in context_document.get("section_taxonomy") or []
        if isinstance(section, dict)
    )

def _amount_percent(text: str) -> int | float | None:
    match = re.search(r"(\d+(?:[,.]\d+)?)\s*(?:%|процент(?:а|ов)?)", text, flags=re.IGNORECASE)
    if not match:
        return None
    raw_value = match.group(1).replace(",", ".")
    value = float(raw_value)
    return int(value) if value.is_integer() else value

def _amount_type(*, label: str, category: str, term_type: str, text: str) -> str:
    combined = _normalized_text(" ".join((label, category, term_type, text)))
    if "обеспечение исполнения" in combined or term_type == "contract_security":
        return "contract_security"
    if "аванс" in combined:
        return "advance"
    if "штраф" in combined or "пени" in combined or "пеня" in combined:
        return "penalty"
    if category in {"financial", "payment"}:
        return "financial_condition"
    return ""

def _days(text: str) -> int | None:
    patterns = (
        r"(?:в течение|не позднее|срок[^.]{0,80}?)(\d{1,3})\s*(?:рабочих|календарных)?\s*дн",
        r"(\d{1,3})\s*(?:рабочих|календарных)?\s*дн",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None

def _deadline_type(*, label: str, category: str, term_type: str, text: str) -> str:
    combined = _normalized_text(" ".join((label, category, term_type, text)))
    if category == "delivery" or "поставк" in combined or term_type == "delivery_deadline":
        return "delivery"
    if category == "payment" or "оплат" in combined:
        return "payment"
    if category == "acceptance" or "приемк" in combined or "приёмк" in combined:
        return "acceptance"
    if "устран" in combined and "замечан" in combined:
        return "correction"
    return ""

def _responsible_party(text: str) -> str:
    combined = _normalized_text(text)
    if any(marker in combined for marker in ("поставщик", "поставщиком", "исполнитель", "исполнителем")):
        return "supplier"
    if any(marker in combined for marker in ("заказчик", "заказчиком")):
        return "customer"
    return ""

def _document_stage(*, label: str, category: str, text: str) -> str:
    combined = _normalized_text(" ".join((label, category, text)))
    if category in {"national_regime", "legal", "qualification"} or "заявк" in combined or "участ" in combined:
        return "bid"
    if category == "documents":
        if any(marker in combined for marker in ("приемк", "приёмк", "поставк", "товар")):
            return "delivery_or_acceptance"
        return "preparation"
    if category == "delivery" or "поставк" in combined:
        return "delivery"
    if category in {"acceptance", "payment"} or "приемк" in combined or "приёмк" in combined:
        return "acceptance"
    if category in {"financial", "contract"}:
        return "contract_execution"
    return ""

def semantic_key(label: str, category: str) -> str:
    combined = _normalized_text(f"{label} {category}")
    if category == "national_regime" or any(
        marker in combined
        for marker in (
            "национальн",
            "страна происхожд",
            "страны происхожд",
            "1875",
            "national",
            "nacional",
            "proiskhozhden",
            "origin",
        )
    ):
        return "national_regime"
    if category == "legal" and any(
        marker in combined
        for marker in ("сро", "лиценз", "саморегулируем", "sro", "license", "licence")
    ):
        return "license_sro"
    if any(
        marker in combined
        for marker in (
            "обеспечение исполнения",
            "независим",
            "contract_security",
            "obespechenie ispolneniya",
            "security",
        )
    ):
        return "contract_security"
    return ""

def impact(category: str, severity: str) -> str:
    if severity == "high" and category in BLOCKER_CATEGORIES:
        return "Проверить до участия: может повлиять на возможность участия."
    if severity == "high":
        return "Проверить до участия и заложить в решение или экономику."
    if category in SUPPLIER_DOCUMENT_CATEGORIES:
        return "Проверить наличие документа у поставщика или подготовить подтверждение."
    if category in PRICE_FACTOR_CATEGORIES:
        return "Учесть в сроках, резерве, стоп-цене или договорной подготовке."
    return "Проверить перед принятием решения."

def _unique_texts(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = _text(value)
        key = _dedupe_text(text)
        if not text or key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result

def _normalized_text(value: Any) -> str:
    return re.sub(r"\s+", " ", _text(value)).strip().casefold()

def _dedupe_text(value: Any) -> str:
    text = re.sub(r"[^\wа-яА-ЯёЁ]+", " ", _text(value), flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip().casefold()

def _text(value: Any) -> str:
    if value in (None, ""):
        return ""
    return str(value).strip()
