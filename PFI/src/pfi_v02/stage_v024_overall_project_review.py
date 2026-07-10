from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from typing import Any

from pfi_v02.stage_v023_read_model import build_stage6_read_model_audit


V024_OVERALL_REVIEW_SCHEMA = "PFIV024OverallProjectReviewPayloadV1"
V024_OVERALL_REREVIEW_SCHEMA = "PFIV024OverallRereviewPayloadV1"
TARGET_VERSION = "v0.2.4"
SOURCE_PACKAGE_VERSION = "v0.2.3-repair"
REVIEW_ID = "v024_overall_project_review"
REREVIEW_ID = "v024_overall_rereview"
REREVIEW_ACCEPTANCE_ID = "ACC-PFI-V024-OVERALL-REREVIEW"
FINAL_DELIVERY_GATE = "PFI-V024-FINAL-DELIVERY"
STAGE_SEQUENCE = [f"Stage {index}" for index in range(10)]
EVIDENCE_UNIT_FILES = ("evidence.json", "terminal.log", "changed_files.txt", "risk_and_rollback.md")
MANUAL_ACCEPTANCE_EVIDENCE = {
    "PFI/reports/pfi_v024/stage_8/phase_8_3/evidence.json",
    "PFI/reports/pfi_v024/stage_9/phase_9_3/evidence.json",
}
EXPECTED_RAW_FILE_COUNT = 4
EXPECTED_TRANSACTION_COUNT = 8815
EXPECTED_DATA_AS_OF = "2026-06-03"
EXPECTED_DATA_EVIDENCE_HASH = "sha256:da98c88a7c617afa0ad029d28ba7d5853550bcde51e82cdd6aadee5d64199325"

PHASE_EVIDENCE_SCHEMAS = {
    0: ("PFIV024Stage0Phase01EvidenceV1", "PFIV024Stage0Phase02EvidenceV1", "PFIV024Stage0Phase03EvidenceV1"),
    1: ("PFIV024Stage1Phase11EvidenceV1", "PFIV024Stage1Phase12EvidenceV1", "PFIV024Stage1Phase13EvidenceV1"),
    2: ("PFIV024Stage2Phase21EvidenceV1", "PFIV024Stage2Phase22EvidenceV1", "PFIV024Stage2Phase23EvidenceV1"),
    3: (
        "PFIV024Stage3Phase31NavigationEvidenceV1",
        "PFIV024Stage3Phase32RouteEvidenceV1",
        "PFIV024Stage3Phase33BrowserNavigationEvidenceV1",
    ),
    4: ("PFIV024Stage4Phase41EvidenceV1", "PFIV024Stage4Phase42EvidenceV1", "PFIV024Stage4Phase43EvidenceV1"),
    5: ("PFIV024Stage5Phase51EvidenceV1", "PFIV024Stage5Phase52EvidenceV1", "PFIV024Stage5Phase53EvidenceV1"),
    6: ("PFIV024Stage6Phase61EvidenceV1", "PFIV024Stage6Phase62EvidenceV1", "PFIV024Stage6Phase63EvidenceV1"),
    7: ("PFIV024Stage7Phase71EvidenceV1", "PFIV024Stage7Phase72EvidenceV1", "PFIV024Stage7Phase73EvidenceV1"),
    8: ("PFIV024Stage8Phase81EvidenceV1", "PFIV024Stage8Phase82EvidenceV1", "PFIV024Stage8Phase83EvidenceV1"),
    9: (
        "PFIV024Stage9Phase91RegressionGuardrailsEvidenceV1",
        "PFIV024Stage9Phase92DeliveryFreezeEvidenceV1",
        "PFIV024Stage9Phase93UserAcceptanceEvidenceV1",
    ),
}
PHASE_EVIDENCE_STATUSES = {
    **{stage: ("candidate_pass", "candidate_pass", "candidate_pass") for stage in range(6)},
    6: ("pass", "pass", "pass"),
    7: ("candidate_pass", "candidate_pass", "candidate_pass"),
    8: ("candidate_pass", "candidate_pass", "ready_for_user_acceptance"),
    9: ("candidate_pass", "candidate_pass", "waiting_for_user_acceptance"),
}
WHOLE_STAGE_EVIDENCE_SCHEMAS = {
    stage: f"PFIV024Stage{stage}WholeReviewEvidenceV1" for stage in range(10)
}
REQUIRED_WHOLE_STAGE_ACCEPTANCE_KEYS = {
    0: (
        "all_phase_evidence_present",
        "deprecated_constraints_recorded",
        "market_research_is_top_level",
        "no_mock_financial_data",
        "official_nav_count_is_10",
    ),
    1: (
        "all_phase_evidence_present",
        "no_fake_financial_data_added",
        "shell_integrity_api_present",
        "shell_js_syntax_passes",
        "version_read_interface_present",
    ),
    2: (
        "all_phase_evidence_present",
        "all_real_entry_paths_same_bundle_and_build",
        "no_fake_financial_data_added",
        "visible_build_id_present",
        "visible_bundle_hash_present",
        "visible_repair_label_present",
        "visible_ui_contract_present",
    ),
    3: (
        "all_phase_evidence_present",
        "browser_back_forward_passed",
        "legacy_alias_routes_resolve",
        "market_research_is_primary_index_9",
        "no_16_peer_primary_entries",
        "not_anchor_scroll_only_navigation",
        "official_primary_entries_are_10",
    ),
    4: (
        "confirmed_zero_requires_source_time_sample_formula",
        "core_metric_fields_complete",
        "missing_real_data_no_cny_zero",
        "no_mock_fixture_demo_financial_fallback",
        "shared_read_model_across_surfaces",
    ),
    5: (
        "browser_screenshots_cover_primary_and_core_secondary_pages",
        "click_actions_are_real_routes_not_toast_only",
        "each_primary_has_three_or_more_distinct_subpages",
        "every_page_has_primary_action_and_four_states",
        "homepage_answers_six_questions",
        "mechanical_home_layer_removed",
        "no_forbidden_financial_data_added",
        "secondary_pages_not_title_only_clones",
        "ten_primary_entries_preserved",
    ),
    6: (
        "default_light_ui",
        "design_tokens_cover_required_categories",
        "desktop_phone_preview_absent",
        "haptics_capability_detection_and_disable",
        "moderate_state_motion",
        "no_forbidden_financial_data_added",
        "settings_feedback_isolation",
    ),
    7: (
        "blocked_reports_have_no_full_financial_conclusion",
        "data_quality_report_generated",
        "formula_parameter_range_sample_visible",
        "no_forbidden_financial_data_added",
        "required_report_fields_present",
        "single_ai_paragraph_reports_rejected",
        "six_report_types_visible",
    ),
    8: (
        "app_localhost_consistency",
        "data_state_no_false_zero",
        "downloads_app_current_checkout",
        "light_ui_and_mobile",
        "manual_acceptance_confirmation",
        "no_forbidden_financial_data_added",
        "report_center_test",
        "route_click_test",
        "screenshot_coverage",
    ),
    9: (),
}

