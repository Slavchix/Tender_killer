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
TENDER_ANALYSIS_PASSPORT_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderAnalysisPassport.jsx"
)
STYLES_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "styles.css"


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
    assert "XCircle" in sections_source
    assert "Ban" in sections_source
    assert "ClipboardCheck" in sections_source
    assert "верно" in sections_source
    assert "неверно" in sections_source
    assert "не относится к заявке" in sections_source
    assert "требует ручной проверки" in sections_source
    assert "analysis-feedback-comment" in sections_source
    assert "feedback_comment" in sections_source
    assert "feedback_history" in sections_source
    assert "analysis-feedback-actions" in sections_source
    assert "feedback_state" in sections_source


def test_tender_analysis_has_compact_mode_and_single_all_bucket():
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    sections_source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")

    assert "analysisViewMode" in analysis_source
    assert "analysis-view-controls" in sections_source
    assert "analysis-mode-toggle" in sections_source
    assert "analysis-filter-chips" in sections_source
    assert "totalCount={analysisItems.length}" in sections_source
    assert "<span>Все</span>" in sections_source
    assert "activeFilter" not in sections_source
    assert "onFilterChange" not in sections_source
    assert "analysisFactFilter" not in analysis_source
    assert "analysis-hidden-facts" in sections_source
    assert "analysis-weak-facts" in sections_source
    assert "operator_summary" in sections_source
    assert "operator_check" in sections_source
    assert "weak_reason" in sections_source
    assert "item.interpretation" in sections_source
    assert "analysis-fact-detail-grid" in sections_source
    assert "Что найдено" in sections_source
    assert "Что означает" in sections_source
    assert "analysis-fact-line" in sections_source
    assert "detailParts" in sections_source
    assert "compactAnalysisFactSentence" in sections_source
    assert "item?.value" in sections_source
    assert "item?.fragment" in sections_source
    assert "точная формулировка в извлеченном тексте не найдена" in sections_source
    assert "analysis-fact-action" not in sections_source
    assert "analysis-fact-impact" not in sections_source
    assert "open={!compact}" in sections_source
    assert "detailed && sourceDetail" in sections_source
    assert "detailed={!compact}" in sections_source


def test_tender_analysis_manual_section_selection_is_not_overridden_by_primary_section():
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")

    assert "useRef" in analysis_source
    assert "userSelectedAnalysisSectionRef" in analysis_source
    assert "function selectAnalysisSection" in analysis_source
    assert "userSelectedAnalysisSectionRef.current = true" in analysis_source
    assert "!userSelectedAnalysisSectionRef.current && primarySection" in analysis_source
    assert "onSelectSection={selectAnalysisSection}" in analysis_source
    assert "onOpenSection={selectAnalysisSection}" in analysis_source


def test_tender_analysis_history_exposes_change_details():
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")

    assert "AnalysisHistoryDetails" in analysis_source
    assert "analysis-history-details" in analysis_source
    assert "changes.added" in analysis_source
    assert "changes.changed" in analysis_source
    assert "changes.removed" in analysis_source
    assert "changes.feedback" in analysis_source
    assert "changes.documents" in analysis_source
    assert "changes.condition_changes" in analysis_source
    assert "Документы" in analysis_source
    assert "Изменившиеся условия" in analysis_source


def test_tender_analysis_passport_renders_v2_compact_block():
    passport_source = TENDER_ANALYSIS_PASSPORT_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "passport.summary_block" in passport_source
    assert "analysis-passport-compact" in passport_source
    assert "analysis-passport-list" in passport_source
    assert "Документы готовы/не готовы" in passport_source
    assert "Ключевые условия" in passport_source
    assert "Красные флаги" in passport_source
    assert "Противоречия" in passport_source
    assert "Ожидаемые условия не найдены" in passport_source
    assert "Итог" in passport_source
    assert "analysis-passport-compact" in styles_source
