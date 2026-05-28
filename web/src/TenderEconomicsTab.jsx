import { useEffect } from 'react'
import { AnalysisList } from './TenderAnalysisTab'
import {
  ProductEconomicsAssumptionsForm,
  ProductEconomicsForm,
} from './TenderEconomicsForms'
import { ProductSupplierOptionsForm } from './TenderEconomicsSuppliers'
import { EconomicsSummary } from './TenderEconomicsSummary'
import {
  economicsStatusLabel,
  formatConfidence,
  formatCostDriver,
  formatMoney,
  formatPercent,
  formatQuantity,
  marketStateValue,
  nmcPriceValue,
  participantBidValue,
  profileStatusLabel,
  taxModeLabel,
} from './formatters'
import { Info, SummaryMetric } from './TenderDetailsShared'

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
      <div className="economics-workbench economics-workspace-grid">
        <aside className="economics-position-rail" role="listbox" aria-label="Позиции для экономики">
          {profiles.length ? profiles.map((profile, index) => {
            const supplierOptions = Array.isArray(profile.raw_payload?.supplier_options)
              ? profile.raw_payload.supplier_options
              : []
            const profileEconomics = profile.raw_payload?.economics || {}
            const costValue = profileEconomics.total_cost ?? profileEconomics.unit_cost
            return (
              <button
                className={index === selectedEconomicsProfileIndex ? 'profile-row economics-profile-row selected' : 'profile-row economics-profile-row'}
                key={`${profile.position_index}-${profile.product_name}-${index}`}
                onClick={() => onSelectedEconomicsProfileChange?.(index)}
                type="button"
              >
                <span className="profile-position">#{profile.position_index || index + 1}</span>
                <span className="profile-name">{profile.product_name || 'Без названия'}</span>
                <span className="profile-meta quantity">{formatQuantity(profile.quantity, profile.unit)}</span>
                <span className="profile-meta classifier">
                  {costValue ? `себестоимость ${formatMoney(costValue)}` : `${supplierOptions.length} поставщиков`}
                </span>
                <span className={`profile-status ${profile.profile_status || 'draft'}`}>{profileStatusLabel(profile.profile_status)}</span>
              </button>
            )
          }) : (
            <p className="muted-text">Товарные позиции пока не сформированы.</p>
          )}
        </aside>
        <>
          {selectedEconomicsProfile ? (
            <>
              <section className="economics-calculation-panel">
                <div className="economics-position-heading">
                  <span>Позиция #{selectedEconomicsProfile.position_index || selectedEconomicsProfileIndex + 1}</span>
                  <strong>{selectedEconomicsProfile.product_name || 'Без названия'}</strong>
                </div>
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
              <aside className="economics-supplier-panel">
                <ProductSupplierOptionsForm
                  profile={selectedEconomicsProfile}
                  onSave={onSupplierOptionSave}
                  onSelect={onSupplierOptionSelect}
                  onAutoSelect={onSupplierOptionAutoSelect}
                  onDiscoveryImport={onSupplierDiscoveryImport}
                  onSearchPrepare={onSupplierSearchPrepare}
                  onPresetSave={onSupplierCatalogPresetsSave}
                  onDiscoveryRun={onSupplierDiscoveryRun}
                  onDiscoveryUrlRun={onSupplierUrlDiscoveryRun}
                  supplierCatalogHealth={supplierCatalogHealth}
                  supplierCatalogHealthLoading={supplierCatalogHealthLoading}
                  supplierCatalogHealthError={supplierCatalogHealthError}
                  onSupplierCatalogHealthRefresh={onSupplierCatalogHealthRefresh}
                  saving={savingSupplierOption}
                  importingDiscovery={importingSupplierCandidate}
                  preparingSearch={preparingSupplierSearch}
                  savingPresets={savingSupplierCatalogPresets}
                  discoveringDiscovery={discoveringDiscovery}
                  autoSelecting={autoSelectingSupplier}
                />
              </aside>
            </>
          ) : (
            <section className="economics-calculation-panel economics-empty-panel">
              <p className="muted-text">Сначала обнови детали закупки, чтобы появились товарные позиции.</p>
            </section>
          )}
        </>
      </div>
    </section>
  )
}

function ProductAutoEconomicsPanel({ profile, onRun, onAccept, saving = false, accepting = false }) {
  const estimate = profile?.raw_payload?.economics_auto || null
  const costDrivers = Array.isArray(estimate?.cost_drivers) ? estimate.cost_drivers : []
  const needsReview = Array.isArray(estimate?.needs_review) ? estimate.needs_review : []

  return (
    <section className="auto-economics-panel">
      <div className="profile-block-heading">
        <h5>Авторасчет</h5>
        <div className="auto-economics-actions">
          <button className="secondary-button compact" disabled={saving || !onRun} onClick={() => onRun?.(profile)} type="button">
            {saving ? 'Расчет...' : 'Рассчитать'}
          </button>
          <button className="secondary-button compact" disabled={accepting || !estimate || !onAccept} onClick={() => onAccept?.(profile)} type="button">
            {accepting ? 'Применяю...' : 'Принять в расчет'}
          </button>
        </div>
      </div>
      {estimate ? (
        <>
          <div className="auto-economics-metrics">
            <Info label="Итого" value={formatMoney(estimate.estimated_total_cost)} />
            <Info label="Скрытые расходы" value={formatMoney(estimate.hidden_costs_total)} />
            <Info label="Резерв" value={formatMoney(estimate.risk_reserve)} />
            <Info label="НДС" value={taxModeLabel(estimate.tax_mode, estimate.vat_rate_percent)} />
            <Info label="Уверенность" value={formatConfidence(estimate.confidence)} />
          </div>
          {estimate.manual_inputs_present && (
            <p className="auto-economics-note">Ручная экономика уже заполнена, авторасчет сохранен как черновик.</p>
          )}
          <p className="auto-economics-note">Авторасчет заполнит пустые допущения по НДС, резерву и марже.</p>
          <AnalysisList
            title="Факторы расходов"
            items={costDrivers.map(formatCostDriver)}
            empty="Скрытые расходы пока не найдены"
          />
          <AnalysisList
            title="Проверить вручную"
            items={needsReview}
            empty="Критичных проверок пока нет"
            danger={needsReview.length > 0}
          />
        </>
      ) : (
        <p className="muted-text">Черновик авторасчета пока не построен.</p>
      )}
    </section>
  )
}
