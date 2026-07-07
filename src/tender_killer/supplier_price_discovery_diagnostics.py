from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from tender_killer.storage import TenderStore
from tender_killer.supplier_officemag_parser import _officemag_product_scopes
from tender_killer.supplier_price_discovery_utils import _dict_items
from tender_killer.supplier_price_discovery_utils import _text
from tender_killer.supplier_provider_policy import ACTION_PRODUCT_PAGE_FETCH
from tender_killer.supplier_provider_policy import ACTION_PUBLIC_SEARCH_FETCH


CATALOG_SEARCH_LINK_KIND = "catalog_search"
MANUAL_PRODUCT_LINK_KIND = "manual_product_url"
ACCESS_BLOCKED_ERROR_KIND = "access_blocked"
ACCESS_BLOCKED_STATUS_CODES = {401, 403, 429, 503}
MAX_INTENT_REJECTION_SAMPLES = 5
NO_SUPPLIER_CANDIDATES_MESSAGE = "\u041d\u043e\u0432\u044b\u0445 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u043e\u0432 \u043f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u043e\u0432 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043e."
PREPARE_SUPPLIER_SEARCH_MESSAGE = "\u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u043f\u043e\u0434\u0433\u043e\u0442\u043e\u0432\u044c \u043f\u043e\u0438\u0441\u043a \u043f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u043e\u0432."


def _extend_intent_rejection_samples(target: dict[str, Any], samples: list[dict[str, Any]]) -> None:
    current = [dict(item) for item in target.get("intent_rejection_samples") or [] if isinstance(item, dict)]
    current = current[:MAX_INTENT_REJECTION_SAMPLES]
    seen = {
        (
            (_text(item.get("url")) or "").casefold(),
            (_text(item.get("name")) or "").casefold(),
        )
        for item in current
    }
    for sample in samples:
        if len(current) >= MAX_INTENT_REJECTION_SAMPLES:
            break
        key = (
            (_text(sample.get("url")) or "").casefold(),
            (_text(sample.get("name")) or "").casefold(),
        )
        if key in seen:
            continue
        seen.add(key)
        current.append(dict(sample))
        if len(current) >= MAX_INTENT_REJECTION_SAMPLES:
            break
    if current:
        target["intent_rejection_samples"] = current


def _with_intent_rejection_diagnostics(
    diagnostics: dict[str, Any],
    rejected_count: int,
    rejection_reasons: dict[str, int] | None = None,
) -> dict[str, Any]:
    if rejected_count <= 0:
        return diagnostics
    updated = dict(diagnostics)
    updated["candidates_rejected_by_intent"] = int(updated.get("candidates_rejected_by_intent") or 0) + rejected_count
    if rejection_reasons:
        current_reasons = dict(updated.get("intent_rejection_reasons") or {})
        for reason, count in rejection_reasons.items():
            current_reasons[reason] = int(current_reasons.get(reason) or 0) + int(count)
        updated["intent_rejection_reasons"] = current_reasons
    return updated


def _increment_reason_counts(target: dict[str, int], reasons: list[str]) -> None:
    for reason in reasons:
        target[reason] = int(target.get(reason) or 0) + 1


def _record_supplier_discovery_diagnostics(
    store: TenderStore,
    source: str,
    external_id: str,
    profiles: list[dict[str, Any]],
    target: dict[str, Any],
    collector_diagnostics: list[dict[str, Any]],
) -> None:
    raw_payload = dict(target.get("raw_payload") or {})
    discovery = dict(raw_payload.get("supplier_discovery") or {})
    candidates = _dict_items(discovery.get("candidates"))
    discovery["status"] = discovery.get("status") or "no_candidates"
    if not candidates:
        discovery["status"] = "no_candidates"
    discovery["collector_diagnostics"] = collector_diagnostics
    discovery["candidates"] = candidates
    raw_payload["supplier_discovery"] = discovery
    target["raw_payload"] = raw_payload
    store.upsert_product_profiles(source, external_id, profiles)


