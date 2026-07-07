# Tender Workbench Decision Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the selected tender detail area into a decision-first workbench with a default `Сводка`, a persistent decision strip, a clearer `Анализ` action row, and the first no-scroll economics workspace structure.

**Architecture:** Keep `TenderDetails.jsx` as the coordinator. Add focused presentational modules for the decision strip and summary tab, then rewire `TenderDetailsTabs.jsx` so work modes are decision-oriented. The first economics pass is a frontend layout/composition change that preserves existing backend behavior and supplier actions.

**Tech Stack:** React/Vite frontend, plain CSS in `web/src/styles.css`, existing Python frontend contract tests in `tests/test_frontend_contract.py`, SQLite-backed API payloads.

---

## File Structure

- Create `web/src/TenderDecisionStrip.jsx`: compact top-level decision anchor shared by tender work modes.
- Create `web/src/TenderSummaryTab.jsx`: default `Сводка` work mode, deriving decision explanations from existing tender/economics/analysis/documents payloads.
- Modify `web/src/TenderDetails.jsx`: render `TenderDecisionStrip`, stop rendering the old `TenderDecisionSummary`, pass summary data/actions to tabs.
- Modify `web/src/TenderDetailsTabs.jsx`: add `summary` tab label `Сводка`, make it the default work mode, pass `onActiveTabChange` into summary cards.
- Modify `web/src/useTenderDetailsUi.js`: default and reset active tab to `summary`.
- Modify `web/src/TenderAnalysisTab.jsx`: add a top action row with `Проанализировать`, `Скачать Word`, and document source hints.
- Modify `web/src/TenderEconomicsTab.jsx`: keep existing behavior but arrange the selected-position content into left position rail, center economics, right suppliers.
- Modify `web/src/styles.css`: add decision strip, summary, analysis action, and economics workspace layout styles.
- Modify `tests/test_frontend_contract.py`: update contracts for new modules, tab labels, analysis Word action, and economics workspace columns.

---

### Task 1: Contract Tests For Decision Workbench Shell

**Files:**
- Modify: `tests/test_frontend_contract.py`

- [ ] **Step 1: Add source constants for new modules**

Insert near the other frontend source constants:

```python
TENDER_DECISION_STRIP_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderDecisionStrip.jsx"
TENDER_SUMMARY_TAB_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderSummaryTab.jsx"
```

- [ ] **Step 2: Add failing contract for the decision strip and summary tab**

Add this test near the tender details contract tests:

```python
def test_tender_workbench_uses_decision_first_summary_shell():
    details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    tabs_source = TENDER_DETAILS_TABS_SOURCE.read_text(encoding="utf-8")
    ui_source = USE_TENDER_DETAILS_UI_SOURCE.read_text(encoding="utf-8")
    strip_source = TENDER_DECISION_STRIP_SOURCE.read_text(encoding="utf-8") if TENDER_DECISION_STRIP_SOURCE.exists() else ""
    summary_source = TENDER_SUMMARY_TAB_SOURCE.read_text(encoding="utf-8") if TENDER_SUMMARY_TAB_SOURCE.exists() else ""
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "from './TenderDecisionStrip'" in details_source
    assert "<TenderDecisionStrip" in details_source
    assert "from './TenderSummaryTab'" in tabs_source
    assert "export function TenderSummaryTab" in summary_source
    assert "export function TenderDecisionStrip" in strip_source
    assert "useState('summary')" in ui_source
    assert "setActiveTab('summary')" in ui_source
    assert "{ id: 'summary', label: 'Сводка' }" in tabs_source
    assert "summary-decision-grid" in summary_source
    assert "summary-next-action" in summary_source
    assert "decision-strip-grid" in strip_source
    assert ".decision-strip" in styles_source
    assert ".summary-decision-grid" in styles_source
    assert find_mojibake(details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(tabs_source, TENDER_DETAILS_TABS_SOURCE) == []
    assert find_mojibake(strip_source, TENDER_DECISION_STRIP_SOURCE) == []
    assert find_mojibake(summary_source, TENDER_SUMMARY_TAB_SOURCE) == []
```

- [ ] **Step 3: Update old overview expectations**

In tests that assert `TenderOverviewTab` is the active first work mode, change those assertions to the new summary ownership. Keep `TenderOverviewTab` contracts only if the module still exists as legacy/passport content.

Required replacements:

```python
assert "<TenderSummaryTab" in tabs_source
assert "Сводка" in tabs_source
assert "Обзор" not in tabs_source
```

