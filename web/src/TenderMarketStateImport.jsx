import { Upload } from 'lucide-react'

export function TenderMarketStateImport({
  value,
  importing,
  onChange,
  onImport,
}) {
  return (
    <details className="market-import-panel">
      <summary>
        <Upload size={15} /> Импорт ставки
      </summary>
      <form className="market-import-form" onSubmit={onImport}>
        <textarea
          className="market-import-textarea"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          spellCheck="false"
          placeholder='{"lastBetCost":48217.7,"nextCost":47975.4,"uniqueSupplierCount":1}'
        />
        <button disabled={importing || !value.trim()} type="submit">
          <Upload size={15} /> {importing ? 'Импортирую' : 'Импорт'}
        </button>
      </form>
    </details>
  )
}
