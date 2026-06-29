from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


version = "v0.2.3"
app_version = "0.2.3"
stage1_build_id = "20260629-stage1"
stage1_bundle_version = "20260629.1"
stage1_ui_contract_version = "PFI-V023-STAGE1-APP-ENTRY-BUNDLE-CONSISTENCY"
stage1_query_string = (
    f"pfi_app_version={app_version}"
    f"&pfi_build={stage1_build_id}"
    f"&pfi_ui_contract={stage1_ui_contract_version}"
)

stage1_web_bundle_files = (
    "web/index.html",
    "web/styles/tokens.css",
    "web/app/shell.js",
)

stage2_phase1_id = "V023-S2-P1"
stage2_phase1_name = "任务包恢复与防幻觉门"
stage2_expected_taskpack_inputs = (
    "~/Downloads/PFI_v0.2.3_Human_Product_Experience_Recovery_Roadmap.txt",
    "~/Downloads/PFI_v0.2.3_Human_Product_Experience_Recovery_TaskPack.zip",
    "PFI/docs/pfi_v023/README.md",
    "PFI/docs/pfi_v023/STAGE0_BASELINE.md",
    "PFI/reports/pfi_v023/stage_1/evidence.json",
)

official_nav = [
    "首页总览",
    "账户与资产",
    "账本流水",
    "投资管理",
    "消费管理",
    "数据源与上传",
    "建议与复盘",
    "报告与洞察",
    "市场与研究",
    "设置",
]

deprecated_constraints = [
    "9 个一级入口",
    "市场与研究不得作为一级入口",
    "暗色 AI 控制台风格",
    "演示数据可用于验收",
    "README/docs 写完成即可 closeout",
]

retained_governance_rules = [
    "一轮只执行一个 Stage",
    "未经过用户验收不得进入下一 Stage",
    "禁止文档声明冒充完成",
    "禁止关键词测试冒充真实交互",
    "每个 Stage 必须生成 Evidence Pack",
]

v01_compatibility_routes = {
    "首页": "首页总览",
    "市场": "市场与研究",
    "研究": "市场与研究",
    "持仓": "投资管理",
    "策略实验室": "市场与研究 / 投资管理共享同一状态",
    "数据与系统": "设置",
}

forbidden_financial_data_terms = [
    "mock",
    "sample",
    "synthetic",
    "fixture",
    "demo",
    "fake",
    "测试样例",
    "自动生成流水",
    "自动生成持仓",
    "写死趋势线",
]

metric_data_statuses = [
    "ready",
    "confirmed_zero",
    "not_loaded",
    "not_mounted",
    "path_error",
    "permission_error",
    "parse_error",
    "outdated",
    "filter_empty",
    "calculation_error",
    "review_required",
]

no_mock_financial_data = True
one_stage_per_run = True
requires_user_acceptance = True
no_auto_closeout = True
light_theme_required = True
human_product_experience_priority = True
stage0_only = True


@dataclass(frozen=True)
class V023EvidenceCommand:
    command: str
    required: bool


@dataclass(frozen=True)
class V023Stage0Contract:
    version: str
    stage: str
    stage_name: str
    official_nav: tuple[str, ...]
    deprecated_constraints: tuple[str, ...]
    retained_governance_rules: tuple[str, ...]
    v01_compatibility_routes: dict[str, str]
    forbidden_financial_data_terms: tuple[str, ...]
    metric_data_statuses: tuple[str, ...]
    no_mock_financial_data: bool
    one_stage_per_run: bool
    requires_user_acceptance: bool
    no_auto_closeout: bool
    light_theme_required: bool
    human_product_experience_priority: bool
    stage0_only: bool
    allowed_files: tuple[str, ...]
    explicitly_not_done: tuple[str, ...]
    validation_commands: tuple[V023EvidenceCommand, ...]
    evidence_files: tuple[str, ...]


@dataclass(frozen=True)
class V023Stage1Contract:
    version: str
    stage: str
    stage_name: str
    task_id: str
    current_stage_only: bool
    no_stage2: bool
    app_version: str
    build_id: str
    bundle_version: str
    ui_contract_version: str
    app_entry_targets: tuple[str, ...]
    app_entry_focus: str
    frontend_bundle_files: tuple[str, ...]
    required_consistency_fields: tuple[str, ...]
    validation_commands: tuple[V023EvidenceCommand, ...]
    evidence_files: tuple[str, ...]
    explicitly_not_done: tuple[str, ...]


@dataclass(frozen=True)
class V023Stage2Phase1Contract:
    version: str
    stage: str
    phase_id: str
    phase_name: str
    current_phase_only: bool
    max_one_phase_per_run: bool
    taskpack_required_before_ui_implementation: bool
    expected_taskpack_inputs: tuple[str, ...]
    allowed_files: tuple[str, ...]
    validation_commands: tuple[V023EvidenceCommand, ...]
    evidence_files: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    explicitly_not_done: tuple[str, ...]


