import { formatAnalysisHistoryDate, formatConditionChange } from './analysisHistoryModel'

export function AnalysisHistory({ history = [] }) {
  const visibleHistory = Array.isArray(history) ? history.slice(0, 5) : []
  if (!visibleHistory.length) {
    return null
  }
  return (
    <details className="analysis-history">
      <summary>История анализа ({visibleHistory.length})</summary>
      <div className="analysis-history-list">
        {visibleHistory.map((entry) => {
          const changes = entry.changes || {}
          return (
            <article className="analysis-history-row" key={entry.id || entry.run_number || entry.analyzed_at}>
              <div>
                <strong>Версия {entry.run_number || '1'}</strong>
                <span>{formatAnalysisHistoryDate(entry.analyzed_at)}</span>
              </div>
              <p>{changes.summary || 'Изменения не зафиксированы.'}</p>
              <small>
                +{changes.added_count || 0} / -{changes.removed_count || 0} / Δ{changes.changed_count || 0}
                {changes.feedback_count ? ` · меток: ${changes.feedback_count}` : ''}
              </small>
              <AnalysisHistoryDetails changes={changes} />
            </article>
          )
        })}
      </div>
    </details>
  )
}

function AnalysisHistoryDetails({ changes = {} }) {
  const documents = changes.documents || {}
  const conditionChanges = Array.isArray(changes.condition_changes)
    ? changes.condition_changes.map(formatConditionChange).filter(Boolean)
    : []
  const groups = [
    ['Добавлено', changes.added],
    ['Изменено', changes.changed],
    ['Удалено', changes.removed],
    ['Метки оператора', changes.feedback],
    ['Документы добавлены', documents.added],
    ['Документы изменены', documents.changed],
    ['Документы удалены', documents.removed],
    ['Изменившиеся условия', conditionChanges],
  ]
    .map(([label, values]) => [label, Array.isArray(values) ? values.filter(Boolean).slice(0, 5) : []])
    .filter(([, values]) => values.length)

  if (!groups.length) {
    return null
  }
  return (
    <details className="analysis-history-details">
      <summary>Показать изменения</summary>
      <div>
        {groups.map(([label, values]) => (
          <section key={label}>
            <strong>{label}</strong>
            <ul>
              {values.map((value) => (
                <li key={value}>{value}</li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </details>
  )
}