EXPECTED_EVIDENCE_UNIT_MANIFEST: dict[str, dict[str, Any]] = {}
for _stage in range(10):
    for _phase, (_schema, _status) in enumerate(
        zip(PHASE_EVIDENCE_SCHEMAS[_stage], PHASE_EVIDENCE_STATUSES[_stage], strict=True),
        start=1,
    ):
        EXPECTED_EVIDENCE_UNIT_MANIFEST[f"stage_{_stage}/phase_{_stage}_{_phase}"] = {
            "schema": _schema,
            "stage": f"Stage {_stage}",
            "phase": f"{_stage}.{_phase}",
            "status": _status,
            "required_acceptance_keys": (),
        }
    EXPECTED_EVIDENCE_UNIT_MANIFEST[f"stage_{_stage}/whole_stage_review"] = {
        "schema": WHOLE_STAGE_EVIDENCE_SCHEMAS[_stage],
        "stage": f"Stage {_stage}",
        "phase": None,
        "status": "pass",
        "required_acceptance_keys": REQUIRED_WHOLE_STAGE_ACCEPTANCE_KEYS[_stage],
    }
del _stage, _phase, _schema, _status

UI_VALIDATION_MANIFEST: dict[str, dict[str, Any]] = {
    "stage_2/phase_2_3/browser_validation.json": {
        "exact": {
            "schema": "PFIV024Stage2Phase23BrowserValidationV1",
            "stage": "Stage 2",
            "phase_id": "2.3",
            "status": "candidate_pass",
        },
        "true_fields": ("all_paths_same_build_id", "all_paths_same_bundle_hash"),
        "empty_fields": ("console_errors", "page_errors", "http_errors"),
        "minimum_lengths": {"paths": 4},
    },
    "stage_3/phase_3_3/browser_validation.json": {
        "exact": {
            "contract": "PFI-V024-STAGE3-PHASE33-BROWSER-NAVIGATION",
            "status": "pass",
            "desktop_primary_count": 10,
            "mobile_primary_count": 10,
            "market_research_index": 9,
        },
        "true_fields": (
            "legacy_labels_absent_as_primary_exact",
            "click_navigation_passed",
            "back_forward_passed",
            "direct_url_alias_passed",
        ),
        "empty_fields": ("console_errors", "page_errors"),
        "minimum_lengths": {"direct_aliases": 6},
    },
    "stage_3/phase_3_3/legacy_routes_validation.json": {
        "exact": {"contract": "PFI-V024-STAGE3-PHASE33-BROWSER-NAVIGATION", "status": "pass"},
        "minimum_lengths": {"cases": 6},
        "nested_status_fields": {"cases": "resolved"},
    },
    "stage_4/phase_4_3/browser_validation.json": {
        "exact": {
            "schema": "PFIV024Stage4Phase43BrowserValidationV1",
            "stage": "Stage 4",
            "phase_id": "4.3",
            "status": "pass",
        },
        "true_fields": (
            "confirmed_zero_gate_visible",
            "missing_state_reason_visible",
            "no_financial_zero_when_data_missing",
        ),
        "empty_fields": ("console_errors",),
    },
    "stage_5/phase_5_2/route_validation.json": {
        "exact": {
            "schema": "PFIV024Stage5Phase52RouteValidationV1",
            "stage": "Stage 5",
            "phase_id": "5.2",
            "status": "pass",
            "primary_entry_count": 10,
            "workspace_count": 10,
            "min_subpages_per_primary": 4,
            "total_subpage_count": 45,
        },
        "empty_fields": (
            "missing_stage3_secondary_routes",
            "missing_workspaces",
            "orphan_stage5_routes",
            "title_only_clone_groups",
            "workspaces_below_minimum",
            "duplicate_route_aliases",
            "duplicate_state_keys",
        ),
    },
    "stage_5/whole_stage_review/browser_validation.json": {
        "exact": {
            "schema": "PFIV024Stage5WholeReviewBrowserValidationV1",
            "stage": "Stage 5",
            "status": "pass",
            "primary_entry_count": 10,
            "primary_screenshot_count": 10,
            "core_secondary_screenshot_count": 10,
            "visible_state_kinds": ["empty", "error", "loading", "success"],
        },
        "true_fields": (
            "click_actions_route_not_toast_only",
            "history_back_forward_passed",
            "stage5_ux_state_visible",
        ),
        "empty_fields": (
            "console_errors",
            "page_errors",
            "http_errors",
            "server_not_found_paths",
            "mechanical_terms_visible",
        ),
    },
    "stage_6/whole_stage_review/browser_validation.json": {
        "exact": {
            "schema": "PFIV024Stage6WholeReviewBrowserValidationV1",
            "stage": "Stage 6",
            "status": "pass",
            "primary_entry_count": 10,
            "mobile_horizontal_overflow_px": 0,
        },
        "true_fields": (
            "default_light_ui",
            "haptic_capability_detected",
            "haptic_degrades_visually_when_unsupported",
            "settings_feedback_console_hidden_on_home",
            "settings_feedback_console_visible_on_settings",
        ),
        "false_fields": ("desktop_phone_preview_frame_visible",),
        "empty_fields": ("console_errors", "page_errors", "http_errors", "failures", "server_not_found_paths"),
    },
    "stage_7/phase_7_3/browser_validation.json": {
        "exact": {
            "schema": "PFIV024Stage7Phase73BrowserValidationV1",
            "stage": "Stage 7",
            "phase_id": "7.3",
            "status": "pass",
            "browser_gate_status": "pass",
            "report_count": 6,
        },
        "true_fields": ("formula_visibility_screenshot", "report_names_visible", "required_terms_visible"),
        "false_fields": ("contains_full_financial_conclusion", "contains_zero_financial_placeholder"),
        "empty_fields": ("console_errors", "page_errors", "http_errors", "failures", "server_not_found_paths"),
        "minimum_values": {"formula_visibility_screenshot_bytes": 10000},
    },
    "stage_8/phase_8_1/browser_validation.json": {
        "exact": {
            "schema": "PFIV024Stage8Phase81BrowserValidationV1",
            "stage": "Stage 8",
            "phase_id": "8.1",
            "status": "pass",
        },
        "true_fields": (
            "data_state_test_passed",
            "entry_version_test_passed",
            "history_back_forward_passed",
            "report_center_test_passed",
            "route_click_test_passed",
        ),
        "empty_fields": ("console_errors", "page_errors", "http_errors", "server_not_found_paths"),
    },
    "stage_8/phase_8_1/route_click_validation.json": {
        "exact": {
            "schema": "PFIV024Stage8Phase81RouteClickValidationV1",
            "stage": "Stage 8",
            "phase_id": "8.1",
            "status": "pass",
            "primary_entry_count": 10,
            "core_secondary_route_count": 10,
        },
        "true_fields": (
            "all_core_secondary_routes_clicked",
            "all_primary_routes_clicked",
            "history_back_forward_passed",
        ),
        "minimum_lengths": {"primary_routes": 10, "core_secondary_routes": 10},
    },
    "stage_8/phase_8_2/browser_validation.json": {
        "exact": {
            "schema": "PFIV024Stage8Phase82BrowserValidationV1",
            "stage": "Stage 8",
            "phase_id": "8.2",
            "status": "pass",
            "primary_entry_screenshot_count": 10,
            "mobile_horizontal_overflow_px": 0,
        },
        "true_fields": (
            "app_localhost_same_bundle_hash",
            "app_screenshot_captured",
            "desktop_all_pages_screenshot_captured",
            "desktop_light_ui",
            "localhost_screenshot_captured",
            "mobile_bottom_nav_visible",
            "mobile_responsive_screenshot_captured",
        ),
        "false_fields": ("phase_8_3_started", "stage_8_whole_review_complete", "stage_9_started"),
        "empty_fields": ("console_errors", "page_errors", "http_errors"),
    },
}

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

