import { AnalysisFeedbackControls, feedbackHistoryText } from './AnalysisFeedbackControls'
import {
  analysisConfidenceLevel,
  analysisEvidenceQuality,
  analysisItemTags,
  analysisSourceAuthority,
  analysisSourceBinding,
  compactAnalysisFactSentence,
} from './analysisFactModel'
import { cleanAnalysisText, uniqueAnalysisTexts } from './analysisTextUtils'

export function AnalysisFactCard({ item, detailed = false, onEvidenceSelect, onFeedback, savingFeedbackId, weak = false }) {
  const sourceLabel = item.source_label || item.source
  const sourceBinding = analysisSourceBinding(item)
  const confidenceLevel = analysisConfidenceLevel(item)
  const evidenceQuality = analysisEvidenceQuality(item)
  const sourceAuthority = analysisSourceAuthority(item)
  const interpretation = item.interpretation && typeof item.interpretation === 'object' ? item.interpretation : {}
  const summary = cleanAnalysisText(item.operator_summary) || cleanAnalysisText(item.description)
  const operatorCheck = cleanAnalysisText(item.operator_check) || cleanAnalysisText(item.operator_action)
  const impact = cleanAnalysisText(item.impact)
  const weakReason = cleanAnalysisText(item.weak_reason)
  const compactSentence = compactAnalysisFactSentence(item, interpretation)
  const sourceNotes = uniqueAnalysisTexts([sourceBinding.detail, confidenceLevel.detail, evidenceQuality.detail])
  const detailParts = [
    cleanAnalysisText(interpretation.found) ? ['Что найдено', cleanAnalysisText(interpretation.found)] : null,
    cleanAnalysisText(interpretation.meaning) || summary ? ['Что означает', cleanAnalysisText(interpretation.meaning) || summary] : null,
    cleanAnalysisText(interpretation.impact) || impact ? ['Влияние', cleanAnalysisText(interpretation.impact) || impact] : null,
    cleanAnalysisText(interpretation.action) || operatorCheck ? ['Что сделать', cleanAnalysisText(interpretation.action) || operatorCheck] : null,
  ].filter(Boolean)
  const sourceDetail = Boolean(
    sourceLabel ||
    sourceBinding.detail ||
    confidenceLevel.detail ||
    evidenceQuality.detail ||
    sourceAuthority.hasContext ||
    item.source_context ||
    item.fragment
  )
  return (
    <article className={`analysis-checklist-row severity-${item.severity || 'medium'} feedback-${item.feedback_state || 'none'}${weak ? ' weak' : ''}`}>
      <div className="analysis-checklist-main">
        <strong>{item.label}</strong>
        <div className="analysis-checklist-tags">
          {analysisItemTags(item).map((tag) => (
            <span key={tag}>{tag}</span>
          ))}
        </div>
      </div>
      <AnalysisFeedbackControls
        disabled={!item.id || !onFeedback || savingFeedbackId === item.id}
        item={item}
        onFeedback={onFeedback}
      />
      {sourceDetail && onEvidenceSelect ? (
        <button className="analysis-evidence-link" onClick={() => onEvidenceSelect(item)} type="button">
          Источник
        </button>
      ) : null}
      <div className="analysis-fact-body">
        {!detailed && compactSentence ? (
          <p className="analysis-fact-line compact">
            <span>{compactSentence}</span>
          </p>
        ) : detailParts.length ? (
          <div className="analysis-fact-detail-grid">
            {detailParts.map(([label, value]) => (
              <section key={label}>
                <strong>{label}</strong>
                <p>{value}</p>
              </section>
            ))}
          </div>
        ) : null}
        {weakReason && (
          <p className="analysis-fact-warning">
            <span>Ограничение</span>
            {weakReason}
          </p>
        )}
        {item.feedback_comment && (
          <p className="analysis-feedback-note">
            <span>Комментарий оператора</span>
            {item.feedback_comment}
          </p>
        )}
        {Array.isArray(item.feedback_history) && item.feedback_history.length ? (
          <details className="analysis-feedback-history">
            <summary>История исправлений</summary>
            <ul>
              {item.feedback_history.slice(-3).map((entry, index) => (
                <li key={`${entry.changed_at || index}-${entry.to_state || index}`}>
                  {feedbackHistoryText(entry)}
                </li>
              ))}
            </ul>
          </details>
        ) : null}
      </div>
      {detailed && sourceDetail && (
        <details className="analysis-source-context" aria-label="Источник" open>
          <summary>
            <span>Источник</span>
            <strong>{sourceLabel || sourceBinding.label}</strong>
          </summary>
          <div className="analysis-source-meta">
            <span className={`analysis-source-binding-${sourceBinding.level}`}>{sourceBinding.label}</span>
            <span className={`analysis-confidence-${confidenceLevel.level}`}>{confidenceLevel.label}</span>
            <span className={`analysis-evidence-quality-${evidenceQuality.level}`}>{evidenceQuality.label}</span>
            {sourceAuthority.hasContext && (
              <span className={`analysis-source-authority-${sourceAuthority.level}`}>{sourceAuthority.label}</span>
            )}
          </div>
          {sourceNotes.map((note) => (
            <p key={note}>{note}</p>
          ))}
          {sourceAuthority.hasContext && (
            <div className="analysis-source-authority">
              <span>{sourceAuthority.label}</span>
              <p>{sourceAuthority.detail}</p>
            </div>
          )}
          {item.source_context && <p>{item.source_context}</p>}
          {item.fragment && <p>{item.fragment}</p>}
        </details>
      )}
    </article>
  )
}
