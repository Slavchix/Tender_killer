import { useMemo, useState } from 'react'
import { BestPriceCandidate } from './TenderEconomicsBestPriceCandidate'
import { PriceCandidateCard } from './TenderEconomicsPriceCandidateCard'
import { tenderReferenceUnitPrice } from './TenderEconomicsPriceComparison'
import { candidateQueueBuckets } from './TenderEconomicsPriceCandidateModel'

// PriceCandidateCard owns candidateNeedsManualPrice and TenderEconomicsPriceCandidatePassport rendering.
export function PriceCandidateQueue({
  profile,
  price_candidates = [],
  reviewingPriceCandidateId = null,
  onConfirm,
  onReject,
}) {
  const buckets = useMemo(() => candidateQueueBuckets(price_candidates), [price_candidates])
  const [activeBucket, setActiveBucket] = useState('ready')
  const preferredBucket = buckets.ready.length ? 'ready' : buckets.review.length ? 'review' : 'blocked'
  const selectedBucket = buckets[activeBucket]?.length ? activeBucket : preferredBucket
  const visibleCandidates = buckets[selectedBucket] || []
  const queuedCandidateCount = buckets.ready.length + buckets.review.length + buckets.blocked.length
  const bestCandidate = buckets.ready[0] || buckets.review[0] || buckets.blocked[0] || null
  if (!queuedCandidateCount) return null
  const tenderUnitPrice = tenderReferenceUnitPrice(profile)

  return (
    <div className="price-candidates-list price-candidate-queue">
      <div className="price-candidates-heading">
        <span>Кандидаты цен</span>
        <em>{queuedCandidateCount}</em>
      </div>
      {bestCandidate && (
        <BestPriceCandidate
          busy={reviewingPriceCandidateId === bestCandidate.id}
          candidate={bestCandidate}
          onConfirm={onConfirm}
          profile={profile}
          tenderUnitPrice={tenderUnitPrice}
        />
      )}
      <div className="candidate-queue-tabs" aria-label="Очередь кандидатов цен">
        {[
          ['ready', 'Готовые', buckets.ready.length],
          ['review', 'Проверить', buckets.review.length],
          ['blocked', 'Блок', buckets.blocked.length],
        ].map(([id, label, count]) => (
          <button
            className={selectedBucket === id ? 'active' : ''}
            disabled={count === 0}
            key={id}
            onClick={() => setActiveBucket(id)}
            type="button"
          >
            {label} <span>{count}</span>
          </button>
        ))}
      </div>
      {visibleCandidates.map((candidate) => (
        <PriceCandidateCard
          busy={reviewingPriceCandidateId === candidate.id}
          candidate={candidate}
          key={candidate.id || `${candidate.source_url || candidate.product_name}-${candidate.unit_price}`}
          onConfirm={onConfirm}
          onReject={onReject}
          profile={profile}
          tenderUnitPrice={tenderUnitPrice}
        />
      ))}
    </div>
  )
}
