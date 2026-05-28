import { useEffect } from 'react'
import { EconomicsSummary } from './TenderEconomicsSummary'
import { TenderEconomicsWorkbench } from './TenderEconomicsWorkbench'
import {
  economicsStatusLabel,
  formatMoney,
  formatPercent,
  marketStateValue,
  nmcPriceValue,
  participantBidValue,
} from './formatters'
import { SummaryMetric } from './TenderDetailsShared'

export function TenderEconomicsTab({
  tender,
  economics,
  productProfiles = [],
  selectedEconomicsProfileIndex = 0,
  onSelectedEconomicsProfileChange,
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
  savingEconomicsPosition = null,
  savingAssumptionsPosition = null,
  savingSupplierOptionPosition = null,
  importingSupplierCandidatePosition = null,
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
  const marketState = economics?.market_state || tender?.market_state
  const missingInputs = economics?.missing_cost_inputs?.length || 0
  const displayedRevenue = economics?.revenue ?? marketState?.nmc_price ?? tender?.price
  const revenueLabel = economics?.revenue_kind === 'current_offer' ? 'Цена участника' : 'НМЦК'
  const profiles = productProfiles || []

  useEffect(() => {
    if (supplierCatalogHealth || supplierCatalogHealthLoading || supplierCatalogHealthError) return
    onSupplierCatalogHealthRefresh?.(false)?.catch?.(() => {})
  }, [
    onSupplierCatalogHealthRefresh,
    supplierCatalogHealth,
    supplierCatalogHealthLoading,
    supplierCatalogHealthError,
  ])

  return (
    <section className="detail-section active economics-section">
      <div className="section-heading-row">
        <h3>Экономика</h3>
      </div>
      <div className="economics-tab-summary tab-summary-grid" aria-label="Сводка экономики">
        <SummaryMetric value={economics ? economicsStatusLabel(economics.status) : 'не рассчитана'} label="статус" />
        <SummaryMetric value={nmcPriceValue(tender, marketState)} label="НМЦК" />
        <SummaryMetric value={participantBidValue(economics?.market_state || tender?.market_state)} label="ставка участника" />
        <SummaryMetric value={marketStateValue(economics?.market_state || tender?.market_state)} label="рынок" />
        <SummaryMetric value={formatMoney(displayedRevenue)} label={revenueLabel} />
        <SummaryMetric value={formatMoney(economics?.estimated_total_cost)} label="затраты" />
        <SummaryMetric value={formatMoney(economics?.break_even_price)} label="безубыток" />
        <SummaryMetric value={economics ? formatPercent(economics.margin_percent) : 'нет'} label="маржа" />
        <SummaryMetric value={missingInputs} label="цен добавить" />
      </div>
      <EconomicsSummary economics={economics} tender={tender} />
      <TenderEconomicsWorkbench
        economics={economics}
        profiles={profiles}
        selectedEconomicsProfileIndex={selectedEconomicsProfileIndex}
        onSelectedEconomicsProfileChange={onSelectedEconomicsProfileChange}
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
    </section>
  )
}
