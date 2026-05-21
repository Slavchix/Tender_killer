from __future__ import annotations

import html
from io import BytesIO
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile


def build_tender_report_docx(tender: dict[str, Any]) -> bytes:
    paragraphs: list[tuple[str, str]] = [("Tender Killer: отчет по закупке", "title")]
    paragraphs.extend(
        [
            ("Паспорт закупки", "heading"),
            (f"Название: {_value(tender.get('title'))}", "normal"),
            (f"Номер: {_value(tender.get('external_id'))}", "normal"),
            (f"Источник: {_value(tender.get('source'))}", "normal"),
            (f"Ссылка: {_value(tender.get('url'))}", "normal"),
            (f"Заказчик: {_value(tender.get('customer'))}", "normal"),
            (f"Регион: {_value(tender.get('region'))}", "normal"),
            (f"Статус: {_value(tender.get('status'))}", "normal"),
            (f"НМЦК/цена: {_money(tender.get('price'))}", "normal"),
            (f"Дедлайн: {_value(tender.get('deadline_at'))}", "normal"),
            ("Что закупают", "heading"),
        ]
    )
    items = tender.get("items") or []
    if items:
        for item in items:
            paragraphs.extend(
                [
                    (f"Позиция №{_value(item.get('position_index'))}: {_value(item.get('name'))}", "normal"),
                    (
                        "Количество: "
                        f"{_value(item.get('quantity'))} {_value(item.get('unit'))}; "
                        f"цена за ед.: {_money(item.get('unit_price'))}; "
                        f"сумма: {_money(item.get('total_price'))}; "
                        f"ОКПД2/КОЗ: {_value(item.get('okpd2'))}",
                        "normal",
                    ),
                ]
            )
            if item.get("details"):
                paragraphs.append((f"Детализация: {item['details']}", "normal"))
    else:
        paragraphs.extend(
            [
                (f"Предмет по карточке: {_value(tender.get('title'))}", "normal"),
                (f"Категория: {_value(tender.get('category'))}", "normal"),
                (f"ОКПД2/КОЗ по карточке: {_value(tender.get('okpd2'))}", "normal"),
                (f"Цена по карточке: {_money(tender.get('price'))}", "normal"),
                (
                    "Структурированные позиции пока не найдены; эти данные используются как базовый предмет для будущего подбора товаров.",
                    "normal",
                ),
            ]
        )

    product_profiles = tender.get("product_profiles") or []
    product_profile_summary = _product_profile_summary(tender, product_profiles)
    paragraphs.extend(
        [
            ("Сводка товарных профилей", "heading"),
            (f"Товарные профили: {product_profile_summary['total']}", "normal"),
            (f"Готовы к поиску: {product_profile_summary['ready']}", "normal"),
            (f"Требуют проверки: {product_profile_summary['needs_review']}", "normal"),
            (f"Найдены товары: {product_profile_summary['matched']}", "normal"),
            (f"Посчитана экономика: {product_profile_summary['priced']}", "normal"),
            (f"Отклонены: {product_profile_summary['rejected']}", "normal"),
        ]
    )
    paragraphs.append(("Товарный профиль для поиска", "heading"))
    if product_profiles:
        for profile in product_profiles:
            paragraphs.extend(
                [
                    (f"Профиль №{_value(profile.get('position_index'))}: {_value(profile.get('product_name'))}", "normal"),
                    (
                        f"Категория: {_value(profile.get('category'))}; "
                        f"ОКПД2/КОЗ: {_value(profile.get('okpd2'))}; "
                        f"код классификатора: {_value(profile.get('classifier_code'))}; "
                        f"тип классификатора: {_value(profile.get('classifier_type'))}; "
                        f"количество: {_value(profile.get('quantity'))} {_value(profile.get('unit'), '')}; "
                        f"источник: {_value(profile.get('source'))}",
                        "normal",
                    ),
                    ("Поисковые фразы:", "normal"),
                    *_list_paragraphs(profile.get("search_phrases") or []),
                    ("Обязательные характеристики:", "normal"),
                    *_list_paragraphs(profile.get("required_characteristics") or ["Пока не найдены."]),
                    ("Стоп-слова для товарного поиска:", "normal"),
                    *_list_paragraphs(profile.get("stop_words") or []),
                ]
            )
    else:
        paragraphs.append(("Товарный профиль пока не сформирован.", "normal"))

    paragraphs.append(("Документы", "heading"))
    documents = tender.get("document_records") or []
    if documents:
        for document in documents:
            paragraphs.append(
                (
                    f"{_value(document.get('name'))} | {_value(document.get('document_type'))} | "
                    f"текст: {_value(document.get('text_status'))}",
                    "normal",
                )
            )
    else:
        paragraphs.append(("Документы пока не найдены.", "normal"))

    analysis = tender.get("analysis") or {}
    paragraphs.extend(
        [
            ("Выжимка ТЗ", "heading"),
            (_value(analysis.get("summary"), "Анализ ТЗ еще не выполнен."), "normal"),
            ("Требования", "heading"),
            *_list_paragraphs(analysis.get("requirements") or ["Требования пока не найдены."]),
            ("Риски", "heading"),
            *_list_paragraphs(analysis.get("risks") or ["Риски пока не найдены."]),
            ("Красные флаги", "heading"),
            *_list_paragraphs(analysis.get("red_flags") or ["Красные флаги пока не найдены."]),
            ("Предварительное решение", "heading"),
            (f"Статус: {_analysis_status(analysis.get('status'))}", "normal"),
            (f"Уверенность: {_confidence(analysis.get('confidence'))}", "normal"),
            ("Будущий расчет экономики", "heading"),
            ("Минимальная возможная цена, найденные товары, поставщики, доставка, налоги, маржа и ставка будут добавлены после подключения товарного поиска и аналитиков.", "normal"),
        ]
    )

    text_samples = [
        document.get("text_content")
        for document in documents
        if isinstance(document.get("text_content"), str) and document.get("text_content").strip()
    ]
    if text_samples:
        paragraphs.append(("Фрагменты извлеченного текста", "heading"))
        for index, text in enumerate(text_samples[:3], start=1):
            paragraphs.append((f"Фрагмент {index}: {_trim_text(text, 900)}", "normal"))

    return _docx_bytes(paragraphs)


def report_filename(tender: dict[str, Any]) -> str:
    external_id = str(tender.get("external_id") or "tender")
    return f"tender-killer-{_safe_filename(external_id)}.docx"


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


def _docx_bytes(paragraphs: list[tuple[str, str]]) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _content_types_xml())
        archive.writestr("_rels/.rels", _rels_xml())
        archive.writestr("word/document.xml", _document_xml(paragraphs))
        archive.writestr("word/styles.xml", _styles_xml())
    return buffer.getvalue()


def _document_xml(paragraphs: list[tuple[str, str]]) -> str:
    body = "\n".join(_paragraph_xml(text, style) for text, style in paragraphs)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}<w:sectPr><w:pgSz w:w=\"11906\" w:h=\"16838\"/><w:pgMar w:top=\"1134\" w:right=\"850\" w:bottom=\"1134\" w:left=\"850\"/></w:sectPr></w:body>"
        "</w:document>"
    )


def _paragraph_xml(text: str, style: str) -> str:
    style_id = {"title": "Title", "heading": "Heading1"}.get(style, "Normal")
    return (
        "<w:p>"
        f"<w:pPr><w:pStyle w:val=\"{style_id}\"/></w:pPr>"
        f"<w:r><w:t xml:space=\"preserve\">{html.escape(str(text))}</w:t></w:r>"
        "</w:p>"
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
