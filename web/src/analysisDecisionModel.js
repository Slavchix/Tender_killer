import { analysisStatusLabel, formatConfidence } from './formatters'

export function buildAnalysisDecision(analysis, documents = []) {
  const operatorView = analysis?.operator_view
  return {
    actionPlan: operatorView?.action_plan || [],
    decision: operatorView?.decision_brief || fallbackAnalysisDecision(analysis, documents),
  }
}

function fallbackAnalysisDecision(analysis, documents = []) {
  if (!analysis) {
    return {
      tone: 'pending',
      title: 'Нужен анализ ТЗ',
      summary: 'Сначала извлеки текст документов и запусти анализ.',
      reasons: documents.length ? [`Документов в карточке: ${documents.length}`] : [],
      primary_section: 'product_compliance',
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
      primary_section: 'decision_risks',
    }
  }

  if (risks.length || requirements.length) {
    return {
      tone: 'review',
      title: 'Проверить условия',
      summary: `${statusText}, уверенность ${confidenceText}. Существенных блокеров нет, но условия надо сверить.`,
      reasons,
      primary_section: 'product_compliance',
    }
  }

  return {
    tone: 'ok',
    title: 'Критичных рисков не видно',
    summary: `${statusText}, уверенность ${confidenceText}. Можно переходить к следующему этапу проверки.`,
    reasons: analysis.summary ? [analysis.summary] : ['Анализ не нашел явных рисков и требований.'],
    primary_section: 'decision_risks',
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
