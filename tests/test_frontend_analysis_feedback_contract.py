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
ANALYSIS_LEGACY_ADAPTER_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "analysisLegacyAdapter.js"
)
ANALYSIS_SECTIONS_MODEL_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "analysisSectionsModel.js"
)
ANALYSIS_TEXT_UTILS_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "analysisTextUtils.js"
)
ANALYSIS_FACT_CARD_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "AnalysisFactCard.jsx"
)
ANALYSIS_FEEDBACK_CONTROLS_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "AnalysisFeedbackControls.jsx"
)
ANALYSIS_VIEW_CONTROLS_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "AnalysisViewControls.jsx"
)
TENDER_ANALYSIS_PASSPORT_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderAnalysisPassport.jsx"
)
STYLES_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "styles.css"
STYLES_ANALYSIS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "styles.analysis.css"
STYLES_ECONOMICS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "styles.economics.css"


def read_styles_source() -> str:
    return "\n".join(
        (
            STYLES_SOURCE.read_text(encoding="utf-8"),
            STYLES_ANALYSIS_SOURCE.read_text(encoding="utf-8"),
            STYLES_ECONOMICS_SOURCE.read_text(encoding="utf-8"),
        )
    )


def test_tender_analysis_renders_fact_feedback_controls():
    api_source = API_SOURCE.read_text(encoding="utf-8")
    hook_source = USE_TENDER_DOCUMENT_ANALYSIS_SOURCE.read_text(encoding="utf-8")
    details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    workspaces_source = TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    sections_source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")
    fact_card_source = ANALYSIS_FACT_CARD_SOURCE.read_text(encoding="utf-8")
    feedback_source = ANALYSIS_FEEDBACK_CONTROLS_SOURCE.read_text(encoding="utf-8")

    assert "export function saveAnalysisFeedback" in api_source
    assert "/analysis/feedback" in api_source
    assert "saveAnalysisFeedback" in hook_source
    assert "savingAnalysisFeedbackId" in hook_source
    assert "onAnalysisFeedback: saveFactFeedback" in details_source
    assert "onAnalysisFeedback," in workspaces_source
    assert "onFeedback={onAnalysisFeedback}" in analysis_source
    assert "onFeedback={onFeedback}" in sections_source
    assert "from './AnalysisFactCard'" in sections_source
    assert "function AnalysisFactCard" not in sections_source
    assert "function AnalysisFeedbackControls" not in sections_source
    assert "CheckCircle2" in feedback_source
    assert "XCircle" in feedback_source
    assert "Ban" in feedback_source
    assert "ClipboardCheck" in feedback_source
    assert "верно" in feedback_source
    assert "неверно" in feedback_source
    assert "не относится к заявке" in feedback_source
    assert "требует ручной проверки" in feedback_source
    assert "analysis-feedback-comment" in feedback_source
    assert "analysis-feedback-actions" in feedback_source
    assert "feedback_state" in feedback_source
    assert "feedback_comment" in fact_card_source
    assert "feedback_history" in fact_card_source


def test_tender_analysis_has_compact_mode_and_single_all_bucket():
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    sections_source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")
    fact_card_source = ANALYSIS_FACT_CARD_SOURCE.read_text(encoding="utf-8")
    view_controls_source = ANALYSIS_VIEW_CONTROLS_SOURCE.read_text(encoding="utf-8")

    assert "analysisViewMode" in analysis_source
    assert "from './AnalysisViewControls'" in sections_source
    assert "function AnalysisViewControls" not in sections_source
    assert "analysis-view-controls" in view_controls_source
    assert "analysis-mode-toggle" in view_controls_source
    assert "analysis-filter-chips" in view_controls_source
    assert "totalCount={analysisItems.length}" in sections_source
    assert "<span>Все</span>" in view_controls_source
    assert "activeFilter" not in sections_source
    assert "onFilterChange" not in sections_source
    assert "analysisFactFilter" not in analysis_source
    assert "analysis-hidden-facts" in sections_source
    assert "analysis-weak-facts" in sections_source
    assert "operator_summary" in fact_card_source
    assert "operator_check" in fact_card_source
    assert "weak_reason" in fact_card_source
    assert "item.interpretation" in fact_card_source
    assert "analysis-fact-detail-grid" in fact_card_source
    assert "Что найдено" in fact_card_source
    assert "Что означает" in fact_card_source
    assert "analysis-fact-line" in fact_card_source
    assert "detailParts" in fact_card_source
    assert "compactAnalysisFactSentence" in fact_card_source
    assert "item?.value" in fact_card_source
    assert "item?.fragment" in fact_card_source
    assert "точная формулировка в извлеченном тексте не найдена" in fact_card_source
    assert "analysis-fact-action" not in sections_source
    assert "analysis-fact-impact" not in sections_source
    assert "open={!compact}" in sections_source
    assert "detailed && sourceDetail" in fact_card_source
    assert "detailed={!compact}" in sections_source


