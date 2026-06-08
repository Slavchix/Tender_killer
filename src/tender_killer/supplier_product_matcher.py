from __future__ import annotations

import re
from typing import Any


TOKEN_RE = re.compile(r"[0-9a-z\u0430-\u044f\u0451]+", re.IGNORECASE)
DIMENSION_RE = re.compile(
    r"(?<!\d)(\d+(?:[,.]\d+)?)\s*(?:x|\u0445|\u00d7)\s*"
    r"(\d+(?:[,.]\d+)?)(?:\s*(?:x|\u0445|\u00d7)\s*(\d+(?:[,.]\d+)?))?",
    re.IGNORECASE,
)
PIECE_PACK_COUNT_RE = re.compile(
    r"(?<!\d)(\d{1,5})\s*(?:pcs?|pieces?|pc\.?|"
    r"\u0448\u0442\.?|\u0448\u0442\u0443\u043a(?:\u0438|a)?|"
    r"\u0435\u0434\.?|\u0435\u0434\u0438\u043d\u0438\u0446(?:\u0430|\u044b)?)(?![a-z\u0430-\u044f\u0451])",
    re.IGNORECASE,
)
WEIGHT_RE = re.compile(
    r"(?<!\d)(\d+(?:[,.]\d+)?)\s*(kg|g|mg|\u043a\u0433|"
    r"\u0433\u0440?\.?|\u0433\u0440\u0430\u043c\u043c(?:\u0430|\u043e\u0432)?)"
    r"(?!\s*/\s*(?:m2|m\^2|m\u00b2|\u043c2|\u043c\^2|\u043c\u00b2))"
    r"(?![a-z\u0430-\u044f\u0451])",
    re.IGNORECASE,
)
VOLUME_RE = re.compile(
    r"(?<!\d)(\d+(?:[,.]\d+)?)\s*(ml|l|liters?|litres?|"
    r"\u043c\u043b|"
    r"\u043b\.?|\u043b\u0438\u0442\u0440(?:\u0430|\u043e\u0432)?)(?![a-z\u0430-\u044f\u0451])",
    re.IGNORECASE,
)
PAPER_SHEET_COUNT_RE = re.compile(
    r"(?<!\d)(\d{2,4})\s*(?:sheets?|лист(?:ов|а)?|л\.?)(?![a-zа-яё])",
    re.IGNORECASE,
)

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
        "toilet",
        "\u043a\u0430\u0440\u0442\u0440\u0438\u0434\u0436",
        "\u0442\u043e\u043d\u0435\u0440",
        "\u0437\u043d\u0430\u043a",
        "\u044d\u0432\u0430\u043a\u0443\u0430\u0446",
        "\u0441\u0442\u0440\u0435\u043b",
        "\u043c\u043e\u0447\u0430\u043b",
        "\u043f\u0430\u043f\u043a",
        "\u0442\u0443\u0430\u043b\u0435\u0442",
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

COLOR_GROUPS = {
    "white": {"white", "\u0431\u0435\u043b"},
    "black": {"black", "\u0447\u0435\u0440\u043d", "\u0447\u0451\u0440\u043d"},
    "red": {"red", "\u043a\u0440\u0430\u0441\u043d"},
    "blue": {"blue", "\u0441\u0438\u043d", "\u0433\u043e\u043b\u0443\u0431"},
    "green": {"green", "\u0437\u0435\u043b\u0435\u043d", "\u0437\u0435\u043b\u0451\u043d"},
    "yellow": {"yellow", "\u0436\u0435\u043b\u0442", "\u0436\u0451\u043b\u0442"},
    "gray": {"gray", "grey", "\u0441\u0435\u0440"},
    "brown": {"brown", "\u043a\u043e\u0440\u0438\u0447\u043d"},
    "transparent": {"transparent", "\u043f\u0440\u043e\u0437\u0440\u0430\u0447"},
}

MATERIAL_GROUPS = {
    "zinc": {"zinc", "galvanized", "\u0446\u0438\u043d\u043a", "\u043e\u0446\u0438\u043d\u043a"},
    "phosphate": {"phosphate", "phosphated", "\u0444\u043e\u0441\u0444\u0430\u0442"},
    "stainless": {"stainless", "\u043d\u0435\u0440\u0436\u0430\u0432"},
    "steel": {"steel", "\u0441\u0442\u0430\u043b"},
    "plastic": {"plastic", "\u043f\u043b\u0430\u0441\u0442\u0438\u043a", "\u043f\u043b\u0430\u0441\u0442\u043c\u0430\u0441"},
    "cardboard": {"cardboard", "\u043a\u0430\u0440\u0442\u043e\u043d"},
    "wood": {"wood", "\u0434\u0435\u0440\u0435\u0432"},
    "rubber": {"rubber", "\u0440\u0435\u0437\u0438\u043d"},
    "brass": {"brass", "\u043b\u0430\u0442\u0443\u043d"},
    "copper": {"copper", "\u043c\u0435\u0434"},
    "aluminum": {"aluminum", "aluminium", "\u0430\u043b\u044e\u043c\u0438\u043d"},
}

