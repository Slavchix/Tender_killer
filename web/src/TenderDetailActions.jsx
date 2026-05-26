import { Bell, ExternalLink, FileText, RefreshCcw } from 'lucide-react'

export function TenderDetailActions({
  tender,
  refreshingDetails,
  downloading,
  extracting,
  analyzing,
  sending,
  onRefreshDetails,
  onDownloadDocuments,
  onExtractDocumentText,
  onAnalyzeTender,
  onSendToTelegram,
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
      <div className="details-action-group secondary-actions">
        <button disabled={downloading} onClick={onDownloadDocuments} type="button">
          <FileText size={15} /> {downloading ? 'Качаю' : 'Документы'}
        </button>
        <button disabled={extracting} onClick={onExtractDocumentText} type="button">
          {extracting ? 'Читаю' : 'Текст'}
        </button>
        <button disabled={analyzing} onClick={onAnalyzeTender} type="button">
          {analyzing ? 'Анализ' : 'Анализ'}
        </button>
        <a
          className="detail-action"
          href={`/api/tenders/${encodeURIComponent(tender.source)}/${encodeURIComponent(tender.external_id)}/report.docx`}
        >
          Word
        </a>
        <button disabled={sending} onClick={onSendToTelegram} type="button">
          <Bell size={15} /> {sending ? 'Отправка' : 'TG'}
        </button>
      </div>
    </div>
  )
}
