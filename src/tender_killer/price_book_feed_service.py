from __future__ import annotations

import base64
import csv
import io
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from tender_killer.price_candidate_service import normalize_price_candidate
from tender_killer.product_profile_service import ensure_product_profiles
from tender_killer.storage import TenderStore


TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)
NUMERIC_FIELDS = {
    "position_index",
    "unit_price",
    "vat_rate_percent",
    "delivery_cost",
    "pack_quantity",
    "stock_quantity",
    "minimum_order_quantity",
    "minimum_order_amount",
}
HEADER_ALIASES = {
    "position_index": "position_index",
    "position": "position_index",
    "pos": "position_index",
    "позиция": "position_index",
    "supplier": "supplier_name",
    "supplier_name": "supplier_name",
    "vendor": "supplier_name",
    "поставщик": "supplier_name",
    "sku": "sku",
    "article": "sku",
    "артикул": "sku",
    "product_name": "product_name",
    "item_name": "product_name",
    "name": "product_name",
    "товар": "product_name",
    "наименование": "product_name",
    "описание": "description",
    "description": "description",
    "price": "unit_price",
    "unit_price": "unit_price",
    "цена": "unit_price",
    "цена_за_ед": "unit_price",
    "цена_за_единицу": "unit_price",
    "unit": "unit",
    "uom": "unit",
    "ед": "unit",
    "единица": "unit",
    "vat": "vat_rate_percent",
    "nds": "vat_rate_percent",
    "ндс": "vat_rate_percent",
    "delivery": "delivery_cost",
    "delivery_cost": "delivery_cost",
    "доставка": "delivery_cost",
    "pack": "pack_quantity",
    "pack_quantity": "pack_quantity",
    "упаковка": "pack_quantity",
    "stock": "stock_quantity",
    "stock_quantity": "stock_quantity",
    "остаток": "stock_quantity",
    "min_order_quantity": "minimum_order_quantity",
    "minimum_order_quantity": "minimum_order_quantity",
    "мин_заказ": "minimum_order_quantity",
    "min_order_amount": "minimum_order_amount",
    "minimum_order_amount": "minimum_order_amount",
    "min_sum": "minimum_order_amount",
    "url": "source_url",
    "source_url": "source_url",
    "ссылка": "source_url",
    "valid_until": "valid_until",
    "актуально_до": "valid_until",
}
STAGE_MODES = {"all", "confident", "review", "errors"}
STOP_WORDS = {
    "and",
    "for",
    "the",
    "item",
    "product",
    "goods",
    "товар",
    "товары",
    "для",
}


