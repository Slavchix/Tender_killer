import { buildDocumentEvidenceItems } from './TenderAnalysisEvidenceModel'

export function AnalysisEvidencePanel({ documents = [], analysis }) {
  const readyDocuments = documents.filter((document) => document.text_status === 'ok')
  const evidenceItems = buildDocumentEvidenceItems(analysis, documents).slice(0, 4)

  return (
    <aside className="analysis-evidence-panel" aria-label="Доказательства из документов">
      <h4>Доказательства</h4>
      {evidenceItems.length ? (
        evidenceItems.map((item) => (
          <article className="analysis-evidence-card analysis-evidence-item" key={item.id}>
            <strong>{item.label}</strong>
            <div className="analysis-evidence-meta">
              <span>{item.typeLabel}</span>
              <span>{item.importanceLabel}</span>
              <span>{item.documentName}</span>
            </div>
            <p>{item.fragment}</p>
            <em className="analysis-evidence-impact">{item.impact}</em>
          </article>
        ))
      ) : (
        <p className="muted-text">После анализа здесь будут короткие фрагменты из ТЗ и документов.</p>
      )}
      <div className="analysis-evidence-card">
        <strong>Источник</strong>
        <p>Текст извлечен у {readyDocuments.length} из {documents.length} документов.</p>
      </div>
    </aside>
  )
}
