import { ProductAutoEconomicsPanel } from './TenderEconomicsAuto'
import { ProductEconomicsForm } from './TenderEconomicsCostForm'
import { ProductEconomicsAssumptionsForm } from './TenderEconomicsForms'
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
  onPriceCandidateConfirm,
  onPriceCandidateReject,
  onAutoEconomicsRun,
  onAutoEconomicsAccept,
  savingEconomics = false,
  savingAssumptions = false,
  savingSupplierOption = false,
  reviewingPriceCandidateId = null,
  autoEstimating = false,
  acceptingAutoEconomics = false,
}) {
  const positionTenderPrice = formatPositionTenderPrice(selectedEconomicsProfile)

  return (
    <>
      <main className="economics-workbench-main">
        <section className="economics-position-card">
          <span>Позиция #{selectedEconomicsProfile.position_index || selectedEconomicsProfileIndex + 1}</span>
          <strong>{selectedEconomicsProfile.product_name || 'Без названия'}</strong>
          <small>
            {formatQuantity(selectedEconomicsProfile.quantity, selectedEconomicsProfile.unit)}
            {positionTenderPrice ? ` · ${positionTenderPrice}` : ''}
          </small>
        </section>
        <ProductSupplierOptionsForm
          profile={selectedEconomicsProfile}
          onSelect={onSupplierOptionSelect}
          onPriceCandidateConfirm={onPriceCandidateConfirm}
          onPriceCandidateReject={onPriceCandidateReject}
          saving={savingSupplierOption}
          reviewingPriceCandidateId={reviewingPriceCandidateId}
        />
      </main>
      <aside className="economics-side-panel">
        <details className="economics-side-section" open>
          <summary>Расчет позиции</summary>
          <ProductAutoEconomicsPanel
            profile={selectedEconomicsProfile}
            onRun={onAutoEconomicsRun}
            onAccept={onAutoEconomicsAccept}
            saving={autoEstimating}
            accepting={acceptingAutoEconomics}
          />
          <ProductEconomicsForm profile={selectedEconomicsProfile} onSave={onEconomicsSave} saving={savingEconomics} />
        </details>
        <details className="economics-side-section">
          <summary>Допущения и резервы</summary>
          <ProductEconomicsAssumptionsForm
            item={economics?.items?.[selectedEconomicsProfileIndex]}
            profile={selectedEconomicsProfile}
            onSave={onEconomicsAssumptionsSave}
            saving={savingAssumptions}
          />
        </details>
      </aside>
    </>
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
