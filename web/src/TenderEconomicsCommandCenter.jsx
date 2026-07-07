import { TenderEconomicsMetrics } from './TenderEconomicsMetrics'
import {
  economicsProgressSteps,
  economicsSecondaryActions,
  nextEconomicsAction,
  priceDiscoveryJobStatusText,
} from './TenderEconomicsCommandCenterModel'

export {
  SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT,
  hasReadyPriceCandidateWithoutCost,
  profileNeedsPriceDiscovery,
} from './TenderEconomicsCommandCenterModel'

export function TenderEconomicsCommandCenter({
  tender,
  economics,
  profiles = [],
  readyPriceCandidateCount = 0,
  hasSupplierOptions = false,
  canRunActivePriceDiscovery = false,
  requiresManualPriceFlow = false,
  priceDiscoveryRunCount = 0,
  runningPriceDiscovery = false,
  confirmingReadyPriceCandidates = false,
  autoSelectingAllSuppliers = false,
  priceDiscoveryJob = null,
  onPriceDiscoveryRun,
  onReadyPriceCandidatesConfirmAll,
  onSupplierOptionAutoSelectAll,
}) {
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
          {secondaryEconomicsActions.length > 0 && (
            <details className="economics-secondary-menu">
              <summary className="economics-secondary-summary">
                Еще <span>{secondaryEconomicsActions.filter((action) => !action.disabled).length}</span>
              </summary>
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
            </details>
          )}
        </div>
      </div>
      <EconomicsProgressStepper steps={economicsSteps} />
      {requiresManualPriceFlow && (
        <p className="muted-text price-discovery-manual-required">
          Крупная закупка: используй быстрые ссылки/ссылка на товар/прайс вместо активного автопоиска цен.
        </p>
      )}
      {priceDiscoveryJobText && <p className="muted-text price-discovery-progress">{priceDiscoveryJobText}</p>}
      <TenderEconomicsMetrics tender={tender} economics={economics} profiles={profiles} />
    </div>
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
