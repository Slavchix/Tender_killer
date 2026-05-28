from __future__ import annotations

import html
import json
import os
import re
import shlex
import subprocess
import zlib
from collections.abc import Callable
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

import httpx

from tender_killer.models import Tender
from tender_killer.text_quality import clean_machine_text


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


PdfOcrRunner = Callable[[Path], tuple[str, tuple[str, ...]]]


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
    def __init__(self, ocr_runner: PdfOcrRunner | None = None) -> None:
        self.ocr_runner = ocr_runner or _ocr_runner_from_environment()

    def extract(self, path: str | Path) -> ExtractedDocument:
        document_path = Path(path)
        try:
            text, warnings = self._extract(document_path)
        except Exception as exc:  # noqa: BLE001 - extraction must not break the whole tender analysis.
            return ExtractedDocument(document_path, "", "error", (str(exc),))

        cleaned = _clean_text(text)
        if cleaned:
            return ExtractedDocument(document_path, cleaned, "ok", tuple(warnings))
        if document_path.suffix.lower() == ".pdf" and self.ocr_runner and not _is_unsupported_document(warnings):
            ocr_text, ocr_warnings = self._extract_pdf_ocr(document_path)
            ocr_cleaned = _clean_text(ocr_text)
            combined_warnings = tuple([*warnings, *ocr_warnings])
            if ocr_cleaned:
                return ExtractedDocument(document_path, ocr_cleaned, "ok", combined_warnings)
            warnings.extend(ocr_warnings)
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

    def _extract_pdf_ocr(self, path: Path) -> tuple[str, tuple[str, ...]]:
        if not self.ocr_runner:
            return "", ()
        try:
            return self.ocr_runner(path)
        except Exception as exc:  # noqa: BLE001 - OCR is optional and must not break extraction.
            return "", (f"OCR fallback failed: {exc}",)


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


def _ocr_runner_from_environment() -> PdfOcrRunner | None:
    command = os.environ.get("TENDER_KILLER_PDF_OCR_COMMAND", "").strip()
    if not command:
        return None
    timeout = _float_env("TENDER_KILLER_PDF_OCR_TIMEOUT_SECONDS", 120.0)
    return _PdfOcrCommandRunner(command, timeout_seconds=timeout)


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, ""))
    except ValueError:
        return default


class _PdfOcrCommandRunner:
    def __init__(self, command: str, timeout_seconds: float) -> None:
        self.command = command
        self.timeout_seconds = timeout_seconds

    def __call__(self, path: Path) -> tuple[str, tuple[str, ...]]:
        args = self._args(path)
        completed = subprocess.run(
            args,
            capture_output=True,
            check=False,
            timeout=self.timeout_seconds,
        )
        warnings = [f"OCR fallback used: {Path(args[0]).name}."]
        if completed.returncode:
            stderr = _decode_text(completed.stderr).strip()
            detail = f": {stderr[:400]}" if stderr else ""
            return "", (f"OCR fallback failed with exit code {completed.returncode}{detail}",)
        stderr = _decode_text(completed.stderr).strip()
        if stderr:
            warnings.append(stderr[:400])
        return _decode_text(completed.stdout), tuple(warnings)

    def _args(self, path: Path) -> list[str]:
        parts = shlex.split(self.command, posix=os.name != "nt")
        uses_path_template = any("{path}" in part for part in parts)
        args = [_strip_wrapping_quotes(part.replace("{path}", str(path))) for part in parts]
        if not uses_path_template:
            args.append(str(path))
        return args


def _strip_wrapping_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


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
    cmap = _pdf_to_unicode_map(streams)
    text_parts: list[str] = []
    for stream in streams:
        if b"begincmap" in stream:
            continue
        for token in _pdf_text_tokens(stream):
            text_parts.append(_decode_pdf_token(token, cmap))
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


def _pdf_to_unicode_map(streams: list[bytes]) -> dict[bytes, str]:
    mapping: dict[bytes, str] = {}
    for stream in streams:
        if b"begincmap" not in stream:
            continue
        mapping.update(_pdf_bfchar_map(stream))
        mapping.update(_pdf_bfrange_map(stream))
    return mapping


def _pdf_bfchar_map(stream: bytes) -> dict[bytes, str]:
    mapping: dict[bytes, str] = {}
    for block in re.findall(rb"beginbfchar(.*?)endbfchar", stream, flags=re.DOTALL):
        for source, target in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            source_bytes = _hex_to_bytes(source)
            target_text = _decode_utf16_hex(target)
            if source_bytes and target_text:
                mapping[source_bytes] = target_text
    return mapping


def _pdf_bfrange_map(stream: bytes) -> dict[bytes, str]:
    mapping: dict[bytes, str] = {}
    for block in re.findall(rb"beginbfrange(.*?)endbfrange", stream, flags=re.DOTALL):
        consumed_spans: list[tuple[int, int]] = []
        for match in re.finditer(
            rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[(.*?)\]",
            block,
            flags=re.DOTALL,
        ):
            consumed_spans.append(match.span())
            start = int(match.group(1), 16)
            end = int(match.group(2), 16)
            source_width = len(_hex_to_bytes(match.group(1)))
            targets = re.findall(rb"<([0-9A-Fa-f]+)>", match.group(3))
            for offset, target in enumerate(targets[: max(0, end - start + 1)]):
                target_text = _decode_utf16_hex(target)
                if target_text:
                    mapping[(start + offset).to_bytes(source_width, "big")] = target_text

        block_without_arrays = _remove_spans(block, consumed_spans)
        for source_start, source_end, target_start in re.findall(
            rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>",
            block_without_arrays,
        ):
            start = int(source_start, 16)
            end = int(source_end, 16)
            target = int(target_start, 16)
            source_width = len(_hex_to_bytes(source_start))
            target_width = len(_hex_to_bytes(target_start))
            for offset in range(max(0, end - start + 1)):
                source_bytes = (start + offset).to_bytes(source_width, "big")
                target_text = _decode_utf16_codepoint(target + offset, target_width)
                if target_text:
                    mapping[source_bytes] = target_text
    return mapping


