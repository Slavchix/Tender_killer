import {
  formatMoney,
  supplierAvailabilityLabel,
  supplierStatusLabel,
} from './formatters'

export function SupplierOptionsList({ supplierOptions = [], saving = false, onSelect }) {
  if (!supplierOptions.length) {
    return <p className="muted-text">Кандидаты поставщиков пока не добавлены.</p>
  }

  return (
    <div className="supplier-options-list">
      {supplierOptions.map((option, index) => {
        const stockText = formatSupplierStock(option)
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
            <span>{formatMoney(option.unit_price)}</span>
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
