from __future__ import annotations

from dataclasses import asdict, dataclass


TARGET_VERSION = "v0.2.4"
SOURCE_PACKAGE_VERSION = "v0.2.3-repair"
REPAIR_LABEL = "PFI v0.2.3 Repair"
STAGE_ID = "Stage 6"
PHASE_6_1_ID = "6.1"
PHASE_6_2_ID = "6.2"
PHASE_6_3_ID = "6.3"
WHOLE_REVIEW_ID = "stage_6_whole_review"
GITHUB_UPLOAD_ID = "stage_6_github_main_upload"


@dataclass(frozen=True)
class V024Stage6GithubUploadContract:
    target_version: str
    source_package_version: str
    repair_label: str
    stage_id: str
    upload_id: str
    review_id: str
    reviewed_phase_ids: list[str]
    validation_commands: list[str]
    stage_6_candidate_complete: bool
    stage_6_review_complete: bool
    stage_6_complete: bool
    github_main_uploaded: bool
    rebased_on_current_origin_main: bool
    remote_main_verification_required: bool
    stage_7_started: bool
    stage_7_allowed_without_user_instruction: bool
    app_bundle_changes_allowed: bool
    data_logic_changes_allowed: bool
    formal_fake_financial_data_allowed: bool
    max_phases_per_run: int
    explicitly_not_done: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_v024_stage6_github_upload_contract() -> V024Stage6GithubUploadContract:
    return V024Stage6GithubUploadContract(
        target_version=TARGET_VERSION,
        source_package_version=SOURCE_PACKAGE_VERSION,
        repair_label=REPAIR_LABEL,
        stage_id=STAGE_ID,
        upload_id=GITHUB_UPLOAD_ID,
        review_id=WHOLE_REVIEW_ID,
        reviewed_phase_ids=[PHASE_6_1_ID, PHASE_6_2_ID, PHASE_6_3_ID],
        validation_commands=[
            "git fetch origin main",
            "git rebase origin/main",
            "node stage6 whole review browser validation",
            "node --check PFI/web/app/shell.js",
            "node --check PFI/scripts/validate_v024_stage6_whole_review_browser.js",
            "python3 -m py_compile PFI/src/pfi_v02/stage_v024_stage6_experience.py",
            "pytest stage6 github upload contract",
            "pytest stage6 whole review and phase regression",
            "pytest stage5 adjacent regression",
            "python3 -m json.tool stage6 upload/whole/browser evidence",
            "git diff --check -- PFI",
            "git push origin HEAD:main",
            "git ls-remote origin refs/heads/main",
        ],
        stage_6_candidate_complete=True,
        stage_6_review_complete=True,
        stage_6_complete=True,
        github_main_uploaded=True,
        rebased_on_current_origin_main=True,
        remote_main_verification_required=True,
        stage_7_started=False,
        stage_7_allowed_without_user_instruction=False,
        app_bundle_changes_allowed=False,
        data_logic_changes_allowed=False,
        formal_fake_financial_data_allowed=False,
        max_phases_per_run=1,
        explicitly_not_done=[
            "Stage 7",
            "app bundle reinstall",
            "launcher C or Info.plist changes",
            "financial data or metric logic changes",
        ],
    )
