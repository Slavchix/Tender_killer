from __future__ import annotations

import hashlib
import re
from typing import Any

from tender_killer.analysis_text_index_service import infer_document_role


PRIMARY_ROLES = {
    "contract_project",
    "pik_obligations_payment",
    "technical_spec",
    "technical_spec_appendix",
}

ROLE_PRIORITY: dict[str, list[str]] = {
    "pik_obligations_payment": [
        "payment_terms",
        "advance",
        "acceptance_documents",
        "delivery_schedule",
        "delivery_place",
        "contract_security",
        "retentions",
        "edi_pik",
    ],
    "contract_project": ["contract_terms", "penalties", "retentions", "termination", "responsibility"],
    "technical_spec": [
        "subject",
        "items",
        "technical_characteristics",
        "delivery_place",
        "delivery_schedule",
        "logistics_responsibility",
        "certificates_closing_docs",
        "warranty",
    ],
    "technical_spec_appendix": ["items", "technical_characteristics", "certificates_closing_docs"],
    "participant_requirements": ["participant_requirements"],
    "signing_sheet": ["signature_metadata"],
    "archive_duplicate": ["duplicate"],
    "unsupported_primary": ["text_quality"],
    "source_card": ["source_card"],
    "other": [],
}

TOPIC_ORDER = (
    "subject",
    "items",
    "technical_characteristics",
    "delivery_place",
    "delivery_schedule",
    "logistics_responsibility",
    "acceptance_process",
    "acceptance_documents",
    "payment_terms",
    "advance",
    "retentions",
    "contract_security",
    "warranty",
    "participant_requirements",
    "certificates_closing_docs",
    "penalties",
    "edi_pik",
    "text_quality",
)

STOP_TOKENS = {
    "поставка",
    "поставки",
    "поставку",
    "товар",
    "товара",
    "товаров",
    "работ",
    "работы",
    "услуг",
    "услуги",
    "оказание",
    "оказания",
    "закупки",
    "для",
    "нужд",
    "муниципальных",
    "государственных",
    "контракт",
    "договора",
}


