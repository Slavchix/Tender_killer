import { buildAnalysisDecision } from './analysisDecisionModel'

export function AnalysisDecisionBrief({ analysis, documents = [], onOpenSection }) {
  const { decision, actionPlan } = buildAnalysisDecision(analysis, documents)
  const primarySection = decision.primary_section || 'decision_risks'

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
        <details className="analysis-action-plan">
          <summary>
            <span>План проверки</span>
            <strong>{actionPlan.length}</strong>
          </summary>
          <div className="analysis-action-plan-list">
            {actionPlan.slice(0, 4).map((item) => (
              <button
                className={`analysis-action-card ${item.status || 'pending'}`}
                key={item.id || item.title}
                onClick={() => onOpenSection?.(item.id || primarySection)}
                type="button"
              >
                <strong>{item.title}</strong>
                <em>{item.next_step}</em>
                {item.items?.length ? <small>{item.items.slice(0, 3).join(', ')}</small> : null}
              </button>
            ))}
          </div>
        </details>
      )}

      <div className="analysis-decision-actions">
        <button className="secondary-button compact" onClick={() => onOpenSection?.(primarySection)} type="button">
          Открыть главное
        </button>
      </div>
    </section>
  )
}