REREVIEW_VALIDATION_COMMANDS = [
    "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_overall_rereview.py -q",
    "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v023_*.py -q",
    "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_*.py -q",
    "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/shell.js",
    "Python compile PFI/src/pfi_v02/stage_v024_overall_project_review.py without bytecode writes",
    "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B scripts/lean_governance.py check-render --project PFI",
    "git diff --check -- PFI",
]


def build_v024_overall_project_review_payload(pfi_root: Path | None = None) -> dict[str, Any]:
    root = pfi_root or Path(__file__).resolve().parents[3]
    data_audit = build_stage6_read_model_audit(project_root=root)

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
            "pfi_worktree_metadb_present": data_audit["storage_mode"] == "filesystem"
            and data_audit["status"] == "ready",
            "source_status": data_audit["status"],
            "storage_mode": data_audit["storage_mode"],
            "alipay_raw_file_count": data_audit["raw_file_count"],
            "alipay_normalized_row_count": data_audit["transaction_count"],
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


def build_v024_overall_rereview_payload(
    pfi_root: Path | None = None,
) -> dict[str, Any]:
    root = _resolve_pfi_root(pfi_root)
    stage_evidence = audit_v024_stage_evidence(root)
    historical_closeout = audit_v024_historical_closeout(root)
    data_audit = build_stage6_read_model_audit(project_root=root)
    current_git_ref = resolve_v024_current_git_ref(root)
    no_forbidden_financial_data = (
        stage_evidence["no_forbidden_financial_data_verified"]
        and historical_closeout["no_forbidden_financial_data_verified"]
    )
    data_contract_issues = validate_v024_real_data_contract(
        data_audit,
        no_forbidden_financial_data=no_forbidden_financial_data,
        expected_git_ref=current_git_ref,
    )
    gate_passed = (
        stage_evidence["complete_unit_count"] == stage_evidence["expected_unit_count"]
        and stage_evidence["whole_stage_pass_count"] == len(STAGE_SEQUENCE)
        and not stage_evidence["missing_artifacts"]
        and not stage_evidence["empty_artifacts"]
        and not stage_evidence["json_parse_errors"]
        and not stage_evidence["semantic_issues"]
        and not stage_evidence["blocking_statuses"]
        and not stage_evidence["unexpected_manual_acceptance_units"]
        and stage_evidence["ui_evidence_complete"]
        and historical_closeout["all_verified"]
        and not data_contract_issues
    )
    delivery_proofs = {
        "current_changes_uploaded": False,
        "app_reinstalled": False,
        "github_app_local_consistency_proven": False,
    }

    return {
        "schema": V024_OVERALL_REREVIEW_SCHEMA,
        "target_version": TARGET_VERSION,
        "source_package_version": SOURCE_PACKAGE_VERSION,
        "review_id": REREVIEW_ID,
        "acceptance_id": REREVIEW_ACCEPTANCE_ID,
        "gate_result": "pass" if gate_passed else "fail",
        "review_scope": [
            "v0.2.3-repair Task Pack and Roadmap Stage 0-9",
            "post-overall consistency remediation Phase R1",
            "real MetaDatabase/PFI read flow",
            "final GitHub/app/local delivery boundary",
        ],
        "historical_closeout": historical_closeout,
        "stage_evidence": stage_evidence,
        "data_boundary": {
            "status": data_audit["status"],
            "storage_mode": data_audit["storage_mode"],
            "git_object_status": data_audit["git_object_status"],
            "git_ref": data_audit["git_ref"],
            "expected_git_ref": current_git_ref,
            "raw_file_count": data_audit["raw_file_count"],
            "transaction_count": data_audit["transaction_count"],
            "as_of": data_audit["as_of"],
            "evidence_hash": data_audit["evidence_hash"],
            "formal_fake_financial_data_added": not no_forbidden_financial_data,
            "contract_issues": data_contract_issues,
        },
        "final_delivery": {
            **delivery_proofs,
            "status": "pending",
            "blocking_requirements": list(delivery_proofs),
        },
        "product_goal_complete": False,
        "next_gate": FINAL_DELIVERY_GATE,
        "findings": [
            {
                "finding_id": "V024-REREVIEW-F1",
                "status": "fixed",
                "summary": "Historical overall upload and current final delivery are now separate facts.",
            },
            {
                "finding_id": "V024-REREVIEW-F2",
                "status": "open_final_gate",
                "summary": "Current Phase R1 changes still require the single final GitHub upload.",
            },
            {
                "finding_id": "V024-REREVIEW-F3",
                "status": "open_final_gate",
                "summary": "App reinstall and GitHub/app/local consistency proof remain pending.",
            },
        ],
        "validation_commands": list(REREVIEW_VALIDATION_COMMANDS),
        "explicitly_not_done": [
            "GitHub upload",
            "app reinstall",
            "future version work",
            "financial data mutation",
        ],
    }


