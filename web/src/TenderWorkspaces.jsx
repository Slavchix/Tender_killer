import { TenderAnalysisTab } from './TenderAnalysisTab'
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
    preparingAnalysis,
    onAnalyzeTender,
    onPrepareTenderAnalysis,
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
    onSupplierOptionAutoSelectAll,
    onReadyPriceCandidatesConfirmAll,
    onPriceCandidatesStage,
    onPriceDiscoveryRun,
    onSupplierDiscoveryImport,
    onPriceCandidateConfirm,
    onPriceCandidateReject,
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
    reviewingPriceCandidateId,
    preparingSupplierSearchPosition,
    savingSupplierCatalogPresetPosition,
    discoveringSupplierPosition,
    autoSelectingSupplierPosition,
    autoSelectingAllSuppliers,
    confirmingReadyPriceCandidates,
    stagingPriceCandidates,
    runningPriceDiscovery,
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

      {mode === 'analysis' && (
        <TenderAnalysisTab
          analysis={analysis}
          analyzing={analyzing}
          preparingAnalysis={preparingAnalysis}
          downloading={downloading}
          extracting={extracting}
          onDownload={onDownloadDocuments}
          onExtract={onExtractDocumentText}
          onAnalyze={onAnalyzeTender}
          onPrepareAnalysis={onPrepareTenderAnalysis}
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
          onSupplierOptionAutoSelectAll={onSupplierOptionAutoSelectAll}
          onReadyPriceCandidatesConfirmAll={onReadyPriceCandidatesConfirmAll}
          onPriceCandidatesStage={onPriceCandidatesStage}
          onPriceDiscoveryRun={onPriceDiscoveryRun}
          onSupplierDiscoveryImport={onSupplierDiscoveryImport}
          onPriceCandidateConfirm={onPriceCandidateConfirm}
          onPriceCandidateReject={onPriceCandidateReject}
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
          reviewingPriceCandidateId={reviewingPriceCandidateId}
          preparingSupplierSearchPosition={preparingSupplierSearchPosition}
          savingSupplierCatalogPresetPosition={savingSupplierCatalogPresetPosition}
          discoveringSupplierPosition={discoveringSupplierPosition}
          autoSelectingSupplierPosition={autoSelectingSupplierPosition}
          autoSelectingAllSuppliers={autoSelectingAllSuppliers}
          confirmingReadyPriceCandidates={confirmingReadyPriceCandidates}
          stagingPriceCandidates={stagingPriceCandidates}
          runningPriceDiscovery={runningPriceDiscovery}
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
  if (mode === 'analysis') return 'Анализ ТЗ'
  return 'Экономика'
}
