from __future__ import annotations

from pathlib import Path


API_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "api.js"
USE_TENDER_DOCUMENT_ANALYSIS_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "useTenderDocumentAnalysis.js"
)
USE_TENDER_ANALYSIS_SAVE_ACTIONS_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "useTenderAnalysisSaveActions.js"
)
TENDER_DETAILS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderDetails.jsx"
TENDER_WORKSPACES_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderWorkspaces.jsx"
TENDER_ANALYSIS_TAB_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderAnalysisTab.jsx"
TENDER_ANALYSIS_HISTORY_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderAnalysisHistory.jsx"
)
TENDER_ANALYSIS_DECISION_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderAnalysisDecisionBrief.jsx"
)
TENDER_ANALYSIS_SECTIONS_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderAnalysisSections.jsx"
)
ANALYSIS_OPERATOR_SECTION_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "AnalysisOperatorSection.jsx"
)
USE_TENDER_ANALYSIS_WORKSPACE_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "useTenderAnalysisWorkspace.js"
)
ANALYSIS_LEGACY_ADAPTER_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "analysisLegacyAdapter.js"
)
ANALYSIS_LEGACY_ITEM_MODEL_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "analysisLegacyItemModel.js"
)
ANALYSIS_SECTIONS_MODEL_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "analysisSectionsModel.js"
)
ANALYSIS_BACKEND_SECTIONS_MODEL_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "analysisBackendSectionsModel.js"
)
ANALYSIS_ITEM_DISPLAY_MODEL_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "analysisItemDisplayModel.js"
)
ANALYSIS_TEXT_UTILS_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "analysisTextUtils.js"
)
ANALYSIS_HISTORY_MODEL_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "analysisHistoryModel.js"
)
ANALYSIS_DECISION_MODEL_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "analysisDecisionModel.js"
)
ANALYSIS_FACT_CARD_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "AnalysisFactCard.jsx"
)
ANALYSIS_FACT_BODY_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "AnalysisFactBody.jsx"
)
ANALYSIS_FACT_SOURCE_CONTEXT_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "AnalysisFactSourceContext.jsx"
)
ANALYSIS_FACT_MODEL_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "analysisFactModel.js"
)
ANALYSIS_FACT_VIEW_MODEL_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "analysisFactViewModel.js"
)
ANALYSIS_FACT_COMPACT_TEXT_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "analysisFactCompactTextModel.js"
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


def read_css_source(path: Path, seen: set[Path] | None = None) -> str:
    seen = seen or set()
    path = path.resolve()
    if path in seen:
        return ""
    seen.add(path)
    source = path.read_text(encoding="utf-8")
    chunks = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("@import "):
            quote = "'" if "'" in stripped else '"'
            parts = stripped.split(quote)
            if len(parts) >= 3:
                chunks.append(read_css_source(path.parent / parts[1], seen))
        chunks.append(line)
    return "\n".join(chunks)


def read_styles_source() -> str:
    return "\n".join(
        (
            read_css_source(STYLES_SOURCE),
            read_css_source(STYLES_ANALYSIS_SOURCE),
            read_css_source(STYLES_ECONOMICS_SOURCE),
        )
    )


