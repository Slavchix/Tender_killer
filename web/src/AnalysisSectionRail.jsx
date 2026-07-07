export function AnalysisSectionRail({ sections, selectedSection, onSelectSection }) {
  return (
    <aside className="analysis-section-rail" aria-label="Разделы анализа">
      {sections.map((section) => (
        <AnalysisSectionRailItem
          active={selectedSection === section.id}
          key={section.id}
          onClick={() => onSelectSection(section.id)}
          title={section.title}
          value={section.value}
        />
      ))}
    </aside>
  )
}

function AnalysisSectionRailItem({ title, value, active = false, onClick }) {
  return (
    <button
      aria-pressed={active}
      className={active ? 'analysis-section-item active' : 'analysis-section-item'}
      onClick={onClick}
      type="button"
    >
      <strong>{title}</strong>
      <span>{value}</span>
    </button>
  )
}
