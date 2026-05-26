export function SummaryMetric({ value, label }) {
  return (
    <span>
      <strong>{value}</strong>
      <em className="summary-label">{label}</em>
    </span>
  )
}

export function Info({ label, value }) {
  return (
    <div className="info">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}
