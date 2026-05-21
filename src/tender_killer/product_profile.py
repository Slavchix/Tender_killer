from __future__ import annotations

import re
from typing import Any


DEFAULT_STOP_WORDS = ["б/у", "уценка", "ремонт", "услуга"]


def build_product_profiles(tender: dict[str, Any]) -> list[dict[str, Any]]:
    items = tender.get("items") or []
    documents = _document_records(tender)
    text = _combined_text(tender)
    standards = _standards(text)
    cert_documents = _cert_documents(text)
    origin_country_requirements = _origin_country_requirements(text)
    profiles: list[dict[str, Any]] = []

    if items:
        for index, item in enumerate(items, start=1):
            product_name = _clean(item.get("name")) or _clean(tender.get("title")) or "Товар не указан"
            okpd2 = _clean(item.get("okpd2")) or _clean(tender.get("okpd2"))
            classifier_code, classifier_source = _item_classifier(item, tender)
            classifier_type = _clean(item.get("classifier_type")) or _classifier_type_for_code(classifier_code)
            details = _clean(item.get("details"))
            document_snippets = _document_requirement_snippets(
                product_name=product_name,
                details=details,
                documents=documents,
                single_item=len(items) == 1,
            )
            profiles.append(
                _profile(
                    tender=tender,
                    position_index=int(item.get("position_index") or index),
                    product_name=product_name,
                    details=details,
                    category=_clean(tender.get("category")),
                    okpd2=okpd2,
                    quantity=item.get("quantity"),
                    unit=_clean(item.get("unit")),
                    unit_price=item.get("unit_price"),
                    total_price=item.get("total_price"),
                    classifier_code=classifier_code,
                    classifier_type=classifier_type,
                    classifiers=_classifiers(classifier_code, classifier_type, okpd2, "tender_item"),
                    evidence=[
                        *_item_evidence(product_name, classifier_code, classifier_source, details),
                        *_document_evidence(document_snippets),
                    ],
                    required_characteristics=_characteristics(details, text, document_snippets),
                    standards=standards,
                    cert_documents=cert_documents,
                    origin_country_requirements=origin_country_requirements,
                    source="item",
                    profile_status="ready",
                    confidence=0.85,
                )
            )
        return profiles

    product_name = _clean(tender.get("title")) or "Товар не указан"
    classifier_code = _clean(tender.get("okpd2"))
    classifier_type = _classifier_type_for_code(classifier_code)
    document_snippets = _document_requirement_snippets(
        product_name=product_name,
        details=None,
        documents=documents,
        single_item=True,
    )
    profiles.append(
        _profile(
            tender=tender,
            position_index=1,
            product_name=product_name,
            details=None,
            category=_clean(tender.get("category")),
            okpd2=classifier_code,
            quantity=None,
            unit=None,
            unit_price=None,
            total_price=tender.get("price"),
            classifier_code=classifier_code,
            classifier_type=classifier_type,
            classifiers=_classifiers(classifier_code, classifier_type, classifier_code, "tender_card"),
            evidence=[*_fallback_evidence(product_name, classifier_code), *_document_evidence(document_snippets)],
            required_characteristics=_characteristics("", text, document_snippets),
            standards=standards,
            cert_documents=cert_documents,
            origin_country_requirements=origin_country_requirements,
            source="card",
            profile_status="needs_review",
            confidence=0.55,
        )
    )
    return profiles


