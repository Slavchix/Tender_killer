from __future__ import annotations

from pathlib import Path
from typing import Any

from tender_killer.price_candidate_confirmation import apply_confirmed_candidate
from tender_killer.price_candidate_confirmation import propagate_confirmed_candidate_to_matching_profiles
from tender_killer.price_candidate_confirmation import profile_has_positive_cost
from tender_killer.price_candidate_profiles import ensure_profiles_with_item_fallback
from tender_killer.price_candidate_profiles import find_profile
from tender_killer.price_candidate_quality import ensure_candidate_confirmable
from tender_killer.price_candidate_ranking import rank_profile_price_candidates
from tender_killer.price_candidate_staging import stage_tender_price_candidates
from tender_killer.storage import TenderStore


REVIEW_STATUSES = {"confirmed", "rejected"}


def review_profile_price_candidate(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    candidate_id: int,
    *,
    review_status: str,
) -> dict[str, Any]:
    status = _review_status(review_status)
    store = TenderStore(database_path)
    store.initialize()
    profiles = ensure_profiles_with_item_fallback(database_path, source, external_id)
    target = find_profile(profiles, position_index)
    candidate = _find_candidate(store, source, external_id, position_index, candidate_id)

    supplier_option_index: int | None = None
    propagated: list[dict[str, int | None]] = []
    if status == "confirmed":
        ensure_candidate_confirmable(target, candidate)
        supplier_option_index = apply_confirmed_candidate(target, candidate)
        propagated = propagate_confirmed_candidate_to_matching_profiles(profiles, target, candidate)
        store.upsert_product_profiles(source, external_id, profiles)
        from tender_killer.price_memory_service import remember_confirmed_price_candidate

        remember_confirmed_price_candidate(
            store.database_path,
            source,
            external_id,
            target,
            {**candidate, "review_status": "confirmed"},
        )

    store.update_price_candidate_review(
        source,
        external_id,
        position_index,
        candidate,
        review_status=status,
        supplier_option_index=supplier_option_index,
    )
    result = {
        "ok": True,
        "position_index": int(position_index),
        "candidate_id": int(candidate_id),
        "review_status": status,
        "supplier_option_index": supplier_option_index,
    }
    if propagated:
        result["propagated_count"] = len(propagated)
        result["propagated"] = propagated
    return result


def confirm_ready_price_candidates(
    database_path: str | Path,
    source: str,
    external_id: str,
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = ensure_profiles_with_item_fallback(database_path, source, external_id)

    confirmed: list[dict[str, int | None]] = []
    propagated: list[dict[str, int | None]] = []
    review_updates: list[tuple[int, dict[str, Any], int | None]] = []
    skipped_existing_cost_count = 0
    skipped_no_ready_candidate_count = 0

    for profile in profiles:
        position_index = int(profile.get("position_index") or 0)
        if profile_has_positive_cost(profile):
            skipped_existing_cost_count += 1
            continue

        candidate = _first_ready_candidate(profile)
        if candidate is None:
            skipped_no_ready_candidate_count += 1
            continue

        supplier_option_index = apply_confirmed_candidate(profile, candidate, selection="bulk_auto_eligible")
        confirmed.append(
            {
                "position_index": position_index,
                "candidate_id": int(candidate["id"]),
                "supplier_option_index": supplier_option_index,
            }
        )
        review_updates.append((position_index, candidate, supplier_option_index))
        propagated.extend(propagate_confirmed_candidate_to_matching_profiles(profiles, profile, candidate))

    if confirmed:
        store.upsert_product_profiles(source, external_id, profiles)
        for position_index, candidate, supplier_option_index in review_updates:
            store.update_price_candidate_review(
                source,
                external_id,
                position_index,
                candidate,
                review_status="confirmed",
                supplier_option_index=supplier_option_index,
            )
            profile = find_profile(profiles, position_index)
            from tender_killer.price_memory_service import remember_confirmed_price_candidate

            remember_confirmed_price_candidate(
                store.database_path,
                source,
                external_id,
                profile,
                {**candidate, "review_status": "confirmed"},
            )

    skipped_count = skipped_existing_cost_count + skipped_no_ready_candidate_count
    result = {
        "ok": True,
        "total_profiles": len(profiles),
        "confirmed_count": len(confirmed),
        "skipped_count": skipped_count,
        "skipped_existing_cost_count": skipped_existing_cost_count,
        "skipped_no_ready_candidate_count": skipped_no_ready_candidate_count,
        "confirmed": confirmed,
    }
    if propagated:
        result["propagated_count"] = len(propagated)
        result["propagated"] = propagated
    return result


def apply_tender_auto_prices(
    database_path: str | Path,
    source: str,
    external_id: str,
) -> dict[str, Any]:
    stage = stage_tender_price_candidates(database_path, source, external_id)
    ready_review = confirm_ready_price_candidates(database_path, source, external_id)
    profiles = ensure_profiles_with_item_fallback(database_path, source, external_id)

    priced_positions: list[int] = []
    missing_cost_positions: list[int] = []
    for profile in profiles:
        position_index = int(profile.get("position_index") or 0)
        if profile_has_positive_cost(profile):
            priced_positions.append(position_index)
        else:
            missing_cost_positions.append(position_index)

    return {
        "ok": True,
        "total_profiles": len(profiles),
        "stage": stage,
        "ready_review": ready_review,
        "applied_count": int(ready_review.get("confirmed_count") or 0),
        "priced_count": len(priced_positions),
        "missing_cost_count": len(missing_cost_positions),
        "priced_positions": priced_positions,
        "missing_cost_positions": missing_cost_positions,
    }


def _first_ready_candidate(profile: dict[str, Any]) -> dict[str, Any] | None:
    for candidate in rank_profile_price_candidates(profile):
        review_status = str(candidate.get("review_status") or "pending").casefold()
        if candidate.get("auto_eligible") is True and review_status not in REVIEW_STATUSES:
            return candidate
    return None


def _find_candidate(
    store: TenderStore,
    source: str,
    external_id: str,
    position_index: int,
    candidate_id: int,
) -> dict[str, Any]:
    for candidate in store.list_price_candidates(source, external_id, position_index):
        if int(candidate.get("id") or 0) == int(candidate_id):
            return candidate
    raise KeyError(f"Price candidate {candidate_id} not found.")


def _review_status(value: str) -> str:
    status = str(value or "").strip().casefold()
    if status not in REVIEW_STATUSES:
        raise ValueError("Price candidate review status must be confirmed or rejected.")
    return status
