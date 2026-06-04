import { ChevronDown, ChevronUp, Filter, Search } from 'lucide-react'
import {
  deadlineOptions,
  lawOptions,
  regionOptions,
  sourceOptions,
  statusOptions,
} from './constants'

export function FiltersPanel({
  activeFilterChips,
  collapsed = false,
  filters,
  onApplyFilters,
  onClearFilters,
  onToggleCollapsed,
  onUpdateFilter,
  variant = 'sidebar',
}) {
  const isTop = variant === 'top'
  const panelClassName = [
    'filters-panel',
    isTop ? 'top-filters-panel' : '',
    isTop && collapsed ? 'is-collapsed' : '',
  ].filter(Boolean).join(' ')

  return (
    <aside className={panelClassName}>
      <div className="filters-header">
        <div className="panel-title">
          <Filter size={18} />
          <span className="filters-title-text">Фильтры</span>
        </div>
        {isTop && (
          <button
            aria-expanded={!collapsed}
            className="secondary-button compact top-filter-toggle"
            onClick={onToggleCollapsed}
            type="button"
          >
            {collapsed ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
            <span>{collapsed ? 'Показать фильтры' : 'Скрыть фильтры'}</span>
          </button>
        )}
      </div>

      {!collapsed && (
        <form className={isTop ? 'top-filter-form' : ''} onSubmit={onApplyFilters}>
          <label className="filter-search-field">
            Поиск
            <div className="input-with-icon">
              <Search size={16} />
              <input
                onChange={(event) => onUpdateFilter('q', event.target.value)}
                placeholder="бумага, кабель, бетон"
                value={filters.q}
              />
            </div>
          </label>

          <label>
            Площадка
            <select
              onChange={(event) => onUpdateFilter('source', event.target.value)}
              value={sourceSelectValue(filters.source)}
            >
              <option value="">Москва + МО</option>
              {sourceOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            Статус
            <select
              onChange={(event) => onUpdateFilter('status', event.target.value)}
              value={filters.status}
            >
              {statusOptions.map((option) => (
                <option key={option.label} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            Дедлайн
            <select
              name="deadline_days"
              onChange={(event) => onUpdateFilter('deadline_days', event.target.value)}
              value={filters.deadline_days}
            >
              {deadlineOptions.map((option) => (
                <option key={option.value || 'unlimited-deadline'} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            Закон
            <select
              onChange={(event) => onUpdateFilter('law', event.target.value)}
              value={filters.law}
            >
              {lawOptions.map((option) => (
                <option key={option.label} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            Регион
            <select
              name="region"
              onChange={(event) => onUpdateFilter('region', event.target.value)}
              value={filters.region}
            >
              {regionOptions.map((option) => (
                <option key={option.value || 'all-regions'} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            ОКПД2
            <input
              onChange={(event) => onUpdateFilter('okpd2', event.target.value)}
              placeholder="17.12, 22.23, 27"
              value={filters.okpd2}
            />
          </label>

          <label>
            ИНН заказчика
            <input
              inputMode="numeric"
              onChange={(event) => onUpdateFilter('customer_inn', event.target.value)}
              placeholder="7708044657"
              value={filters.customer_inn}
            />
          </label>

          <div className="split top-price-fields">
            <label>
              Мин. цена
              <input
                inputMode="numeric"
                onChange={(event) => onUpdateFilter('min_price', event.target.value)}
                placeholder="0"
                value={filters.min_price}
              />
            </label>
            <label>
              Макс. цена
              <input
                inputMode="numeric"
                onChange={(event) => onUpdateFilter('max_price', event.target.value)}
                placeholder="500000"
                value={filters.max_price}
              />
            </label>
          </div>

          <div className="top-filter-actions">
            <button className="primary-button" type="submit">
              Применить
            </button>
            <button className="secondary-button compact" onClick={onClearFilters} type="button">
              Очистить
            </button>
          </div>
        </form>
      )}

      <div className="applied-filters">
        <span>Применено сейчас</span>
        <div>
          {activeFilterChips.map((chip) => (
            <strong key={chip}>{chip}</strong>
          ))}
        </div>
      </div>
    </aside>
  )
}

function sourceSelectValue(value) {
  const values = splitFilterValues(value)
  return values.length === 1 ? values[0] : ''
}

function splitFilterValues(value) {
  return String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}
