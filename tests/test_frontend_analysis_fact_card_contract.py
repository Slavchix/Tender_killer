from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_FACT_CARD_SOURCE = ROOT / "web" / "src" / "AnalysisFactCard.jsx"
ANALYSIS_FACT_BODY_SOURCE = ROOT / "web" / "src" / "AnalysisFactBody.jsx"
ANALYSIS_FACT_SOURCE_CONTEXT_SOURCE = ROOT / "web" / "src" / "AnalysisFactSourceContext.jsx"
ANALYSIS_FACT_MODEL_SOURCE = ROOT / "web" / "src" / "analysisFactModel.js"
ANALYSIS_FACT_VIEW_MODEL_SOURCE = ROOT / "web" / "src" / "analysisFactViewModel.js"
ANALYSIS_FACT_COMPACT_TEXT_SOURCE = ROOT / "web" / "src" / "analysisFactCompactTextModel.js"
ANALYSIS_FACT_SOURCE_MODEL_SOURCE = ROOT / "web" / "src" / "analysisFactSourceModel.js"
ANALYSIS_FACT_SOURCE_LABELS_SOURCE = ROOT / "web" / "src" / "analysisFactSourceLabels.js"
ANALYSIS_FACT_TAG_MODEL_SOURCE = ROOT / "web" / "src" / "analysisFactTagModel.js"
TENDER_ANALYSIS_SECTIONS_SOURCE = ROOT / "web" / "src" / "TenderAnalysisSections.jsx"


def test_analysis_fact_card_delegates_fact_metadata_to_model():
    card_source = ANALYSIS_FACT_CARD_SOURCE.read_text(encoding="utf-8")
    sections_source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")
    model_source = ANALYSIS_FACT_MODEL_SOURCE.read_text(encoding="utf-8")
    view_model_source = ANALYSIS_FACT_VIEW_MODEL_SOURCE.read_text(encoding="utf-8")

    assert "from './analysisFactViewModel'" in card_source
    assert "from './analysisFactModel'" in view_model_source
    assert "from './analysisFactModel'" in sections_source
    assert "export function isWeakAnalysisFact" in model_source
    assert "compactAnalysisFactSentence" in model_source
    assert "analysisSourceBinding" in model_source
    assert "analysisEvidenceQuality" in model_source
    assert "function analysisSourceBinding" not in card_source
    assert "function analysisEvidenceQuality" not in card_source
    assert "export function isWeakAnalysisFact" not in card_source


def test_analysis_fact_model_is_split_by_responsibility():
    model_source = ANALYSIS_FACT_MODEL_SOURCE.read_text(encoding="utf-8")
    compact_source = ANALYSIS_FACT_COMPACT_TEXT_SOURCE.read_text(encoding="utf-8")
    source_model_source = ANALYSIS_FACT_SOURCE_MODEL_SOURCE.read_text(encoding="utf-8")
    tag_model_source = ANALYSIS_FACT_TAG_MODEL_SOURCE.read_text(encoding="utf-8")

    assert "from './analysisFactCompactTextModel'" in model_source
    assert "from './analysisFactSourceModel'" in model_source
    assert "from './analysisFactTagModel'" in model_source
    assert "export { compactAnalysisFactSentence }" in model_source
    assert "export { analysisItemTags }" in model_source
    assert "export function compactAnalysisFactSentence" in compact_source
    assert "export function analysisSourceBinding" in source_model_source
    assert "export function analysisEvidenceQuality" in source_model_source
    assert "export function analysisItemTags" in tag_model_source
    assert "function sourceTopicLabel" not in model_source
    assert "function priceImpactLabel" not in model_source
    assert "function isSpecificCompactFactText" not in model_source


def test_analysis_fact_source_model_is_split_by_labels():
    source_model_source = ANALYSIS_FACT_SOURCE_MODEL_SOURCE.read_text(encoding="utf-8")
    labels_source = ANALYSIS_FACT_SOURCE_LABELS_SOURCE.read_text(encoding="utf-8")

    assert "from './analysisFactSourceLabels'" in source_model_source
    assert "export function sourceBindingLabel" in labels_source
    assert "export function confidenceLevelLabel" in labels_source
    assert "export function evidenceQualityLabel" in labels_source
    assert "export function sourceAuthorityLabel" in labels_source
    assert "export function sourceTopicLabel" in labels_source
    assert "export function sourceDocumentRoleLabel" in labels_source
    assert "function sourceBindingLabel" not in source_model_source
    assert "function confidenceLevelLabel" not in source_model_source
    assert "function evidenceQualityLabel" not in source_model_source
    assert "function sourceTopicLabel" not in source_model_source


def test_analysis_fact_card_is_split_by_responsibility():
    card_source = ANALYSIS_FACT_CARD_SOURCE.read_text(encoding="utf-8")
    body_source = ANALYSIS_FACT_BODY_SOURCE.read_text(encoding="utf-8")
    source_context_source = ANALYSIS_FACT_SOURCE_CONTEXT_SOURCE.read_text(encoding="utf-8")
    view_model_source = ANALYSIS_FACT_VIEW_MODEL_SOURCE.read_text(encoding="utf-8")

    assert "from './AnalysisFactBody'" in card_source
    assert "from './AnalysisFactSourceContext'" in card_source
    assert "from './analysisFactViewModel'" in card_source
    assert "export function AnalysisFactBody" in body_source
    assert "export function AnalysisFactSourceContext" in source_context_source
    assert "export function buildAnalysisFactView" in view_model_source
    assert "feedbackHistoryText" in body_source
    assert "analysis-feedback-history" in body_source
    assert "analysis-fact-detail-grid" in body_source
    assert "analysis-source-context" in source_context_source
    assert "sourceNotes.map" in source_context_source
    assert "compactAnalysisFactSentence" in view_model_source
    assert "analysisSourceBinding" in view_model_source
    assert "uniqueAnalysisTexts" in view_model_source
    assert "detailParts" in view_model_source
    assert "feedbackHistoryText" not in card_source
    assert "analysis-fact-detail-grid" not in card_source
    assert "analysis-source-context" not in card_source
    assert "sourceNotes.map" not in card_source
    assert "compactAnalysisFactSentence" not in card_source
