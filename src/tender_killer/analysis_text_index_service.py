from __future__ import annotations

import re
from typing import Any


MAX_CHUNKS_PER_DOCUMENT = 120
MAX_CHUNK_CHARS = 900
ATTENTION_QUALITY_STATUSES = {"empty", "noisy", "extraction_error"}

ROLE_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "technical_specification",
        (
            "описание объекта",
            "техническое задание",
            "тз",
            "technical specification",
            "specification",
        ),
    ),
    (
        "contract",
        (
            "проект контракта",
            "контракт",
            "договор",
            "contract",
        ),
    ),
    (
        "participant_requirements",
        (
            "participant requirements",
            "requirements for participant",
            "единые требования",
            "требования к участнику",
            "требования участников",
            "ст. 31",
            "ст 31",
            "44-фз",
        ),
    ),
    (
        "nmck",
        (
            "нмцк",
            "обоснование",
            "расчет",
            "расчёт",
            "начальная максимальная",
            "price calculation",
        ),
    ),
)


def build_analysis_text_index(documents: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Build a compact document index for explainable Analysis/TZ facts."""
    indexed_documents = [_indexed_document(index, document) for index, document in enumerate(documents or [], start=1)]
    chunks_count = sum(document["quality"]["chunks"] for document in indexed_documents)
    attention_count = sum(
        1
        for document in indexed_documents
        if document["quality"]["status"] in ATTENTION_QUALITY_STATUSES
    )
    return {
        "version": 1,
        "metrics": {
            "documents": len(indexed_documents),
            "chunks": chunks_count,
            "attention": attention_count,
        },
        "documents": indexed_documents,
    }


def document_roles_from_text_index(text_index: dict[str, Any] | None) -> dict[str, str]:
    if not isinstance(text_index, dict):
        return {}
    roles: dict[str, str] = {}
    for document in text_index.get("documents") if isinstance(text_index.get("documents"), list) else []:
        if not isinstance(document, dict):
            continue
        name = _text(document.get("name"))
        role = _text(document.get("document_role"))
        if name and role:
            roles[name] = role
    return roles


def infer_document_role(document: dict[str, Any] | None) -> str:
    document = document or {}
    identity = " ".join(
        part
        for part in (
            _text(document.get("document_type")),
            _text(document.get("name")),
            _text(document.get("url")),
        )
        if part
    ).casefold()
    for role, markers in ROLE_MARKERS:
        if any(marker in identity for marker in markers):
            return role
    text_preview = _normalized_text(_text(document.get("text_content")))[:1200]
    for role, markers in ROLE_MARKERS:
        if any(marker in text_preview for marker in markers):
            return role
    return "other"


def _indexed_document(index: int, document: dict[str, Any]) -> dict[str, Any]:
    name = _text(document.get("name") or document.get("url")) or f"Документ {index}"
    text = _text(document.get("text_content"))
    pages = _document_pages(text)
    chunks: list[dict[str, Any]] = []
    sections_by_key: dict[tuple[str, int | None], dict[str, Any]] = {}

    for page_number, page_text in pages:
        section_title = ""
        for paragraph in _paragraphs(page_text):
            heading = _heading(paragraph)
            if heading:
                section_title = heading
                _section(sections_by_key, section_title, page_number)
                remaining = paragraph[len(heading) :].strip(" .:-\n\t")
                if not remaining:
                    continue
                paragraph = remaining

            for chunk_text in _split_chunk_text(paragraph):
                if len(chunks) >= MAX_CHUNKS_PER_DOCUMENT:
                    break
                chunk_id = f"d{index}:p{page_number or 0}:c{len(chunks) + 1}"
                chunk = {
                    "id": chunk_id,
                    "page": page_number,
                    "section": section_title,
                    "kind": _chunk_kind(chunk_text),
                    "text": chunk_text,
                }
                chunks.append(chunk)
                if section_title:
                    _section(sections_by_key, section_title, page_number)["chunk_ids"].append(chunk_id)
            if len(chunks) >= MAX_CHUNKS_PER_DOCUMENT:
                break

    return {
        "name": name,
        "document_type": _text(document.get("document_type")),
        "document_role": infer_document_role(document),
        "quality": _quality(document, text, pages_count=len(pages), chunks_count=len(chunks)),
        "sections": list(sections_by_key.values()),
        "chunks": chunks,
    }


def _document_pages(text: str) -> list[tuple[int | None, str]]:
    if not text.strip():
        return []
    if "\f" not in text:
        return [(1, text)]
    return [(index + 1, page_text) for index, page_text in enumerate(text.split("\f")) if page_text.strip()]


def _paragraphs(page_text: str) -> list[str]:
    lines = [line.strip() for line in page_text.replace("\r", "\n").split("\n")]
    paragraphs: list[str] = []
    buffer: list[str] = []
    for line in lines:
        if not line:
            if buffer:
                paragraphs.append(" ".join(buffer).strip())
                buffer = []
            continue
        heading = _heading(line)
        if heading and heading == line.strip(" ."):
            paragraphs.append(" ".join(buffer).strip())
            paragraphs.append(line)
            buffer = []
            continue
        if heading and buffer:
            paragraphs.append(" ".join(buffer).strip())
            buffer = [line]
            continue
        buffer.append(line)
    if buffer:
        paragraphs.append(" ".join(buffer).strip())
    if not paragraphs:
        compact = _compact(page_text)
        return [compact] if compact else []
    return [paragraph for paragraph in paragraphs if paragraph]


def _split_chunk_text(text: str) -> list[str]:
    compact = _compact(text)
    if not compact:
        return []
    if len(compact) <= MAX_CHUNK_CHARS:
        return [compact]

    chunks: list[str] = []
    current = ""
    for sentence in re.split(r"(?<=[.!?;:])\s+", compact):
        if not sentence:
            continue
        if current and len(current) + len(sentence) + 1 > MAX_CHUNK_CHARS:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks or [compact[:MAX_CHUNK_CHARS].rstrip()]


def _heading(paragraph: str) -> str:
    text = paragraph.strip()
    if not text:
        return ""
    for title in (
        "Техническое задание",
        "Описание объекта закупки",
        "Проект контракта",
        "Единые требования",
        "Требования к участникам",
        "НМЦК",
    ):
        if text.casefold().startswith(title.casefold()):
            return title
    patterns = (
        r"^(Раздел\s+\d+(?:[.\d]*)?\.?\s+[^\n]{3,90})",
        r"^(\d+(?:\.\d+)*\.?\s+[А-ЯЁA-Z][^\n]{3,90})",
    )
    for pattern in patterns:
        match = re.match(pattern, text)
        if match:
            return match.group(1).strip(" .")
    return ""


def _section(
    sections_by_key: dict[tuple[str, int | None], dict[str, Any]],
    title: str,
    page_number: int | None,
) -> dict[str, Any]:
    key = (title, page_number)
    if key not in sections_by_key:
        sections_by_key[key] = {"title": title, "page": page_number, "chunk_ids": []}
    return sections_by_key[key]


def _chunk_kind(text: str) -> str:
    if "\t" in text or "|" in text:
        return "table"
    return "paragraph"


def _quality(
    document: dict[str, Any],
    text: str,
    *,
    pages_count: int,
    chunks_count: int,
) -> dict[str, Any]:
    compact = _compact(text)
    raw_status = _text(document.get("text_status")).casefold()
    if raw_status and raw_status not in {"ok", "ready"}:
        status = "extraction_error" if raw_status == "error" else "empty"
    elif not compact:
        status = "empty"
    elif _looks_noisy(compact):
        status = "noisy"
    elif len(compact) < 80:
        status = "short"
    else:
        status = "ok"
    return {
        "status": status,
        "chars": len(compact),
        "pages": pages_count,
        "chunks": chunks_count,
    }


def _looks_noisy(text: str) -> bool:
    if "�" in text:
        return True
    if len(text) < 40:
        return False
    letters_digits = sum(1 for char in text if char.isalnum())
    return letters_digits / max(len(text), 1) < 0.45


def _compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _normalized_text(value: str) -> str:
    return _compact(value).casefold()


def _text(value: Any) -> str:
    if value in (None, ""):
        return ""
    return str(value).strip()
