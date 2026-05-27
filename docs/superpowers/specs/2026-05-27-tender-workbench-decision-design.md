# Tender Workbench Decision UX

Date: 2026-05-27.

## Goal

Make the selected tender screen a fast decision workbench, not a long detail card.
The operator should understand the current tender decision within seconds:

- whether to participate, participate cautiously, or skip;
- expected margin and stop price;
- what blocks the decision;
- which tab owns the next action.

The site remains the main workbench. Telegram remains notifications and quick entry.
The app still does not submit applications, sign documents, log into private cabinets,
or perform legally significant actions.

## Target Navigation

The selected tender area should use five top-level work modes:

1. `Сводка`
2. `Анализ`
3. `Экономика`
4. `Документы`
5. `Статус`

`Товары` should no longer be a heavy top-level destination. Product positions are
inputs to analysis and economics, so they should appear as selectors inside those
workspaces.

## Persistent Decision Strip

Every tender work mode should share a compact decision strip near the top of the
selected tender area. It is the anchor that keeps the workbench from becoming a
set of disconnected screens.

The strip should summarize:

- decision: participate, participate cautiously, skip, or not ready;
- margin and margin percent when available;
- stop price / bid threshold when available;
- product position readiness;
- risk count and highest severity;
- document processing readiness;
- next recommended step.

The strip is informational. Mutations stay in the owning tabs.

## `Сводка`

`Сводка` is the first screen for a selected tender. It should answer "what do we do
with this tender?" rather than display every raw field.

Primary sections:

- decision strip;
- short explanation of the current decision;
- economics summary: revenue, estimated costs, margin, missing price inputs;
- analysis summary: key risks, requirements, red flags, blockers;
- document summary: downloaded/extracted status and missing source material;
- next action card.

`Сводка` may link to the owning tab for each issue, but should not contain deep
forms, supplier catalog controls, raw document text, or long product cards.

## `Экономика`

`Экономика` is a dedicated calculation workspace. It should avoid vertical hunting
through many product blocks.

Target layout on desktop:

- left rail: product positions with readiness badges;
- center panel: selected position calculation, cost inputs, auto-economics, margin;
- right panel: selected position supplier options, catalog presets, discovery,
  candidate import, and supplier diagnostics.

The tender-level economics summary stays visible above the workspace. Selecting a
position updates the center and right panels without leaving the tab.

The economics tab owns:

- manual cost inputs;
- economics assumptions;
- supplier candidates and selected supplier;
- catalog presets and catalog health;
- supplier search preparation;
- supplier discovery and manual URL discovery;
- auto-economics preview and accept;
- bid thresholds and participation economics.

## `Анализ`

`Анализ` is a dedicated tender requirements and risk workspace. It should not mix
pricing forms, supplier catalogs, or economics editing into the same surface.

Top actions:

- run or refresh analysis;
- download the Word report;
- update/download/extract documents when source material is missing.

Target layout on desktop:

- left rail: analysis sections such as risks, requirements, certificates, delivery,
  acceptance, penalties, national regime;
- center panel: checklist and findings for the active section;
- right panel: evidence from documents and the effect on the tender decision.

Each finding should be checkable. Preferred shape:

- finding text;
- severity;
- category;
- source document reference;
- short evidence fragment when available;
- impact on economics or participation decision when available.

The Word report is the full export. The screen is the fast working view.

## `Документы`

`Документы` remains the source library. It owns:

- document download;
- text extraction;
- processing status;
- raw text preview;
- source file links;
- document search and extracted fragment navigation as a follow-up source-library
  capability.

Long document text should live here, not in `Сводка` or `Анализ`. Analysis should
show only evidence fragments and links back to the source document view.

## `Статус`

`Статус` owns workflow state and operator notes:

- new/open/interesting/in work/skip/archive status;
- note;
- next manual action;
- Telegram notification status if relevant.

It should not duplicate economics or analysis forms.

## Data Flow

SQLite remains the source of truth.

Existing tender detail payloads can continue to supply:

- `tender.economics`;
- `tender.product_profiles`;
- `tender.analysis`;
- `tender.documents`;
- workflow status fields.

The first implementation should be mostly frontend composition. Backend changes
are only needed when a tab needs a cleaner payload contract.

`Сводка` should derive its first version from existing payloads. A backend
decision summary service can be added in a separate slice when the frontend
contract stabilizes.

## Component Boundaries

Keep `TenderDetails.jsx` as a coordinator only.

Expected frontend modules:

- `TenderDecisionStrip.jsx`;
- `TenderSummaryTab.jsx`;
- `TenderAnalysisWorkspace.jsx`;
- `TenderEconomicsWorkspace.jsx`;
- `ProductPositionRail.jsx`;
- `ProductEconomicsEditor.jsx`;
- `SupplierWorkspace.jsx`;
- `SupplierCatalogPanel.jsx`;
- `SupplierDiscoveryPanel.jsx`;
- `TenderDocumentEvidencePanel.jsx`.

Large existing UI blocks should move out of `TenderEconomicsTab.jsx` in small,
contract-tested slices.

## Error Handling

Errors should appear in the tab that owns the failed action:

- supplier/catalog/discovery errors in `Экономика`;
- document download/extraction errors in `Документы` and as missing-source hints
  in `Анализ`;
- analysis errors in `Анализ`;
- workflow save errors in `Статус`.

`Сводка` should show readiness and blockers, not raw stack traces or low-level
API errors.

## Testing

Each rollout slice should include:

- frontend contract tests for tab labels, visible actions, and ownership;
- JSX parse check;
- targeted backend/API tests when routes or payload contracts change;
- full pytest before commit:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full
```

## Rollout Plan

1. Add `TenderDecisionStrip` and introduce `Сводка` as the default decision view.
2. Rename/reframe current `Обзор` content into the new summary model.
3. Rebuild `Экономика` into the three-column workspace without changing backend
   behavior.
4. Split supplier/catalog/discovery UI out of the current economics file.
5. Rebuild `Анализ` into a section/evidence workspace and add `Скачать Word`.
6. Keep `Документы` as source-library view and link evidence back to it.
7. Remove or demote the old heavy `Товары` top-level tab after its useful passport
   pieces are available inside analysis/economics.

## Non-Goals

- No application submission.
- No signing.
- No private-cabinet login automation.
- No automatic supplier selection that changes economics without operator review.
- No hiding source evidence behind opaque generated text.
