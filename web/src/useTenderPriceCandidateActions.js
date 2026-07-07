import {
  applyTenderAutoPrices as applyTenderAutoPricesRequest,
  confirmProfilePriceCandidate as confirmProfilePriceCandidateRequest,
  confirmReadyTenderPriceCandidates as confirmReadyTenderPriceCandidatesRequest,
  rejectProfilePriceCandidate as rejectProfilePriceCandidateRequest,
  runTenderPriceDiscovery as runTenderPriceDiscoveryRequest,
  stageTenderPriceBookFeed as stageTenderPriceBookFeedRequest,
  stageTenderPriceBookFeedFile as stageTenderPriceBookFeedFileRequest,
  stageTenderPriceCandidates as stageTenderPriceCandidatesRequest,
} from './api'

const READY_PRICE_CANDIDATES_REVIEW_ID = 'ready-price-candidates-bulk'
const PRICE_CANDIDATE_STAGE_REVIEW_ID = 'price-candidates-stage'
const PRICE_DISCOVERY_RUN_ID = 'price-discovery-run'
const PRICE_AUTO_APPLY_ID = 'price-auto-apply'
const PRICE_BOOK_FEED_STAGE_ID = 'price-book-feed-stage'

export function isPriceDiscoveryJobActive(job) {
  return job?.status === 'queued' || (job?.status === 'running' && !isPriceDiscoveryJobComplete(job))
}

function isPriceDiscoveryJobComplete(job) {
  if (!job) return false
  const status = String(job.status || '').toLowerCase()
  if (status === 'succeeded' || status === 'failed') return true
  const total = Number(job.total_profiles || 0)
  const searched = Number(job.searched_count || 0)
  return status === 'running' && total > 0 && searched >= total
}

export function priceDiscoveryStatusMessage(job) {
  if (job?.status === 'manual_required') {
    return job.message || 'Крупная закупка: используй быстрые ссылки/ссылка на товар/прайс вместо активного автопоиска цен.'
  }
  if (!job?.job_id) return ''

  const staged = Number(job.staged_count || job.result?.staged_count || 0)
  const ready = Number(job.ready_count || job.result?.ready_count || 0)
  const noCandidates = Number(job.no_candidates_count || job.result?.no_candidates_count || 0)
  const searched = Number(job.searched_count || 0)
  const total = Number(job.total_profiles || 0)
  const limited = Number(job.limited_count || 0)
  const progressNote = total > 0 ? `${searched}/${total}` : `${searched}`

  if (job.status === 'failed') {
    return `Поиск цен завершился ошибкой: ${job.error || 'подробности не получены'}`
  }
  if (job.status === 'succeeded' || isPriceDiscoveryJobComplete(job)) {
    const limitNote = job.partial ? `, осталось ${limited}` : ''
    return `Поиск цен завершен: подготовлено ${staged}, готово ${ready}, без кандидатов ${noCandidates}${limitNote}`
  }
  return `Идет поиск цен: проверено ${progressNote}, подготовлено ${staged}, готово ${ready}`
}

