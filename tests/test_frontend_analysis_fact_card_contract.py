from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_FACT_CARD_SOURCE = ROOT / "web" / "src" / "AnalysisFactCard.jsx"
ANALYSIS_FACT_MODEL_SOURCE = ROOT / "web" / "src" / "analysisFactModel.js"
TENDER_ANALYSIS_SECTIONS_SOURCE = ROOT / "web" / "src" / "TenderAnalysisSections.jsx"


def test_analysis_fact_card_delegates_fact_metadata_to_model():
    card_source = ANALYSIS_FACT_CARD_SOURCE.read_text(encoding="utf-8")
    sections_source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")
    model_source = ANALYSIS_FACT_MODEL_SOURCE.read_text(encoding="utf-8")

    assert "from './analysisFactModel'" in card_source
    assert "from './analysisFactModel'" in sections_source
    assert "export function isWeakAnalysisFact" in model_source
    assert "export function compactAnalysisFactSentence" in model_source
    assert "export function analysisSourceBinding" in model_source
    assert "export function analysisEvidenceQuality" in model_source
    assert "function analysisSourceBinding" not in card_source
    assert "function analysisEvidenceQuality" not in card_source
    assert "export function isWeakAnalysisFact" not in card_source
