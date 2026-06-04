from __future__ import annotations

from typing import Any

from tender_killer.analysis_text_index_service import infer_document_role


READY_TEXT_STATUS = "ok"


def annotate_document_roles(documents: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    annotated: list[dict[str, Any]] = []
    for document in documents or []:
        role = str(document.get("document_role") or "").strip() or infer_document_role(document)
        annotated.append({**document, "document_role": role})
    return annotated


def document_roles_summary(documents: list[dict[str, Any]] | None) -> dict[str, list[str]]:
    roles: dict[str, list[str]] = {}
    for document in documents or []:
        name = _text(document.get("name") or document.get("url"))
        role = _text(document.get("document_role")) or infer_document_role(document)
        if not name or not role:
            continue
        roles.setdefault(role, []).append(name)
    return {role: names for role, names in roles.items() if names}


def build_document_coverage(documents: list[dict[str, Any]] | None) -> dict[str, Any]:
    document_rows = annotate_document_roles(documents)
    total = len(document_rows)
    ready_rows = [document for document in document_rows if _is_ready(document)]
    not_ready_rows = [document for document in document_rows if not _is_ready(document)]
    role_metrics = _role_metrics(document_rows)
    status = _coverage_status(total, len(ready_rows))
    return {
        "version": 1,
        "status": status,
        "total": total,
        "ready": len(ready_rows),
        "missing": len(not_ready_rows),
        "is_complete": status == "complete",
        "summary": _coverage_summary(status, total, ready_rows, not_ready_rows),
        "roles": role_metrics,
        "not_ready": [_not_ready_item(document) for document in not_ready_rows],
    }


def _is_ready(document: dict[str, Any]) -> bool:
    return _text(document.get("text_status")).casefold() == READY_TEXT_STATUS and bool(_text(document.get("text_content")))


def _coverage_status(total: int, ready: int) -> str:
    if total == 0:
        return "no_documents"
    if ready == total:
        return "complete"
    if ready == 0:
        return "empty"
    return "incomplete"


def _coverage_summary(
    status: str,
    total: int,
    ready_rows: list[dict[str, Any]],
    not_ready_rows: list[dict[str, Any]],
) -> str:
    if status == "no_documents":
        return "Документы для анализа не найдены."
    if status == "complete":
        return f"Прочитано {len(ready_rows)}/{total} документов."
    missing_names = ", ".join(_text(document.get("name") or document.get("url")) for document in not_ready_rows[:4])
    if len(not_ready_rows) > 4:
        missing_names = f"{missing_names}, еще {len(not_ready_rows) - 4}"
    return f"Прочитано {len(ready_rows)}/{total} документов. Не прочитано: {missing_names}."


def _role_metrics(documents: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    roles: dict[str, dict[str, int]] = {}
    for document in documents:
        role = _text(document.get("document_role")) or "other"
        metrics = roles.setdefault(role, {"total": 0, "ready": 0, "not_ready": 0})
        metrics["total"] += 1
        if _is_ready(document):
            metrics["ready"] += 1
        else:
            metrics["not_ready"] += 1
    return roles


def _not_ready_item(document: dict[str, Any]) -> dict[str, str]:
    return {
        "name": _text(document.get("name") or document.get("url")),
        "document_type": _text(document.get("document_type")),
        "document_role": _text(document.get("document_role")) or "other",
        "text_status": _text(document.get("text_status")) or "pending",
        "text_error": _text(document.get("text_error")),
    }


def _text(value: Any) -> str:
    if value in (None, ""):
        return ""
    return str(value).strip()
