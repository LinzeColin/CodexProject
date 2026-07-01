from __future__ import annotations

from dataclasses import asdict, dataclass


TARGET_VERSION = "v0.2.4"
SOURCE_PACKAGE_VERSION = "v0.2.3-repair"
REPAIR_LABEL = "PFI v0.2.3 Repair"
STAGE = "Stage 8"
STAGE_NAME = "端到端浏览器与 app 验收"
PHASE_8_1_ID = "8.1"
PHASE_8_1_NAME = "自动验收"
PHASE_8_2_ID = "8.2"
PHASE_8_2_NAME = "截图验收"
PHASE_8_3_ID = "8.3"
PHASE_8_3_NAME = "人工验收"
PHASE_8_1_TASK_IDS = ["T8.1.1", "T8.1.2", "T8.1.3", "T8.1.4"]
PHASE_8_2_TASK_IDS = ["T8.2.1", "T8.2.2", "T8.2.3", "T8.2.4"]
PHASE_8_3_TASK_IDS = ["T8.3.1", "T8.3.2", "T8.3.3"]
AUTOMATED_CHECKS = [
    "route_click_test",
    "entry_version_test",
    "data_state_test",
    "report_center_test",
]


@dataclass(frozen=True)
class V024Stage8Phase81Contract:
    target_version: str
    source_package_version: str
    repair_label: str
    stage: str
    stage_name: str
    phase_id: str
    phase_name: str
    current_phase_only: bool
    max_one_phase_per_run: bool
    stage_7_github_main_uploaded_required: bool
    task_ids: list[str]
    automated_checks: list[str]
    allowed_files: list[str]
    validation_commands: list[str]
    evidence_files: list[str]
    phase_8_2_started: bool
    phase_8_3_started: bool
    stage_8_whole_review_complete: bool
    github_main_uploaded: bool
    stage_9_started: bool
    app_bundle_changes_allowed: bool
    data_logic_changes_allowed: bool
    formal_fake_financial_data_allowed: bool
    explicitly_not_done: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class V024Stage8Phase82Contract:
    target_version: str
    source_package_version: str
    repair_label: str
    stage: str
    stage_name: str
    phase_id: str
    phase_name: str
    current_phase_only: bool
    max_one_phase_per_run: bool
    phase_8_1_required: bool
    task_ids: list[str]
    required_screenshot_groups: list[str]
    allowed_files: list[str]
    validation_commands: list[str]
    evidence_files: list[str]
    phase_8_3_started: bool
    stage_8_whole_review_complete: bool
    github_main_uploaded: bool
    stage_9_started: bool
    app_bundle_changes_allowed: bool
    data_logic_changes_allowed: bool
    formal_fake_financial_data_allowed: bool
    explicitly_not_done: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class V024Stage8Phase83Contract:
    target_version: str
    source_package_version: str
    repair_label: str
    stage: str
    stage_name: str
    phase_id: str
    phase_name: str
    current_phase_only: bool
    max_one_phase_per_run: bool
    phase_8_1_required: bool
    phase_8_2_required: bool
    task_ids: list[str]
    required_artifacts: list[str]
    allowed_files: list[str]
    validation_commands: list[str]
    user_acceptance_claim_allowed_without_user_confirmation: bool
    no_auto_next_stage: bool
    stage_8_whole_review_complete: bool
    github_main_uploaded: bool
    stage_9_started: bool
    app_bundle_changes_allowed: bool
    data_logic_changes_allowed: bool
    formal_fake_financial_data_allowed: bool
    explicitly_not_done: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_v024_stage8_phase81_contract() -> V024Stage8Phase81Contract:
    return V024Stage8Phase81Contract(
        target_version=TARGET_VERSION,
        source_package_version=SOURCE_PACKAGE_VERSION,
        repair_label=REPAIR_LABEL,
        stage=STAGE,
        stage_name=STAGE_NAME,
        phase_id=PHASE_8_1_ID,
        phase_name=PHASE_8_1_NAME,
        current_phase_only=True,
        max_one_phase_per_run=True,
        stage_7_github_main_uploaded_required=True,
        task_ids=PHASE_8_1_TASK_IDS,
        automated_checks=AUTOMATED_CHECKS,
        allowed_files=[
            "PFI/src/pfi_v02/stage_v024_stage8_e2e_acceptance.py",
            "PFI/scripts/validate_v024_stage8_phase81_e2e_auto.js",
            "PFI/tests/test_v024_stage8_phase81_e2e_auto_acceptance.py",
            "PFI/docs/pfi_v024/STAGE8_E2E_ACCEPTANCE.md",
            "PFI/docs/pfi_v024/RUN_CONTRACT.md",
            "PFI/reports/pfi_v024/stage_8/phase_8_1/*",
            "PFI/README.md",
            "PFI/HANDOFF.md",
            "PFI/CHANGELOG.md",
            "PFI/功能清单.md",
            "PFI/开发记录.md",
            "PFI/模型参数文件.md",
        ],
        validation_commands=[
            "node PFI/scripts/validate_v024_stage8_phase81_e2e_auto.js",
            "node --check PFI/scripts/validate_v024_stage8_phase81_e2e_auto.js",
            "node --check PFI/web/app/shell.js",
            "python3 -m pytest PFI/tests/test_v024_stage8_phase81_e2e_auto_acceptance.py -q",
            "python3 -m pytest PFI/tests/test_v024_stage7_github_upload_contract.py -q",
            "python3 -m json.tool PFI/reports/pfi_v024/stage_8/phase_8_1/evidence.json",
            "python3 -m json.tool PFI/reports/pfi_v024/stage_8/phase_8_1/browser_validation.json",
            "git diff --check -- PFI",
        ],
        evidence_files=[
            "PFI/reports/pfi_v024/stage_8/phase_8_1/evidence.json",
            "PFI/reports/pfi_v024/stage_8/phase_8_1/browser_validation.json",
            "PFI/reports/pfi_v024/stage_8/phase_8_1/route_click_validation.json",
            "PFI/reports/pfi_v024/stage_8/phase_8_1/entry_version_validation.json",
            "PFI/reports/pfi_v024/stage_8/phase_8_1/data_state_validation.json",
            "PFI/reports/pfi_v024/stage_8/phase_8_1/report_center_validation.json",
            "PFI/reports/pfi_v024/stage_8/phase_8_1/terminal.log",
            "PFI/reports/pfi_v024/stage_8/phase_8_1/changed_files.txt",
            "PFI/reports/pfi_v024/stage_8/phase_8_1/risk_and_rollback.md",
        ],
        phase_8_2_started=False,
        phase_8_3_started=False,
        stage_8_whole_review_complete=False,
        github_main_uploaded=False,
        stage_9_started=False,
        app_bundle_changes_allowed=False,
        data_logic_changes_allowed=False,
        formal_fake_financial_data_allowed=False,
        explicitly_not_done=[
            "Phase 8.2 screenshot acceptance",
            "Phase 8.3 manual acceptance",
            "Stage 8 whole-stage review",
            "Stage 8 GitHub main upload",
            "Stage 9 regression freeze",
            "GitHub main upload",
            "app bundle reinstall",
            "financial data mutation or synthesis",
        ],
    )


