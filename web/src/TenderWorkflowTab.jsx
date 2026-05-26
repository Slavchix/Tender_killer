import { workflowLabels } from './constants'
import { formatDate } from './formatters'
import { Info, SummaryMetric } from './TenderDetailsShared'

export function WorkflowTabPanel({ tender, raw, note, saving, onNoteChange, onSaveWorkflow }) {
  const currentStatus = tender.workflow_status || 'new'
  const noteState = note?.trim() ? 'есть' : 'нет'

  return (
    <section className="detail-section active workflow-section">
      <div className="section-heading-row">
        <h3>Рабочий статус</h3>
      </div>
      <div className="workflow-status-summary tab-summary-grid" aria-label="Сводка рабочего статуса">
        <SummaryMetric value={workflowLabels[currentStatus] || 'Новая'} label="текущий статус" />
        <SummaryMetric value={noteState} label="заметка" />
        <SummaryMetric value={formatDate(tender.deadline_at)} label="срок" />
      </div>
      <div className="workflow-actions">
        {Object.entries(workflowLabels).map(([status, label]) => (
          <button
            className={status === currentStatus ? 'active' : ''}
            disabled={saving}
            key={status}
            onClick={() => onSaveWorkflow(status)}
            type="button"
          >
            {label}
          </button>
        ))}
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
      <details className="debug-details">
        <summary>Сырые признаки</summary>
        <div className="raw-grid">
          <Info label="Закон" value={raw.federalLawName || raw.SourcePlatformName || 'не найден'} />
          <Info label="ОКПД2" value={tender.okpd2 || raw.Koz2Value || 'не найден'} />
          <Info label="Категория" value={tender.category || raw.CategoryName || 'не найдена'} />
        </div>
      </details>
    </section>
  )
}