def stage_tender_price_book_feed(
    database_path: str | Path,
    source: str,
    external_id: str,
    rows: list[dict[str, Any]],
    *,
    feed_name: str = "price book",
    stage_mode: str = "all",
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = ensure_product_profiles(database_path, source, external_id)
    stage_mode = _stage_mode(stage_mode)
    profiles_by_position = {
        int(profile.get("position_index") or 0): profile
        for profile in profiles
        if int(profile.get("position_index") or 0) > 0
    }

    staged_count = 0
    matched_count = 0
    skipped_count = 0
    position_counts: dict[int, int] = {}
    quality_rows: list[dict[str, Any]] = []

    for row_index, row in enumerate(rows, start=1):
        assessment = _assess_feed_row(row_index, row, profiles, profiles_by_position)
        quality_rows.append(assessment)
        if not assessment["can_stage"]:
            assessment["stage_action"] = "error" if assessment["status"] == "error" else "left_for_review"
            skipped_count += 1
            continue
        if not _stage_mode_allows(stage_mode, assessment):
            assessment["stage_action"] = "left_for_review"
            skipped_count += 1
            continue

        profile = assessment["_profile"]
        match_reason = assessment["reason"]
        candidate = _candidate_from_feed_row(row, profile, feed_name=feed_name, row_index=row_index, match_reason=match_reason)
        if not candidate:
            assessment["status"] = "error"
            assessment["reason"] = "missing_unit_price"
            assessment["can_stage"] = False
            assessment["stage_action"] = "error"
            skipped_count += 1
            continue
        normalized = normalize_price_candidate(profile, candidate)
        saved = store.upsert_price_candidates(
            source,
            external_id,
            int(profile["position_index"]),
            [normalized],
            origin="price_book_feed",
        )
        if not saved:
            assessment["stage_action"] = "error"
            skipped_count += 1
            continue
        assessment["stage_action"] = "staged"
        matched_count += 1
        staged_count += len(saved)
        position = int(profile["position_index"])
        position_counts[position] = position_counts.get(position, 0) + len(saved)

    return {
        "ok": True,
        "feed_name": feed_name,
        "stage_mode": stage_mode,
        "rows_count": len(rows),
        "matched_count": matched_count,
        "staged_count": staged_count,
        "skipped_count": skipped_count,
        "quality_report": _quality_report(quality_rows, stage_mode),
        "positions": [
            {"position_index": position, "staged_count": count}
            for position, count in sorted(position_counts.items())
        ],
    }


def stage_tender_price_book_feed_file(
    database_path: str | Path,
    source: str,
    external_id: str,
    *,
    file_name: str,
    content_base64: str,
    feed_name: str = "price book",
    stage_mode: str = "all",
) -> dict[str, Any]:
    file_bytes = _decode_base64_file(content_base64)
    rows, file_import = parse_price_book_feed_file(file_name, file_bytes)
    result = stage_tender_price_book_feed(
        database_path,
        source,
        external_id,
        rows,
        feed_name=feed_name,
        stage_mode=stage_mode,
    )
    result["file_import"] = file_import
    return result


def parse_price_book_feed_file(file_name: str, file_bytes: bytes) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    suffix = Path(str(file_name or "")).suffix.casefold()
    if suffix in {".xlsx", ".xlsm"}:
        rows = _rows_from_xlsx(file_bytes)
        file_type = "xlsx"
    elif suffix in {".csv", ".tsv", ".txt", ""}:
        rows = _rows_from_delimited_file(file_bytes)
        file_type = "csv" if suffix != ".tsv" else "tsv"
    else:
        raise ValueError("unsupported price book file type")
    return rows, {
        "file_name": str(file_name or "price-book"),
        "file_type": file_type,
        "rows_count": len(rows),
    }


def _assess_feed_row(
    row_index: int,
    row: Any,
    profiles: list[dict[str, Any]],
    profiles_by_position: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(row, dict):
        return _quality_row(row_index, "error", "invalid_row")
    unit_price = _number(row.get("unit_price") or row.get("price"))
    if unit_price is None or unit_price <= 0:
        return _quality_row(row_index, "error", "missing_unit_price", row=row)
    match = _match_feed_row(row, profiles, profiles_by_position)
    if match is None:
        return _quality_row(row_index, "review", "no_matching_position", row=row)
    profile, match_reason = match
    status = "exact_position" if match_reason == "position_index" else "name_match"
    return _quality_row(row_index, status, match_reason, row=row, profile=profile, can_stage=True)


def _quality_row(
    row_index: int,
    status: str,
    reason: str,
    *,
    row: dict[str, Any] | None = None,
    profile: dict[str, Any] | None = None,
    can_stage: bool = False,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "row_index": row_index,
        "status": status,
        "reason": reason,
        "can_stage": can_stage,
        "stage_action": "pending",
    }
    if row:
        result["product_name"] = _text(row.get("product_name") or row.get("name") or row.get("item_name") or row.get("description"))
        result["unit_price"] = _number(row.get("unit_price") or row.get("price"))
        result["supplier_name"] = _text(row.get("supplier_name") or row.get("supplier") or row.get("vendor"))
    if profile:
        result["_profile"] = profile
        result["position_index"] = int(profile.get("position_index") or 0)
        result["matched_product_name"] = _text(profile.get("product_name"))
    return result


def _quality_report(rows: list[dict[str, Any]], stage_mode: str) -> dict[str, Any]:
    public_rows = [_public_quality_row(row) for row in rows]
    summary = {
        "rows_count": len(rows),
        "exact_position_count": sum(1 for row in rows if row["status"] == "exact_position"),
        "name_match_count": sum(1 for row in rows if row["status"] == "name_match"),
        "review_count": sum(1 for row in rows if row["status"] == "review"),
        "error_count": sum(1 for row in rows if row["status"] == "error"),
        "stageable_count": sum(1 for row in rows if row.get("can_stage")),
        "selected_count": sum(1 for row in rows if row.get("can_stage") and _stage_mode_allows(stage_mode, row)),
    }
    return {
        "stage_mode": stage_mode,
        "summary": summary,
        "rows": public_rows,
    }


def _public_quality_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "_profile"}


def _stage_mode(value: Any) -> str:
    text = str(value or "all").strip().casefold()
    return text if text in STAGE_MODES else "all"


def _stage_mode_allows(stage_mode: str, row: dict[str, Any]) -> bool:
    if stage_mode == "errors":
        return False
    if stage_mode == "confident":
        return row.get("status") == "exact_position"
    if stage_mode == "review":
        return row.get("status") == "name_match"
    return row.get("status") in {"exact_position", "name_match"}


def _match_feed_row(
    row: dict[str, Any],
    profiles: list[dict[str, Any]],
    profiles_by_position: dict[int, dict[str, Any]],
) -> tuple[dict[str, Any], str] | None:
    position = _integer(row.get("position_index") or row.get("position") or row.get("pos"))
    if position and position in profiles_by_position:
        return profiles_by_position[position], "position_index"

    row_tokens = _tokens(
        row.get("product_name"),
        row.get("name"),
        row.get("item_name"),
        row.get("description"),
        row.get("sku"),
        row.get("article"),
    )
    if not row_tokens:
        return None

    best_profile: dict[str, Any] | None = None
    best_score = 0
    for profile in profiles:
        profile_tokens = _tokens(profile.get("product_name"), profile.get("normalized_name"), profile.get("details"))
        if not profile_tokens:
            continue
        score = len(row_tokens & profile_tokens)
        if score > best_score:
            best_score = score
            best_profile = profile

    if best_profile is None:
        return None
    threshold = 2 if len(row_tokens) >= 2 else 1
    return (best_profile, "name_match") if best_score >= threshold else None


def _decode_base64_file(content_base64: str) -> bytes:
    try:
        return base64.b64decode(str(content_base64 or ""), validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid file content") from exc


def _rows_from_delimited_file(file_bytes: bytes) -> list[dict[str, Any]]:
    text = _decode_text(file_bytes)
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return []
    delimiter = _detect_delimiter(lines[0])
    reader = csv.DictReader(io.StringIO("\n".join(lines)), delimiter=delimiter)
    rows = []
    for raw_row in reader:
        row = _normalized_feed_row(raw_row)
        if row:
            rows.append(row)
    return rows


def _rows_from_xlsx(file_bytes: bytes) -> list[dict[str, Any]]:
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
            shared_strings = _xlsx_shared_strings(archive)
            sheet_name = _first_sheet_name(archive)
            sheet_root = ElementTree.fromstring(archive.read(sheet_name))
    except (KeyError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        raise ValueError("invalid xlsx file") from exc

    namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    table_rows: list[list[str]] = []
    for row_node in sheet_root.findall(f".//{namespace}row"):
        values_by_column: dict[int, str] = {}
        for cell_node in row_node.findall(f"{namespace}c"):
            column_index = _xlsx_column_index(str(cell_node.get("r") or ""))
            values_by_column[column_index] = _xlsx_cell_value(cell_node, shared_strings, namespace)
        if values_by_column:
            max_index = max(values_by_column)
            table_rows.append([values_by_column.get(index, "") for index in range(max_index + 1)])

    if len(table_rows) < 2:
        return []
    headers = table_rows[0]
    rows = []
    for values in table_rows[1:]:
        raw_row = {headers[index]: values[index] for index in range(min(len(headers), len(values)))}
        row = _normalized_feed_row(raw_row)
        if row:
            rows.append(row)
    return rows


def _xlsx_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    strings: list[str] = []
    for item in root.findall(f"{namespace}si"):
        text = "".join(node.text or "" for node in item.findall(f".//{namespace}t"))
        strings.append(text)
    return strings


def _first_sheet_name(archive: zipfile.ZipFile) -> str:
    names = sorted(name for name in archive.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"))
    if not names:
        raise KeyError("worksheet")
    return names[0]


def _xlsx_cell_value(cell_node: ElementTree.Element, shared_strings: list[str], namespace: str) -> str:
    cell_type = cell_node.get("t")
    value_node = cell_node.find(f"{namespace}v")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell_node.findall(f".//{namespace}t")).strip()
    value = (value_node.text or "").strip() if value_node is not None else ""
    if cell_type == "s":
        index = _integer(value)
        return shared_strings[index] if index is not None and 0 <= index < len(shared_strings) else ""
    return value


def _xlsx_column_index(reference: str) -> int:
    letters = "".join(char for char in reference if char.isalpha()).upper()
    index = 0
    for char in letters:
        index = index * 26 + (ord(char) - ord("A") + 1)
    return max(0, index - 1)


def _decode_text(file_bytes: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="replace")


def _detect_delimiter(header_line: str) -> str:
    candidates = ["\t", ";", ","]
    return max(candidates, key=lambda delimiter: str(header_line or "").count(delimiter))


def _normalized_feed_row(raw_row: dict[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for raw_key, raw_value in raw_row.items():
        key = _normalize_feed_header(raw_key)
        if not key:
            continue
        value = str(raw_value or "").strip()
        if not value:
            continue
        row[key] = _parse_feed_value(key, value)
    return row


def _normalize_feed_header(header: Any) -> str:
    key = (
        str(header or "")
        .strip()
        .casefold()
        .replace("ё", "е")
    )
    key = re.sub(r"[№#]", "", key)
    key = re.sub(r"[^a-zа-я0-9]+", "_", key, flags=re.UNICODE).strip("_")
    return HEADER_ALIASES.get(key, "")


def _parse_feed_value(key: str, value: Any) -> Any:
    if key not in NUMERIC_FIELDS:
        return value
    number = _number(value)
    return number if number is not None else value


def _candidate_from_feed_row(
    row: dict[str, Any],
    profile: dict[str, Any],
    *,
    feed_name: str,
    row_index: int,
    match_reason: str,
) -> dict[str, Any]:
    unit_price = _number(row.get("unit_price") or row.get("price"))
    if unit_price is None or unit_price <= 0:
        return {}
    supplier_name = _text(row.get("supplier_name") or row.get("supplier") or row.get("vendor"))
    provider = _text(row.get("provider") or supplier_name or feed_name)
    product_name = _text(row.get("product_name") or row.get("name") or row.get("item_name")) or _text(profile.get("product_name"))
    raw_payload = {
        **row,
        "feed_name": feed_name,
        "row_index": row_index,
        "source_kind": "price_book_feed",
    }
    candidate = {
        "provider": provider,
        "supplier_name": supplier_name,
        "product_name": product_name,
        "name": product_name,
        "source_url": row.get("source_url") or row.get("url"),
        "source_query": row.get("source_query") or row.get("product_name") or row.get("name") or profile.get("product_name"),
        "source_kind": "price_book_feed",
        "unit_price": unit_price,
        "currency": row.get("currency") or "RUB",
        "vat_mode": row.get("vat_mode"),
        "vat_rate_percent": row.get("vat_rate_percent"),
        "availability": row.get("availability"),
        "delivery_note": row.get("delivery_note"),
        "delivery_cost": row.get("delivery_cost"),
        "unit": row.get("unit") or row.get("uom") or profile.get("unit"),
        "pack_quantity": row.get("pack_quantity") or row.get("quantity_per_pack"),
        "stock_quantity": row.get("stock_quantity") or row.get("stock"),
        "preorder_quantity": row.get("preorder_quantity"),
        "minimum_order_quantity": row.get("minimum_order_quantity") or row.get("min_order_quantity"),
        "minimum_order_amount": row.get("minimum_order_amount") or row.get("min_order_amount"),
        "price_breaks": row.get("price_breaks"),
        "confidence": row.get("confidence") or "high",
        "confidence_reasons": ["price_book_feed", match_reason],
        "match_reasons": ["price_book_feed", match_reason],
        "feed_name": feed_name,
        "sku": row.get("sku") or row.get("article"),
        "valid_until": row.get("valid_until"),
        "raw_payload": raw_payload,
    }
    return {key: value for key, value in candidate.items() if value not in (None, "")}


def _tokens(*values: Any) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        for token in TOKEN_RE.findall(str(value or "").casefold()):
            if len(token) > 1 and token not in STOP_WORDS:
                tokens.add(token)
    return tokens


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _integer(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
