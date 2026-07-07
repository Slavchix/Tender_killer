import { formatPercent, tenderDecisionNextStep } from './formatters'

export function TenderSummaryTab({
  tender,
  economics,
  analysis,
  onOpenTab,
}) {
  const margin = Number(economics?.margin_percent)
  const marginText = Number.isFinite(margin) ? formatPercent(margin) : 'нужны цены'
  const riskCount = (analysis?.risks?.length || 0) + (analysis?.red_flags?.length || 0)
  const missingCostInputs = economics?.missing_cost_inputs?.length || 0

  return (
    <section className="detail-section active summary-section">
      <div className="section-heading-row">
        <div>
          <h3>Сводка решения</h3>
          <p className="muted-text">Короткий ответ по тендеру и следующий шаг.</p>
        </div>
      </div>

      <div className="summary-work-grid">
        <SummaryCard
          title="Экономика"
          action="Открыть экономику"
          variant="economics"
          onClick={() => onOpenTab?.('economics')}
        >
          <p>{economics ? `Расчет есть, маржа ${marginText}.` : 'Расчет еще не готов.'}</p>
          {missingCostInputs > 0 && <em>{missingCostInputs} позиций без себестоимости</em>}
        </SummaryCard>

        <SummaryCard
          title="Анализ"
          action="Открыть анализ"
          variant="analysis"
          onClick={() => onOpenTab?.('analysis')}
        >
          <p>{analysis ? `Рисков: ${riskCount}.` : 'Анализ ТЗ еще не запускался.'}</p>
          {analysis?.summary && <em>{analysis.summary}</em>}
        </SummaryCard>

        <article className="summary-next-action summary-card">
          <span>Следующий шаг</span>
          <strong>{tenderDecisionNextStep(tender, economics)}</strong>
          <p>{missingCostInputs ? 'Закрыть недостающие цены в экономике.' : 'Проверить риски и документы перед финальным решением.'}</p>
        </article>
      </div>
    </section>
  )
}

function SummaryCard({ title, action, variant = 'secondary', onClick, children }) {
  return (
    <article className={`summary-card ${variant === 'economics' || variant === 'analysis' ? 'primary' : 'secondary'} ${variant}`}>
      <span>{title}</span>
      {children}
      <button className="secondary-button compact" onClick={onClick} type="button">
        {action}
      </button>
    </article>
  )
}
