from __future__ import annotations

import html
from io import BytesIO
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from tender_killer.analysis_evidence_service import build_analysis_evidence_items
from tender_killer.analysis_operator_view_service import build_analysis_operator_view
from tender_killer.analysis_operator_view_service import MAJOR_SECTION_DEFINITIONS
from tender_killer.analysis_operator_view_service import MAJOR_SECTION_IDS
from tender_killer.analysis_passport_service import build_analysis_tz_passport

DocxElement = tuple[str, Any, str]


def build_tender_report_docx(tender: dict[str, Any]) -> bytes:
    analysis = tender.get("analysis") or {}
    economics = tender.get("economics") or {}
    documents = tender.get("document_records") or []
    product_profiles = tender.get("product_profiles") or []
    product_profile_summary = _product_profile_summary(tender, product_profiles)
    elements: list[DocxElement] = [
        _p("Tender Killer: отчет по закупке", "title"),
        _p("Краткое решение", "heading"),
        _table(
            [
                ["Предварительный статус", _analysis_status(analysis.get("status"))],
                ["Уверенность", _confidence(analysis.get("confidence"))],
                ["Товарных позиций", str(product_profile_summary["total"])],
                ["Сумма закупки", _money(tender.get("price"))],
                ["Дедлайн", _value(tender.get("deadline_at"))],
            ]
        ),
        *_tender_decision_elements(tender.get("decision")),
        *_analysis_tz_passport_elements(analysis, documents),
        _p("Паспорт закупки", "heading"),
        _table(
            [
                ["Название", _value(tender.get("title"))],
                ["Номер", _value(tender.get("external_id"))],
                ["Источник", _value(tender.get("source"))],
                ["Ссылка", _value(tender.get("url"))],
                ["Заказчик", _value(tender.get("customer"))],
                ["Регион", _value(tender.get("region"))],
                ["Статус", _value(tender.get("status"))],
                ["НМЦК/цена", _money(tender.get("price"))],
            ]
        ),
        _p("Что закупают", "heading"),
    ]
    items = tender.get("items") or []
    if items:
        item_rows = [["№", "Товар", "Детали", "Кол-во", "Цена", "Классификатор"]]
        for item in items:
            classifier = _classifier_label(item.get("classifier_code") or item.get("okpd2"), item.get("classifier_type"))
            item_rows.append(
                [
                    _value(item.get("position_index")),
                    _value(item.get("name")),
                    _value(item.get("details"), ""),
                    f"{_value(item.get('quantity'))} {_value(item.get('unit'), '')}".strip(),
                    f"{_money(item.get('unit_price'))} / {_money(item.get('total_price'))}",
                    classifier,
                ]
            )
        elements.append(_table(item_rows))
    else:
        elements.append(
            _table(
                [
                    ["Предмет по карточке", _value(tender.get("title"))],
                    ["Категория", _value(tender.get("category"))],
                    ["ОКПД2/КОЗ по карточке", _value(tender.get("okpd2"))],
                    ["Цена по карточке", _money(tender.get("price"))],
                    [
                        "Комментарий",
                        "Структурированные позиции пока не найдены; эти данные используются как базовый предмет для будущего подбора товаров.",
                    ],
                ]
            )
        )

    elements.extend(
        [
            _p("Сводка товарных профилей", "heading"),
            _table(
                [
                    ["Товарные профили", str(product_profile_summary["total"])],
                    ["Готовы к поиску", str(product_profile_summary["ready"])],
                    ["Требуют проверки", str(product_profile_summary["needs_review"])],
                    ["Найдены товары", str(product_profile_summary["matched"])],
                    ["Посчитана экономика", str(product_profile_summary["priced"])],
                    ["Отклонены", str(product_profile_summary["rejected"])],
                ]
            ),
        ]
    )

    elements.append(_p("Документы", "heading"))
    if documents:
        document_rows = [["Документ", "Тип", "Статус текста"]]
        for document in documents:
            document_rows.append(
                [_value(document.get("name")), _value(document.get("document_type")), _value(document.get("text_status"))]
            )
        elements.append(_table(document_rows))
    else:
        elements.append(_p("Документы пока не найдены.", "normal"))

    elements.extend(
        [
            _p("Решение по анализу ТЗ", "heading"),
            *_analysis_decision_elements(analysis, documents),
            *_analysis_four_block_elements(analysis, documents),
            *_economics_elements(economics),
        ]
    )

    return _docx_bytes(elements)


