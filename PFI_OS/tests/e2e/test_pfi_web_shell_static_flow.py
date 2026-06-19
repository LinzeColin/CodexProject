from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_workspace_switching_is_local_state_without_full_page_reload():
    html = _text(WEB_ROOT / "index.html")
    js = _text(WEB_ROOT / "app" / "shell.js")

    assert "setActiveWorkspace" in js
    assert "writeContext({ ...currentContext(), workspace: workspaceId })" in js
    assert "main.dataset.activeWorkspace = workspaceId" in js
    assert "location.reload" not in js
    assert "window.location" not in js
    assert "href=\"/\"" not in html
    assert 'data-active-workspace="home"' in html


def test_homepage_summary_read_model_updates_cards_table_and_evidence_drawer():
    html = _text(WEB_ROOT / "index.html")
    js = _text(WEB_ROOT / "app" / "shell.js")

    assert 'id="pfi-home-summary"' in html
    assert "readHomeSummary" in js
    assert "applyHomeSummary(readHomeSummary())" in js
    assert "applyDecisionRows" in js
    assert "applyEvidenceDrawer" in js
    assert "data-home-card" in html
    assert "data-home-decision-rows" in html
    assert "data-evidence-field" in html
    assert "PFIOSHomeSummaryV1" in html


def test_response_feedback_acceptance_states_are_wired():
    html = _text(WEB_ROOT / "index.html")
    js = _text(WEB_ROOT / "app" / "shell.js")

    assert "instant: 100" in js
    assert "skeleton: 300" in js
    assert "stepped: 1000" in js
    assert "background: 10000" in js
    assert "setPressedFeedback" in js
    assert "requestAnimationFrame" in js
    assert "data-skeleton" in html
    assert "data-error-banner" in html
    assert "data-retry" in html
    assert "data-cache-fallback" in html
    assert "showRecoverableError" in js
    assert "Cached fallback is active" in js
    assert "Background job PFI-" in js


def test_task_center_evidence_drawer_and_command_palette_are_reachable():
    html = _text(WEB_ROOT / "index.html")
    js = _text(WEB_ROOT / "app" / "shell.js")

    assert "data-task-center" in html
    assert "data-task-toggle" in html
    assert "toggleTaskCenter" in js
    assert "data-evidence-drawer" in html
    assert "data-evidence-toggle" in html
    assert "setEvidenceDrawer" in js
    assert "data-command-palette" in html
    assert "openCommandPalette" in js
    assert "event.key.toLowerCase() === \"k\"" in js
    assert "Escape" in js


def test_compact_table_controls_have_filter_sort_and_export_interfaces():
    html = _text(WEB_ROOT / "index.html")
    js = _text(WEB_ROOT / "app" / "shell.js")

    assert "compact-table" in html
    assert "data-table-filter" in html
    assert "data-table-sort" in html
    assert "data-table-export" in html
    assert "filterRows" in js
    assert "sortRows" in js
    assert "exportRows" in js
    assert "pfi-decision-queue.json" in js


def test_accessibility_contract_covers_keyboard_focus_and_named_regions():
    html = _text(WEB_ROOT / "index.html")
    css = _text(WEB_ROOT / "styles" / "tokens.css")

    assert "skip-link" in html
    assert "aria-label=\"Primary workspaces\"" in html
    assert "aria-label=\"Global context\"" in html
    assert "aria-label=\"Evidence drawer\"" in html
    assert "aria-live=\"polite\"" in html
    assert "aria-live=\"assertive\"" in html
    assert ":focus-visible" in css
    assert "--pfi-target: 44px" in css
