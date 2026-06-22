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
    sections_source = (WEB_SRC / "TenderAnalysisSections.jsx").read_text(encoding="utf-8")

    assert "uniqueEvidenceNotes" in tab_source
    assert "uniqueAnalysisTexts" in sections_source
    assert "sourceNotes.map" in sections_source