def _tender_discovery_diagnostics(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    diagnostics_by_provider: dict[str, dict[str, Any]] = {}
    for profile in profiles:
        raw_payload = profile.get("raw_payload") if isinstance(profile.get("raw_payload"), dict) else {}
        discovery = raw_payload.get("supplier_discovery") if isinstance(raw_payload.get("supplier_discovery"), dict) else {}
        diagnostics = discovery.get("collector_diagnostics") if isinstance(discovery.get("collector_diagnostics"), list) else []
        for item in diagnostics:
            if isinstance(item, dict) and _diagnostics_has_signal(item):
                _merge_diagnostics(diagnostics_by_provider, item)
    return list(diagnostics_by_provider.values())


def _supplier_discovery_error_message(exc: ValueError) -> str:
    message = str(exc)
    lowered = message.casefold()
    if NO_SUPPLIER_CANDIDATES_MESSAGE.casefold() in lowered or "new candidates" in lowered:
        return NO_SUPPLIER_CANDIDATES_MESSAGE
    if PREPARE_SUPPLIER_SEARCH_MESSAGE.casefold() in lowered or "prepare" in lowered:
        return PREPARE_SUPPLIER_SEARCH_MESSAGE
    return message


def _collector_diagnostics(provider: str) -> dict[str, Any]:
    return {
        "provider": provider,
        "queries_seen": 0,
        "links_seen": 0,
        "links_skipped": 0,
        "pages_fetched": 0,
        "candidates_found": 0,
        "errors": [],
    }


def _skipped_collector_diagnostics(provider: str, reason: str) -> dict[str, Any]:
    diagnostics = _collector_diagnostics(provider)
    diagnostics["run_state"] = "skipped"
    diagnostics["skip_reason"] = reason
    return diagnostics


def _blocked_collector_diagnostics(provider: str) -> dict[str, Any]:
    diagnostics = _collector_diagnostics(provider)
    diagnostics["run_state"] = "blocked"
    diagnostics["skip_reason"] = ACCESS_BLOCKED_ERROR_KIND
    diagnostics["error_kind"] = ACCESS_BLOCKED_ERROR_KIND
    return diagnostics


def _fetch_action_for_link(link: dict[str, Any]) -> str:
    return ACTION_PRODUCT_PAGE_FETCH if _text(link.get("link_kind")) == MANUAL_PRODUCT_LINK_KIND else ACTION_PUBLIC_SEARCH_FETCH


def _mark_policy_skipped(diagnostics: dict[str, Any], reason: str) -> None:
    diagnostics["run_state"] = "skipped"
    diagnostics["skip_reason"] = reason
    policy_reasons = diagnostics.setdefault("policy_skip_reasons", {})
    policy_reasons[reason] = int(policy_reasons.get(reason) or 0) + 1


def _mark_catalog_access_blocked(
    diagnostics: dict[str, Any],
    url: str,
    *,
    error: BaseException | None = None,
) -> None:
    diagnostics["run_state"] = "blocked"
    diagnostics["skip_reason"] = ACCESS_BLOCKED_ERROR_KIND
    diagnostics["error_kind"] = ACCESS_BLOCKED_ERROR_KIND
    if error is None:
        diagnostics["errors"].append(f"{ACCESS_BLOCKED_ERROR_KIND} body from {url}")
        return
    diagnostics["errors"].append(f"{ACCESS_BLOCKED_ERROR_KIND} error from {url}: {error}")


def _skip_remaining_links(diagnostics: dict[str, Any], links: list[dict[str, Any]], current_index: int) -> None:
    diagnostics["links_skipped"] += max(0, len(links) - int(current_index) - 1)


def _catalog_access_block_reason_from_error(exc: BaseException) -> str | None:
    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if isinstance(status_code, int) and status_code in ACCESS_BLOCKED_STATUS_CODES:
        return ACCESS_BLOCKED_ERROR_KIND
    text = str(exc).casefold()
    if any(
        marker in text
        for marker in (
            ACCESS_BLOCKED_ERROR_KIND,
            "forbidden",
            "captcha",
            "\u043a\u0430\u043f\u0447",
            "browser check",
            "\u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0432\u0430\u0448\u0435\u0433\u043e \u0432\u0435\u0431-\u0431\u0440\u0430\u0443\u0437\u0435\u0440\u0430",
            "\u043f\u0440\u043e\u0439\u0434\u0438\u0442\u0435 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0443",
        )
    ):
        return ACCESS_BLOCKED_ERROR_KIND
    return None


def _catalog_access_block_reason_from_body(body: str) -> str | None:
    text = re.sub(r"\s+", " ", str(body or "")).casefold()
    if not text:
        return None
    if "if you are not a bot" in text:
        return ACCESS_BLOCKED_ERROR_KIND
    if "forbidden" in text and ("origin:" in text or "copy the report" in text):
        return ACCESS_BLOCKED_ERROR_KIND
    if any(
        marker in text
        for marker in (
            "access denied",
            "browser verification",
            "verification required",
            "captcha",
            "\u043a\u0430\u043f\u0447",
            "browser check",
            "\u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0432\u0430\u0448\u0435\u0433\u043e \u0432\u0435\u0431-\u0431\u0440\u0430\u0443\u0437\u0435\u0440\u0430",
            "\u043f\u0440\u043e\u0439\u0434\u0438\u0442\u0435 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0443",
        )
    ):
        return ACCESS_BLOCKED_ERROR_KIND
    return None


def _catalog_body_has_provider_product_signal(provider: str, body: str) -> bool:
    body_text = str(body or "")
    if not body_text.strip():
        return False
    soup = BeautifulSoup(body_text, "html.parser")
    if re.search(r'"@type"\s*:\s*(?:"Product"|\[[^\]]*"Product")', body_text, re.IGNORECASE):
        return True
    provider_key = str(provider or "").casefold()
    if provider_key == "officemag":
        return bool(
            _officemag_product_scopes(soup)
            or soup.select_one(".ProductHead__name, .Product__price, .js-productSum")
        )
    if provider_key == "komus":
        return bool(soup.select_one("a[href*='/p/'], .product-card, [data-qa*='product' i]"))
    if provider_key == "petrovich":
        return bool(soup.select_one("a[href^='/product/'], a[href*='/product/'], .product-card, [data-test*='product' i]"))
    if provider_key in {"vseinstrumenti", "lemanapro"}:
        return bool(soup.select_one("a[href*='/product/'], .product-card, [data-qa*='product' i]"))
    return False


def _merge_diagnostics(current: dict[str, dict[str, Any]], item: dict[str, Any]) -> None:
    provider = str(item.get("provider") or "unknown")
    target = current.setdefault(provider, _collector_diagnostics(provider))
    for field in (
        "queries_seen",
        "links_seen",
        "links_skipped",
        "pages_fetched",
        "candidates_found",
        "candidates_rejected_by_intent",
    ):
        value = int(item.get(field) or 0)
        if field not in target and value == 0:
            continue
        target[field] = int(target.get(field) or 0) + value
    for reason, count in dict(item.get("intent_rejection_reasons") or {}).items():
        target_reasons = target.setdefault("intent_rejection_reasons", {})
        target_reasons[str(reason)] = int(target_reasons.get(str(reason)) or 0) + int(count or 0)
    _extend_intent_rejection_samples(
        target,
        [dict(sample) for sample in item.get("intent_rejection_samples") or [] if isinstance(sample, dict)],
    )
    if run_state := _text(item.get("run_state")):
        target["run_state"] = run_state
    if skip_reason := _text(item.get("skip_reason")):
        target["skip_reason"] = skip_reason
    if error_kind := _text(item.get("error_kind")):
        target["error_kind"] = error_kind
    for field in ("candidate_limit", "candidates_seen", "candidates_limited", "candidates_staged"):
        if field in item:
            target[field] = int(item.get(field) or 0)
    target["errors"].extend([str(error) for error in item.get("errors") or []])


def _diagnostics_is_access_blocked(item: dict[str, Any]) -> bool:
    if _text(item.get("error_kind")) == ACCESS_BLOCKED_ERROR_KIND:
        return True
    if _text(item.get("skip_reason")) == ACCESS_BLOCKED_ERROR_KIND:
        return True
    return any(_catalog_access_block_reason_from_error(RuntimeError(str(error))) for error in item.get("errors") or [])


def _diagnostics_has_signal(item: dict[str, Any]) -> bool:
    return bool(
        item.get("pages_fetched")
        or item.get("candidates_found")
        or item.get("candidates_rejected_by_intent")
        or item.get("run_state") == "skipped"
        or item.get("run_state") == "blocked"
        or item.get("skip_reason")
        or item.get("error_kind")
        or item.get("errors")
    )
