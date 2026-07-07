import { workflowLabels } from './constants'
import { formatDate } from './formatters'

export function WorkflowTabPanel({ tender, note, saving, onNoteChange, onSaveWorkflow }) {
  const currentStatus = tender.workflow_status || 'new'
  const noteState = note?.trim() ? 'есть' : 'нет'

  return (
    <section className="detail-section active workflow-section">
      <div className="section-heading-row workflow-heading-row">
        <div>
          <h3>Рабочий статус</h3>
          <p className="muted-text">Решение и заметка по закупке.</p>
        </div>
        <label className="workflow-status-select">
          Статус
          <select
            disabled={saving}
            value={currentStatus}
            onChange={(event) => onSaveWorkflow(event.target.value)}
          >
            {Object.entries(workflowLabels).map(([status, label]) => (
              <option key={status} value={status}>
                {label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="workflow-compact-row" aria-label="Сводка рабочего статуса">
        <span>
          <strong>{workflowLabels[currentStatus] || 'Новая'}</strong>
          <em>статус</em>
        </span>
        <span>
          <strong>{noteState}</strong>
          <em>заметка</em>
        </span>
        <span>
          <strong>{formatDate(tender.deadline_at)}</strong>
          <em>срок</em>
        </span>
      </div>

      <div className="workflow-note-panel">
        <label className="note-editor">
          Заметка
          <textarea
            value={note}
            onChange={(event) => onNoteChange(event.target.value)}
            placeholder="Например: проверить доставку, сертификаты, маржу."
          />
        </label>
        <button className="secondary-button" disabled={saving} onClick={() => onSaveWorkflow()} type="button">
          {saving ? 'Сохранение...' : 'Сохранить заметку'}
        </button>
      </div>
    </section>
  )
}
