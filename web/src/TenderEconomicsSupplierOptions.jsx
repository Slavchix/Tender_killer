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
      {supplierOptions.map((option, index) => (
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
      ))}
    </div>
  )
}

function ignoreSupplierOptionActionError(result) {
  if (result?.catch) {
    result.catch(() => {})
  }
}
