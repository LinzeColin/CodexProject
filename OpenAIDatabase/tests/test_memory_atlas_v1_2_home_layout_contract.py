import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "memory-atlas"
STYLES = APP / "src" / "styles.css"
PACKAGE = APP / "package.json"
BROWSER_VALIDATOR = (
    APP / "scripts" / "validate_memory_atlas_v1_2_home_multiviewport.cjs"
)


def test_home_workspace_reserves_a_real_command_palette_row() -> None:
    css = STYLES.read_text(encoding="utf-8")

    assert (
        "grid-template-rows: auto auto auto "
        "clamp(160px, 26dvh, 240px) minmax(0, 1fr);"
    ) in css
    assert (
        "grid-template-rows: auto auto auto "
        "clamp(132px, 22dvh, 160px) minmax(0, 1fr);"
    ) in css


def test_command_palette_is_bounded_and_scrollable() -> None:
    css = STYLES.read_text(encoding="utf-8")

    required_declarations = (
        "min-height: 0;",
        "height: 100%;",
        "max-height: 100%;",
        "overflow-y: auto;",
        "overscroll-behavior: contain;",
    )
    palette_block = css.split(".command-palette {", maxsplit=1)[1].split("}", maxsplit=1)[0]
    for declaration in required_declarations:
        assert declaration in palette_block


def test_home_overview_preserves_internal_scroll() -> None:
    css = STYLES.read_text(encoding="utf-8")
    visual_workspace_index = css.index(".visual-workspace {")
    home_override_index = css.index(".visual-workspace.home-overview-view {")
    home_override = css[home_override_index:].split("}", maxsplit=1)[0]

    assert home_override_index > visual_workspace_index
    for declaration in (
        "grid-template-rows: none;",
        "overflow-x: hidden;",
        "overflow-y: auto;",
        "overscroll-behavior: contain;",
    ):
        assert declaration in home_override


def test_mobile_home_content_uses_the_remaining_grid_height() -> None:
    css = STYLES.read_text(encoding="utf-8")
    mobile_css = css.split("@media (max-width: 720px) {", maxsplit=1)[1]

    assert '.content-grid.wide-view[data-view="home"] {' in mobile_css
    home_grid_block = mobile_css.split(
        '.content-grid.wide-view[data-view="home"] {', maxsplit=1
    )[1].split("}", maxsplit=1)[0]
    assert "grid-template-rows: minmax(0, 1fr);" in home_grid_block


def test_real_three_viewport_browser_gate_is_registered() -> None:
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))

    assert package["scripts"]["validate:v1.2-home-multiviewport"] == (
        "node scripts/validate_memory_atlas_v1_2_home_multiviewport.cjs"
    )
    assert BROWSER_VALIDATOR.is_file()

    validator = BROWSER_VALIDATOR.read_text(encoding="utf-8")
    for contract in (
        'name: "desktop-low-height", width: 1470, height: 661',
        'name: "desktop-standard", width: 1440, height: 900',
        'name: "mobile", width: 390, height: 844',
        "assertNoPairwiseOverlap",
        "assertNoHorizontalOverflow",
        "assertViewportContainment",
        "assertPaletteContentReachable",
        "assertCriticalContentReachable",
        "assertNestedHomeContentFits",
        "assertBehaviorSummariesReachable",
    ):
        assert contract in validator
