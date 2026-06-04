import { useEffect } from 'react'
import { TenderEconomicsMetrics } from './TenderEconomicsMetrics'
import { EconomicsSummary } from './TenderEconomicsSummary'
import { TenderEconomicsWorkbench } from './TenderEconomicsWorkbench'

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
  onSupplierOptionAutoSelectAll,
  onReadyPriceCandidatesConfirmAll,
  onPriceCandidatesStage,
  onAutoPricesApply,
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
  savingEconomicsPosition = null,
  savingAssumptionsPosition = null,
  savingSupplierOptionPosition = null,
  importingSupplierCandidatePosition = null,
  reviewingPriceCandidateId = null,
  preparingSupplierSearchPosition = null,
  savingSupplierCatalogPresetPosition = null,
  discoveringSupplierPosition = null,
  autoSelectingSupplierPosition = null,
  autoSelectingAllSuppliers = false,
  confirmingReadyPriceCandidates = false,
  stagingPriceCandidates = false,
  runningPriceDiscovery = false,
  applyingAutoPrices = false,
  autoEstimatingPosition = null,
  acceptingAutoEconomicsPosition = null,
  supplierCatalogHealth = null,
  supplierCatalogHealthLoading = false,
  supplierCatalogHealthError = '',
  priceDiscoveryJob = null,
  onSupplierCatalogHealthRefresh,
}) {
  const profiles = productProfiles || []
  const hasSupplierOptions = profiles.some((profile) => {
    const supplierOptions = profile?.raw_payload?.supplier_options
    return Array.isArray(supplierOptions) && supplierOptions.length > 0
  })
  const readyPriceCandidateCount = profiles.filter(hasReadyPriceCandidateWithoutCost).length
  const priceCandidateSourceCount = profiles.filter(hasPriceCandidateSource).length
  const priceDiscoveryRunCount = profiles.filter(profileNeedsPriceDiscovery).length
  const autoPriceApplyCount = Math.max(readyPriceCandidateCount, priceCandidateSourceCount)
  const priceDiscoveryJobText = priceDiscoveryJobStatusText(priceDiscoveryJob)

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
        <button
          className="secondary-button compact"
          disabled={runningPriceDiscovery || !onPriceDiscoveryRun || priceDiscoveryRunCount === 0}
          onClick={() => ignoreEconomicsActionError(onPriceDiscoveryRun?.())}
          type="button"
        >
          {runningPriceDiscovery ? 'Ищу...' : `Найти цены (${priceDiscoveryRunCount})`}
        </button>
        <button
          className="secondary-button compact"
          disabled={stagingPriceCandidates || !onPriceCandidatesStage || priceCandidateSourceCount === 0}
          onClick={() => ignoreEconomicsActionError(onPriceCandidatesStage?.())}
          type="button"
        >
          {stagingPriceCandidates ? 'Готовлю...' : `Подготовить цены (${priceCandidateSourceCount})`}
        </button>
        <button
          className="secondary-button compact"
          disabled={applyingAutoPrices || !onAutoPricesApply || autoPriceApplyCount === 0}
          onClick={() => ignoreEconomicsActionError(onAutoPricesApply?.())}
          type="button"
        >
          {applyingAutoPrices ? 'Применяю...' : `Автоцены в расчет (${autoPriceApplyCount})`}
        </button>
        <button
          className="secondary-button compact"
          disabled={confirmingReadyPriceCandidates || !onReadyPriceCandidatesConfirmAll || readyPriceCandidateCount === 0}
          onClick={() => ignoreEconomicsActionError(onReadyPriceCandidatesConfirmAll?.())}
          type="button"
        >
          {confirmingReadyPriceCandidates ? 'Принимаю...' : `Готовые цены в расчет (${readyPriceCandidateCount})`}
        </button>
        <button
          className="secondary-button compact"
          disabled={autoSelectingAllSuppliers || !onSupplierOptionAutoSelectAll || !hasSupplierOptions}
          onClick={() => ignoreEconomicsActionError(onSupplierOptionAutoSelectAll?.())}
          type="button"
        >
          {autoSelectingAllSuppliers ? 'Выбираю...' : 'Лучшие цены в расчет'}
        </button>
      </div>
      {priceDiscoveryJobText && <p className="muted-text price-discovery-progress">{priceDiscoveryJobText}</p>}
      <TenderEconomicsMetrics economics={economics} tender={tender} />
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
        onReadyPriceCandidatesConfirmAll={onReadyPriceCandidatesConfirmAll}
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

function ignoreEconomicsActionError(result) {
  if (result?.catch) {
    result.catch(() => {})
  }
}

function priceDiscoveryJobStatusText(job) {
  if (!job?.job_id) return ''
  const searched = Number(job.searched_count || 0)
  const total = Number(job.total_profiles || 0)
  const staged = Number(job.staged_count || job.result?.staged_count || 0)
  const ready = Number(job.ready_count || job.result?.ready_count || 0)
  const progress = total > 0 ? `${searched}/${total}` : `${searched}`
  if (job.status === 'failed') return `Поиск цен: ошибка, проверено ${progress}.`
  if (job.status === 'succeeded') return `Поиск цен завершен: проверено ${progress}, подготовлено ${staged}, готово ${ready}.`
  return `Поиск цен выполняется: проверено ${progress}, подготовлено ${staged}, готово ${ready}.`
}

function hasReadyPriceCandidateWithoutCost(profile) {
  if (hasPositiveEconomicsCost(profile)) return false
  const candidates = Array.isArray(profile?.price_candidates) ? profile.price_candidates : []
  return candidates.some((candidate) => {
    const reviewStatus = String(candidate?.review_status || 'pending').toLowerCase()
    return candidate?.auto_eligible === true && reviewStatus !== 'confirmed' && reviewStatus !== 'rejected'
  })
}

function hasPriceCandidateSource(profile) {
  const supplierOptions = profile?.raw_payload?.supplier_options
  const discoveryCandidates = profile?.raw_payload?.supplier_discovery?.candidates
  return (
    (Array.isArray(supplierOptions) && supplierOptions.some((option) => Number(option?.unit_price || option?.price || 0) > 0)) ||
    (Array.isArray(discoveryCandidates) && discoveryCandidates.some((candidate) => Number(candidate?.unit_price || candidate?.price || 0) > 0))
  )
}

function profileNeedsPriceDiscovery(profile) {
  return !hasPositiveEconomicsCost(profile)
}

function hasPositiveEconomicsCost(profile) {
  const economics = profile?.raw_payload?.economics || {}
  return Number(economics.unit_cost || 0) > 0 || Number(economics.total_cost || 0) > 0
}
