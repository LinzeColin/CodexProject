from __future__ import annotations

from dataclasses import asdict, dataclass


TARGET_VERSION = "v0.2.4"
SOURCE_PACKAGE_VERSION = "v0.2.3-repair"
STAGE_ID = "Stage 2"
PHASE_2_1_ID = "2.1"

PROJECT_ROOT = "/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/pfi/PFI"


ENTRY_SURFACES = [
    {
        "surface_id": "streamlit_host",
        "path": "PFI/src/pfi_os/app/streamlit_app.py",
        "entry_function": "_pfi_web_shell_html",
        "role": "Embeds static HTML and inlines CSS/routes/pages/shell into Streamlit.",
    },
    {
        "surface_id": "static_html",
        "path": "PFI/web/index.html",
        "entry_function": "body dataset and static shell scaffold",
        "role": "Canonical static Web Shell markup used by Streamlit embedding.",
    },
    {
        "surface_id": "shell_runtime",
        "path": "PFI/web/app/shell.js",
        "entry_function": "window.PFI_STAGE1_SHELL",
        "role": "Runtime shell, routing, metadata fallback, and error boundary.",
    },
    {
        "surface_id": "version_runtime",
        "path": "PFI/web/app/version.js",
        "entry_function": "window.PFI_READ_STAGE1_VERSION",
        "role": "Stage 1 version read interface and repair label source.",
    },
    {
        "surface_id": "macos_template_app",
        "path": "PFI/macos/PFI.app",
        "entry_function": "Contents/MacOS/PFI",
        "role": "Template bundle copied into user-facing app locations.",
    },
    {
        "surface_id": "native_launcher_source",
        "path": "PFI/macos/PFI_launcher.c",
        "entry_function": "PFI_PROJECT_ROOT binding discovery",
        "role": "Native launcher that resolves StartPFI.command from bound project roots.",
    },
    {
        "surface_id": "launcher_installer",
        "path": "PFI/scripts/installPFIEntryApps.sh",
        "entry_function": "install_app",
        "role": "Builds launcher and writes Contents/Resources/PFI_PROJECT_ROOT.",
    },
    {
        "surface_id": "start_command",
        "path": "PFI/StartPFI.command",
        "entry_function": "macOS app launch target",
        "role": "Command executed by native launcher.",
    },
    {
        "surface_id": "start_script",
        "path": "PFI/scripts/startPFI.sh",
        "entry_function": "streamlit launcher on localhost ports 8501..8510",
        "role": "Starts or reuses the Streamlit service and opens versioned URL.",
    },
]


INSTALLED_APP_BINDINGS = [
    {
        "path": "/Applications/PFI.app",
        "binding_type": "installed_app",
        "project_root": PROJECT_ROOT,
        "dry_run_status": "spawn-command",
    },
    {
        "path": "~/Downloads/PFI.app",
        "binding_type": "installed_app",
        "project_root": PROJECT_ROOT,
        "dry_run_status": "spawn-command",
    },
    {
        "path": "~/Desktop/PFI.app",
        "binding_type": "symlink_to_applications",
        "project_root": PROJECT_ROOT,
        "dry_run_status": "spawn-command",
    },
]


OLD_UI_SIGNATURES = [
    {
        "signature_id": "legacy_query_contract_v023_stage1",
        "surface": "PFI/scripts/startPFI.sh",
        "observed_value": "pfi_build=20260629-stage1&pfi_ui_contract=PFI-V023-STAGE1-APP-ENTRY-BUNDLE-CONSISTENCY",
        "status": "recorded_for_phase_2_2",
    },
    {
        "signature_id": "legacy_index_dataset_v023_stage1",
        "surface": "PFI/web/index.html",
        "observed_value": "data-pfi-build-id=20260629-stage1; data-pfi-ui-contract-version=PFI-V023-STAGE1-APP-ENTRY-BUNDLE-CONSISTENCY",
        "status": "recorded_for_phase_2_2",
    },
    {
        "signature_id": "legacy_shell_fallback_v023_stage1",
        "surface": "PFI/web/app/shell.js",
        "observed_value": "buildId fallback 20260629-stage1; uiContractVersion fallback PFI-V023-STAGE1-APP-ENTRY-BUNDLE-CONSISTENCY",
        "status": "recorded_for_phase_2_2",
    },
]