def build_stage0_contract() -> dict[str, Any]:
    contract = V023Stage0Contract(
        version=version,
        stage="Stage 0",
        stage_name="需求锁定、历史约束废弃、证据基线建立",
        official_nav=tuple(official_nav),
        deprecated_constraints=tuple(deprecated_constraints),
        retained_governance_rules=tuple(retained_governance_rules),
        v01_compatibility_routes=dict(v01_compatibility_routes),
        forbidden_financial_data_terms=tuple(forbidden_financial_data_terms),
        metric_data_statuses=tuple(metric_data_statuses),
        no_mock_financial_data=no_mock_financial_data,
        one_stage_per_run=one_stage_per_run,
        requires_user_acceptance=requires_user_acceptance,
        no_auto_closeout=no_auto_closeout,
        light_theme_required=light_theme_required,
        human_product_experience_priority=human_product_experience_priority,
        stage0_only=stage0_only,
        allowed_files=(
            "PFI/docs/pfi_v023/*",
            "PFI/src/pfi_v02/stage_v023_contract.py",
            "PFI/tests/test_v023_stage0_contract.py",
            "PFI/reports/pfi_v023/stage_0/*",
        ),
        explicitly_not_done=(
            "Stage 1 app/localhost/frontend bundle consistency",
            "UI visual rebuild",
            "route implementation",
            "data computation or read-model changes",
            "report generation implementation",
            "app bundle reinstall",
        ),
        validation_commands=(
            V023EvidenceCommand("node --check PFI/web/app/shell.js", True),
            V023EvidenceCommand("python3 -m py_compile PFI/src/pfi_v02/stage_v023_contract.py", True),
            V023EvidenceCommand("python3 -m py_compile PFI/tests/test_v023_stage0_contract.py", True),
            V023EvidenceCommand("python3 -m pytest PFI/tests/test_v023_stage0_contract.py -q", True),
            V023EvidenceCommand("git diff --check -- PFI", True),
        ),
        evidence_files=(
            "PFI/reports/pfi_v023/stage_0/evidence.json",
            "PFI/reports/pfi_v023/stage_0/terminal.log",
            "PFI/reports/pfi_v023/stage_0/changed_files.txt",
        ),
    )
    payload = asdict(contract)
    payload["validation_commands"] = [asdict(item) for item in contract.validation_commands]
    return payload


def build_stage2_phase1_contract() -> dict[str, Any]:
    contract = V023Stage2Phase1Contract(
        version=version,
        stage="Stage 2",
        phase_id=stage2_phase1_id,
        phase_name=stage2_phase1_name,
        current_phase_only=True,
        max_one_phase_per_run=True,
        taskpack_required_before_ui_implementation=True,
        expected_taskpack_inputs=stage2_expected_taskpack_inputs,
        allowed_files=(
            "PFI/HANDOFF.md",
            "PFI/docs/pfi_v023/*",
            "PFI/src/pfi_v02/stage_v023_contract.py",
            "PFI/tests/test_v023_stage2_phase1_taskpack_recovery.py",
            "PFI/reports/pfi_v023/stage_2/phase_1/*",
        ),
        validation_commands=(
            V023EvidenceCommand("python3 -m pytest PFI/tests/test_v023_stage2_phase1_taskpack_recovery.py -q", True),
            V023EvidenceCommand(
                "python3 -m pytest PFI/tests/test_v023_stage0_contract.py "
                "PFI/tests/test_v023_stage1_app_entry_bundle_contract.py "
                "PFI/tests/test_pfi_app_entry_version_contract.py "
                "PFI/tests/test_v023_stage2_phase1_taskpack_recovery.py -q",
                True,
            ),
            V023EvidenceCommand("git diff --check -- PFI", True),
        ),
        evidence_files=(
            "PFI/docs/pfi_v023/STAGE2_PHASE1_TASKPACK_RECOVERY.md",
            "PFI/reports/pfi_v023/stage_2/phase_1/evidence.json",
            "PFI/reports/pfi_v023/stage_2/phase_1/terminal.log",
            "PFI/reports/pfi_v023/stage_2/phase_1/changed_files.txt",
        ),
        stop_conditions=(
            "Official v0.2.3 Stage 2 Roadmap or TaskPack is missing from current GitHub main and checked local input paths.",
            "Do not infer Stage 2 page, route, read-model, report, or data behavior from older v0.2.1/v0.2.2 stage names.",
            "Do not implement UI changes until the real v0.2.3 Stage 2 phase/task list is restored or supplied.",
        ),
        explicitly_not_done=(
            "Stage 2 page rebuild",
            "route implementation changes",
            "data computation or read-model changes",
            "report generation implementation",
            "app bundle reinstall",
            "GitHub main upload for intermediate phase",
            "mock/sample/synthetic/fixture/demo/fake financial data",
        ),
    )
    payload = asdict(contract)
    payload["validation_commands"] = [asdict(item) for item in contract.validation_commands]
    return payload


