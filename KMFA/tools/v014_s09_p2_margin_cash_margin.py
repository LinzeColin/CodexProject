#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S09-P2 margin and cash margin evidence.

This validates the v0.1.4 S09-P1 dependency, reuses the public-safe
legacy S09-P2 margin artifacts, and records the phase-level no-go /
upload-deferred boundary for the v0.1.4 Stage 1-18 run.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s09_p1_project_cost_fact_layer import (
    validate_v014_s09_p1_project_cost_fact_layer,
)
from KMFA.tools.project_margin_cash_margin import (
    DEFAULT_OUTPUT_DIFFERENCE_SUMMARY as LEGACY_DIFFERENCE_SUMMARY_PATH,
    DEFAULT_OUTPUT_MANIFEST as LEGACY_MARGIN_MANIFEST_PATH,
    DEFAULT_OUTPUT_MARGIN_RECORDS as LEGACY_MARGIN_RECORDS_PATH,
    DEFAULT_OUTPUT_STAGE_MANIFEST as LEGACY_STAGE_MANIFEST_PATH,
    REQUIRED_MARGIN_METRICS,
    read_json,
    read_jsonl,
    validate_project_margin_cash_margin_artifacts,
)


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S09_P2_MARGIN_CASH_MARGIN")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/margin_cash_margin_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/margin_cash_margin_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
RISK_REGISTER_PATH = PUBLIC_OUTPUT_DIR / "human/risk_register.md"
ROLLBACK_PLAN_PATH = PUBLIC_OUTPUT_DIR / "human/rollback_plan.md"
TASK_ID = "KMFA-V014-S09-P2-MARGIN-CASH-MARGIN-20260704"
ACCEPTANCE_ID = "ACC-V014-S09-P2-MARGIN-CASH-MARGIN"
SCHEMA_VERSION = "kmfa.v014_s09_p2_margin_cash_margin.v1"
PHASE_SCOPE = "v014_s09_p2_margin_cash_margin_only"
RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_PHASE = "S09-P3"
NEXT_INSTRUCTION = (
    "Start v0.1.4 S09-P3 scope reconciliation as a separate run only after user instruction. "
    "Do not perform Stage 9 review, GitHub upload, raw value matching, lineage full check, "
    "formal report release, live connector, app reinstall, OpMe deep coupling, Redcircle automatic connector, "
    "or business execution in the S09-P2 run. GitHub main upload remains deferred until v1.4 Stage 1-18 "
    "are complete, overall review has passed, and findings are fixed."
)


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def validate_s09_p1_dependency() -> dict[str, Any]:
    result = validate_v014_s09_p1_project_cost_fact_layer()
    if result.get("stage_id") != "S09" or result.get("phase_id") != "S09-P1":
        raise RuntimeError("v0.1.4 S09-P2 requires validated S09-P1 dependency")
    if result.get("status") != "completed_validated_local_only_no_go_upload_deferred_project_cost_fact_layer":
        raise RuntimeError("v0.1.4 S09-P2 requires completed S09-P1 dependency")
    progress = result.get("stage9_phase_progress", {})
    if progress.get("s09_p2_performed") is not False:
        raise RuntimeError("S09-P1 dependency must not already include S09-P2")
    if result.get("github_upload", {}).get("github_upload_performed") is not False:
        raise RuntimeError("S09-P1 dependency must not include GitHub upload")
    if result.get("github_upload", {}).get("github_upload_deferred_until_v014_stage1_18_complete") is not True:
        raise RuntimeError("S09-P1 dependency must keep upload deferred")
    return result


def _count_false_values(container: dict[str, Any]) -> int:
    return sum(1 for value in container.values() if value is False)


def _count_nested_false_safety(records: list[dict[str, Any]]) -> int:
    total = 0
    for record in records:
        safety = record.get("public_repo_safety", {})
        if isinstance(safety, dict):
            total += _count_false_values(safety)
    return total


