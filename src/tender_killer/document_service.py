from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import httpx

from tender_killer.documents import DocumentTextExtractor
from tender_killer.schema import ensure_documents_table


def download_tender_documents_payload(
    database_path: str | Path,
    source: str,
    external_id: str,
    documents_dir: str | Path = Path("data/documents"),
    downloader=None,
    document_listing_resolver=None,
) -> dict[str, Any]:
    target_root = Path(documents_dir) / _safe_path_part(source) / _safe_path_part(external_id)
    target_root.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    failed: list[dict[str, str]] = []
    downloader = downloader or _download_file
    document_listing_resolver = document_listing_resolver or _resolve_document_listing

    with _connect(database_path) as connection:
        ensure_documents_table(connection)
        rows = _fetch_download_rows(connection, source, external_id)
        if not rows:
            tender_row = connection.execute(
                "SELECT documents_json FROM tenders WHERE source = ? AND external_id = ?",
                (source, external_id),
            ).fetchone()
            if tender_row is None:
                raise KeyError(f"Tender {source}/{external_id} not found.")
            fallback_documents = _json_list(tender_row["documents_json"])
            _insert_fallback_document_rows(connection, source, external_id, fallback_documents)
            rows = _fetch_download_rows(connection, source, external_id)
        if rows:
            expanded = _expand_document_listing_rows(
                connection,
                source,
                external_id,
                rows,
                document_listing_resolver,
                failed,
            )
            if expanded:
                rows = _fetch_download_rows(connection, source, external_id)
        for row in rows:
            filename = _safe_filename(row["name"] or _filename_from_url(row["url"]) or f"document-{row['document_index']}")
            target_path = _unique_target_path(target_root, filename)
            try:
                downloader(row["url"], target_path)
            except Exception as exc:  # noqa: BLE001 - report per-document failure to UI.
                failed.append({"url": row["url"], "error": str(exc)})
                continue
            downloaded += 1
            connection.execute(
                """
                UPDATE tender_documents
                SET name = COALESCE(name, ?), local_path = ?, downloaded_at = ?, text_status = CASE
                    WHEN text_status = 'pending' THEN 'downloaded'
                    ELSE text_status
                END
                WHERE source = ? AND external_id = ? AND url = ?
                """,
                (
                    filename,
                    str(target_path),
                    datetime.now().isoformat(timespec="seconds"),
                    source,
                    external_id,
                    row["url"],
                ),
            )
        document_records = _fetch_document_records(connection, source, external_id)
    return {"ok": True, "downloaded": downloaded, "failed": failed, "document_records": document_records}


def extract_tender_document_text_payload(
    database_path: str | Path,
    source: str,
    external_id: str,
    extractor: DocumentTextExtractor | None = None,
) -> dict[str, Any]:
    text_extractor = extractor or DocumentTextExtractor()
    extracted_count = 0
    failed: list[dict[str, str]] = []

    with _connect(database_path) as connection:
        ensure_documents_table(connection)
        exists = connection.execute(
            "SELECT 1 FROM tenders WHERE source = ? AND external_id = ?",
            (source, external_id),
        ).fetchone()
        if exists is None:
            raise KeyError(f"Tender {source}/{external_id} not found.")

        rows = connection.execute(
            """
            SELECT url, local_path
            FROM tender_documents
            WHERE source = ? AND external_id = ?
            ORDER BY document_index
            """,
            (source, external_id),
        ).fetchall()
        for row in rows:
            url = str(row["url"])
            local_path = str(row["local_path"] or "")
            if not local_path or not Path(local_path).exists():
                error = "local file is missing"
                failed.append({"url": url, "error": error})
                connection.execute(
                    """
                    UPDATE tender_documents
                    SET text_status = ?, text_error = ?
                    WHERE source = ? AND external_id = ? AND url = ?
                    """,
                    ("missing_file", error, source, external_id, url),
                )
                continue

            result = text_extractor.extract(local_path)
            text_error = "; ".join(result.warnings)
            connection.execute(
                """
                UPDATE tender_documents
                SET text_status = ?, text_content = ?, text_extracted_at = ?, text_error = ?
                WHERE source = ? AND external_id = ? AND url = ?
                """,
                (
                    result.status,
                    result.text,
                    datetime.now().isoformat(timespec="seconds"),
                    text_error,
                    source,
                    external_id,
                    url,
                ),
            )
            if result.status == "ok":
                extracted_count += 1
            else:
                failed.append({"url": url, "error": text_error or result.status})

        document_records = _fetch_document_records(connection, source, external_id)
    return {"ok": True, "extracted": extracted_count, "failed": failed, "document_records": document_records}