def _profile(
    *,
    tender: dict[str, Any],
    position_index: int,
    product_name: str,
    details: str | None,
    category: str | None,
    okpd2: str | None,
    quantity: Any,
    unit: str | None,
    unit_price: Any,
    total_price: Any,
    classifier_code: str | None,
    classifier_type: str | None,
    classifiers: list[dict[str, str]],
    evidence: list[dict[str, str]],
    required_characteristics: list[str],
    standards: list[str],
    cert_documents: list[str],
    origin_country_requirements: list[str],
    source: str,
    profile_status: str,
    confidence: float,
) -> dict[str, Any]:
    return {
        "tender_source": _clean(tender.get("source")) or _clean(tender.get("tender_source")),
        "tender_external_id": _clean(tender.get("external_id")) or _clean(tender.get("tender_external_id")),
        "position_index": position_index,
        "product_name": product_name,
        "normalized_name": _normalize_name(product_name),
        "details": details,
        "category": category,
        "okpd2": okpd2,
        "quantity": quantity,
        "unit": unit,
        "unit_price": unit_price,
        "total_price": total_price,
        "classifier_code": classifier_code,
        "classifier_type": classifier_type,
        "classifiers": classifiers,
        "required_characteristics": required_characteristics,
        "standards": standards,
        "cert_documents": cert_documents,
        "brand_model": [],
        "origin_country_requirements": origin_country_requirements,
        "search_phrases": _search_phrases(product_name, details, okpd2, classifier_code),
        "stop_words": list(DEFAULT_STOP_WORDS),
        "evidence": evidence,
        "profile_status": profile_status,
        "confidence": confidence,
        "source": source,
        "raw_payload": {},
    }


def _search_phrases(
    product_name: str,
    details: str | None,
    okpd2: str | None,
    classifier_code: str | None,
) -> list[str]:
    phrases = [product_name, details]
    if okpd2:
        phrases.append(f"{product_name} {okpd2}")
    if classifier_code:
        phrases.append(f"{product_name} {classifier_code}")
    return _unique(phrases)


def _normalize_name(product_name: str) -> str:
    return product_name.casefold()


def _classifiers(
    classifier_code: str | None,
    classifier_type: str | None,
    okpd2: str | None,
    source: str,
) -> list[dict[str, str]]:
    classifiers: list[dict[str, str]] = []
    if classifier_code:
        classifiers.append(
            {
                "type": _classifier_type_value(classifier_type),
                "code": classifier_code,
                "source": source,
            }
        )
    if okpd2 and okpd2 != classifier_code:
        classifiers.append({"type": "okpd2", "code": okpd2, "source": source})
    return classifiers


def _item_classifier(item: dict[str, Any], tender: dict[str, Any]) -> tuple[str | None, str | None]:
    classifier_code = _clean(item.get("classifier_code"))
    if classifier_code:
        return classifier_code, "tender_item.classifier_code"
    classifier_code = _clean(item.get("okpd2"))
    if classifier_code:
        return classifier_code, "tender_item.okpd2"
    classifier_code = _clean(tender.get("okpd2"))
    if classifier_code:
        return classifier_code, "tender.okpd2"
    return None, None


def _item_evidence(
    product_name: str,
    classifier_code: str | None,
    classifier_source: str | None,
    details: str | None,
) -> list[dict[str, str]]:
    evidence = [{"field": "product_name", "source": "tender_item.name", "value": product_name}]
    if classifier_code and classifier_source:
        evidence.append({"field": "classifier", "source": classifier_source, "value": classifier_code})
    if details:
        evidence.append({"field": "details", "source": "tender_item.details", "value": details})
    return evidence


def _fallback_evidence(product_name: str, classifier_code: str | None) -> list[dict[str, str]]:
    evidence = [{"field": "product_name", "source": "tender.title", "value": product_name}]
    if classifier_code:
        evidence.append({"field": "classifier", "source": "tender.okpd2", "value": classifier_code})
    return evidence


def _classifier_type_value(classifier_type: str | None) -> str:
    if not classifier_type:
        return "unknown"
    normalized = classifier_type.casefold().replace(" ", "").replace("-", "")
    if normalized in {"окпд2", "okpd2"}:
        return "okpd2"
    if normalized in {"коз2", "koz2"}:
        return "koz2"
    return classifier_type


def _classifier_type_for_code(code: str | None) -> str | None:
    if not code:
        return None
    parts = code.split(".")
    if len(parts) > 4:
        return "КОЗ-2"
    return "ОКПД2"


def _characteristics(details: str | None, text: str, document_snippets: list[dict[str, str]] | None = None) -> list[str]:
    values: list[str] = []
    if details:
        values.append(details)
    for snippet in document_snippets or []:
        values.append(snippet.get("value"))
    lower = text.casefold()
    if "гост" in lower:
        values.append("ГОСТ")
    if "сертификат" in lower:
        values.append("сертификат соответствия")
    if "деклараци" in lower:
        values.append("декларация соответствия")
    if "страна происхождения" in lower:
        values.append("страна происхождения")
    for match in re.findall(
        r"(?:белизн[а-я\s]*?\d+\s*CIE|плотност[а-я\s]*?\d+\s*г/м2|формат\s*[AА]\d)",
        text,
        flags=re.IGNORECASE,
    ):
        values.append(_clean(match))
    return _unique(values)


