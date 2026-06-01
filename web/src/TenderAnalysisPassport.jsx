import { analysisStatusLabel } from './formatters'

export function AnalysisPassport({ analysis }) {
  const passport = analysis?.tz_passport
  if (!passport) return null

  const sections = Array.isArray(passport.sections) ? passport.sections : []

  return (
    <section className="analysis-passport" aria-label="Паспорт ТЗ">
      <div className="analysis-passport-header">
        <div>
          <span>Паспорт ТЗ</span>
          <h4>{passport.title || 'Предмет закупки не определен'}</h4>
        </div>
        <strong>{analysisStatusLabel(passport.status || 'needs_review')}</strong>
      </div>
      <div className="analysis-passport-grid">
        {sections.map((section) => (
          <PassportSection key={section.id} section={section} />
        ))}
      </div>
    </section>
  )
}

function PassportSection({ section }) {
  const items = Array.isArray(section.items) ? section.items : []

  return (
    <article className={`analysis-passport-section ${section.tone || 'default'}`}>
      <div className="analysis-passport-section-title">
        <span>{section.title}</span>
        <strong>{section.count ?? items.length}</strong>
      </div>
      {items.length ? (
        <div className="analysis-passport-items">
          {items.map((item, index) => (
            <div className="analysis-passport-item" key={item.id || `${item.label}-${index}`}>
              <strong>{item.label}</strong>
              {item.value && <p>{item.value}</p>}
              <div className="analysis-passport-meta">
                {item.source && <span>{item.source}</span>}
                {item.impact && <em>{item.impact}</em>}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="muted-text">{section.empty}</p>
      )}
    </article>
  )
}
