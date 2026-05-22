# Tender Workbench v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the tender detail area readable by turning the narrow right panel into a wider workbench with a compact decision summary and product sub-tabs.

**Architecture:** Keep the current React/Vite single-file UI structure for this slice, but introduce explicit UI sections/classes that can be split into components later. The tender list remains the selection surface; the selected tender detail becomes the primary workbench area.

**Tech Stack:** React state, existing CSS, existing pytest frontend contract tests.

---

### Task 1: Frontend Contract

**Files:**
- Modify: `tests/test_frontend_contract.py`

- [ ] Add a contract test that requires `TenderDecisionSummary`, `workbench-layout`, `decision-summary-grid`, `product-detail-tabs`, and product detail modes `Паспорт`, `Цены`, `Поставщики`, `ТЗ`.
- [ ] Run the test and confirm it fails because the workbench structure is absent.

### Task 2: Wider Workbench

**Files:**
- Modify: `web/src/App.jsx`
- Modify: `web/src/styles.css`

- [ ] Change the main tender workspace class from `workspace` to `workspace workbench-layout`.
- [ ] Update desktop grid columns so the detail panel gets a real workbench width instead of behaving as a narrow sidebar.
- [ ] Keep existing responsive collapse for narrower screens.

### Task 3: Decision Summary

**Files:**
- Modify: `web/src/App.jsx`
- Modify: `web/src/styles.css`

- [ ] Add `TenderDecisionSummary({ tender, economics })`.
- [ ] Render it below the tender title and before actions.
- [ ] Show price, deadline, customer, workflow status, economics status/margin, and next step.

### Task 4: Product Detail Sub-Tabs

**Files:**
- Modify: `web/src/App.jsx`
- Modify: `web/src/styles.css`

- [ ] Add local `activeProfileMode` state inside `ProductProfileDetail`.
- [ ] Split the product detail content into modes: `overview`, `pricing`, `suppliers`, `requirements`.
- [ ] Move identification/search package to `Паспорт`, economics form to `Цены`, supplier form to `Поставщики`, and requirements/evidence to `ТЗ`.

### Task 5: Verification And Handoff

**Files:**
- Modify: `README.md`
- Modify: `memory/project-context.md`

- [ ] Run targeted frontend contract tests.
- [ ] Run full pytest with the standard command.
- [ ] Update README and memory with the workbench checkpoint and final test count.
- [ ] Commit and push the branch.
