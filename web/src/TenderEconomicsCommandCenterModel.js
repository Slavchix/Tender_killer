export const SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT = 5

export function hasReadyPriceCandidateWithoutCost(profile) {
  if (hasPositiveEconomicsCost(profile)) return false
  const candidates = Array.isArray(profile?.price_candidates) ? profile.price_candidates : []
  return candidates.some((candidate) => {
    const reviewStatus = String(candidate?.review_status || 'pending').toLowerCase()
    return candidate?.auto_eligible === true && reviewStatus !== 'confirmed' && reviewStatus !== 'rejected'
  })
}

export function profileNeedsPriceDiscovery(profile) {
  return !hasPositiveEconomicsCost(profile)
}

export function hasPositiveEconomicsCost(profile) {
  const economics = profile?.raw_payload?.economics || {}
  return Number(economics.unit_cost || 0) > 0 || Number(economics.total_cost || 0) > 0
}

export function nextEconomicsAction({
  canRunActivePriceDiscovery,
  requiresManualPriceFlow,
  priceDiscoveryRunCount,
  readyPriceCandidateCount,
  hasSupplierOptions,
  runningPriceDiscovery,
  confirmingReadyPriceCandidates,
  autoSelectingAllSuppliers,
  onPriceDiscoveryRun,
  onReadyPriceCandidatesConfirmAll,
  onSupplierOptionAutoSelectAll,
}) {
  if (canRunActivePriceDiscovery && priceDiscoveryRunCount > 0) {
    return {
      id: 'discover',
      label: runningPriceDiscovery ? 'Ищу цены...' : `Найти цены (${priceDiscoveryRunCount})`,
      description: 'Активный автопоиск доступен только для мелкой закупки до 5 позиций.',
      disabled: runningPriceDiscovery || !onPriceDiscoveryRun,
      onRun: onPriceDiscoveryRun,
    }
  }
  if (requiresManualPriceFlow && priceDiscoveryRunCount > 0) {
    return {
      id: 'manual',
      label: `Добавить цены (${priceDiscoveryRunCount})`,
      description: 'Для крупной закупки используй ссылки, прайс или КП без массового запуска.',
      disabled: true,
    }
  }
  if (readyPriceCandidateCount > 0) {
    return {
      id: 'ready',
      label: confirmingReadyPriceCandidates ? 'Принимаю...' : `Принять готовые (${readyPriceCandidateCount})`,
      description: 'Добавить проверенные кандидаты в расчет позиции.',
      disabled: confirmingReadyPriceCandidates || !onReadyPriceCandidatesConfirmAll,
      onRun: onReadyPriceCandidatesConfirmAll,
    }
  }
  if (hasSupplierOptions) {
    return {
      id: 'best',
      label: autoSelectingAllSuppliers ? 'Выбираю...' : 'Лучшие в расчет',
      description: 'Выбрать лучшие цены поставщиков для расчета.',
      disabled: autoSelectingAllSuppliers || !onSupplierOptionAutoSelectAll,
      onRun: onSupplierOptionAutoSelectAll,
    }
  }
  return {
    id: 'review',
    label: 'Проверить расчет',
    description: 'Цены закрыты или ожидают ручной проверки.',
    disabled: true,
  }
}

export function economicsSecondaryActions({
  canRunActivePriceDiscovery,
  priceDiscoveryRunCount,
  readyPriceCandidateCount,
  hasSupplierOptions,
  runningPriceDiscovery,
  confirmingReadyPriceCandidates,
  autoSelectingAllSuppliers,
  onPriceDiscoveryRun,
  onReadyPriceCandidatesConfirmAll,
  onSupplierOptionAutoSelectAll,
}) {
  const actions = []
  if (canRunActivePriceDiscovery) {
    actions.push({
      id: 'discover',
      label: runningPriceDiscovery ? 'Ищу...' : `Поиск (${priceDiscoveryRunCount})`,
      description: 'Активный автопоиск цен по позициям.',
      disabled: runningPriceDiscovery || !onPriceDiscoveryRun || priceDiscoveryRunCount === 0,
      onRun: onPriceDiscoveryRun,
    })
  }
  actions.push({
    id: 'ready',
    label: confirmingReadyPriceCandidates ? 'Принимаю...' : `Готовые (${readyPriceCandidateCount})`,
    description: 'Принять готовых кандидатов цен.',
    disabled: confirmingReadyPriceCandidates || !onReadyPriceCandidatesConfirmAll || readyPriceCandidateCount === 0,
    onRun: onReadyPriceCandidatesConfirmAll,
  })
  actions.push({
    id: 'best',
    label: autoSelectingAllSuppliers ? 'Выбираю...' : 'Лучшие цены',
    description: 'Поставить лучшие цены в расчет.',
    disabled: autoSelectingAllSuppliers || !onSupplierOptionAutoSelectAll || !hasSupplierOptions,
    onRun: onSupplierOptionAutoSelectAll,
  })
  return actions
}

export function economicsProgressSteps({
  profiles = [],
  readyPriceCandidateCount = 0,
  hasSupplierOptions = false,
  requiresManualPriceFlow = false,
}) {
  const total = profiles.length
  const priced = profiles.filter(hasPositiveEconomicsCost).length
  const missing = Math.max(0, total - priced)
  return [
    {
      id: 'prices',
      label: 'Цены',
      value: total > 0 ? `${priced}/${total}` : '0',
      detail: requiresManualPriceFlow ? 'ручной поток' : `добавить ${missing}`,
      tone: priced === total && total > 0 ? 'done' : missing > 0 ? 'active' : 'idle',
    },
    {
      id: 'candidates',
      label: 'Кандидаты',
      value: String(readyPriceCandidateCount),
      detail: readyPriceCandidateCount > 0 ? 'готовы к приемке' : 'очередь пуста',
      tone: readyPriceCandidateCount > 0 ? 'active' : 'idle',
    },
    {
      id: 'calculation',
      label: 'Расчет',
      value: hasSupplierOptions ? 'варианты' : priced > 0 ? 'собирается' : 'ждет цен',
      detail: hasSupplierOptions ? 'можно выбрать' : 'маржа после цен',
      tone: hasSupplierOptions || (priced === total && total > 0) ? 'done' : 'idle',
    },
  ]
}

export function priceDiscoveryJobStatusText(job) {
  if (!job?.job_id) return ''
  const searched = Number(job.searched_count || 0)
  const total = Number(job.total_profiles || 0)
  const staged = Number(job.staged_count || job.result?.staged_count || 0)
  const ready = Number(job.ready_count || job.result?.ready_count || 0)
  const progress = total > 0 ? `${searched}/${total}` : `${searched}`
  const completedByProgress = job.status === 'running' && total > 0 && searched >= total
  if (job.status === 'failed') return `Поиск цен: ошибка, проверено ${progress}.`
  if (job.status === 'succeeded' || completedByProgress) {
    return `Поиск цен завершен: проверено ${progress}, подготовлено ${staged}, готово ${ready}.`
  }
  return `Поиск цен выполняется: проверено ${progress}, подготовлено ${staged}, готово ${ready}.`
}
