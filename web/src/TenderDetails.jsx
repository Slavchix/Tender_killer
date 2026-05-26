import { TenderDetailActions } from './TenderDetailActions'
import { TenderDetailsHeader } from './TenderDetailsHeader'
import { TenderDetailsStatusStack } from './TenderDetailsStatusStack'
import { TenderDetailsTabs } from './TenderDetailsTabs'
import { PriceChangeBanner, TenderDecisionSummary } from './TenderDecisionSummary'
import { useTenderDocumentAnalysis } from './useTenderDocumentAnalysis'
import { useTenderDetailsUi } from './useTenderDetailsUi'
import { useTenderNotification } from './useTenderNotification'
import { useTenderProductProfiles } from './useTenderProductProfiles'
import { useTenderRefreshDetails } from './useTenderRefreshDetails'
import { useTenderWorkflow } from './useTenderWorkflow'

export function TenderDetails({ tender, onTenderRefresh, onWorkflowUpdate }) {
  const { note, setNote, saving, saveWorkflow } = useTenderWorkflow(tender, onWorkflowUpdate)
  const { sending, notifyStatus, setNotifyStatus, sendToTelegram } = useTenderNotification(tender)
  const {
    documentRecords,
    setDocumentRecords,
    analysis,
    setAnalysis,
    downloading,
    extracting,
    analyzing,
    downloadStatus,
    extractStatus,
    downloadDocuments,
    extractDocumentText,
    analyzeTender,
  } = useTenderDocumentAnalysis(tender)
  const {
    raw,
    activeTab,
    setActiveTab,
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
    preparingSupplierSearchPosition,
    autoSelectingSupplierPosition,
    autoEstimatingPosition,
    acceptingAutoEconomicsPosition,
    applyProductTenderState,
    rebuildProductProfiles,
    saveProfileEconomics,
    saveProfileEconomicsAssumptions,
    saveSupplierOption,
    selectSupplierOption,
    autoSelectSupplierOption,
    prepareSupplierSearch,
    runProfileAutoEconomics,
    acceptProfileAutoEconomics,
  } = useTenderProductProfiles(tender, onTenderRefresh, setDetailStatus)
  const { refreshingDetails, refreshDetails } = useTenderRefreshDetails({
    tender,
    onTenderRefresh,
    setDetailStatus,
    setDocumentRecords,
    setAnalysis,
    applyProductTenderState,
  })

  return (
    <div className="details">
      <TenderDetailsHeader tender={tender} />

      <TenderDecisionSummary tender={tender} economics={economics} />
      <PriceChangeBanner change={tender.price_change} />

      <TenderDetailActions
        tender={tender}
        refreshingDetails={refreshingDetails}
        downloading={downloading}
        extracting={extracting}
        analyzing={analyzing}
        sending={sending}
        onRefreshDetails={refreshDetails}
        onDownloadDocuments={downloadDocuments}
        onExtractDocumentText={extractDocumentText}
        onAnalyzeTender={analyzeTender}
        onSendToTelegram={sendToTelegram}
      />

      <TenderDetailsStatusStack messages={statusMessages} />

      <TenderDetailsTabs
        tender={tender}
        raw={raw}
        activeTab={activeTab}
        onActiveTabChange={setActiveTab}
        productProfiles={productProfiles}
        productProfileSummary={productProfileSummary}
        selectedProfileIndex={selectedProfileIndex}
        onSelectedProfileIndexChange={setSelectedProfileIndex}
        profilesLoading={profilesLoading}
        onRebuildProductProfiles={rebuildProductProfiles}
        documentRecords={documentRecords}
        downloading={downloading}
        extracting={extracting}
        onDownloadDocuments={downloadDocuments}
        onExtractDocumentText={extractDocumentText}
        analysis={analysis}
        analyzing={analyzing}
        onAnalyzeTender={analyzeTender}
        economics={economics}
        onEconomicsSave={saveProfileEconomics}
        onEconomicsAssumptionsSave={saveProfileEconomicsAssumptions}
        onSupplierOptionSave={saveSupplierOption}
        onSupplierOptionSelect={selectSupplierOption}
        onSupplierOptionAutoSelect={autoSelectSupplierOption}
        onSupplierSearchPrepare={prepareSupplierSearch}
        onAutoEconomicsRun={runProfileAutoEconomics}
        onAutoEconomicsAccept={acceptProfileAutoEconomics}
        savingEconomicsPosition={savingEconomicsPosition}
        savingAssumptionsPosition={savingAssumptionsPosition}
        savingSupplierOptionPosition={savingSupplierOptionPosition}
        preparingSupplierSearchPosition={preparingSupplierSearchPosition}
        autoSelectingSupplierPosition={autoSelectingSupplierPosition}
        autoEstimatingPosition={autoEstimatingPosition}
        acceptingAutoEconomicsPosition={acceptingAutoEconomicsPosition}
        note={note}
        saving={saving}
        onNoteChange={setNote}
        onSaveWorkflow={saveWorkflow}
      />
    </div>
  )
}
