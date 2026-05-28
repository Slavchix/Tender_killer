import { useState } from 'react'
import { TenderTabPanels } from './TenderTabPanels'
import { TenderWorkspaces } from './TenderWorkspaces'

export function TenderDetailsTabs({
  tender,
  productState,
  documentState,
  analysisState,
  economicsState,
  workflowState,
}) {
  const [workspaceMode, setWorkspaceMode] = useState(null)
  const workspaceModes = new Set(['products', 'documents', 'analysis', 'economics'])

  function openWorkspace(mode) {
    setWorkspaceMode(mode)
  }

  return (
    <>
      <TenderTabPanels
        tender={tender}
        productState={productState}
        documentState={documentState}
        analysisState={analysisState}
        economicsState={economicsState}
        workflowState={workflowState}
        onOpenTab={(tabId) => {
          if (workspaceModes.has(tabId)) openWorkspace(tabId)
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
