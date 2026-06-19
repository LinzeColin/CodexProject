import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_visual_baseline_declares_required_viewports_and_regions():
    baseline = json.loads(_text(WEB_ROOT / "tests" / "visual-baseline.json"))

    assert baseline["schema"] == "PFIOSWebShellVisualBaselineV1"
    assert baseline["screenshot_artifact_prefix"] == "pfi-web-shell"
    assert baseline["min_click_target_px"] == 44
    assert {item["name"] for item in baseline["viewports"]} == {"desktop", "tablet", "mobile"}
    desktop = next(item for item in baseline["viewports"] if item["name"] == "desktop")
    assert desktop["expected_regions"] == ["top-bar", "side-nav", "workspace", "evidence-drawer"]


def test_visual_tokens_support_readable_light_and_dark_shell():
    css = _text(WEB_ROOT / "styles" / "tokens.css")

    assert ":root" in css
    assert "@media (prefers-color-scheme: dark)" in css
    assert "--pfi-bg:" in css
    assert "--pfi-surface:" in css
    assert "--pfi-ink:" in css
    assert "--pfi-blue:" in css
    assert "--pfi-teal:" in css
    assert "--pfi-amber:" in css
    assert "--pfi-red:" in css
    assert "linear-gradient" not in css
    assert "gradient" not in css
    assert "orb" not in css
    assert "bokeh" not in css


def test_visual_layout_has_stable_shell_dimensions_and_canvas_chart_asset():
    html = _text(WEB_ROOT / "index.html")
    css = _text(WEB_ROOT / "styles" / "tokens.css")
    js = _text(WEB_ROOT / "app" / "shell.js")

    assert "grid-template-columns: 212px minmax(0, 1fr) 320px;" in css
    assert "grid-template-rows: 64px minmax(0, 1fr);" in css
    assert "min-height: var(--pfi-target);" in css
    assert '<canvas id="market-sparkline"' in html
    assert "drawSparkline" in js
    assert "canvas.getContext" in js


def test_visual_state_styles_cover_loading_error_drawer_and_compact_table():
    html = _text(WEB_ROOT / "index.html")
    css = _text(WEB_ROOT / "styles" / "tokens.css")

    assert ".skeleton-row" in css
    assert ".inline-error" in css
    assert ".toast" in css
    assert ".evidence-drawer" in css
    assert ".compact-table" in css
    assert ".status-pill" in css
    assert "data-skeleton" in html
    assert "data-error-banner" in html
    assert "data-toast" in html
