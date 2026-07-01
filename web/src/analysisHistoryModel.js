export function formatConditionChange(item = {}) {
  const label = item.label || item.family || 'условие'
  const type = item.change_type === 'added'
    ? 'добавлено'
    : item.change_type === 'removed'
      ? 'удалено'
      : 'изменено'
  return `${label}: ${type}`
}

export function formatAnalysisHistoryDate(value) {
  if (!value) {
    return 'дата не указана'
  }
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return String(value)
  }
  return parsed.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