- [ ] **Step 4: Run the focused contract test and verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_frontend_contract.py::test_tender_workbench_uses_decision_first_summary_shell -q
```

Expected: fail because `TenderDecisionStrip.jsx` and `TenderSummaryTab.jsx` do not exist yet.

---

### Task 2: Implement `TenderDecisionStrip` And `TenderSummaryTab`

**Files:**
- Create: `web/src/TenderDecisionStrip.jsx`
- Create: `web/src/TenderSummaryTab.jsx`
- Modify: `web/src/TenderDetails.jsx`
- Modify: `web/src/TenderDetailsTabs.jsx`
- Modify: `web/src/useTenderDetailsUi.js`
- Modify: `web/src/styles.css`
- Test: `tests/test_frontend_contract.py`

- [ ] **Step 1: Create `TenderDecisionStrip.jsx`**

Create a presentational component with these exported names and CSS hooks:

```jsx
import { workflowLabels } from './constants'
import { documentStatusCounts, economicsStatusLabel, formatMoney, formatPercent } from './formatters'
import { SummaryMetric } from './TenderDetailsShared'

export function TenderDecisionStrip({ tender, economics, productProfiles = [], documents = [], analysis }) {
  const decision = decisionLabel(tender, economics, analysis)
  const margin = Number(economics?.margin_percent)
  const marginText = Number.isFinite(margin) ? formatPercent(margin) : 'нужны цены'
  const stopPrice = economics?.minimum_margin_price ?? economics?.break_even_price ?? economics?.interesting_price
  const documentCounts = documentStatusCounts(documents)
  const risksCount = (analysis?.risks?.length || 0) + (analysis?.red_flags?.length || 0)
  const readyProducts = productProfiles.filter((profile) => profile.raw_payload?.economics || profile.raw_payload?.selected_supplier_option).length

  return (
    <section className="decision-strip" aria-label="Решение по закупке">
      <div className="decision-strip-grid">
        <SummaryMetric value={decision} label="решение" />
        <SummaryMetric value={economics ? marginText : economicsStatusLabel(economics?.status)} label="маржа" />
        <SummaryMetric value={formatMoney(stopPrice)} label="стоп-цена" />
        <SummaryMetric value={`${readyProducts}/${productProfiles.length || tender.items?.length || 0}`} label="позиции" />
        <SummaryMetric value={risksCount} label="риски" />
        <SummaryMetric value={`${documentCounts.extracted}/${documents.length}`} label="документы" />
      </div>
    </section>
  )
}

function decisionLabel(tender, economics, analysis) {
  if (economics?.participation_decision?.label) return economics.participation_decision.label
  if ((analysis?.red_flags?.length || 0) > 0) return 'Проверить риски'
  if (economics?.margin_percent != null) return 'Можно считать'
  if (tender.workflow_status === 'skip') return 'Пропустить'
  return 'Не готово'
}
```

- [ ] **Step 2: Create `TenderSummaryTab.jsx`**

Create a default summary tab that renders only summaries and tab navigation buttons:

```jsx
import { documentStatusCounts, formatMoney, formatPercent, tenderDecisionNextStep } from './formatters'
import { SummaryMetric } from './TenderDetailsShared'

export function TenderSummaryTab({
  tender,
  economics,
  analysis,
  productProfiles = [],
  documents = [],
  onOpenTab,
}) {
  const documentCounts = documentStatusCounts(documents)
  const missingPrices = economics?.missing_cost_inputs?.length || 0
  const margin = Number(economics?.margin_percent)
  const marginText = Number.isFinite(margin) ? formatPercent(margin) : 'нужны цены'
  const risksCount = (analysis?.risks?.length || 0) + (analysis?.red_flags?.length || 0)

  return (
    <section className="detail-section active summary-section">
      <div className="section-heading-row">
        <div>
          <h3>Сводка решения</h3>
          <p className="muted-text">Короткий ответ по тендеру и следующий шаг.</p>
        </div>
      </div>

      <div className="summary-decision-grid">
        <SummaryMetric value={formatMoney(tender.price)} label="НМЦК" />
        <SummaryMetric value={marginText} label="маржа" />
        <SummaryMetric value={formatMoney(economics?.minimum_margin_price ?? economics?.break_even_price)} label="стоп-цена" />
        <SummaryMetric value={`${productProfiles.length || tender.items?.length || 0}`} label="позиции" />
        <SummaryMetric value={risksCount} label="риски" />
        <SummaryMetric value={`${documentCounts.extracted}/${documents.length}`} label="документы" />
      </div>

      <div className="summary-work-grid">
        <article className="summary-next-action">
          <span>Следующий шаг</span>
          <strong>{tenderDecisionNextStep(tender, economics)}</strong>
          <p>{missingPrices ? 'Закрыть недостающие цены в экономике.' : 'Проверить риски и документы перед финальным решением.'}</p>
        </article>
        <SummaryCard title="Экономика" action="Открыть экономику" onClick={() => onOpenTab?.('economics')}>
          <p>{economics ? `Расчет есть, маржа ${marginText}.` : 'Расчет еще не готов.'}</p>
        </SummaryCard>
        <SummaryCard title="Анализ" action="Открыть анализ" onClick={() => onOpenTab?.('analysis')}>
          <p>{analysis ? `Рисков: ${risksCount}.` : 'Анализ ТЗ еще не запускался.'}</p>
        </SummaryCard>
        <SummaryCard title="Документы" action="Открыть документы" onClick={() => onOpenTab?.('documents')}>
          <p>Извлечено текстов: {documentCounts.extracted} из {documents.length}.</p>
        </SummaryCard>
      </div>
    </section>
  )
}

