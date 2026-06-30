from __future__ import annotations

from pathlib import Path


WEB_SRC = Path("web/src")


def test_tz_analysis_secondary_tools_are_collapsed_and_localized():
    source = (WEB_SRC / "TenderAnalysisTab.jsx").read_text(encoding="utf-8")

    assert "analysis-secondary-drawer" in source
    assert "Проверка ТЗ и подсказки" in source
    assert "Контрольные вопросы" in source
    assert "Подсказки оператора" in source
    assert "Рабочий процесс ТЗ" in source
    assert "Скачать отчет" in source
    assert "оператор" in source
    assert "{entry.actor || 'operator'}" not in source
    assert "Workflow ТЗ" not in source
    assert "AI-вопросы" not in source
    assert "<span><BookOpenCheck size={15} /> Playbooks</span>" not in source
    assert "или playbook" not in source


def test_tz_analysis_source_details_are_deduplicated():
    tab_source = (WEB_SRC / "TenderAnalysisTab.jsx").read_text(encoding="utf-8")
    evidence_model_source = (WEB_SRC / "TenderAnalysisEvidenceModel.js").read_text(encoding="utf-8")
    evidence_drilldown_source = (WEB_SRC / "TenderAnalysisEvidenceDrilldown.jsx").read_text(encoding="utf-8")
    fact_card_source = (WEB_SRC / "AnalysisFactCard.jsx").read_text(encoding="utf-8")
    fact_model_source = (WEB_SRC / "analysisFactModel.js").read_text(encoding="utf-8")

    assert "uniqueEvidenceNotes" not in tab_source
    assert "uniqueEvidenceNotes" in evidence_model_source
    assert "uniqueEvidenceNotes" in evidence_drilldown_source
    assert "uniqueAnalysisTexts" in fact_card_source
    assert "uniqueAnalysisTexts" in fact_model_source
    assert "sourceNotes.map" in fact_card_source


def test_tz_analysis_evidence_drilldown_is_delegated():
    tab_source = (WEB_SRC / "TenderAnalysisTab.jsx").read_text(encoding="utf-8")
    evidence_model_source = (WEB_SRC / "TenderAnalysisEvidenceModel.js").read_text(encoding="utf-8")
    evidence_drilldown_source = (WEB_SRC / "TenderAnalysisEvidenceDrilldown.jsx").read_text(encoding="utf-8")

    assert "from './TenderAnalysisEvidenceDrilldown'" in tab_source
    assert "from './TenderAnalysisEvidenceModel'" in tab_source
    assert "function AnalysisEvidenceDrilldownPanel" not in tab_source
    assert "function resolveEvidenceDrilldown" not in tab_source
    assert "export function AnalysisEvidenceDrilldownPanel" in evidence_drilldown_source
    assert "export function resolveEvidenceDrilldown" in evidence_model_source