def document_row_to_payload(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    raw_payload_json = payload.pop("raw_payload_json", None)
    payload["raw_payload"] = _json_object(raw_payload_json)
    return payload


def _connect(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def _fetch_download_rows(connection: sqlite3.Connection, source: str, external_id: str) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT document_index, name, url
        FROM tender_documents
        WHERE source = ? AND external_id = ?
        ORDER BY document_index
        """,
        (source, external_id),
    ).fetchall()


def _fetch_document_records(connection: sqlite3.Connection, source: str, external_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT *
        FROM tender_documents
        WHERE source = ? AND external_id = ?
        ORDER BY document_index
        """,
        (source, external_id),
    ).fetchall()
    return [document_row_to_payload(row) for row in rows]


def _insert_fallback_document_rows(
    connection: sqlite3.Connection,
    source: str,
    external_id: str,
    documents: list[Any],
) -> None:
    rows = [
        {
            "source": source,
            "external_id": external_id,
            "document_index": index,
            "name": _filename_from_url(url) or f"document-{index}",
            "document_type": None,
            "url": url,
            "source_document_id": None,
            "raw_payload_json": "{}",
        }
        for index, url in enumerate(documents, start=1)
        if isinstance(url, str) and url
    ]
    if not rows:
        return
    connection.executemany(
        """
        INSERT OR IGNORE INTO tender_documents (
            source, external_id, document_index, name, document_type, url,
            source_document_id, raw_payload_json
        )
        VALUES (
            :source, :external_id, :document_index, :name, :document_type, :url,
            :source_document_id, :raw_payload_json
        )
        """,
        rows,
    )


def _expand_document_listing_rows(
    connection: sqlite3.Connection,
    source: str,
    external_id: str,
    rows: list[sqlite3.Row],
    resolver,
    failed: list[dict[str, str]],
) -> bool:
    expanded_any = False
    for row in rows:
        url = str(row["url"] or "")
        if not _is_document_listing_url(url):
            continue
        try:
            documents = resolver(url)
        except Exception as exc:  # noqa: BLE001 - surface source errors to the UI.
            failed.append({"url": url, "error": str(exc)})
            continue
        records = _document_rows_from_listing(source, external_id, documents)
        if not records:
            continue
        connection.execute(
            "DELETE FROM tender_documents WHERE source = ? AND external_id = ? AND url = ?",
            (source, external_id, url),
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO tender_documents (
                source, external_id, document_index, name, document_type, url,
                source_document_id, raw_payload_json
            )
            VALUES (
                :source, :external_id, :document_index, :name, :document_type, :url,
                :source_document_id, :raw_payload_json
            )
            """,
            records,
        )
        expanded_any = True
    return expanded_any


def _document_rows_from_listing(
    source: str,
    external_id: str,
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, document in enumerate(documents, start=1):
        url = document.get("Url") or document.get("url") or document.get("href") or document.get("downloadUrl")
        if not url:
            continue
        rows.append(
            {
                "source": source,
                "external_id": external_id,
                "document_index": index,
                "name": document.get("FileName") or document.get("UserFileNameFromOuterSystem") or document.get("name"),
                "document_type": document.get("Type") or document.get("type") or document.get("DocumentType"),
                "url": str(url),
                "source_document_id": str(document.get("Id") or document.get("id") or "") or None,
                "raw_payload_json": json.dumps(document, ensure_ascii=False),
            }
        )
    return rows


def _is_document_listing_url(url: str) -> bool:
    return "/GetTradeDocuments" in url


def _resolve_document_listing(url: str) -> list[dict[str, Any]]:
    response = httpx.get(
        url,
        headers={"Accept": "application/json, text/plain, */*", "XXX-TenantId-Header": "2"},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def _download_file(url: str, target_path: Path) -> None:
    with httpx.stream("GET", url, follow_redirects=True, timeout=60) as response:
        response.raise_for_status()
        with target_path.open("wb") as file:
            for chunk in response.iter_bytes():
                file.write(chunk)


def _json_list(value: str | None) -> list[Any]:
    if not value:
        return []
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _json_object(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _safe_path_part(value: str) -> str:
    return re.sub(r"[^A-Za-zА-Яа-я0-9_.-]+", "_", value).strip("._") or "item"


def _safe_filename(value: str) -> str:
    name = Path(value.replace("\\", "/")).name
    safe = re.sub(r"[^A-Za-zА-Яа-я0-9_.() -]+", "_", name).strip()
    return safe or "document"


def _unique_target_path(directory: Path, filename: str) -> Path:
    target = directory / filename
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    index = 2
    while True:
        candidate = directory / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def _filename_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    for key in ("fileName", "name"):
        if key in query and query[key]:
            return query[key][-1]
    name = Path(unquote(parsed.path)).name
    return name or None
