from pathlib import Path


WEB_SRC = Path(__file__).resolve().parents[1] / "web" / "src"


def test_analysis_secondary_styles_are_split_from_base_analysis_css():
    app_source = (WEB_SRC / "App.jsx").read_text(encoding="utf-8")
    base_source = (WEB_SRC / "styles.analysis.css").read_text(encoding="utf-8")
    secondary_source = (WEB_SRC / "styles.analysis.secondary.css").read_text(encoding="utf-8")

    assert "import './styles.analysis.secondary.css'" in app_source
    assert ".analysis-secondary-drawer" in secondary_source
    assert ".analysis-workflow-panel" in secondary_source
    assert ".analysis-playbook-sources" in secondary_source
    assert ".analysis-saas-panel-head" in secondary_source
    assert ".analysis-secondary-drawer" not in base_source
    assert ".analysis-workflow-panel" not in base_source
    assert ".analysis-playbook-sources" not in base_source
