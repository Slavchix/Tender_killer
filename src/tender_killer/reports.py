from __future__ import annotations

import html
from io import BytesIO
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from tender_killer.analysis_evidence_service import build_analysis_evidence_items
from tender_killer.analysis_operator_view_service import build_analysis_operator_view
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
                ["Документов с текстом", str(len([doc for doc in documents if doc.get("text_content")]))],
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
            _p(f"Товарные профили: {product_profile_summary['total']}", "normal"),
            _p(f"Готовы к поиску: {product_profile_summary['ready']}", "normal"),
            _p(f"Требуют проверки: {product_profile_summary['needs_review']}", "normal"),
            _p("Товарный профиль для поиска", "heading"),
        ]
    )
    if product_profiles:
        for profile in product_profiles:
            elements.extend(
                [
                    _p(f"Профиль №{_value(profile.get('position_index'))}: {_value(profile.get('product_name'))}", "heading2"),
                    _table(
                        [
                            ["Категория", _value(profile.get("category"))],
                            ["ОКПД2", _value(profile.get("okpd2"))],
                            ["Код классификатора", _value(profile.get("classifier_code"))],
                            ["Тип классификатора", _value(profile.get("classifier_type"))],
                            ["Количество", f"{_value(profile.get('quantity'))} {_value(profile.get('unit'), '')}".strip()],
                            ["Источник профиля", _value(profile.get("source"))],
                            ["Детали", _value(profile.get("details"))],
                        ]
                    ),
                    _p("Поисковые фразы", "heading2"),
                    *_list_elements(profile.get("search_phrases") or []),
                    _p("Требования из карточки и ТЗ", "heading2"),
                    *_list_elements(profile.get("required_characteristics") or ["Пока не найдены."]),
                    *_profile_evidence_elements(profile),
                    _p("Документы/сертификаты", "heading2"),
                    *_list_elements(profile.get("cert_documents") or ["Пока не найдены."]),
                    _p("Стандарты", "heading2"),
                    *_list_elements(profile.get("standards") or ["Пока не найдены."]),
                    _p("Стоп-слова для товарного поиска", "heading2"),
                    *_list_elements(profile.get("stop_words") or []),
                ]
            )
    else:
        elements.append(_p("Товарный профиль пока не сформирован.", "normal"))

    elements.append(_p("Документы и ТЗ", "heading"))
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
            *_analysis_operator_sections_elements(analysis, documents),
            _p("Выжимка ТЗ", "heading"),
            _p(_value(analysis.get("summary"), "Анализ ТЗ еще не выполнен."), "normal"),
            *_analysis_checklist_elements(analysis),
            *_analysis_evidence_elements(analysis, documents),
            _p("Требования", "heading"),
            *_list_elements(analysis.get("requirements") or ["Требования пока не найдены."]),
            _p("Риски", "heading"),
            *_list_elements(analysis.get("risks") or ["Риски пока не найдены."]),
            _p("Красные флаги", "heading"),
            *_list_elements(analysis.get("red_flags") or ["Красные флаги пока не найдены."]),
            *_economics_elements(economics),
        ]
    )

    text_samples = [
        document.get("text_content")
        for document in documents
        if isinstance(document.get("text_content"), str) and document.get("text_content").strip()
    ]
    if text_samples:
        elements.append(_p("Приложение: фрагменты извлеченного текста", "heading"))
        for index, text in enumerate(text_samples[:3], start=1):
            elements.append(_p(f"Фрагмент {index}: {_trim_text(text, 900)}", "normal"))

    return _docx_bytes(elements)


def report_filename(tender: dict[str, Any]) -> str:
    external_id = str(tender.get("external_id") or "tender")
    return f"tender-killer-{_safe_filename(external_id)}.docx"


def _p(text: str, style: str = "normal") -> DocxElement:
    return ("p", text, style)


def _table(rows: list[list[Any]]) -> DocxElement:
    return ("table", rows, "")


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
                ["Документов", str(len(documents))],
            ]
        )
    ]
    if decision["reasons"]:
        elements.append(_p("Ключевые причины", "heading2"))
        elements.extend(_list_elements(decision["reasons"][:3]))
    return elements


def _analysis_operator_sections_elements(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> list[DocxElement]:
    operator_view = _analysis_operator_view(analysis, documents)
    sections = operator_view.get("sections") if isinstance(operator_view, dict) else []
    if not isinstance(sections, list):
        return []

    rows: list[list[Any]] = [["Section", "Item", "Category", "Severity", "Source", "Impact"]]
    for section in sections:
        if not isinstance(section, dict) or section.get("id") not in {"blockers", "price_factors"}:
            continue
        title = _value(section.get("title"), _value(section.get("id")))
        for item in section.get("items") or []:
            if not isinstance(item, dict):
                continue
            rows.append(
                [
                    title,
                    _value(item.get("label")),
                    _value(item.get("category")),
                    _value(item.get("severity")),
                    _value(item.get("source")),
                    _value(item.get("impact") or item.get("description"), ""),
                ]
            )
    if len(rows) <= 1:
        return []
    return [_p("Operator analysis sections", "heading2"), _table(rows)]


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
    operator_view = analysis.get("operator_view") if isinstance(analysis, dict) else None
    if isinstance(operator_view, dict) and operator_view.get("version") == 2:
        return operator_view
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


def _economics_elements(economics: dict[str, Any]) -> list[DocxElement]:
    if not economics:
        return [
            _p("Будущий расчет экономики", "heading"),
            _p("Минимальная возможная цена, найденные товары, поставщики, доставка, налоги, маржа и ставка будут добавлены после подключения товарного поиска и аналитиков.", "normal"),
        ]
    rows = [
        ["Статус", _economics_status(economics.get("status"))],
        ["НМЦК/выручка", _money(economics.get("revenue"))],
        ["Себестоимость поставщика", _money(economics.get("supplier_cost"))],
        ["Резерв риска", f"{_money(economics.get('risk_reserve'))} / {_percent(economics.get('risk_reserve_rate_percent'))}"],
        ["Итого затраты", _money(economics.get("estimated_total_cost"))],
        ["Маржа", f"{_money(economics.get('gross_margin'))} / {_percent(economics.get('margin_percent'))}"],
        ["Не хватает цен", ", ".join(economics.get("missing_cost_inputs") or []) or "нет"],
        ["Риски исполнения", ", ".join(economics.get("risk_types") or []) or "нет"],
    ]
    elements = [_p("Черновик экономики", "heading"), _table(rows)]
    if economics.get("recommendation"):
        elements.append(_p(_value(economics.get("recommendation")), "normal"))
    item_rows = [["Товар", "Кол-во", "Себестоимость", "Доп. расходы"]]
    for item in economics.get("items") or []:
        if not isinstance(item, dict):
            continue
        item_rows.append(
            [
                _value(item.get("product_name")),
                f"{_value(item.get('quantity'))} {_value(item.get('unit'), '')}".strip(),
                _money(item.get("total_cost")),
                _money(item.get("extra_costs")),
            ]
        )
    if len(item_rows) > 1:
        elements.extend([_p("Позиции расчета", "heading2"), _table(item_rows)])
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
            body_parts.append(_table_xml(payload))
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
    style_id = {"title": "Title", "heading": "Heading1", "heading2": "Heading2"}.get(style, "Normal")
    return (
        "<w:p>"
        f"<w:pPr><w:pStyle w:val=\"{style_id}\"/></w:pPr>"
        f"<w:r><w:t xml:space=\"preserve\">{html.escape(str(text))}</w:t></w:r>"
        "</w:p>"
    )


def _table_xml(rows: list[list[Any]]) -> str:
    body = "".join(_row_xml(row) for row in rows)
    return (
        "<w:tbl>"
        "<w:tblPr>"
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


def _row_xml(row: list[Any]) -> str:
    return f"<w:tr>{''.join(_cell_xml(value) for value in row)}</w:tr>"


def _cell_xml(value: Any) -> str:
    return (
        "<w:tc>"
        '<w:tcPr><w:tcW w:w="2400" w:type="dxa"/></w:tcPr>'
        f"{_paragraph_xml(_value(value, ''), 'normal')}"
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
        '<w:style w:type="paragraph" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
        '<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:rPr><w:b/><w:sz w:val="20"/></w:rPr></w:style>'
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
