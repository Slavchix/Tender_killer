import { AnalysisDocumentSummaryItem } from './AnalysisDocumentSummaryItem'
import { AnalysisFactCard } from './AnalysisFactCard'
import { isWeakAnalysisFact } from './analysisFactModel'
import { displayableAnalysisItems, isAnalysisFactItem } from './analysisSectionsModel'
import { AnalysisViewControls } from './AnalysisViewControls'

const ANALYSIS_COMPACT_LIMIT = 3

export function AnalysisOperatorSection({
  section,
  viewMode = 'compact',
  onViewModeChange,
  onEvidenceSelect,
  onFeedback,
  savingFeedbackId,
}) {
  const items = displayableAnalysisItems(section.items)
  const documentSummary = items.find((item) => item.type === 'document_summary')
  const analysisItems = items.filter(isAnalysisFactItem)
  const primaryItems = analysisItems.filter((item) => !isWeakAnalysisFact(item))
  const weakItems = analysisItems.filter(isWeakAnalysisFact)
  const compact = viewMode !== 'detailed'
  const visiblePrimaryItems = compact ? primaryItems.slice(0, ANALYSIS_COMPACT_LIMIT) : primaryItems
  const hiddenPrimaryItems = compact ? primaryItems.slice(ANALYSIS_COMPACT_LIMIT) : []

  return (
    <div className={`analysis-card operator-section ${section.tone || 'default'}`}>
      <div className="analysis-checklist-header">
        <span>{section.title}</span>
        <strong>{section.count ?? analysisItems.length}</strong>
      </div>
      {documentSummary && <AnalysisDocumentSummaryItem item={documentSummary} />}
      {analysisItems.length ? (
        <>
          <AnalysisViewControls
            totalCount={analysisItems.length}
            viewMode={viewMode}
            onViewModeChange={onViewModeChange}
          />
          <div className="analysis-checklist-list">
            {visiblePrimaryItems.map((item, index) => (
              <AnalysisFactCard
                detailed={!compact}
                item={item}
                key={item.id || `${item.label}-${index}`}
                onEvidenceSelect={onEvidenceSelect}
                onFeedback={onFeedback}
                savingFeedbackId={savingFeedbackId}
              />
            ))}
            {hiddenPrimaryItems.length ? (
              <details className="analysis-hidden-facts">
                <summary>Показать еще {hiddenPrimaryItems.length}</summary>
                <div className="analysis-checklist-list">
                  {hiddenPrimaryItems.map((item, index) => (
                    <AnalysisFactCard
                      detailed={!compact}
                      item={item}
                      key={item.id || `${item.label}-hidden-${index}`}
                      onEvidenceSelect={onEvidenceSelect}
                      onFeedback={onFeedback}
                      savingFeedbackId={savingFeedbackId}
                    />
                  ))}
                </div>
              </details>
            ) : null}
            {weakItems.length ? (
              <details className="analysis-weak-facts" open={!compact}>
                <summary>Слабые совпадения / ручная проверка ({weakItems.length})</summary>
                <div className="analysis-checklist-list">
                  {weakItems.map((item, index) => (
                    <AnalysisFactCard
                      detailed={!compact}
                      item={item}
                      key={item.id || `${item.label}-weak-${index}`}
                      onEvidenceSelect={onEvidenceSelect}
                      onFeedback={onFeedback}
                      savingFeedbackId={savingFeedbackId}
                      weak
                    />
                  ))}
                </div>
              </details>
            ) : null}
            {!analysisItems.length && <p className="muted-text">В анализе пока нет подтвержденных пунктов.</p>}
          </div>
        </>
      ) : (
        !documentSummary && <p className="muted-text">{section.empty}</p>
      )}
    </div>
  )
}
