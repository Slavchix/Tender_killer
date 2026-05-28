import { useState } from 'react'
import { TenderDetailsNavigation } from './TenderDetailsNavigation'
import { TenderTabPanels } from './TenderTabPanels'
import { TenderWorkspaces } from './TenderWorkspaces'

export function TenderDetailsTabs({
  tender,
  tabState,
  productState,
  documentState,
  analysisState,
  economicsState,
  workflowState,
}) {
  const [workspaceMode, setWorkspaceMode] = useState(null)
  const { activeTab, onActiveTabChange } = tabState
  const { productProfiles } = productState
  const { documentRecords } = documentState
  const tabs = [
    { id: 'summary', label: 'Сводка' },
    { id: 'documents', label: `Документы ${documentRecords.length}` },
    { id: 'workflow', label: 'Статус' },
  ]
  const workspaceActions = [
    { id: 'products', label: `Товары ${productProfiles.length || tender.items?.length || 0}` },
    { id: 'analysis', label: 'Анализ ТЗ' },
    { id: 'economics', label: 'Экономика' },
  ]
  const workspaceModes = new Set(workspaceActions.map((action) => action.id))

  function openTab(tabId) {
    onActiveTabChange(tabId)
  }

  function openWorkspace(mode) {
    setWorkspaceMode(mode)
  }

  return (
    <>
      <TenderDetailsNavigation
        activeTab={activeTab}
        tabs={tabs}
        workspaceMode={workspaceMode}
        workspaceActions={workspaceActions}
        onTabOpen={openTab}
        onWorkspaceOpen={openWorkspace}
      />

      <TenderTabPanels
        tender={tender}
        tabState={tabState}
        productState={productState}
        documentState={documentState}
        analysisState={analysisState}
        economicsState={economicsState}
        workflowState={workflowState}
        onOpenTab={(tabId) => {
          if (workspaceModes.has(tabId)) openWorkspace(tabId)
          else openTab(tabId)
        }}
      />

      <TenderWorkspaces
        mode={workspaceMode}
        onClose={() => setWorkspaceMode(null)}
        tender={tender}
        productState={productState}
        documentState={documentState}
        analysisState={analysisState}
        economicsState={economicsState}
      />
    </>
  )
}
