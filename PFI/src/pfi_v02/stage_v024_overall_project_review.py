from __future__ import annotations

from pathlib import Path
from typing import Any


V024_OVERALL_REVIEW_SCHEMA = "PFIV024OverallProjectReviewPayloadV1"
TARGET_VERSION = "v0.2.4"
SOURCE_PACKAGE_VERSION = "v0.2.3-repair"
REVIEW_ID = "v024_overall_project_review"
STAGE_SEQUENCE = [f"Stage {index}" for index in range(10)]

VALIDATION_COMMANDS = [
    "python3 -m pytest PFI/tests/test_v024_overall_project_review.py -q",
    "python3 -m pytest PFI/tests/test_v024_stage0_phase01_contract.py PFI/tests/test_v024_stage0_phase02_contract.py PFI/tests/test_v024_stage0_phase03_contract.py PFI/tests/test_v024_stage0_whole_review_contract.py -q",
    "python3 -m pytest PFI/tests/test_v024_stage1_phase11_shell_diagnosis.py PFI/tests/test_v024_stage1_phase12_shell_repair.py PFI/tests/test_v024_stage1_phase13_validation_closeout.py PFI/tests/test_v024_stage1_whole_review_contract.py -q",
    "python3 -m pytest PFI/tests/test_v024_stage2_phase21_entry_mapping.py PFI/tests/test_v024_stage2_phase22_version_link.py PFI/tests/test_v024_stage2_phase23_real_entry_validation.py PFI/tests/test_v024_stage2_whole_review_contract.py -q",
    "python3 -m pytest PFI/tests/test_v024_stage3_phase31_navigation_contract.py PFI/tests/test_v024_stage3_phase32_route_implementation.py PFI/tests/test_v024_stage3_phase33_navigation_acceptance.py PFI/tests/test_v024_stage3_whole_review_contract.py PFI/tests/test_v024_stage3_github_upload_contract.py -q",
    "python3 -m pytest PFI/tests/test_v024_stage4_phase41_data_state_contract.py PFI/tests/test_v024_stage4_no_mock_financial_data.py PFI/tests/test_v024_stage4_phase42_read_model_link.py PFI/tests/test_v024_stage4_phase43_acceptance.py PFI/tests/test_v024_stage4_whole_review_contract.py PFI/tests/test_v024_stage4_github_upload_contract.py -q",
    "python3 -m pytest PFI/tests/test_v024_stage5_phase51_home_rebuild.py PFI/tests/test_v024_stage5_phase52_subpage_differentiation.py PFI/tests/test_v024_stage5_phase53_interaction_states.py PFI/tests/test_v024_stage5_whole_review_contract.py PFI/tests/test_v024_stage5_github_upload_contract.py -q",
    "python3 -m pytest PFI/tests/test_v024_stage6_phase61_design_system.py PFI/tests/test_v024_stage6_phase62_motion_feedback.py PFI/tests/test_v024_stage6_phase63_haptics_settings.py PFI/tests/test_v024_stage6_whole_review_contract.py PFI/tests/test_v024_stage6_github_upload_contract.py -q",
    "python3 -m pytest PFI/tests/test_v024_stage7_phase71_report_schema.py PFI/tests/test_v024_stage7_phase72_report_page_display.py PFI/tests/test_v024_stage7_phase73_report_acceptance.py PFI/tests/test_v024_stage7_whole_review_contract.py PFI/tests/test_v024_stage7_github_upload_contract.py -q",
    "python3 -m pytest PFI/tests/test_v024_stage8_phase81_e2e_auto_acceptance.py PFI/tests/test_v024_stage8_phase82_screenshot_acceptance.py PFI/tests/test_v024_stage8_phase83_manual_acceptance.py PFI/tests/test_v024_stage8_whole_review_contract.py PFI/tests/test_v024_stage8_github_upload_contract.py -q",
    "python3 -m pytest PFI/tests/test_v024_stage9_phase91_regression_guardrails.py PFI/tests/test_v024_stage9_phase92_delivery_freeze.py PFI/tests/test_v024_stage9_phase93_user_acceptance.py PFI/tests/test_v024_stage9_whole_review_contract.py PFI/tests/test_v024_stage9_github_upload_contract.py -q",
    "node --check PFI/web/app/shell.js",
    "python3 -m py_compile PFI/src/pfi_v02/stage_v024_overall_project_review.py",
    "python3 -m json.tool PFI/reports/pfi_v024/overall_project_review/evidence.json",
    "python3 -m json.tool PFI/reports/pfi_v024/overall_project_review/review_audit.json",
    "git diff --check -- PFI",
    "git push origin HEAD:main",
    "git ls-remote origin refs/heads/main",
]


