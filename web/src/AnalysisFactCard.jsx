import { AnalysisFeedbackControls } from './AnalysisFeedbackControls'
import { AnalysisFactBody } from './AnalysisFactBody'
import { AnalysisFactSourceContext } from './AnalysisFactSourceContext'
import { buildAnalysisFactView } from './analysisFactViewModel'

export function AnalysisFactCard({ item, detailed = false, onEvidenceSelect, onFeedback, savingFeedbackId, weak = false }) {
  const view = buildAnalysisFactView(item)

  return (
    <article className={`analysis-checklist-row severity-${item.severity || 'medium'} feedback-${item.feedback_state || 'none'}${weak ? ' weak' : ''}`}>
      <div className="analysis-checklist-main">
        <strong>{item.label}</strong>
        <div className="analysis-checklist-tags">
          {view.tags.map((tag) => (
            <span key={tag}>{tag}</span>
          ))}
        </div>
      </div>
      <AnalysisFeedbackControls
        disabled={!item.id || !onFeedback || savingFeedbackId === item.id}
        item={item}
        onFeedback={onFeedback}
      />
      {view.sourceDetail && onEvidenceSelect ? (
        <button className="analysis-evidence-link" onClick={() => onEvidenceSelect(item)} type="button">
          Источник
        </button>
      ) : null}
      <AnalysisFactBody detailed={detailed} view={view} />
      {detailed && view.sourceDetail && <AnalysisFactSourceContext item={item} view={view} />}
    </article>
  )
}
