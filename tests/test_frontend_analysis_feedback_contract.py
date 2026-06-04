from __future__ import annotations

from pathlib import Path


API_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "api.js"
USE_TENDER_DOCUMENT_ANALYSIS_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "useTenderDocumentAnalysis.js"
)
TENDER_DETAILS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderDetails.jsx"
TENDER_WORKSPACES_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderWorkspaces.jsx"
TENDER_ANALYSIS_TAB_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderAnalysisTab.jsx"
TENDER_ANALYSIS_SECTIONS_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderAnalysisSections.jsx"
)


def test_tender_analysis_renders_fact_feedback_controls():
    api_source = API_SOURCE.read_text(encoding="utf-8")
    hook_source = USE_TENDER_DOCUMENT_ANALYSIS_SOURCE.read_text(encoding="utf-8")
    details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    workspaces_source = TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    sections_source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")

    assert "export function saveAnalysisFeedback" in api_source
    assert "/analysis/feedback" in api_source
    assert "saveAnalysisFeedback" in hook_source
    assert "savingAnalysisFeedbackId" in hook_source
    assert "onAnalysisFeedback: saveFactFeedback" in details_source
    assert "onAnalysisFeedback," in workspaces_source
    assert "onFeedback={onAnalysisFeedback}" in analysis_source
    assert "onFeedback={onFeedback}" in sections_source
    assert "CheckCircle2" in sections_source
    assert "Star" in sections_source
    assert "ShieldOff" in sections_source
    assert "EyeOff" in sections_source
    assert "analysis-feedback-actions" in sections_source
    assert "feedback_state" in sections_source
