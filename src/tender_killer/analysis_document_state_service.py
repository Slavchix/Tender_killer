from __future__ import annotations

from typing import Any


def build_document_items(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not documents:
        return []
    document_state = build_document_state(documents)
    document_labels = [
        _text(document.get("name") or document.get("url")) or f"Документ {index + 1}"
        for index, document in enumerate(documents)
    ]
    return [
        {
            "id": "documents:summary",
            "type": "document_summary",
            "kind": "document_summary",
            "label": "Документы для анализа",
            "value": "",
            "description": _document_summary_description(document_state),
            "category": "documents",
            "severity": "medium" if document_state["attention"] == 0 else "high",
            "status": document_state["status"],
            "source": "",
            "document_name": "",
            "source_page": None,
            "source_label": "",
            "source_context": "",
            "fragment": "",
            "impact": "",
            "operator_group": "document",
            "operator_action": document_state["next_step"],
            "price_impact": "none",
            "priority": 5,
            "rule_id": "",
            "is_blocker": False,
            "is_price_factor": False,
            "needs_review": document_state["status"] != "ready",
            "documents": document_labels[:8],
        }
    ]


def build_document_state(documents: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(documents)
    downloaded = sum(1 for document in documents if document.get("local_path"))
    text_ready = sum(1 for document in documents if document.get("text_status") == "ok")
    missing_download = sum(1 for document in documents if not document.get("local_path"))
    missing_text = total - text_ready
    if total == 0:
        status = "no_documents"
        summary = "Документы по закупке пока не найдены."
        next_step = "Обновить карточку закупки или открыть источник."
    elif text_ready == total:
        status = "ready"
        summary = "Текст извлечен по всем документам."
        next_step = "Переходить к проверке четырех блоков анализа."
    elif downloaded == 0:
        status = "needs_download"
        summary = "Документы нужно скачать перед анализом."
        next_step = "Скачать документы и извлечь текст."
    else:
        status = "needs_text"
        summary = "Текст извлечен не по всем документам."
        next_step = "Извлечь текст и проверить проблемные файлы."
    return {
        "status": status,
        "summary": summary,
        "next_step": next_step,
        "total": total,
        "downloaded": downloaded,
        "text_ready": text_ready,
        "attention": missing_text,
        "missing_download": missing_download,
        "missing_text": missing_text,
    }


def _document_summary_description(document_state: dict[str, Any]) -> str:
    total = document_state["total"]
    suffix = "файл" if total == 1 else "файла" if total in {2, 3, 4} else "файлов"
    return (
        f"{total} {suffix}: {document_state['downloaded']} скачано, "
        f"{document_state['text_ready']} с извлеченным текстом, {document_state['attention']} требуют внимания."
    )


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()
