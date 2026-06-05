from __future__ import annotations

import re
from typing import Any


TOKEN_RE = re.compile(r"[0-9a-z\u0430-\u044f\u0451]+", re.IGNORECASE)

STOP_WORDS = {
    "and",
    "for",
    "from",
    "with",
    "the",
    "item",
    "goods",
    "product",
    "products",
    "service",
    "services",
    "device",
    "devices",
    "printing",
    "electrophotographic",
    "office",
    "\u0434\u043b\u044f",
    "\u0438",
    "\u0438\u0437",
    "\u0441",
    "\u0432",
    "\u043d\u0430",
    "\u043f\u043e",
    "\u0442\u043e\u0432\u0430\u0440",
    "\u0442\u043e\u0432\u0430\u0440\u0430",
    "\u0442\u043e\u0432\u0430\u0440\u044b",
    "\u0443\u0441\u043b\u0443\u0433\u0430",
    "\u0443\u0441\u043b\u0443\u0433\u0438",
    "\u0443\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432",
    "\u0443\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u043e",
    "\u043f\u0435\u0447\u0430\u0442\u0430\u044e\u0449\u0438\u0445",
    "\u044d\u043b\u0435\u043a\u0442\u0440\u043e\u0444\u043e\u0442\u043e\u0433\u0440\u0430\u0444\u0438\u0447\u0435\u0441\u043a\u0438\u0445",
    "\u043e\u0444\u0438\u0441\u043d\u0430\u044f",
    "\u043e\u0444\u0438\u0441\u043d\u043e\u0439",
    "\u0437\u0430\u043a\u0443\u043f\u043a\u0430",
    "\u0437\u0430\u043a\u0443\u043f\u043a\u0438",
    "\u043f\u043e\u043a\u0443\u043f\u043a\u0430",
    "\u043f\u043e\u043a\u0443\u043f\u043a\u0438",
    "\u043f\u043e\u0441\u0442\u0430\u0432\u043a\u0430",
    "\u043f\u043e\u0441\u0442\u0430\u0432\u043a\u0438",
    "\u043f\u0440\u0438\u043e\u0431\u0440\u0435\u0442\u0435\u043d\u0438\u0435",
    "\u0442\u0435\u0445\u043d\u0438\u043a\u0430",
    "\u0442\u0435\u0445\u043d\u0438\u043a\u0438",
}

RUSSIAN_STEM_ENDINGS = (
    "\u0438\u044f\u043c\u0438",
    "\u044f\u043c\u0438",
    "\u0430\u043c\u0438",
    "\u043e\u0433\u043e",
    "\u0435\u0433\u043e",
    "\u0435\u043c\u0443",
    "\u044b\u043c\u0438",
    "\u0438\u043c\u0438",
    "\u0430\u044f",
    "\u044f\u044f",
    "\u043e\u0435",
    "\u0435\u0435",
    "\u044b\u0439",
    "\u0438\u0439",
    "\u043e\u0439",
    "\u0443\u044e",
    "\u044e\u044e",
    "\u0430\u0445",
    "\u044f\u0445",
    "\u0430\u043c",
    "\u044f\u043c",
    "\u043e\u043c",
    "\u0435\u043c",
    "\u0430",
    "\u044f",
    "\u044b",
    "\u0438",
    "\u0443",
    "\u044e",
    "\u0435",
    "\u043e",
)

