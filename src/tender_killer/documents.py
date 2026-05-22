from __future__ import annotations

import html
import json
import re
import zlib
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

import httpx

from tender_killer.models import Tender


@dataclass(frozen=True)
class DownloadedDocument:
    url: str
    path: Path
    content_type: str | None = None


@dataclass(frozen=True)
class ExtractedDocument:
    path: Path
    text: str
    status: str
    warnings: tuple[str, ...] = field(default_factory=tuple)


class DocumentDownloader:
    def __init__(self, base_dir: str | Path, timeout_seconds: float = 30) -> None:
        self.base_dir = Path(base_dir)
        self.timeout_seconds = timeout_seconds

    def download(self, tender: Tender) -> list[DownloadedDocument]:
        target_dir = self.base_dir / tender.source / _safe_path_part(tender.external_id)
        target_dir.mkdir(parents=True, exist_ok=True)

        downloaded: list[DownloadedDocument] = []
        for index, url in enumerate(tender.documents, start=1):
            content, content_type = self.fetch_bytes(url)
            filename = _filename_from_url(url, content_type, index)
            path = _unique_path(target_dir / filename)
            path.write_bytes(content)
            downloaded.append(DownloadedDocument(url=url, path=path, content_type=content_type))

        _write_manifest(target_dir, tender, downloaded)
        return downloaded

    def fetch_bytes(self, url: str) -> tuple[bytes, str | None]:
        response = httpx.get(
            url,
            headers={"User-Agent": "TenderKiller/0.1 (+https://github.com/Slavchix/Tender_killer)"},
            timeout=self.timeout_seconds,
            follow_redirects=True,
        )
        response.raise_for_status()
        return response.content, response.headers.get("content-type")


class DocumentTextExtractor:
    def extract(self, path: str | Path) -> ExtractedDocument:
        document_path = Path(path)
        try:
            text, warnings = self._extract(document_path)
        except Exception as exc:  # noqa: BLE001 - extraction must not break the whole tender analysis.
            return ExtractedDocument(document_path, "", "error", (str(exc),))

        cleaned = _clean_text(text)
        if cleaned:
            return ExtractedDocument(document_path, cleaned, "ok", tuple(warnings))
        if _is_unsupported_document(warnings):
            return ExtractedDocument(document_path, "", "unsupported", tuple(warnings))
        return ExtractedDocument(
            document_path,
            "",
            "empty",
            tuple(warnings) or ("No machine-readable text extracted; document may be scanned or unsupported.",),
        )

    def _extract(self, path: Path) -> tuple[str, list[str]]:
        suffix = path.suffix.lower()
        data = path.read_bytes()
        return self._extract_bytes(data, suffix, path.name)

    def _extract_bytes(self, data: bytes, suffix: str, name: str) -> tuple[str, list[str]]:
        if suffix == ".docx":
            return _extract_docx(data), []
        if suffix == ".doc":
            if data.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
                return "", ["Legacy binary .doc text extraction is not supported yet; convert to .docx or PDF."]
            return _extract_legacy_doc(data), [
                "Legacy .doc text was extracted heuristically; verify the source document."
            ]
        if suffix == ".xlsx":
            return _extract_xlsx(data), []
        if suffix == ".zip":
            return _extract_zip(data, self), []
        if suffix == ".pdf":
            return _extract_pdf(data), []
        if suffix == ".rar":
            return "", [f"RAR archive text extraction is not supported yet for {name}; file was downloaded."]
        if suffix in {".txt", ".csv", ".xml", ".json"}:
            return _decode_text(data), []
        if suffix in {".html", ".htm"}:
            return _strip_html(_decode_text(data)), []
        return "", [f"Unsupported document type for {name}"]


class TenderDocumentProcessor:
    def __init__(self, downloader: DocumentDownloader, extractor: DocumentTextExtractor) -> None:
        self.downloader = downloader
        self.extractor = extractor

    def process(self, tender: Tender) -> list[ExtractedDocument]:
        downloaded = self.downloader.download(tender)
        results: list[ExtractedDocument] = []
        for document in downloaded:
            extracted = self.extractor.extract(document.path)
            self._write_extracted_text(document.path, extracted)
            results.append(extracted)
        return results

    def _write_extracted_text(self, document_path: Path, extracted: ExtractedDocument) -> None:
        text_dir = document_path.parent / "extracted_text"
        text_dir.mkdir(parents=True, exist_ok=True)
        text_path = text_dir / f"{document_path.stem}.txt"
        text_path.write_text(extracted.text, encoding="utf-8")


