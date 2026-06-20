from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _retired_fragments() -> list[str]:
    return ["E" + "VA", "Quant" + "Lab", "Token" + " ROI"]


def test_gate2_shell_acceptance_script_defines_formal_user_facing_uat_contract():
    script = _text(PROJECT_ROOT / "scripts" / "pfiGate2ShellAcceptance.sh")

    assert "PFIGate2ShellAcceptanceV1" in script
    assert "Gate2 Shell UAT" in script
    assert "JOURNEY_HOME_TO_BACKTEST" in script
    assert "JOURNEY_STRATEGY_MARKET_FEEL" in script
    assert "JOURNEY_RESEARCH_REPORT_POLICY" in script
    assert "JOURNEY_DATA_SYSTEM_DIAGNOSTICS" in script
    for required in [
        "单标的回测",
        "盘感训练",
        "报告中心",
        "政策雷达",
        "数据中心",
        "禁止实盘自动下单",
        "不输出实盘信号",
        "隐私边界",
    ]:
        assert required in script


def test_gate2_shell_acceptance_covers_a11y_performance_and_no_legacy_page_gate():
    script = _text(PROJECT_ROOT / "scripts" / "pfiGate2ShellAcceptance.sh")

    for required in [
        "PERFORMANCE_BUDGET",
        "shell_ready_ms",
        "workspace_switch_ms",
        "function_open_ms",
        "WCAGStructuralProof",
        "AxeWCAG2AA",
        "NoUnlabeledInteractive",
        "MinTarget44px",
        "FocusVisible",
        "NoLegacyPageImport",
        "NoLegacyPageNavigation",
        "PrimaryActionNavigation",
        "SameShellRunner",
        "ChineseFirstSurface",
        "NoVisibleLegacyOrError",
        "AllFeatureControls",
        "TotalPanelsOpened",
    ]:
        assert required in script
    assert "a[data-feature-view]" in script
    assert "pfi_legacy=1" in script
    assert "feature controls are buttons" in script
    assert "verifyAllVisibleFeatureControls" in script
    assert "all_feature_control_panels_opened" in script


def test_gate2_shell_acceptance_is_lightweight_browser_only_and_fail_closed():
    script = _text(PROJECT_ROOT / "scripts" / "pfiGate2ShellAcceptance.sh")

    assert "write_blocked_payload" in script
    assert "status\": \"Blocked\"" in script
    assert "scripts/startPFIOS.sh" in script
    assert "scripts/stopPFIOS.sh" in script
    assert "playwright.chromium.launch" in script
    assert "finalAcceptanceCheck.sh" not in script
    assert "scripts/ciSmoke.sh" not in script
    assert "scripts/runTests.sh" not in script
    assert "full pytest" in script
    assert "broker connections" in script
    assert "real orders" in script


def test_gate2_target_gate_and_generated_artifacts_are_wired():
    gate = _text(PROJECT_ROOT / "scripts" / "pfiGate.sh")
    gitignore = _text(PROJECT_ROOT / ".gitignore")
    script_tests = _text(PROJECT_ROOT / "tests" / "test_scripts.py")

    assert "tests/contract/test_pfi005_gate2_shell_acceptance.py" in gate
    assert "data/systemAudit/PFIGate2ShellAcceptance*.json" in gitignore
    assert "data/systemAudit/PFIGate2ShellAcceptance*.png" in gitignore
    assert "scripts/pfiGate2ShellAcceptance.sh" in script_tests


def test_web_shell_assets_support_gate2_same_shell_feature_journeys():
    html = _text(WEB_ROOT / "index.html")
    js = _text(WEB_ROOT / "app" / "shell.js")

    assert "FUNCTION_VIEWS" in js
    assert "openFunctionView" in js
    assert "renderFunctionDetail" in js
    assert "runFunctionAction" in js
    assert "renderFunctionRunner" in js
    assert "hideFunctionRunner" in js
    assert "window.open" not in js
    assert "location.reload" not in js
    assert "window.location.href" not in js
    assert "a data-feature-view" not in html
    for view in ["single", "market_feel", "reports", "policy", "tools"]:
        assert f'view: "{view}"' in js
    for label in ["单标的回测", "盘感训练", "报告中心", "政策雷达", "数据中心"]:
        assert label in js
    assert 'button.dataset.featureView = target.view' in js
    assert 'featureControl.dataset.featureView' in js


def test_gate2_user_visible_contract_does_not_reintroduce_retired_identity_terms():
    active_text = "\n".join(
        [
            _text(WEB_ROOT / "index.html"),
            _text(WEB_ROOT / "app" / "shell.js"),
            _text(PROJECT_ROOT / "scripts" / "pfiGate2ShellAcceptance.sh"),
            _text(PROJECT_ROOT / "docs" / "ux" / "PFI_WEB_SHELL_ACCEPTANCE.md"),
        ]
    )

    for fragment in _retired_fragments():
        assert fragment not in active_text
