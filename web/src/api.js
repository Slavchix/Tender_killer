function apiJson(path, { method = 'GET', body, errorMessage = 'API не отвечает', signal } = {}) {
  const options = { method }
  if (signal) {
    options.signal = signal
  }
  if (body !== undefined) {
    options.headers = { 'Content-Type': 'application/json' }
    options.body = JSON.stringify(body)
  }
  return fetch(path, options)
    .then(async (response) => {
      const payload = await response.json().catch(() => null)
      if (response.ok) return payload
      const error = new Error((payload && payload.error) || errorMessage)
      error.payload = payload
      error.status = response.status
      throw error
    })
    .catch((error) => {
      if (error.name === 'AbortError') {
        throw new Error(errorMessage)
      }
      throw error
    })
}

function tenderPath(tenderOrSource, externalId) {
  const source = typeof tenderOrSource === 'object' ? tenderOrSource.source : tenderOrSource
  const id = typeof tenderOrSource === 'object' ? tenderOrSource.external_id : externalId
  return `/api/tenders/${encodeURIComponent(source)}/${encodeURIComponent(id)}`
}

function productProfilePath(tender, profile) {
  return `${tenderPath(tender)}/product-profiles/${profile.position_index}`
}

export function fetchTenderDetail(source, externalId) {
  return apiJson(tenderPath(source, externalId), { errorMessage: 'Карточка не найдена' })
}

export function fetchTenderPage(params) {
  return apiJson(`/api/tenders?${params.toString()}`)
}

export function fetchDashboardQueues(params = new URLSearchParams()) {
  return apiJson(`/api/dashboard/queues?${params.toString()}`, {
    errorMessage: 'Не удалось загрузить очереди решений',
  })
}

export function fetchSourceStatus() {
  return apiJson('/api/sources/status')
}

export function fetchSupplierCatalogHealth({ live = false } = {}) {
  const suffix = live ? '?live=1' : ''
  return apiJson(`/api/supplier-catalogs/health${suffix}`, {
    errorMessage: 'Не удалось проверить каталоги поставщиков',
  })
}

export function runSearch(filters) {
  return apiJson('/api/search', {
    method: 'POST',
    body: filters,
    errorMessage: 'Не удалось запустить поиск',
  })
}

export function fetchDatabaseTables() {
  return apiJson('/api/db/tables', { errorMessage: 'Не удалось открыть SQLite' })
}

export function fetchDatabaseTable(tableName, params) {
  return apiJson(`/api/db/tables/${encodeURIComponent(tableName)}?${params.toString()}`, {
    errorMessage: 'Не удалось прочитать таблицу',
  })
}

export function saveTenderWorkflow(tender, payload) {
  return apiJson(`${tenderPath(tender)}/workflow`, {
    method: 'POST',
    body: payload,
    errorMessage: 'Не удалось сохранить статус',
  })
}

export function sendTenderNotification(tender) {
  return apiJson(`${tenderPath(tender)}/notify`, {
    method: 'POST',
    errorMessage: 'Не удалось отправить в Telegram',
  })
}

export function downloadTenderDocuments(tender) {
  return apiJson(`${tenderPath(tender)}/documents/download`, {
    method: 'POST',
    errorMessage: 'Не удалось скачать документы',
  })
}

export function extractTenderDocumentText(tender) {
  return apiJson(`${tenderPath(tender)}/documents/extract-text`, {
    method: 'POST',
    errorMessage: 'Не удалось извлечь текст документов',
  })
}

export function runTenderAnalysis(tender) {
  return apiJson(`${tenderPath(tender)}/analysis/run`, {
    method: 'POST',
    errorMessage: 'Не удалось проанализировать ТЗ',
  })
}

export function refreshTenderDetails(tender) {
  return apiJson(`${tenderPath(tender)}/details/refresh`, {
    method: 'POST',
    errorMessage: 'Не удалось обновить детали',
  })
}

export function importTenderMarketState(tender, payload, { signal } = {}) {
  return apiJson(`${tenderPath(tender)}/market-state/import`, {
    method: 'POST',
    body: payload,
    signal,
    errorMessage: 'Не удалось импортировать ставку',
  })
}

export function rebuildTenderProductProfiles(tender) {
  return apiJson(`${tenderPath(tender)}/product-profiles/rebuild`, {
    method: 'POST',
    errorMessage: 'Не удалось обновить товарные профили',
  })
}

