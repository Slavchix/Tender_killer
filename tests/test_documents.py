from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile

from tender_killer.documents import DocumentDownloader, DocumentTextExtractor, TenderDocumentProcessor
from tender_killer.models import Tender


def _zip_bytes(files: dict[str, str | bytes]) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def _docx_bytes(text: str) -> bytes:
    return _zip_bytes(
        {
            "word/document.xml": (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>"
            )
        }
    )


def _xlsx_bytes(*values: str) -> bytes:
    shared_strings = "".join(f"<si><t>{value}</t></si>" for value in values)
    cells = "".join(
        f'<c r="A{index}" t="s"><v>{index - 1}</v></c>'
        for index, _ in enumerate(values, start=1)
    )
    return _zip_bytes(
        {
            "xl/sharedStrings.xml": (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                f"{shared_strings}</sst>"
            ),
            "xl/worksheets/sheet1.xml": (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                f"<sheetData><row>{cells}</row></sheetData></worksheet>"
            ),
        }
    )


def test_downloader_saves_documents_and_manifest(tmp_path):
    tender = Tender(
        source="moscow_supplier_portal",
        external_id="10205128",
        url="https://example.test/tender",
        title="Decorations",
        documents=["https://example.test/files/spec.docx"],
    )
    downloader = DocumentDownloader(tmp_path)
    downloader.fetch_bytes = lambda url: (b"doc-content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    results = downloader.download(tender)

    assert len(results) == 1
    assert results[0].path.read_bytes() == b"doc-content"
    assert results[0].path.name == "spec.docx"
    manifest = results[0].path.parent / "manifest.json"
    assert "https://example.test/files/spec.docx" in manifest.read_text(encoding="utf-8")


def test_docx_extractor_reads_document_text(tmp_path):
    path = tmp_path / "spec.docx"
    path.write_bytes(_docx_bytes("Office paper whiteness 146 CIE"))

    result = DocumentTextExtractor().extract(path)

    assert result.status == "ok"
    assert "Office paper whiteness 146 CIE" in result.text


def test_legacy_doc_extractor_reads_cp1251_text(tmp_path):
    path = tmp_path / "spec.doc"
    path.write_bytes("Срок поставки 10 календарных дней".encode("cp1251"))

    result = DocumentTextExtractor().extract(path)

    assert result.status == "ok"
    assert "Срок поставки 10 календарных дней" in result.text


def test_binary_doc_extractor_reports_unsupported_status(tmp_path):
    path = tmp_path / "binary.doc"
    path.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 128)

    result = DocumentTextExtractor().extract(path)

    assert result.status == "unsupported"
    assert "binary .doc" in result.warnings[0]


def test_unsupported_rar_extractor_reports_unsupported_status(tmp_path):
    path = tmp_path / "attachments.rar"
    path.write_bytes(b"Rar!\x1a\x07\x00")

    result = DocumentTextExtractor().extract(path)

    assert result.status == "unsupported"
    assert "RAR" in result.warnings[0]


def test_xlsx_extractor_reads_shared_strings(tmp_path):
    path = tmp_path / "positions.xlsx"
    path.write_bytes(_xlsx_bytes("Paper A4", "80 g/m2"))

    result = DocumentTextExtractor().extract(path)

    assert result.status == "ok"
    assert "Paper A4" in result.text
    assert "80 g/m2" in result.text


def test_zip_extractor_reads_supported_nested_files(tmp_path):
    path = tmp_path / "archive.zip"
    path.write_bytes(
        _zip_bytes(
            {
                "spec.docx": _docx_bytes("Nested contract text"),
                "readme.txt": "Plain attachment",
            }
        )
    )

    result = DocumentTextExtractor().extract(path)

    assert result.status == "ok"
    assert "Nested contract text" in result.text
    assert "Plain attachment" in result.text


def test_pdf_extractor_reads_simple_literal_text(tmp_path):
    path = tmp_path / "contract.pdf"
    path.write_bytes(b"%PDF-1.4\n1 0 obj\nstream\nBT (Delivery within 5 days) Tj ET\nendstream\nendobj\n%%EOF")

    result = DocumentTextExtractor().extract(path)

    assert result.status == "ok"
    assert "Delivery within 5 days" in result.text


def test_pdf_extractor_rejects_binary_literal_garbage(tmp_path):
    path = tmp_path / "contract.pdf"
    path.write_bytes(
        b"%PDF-1.4\n1 0 obj\nstream\nBT (\x02=\x02j\x02Z\x02`\x02^\x02Z\x02g\x02k) Tj ET\nendstream\nendobj\n%%EOF"
    )

    result = DocumentTextExtractor().extract(path)

    assert result.status == "empty"
    assert result.text == ""
    assert "machine-readable" in result.warnings[0]


def test_pdf_extractor_rejects_fragmented_pdf_literal_noise(tmp_path):
    path = tmp_path / "contract.pdf"
    noise = "\n".join(
        [
            "1",
            "2",
            "3",
            "л",
            "л",
            "·",
            "!",
            "C#Ce",
            "ёяАІ",
            "lOK8",
            "ёякаґ",
            "4-'0VWёяА@#",
            "T42UV",
        ]
    )
    path.write_bytes(f"%PDF-1.4\nstream\nBT ({noise}) Tj ET\nendstream\n%%EOF".encode("utf-8"))

    result = DocumentTextExtractor().extract(path)

    assert result.status == "empty"
    assert result.text == ""
    assert "machine-readable" in result.warnings[0]


def test_processor_downloads_documents_and_writes_extracted_text(tmp_path):
    tender = Tender(
        source="mosreg_market",
        external_id="3668200",
        url="https://example.test/tender",
        title="Office supplies",
        documents=["https://example.test/spec.docx"],
    )
    downloader = DocumentDownloader(tmp_path / "documents")
    downloader.fetch_bytes = lambda url: (_docx_bytes("Specification text"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    processor = TenderDocumentProcessor(downloader, DocumentTextExtractor())

    results = processor.process(tender)

    assert len(results) == 1
    assert results[0].status == "ok"
    text_path = tmp_path / "documents" / "mosreg_market" / "3668200" / "extracted_text" / "spec.txt"
    assert text_path.read_text(encoding="utf-8") == "Specification text"