export function useTenderPriceCandidateActions({
  tender,
  updateFromNextTender,
  setDetailStatus,
  reviewingPriceCandidateId,
  setReviewingPriceCandidateId,
  priceDiscoveryJob,
  setPriceDiscoveryJob,
}) {
  function confirmReadyPriceCandidates() {
    setReviewingPriceCandidateId(READY_PRICE_CANDIDATES_REVIEW_ID)
    setDetailStatus('')
    return confirmReadyTenderPriceCandidatesRequest(tender)
      .then((nextTender) => {
        const review = nextTender.price_candidate_bulk_review || {}
        const confirmed = Number(review.confirmed_count || 0)
        const skipped = Number(review.skipped_count || 0)
        return updateFromNextTender(nextTender, `Готовые цены приняты: ${confirmed}, пропущено: ${skipped}`)
      })
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setReviewingPriceCandidateId(null))
  }

  function stagePriceCandidates() {
    setReviewingPriceCandidateId(PRICE_CANDIDATE_STAGE_REVIEW_ID)
    setDetailStatus('')
    return stageTenderPriceCandidatesRequest(tender)
      .then((nextTender) => {
        const stage = nextTender.price_candidate_stage || {}
        const memoryStage = nextTender.price_memory_stage || {}
        const staged = Number(stage.staged_count || 0)
        const ready = Number(stage.ready_count || 0)
        const review = Number(stage.review_count || 0)
        const memory = Number(memoryStage.staged_count || 0)
        const memoryNote = memory > 0 ? `, из памяти: ${memory}` : ''
        return updateFromNextTender(nextTender, `Кандидаты цен подготовлены: ${staged}${memoryNote}, готово: ${ready}, проверить: ${review}`)
      })
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setReviewingPriceCandidateId(null))
  }

  function stagePriceBookFeed(payload) {
    setReviewingPriceCandidateId(PRICE_BOOK_FEED_STAGE_ID)
    setDetailStatus('')
    return stageTenderPriceBookFeedRequest(tender, payload)
      .then((nextTender) => {
        const feed = nextTender.price_book_feed || {}
        const staged = Number(feed.staged_count || 0)
        const matched = Number(feed.quality_report?.summary?.stageable_count || feed.matched_count || 0)
        const skipped = Number(feed.skipped_count || 0)
        const mode = feed.stage_mode ? `, режим: ${priceBookStageModeLabel(feed.stage_mode)}` : ''
        return updateFromNextTender(nextTender, `Прайс загружен: кандидатов ${staged}, совпадений ${matched}, пропущено ${skipped}${mode}`)
      })
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setReviewingPriceCandidateId(null))
  }

  function stagePriceBookFeedFile(payload) {
    setReviewingPriceCandidateId(PRICE_BOOK_FEED_STAGE_ID)
    setDetailStatus('')
    return stageTenderPriceBookFeedFileRequest(tender, payload)
      .then((nextTender) => {
        const feed = nextTender.price_book_feed || {}
        const fileImport = feed.file_import || {}
        const staged = Number(feed.staged_count || 0)
        const matched = Number(feed.quality_report?.summary?.stageable_count || feed.matched_count || 0)
        const skipped = Number(feed.skipped_count || 0)
        const fileName = fileImport.file_name || 'файл'
        return updateFromNextTender(nextTender, `Файл ${fileName}: кандидатов ${staged}, совпадений ${matched}, пропущено ${skipped}`)
      })
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setReviewingPriceCandidateId(null))
  }

  function applyAutoPrices() {
    setReviewingPriceCandidateId(PRICE_AUTO_APPLY_ID)
    setDetailStatus('')
    return applyTenderAutoPricesRequest(tender)
      .then((nextTender) => {
        const autoApply = nextTender.price_auto_apply || {}
        const applied = Number(autoApply.applied_count || 0)
        const missing = Number(autoApply.missing_cost_count || 0)
        return updateFromNextTender(nextTender, `Автоцены применены: ${applied}, без цены: ${missing}`)
      })
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setReviewingPriceCandidateId(null))
  }

  function runPriceDiscovery() {
    setReviewingPriceCandidateId(PRICE_DISCOVERY_RUN_ID)
    setDetailStatus('')
    return runTenderPriceDiscoveryRequest(tender)
      .then((nextTender) => {
        const job = nextTender.price_discovery_job || nextTender.price_discovery_run || {}
        setPriceDiscoveryJob(job)
        setDetailStatus(priceDiscoveryStatusMessage(job))
        if (!isPriceDiscoveryJobActive(job)) {
          updateFromNextTender(nextTender, priceDiscoveryStatusMessage(job))
          setReviewingPriceCandidateId(null)
        }
        return nextTender
      })
      .catch((err) => {
        setPriceDiscoveryJob(null)
        setReviewingPriceCandidateId(null)
        setDetailStatus(err.message)
        throw err
      })
  }

  function confirmPriceCandidate(profile, candidate) {
    return reviewPriceCandidate(profile, candidate, confirmProfilePriceCandidateRequest, 'Цена кандидата принята в экономику')
  }

  function rejectPriceCandidate(profile, candidate) {
    return reviewPriceCandidate(profile, candidate, rejectProfilePriceCandidateRequest, 'Цена кандидата отклонена')
  }

  function reviewPriceCandidate(profile, candidate, request, message) {
    if (!profile?.position_index || !candidate?.id) return null
    setReviewingPriceCandidateId(candidate.id)
    setDetailStatus('')
    return request(tender, profile, candidate.id)
      .then((nextTender) => updateFromNextTender(nextTender, message))
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setReviewingPriceCandidateId(null))
  }

  return {
    confirmingReadyPriceCandidates: reviewingPriceCandidateId === READY_PRICE_CANDIDATES_REVIEW_ID,
    stagingPriceCandidates: reviewingPriceCandidateId === PRICE_CANDIDATE_STAGE_REVIEW_ID,
    stagingPriceBookFeed: reviewingPriceCandidateId === PRICE_BOOK_FEED_STAGE_ID,
    runningPriceDiscovery: reviewingPriceCandidateId === PRICE_DISCOVERY_RUN_ID || isPriceDiscoveryJobActive(priceDiscoveryJob),
    applyingAutoPrices: reviewingPriceCandidateId === PRICE_AUTO_APPLY_ID,
    confirmReadyPriceCandidates,
    stagePriceCandidates,
    stagePriceBookFeed,
    stagePriceBookFeedFile,
    applyAutoPrices,
    runPriceDiscovery,
    confirmPriceCandidate,
    rejectPriceCandidate,
  }
}

function priceBookStageModeLabel(mode) {
  if (mode === 'confident') return 'только уверенные'
  if (mode === 'review') return 'только спорные'
  if (mode === 'errors') return 'только ошибки'
  return 'все строки'
}