def validate_legacy_s09_p2_artifacts() -> dict[str, Any]:
    legacy_manifest = read_json(LEGACY_MARGIN_MANIFEST_PATH)
    margin_records = read_jsonl(LEGACY_MARGIN_RECORDS_PATH)
    difference_summary = read_jsonl(LEGACY_DIFFERENCE_SUMMARY_PATH)
    legacy_stage_manifest = read_json(LEGACY_STAGE_MANIFEST_PATH)
    validate_project_margin_cash_margin_artifacts(legacy_manifest, margin_records, difference_summary)

    summary = legacy_manifest.get("summary", {})
    upstream = legacy_manifest.get("upstream_quality_summary", {})
    difference_types = Counter(str(item.get("difference_type")) for item in difference_summary)
    authority_system_overwrite_allowed_count = sum(
        1 for record in margin_records if record.get("authority_system_overwrite_allowed") is True
    )
    public_amount_values_committed_count = sum(
        1 for record in margin_records if record.get("public_amount_values_committed") is True
    ) + sum(1 for item in difference_summary if item.get("public_amount_values_committed") is True)
    raw_layer_write_allowed_count = sum(
        1 for record in margin_records if record.get("raw_layer_write_allowed") is True
    ) + sum(1 for item in difference_summary if item.get("raw_layer_write_allowed") is True)
    formal_report_allowed_count = sum(
        1 for record in margin_records if record.get("formal_report_allowed") is True
    )
    s09_p3_reconciliation_performed_count = sum(
        1 for item in difference_summary if item.get("s09_p3_reconciliation_performed") is True
    )
    authority_hash_ref_count = sum(len(record.get("authority_value_hash_refs", {})) for record in margin_records)
    authority_private_ref_count = sum(len(record.get("authority_value_private_refs", {})) for record in margin_records)
    system_hash_ref_count = sum(
        len(record.get("system_recomputed_value_hash_refs", {})) for record in margin_records
    )
    system_private_ref_count = sum(
        len(record.get("system_recomputed_value_private_refs", {})) for record in margin_records
    )
    cash_hash_ref_count = sum(len(record.get("cash_margin_value_hash_refs", {})) for record in margin_records)
    cash_private_ref_count = sum(len(record.get("cash_margin_value_private_refs", {})) for record in margin_records)

    return {
        "legacy_manifest": legacy_manifest,
        "legacy_stage_manifest": legacy_stage_manifest,
        "required_margin_metric_count": len(REQUIRED_MARGIN_METRICS),
        "required_margin_metrics": list(REQUIRED_MARGIN_METRICS),
        "project_cost_fact_record_count": summary.get("project_cost_fact_record_count"),
        "margin_record_count": len(margin_records),
        "difference_summary_count": len(difference_summary),
        "authority_field_group_count": summary.get("authority_field_group_count"),
        "upstream_manual_review_queue_count": summary.get("upstream_manual_review_queue_count"),
        "upstream_unresolved_difference_count": summary.get("upstream_unresolved_difference_count"),
        "zero_delta_fail_count": upstream.get("zero_delta_fail_count"),
        "blocked_quality_result_count": upstream.get("blocked_quality_result_count"),
        "formal_calculation_blocked": upstream.get("formal_calculation_blocked"),
        "calculation_status": legacy_manifest.get("calculation_status"),
        "mapping_version": legacy_manifest.get("mapping_version"),
        "formula_version": legacy_manifest.get("formula_version"),
        "difference_type_count": len(difference_types),
        "difference_records_by_type": dict(sorted(difference_types.items())),
        "authority_hash_ref_count": authority_hash_ref_count,
        "authority_private_ref_count": authority_private_ref_count,
        "system_hash_ref_count": system_hash_ref_count,
        "system_private_ref_count": system_private_ref_count,
        "cash_hash_ref_count": cash_hash_ref_count,
        "cash_private_ref_count": cash_private_ref_count,
        "authority_system_overwrite_allowed_count": authority_system_overwrite_allowed_count,
        "public_amount_values_committed_count": public_amount_values_committed_count,
        "raw_layer_write_allowed_count": raw_layer_write_allowed_count,
        "formal_report_allowed_count": formal_report_allowed_count,
        "s09_p3_reconciliation_performed_count": s09_p3_reconciliation_performed_count,
        "quality_gate_false_count": _count_false_values(legacy_manifest.get("quality_gate", {})),
        "public_safety_false_count": _count_false_values(legacy_manifest.get("public_repo_safety", {})),
        "record_public_safety_false_count": _count_nested_false_safety(margin_records),
        "difference_public_safety_false_count": _count_nested_false_safety(difference_summary),
        "stage_scope": legacy_manifest.get("stage_scope", {}),
        "quality_gate": legacy_manifest.get("quality_gate", {}),
        "public_repo_safety": legacy_manifest.get("public_repo_safety", {}),
        "artifact_refs": {
            "legacy_manifest": LEGACY_MARGIN_MANIFEST_PATH.as_posix(),
            "legacy_margin_records": LEGACY_MARGIN_RECORDS_PATH.as_posix(),
            "legacy_difference_summary": LEGACY_DIFFERENCE_SUMMARY_PATH.as_posix(),
            "legacy_stage_manifest": LEGACY_STAGE_MANIFEST_PATH.as_posix(),
        },
    }


