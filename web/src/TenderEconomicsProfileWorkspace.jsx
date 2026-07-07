import { ProductAutoEconomicsPanel } from './TenderEconomicsAuto'
import { ProductEconomicsForm } from './TenderEconomicsCostForm'
import { ProductEconomicsAssumptionsForm } from './TenderEconomicsForms'
import { ManualSupplierPricePanel } from './TenderEconomicsManualSupplierPricePanel'
import { PositionEconomicsScenario, buildPositionScenarioState } from './TenderEconomicsPositionScenario'
import { ProductSupplierOptionsForm } from './TenderEconomicsSuppliers'
import { tenderReferenceTotalPrice, tenderReferenceUnitPrice } from './TenderEconomicsPriceComparison'
import { formatMoney, formatQuantity } from './formatters'

export function TenderEconomicsProfileWorkspace({
  economics,
  selectedEconomicsProfile,
  selectedEconomicsProfileIndex = 0,
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
  savingEconomics = false,
  savingAssumptions = false,
  savingSupplierOption = false,
  importingSupplierCandidate = false,
  reviewingPriceCandidateId = null,
  preparingSupplierSearch = false,
  discoveringSupplier = false,
  autoEstimating = false,
  acceptingAutoEconomics = false,
}) {
  const positionTenderPrice = formatPositionTenderPrice(selectedEconomicsProfile)
  const selectedEconomicsItem = economics?.items?.[selectedEconomicsProfileIndex]
  const positionScenarioState = buildPositionScenarioState(selectedEconomicsProfile, selectedEconomicsItem)

  return (
    <main className="economics-workbench-main">
      <section className="economics-position-card">
        <span>Позиция #{selectedEconomicsProfile.position_index || selectedEconomicsProfileIndex + 1}</span>
        <strong>{selectedEconomicsProfile.product_name || 'Без названия'}</strong>
        <small>
          {formatQuantity(selectedEconomicsProfile.quantity, selectedEconomicsProfile.unit)}
          {positionTenderPrice ? ` · ${positionTenderPrice}` : ''}
        </small>
      </section>
      <PositionEconomicsScenario
        acceptingAutoEconomics={acceptingAutoEconomics}
        autoEstimating={autoEstimating}
        onAutoEconomicsAccept={onAutoEconomicsAccept}
        onAutoEconomicsRun={onAutoEconomicsRun}
        onPriceCandidateConfirm={onPriceCandidateConfirm}
        profile={selectedEconomicsProfile}
        reviewingPriceCandidateId={reviewingPriceCandidateId}
        scenario={positionScenarioState}
      />
      <section className="economics-center-calculation" id="position-calculation-panel" aria-label="Расчет позиции">
        <ProductAutoEconomicsPanel
          profile={selectedEconomicsProfile}
          onRun={onAutoEconomicsRun}
          onAccept={onAutoEconomicsAccept}
          saving={autoEstimating}
          accepting={acceptingAutoEconomics}
        />
        <ProductEconomicsForm profile={selectedEconomicsProfile} onSave={onEconomicsSave} saving={savingEconomics} />
        <ProductEconomicsAssumptionsForm
          item={economics?.items?.[selectedEconomicsProfileIndex]}
          profile={selectedEconomicsProfile}
          onSave={onEconomicsAssumptionsSave}
          saving={savingAssumptions}
        />
      </section>
      <ProductSupplierOptionsForm
        profile={selectedEconomicsProfile}
        onSelect={onSupplierOptionSelect}
        onPriceCandidateConfirm={onPriceCandidateConfirm}
        onPriceCandidateReject={onPriceCandidateReject}
        saving={savingSupplierOption}
        reviewingPriceCandidateId={reviewingPriceCandidateId}
      />
      <ManualSupplierPricePanel
        selectedEconomicsProfile={selectedEconomicsProfile}
        importingSupplierCandidate={importingSupplierCandidate}
        preparingSupplierSearch={preparingSupplierSearch}
        discoveringSupplier={discoveringSupplier}
        onSupplierDiscoveryImport={onSupplierDiscoveryImport}
        onSupplierSearchPrepare={onSupplierSearchPrepare}
        onSupplierDiscoveryRun={onSupplierDiscoveryRun}
        onSupplierUrlDiscoveryRun={onSupplierUrlDiscoveryRun}
        onSupplierManualPriceStage={onSupplierManualPriceStage}
      />
    </main>
  )
}

function formatPositionTenderPrice(profile) {
  const unitPrice = tenderReferenceUnitPrice(profile)
  const totalPrice = tenderReferenceTotalPrice(profile)
  const parts = []
  if (unitPrice != null) parts.push(`цена тендера ${formatMoney(unitPrice)}`)
  if (totalPrice != null) parts.push(`сумма ${formatMoney(totalPrice)}`)
  return parts.join(' · ')
}