export function saveProfileEconomics(tender, profile, economicsInputs) {
  return apiJson(`${productProfilePath(tender, profile)}/economics`, {
    method: 'POST',
    body: economicsInputs,
    errorMessage: 'Не удалось сохранить экономику',
  })
}

export function saveProfileEconomicsAssumptions(tender, profile, assumptionsInputs) {
  return apiJson(`${productProfilePath(tender, profile)}/economics/assumptions`, {
    method: 'POST',
    body: assumptionsInputs,
    errorMessage: 'Не удалось сохранить допущения экономики',
  })
}

export function addProfileSupplierOption(tender, profile, supplierOption) {
  return apiJson(`${productProfilePath(tender, profile)}/supplier-options`, {
    method: 'POST',
    body: supplierOption,
    errorMessage: 'Не удалось сохранить поставщика',
  })
}

export function selectProfileSupplierOption(tender, profile, optionIndex) {
  return apiJson(`${productProfilePath(tender, profile)}/supplier-options/${optionIndex}/select`, {
    method: 'POST',
    errorMessage: 'Не удалось взять поставщика в расчет',
  })
}

export function autoSelectProfileSupplierOption(tender, profile) {
  return apiJson(`${productProfilePath(tender, profile)}/supplier-options/best/select`, {
    method: 'POST',
    errorMessage: 'Не удалось выбрать лучшего поставщика',
  })
}

export function autoSelectTenderSupplierOptions(tender) {
  return apiJson(`${tenderPath(tender)}/product-profiles/supplier-options/best/select`, {
    method: 'POST',
    errorMessage: 'Не удалось выбрать лучшие цены поставщиков',
  })
}

export function importProfileSupplierDiscoveryCandidate(tender, profile, candidateIndex) {
  return apiJson(`${productProfilePath(tender, profile)}/supplier-discovery/candidates/${candidateIndex}/import`, {
    method: 'POST',
    errorMessage: 'Не удалось добавить найденного поставщика',
  })
}

export function confirmProfilePriceCandidate(tender, profile, candidateId) {
  return apiJson(`${productProfilePath(tender, profile)}/price-candidates/${candidateId}/confirm`, {
    method: 'POST',
    errorMessage: 'Не удалось принять цену кандидата',
  })
}

export function rejectProfilePriceCandidate(tender, profile, candidateId) {
  return apiJson(`${productProfilePath(tender, profile)}/price-candidates/${candidateId}/reject`, {
    method: 'POST',
    errorMessage: 'Не удалось отклонить цену кандидата',
  })
}

export function prepareProfileSupplierSearch(tender, profile) {
  return apiJson(`${productProfilePath(tender, profile)}/supplier-search/prepare`, {
    method: 'POST',
    errorMessage: 'Не удалось подготовить поиск поставщиков',
  })
}

export function saveProfileSupplierCatalogPresets(tender, profile, presetIds) {
  return apiJson(`${productProfilePath(tender, profile)}/supplier-catalog-presets`, {
    method: 'POST',
    body: { preset_ids: presetIds },
    errorMessage: 'Не удалось сохранить каталоги поставщиков',
  })
}

export function runProfileSupplierDiscovery(tender, profile) {
  return apiJson(`${productProfilePath(tender, profile)}/supplier-discovery/run`, {
    method: 'POST',
    errorMessage: 'Не удалось найти кандидатов поставщиков',
  })
}

export function runProfileSupplierUrlDiscovery(tender, profile, payload) {
  return apiJson(`${productProfilePath(tender, profile)}/supplier-discovery/url`, {
    method: 'POST',
    body: payload,
    errorMessage: 'Не удалось проверить ссылку поставщика',
  })
}

export function runProfileAutoEconomics(tender, profile) {
  return apiJson(`${productProfilePath(tender, profile)}/economics/auto-estimate`, {
    method: 'POST',
    errorMessage: 'Не удалось рассчитать экономику автоматически',
  })
}

export function acceptProfileAutoEconomics(tender, profile) {
  return apiJson(`${productProfilePath(tender, profile)}/economics/auto-estimate/accept`, {
    method: 'POST',
    errorMessage: 'Не удалось принять авторасчет в экономику',
  })
}
