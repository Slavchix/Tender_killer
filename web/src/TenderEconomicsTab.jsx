import { TenderEconomicsMetrics } from './TenderEconomicsMetrics'
import { EconomicsSummary } from './TenderEconomicsSummary'
import { TenderEconomicsWorkbench } from './TenderEconomicsWorkbench'

const SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT = 5

export function TenderEconomicsTab({
  tender,
  economics,
  productProfiles = [],
  selectedEconomicsProfileIndex = 0,
  onSelectedEconomicsProfileChange,
  onEconomicsSave,
  onEconomicsAssumptionsSave,
  onSupplierOptionSelect,
  onSupplierOptionAutoSelectAll,
  onReadyPriceCandidatesConfirmAll,
  onPriceDiscoveryRun,
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
  autoSelectingAllSuppliers = false,
  confirmingReadyPriceCandidates = false,
  runningPriceDiscovery = false,
  autoEstimatingPosition = null,
  acceptingAutoEconomicsPosition = null,
  priceDiscoveryJob = null,
}) {
  const profiles = enrichEconomicsProfiles(productProfiles, tender?.items)
  const hasSupplierOptions = profiles.some((profile) => {
    const supplierOptions = profile?.raw_payload?.supplier_options
    return Array.isArray(supplierOptions) && supplierOptions.length > 0
  })
  const readyPriceCandidateCount = profiles.filter(hasReadyPriceCandidateWithoutCost).length
  const priceDiscoveryRunCount = profiles.filter(profileNeedsPriceDiscovery).length
  const canRunActivePriceDiscovery = profiles.length > 0 && profiles.length <= SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT
  const requiresManualPriceFlow = profiles.length > SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT
  const priceDiscoveryJobText = priceDiscoveryJobStatusText(priceDiscoveryJob)
  const economicsSteps = economicsProgressSteps({
    profiles,
    readyPriceCandidateCount,
    hasSupplierOptions,
    requiresManualPriceFlow,
  })
  const primaryEconomicsAction = nextEconomicsAction({
    canRunActivePriceDiscovery,
    requiresManualPriceFlow,
    priceDiscoveryRunCount,
    readyPriceCandidateCount,
    hasSupplierOptions,
    runningPriceDiscovery,
    confirmingReadyPriceCandidates,
    autoSelectingAllSuppliers,
    onPriceDiscoveryRun,
    onReadyPriceCandidatesConfirmAll,
    onSupplierOptionAutoSelectAll,
  })
  const secondaryEconomicsActions = economicsSecondaryActions({
    canRunActivePriceDiscovery,
    priceDiscoveryRunCount,
    readyPriceCandidateCount,
    hasSupplierOptions,
    runningPriceDiscovery,
    confirmingReadyPriceCandidates,
    autoSelectingAllSuppliers,
    onPriceDiscoveryRun,
    onReadyPriceCandidatesConfirmAll,
    onSupplierOptionAutoSelectAll,
  }).filter((action) => action.id !== primaryEconomicsAction?.id)

  return (
    <section className="detail-section active economics-section">
      <div className="economics-command-center">
        <div className="section-heading-row economics-command-heading">
          <div>
            <h3>Экономика</h3>
            <p>Закрой цены по позициям, проверь кандидатов и собери расчет участия.</p>
          </div>
          <div className="economics-command-actions">
            {primaryEconomicsAction && (
              <button
                className="secondary-button compact economics-primary-action"
                disabled={primaryEconomicsAction.disabled}
                onClick={() => ignoreEconomicsActionError(primaryEconomicsAction.onRun?.())}
                title={primaryEconomicsAction.description}
                type="button"
              >
                {primaryEconomicsAction.label}
              </button>
            )}
            <div className="economics-secondary-actions" aria-label="Дополнительные действия экономики">
              {secondaryEconomicsActions.map((action) => (
                <button
                  className="secondary-button compact"
                  disabled={action.disabled}
                  key={action.id}
                  onClick={() => ignoreEconomicsActionError(action.onRun?.())}
                  title={action.description}
                  type="button"
                >
                  {action.label}
                </button>
              ))}
            </div>
            {canRunActivePriceDiscovery && (
              <button
                className="secondary-button compact"
                disabled={runningPriceDiscovery || !onPriceDiscoveryRun || priceDiscoveryRunCount === 0}
                onClick={() => ignoreEconomicsActionError(onPriceDiscoveryRun?.())}
                type="button"
              >
                {runningPriceDiscovery ? 'Ищу...' : `Найти цены (${priceDiscoveryRunCount})`}
              </button>
            )}
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
        </div>
        <EconomicsProgressStepper steps={economicsSteps} />
        {requiresManualPriceFlow && (
          <p className="muted-text price-discovery-manual-required">
            Крупная закупка: используй quick links/manual URL/feed вместо активного автопоиска цен.
          </p>
        )}
        {priceDiscoveryJobText && <p className="muted-text price-discovery-progress">{priceDiscoveryJobText}</p>}
        <TenderEconomicsMetrics tender={tender} economics={economics} profiles={profiles} />
      </div>
      <TenderEconomicsWorkbench
        economics={economics}
        profiles={profiles}
        selectedEconomicsProfileIndex={selectedEconomicsProfileIndex}
        onSelectedEconomicsProfileChange={onSelectedEconomicsProfileChange}
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
        savingEconomicsPosition={savingEconomicsPosition}
        savingAssumptionsPosition={savingAssumptionsPosition}
        savingSupplierOptionPosition={savingSupplierOptionPosition}
        importingSupplierCandidatePosition={importingSupplierCandidatePosition}
        reviewingPriceCandidateId={reviewingPriceCandidateId}
        preparingSupplierSearchPosition={preparingSupplierSearchPosition}
        discoveringSupplierPosition={discoveringSupplierPosition}
        autoEstimatingPosition={autoEstimatingPosition}
        acceptingAutoEconomicsPosition={acceptingAutoEconomicsPosition}
      />
      <EconomicsSummary economics={economics} tender={tender} profiles={profiles} />
    </section>
  )
}