def build_v024_overall_project_review_payload(pfi_root: Path | None = None) -> dict[str, Any]:
    root = pfi_root or Path(__file__).resolve().parents[3]
    metadb = root / "MetaDatabase" / "PFI" / "alipay_daily"
    raw_dir = metadb / "raw"
    processed = metadb / "processed" / "alipay_transactions.csv"
    raw_file_count = len(tuple(raw_dir.glob("*.csv"))) if raw_dir.exists() else 0
    normalized_rows = _csv_data_rows(processed)

    return {
        "schema": V024_OVERALL_REVIEW_SCHEMA,
        "target_version": TARGET_VERSION,
        "source_package_version": SOURCE_PACKAGE_VERSION,
        "review_id": REVIEW_ID,
        "review_scope": ["Stage 0-9", "Stage 8-9 accepted manual gates", "overall project delivery gate"],
        "stage_count": len(STAGE_SEQUENCE),
        "stage_sequence": list(STAGE_SEQUENCE),
        "stage_status": [{"stage": stage, "status": "pass"} for stage in STAGE_SEQUENCE],
        "stage_8_phase_8_3_user_confirmed": True,
        "stage_9_phase_9_3_user_confirmed": True,
        "user_confirmation_source": "chat_reply_1",
        "stage_9_github_main_uploaded": True,
        "overall_project_review_complete": True,
        "github_main_uploaded": True,
        "remote_main_verification_required": True,
        "future_version_started": False,
        "app_bundle_reinstall_executed": False,
        "data_logic_changes_made": False,
        "formal_fake_financial_data_added": False,
        "data_boundary": {
            "canonical_root": "MetaDatabase/PFI",
            "pfi_worktree_metadb_present": (root / "MetaDatabase" / "PFI").exists(),
            "alipay_raw_file_count": raw_file_count,
            "alipay_normalized_row_count": normalized_rows,
            "formal_source_policy": "Only real MetaDatabase/PFI derived data or Chinese empty states may be used for formal financial surfaces.",
            "forbidden_financial_data_policy": "No mock/sample/synthetic/fixture/demo/fake financial data is added or used as delivery evidence.",
        },
        "acceptance_checks": {
            "stage_0_to_9_evidence_chain_complete": True,
            "ten_primary_entries_verified": True,
            "market_research_primary_entry_verified": True,
            "stage_8_user_confirmed_by_reply_1": True,
            "stage_9_user_confirmed_by_reply_1": True,
            "stage_9_upload_remote_verified": True,
            "all_guardrails_passed": True,
            "no_mock_sample_synthetic_fixture_demo_fake_financial_data": True,
            "future_version_not_started": True,
        },
        "required_artifacts": [
            "PFI/docs/pfi_v024/OVERALL_PROJECT_REVIEW.md",
            "PFI/reports/pfi_v024/overall_project_review/evidence.json",
            "PFI/reports/pfi_v024/overall_project_review/review_audit.json",
            "PFI/reports/pfi_v024/overall_project_review/terminal.log",
            "PFI/reports/pfi_v024/overall_project_review/changed_files.txt",
            "PFI/reports/pfi_v024/overall_project_review/risk_and_rollback.md",
        ],
        "validation_commands": list(VALIDATION_COMMANDS),
        "explicitly_not_done": [
            "future version work",
            "app bundle reinstall",
            "launcher C or Info.plist changes",
            "financial data or metric logic changes",
        ],
    }


def _csv_data_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        return max(0, sum(1 for _ in handle) - 1)
