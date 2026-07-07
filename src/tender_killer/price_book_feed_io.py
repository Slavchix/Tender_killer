from __future__ import annotations

import base64
import csv
import io
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


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


def decode_base64_file(content_base64: str) -> bytes:
    try:
        return base64.b64decode(str(content_base64 or ""), validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid file content") from exc


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
