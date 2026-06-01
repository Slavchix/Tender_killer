import {
  normalizeListItems,
  analysisCategoryLabel,
  analysisSeverityLabel,
  documentStatusCounts,
  documentStatusLabel,
} from './formatters'
import { buildDocumentEvidenceItems } from './TenderAnalysisEvidenceModel'

export function analysisSectionItems(analysis, documents = []) {
  const operatorView = analysis?.operator_view
  const operatorSections = Array.isArray(operatorView?.sections) ? operatorView.sections : []
  if (operatorSections.length) {
    return operatorSections.map((section) => ({
      id: section.id,
      title: section.title,
      value: section.count ?? section.items?.length ?? 0,
    }))
  }

  const requirementsCount = analysis?.requirements?.length || 0
  const risksCount = (analysis?.risks?.length || 0) + (analysis?.red_flags?.length || 0)
  const checklistCount = analysis?.checklist?.length || 0
  const documentCounts = documentStatusCounts(documents)

  return [
    { id: 'risks', title: 'Риски', value: risksCount },
    { id: 'requirements', title: 'Требования', value: requirementsCount },
    { id: 'documents', title: 'Документы', value: `${documentCounts.ok}/${documents.length}` },
    { id: 'checklist', title: 'Чеклист', value: checklistCount },
  ]
}

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

export function AnalysisSectionBody({ sectionId, analysis, documents = [] }) {
  const operatorView = analysis?.operator_view
  const operatorSection = operatorView?.sections?.find((section) => section.id === sectionId)
  if (operatorSection) {
    return <AnalysisOperatorSection section={operatorSection} />
  }

  const documentCounts = documentStatusCounts(documents)
  const evidenceItems = buildDocumentEvidenceItems(analysis, documents)

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
        <AnalysisDocumentEvidenceList evidenceItems={evidenceItems} />
        <AnalysisDocumentList documents={documents} />
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

function AnalysisOperatorSection({ section }) {
  const items = Array.isArray(section.items) ? section.items : []

  return (
    <div className={`analysis-card operator-section ${section.tone || 'default'}`}>
      <div className="analysis-checklist-header">
        <span>{section.title}</span>
        <strong>{section.count ?? items.length}</strong>
      </div>
      {items.length ? (
        <div className="analysis-checklist-list">
          {items.map((item, index) => {
            const sourceLabel = item.source_label || item.source
            return (
              <article className={`analysis-checklist-row severity-${item.severity || 'medium'}`} key={item.id || `${item.label}-${index}`}>
                <div className="analysis-checklist-main">
                  <strong>{item.label}</strong>
                  <div className="analysis-checklist-tags">
                    <span>{analysisCategoryLabel(item.category)}</span>
                    <span>{analysisSeverityLabel(item.severity)}</span>
                    {item.status && <span>{operatorStatusLabel(item.status)}</span>}
                  </div>
                </div>
                {item.description && <p>{item.description}</p>}
                {item.impact && <em className="analysis-evidence-impact">{item.impact}</em>}
                {sourceLabel && (
                  <div className="analysis-source-context">
                    <span>Источник</span>
                    <strong>{sourceLabel}</strong>
                    {item.source_context && <p>{item.source_context}</p>}
                  </div>
                )}
              </article>
            )
          })}
        </div>
      ) : (
        <p className="muted-text">{section.empty}</p>
      )}
    </div>
  )
}

function operatorStatusLabel(status) {
  if (status === 'attention') return 'проверить'
  return documentStatusLabel(status)
}

function AnalysisDocumentEvidenceList({ evidenceItems = [] }) {
  if (!evidenceItems.length) {
    return (
      <div className="analysis-document-evidence-grid">
        <p className="muted-text">Фрагменты с влиянием на решение появятся после анализа документов.</p>
      </div>
    )
  }

  return (
    <div className="analysis-document-evidence-grid">
      {evidenceItems.map((item) => (
        <article className="analysis-evidence-card analysis-evidence-item" key={item.id}>
          <div className="analysis-evidence-meta">
            <span>{item.typeLabel}</span>
            <span>{item.importanceLabel}</span>
          </div>
          <strong>{item.label}</strong>
          <p>{item.fragment}</p>
          <em className="analysis-evidence-impact">{item.impact}</em>
          <small>{item.documentName}</small>
        </article>
      ))}
    </div>
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

function AnalysisDocumentList({ documents = [] }) {
  if (!documents.length) {
    return (
      <div className="analysis-document-list">
        <p className="muted-text">Документы по закупке пока не загружены.</p>
      </div>
    )
  }

  return (
    <div className="analysis-document-list">
      {documents.map((document, index) => (
        <article className="analysis-document-row" key={`${document.name || document.url}-${index}`}>
          <strong>{document.name || document.url || `Документ ${index + 1}`}</strong>
          <span>{documentStatusLabel(document.text_status)}</span>
          <p>{document.text_status === 'ok' ? 'Текст готов для анализа.' : 'Документ требует внимания или не содержит машинно-читаемый текст.'}</p>
        </article>
      ))}
    </div>
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

export function AnalysisChecklist({ items = [] }) {
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