def build_manifest() -> dict[str, Any]:
    s09_p1 = validate_s09_p1_dependency()
    legacy = validate_legacy_s09_p2_artifacts()
    hard_blocks = [
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "business_amount_values_remain_private_ref_or_hash_only",
        "authority_system_overwrite_forbidden",
        "public_margin_amount_values_forbidden",
        "upstream_zero_delta_failure_blocks_formal_calculation",
        "upstream_source_difference_blocks_formal_calculation",
        "upstream_entity_matching_review_queue_blocks_formal_calculation",
        "s09_p3_scope_reconciliation_not_performed",
        "stage9_review_not_performed",
        "formal_report_release_blocked",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "github_upload_deferred_until_v014_stage1_18_complete",
        "business_execution_blocked",
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S09",
        "phase_id": "S09-P2",
        "phase_name": "v0.1.4 margin and cash margin",
        "task_id": TASK_ID,
        "phase_scope": PHASE_SCOPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_margin_cash_margin",
        "completed_task_ids": ["S9PBT01", "S9PBT02", "S9PBT03"],
        "acceptance_id": ACCEPTANCE_ID,
        "s09_p1_dependency_validated": True,
        "s09_p1_dependency_status": s09_p1["status"],
        "legacy_s09_p2_dependency_validated": True,
        "stage9_phase_progress": {
            "completed_phase_count": 2,
            "total_phase_count": 3,
            "derived_percent_bps": 6667,
            "derived_percent_label": "66.67%",
            "s09_p1_performed": True,
            "s09_p2_performed": True,
            "s09_p3_performed": False,
            "stage9_review_performed": False,
        },
        "legacy_s09_p2_summary": {
            "required_margin_metric_count": legacy["required_margin_metric_count"],
            "required_margin_metrics": legacy["required_margin_metrics"],
            "project_cost_fact_record_count": legacy["project_cost_fact_record_count"],
            "margin_record_count": legacy["margin_record_count"],
            "difference_summary_count": legacy["difference_summary_count"],
            "authority_field_group_count": legacy["authority_field_group_count"],
            "upstream_manual_review_queue_count": legacy["upstream_manual_review_queue_count"],
            "upstream_unresolved_difference_count": legacy["upstream_unresolved_difference_count"],
            "zero_delta_fail_count": legacy["zero_delta_fail_count"],
            "blocked_quality_result_count": legacy["blocked_quality_result_count"],
            "formal_calculation_blocked": legacy["formal_calculation_blocked"],
            "calculation_status": legacy["calculation_status"],
        },
        "margin_cash_margin_policy": {
            "mapping_version": legacy["mapping_version"],
            "formula_version": legacy["formula_version"],
            "difference_type_count": legacy["difference_type_count"],
            "difference_records_by_type": legacy["difference_records_by_type"],
            "authority_hash_ref_count": legacy["authority_hash_ref_count"],
            "authority_private_ref_count": legacy["authority_private_ref_count"],
            "system_hash_ref_count": legacy["system_hash_ref_count"],
            "system_private_ref_count": legacy["system_private_ref_count"],
            "cash_hash_ref_count": legacy["cash_hash_ref_count"],
            "cash_private_ref_count": legacy["cash_private_ref_count"],
            "authority_system_overwrite_allowed": False,
            "authority_system_overwrite_allowed_count": legacy["authority_system_overwrite_allowed_count"],
            "public_amount_values_committed_count": legacy["public_amount_values_committed_count"],
            "raw_layer_write_allowed_count": legacy["raw_layer_write_allowed_count"],
            "formal_report_allowed_count": legacy["formal_report_allowed_count"],
            "s09_p3_reconciliation_performed_count": legacy["s09_p3_reconciliation_performed_count"],
            "quality_gate_false_count": legacy["quality_gate_false_count"],
            "public_safety_false_count": legacy["public_safety_false_count"],
            "record_public_safety_false_count": legacy["record_public_safety_false_count"],
            "difference_public_safety_false_count": legacy["difference_public_safety_false_count"],
        },
        "phase_boundaries": {
            "s09_p1_dependency_included": True,
            "s09_p2_margin_cash_margin_scope_included": True,
            "s09_p3_scope_reconciliation_scope_included": False,
            "stage9_review_scope_included": False,
            "s10_report_scope_included": False,
            "lineage_full_check_scope_included": False,
            "formal_report_scope_included": False,
            "ui_scope_included": False,
            "external_connector_scope_included": False,
            "github_upload_scope_included": False,
        },
        "quality_gate": {
            "current_data_quality_grade": "Q4",
            "current_report_grade": "D",
            "release_permission": "blocked",
            "q5_formal_calculation_allowed": False,
            "q5_formal_calculation_allowed_count": 0,
            "formal_report_allowed": False,
            "formal_report_allowed_count": 0,
            "business_decision_basis_allowed": False,
            "business_execution_allowed": False,
            "delivery_allowed": False,
            "raw_layer_write_allowed": False,
            "automatic_external_action_allowed": False,
        },
        "github_upload": {
            "github_upload_ready_next_gate": False,
            "github_upload_deferred_until_v014_stage1_18_complete": True,
            "github_upload_performed": False,
            "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        },
        "raw_data_boundary": {
            "raw_inbox_ref": RAW_INBOX_REF,
            "raw_inbox_read_by_this_phase": False,
            "raw_inbox_listed_by_this_phase": False,
            "raw_inbox_inventory_by_this_phase": False,
            "raw_inbox_stat_by_this_phase": False,
            "raw_inbox_hashed_by_this_phase": False,
            "raw_inbox_modified_by_this_phase": False,
            "raw_inbox_deleted_by_this_phase": False,
            "raw_inbox_moved_by_this_phase": False,
            "raw_inbox_renamed_by_this_phase": False,
            "raw_inbox_overwritten_by_this_phase": False,
            "raw_inbox_written_by_this_phase": False,
            "raw_inbox_mutated_by_this_phase": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        },
        "public_repo_safety": {
            "protected_source_payload_committed": False,
            "zip_committed": False,
            "excel_workbook_committed": False,
            "wps_native_file_committed": False,
            "redcircle_native_file_committed": False,
            "csv_committed": False,
            "pdf_committed": False,
            "private_csv_committed": False,
            "sqlite_or_db_committed": False,
            "credentials_committed": False,
            "connector_secret_committed": False,
            "field_plaintext_committed": False,
            "source_header_plaintext_committed": False,
            "raw_file_names_committed": False,
            "raw_file_hashes_committed": False,
            "tab_labels_committed": False,
            "zip_member_names_committed": False,
            "source_record_payload_committed": False,
            "normalized_source_values_committed": False,
            "business_amount_values_committed": False,
            "project_or_customer_plaintext_committed": False,
        },
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "artifact_refs": {
            **legacy["artifact_refs"],
            "manifest": MANIFEST_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PLAN_PATH.as_posix(),
            "generator": "KMFA/tools/v014_s09_p2_margin_cash_margin.py",
            "validator": "KMFA/tools/check_v014_s09_p2_margin_cash_margin.py",
            "unit_test": "KMFA/tests/test_v014_s09_p2_margin_cash_margin.py",
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s09_p2_margin_cash_margin.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s09_p2_margin_cash_margin.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s09_p2_margin_cash_margin -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s09_p2_margin_cash_margin.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_project_margin_cash_margin -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s09_p1_project_cost_fact_layer.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PLAN_PATH.as_posix(),
            "KMFA/tools/v014_s09_p2_margin_cash_margin.py",
            "KMFA/tools/check_v014_s09_p2_margin_cash_margin.py",
            "KMFA/tests/test_v014_s09_p2_margin_cash_margin.py",
        ],
        "next_recommended_phase": NEXT_PHASE,
        "next_phase_instruction": NEXT_INSTRUCTION,
    }


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["legacy_s09_p2_summary"]
    policy = manifest["margin_cash_margin_policy"]
    lines = [
        "# KMFA v0.1.4 S09-P2 Margin And Cash Margin",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        "- dependency: `v0.1.4 S09-P1 PASS`",
        "- legacy_s09_p2_dependency_validated: `true`",
        f"- required_margin_metric_count: `{summary['required_margin_metric_count']}`",
        f"- project_cost_fact_record_count: `{summary['project_cost_fact_record_count']}`",
        f"- margin_record_count: `{summary['margin_record_count']}`",
        f"- difference_summary_count: `{summary['difference_summary_count']}`",
        f"- authority_field_group_count: `{summary['authority_field_group_count']}`",
        f"- upstream_manual_review_queue_count: `{summary['upstream_manual_review_queue_count']}`",
        f"- upstream_unresolved_difference_count: `{summary['upstream_unresolved_difference_count']}`",
        f"- zero_delta_fail_count: `{summary['zero_delta_fail_count']}`",
        f"- blocked_quality_result_count: `{summary['blocked_quality_result_count']}`",
        f"- calculation_status: `{summary['calculation_status']}`",
        f"- difference_type_count: `{policy['difference_type_count']}`",
        f"- authority_hash_ref_count: `{policy['authority_hash_ref_count']}`",
        f"- system_hash_ref_count: `{policy['system_hash_ref_count']}`",
        f"- cash_hash_ref_count: `{policy['cash_hash_ref_count']}`",
        "",
        "## Boundary",
        "",
        "- s09_p1_dependency_included: `true`",
        "- s09_p2_margin_cash_margin_scope_included: `true`",
        "- s09_p3_scope_reconciliation_scope_included: `false`",
        "- stage9_review_scope_included: `false`",
        "- github_upload_deferred_until_v014_stage1_18_complete: `true`",
        "- github_upload_performed: `false`",
        "- authority_system_overwrite_allowed: `false`",
        "- public_amount_values_committed_count: `0`",
        "- formal_report_allowed: `false`",
        "- business_decision_basis_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Raw Data Boundary",
        "",
        f"- raw_inbox_ref: `{RAW_INBOX_REF}`",
        "- raw_inbox_read_by_this_phase: `false`",
        "- raw_inbox_listed_by_this_phase: `false`",
        "- raw_inbox_stat_by_this_phase: `false`",
        "- raw_inbox_hashed_by_this_phase: `false`",
        "- raw_inbox_mutated_by_this_phase: `false`",
        "",
        (
            "This phase did not enumerate, copy, modify, move, rename, delete, overwrite, "
            "or write generated files inside the operator-designated local finance inbox. It only reused "
            "public-safe aggregate and hash/ref evidence already present in the repository."
        ),
        "",
        "## Public Safety",
        "",
        (
            "Evidence contains only metric names, aggregate counts, hash/ref status, queued "
            "difference categories, quality blockers, validator references, and governance paths."
        ),
        (
            "It does not contain source filenames, source hashes from the private inbox, tab labels, "
            "ZIP member names, field/header plaintext, row values, business amount values, credentials, "
            "contracts, payroll, tax filings, or bank statements."
        ),
        "",
        "## Next Step",
        "",
        manifest["next_phase_instruction"],
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_test_results() -> None:
    lines = [
        "# KMFA v0.1.4 S09-P2 Margin And Cash Margin Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `pending_final_validation_local_only`",
        "- github_upload_performed: `false`",
        "- raw_inbox_read_by_this_phase: `false`",
        "- raw_inbox_mutated_by_this_phase: `false`",
        "- s09_p3_performed: `false`",
        "- stage9_review_performed: `false`",
        "- raw_value_matching_performed: `false`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Command Results",
        "",
        "- PENDING: final validation results will be recorded before local commit.",
        "",
    ]
    TEST_RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_risk_register() -> None:
    lines = [
        "# KMFA v0.1.4 S09-P2 Risk Register",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `public_safe_local_only_no_go`",
        "- current_data_quality_grade: `Q4`",
        "- current_report_grade: `D`",
        "- release_permission: `blocked`",
        "",
        "| Risk | Current Control | Residual Status |",
        "|---|---|---|",
        "| Upstream zero-delta failure | Keep formal calculation and formal report blocked | active blocker |",
        "| Upstream unresolved source difference | Carry difference summary forward to S09-P3 without closing it in S09-P2 | active blocker |",
        "| Authority/system overwrite risk | Enforce `authority_system_overwrite_allowed=false` and count `0` | controlled |",
        "| Public business value leakage | Store only aggregate counts, hash/ref status and category names | controlled |",
        "| Scope creep into S09-P3 or Stage 9 review | Keep `s09_p3_performed=false` and `stage9_review_performed=false` | controlled |",
        "| Premature GitHub upload | Keep upload deferred until v1.4 Stage 1-18 complete and overall review/fix pass | controlled |",
        "",
        "No risk item authorizes raw inbox access, raw value matching, formal report release, external connector use, app reinstall, or business execution.",
        "",
    ]
    RISK_REGISTER_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_rollback_plan() -> None:
    lines = [
        "# KMFA v0.1.4 S09-P2 Rollback Plan",
        "",
        f"- task_id: `{TASK_ID}`",
        "- rollback_scope: `V014_S09_P2_MARGIN_CASH_MARGIN artifacts, validator, unit test and governance rows only`",
        "- raw_data_action: `none`",
        "- github_action: `none; no push was performed by this phase`",
        "",
        "## Steps",
        "",
        "1. Revert `KMFA/stage_artifacts/V014_S09_P2_MARGIN_CASH_MARGIN/`.",
        "2. Revert `KMFA/tools/v014_s09_p2_margin_cash_margin.py` and `KMFA/tools/check_v014_s09_p2_margin_cash_margin.py`.",
        "3. Revert `KMFA/tests/test_v014_s09_p2_margin_cash_margin.py`.",
        "4. Revert S09-P2 rows in KMFA governance, traceability, model parameter and project record files.",
        "5. Re-run S09-P1 validator to confirm the next allowed phase returns to S09-P2.",
        "",
        "Rollback must not read, list, copy, move, rename, delete, overwrite, write or mutate the operator-designated raw/private finance inbox.",
        "",
    ]
    ROLLBACK_PLAN_PATH.write_text("\n".join(lines), encoding="utf-8")


def generate() -> dict[str, Any]:
    (PUBLIC_OUTPUT_DIR / "machine").mkdir(parents=True, exist_ok=True)
    (PUBLIC_OUTPUT_DIR / "human").mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(manifest)
    write_test_results()
    write_risk_register()
    write_rollback_plan()
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["legacy_s09_p2_summary"]
    print(
        "PASS: KMFA v0.1.4 S09-P2 margin and cash margin generated "
        f"(margin_metrics={summary['required_margin_metric_count']}, "
        f"margin_records={summary['margin_record_count']}, "
        f"difference_summary={summary['difference_summary_count']}, "
        "s09p3=false, stage9_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
