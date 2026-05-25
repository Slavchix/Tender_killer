import { Bell, FileText, RefreshCcw } from 'lucide-react'
import { sourceLabels } from './constants'
import { formatDate, formatDateTime, formatMoney } from './formatters'

function Metric({ label, value, tone }) {
  return (
    <div className={`metric ${tone || ''}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

export function DashboardView({ tenderPage, stats, workflowCounts, sources, sourceStatusError, searchSummary, error, onRefreshSources, onOpenTenders, tenders }) {
  const queue = [
    { label: 'Новые', value: workflowCounts.new || 0 },
    { label: 'Интересные', value: workflowCounts.interesting || 0 },
    { label: 'В работе', value: workflowCounts.in_progress || 0 },
    { label: 'Архив', value: workflowCounts.archive || 0 },
  ]

  return (
    <section className="dashboard-view">
      <section className="metrics">
        <Metric label="Найдено" value={tenderPage.total} />
        <Metric label="Активные" value={stats.active} />
        <Metric label="Сумма в выдаче" value={formatMoney(stats.totalPrice)} />
        <Metric label="API" value={error ? 'ошибка' : 'ok'} tone={error ? 'danger' : 'good'} />
      </section>
      {searchSummary && <div className="run-summary">{searchSummary}</div>}
      <section className="dashboard-grid">
        <SourceStatusPanel
          error={sourceStatusError}
          onRefresh={onRefreshSources}
          sources={sources}
        />
        <section className="dashboard-panel">
          <div className="panel-title"><FileText size={18} /> Очередь</div>
          <div className="dashboard-kpis">
            {queue.map((item) => (
              <div key={item.label}>
                <span>{item.label}</span>
                <strong>{item.value}</strong>
              </div>
            ))}
          </div>
          <button className="primary-button dashboard-open-button" onClick={onOpenTenders} type="button">
            Открыть закупки
          </button>
        </section>
      </section>
      <section className="dashboard-secondary-grid">
        <DashboardAttentionPanel
          error={error}
          onOpenTenders={onOpenTenders}
          sources={sources}
          workflowCounts={workflowCounts}
        />
        <DashboardTenderPreview onOpenTenders={onOpenTenders} tenders={tenders} />
      </section>
    </section>
  )
}

function DashboardAttentionPanel({ error, sources, workflowCounts, onOpenTenders }) {
  const sourceErrors = (sources || []).filter((source) => source.last_error)
  const attentionItems = []

  if (error) attentionItems.push({ label: 'API сайта', value: error })
  if (sourceErrors.length) attentionItems.push({ label: 'Источники', value: `${sourceErrors.length} требуют проверки` })
  if (workflowCounts.new) attentionItems.push({ label: 'Новые закупки', value: `${workflowCounts.new} еще не разобраны` })
  if (workflowCounts.interesting) attentionItems.push({ label: 'Интересные', value: `${workflowCounts.interesting} ждут решения` })

  return (
    <section className="dashboard-panel">
      <div className="panel-title"><Bell size={18} /> Требует внимания</div>
      <div className="dashboard-attention-list">
        {attentionItems.map((item) => (
          <button key={item.label} onClick={onOpenTenders} type="button">
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </button>
        ))}
        {!attentionItems.length && <div className="dashboard-empty-note">Критичных событий нет</div>}
      </div>
    </section>
  )
}

function DashboardTenderPreview({ tenders, onOpenTenders }) {
  const previewTenders = (tenders || []).slice(0, 5)

  return (
    <section className="dashboard-panel">
      <div className="panel-title"><FileText size={18} /> Последние закупки</div>
      <div className="dashboard-tender-list">
        {previewTenders.map((tender) => (
          <button key={`${tender.source}-${tender.external_id}`} onClick={onOpenTenders} type="button">
            <strong>{tender.title}</strong>
            <span>{sourceLabels[tender.source] || tender.source} · {formatMoney(tender.price)} · {formatDate(tender.deadline_at)}</span>
          </button>
        ))}
        {!previewTenders.length && <div className="dashboard-empty-note">Запусти поиск, чтобы увидеть свежие закупки</div>}
      </div>
    </section>
  )
}

function SourceStatusPanel({ sources, error, onRefresh }) {
  return (
    <section className="source-status-panel">
      <div className="source-status-header">
        <div className="panel-title"><RefreshCcw size={18} /> Источники</div>
        <button className="icon-button small" onClick={onRefresh} title="Обновить статус источников" type="button">
          <RefreshCcw size={16} />
        </button>
      </div>
      {error && <div className="source-status-error">{error}</div>}
      <div className="source-status-list">
        {(sources || []).map((source) => (
          <SourceStatusRow key={source.source} source={source} />
        ))}
        {!sources?.length && !error && <span className="source-status-empty">Статус источников пока не загружен</span>}
      </div>
    </section>
  )
}

function SourceStatusRow({ source }) {
  const tone = source.last_error ? 'danger' : source.last_success_at ? 'good' : 'idle'
  const statusText = source.last_error ? 'ошибка' : source.last_success_at ? 'ok' : 'нет запусков'
  return (
    <div className={`source-status-row ${tone}`}>
      <span className="source-status-dot" />
      <div className="source-status-main">
        <div>
          <strong>{source.label || sourceLabels[source.source] || source.source}</strong>
          <span>{statusText}</span>
        </div>
        <div className="source-status-meta">
          <span>успех: {formatDateTime(source.last_success_at)}</span>
          <span>checkpoint: {formatDateTime(source.last_seen_published_at)}</span>
          {source.last_error && <span className="source-status-message">{source.last_error}</span>}
        </div>
      </div>
    </div>
  )
}