KNOWN_BRANDS = {
    "ballet",
    "brauberg",
    "fastenpro",
    "gigant",
    "laima",
    "sakura",
    "snegurochka",
    "staff",
    "svetocopy",
    "\u0431\u0430\u043b\u043b\u0435\u0442",
    "\u0433\u0438\u0433\u0430\u043d\u0442",
    "\u0441\u043d\u0435\u0433\u0443\u0440\u043e\u0447\u043a\u0430",
}


def supplier_product_name_matches_query(query_text: Any, product_name: Any) -> bool:
    """Return True only when supplier product title fits the tender search intent."""

    query_tokens = _tokens(query_text)
    product_tokens = _tokens(product_name)
    if not query_tokens or not product_tokens:
        return True

    if _dimension_mismatch(query_text, product_name):
        return False
    if _piece_pack_count_mismatch(query_text, product_name):
        return False
    if _weight_mismatch(query_text, product_name):
        return False
    if _volume_mismatch(query_text, product_name):
        return False
    if _material_mismatch(query_tokens, product_tokens):
        return False
    if _color_mismatch(query_tokens, product_tokens):
        return False
    if _brand_mismatch(query_tokens, product_tokens):
        return False

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
        if query_family == "office_paper" and _paper_format_mismatch(query_tokens, product_tokens):
            return False
        if query_family == "office_paper" and _paper_sheet_count_mismatch(query_text, product_name):
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


def supplier_product_name_mismatch_reasons(query_text: Any, product_name: Any) -> list[str]:
    """Return structured reasons when a supplier title does not fit the search intent."""

    query_tokens = _tokens(query_text)
    product_tokens = _tokens(product_name)
    if not query_tokens or not product_tokens:
        return []

    reasons: list[str] = []
    if _dimension_mismatch(query_text, product_name):
        reasons.append("dimension_mismatch")
    if _piece_pack_count_mismatch(query_text, product_name):
        reasons.append("piece_pack_count_mismatch")
    if _weight_mismatch(query_text, product_name):
        reasons.append("weight_mismatch")
    if _volume_mismatch(query_text, product_name):
        reasons.append("volume_mismatch")
    if _material_mismatch(query_tokens, product_tokens):
        reasons.append("material_mismatch")
    if _color_mismatch(query_tokens, product_tokens):
        reasons.append("color_mismatch")
    if _brand_mismatch(query_tokens, product_tokens):
        reasons.append("brand_mismatch")

    query_family = _detect_family(query_tokens)
    product_family = _detect_family(product_tokens)
    if query_family:
        if (
            _has_any_prefix(product_tokens, FAMILY_REJECT_PREFIXES.get(query_family, set()))
            or (product_family and product_family != query_family)
            or not product_family
        ):
            reasons.append("product_family_mismatch")
        if query_family == "office_paper" and _plain_paper_query_rejects_product(query_tokens, product_tokens):
            reasons.append("colored_paper_mismatch")
        if query_family == "office_paper" and _paper_format_mismatch(query_tokens, product_tokens):
            reasons.append("paper_format_mismatch")
        if query_family == "office_paper" and _paper_sheet_count_mismatch(query_text, product_name):
            reasons.append("paper_sheet_count_mismatch")
        if not _family_modifiers_match(query_family, query_tokens, product_tokens):
            reasons.append("family_modifier_mismatch")

    if not reasons and not supplier_product_name_matches_query(query_text, product_name):
        reasons.append("product_name_mismatch")
    return _dedupe_reasons(reasons)


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


def _paper_sheet_count_mismatch(query_text: Any, product_name: Any) -> bool:
    query_counts = _paper_sheet_counts(query_text)
    product_counts = _paper_sheet_counts(product_name)
    return bool(query_counts and product_counts and query_counts.isdisjoint(product_counts))


def _paper_format_mismatch(query_tokens: list[str], product_tokens: list[str]) -> bool:
    query_formats = _paper_formats(query_tokens)
    product_formats = _paper_formats(product_tokens)
    return bool(query_formats and product_formats and query_formats.isdisjoint(product_formats))


