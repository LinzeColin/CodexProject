from __future__ import annotations

from dataclasses import asdict, dataclass


TARGET_VERSION = "v0.2.4"
SOURCE_PACKAGE_VERSION = "v0.2.3-repair"
STAGE_ID = "Stage 1"
PHASE_1_1_ID = "1.1"
PHASE_1_2_ID = "1.2"
PHASE_1_3_ID = "1.3"

SHELL_JS_SHA256_AT_PHASE_1_1 = "bb2492ead4404dd8affd730b3c231884281aa163ce3adb1a438a3e26e9c3aa90"
SHELL_JS_BYTES_AT_PHASE_1_1 = 272357
SHELL_JS_LINES_AT_PHASE_1_1 = 5510


@dataclass(frozen=True)
class V024Stage1Phase11Contract:
    target_version: str
    source_package_version: str
    stage_id: str
    phase_id: str
    phase_name: str
    task_ids: list[str]
    phase_1_1_complete: bool
    phase_1_2_complete: bool
    phase_1_3_complete: bool
    stage_1_complete: bool
    max_phases_per_run: int
    shell_js_path: str
    shell_snapshot_path: str
    shell_js_sha256: str
    shell_js_bytes: int
    shell_js_lines: int
    syntax_check_required: bool
    syntax_check_current_result: str
    fragmented_range_findings: list[dict[str, str]]
    residual_phase_1_2_gaps: list[str]
    business_ui_changes_allowed: bool
    data_logic_changes_allowed: bool
    shell_js_modification_allowed: bool
    next_phase_requires_user_acceptance: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_v024_stage1_phase11_contract() -> V024Stage1Phase11Contract:
    return V024Stage1Phase11Contract(
        target_version=TARGET_VERSION,
        source_package_version=SOURCE_PACKAGE_VERSION,
        stage_id=STAGE_ID,
        phase_id=PHASE_1_1_ID,
        phase_name="现状定位",
        task_ids=["T1.1.1", "T1.1.2", "T1.1.3"],
        phase_1_1_complete=True,
        phase_1_2_complete=False,
        phase_1_3_complete=False,
        stage_1_complete=False,
        max_phases_per_run=1,
        shell_js_path="PFI/web/app/shell.js",
        shell_snapshot_path="PFI/reports/pfi_v024/stage_1/phase_1_1/shell.js.snapshot",
        shell_js_sha256=SHELL_JS_SHA256_AT_PHASE_1_1,
        shell_js_bytes=SHELL_JS_BYTES_AT_PHASE_1_1,
        shell_js_lines=SHELL_JS_LINES_AT_PHASE_1_1,
        syntax_check_required=True,
        syntax_check_current_result="pass_via_codex_bundled_node",
        fragmented_range_findings=[],
        residual_phase_1_2_gaps=[
            "no unified window-level shell integrity API exposes version, init, route mount, and error boundary together",
            "bootPFIShell exists as an internal boot function but is not exported as a stable shell initialization contract",
            "route mounting exists through route helpers but is not exposed as a Stage 1 shell mount API",
            "errors are handled locally with catch blocks but no named Stage 1 shell error boundary is exported",
        ],
        business_ui_changes_allowed=False,
        data_logic_changes_allowed=False,
        shell_js_modification_allowed=False,
        next_phase_requires_user_acceptance=True,
    )


@dataclass(frozen=True)
class V024Stage1Phase12Contract:
    target_version: str
    source_package_version: str
    stage_id: str
    phase_id: str
    phase_name: str
    task_ids: list[str]
    phase_1_1_complete: bool
    phase_1_2_complete: bool
    phase_1_3_complete: bool
    stage_1_complete: bool
    max_phases_per_run: int
    shell_js_path: str
    version_js_path: str
    shell_integrity_api: str
    version_read_interface: str
    initialization_entry: str
    route_mount_entry: str
    error_boundary_entry: str
    shell_js_modification_allowed: bool
    version_js_required: bool
    business_ui_changes_allowed: bool
    data_logic_changes_allowed: bool
    formal_fake_financial_data_allowed: bool
    next_phase_requires_user_acceptance: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_v024_stage1_phase12_contract() -> V024Stage1Phase12Contract:
    return V024Stage1Phase12Contract(
        target_version=TARGET_VERSION,
        source_package_version=SOURCE_PACKAGE_VERSION,
        stage_id=STAGE_ID,
        phase_id=PHASE_1_2_ID,
        phase_name="最小恢复",
        task_ids=["T1.2.1", "T1.2.2", "T1.2.3", "T1.2.4"],
        phase_1_1_complete=True,
        phase_1_2_complete=True,
        phase_1_3_complete=False,
        stage_1_complete=False,
        max_phases_per_run=1,
        shell_js_path="PFI/web/app/shell.js",
        version_js_path="PFI/web/app/version.js",
        shell_integrity_api="window.PFI_STAGE1_SHELL",
        version_read_interface="window.PFI_READ_STAGE1_VERSION",
        initialization_entry="initializePFIStage1Shell",
        route_mount_entry="mountPFIStage1Route",
        error_boundary_entry="handlePFIStage1ShellError",
        shell_js_modification_allowed=True,
        version_js_required=True,
        business_ui_changes_allowed=False,
        data_logic_changes_allowed=False,
        formal_fake_financial_data_allowed=False,
        next_phase_requires_user_acceptance=True,
    )


@dataclass(frozen=True)
class V024Stage1Phase13Contract:
    target_version: str
    source_package_version: str
    stage_id: str
    phase_id: str
    phase_name: str
    task_ids: list[str]
    phase_1_1_complete: bool
    phase_1_2_complete: bool
    phase_1_3_complete: bool
    stage_1_candidate_complete: bool
    stage_1_complete: bool
    max_phases_per_run: int
    validation_commands: list[str]
    changed_files_audit_required: bool
    whole_stage_review_required: bool
    github_main_upload_allowed: bool
    business_ui_changes_allowed: bool
    data_logic_changes_allowed: bool
    next_phase_requires_user_acceptance: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_v024_stage1_phase13_contract() -> V024Stage1Phase13Contract:
    return V024Stage1Phase13Contract(
        target_version=TARGET_VERSION,
        source_package_version=SOURCE_PACKAGE_VERSION,
        stage_id=STAGE_ID,
        phase_id=PHASE_1_3_ID,
        phase_name="验证",
        task_ids=["T1.3.1", "T1.3.2", "T1.3.3"],
        phase_1_1_complete=True,
        phase_1_2_complete=True,
        phase_1_3_complete=True,
        stage_1_candidate_complete=True,
        stage_1_complete=False,
        max_phases_per_run=1,
        validation_commands=[
            "node --check PFI/web/app/shell.js",
            "node --check PFI/web/app/version.js",
            "pytest stage1 phase13 contract",
            "pytest v024 stage1 regression",
            "changed files audit",
        ],
        changed_files_audit_required=True,
        whole_stage_review_required=True,
        github_main_upload_allowed=False,
        business_ui_changes_allowed=False,
        data_logic_changes_allowed=False,
        next_phase_requires_user_acceptance=True,
    )