def _document_requirement_snippets(
    *,
    product_name: str,
    details: str | None,
    documents: list[dict[str, str]],
    single_item: bool,
) -> list[dict[str, str]]:
    tokens = _requirement_tokens(product_name, details)
    values: list[dict[str, str]] = []
    for document in documents:
        for sentence in _sentences(document["text"]):
            normalized = sentence.casefold()
            token_match = any(token in normalized for token in tokens)
            risk_match = single_item and _looks_like_requirement(normalized)
            if not token_match and not risk_match:
                continue
            value = _clean(sentence)
            if not value:
                continue
            values.append({"source": document["name"], "value": _trim(value, 260)})
            if len(values) >= 8:
                return _unique_snippets(values)
    return _unique_snippets(values)


def _document_evidence(snippets: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {"field": "document_requirement", "source": snippet["source"], "value": snippet["value"]}
        for snippet in snippets
    ]


def _document_records(tender: dict[str, Any]) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for index, document in enumerate(tender.get("document_records") or [], start=1):
        if not isinstance(document, dict):
            continue
        text = _clean(document.get("text_content"))
        if not text:
            continue
        name = _clean(document.get("name")) or f"document_{index}"
        records.append({"name": name, "text": text})
    return records


def _requirement_tokens(product_name: str, details: str | None) -> list[str]:
    source = f"{product_name} {details or ''}"
    ignored = {"для", "или", "при", "под", "над", "без", "поставка", "товар", "работ", "услуг"}
    tokens = [
        token
        for token in re.findall(r"[A-Za-zА-Яа-яЁё0-9]{4,}", source.casefold())
        if token not in ignored
    ]
    return _unique(tokens)


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]


def _looks_like_requirement(value: str) -> bool:
    markers = (
        "должен",
        "должна",
        "соответств",
        "сертификат",
        "деклараци",
        "гост",
        "ту ",
        "срок поставки",
        "страна происхождения",
        "качества",
    )
    return any(marker in value for marker in markers)


def _unique_snippets(values: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    result: list[dict[str, str]] = []
    for value in values:
        key = (value["source"], value["value"])
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def _trim(value: str, limit: int) -> str:
    return value if len(value) <= limit else f"{value[:limit].rstrip()}..."


def _standards(text: str) -> list[str]:
    values: list[str] = []
    patterns = [
        r"\bГОСТ(?:\s+[А-ЯA-Z])?(?:\s+\d+(?:[-/]\d+)*)?",
        r"\bТУ\s+\d+(?:[-/]\d+)*",
        r"\bТР\s+ТС\s+\d+/\d+",
        r"\bТР\s+ЕАЭС\s+\d+/\d+",
    ]
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            values.append(_clean(match))
    return _unique(values)


def _cert_documents(text: str) -> list[str]:
    lower = text.casefold()
    values: list[str] = []
    if "сертификат соответствия" in lower:
        values.append("сертификат соответствия")
    if "декларация соответствия" in lower:
        values.append("декларация соответствия")
    if "регистрационное удостоверение" in lower:
        values.append("регистрационное удостоверение")
    if re.search(r"\bсгр\b", text, flags=re.IGNORECASE):
        values.append("СГР")
    return values


def _origin_country_requirements(text: str) -> list[str]:
    lower = text.casefold()
    values: list[str] = []
    if "страна происхождения" in lower:
        values.append("страна происхождения")
    if "российский товар" in lower:
        values.append("российский товар")
    return values


def _combined_text(tender: dict[str, Any]) -> str:
    parts: list[str] = []
    analysis = tender.get("analysis") or {}
    if isinstance(analysis, dict):
        parts.append(str(analysis.get("summary") or ""))
    for document in tender.get("document_records") or []:
        if isinstance(document, dict):
            parts.append(str(document.get("text_content") or ""))
    return "\n".join(parts)


def _clean(value: Any) -> str | None:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or None


def _unique(values: list[str | None]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result