function ignoreEconomicsActionError(result) {
  if (result?.catch) {
    result.catch(() => {})
  }
}

function EconomicsProgressStepper({ steps = [] }) {
  if (!steps.length) return null
  return (
    <div className="economics-stepper" aria-label="Ход расчета экономики">
      {steps.map((step) => (
        <div className={`economics-step ${step.tone || 'idle'}`} key={step.id}>
          <span>{step.label}</span>
          <strong>{step.value}</strong>
          <em>{step.detail}</em>
        </div>
      ))}
    </div>
  )
}

function nextEconomicsAction({
  canRunActivePriceDiscovery,
  requiresManualPriceFlow,
  priceDiscoveryRunCount,
  readyPriceCandidateCount,
  hasSupplierOptions,
  runningPriceDiscovery,
  confirmingReadyPriceCandidates,
  autoSelectingAllSuppliers,
  onPriceDiscoveryRun,
  onReadyPriceCandidatesConfirmAll,
  onSupplierOptionAutoSelectAll,
}) {
  if (canRunActivePriceDiscovery && priceDiscoveryRunCount > 0) {
    return {
      id: 'discover',
      label: runningPriceDiscovery ? 'Ищу цены...' : `Найти цены (${priceDiscoveryRunCount})`,
      description: 'Активный автопоиск доступен только для мелкой закупки до 5 позиций.',
      disabled: runningPriceDiscovery || !onPriceDiscoveryRun,
      onRun: onPriceDiscoveryRun,
    }
  }
  if (requiresManualPriceFlow && priceDiscoveryRunCount > 0) {
    return {
      id: 'manual',
      label: `Добавить цены (${priceDiscoveryRunCount})`,
      description: 'Для крупной закупки используй ссылки, ручной URL, feed или КП без массового запуска.',
      disabled: true,
    }
  }
  if (readyPriceCandidateCount > 0) {
    return {
      id: 'ready',
      label: confirmingReadyPriceCandidates ? 'Принимаю...' : `Принять готовые (${readyPriceCandidateCount})`,
      description: 'Добавить проверенные кандидаты в расчет позиции.',
      disabled: confirmingReadyPriceCandidates || !onReadyPriceCandidatesConfirmAll,
      onRun: onReadyPriceCandidatesConfirmAll,
    }
  }
  if (hasSupplierOptions) {
    return {
      id: 'best',
      label: autoSelectingAllSuppliers ? 'Выбираю...' : 'Лучшие в расчет',
      description: 'Выбрать лучшие цены поставщиков для расчета.',
      disabled: autoSelectingAllSuppliers || !onSupplierOptionAutoSelectAll,
      onRun: onSupplierOptionAutoSelectAll,
    }
  }
  return {
    id: 'review',
    label: 'Проверить расчет',
    description: 'Цены закрыты или ожидают ручной проверки.',
    disabled: true,
  }
}

