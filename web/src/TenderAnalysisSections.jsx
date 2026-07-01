import { AnalysisOperatorSection } from './AnalysisOperatorSection'
import {
  analysisSectionItems,
  visibleMajorAnalysisSections,
} from './analysisSectionsModel'

export { analysisSectionItems }
export { AnalysisSectionRail } from './AnalysisSectionRail'
export { AnalysisList, AnalysisChecklist } from './AnalysisSharedLists'

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
