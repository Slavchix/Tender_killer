from __future__ import annotations

import json
import re
from typing import Any


MOSCOW = "\u043c\u043e\u0441\u043a\u0432\u0430"
MOSCOW_OBLAST = "\u043c\u043e\u0441\u043a\u043e\u0432\u0441\u043a\u0430\u044f \u043e\u0431\u043b\u0430\u0441\u0442\u044c"


def normalize_law(raw_payload: dict[str, Any] | None) -> str | None:
    text = _payload_text(raw_payload)
    digits = re.sub(r"\D+", "", text)
    if "223" in digits:
        return "223-\u0424\u0417"
    if "44" in digits:
        return "44-\u0424\u0417"
    return None


def normalize_status(status: str | None) -> str | None:
    text = _normalize_text(status)
    if not text:
        return None
    if any(marker in text for marker in ("cancel", "\u043e\u0442\u043c\u0435\u043d", "\u0430\u043d\u043d\u0443\u043b\u0438\u0440")):
        return "cancelled"
    if any(
        marker in text
        for marker in (
            "finish",
            "complete",
            "\u0437\u0430\u0432\u0435\u0440\u0448",
            "\u043f\u0440\u043e\u0432\u0435\u0434\u0435\u043d",
            "\u0437\u0430\u043a\u043b\u044e\u0447\u0435\u043d",
            "р·р°рірµсђс",
        )
    ):
        return "completed"
    if any(
        marker in text
        for marker in (
            "active",
            "reception",
            "proposal",
            "application",
            "\u043f\u0440\u0438\u0435\u043c",
            "\u043f\u0440\u0438\u0451\u043c",
            "\u0430\u043a\u0442\u0438\u0432",
            "р°рєс‚рёрІ",
            "рїсђрёрµрј",
            "рїсђрёс‘рј",
        )
    ):
        return "active"
    return None


def normalize_region_code(region: str | None, source: str | None = None) -> str | None:
    text = _normalize_text(region)
    source_text = _normalize_text(source)
    if "mosreg" in source_text or "moscow oblast" in text or MOSCOW_OBLAST in text or "\u043c\u043e" == text:
        return "50"
    if "moscow_supplier" in source_text or "moscow" == text or MOSCOW in text:
        return "77"
    return None


def _payload_text(raw_payload: dict[str, Any] | None) -> str:
    if not raw_payload:
        return ""
    parts: list[str] = []
    for key in (
        "law",
        "lawName",
        "federalLawName",
        "FederalLawName",
        "federalLaw",
        "FederalLaw",
        "purchaseLaw",
    ):
        value = raw_payload.get(key)
        if value:
            parts.append(str(value))
    if not parts:
        parts.append(json.dumps(raw_payload, ensure_ascii=False))
    return " ".join(parts)


def _normalize_text(value: str | None) -> str:
    return str(value or "").strip().casefold().replace("\u0451", "\u0435")
