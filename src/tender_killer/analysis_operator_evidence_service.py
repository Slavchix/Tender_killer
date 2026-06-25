from __future__ import annotations

import re
from typing import Any

from tender_killer.analysis_condition_groups_service import conflict_evidence_quality


def build_operator_source_binding(
    *,
    raw_item: dict[str, Any],
    source: str,
    source_label: str,
    source_context: str,
    fragment: str,
    needs_review: bool,
) -> dict[str, str]:
    raw_binding = raw_item.get("source_binding")
    if isinstance(raw_binding, dict) and raw_binding.get("level"):
        return {
            "level": _text(raw_binding.get("level")),
            "label": _text(raw_binding.get("label")),
            "detail": _text(raw_binding.get("detail")),
            "document_name": _text(raw_binding.get("document_name")) or source,
            "source_label": _text(raw_binding.get("source_label")) or source_label,
        }
    if needs_review:
        return {
            "level": "unbound",
            "label": "нужна ручная проверка",
            "detail": "Факт не удалось надежно связать с документом.",
            "document_name": source,
            "source_label": source_label,
        }
    if source and fragment:
        return {
            "level": "explicit",
            "label": "источник подтвержден",
            "detail": "Факт найден в документе и связан с фрагментом текста.",
            "document_name": source,
            "source_label": source_label,
        }
    if source or source_context:
        return {
            "level": "context",
            "label": "источник по контексту",
            "detail": "Факт связан с документом или контекстом, но требует быстрой сверки формулировки.",
            "document_name": source,
            "source_label": source_label,
        }
    return {
        "level": "inferred",
        "label": "вывод без источника",
        "detail": "Факт получен из анализа без точной документальной привязки.",
        "document_name": source,
        "source_label": source_label,
    }


def build_operator_confidence_level(
    raw_item: dict[str, Any],
    source_binding: dict[str, str],
    *,
    fragment: str,
    source_context: str,
) -> dict[str, str]:
    raw_level = raw_item.get("confidence_level")
    if isinstance(raw_level, dict) and raw_level.get("level"):
        return {
            "level": _text(raw_level.get("level")),
            "label": _text(raw_level.get("label")),
            "detail": _text(raw_level.get("detail")),
        }
    level = source_binding.get("level")
    if level == "unbound":
        return {
            "level": "low",
            "label": "уверенность низкая",
            "detail": "Нет надежной привязки к документу, нужна ручная проверка.",
        }
    if level == "explicit" and fragment and source_context:
        return {
            "level": "high",
            "label": "уверенность высокая",
            "detail": "Есть документ, фрагмент и контекст источника.",
        }
    if level in {"explicit", "context"}:
        return {
            "level": "medium",
            "label": "уверенность средняя",
            "detail": "Есть источник или контекст, но формулировку стоит сверить вручную.",
        }
    return {
        "level": "low",
        "label": "уверенность низкая",
        "detail": "Вывод сделан без точного источника.",
    }


def build_operator_evidence_quality(
    *,
    source_binding: dict[str, str],
    confidence_level: dict[str, str],
    conflict_flags: list[str],
    expected_missing: bool,
) -> dict[str, str]:
    if conflict_flags:
        return conflict_evidence_quality(conflict_flags)
    if expected_missing:
        return {
            "level": "missing",
            "label": "не найдено",
            "detail": "Точная формулировка не найдена в извлеченном тексте документов.",
        }
    binding_level = source_binding.get("level")
    confidence = confidence_level.get("level")
    if binding_level == "explicit" and confidence == "high":
        return {
            "level": "exact",
            "label": "точное доказательство",
            "detail": "Есть документ, фрагмент и контекст источника.",
        }
    if binding_level in {"explicit", "context"}:
        return {
            "level": "context",
            "label": "контекст источника",
            "detail": source_binding.get("detail") or "Факт связан с документом или контекстом и требует быстрой сверки.",
        }
    return {
        "level": "inferred",
        "label": "вывод без точного источника",
        "detail": source_binding.get("detail") or "Факт получен без точной документальной привязки.",
    }


def operator_evidence_text(*, label: str, value: str, fragment: str) -> str:
    for candidate in (fragment, value):
        if candidate and not _description_is_only_label(candidate, label):
            return candidate
    return ""


def operator_source_context(
    *,
    raw_context: str,
    source: str,
    evidence_text: str,
    impact: str,
) -> str:
    if raw_context:
        return raw_context
    if not source or not evidence_text or not impact:
        return ""
    return f"Почему важно: {_compact_text(impact, 190)}"


def operator_evidence_summary(*, source_label: str, evidence_text: str, impact: str) -> str:
    parts = []
    if source_label:
        parts.append(source_label)
    if evidence_text:
        parts.append(_compact_text(evidence_text, 180))
    if impact:
        parts.append(f"вывод: {_compact_text(impact, 180)}")
    return " · ".join(parts)


def source_label(source: str, page: int | None) -> str:
    if not source:
        return ""
    if page is None:
        return source
    return f"{source} · стр. {page}"


def source_page(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        page = int(value)
    except (TypeError, ValueError):
        return None
    return page if page > 0 else None


def _description_is_only_label(description: str, label: str) -> bool:
    return _dedupe_text(description) == _dedupe_text(label)


def _dedupe_text(value: Any) -> str:
    return re.sub(r"\s+", " ", _text(value)).strip().casefold()


def _compact_text(value: Any, limit: int) -> str:
    text = re.sub(r"\s+", " ", _text(value)).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip(" .,;:") + "…"


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()
