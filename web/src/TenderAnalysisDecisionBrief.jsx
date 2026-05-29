import { analysisStatusLabel, formatConfidence } from './formatters'

export function AnalysisDecisionBrief({ analysis, documents = [], onOpenSection }) {
  const decision = buildAnalysisDecision(analysis, documents)

  return (
    <section className={`analysis-decision-brief ${decision.tone}`} aria-label="Короткое решение по анализу ТЗ">
      <div className="analysis-decision-head">
        <span>Короткое решение</span>
        <strong>{decision.title}</strong>
        <p>{decision.summary}</p>
      </div>

      <div className="analysis-reason-list">
        <span>Ключевые причины</span>
        {decision.reasons.length ? (
          <ol>
            {decision.reasons.slice(0, 3).map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ol>
        ) : (
          <p className="muted-text">Запусти анализ, чтобы увидеть причины решения.</p>
        )}
      </div>

      <div className="analysis-decision-actions">
        <button className="secondary-button compact" onClick={() => onOpenSection?.('risks')} type="button">
          Открыть риски
        </button>
        <button className="secondary-button compact" onClick={() => onOpenSection?.('requirements')} type="button">
          Открыть требования
        </button>
      </div>
    </section>
  )
}

export function buildAnalysisDecision(analysis, documents = []) {
  if (!analysis) {
    return {
      tone: 'pending',
      title: 'Нужен анализ ТЗ',
      summary: 'Сначала извлеки текст документов и запусти анализ, чтобы получить решение.',
      reasons: documents.length
        ? [`Документов в карточке: ${documents.length}`]
        : [],
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
    }
  }

  if (risks.length || requirements.length) {
    return {
      tone: 'review',
      title: 'Проверить условия',
      summary: `${statusText}, уверенность ${confidenceText}. Существенных блокеров нет, но условия надо сверить.`,
      reasons,
    }
  }

  return {
    tone: 'ok',
    title: 'Критичных рисков не видно',
    summary: `${statusText}, уверенность ${confidenceText}. Можно переходить к экономике и поставщикам.`,
    reasons: analysis.summary ? [analysis.summary] : ['Анализ не нашел явных рисков и требований.'],
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
