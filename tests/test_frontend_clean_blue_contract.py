from __future__ import annotations

from pathlib import Path

from tender_killer.encoding_guard import find_mojibake


ROOT = Path(__file__).resolve().parents[1]
APP_SOURCE = ROOT / "web" / "src" / "App.jsx"
DASHBOARD_SOURCE = ROOT / "web" / "src" / "Dashboard.jsx"
STYLES_SOURCE = ROOT / "web" / "src" / "styles.css"


def test_app_exposes_persisted_light_dark_theme_toggle():
    app_source = APP_SOURCE.read_text(encoding="utf-8")

    assert "THEME_STORAGE_KEY" in app_source
    assert "const [theme, setTheme] = useState(initialTheme)" in app_source
    assert "document.documentElement.dataset.theme = theme" in app_source
    assert "window.localStorage.setItem(THEME_STORAGE_KEY, theme)" in app_source
    assert "className=\"icon-button theme-toggle-button\"" in app_source
    assert "theme === 'dark' ? <Sun" in app_source
    assert "theme === 'dark' ? 'Светлая тема' : 'Темная тема'" in app_source
    assert find_mojibake(app_source, APP_SOURCE) == []


def test_clean_blue_tokens_are_the_only_hardcoded_hex_colors():
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")
    token_block = styles_source.split("* {", 1)[0]
    rest = styles_source.split("* {", 1)[1]

    assert ":root," in styles_source
    assert "[data-theme=\"light\"]" in styles_source
    assert "[data-theme=\"dark\"]" in styles_source
    assert "--color-bg: #F6F8FB" in token_block
    assert "--color-surface: #FFFFFF" in token_block
    assert "--color-text: #0F172A" in token_block
    assert "--color-primary: #2563EB" in token_block
    assert "--color-secondary: #0891B2" in token_block
    assert "--color-success: #16A34A" in token_block
    assert "--color-warning: #F59E0B" in token_block
    assert "--color-purple: #7C3AED" in token_block
    assert "--color-danger: #DC2626" in token_block
    assert "--color-bg: #0B1220" in token_block
    assert "--radius-card: 16px" in token_block
    assert "#" not in rest
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_dashboard_uses_queue_rail_and_work_panels():
    dashboard_source = DASHBOARD_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "DashboardQueueColumn" in dashboard_source
    assert "DashboardDeadlinePanel" in dashboard_source
    assert "DashboardDocumentProblemsPanel" in dashboard_source
    assert "DashboardWorkInProgressPanel" in dashboard_source
    assert "dashboardQueueColumns(dashboardQueues, tenders)" in dashboard_source
    assert "Разобрать" in dashboard_source
    assert "Посчитать" in dashboard_source
    assert "Проверить лимит" in dashboard_source
    assert "Готово" in dashboard_source
    assert "Срочные дедлайны" in dashboard_source
    assert "Проблемы документов" in dashboard_source
    assert "Наши закупки в работе" in dashboard_source
    assert "В работе" in dashboard_source
    assert "Готовим заявку" in dashboard_source
    assert "Завершенные" in dashboard_source
    assert ".dashboard-command-grid" in styles_source
    assert ".dashboard-queue-board" in styles_source
    assert ".dashboard-right-rail" in styles_source
    assert ".dashboard-work-tabs" in styles_source
    assert find_mojibake(dashboard_source, DASHBOARD_SOURCE) == []


def test_dashboard_cards_open_exact_tender_details():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    dashboard_source = DASHBOARD_SOURCE.read_text(encoding="utf-8")

    assert "function openTenderFromDashboard(tender)" in app_source
    assert "openTenderDetails(tender)" in app_source
    assert "onOpenTender={openTenderFromDashboard}" in app_source
    assert "onClick={() => onOpenTender(item)}" in dashboard_source
    assert "onClick={() => onOpenTender(tender)}" in dashboard_source
    assert "onClick={onOpenTenders}" not in dashboard_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(dashboard_source, DASHBOARD_SOURCE) == []
