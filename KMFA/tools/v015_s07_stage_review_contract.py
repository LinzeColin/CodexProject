#!/usr/bin/env python3
"""Executable, aggregate-only contract for the KMFA v1.5 S07 Stage Review."""

from __future__ import annotations

from typing import Any

from KMFA.tools import v015_s07_p1_zero_delta_validator as p1
from KMFA.tools import v015_s07_p2_conflict_classification as p2
from KMFA.tools import v015_s07_p3_release_gate as p3


RUN_PHASE_ID = "V015_S07_STAGE_REVIEW"
TASK_ID = "KMFA-V015-S07-STAGE-REVIEW-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S07-STAGE-REVIEW"
VERSION = "1.5.0-dev-s07-review"

CHECK_IDS = (
    "P1_ZERO_DIFFERENCE",
    "P1_OPEN_BOUNDARY",
    "P1_PUBLIC_SAFE",
    "P2_QUEUE_CONTINUITY",
    "P2_CONFLICT_BOUNDARY",
    "P2_SYSTEM_RESPONSIBILITY",
    "P2_PUBLIC_SAFE",
    "P3_HUMAN_LABELS",
    "P3_CLOSURE_PROTOCOL",
    "P3_REGRESSION_ALL",
    "P3_CURRENT_REPORT_CLOSED",
    "CROSS_PHASE_OPEN_COUNT",
    "CROSS_PHASE_CONFLICT_COUNT",
    "CROSS_PHASE_PROJECT_COUNT",
    "NO_RAW_OR_RELEASE_MUTATION",
    "NEXT_STAGE_CLOSED",
)


def _check(check_id: str, condition: bool) -> dict[str, str]:
    return {"check_id": check_id, "status": "PASS" if condition else "FAIL"}


def public_verification() -> dict[str, Any]:
    """Re-run the three live kernels and return only public-safe aggregate facts."""

    p1_public = p1.public_projection()
    p1_private = p1.validate_private_golden_scope()
    p2_public = p2.public_projection()
    p2_private = p2.validate_private_conflict_boundary()
    p3_public = p3.public_projection()
    p3_private = p3.validate_private_regression_gate()

    checks = [
        _check(
            CHECK_IDS[0],
            p1_private["private_zero_difference"] is True
            and p1_private["private_formula_fail_count"] == 0
            and p1_public["money_tolerance_cents"] == 0,
        ),
        _check(
            CHECK_IDS[1],
            p1_private["open_unconfirmed_item_count"] == 128
            and p1_private["open_items_may_be_treated_as_resolved"] is False,
        ),
        _check(
            CHECK_IDS[2],
            all(
                p1_public[key] == 0
                for key in (
                    "private_project_identity_count_public",
                    "private_money_value_count_public",
                    "private_source_locator_count_public",
                    "private_digest_count_public",
                )
            ),
        ),
        _check(
            CHECK_IDS[3],
            p2_private["private_queue_item_count"] == 147
            and p2_private["private_open_unconfirmed_item_count"] == 128,
        ),
        _check(
            CHECK_IDS[4],
            p2_private["private_conflict_candidate_count"] == 6
            and p2_private["private_conflict_auto_selected_count"] == 0
            and p2_private["private_conflict_candidates_treated_as_resolved"] is False,
        ),
        _check(
            CHECK_IDS[5],
            p2_public["persistent_same_source_mismatch_is_system_error"] is True
            and p2_public["system_problem_assigned_to_user_count"] == 0,
        ),
        _check(
            CHECK_IDS[6],
            all(
                p2_private[key] == 0
                for key in (
                    "private_value_count_public",
                    "private_identity_count_public",
                    "private_source_locator_count_public",
                    "private_digest_count_public",
                )
            ),
        ),
        _check(
            CHECK_IDS[7],
            p3_public["status_labels_zh"] == ["可内部使用", "需确认", "暂不可使用"]
            and p3_public["ui_technical_abbreviation_count"] == 0,
        ),
        _check(
            CHECK_IDS[8],
            p3_public["closure_kind_count"] == 4
            and p3_public["closure_success_count"] == 4
            and p3_public["status_only_closure_rejected"] is True
            and p3_public["missing_recalculation_rejected"] is True,
        ),
        _check(
            CHECK_IDS[9],
            p3_private["private_historical_project_count"] == 8
            and p3_private["private_selected_for_rerun_count"] == 8
            and p3_private["private_regression_pass_count"] == 8
            and p3_private["private_regression_fail_count"] == 0
            and p3_private["private_regression_pass_rate_bps"] == 10000,
        ),
        _check(
            CHECK_IDS[10],
            p3_public["current_report_display_label_zh"] == "暂不可使用"
            and p3_public["current_formal_report_release_allowed"] is False
            and p3_public["current_internal_use_allowed"] is False,
        ),
        _check(
            CHECK_IDS[11],
            p1_private["open_unconfirmed_item_count"]
            == p2_private["private_open_unconfirmed_item_count"]
            == p3_private["private_open_unconfirmed_item_count"]
            == 128,
        ),
        _check(
            CHECK_IDS[12],
            p2_private["private_conflict_candidate_count"]
            == p3_public["current_private_conflict_candidate_count"]
            == 6,
        ),
        _check(
            CHECK_IDS[13],
            p1_private["private_project_count"]
            == p3_private["private_historical_project_count"]
            == p3_private["private_selected_for_rerun_count"]
            == 8,
        ),
        _check(
            CHECK_IDS[14],
            all(
                projection["raw_root_access_count"] == 0
                and projection["raw_business_content_read"] is False
                and projection["raw_mutation_performed"] is False
                and projection["formal_report_generated"] is False
                and projection["github_upload_performed"] is False
                and projection["app_reinstall_performed"] is False
                and projection["business_execution_performed"] is False
                for projection in (p1_public, p2_public, p3_public)
            ),
        ),
        _check(
            CHECK_IDS[15],
            p3_public["s08_p1_entry_allowed"] is False
            and p3_public["s07_stage_review_started"] is False,
        ),
    ]
    failed = sum(row["status"] != "PASS" for row in checks)
    return {
        "schema_version": "kmfa.v015.s07_stage_review.binding_verification.v1",
        "run_phase_id": RUN_PHASE_ID,
        "public_safe": True,
        "p1_private_project_count": p1_private["private_project_count"],
        "p1_private_accepted_field_count": p1_private["private_accepted_field_count"],
        "p1_private_formula_check_count": p1_private["private_formula_check_count"],
        "p1_private_formula_fail_count": p1_private["private_formula_fail_count"],
        "private_zero_difference": p1_private["private_zero_difference"],
        "open_unconfirmed_item_count": p1_private["open_unconfirmed_item_count"],
        "private_queue_item_count": p2_private["private_queue_item_count"],
        "private_conflict_candidate_count": p2_private["private_conflict_candidate_count"],
        "private_conflict_auto_selected_count": p2_private["private_conflict_auto_selected_count"],
        "private_historical_project_count": p3_private["private_historical_project_count"],
        "private_regression_pass_count": p3_private["private_regression_pass_count"],
        "private_regression_fail_count": p3_private["private_regression_fail_count"],
        "private_regression_pass_rate_bps": p3_private["private_regression_pass_rate_bps"],
        "current_report_display_label_zh": p3_public["current_report_display_label_zh"],
        "current_formal_report_release_allowed": p3_public["current_formal_report_release_allowed"],
        "checks": checks,
        "accounting": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }
