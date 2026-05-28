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
      <div className="market-import-help" id="market-import-help">
        <span>Что вставить: JSON-ответ запроса GetBetUpdate с портала zakupki.mos.ru.</span>
        <span>Где взять: открой закупку на портале, нажми F12 &gt; Network &gt; Fetch/XHR, выбери GetBetUpdate?auctionId=... и скопируй Response.</span>
        <span>Важные поля: lastBetCost, nextCost, uniqueSupplierCount. Можно вставить весь ответ целиком.</span>
      </div>
      <form
        className="market-import-form"
        aria-busy={importing}
        aria-describedby="market-import-help"
        onSubmit={onImport}
      >
        <textarea
          className="market-import-textarea"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          spellCheck="false"
          placeholder='{"lastBetCost":48217.7,"nextCost":47975.4,"uniqueSupplierCount":1}'
        />
        <button disabled={!value.trim()} type="submit">
          <Upload size={15} /> {importing ? 'Повторить' : 'Импорт'}
        </button>
      </form>
    </details>
  )
}
