import { CalendarDays, Save, UserRound } from 'lucide-react'

export function AnalysisWorkflowPanel({ workflow = {}, draft, disabled = false, saving = false, onChange, onSubmit }) {
  const statuses = Array.isArray(workflow.statuses) ? workflow.statuses : []
  const journal = Array.isArray(workflow.journal) ? workflow.journal.slice(-4).reverse() : []
  const safeDraft = draft || {
    status: workflow.status || 'analysis_ready',
    responsible: '',
    deadline: '',
    comment: '',
  }
  return (
    <form className="analysis-workflow-panel" onSubmit={onSubmit}>
      <div className="analysis-saas-panel-head">
        <span><CalendarDays size={15} /> Рабочий процесс ТЗ</span>
        <strong>{workflow.status_label || workflowStatusLabel(workflow.status)}</strong>
      </div>
      <div className="analysis-workflow-steps">
        {statuses.map((status) => (
          <span className={status.current ? 'current' : status.done ? 'done' : ''} key={status.id}>
            {status.label || status.id}
          </span>
        ))}
      </div>
      <div className="analysis-workflow-form">
        <label>
          <span>Статус</span>
          <select disabled={disabled} onChange={(event) => onChange?.('status', event.target.value)} value={safeDraft.status}>
            {statuses.map((status) => (
              <option key={status.id} value={status.id}>{status.label || status.id}</option>
            ))}
          </select>
        </label>
        <label>
          <span><UserRound size={13} /> Ответственный</span>
          <input disabled={disabled} onChange={(event) => onChange?.('responsible', event.target.value)} value={safeDraft.responsible} />
        </label>
        <label>
          <span>Дедлайн</span>
          <input disabled={disabled} onChange={(event) => onChange?.('deadline', event.target.value)} type="date" value={safeDraft.deadline} />
        </label>
        <label className="wide">
          <span>Комментарий</span>
          <textarea disabled={disabled} onChange={(event) => onChange?.('comment', event.target.value)} rows={2} value={safeDraft.comment} />
        </label>
      </div>
      <button className="secondary-button compact" disabled={disabled} type="submit">
        <Save size={15} /> {saving ? 'Сохраняю...' : 'Сохранить'}
      </button>
      {journal.length ? (
        <div className="analysis-workflow-journal">
          {journal.map((entry, index) => (
            <span key={`${entry.changed_at || index}-${entry.action || index}`}>
              {entry.actor || 'оператор'} · {entry.comment || entry.action}
            </span>
          ))}
        </div>
      ) : null}
    </form>
  )
}

export function workflowStatusLabel(status) {
  const labels = {
    documents_not_downloaded: 'документы не скачаны',
    text_extracted: 'текст извлечен',
    analysis_ready: 'анализ готов',
    operator_checked: 'оператор проверил',
    has_blockers: 'есть блокеры',
  }
  return labels[status] || 'анализ готов'
}