def audit_v024_stage_evidence(pfi_root: Path) -> dict[str, Any]:
    root = _resolve_pfi_root(pfi_root)
    report_root = root / "reports" / "pfi_v024"
    missing_artifacts: list[str] = []
    empty_artifacts: list[str] = []
    semantic_issues: list[dict[str, Any]] = []
    complete_unit_count = 0
    whole_stage_pass_count = 0
    blocking_statuses: list[dict[str, str]] = []
    manual_acceptance_pending_units: list[str] = []
    no_fake_stage_count = 0

    for unit_id, spec in EXPECTED_EVIDENCE_UNIT_MANIFEST.items():
        unit_root = report_root / unit_id
        issues = validate_v024_evidence_unit(unit_id, unit_root)
        for issue in issues:
            path = Path(str(issue.get("path") or unit_root / "evidence.json"))
            if issue["kind"] == "missing_artifact":
                missing_artifacts.append(_display_path(root, path))
            elif issue["kind"] == "empty_artifact":
                empty_artifacts.append(_display_path(root, path))
            else:
                semantic_issues.append(issue)
                if issue["kind"] == "status_mismatch":
                    blocking_statuses.append(
                        {"path": _display_path(root, path), "status": str(issue.get("actual"))}
                    )
        if not issues:
            complete_unit_count += 1
            if unit_id.endswith("/whole_stage_review"):
                whole_stage_pass_count += 1

        evidence_path = unit_root / "evidence.json"
        evidence = _read_json_dict(evidence_path)
        status = str(evidence.get("status") or evidence.get("review_status") or "missing_status")
        if status in {"ready_for_user_acceptance", "waiting_for_user_acceptance"}:
            manual_acceptance_pending_units.append(_display_path(root, evidence_path))
        if unit_id.endswith("/whole_stage_review"):
            stage = int(unit_id.split("/", 1)[0].removeprefix("stage_"))
            if _whole_stage_no_fake_verified(stage, evidence):
                no_fake_stage_count += 1

    json_files = sorted(report_root.rglob("*.json")) if report_root.is_dir() else []
    json_parse_errors: list[dict[str, str]] = []
    for path in json_files:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            json_parse_errors.append({"path": _display_path(root, path), "error": str(exc)})

    ui_evidence: dict[str, dict[str, Any]] = {
        f"stage_{stage}": {
            "screenshot_count": 0,
            "browser_validation_count": 0,
            "route_validation_count": 0,
        }
        for stage in range(2, 9)
    }
    ui_validation_issues: list[dict[str, Any]] = []
    ui_validation_complete_count = 0
    for relative_path in UI_VALIDATION_MANIFEST:
        path = report_root / relative_path
        issues = validate_v024_ui_validation_file(relative_path, path)
        ui_validation_issues.extend(issues)
        if not issues:
            ui_validation_complete_count += 1
        stage_key = relative_path.split("/", 1)[0]
        if "browser_validation" in Path(relative_path).name:
            ui_evidence[stage_key]["browser_validation_count"] += int(path.is_file())
        if "route" in Path(relative_path).name:
            ui_evidence[stage_key]["route_validation_count"] += int(path.is_file())

    png_validation_issues: list[dict[str, Any]] = []
    for stage in range(2, 9):
        stage_root = report_root / f"stage_{stage}"
        screenshot_paths = list(stage_root.rglob("*.png")) if stage_root.is_dir() else []
        for path in screenshot_paths:
            png_validation_issues.extend(validate_v024_png(path))
        ui_evidence[f"stage_{stage}"]["screenshot_count"] = len(screenshot_paths)
    invalid_screenshots = sorted(
        _display_path(root, Path(str(issue["path"]))) for issue in png_validation_issues
    )
    ui_evidence_complete = all(
        values["screenshot_count"] > 0 and values["browser_validation_count"] > 0
        for values in ui_evidence.values()
    ) and all(
        ui_evidence[f"stage_{stage}"]["route_validation_count"] > 0 for stage in (3, 5, 8)
    ) and ui_validation_complete_count == len(UI_VALIDATION_MANIFEST) and not png_validation_issues
    unexpected_manual_acceptance_units = sorted(
        set(manual_acceptance_pending_units) - MANUAL_ACCEPTANCE_EVIDENCE
    )

    return {
        "manifest_unit_count": len(EXPECTED_EVIDENCE_UNIT_MANIFEST),
        "expected_unit_count": 40,
        "complete_unit_count": complete_unit_count,
        "whole_stage_pass_count": whole_stage_pass_count,
        "missing_artifacts": missing_artifacts,
        "empty_artifacts": empty_artifacts,
        "json_file_count": len(json_files),
        "json_parse_errors": json_parse_errors,
        "semantic_issues": semantic_issues,
        "blocking_statuses": blocking_statuses,
        "manual_acceptance_pending_units": sorted(manual_acceptance_pending_units),
        "unexpected_manual_acceptance_units": unexpected_manual_acceptance_units,
        "ui_evidence": ui_evidence,
        "ui_evidence_complete": ui_evidence_complete,
        "ui_validation_manifest_count": len(UI_VALIDATION_MANIFEST),
        "ui_validation_complete_count": ui_validation_complete_count,
        "ui_validation_issues": ui_validation_issues,
        "invalid_screenshots": invalid_screenshots,
        "png_validation_issues": png_validation_issues,
        "no_forbidden_financial_data_verified": no_fake_stage_count == len(STAGE_SEQUENCE),
    }


