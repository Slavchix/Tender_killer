import { analysisStatusLabel } from './formatters'

export function AnalysisPassport({ analysis, sections = [], selectedSection, onSelectSection }) {
  const passport = analysis?.tz_passport
  if (!passport) return null

  const navSections = Array.isArray(sections) ? sections : []
  const navItems = navSections.map(passportSectionNavItem).filter(Boolean)
  const summaryBlock = passport.summary_block && typeof passport.summary_block === 'object'
    ? passport.summary_block
    : null

  return (
    <section className="analysis-passport" aria-label="Паспорт ТЗ">
      <div className="analysis-passport-header">
        <div>
          <span>Паспорт ТЗ</span>
          <h4>{passport.title || 'Предмет закупки не определен'}</h4>
        </div>
        <strong>{analysisStatusLabel(passport.status || 'needs_review')}</strong>
      </div>
      {summaryBlock && (
        <div className="analysis-passport-compact" aria-label="Паспорт ТЗ v2">
          <PassportSummaryRow label="Предмет" value={summaryBlock.subject} />
          <PassportSummaryRow label="Документы готовы/не готовы" value={summaryBlock.documents} />
          <PassportSummaryRow label="Ключевые условия" value={summaryBlock.key_conditions} />
          <PassportSummaryRow label="Красные флаги" value={summaryBlock.red_flags} />
          <PassportSummaryRow label="Противоречия" value={summaryBlock.conflicts} />
          <PassportSummaryRow label="Ожидаемые условия не найдены" value={summaryBlock.expected_missing} />
          <PassportSummaryRow label="Итог" value={summaryBlock.verdict} />
        </div>
      )}
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

function PassportSummaryRow({ label, value }) {
  const values = normalizePassportValues(value)
  return (
    <div className="analysis-passport-row">
      <span>{label}</span>
      {values.length > 1 ? (
        <ul className="analysis-passport-list">
          {values.slice(0, 5).map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <strong>{values[0] || 'нет'}</strong>
      )}
    </div>
  )
}

function normalizePassportValues(value) {
  if (Array.isArray(value)) {
    return value.map((item) => String(item || '').trim()).filter(Boolean)
  }
  const text = String(value || '').trim()
  return text ? [text] : []
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
