export function AnalysisFactSourceContext({ item, view }) {
  return (
    <details className="analysis-source-context" aria-label="Источник" open>
      <summary>
        <span>Источник</span>
        <strong>{view.sourceLabel || view.sourceBinding.label}</strong>
      </summary>
      <div className="analysis-source-meta">
        <span className={`analysis-source-binding-${view.sourceBinding.level}`}>{view.sourceBinding.label}</span>
        <span className={`analysis-confidence-${view.confidenceLevel.level}`}>{view.confidenceLevel.label}</span>
        <span className={`analysis-evidence-quality-${view.evidenceQuality.level}`}>{view.evidenceQuality.label}</span>
        {view.sourceAuthority.hasContext && (
          <span className={`analysis-source-authority-${view.sourceAuthority.level}`}>{view.sourceAuthority.label}</span>
        )}
      </div>
      {view.sourceNotes.map((note) => (
        <p key={note}>{note}</p>
      ))}
      {view.sourceAuthority.hasContext && (
        <div className="analysis-source-authority">
          <span>{view.sourceAuthority.label}</span>
          <p>{view.sourceAuthority.detail}</p>
        </div>
      )}
      {item.source_context && <p>{item.source_context}</p>}
      {item.fragment && <p>{item.fragment}</p>}
    </details>
  )
}
