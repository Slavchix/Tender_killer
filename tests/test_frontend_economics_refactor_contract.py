from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRICE_CANDIDATE_MODEL_SOURCE = ROOT / "web" / "src" / "TenderEconomicsPriceCandidateModel.js"
PRICE_CANDIDATE_LABELS_SOURCE = ROOT / "web" / "src" / "TenderEconomicsPriceCandidateLabels.js"
PRICE_CANDIDATE_QUEUE_SOURCE = ROOT / "web" / "src" / "TenderEconomicsPriceCandidateQueue.jsx"
PRICE_CANDIDATE_CARD_SOURCE = ROOT / "web" / "src" / "TenderEconomicsPriceCandidateCard.jsx"
PRICE_CANDIDATE_PASSPORT_SOURCE = ROOT / "web" / "src" / "TenderEconomicsPriceCandidatePassport.jsx"


def test_price_candidate_labels_are_split_from_core_model():
    model_source = PRICE_CANDIDATE_MODEL_SOURCE.read_text(encoding="utf-8")
    labels_source = PRICE_CANDIDATE_LABELS_SOURCE.read_text(encoding="utf-8")
    queue_source = PRICE_CANDIDATE_QUEUE_SOURCE.read_text(encoding="utf-8")
    passport_source = PRICE_CANDIDATE_PASSPORT_SOURCE.read_text(encoding="utf-8")

    assert "from './TenderEconomicsPriceCandidateLabels'" in model_source
    assert "export function candidateQueueBuckets" in model_source
    assert "export function candidatePricingPassport" in model_source
    assert "export function priceCandidateReasonLabel" not in model_source
    assert "export function priceCandidateReasonLabel" in labels_source
    assert "export function priceCandidateFlagLabel" in labels_source
    assert "export function priceCandidateQualityLabel" in labels_source
    assert "export function formatSourceKindLabel" in labels_source
    assert "supplierConfidenceLabel" in labels_source
    assert "supplierConfidenceLabel" not in model_source
    assert "from './TenderEconomicsPriceCandidateModel'" in queue_source
    assert "from './TenderEconomicsPriceCandidateModel'" in passport_source


def test_price_candidate_card_is_split_from_queue_shell():
    queue_source = PRICE_CANDIDATE_QUEUE_SOURCE.read_text(encoding="utf-8")
    card_source = PRICE_CANDIDATE_CARD_SOURCE.read_text(encoding="utf-8")

    assert "from './TenderEconomicsPriceCandidateCard'" in queue_source
    assert "export function PriceCandidateCard" in card_source
    assert "visibleCandidates.map((candidate) => (" in queue_source
    assert "<PriceCandidateCard" in queue_source
    assert "price-candidate-row" not in queue_source
    assert "price-candidate-row" in card_source
    assert "CandidatePricePassport" not in queue_source
    assert "CandidatePricePassport" in card_source
    assert "CandidateDecisionTrace" not in queue_source
    assert "CandidateDecisionTrace" in card_source
    assert "priceCandidateReasonItems" not in queue_source
    assert "priceCandidateReasonItems" in card_source
