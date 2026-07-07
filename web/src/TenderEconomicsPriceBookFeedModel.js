const NUMERIC_FIELDS = new Set([
  'position_index',
  'unit_price',
  'vat_rate_percent',
  'delivery_cost',
  'pack_quantity',
  'stock_quantity',
  'minimum_order_quantity',
  'minimum_order_amount',
])

const HEADER_ALIASES = {
  position_index: 'position_index',
  position: 'position_index',
  pos: 'position_index',
  позиция: 'position_index',
  supplier: 'supplier_name',
  supplier_name: 'supplier_name',
  vendor: 'supplier_name',
  поставщик: 'supplier_name',
  sku: 'sku',
  article: 'sku',
  артикул: 'sku',
  product_name: 'product_name',
  item_name: 'product_name',
  name: 'product_name',
  товар: 'product_name',
  наименование: 'product_name',
  описание: 'description',
  description: 'description',
  price: 'unit_price',
  unit_price: 'unit_price',
  цена: 'unit_price',
  цена_за_ед: 'unit_price',
  цена_за_единицу: 'unit_price',
  unit: 'unit',
  uom: 'unit',
  ед: 'unit',
  единица: 'unit',
  vat: 'vat_rate_percent',
  nds: 'vat_rate_percent',
  ндс: 'vat_rate_percent',
  delivery: 'delivery_cost',
  delivery_cost: 'delivery_cost',
  доставка: 'delivery_cost',
  pack: 'pack_quantity',
  pack_quantity: 'pack_quantity',
  упаковка: 'pack_quantity',
  stock: 'stock_quantity',
  stock_quantity: 'stock_quantity',
  остаток: 'stock_quantity',
  min_order_quantity: 'minimum_order_quantity',
  minimum_order_quantity: 'minimum_order_quantity',
  мин_заказ: 'minimum_order_quantity',
  min_order_amount: 'minimum_order_amount',
  minimum_order_amount: 'minimum_order_amount',
  min_sum: 'minimum_order_amount',
  url: 'source_url',
  source_url: 'source_url',
  ссылка: 'source_url',
  valid_until: 'valid_until',
  актуально_до: 'valid_until',
}

export function buildPriceBookFeedQuality(rows = [], profiles = []) {
  const profilesByPosition = new Map(
    profiles
      .filter((profile) => profile?.position_index)
      .map((profile) => [Number(profile.position_index), profile])
  )
  const summary = {
    exact_position: 0,
    name_match: 0,
    review: 0,
    error: 0,
    rows: [],
  }

  rows.forEach((row) => {
    let status = 'review'
    let statusLabel = 'Нужна проверка'
    let profile = null
    if (!row?.unit_price) {
      status = 'error'
      statusLabel = 'Нет цены'
      summary.error += 1
    } else if (row.position_index && profilesByPosition.has(Number(row.position_index))) {
      status = 'exact_position'
      statusLabel = 'Точно по позиции'
      profile = profilesByPosition.get(Number(row.position_index))
      summary.exact_position += 1
    } else {
      profile = matchProfileByName(row, profiles)
      if (profile) {
        status = 'name_match'
        statusLabel = 'По названию'
        summary.name_match += 1
      } else {
        summary.review += 1
      }
    }
    summary.rows.push({
      row,
      profile,
      status,
      status_label: statusLabel,
    })
  })

  return summary
}

export function feedQualitySummary(quality) {
  if (!quality?.rows?.length) return 'нет строк'
  const parts = [
    `${quality.rows.length} строк`,
    `${quality.exact_position} точно`,
    `${quality.name_match} по названию`,
  ]
  if (quality.review) parts.push(`${quality.review} проверить`)
  if (quality.error) parts.push(`${quality.error} ошибок`)
  return parts.join(' · ')
}

export function matchProfileByName(row, profiles = []) {
  const rowTokens = normalizedTokens([row?.product_name, row?.description, row?.sku].filter(Boolean).join(' '))
  if (rowTokens.length === 0) return null
  let bestProfile = null
  let bestScore = 0
  profiles.forEach((profile) => {
    const profileTokens = normalizedTokens(profile?.product_name)
    if (profileTokens.length === 0) return
    const matches = profileTokens.filter((token) => rowTokens.includes(token)).length
    const score = matches / Math.max(1, profileTokens.length)
    if (score > bestScore) {
      bestScore = score
      bestProfile = profile
    }
  })
  return bestScore >= 0.55 ? bestProfile : null
}

export function parsePriceBookFeedText(value) {
  const lines = String(value || '')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
  if (lines.length === 0) {
    return { columns: [], mapped_columns: 0, rows: [], skipped_rows: 0, error: '' }
  }
  if (lines.length === 1) {
    return { columns: [], mapped_columns: 0, rows: [], skipped_rows: 0, error: 'Нужна строка заголовков и хотя бы одна строка данных.' }
  }

  const delimiter = detectDelimiter(lines[0])
  const columns = splitDelimitedLine(lines[0], delimiter)
  const mappedHeaders = columns.map(normalizeFeedHeader)
  const mappedColumns = mappedHeaders.filter(Boolean).length
  const rows = []
  let skippedRows = 0

  lines.slice(1).forEach((line) => {
    const cells = splitDelimitedLine(line, delimiter)
    const row = {}
    mappedHeaders.forEach((key, index) => {
      if (!key) return
      const rawValue = (cells[index] || '').trim()
      if (!rawValue) return
      row[key] = parseFeedValue(key, rawValue)
    })
    if (row.unit_price && (row.position_index || row.product_name || row.sku)) {
      rows.push(row)
    } else {
      skippedRows += 1
    }
  })

  return {
    columns,
    mapped_columns: mappedColumns,
    rows,
    skipped_rows: skippedRows,
    error: mappedColumns === 0 ? 'Не удалось распознать колонки.' : '',
  }
}

export function normalizeFeedHeader(header) {
  const key = String(header || '')
    .trim()
    .toLowerCase()
    .replace(/ё/g, 'е')
    .replace(/[№#]/g, '')
    .replace(/[^a-zа-я0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
  return HEADER_ALIASES[key] || ''
}

export function splitDelimitedLine(line, delimiter) {
  const cells = []
  let current = ''
  let quoted = false
  const text = String(line || '')
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index]
    const next = text[index + 1]
    if (char === '"' && quoted && next === '"') {
      current += '"'
      index += 1
      continue
    }
    if (char === '"') {
      quoted = !quoted
      continue
    }
    if (char === delimiter && !quoted) {
      cells.push(current)
      current = ''
      continue
    }
    current += char
  }
  cells.push(current)
  return cells
}

function normalizedTokens(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/ё/g, 'е')
    .replace(/[^a-zа-я0-9]+/g, ' ')
    .split(' ')
    .map((token) => token.trim())
    .filter((token) => token.length > 2)
}

function detectDelimiter(headerLine) {
  const candidates = ['\t', ';', ',']
  return candidates.reduce((best, delimiter) => (
    countOccurrences(headerLine, delimiter) > countOccurrences(headerLine, best) ? delimiter : best
  ), ';')
}

function countOccurrences(value, delimiter) {
  return String(value || '').split(delimiter).length - 1
}

function parseFeedValue(key, value) {
  if (!NUMERIC_FIELDS.has(key)) return value
  const number = Number(String(value).replace(/\s/g, '').replace(',', '.'))
  return Number.isFinite(number) ? number : value
}
