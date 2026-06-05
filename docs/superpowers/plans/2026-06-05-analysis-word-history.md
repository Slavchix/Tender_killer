# Analysis Word And History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the Word report into a participation map and add saved analysis history with compact change summaries.

**Architecture:** Keep the Word work in `reports.py`, reusing the existing `operator_view`, `analysis_facts`, and document contracts. Add history as a backend-owned service/table that snapshots analysis runs and attaches a compact history block to tender detail payloads.

**Tech Stack:** Python services, SQLite schema/store, pytest contract tests, existing React analysis UI.

---

### Task 1: Word Participation Map

**Files:**
- Modify: `src/tender_killer/reports.py`
- Modify: `tests/test_reports.py`

- [ ] Add a failing report test that opens `word/document.xml` and requires these labels: `КАРТА УЧАСТИЯ`, `Краткое решение`, `Таблица рисков`, `Чеклист участия`, `Источники`, `Приложения`.
- [ ] Implement compact report sections in `build_tender_report_docx(...)`, using `operator_view.decision_brief`, `operator_view.sections`, `operator_view.action_plan`, source labels, confidence/source binding fields, and document records.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests/test_reports.py -q`.

### Task 2: Analysis History Backend

**Files:**
- Modify: `src/tender_killer/schema.py`
- Modify: `src/tender_killer/storage.py`
- Create: `src/tender_killer/analysis_history_service.py`
- Modify: `src/tender_killer/analysis_service.py`
- Modify: `src/tender_killer/tender_detail_service.py`
- Modify: `tests/test_analysis_456_features.py`

- [ ] Add a failing API/service test that runs analysis twice, expects `analysis_history` in detail payload, and verifies added/removed/changed fact summaries.
- [ ] Create table `tender_analysis_history` keyed by tender source/external id and run id, with analyzed timestamp, status, confidence, summary, raw snapshot JSON, change summary JSON.
- [ ] Add store helpers to insert and list analysis history rows.
- [ ] Add a history service that compares previous `analysis_facts.items` to the new facts by `id`, recording added, removed, changed labels and feedback counts.
- [ ] Call the history service from `analyze_tender_payload(...)` after the new analysis payload is built and stored.
- [ ] Attach latest history rows to `get_tender_detail_payload(...)`.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests/test_analysis_456_features.py tests/test_analysis_service.py tests/test_web_api.py -q`.

### Task 3: Compact History UI

**Files:**
- Modify: `web/src/TenderAnalysisTab.jsx`
- Modify: `web/src/styles.css`
- Modify: `tests/test_frontend_contract.py`

- [ ] Add a frontend contract that requires `analysis-history`, `История анализа`, and `analysis.analysis_history`.
- [ ] Render a collapsed history block in the analysis modal with date, status, confidence, and added/removed/changed counts.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests/test_frontend_contract.py -q`.

### Task 4: Verification And Publish

- [ ] Run targeted backend and frontend contract tests.
- [ ] Run Word/report tests.
- [ ] Run `git diff --check`.
- [ ] Commit and push to `codex/moscow-mo-parser`.