FAMILY_PREFIXES = {
    "cartridge": {
        "cartridge",
        "toner",
        "laserjet",
        "\u043a\u0430\u0440\u0442\u0440\u0438\u0434\u0436",
        "\u0442\u043e\u043d\u0435\u0440",
        "\u0444\u043e\u0442\u043e\u0431\u0430\u0440\u0430\u0431\u0430\u043d",
    },
    "office_paper": {
        "paper",
        "\u0431\u0443\u043c\u0430\u0433",
    },
    "pen": {
        "pen",
        "\u0440\u0443\u0447\u043a",
    },
    "sharpener": {
        "sharpener",
        "\u0442\u043e\u0447\u0438\u043b\u043a",
    },
    "pencil": {
        "pencil",
        "\u043a\u0430\u0440\u0430\u043d\u0434\u0430\u0448",
    },
    "adhesive_tape": {
        "tape",
        "\u043a\u043b\u0435\u0439\u043a",
        "\u0441\u043a\u043e\u0442\u0447",
    },
    "calendar": {
        "calendar",
        "\u043a\u0430\u043b\u0435\u043d\u0434\u0430\u0440",
    },
    "leaflet": {
        "leaflet",
        "\u043b\u0438\u0441\u0442\u043e\u0432\u043a",
    },
    "safety_sign": {
        "sign",
        "evacuation",
        "arrow",
        "\u0437\u043d\u0430\u043a",
        "\u044d\u0432\u0430\u043a\u0443\u0430\u0446",
        "\u0441\u0442\u0440\u0435\u043b",
    },
    "sponge": {
        "sponge",
        "\u043c\u043e\u0447\u0430\u043b",
    },
    "folder_binder": {
        "folder",
        "binder",
        "\u043f\u0430\u043f\u043a",
        "\u0441\u043a\u043e\u0440\u043e\u0441\u0448\u0438\u0432",
    },
    "mop": {
        "mop",
        "\u0448\u0432\u0430\u0431\u0440",
    },
}

FAMILY_REJECT_PREFIXES = {
    "cartridge": {
        "paper",
        "sign",
        "evacuation",
        "arrow",
        "sponge",
        "folder",
        "binder",
        "mop",
        "napkin",
        "\u0431\u0443\u043c\u0430\u0433",
        "\u0437\u043d\u0430\u043a",
        "\u044d\u0432\u0430\u043a\u0443\u0430\u0446",
        "\u0441\u0442\u0440\u0435\u043b",
        "\u043c\u043e\u0447\u0430\u043b",
        "\u043f\u0430\u043f\u043a",
        "\u0441\u043a\u043e\u0440\u043e\u0441\u0448\u0438\u0432",
        "\u0441\u0430\u043b\u0444\u0435\u0442",
    },
    "office_paper": {
        "cartridge",
        "toner",
        "sign",
        "evacuation",
        "arrow",
        "sponge",
        "folder",
        "binder",
        "\u043a\u0430\u0440\u0442\u0440\u0438\u0434\u0436",
        "\u0442\u043e\u043d\u0435\u0440",
        "\u0437\u043d\u0430\u043a",
        "\u044d\u0432\u0430\u043a\u0443\u0430\u0446",
        "\u0441\u0442\u0440\u0435\u043b",
        "\u043c\u043e\u0447\u0430\u043b",
        "\u043f\u0430\u043f\u043a",
    },
}

FAMILY_STRICT_MODIFIER_FAMILIES = {"folder_binder"}

FAMILY_WEAK_MODIFIER_PREFIXES = {
    "office",
    "офис",
    "канцеляр",
    "прочн",
}

COLORED_PAPER_PREFIXES = {
    "color",
    "colour",
    "\u0446\u0432\u0435\u0442\u043d",
    "\u043f\u0430\u0441\u0442\u0435\u043b",
    "\u0438\u043d\u0442\u0435\u043d\u0441\u0438\u0432",
    "\u044f\u0440\u043a",
}


