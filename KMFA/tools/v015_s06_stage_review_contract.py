#!/usr/bin/env python3
"""Executable aggregate-only contract for the KMFA v1.5 S06 Stage Review."""

from __future__ import annotations

from typing import Any

from KMFA.tools import v015_s06_p3_baseline_coverage_boundary as p3


RUN_PHASE_ID = "V015_S06_STAGE_REVIEW"
TASK_ID = "KMFA-V015-S06-STAGE-REVIEW-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S06-STAGE-REVIEW"
VERSION = "1.5.0-dev-s06-review"

CHECK_IDS = (
    "FIXTURE_PROJECT_COUNT_EXACT",
    "FIXTURE_FIELD_COUNT_EXACT",
    "FIXTURE_MONEY_ZERO_DIFFERENCE",
    "FIXTURE_IMMUTABLE",
    "OPEN_ITEM_CATEGORY_ACCOUNTING",
    "OPEN_ITEM_STATUS_ACCOUNTING",
    "OPEN_ITEM_ROUTE_COVERAGE",
    "SCENARIO_DISPOSITION_ACCOUNTING",
    "EMPIRICAL_GAP_EXPLICIT",
    "DOWNSTREAM_BOUNDARIES_CLOSED",
    "PUBLIC_PROJECTION_AGGREGATE_ONLY",
    "NO_RAW_GITHUB_APP_MUTATION",
)


def _check(check_id: str, condition: bool) -> dict[str, str]:
    return {"check_id": check_id, "status": "PASS" if condition else "FAIL"}


def public_verification() -> dict[str, Any]:
    """Revalidate the private fixture while returning aggregate-only evidence."""

    projection = p3.current_public_projection()
    categories = projection["open_item_category_counts"]
    statuses = projection["open_item_status_counts"]
    checks = [
        _check(CHECK_IDS[0], projection["fixture_project_count"] == 8),
        _check(CHECK_IDS[1], projection["fixture_accepted_field_count"] == 92),
        _check(CHECK_IDS[2], projection["fixture_money_difference_cents"] == 0),
        _check(CHECK_IDS[3], projection["fixture_immutable"] is True and projection["fixture_overwrite_allowed"] is False),
        _check(CHECK_IDS[4], categories == {"AMBIGUOUS": 46, "CONFLICT": 6, "MISSING": 82, "NOT_APPLICABLE": 13} and sum(categories.values()) == 147),
        _check(CHECK_IDS[5], statuses == {"OPEN": 128, "ROUTED_DERIVATION": 6, "ROUTED_EXCLUSION": 13} and sum(statuses.values()) == 147),
        _check(CHECK_IDS[6], projection["open_item_impact_coverage_bps"] == 10000 and projection["open_item_resolution_path_coverage_bps"] == 10000),
        _check(CHECK_IDS[7], projection["required_scenario_count"] == 5 and projection["covered_scenario_count"] == 4 and projection["future_sample_count"] == 1 and projection["coverage_disposition_count"] == 5),
        _check(CHECK_IDS[8], projection["empirical_coverage_complete"] is False and projection["registered_gap_satisfies_stop_condition"] is True),
        _check(CHECK_IDS[9], projection["downstream_cross_period_claim_allowed"] is False and projection["tax_normalization_allowed"] is False and projection["open_items_may_be_treated_as_resolved"] is False),
        _check(CHECK_IDS[10], projection["public_project_identity_count"] == 0 and projection["public_money_value_count"] == 0 and projection["public_source_locator_count"] == 0 and projection["public_private_fixture_hash_count"] == 0),
        _check(CHECK_IDS[11], projection["raw_mutation_performed"] is False and projection["github_upload_performed"] is False and projection["app_reinstall_performed"] is False),
    ]
    failed = sum(row["status"] != "PASS" for row in checks)
    return {
        "schema_version": "kmfa.v015.s06_stage_review.binding_verification.v1",
        "run_phase_id": RUN_PHASE_ID,
        "public_safe": True,
        "private_fixture_revalidated": True,
        "golden_fixture_project_count": projection["fixture_project_count"],
        "golden_fixture_accepted_field_count": projection["fixture_accepted_field_count"],
        "golden_fixture_money_difference_cents": projection["fixture_money_difference_cents"],
        "open_item_count": projection["open_item_count"],
        "open_item_status_counts": statuses,
        "required_scenario_count": projection["required_scenario_count"],
        "observed_scenario_count": projection["covered_scenario_count"],
        "registered_future_sample_count": projection["future_sample_count"],
        "empirical_coverage_complete": False,
        "registered_gap_satisfies_stop_condition": True,
        "downstream_cross_period_claim_allowed": False,
        "tax_normalization_allowed": False,
        "open_items_may_be_treated_as_resolved": False,
        "checks": checks,
        "accounting": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }
