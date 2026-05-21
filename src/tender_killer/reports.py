from __future__ import annotations

import html
from io import BytesIO
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

DocxElement = tuple[str, Any, str]


def build_tender_report_docx(tender: dict[str, Any]) -> bytes:
    analysis = tender.get("analysis") or {}
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
            _p("Выжимка ТЗ", "heading"),
            _p(_value(analysis.get("summary"), "Анализ ТЗ еще не выполнен."), "normal"),
            _p("Требования", "heading"),
            *_list_elements(analysis.get("requirements") or ["Требования пока не найдены."]),
            _p("Риски", "heading"),
            *_list_elements(analysis.get("risks") or ["Риски пока не найдены."]),
            _p("Красные флаги", "heading"),
            *_list_elements(analysis.get("red_flags") or ["Красные флаги пока не найдены."]),
            _p("Будущий расчет экономики", "heading"),
            _p("Минимальная возможная цена, найденные товары, поставщики, доставка, налоги, маржа и ставка будут добавлены после подключения товарного поиска и аналитиков.", "normal"),
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


def _trim_text(value: str, limit: int) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= limit else f"{text[:limit]}..."


def _safe_filename(value: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in value).strip("._") or "tender"
