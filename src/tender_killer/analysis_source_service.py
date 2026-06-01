from __future__ import annotations

import re
from typing import Any


def attach_document_sources(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> None:
    for collection_name in ("checklist", "execution_terms"):
        collection = analysis.get(collection_name)
        if not isinstance(collection, list):
            continue
        for item in collection:
            if not isinstance(item, dict):
                continue
            fragment = str(item.get("evidence") or item.get("value") or "").strip()
            source = document_source_for_fragment(fragment, documents)
            if not source:
                continue
            item.setdefault("document_name", source["document_name"])
            item.setdefault("source", source["document_name"])
            item.setdefault("source_label", source["source_label"])
            item.setdefault("source_context", source["source_context"])
            if source.get("source_page") is not None:
                item.setdefault("source_page", source["source_page"])


def document_source_for_fragment(fragment: str, documents: list[dict[str, Any]]) -> dict[str, Any]:
    needle = _normalized_text(fragment)
    if not needle:
        return {}
    for document in documents:
        document_name = str(document.get("name") or document.get("url") or "").strip()
        for page_number, page_text in _document_pages(str(document.get("text_content") or "")):
            haystack = _normalized_text(page_text)
            if needle not in haystack:
                continue
            return {
                "document_name": document_name,
                "source": document_name,
                "source_page": page_number,
                "source_label": _source_label(document_name, page_number),
                "source_context": _source_context(fragment, page_text),
            }
    return {}


def _document_pages(text: str) -> list[tuple[int | None, str]]:
    if "\f" not in text:
        return [(None, text)]
    return [(index + 1, page_text) for index, page_text in enumerate(text.split("\f")) if page_text.strip()]


def _source_label(document_name: str, page_number: int | None) -> str:
    if page_number is None:
        return f"{document_name} · стр. не определена" if document_name else "Документ не привязан"
    return f"{document_name} · стр. {page_number}" if document_name else f"стр. {page_number}"


def _source_context(fragment: str, page_text: str) -> str:
    compact_page = re.sub(r"\s+", " ", page_text).strip()
    if not compact_page:
        return ""
    needle = _normalized_text(fragment)
    haystack = _normalized_text(compact_page)
    index = haystack.find(needle)
    if index < 0:
        return _trim_context(compact_page, 520)

    start = max(0, index - 180)
    end = min(len(compact_page), index + len(needle) + 220)
    return _trim_context(compact_page[start:end], 520, prefix=start > 0, suffix=end < len(compact_page))


def _trim_context(value: str, limit: int, *, prefix: bool = False, suffix: bool = False) -> str:
    text = value.strip()
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
        suffix = False
    if prefix:
        text = f"…{text}"
    if suffix:
        text = f"{text}…"
    return text


def _normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()
