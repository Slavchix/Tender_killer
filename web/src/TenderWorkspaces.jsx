import { TenderAnalysisTab } from './TenderAnalysisTab'
import { TenderDocumentsTab } from './TenderDocumentsTab'
import { TenderEconomicsTab } from './TenderEconomicsTab'
import { TenderFullscreenWorkspace } from './TenderFullscreenWorkspace'
import { TenderProductsTab } from './TenderProductsTab'

export function TenderWorkspaces({
  mode,
  onClose,
  tender,
  productState,
  documentState,
  analysisState,
  economicsState,
}) {
  const reportHref = `/api/tenders/${encodeURIComponent(tender.source)}/${encodeURIComponent(tender.external_id)}/report.docx`
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
    productProfiles,
    productProfileSummary,
    selectedProfileIndex,
    onSelectedProfileIndexChange,
    profilesLoading,
    onRebuildProductProfiles,
  } = productState
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

  return (
    <TenderFullscreenWorkspace
      mode={mode}
      onClose={onClose}
      subtitle={tender.title}
      title={workspaceTitle(mode)}
    >
      {mode === 'products' && (
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

      {mode === 'documents' && (
        <TenderDocumentsTab
          documents={documentRecords}
          downloading={downloading}
          extracting={extracting}
          onDownload={onDownloadDocuments}
          onExtract={onExtractDocumentText}
        />
      )}

      {mode === 'analysis' && (
        <TenderAnalysisTab
          analysis={analysis}
          analyzing={analyzing}
          onAnalyze={onAnalyzeTender}
          reportHref={reportHref}
          documents={documentRecords}
        />
      )}

      {mode === 'economics' && (
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
  )
}

function workspaceTitle(mode) {
  if (mode === 'products') return 'Товары'
  if (mode === 'documents') return 'Документы'
  if (mode === 'analysis') return 'Анализ ТЗ'
  return 'Экономика'
}
