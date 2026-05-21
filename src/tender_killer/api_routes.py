from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import unquote


@dataclass(frozen=True)
class TenderPath:
    source: str
    external_id: str


def parse_tender_path(path: str, suffix: str = "") -> TenderPath | None:
    parts = path.split("/")
    suffix_parts = [part for part in suffix.split("/") if part]
    expected_length = 5 + len(suffix_parts)
    if len(parts) != expected_length:
        return None
    if parts[:3] != ["", "api", "tenders"]:
        return None
    if suffix_parts and parts[5:] != suffix_parts:
        return None
    if not parts[3] or not parts[4]:
        return None
    return TenderPath(source=unquote(parts[3]), external_id=unquote(parts[4]))


def parse_database_table_path(path: str) -> str | None:
    parts = path.split("/")
    if len(parts) != 5 or parts[:4] != ["", "api", "db", "tables"] or not parts[4]:
        return None
    return unquote(parts[4])