function SummaryCard({ title, action, onClick, children }) {
  return (
    <article className="summary-card">
      <span>{title}</span>
      {children}
      <button className="secondary-button compact" onClick={onClick} type="button">{action}</button>
    </article>
  )
}
```

- [ ] **Step 3: Wire the components into `TenderDetails.jsx`**

Replace the old `TenderDecisionSummary` render with:

```jsx
import { TenderDecisionStrip } from './TenderDecisionStrip'
import { PriceChangeBanner } from './TenderDecisionSummary'

// ...
<TenderDecisionStrip
  tender={tender}
  economics={economics}
  productProfiles={productProfiles}
  documents={documentRecords}
  analysis={analysis}
/>
<PriceChangeBanner change={tender.price_change} />
```

- [ ] **Step 4: Wire `TenderSummaryTab` into `TenderDetailsTabs.jsx`**

Add the import:

```jsx
import { TenderSummaryTab } from './TenderSummaryTab'
```

Change tabs so the first item is:

```jsx
{ id: 'summary', label: 'Сводка' },
```

Render it before the legacy detail work modes:

```jsx
{activeTab === 'summary' && (
  <TenderSummaryTab
    tender={tender}
    economics={economics}
    analysis={analysis}
    productProfiles={productProfiles}
    documents={documentRecords}
    onOpenTab={onActiveTabChange}
  />
)}
```

- [ ] **Step 5: Change the default tab in `useTenderDetailsUi.js`**

Replace:

```js
const [activeTab, setActiveTab] = useState('overview')
setActiveTab('overview')
```

with:

```js
const [activeTab, setActiveTab] = useState('summary')
setActiveTab('summary')
```

- [ ] **Step 6: Add CSS hooks**

Add styles for `.decision-strip`, `.decision-strip-grid`, `.summary-section`, `.summary-decision-grid`, `.summary-work-grid`, `.summary-card`, and `.summary-next-action`.

- [ ] **Step 7: Run focused verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_frontend_contract.py::test_tender_workbench_uses_decision_first_summary_shell -q
```

Expected: pass.

---

### Task 3: Add Analysis Word Action And Source-Oriented Layout Hooks

**Files:**
- Modify: `tests/test_frontend_contract.py`
- Modify: `web/src/TenderAnalysisTab.jsx`
- Modify: `web/src/TenderDetailsTabs.jsx`
- Modify: `web/src/styles.css`

- [ ] **Step 1: Add failing analysis contract**

Add this test:

```python
def test_analysis_tab_exposes_word_report_and_source_evidence_workspace():
    tabs_source = TENDER_DETAILS_TABS_SOURCE.read_text(encoding="utf-8")
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "reportHref" in tabs_source
    assert "export function TenderAnalysisTab" in analysis_source
    assert "analysis-action-row" in analysis_source
    assert "Скачать Word" in analysis_source
    assert "analysis-workspace" in analysis_source
    assert "analysis-section-rail" in analysis_source
    assert "analysis-evidence-panel" in analysis_source
    assert ".analysis-workspace" in styles_source
    assert ".analysis-evidence-panel" in styles_source
    assert find_mojibake(tabs_source, TENDER_DETAILS_TABS_SOURCE) == []
    assert find_mojibake(analysis_source, TENDER_ANALYSIS_TAB_SOURCE) == []
```

- [ ] **Step 2: Pass report URL from `TenderDetailsTabs.jsx`**

Create a local report href:

```jsx
const reportHref = `/api/tenders/${encodeURIComponent(tender.source)}/${encodeURIComponent(tender.external_id)}/report.docx`
```

Pass it into `TenderAnalysisTab`:

```jsx
<TenderAnalysisTab
  analysis={analysis}
  analyzing={analyzing}
  onAnalyze={onAnalyzeTender}
  reportHref={reportHref}
  documents={documentRecords}
/>
```

- [ ] **Step 3: Update `TenderAnalysisTab.jsx`**

Add props and top actions:

