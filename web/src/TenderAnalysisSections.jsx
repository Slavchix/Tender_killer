import {
  normalizeListItems,
  analysisCategoryLabel,
  analysisSeverityLabel,
  documentStatusCounts,
  documentStatusLabel,
} from './formatters'

export function analysisSectionItems(analysis, documents = []) {
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
  const documentCounts = documentStatusCounts(documents)

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