def _paper_formats(tokens: list[str]) -> set[str]:
    formats: set[str] = set()
    for token in tokens:
        normalized = token.replace("\u0430", "a")
        if normalized in {"a3", "a4", "a5"}:
            formats.add(normalized)
    return formats


def _paper_sheet_counts(value: Any) -> set[int]:
    return {int(match.group(1)) for match in PAPER_SHEET_COUNT_RE.finditer(str(value or ""))}


def _dimension_mismatch(query_text: Any, product_name: Any) -> bool:
    query_dimensions = _dimensions(query_text)
    product_dimensions = _dimensions(product_name)
    return bool(query_dimensions and product_dimensions and query_dimensions.isdisjoint(product_dimensions))


def _dimensions(value: Any) -> set[tuple[str, ...]]:
    return {
        tuple(_normalized_decimal(part) for part in match.groups() if part is not None)
        for match in DIMENSION_RE.finditer(str(value or "").casefold())
    }


def _piece_pack_count_mismatch(query_text: Any, product_name: Any) -> bool:
    query_counts = _piece_pack_counts(query_text)
    product_counts = _piece_pack_counts(product_name)
    return bool(query_counts and product_counts and query_counts.isdisjoint(product_counts))


def _piece_pack_counts(value: Any) -> set[int]:
    return {int(match.group(1)) for match in PIECE_PACK_COUNT_RE.finditer(str(value or ""))}


def _weight_mismatch(query_text: Any, product_name: Any) -> bool:
    query_weights = _weights_in_grams(query_text)
    product_weights = _weights_in_grams(product_name)
    return bool(query_weights and product_weights and query_weights.isdisjoint(product_weights))


def _weights_in_grams(value: Any) -> set[str]:
    weights: set[str] = set()
    for match in WEIGHT_RE.finditer(str(value or "").casefold()):
        amount = _decimal_number(match.group(1))
        unit = match.group(2)
        if amount is None:
            continue
        if unit in {"kg", "\u043a\u0433"}:
            grams = amount * 1000
        elif unit == "mg":
            grams = amount / 1000
        else:
            grams = amount
        weights.add(f"{grams:g}")
    return weights


def _volume_mismatch(query_text: Any, product_name: Any) -> bool:
    query_volumes = _volumes_in_milliliters(query_text)
    product_volumes = _volumes_in_milliliters(product_name)
    return bool(query_volumes and product_volumes and query_volumes.isdisjoint(product_volumes))


def _volumes_in_milliliters(value: Any) -> set[str]:
    volumes: set[str] = set()
    for match in VOLUME_RE.finditer(str(value or "").casefold()):
        amount = _decimal_number(match.group(1))
        unit = match.group(2)
        if amount is None:
            continue
        if unit in {"ml", "\u043c\u043b"}:
            milliliters = amount
        else:
            milliliters = amount * 1000
        volumes.add(f"{milliliters:g}")
    return volumes


def _material_mismatch(query_tokens: list[str], product_tokens: list[str]) -> bool:
    query_materials = _token_groups(query_tokens, MATERIAL_GROUPS)
    product_materials = _token_groups(product_tokens, MATERIAL_GROUPS)
    return bool(query_materials and product_materials and query_materials.isdisjoint(product_materials))


def _color_mismatch(query_tokens: list[str], product_tokens: list[str]) -> bool:
    query_colors = _token_groups(query_tokens, COLOR_GROUPS)
    product_colors = _token_groups(product_tokens, COLOR_GROUPS)
    return bool(query_colors and product_colors and query_colors.isdisjoint(product_colors))


def _brand_mismatch(query_tokens: list[str], product_tokens: list[str]) -> bool:
    query_brands = {token for token in query_tokens if token in KNOWN_BRANDS}
    product_brands = {token for token in product_tokens if token in KNOWN_BRANDS}
    return bool(query_brands and product_brands and query_brands.isdisjoint(product_brands))


def _token_groups(tokens: list[str], groups: dict[str, set[str]]) -> set[str]:
    matched: set[str] = set()
    for group, prefixes in groups.items():
        if any(any(token.startswith(prefix) for prefix in prefixes) for token in tokens):
            matched.add(group)
    return matched


def _normalized_decimal(value: str) -> str:
    number = value.replace(",", ".")
    if "." not in number:
        return str(int(number))
    return f"{float(number):g}"


def _decimal_number(value: str) -> float | None:
    try:
        return float(value.replace(",", "."))
    except ValueError:
        return None


def _dedupe_reasons(values: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique


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