def build_v024_stage8_phase82_contract() -> V024Stage8Phase82Contract:
    return V024Stage8Phase82Contract(
        target_version=TARGET_VERSION,
        source_package_version=SOURCE_PACKAGE_VERSION,
        repair_label=REPAIR_LABEL,
        stage=STAGE,
        stage_name=STAGE_NAME,
        phase_id=PHASE_8_2_ID,
        phase_name=PHASE_8_2_NAME,
        current_phase_only=True,
        max_one_phase_per_run=True,
        phase_8_1_required=True,
        task_ids=PHASE_8_2_TASK_IDS,
        required_screenshot_groups=["app", "localhost", "primary_entries", "mobile"],
        allowed_files=[
            "PFI/src/pfi_v02/stage_v024_stage8_e2e_acceptance.py",
            "PFI/scripts/validate_v024_stage8_phase82_screenshots.js",
            "PFI/tests/test_v024_stage8_phase82_screenshot_acceptance.py",
            "PFI/docs/pfi_v024/STAGE8_E2E_ACCEPTANCE.md",
            "PFI/docs/pfi_v024/RUN_CONTRACT.md",
            "PFI/reports/pfi_v024/stage_8/phase_8_2/*",
            "PFI/README.md",
            "PFI/HANDOFF.md",
            "PFI/CHANGELOG.md",
            "PFI/功能清单.md",
            "PFI/开发记录.md",
            "PFI/模型参数文件.md",
        ],
        validation_commands=[
            "node PFI/scripts/validate_v024_stage8_phase82_screenshots.js",
            "node --check PFI/scripts/validate_v024_stage8_phase82_screenshots.js",
            "node --check PFI/web/app/shell.js",
            "python3 -m pytest PFI/tests/test_v024_stage8_phase82_screenshot_acceptance.py -q",
            "python3 -m pytest PFI/tests/test_v024_stage8_phase81_e2e_auto_acceptance.py -q",
            "python3 -m json.tool PFI/reports/pfi_v024/stage_8/phase_8_2/evidence.json",
            "python3 -m json.tool PFI/reports/pfi_v024/stage_8/phase_8_2/browser_validation.json",
            "python3 -m json.tool PFI/reports/pfi_v024/stage_8/phase_8_2/screenshot_index.json",
            "git diff --check -- PFI",
        ],
        evidence_files=[
            "PFI/reports/pfi_v024/stage_8/phase_8_2/evidence.json",
            "PFI/reports/pfi_v024/stage_8/phase_8_2/browser_validation.json",
            "PFI/reports/pfi_v024/stage_8/phase_8_2/screenshot_index.json",
            "PFI/reports/pfi_v024/stage_8/phase_8_2/app_entry_validation.json",
            "PFI/reports/pfi_v024/stage_8/phase_8_2/screenshots/app_home.png",
            "PFI/reports/pfi_v024/stage_8/phase_8_2/screenshots/localhost_home.png",
            "PFI/reports/pfi_v024/stage_8/phase_8_2/screenshots/mobile_responsive.png",
            "PFI/reports/pfi_v024/stage_8/phase_8_2/terminal.log",
            "PFI/reports/pfi_v024/stage_8/phase_8_2/changed_files.txt",
            "PFI/reports/pfi_v024/stage_8/phase_8_2/risk_and_rollback.md",
        ],
        phase_8_3_started=False,
        stage_8_whole_review_complete=False,
        github_main_uploaded=False,
        stage_9_started=False,
        app_bundle_changes_allowed=False,
        data_logic_changes_allowed=False,
        formal_fake_financial_data_allowed=False,
        explicitly_not_done=[
            "Phase 8.3 manual acceptance",
            "Stage 8 whole-stage review",
            "Stage 8 GitHub main upload",
            "Stage 9 regression freeze",
            "GitHub main upload",
            "app bundle reinstall",
            "financial data mutation or synthesis",
        ],
    )


