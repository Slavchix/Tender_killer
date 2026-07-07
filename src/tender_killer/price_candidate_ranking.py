from __future__ import annotations

from typing import Any

from tender_killer.price_candidate_common import number_or_none as _number
from tender_killer.price_candidate_common import raw_payload as _raw_payload
from tender_killer.price_candidate_normalization import normalize_price_candidate
from tender_killer.price_candidate_passport import build_pricing_passport
from tender_killer.price_candidate_quality import candidate_score as _candidate_score
from tender_killer.price_candidate_quality import evaluate_price_candidate_quality


def rank_profile_price_candidates(profile: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = profile.get("price_candidates") if isinstance(profile.get("price_candidates"), list) else []
    ranked: list[dict[str, Any]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        candidate = _rankable_price_candidate(profile, candidate)
        quality = evaluate_price_candidate_quality(profile, candidate)
        score, reasons = _candidate_score(candidate, quality)
        ranked_candidate = {**candidate, **quality, "score": score, "score_reasons": reasons}
        ranked_candidate["pricing_passport"] = build_pricing_passport(profile, ranked_candidate)
        ranked.append(ranked_candidate)
    return sorted(ranked, key=_rank_key)


def _rankable_price_candidate(profile: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    raw_payload = _raw_payload(candidate)
    if _number(candidate.get("unit_price") or raw_payload.get("unit_price")) is None:
        return {**candidate}
    return normalize_price_candidate(profile, candidate)


def _rank_key(candidate: dict[str, Any]) -> tuple[float, float, int]:
    price = _number(candidate.get("unit_price"))
    normalized_price = price if price is not None else float("inf")
    return (-float(candidate.get("score") or 0), normalized_price, int(candidate.get("id") or 0))