```jsx
export function TenderAnalysisTab({ analysis, analyzing, onAnalyze, reportHref, documents = [] }) {
  // existing counts
  return (
    <section className="detail-section active analysis-section">
      <div className="section-heading-row analysis-action-row">
        <div>
          <h3>Анализ ТЗ</h3>
          <p className="muted-text">Риски, требования и доказательства из документов.</p>
        </div>
        <div className="analysis-actions">
          <button className="secondary-button compact" disabled={analyzing} onClick={onAnalyze} type="button">
            {analyzing ? 'Анализ...' : 'Проанализировать'}
          </button>
          <a className="secondary-button compact" href={reportHref}>Скачать Word</a>
        </div>
      </div>
      {/* existing summary and analysis content move inside analysis-workspace */}
    </section>
  )
}
```

Add lightweight workspace hooks:

```jsx
<div className="analysis-workspace">
  <aside className="analysis-section-rail">...</aside>
  <div className="analysis-main-panel">...</div>
  <aside className="analysis-evidence-panel">...</aside>
</div>
```

- [ ] **Step 4: Add CSS hooks and run focused verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_frontend_contract.py::test_analysis_tab_exposes_word_report_and_source_evidence_workspace -q
```

Expected: pass.

---

### Task 4: Reframe Economics Into A Three-Column Workspace

**Files:**
- Modify: `tests/test_frontend_contract.py`
- Modify: `web/src/TenderEconomicsTab.jsx`
- Modify: `web/src/styles.css`

- [ ] **Step 1: Add failing economics layout contract**

Add this test:

```python
def test_economics_tab_uses_three_column_position_workspace():
    economics_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "economics-position-rail" in economics_source
    assert "economics-calculation-panel" in economics_source
    assert "economics-supplier-panel" in economics_source
    assert "<ProductEconomicsForm profile={selectedEconomicsProfile}" in economics_source
    assert "<ProductSupplierOptionsForm" in economics_source
    assert ".economics-workspace-grid" in styles_source
    assert ".economics-position-rail" in styles_source
    assert ".economics-calculation-panel" in styles_source
    assert ".economics-supplier-panel" in styles_source
    assert find_mojibake(economics_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []
```

- [ ] **Step 2: Wrap existing selected-position UI into three panels**

Inside `TenderEconomicsTab`, keep existing state and handlers. Change the workbench body to:

```jsx
<div className="economics-workspace-grid">
  <aside className="economics-position-rail">
    {/* existing product profile buttons */}
  </aside>

  <section className="economics-calculation-panel">
    <ProductAutoEconomicsPanel ... />
    <ProductEconomicsForm ... />
    <ProductEconomicsAssumptionsForm ... />
  </section>

  <aside className="economics-supplier-panel">
    <ProductSupplierOptionsForm ... />
  </aside>
</div>
```

- [ ] **Step 3: Add responsive CSS**

Add desktop three-column grid:

```css
.economics-workspace-grid {
  display: grid;
  grid-template-columns: minmax(190px, 0.55fr) minmax(320px, 1fr) minmax(300px, 0.95fr);
  gap: 12px;
  align-items: start;
}
```

Add mobile fallback:

```css
@media (max-width: 1100px) {
  .economics-workspace-grid {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 4: Run focused economics contract**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_frontend_contract.py::test_economics_tab_uses_three_column_position_workspace -q
```

Expected: pass.

---

### Task 5: Full Frontend Contract, JSX Parse, Full Pytest, Commit

**Files:**
- Verify all changed files.

- [ ] **Step 1: Run frontend contract tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_frontend_contract.py -q
```

Expected: all frontend contract tests pass.

- [ ] **Step 2: Run JSX parse check**

Run the existing Node/Babel parse command pattern used in this project. If Node remains blocked in the shell, use the Node REPL MCP parser path if available. Expected: every changed JSX file parses successfully.

- [ ] **Step 3: Run full pytest**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full
```

Expected: all tests pass. If sandbox cleanup fails with `PermissionError`, rerun with approved escalation.

- [ ] **Step 4: Commit**

Stage only the implementation files and tests:

```powershell
git add tests/test_frontend_contract.py web/src/TenderDecisionStrip.jsx web/src/TenderSummaryTab.jsx web/src/TenderDetails.jsx web/src/TenderDetailsTabs.jsx web/src/useTenderDetailsUi.js web/src/TenderAnalysisTab.jsx web/src/TenderEconomicsTab.jsx web/src/styles.css
git commit -m "Add tender decision workbench shell"
```

Expected: one focused commit. Do not push unless the user asks.

---

## Self-Review

- Spec coverage: this plan covers the decision strip, `Сводка`, `Анализ` Word action, source evidence layout hooks, and the first economics three-column layout. It intentionally leaves full evidence linking and removing/demoting `Товары` for a later slice after product passport pieces are available inside analysis/economics.
- Placeholder scan: no unresolved markers or undefined future task is required for this phase.
- Type consistency: all new React props are passed from `TenderDetailsTabs.jsx` into the owning tab components; backend payload names stay unchanged.
