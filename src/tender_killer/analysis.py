from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class TenderAnalysisResult:
    summary: str
    requirements: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)
    status: str = "needs_review"
    confidence: float = 0.1
    matches: dict[str, list[str]] = field(default_factory=dict)
    checklist: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("requirements", "сертификат/декларация", ("сертификат", "деклараци")),
    ("requirements", "паспорт качества", ("паспорт качества",)),
    ("requirements", "срок поставки", ("срок постав",)),
    ("requirements", "приемка через ЕИС", ("приемка", "еис")),
    ("requirements", "ГОСТ/ТУ", ("гост", "техническ")),
    ("requirements", "гарантия", ("гарантийн", "гарантия")),
    ("risks", "обеспечение исполнения контракта", ("обеспечение исполнения", "независимая гарантия")),
    ("risks", "штрафы/пени", ("штраф", "пеня", "пени")),
    ("risks", "короткий срок поставки", ("в течение 3", "в течение трех", "3 рабочих")),
    (
        "red_flags",
        "национальный режим/страна происхождения",
        ("1875", "национальный режим", "страна происхождения", "страну происхождения", "происхождения товара"),
    ),
    ("red_flags", "реестр российской продукции", ("реестр российской промышленной продукции", "ррпп", "рпп", "ерпт")),
    ("red_flags", "лицензия/СРО", ("лиценз", "сро")),
)

RULE_METADATA: dict[str, tuple[str, str]] = {
    "сертификат/декларация": ("documents", "medium"),
    "паспорт качества": ("documents", "medium"),
    "срок поставки": ("delivery", "medium"),
    "приемка через ЕИС": ("acceptance", "medium"),
    "ГОСТ/ТУ": ("standards", "medium"),
    "гарантия": ("contract", "medium"),
    "обеспечение исполнения контракта": ("financial", "high"),
    "штрафы/пени": ("financial", "medium"),
    "короткий срок поставки": ("delivery", "high"),
    "национальный режим/страна происхождения": ("national_regime", "high"),
    "реестр российской продукции": ("national_regime", "high"),
    "лицензия/СРО": ("legal", "high"),
}


def analyze_tender_texts(texts: list[str]) -> TenderAnalysisResult:
    text = _clean_text("\n".join(texts))
    if not text:
        return TenderAnalysisResult(
            summary="Текст документов не извлечен или пустой.",
            red_flags=["нет текста для анализа"],
            matches={"missing_text": []},
        )

    lower_text = text.lower()
    requirements: list[str] = []
    risks: list[str] = []
    red_flags: list[str] = []
    matches: dict[str, list[str]] = {}
    checklist: list[dict[str, str]] = []

    for bucket, label, needles in RULES:
        found = [needle for needle in needles if needle in lower_text]
        if not found:
            continue
        matches[label] = found
        _append_checklist_item(checklist, label, _evidence_for_needles(text, found))
        if bucket == "requirements":
            _append_unique(requirements, label)
        elif bucket == "risks":
            _append_unique(risks, label)
        elif bucket == "red_flags":
            _append_unique(red_flags, label)

    summary = _summary_from_text(text)
    confidence = _confidence(requirements, risks, red_flags)
    return TenderAnalysisResult(
        summary=summary,
        requirements=requirements,
        risks=risks,
        red_flags=red_flags,
        status="needs_review",
        confidence=confidence,
        matches=matches,
        checklist=checklist,
    )


def _summary_from_text(text: str) -> str:
    for pattern in (
        r"(?:техническое задание\s*:\s*)?((?:поставка|оказание|выполнение|приобретение)[^.]{8,180})",
        r"(?:предмет(?:ом)?\s+(?:контракта|закупки)[^:]*:\s*)([^.]{8,180})",
    ):
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _clean_text(match.group(1)).rstrip(".")
    first_sentence = re.split(r"[.!?]\s+", text, maxsplit=1)[0]
    return _clean_text(first_sentence[:220]).rstrip(".") or "Текст извлечен, но предмет закупки не найден явно."


def _confidence(requirements: list[str], risks: list[str], red_flags: list[str]) -> float:
    score = 0.3 + len(requirements) * 0.12 + len(risks) * 0.1 + len(red_flags) * 0.12
    return min(0.95, round(score, 2))


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _append_checklist_item(values: list[dict[str, str]], label: str, evidence: str) -> None:
    if any(item["label"] == label for item in values):
        return
    category, severity = RULE_METADATA.get(label, ("general", "medium"))
    values.append(
        {
            "label": label,
            "category": category,
            "severity": severity,
            "evidence": evidence,
        }
    )


def _evidence_for_needles(text: str, needles: list[str]) -> str:
    lower_needles = [needle.casefold() for needle in needles]
    for sentence in _sentences(text):
        normalized = sentence.casefold()
        if any(needle in normalized for needle in lower_needles):
            return _trim(sentence, 260)
    return ""


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def _trim(value: str, limit: int) -> str:
    cleaned = _clean_text(value)
    return cleaned if len(cleaned) <= limit else f"{cleaned[:limit].rstrip()}..."
