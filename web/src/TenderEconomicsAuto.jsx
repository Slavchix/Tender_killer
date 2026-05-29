import { AnalysisList } from './TenderAnalysisSections'
import {
  formatConfidence,
  formatCostDriver,
  formatMoney,
  taxModeLabel,
} from './formatters'
import { Info } from './TenderDetailsShared'

export function ProductAutoEconomicsPanel({ profile, onRun, onAccept, saving = false, accepting = false }) {
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
