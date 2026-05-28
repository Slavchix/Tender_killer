import { workflowLabels } from './constants'
import {
  economicsStatusLabel,
  formatDate,
  formatMoney,
  formatPercent,
  formatPriceChangeDirection,
  formatSignedMoney,
  formatSignedPercent,
  nmcPriceValue,
  participantBidValue,
  tenderDecisionNextStep,
} from './formatters'
import { Info } from './TenderDetailsShared'

export function TenderDecisionSummary({ tender, economics }) {
  const marginValue = Number(economics?.margin_percent)
  const marginText = Number.isFinite(marginValue) ? formatPercent(marginValue) : 'нужны цены'
  const economicsText = economics ? `${economicsStatusLabel(economics.status)} · ${marginText}` : 'экономика не рассчитана'
  const nextStep = tenderDecisionNextStep(tender, economics)

  return (
    <section className="decision-summary" aria-label="Краткое решение по закупке">
      <div className="decision-summary-grid">
        <Info label="НМЦК" value={nmcPriceValue(tender, economics?.market_state || tender.market_state)} />
        <Info label="Ставка участника" value={participantBidValue(economics?.market_state || tender.market_state)} />
        <Info label="Срок" value={formatDate(tender.deadline_at)} />
        <Info label="Заказчик" value={tender.customer || 'не указан'} />
        <Info label="Экономика" value={economicsText} />
        <Info label="Статус" value={workflowLabels[tender.workflow_status] || 'Новая'} />
        <Info label="Следующий шаг" value={nextStep} />
      </div>
    </section>
  )
}

export function PriceChangeBanner({ change }) {
  if (!change) return null
  const previousPrice = Number(change.previous_price)
  const currentPrice = Number(change.current_price)
  if (!Number.isFinite(previousPrice) || !Number.isFinite(currentPrice)) return null

  const delta = Number(change.delta)
  const deltaPercent = Number(change.delta_percent)
  const kindLabel = change.price_kind === 'current_offer' ? 'Цена участника' : 'НМЦК'
  const percentText = Number.isFinite(deltaPercent) ? ` · ${formatSignedPercent(deltaPercent)}` : ''

  return (
    <section className={`price-change-banner ${change.direction || 'changed'}`} aria-label="Изменение цены">
      <div className="price-change-copy">
        <span>{kindLabel}</span>
        <strong>{formatPriceChangeDirection(change)}</strong>
      </div>
      <div className="price-change-values">
        <span>было {formatMoney(previousPrice)}</span>
        <span>стало {formatMoney(currentPrice)}</span>
        {Number.isFinite(delta) && (
          <strong className="price-change-delta">
            {formatSignedMoney(delta)}{percentText}
          </strong>
        )}
      </div>
    </section>
  )
}
