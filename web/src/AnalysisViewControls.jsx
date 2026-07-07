export function AnalysisViewControls({ totalCount, viewMode, onViewModeChange }) {
  return (
    <div className="analysis-view-controls" aria-label="Настройки отображения анализа">
      <div className="analysis-mode-toggle" role="group" aria-label="Детализация">
        <button
          className={viewMode !== 'detailed' ? 'active' : ''}
          onClick={() => onViewModeChange?.('compact')}
          type="button"
        >
          Кратко
        </button>
        <button
          className={viewMode === 'detailed' ? 'active' : ''}
          onClick={() => onViewModeChange?.('detailed')}
          type="button"
        >
          Подробно
        </button>
      </div>
      <div className="analysis-filter-chips" role="group" aria-label="Фильтр фактов">
        <span className="active">
          <span>Все</span>
          <strong>{totalCount || 0}</strong>
        </span>
      </div>
    </div>
  )
}
