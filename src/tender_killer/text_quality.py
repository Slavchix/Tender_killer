from __future__ import annotations

import re
import unicodedata

_WORD_RE = re.compile(r"[^\W\d_]{3,}", flags=re.UNICODE)
_TOKEN_RE = re.compile(r"[\w./-]+", flags=re.UNICODE)


def clean_machine_text(value: str) -> str:
    lines: list[str] = []
    strong_lines = 0
    weak_lines = 0
    for line in value.splitlines():
        cleaned = re.sub(r"[ \t]+", " ", line).strip()
        if not cleaned or not is_machine_readable_text(cleaned):
            continue

        score = _meaningful_line_score(cleaned)
        if score <= 0:
            continue
        if score >= 2:
            strong_lines += 1
        else:
            weak_lines += 1
        lines.append(cleaned)

    if not lines:
        return ""
    if strong_lines == 0 and (weak_lines < 2 or len(lines) > 8):
        return ""
    return "\n".join(lines)


def is_machine_readable_text(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    if any(_is_bad_control(character) for character in text):
        return False

    visible = [character for character in text if not character.isspace()]
    if not visible:
        return False
    printable_count = sum(1 for character in visible if character.isprintable())
    if printable_count / len(visible) < 0.9:
        return False

    text_characters = sum(1 for character in visible if character.isalnum())
    if len(visible) >= 8 and text_characters < 4:
        return False
    symbol_count = sum(1 for character in visible if unicodedata.category(character)[0] in {"C", "S"})
    punctuation_count = sum(1 for character in visible if unicodedata.category(character)[0] == "P")
    if len(visible) >= 4 and (symbol_count + punctuation_count) / len(visible) > 0.3:
        return False
    return symbol_count / len(visible) <= 0.25


def _meaningful_line_score(value: str) -> int:
    visible = [character for character in value if not character.isspace()]
    if len(visible) < 3:
        return 0

    tokens = _TOKEN_RE.findall(value)
    words = _WORD_RE.findall(value)
    if len(words) >= 2:
        return 2

    has_digit = any(character.isdigit() for character in value)
    if words and has_digit and _has_separated_word_and_number(value):
        return 1
    if any(len(word) >= 6 for word in words) and len(visible) >= 8:
        return 2
    if has_digit and _looks_like_measurement(value):
        return 1
    return 0


def _looks_like_measurement(value: str) -> bool:
    return bool(
        re.search(r"(?<!\w)\d+\s*[A-Za-zА-Яа-яЁё]+(?:[./-][A-Za-zА-Яа-яЁё0-9]+)?", value)
    )


def _has_separated_word_and_number(value: str) -> bool:
    return bool(
        re.search(r"[^\W\d_]{2,}\s+[^\W_]*\d|\d+\s+[^\W\d_]{2,}", value, flags=re.UNICODE)
    )


def _is_bad_control(character: str) -> bool:
    return unicodedata.category(character)[0] == "C" and character not in {"\n", "\r", "\t"}
