import { useMemo, useState } from 'react'

const DEFAULT_FEED_NAME = 'Прайс / КП'
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

export function TenderEconomicsPriceBookFeed({
  profiles = [],
  onPriceBookFeedStage,
  stagingPriceBookFeed = false,
}) {
  const [feedName, setFeedName] = useState(DEFAULT_FEED_NAME)
  const [feedText, setFeedText] = useState('')
  const parsed = useMemo(() => parsePriceBookFeedText(feedText), [feedText])
  const feedPreviewRows = parsed.rows.slice(0, 5)
  const canSubmit = parsed.rows.length > 0 && !parsed.error && !stagingPriceBookFeed && onPriceBookFeedStage

  function submitFeed(event) {
    event.preventDefault()
    if (!canSubmit) return
    onPriceBookFeedStage({
      feed_name: feedName.trim() || DEFAULT_FEED_NAME,
      rows: parsed.rows,
    })
  }

  return (
    <details className="economics-card price-book-feed-panel">
      <summary>
        <span>Price book / КП / feed</span>
        <em>{parsed.rows.length ? `${parsed.rows.length} строк · ${parsed.mapped_columns} колонок` : `${profiles.length} позиций`}</em>
      </summary>
      <form className="price-book-feed-form" onSubmit={submitFeed}>
        <div className="price-book-feed-controls">
          <label>
            <span>Источник</span>
            <input
              onChange={(event) => setFeedName(event.target.value)}
              placeholder={DEFAULT_FEED_NAME}
              value={feedName}
            />
          </label>
          <button className="secondary-button compact" disabled={!canSubmit} type="submit">
            {stagingPriceBookFeed ? 'Загружаю...' : 'Загрузить в кандидаты'}
          </button>
        </div>
        <textarea
          className="price-book-feed-input"
          onChange={(event) => setFeedText(event.target.value)}
          placeholder="position_index;supplier_name;product_name;unit_price;unit;source_url"
          rows={5}
          value={feedText}
        />
        <div className="price-book-feed-status">
          <span>{parsed.error || `Готово к загрузке: ${parsed.rows.length}`}</span>
          {parsed.skipped_rows > 0 && <em>Пропущено строк: {parsed.skipped_rows}</em>}
        </div>
        {feedPreviewRows.length > 0 && (
          <div className="price-book-feed-preview" aria-label="Preview price book feed">
            {feedPreviewRows.map((row, index) => (
              <div className="price-book-feed-row" key={`${row.position_index || row.product_name || index}-${index}`}>
                <strong>{row.position_index ? `#${row.position_index}` : row.product_name || row.sku || 'строка'}</strong>
                <span>{row.supplier_name || row.provider || 'поставщик не указан'}</span>
                <span>{row.product_name || row.description || 'товар не указан'}</span>
                <em>{row.unit_price ? `${row.unit_price} ₽${row.unit ? ` / ${row.unit}` : ''}` : 'нет цены'}</em>
              </div>
            ))}
          </div>
        )}
      </form>
    </details>
  )
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
