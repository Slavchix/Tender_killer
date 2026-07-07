from __future__ import annotations

import html
from io import BytesIO
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile


DocxElement = tuple[str, Any, str]


def paragraph(text: str, style: str = "normal") -> DocxElement:
    return ("p", text, style)


def table(rows: list[list[Any]], style: str = "") -> DocxElement:
    return ("table", rows, style)


def docx_bytes(elements: list[DocxElement]) -> bytes:
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
