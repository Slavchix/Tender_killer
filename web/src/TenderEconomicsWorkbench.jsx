import { EconomicsPositionRail } from './TenderEconomicsPositionRail'
import { TenderEconomicsProfileWorkspace } from './TenderEconomicsProfileWorkspace'

export function TenderEconomicsWorkbench({
  economics,
  profiles = [],
  selectedEconomicsProfileIndex = 0,
  onSelectedEconomicsProfileChange,
  onEconomicsSave,
  onEconomicsAssumptionsSave,
  onSupplierOptionSelect,
  onSupplierDiscoveryImport,
  onSupplierSearchPrepare,
  onSupplierDiscoveryRun,
  onSupplierUrlDiscoveryRun,
  onSupplierManualPriceStage,
  onPriceCandidateConfirm,
  onPriceCandidateReject,
  onAutoEconomicsRun,
  onAutoEconomicsAccept,
  savingEconomicsPosition = null,
  savingAssumptionsPosition = null,
  savingSupplierOptionPosition = null,
  importingSupplierCandidatePosition = null,
  reviewingPriceCandidateId = null,
  preparingSupplierSearchPosition = null,
  discoveringSupplierPosition = null,
  autoEstimatingPosition = null,
  acceptingAutoEconomicsPosition = null,
}) {
  const selectedEconomicsProfile = profiles[selectedEconomicsProfileIndex] || profiles[0] || null
  const selectedPosition = selectedEconomicsProfile?.position_index
  const savingEconomics = savingEconomicsPosition === selectedPosition
  const savingAssumptions = savingAssumptionsPosition === selectedPosition
  const savingSupplierOption = savingSupplierOptionPosition === selectedPosition
  const importingSupplierCandidate = importingSupplierCandidatePosition === selectedPosition
  const preparingSupplierSearch = preparingSupplierSearchPosition === selectedPosition
  const discoveringSupplier = discoveringSupplierPosition === selectedPosition
  const autoEstimating = autoEstimatingPosition === selectedPosition
  const acceptingAutoEconomics = acceptingAutoEconomicsPosition === selectedPosition

  return (
    <section className="economics-workspace-shell" aria-label="Рабочий пульт экономики">
      <div className="economics-workbench economics-workspace-grid">
        <EconomicsPositionRail
          profiles={profiles}
          selectedEconomicsProfileIndex={selectedEconomicsProfileIndex}
          onSelectedEconomicsProfileChange={onSelectedEconomicsProfileChange}
        />
        {selectedEconomicsProfile ? (
          <TenderEconomicsProfileWorkspace
            economics={economics}
            selectedEconomicsProfile={selectedEconomicsProfile}
            selectedEconomicsProfileIndex={selectedEconomicsProfileIndex}
            onEconomicsSave={onEconomicsSave}
            onEconomicsAssumptionsSave={onEconomicsAssumptionsSave}
            onSupplierOptionSelect={onSupplierOptionSelect}
            onSupplierDiscoveryImport={onSupplierDiscoveryImport}
            onSupplierSearchPrepare={onSupplierSearchPrepare}
            onSupplierDiscoveryRun={onSupplierDiscoveryRun}
            onSupplierUrlDiscoveryRun={onSupplierUrlDiscoveryRun}
            onSupplierManualPriceStage={onSupplierManualPriceStage}
            onPriceCandidateConfirm={onPriceCandidateConfirm}
            onPriceCandidateReject={onPriceCandidateReject}
            onAutoEconomicsRun={onAutoEconomicsRun}
            onAutoEconomicsAccept={onAutoEconomicsAccept}
            savingEconomics={savingEconomics}
            savingAssumptions={savingAssumptions}
            savingSupplierOption={savingSupplierOption}
            importingSupplierCandidate={importingSupplierCandidate}
            reviewingPriceCandidateId={reviewingPriceCandidateId}
            preparingSupplierSearch={preparingSupplierSearch}
            discoveringSupplier={discoveringSupplier}
            autoEstimating={autoEstimating}
            acceptingAutoEconomics={acceptingAutoEconomics}
          />
        ) : (
          <section className="economics-calculation-panel economics-empty-panel">
            <p className="muted-text">Сначала обнови детали закупки, чтобы появились товарные позиции.</p>
          </section>
        )}
      </div>
    </section>
  )
}