def _remove_spans(value: bytes, spans: list[tuple[int, int]]) -> bytes:
    if not spans:
        return value
    parts: list[bytes] = []
    cursor = 0
    for start, end in sorted(spans):
        parts.append(value[cursor:start])
        cursor = end
    parts.append(value[cursor:])
    return b"".join(parts)


def _pdf_text_tokens(stream: bytes) -> list[bytes]:
    token_pattern = rb"\((?:\\.|[^\\)])*\)|<[0-9A-Fa-f\s]+>"
    operator_pattern = re.compile(
        rb"(?P<token>" + token_pattern + rb")\s*Tj|(?P<array>\[(?:.*?)\]\s*TJ)",
        flags=re.DOTALL,
    )
    tokens: list[bytes] = []
    for match in operator_pattern.finditer(stream):
        token = match.group("token")
        if token is not None:
            tokens.append(token)
            continue
        array = match.group("array") or b""
        tokens.extend(token_match.group(0) for token_match in re.finditer(token_pattern, array, flags=re.DOTALL))
    return tokens


def _decode_pdf_token(token: bytes, cmap: dict[bytes, str]) -> str:
    if token.startswith(b"(") and token.endswith(b")"):
        return _decode_pdf_bytes(_pdf_literal_bytes(token[1:-1]), cmap)
    if token.startswith(b"<") and token.endswith(b">"):
        return _decode_pdf_bytes(_hex_to_bytes(re.sub(rb"\s+", b"", token[1:-1])), cmap)
    return ""


def _decode_pdf_bytes(value: bytes, cmap: dict[bytes, str]) -> str:
    if cmap:
        mapped = _decode_pdf_cmap_bytes(value, cmap)
        if mapped.strip():
            return mapped
    return _decode_text(value)


def _decode_pdf_cmap_bytes(value: bytes, cmap: dict[bytes, str]) -> str:
    lengths = sorted({len(source) for source in cmap}, reverse=True)
    if not lengths:
        return ""

    parts: list[str] = []
    index = 0
    while index < len(value):
        for length in lengths:
            chunk = value[index : index + length]
            if chunk in cmap:
                parts.append(cmap[chunk])
                index += length
                break
        else:
            byte = value[index]
            if byte in {0x09, 0x0A, 0x0D, 0x20}:
                parts.append(chr(byte))
            index += 1
    return "".join(parts)


def _decode_pdf_literal(value: bytes) -> str:
    return _decode_text(_pdf_literal_bytes(value))


def _pdf_literal_bytes(value: bytes) -> bytes:
    escapes = {
        ord("n"): b"\n",
        ord("r"): b"\r",
        ord("t"): b"\t",
        ord("b"): b"\b",
        ord("f"): b"\f",
        ord("("): b"(",
        ord(")"): b")",
        ord("\\"): b"\\",
    }
    result = bytearray()
    index = 0
    while index < len(value):
        byte = value[index]
        if byte != ord("\\"):
            result.append(byte)
            index += 1
            continue

        index += 1
        if index >= len(value):
            break
        escaped = value[index]
        if escaped in escapes:
            result.extend(escapes[escaped])
            index += 1
            continue
        if escaped in {ord("\n"), ord("\r")}:
            index += 1
            if escaped == ord("\r") and index < len(value) and value[index] == ord("\n"):
                index += 1
            continue
        if ord("0") <= escaped <= ord("7"):
            octal = bytes([escaped])
            index += 1
            while index < len(value) and len(octal) < 3 and ord("0") <= value[index] <= ord("7"):
                octal += bytes([value[index]])
                index += 1
            result.append(int(octal, 8))
            continue
        result.append(escaped)
        index += 1
    return bytes(result)


def _hex_to_bytes(value: bytes) -> bytes:
    normalized = re.sub(rb"\s+", b"", value)
    if len(normalized) % 2:
        normalized += b"0"
    try:
        return bytes.fromhex(normalized.decode("ascii"))
    except ValueError:
        return b""


def _decode_utf16_hex(value: bytes) -> str:
    raw = _hex_to_bytes(value)
    if not raw:
        return ""
    if len(raw) % 2 == 0:
        try:
            return raw.decode("utf-16-be")
        except UnicodeDecodeError:
            pass
    return _decode_text(raw)


def _decode_utf16_codepoint(value: int, width: int) -> str:
    if width <= 0:
        return ""
    try:
        return value.to_bytes(width, "big").decode("utf-16-be")
    except (OverflowError, UnicodeDecodeError):
        return ""


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
    return clean_machine_text(text)


def _is_unsupported_document(warnings: list[str]) -> bool:
    return any("Unsupported document type" in warning or "not supported yet" in warning for warning in warnings)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
