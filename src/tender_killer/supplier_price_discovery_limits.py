from __future__ import annotations

from typing import Any

from tender_killer.supplier_price_discovery_diagnostics import _collector_diagnostics
from tender_killer.supplier_price_discovery_matching import _supplier_candidate_rank_key
from tender_killer.supplier_price_discovery_utils import _positive_env_int


DEFAULT_BULK_DISCOVERY_PROFILE_THRESHOLD = 3
DEFAULT_BULK_DISCOVERY_CANDIDATE_LIMIT = 5
DEFAULT_SINGLE_DISCOVERY_CANDIDATE_LIMIT = 12


def _candidate_limit_for_single_profile() -> int:
    return _positive_env_int(
        "TENDER_KILLER_PRICE_DISCOVERY_SINGLE_CANDIDATES_PER_POSITION",
        DEFAULT_SINGLE_DISCOVERY_CANDIDATE_LIMIT,
    )


def _candidate_limit_for_profile_count(profile_count: int) -> int:
    threshold = _positive_env_int(
        "TENDER_KILLER_PRICE_DISCOVERY_BULK_PROFILE_THRESHOLD",
        DEFAULT_BULK_DISCOVERY_PROFILE_THRESHOLD,
    )
    if int(profile_count or 0) > threshold:
        return _positive_env_int(
            "TENDER_KILLER_PRICE_DISCOVERY_BULK_CANDIDATES_PER_POSITION",
            DEFAULT_BULK_DISCOVERY_CANDIDATE_LIMIT,
        )
    return _candidate_limit_for_single_profile()


def _limit_supplier_candidates_for_profile(
    profile: dict[str, Any],
    candidates: list[dict[str, Any]],
    candidate_limit: int | None,
) -> list[dict[str, Any]]:
    if candidate_limit is None or candidate_limit <= 0 or len(candidates) <= candidate_limit:
        return candidates
    ranked = sorted(candidates, key=lambda candidate: _supplier_candidate_rank_key(profile, candidate))
    return ranked[:candidate_limit]


def _candidate_limit_diagnostics(candidate_limit: int | None, *, collected_count: int, staged_count: int) -> dict[str, Any]:
    diagnostics = _collector_diagnostics("candidate_limiter")
    diagnostics["run_state"] = "applied"
    diagnostics["candidate_limit"] = int(candidate_limit or 0)
    diagnostics["candidates_seen"] = int(collected_count)
    diagnostics["candidates_limited"] = max(0, int(collected_count) - int(staged_count))
    diagnostics["candidates_staged"] = int(staged_count)
    diagnostics["candidates_found"] = int(collected_count)
    return diagnostics