def build_stage1_contract() -> dict[str, Any]:
    contract = V023Stage1Contract(
        version=version,
        stage="Stage 1",
        stage_name="App 入口与前端版本一致性",
        task_id="V023-S1-T01",
        current_stage_only=True,
        no_stage2=True,
        app_version=app_version,
        build_id=stage1_build_id,
        bundle_version=stage1_bundle_version,
        ui_contract_version=stage1_ui_contract_version,
        app_entry_targets=(
            "~/Downloads/PFI.app",
            "/Applications/PFI.app",
            "~/Desktop/PFI.app",
        ),
        app_entry_focus="~/Downloads/PFI.app",
        frontend_bundle_files=stage1_web_bundle_files,
        required_consistency_fields=(
            "project_root",
            "app_version",
            "build_id",
            "ui_contract_version",
            "web_bundle_hash",
            "web_index_sha256",
            "shell_js_sha256",
            "served_url",
            "browser_profile",
        ),
        validation_commands=(
            V023EvidenceCommand("node --check PFI/web/app/shell.js", True),
            V023EvidenceCommand("python3 -m pytest PFI/tests/test_v023_stage0_contract.py PFI/tests/test_v023_stage1_app_entry_bundle_contract.py PFI/tests/test_pfi_app_entry_version_contract.py -q", True),
            V023EvidenceCommand("PFI/scripts/installPFIEntryApps.sh --downloads-only", True),
            V023EvidenceCommand("PFI/scripts/macosRuntimeAcceptance.sh --launch-method app --app-path ~/Downloads/PFI.app --skip-app-acceptance --summary-json", True),
            V023EvidenceCommand("fresh browser profile bundle verification", True),
            V023EvidenceCommand("git diff --check -- PFI", True),
        ),
        evidence_files=(
            "PFI/docs/pfi_v023/STAGE1_APP_ENTRY_BUNDLE_CONSISTENCY.md",
            "PFI/reports/pfi_v023/stage_1/evidence.json",
            "PFI/reports/pfi_v023/stage_1/terminal.log",
            "PFI/reports/pfi_v023/stage_1/changed_files.txt",
            "PFI/reports/pfi_v023/stage_1/browser_fresh_profile.json",
        ),
        explicitly_not_done=(
            "Stage 2 page rebuild",
            "route implementation changes",
            "data computation or read-model changes",
            "report generation implementation",
            "mock/sample/synthetic/fixture/demo/fake financial data",
        ),
    )
    payload = asdict(contract)
    payload["validation_commands"] = [asdict(item) for item in contract.validation_commands]
    return payload


def current_stage0_baseline(root: Path | None = None) -> dict[str, Any]:
    project_root = root or Path(__file__).resolve().parents[2]
    web_index = project_root / "web" / "index.html"
    shell_js = project_root / "web" / "app" / "shell.js"
    index_text = web_index.read_text(encoding="utf-8")
    shell_text = shell_js.read_text(encoding="utf-8")
    return {
        "web_index_exists": web_index.exists(),
        "shell_js_exists": shell_js.exists(),
        "web_index_primary_entry_count_marker": 'data-primary-workspaces="10"' in index_text,
        "web_index_has_market_research": "市场与研究" in index_text,
        "shell_has_market_research": "市场与研究" in shell_text,
        "shell_has_strategy_lab_keyword": "策略实验室" in shell_text,
        "stage0_modifies_ui": False,
    }


def stage1_file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def build_stage1_web_bundle_manifest(root: Path | None = None) -> dict[str, Any]:
    project_root = root or Path(__file__).resolve().parents[2]
    files = []
    bundle_digest = hashlib.sha256()
    for relative in stage1_web_bundle_files:
        path = project_root / relative
        file_hash = stage1_file_sha256(path)
        files.append(
            {
                "path": f"PFI/{relative}",
                "sha256": file_hash,
                "bytes": path.stat().st_size,
            }
        )
        bundle_digest.update(relative.encode("utf-8"))
        bundle_digest.update(b"\0")
        bundle_digest.update(file_hash.encode("ascii"))
        bundle_digest.update(b"\0")
    return {
        "schema": "PFIV023Stage1WebBundleManifestV1",
        "files": files,
        "web_bundle_hash": bundle_digest.hexdigest(),
    }


def build_stage1_runtime_metadata(root: Path | None = None) -> dict[str, Any]:
    manifest = build_stage1_web_bundle_manifest(root)
    hash_by_path = {item["path"]: item["sha256"] for item in manifest["files"]}
    return {
        "schema": "PFIV023Stage1RuntimeMetadataV1",
        "pfiVersion": version,
        "appVersion": app_version,
        "buildId": stage1_build_id,
        "bundleVersion": stage1_bundle_version,
        "uiContractVersion": stage1_ui_contract_version,
        "stage": "Stage 1",
        "stageName": "App 入口与前端版本一致性",
        "webBundleHash": manifest["web_bundle_hash"],
        "webIndexSha256": hash_by_path["PFI/web/index.html"],
        "shellJsSha256": hash_by_path["PFI/web/app/shell.js"],
        "frontendBundleFiles": tuple(stage1_web_bundle_files),
    }
