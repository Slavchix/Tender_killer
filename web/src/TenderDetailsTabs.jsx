import { useState } from 'react'
import { TenderDetailsNavigation } from './TenderDetailsNavigation'
import { TenderTabPanels } from './TenderTabPanels'
import { TenderWorkspaces } from './TenderWorkspaces'

export function TenderDetailsTabs({
  tender,
  raw,
  activeTab,
  onActiveTabChange,
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
  analyzing,
  onAnalyzeTender,
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
  note,
  saving,
  onNoteChange,
  onSaveWorkflow,
}) {
  const [workspaceMode, setWorkspaceMode] = useState(null)
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
        activeTab={activeTab}
        tender={tender}
        raw={raw}
        productProfiles={productProfiles}
        productProfileSummary={productProfileSummary}
        selectedProfileIndex={selectedProfileIndex}
        onSelectedProfileIndexChange={onSelectedProfileIndexChange}
        profilesLoading={profilesLoading}
        onRebuildProductProfiles={onRebuildProductProfiles}
        documentRecords={documentRecords}
        downloading={downloading}
        extracting={extracting}
        onDownloadDocuments={onDownloadDocuments}
        onExtractDocumentText={onExtractDocumentText}
        analysis={analysis}
        economics={economics}
        onOpenTab={(tabId) => {
          if (tabId === 'analysis' || tabId === 'economics') openWorkspace(tabId)
          else openTab(tabId)
        }}
        note={note}
        saving={saving}
        onNoteChange={onNoteChange}
        onSaveWorkflow={onSaveWorkflow}
      />

      <TenderWorkspaces
        mode={workspaceMode}
        onClose={() => setWorkspaceMode(null)}
        tender={tender}
        documentRecords={documentRecords}
        analysis={analysis}
        analyzing={analyzing}
        onAnalyzeTender={onAnalyzeTender}
        economics={economics}
        productProfiles={productProfiles}
        selectedProfileIndex={selectedProfileIndex}
        onSelectedProfileIndexChange={onSelectedProfileIndexChange}
        onEconomicsSave={onEconomicsSave}
        onEconomicsAssumptionsSave={onEconomicsAssumptionsSave}
        onSupplierOptionSave={onSupplierOptionSave}
        onSupplierOptionSelect={onSupplierOptionSelect}
        onSupplierOptionAutoSelect={onSupplierOptionAutoSelect}
        onSupplierDiscoveryImport={onSupplierDiscoveryImport}
        onSupplierSearchPrepare={onSupplierSearchPrepare}
        onSupplierCatalogPresetsSave={onSupplierCatalogPresetsSave}
        onSupplierDiscoveryRun={onSupplierDiscoveryRun}
        onSupplierUrlDiscoveryRun={onSupplierUrlDiscoveryRun}
        onAutoEconomicsRun={onAutoEconomicsRun}
        onAutoEconomicsAccept={onAutoEconomicsAccept}
        savingEconomicsPosition={savingEconomicsPosition}
        savingAssumptionsPosition={savingAssumptionsPosition}
        savingSupplierOptionPosition={savingSupplierOptionPosition}
        importingSupplierCandidatePosition={importingSupplierCandidatePosition}
        preparingSupplierSearchPosition={preparingSupplierSearchPosition}
        savingSupplierCatalogPresetPosition={savingSupplierCatalogPresetPosition}
        discoveringSupplierPosition={discoveringSupplierPosition}
        autoSelectingSupplierPosition={autoSelectingSupplierPosition}
        autoEstimatingPosition={autoEstimatingPosition}
        acceptingAutoEconomicsPosition={acceptingAutoEconomicsPosition}
        supplierCatalogHealth={supplierCatalogHealth}
        supplierCatalogHealthLoading={supplierCatalogHealthLoading}
        supplierCatalogHealthError={supplierCatalogHealthError}
        onSupplierCatalogHealthRefresh={onSupplierCatalogHealthRefresh}
      />
    </>
  )
}