def report_filename(tender: dict[str, Any]) -> str:
    external_id = str(tender.get("external_id") or "tender")
    return f"tender-killer-{_safe_filename(external_id)}.docx"


def _p(text: str, style: str = "normal") -> DocxElement:
    return ("p", text, style)


def _table(rows: list[list[Any]], style: str = "") -> DocxElement:
    return ("table", rows, style)


def _list_elements(values: list[Any]) -> list[DocxElement]:
    return [_p(f"- {_value(value)}", "normal") for value in values]


def _tender_decision_elements(decision: Any) -> list[DocxElement]:
    if not isinstance(decision, dict) or not any(
        decision.get(key) for key in ("label", "summary", "next_step", "reasons", "blockers")
    ):
        return []

    elements: list[DocxElement] = [
        _p("Решение Tender Killer", "heading"),
        _table(
            [
                ["Статус", _value(decision.get("label"))],
                ["Комментарий", _value(decision.get("summary"))],
                ["Следующий шаг", _value(decision.get("next_step"))],
            ]
        ),
    ]
    reasons = _text_list(decision.get("reasons"))
    blockers = _text_list(decision.get("blockers"))
    if reasons:
        elements.append(_p("Причины решения", "heading2"))
        elements.extend(_list_elements(reasons))
    if blockers:
        elements.append(_p("Блокеры", "heading2"))
        elements.extend(_list_elements(blockers))
    return elements


