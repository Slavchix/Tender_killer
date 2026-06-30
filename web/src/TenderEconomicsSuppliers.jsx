import { PriceCandidateQueue } from './TenderEconomicsPriceCandidateQueue'
import { SupplierOptionsList } from './TenderEconomicsSupplierOptions'
import { candidateQueueBuckets } from './TenderEconomicsPriceCandidateModel'

export function ProductSupplierOptionsForm({
  profile,
  onSelect,
  onPriceCandidateConfirm,
  onPriceCandidateReject,
  saving = false,
  reviewingPriceCandidateId = null,
}) {
  const supplierOptions = Array.isArray(profile?.raw_payload?.supplier_options)
    ? profile.raw_payload.supplier_options
    : []
  const priceCandidates = Array.isArray(profile?.price_candidates) ? profile.price_candidates : []
  const candidateBuckets = candidateQueueBuckets(priceCandidates)
  const queuedCandidateCount = candidateBuckets.ready.length + candidateBuckets.review.length + candidateBuckets.blocked.length
  const showSupplierOptions = supplierOptions.length > 0 && queuedCandidateCount === 0
  const showEmptyState = queuedCandidateCount === 0 && supplierOptions.length === 0

  return (
    <section className="profile-block supplier-options-block">
      <PriceCandidateQueue
        profile={profile}
        price_candidates={priceCandidates}
        reviewingPriceCandidateId={reviewingPriceCandidateId}
        onConfirm={(candidate) => onPriceCandidateConfirm?.(profile, candidate)}
        onReject={(candidate) => onPriceCandidateReject?.(profile, candidate)}
      />
      {showSupplierOptions && (
        <SupplierOptionsList
          profile={profile}
          supplierOptions={supplierOptions}
          saving={saving}
          onSelect={(optionIndex) => onSelect?.(profile, optionIndex)}
        />
      )}
      {showEmptyState && <PriceCandidatesEmptyState />}
    </section>
  )
}

function PriceCandidatesEmptyState() {
  return (
    <div className="price-candidates-empty">
      <strong>Кандидатов цен пока нет</strong>
      <p>Подготовь быстрые ссылки, вставь ссылку на товар или внеси цену из прайса/КП после проверки.</p>
    </div>
  )
}
