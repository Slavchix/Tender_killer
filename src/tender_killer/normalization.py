from __future__ import annotations

from datetime import datetime
from typing import Any


def first_present(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = nested_get(payload, key)
        if value not in (None, ""):
            return value
    return None


def nested_get(payload: dict[str, Any], key: str) -> Any:
    current: Any = payload
    for part in key.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def parse_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    normalized = str(value).replace("\xa0", "").replace(" ", "").replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


def parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    for candidate in (text, text.replace(" ", "T")):
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            pass
    for fmt in ("%d.%m.%Y %H:%M", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    return None


def absolute_url(base_url: str, value: Any) -> str:
    if not value:
        return base_url
    text = str(value)
    if text.startswith(("http://", "https://")):
        return text
    if text.startswith("/"):
        origin = base_url.split("/", 3)[:3]
        return "/".join(origin) + text
    return base_url.rstrip("/") + "/" + text.lstrip("/")

