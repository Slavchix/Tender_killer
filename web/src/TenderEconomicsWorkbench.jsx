import { EconomicsPositionRail } from './TenderEconomicsPositionRail'
import { TenderEconomicsProfileWorkspace } from './TenderEconomicsProfileWorkspace'

export function TenderEconomicsWorkbench({
  economics,
  profiles = [],
  selectedEconomicsProfileIndex = 0,
  onSelectedEconomicsProfileChange,
  onEconomicsSave,
  onEconomicsAssumptionsSave,
  onSupplierOptionSave,
  onSupplierOptionSelect,
  onSupplierOptionAutoSelect,
  onSupplierDiscoveryImport,
  onPriceCandidateConfirm,
  onPriceCandidateReject,
  onSupplierSearchPrepare,
  onSupplierCatalogPresetsSave,
  onSupplierDiscoveryRun,
  onSupplierUrlDiscoveryRun,
  onAutoEconomicsRun,
  onAutoEconomicsAccept,
  savingEconomicsPosition = null,
  savingAssumptionsPosition = null,
  savingSupplierOptionPosition = null,
  importingSupplierCandidatePosition = null,
  reviewingPriceCandidateId = null,
  preparingSupplierSearchPosition = null,
  savingSupplierCatalogPresetPosition = null,
  discoveringSupplierPosition = null,
  autoSelectingSupplierPosition = null,
  autoEstimatingPosition = null,
  acceptingAutoEconomicsPosition = null,
  supplierCatalogHealth = null,
  supplierCatalogHealthLoading = false,
  supplierCatalogHealthError = '',
  onSupplierCatalogHealthRefresh,
}) {
  const selectedEconomicsProfile = profiles[selectedEconomicsProfileIndex] || profiles[0] || null
  const selectedPosition = selectedEconomicsProfile?.position_index
  const savingEconomics = savingEconomicsPosition === selectedPosition
  const savingAssumptions = savingAssumptionsPosition === selectedPosition
  const savingSupplierOption = savingSupplierOptionPosition === selectedPosition
  const importingSupplierCandidate = importingSupplierCandidatePosition === selectedPosition
  const preparingSupplierSearch = preparingSupplierSearchPosition === selectedPosition
  const savingSupplierCatalogPresets = savingSupplierCatalogPresetPosition === selectedPosition
  const discoveringDiscovery = discoveringSupplierPosition === selectedPosition
  const autoSelectingSupplier = autoSelectingSupplierPosition === selectedPosition
  const autoEstimating = autoEstimatingPosition === selectedPosition
  const acceptingAutoEconomics = acceptingAutoEconomicsPosition === selectedPosition

  return (
    <div className="economics-workbench economics-workspace-grid">
      <EconomicsPositionRail
        profiles={profiles}
        selectedEconomicsProfileIndex={selectedEconomicsProfileIndex}
        onSelectedEconomicsProfileChange={onSelectedEconomicsProfileChange}
      />
      <>
        {selectedEconomicsProfile ? (
          <TenderEconomicsProfileWorkspace
            economics={economics}
            selectedEconomicsProfile={selectedEconomicsProfile}
            selectedEconomicsProfileIndex={selectedEconomicsProfileIndex}
            onEconomicsSave={onEconomicsSave}
            onEconomicsAssumptionsSave={onEconomicsAssumptionsSave}
            onSupplierOptionSave={onSupplierOptionSave}
            onSupplierOptionSelect={onSupplierOptionSelect}
            onSupplierOptionAutoSelect={onSupplierOptionAutoSelect}
            onSupplierDiscoveryImport={onSupplierDiscoveryImport}
            onPriceCandidateConfirm={onPriceCandidateConfirm}
            onPriceCandidateReject={onPriceCandidateReject}
            onSupplierSearchPrepare={onSupplierSearchPrepare}
            onSupplierCatalogPresetsSave={onSupplierCatalogPresetsSave}
            onSupplierDiscoveryRun={onSupplierDiscoveryRun}
            onSupplierUrlDiscoveryRun={onSupplierUrlDiscoveryRun}
            onAutoEconomicsRun={onAutoEconomicsRun}
            onAutoEconomicsAccept={onAutoEconomicsAccept}
            savingEconomics={savingEconomics}
            savingAssumptions={savingAssumptions}
            savingSupplierOption={savingSupplierOption}
            importingSupplierCandidate={importingSupplierCandidate}
            reviewingPriceCandidateId={reviewingPriceCandidateId}
            preparingSupplierSearch={preparingSupplierSearch}
            savingSupplierCatalogPresets={savingSupplierCatalogPresets}
            discoveringDiscovery={discoveringDiscovery}
            autoSelectingSupplier={autoSelectingSupplier}
            autoEstimating={autoEstimating}
            acceptingAutoEconomics={acceptingAutoEconomics}
            supplierCatalogHealth={supplierCatalogHealth}
            supplierCatalogHealthLoading={supplierCatalogHealthLoading}
            supplierCatalogHealthError={supplierCatalogHealthError}
            onSupplierCatalogHealthRefresh={onSupplierCatalogHealthRefresh}
          />
        ) : (
          <section className="economics-calculation-panel economics-empty-panel">
            <p className="muted-text">Сначала обнови детали закупки, чтобы появились товарные позиции.</p>
          </section>
        )}
      </>
    </div>
  )
}
