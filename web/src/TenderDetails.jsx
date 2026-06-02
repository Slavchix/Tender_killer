import { TenderDetailActions } from './TenderDetailActions'
import { TenderDecisionStrip } from './TenderDecisionStrip'
import { TenderDetailsHeader } from './TenderDetailsHeader'
import { TenderDetailsStatusStack } from './TenderDetailsStatusStack'
import { TenderDetailsTabs } from './TenderDetailsTabs'
import { PriceChangeBanner } from './TenderDecisionSummary'
import { useTenderDocumentAnalysis } from './useTenderDocumentAnalysis'
import { useTenderDetailsUi } from './useTenderDetailsUi'
import { useTenderMarketStateImport } from './useTenderMarketStateImport'
import { useTenderNotification } from './useTenderNotification'
import { useTenderProductProfiles } from './useTenderProductProfiles'
import { useTenderRefreshDetails } from './useTenderRefreshDetails'
import { useTenderWorkflow } from './useTenderWorkflow'

export function TenderDetails({ tender, onTenderRefresh, onWorkflowUpdate }) {
  const { note, setNote, saving, saveWorkflow } = useTenderWorkflow(tender, onWorkflowUpdate)
  const { notifyStatus, setNotifyStatus } = useTenderNotification(tender)
  const {
    documentRecords,
    setDocumentRecords,
    analysis,
    setAnalysis,
    downloading,
    extracting,
    analyzing,
    preparingAnalysis,
    downloadStatus,
    extractStatus,
    downloadDocuments,
    extractDocumentText,
    analyzeTender,
    prepareTenderAnalysis,
  } = useTenderDocumentAnalysis(tender)
  const {
    detailStatus,
    setDetailStatus,
    statusMessages,
  } = useTenderDetailsUi({
    tender,
    notifyStatus,
    downloadStatus,
    extractStatus,
    setNotifyStatus,
  })
  const {
    productProfiles,
    productProfileSummary,
    economics,
    selectedProfileIndex,
    setSelectedProfileIndex,
    profilesLoading,
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
    autoEstimatingPosition,
    acceptingAutoEconomicsPosition,
    supplierCatalogHealth,
    supplierCatalogHealthLoading,
    supplierCatalogHealthError,
    refreshSupplierCatalogHealth,
    applyProductTenderState,
    rebuildProductProfiles,
    saveProfileEconomics,
    saveProfileEconomicsAssumptions,
    saveSupplierOption,
    selectSupplierOption,
    autoSelectSupplierOption,
    autoSelectAllSupplierOptions,
    confirmReadyPriceCandidates,
    stagePriceCandidates,
    importSupplierDiscoveryCandidate,
    confirmPriceCandidate,
    rejectPriceCandidate,
    prepareSupplierSearch,
    saveSupplierCatalogPresets,
    runSupplierDiscovery,
    runSupplierUrlDiscovery,
    runProfileAutoEconomics,
    acceptProfileAutoEconomics,
  } = useTenderProductProfiles(tender, onTenderRefresh, setDetailStatus)
  const {
    marketImportText,
    setMarketImportText,
    importingMarketState,
    importMarketState,
  } = useTenderMarketStateImport({
    tender,
    onTenderRefresh,
    setDetailStatus,
    applyProductTenderState,
  })
  const { refreshingDetails, refreshDetails } = useTenderRefreshDetails({
    tender,
    onTenderRefresh,
    setDetailStatus,
    setDocumentRecords,
    setAnalysis,
    applyProductTenderState,
  })

  const productState = {
    productProfiles,
    productProfileSummary,
    selectedProfileIndex,
    onSelectedProfileIndexChange: setSelectedProfileIndex,
    profilesLoading,
    onRebuildProductProfiles: rebuildProductProfiles,
  }
  const documentState = {
    documentRecords,
    downloading,
    extracting,
    onDownloadDocuments: downloadDocuments,
    onExtractDocumentText: extractDocumentText,
  }
  const analysisState = {
    analysis,
    analyzing,
    preparingAnalysis,
    onAnalyzeTender: analyzeTender,
    onPrepareTenderAnalysis: prepareTenderAnalysis,
  }
  const economicsState = {
    economics,
    onEconomicsSave: saveProfileEconomics,
    onEconomicsAssumptionsSave: saveProfileEconomicsAssumptions,
    onSupplierOptionSave: saveSupplierOption,
    onSupplierOptionSelect: selectSupplierOption,
    onSupplierOptionAutoSelect: autoSelectSupplierOption,
    onSupplierOptionAutoSelectAll: autoSelectAllSupplierOptions,
    onReadyPriceCandidatesConfirmAll: confirmReadyPriceCandidates,
    onPriceCandidatesStage: stagePriceCandidates,
    onSupplierDiscoveryImport: importSupplierDiscoveryCandidate,
    onPriceCandidateConfirm: confirmPriceCandidate,
    onPriceCandidateReject: rejectPriceCandidate,
    onSupplierSearchPrepare: prepareSupplierSearch,
    onSupplierCatalogPresetsSave: saveSupplierCatalogPresets,
    onSupplierDiscoveryRun: runSupplierDiscovery,
    onSupplierUrlDiscoveryRun: runSupplierUrlDiscovery,
    onAutoEconomicsRun: runProfileAutoEconomics,
    onAutoEconomicsAccept: acceptProfileAutoEconomics,
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
    autoEstimatingPosition,
    acceptingAutoEconomicsPosition,
    supplierCatalogHealth,
    supplierCatalogHealthLoading,
    supplierCatalogHealthError,
    onSupplierCatalogHealthRefresh: refreshSupplierCatalogHealth,
  }
  const workflowState = {
    note,
    saving,
    onNoteChange: setNote,
    onSaveWorkflow: saveWorkflow,
  }

  return (
    <div className="details">
      <TenderDetailsHeader tender={tender} />

      <TenderDecisionStrip
        tender={tender}
        economics={economics}
        productProfiles={productProfiles}
        documents={documentRecords}
        analysis={analysis}
      />
      <PriceChangeBanner change={tender.price_change} />

      <TenderDetailActions
        tender={tender}
        refreshingDetails={refreshingDetails}
        onRefreshDetails={refreshDetails}
        marketImportText={marketImportText}
        importingMarketState={importingMarketState}
        onMarketImportTextChange={setMarketImportText}
        onMarketStateImport={importMarketState}
      />

      <TenderDetailsStatusStack messages={statusMessages} />

      <TenderDetailsTabs
        tender={tender}
        productState={productState}
        documentState={documentState}
        analysisState={analysisState}
        economicsState={economicsState}
        workflowState={workflowState}
      />
    </div>
  )
}
