# Rule-Based TZ Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first non-LLM tender document analysis layer that turns extracted document text into a practical supplier summary, requirement list, and red flags.

**Architecture:** Keep analysis deterministic and local for v1. A new focused analyzer module reads extracted document text, produces a structured `TenderAnalysisResult`, stores it in SQLite, exposes it through the local API, and renders it in the tender detail panel.

**Tech Stack:** Python 3.12, SQLite, stdlib regex/dataclasses, existing local HTTP API, React/Vite.

---

### Task 1: Rule-Based Analyzer

**Files:**
- Create: `src/tender_killer/analysis.py`
- Test: `tests/test_analysis.py`

- [ ] Write failing tests for detecting documents, delivery, national regime, security, penalties, and recommended cautious status.
- [ ] Implement `TenderAnalysisResult` and `analyze_tender_texts(texts)` with deterministic regex/keyword rules.
- [ ] Verify `pytest tests/test_analysis.py -q` passes.

### Task 2: SQLite/API Integration

**Files:**
- Modify: `src/tender_killer/web_api.py`
- Test: `tests/test_web_api.py`

- [ ] Write failing API tests for `analyze_tender_payload`.
- [ ] Add `tender_analysis` table with fields for summary, requirements, risks, red flags, recommended status, confidence, raw JSON, timestamps.
- [ ] Add `POST /api/tenders/{source}/{external_id}/analysis/run`.
- [ ] Include `analysis` in `get_tender_payload`.
- [ ] Verify web API tests pass.

### Task 3: Web UI

**Files:**
- Modify: `web/src/App.jsx`
- Modify: `web/src/styles.css`

- [ ] Add `Проанализировать ТЗ` button in tender details.
- [ ] Render summary, requirements, risks, red flags, status, confidence.
- [ ] Keep raw document preview secondary.
- [ ] Verify Vite build passes.

### Task 4: Memory And Verification

**Files:**
- Modify: `memory/project-context.md`

- [ ] Record the rule-based analysis checkpoint.
- [ ] Run full pytest.
- [ ] Run Vite build.
- [ ] Restart local API so the site uses the new endpoint.
