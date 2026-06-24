import {
  documentStatusCounts,
  economicsStatusLabel,
  formatMoney,
  formatPercent,
  nmcPriceValue,
  participantBidValue,
  tenderDecisionLabel,
} from './formatters'
import { SummaryMetric } from './TenderDetailsShared'

export function TenderDecisionStrip({ tender, economics, productProfiles = [], documents = [], analysis }) {
  const decisionMetrics = tender.decision?.metrics || {}
  const margin = Number(decisionMetrics.margin_percent ?? economics?.margin_percent)
  const marginText = Number.isFinite(margin) ? formatPercent(margin) : 'нужны цены'
  const stopPrice = tender.decision?.limit_price ?? economics?.stop_price ?? economics?.target_bid_price ?? economics?.minimum_margin_price ?? economics?.break_even_price ?? economics?.interesting_price
  const documentCounts = documentStatusCounts(documents)
  const decisionBlockerCount = Array.isArray(tender.decision?.blockers) ? tender.decision.blockers.length : null
  const riskCount = decisionBlockerCount ?? (analysis?.risks?.length || 0) + (analysis?.red_flags?.length || 0)
  const positionTotal = numericMetric(decisionMetrics.positions_total, productProfiles.length || tender.items?.length || 0)
  const readyProductsFallback = productProfiles.filter((profile) => {
    const raw = profile.raw_payload || {}
    return raw.economics || raw.selected_supplier_option != null
  }).length
  const readyProducts = numericMetric(decisionMetrics.positions_priced, readyProductsFallback)
  const documentsReady = numericMetric(decisionMetrics.documents_ready, documentCounts.ok)
  const documentsTotal = numericMetric(decisionMetrics.documents_total, documents.length)
  const priceQuality = priceQualityText(decisionMetrics)
  const decisionReasons = Array.isArray(tender.decision?.reasons) ? tender.decision.reasons.filter(Boolean).slice(0, 2) : []
  const decisionBlockers = Array.isArray(tender.decision?.blockers) ? tender.decision.blockers.filter(Boolean).slice(0, 2) : []
  const decisionTree = tender.decision?.reason_tree || null
  const hasDecisionTree = decisionTree && (
    nonEmptyList(decisionTree.positive).length
    || nonEmptyList(decisionTree.negative).length
    || nonEmptyList(decisionTree.actions).length
  )
  const hasDecisionExplanation = !hasDecisionTree && (decisionReasons.length > 0 || decisionBlockers.length > 0)

  return (
    <section className="decision-strip" aria-label="Решение по закупке">
      <div className="decision-strip-grid">
        <SummaryMetric value={tenderDecisionLabel(tender, economics)} label="решение" />
        <SummaryMetric value={nmcPriceValue(tender, economics?.market_state || tender.market_state)} label="НМЦК" />
        <SummaryMetric value={participantBidValue(economics?.market_state || tender.market_state)} label="ставка участника" />
        <SummaryMetric value={Number.isFinite(margin) ? marginText : economicsStatusLabel(economics?.status)} label="маржа" />
        <SummaryMetric value={formatMoney(stopPrice)} label="стоп-цена" />
        <SummaryMetric value={`${readyProducts}/${positionTotal}`} label="позиции" />
        <SummaryMetric value={priceQuality} label="проверка цен" />
        <SummaryMetric value={riskCount} label="риски" />
        <SummaryMetric value={`${documentsReady}/${documentsTotal}`} label="документы" />
      </div>
      {hasDecisionExplanation && (
        <div className="decision-strip-explanation" aria-label="Причины решения">
          {decisionReasons.length > 0 && (
            <div className="decision-strip-reasons">
              <span>Почему</span>
              {decisionReasons.map((reason) => (
                <p key={reason}>{reason}</p>
              ))}
            </div>
          )}
          {decisionBlockers.length > 0 && (
            <div className="decision-strip-blockers">
              <span>Блокеры</span>
              {decisionBlockers.map((blocker) => (
                <p key={blocker}>{blocker}</p>
              ))}
            </div>
          )}
        </div>
      )}
      {hasDecisionTree && <DecisionTree decisionTree={decisionTree} />}
    </section>
  )
}

function DecisionTree({ decisionTree }) {
  return (
    <div className="decision-tree" aria-label="Дерево причин решения">
      <DecisionTreeBranch title="Помогает" tone="positive" items={decisionTree.positive} />
      <DecisionTreeBranch title="Мешает" tone="negative" items={decisionTree.negative} />
      <DecisionTreeBranch title="Что сделать" tone="actions" items={decisionTree.actions} />
    </div>
  )
}

function DecisionTreeBranch({ title, tone, items }) {
  const branchItems = nonEmptyList(items).slice(0, 4)
  if (!branchItems.length) {
    return null
  }
  return (
    <div className={`decision-tree-branch ${tone}`}>
      <span>{title}</span>
      {branchItems.map((item) => (
        <p key={item}>{item}</p>
      ))}
    </div>
  )
}

function nonEmptyList(value) {
  return Array.isArray(value) ? value.filter(Boolean) : []
}

function numericMetric(value, fallback) {
  const number = Number(value)
  return Number.isFinite(number) ? number : fallback
}

function priceQualityText(decisionMetrics) {
  const review = numericMetric(decisionMetrics.price_candidates_review, 0)
  const blocked = numericMetric(decisionMetrics.price_candidates_blocked, 0)
  const total = numericMetric(decisionMetrics.price_candidates_total, 0)
  if (blocked > 0) return `проверить ${review} / блок ${blocked}`
  if (review > 0) return `проверить ${review}`
  if (total > 0) return 'ок'
  return 'нет кандидатов'
}
