import { feedbackHistoryText } from './AnalysisFeedbackControls'

export function AnalysisFactBody({ detailed = false, view }) {
  return (
    <div className="analysis-fact-body">
      {!detailed && view.compactSentence ? (
        <p className="analysis-fact-line compact">
          <span>{view.compactSentence}</span>
        </p>
      ) : view.detailParts.length ? (
        <div className="analysis-fact-detail-grid">
          {view.detailParts.map(([label, value]) => (
            <section key={label}>
              <strong>{label}</strong>
              <p>{value}</p>
            </section>
          ))}
        </div>
      ) : null}
      {view.weakReason && (
        <p className="analysis-fact-warning">
          <span>Ограничение</span>
          {view.weakReason}
        </p>
      )}
      {view.feedbackComment && (
        <p className="analysis-feedback-note">
          <span>Комментарий оператора</span>
          {view.feedbackComment}
        </p>
      )}
      {view.feedbackHistory.length ? (
        <details className="analysis-feedback-history">
          <summary>История исправлений</summary>
          <ul>
            {view.feedbackHistory.slice(-3).map((entry, index) => (
              <li key={`${entry.changed_at || index}-${entry.to_state || index}`}>
                {feedbackHistoryText(entry)}
              </li>
            ))}
          </ul>
        </details>
      ) : null}
    </div>
  )
}
