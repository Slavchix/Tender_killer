import { AnalysisList } from './TenderAnalysisSections'
import {
  formatConfidence,
  formatCostDriver,
  formatMoney,
  taxModeLabel,
} from './formatters'
import { Info } from './TenderDetailsShared'

export function ProductAutoEconomicsPanel({ profile, onRun, onAccept, saving = false, accepting = false }) {
  const estimate = normalizeAutoEconomicsEstimate(profile?.raw_payload?.economics_auto || null)
  const priceEvidence = supplierPriceEvidence(estimate)
  const costDrivers = Array.isArray(estimate?.cost_drivers) ? estimate.cost_drivers : []
  const needsReview = Array.isArray(estimate?.needs_review) ? estimate.needs_review : []
  const canAcceptEstimate = Boolean(estimate && priceEvidence)

  return (
    <section className="auto-economics-panel">
      <div className="profile-block-heading">
        <h5>Авторасчет</h5>
        <div className="auto-economics-actions">
          <button className="secondary-button compact" disabled={saving || !onRun} onClick={() => onRun?.(profile)} type="button">
            {saving ? 'Расчет...' : 'Рассчитать'}
          </button>
          <button className="secondary-button compact" disabled={accepting || !canAcceptEstimate || !onAccept} onClick={() => onAccept?.(profile)} type="button">
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
          <AutoEconomicsPriceSource estimate={estimate} evidence={priceEvidence} />
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

function AutoEconomicsPriceSource({ estimate, evidence }) {
  if (!evidence) {
    return (
      <div className="price-source-note needs_review">
        <span>Источник цены</span>
        <strong>Цена поставщика не выбрана</strong>
        <em>Цена позиции тендера используется только как справка, не как себестоимость.</em>
      </div>
    )
  }

  const supplier = evidence.value || evidence.url || 'поставщик'
  const mode = evidence.source === 'selected_supplier' ? 'выбран вручную' : 'лучший кандидат'

  return (
    <div className="price-source-note confirmed">
      <span>Источник цены</span>
      <strong>{supplier} · {formatMoney(estimate.estimated_unit_cost)}</strong>
      <em>{mode}</em>
      {evidence.url && (
        <a className="price-source-link" href={evidence.url} rel="noreferrer" target="_blank">
          Открыть товар
        </a>
      )}
    </div>
  )
}

function supplierPriceEvidence(estimate) {
  const evidence = Array.isArray(estimate?.evidence) ? estimate.evidence : []
  return evidence.find((item) => (
    item?.source === 'selected_supplier'
    || item?.source === 'best_supplier_option'
    || item?.url
  )) || null
}

function normalizeAutoEconomicsEstimate(estimate) {
  if (!estimate) return null
  const baseSource = String(estimate.base_source || '')
  if (!baseSource.startsWith('source_position')) return estimate

  const needsReview = Array.isArray(estimate.needs_review) ? estimate.needs_review : []
  return {
    ...estimate,
    status: 'needs_review',
    estimated_unit_cost: 0,
    base_total_cost: 0,
    hidden_costs_total: 0,
    risk_reserve: 0,
    estimated_total_cost: 0,
    confidence: 0,
    needs_review: [
      ...needsReview,
      'Старый авторасчет использовал цену позиции тендера. Пересчитайте после выбора поставщика.',
    ],
  }
}