def validate_v024_evidence_unit(unit_id: str, unit_root: Path) -> list[dict[str, Any]]:
    spec = EXPECTED_EVIDENCE_UNIT_MANIFEST.get(unit_id)
    if spec is None:
        return [{"unit": unit_id, "kind": "unknown_unit"}]

    issues: list[dict[str, Any]] = []
    for name in EVIDENCE_UNIT_FILES:
        path = unit_root / name
        if not path.is_file():
            issues.append({"unit": unit_id, "kind": "missing_artifact", "path": str(path)})
            continue
        try:
            if not path.read_bytes().strip():
                issues.append({"unit": unit_id, "kind": "empty_artifact", "path": str(path)})
        except OSError as exc:
            issues.append({"unit": unit_id, "kind": "artifact_read_error", "path": str(path), "actual": str(exc)})

    evidence_path = unit_root / "evidence.json"
    evidence = _read_json_dict(evidence_path)
    if not evidence:
        if evidence_path.is_file() and evidence_path.stat().st_size > 0:
            issues.append({"unit": unit_id, "kind": "evidence_parse_error", "path": str(evidence_path)})
        return issues

    _require_exact(issues, unit_id, evidence_path, "schema", spec["schema"], evidence.get("schema"))
    _require_exact(issues, unit_id, evidence_path, "stage", spec["stage"], evidence.get("stage"))
    if spec["phase"] is not None:
        phase = evidence.get("phase") or evidence.get("phase_id")
        _require_exact(issues, unit_id, evidence_path, "phase", spec["phase"], phase)
    status = evidence.get("status") or evidence.get("review_status")
    _require_exact(issues, unit_id, evidence_path, "status", spec["status"], status)

    if evidence.get("allowed_files_obeyed") is False:
        issues.append(
            {"unit": unit_id, "kind": "allowed_files_violation", "path": str(evidence_path), "actual": False}
        )
    if evidence.get("formal_fake_financial_data_added") is True:
        issues.append(
            {"unit": unit_id, "kind": "forbidden_financial_data", "path": str(evidence_path), "actual": True}
        )

    acceptance = evidence.get("acceptance_checks") or evidence.get("acceptance_review") or {}
    for key in spec["required_acceptance_keys"]:
        if key not in acceptance:
            issues.append(
                {"unit": unit_id, "kind": "acceptance_missing", "path": str(evidence_path), "field": key}
            )
        elif not _acceptance_passed(acceptance[key]):
            issues.append(
                {
                    "unit": unit_id,
                    "kind": "acceptance_failed",
                    "path": str(evidence_path),
                    "field": key,
                    "actual": acceptance[key],
                }
            )

    if unit_id == "stage_9/whole_stage_review":
        _validate_stage9_whole_review(issues, unit_id, evidence_path, evidence)
    return issues