def test_tender_analysis_renders_fact_feedback_controls():
    api_source = API_SOURCE.read_text(encoding="utf-8")
    hook_source = USE_TENDER_DOCUMENT_ANALYSIS_SOURCE.read_text(encoding="utf-8")
    save_actions_source = (
        USE_TENDER_ANALYSIS_SAVE_ACTIONS_SOURCE.read_text(encoding="utf-8")
        if USE_TENDER_ANALYSIS_SAVE_ACTIONS_SOURCE.exists()
        else ""
    )
    details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    workspaces_source = TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    sections_source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")
    operator_section_source = ANALYSIS_OPERATOR_SECTION_SOURCE.read_text(encoding="utf-8")
    fact_card_source = ANALYSIS_FACT_CARD_SOURCE.read_text(encoding="utf-8")
    fact_view_model_source = ANALYSIS_FACT_VIEW_MODEL_SOURCE.read_text(encoding="utf-8")
    feedback_source = ANALYSIS_FEEDBACK_CONTROLS_SOURCE.read_text(encoding="utf-8")

    assert "export function saveAnalysisFeedback" in api_source
    assert "/analysis/feedback" in api_source
    assert "from './useTenderAnalysisSaveActions'" in hook_source
    assert "useTenderAnalysisSaveActions(tender, setAnalysis)" in hook_source
    assert "saveAnalysisFeedback" in save_actions_source
    assert "savingAnalysisFeedbackId" in hook_source
    assert "onAnalysisFeedback: saveFactFeedback" in details_source
    assert "onAnalysisFeedback," in workspaces_source
    assert "onFeedback={onAnalysisFeedback}" in analysis_source
    assert "onFeedback={onFeedback}" in sections_source
    assert "from './AnalysisFactCard'" in operator_section_source
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
    assert "feedback_comment" in fact_view_model_source
    assert "feedback_history" in fact_view_model_source


def test_tender_analysis_has_compact_mode_and_single_all_bucket():
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    sections_source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")
    operator_section_source = ANALYSIS_OPERATOR_SECTION_SOURCE.read_text(encoding="utf-8")
    workspace_hook_source = USE_TENDER_ANALYSIS_WORKSPACE_SOURCE.read_text(encoding="utf-8")
    fact_card_source = ANALYSIS_FACT_CARD_SOURCE.read_text(encoding="utf-8")
    fact_body_source = ANALYSIS_FACT_BODY_SOURCE.read_text(encoding="utf-8")
    fact_model_source = ANALYSIS_FACT_MODEL_SOURCE.read_text(encoding="utf-8")
    fact_view_model_source = ANALYSIS_FACT_VIEW_MODEL_SOURCE.read_text(encoding="utf-8")
    fact_compact_source = ANALYSIS_FACT_COMPACT_TEXT_SOURCE.read_text(encoding="utf-8")
    view_controls_source = ANALYSIS_VIEW_CONTROLS_SOURCE.read_text(encoding="utf-8")

    assert "analysisViewMode" in workspace_hook_source
    assert "from './AnalysisViewControls'" in operator_section_source
    assert "function AnalysisViewControls" not in sections_source
    assert "analysis-view-controls" in view_controls_source
    assert "analysis-mode-toggle" in view_controls_source
    assert "analysis-filter-chips" in view_controls_source
    assert "totalCount={analysisItems.length}" in operator_section_source
    assert "<span>Все</span>" in view_controls_source
    assert "activeFilter" not in sections_source
    assert "onFilterChange" not in sections_source
    assert "analysisFactFilter" not in analysis_source
    assert "analysis-hidden-facts" in operator_section_source
    assert "analysis-weak-facts" in operator_section_source
    assert "operator_summary" in fact_view_model_source
    assert "operator_check" in fact_view_model_source
    assert "weak_reason" in fact_view_model_source
    assert "item.interpretation" in fact_view_model_source
    assert "analysis-fact-detail-grid" in fact_body_source
    assert "Что найдено" in fact_view_model_source
    assert "Что означает" in fact_view_model_source
    assert "analysis-fact-line" in fact_body_source
    assert "detailParts" in fact_view_model_source
    assert "compactAnalysisFactSentence" in fact_view_model_source
    assert "item?.value" in fact_compact_source
    assert "item?.fragment" in fact_compact_source
    assert "точная формулировка в извлеченном тексте не найдена" in fact_compact_source
    assert "analysis-fact-action" not in sections_source
    assert "analysis-fact-impact" not in sections_source
    assert "open={!compact}" in operator_section_source
    assert "detailed && view.sourceDetail" in fact_card_source
    assert "detailed={!compact}" in operator_section_source


