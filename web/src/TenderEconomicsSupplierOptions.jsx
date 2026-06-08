import {
  formatMoney,
  supplierAvailabilityLabel,
  supplierStatusLabel,
} from './formatters'
import { priceComparisonForUnitPrice, tenderReferenceUnitPrice } from './TenderEconomicsPriceComparison'

export function SupplierOptionsList({ profile, supplierOptions = [], saving = false, onSelect }) {
  if (!supplierOptions.length) {
    return <p className="muted-text">Кандидаты поставщиков пока не добавлены.</p>
  }
  const tenderUnitPrice = tenderReferenceUnitPrice(profile)

  return (
    <div className="supplier-options-list">
      {supplierOptions.map((option, index) => {
        const stockText = formatSupplierStock(option)
        const optionUnitPrice = numberOrNull(option.unit_price)
        const priceComparison = priceComparisonForUnitPrice(optionUnitPrice, tenderUnitPrice)
        return (
          <div
            className={option.status === 'selected' ? 'supplier-option-row selected' : 'supplier-option-row'}
            key={`${option.url || option.name || 'supplier'}-${index}`}
          >
            <div>
              {option.url ? (
                <a href={option.url} target="_blank" rel="noreferrer">{option.name || option.url}</a>
              ) : (
                <strong>{option.name || 'Поставщик'}</strong>
              )}
              {option.note && <p>{option.note}</p>}
              {option.source_query && <p>Запрос: {option.source_query}</p>}
              {stockText && <p>{stockText}</p>}
            </div>
            <div className="supplier-option-price-summary">
              <span>{formatMoney(option.unit_price)}</span>
              {tenderUnitPrice != null && (
                <small className="supplier-option-reference-price">Тендер: {formatMoney(tenderUnitPrice)}</small>
              )}
              {priceComparison && (
                <small className={`supplier-option-price-delta ${priceComparison.tone}`}>
                  {priceComparison.label}
                </small>
              )}
            </div>
            <em>{supplierAvailabilityLabel(option.availability)} · {supplierStatusLabel(option.status)}</em>
            <button
              className="supplier-select-button"
              disabled={saving || !onSelect || option.status === 'selected'}
              onClick={() => ignoreSupplierOptionActionError(onSelect?.(index))}
              type="button"
            >
              {option.status === 'selected' ? 'В расчете' : 'В расчет'}
            </button>
          </div>
        )
      })}
    </div>
  )
}

function formatSupplierStock(option = {}) {
  const stock = numberOrNull(option.stock_quantity ?? option.raw_payload?.stock_quantity)
  const preorder = numberOrNull(option.preorder_quantity ?? option.raw_payload?.preorder_quantity)
  const parts = []
  if (stock != null) parts.push(`Склад: ${formatQuantity(stock)} шт.`)
  if (preorder != null) parts.push(`Под заказ: ${formatQuantity(preorder)} шт.`)
  return parts.join(' · ')
}

function formatQuantity(value) {
  return Number.isInteger(value) ? String(value) : String(value).replace('.', ',')
}

function numberOrNull(value) {
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}

function ignoreSupplierOptionActionError(result) {
  if (result?.catch) {
    result.catch(() => {})
  }
}
