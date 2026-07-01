export function AnalysisDocumentSummaryItem({ item }) {
  const documents = Array.isArray(item.documents) ? item.documents : []
  return (
    <details className="analysis-document-summary">
      <summary>
        <strong>{item.label}</strong>
        <span>{item.description}</span>
      </summary>
      {documents.length ? (
        <ul>
          {documents.map((document) => (
            <li key={document}>{document}</li>
          ))}
        </ul>
      ) : null}
    </details>
  )
}
