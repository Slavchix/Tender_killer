import { documentStatusCounts, formatMoney, formatPercent, nmcPriceValue, participantBidValue, tenderDecisionNextStep } from './formatters'
import { SummaryMetric } from './TenderDetailsShared'

export function TenderSummaryTab({
  tender,
  economics,
  analysis,
  productProfiles = [],
  documents = [],
  onOpenTab,
}) {
  const documentCounts = documentStatusCounts(documents)
  const margin = Number(economics?.margin_percent)
  const marginText = Number.isFinite(margin) ? formatPercent(margin) : 'нужны цены'
  const riskCount = (analysis?.risks?.length || 0) + (analysis?.red_flags?.length || 0)
  const positionCount = productProfiles.length || tender.items?.length || 0
  const readyProducts = productProfiles.filter((profile) => {
    const raw = profile.raw_payload || {}
    return raw.economics || raw.selected_supplier_option != null
  }).length
  const missingCostInputs = economics?.missing_cost_inputs?.length || 0
  const stopPrice = economics?.minimum_margin_price ?? economics?.break_even_price
  const marketState = economics?.market_state || tender.market_state

  return (
    <section className="detail-section active summary-section">
      <div className="section-heading-row">
        <div>
          <h3>Сводка решения</h3>
          <p className="muted-text">Короткий ответ по тендеру и следующий шаг.</p>
        </div>
      </div>

      <div className="summary-decision-grid" aria-label="Сводка решения по тендеру">
        <SummaryMetric value={nmcPriceValue(tender, marketState)} label="НМЦК" />
        <SummaryMetric value={participantBidValue(marketState)} label="ставка участника" />
        <SummaryMetric value={marginText} label="маржа" />
        <SummaryMetric value={formatMoney(stopPrice)} label="стоп-цена" />
        <SummaryMetric value={positionCount} label="позиции" />
        <SummaryMetric value={riskCount} label="риски" />
        <SummaryMetric value={`${documentCounts.ok}/${documents.length}`} label="документы" />
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

        <article className="summary-next-action summary-card secondary">
          <span>Следующий шаг</span>
          <strong>{tenderDecisionNextStep(tender, economics)}</strong>
          <p>{missingCostInputs ? 'Закрыть недостающие цены в экономике.' : 'Проверить риски и документы перед финальным решением.'}</p>
        </article>

        <SummaryCard
          title="Товары"
          action="Открыть товары"
          variant="products"
          onClick={() => onOpenTab?.('products')}
        >
          <p>{positionCount ? `${positionCount} позиций, к расчету готово ${readyProducts}.` : 'Позиции еще не сформированы.'}</p>
          {missingCostInputs > 0 && <em>{missingCostInputs} позиций без себестоимости</em>}
        </SummaryCard>

        <SummaryCard
          title="Документы"
          action="Открыть документы"
          variant="documents"
          onClick={() => onOpenTab?.('documents')}
        >
          <p>Извлечено текстов: {documentCounts.ok} из {documents.length}.</p>
          {documentCounts.attention > 0 && <em>{documentCounts.attention} документов требуют внимания</em>}
        </SummaryCard>
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