def _write_manifest(target_dir: Path, tender: Tender, documents: list[DownloadedDocument]) -> None:
    manifest = {
        "source": tender.source,
        "external_id": tender.external_id,
        "tender_url": tender.url,
        "documents": [
            {"url": document.url, "path": str(document.path), "content_type": document.content_type}
            for document in documents
        ],
    }
    (target_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _filename_from_url(url: str, content_type: str | None, index: int) -> str:
    parsed = urlparse(url)
    name = unquote(Path(parsed.path).name)
    if not name or "." not in name:
        name = f"document-{index}{_extension_from_content_type(content_type)}"
    return _safe_filename(name)


def _extension_from_content_type(content_type: str | None) -> str:
    if not content_type:
        return ".bin"
    normalized = content_type.lower()
    if "pdf" in normalized:
        return ".pdf"
    if "wordprocessingml" in normalized or "msword" in normalized:
        return ".docx"
    if "spreadsheetml" in normalized or "excel" in normalized:
        return ".xlsx"
    if "zip" in normalized:
        return ".zip"
    if "html" in normalized:
        return ".html"
    if "text" in normalized:
        return ".txt"
    return ".bin"


def _safe_path_part(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._") or "unknown"


def _safe_filename(value: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", value).strip(" ._")
    return name or "document.bin"


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 2
    while True:
        candidate = parent / f"{stem}-{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _extract_docx(data: bytes) -> str:
    with ZipFile(BytesIO(data)) as archive:
        document_xml = archive.read("word/document.xml")
    return _text_from_xml(document_xml)


def _extract_legacy_doc(data: bytes) -> str:
    if data.startswith(b"PK"):
        return _extract_docx(data)

    text = _decode_text(data.replace(b"\x00", b" "))
    if "<html" in text[:1000].lower():
        return _strip_html(text)
    if "{\\rtf" in text[:1000].lower():
        return _strip_rtf(text)
    return _printable_text(text)


def _extract_xlsx(data: bytes) -> str:
    with ZipFile(BytesIO(data)) as archive:
        shared_strings = _xlsx_shared_strings(archive)
        parts: list[str] = []
        for name in sorted(archive.namelist()):
            if name.startswith("xl/worksheets/") and name.endswith(".xml"):
                parts.extend(_xlsx_sheet_values(archive.read(name), shared_strings))
    return "\n".join(parts)


def _xlsx_shared_strings(archive: ZipFile) -> list[str]:
    try:
        raw = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(raw)
    return [" ".join(node.itertext()) for node in root.iter() if _local_name(node.tag) == "si"]


def _xlsx_sheet_values(raw: bytes, shared_strings: list[str]) -> list[str]:
    root = ET.fromstring(raw)
    values: list[str] = []
    for cell in root.iter():
        if _local_name(cell.tag) != "c":
            continue
        cell_type = cell.attrib.get("t")
        value_node = next((child for child in cell if _local_name(child.tag) == "v"), None)
        inline_node = next((child for child in cell if _local_name(child.tag) == "is"), None)
        if inline_node is not None:
            values.append(" ".join(inline_node.itertext()))
        elif value_node is not None and value_node.text is not None:
            value = value_node.text
            if cell_type == "s" and value.isdigit() and int(value) < len(shared_strings):
                values.append(shared_strings[int(value)])
            else:
                values.append(value)
    return values


def _extract_zip(data: bytes, extractor: DocumentTextExtractor) -> str:
    parts: list[str] = []
    with ZipFile(BytesIO(data)) as archive:
        for name in sorted(archive.namelist()):
            if name.endswith("/"):
                continue
            suffix = Path(name).suffix.lower()
            if suffix not in {".docx", ".xlsx", ".pdf", ".txt", ".csv", ".html", ".htm", ".xml", ".json"}:
                continue
            try:
                text, _warnings = extractor._extract_bytes(archive.read(name), suffix, name)
            except (BadZipFile, KeyError, ET.ParseError, ValueError):
                continue
            if text:
                parts.append(f"{name}\n{text}")
    return "\n\n".join(parts)


def _extract_pdf(data: bytes) -> str:
    streams = _pdf_streams(data)
    text_parts: list[str] = []
    for stream in streams:
        for literal in re.findall(rb"\((?:\\.|[^\\)])*\)", stream):
            text_parts.append(_decode_pdf_literal(literal[1:-1]))
        for array in re.findall(rb"\[((?:\s*\((?:\\.|[^\\)])*\)\s*)+)\]\s*TJ", stream):
            for literal in re.findall(rb"\((?:\\.|[^\\)])*\)", array):
                text_parts.append(_decode_pdf_literal(literal[1:-1]))
    return "\n".join(text_parts)


def _pdf_streams(data: bytes) -> list[bytes]:
    streams: list[bytes] = []
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, flags=re.DOTALL):
        stream = match.group(1)
        try:
            stream = zlib.decompress(stream)
        except zlib.error:
            pass
        streams.append(stream)
    if not streams:
        streams.append(data)
    return streams


def _decode_pdf_literal(value: bytes) -> str:
    value = (
        value.replace(rb"\(", b"(")
        .replace(rb"\)", b")")
        .replace(rb"\\", b"\\")
        .replace(rb"\n", b"\n")
        .replace(rb"\r", b"\r")
        .replace(rb"\t", b"\t")
    )
    return _decode_text(value)


def _text_from_xml(raw: bytes) -> str:
    root = ET.fromstring(raw)
    return "\n".join(text for text in root.itertext() if text.strip())


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8", "cp1251", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _strip_html(text: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(text)


def _strip_rtf(text: str) -> str:
    text = re.sub(r"\\'[0-9a-fA-F]{2}", " ", text)
    text = re.sub(r"\\[a-zA-Z]+-?\d* ?", " ", text)
    text = re.sub(r"[{}]", " ", text)
    return _printable_text(text)


def _printable_text(text: str) -> str:
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]+", " ", text)
    chunks = re.findall(r"[0-9A-Za-zА-Яа-яЁё№«».,;:!?%()\"'/\\\- ]{4,}", text)
    return "\n".join(chunk.strip() for chunk in chunks if chunk.strip())


def _clean_text(text: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _is_unsupported_document(warnings: list[str]) -> bool:
    return any("Unsupported document type" in warning or "not supported yet" in warning for warning in warnings)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
