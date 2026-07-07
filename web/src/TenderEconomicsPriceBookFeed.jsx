import { useMemo, useState } from 'react'
import {
  buildPriceBookFeedQuality,
  feedQualitySummary,
  parsePriceBookFeedText,
} from './TenderEconomicsPriceBookFeedModel'

const DEFAULT_FEED_NAME = 'Прайс / КП'

export function TenderEconomicsPriceBookFeed({
  profiles = [],
  onPriceBookFeedStage,
  onPriceBookFeedFileStage,
  stagingPriceBookFeed = false,
}) {
  const [feedName, setFeedName] = useState(DEFAULT_FEED_NAME)
  const [feedText, setFeedText] = useState('')
  const [stageMode, setStageMode] = useState('all')
  const [selectedFile, setSelectedFile] = useState(null)
  const [fileError, setFileError] = useState('')
  const parsed = useMemo(() => parsePriceBookFeedText(feedText), [feedText])
  const quality = useMemo(() => buildPriceBookFeedQuality(parsed.rows, profiles), [parsed.rows, profiles])
  const feedPreviewRows = quality.rows.slice(0, 5)
  const canSubmit = parsed.rows.length > 0 && !parsed.error && !stagingPriceBookFeed && onPriceBookFeedStage
  const canSubmitFile = selectedFile && !stagingPriceBookFeed && onPriceBookFeedFileStage

  function submitFeed(event) {
    event.preventDefault()
    if (!canSubmit) return
    onPriceBookFeedStage({
      feed_name: feedName.trim() || DEFAULT_FEED_NAME,
      rows: parsed.rows,
      stage_mode: stageMode,
    })
  }

  function submitFile() {
    if (!canSubmitFile) return
    setFileError('')
    fileToBase64(selectedFile)
      .then((contentBase64) => onPriceBookFeedFileStage({
        feed_name: feedName.trim() || DEFAULT_FEED_NAME,
        file_name: selectedFile.name,
        content_base64: contentBase64,
        stage_mode: stageMode,
      }))
      .catch((err) => setFileError(err.message || 'Не удалось прочитать файл'))
  }

  return (
    <details className="economics-card price-book-feed-panel">
      <summary>
        <span>Прайс / КП</span>
        <em>{parsed.rows.length ? feedQualitySummary(quality) : `${profiles.length} позиций`}</em>
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
          <label>
            <span>Режим загрузки</span>
            <select onChange={(event) => setStageMode(event.target.value)} value={stageMode}>
              <option value="all">Все совпадения</option>
              <option value="confident">Только уверенные</option>
              <option value="review">Только спорные</option>
              <option value="errors">Только ошибки</option>
            </select>
          </label>
          <button className="secondary-button compact" disabled={!canSubmit} type="submit">
            {stagingPriceBookFeed ? 'Загружаю...' : 'Загрузить в кандидаты'}
          </button>
        </div>
        <div className="price-book-feed-file">
          <label>
            <span>Файл CSV/XLSX</span>
            <input
              accept=".csv,.tsv,.txt,.xlsx,.xlsm"
              onChange={(event) => {
                setSelectedFile(event.target.files?.[0] || null)
                setFileError('')
              }}
              type="file"
            />
          </label>
          <button className="secondary-button compact" disabled={!canSubmitFile} onClick={submitFile} type="button">
            Загрузить файл
          </button>
        </div>
        {fileError && <div className="price-book-feed-status error">{fileError}</div>}
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
        {quality.rows.length > 0 && (
          <div className="price-book-feed-quality">
            <strong>Качество сопоставления</strong>
            <span>Точно по позиции: {quality.exact_position}</span>
            <span>По названию: {quality.name_match}</span>
            <span>Нужна проверка: {quality.review}</span>
          </div>
        )}
        {feedPreviewRows.length > 0 && (
          <div className="price-book-feed-preview" aria-label="Предпросмотр прайса">
            {feedPreviewRows.map((item, index) => (
              <div
                className={`price-book-feed-row price-book-feed-quality-row ${item.status}`}
                key={`${item.row.position_index || item.row.product_name || index}-${index}`}
              >
                {item.profile && <mark>{item.profile.position_index ? `#${item.profile.position_index}` : 'позиция'}</mark>}
                <strong>
                  {item.row.position_index ? `#${item.row.position_index}` : item.row.product_name || item.row.sku || 'строка'}
                </strong>
                <span>{item.status_label}</span>
                <span>{item.row.supplier_name || item.row.provider || 'поставщик не указан'}</span>
                <span>{item.row.product_name || item.row.description || 'товар не указан'}</span>
                <em>{item.row.unit_price ? `${item.row.unit_price} ₽${item.row.unit ? ` / ${item.row.unit}` : ''}` : 'нет цены'}</em>
              </div>
            ))}
          </div>
        )}
      </form>
    </details>
  )
}

export function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = String(reader.result || '')
      resolve(result.includes(',') ? result.split(',').pop() : result)
    }
    reader.onerror = () => reject(new Error('Не удалось прочитать файл'))
    reader.readAsDataURL(file)
  })
}
