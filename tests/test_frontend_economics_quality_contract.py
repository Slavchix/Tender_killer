from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ECONOMICS_METRICS_SOURCE = ROOT / "web" / "src" / "TenderEconomicsMetrics.jsx"


def test_economics_metrics_uses_backend_price_quality_funnel():
    source = ECONOMICS_METRICS_SOURCE.read_text(encoding="utf-8")

    assert "economics?.price_quality" in source
    assert "priceQuality?.positions_priced" in source
    assert "priceQuality?.candidates_total" in source
    assert "qualityFunnelMetric(priceQuality)" in source
    assert 'label="проверка цен"' in source
