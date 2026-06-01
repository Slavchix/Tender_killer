import { analysisStatusLabel } from './formatters'

export function AnalysisPassport({ analysis, sections = [], selectedSection, onSelectSection }) {
  const passport = analysis?.tz_passport
  if (!passport) return null

  const navSections = Array.isArray(sections) ? sections : []
  const navItems = navSections.map(passportSectionNavItem).filter(Boolean)

  return (
    <section className="analysis-passport" aria-label="Паспорт ТЗ">
      <div className="analysis-passport-header">
        <div>
          <span>Паспорт ТЗ</span>
          <h4>{passport.title || 'Предмет закупки не определен'}</h4>
        </div>
        <strong>{analysisStatusLabel(passport.status || 'needs_review')}</strong>
      </div>
      {navItems.length > 0 && (
        <div className="analysis-passport-nav">
          {navItems.map((item) => (
            <button
              aria-pressed={selectedSection === item.target}
              className={selectedSection === item.target ? 'active' : undefined}
              disabled={!onSelectSection}
              key={item.id}
              onClick={() => onSelectSection?.(item.target)}
              type="button"
            >
              <span>{item.title}</span>
              <strong>{item.count}</strong>
            </button>
          ))}
        </div>
      )}
    </section>
  )
}

function passportSectionNavItem(section) {
  const target = section.id
  if (!target) return null

  return {
    id: section.id,
    target,
    title: section.title,
    count: section.value ?? section.count ?? (Array.isArray(section.items) ? section.items.length : 0),
  }
}
