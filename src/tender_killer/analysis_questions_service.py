from __future__ import annotations

import re
from typing import Any


QUESTION_SPECS: tuple[dict[str, str], ...] = (
    {
        "id": "advance",
        "question": "Есть ли аванс?",
        "missing": "В документах не найден подтвержденный фрагмент про аванс.",
    },
    {
        "id": "payment_documents",
        "question": "Какие документы нужны для оплаты?",
        "missing": "В документах не найден подтвержденный фрагмент про документы для оплаты.",
    },
    {
        "id": "participation_blockers",
        "question": "Что может помешать участию?",
        "missing": "Явные блокеры участия с подтвержденным фрагментом не найдены.",
    },
    {
        "id": "acceptance_source",
        "question": "Где сказано про приемку?",
        "missing": "В документах не найден подтвержденный фрагмент про приемку.",
    },
)


def build_analysis_ai_questions(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Build deterministic source-bound answers over the fact layer."""
    return {
        "version": 1,
        "items": [_answer_question(spec, items) for spec in QUESTION_SPECS],
    }


def _answer_question(spec: dict[str, str], items: list[dict[str, Any]]) -> dict[str, Any]:
    matched_items = sorted(
        [item for item in items if _matches_question(spec["id"], item)],
        key=lambda item: _question_rank(spec["id"], item),
    )
    sources = [source for source in (_source_answer_item(item) for item in matched_items) if source]
    if not sources:
        return {
            "id": spec["id"],
            "question": spec["question"],
            "answer": spec["missing"],
            "answer_status": "not_found",
            "sources": [],
        }

    first = sources[0]
    return {
        "id": spec["id"],
        "question": spec["question"],
        "answer": _answer_text(spec["id"], sources),
        "answer_status": "found",
        "sources": sources[:3],
        "source_label": first.get("source_label", ""),
        "fragment": first.get("fragment", ""),
    }


def _matches_question(question_id: str, item: dict[str, Any]) -> bool:
    text = _normalized(" ".join(_text(item.get(key)) for key in ("label", "value", "fragment")))
    category = _text(item.get("category"))
    if question_id == "advance":
        return any(marker in text for marker in ("аванс", "advance", "prepayment"))
    if question_id == "payment_documents":
        document_markers = (
            "upd",
            "упд",
            "closing document",
            "закрывающ",
            "acceptance act",
            "акт прием",
            "акт приём",
        )
        if any(marker in text for marker in ("аванс", "advance", "prepayment")) and not any(
            marker in text for marker in document_markers
        ):
            return False
        return (
            category == "payment"
            or any(
                marker in text
                for marker in ("оплат", "payment", *document_markers)
            )
        )
    if question_id == "participation_blockers":
        return bool(
            item.get("is_blocker")
            or item.get("conflict_flags")
            or item.get("needs_review")
            or _text(item.get("severity")) == "high"
        )
    if question_id == "acceptance_source":
        return category == "acceptance" or any(
            marker in text
            for marker in ("прием", "приём", "acceptance", "signed acceptance act", "акт")
        )
    return False


def _source_answer_item(item: dict[str, Any]) -> dict[str, Any] | None:
    fragment = _text(item.get("fragment") or item.get("source_context"))
    source_label = _text(item.get("source_label") or item.get("document_name") or item.get("source"))
    if not fragment or not source_label:
        return None
    return {
        "fact_id": _text(item.get("id")),
        "label": _text(item.get("label")),
        "source_label": source_label,
        "document_name": _text(item.get("document_name") or item.get("source")),
        "fragment": fragment,
    }


def _question_rank(question_id: str, item: dict[str, Any]) -> tuple[int, str]:
    text = _normalized(" ".join(_text(item.get(key)) for key in ("label", "value", "fragment")))
    category = _text(item.get("category"))
    if question_id == "payment_documents":
        if category == "payment":
            return (0, _text(item.get("label")))
        if any(marker in text for marker in ("upd", "упд", "закрывающ", "closing document")):
            return (1, _text(item.get("label")))
        return (2, _text(item.get("label")))
    if question_id == "acceptance_source":
        return (0 if category == "acceptance" else 1, _text(item.get("label")))
    if question_id == "participation_blockers":
        return (0 if item.get("is_blocker") else 1, _text(item.get("label")))
    return (0, _text(item.get("label")))


def _answer_text(question_id: str, sources: list[dict[str, Any]]) -> str:
    fragments = [_compact(source.get("fragment"), 140) for source in sources if source.get("fragment")]
    if question_id == "participation_blockers":
        labels = [source.get("label") for source in sources if source.get("label")]
        return "Нужно проверить: " + "; ".join(_unique(labels or fragments)[:3])
    return fragments[0] if fragments else "Найдено, но требуется сверка фрагмента."


def _unique(values: list[Any]) -> list[str]:
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


def _compact(value: Any, limit: int) -> str:
    text = re.sub(r"\s+", " ", _text(value)).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip(" .,;:") + "..."


def _normalized(value: Any) -> str:
    return re.sub(r"\s+", " ", _text(value)).strip().casefold()


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()
