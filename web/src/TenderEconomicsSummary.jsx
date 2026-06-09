import {
  economicsStatusLabel,
  formatMoney,
  formatPercent,
  formatQuantity,
  marketStateCaption,
  marketStateValue,
  nmcPriceValue,
  participantBidValue,
} from './formatters'
import { Info } from './TenderDetailsShared'
import { BidScenarioStrip, ParticipationDecisionCard } from './TenderEconomicsDecisionScenarios'
import { tenderReferenceTotalPrice, tenderReferenceUnitPrice } from './TenderEconomicsPriceComparison'

export function EconomicsSummary({ economics, tender, profiles = [] }) {
  if (!economics) {
    return (
      <p className="muted-text">
        {tender?.price ? 'НМЦК подтянута из карточки закупки. Добавь себестоимость по позициям, чтобы посчитать маржу.' : 'Черновик экономики пока не рассчитан.'}
      </p>
    )
  }

  const missingInputs = economics.missing_cost_inputs || []
  const riskTypes = economics.risk_types || []
  const items = economics.items || []
  const itemProfiles = profilesByEconomicsItem(profiles)
  const bidScenarios = economics.bid_scenarios || []
  const participationDecision = economics.participation_decision || null
  const analysisCostDrivers = economics.analysis_cost_drivers || []
  const analysisReserveHint = economics.analysis_reserve_hint || {}
  const marketState = economics.market_state || tender?.market_state
  const revenueLabel = economics.revenue_kind === 'current_offer' ? 'Цена участника' : 'НМЦК'

  return (
    <details className="economics-card economics-analysis-drawer">
      <summary>
        <span>Анализ ТЗ и расчетная сводка</span>
        <em>
          {analysisCostDrivers.length} факторов · {riskTypes.length} рисков · {missingInputs.length} цен добавить
        </em>
      </summary>
      <div className="economics-analysis-body">
        <div className="analysis-status-row">
          <strong>{economicsStatusLabel(economics.status)}</strong>
          <span>Маржа: {formatPercent(economics.margin_percent)}</span>
        </div>
        {economics.recommendation && <p>{economics.recommendation}</p>}
        <ParticipationDecisionCard decision={participationDecision} />
        <BidScenarioStrip scenarios={bidScenarios} />
        <div className="economics-grid">
          <Info label="НМЦК" value={nmcPriceValue(tender, marketState)} />
          <Info label="Ставка участника" value={participantBidValue(marketState)} />
          <Info label={revenueLabel === 'Цена участника' ? 'Расчет от ставки' : 'Расчет от НМЦК'} value={formatMoney(economics.revenue)} />
          <Info label="Рынок" value={`${marketStateValue(marketState)} · ${marketStateCaption(economics?.market_state || tender?.market_state)}`} />
          <Info label="Себестоимость" value={formatMoney(economics.supplier_cost)} />
          <Info label="Резерв риска" value={`${formatMoney(economics.risk_reserve)} · ${formatPercent(economics.risk_reserve_rate_percent)}`} />
          <Info label="Итого затраты" value={formatMoney(economics.estimated_total_cost)} />
          <Info label="Безубыток" value={formatMoney(economics.break_even_price)} />
          <Info label="Минимальная ставка" value={formatMoney(economics.minimum_margin_price)} />
          <Info label="Интересная ставка" value={formatMoney(economics.interesting_price)} />
          <Info label="Маржа" value={`${formatMoney(economics.gross_margin)} · ${formatPercent(economics.margin_percent)}`} />
          <Info label="Риски исполнения" value={riskTypes.length ? riskTypes.join(', ') : 'нет'} />
        </div>
        {missingInputs.length > 0 && (
          <div className="economics-warning">
            <strong>Нужны цены</strong>
            <p>{missingInputs.join(', ')}</p>
          </div>
        )}
        {analysisCostDrivers.length > 0 && (
          <div className="analysis-cost-drivers">
            <div className="analysis-status-row">
              <strong>Факторы из ТЗ</strong>
              <span>подсказка резерва: {formatPercent(analysisReserveHint.rate_percent)}</span>
            </div>
            <div className="analysis-cost-driver-list">
              {analysisCostDrivers.slice(0, 5).map((driver, index) => (
                <div className="analysis-cost-driver" key={`${driver.label}-${index}`}>
                  <strong>{driver.label}</strong>
                  <span>{driver.category || 'general'} · {driver.severity || 'medium'}</span>
                  {(driver.impact || driver.source) && <em>{driver.impact || driver.source}</em>}
                </div>
              ))}
            </div>
          </div>
        )}
        {items.length > 0 && (
          <div className="economics-items">
            {items.map((item, index) => {
              const profile = itemProfiles.get(Number(item?.position_index)) || itemProfiles.get(index + 1)
              const unitCost = positiveValue(item?.unit_cost, tenderReferenceUnitPrice(profile))
              const totalCost = positiveValue(item?.total_cost, tenderReferenceTotalPrice(profile))
              const pricePassport = item.price_passport || null
              const unitNormalization = item.unit_normalization || null

              return (
                <div className="economics-item" key={`${item.product_name}-${index}`}>
                  <strong>{item.product_name}</strong>
                  <span>{formatQuantity(item.quantity, item.unit)}</span>
                  <span>{unitCost != null ? `${formatMoney(unitCost)} за ед.` : 'цена не указана'}</span>
                  <span>{formatMoney(totalCost)}</span>
                  <div className="economics-item-passport">
                    <span>{formatPricePassport(pricePassport)}</span>
                    <span>{formatUnitNormalization(unitNormalization)}</span>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </details>
  )
}

function profilesByEconomicsItem(profiles = []) {
  const result = new Map()
  ;(Array.isArray(profiles) ? profiles : []).forEach((profile, index) => {
    const positionIndex = Number(profile?.position_index)
    if (Number.isFinite(positionIndex) && positionIndex > 0) {
      result.set(positionIndex, profile)
    }
    if (!result.has(index + 1)) {
      result.set(index + 1, profile)
    }
  })
  return result
}

function positiveValue(primary, fallback) {
  const number = Number(primary)
  return Number.isFinite(number) && number > 0 ? primary : fallback
}

function formatPricePassport(passport) {
  if (!passport) return 'Источник: не указан'
  const source = passport.source_label || passport.provider || passport.source_type || 'не указан'
  const status = pricePassportStatusLabel(passport.status)
  const inclusion = passport.included_in_calculation ? 'в расчете' : 'не в расчете'
  return `Источник: ${source} · ${status} · ${inclusion}`
}

function pricePassportStatusLabel(status) {
  return {
    confirmed: 'подтверждена',
    manual: 'ручная',
    review: 'на проверке',
    missing: 'нет цены',
  }[status] || 'на проверке'
}

function formatUnitNormalization(normalization) {
  if (!normalization) return 'Единицы: не проверены'
  const tenderUnit = normalization.tender_unit || 'ед.'
  const supplierUnit = normalization.supplier_unit || tenderUnit
  const coefficient = Number(normalization.coefficient)
  const coefficientText = Number.isFinite(coefficient) && coefficient !== 1 ? ` · x${formatCompactNumber(coefficient)}` : ''
  const normalizedPrice = Number(normalization.normalized_unit_price)
  const priceText = Number.isFinite(normalizedPrice) ? ` · ${formatMoney(normalizedPrice)} за ${tenderUnit}` : ''
  return `Единицы: ${supplierUnit} -> ${tenderUnit}${coefficientText}${priceText}`
}

function formatCompactNumber(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return String(value || '1')
  return Number.isInteger(number) ? String(number) : number.toFixed(2).replace(/\.?0+$/, '')
}
