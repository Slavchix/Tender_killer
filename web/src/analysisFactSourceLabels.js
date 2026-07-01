export function sourceBindingLabel(level) {
  if (level === 'explicit') return 'источник подтвержден'
  if (level === 'context') return 'источник по контексту'
  if (level === 'unbound') return 'нужна ручная проверка'
  return 'вывод без источника'
}

export function confidenceLevelLabel(level) {
  if (level === 'high') return 'уверенность высокая'
  if (level === 'low') return 'уверенность низкая'
  return 'уверенность средняя'
}

export function sourceAuthorityLabel(level) {
  if (level === 'primary_for_topic') return 'главный источник по теме'
  if (level === 'primary_document') return 'основной документ'
  if (level === 'supporting_document') return 'вспомогательный источник'
  return 'контекст источника'
}

export function sourceDocumentRoleLabel(role) {
  if (role === 'technical_spec' || role === 'technical_specification') return 'ТЗ'
  if (role === 'technical_spec_appendix') return 'приложение к ТЗ'
  if (role === 'contract_project') return 'проект контракта'
  if (role === 'pik_obligations_payment') return 'ПИК, оплата и приемка'
  if (role === 'participant_requirements') return 'требования к участнику'
  if (role === 'unsupported_primary') return 'основной документ без текста'
  if (role === 'other') return 'другой документ'
  return role
}

export function sourceTopicLabel(topic) {
  const labels = {
    acceptance_documents: 'приемочные документы',
    acceptance_process: 'приемка',
    advance: 'аванс',
    certificates_closing_docs: 'сертификаты и закрывающие',
    contract_security: 'обеспечение контракта',
    delivery_place: 'место поставки',
    delivery_schedule: 'срок поставки',
    logistics_responsibility: 'логистика',
    participant_requirements: 'требования к участнику',
    payment_terms: 'условия оплаты',
    penalties: 'штрафы',
    technical_characteristics: 'характеристики',
    warranty: 'гарантия',
  }
  return labels[topic] || topic
}

export function sourceRoleConfidenceLabel(value) {
  if (value === 'high') return 'уверенно'
  if (value === 'medium') return 'средняя уверенность'
  if (value === 'low') return 'низкая уверенность'
  return value
}

export function sourceTextQualityLabel(value) {
  if (value === 'ok') return 'текст извлечен'
  if (value === 'empty') return 'текст пустой'
  if (value === 'short') return 'мало текста'
  if (value === 'unsupported') return 'формат не прочитан'
  return value
}

export function evidenceQualityLabel(level) {
  if (level === 'exact') return 'точное доказательство'
  if (level === 'context') return 'контекст источника'
  if (level === 'conflict') return 'противоречие'
  if (level === 'missing') return 'не найдено'
  return 'вывод без источника'
}