def build_analysis_context_pack(
    documents: list[dict[str, Any]] | None,
    *,
    tender: dict[str, Any] | None = None,
    items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build deterministic document context used before fact/agent interpretation."""
    document_rows = documents or []
    context_documents = [
        _context_document(index, document, tender=tender or {})
        for index, document in enumerate(document_rows, start=1)
        if isinstance(document, dict)
    ]
    _attach_duplicate_groups(context_documents)
    expected_missing_reasons = _expected_missing_reasons(context_documents)
    mismatch_flags = _unique_texts(
        flag for document in context_documents for flag in document.get("mismatch_flags", [])
    )
    topic_coverage = _topic_coverage(context_documents)
    return {
        "version": 1,
        "mode": "deterministic_document_context",
        "tender_identity": _tender_identity(tender or {}, items or []),
        "metrics": {
            "documents": len(context_documents),
            "primary_documents": sum(1 for document in context_documents if document.get("document_role") in PRIMARY_ROLES),
            "unsupported_primary": sum(
                1 for document in context_documents if document.get("document_role") == "unsupported_primary"
            ),
            "duplicate_groups": _duplicate_groups_count(context_documents),
            "mismatch_flags": len(mismatch_flags),
            "topics": len(topic_coverage),
        },
        "mismatch_flags": mismatch_flags,
        "expected_missing_reasons": expected_missing_reasons,
        "topic_coverage": topic_coverage,
        "cross_document_links": _cross_document_links(context_documents),
        "documents": context_documents,
    }


def _context_document(index: int, document: dict[str, Any], *, tender: dict[str, Any]) -> dict[str, Any]:
    text = _text(document.get("text_content"))
    role, role_evidence = _document_role(document, text)
    section_taxonomy = _section_taxonomy(text, role)
    identity_match = _tender_identity_match(text, tender)
    mismatch_flags = []
    if identity_match.get("subject", {}).get("status") == "mismatch":
        mismatch_flags.append("subject_mismatch")
    text_hash = _sha1(_compact(text)) if _compact(text) else ""
    content_hash = text_hash or _sha1(
        " ".join(
            _text(document.get(key))
            for key in ("name", "document_type", "url", "source_document_id")
            if _text(document.get(key))
        )
    )
    return {
        "id": f"document:{index}",
        "name": _document_name(document, index),
        "document_type": _text(document.get("document_type")),
        "document_role": role,
        "document_role_confidence": _role_confidence(role, role_evidence),
        "role_evidence": role_evidence,
        "source_priority": _source_priority(role, section_taxonomy),
        "text_quality": _text_quality(document, text),
        "content_hash": content_hash,
        "text_hash": text_hash,
        "archive_entries": _archive_entries(document, text),
        "duplicate_group_id": "",
        "revision_group_id": _revision_group_id(document),
        "tender_identity_match": identity_match,
        "mismatch_flags": mismatch_flags,
        "section_taxonomy": section_taxonomy,
    }


def _document_role(document: dict[str, Any], text: str) -> tuple[str, list[str]]:
    identity = _normalized(" ".join(_text(document.get(key)) for key in ("document_type", "name", "url")))
    preview = _normalized(text[:5000])
    inferred = infer_document_role(document)
    evidence: list[str] = []
    if _text(document.get("text_status")).casefold() not in {"ok", "ready"}:
        if inferred in {"technical_specification", "contract"}:
            return "unsupported_primary", ["primary document text is not readable"]
    if "пик" in identity or "сведения об обязательствах сторон и порядке оплаты" in preview:
        evidence.append("ПИК / сведения об обязательствах и оплате")
        return "pik_obligations_payment", evidence
    if "приложение к описанию объекта закупки" in identity:
        evidence.append("приложение к описанию объекта закупки")
        return "technical_spec_appendix", evidence
    if inferred == "technical_specification":
        evidence.append("описание объекта закупки / техническое задание")
        return "technical_spec", evidence
    if inferred == "contract":
        evidence.append("проект контракта / договор")
        return "contract_project", evidence
    if inferred == "participant_requirements":
        evidence.append("единые требования / ст. 31")
        return "participant_requirements", evidence
    if inferred == "nmck":
        evidence.append("НМЦК / расчет цены")
        return "source_card", evidence
    if "лист подписания" in preview and len(_compact(text)) < 4000:
        evidence.append("лист подписания")
        return "signing_sheet", evidence
    return "other", evidence


def _source_priority(role: str, section_taxonomy: list[dict[str, Any]]) -> list[str]:
    if role == "participant_requirements":
        return ["participant_requirements"]
    base = ROLE_PRIORITY.get(role, [])
    topics = [str(item.get("topic")) for item in section_taxonomy if item.get("topic")]
    return _unique_texts([*base, *topics])


def _section_taxonomy(text: str, role: str) -> list[dict[str, Any]]:
    compact = _compact(text)
    if not compact:
        return [{"topic": "text_quality", "confidence": "missing", "evidence": "Текст документа не извлечен."}]
    if role == "participant_requirements":
        return [
            {
                "topic": "participant_requirements",
                "confidence": "high",
                "evidence": _first_evidence(compact, ("статья 31", "единые требования", "участник закупки")),
                "markers": ["статья 31", "единые требования"],
            }
        ]
    taxonomy: list[dict[str, Any]] = []
    for topic in TOPIC_ORDER:
        evidence, markers = _topic_evidence(topic, compact)
        if not evidence:
            continue
        taxonomy.append(
            {
                "topic": topic,
                "confidence": "high" if topic in ROLE_PRIORITY.get(role, []) else "medium",
                "evidence": evidence,
                "markers": markers,
            }
        )
    return taxonomy


def _topic_evidence(topic: str, text: str) -> tuple[str, list[str]]:
    paragraphs = _paragraphs(text)
    for paragraph in paragraphs:
        markers = _topic_markers(topic, paragraph)
        if markers:
            return _short(paragraph, 320), markers
    return "", []


def _topic_markers(topic: str, paragraph: str) -> list[str]:
    text = _normalized(paragraph)
    if topic == "subject" and any(marker in text for marker in ("предмет контракта", "предмет договора", "наименование объекта закупки")):
        return ["subject"]
    if topic == "technical_characteristics" and any(
        marker in text for marker in ("техническ", "характеристик", "окпд2", "ктру", "детализированное наименование")
    ):
        return ["technical_characteristics"]
    if topic == "items" and any(marker in text for marker in ("количество", "единица измерения", "наименование товара")):
        return ["items"]
    if topic == "delivery_place" and any(marker in text for marker in ("место доставки", "место поставки", "адрес поставки")):
        return ["delivery_place"]
    if topic == "delivery_schedule" and any(marker in text for marker in ("срок постав", "срок исполнения", "срок окончания")):
        return ["delivery_schedule"]
    if topic == "logistics_responsibility" and any(marker in text for marker in ("разгруз", "транспорт", "за свой счет", "упаков")):
        return ["logistics_responsibility"]
    if topic == "acceptance_process" and any(marker in text for marker in ("порядок прием", "порядок приём", "приемка товара", "приёмка товара")):
        return ["acceptance_process"]
    if topic == "acceptance_documents" and any(
        marker in text
        for marker in (
            "упд",
            "документ о приемке",
            "документ о приёмке",
            "документа о приемке",
            "документа о приёмке",
            "акт прием",
            "акт приём",
            "акт выполненных",
            "акт оказанных",
            "подписания акта",
            "накладн",
            "закрывающ",
        )
    ):
        return ["acceptance_documents"]
    if topic == "payment_terms" and (
        "порядок и сроки оплаты" in text
        or "порядок оплаты" in text
        or ("оплат" in text and any(marker in text for marker in ("100", "фактическ", "течение", "рабоч")))
        or ("оплат" in text and any(marker in text for marker in ("после", "подписания акта", "документа о приемке", "документа о приёмке")))
    ):
        return ["payment_terms"]
    if topic == "advance" and "аванс" in text:
        return ["advance"]
    if topic == "retentions" and any(marker in text for marker in ("удерж", "неустоек из суммы", "из суммы, подлежащей оплате")):
        return ["retentions"]
    if topic == "contract_security" and any(marker in text for marker in ("обеспечение исполнения", "независимая гарантия")):
        return ["contract_security"]
    if topic == "warranty" and any(marker in text for marker in ("гарантия качества", "гарантийн", "гарантия")):
        return ["warranty"]
    if topic == "participant_requirements" and any(marker in text for marker in ("статья 31", "единые требования", "участник закупки")):
        return ["participant_requirements"]
    if topic == "certificates_closing_docs" and any(
        marker in text
        for marker in (
            "сертификат",
            "деклараци",
            "паспорт качества",
            "регистрационное удостоверение",
            "certificate",
            "declaration",
            "quality passport",
        )
    ):
        return ["certificates_closing_docs"]
    if topic == "penalties" and any(marker in text for marker in ("штраф", "пени", "пеня", "неустойк", "просрочк")):
        return ["penalties"]
    if topic == "edi_pik" and any(marker in text for marker in ("пик", "эдо", "документ о приемке", "документ о приёмке")):
        return ["edi_pik"]
    return []


def _tender_identity_match(text: str, tender: dict[str, Any]) -> dict[str, Any]:
    tender_title = _text(tender.get("title"))
    document_subject = _extract_subject(text)
    if not tender_title or not document_subject:
        status = "unknown"
    else:
        tender_tokens = _identity_tokens(tender_title)
        subject_tokens = _identity_tokens(document_subject)
        overlap = sorted(tender_tokens & subject_tokens)
        status = "match" if overlap or not subject_tokens or not tender_tokens else "mismatch"
    return {
        "subject": {
            "status": status,
            "tender_title": tender_title,
            "document_subject": document_subject,
            "overlap_tokens": overlap if tender_title and document_subject else [],
        }
    }


def _extract_subject(text: str) -> str:
    compact = _compact(text[:8000])
    pattern = (
        r"(?:Наименование объекта закупки|Предмет контракта|Предмет договора)\s*[:\-]\s*"
        r"(.{5,180}?)(?:[.;]\s|$|\s\d+\.\s| Код\s)"
    )
    match = re.search(pattern, compact, flags=re.IGNORECASE)
    return _compact(match.group(1)).strip(" .:;") if match else ""


def _identity_tokens(value: str) -> set[str]:
    tokens = set(re.findall(r"[а-яёa-z0-9]{4,}", _normalized(value)))
    return {token for token in tokens if token not in STOP_TOKENS}


def _attach_duplicate_groups(documents: list[dict[str, Any]]) -> None:
    groups: dict[str, list[dict[str, Any]]] = {}
    for document in documents:
        text_hash = _text(document.get("text_hash"))
        if text_hash:
            groups.setdefault(text_hash, []).append(document)
    duplicate_index = 1
    for grouped_documents in groups.values():
        if len(grouped_documents) < 2:
            continue
        group_id = f"duplicate:{duplicate_index}"
        duplicate_index += 1
        for document in grouped_documents:
            document["duplicate_group_id"] = group_id


def _duplicate_groups_count(documents: list[dict[str, Any]]) -> int:
    return len({document.get("duplicate_group_id") for document in documents if document.get("duplicate_group_id")})


def _expected_missing_reasons(documents: list[dict[str, Any]]) -> list[str]:
    reasons: list[str] = []
    if any(document.get("document_role") == "unsupported_primary" for document in documents):
        reasons.append("missing_because_primary_doc_unread")
    all_topics = {item.get("topic") for document in documents for item in document.get("section_taxonomy", [])}
    for topic in ("payment_terms", "acceptance_documents", "delivery_schedule"):
        if topic not in all_topics:
            reasons.append(f"missing_because_no_section:{topic}")
    return reasons


def _topic_coverage(documents: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    coverage: dict[str, dict[str, Any]] = {}
    for document in documents:
        for section in document.get("section_taxonomy", []):
            topic = _text(section.get("topic"))
            if not topic:
                continue
            item = coverage.setdefault(topic, {"documents": [], "count": 0})
            item["count"] += 1
            item["documents"].append(document["name"])
    return coverage


def _cross_document_links(documents: list[dict[str, Any]]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    targets = [
        document
        for document in documents
        if document.get("document_role") in {"technical_spec", "technical_spec_appendix", "pik_obligations_payment"}
    ]
    for source in documents:
        if source.get("document_role") != "contract_project":
            continue
        for target in targets[:6]:
            if source["id"] == target["id"]:
                continue
            links.append(
                {
                    "source_document_id": source["id"],
                    "target_document_id": target["id"],
                    "relation": "contract_references_appendix",
                    "reason": "Контрактные условия обычно раскрываются в приложениях и ПИК.",
                }
            )
    return links


def _tender_identity(tender: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "source": _text(tender.get("source")),
        "external_id": _text(tender.get("external_id")),
        "title": _text(tender.get("title")),
        "customer": _text(tender.get("customer")),
        "items_count": len(items),
    }


def _text_quality(document: dict[str, Any], text: str) -> dict[str, Any]:
    status = _text(document.get("text_status")).casefold()
    compact = _compact(text)
    if status not in {"ok", "ready"}:
        quality = "extraction_error" if status == "error" else "not_ready"
    elif not compact:
        quality = "empty"
    elif _looks_noisy(compact):
        quality = "noisy"
    else:
        quality = "ok"
    return {
        "status": quality,
        "text_status": status or "pending",
        "chars": len(compact),
        "text_error": _text(document.get("text_error")),
    }


def _looks_noisy(text: str) -> bool:
    if "пїЅ" in text.casefold():
        return True
    if len(text) < 40:
        return False
    letters_digits = sum(1 for char in text if char.isalnum())
    return letters_digits / max(len(text), 1) < 0.45


def _archive_entries(document: dict[str, Any], text: str) -> list[str]:
    raw_entries = []
    raw_payload = document.get("raw_payload") if isinstance(document.get("raw_payload"), dict) else {}
    for key in ("archive_entries", "files"):
        value = raw_payload.get(key)
        if isinstance(value, list):
            raw_entries.extend(_text(item) for item in value)
    if raw_entries:
        return _unique_texts(raw_entries)
    if ".zip" not in _text(document.get("name")).casefold():
        return []
    entries = re.findall(r"([^\n\r]{4,120}\.(?:docx?|xlsx?|pdf|html))", text, flags=re.IGNORECASE)
    return _unique_texts(entries[:12])


def _revision_group_id(document: dict[str, Any]) -> str:
    name = _normalized(_text(document.get("name") or document.get("url")))
    name = re.sub(r"сост\.\s*\d{2}\.\d{2}\.\d{4}", "", name)
    name = re.sub(r"\b\d{4}[_-]\d{2}[_-]\d{2}[^.\s]*", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return f"revision:{_sha1(name)[:10]}" if name else ""


def _role_confidence(role: str, role_evidence: list[str]) -> str:
    if role == "unsupported_primary":
        return "high"
    if role_evidence:
        return "high"
    if role == "other":
        return "low"
    return "medium"


def _document_name(document: dict[str, Any], index: int) -> str:
    return _text(document.get("name") or document.get("url")) or f"Документ {index}"


def _first_evidence(text: str, markers: tuple[str, ...]) -> str:
    normalized = _normalized(text)
    for marker in markers:
        position = normalized.find(marker)
        if position >= 0:
            return _short(text[max(0, position - 120) : position + 320], 320)
    return _short(text, 320)


def _paragraphs(text: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"(?:\n{2,}|\f|(?<=\.)\s+)", text) if part.strip()]
    if not parts:
        return [text]
    return [_compact(part) for part in parts]


def _short(value: Any, limit: int) -> str:
    text = _compact(_text(value))
    if len(text) <= limit:
        return text
    return f"{text[: max(0, limit - 1)].rstrip()}…"


def _sha1(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def _unique_texts(values: Any) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _text(value)
        key = text.casefold()
        if not text or key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _normalized(value: Any) -> str:
    return _compact(_text(value)).casefold()


def _text(value: Any) -> str:
    if value in (None, ""):
        return ""
    return str(value).strip()
