# Decision Engine v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one backend decision payload that combines economics, analysis, documents, market state, and product profiles into a single tender recommendation.

**Architecture:** Add a pure `decision_service.py` with `build_tender_decision(tender)`. `tender_detail_service.get_tender_payload()` will attach the decision after it builds `market_state` and `economics`, so every future UI/report surface can read the same `tender["decision"]` object from the detail payload.

**Tech Stack:** Python 3.12, existing SQLite-backed payload services, pytest.

---

### Task 1: Pure Decision Service

**Files:**
- Create: `src/tender_killer/decision_service.py`
- Test: `tests/test_decision_service.py`

- [ ] **Step 1: Write failing tests**

Cover these cases in `tests/test_decision_service.py`:

```python
from tender_killer.decision_service import build_tender_decision


def test_decision_requires_costs_before_participation():
    decision = build_tender_decision({
        "title": "Paper",
        "economics": {
            "status": "needs_costs",
            "missing_cost_inputs": ["Paper A4"],
            "participation_decision": {"status": "needs_costs", "label": "Не хватает цен"},
        },
        "document_records": [{"text_status": "empty"}],
    })

    assert decision["status"] == "missing_prices"
    assert decision["label"] == "Не хватает цен"
    assert decision["next_step"] == "Добавить себестоимость"
    assert "Paper A4" in decision["blockers"]
    assert decision["metrics"]["documents_ready"] == 0


def test_decision_marks_guarded_bid_when_economics_has_limit():
    decision = build_tender_decision({
        "economics": {
            "status": "manual_review",
            "margin_percent": 8.5,
            "participation_decision": {
                "status": "guarded_bid",
                "label": "Только с лимитом",
                "limit_price": 14903.23,
                "recommendation": "Участвовать только с лимитом.",
            },
        },
        "analysis": {"status": "ok", "risks": [], "red_flags": [], "requirements": []},
        "market_state": {"current_offer_price": 16000, "bid_count": 2},
        "document_records": [{"text_status": "ok"}],
        "product_profiles": [{"profile_status": "priced"}],
    })

    assert decision["status"] == "with_limit"
    assert decision["label"] == "Только с лимитом"
    assert decision["limit_price"] == 14903.23
    assert decision["metrics"]["current_offer_price"] == 16000
    assert decision["metrics"]["bid_count"] == 2


def test_decision_requires_analysis_review_for_red_flags():
    decision = build_tender_decision({
        "economics": {
            "status": "interesting",
            "margin_percent": 25,
            "participation_decision": {"status": "can_bid", "label": "Можно заходить"},
        },
        "analysis": {
            "status": "needs_review",
            "risks": ["короткий срок поставки"],
            "red_flags": ["лицензия/СРО"],
            "requirements": [],
        },
        "document_records": [{"text_status": "ok"}],
    })

    assert decision["status"] == "needs_review"
    assert decision["label"] == "Проверить ТЗ"
    assert "лицензия/СРО" in decision["blockers"]
    assert decision["next_step"] == "Проверить анализ"
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_decision_service.py -q -p no:cacheprovider
```

Expected: import failure for `tender_killer.decision_service`.

- [ ] **Step 3: Implement the service**

Create `build_tender_decision(tender)` with stable keys:

```python
{
    "status": "missing_prices|needs_review|with_limit|skip|interesting",
    "label": "...",
    "tone": "pending|warning|danger|success",
    "summary": "...",
    "next_step": "...",
    "reasons": [...],
    "blockers": [...],
    "limit_price": 14903.23,
    "metrics": {
        "nmc_price": ...,
        "current_offer_price": ...,
        "bid_count": ...,
        "margin_percent": ...,
        "documents_ready": ...,
        "documents_total": ...,
        "positions_total": ...,
        "positions_priced": ...,
    },
}
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_decision_service.py -q -p no:cacheprovider
```

Expected: all tests pass.

### Task 2: Attach Decision To Tender Detail Payload

**Files:**
- Modify: `src/tender_killer/tender_detail_service.py`
- Modify: `tests/test_tender_detail_service.py`

- [ ] **Step 1: Write failing integration test**

Add a test that saves a tender with product economics, calls `get_tender_payload()`, and asserts `detail["decision"]["status"] == "interesting"` or `"missing_prices"`.

- [ ] **Step 2: Run the integration test and verify it fails**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_tender_detail_service.py::test_get_tender_payload_includes_decision_summary -q -p no:cacheprovider
```

Expected: `KeyError: 'decision'`.

- [ ] **Step 3: Wire the service**

Import `build_tender_decision` and assign `payload["decision"]` after `payload["economics"]`.

- [ ] **Step 4: Run targeted verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_decision_service.py tests\test_tender_detail_service.py -q -p no:cacheprovider
```

Expected: all targeted tests pass.

### Task 3: Final Verification

**Files:**
- No additional files unless tests reveal a gap.

- [ ] **Step 1: Run full verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full
```

Expected: full suite passes.

- [ ] **Step 2: Commit and push**

Stage only plan, service, and tests:

```powershell
git add docs/superpowers/plans/2026-05-29-decision-engine-v1.md src/tender_killer/decision_service.py src/tender_killer/tender_detail_service.py tests/test_decision_service.py tests/test_tender_detail_service.py
git commit -m "Add tender decision engine"
git push
```
