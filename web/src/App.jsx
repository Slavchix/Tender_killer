import { useEffect, useMemo, useState } from 'react'
import {
  Bell,
  Building2,
  CalendarClock,
  CircleDollarSign,
  Database,
  ExternalLink,
  FileText,
  Filter,
  RefreshCcw,
  Scale,
  Search,
} from 'lucide-react'
import './styles.css'

const sourceLabels = {
  moscow_supplier_portal: 'Москва',
  mosreg_market: 'МО',
}

const initialFilters = {
  q: '',
  source: '',
  law: '',
  region: '',
  status: '',
  okpd2: '',
  min_price: '',
  max_price: '',
}

function App() {
  const [filters, setFilters] = useState(initialFilters)
  const [appliedFilters, setAppliedFilters] = useState(initialFilters)
  const [tenders, setTenders] = useState([])
  const [selected, setSelected] = useState(null)
  const [details, setDetails] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    loadTenders()
  }, [appliedFilters])

  useEffect(() => {
    if (!selected) {
      setDetails(null)
      return
    }
    fetch(`/api/tenders/${encodeURIComponent(selected.source)}/${encodeURIComponent(selected.external_id)}`)
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('Карточка не найдена')))
      .then(setDetails)
      .catch((err) => setError(err.message))
  }, [selected])

  function loadTenders() {
    setLoading(true)
    setError('')
    const params = new URLSearchParams()
    Object.entries(appliedFilters).forEach(([key, value]) => {
      if (value) params.set(key, value)
    })
    fetch(`/api/tenders?${params.toString()}`)
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('API не отвечает')))
      .then((payload) => {
        setTenders(payload.items || [])
        setSelected((current) => current || payload.items?.[0] || null)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  const stats = useMemo(() => {
    const active = tenders.filter((item) => /актив|прием|приём|подач/i.test(item.status || '')).length
    const totalPrice = tenders.reduce((sum, item) => sum + (Number(item.price) || 0), 0)
    return { active, totalPrice }
  }, [tenders])

  function updateFilter(name, value) {
    setFilters((current) => ({ ...current, [name]: value }))
  }

  function applyFilters(event) {
    event.preventDefault()
    setAppliedFilters(filters)
    setSelected(null)
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <div className="eyebrow">Tender Killer</div>
          <h1>Панель закупок</h1>
        </div>
        <div className="top-actions">
          <button className="icon-button" onClick={loadTenders} title="Обновить список">
            <RefreshCcw size={18} />
          </button>
          <span className="status-pill"><Database size={16} /> SQLite</span>
          <span className="status-pill"><Bell size={16} /> Telegram: уведомления</span>
        </div>
      </header>

      <section className="metrics">
        <Metric label="Найдено" value={tenders.length} />
        <Metric label="Активные" value={stats.active} />
        <Metric label="Сумма в выдаче" value={formatMoney(stats.totalPrice)} />
        <Metric label="API" value={error ? 'ошибка' : 'ok'} tone={error ? 'danger' : 'good'} />
      </section>

      <section className="workspace">
        <aside className="filters-panel">
          <div className="panel-title"><Filter size={18} /> Фильтры</div>
          <form onSubmit={applyFilters}>
            <label>
              Поиск
              <div className="input-with-icon">
                <Search size={16} />
                <input value={filters.q} onChange={(event) => updateFilter('q', event.target.value)} placeholder="бумага, кабель, бетон" />
              </div>
            </label>
            <label>
              Площадка
              <select value={filters.source} onChange={(event) => updateFilter('source', event.target.value)}>
                <option value="">Все</option>
                <option value="moscow_supplier_portal">Москва</option>
                <option value="mosreg_market">МО</option>
              </select>
            </label>
            <label>
              Закон
              <select value={filters.law} onChange={(event) => updateFilter('law', event.target.value)}>
                <option value="">Все</option>
                <option value="44-ФЗ">44-ФЗ</option>
                <option value="223-ФЗ">223-ФЗ</option>
              </select>
            </label>
            <label>
              Регион
              <input value={filters.region} onChange={(event) => updateFilter('region', event.target.value)} placeholder="Москва" />
            </label>
            <label>
              Статус
              <select value={filters.status} onChange={(event) => updateFilter('status', event.target.value)}>
                <option value="">Все</option>
                <option value="Актив">Активные</option>
                <option value="Прием">Прием заявок</option>
                <option value="Заверш">Завершенные</option>
                <option value="Отмен">Отмененные</option>
              </select>
            </label>
            <label>
              ОКПД2
              <input value={filters.okpd2} onChange={(event) => updateFilter('okpd2', event.target.value)} placeholder="17.12" />
            </label>
            <div className="split">
              <label>
                Мин. цена
                <input value={filters.min_price} onChange={(event) => updateFilter('min_price', event.target.value)} inputMode="numeric" placeholder="0" />
              </label>
              <label>
                Макс. цена
                <input value={filters.max_price} onChange={(event) => updateFilter('max_price', event.target.value)} inputMode="numeric" placeholder="500000" />
              </label>
            </div>
            <button className="primary-button" type="submit">Применить</button>
          </form>
        </aside>

        <section className="tender-list">
          <div className="list-header">
            <h2>Закупки</h2>
            {loading && <span>обновление...</span>}
          </div>
          {error && <div className="error-box">{error}</div>}
          <div className="rows">
            {tenders.map((tender) => (
              <button
                className={`tender-row ${selected?.source === tender.source && selected?.external_id === tender.external_id ? 'selected' : ''}`}
                key={`${tender.source}-${tender.external_id}`}
                onClick={() => setSelected(tender)}
              >
                <div className="row-main">
                  <span className="source-chip">{sourceLabels[tender.source] || tender.source}</span>
                  <strong>{tender.title}</strong>
                  <span>{tender.customer || 'Заказчик не указан'}</span>
                </div>
                <div className="row-meta">
                  <span><CircleDollarSign size={15} /> {formatMoney(tender.price)}</span>
                  <span><Scale size={15} /> {tender.law || 'закон не указан'}</span>
                  <span><CalendarClock size={15} /> {formatDate(tender.deadline_at)}</span>
                  <span><FileText size={15} /> {tender.documents_count}</span>
                </div>
              </button>
            ))}
          </div>
        </section>

        <aside className="details-panel">
          {details ? <TenderDetails tender={details} /> : <div className="empty-state">Выбери закупку из списка</div>}
        </aside>
      </section>
    </main>
  )
}

function Metric({ label, value, tone }) {
  return (
    <div className={`metric ${tone || ''}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function TenderDetails({ tender }) {
  const raw = safeJson(tender.raw_payload_json)
  return (
    <div className="details">
      <div className="panel-title"><Building2 size={18} /> Карточка</div>
      <h2>{tender.title}</h2>
      <div className="detail-grid">
        <Info label="Источник" value={sourceLabels[tender.source] || tender.source} />
        <Info label="Номер" value={tender.external_id} />
        <Info label="Цена" value={formatMoney(tender.price)} />
        <Info label="Дедлайн" value={formatDate(tender.deadline_at)} />
        <Info label="Статус" value={tender.status || 'не указан'} />
        <Info label="Регион" value={tender.region || 'не указан'} />
      </div>
      <a className="source-link" href={tender.url} target="_blank" rel="noreferrer">
        Открыть источник <ExternalLink size={16} />
      </a>

      <section className="detail-section">
        <h3>Заказчик</h3>
        <p>{tender.customer || 'Не указан'}</p>
      </section>

      <section className="detail-section">
        <h3>Документы</h3>
        {tender.documents?.length ? (
          <ul className="document-list">
            {tender.documents.map((url) => <li key={url}>{url}</li>)}
          </ul>
        ) : (
          <p>Документы пока не найдены в карточке.</p>
        )}
      </section>

      <section className="detail-section">
        <h3>Сырые признаки</h3>
        <div className="raw-grid">
          <Info label="Закон" value={raw.federalLawName || raw.SourcePlatformName || 'не найден'} />
          <Info label="ОКПД2" value={tender.okpd2 || raw.Koz2Value || 'не найден'} />
          <Info label="Категория" value={tender.category || raw.CategoryName || 'не найдена'} />
        </div>
      </section>
    </div>
  )
}

function Info({ label, value }) {
  return (
    <div className="info">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function formatMoney(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return 'не указана'
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(number)
}

function formatDate(value) {
  if (!value) return 'не указан'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }).format(date)
}

function safeJson(value) {
  try {
    return JSON.parse(value || '{}')
  } catch {
    return {}
  }
}

export default App
