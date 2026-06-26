import ast
from pathlib import Path

from pfi_os.ui_contracts.pfi_v02_stage0 import (
    ACTIVE_VIEW_COMPATIBILITY,
    CURRENT_SIX_WORKSPACE_COMPATIBILITY,
    LOCAL_ACTIVE_RUNTIME_PATHS,
    LOCAL_PUBLIC_ASSUMPTION_GAPS,
    PUBLIC_ASSUMPTION_COMPATIBILITY,
    V02_TARGET_PRIMARY_ENTRIES,
    build_stage0_contract,
    target_primary_labels,
)
from pfi_os.ui_contracts.web_shell import PRIMARY_WORKSPACES


ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _active_pfi_view_options() -> dict[str, str]:
    source = _read("src/pfi_os/app/streamlit_app.py")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "ACTIVE_PFI_VIEW_OPTIONS":
                    return ast.literal_eval(node.value)
    raise AssertionError("ACTIVE_PFI_VIEW_OPTIONS not found")


def test_v02_target_ia_is_exact_eight_entries_without_excluded_product_l1():
    assert target_primary_labels() == (
        "首页总览",
        "账户与资产",
        "账本流水",
        "投资管理",
        "消费管理",
        "数据源与同步",
        "建议与复盘",
        "报告与洞察",
    )
    assert [entry.index for entry in V02_TARGET_PRIMARY_ENTRIES] == list(range(1, 9))

    forbidden = {"Alpha", "System", "Development", "系统与开发", "R" + "alpha"}
    for label in target_primary_labels():
        assert label not in forbidden


def test_current_web_shell_six_workspaces_are_preserved_as_compatibility_aliases():
    html = _read("web/index.html")
    current_labels = tuple(item.label for item in PRIMARY_WORKSPACES)
    mapped_labels = tuple(entry.existing_entry for entry in CURRENT_SIX_WORKSPACE_COMPATIBILITY)

    assert current_labels == ("首页", "市场", "研究", "持仓", "策略实验室", "数据与系统")
    assert mapped_labels == current_labels
    assert 'data-primary-workspaces="6"' in html
    assert all(entry.keep_accessible for entry in CURRENT_SIX_WORKSPACE_COMPATIBILITY)
    for entry in CURRENT_SIX_WORKSPACE_COMPATIBILITY:
        assert any(entry.v02_location.startswith(label) for label in target_primary_labels())


def test_all_active_streamlit_owner_views_have_v02_destination():
    active_options = _active_pfi_view_options()
    mapped_entries = {entry.existing_entry for entry in ACTIVE_VIEW_COMPATIBILITY}

    assert set(active_options.values()) == mapped_entries
    assert "策略实验室｜盘感训练" in mapped_entries
    assert "数据与系统｜模拟实验" in mapped_entries
    assert any(entry.v02_location == "投资管理 > 策略实验室 / 大数据模拟器" for entry in ACTIVE_VIEW_COMPATIBILITY)
    assert all(entry.keep_accessible for entry in ACTIVE_VIEW_COMPATIBILITY)


def test_public_big_data_and_qbvs_assumptions_are_recorded_without_requiring_local_move():
    public_entries = {entry.existing_entry: entry for entry in PUBLIC_ASSUMPTION_COMPATIBILITY}

    assert public_entries["PFI/大数据模拟器"].v02_location == "投资管理 > 策略实验室 / 大数据模拟器"
    assert public_entries["qbvs/ active runtime"].status == "BoundaryLocked"
    assert "No local PFI/大数据模拟器 directory under CodexProject." in LOCAL_PUBLIC_ASSUMPTION_GAPS
    assert "No local qbvs/ directory under PFI_OS." in LOCAL_PUBLIC_ASSUMPTION_GAPS
    assert not (ROOT.parent / "PFI" / "大数据模拟器").exists()
    assert not (ROOT / "qbvs").exists()


def test_local_active_runtime_paths_exist_or_are_private_data_boundary():
    for relative_path in LOCAL_ACTIVE_RUNTIME_PATHS:
        if relative_path.startswith("$PFI_OS_DATA_HOME"):
            assert "private/operational/pfi.sqlite" in relative_path
            continue
        assert (ROOT / relative_path).exists(), relative_path


def test_stage0_audit_document_covers_required_output_and_forbidden_literals():
    audit = _read("docs/pfi_v02/STAGE0_COMPATIBILITY_AUDIT.md")
    contract = build_stage0_contract()

    for required in [
        "Current local PFI project root",
        "Existing Owner-Facing Entries",
        "Active runtime paths not to move",
        "Test Availability Report",
        "Local PFI OS / ledger system",
        "Current UI/routes",
        "Compatibility Matrix",
        "Proposed / Modified Files",
        "Rollback Plan",
        "Single Acceptance Target",
        "Phase 0A",
        "Phase 0B",
        "Phase 0C",
    ]:
        assert required in audit

    combined = audit + repr(contract)
    for forbidden_literal in ["R" + "alpha", "Serenity" + "-Alipay"]:
        assert forbidden_literal not in combined


def test_owner_entry_files_reference_v02_stage0_contract():
    expected_files = ["README.md", "PLANS.md", "功能清单", "开发记录", "模型参数文件", "HANDOFF.md"]

    for relative_path in expected_files:
        text = _read(relative_path)
        assert "PFI V0.2 Stage 0" in text
        assert "docs/pfi_v02/STAGE0_COMPATIBILITY_AUDIT.md" in text


def test_contract_shape_is_serializable_and_non_trading():
    contract = build_stage0_contract()

    assert contract["schema"] == "PFIV02Stage0CompatibilityContractV1"
    assert len(contract["target_primary_entries"]) == 8
    assert len(contract["compatibility_entries"]) >= 20
    assert "no trading password" in contract["non_trading_boundary"]
    assert "no automatic real-money order submission" in contract["non_trading_boundary"]
