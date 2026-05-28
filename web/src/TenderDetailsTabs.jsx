import { useState } from 'react'
import { TenderProductsTab } from './TenderProductsTab'
import { TenderDocumentsTab } from './TenderDocumentsTab'
import { TenderAnalysisTab } from './TenderAnalysisTab'
import { TenderEconomicsTab } from './TenderEconomicsTab'
import { TenderFullscreenWorkspace } from './TenderFullscreenWorkspace'
import { TenderSummaryTab } from './TenderSummaryTab'
import { WorkflowTabPanel } from './TenderWorkflowTab'

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
  const reportHref = `/api/tenders/${encodeURIComponent(tender.source)}/${encodeURIComponent(tender.external_id)}/report.docx`
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
      <div className="detail-navigation">
        <nav className="detail-tabs" aria-label="Разделы карточки">
          {tabs.map((tab) => (
            <button
              className={activeTab === tab.id ? 'active' : ''}
              key={tab.id}
              onClick={() => openTab(tab.id)}
              type="button"
            >
              {tab.label}
            </button>
          ))}
        </nav>

        <div className="detail-workspace-launchers" aria-label="Рабочие области тендера">
          {workspaceActions.map((action) => (
            <button
              aria-haspopup="dialog"
              className={workspaceMode === action.id ? 'active' : ''}
              key={action.id}
              onClick={() => openWorkspace(action.id)}
              type="button"
            >
              {action.label}
            </button>
          ))}
        </div>
      </div>

      <div className="detail-tab-panel">
        {activeTab === 'summary' && (
          <TenderSummaryTab
            tender={tender}
            economics={economics}
            analysis={analysis}
            productProfiles={productProfiles}
            documents={documentRecords}
            onOpenTab={(tabId) => {
              if (tabId === 'analysis' || tabId === 'economics') openWorkspace(tabId)
              else openTab(tabId)
            }}
          />
        )}

        {activeTab === 'products' && (
          <TenderProductsTab
            tender={tender}
            productProfiles={productProfiles}
            productProfileSummary={productProfileSummary}
            selectedProfileIndex={selectedProfileIndex}
            onSelectedProfileIndexChange={onSelectedProfileIndexChange}
            profilesLoading={profilesLoading}
            onRebuildProductProfiles={onRebuildProductProfiles}
          />
        )}

        {activeTab === 'documents' && (
          <TenderDocumentsTab
            documents={documentRecords}
            downloading={downloading}
            extracting={extracting}
            onDownload={onDownloadDocuments}
            onExtract={onExtractDocumentText}
          />
        )}

        {activeTab === 'workflow' && (
          <WorkflowTabPanel
            tender={tender}
            raw={raw}
            note={note}
            saving={saving}
            onNoteChange={onNoteChange}
            onSaveWorkflow={onSaveWorkflow}
          />
        )}
      </div>

      <TenderFullscreenWorkspace
        mode={workspaceMode}
        onClose={() => setWorkspaceMode(null)}
        subtitle={tender.title}
        title={workspaceMode === 'analysis' ? 'Анализ ТЗ' : 'Экономика'}
      >
        {workspaceMode === 'analysis' && (
          <TenderAnalysisTab
            analysis={analysis}
            analyzing={analyzing}
            onAnalyze={onAnalyzeTender}
            reportHref={reportHref}
            documents={documentRecords}
          />
        )}

        {workspaceMode === 'economics' && (
          <TenderEconomicsTab
            tender={tender}
            economics={economics}
            productProfiles={productProfiles}
            selectedEconomicsProfileIndex={selectedProfileIndex}
            onSelectedEconomicsProfileChange={onSelectedProfileIndexChange}
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
        )}
      </TenderFullscreenWorkspace>
    </>
  )
}
