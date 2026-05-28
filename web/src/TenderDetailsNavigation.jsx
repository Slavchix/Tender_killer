export function TenderDetailsNavigation({
  activeTab,
  tabs,
  workspaceMode,
  workspaceActions,
  onTabOpen,
  onWorkspaceOpen,
}) {
  return (
    <div className="detail-navigation">
      <nav className="detail-tabs" aria-label="Разделы карточки">
        {tabs.map((tab) => (
          <button
            className={activeTab === tab.id ? 'active' : ''}
            key={tab.id}
            onClick={() => onTabOpen(tab.id)}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <div className="detail-workspace-launchers" aria-label="Рабочие области тендера">
        {workspaceActions.map((action) => (
          <button
            aria-haspopup="dialog"
            className={workspaceMode === action.id ? 'active' : ''}
            key={action.id}
            onClick={() => onWorkspaceOpen(action.id)}
            type="button"
          >
            {action.label}
          </button>
        ))}
      </div>
    </div>
  )
}
