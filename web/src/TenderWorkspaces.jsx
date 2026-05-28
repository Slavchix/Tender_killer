import { TenderAnalysisTab } from './TenderAnalysisTab'
import { TenderEconomicsTab } from './TenderEconomicsTab'
import { TenderFullscreenWorkspace } from './TenderFullscreenWorkspace'

export function TenderWorkspaces({
  mode,
  onClose,
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
}) {
  const reportHref = `/api/tenders/${encodeURIComponent(tender.source)}/${encodeURIComponent(tender.external_id)}/report.docx`

  return (
    <TenderFullscreenWorkspace
      mode={mode}
      onClose={onClose}
      subtitle={tender.title}
      title={mode === 'analysis' ? 'Анализ ТЗ' : 'Экономика'}
    >
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
