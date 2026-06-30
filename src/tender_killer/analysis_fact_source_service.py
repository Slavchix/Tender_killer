from __future__ import annotations

from typing import Any

from tender_killer.analysis_source_service import document_source_for_fragment


def document_source(item: dict[str, Any], fragment: str, documents: list[dict[str, Any]]) -> dict[str, Any]:
    explicit_document = _text(item.get("document_name") or item.get("source"))
    explicit_source = {
        "document_name": explicit_document,
        "source_page": item.get("source_page"),
        "source_label": _text(item.get("source_label")),
        "source_context": _text(item.get("source_context")),
    }
    if (
        explicit_source["document_name"]
        and (explicit_source["source_page"] not in (None, "") or explicit_source["source_context"])
    ):
        return explicit_source

    matched = document_source_for_fragment(fragment, documents)
    if matched:
        return {
            "document_name": _text(matched.get("document_name")),
            "source_page": matched.get("source_page"),
            "source_label": _text(matched.get("source_label")),
            "source_context": _text(matched.get("source_context")),
        }

    if explicit_document:
        return explicit_source
    return {
        "document_name": resolve_document_name(item, fragment, documents),
        "source_page": item.get("source_page"),
        "source_label": _text(item.get("source_label")),
        "source_context": _text(item.get("source_context")),
    }


def resolve_document_name(item: dict[str, Any], fragment: str, documents: list[dict[str, Any]]) -> str:
    explicit = _text(item.get("document_name") or item.get("source"))
    if explicit:
        return explicit
    needle = _normalized_text(fragment)
    if not needle:
        return ""
    for document in documents:
        haystack = _normalized_text(document.get("text_content"))
        if needle in haystack:
            return _text(document.get("name") or document.get("url"))
    return ""


def page_number(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        page = int(value)
    except (TypeError, ValueError):
        return None
    return page if page > 0 else None


def source_label(document_name: str, page_number: int | None) -> str:
    if not document_name:
        return ""
    if page_number is None:
        return f"{document_name} · стр. не определена"
    return f"{document_name} · стр. {page_number}"


def evidence_sources(document_name: str, source_label: str, fragment: str) -> list[dict[str, Any]]:
    if not _text(fragment):
        return []
    return [
        {
            "document_name": _text(document_name),
            "source_label": _text(source_label),
            "fragment": _text(fragment),
        }
    ]


def _normalized_text(value: Any) -> str:
    return _text(value).casefold()


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()