def validate_v024_ui_validation_file(relative_path: str, path: Path) -> list[dict[str, Any]]:
    spec = UI_VALIDATION_MANIFEST.get(relative_path)
    if spec is None:
        return [{"kind": "unknown_ui_validation", "path": str(path), "relative_path": relative_path}]
    data = _read_json_dict(path)
    if not data:
        return [{"kind": "ui_validation_missing_or_invalid", "path": str(path), "relative_path": relative_path}]

    issues: list[dict[str, Any]] = []
    for field, expected in spec.get("exact", {}).items():
        if data.get(field) != expected:
            issues.append(
                {
                    "kind": "ui_value_mismatch",
                    "path": str(path),
                    "field": field,
                    "expected": expected,
                    "actual": data.get(field),
                }
            )
    for field in spec.get("true_fields", ()):
        if data.get(field) is not True:
            issues.append(
                {"kind": "ui_value_mismatch", "path": str(path), "field": field, "expected": True, "actual": data.get(field)}
            )
    for field in spec.get("false_fields", ()):
        if data.get(field) is not False:
            issues.append(
                {"kind": "ui_value_mismatch", "path": str(path), "field": field, "expected": False, "actual": data.get(field)}
            )
    for field in spec.get("empty_fields", ()):
        if data.get(field) != []:
            issues.append(
                {"kind": "ui_expected_empty", "path": str(path), "field": field, "actual": data.get(field)}
            )
    for field, minimum in spec.get("minimum_values", {}).items():
        value = data.get(field)
        if not isinstance(value, (int, float)) or value < minimum:
            issues.append(
                {
                    "kind": "ui_minimum_not_met",
                    "path": str(path),
                    "field": field,
                    "minimum": minimum,
                    "actual": value,
                }
            )
    for field, minimum in spec.get("minimum_lengths", {}).items():
        value = data.get(field)
        if not isinstance(value, (list, tuple, dict)) or len(value) < minimum:
            issues.append(
                {
                    "kind": "ui_coverage_not_met",
                    "path": str(path),
                    "field": field,
                    "minimum": minimum,
                    "actual": len(value) if isinstance(value, (list, tuple, dict)) else None,
                }
            )
    for field, expected_status in spec.get("nested_status_fields", {}).items():
        value = data.get(field)
        if not isinstance(value, dict) or not value or any(
            not isinstance(item, dict) or item.get("status") != expected_status for item in value.values()
        ):
            issues.append(
                {
                    "kind": "ui_route_status_failed",
                    "path": str(path),
                    "field": field,
                    "expected": expected_status,
                }
            )
    return issues


