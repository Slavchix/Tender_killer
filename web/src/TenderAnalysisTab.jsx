import {
  normalizeListItems,
  analysisCategoryLabel,
  analysisSeverityLabel,
  analysisStatusLabel,
  formatConfidence,
} from './formatters'
import { SummaryMetric } from './TenderDetailsShared'

export function TenderAnalysisTab({ analysis, analyzing, onAnalyze }) {
  const requirementsCount = analysis?.requirements?.length || 0
  const risksCount = (analysis?.risks?.length || 0) + (analysis?.red_flags?.length || 0)
  const checklistCount = analysis?.checklist?.length || 0

  return (
    <section className="detail-section active analysis-section">
      <div className="section-heading-row">
        <h3>Выжимка ТЗ</h3>
        <button className="secondary-button compact" disabled={analyzing} onClick={onAnalyze} type="button">
          {analyzing ? 'Анализ...' : 'Проанализировать'}
        </button>
      </div>
      <div className="analysis-tab-summary tab-summary-grid" aria-label="Сводка анализа ТЗ">
        <SummaryMetric value={analysis ? analysisStatusLabel(analysis.status) : 'нет анализа'} label="статус" />
        <SummaryMetric value={analysis ? formatConfidence(analysis.confidence) : 'нет'} label="уверенность" />
        <SummaryMetric value={requirementsCount} label="требований" />
        <SummaryMetric value={risksCount} label="рисков" />
        <SummaryMetric value={checklistCount} label="пунктов" />
      </div>
      {analysis ? (
        <div className="analysis-card">
          <p>{analysis.summary}</p>
          <AnalysisChecklist items={analysis.checklist} />
          <AnalysisList title="Требования" items={analysis.requirements} empty="Явные требования пока не найдены" />
          <AnalysisList title="Риски" items={analysis.risks} empty="Явные риски пока не найдены" />
          <AnalysisList title="Красные флаги" items={analysis.red_flags} empty="Критичные признаки пока не найдены" danger />
        </div>
      ) : (
        <p className="muted-text">Сначала извлеки текст документов, затем запусти анализ ТЗ.</p>
      )}
    </section>
  )
}

export function AnalysisList({ title, items = [], empty, danger = false }) {
  const normalizedItems = normalizeListItems(items)
  return (
    <div className={danger ? 'analysis-list danger' : 'analysis-list'}>
      <span>{title}</span>
      {normalizedItems.length ? (
        <ul>
          {normalizedItems.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>{empty}</p>
      )}
    </div>
  )
}

function AnalysisChecklist({ items = [] }) {
  const normalizedItems = (Array.isArray(items) ? items : [])
    .filter((item) => item && typeof item === 'object' && item.label)

  if (!normalizedItems.length) return null

  return (
    <div className="analysis-checklist">
      <div className="analysis-checklist-header">
        <span>Проверочный список</span>
        <strong>{normalizedItems.length}</strong>
      </div>
      <div className="analysis-checklist-list">
        {normalizedItems.map((item, index) => (
          <article className={`analysis-checklist-row severity-${item.severity || 'medium'}`} key={`${item.label}-${index}`}>
            <div className="analysis-checklist-main">
              <strong>{item.label}</strong>
              <div className="analysis-checklist-tags">
                <span>{analysisCategoryLabel(item.category)}</span>
                <span>{analysisSeverityLabel(item.severity)}</span>
              </div>
            </div>
            {item.evidence && <p>{item.evidence}</p>}
          </article>
        ))}
      </div>
    </div>
  )
}
