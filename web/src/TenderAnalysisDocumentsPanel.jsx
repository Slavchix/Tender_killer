import {
  documentLabel,
  documentStatusCounts,
  documentStatusLabel,
  documentTextPreview,
} from './formatters'
import { SummaryMetric } from './TenderDetailsShared'

export function AnalysisDocumentsPanel({ documents = [], preparing, downloading, extracting, onDownload, onExtract }) {
  return (
    <details className="document-table-toggle analysis-documents-toggle">
      <summary>Показать документы ({documents.length})</summary>
      <p className="muted-text">Скачивание, извлечение текста и проверка файлов перед анализом ТЗ.</p>
      <DocumentStatusSummary
        documents={documents}
        preparing={preparing}
        downloading={downloading}
        extracting={extracting}
        onDownload={onDownload}
        onExtract={onExtract}
      />
      {documents.length ? (
        <div className="document-table compact">
          {documents.map((document) => (
            <div className="document-row" key={document.url}>
              <div>
                <a href={document.url} target="_blank" rel="noreferrer">
                  {document.name || documentLabel(document.url)}
                </a>
                <span>{document.document_type || 'тип не указан'}</span>
                {document.text_content && (
                  <details className="document-preview-toggle">
                    <summary>Показать извлеченный текст</summary>
                    <p className="document-preview">{documentTextPreview(document.text_content)}</p>
                  </details>
                )}
                {document.text_error && <p className="document-error">{document.text_error}</p>}
              </div>
              <div className="document-row-status">
                <strong className={`download-status ${document.local_path ? 'downloaded' : 'missing'}`}>
                  {document.local_path ? 'скачан' : 'не скачан'}
                </strong>
                <em className={`document-status ${document.text_status || 'pending'}`}>
                  {documentStatusLabel(document.text_status)}
                </em>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="muted-text">Документы пока не найдены в карточке.</p>
      )}
    </details>
  )
}

function DocumentStatusSummary({ documents, preparing, downloading, extracting, onDownload, onExtract }) {
  const counts = documentStatusCounts(documents)
  const actionDisabled = preparing || downloading || extracting

  return (
    <div className="document-status-summary" aria-label="Сводка документов">
      <div className="document-status-metrics tab-summary-grid">
        <SummaryMetric value={counts.total} label="всего" />
        <SummaryMetric value={counts.downloaded} label="скачано" />
        <SummaryMetric value={counts.ok} label="текст" />
        <SummaryMetric value={counts.attention} label="проверить" />
      </div>
      <div className="document-status-actions">
        <button className="secondary-button compact" disabled={actionDisabled} onClick={onDownload} type="button">
          {downloading ? 'Качаю...' : 'Скачать документы'}
        </button>
        <button className="secondary-button compact" disabled={actionDisabled || !counts.downloaded} onClick={onExtract} type="button">
          {extracting ? 'Читаю...' : 'Извлечь текст'}
        </button>
      </div>
    </div>
  )
}