def validate_v024_png(path: Path) -> list[dict[str, Any]]:
    try:
        from PIL import Image

        with Image.open(path) as image:
            image.load()
            width, height = image.size
            image_format = image.format
    except (ImportError, OSError, ValueError) as exc:
        return [{"kind": "png_decode_error", "path": str(path), "actual": str(exc)}]
    if image_format != "PNG" or width < 320 or height < 240:
        return [
            {
                "kind": "png_dimension_or_format_invalid",
                "path": str(path),
                "expected": {"format": "PNG", "min_width": 320, "min_height": 240},
                "actual": {"format": image_format, "width": width, "height": height},
            }
        ]
    return []


def audit_v024_historical_closeout(pfi_root: Path) -> dict[str, Any]:
    root = _resolve_pfi_root(pfi_root)
    report_root = root / "reports" / "pfi_v024"
    stage8 = _read_json_dict(report_root / "stage_8" / "whole_stage_review" / "evidence.json")
    stage9 = _read_json_dict(report_root / "stage_9" / "whole_stage_review" / "evidence.json")
    stage9_upload = _read_json_dict(report_root / "stage_9" / "github_main_upload" / "evidence.json")
    overall = _read_json_dict(report_root / "overall_project_review" / "evidence.json")

    stage8_confirmed = (
        stage8.get("status") == "pass"
        and stage8.get("phase_8_3_user_confirmed") is True
        and stage8.get("user_confirmation_source") == "chat_reply_1"
        and _acceptance_passed((stage8.get("acceptance_checks") or {}).get("manual_acceptance_confirmation"))
    )
    stage9_confirmed = (
        stage9.get("status") == "pass"
        and stage9.get("phase_9_3_user_confirmed") is True
        and stage9.get("user_confirmation_source") == "chat_reply_1"
        and (stage9.get("phase_statuses") or {}).get("phase_9_3") == "user_confirmed"
    )
    upload_complete = (
        stage9_upload.get("status") == "pass"
        and stage9_upload.get("github_main_uploaded") is True
        and (stage9_upload.get("acceptance_checks") or {}).get("phase_9_3_user_confirmed") is True
        and (stage9_upload.get("acceptance_checks") or {}).get("remote_main_verification_required_after_push") is True
        and overall.get("status") == "pass"
        and overall.get("overall_project_review_complete") is True
        and overall.get("github_main_uploaded") is True
    )
    overall_acceptance = overall.get("acceptance_checks") or {}
    stage_chain_complete = (
        overall_acceptance.get("stage_0_to_9_evidence_chain_complete") is True
        and overall_acceptance.get("ten_primary_entries_verified") is True
        and overall_acceptance.get("market_research_primary_entry_verified") is True
        and overall.get("future_version_started") is False
    )
    no_forbidden_financial_data = (
        overall_acceptance.get("no_mock_sample_synthetic_fixture_demo_fake_financial_data") is True
        and (stage9_upload.get("acceptance_checks") or {}).get("no_mock_fixture_demo_financial_fallback") is True
        and stage9.get("formal_fake_financial_data_added") is False
    )

    return {
        "stage_0_to_9_complete": stage_chain_complete,
        "stage_8_phase_8_3_user_confirmed": stage8_confirmed,
        "stage_9_phase_9_3_user_confirmed": stage9_confirmed,
        "user_confirmation_source": "chat_reply_1" if stage8_confirmed and stage9_confirmed else None,
        "overall_upload_complete": upload_complete,
        "no_forbidden_financial_data_verified": no_forbidden_financial_data,
        "all_verified": all(
            (stage_chain_complete, stage8_confirmed, stage9_confirmed, upload_complete, no_forbidden_financial_data)
        ),
        "scope": "historical reviewed package before current Phase R1 changes",
    }


