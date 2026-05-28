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
  const {
    productProfiles,
    productProfileSummary,
    selectedProfileIndex,
    onSelectedProfileIndexChange,
    profilesLoading,
    onRebuildProductProfiles,
  } = productState
  const {
    documentRecords,
    downloading,
    extracting,
    onDownloadDocuments,
    onExtractDocumentText,
  } = documentState
  const {
    analysis,
    analyzing,
    onAnalyzeTender,
  } = analysisState
  const {
    economics,
    onEconomicsSave,
    onEconomicsAssumptionsSave,
    onSupplierOptionSave,
    onSupplierOptionSelect,
    onSupplierOptionAutoSelect,
    onSupplierDiscoveryImport,
    onSupplierSearchPrepare,
    onSupplierCatalogPresetsSave,
    onSupplierDiscoveryRun,
    onSupplierUrlDiscoveryRun,
    onAutoEconomicsRun,
    onAutoEconomicsAccept,
    savingEconomicsPosition,
    savingAssumptionsPosition,
    savingSupplierOptionPosition,
    importingSupplierCandidatePosition,
    preparingSupplierSearchPosition,
    savingSupplierCatalogPresetPosition,
    discoveringSupplierPosition,
    autoSelectingSupplierPosition,
    autoEstimatingPosition,
    acceptingAutoEconomicsPosition,
    supplierCatalogHealth,
    supplierCatalogHealthLoading,
    supplierCatalogHealthError,
    onSupplierCatalogHealthRefresh,
  } = economicsState
  const {
    raw,
    note,
    saving,
    onNoteChange,
    onSaveWorkflow,
  } = workflowState
  const tabs = [
    { id: 'summary', label: 'Сводка' },
    { id: 'products', label: `Товары ${productProfiles.length || tender.items?.length || 0}` },
    { id: 'documents', label: `Документы ${documentRecords.length}` },
    { id: 'workflow', label: 'Статус' },
  ]
  const workspaceActions = [
    { id: 'analysis', label: 'Анализ ТЗ' },
    { id: 'economics', label: 'Экономика' },
  ]
  const workspaceProps = {
    tender,
    documentRecords,
    analysis,
    analyzing,
    onAnalyzeTender,
    economics,
    productProfiles,
    selectedProfileIndex,
    onSelectedProfileIndexChange,
    onEconomicsSave,
    onEconomicsAssumptionsSave,
    onSupplierOptionSave,
    onSupplierOptionSelect,
    onSupplierOptionAutoSelect,
    onSupplierDiscoveryImport,
    onSupplierSearchPrepare,
    onSupplierCatalogPresetsSave,
    onSupplierDiscoveryRun,
    onSupplierUrlDiscoveryRun,
    onAutoEconomicsRun,
    onAutoEconomicsAccept,
    savingEconomicsPosition,
    savingAssumptionsPosition,
    savingSupplierOptionPosition,
    importingSupplierCandidatePosition,
    preparingSupplierSearchPosition,
    savingSupplierCatalogPresetPosition,
    discoveringSupplierPosition,
    autoSelectingSupplierPosition,
    autoEstimatingPosition,
    acceptingAutoEconomicsPosition,
    supplierCatalogHealth,
    supplierCatalogHealthLoading,
    supplierCatalogHealthError,
    onSupplierCatalogHealthRefresh,
  }
  const tabPanelProps = {
    activeTab,
    tender,
    raw,
    productProfiles,
    productProfileSummary,
    selectedProfileIndex,
    onSelectedProfileIndexChange,
    profilesLoading,
    onRebuildProductProfiles,
    documentRecords,
    downloading,
    extracting,
    onDownloadDocuments,
    onExtractDocumentText,
    analysis,
    economics,
    note,
    saving,
    onNoteChange,
    onSaveWorkflow,
  }

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
        onOpenTab={(tabId) => {
          if (tabId === 'analysis' || tabId === 'economics') openWorkspace(tabId)
          else openTab(tabId)
        }}
        {...tabPanelProps}
      />

      <TenderWorkspaces
        mode={workspaceMode}
        onClose={() => setWorkspaceMode(null)}
        {...workspaceProps}
      />
    </>
  )
}
