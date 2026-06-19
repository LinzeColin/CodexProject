import re
from pathlib import Path

from pfi_os.ui_contracts import (
    EVIDENCE_DRAWER_SECTIONS,
    GLOBAL_CONTEXT_FIELDS,
    PRIMARY_WORKSPACES,
    build_web_shell_contract,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _retired_fragments() -> list[str]:
    return ["Token" + " ROI", "E" + "VA", "Quant" + "Lab"]


def test_web_shell_contract_exposes_pfi_first_six_workspace_shape():
    contract = build_web_shell_contract()
    workspace_labels = [item.label for item in PRIMARY_WORKSPACES]
    workspace_ids = [item.workspace_id for item in PRIMARY_WORKSPACES]
    html = _text(WEB_ROOT / "index.html")
    nav_ids = re.findall(r'data-workspace="([^"]+)"', html)

    assert contract.schema == "PFIOSWebShellContractV1"
    assert contract.feature_flag == "PFI_UI_V2"
    assert contract.fallback_value == "1"
    assert workspace_labels == ["首页", "市场", "研究", "持仓", "策略实验室", "数据与系统"]
    assert workspace_ids == ["home", "market", "research", "portfolio", "strategy", "data"]
    assert nav_ids == workspace_ids
    assert 'data-primary-workspaces="6"' in html
    assert "PFI OS" in html


def test_web_shell_preserves_global_context_and_cached_home_contract():
    contract = build_web_shell_contract()
    html = _text(WEB_ROOT / "index.html")
    js = _text(WEB_ROOT / "app" / "shell.js")

    assert contract.cached_home_target_seconds == 2
    assert 'data-cached-home-target-seconds="2"' in html
    assert "CONTEXT_STORAGE_KEY" in js
    assert "pfi-context-v1" in js
    for field in GLOBAL_CONTEXT_FIELDS:
        assert f'data-context-field="{field}"' in html
    assert 'data-card-source="operational_store:task_records"' in html
    assert 'data-card-source="operational_store:source_records"' in html
    assert 'data-card-source="operational_store:holding_snapshots"' in html
    assert 'data-card-source="operational_store:evidence_records"' in html
    assert "PFIOSHomeSummaryV1" in html


def test_web_shell_renders_phase_c_workflow_runtime_cards():
    html = _text(WEB_ROOT / "index.html")
    js = _text(WEB_ROOT / "app" / "shell.js")
    css = _text(WEB_ROOT / "styles" / "tokens.css")

    assert "data-workflow-cards" in html
    assert 'data-workflow-card="strategy"' in html
    assert 'data-workflow-card="market"' in html
    assert 'data-workflow-card="research"' in html
    assert 'data-workflow-card="portfolio"' in html
    assert "workflow_cards" in html
    assert "applyWorkflowCards" in js
    assert "workflowFreshnessLabel" in js
    assert "showWorkflowEvidence" in js
    assert "data-runtime-target" in html
    assert ".workflow-grid" in css
    assert ".workflow-card" in css


def test_streamlit_launcher_exposes_pfi_ui_v2_feature_flag_with_fallback():
    source = _text(PROJECT_ROOT / "src" / "pfi_os" / "app" / "streamlit_app.py")

    assert "def _pfi_ui_v2_enabled" in source
    assert 'os.environ.get("PFI_UI_V2", "1") != "0"' in source
    assert "render_pfi_ui_v2_shell()" in source
    assert "return" in source.split("render_pfi_ui_v2_shell()", maxsplit=1)[1]
    assert '[data-testid="stToolbar"]' in source
    assert "padding-top: 0" in source


def test_launch_scripts_default_to_pfi_web_shell_with_legacy_opt_out():
    app_launcher = _text(PROJECT_ROOT / "StartPFIOS.command")
    cli_launcher = _text(PROJECT_ROOT / "scripts" / "startPFIOS.sh")
    shell_html = _text(PROJECT_ROOT / "web" / "index.html")

    for source in (app_launcher, cli_launcher):
        assert 'export PFI_UI_V2="${PFI_UI_V2:-1}"' in source
        assert "Starting PFI OS at" in source
        assert "streamlit run src/pfi_os/app/streamlit_app.py" in source
    assert 'data-fallback-flag-value="1"' in shell_html


def test_streamlit_launcher_can_inline_web_shell_assets():
    from pfi_os.app.streamlit_app import _pfi_web_shell_html

    rendered = _pfi_web_shell_html()

    assert '<link rel="stylesheet" href="./styles/tokens.css" />' not in rendered
    assert '<script src="./app/shell.js"></script>' not in rendered
    assert "<style>" in rendered
    assert "<script>" in rendered
    assert "PFIOSWebShellContractV1" in rendered


def test_web_shell_evidence_drawer_and_safety_boundary_are_explicit():
    contract = build_web_shell_contract()
    html = _text(WEB_ROOT / "index.html")

    assert "no live automatic orders" in contract.safety_boundary
    assert "broker submission" in contract.safety_boundary
    assert "private-data commit path" in contract.safety_boundary
    assert "data-evidence-drawer" in html
    for section in EVIDENCE_DRAWER_SECTIONS:
        assert f"<dt>{section}</dt>" in html
    assert "外部模型未启用" in html


def test_web_shell_contract_purposes_are_chinese_user_oriented():
    contract = build_web_shell_contract()
    purposes = "\n".join(item.purpose for item in contract.primary_workspaces)

    for required in ["市场宽度", "政策", "组合暴露", "回测", "盘感训练", "隐私"]:
        assert required in purposes
    assert "backtest" not in purposes.lower()
    assert "portfolio" not in purposes.lower()


def test_web_shell_active_user_surface_has_no_retired_identity_or_value_text():
    active_text = "\n".join(
        [
            _text(WEB_ROOT / "index.html"),
            _text(WEB_ROOT / "styles" / "tokens.css"),
            _text(WEB_ROOT / "app" / "shell.js"),
            _text(PROJECT_ROOT / "docs" / "ux" / "PFI_WEB_SHELL_ACCEPTANCE.md"),
        ]
    )

    for fragment in _retired_fragments():
        assert fragment not in active_text
