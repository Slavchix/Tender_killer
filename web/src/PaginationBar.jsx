import { ChevronLeft, ChevronRight } from 'lucide-react'
import { defaultTenderPageLimit } from './constants'

export function PaginationBar({ page, shown, loading, onPrevious, onNext, pageLimit, pageLimitOptions, onPageLimitChange }) {
  const total = Number(page.total) || 0
  const offset = Number(page.offset) || 0
  const limit = Math.max(1, Number(page.limit) || pageLimit || defaultTenderPageLimit)
  const from = total === 0 ? 0 : offset + 1
  const to = Math.min(total, offset + shown)
  const pageNumber = total === 0 ? 0 : Math.floor(offset / limit) + 1
  const pageCount = total === 0 ? 0 : Math.ceil(total / limit)

  return (
    <div className="pagination-bar">
      <div>
        <strong>{from}-{to}</strong>
        <span>из {total}</span>
        <em>{pageNumber}/{pageCount}</em>
      </div>
      <div className="pagination-actions">
        <label className="page-size-control">
          <span>На странице</span>
          <select
            aria-label="Закупок на странице"
            disabled={loading}
            onChange={(event) => onPageLimitChange(event.target.value)}
            value={pageLimit}
          >
            {pageLimitOptions.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </label>
        <button disabled={loading || !page.has_previous} onClick={onPrevious} title="Предыдущая страница" type="button">
          <ChevronLeft size={18} />
        </button>
        <button disabled={loading || !page.has_next} onClick={onNext} title="Следующая страница" type="button">
          <ChevronRight size={18} />
        </button>
      </div>
    </div>
  )
}
