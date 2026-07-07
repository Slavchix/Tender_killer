from __future__ import annotations

from typing import Any

from tender_killer.analysis_passport_service import build_analysis_tz_passport
from tender_killer.analysis_operator_sections_service import MAJOR_SECTION_IDS
from tender_killer.reports_docx_writer import DocxElement
from tender_killer.reports_docx_writer import paragraph as _p
from tender_killer.reports_docx_writer import table as _table


def analysis_tz_passport_elements(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> list[DocxElement]:
    if not isinstance(analysis, dict) or not analysis:
        return []
    passport = analysis_tz_passport(analysis, documents)
    sections = passport.get("sections") if isinstance(passport, dict) else []
    if not isinstance(sections, list):
        return []

    rows: list[list[Any]] = [["Раздел", "Условие", "Значение", "Источник", "Влияние"]]
    for section in sections:
        if not isinstance(section, dict):
            continue
        title = _value(section.get("title"), _value(section.get("id")))
        for item in section.get("items") or []:
            if not isinstance(item, dict):
                continue
            rows.append(
                [
                    title,
                    _value(item.get("label")),
                    _value(item.get("value"), ""),
                    _value(item.get("source"), ""),
                    _value(item.get("impact") or item.get("description"), ""),
                ]
            )
    if len(rows) <= 1:
        return []
    return [
        _p("Паспорт ТЗ", "heading"),
        _table(
            [
                ["Предмет", _value(passport.get("title"))],
                ["Статус", _analysis_status(passport.get("status"))],
                ["Уверенность", _confidence(passport.get("confidence"))],
            ]
        ),
        _table(rows),
    ]


def analysis_tz_passport(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> dict[str, Any]:
    passport = analysis.get("tz_passport") if isinstance(analysis, dict) else None
    if isinstance(passport, dict) and passport.get("version") in {1, 2} and passport.get("summary_block"):
        return passport
    if isinstance(passport, dict) and passport.get("version") == 1:
        return passport
    return build_analysis_tz_passport(analysis, documents)


def analysis_management_brief_elements(
    analysis: dict[str, Any],
    documents: list[dict[str, Any]],
    operator_view: dict[str, Any],
) -> list[DocxElement]:
    if not isinstance(analysis, dict) or not analysis:
        return []
    passport = analysis_tz_passport(analysis, documents)
    if not isinstance(passport, dict):
        return []
    verdict = passport.get("verdict") if isinstance(passport.get("verdict"), dict) else {}
    document_summary = passport.get("documents") if isinstance(passport.get("documents"), dict) else {}
    rows = [
        ["Решение по ТЗ", _value(verdict.get("label") or passport.get("title"))],
        ["Паспорт ТЗ v2", _value(passport.get("subject"))],
        ["Документы готовы/не готовы", _value(document_summary.get("label"), "не указано")],
        ["Ключевые условия", _brief_list_value(passport.get("key_conditions"))],
        ["Красные флаги", _brief_list_value(passport.get("red_flags"))],
        ["Противоречия", _brief_list_value(passport.get("conflicts"))],
        ["Ожидаемые условия не найдены", _brief_list_value(passport.get("expected_missing"))],
    ]
    elements: list[DocxElement] = [_p("Управленческий brief по ТЗ", "heading"), _table(rows, "analysis")]
    action_rows = _analysis_brief_action_rows(operator_view)
    if len(action_rows) > 1:
        elements.extend([_p("Действия оператора", "heading2"), _table(action_rows, "analysis")])
    source_rows = _analysis_brief_source_rows(operator_view, documents)
    if len(source_rows) > 1:
        elements.extend([_p("Ссылки на источники", "heading2"), _table(source_rows, "analysis")])
    change_rows = _analysis_brief_change_rows(analysis)
    if len(change_rows) > 1:
        elements.extend([_p("Что изменилось с прошлой версии", "heading2"), _table(change_rows, "analysis")])
    return elements


def analysis_saas_elements(operator_view: dict[str, Any]) -> list[DocxElement]:
    if not isinstance(operator_view, dict):
        return []
    elements: list[DocxElement] = []
    workflow = operator_view.get("tz_workflow")
    if isinstance(workflow, dict):
        elements.extend(
            [
                _p("Рабочий статус ТЗ", "heading"),
                _table(
                    [
                        ["Статус", _value(workflow.get("status_label") or workflow.get("status"))],
                        ["Ответственный", _value(workflow.get("responsible"), "")],
                        ["Дедлайн", _value(workflow.get("deadline"), "")],
                        ["Комментарий", _value(workflow.get("comment"), "")],
                    ],
                    "analysis",
                ),
            ]
        )
        journal = workflow.get("journal")
        if isinstance(journal, list) and journal:
            journal_rows = [
                [
                    _value(entry.get("action")),
                    _value(entry.get("actor"), ""),
                    _short_text(entry.get("comment"), 180),
                ]
                for entry in journal[-5:]
                if isinstance(entry, dict)
            ]
            if journal_rows:
                elements.append(_table([["Журнал", "Кто", "Комментарий"], *journal_rows], "analysis"))

    condition_groups = operator_view.get("condition_groups")
    condition_items = condition_groups.get("items") if isinstance(condition_groups, dict) else None
    if isinstance(condition_items, list) and condition_items:
        rows: list[list[Any]] = [["Условие", "Статус условия", "Источник", "Что сделать"]]
        for item in condition_items[:8]:
            if not isinstance(item, dict):
                continue
            rows.append(
                [
                    _short_text(item.get("label") or item.get("family"), 100),
                    _analysis_condition_group_status(item),
                    _short_text("; ".join(_text_list(item.get("sources"))), 220),
                    _short_text(item.get("operator_action") or item.get("resolution"), 240),
                ]
            )
        if len(rows) > 1:
            elements.extend([_p("Сводка условий ТЗ", "heading"), _table(rows, "analysis")])

    questions = operator_view.get("ai_questions")
    question_items = questions.get("items") if isinstance(questions, dict) else None
    if isinstance(question_items, list) and question_items:
        rows: list[list[Any]] = [["Вопрос", "Ответ", "Источник"]]
        for item in question_items[:6]:
            if not isinstance(item, dict):
                continue
            sources = item.get("sources") if isinstance(item.get("sources"), list) else []
            source_text = "; ".join(_question_source_text(source) for source in sources[:2] if isinstance(source, dict))
            rows.append(
                [
                    _short_text(item.get("question"), 120),
                    _short_text(item.get("answer"), 180),
                    _short_text(source_text, 220),
                ]
            )
        if len(rows) > 1:
            elements.extend([_p("Контрольные вопросы ТЗ", "heading"), _table(rows, "analysis")])

    playbooks = operator_view.get("playbooks")
    playbook_items = playbooks.get("items") if isinstance(playbooks, dict) else None
    if isinstance(playbook_items, list) and playbook_items:
        rows = [["Риск", "Серьезность", "Что сделать", "Когда эскалировать"]]
        for item in playbook_items[:6]:
            if not isinstance(item, dict):
                continue
            rows.append(
                [
                    _short_text(item.get("title") or item.get("id"), 100),
                    _value(item.get("severity"), ""),
                    _short_text("; ".join(_text_list(item.get("what_to_do"))), 220),
                    _short_text("; ".join(_text_list(item.get("when_to_use"))), 220),
                ]
            )
        if len(rows) > 1:
            elements.extend([_p("Плейбуки оператора", "heading"), _table(rows, "analysis")])

    return elements


def analysis_history_elements(analysis: dict[str, Any]) -> list[DocxElement]:
    history = analysis.get("analysis_history") if isinstance(analysis, dict) else None
    if not isinstance(history, list) or not history:
        return []
    rows: list[list[Any]] = [["Версия", "Когда", "Итог", "Детали"]]
    for entry in history[:5]:
        if not isinstance(entry, dict):
            continue
        changes = entry.get("changes") if isinstance(entry.get("changes"), dict) else {}
        details = _analysis_history_detail_text(changes)
        rows.append(
            [
                _value(entry.get("run_number"), "1"),
                _value(entry.get("analyzed_at"), ""),
                _short_text(changes.get("summary") or entry.get("summary"), 160),
                _short_text(details, 240),
            ]
        )
    if len(rows) <= 1:
        return []
    return [_p("История анализа", "heading"), _table(rows, "analysis")]


def _analysis_history_detail_text(changes: dict[str, Any]) -> str:
    parts: list[str] = []
    for label, key in (
        ("добавлено", "added"),
        ("изменено", "changed"),
        ("удалено", "removed"),
        ("метки", "feedback"),
    ):
        values = _text_list(changes.get(key))
        if values:
            parts.append(f"{label}: {', '.join(values[:3])}")
    documents = changes.get("documents")
    if isinstance(documents, dict):
        document_parts = []
        for label, key in (("документы добавлены", "added"), ("документы изменены", "changed"), ("документы удалены", "removed")):
            values = _text_list(documents.get(key))
            if values:
                document_parts.append(f"{label}: {', '.join(values[:3])}")
        if document_parts:
            parts.append("; ".join(document_parts))
    condition_changes = changes.get("condition_changes")
    if isinstance(condition_changes, list):
        labels = [
            _value(item.get("label"), "")
            for item in condition_changes
            if isinstance(item, dict) and _value(item.get("label"), "")
        ]
        if labels:
            parts.append(f"условия: {', '.join(labels[:3])}")
    if parts:
        return "; ".join(parts)
    return f"+{_int_value(changes.get('added_count'))} / -{_int_value(changes.get('removed_count'))} / Δ{_int_value(changes.get('changed_count'))}"


def _analysis_condition_group_status(item: dict[str, Any]) -> str:
    status = {
        "confirmed": "подтверждено",
        "conflict": "противоречие",
        "expected_missing": "не найдено",
        "manual_review": "ручная проверка",
    }.get(_value(item.get("status"), ""), _value(item.get("status"), ""))
    source_status = {
        "primary_source": "главный источник",
        "explicit_source": "точный источник",
        "conflicting_sources": "конфликт источников",
        "missing": "источник не найден",
        "needs_source_review": "источник проверить",
        "inferred": "источник выведен",
    }.get(_value(item.get("source_status"), ""), _value(item.get("source_status"), ""))
    if status and source_status:
        return f"{status} / {source_status}"
    return status or source_status


def _question_source_text(source: dict[str, Any]) -> str:
    label = _value(source.get("source_label") or source.get("document_name"), "")
    fragment = _short_text(source.get("fragment"), 150)
    if label and fragment:
        return f"{label}: {fragment}"
    return label or fragment


def _analysis_brief_action_rows(operator_view: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = [["Блок", "Что сделать", "Статус"]]
    for step in operator_view.get("action_plan") or []:
        if not isinstance(step, dict):
            continue
        rows.append(
            [
                _short_text(step.get("title") or step.get("id"), 90),
                _short_text(step.get("next_step"), 220),
                _short_text(step.get("status"), 80),
            ]
        )
    return rows


def _analysis_brief_source_rows(operator_view: dict[str, Any], documents: list[dict[str, Any]]) -> list[list[Any]]:
    rows: list[list[Any]] = [["Источник", "Статус", "Ссылка"]]
    for document in documents[:8]:
        if not isinstance(document, dict):
            continue
        rows.append(
            [
                _short_text(document.get("name") or document.get("url"), 120),
                _short_text(document.get("text_status") or document.get("document_type"), 90),
                _short_text(document.get("url"), 220),
            ]
        )
    if len(rows) > 1:
        return rows
    for item in _operator_items_by_section(operator_view, set(MAJOR_SECTION_IDS))[:8]:
        source = _source_label_for_item(item)
        if not source:
            continue
        rows.append([_short_text(source, 120), _short_text(item.get("label"), 120), _short_text(item.get("fragment"), 220)])
    return rows


def _analysis_brief_change_rows(analysis: dict[str, Any]) -> list[list[Any]]:
    history = analysis.get("analysis_history") if isinstance(analysis, dict) else None
    latest = history[0] if isinstance(history, list) and history and isinstance(history[0], dict) else {}
    changes = latest.get("changes") if isinstance(latest.get("changes"), dict) else {}
    rows: list[list[Any]] = [["Тип", "Детали"]]
    if changes.get("summary"):
        rows.append(["Итог", _short_text(changes.get("summary"), 220)])
    documents = changes.get("documents") if isinstance(changes.get("documents"), dict) else {}
    for label, key in (("Новые документы", "added"), ("Измененные документы", "changed"), ("Удаленные документы", "removed")):
        values = _text_list(documents.get(key))
        if values:
            rows.append([label, _brief_list_value(values)])
    condition_changes = changes.get("condition_changes")
    if isinstance(condition_changes, list):
        values = [
            f"{_value(item.get('label'), '')}: {_value(item.get('change_type'), '')}"
            for item in condition_changes
            if isinstance(item, dict) and _value(item.get("label"), "")
        ]
        if values:
            rows.append(["Изменившиеся условия", _brief_list_value(values)])
    return rows


def _operator_items_by_section(operator_view: dict[str, Any], section_ids: set[str]) -> list[dict[str, Any]]:
    sections = operator_view.get("major_blocks") or operator_view.get("sections") or []
    items: list[dict[str, Any]] = []
    for section in sections:
        if not isinstance(section, dict) or section.get("id") not in section_ids:
            continue
        for item in section.get("items") or []:
            if isinstance(item, dict) and item.get("type") != "document_summary" and item.get("kind") != "document_summary":
                items.append(item)
    return sorted(items, key=lambda item: _int_value(item.get("priority")))


def _source_label_for_item(item: dict[str, Any]) -> str:
    binding = item.get("source_binding")
    if isinstance(binding, dict):
        source_label = _value(binding.get("source_label"), "").strip()
        if source_label:
            return source_label
    return _value(item.get("source_label") or item.get("document_name") or item.get("source"), "").strip()


def _brief_list_value(values: Any, *, fallback: str = "нет") -> str:
    items = _text_list(values)
    if not items:
        return fallback
    return "; ".join(items[:6]) + (f"; и еще {len(items) - 6}" if len(items) > 6 else "")


def _text_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, list):
        return [str(value).strip() for value in values if str(value).strip()]
    if isinstance(values, str):
        stripped = values.strip()
        return [stripped] if stripped else []
    return [str(values)]


def _short_text(value: Any, limit: int) -> str:
    text = " ".join(_value(value, "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _value(value: Any, fallback: str = "не указано") -> str:
    if value is None or value == "":
        return fallback
    return str(value)


def _confidence(value: Any) -> str:
    try:
        return f"{round(float(value) * 100)}%"
    except (TypeError, ValueError):
        return "не указана"


def _analysis_status(value: Any) -> str:
    return {"needs_review": "Нужна проверка", "interesting": "Интересно", "skipped": "Пропустить"}.get(
        str(value or ""),
        "Нужна проверка",
    )