BUILD_HASH_DISPLAY_SPEC = [
    {
        "surface": "PFI/web/index.html",
        "display_location": "body dataset and visible app status strip",
        "fields": ["repairLabel", "buildId", "bundleHash", "uiContractVersion"],
        "implementation_phase": "2.2",
    },
    {
        "surface": "PFI/web/app/version.js",
        "display_location": "window.PFI_STAGE1_VERSION and read function",
        "fields": ["targetVersion", "repairLabel", "buildId", "bundleVersion", "uiContractVersion"],
        "implementation_phase": "2.2",
    },
    {
        "surface": "PFI/web/app/entry_audit.js",
        "display_location": "entry audit read model",
        "fields": ["appPath", "localhostUrl", "webIndexSha256", "shellJsSha256", "bundleHash"],
        "implementation_phase": "2.2",
    },
]


@dataclass(frozen=True)
class V024Stage2Phase21Contract:
    target_version: str
    source_package_version: str
    stage_id: str
    phase_id: str
    phase_name: str
    task_ids: list[str]
    phase_2_1_complete: bool
    phase_2_2_complete: bool
    phase_2_3_complete: bool
    stage_2_complete: bool
    max_phases_per_run: int
    entry_surfaces: list[dict[str, str]]
    installed_app_bindings: list[dict[str, str]]
    old_ui_signatures: list[dict[str, str]]
    build_hash_display_spec: list[dict[str, object]]
    evidence_pack_required: list[str]
    business_ui_changes_allowed: bool
    data_logic_changes_allowed: bool
    app_bundle_changes_allowed: bool
    launcher_changes_allowed: bool
    github_main_upload_allowed: bool
    next_phase_requires_user_acceptance: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_v024_stage2_phase21_contract() -> V024Stage2Phase21Contract:
    return V024Stage2Phase21Contract(
        target_version=TARGET_VERSION,
        source_package_version=SOURCE_PACKAGE_VERSION,
        stage_id=STAGE_ID,
        phase_id=PHASE_2_1_ID,
        phase_name="入口链路映射",
        task_ids=["T2.1.1", "T2.1.2", "T2.1.3", "T2.1.4"],
        phase_2_1_complete=True,
        phase_2_2_complete=False,
        phase_2_3_complete=False,
        stage_2_complete=False,
        max_phases_per_run=1,
        entry_surfaces=ENTRY_SURFACES,
        installed_app_bindings=INSTALLED_APP_BINDINGS,
        old_ui_signatures=OLD_UI_SIGNATURES,
        build_hash_display_spec=BUILD_HASH_DISPLAY_SPEC,
        evidence_pack_required=[
            "PFI/reports/pfi_v024/stage_2/phase_2_1/evidence.json",
            "PFI/reports/pfi_v024/stage_2/phase_2_1/terminal.log",
            "PFI/reports/pfi_v024/stage_2/phase_2_1/changed_files.txt",
            "PFI/reports/pfi_v024/stage_2/phase_2_1/entry_map.md",
            "PFI/reports/pfi_v024/stage_2/phase_2_1/old_ui_signatures.json",
            "PFI/reports/pfi_v024/stage_2/phase_2_1/build_hash_display_spec.md",
            "PFI/reports/pfi_v024/stage_2/phase_2_1/risk_and_rollback.md",
        ],
        business_ui_changes_allowed=False,
        data_logic_changes_allowed=False,
        app_bundle_changes_allowed=False,
        launcher_changes_allowed=False,
        github_main_upload_allowed=False,
        next_phase_requires_user_acceptance=True,
    )