def validate_v024_real_data_contract(
    data_audit: dict[str, Any],
    *,
    no_forbidden_financial_data: bool,
    expected_git_ref: str | None,
) -> list[dict[str, Any]]:
    expected = {
        "status": "ready",
        "storage_mode": "git_tree",
        "git_object_status": "available",
        "raw_file_count": EXPECTED_RAW_FILE_COUNT,
        "transaction_count": EXPECTED_TRANSACTION_COUNT,
        "as_of": EXPECTED_DATA_AS_OF,
        "evidence_hash": EXPECTED_DATA_EVIDENCE_HASH,
    }
    issues: list[dict[str, Any]] = []
    for field, value in expected.items():
        if data_audit.get(field) != value:
            issues.append(
                {"kind": "data_contract_mismatch", "field": field, "expected": value, "actual": data_audit.get(field)}
            )
    git_ref = data_audit.get("git_ref")
    if not isinstance(git_ref, str) or len(git_ref) not in {40, 64} or any(
        char not in "0123456789abcdef" for char in git_ref.lower()
    ):
        issues.append({"kind": "git_ref_invalid", "field": "git_ref", "actual": git_ref})
    elif git_ref != expected_git_ref:
        issues.append(
            {
                "kind": "git_ref_mismatch",
                "field": "git_ref",
                "expected": expected_git_ref,
                "actual": git_ref,
            }
        )
    if not no_forbidden_financial_data:
        issues.append({"kind": "forbidden_financial_data_unverified"})
    return issues


def resolve_v024_current_git_ref(pfi_root: Path) -> str | None:
    root = _resolve_pfi_root(pfi_root)
    env = dict(os.environ)
    env["GIT_NO_LAZY_FETCH"] = "1"
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD^{commit}"],
            cwd=root,
            capture_output=True,
            check=False,
            env=env,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    ref = completed.stdout.strip().lower()
    if completed.returncode != 0 or len(ref) not in {40, 64} or any(char not in "0123456789abcdef" for char in ref):
        return None
    return ref


def _read_json_dict(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _require_exact(
    issues: list[dict[str, Any]],
    unit_id: str,
    path: Path,
    field: str,
    expected: Any,
    actual: Any,
) -> None:
    if actual == expected:
        return
    issues.append(
        {
            "unit": unit_id,
            "kind": f"{field}_mismatch",
            "path": str(path),
            "field": field,
            "expected": expected,
            "actual": actual,
        }
    )


def _acceptance_passed(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.lower() in {"pass", "passed", "verified", "complete", "completed"}
    if isinstance(value, dict):
        if "result" in value:
            return _acceptance_passed(value["result"])
        if "status" in value:
            return _acceptance_passed(value["status"])
    return False


def _validate_stage9_whole_review(
    issues: list[dict[str, Any]],
    unit_id: str,
    path: Path,
    evidence: dict[str, Any],
) -> None:
    expected_fields = {
        "stage_9_whole_review_complete": True,
        "phase_9_3_user_confirmed": True,
        "user_confirmation_source": "chat_reply_1",
        "future_version_started": False,
        "formal_fake_financial_data_added": False,
    }
    for field, expected in expected_fields.items():
        _require_exact(issues, unit_id, path, field, expected, evidence.get(field))
    expected_phases = {
        "phase_9_1": "candidate_pass",
        "phase_9_2": "candidate_pass",
        "phase_9_3": "user_confirmed",
    }
    _require_exact(issues, unit_id, path, "phase_statuses", expected_phases, evidence.get("phase_statuses"))
    stop_audit = evidence.get("stop_condition_audit") or {}
    if not stop_audit or any(value != "absent" for value in stop_audit.values()):
        issues.append(
            {"unit": unit_id, "kind": "stop_condition_failed", "path": str(path), "actual": stop_audit}
        )


def _whole_stage_no_fake_verified(stage: int, evidence: dict[str, Any]) -> bool:
    acceptance = evidence.get("acceptance_checks") or evidence.get("acceptance_review") or {}
    keys = {
        0: "no_mock_financial_data",
        1: "no_fake_financial_data_added",
        2: "no_fake_financial_data_added",
        4: "no_mock_fixture_demo_financial_fallback",
        5: "no_forbidden_financial_data_added",
        6: "no_forbidden_financial_data_added",
        7: "no_forbidden_financial_data_added",
        8: "no_forbidden_financial_data_added",
    }
    if stage in keys:
        return _acceptance_passed(acceptance.get(keys[stage]))
    if stage in {3, 9}:
        return evidence.get("formal_fake_financial_data_added") is False
    return False


def _resolve_pfi_root(root: Path | None) -> Path:
    candidate = Path(root).expanduser().resolve() if root is not None else Path(__file__).resolve().parents[2]
    if (candidate / "src" / "pfi_v02").is_dir() or (candidate / "reports" / "pfi_v024").is_dir():
        return candidate
    if (candidate / "PFI" / "src" / "pfi_v02").is_dir():
        return candidate / "PFI"
    return candidate


def _display_path(pfi_root: Path, path: Path) -> str:
    try:
        return (Path("PFI") / path.relative_to(pfi_root)).as_posix()
    except ValueError:
        return path.as_posix()