def test_tender_analysis_uses_backend_condition_groups_instead_of_frontend_semantics():
    sections_source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")
    model_source = ANALYSIS_SECTIONS_MODEL_SOURCE.read_text(encoding="utf-8")

    assert "from './analysisSectionsModel'" in sections_source
    assert "operatorView?.condition_groups" in model_source
    assert "backendConditionFamily" in model_source
    assert "operatorSections.map((section) => normalizeOperatorSection(section, conditionGroups))" in model_source
    assert "MAJOR_ANALYSIS_SECTIONS.map((definition) => normalizeOperatorSection" not in model_source
    assert "buildLegacyAnalysisSections(analysis, documents, MAJOR_ANALYSIS_SECTIONS)" in model_source
    assert "id: definition.id" not in model_source
    assert "function buildMajorAnalysisSections" not in sections_source
    assert "function normalizeOperatorSection" not in sections_source
    assert "function conditionGroupByFactId" not in sections_source
    assert "function displayableAnalysisItems" not in sections_source
    assert "function analysisSemanticFamily" not in sections_source
    assert "semanticAnalysisItemKey" not in sections_source
    assert "isRelevantAnalysisText" not in sections_source
    assert "meaningfulAnalysisTokens" not in sections_source


def test_tender_analysis_legacy_fallback_lives_in_adapter():
    sections_source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")
    model_source = ANALYSIS_SECTIONS_MODEL_SOURCE.read_text(encoding="utf-8")
    legacy_source = ANALYSIS_LEGACY_ADAPTER_SOURCE.read_text(encoding="utf-8")

    assert "analysisSectionItems" in sections_source
    assert "buildLegacyAnalysisSections" in model_source
    assert "from './analysisLegacyAdapter'" in model_source
    assert "function legacyMajorSections" not in sections_source
    assert "function legacyItem" not in sections_source
    assert "function fallbackOperatorAction" not in sections_source
    assert "export function buildLegacyAnalysisSections" in legacy_source
    assert "function legacyItem" in legacy_source


def test_tender_analysis_text_helpers_live_in_shared_module():
    sections_source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")
    model_source = ANALYSIS_SECTIONS_MODEL_SOURCE.read_text(encoding="utf-8")
    fact_card_source = ANALYSIS_FACT_CARD_SOURCE.read_text(encoding="utf-8")
    feedback_source = ANALYSIS_FEEDBACK_CONTROLS_SOURCE.read_text(encoding="utf-8")
    text_utils_source = ANALYSIS_TEXT_UTILS_SOURCE.read_text(encoding="utf-8")

    assert "export function cleanAnalysisText" in text_utils_source
    assert "export function normalizedAnalysisText" in text_utils_source
    assert "export function uniqueAnalysisTexts" in text_utils_source
    assert "from './analysisTextUtils'" in model_source
    assert "from './analysisTextUtils'" in fact_card_source
    assert "from './analysisTextUtils'" in feedback_source
    assert "function cleanAnalysisText" not in sections_source
    assert "function cleanAnalysisText" not in model_source
    assert "function cleanAnalysisText" not in fact_card_source
    assert "function cleanAnalysisText" not in feedback_source
    assert "function normalizedAnalysisText" not in model_source
    assert "function normalizedAnalysisText" not in fact_card_source
    assert "function uniqueAnalysisTexts" not in fact_card_source


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
    styles_source = read_styles_source()

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
