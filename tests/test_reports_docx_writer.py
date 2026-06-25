from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile

from tender_killer.reports_docx_writer import docx_bytes
from tender_killer.reports_docx_writer import paragraph
from tender_killer.reports_docx_writer import table


def test_docx_writer_builds_document_xml_with_paragraphs_and_tables():
    content = docx_bytes(
        [
            paragraph("ТЗ & риск", "heading"),
            table([["Поле", "Значение"], ["Оплата", "7 дней"]]),
        ]
    )

    with ZipFile(BytesIO(content)) as archive:
        names = set(archive.namelist())
        document_xml = archive.read("word/document.xml").decode("utf-8")

    assert "[Content_Types].xml" in names
    assert "word/styles.xml" in names
    assert "ТЗ &amp; риск" in document_xml
    assert "<w:tbl>" in document_xml
    assert "Оплата" in document_xml
