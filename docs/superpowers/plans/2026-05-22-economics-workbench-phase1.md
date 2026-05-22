# Economics Workbench Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move manual product cost and supplier candidate controls from the product card into the `Экономика` workbench without changing persistence.

**Architecture:** Keep existing API endpoints and storage fields. Reuse `ProductEconomicsForm` and `ProductSupplierOptionsForm`, but render them from `EconomicsTabPanel` against the selected product profile. Product detail keeps passport and requirements only.

**Tech Stack:** React in `web/src/App.jsx`, CSS in `web/src/styles.css`, frontend contract tests in `tests/test_frontend_contract.py`, Python pytest verification.

---

## File Map

- Modify `web/src/App.jsx`: pass product profile state/actions into `EconomicsTabPanel`, add selected economics position UI, remove pricing/supplier modes from `ProductProfileDetail`.
- Modify `web/src/styles.css`: add economics workbench layout styles.
- Modify `tests/test_frontend_contract.py`: assert economics owns forms and product passport no longer owns money tabs.

---

## Task 1: Frontend Contract For Economics-Owned Money Forms

**Files:**
- Modify: `tests/test_frontend_contract.py`

- [ ] **Step 1: Write failing contract test**

Add a test that asserts:

```python
def test_economics_tab_owns_product_costs_and_suppliers():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "function EconomicsTabPanel({" in app_source
    assert "productProfiles" in app_source
    assert "selectedEconomicsProfileIndex" in app_source
    assert "<ProductEconomicsForm profile={selectedEconomicsProfile}" in app_source
    assert "<ProductSupplierOptionsForm profile={selectedEconomicsProfile}" in app_source
    assert "economics-workbench" in app_source
    assert ".economics-workbench" in styles_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []
```

- [ ] **Step 2: Write failing product passport test**

Add a test that asserts:

```python
def test_product_detail_keeps_passport_and_requirements_only():
    app_source = APP_SOURCE.read_text(encoding="utf-8")

    assert "const productDetailModes = [" in app_source
    assert "{ id: 'pricing'" not in app_source
    assert "{ id: 'suppliers'" not in app_source
    assert "activeProfileMode === 'pricing'" not in app_source
    assert "activeProfileMode === 'suppliers'" not in app_source
    assert find_mojibake(app_source, APP_SOURCE) == []
```

- [ ] **Step 3: Run red tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_frontend_contract.py::test_economics_tab_owns_product_costs_and_suppliers tests\test_frontend_contract.py::test_product_detail_keeps_passport_and_requirements_only -q -p no:cacheprovider --basetemp pytest-cache-files-economics-workbench-red
```

Expected: fail because economics tab does not own forms yet and product detail still contains pricing/supplier modes.

---

## Task 2: Move Forms Into Economics Tab

**Files:**
- Modify: `web/src/App.jsx`
- Modify: `web/src/styles.css`

- [ ] **Step 1: Pass state/actions to `EconomicsTabPanel`**

Change the economics tab render to:

```jsx
<EconomicsTabPanel
  tender={tender}
  economics={economics}
  productProfiles={productProfiles}
  selectedEconomicsProfileIndex={selectedProfileIndex}
  onSelectedEconomicsProfileChange={setSelectedProfileIndex}
  onEconomicsSave={saveProfileEconomics}
  onSupplierOptionSave={saveSupplierOption}
  savingEconomicsPosition={savingEconomicsPosition}
  savingSupplierOptionPosition={savingSupplierOptionPosition}
/>
```

- [ ] **Step 2: Render product list and selected position in `EconomicsTabPanel`**

Inside `EconomicsTabPanel`, derive:

```jsx
const profiles = productProfiles || []
const selectedEconomicsProfile = profiles[selectedEconomicsProfileIndex] || profiles[0] || null
```

Render:

```jsx
<div className="economics-workbench">
  <div className="economics-position-list">...</div>
  <div className="economics-position-panel">
    <ProductEconomicsForm profile={selectedEconomicsProfile} onSave={onEconomicsSave} saving={...} />
    <ProductSupplierOptionsForm profile={selectedEconomicsProfile} onSave={onSupplierOptionSave} saving={...} />
  </div>
</div>
```

Use existing `profile-row`, `profile-name`, `profile-meta`, and `profile-status` classes for the list.

- [ ] **Step 3: Remove money forms from `ProductProfileDetail`**

Remove props:

```jsx
onEconomicsSave
onSupplierOptionSave
savingEconomics
savingSupplierOption
```

Remove rendering branches:

```jsx
activeProfileMode === 'pricing'
activeProfileMode === 'suppliers'
```

Keep `overview` and `requirements`.

- [ ] **Step 4: Update `productDetailModes`**

Change to:

```jsx
const productDetailModes = [
  { id: 'overview', label: 'Паспорт' },
  { id: 'requirements', label: 'ТЗ' },
]
```

- [ ] **Step 5: Add CSS**

Add:

```css
.economics-workbench {
  display: grid;
  grid-template-columns: minmax(180px, 0.8fr) minmax(0, 1.4fr);
  gap: 10px;
  align-items: start;
}

.economics-position-list {
  max-height: 460px;
  overflow: auto;
  background: #202b27;
  border: 1px solid #304039;
  border-radius: 7px;
}

.economics-position-panel {
  display: grid;
  gap: 10px;
  min-width: 0;
}

@media (max-width: 760px) {
  .economics-workbench {
    grid-template-columns: 1fr;
  }
}
```

---

## Task 3: Verify And Commit

**Files:**
- Modify: `tests/test_frontend_contract.py`
- Modify: `web/src/App.jsx`
- Modify: `web/src/styles.css`

- [ ] **Step 1: Run frontend contract**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_frontend_contract.py -q -p no:cacheprovider --basetemp pytest-cache-files-economics-workbench
```

- [ ] **Step 2: Parse JSX**

Run the Babel parser through Node REPL:

```js
const fs = await import('node:fs/promises')
const parser = await import('@babel/parser')
const source = await fs.readFile('C:/Users/zinin.v.a/Documents/tender_killer/web/src/App.jsx', 'utf8')
parser.parse(source, { sourceType: 'module', plugins: ['jsx'] })
```

- [ ] **Step 3: Run focused tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_frontend_contract.py tests\test_economics.py tests\test_economics_service.py tests\test_supplier_option_service.py -q -p no:cacheprovider --basetemp pytest-cache-files-economics-workbench-focused
```

- [ ] **Step 4: Run full tests**

Run outside sandbox:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full
```

- [ ] **Step 5: Commit and push**

```powershell
git add docs/superpowers/plans/2026-05-22-economics-workbench-phase1.md tests/test_frontend_contract.py web/src/App.jsx web/src/styles.css
git commit -m "Move pricing controls to economics tab"
git push origin codex/moscow-mo-parser
```