def test_tender_analysis_uses_backend_condition_groups_instead_of_frontend_semantics():
    sections_source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")
    model_source = ANALYSIS_SECTIONS_MODEL_SOURCE.read_text(encoding="utf-8")
    backend_source = ANALYSIS_BACKEND_SECTIONS_MODEL_SOURCE.read_text(encoding="utf-8")
    display_source = ANALYSIS_ITEM_DISPLAY_MODEL_SOURCE.read_text(encoding="utf-8")

    assert "from './analysisSectionsModel'" in sections_source
    assert "operatorView?.condition_groups" in model_source
    assert "backendConditionFamily" in display_source
    assert "buildBackendAnalysisSections(operatorSections, conditionGroups)" in model_source
    assert "operatorSections) ? operatorSections : []).map((section) => (" in backend_source
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


def test_analysis_sections_model_is_split_by_responsibility():
    model_source = ANALYSIS_SECTIONS_MODEL_SOURCE.read_text(encoding="utf-8")
    backend_source = ANALYSIS_BACKEND_SECTIONS_MODEL_SOURCE.read_text(encoding="utf-8")
    display_source = ANALYSIS_ITEM_DISPLAY_MODEL_SOURCE.read_text(encoding="utf-8")

    assert "from './analysisBackendSectionsModel'" in model_source
    assert "from './analysisItemDisplayModel'" in model_source
    assert "export { displayableAnalysisItems, isAnalysisFactItem }" in model_source
    assert "export function buildBackendAnalysisSections" in backend_source
    assert "function normalizeOperatorSection" in backend_source
    assert "function conditionGroupByFactId" in backend_source
    assert "export function displayableAnalysisItems" in display_source
    assert "export function isAnalysisFactItem" in display_source
    assert "function legacyAnalysisItemRank" in display_source
    assert "function normalizeOperatorSection" not in model_source
    assert "function conditionGroupByFactId" not in model_source
    assert "function displayableAnalysisItems" not in model_source
    assert "function legacyAnalysisItemRank" not in model_source


def test_tender_analysis_legacy_fallback_lives_in_adapter():
    sections_source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")
    model_source = ANALYSIS_SECTIONS_MODEL_SOURCE.read_text(encoding="utf-8")
    legacy_source = ANALYSIS_LEGACY_ADAPTER_SOURCE.read_text(encoding="utf-8")
    legacy_item_source = (
        ANALYSIS_LEGACY_ITEM_MODEL_SOURCE.read_text(encoding="utf-8")
        if ANALYSIS_LEGACY_ITEM_MODEL_SOURCE.exists()
        else ""
    )

    assert "analysisSectionItems" in sections_source
    assert "buildLegacyAnalysisSections" in model_source
    assert "from './analysisLegacyAdapter'" in model_source
    assert "function legacyMajorSections" not in sections_source
    assert "function legacyItem" not in sections_source
    assert "function fallbackOperatorAction" not in sections_source
    assert "from './analysisLegacyItemModel'" in legacy_source
    assert "export function buildLegacyAnalysisSections" in legacy_source
    assert "function legacyItem" not in legacy_source
    assert "function fallbackOperatorAction" not in legacy_source
    assert "export function legacyItem" in legacy_item_source
    assert "export function legacyAnalysisItemCount" in legacy_item_source
    assert "export function dedupeItems" in legacy_item_source
    assert "export function normalizeReasonList" in legacy_item_source


def test_tender_analysis_text_helpers_live_in_shared_module():
    sections_source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")
    model_source = ANALYSIS_SECTIONS_MODEL_SOURCE.read_text(encoding="utf-8")
    backend_source = ANALYSIS_BACKEND_SECTIONS_MODEL_SOURCE.read_text(encoding="utf-8")
    display_source = ANALYSIS_ITEM_DISPLAY_MODEL_SOURCE.read_text(encoding="utf-8")
    fact_card_source = ANALYSIS_FACT_CARD_SOURCE.read_text(encoding="utf-8")
    fact_view_model_source = ANALYSIS_FACT_VIEW_MODEL_SOURCE.read_text(encoding="utf-8")
    feedback_source = ANALYSIS_FEEDBACK_CONTROLS_SOURCE.read_text(encoding="utf-8")
    text_utils_source = ANALYSIS_TEXT_UTILS_SOURCE.read_text(encoding="utf-8")

    assert "export function cleanAnalysisText" in text_utils_source
    assert "export function normalizedAnalysisText" in text_utils_source
    assert "export function uniqueAnalysisTexts" in text_utils_source
    assert "from './analysisTextUtils'" in backend_source
    assert "from './analysisTextUtils'" in display_source
    assert "from './analysisTextUtils'" in fact_view_model_source
    assert "from './analysisTextUtils'" in feedback_source
    assert "function cleanAnalysisText" not in sections_source
    assert "function cleanAnalysisText" not in model_source
    assert "function cleanAnalysisText" not in backend_source
    assert "function cleanAnalysisText" not in display_source
    assert "function cleanAnalysisText" not in fact_card_source
    assert "function cleanAnalysisText" not in fact_view_model_source
    assert "function cleanAnalysisText" not in feedback_source
    assert "function normalizedAnalysisText" not in model_source
    assert "function normalizedAnalysisText" not in display_source
    assert "function normalizedAnalysisText" not in fact_card_source
    assert "function uniqueAnalysisTexts" not in fact_card_source