def _analysis_decision_elements(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> list[DocxElement]:
    decision = _analysis_decision(analysis, documents)
    elements = [
        _table(
            [
                ["Вердикт", decision["title"]],
                ["Комментарий", decision["summary"]],
            ]
        )
    ]
    if decision["reasons"]:
        elements.append(_p("Ключевые причины", "heading2"))
        elements.extend(_list_elements(decision["reasons"][:3]))
    return elements


def _analysis_four_block_elements(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> list[DocxElement]:
    operator_view = _report_operator_view(analysis, documents)
    rows = _analysis_four_block_rows(operator_view, analysis)
    if len(rows) <= 1:
        return []
    return [_p("Анализ ТЗ: 4 блока", "heading"), _table(rows, "analysis")]


def _report_operator_view(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> dict[str, Any]:
    operator_view = analysis.get("operator_view") if isinstance(analysis, dict) else None
    if isinstance(operator_view, dict) and _has_four_block_sections(operator_view):
        return operator_view
    return build_analysis_operator_view(analysis, documents)


def _has_four_block_sections(operator_view: dict[str, Any]) -> bool:
    sections = operator_view.get("major_blocks") or operator_view.get("sections")
    if not isinstance(sections, list):
        return False
    section_ids = {str(section.get("id") or "") for section in sections if isinstance(section, dict)}
    return set(MAJOR_SECTION_IDS).issubset(section_ids)


def _analysis_four_block_rows(operator_view: dict[str, Any], analysis: dict[str, Any] | None = None) -> list[list[Any]]:
    rows: list[list[Any]] = [["Блок", "Пункт", "Что значит", "Действие", "Источник"]]
    sections = operator_view.get("major_blocks") or operator_view.get("sections") or []
    section_map = {section.get("id"): section for section in sections if isinstance(section, dict)}
    supplemental_items = _report_supplemental_items(analysis or {})
    for definition in MAJOR_SECTION_DEFINITIONS:
        section = section_map.get(definition["id"]) or definition
        title = _value(section.get("title"), definition["title"])
        items = _merge_report_items(
            _report_section_items(section),
            supplemental_items.get(definition["id"], []),
        )
        if not items:
            rows.append([title, "Не найдено", _value(section.get("empty"), definition["empty"]), "", ""])
            continue
        for item in items[:7]:
            rows.append(
                [
                    title,
                    _short_text(item.get("label"), 90),
                    _short_text(
                        item.get("description")
                        or item.get("value")
                        or item.get("impact")
                        or item.get("fragment"),
                        220,
                    ),
                    _short_text(item.get("operator_action") or item.get("next_step"), 170),
                    _short_text(_item_source_text(item), 220),
                ]
            )
        if len(items) > 7:
            rows.append([title, f"и еще {len(items) - 7} пункт — см. в интерфейсе", "", "", ""])
    return rows


def _merge_report_items(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in [*left, *right]:
        key = (_short_text(item.get("label"), 80).lower(), _short_text(_item_source_text(item), 120).lower())
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return sorted(merged, key=lambda item: _int_value(item.get("priority")))


def _report_section_items(section: dict[str, Any]) -> list[dict[str, Any]]:
    items = [
        item
        for item in section.get("items") or []
        if isinstance(item, dict) and item.get("type") != "document_summary" and item.get("kind") != "document_summary"
    ]
    return sorted(items, key=lambda item: _int_value(item.get("priority")))


def _report_supplemental_items(analysis: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = {section_id: [] for section_id in MAJOR_SECTION_IDS}
    checklist = analysis.get("checklist") if isinstance(analysis, dict) else None
    if not isinstance(checklist, list):
        return buckets
    for index, raw_item in enumerate(checklist):
        if not isinstance(raw_item, dict):
            continue
        evidence = _value(raw_item.get("fragment") or raw_item.get("evidence"), "").strip()
        label = _value(raw_item.get("label"), "").strip()
        if not label or not evidence:
            continue
        section_id = _report_section_id(raw_item)
        item = {
            "label": label,
            "description": _value(raw_item.get("value") or raw_item.get("description") or evidence, ""),
            "operator_action": _value(
                raw_item.get("operator_action"),
                "Проверить допустимость участия до расчета."
                if section_id == "decision_risks"
                else "Проверить условие перед решением.",
            ),
            "source_label": _value(raw_item.get("source_label") or raw_item.get("source") or raw_item.get("document_name"), ""),
            "fragment": evidence,
            "priority": _int_value(raw_item.get("priority")) or 70 + index,
        }
        buckets[section_id].append(item)
    return buckets


def _report_section_id(item: dict[str, Any]) -> str:
    category = str(item.get("category") or "")
    severity = str(item.get("severity") or "")
    if severity in {"high", "critical"} or category in {"legal", "national_regime"}:
        return "decision_risks"
    if category in {"delivery", "contract", "warranty", "storage"}:
        return "fulfillment_terms"
    if category in {"acceptance", "financial", "payment"}:
        return "acceptance_payment"
    return "product_compliance"


def _item_source_text(item: dict[str, Any]) -> str:
    source = _value(item.get("source_label") or item.get("document_name") or item.get("source"), "")
    fragment = _short_text(item.get("fragment") or item.get("source_context"), 180)
    if source and fragment:
        return f"{source}: {fragment}"
    return source or fragment


def _analysis_tz_passport_elements(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> list[DocxElement]:
    if not isinstance(analysis, dict) or not analysis:
        return []
    passport = _analysis_tz_passport(analysis, documents)
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


def _analysis_tz_passport(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> dict[str, Any]:
    passport = analysis.get("tz_passport") if isinstance(analysis, dict) else None
    if isinstance(passport, dict) and passport.get("version") == 1:
        return passport
    return build_analysis_tz_passport(analysis, documents)


def _analysis_decision(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> dict[str, Any]:
    if not analysis:
        return {
            "title": "Нужен анализ ТЗ",
            "summary": "Сначала извлеките текст документов и запустите анализ.",
            "reasons": [f"Документов в карточке: {len(documents)}"] if documents else [],
        }

    operator_view = analysis.get("operator_view") if isinstance(analysis, dict) else None
    decision = operator_view.get("decision_brief") if isinstance(operator_view, dict) else None
    if isinstance(decision, dict) and any(decision.get(key) for key in ("title", "summary", "reasons")):
        return {
            "title": _value(decision.get("title"), "Analysis decision"),
            "summary": _value(decision.get("summary"), ""),
            "reasons": _text_list(decision.get("reasons")),
        }

    red_flags = _text_list(analysis.get("red_flags"))
    risks = _text_list(analysis.get("risks"))
    requirements = _text_list(analysis.get("requirements"))
    checklist = [item for item in analysis.get("checklist") or [] if isinstance(item, dict)]
    has_high_check = any(item.get("severity") == "high" for item in checklist)
    status_text = _analysis_status(analysis.get("status"))
    confidence_text = _confidence(analysis.get("confidence"))
    reasons = [
        *[f"Красный флаг: {item}" for item in red_flags],
        *[f"Риск: {item}" for item in risks],
        *[f"Требование: {item}" for item in requirements],
    ]

    if red_flags or has_high_check:
        return {
            "title": "Нужна ручная проверка",
            "summary": f"{status_text}, уверенность {confidence_text}. Сначала проверьте критичные условия.",
            "reasons": reasons,
        }
    if risks or requirements:
        return {
            "title": "Проверить условия",
            "summary": f"{status_text}, уверенность {confidence_text}. Существенных блокеров нет, но условия надо сверить.",
            "reasons": reasons,
        }
    return {
        "title": "Критичных рисков не видно",
        "summary": f"{status_text}, уверенность {confidence_text}. Можно переходить к экономике и поставщикам.",
        "reasons": [_value(analysis.get("summary"), "Анализ не нашел явных рисков и требований.")],
    }


def _analysis_operator_view(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> dict[str, Any]:
    return build_analysis_operator_view(analysis, documents)


def _analysis_checklist_elements(analysis: dict[str, Any]) -> list[DocxElement]:
    checklist = analysis.get("checklist") or []
    if not isinstance(checklist, list) or not checklist:
        return []
    rows = [["Категория", "Проверка", "Важность", "Фрагмент"]]
    for item in checklist:
        if not isinstance(item, dict):
            continue
        rows.append(
            [
                _value(item.get("category")),
                _value(item.get("label")),
                _value(item.get("severity")),
                _value(item.get("evidence"), ""),
            ]
        )
    if len(rows) == 1:
        return []
    return [_p("Проверочный список", "heading"), _table(rows)]


def _analysis_evidence_elements(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> list[DocxElement]:
    evidence_items = _analysis_evidence_items(analysis, documents)
    if not evidence_items:
        return []
    rows = [["Тип условия", "Проверка", "Важность", "Документ", "Фрагмент", "Влияние"]]
    for item in evidence_items:
        rows.append(
            [
                item["type_label"],
                item["label"],
                item["importance_label"],
                item["document_name"],
                item["fragment"],
                item["impact"],
            ]
        )
    return [_p("Доказательства из документов", "heading"), _table(rows)]


def _analysis_evidence_items(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> list[dict[str, str]]:
    return build_analysis_evidence_items(analysis, documents)


def _text_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [_value(value, "").strip() for value in values if _value(value, "").strip()]


def _limited_text_list(values: Any, *, fallback: str, limit: int = 8) -> list[str]:
    items = _text_list(values)
    if not items:
        return [fallback]
    if len(items) <= limit:
        return items
    return [*items[:limit], f"и еще {len(items) - limit} пунктов"]


def _short_text(value: Any, limit: int) -> str:
    text = _value(value, "").replace("\n", " ").strip()
    while "  " in text:
        text = text.replace("  ", " ")
    if len(text) <= limit:
        return text
    return f"{text[: max(0, limit - 1)].rstrip()}…"


def _missing_costs_summary(values: Any) -> str:
    missing = _text_list(values)
    if not missing:
        return "нет"
    return f"{len(missing)} позиций"


def _economics_elements(economics: dict[str, Any]) -> list[DocxElement]:
    if not economics:
        return [
            _p("Экономика", "heading"),
            _p("Расчет экономики еще не подготовлен.", "normal"),
        ]
    missing_cost_inputs = _text_list(economics.get("missing_cost_inputs"))
    rows = [
        ["Статус", _economics_status(economics.get("status"))],
        ["НМЦК/выручка", _money(economics.get("revenue"))],
        ["Себестоимость поставщика", _money(economics.get("supplier_cost"))],
        ["Резерв риска", f"{_money(economics.get('risk_reserve'))} / {_percent(economics.get('risk_reserve_rate_percent'))}"],
        ["Итого затраты", _money(economics.get("estimated_total_cost"))],
        ["Маржа", f"{_money(economics.get('gross_margin'))} / {_percent(economics.get('margin_percent'))}"],
        ["Не хватает цен", _missing_costs_summary(missing_cost_inputs)],
        ["Риски исполнения", ", ".join(_limited_text_list(economics.get("risk_types"), fallback="нет", limit=5))],
    ]
    elements = [_p("Экономика", "heading"), _table(rows)]
    if economics.get("recommendation"):
        elements.append(_p(_value(economics.get("recommendation")), "normal"))
    if missing_cost_inputs:
        elements.append(_p("Первые позиции без себестоимости", "heading2"))
        elements.extend(_list_elements(_limited_text_list(missing_cost_inputs, fallback="нет", limit=5)))
    return elements


def _profile_evidence_elements(profile: dict[str, Any]) -> list[DocxElement]:
    rows = [
        ["Документ", "Требование"],
        *[
            [_value(item.get("source")), _value(item.get("value"))]
            for item in profile.get("evidence") or []
            if isinstance(item, dict) and item.get("field") == "document_requirement"
        ],
    ]
    if len(rows) == 1:
        return []
    return [_p("Подтверждения из ТЗ", "heading2"), _table(rows)]


def _list_paragraphs(values: list[Any]) -> list[tuple[str, str]]:
    return [(f"- {_value(value)}", "normal") for value in values]


def _product_profile_summary(tender: dict[str, Any], product_profiles: list[Any]) -> dict[str, int]:
    summary = tender.get("product_profile_summary")
    keys = ("total", "ready", "needs_review", "matched", "priced", "rejected")
    if isinstance(summary, dict):
        return {key: _int_value(summary.get(key)) for key in keys}

    counts = dict.fromkeys(keys, 0)
    counts["total"] = len(product_profiles)
    for profile in product_profiles:
        if not isinstance(profile, dict):
            continue
        status = str(profile.get("profile_status") or "")
        if status in counts and status != "total":
            counts[status] += 1
    return counts


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _docx_bytes(elements: list[DocxElement]) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _content_types_xml())
        archive.writestr("_rels/.rels", _rels_xml())
        archive.writestr("word/document.xml", _document_xml(elements))
        archive.writestr("word/styles.xml", _styles_xml())
    return buffer.getvalue()


def _document_xml(elements: list[DocxElement]) -> str:
    body_parts: list[str] = []
    for kind, payload, style in elements:
        if kind == "table":
            body_parts.append(_table_xml(payload, style))
        else:
            body_parts.append(_paragraph_xml(payload, style))
    body = "\n".join(body_parts)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}<w:sectPr><w:pgSz w:w=\"11906\" w:h=\"16838\"/><w:pgMar w:top=\"1134\" w:right=\"850\" w:bottom=\"1134\" w:left=\"850\"/></w:sectPr></w:body>"
        "</w:document>"
    )


def _paragraph_xml(text: str, style: str) -> str:
    style_id = {
        "title": "Title",
        "heading": "Heading1",
        "heading2": "Heading2",
        "table_header": "TableHeader",
    }.get(style, "Normal")
    return (
        "<w:p>"
        f"<w:pPr><w:pStyle w:val=\"{style_id}\"/></w:pPr>"
        f"<w:r><w:t xml:space=\"preserve\">{html.escape(str(text))}</w:t></w:r>"
        "</w:p>"
    )


def _table_xml(rows: list[list[Any]], style: str = "") -> str:
    body = "".join(_row_xml(row, is_header=index == 0) for index, row in enumerate(rows))
    width = "10300" if style == "analysis" else "9800"
    return (
        "<w:tbl>"
        "<w:tblPr>"
        '<w:tblStyle w:val="CompactTable"/>'
        f'<w:tblW w:w="{width}" w:type="dxa"/>'
        '<w:tblCellMar><w:top w:w="80" w:type="dxa"/><w:left w:w="90" w:type="dxa"/><w:bottom w:w="80" w:type="dxa"/><w:right w:w="90" w:type="dxa"/></w:tblCellMar>'
        '<w:tblBorders><w:top w:val="single" w:sz="4" w:color="B7C9C3"/>'
        '<w:left w:val="single" w:sz="4" w:color="B7C9C3"/>'
        '<w:bottom w:val="single" w:sz="4" w:color="B7C9C3"/>'
        '<w:right w:val="single" w:sz="4" w:color="B7C9C3"/>'
        '<w:insideH w:val="single" w:sz="4" w:color="B7C9C3"/>'
        '<w:insideV w:val="single" w:sz="4" w:color="B7C9C3"/></w:tblBorders>'
        "</w:tblPr>"
        f"{body}"
        "</w:tbl>"
    )


def _row_xml(row: list[Any], *, is_header: bool) -> str:
    return f"<w:tr>{''.join(_cell_xml(value, is_header=is_header) for value in row)}</w:tr>"


def _cell_xml(value: Any, *, is_header: bool = False) -> str:
    shading = '<w:shd w:fill="E6F4EA" w:val="clear"/>' if is_header else ""
    return (
        "<w:tc>"
        f'<w:tcPr><w:tcW w:w="2400" w:type="dxa"/>{shading}</w:tcPr>'
        f"{_paragraph_xml(_value(value, ''), 'table_header' if is_header else 'normal')}"
        "</w:tc>"
    )


def _content_types_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        "</Types>"
    )


def _rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )


def _styles_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/><w:sz w:val="20"/><w:color w:val="20342C"/></w:rPr></w:rPrDefault></w:docDefaults>'
        '<w:style w:type="paragraph" w:styleId="Normal"><w:name w:val="Normal"/><w:pPr><w:spacing w:after="80" w:line="240" w:lineRule="auto"/></w:pPr><w:rPr><w:sz w:val="20"/><w:color w:val="20342C"/></w:rPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:pPr><w:spacing w:after="180"/></w:pPr><w:rPr><w:b/><w:sz w:val="34"/><w:color w:val="1F4D3A"/></w:rPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:pPr><w:spacing w:before="180" w:after="90"/><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="3" w:color="7ACB83"/></w:pBdr></w:pPr><w:rPr><w:b/><w:sz w:val="25"/><w:color w:val="1F4D3A"/></w:rPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:pPr><w:spacing w:before="120" w:after="70"/></w:pPr><w:rPr><w:b/><w:sz w:val="21"/><w:color w:val="2F6B4F"/></w:rPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="TableHeader"><w:name w:val="TableHeader"/><w:pPr><w:spacing w:after="0"/></w:pPr><w:rPr><w:b/><w:sz w:val="19"/><w:color w:val="1F4D3A"/></w:rPr></w:style>'
        '<w:style w:type="table" w:styleId="CompactTable"><w:name w:val="CompactTable"/><w:tblPr><w:tblCellMar><w:top w:w="80" w:type="dxa"/><w:left w:w="90" w:type="dxa"/><w:bottom w:w="80" w:type="dxa"/><w:right w:w="90" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style>'
        "</w:styles>"
    )


def _value(value: Any, fallback: str = "не указано") -> str:
    if value is None or value == "":
        return fallback
    return str(value)


def _money(value: Any) -> str:
    try:
        return f"{float(value):,.2f} ₽".replace(",", " ")
    except (TypeError, ValueError):
        return "не указано"


def _percent(value: Any) -> str:
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "не указано"


def _classifier_label(code: Any, classifier_type: Any) -> str:
    if code and classifier_type:
        return f"{classifier_type}: {code}"
    if code:
        return str(code)
    if classifier_type:
        return str(classifier_type)
    return "не указано"


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


def _economics_status(value: Any) -> str:
    return {
        "interesting": "интересно",
        "manual_review": "ручная проверка",
        "low_margin": "низкая маржа",
        "needs_costs": "нужны себестоимости",
        "needs_price": "нужна НМЦК",
    }.get(str(value or ""), "ручная проверка")


def _trim_text(value: str, limit: int) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= limit else f"{text[:limit]}..."


def _safe_filename(value: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in value).strip("._") or "tender"
