import { ChevronLeft, ChevronRight, Filter, Search } from 'lucide-react'
import {
  lawOptions,
  regionOptions,
  sourceOptions,
  statusOptions,
} from './constants'

export function FiltersPanel({
  activeFilterChips,
  filters,
  filtersCollapsed,
  onApplyFilters,
  onClearFilters,
  onToggleCollapsed,
  onToggleMultiFilter,
  onUpdateFilter,
}) {
  function isSelected(name, value) {
    return splitFilterValues(filters[name]).includes(value)
  }

  return (
    <aside className={filtersCollapsed ? 'filters-panel collapsed' : 'filters-panel'}>
      <div className="filters-header">
        <div className="panel-title">
          <Filter size={18} />
          <span className="filters-title-text">Фильтры</span>
        </div>
        <button
          aria-expanded={!filtersCollapsed}
          className="icon-button small filter-collapse-button"
          onClick={onToggleCollapsed}
          title={filtersCollapsed ? 'Развернуть фильтры' : 'Свернуть фильтры'}
          type="button"
        >
          {filtersCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {!filtersCollapsed && (
        <>
          <form onSubmit={onApplyFilters}>
            <label>
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

            <div className="filter-group">
              Площадка
              <div className="check-grid">
                {sourceOptions.map((option) => (
                  <button
                    className={isSelected('source', option.value) || !filters.source ? 'selected' : ''}
                    key={option.value}
                    onClick={() => onToggleMultiFilter('source', option.value)}
                    type="button"
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="filter-group">
              Закон
              <div className="segmented-control">
                {lawOptions.map((option) => (
                  <button
                    className={filters.law === option.value ? 'selected' : ''}
                    key={option.label}
                    onClick={() => onUpdateFilter('law', option.value)}
                    type="button"
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="filter-group">
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
            </div>

            <div className="filter-group">
              Статус
              <div className="segmented-control wrap">
                {statusOptions.map((option) => (
                  <button
                    className={filters.status === option.value ? 'selected' : ''}
                    key={option.label}
                    onClick={() => onUpdateFilter('status', option.value)}
                    type="button"
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

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

            <div className="split">
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

            <button className="primary-button" type="submit">
              Применить
            </button>
            <button className="secondary-button compact" onClick={onClearFilters} type="button">
              Очистить
            </button>
          </form>

          <div className="applied-filters">
            <span>Применено сейчас</span>
            <div>
              {activeFilterChips.map((chip) => (
                <strong key={chip}>{chip}</strong>
              ))}
            </div>
          </div>
        </>
      )}
    </aside>
  )
}

function splitFilterValues(value) {
  return String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}
