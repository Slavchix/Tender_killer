import {
  analysisStatusLabel,
  documentStatusCounts,
  formatConfidence,
} from './formatters'
import { SummaryMetric } from './TenderDetailsShared'

export function AnalysisSummary({ analysis, documents = [] }) {
  const requirementsCount = analysis?.requirements?.length || 0
  const risksCount = (analysis?.risks?.length || 0) + (analysis?.red_flags?.length || 0)
  const checklistCount = analysis?.checklist?.length || 0
  const documentCounts = documentStatusCounts(documents)

  return (
    <div className="analysis-tab-summary tab-summary-grid" aria-label="Сводка анализа ТЗ">
      <SummaryMetric value={analysis ? analysisStatusLabel(analysis.status) : 'нет анализа'} label="статус" />
      <SummaryMetric value={analysis ? formatConfidence(analysis.confidence) : 'нет'} label="уверенность" />
      <SummaryMetric value={requirementsCount} label="требований" />
      <SummaryMetric value={risksCount} label="рисков" />
      <SummaryMetric value={checklistCount} label="пунктов" />
      <SummaryMetric value={`${documentCounts.ok}/${documents.length}`} label="документов" />
    </div>
  )
}
