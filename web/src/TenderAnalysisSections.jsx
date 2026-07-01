import { AnalysisFactCard } from './AnalysisFactCard'
import { isWeakAnalysisFact } from './analysisFactModel'
import { AnalysisViewControls } from './AnalysisViewControls'
import {
  analysisSectionItems,
  displayableAnalysisItems,
  isAnalysisFactItem,
  visibleMajorAnalysisSections,
} from './analysisSectionsModel'

const ANALYSIS_COMPACT_LIMIT = 3
export { analysisSectionItems }
export { AnalysisList, AnalysisChecklist } from './AnalysisSharedLists'

export function AnalysisSectionRail({ sections, selectedSection, onSelectSection }) {
  return (
    <aside className="analysis-section-rail" aria-label="Разделы анализа">
      {sections.map((section) => (
        <AnalysisSectionRailItem
          active={selectedSection === section.id}
          key={section.id}
          onClick={() => onSelectSection(section.id)}
          title={section.title}
          value={section.value}
        />
      ))}
    </aside>
  )
}

export function AnalysisSectionBody({
  sectionId,
  analysis,
  documents = [],
  viewMode = 'compact',
  onViewModeChange,
  onEvidenceSelect,
  onFeedback,
  savingFeedbackId,
}) {
  const sections = visibleMajorAnalysisSections(analysis, documents)
  const section = sections.find((item) => item.id === sectionId) || sections[0]
  if (!section) {
    return (
      <div className="analysis-card operator-section default">
        <p className="muted-text">В анализе пока нет условий для отображения.</p>
      </div>
    )
  }
  return (
    <AnalysisOperatorSection
      section={section}
      viewMode={viewMode}
      onViewModeChange={onViewModeChange}
      onEvidenceSelect={onEvidenceSelect}
      onFeedback={onFeedback}
      savingFeedbackId={savingFeedbackId}
    />
  )
}

function AnalysisOperatorSection({
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
      {documentSummary && <DocumentSummaryItem item={documentSummary} />}
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

function DocumentSummaryItem({ item }) {
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

function AnalysisSectionRailItem({ title, value, active = false, onClick }) {
  return (
    <button
      aria-pressed={active}
      className={active ? 'analysis-section-item active' : 'analysis-section-item'}
      onClick={onClick}
      type="button"
    >
      <strong>{title}</strong>
      <span>{value}</span>
    </button>
  )
}