function economicsSecondaryActions({
  canRunActivePriceDiscovery,
  priceDiscoveryRunCount,
  readyPriceCandidateCount,
  hasSupplierOptions,
  runningPriceDiscovery,
  confirmingReadyPriceCandidates,
  autoSelectingAllSuppliers,
  onPriceDiscoveryRun,
  onReadyPriceCandidatesConfirmAll,
  onSupplierOptionAutoSelectAll,
}) {
  const actions = []
  if (canRunActivePriceDiscovery) {
    actions.push({
      id: 'discover',
      label: runningPriceDiscovery ? 'Ищу...' : `Поиск (${priceDiscoveryRunCount})`,
      description: 'Активный автопоиск цен по позициям.',
      disabled: runningPriceDiscovery || !onPriceDiscoveryRun || priceDiscoveryRunCount === 0,
      onRun: onPriceDiscoveryRun,
    })
  }
  actions.push({
    id: 'ready',
    label: confirmingReadyPriceCandidates ? 'Принимаю...' : `Готовые (${readyPriceCandidateCount})`,
    description: 'Принять готовых кандидатов цен.',
    disabled: confirmingReadyPriceCandidates || !onReadyPriceCandidatesConfirmAll || readyPriceCandidateCount === 0,
    onRun: onReadyPriceCandidatesConfirmAll,
  })
  actions.push({
    id: 'best',
    label: autoSelectingAllSuppliers ? 'Выбираю...' : 'Лучшие цены',
    description: 'Поставить лучшие цены в расчет.',
    disabled: autoSelectingAllSuppliers || !onSupplierOptionAutoSelectAll || !hasSupplierOptions,
    onRun: onSupplierOptionAutoSelectAll,
  })
  return actions
}

function economicsProgressSteps({
  profiles = [],
  readyPriceCandidateCount = 0,
  hasSupplierOptions = false,
  requiresManualPriceFlow = false,
}) {
  const total = profiles.length
  const priced = profiles.filter(hasPositiveEconomicsCost).length
  const missing = Math.max(0, total - priced)
  return [
    {
      id: 'prices',
      label: 'Цены',
      value: total > 0 ? `${priced}/${total}` : '0',
      detail: requiresManualPriceFlow ? 'ручной поток' : `добавить ${missing}`,
      tone: priced === total && total > 0 ? 'done' : missing > 0 ? 'active' : 'idle',
    },
    {
      id: 'candidates',
      label: 'Кандидаты',
      value: String(readyPriceCandidateCount),
      detail: readyPriceCandidateCount > 0 ? 'готовы к приемке' : 'очередь пуста',
      tone: readyPriceCandidateCount > 0 ? 'active' : 'idle',
    },
    {
      id: 'calculation',
      label: 'Расчет',
      value: hasSupplierOptions ? 'варианты' : priced > 0 ? 'собирается' : 'ждет цен',
      detail: hasSupplierOptions ? 'можно выбрать' : 'маржа после цен',
      tone: hasSupplierOptions || (priced === total && total > 0) ? 'done' : 'idle',
    },
  ]
}

function enrichEconomicsProfiles(productProfiles = [], tenderItems = []) {
  const itemByPosition = new Map()
  ;(Array.isArray(tenderItems) ? tenderItems : []).forEach((item, index) => {
    if (!item || typeof item !== 'object') return
    const positionIndex = Number(item.position_index || index + 1)
    if (Number.isFinite(positionIndex) && positionIndex > 0) {
      itemByPosition.set(positionIndex, item)
    }
  })

  return (Array.isArray(productProfiles) ? productProfiles : []).map((profile) => {
    if (!profile || typeof profile !== 'object') return profile
    const positionIndex = Number(profile.position_index || 0)
    const item = itemByPosition.get(positionIndex)
    if (!item) return profile
    const enriched = { ...profile }
    ;['quantity', 'unit', 'unit_price', 'total_price'].forEach((key) => {
      if ((enriched[key] == null || enriched[key] === '') && item[key] != null && item[key] !== '') {
        enriched[key] = item[key]
      }
    })
    return enriched
  })
}

function priceDiscoveryJobStatusText(job) {
  if (!job?.job_id) return ''
  const searched = Number(job.searched_count || 0)
  const total = Number(job.total_profiles || 0)
  const staged = Number(job.staged_count || job.result?.staged_count || 0)
  const ready = Number(job.ready_count || job.result?.ready_count || 0)
  const progress = total > 0 ? `${searched}/${total}` : `${searched}`
  const completedByProgress = job.status === 'running' && total > 0 && searched >= total
  if (job.status === 'failed') return `Поиск цен: ошибка, проверено ${progress}.`
  if (job.status === 'succeeded' || completedByProgress) return `Поиск цен завершен: проверено ${progress}, подготовлено ${staged}, готово ${ready}.`
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

function profileNeedsPriceDiscovery(profile) {
  return !hasPositiveEconomicsCost(profile)
}

function hasPositiveEconomicsCost(profile) {
  const economics = profile?.raw_payload?.economics || {}
  return Number(economics.unit_cost || 0) > 0 || Number(economics.total_cost || 0) > 0
}
