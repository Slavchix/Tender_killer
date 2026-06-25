from __future__ import annotations

import re
from typing import Any

from tender_killer.analysis_types import OperatorItem


def build_context_operator_items(context_pack: Any) -> list[OperatorItem]:
    if not isinstance(context_pack, dict) or context_pack.get("version") != 1:
        return []
    items: list[OperatorItem] = []
    for document in context_pack.get("documents") if isinstance(context_pack.get("documents"), list) else []:
        if not isinstance(document, dict):
            continue
        items.extend(_context_document_items(document))
    return items


def _context_document_items(document: dict[str, Any]) -> list[OperatorItem]:
    result: list[OperatorItem] = []
    name = _text(document.get("name"))
    if "subject_mismatch" in _text_list(document.get("mismatch_flags")):
        subject = document.get("tender_identity_match") if isinstance(document.get("tender_identity_match"), dict) else {}
        subject_info = subject.get("subject") if isinstance(subject.get("subject"), dict) else {}
        tender_title = _text(subject_info.get("tender_title"))
        document_subject = _text(subject_info.get("document_subject"))
        fragment = _context_subject_mismatch_fragment(tender_title, document_subject)
        result.append(
            {
                "id": f"context:{_slug(name)}:subject_mismatch",
                "kind": "risk",
                "type": "risk",
                "label": "Документ не совпадает с карточкой закупки",
                "value": fragment,
                "description": (
                    "В документах найден предмет, который отличается от карточки закупки. "
                    "Такой документ нельзя использовать как подтвержденный источник без ручной проверки."
                ),
                "category": "legal",
                "severity": "high",
                "document_name": name,
                "source": name,
                "source_label": name,
                "fragment": fragment,
                "source_context": fragment,
                "operator_action": "Проверить релевантность документа и не использовать его условия без подтверждения.",
                "price_impact": "manual_review",
                "priority": 98,
                "needs_review": True,
                "is_blocker": True,
                "is_price_factor": False,
            }
        )
    if _text(document.get("document_role")) == "unsupported_primary":
        quality = document.get("text_quality") if isinstance(document.get("text_quality"), dict) else {}
        reason = _text(quality.get("text_error")) or _text(quality.get("status")) or "текст не извлечен"
        result.append(
            {
                "id": f"context:{_slug(name)}:unsupported_primary",
                "kind": "requirement",
                "type": "requirement",
                "label": "Главный документ ТЗ не прочитан",
                "value": reason,
                "description": "Один из главных документов закупки не прочитан, поэтому условия нельзя считать полными.",
                "category": "documents",
                "severity": "medium",
                "document_name": name,
                "source": name,
                "source_label": name,
                "fragment": reason,
                "source_context": reason,
                "operator_action": "Открыть документ вручную или повторить извлечение текста перед решением по заявке.",
                "price_impact": "documents",
                "priority": 82,
                "needs_review": True,
                "expected_missing": True,
                "is_blocker": False,
                "is_price_factor": False,
            }
        )
    return result


def _context_subject_mismatch_fragment(tender_title: str, document_subject: str) -> str:
    if tender_title and document_subject:
        return f"В карточке: {tender_title}. В документе: {document_subject}."
    if document_subject:
        return f"В документе найден другой предмет: {document_subject}."
    return "Документ не совпадает с карточкой закупки."


def _text_list(value: Any) -> list[str]:
    values = value if isinstance(value, list) else [value]
    return [_text(item) for item in values if _text(item)]


def _slug(value: str) -> str:
    normalized = re.sub(r"\s+", "-", value.strip().casefold())
    normalized = re.sub(r"[^0-9a-zа-яё_-]+", "", normalized)
    return normalized or "item"


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()
