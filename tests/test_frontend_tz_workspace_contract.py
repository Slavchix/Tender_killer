from __future__ import annotations

from pathlib import Path


WEB_SRC = Path("web/src")


def test_tz_analysis_secondary_tools_are_collapsed_and_localized():
    source = (WEB_SRC / "TenderAnalysisTab.jsx").read_text(encoding="utf-8")
    secondary_source = (WEB_SRC / "TenderAnalysisSecondaryDrawers.jsx").read_text(encoding="utf-8")
    workflow_source = (WEB_SRC / "TenderAnalysisWorkflowPanel.jsx").read_text(encoding="utf-8")
    playbooks_source = (WEB_SRC / "TenderAnalysisPlaybooksPanel.jsx").read_text(encoding="utf-8")

    assert "AnalysisSecondaryDrawers" in source
    assert "function AnalysisWorkflowPanel" not in source
    assert "function AnalysisQuestionsPanel" not in source
    assert "function AnalysisPlaybooksPanel" not in source
    assert "analysis-secondary-drawer" in secondary_source
    assert "Проверка ТЗ и подсказки" in secondary_source
    assert "Контрольные вопросы" in secondary_source
    assert "Подсказки оператора" in playbooks_source
    assert "Рабочий процесс ТЗ" in workflow_source
    assert "Скачать отчет" in source
    assert "оператор" in playbooks_source or "оператор" in workflow_source
    assert "{entry.actor || 'operator'}" not in workflow_source
    assert "Workflow ТЗ" not in secondary_source + workflow_source
    assert "AI-вопросы" not in secondary_source
    assert "<span><BookOpenCheck size={15} /> Playbooks</span>" not in playbooks_source
    assert "или playbook" not in secondary_source + playbooks_source


def test_tz_analysis_source_details_are_deduplicated():
    tab_source = (WEB_SRC / "TenderAnalysisTab.jsx").read_text(encoding="utf-8")
    evidence_model_source = (WEB_SRC / "TenderAnalysisEvidenceModel.js").read_text(encoding="utf-8")
    evidence_drilldown_source = (WEB_SRC / "TenderAnalysisEvidenceDrilldown.jsx").read_text(encoding="utf-8")
    fact_source_context_source = (WEB_SRC / "AnalysisFactSourceContext.jsx").read_text(encoding="utf-8")
    fact_view_model_source = (WEB_SRC / "analysisFactViewModel.js").read_text(encoding="utf-8")
    fact_source_model_source = (WEB_SRC / "analysisFactSourceModel.js").read_text(encoding="utf-8")

    assert "uniqueEvidenceNotes" not in tab_source
    assert "uniqueEvidenceNotes" in evidence_model_source
    assert "uniqueEvidenceNotes" in evidence_drilldown_source
    assert "uniqueAnalysisTexts" in fact_view_model_source
    assert "uniqueAnalysisTexts" in fact_source_model_source
    assert "sourceNotes.map" in fact_source_context_source


def test_tz_analysis_evidence_drilldown_is_delegated():
    tab_source = (WEB_SRC / "TenderAnalysisTab.jsx").read_text(encoding="utf-8")
    workspace_hook_source = (WEB_SRC / "useTenderAnalysisWorkspace.js").read_text(encoding="utf-8")
    evidence_model_source = (WEB_SRC / "TenderAnalysisEvidenceModel.js").read_text(encoding="utf-8")
    evidence_drilldown_source = (WEB_SRC / "TenderAnalysisEvidenceDrilldown.jsx").read_text(encoding="utf-8")

    assert "from './TenderAnalysisEvidenceDrilldown'" in tab_source
    assert "from './TenderAnalysisEvidenceModel'" in workspace_hook_source
    assert "function AnalysisEvidenceDrilldownPanel" not in tab_source
    assert "function resolveEvidenceDrilldown" not in tab_source
    assert "export function AnalysisEvidenceDrilldownPanel" in evidence_drilldown_source
    assert "export function resolveEvidenceDrilldown" in evidence_model_source
