import { analysisStatusLabel, formatConfidence } from './formatters'

export function AnalysisDecisionBrief({ analysis, documents = [], onOpenSection }) {
  const operatorView = analysis?.operator_view
  const decision = operatorView?.decision_brief || fallbackAnalysisDecision(analysis, documents)
  const actionPlan = operatorView?.action_plan || []
  const documentState = operatorView?.document_state
  const primarySection = decision.primary_section || 'blockers'

  return (
    <section className={`analysis-decision-brief ${decision.tone || 'pending'}`} aria-label="Короткое решение по анализу ТЗ">
      <div className="analysis-decision-head">
        <span>Короткое решение</span>
        <strong>{decision.title}</strong>
        <p>{decision.summary}</p>
      </div>

      <div className="analysis-reason-list">
        <span>Ключевые причины</span>
        {decision.reasons?.length ? (
          <ol>
            {decision.reasons.slice(0, 3).map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ol>
        ) : (
          <p className="muted-text">Запусти анализ, чтобы увидеть причины решения.</p>
        )}
      </div>

      {actionPlan.length > 0 && (
        <div className="analysis-action-plan">
          <span>План проверки</span>
          {actionPlan.slice(0, 4).map((item) => (
            <button
              className={`analysis-action-card ${item.status || 'pending'}`}
              key={item.id || item.title}
              onClick={() => onOpenSection?.(item.id === 'documents' ? 'evidence' : item.id)}
              type="button"
            >
              <strong>{item.title}</strong>
              <em>{item.next_step}</em>
              {item.items?.length ? <small>{item.items.slice(0, 3).join(', ')}</small> : null}
            </button>
          ))}
        </div>
      )}

      {documentState && (
        <div className={`analysis-document-state ${documentState.status || 'pending'}`}>
          <span>Документы</span>
          <strong>{documentState.text_ready}/{documentState.total}</strong>
          <p>{documentState.summary}</p>
        </div>
      )}

      <div className="analysis-decision-actions">
        <button className="secondary-button compact" onClick={() => onOpenSection?.(primarySection)} type="button">
          Открыть главное
        </button>
        <button className="secondary-button compact" onClick={() => onOpenSection?.('evidence')} type="button">
          Открыть доказательства
        </button>
      </div>
    </section>
  )
}

function fallbackAnalysisDecision(analysis, documents = []) {
  if (!analysis) {
    return {
      tone: 'pending',
      title: 'Нужен анализ ТЗ',
      summary: 'Сначала извлеки текст документов и запусти анализ.',
      reasons: documents.length ? [`Документов в карточке: ${documents.length}`] : [],
      primary_section: 'documents',
    }
  }

  const redFlags = normalizeReasonList(analysis.red_flags)
  const risks = normalizeReasonList(analysis.risks)
  const requirements = normalizeReasonList(analysis.requirements)
  const checklist = Array.isArray(analysis.checklist) ? analysis.checklist : []
  const highChecklist = checklist.filter((item) => item?.severity === 'high' && item?.label)
  const confidenceText = formatConfidence(analysis.confidence)
  const statusText = analysisStatusLabel(analysis.status)
  const reasons = [
    ...redFlags.map((item) => `Красный флаг: ${item}`),
    ...highChecklist.map((item) => `Высокий риск: ${item.label}`),
    ...risks.map((item) => `Риск: ${item}`),
    ...requirements.map((item) => `Требование: ${item}`),
  ]

  if (redFlags.length || highChecklist.length) {
    return {
      tone: 'danger',
      title: 'Нужна ручная проверка',
      summary: `${statusText}, уверенность ${confidenceText}. Сначала проверь критичные условия.`,
      reasons,
      primary_section: 'blockers',
    }
  }

  if (risks.length || requirements.length) {
    return {
      tone: 'review',
      title: 'Проверить условия',
      summary: `${statusText}, уверенность ${confidenceText}. Существенных блокеров нет, но условия надо сверить.`,
      reasons,
      primary_section: 'requirements',
    }
  }

  return {
    tone: 'ok',
    title: 'Критичных рисков не видно',
    summary: `${statusText}, уверенность ${confidenceText}. Можно переходить к экономике и поставщикам.`,
    reasons: analysis.summary ? [analysis.summary] : ['Анализ не нашел явных рисков и требований.'],
    primary_section: 'price_factors',
  }
}

function normalizeReasonList(items) {
  return (Array.isArray(items) ? items : [])
    .map((item) => {
      if (typeof item === 'string') return item
      if (item && typeof item === 'object') return item.label || item.text || item.value || ''
      return ''
    })
    .map((item) => item.trim())
    .filter(Boolean)
}