def test_tender_analysis_manual_section_selection_is_not_overridden_by_primary_section():
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    workspace_hook_source = USE_TENDER_ANALYSIS_WORKSPACE_SOURCE.read_text(encoding="utf-8")

    assert "useRef" in workspace_hook_source
    assert "userSelectedAnalysisSectionRef" in workspace_hook_source
    assert "function selectAnalysisSection" in workspace_hook_source
    assert "userSelectedAnalysisSectionRef.current = true" in workspace_hook_source
    assert "!userSelectedAnalysisSectionRef.current && primarySection" in workspace_hook_source
    assert "onSelectSection={selectAnalysisSection}" in analysis_source
    assert "onOpenSection={selectAnalysisSection}" in analysis_source


def test_tender_analysis_history_exposes_change_details():
    history_source = TENDER_ANALYSIS_HISTORY_SOURCE.read_text(encoding="utf-8")

    assert "AnalysisHistoryDetails" in history_source
    assert "analysis-history-details" in history_source
    assert "changes.added" in history_source
    assert "changes.changed" in history_source
    assert "changes.removed" in history_source
    assert "changes.feedback" in history_source
    assert "changes.documents" in history_source
    assert "changes.condition_changes" in history_source
    assert "Документы" in history_source
    assert "Изменившиеся условия" in history_source


def test_tender_analysis_history_is_split_from_tab():
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    history_source = TENDER_ANALYSIS_HISTORY_SOURCE.read_text(encoding="utf-8")
    history_model_source = ANALYSIS_HISTORY_MODEL_SOURCE.read_text(encoding="utf-8")

    assert "from './TenderAnalysisHistory'" in analysis_source
    assert "<AnalysisHistory history={analysisHistory}" in analysis_source
    assert "export function AnalysisHistory" in history_source
    assert "from './analysisHistoryModel'" in history_source
    assert "export function formatAnalysisHistoryDate" in history_model_source
    assert "export function formatConditionChange" in history_model_source
    assert "function AnalysisHistory" not in analysis_source
    assert "function AnalysisHistoryDetails" not in analysis_source
    assert "function formatConditionChange" not in analysis_source
    assert "function formatAnalysisHistoryDate" not in analysis_source


def test_tender_analysis_decision_fallback_is_split_from_component():
    decision_source = TENDER_ANALYSIS_DECISION_SOURCE.read_text(encoding="utf-8")
    decision_model_source = ANALYSIS_DECISION_MODEL_SOURCE.read_text(encoding="utf-8")

    assert "from './analysisDecisionModel'" in decision_source
    assert "buildAnalysisDecision(analysis, documents)" in decision_source
    assert "export function buildAnalysisDecision" in decision_model_source
    assert "function fallbackAnalysisDecision" in decision_model_source
    assert "function normalizeReasonList" in decision_model_source
    assert "analysisStatusLabel" in decision_model_source
    assert "formatConfidence" in decision_model_source
    assert "function fallbackAnalysisDecision" not in decision_source
    assert "function normalizeReasonList" not in decision_source
    assert "analysisStatusLabel" not in decision_source
    assert "formatConfidence" not in decision_source


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
