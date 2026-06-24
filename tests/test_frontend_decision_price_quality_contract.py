from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECISION_STRIP_SOURCE = ROOT / "web" / "src" / "TenderDecisionStrip.jsx"


def test_decision_strip_exposes_price_quality_review_counts():
    source = DECISION_STRIP_SOURCE.read_text(encoding="utf-8")

    assert "priceQualityText(decisionMetrics)" in source
    assert "price_candidates_review" in source
    assert "price_candidates_blocked" in source
    assert 'label="проверка цен"' in source