def build_v024_stage8_phase83_contract() -> V024Stage8Phase83Contract:
    return V024Stage8Phase83Contract(
        target_version=TARGET_VERSION,
        source_package_version=SOURCE_PACKAGE_VERSION,
        repair_label=REPAIR_LABEL,
        stage=STAGE,
        stage_name=STAGE_NAME,
        phase_id=PHASE_8_3_ID,
        phase_name=PHASE_8_3_NAME,
        current_phase_only=True,
        max_one_phase_per_run=True,
        phase_8_1_required=True,
        phase_8_2_required=True,
        task_ids=PHASE_8_3_TASK_IDS,
        required_artifacts=[
            "manual_acceptance.md",
            "defects.md",
            "evidence.json",
            "terminal.log",
            "changed_files.txt",
            "risk_and_rollback.md",
        ],
        allowed_files=[
            "PFI/src/pfi_v02/stage_v024_stage8_e2e_acceptance.py",
            "PFI/tests/test_v024_stage8_phase83_manual_acceptance.py",
            "PFI/docs/pfi_v024/STAGE8_E2E_ACCEPTANCE.md",
            "PFI/docs/pfi_v024/RUN_CONTRACT.md",
            "PFI/reports/pfi_v024/stage_8/phase_8_3/*",
            "PFI/README.md",
            "PFI/HANDOFF.md",
            "PFI/CHANGELOG.md",
            "PFI/功能清单.md",
            "PFI/开发记录.md",
            "PFI/模型参数文件.md",
        ],
        validation_commands=[
            "python3 -m pytest PFI/tests/test_v024_stage8_phase83_manual_acceptance.py -q",
            "python3 -m pytest PFI/tests/test_v024_stage8_phase82_screenshot_acceptance.py -q",
            "python3 -m pytest PFI/tests/test_v024_stage8_phase81_e2e_auto_acceptance.py -q",
            "python3 -m py_compile PFI/src/pfi_v02/stage_v024_stage8_e2e_acceptance.py",
            "python3 -m json.tool PFI/reports/pfi_v024/stage_8/phase_8_3/evidence.json",
            "git diff --check -- PFI",
        ],
        user_acceptance_claim_allowed_without_user_confirmation=False,
        no_auto_next_stage=True,
        stage_8_whole_review_complete=False,
        github_main_uploaded=False,
        stage_9_started=False,
        app_bundle_changes_allowed=False,
        data_logic_changes_allowed=False,
        formal_fake_financial_data_allowed=False,
        explicitly_not_done=[
            "Stage 8 whole-stage review",
            "Stage 8 GitHub main upload",
            "Stage 9 regression freeze",
            "GitHub main upload",
            "app bundle reinstall",
            "financial data mutation or synthesis",
            "user acceptance claim without user confirmation",
        ],
    )
