import { useState } from 'react'
import {
  normalizeListItems,
  analysisCategoryLabel,
  analysisSeverityLabel,
  analysisStatusLabel,
  documentStatusCounts,
  documentStatusLabel,
  formatConfidence,
} from './formatters'
import { SummaryMetric } from './TenderDetailsShared'

export function TenderAnalysisTab({ analysis, analyzing, onAnalyze, reportHref, documents = [] }) {
  const [selectedAnalysisSection, setSelectedAnalysisSection] = useState('checklist')
  const requirementsCount = analysis?.requirements?.length || 0
  const risksCount = (analysis?.risks?.length || 0) + (analysis?.red_flags?.length || 0)
  const checklistCount = analysis?.checklist?.length || 0
  const documentCounts = documentStatusCounts(documents)
  const analysisSections = [
    { id: 'risks', title: 'Риски', value: risksCount },
    { id: 'requirements', title: 'Требования', value: requirementsCount },
    { id: 'documents', title: 'Документы', value: `${documentCounts.ok}/${documents.length}` },
    { id: 'checklist', title: 'Чеклист', value: checklistCount },
  ]

  return (
    <section className="detail-section active analysis-section">
      <div className="section-heading-row analysis-action-row">
        <div>
          <h3>Анализ ТЗ</h3>
          <p className="muted-text">Риски, требования и доказательства из документов.</p>
        </div>
        <div className="analysis-actions">
          <button className="secondary-button compact" disabled={analyzing} onClick={onAnalyze} type="button">
            {analyzing ? 'Анализ...' : 'Проанализировать'}
          </button>
          <a className="secondary-link-button compact" href={reportHref}>
            Скачать Word
          </a>
        </div>
      </div>
      <div className="analysis-tab-summary tab-summary-grid" aria-label="Сводка анализа ТЗ">
        <SummaryMetric value={analysis ? analysisStatusLabel(analysis.status) : 'нет анализа'} label="статус" />
        <SummaryMetric value={analysis ? formatConfidence(analysis.confidence) : 'нет'} label="уверенность" />
        <SummaryMetric value={requirementsCount} label="требований" />
        <SummaryMetric value={risksCount} label="рисков" />
        <SummaryMetric value={checklistCount} label="пунктов" />
        <SummaryMetric value={`${documentCounts.ok}/${documents.length}`} label="документов" />
      </div>

      <div className="analysis-workspace">
        <aside className="analysis-section-rail" aria-label="Разделы анализа">
          {analysisSections.map((section) => (
            <AnalysisSectionRailItem
              active={selectedAnalysisSection === section.id}
              key={section.id}
              onClick={() => setSelectedAnalysisSection(section.id)}
              title={section.title}
              value={section.value}
            />
          ))}
        </aside>

        <div className="analysis-main-panel">
          {analysis ? (
            renderAnalysisSection(selectedAnalysisSection, analysis, documents, documentCounts)
          ) : (
            <p className="muted-text">Сначала извлеки текст документов, затем запусти анализ ТЗ.</p>
          )}
        </div>

        <AnalysisEvidencePanel documents={documents} analysis={analysis} />
      </div>
    </section>
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

function renderAnalysisSection(sectionId, analysis, documents, documentCounts) {
  if (sectionId === 'risks') {
    return (
      <div className="analysis-card">
        <p>{analysis.summary}</p>
        <AnalysisList title="Риски" items={analysis.risks} empty="Явные риски пока не найдены" />
        <AnalysisList title="Красные флаги" items={analysis.red_flags} empty="Критичные признаки пока не найдены" danger />
      </div>
    )
  }

  if (sectionId === 'requirements') {
    return (
      <div className="analysis-card">
        <p>{analysis.summary}</p>
        <AnalysisList title="Требования" items={analysis.requirements} empty="Явные требования пока не найдены" />
      </div>
    )
  }

  if (sectionId === 'documents') {
    return (
      <div className="analysis-card">
        <p>Текст извлечен у {documentCounts.ok} из {documents.length} документов.</p>
        <div className="analysis-document-list">
          {documents.length ? documents.map((document, index) => (
            <article className="analysis-document-row" key={`${document.name || document.url}-${index}`}>
              <strong>{document.name || document.url || `Документ ${index + 1}`}</strong>
              <span>{documentStatusLabel(document.text_status)}</span>
              <p>{document.text_status === 'ok' ? 'Текст готов для анализа.' : 'Документ требует внимания или не содержит машинно-читаемый текст.'}</p>
            </article>
          )) : (
            <p className="muted-text">Документы по закупке пока не загружены.</p>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="analysis-card">
      <p>{analysis.summary}</p>
      <AnalysisChecklist items={analysis.checklist} />
    </div>
  )
}

function AnalysisEvidencePanel({ documents = [], analysis }) {
  const readyDocuments = documents.filter((document) => document.text_status === 'ok')
  const evidenceItems = (analysis?.checklist || []).filter((item) => item?.evidence).slice(0, 3)

  return (
    <aside className="analysis-evidence-panel" aria-label="Доказательства из документов">
      <h4>Доказательства</h4>
      {evidenceItems.length ? (
        evidenceItems.map((item, index) => (
          <article className="analysis-evidence-card" key={`${item.label}-${index}`}>
            <strong>{item.label}</strong>
            <p>{item.evidence}</p>
          </article>
        ))
      ) : (
        <p className="muted-text">После анализа здесь будут короткие фрагменты из ТЗ и документов.</p>
      )}
      <div className="analysis-evidence-card">
        <strong>Источник</strong>
        <p>Текст извлечен у {readyDocuments.length} из {documents.length} документов.</p>
      </div>
    </aside>
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
