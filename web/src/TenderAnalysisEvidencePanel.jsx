export function AnalysisEvidencePanel({ documents = [], analysis }) {
  const readyDocuments = documents.filter((document) => document.text_status === 'ok')
  const evidenceItems = (analysis?.checklist || []).filter((item) => item?.evidence).slice(0, 3)

  return (
    <aside className="analysis-evidence-panel" aria-label="Доказательства из документов">
      <h4>Доказательства</h4>
      {evidenceItems.length ? (
        evidenceItems.map((item, index) => (
          <article className="analysis-evidence-card" key={`${item.label}-${index}`}>
            <strong>{item.label}</strong>
            <p>{item.evidence}</p>
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
