import { ExternalLink, RefreshCcw } from 'lucide-react'

export function TenderDetailActions({
  tender,
  refreshingDetails,
  onRefreshDetails,
}) {
  return (
    <div className="detail-actions" aria-label="Действия с закупкой">
      <div className="details-action-group primary-actions">
        <a className="detail-action primary" href={tender.url} target="_blank" rel="noreferrer">
          <ExternalLink size={15} /> Источник
        </a>
        <button disabled={refreshingDetails} onClick={() => onRefreshDetails()} type="button">
          <RefreshCcw size={15} /> {refreshingDetails ? 'Обновляю' : 'Обновить'}
        </button>
      </div>
    </div>
  )
}