def supplier_product_name_matches_query(query_text: Any, product_name: Any) -> bool:
    """Return True only when supplier product title fits the tender search intent."""

    query_tokens = _tokens(query_text)
    product_tokens = _tokens(product_name)
    if not query_tokens or not product_tokens:
        return True

    query_family = _detect_family(query_tokens)
    product_family = _detect_family(product_tokens)

    if query_family:
        if _has_any_prefix(product_tokens, FAMILY_REJECT_PREFIXES.get(query_family, set())):
            return False
        if product_family and product_family != query_family:
            return False
        if not product_family:
            return False
        if query_family == "office_paper" and _plain_paper_query_rejects_product(query_tokens, product_tokens):
            return False

        query_models = _model_tokens(query_tokens)
        product_models = _model_tokens(product_tokens)
        if query_models and product_models and query_models & product_models:
            return True

        query_stems = _strong_stems(query_tokens)
        product_stems = _strong_stems(product_tokens)
        if not _family_modifiers_match(query_family, query_tokens, product_tokens):
            return False
        return bool(query_stems & product_stems)

    query_models = _model_tokens(query_tokens)
    product_models = _model_tokens(product_tokens)
    if query_models and product_models and query_models & product_models:
        return True

    query_stems = _strong_stems(query_tokens)
    product_stems = _strong_stems(product_tokens)
    overlap = query_stems & product_stems
    if len(query_stems) <= 1:
        return bool(overlap)
    return len(overlap) >= 2


def _tokens(value: Any) -> list[str]:
    return [token.replace("\u0451", "\u0435") for token in TOKEN_RE.findall(str(value or "").casefold())]


def _detect_family(tokens: list[str]) -> str | None:
    for family, prefixes in FAMILY_PREFIXES.items():
        if _has_any_prefix(tokens, prefixes):
            return family
    return None


def _has_any_prefix(tokens: list[str], prefixes: set[str]) -> bool:
    return any(any(token.startswith(prefix) for prefix in prefixes) for token in tokens)


def _plain_paper_query_rejects_product(query_tokens: list[str], product_tokens: list[str]) -> bool:
    query_mentions_color = _has_any_prefix(query_tokens, COLORED_PAPER_PREFIXES)
    product_mentions_color = _has_any_prefix(product_tokens, COLORED_PAPER_PREFIXES)
    return product_mentions_color and not query_mentions_color


def _strong_stems(tokens: list[str]) -> set[str]:
    stems: set[str] = set()
    for token in tokens:
        if token.isdigit() or len(token) < 4 or token in STOP_WORDS:
            continue
        stems.add(_stem_token(token))
    return stems


def _family_modifiers_match(query_family: str, query_tokens: list[str], product_tokens: list[str]) -> bool:
    if query_family not in FAMILY_STRICT_MODIFIER_FAMILIES:
        return True
    query_modifiers = _family_modifier_stems(query_tokens, query_family)
    if not query_modifiers:
        return True
    product_modifiers = _family_modifier_stems(product_tokens, query_family)
    return bool(query_modifiers & product_modifiers)


def _family_modifier_stems(tokens: list[str], family: str) -> set[str]:
    family_prefixes = FAMILY_PREFIXES.get(family, set())
    modifiers: set[str] = set()
    for token in tokens:
        if token.isdigit() or len(token) < 4 or token in STOP_WORDS:
            continue
        if any(token.startswith(prefix) for prefix in family_prefixes):
            continue
        if any(token.startswith(prefix) for prefix in FAMILY_WEAK_MODIFIER_PREFIXES):
            continue
        modifiers.add(_stem_token(token))
    return modifiers


def _stem_token(token: str) -> str:
    if _is_cyrillic_token(token):
        for ending in RUSSIAN_STEM_ENDINGS:
            if token.endswith(ending) and len(token) - len(ending) >= 4:
                stem = token[: -len(ending)]
                return stem[:-1] if stem.endswith("нн") and len(stem) > 4 else stem
    return token[:6]


def _is_cyrillic_token(token: str) -> bool:
    return any("\u0430" <= char <= "\u044f" for char in token)


def _model_tokens(tokens: list[str]) -> set[str]:
    models: set[str] = set()
    for token in tokens:
        has_digit = any(char.isdigit() for char in token)
        has_alpha = any(char.isalpha() for char in token)
        if has_digit and has_alpha and len(token) >= 3:
            models.add(token)
        elif token.isdigit() and len(token) >= 4:
            models.add(token)
    return models
