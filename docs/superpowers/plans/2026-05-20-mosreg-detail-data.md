# Mosreg Detail Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enrich Mosreg tenders with detail documents and line items, store them in SQLite, and show them on the web tender card.

**Architecture:** Keep the list adapter as the entry point, then enrich each payload with known detail JSON where available. Store line items in a separate `tender_items` table keyed by `source + external_id + position_index`; expose them through `GET /api/tenders/{source}/{external_id}` and render them in the React details panel.

**Tech Stack:** Python 3.12, SQLite, httpx, pytest, React/Vite.

---

### Task 1: Tender Items Model And Storage

**Files:**
- Modify: `src/tender_killer/models.py`
- Modify: `src/tender_killer/storage.py`
- Test: `tests/test_storage.py`

- [ ] Add a `TenderItem` dataclass with fields for name, details, quantity, unit, unit price, total price, OKPD2, and raw payload.
- [ ] Add `items: list[TenderItem]` to `Tender`.
- [ ] Add SQLite table `tender_items`.
- [ ] Replace stored items on each tender upsert so current detail data stays in sync.

### Task 2: Mosreg Detail Normalization

**Files:**
- Modify: `src/tender_killer/adapters/mosreg.py`
- Test: `tests/test_models_and_normalization.py`

- [ ] Normalize product/item arrays from Mosreg payloads into `TenderItem`.
- [ ] Fetch and normalize real document names/URLs from `GetTradeDocuments`.
- [ ] Keep the existing synthetic document endpoint as fallback when document fetch fails.

### Task 3: API And Web Card

**Files:**
- Modify: `src/tender_killer/web_api.py`
- Modify: `web/src/App.jsx`
- Modify: `web/src/styles.css`
- Test: `tests/test_web_api.py`

- [ ] Return `items` from tender detail API.
- [ ] Add `items_count` to list API.
- [ ] Render positions in the right-side card with quantity, unit, prices, and OKPD2.
- [ ] Show document links as clickable anchors.

### Task 4: Verification

**Files:**
- Run all tests and build.

- [ ] Run `.\.venv\Scripts\python.exe -m pytest --basetemp .pytest-tmp-detail-full -q`.
- [ ] Run Vite production build.
