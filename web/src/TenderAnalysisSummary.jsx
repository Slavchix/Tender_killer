import {
  analysisStatusLabel,
  documentStatusCounts,
  formatConfidence,
} from './formatters'
import { SummaryMetric } from './TenderDetailsShared'

export function AnalysisSummary({ analysis, documents = [] }) {
  const operatorView = analysis?.operator_view
  const operatorMetrics = operatorView?.metrics
  const requirementsCount = operatorMetrics?.requirements ?? analysis?.requirements?.length ?? 0
  const risksCount = operatorMetrics?.risks ?? ((analysis?.risks?.length || 0) + (analysis?.red_flags?.length || 0))
  const checklistCount = operatorMetrics?.checklist ?? analysis?.checklist?.length ?? 0
  const documentState = operatorView?.document_state
  const documentCounts = documentStatusCounts(documents)
  const readyDocuments = documentState?.text_ready ?? operatorMetrics?.documents_ready ?? documentCounts.ok
  const totalDocuments = documentState?.total ?? operatorMetrics?.documents_total ?? documents.length

  return (
    <div className="analysis-tab-summary tab-summary-grid" aria-label="Сводка анализа ТЗ">
      <SummaryMetric value={analysis ? analysisStatusLabel(analysis.status) : 'нет анализа'} label="статус" />
      <SummaryMetric value={analysis ? formatConfidence(analysis.confidence) : 'нет'} label="уверенность" />
      <SummaryMetric value={requirementsCount} label="требований" />
      <SummaryMetric value={risksCount} label="рисков" />
      <SummaryMetric value={checklistCount} label="пунктов" />
      <SummaryMetric value={`${readyDocuments}/${totalDocuments}`} label="документов" />
    </div>
  )
}
