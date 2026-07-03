#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S09-P3 scope reconciliation replay evidence.

This replay validates the v0.1.3 S09-P2 dependency, reuses the public-safe
legacy S09-P3 scope reconciliation artifacts, and records the phase-level
upload-deferred boundary for the v0.1.3 Stage 1-10 run.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s09_p2_margin_cash_margin_replay import (
    validate_v013_s09_p2_margin_cash_margin_replay,
)
from KMFA.tools.project_scope_reconciliation import (
    DEFAULT_OUTPUT_DOMAIN_CONTROLS as LEGACY_DOMAIN_CONTROLS_PATH,
    DEFAULT_OUTPUT_MANIFEST as LEGACY_SCOPE_MANIFEST_PATH,
    DEFAULT_OUTPUT_RECONCILIATION_RECORDS as LEGACY_RECONCILIATION_RECORDS_PATH,
    DEFAULT_OUTPUT_STAGE_MANIFEST as LEGACY_STAGE_MANIFEST_PATH,
    REQUIRED_HUMAN_FIELDS,
    REQUIRED_RECONCILIATION_DOMAINS,
    read_json,
    read_jsonl,
    validate_project_scope_reconciliation_artifacts,
)


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S09_P3_SCOPE_RECONCILIATION_REPLAY")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/scope_reconciliation_replay_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/scope_reconciliation_replay_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
TASK_ID = "KMFA-V013-S09-P3-SCOPE-RECONCILIATION-REPLAY-20260703"
SCHEMA_VERSION = "kmfa.v013_s09_p3_scope_reconciliation_replay.v1"
PHASE_SCOPE = "v013_s09_p3_scope_reconciliation_replay_only"
RAW_DIR = "/Users/linzezhang/Downloads/KMFA_MetaData"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 Stage 9 review as a separate run. GitHub main upload remains deferred "
    "until v0.1.3 Stages 1-10 are complete, the whole Stage 1-10 review passes, and findings "
    "are fixed; do not run GitHub upload, raw value matching, lineage full check, formal report "
    "release, live connector, Redcircle automatic connector, or business execution in the S09-P3 run."
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


def validate_s09_p2_dependency() -> dict[str, Any]:
    result = validate_v013_s09_p2_margin_cash_margin_replay()
    if result.get("stage_id") != "S09" or result.get("phase_id") != "S09-P2":
        raise RuntimeError("v0.1.3 S09-P3 requires validated S09-P2 replay dependency")
    if result.get("status") != "completed_validated_local_only_no_go_upload_deferred_margin_cash_margin_replayed":
        raise RuntimeError("v0.1.3 S09-P3 requires completed S09-P2 replay dependency")
    if result.get("s09_p3_performed") is not False:
        raise RuntimeError("S09-P2 dependency must not already include S09-P3")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("S09-P2 dependency must not include GitHub upload")
    if result.get("github_upload_deferred_until_stage10_batch") is not True:
        raise RuntimeError("S09-P2 dependency must keep upload deferred")
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


def _count_records_with_false(records: list[dict[str, Any]], key: str) -> int:
    return sum(1 for record in records if record.get(key) is False)


def _count_records_with_true(records: list[dict[str, Any]], key: str) -> int:
    return sum(1 for record in records if record.get(key) is True)


def _all_human_fields_present(records: list[dict[str, Any]]) -> bool:
    required = set(REQUIRED_HUMAN_FIELDS)
    return all(required.issubset(record.keys()) for record in records)


def validate_legacy_s09_p3_artifacts() -> dict[str, Any]:
    legacy_manifest = read_json(LEGACY_SCOPE_MANIFEST_PATH)
    reconciliation_records = read_jsonl(LEGACY_RECONCILIATION_RECORDS_PATH)
    domain_controls = read_jsonl(LEGACY_DOMAIN_CONTROLS_PATH)
    legacy_stage_manifest = read_json(LEGACY_STAGE_MANIFEST_PATH)
    validate_project_scope_reconciliation_artifacts(legacy_manifest, reconciliation_records, domain_controls)

    summary = legacy_manifest.get("summary", {})
    records_by_domain = Counter(str(record.get("reconciliation_domain")) for record in reconciliation_records)
    controls_by_domain = Counter(str(control.get("reconciliation_domain")) for control in domain_controls)
    pending_review_count = sum(
        1 for record in reconciliation_records if record.get("resolution_status") == "pending_owner_or_authorized_review"
    )
    pending_domain_control_count = sum(
        1 for control in domain_controls if control.get("control_status") == "active_pending_difference_review"
    )
    closed_record_count = sum(1 for record in reconciliation_records if record.get("closed_at") is not None)
    closed_domain_control_count = sum(1 for control in domain_controls if control.get("closed_at") is not None)

    return {
        "legacy_manifest": legacy_manifest,
        "legacy_stage_manifest": legacy_stage_manifest,
        "required_reconciliation_domain_count": len(REQUIRED_RECONCILIATION_DOMAINS),
        "required_reconciliation_domains": list(REQUIRED_RECONCILIATION_DOMAINS),
        "required_human_field_count": len(REQUIRED_HUMAN_FIELDS),
        "required_human_fields": list(REQUIRED_HUMAN_FIELDS),
        "upstream_margin_record_count": summary.get("upstream_margin_record_count"),
        "source_difference_summary_count": summary.get("source_difference_summary_count"),
        "reconciliation_record_count": len(reconciliation_records),
        "domain_control_count": len(domain_controls),
        "confirmed_resolution_count": summary.get("confirmed_resolution_count"),
        "pending_resolution_count": summary.get("pending_resolution_count"),
        "reconciliation_records_by_domain": dict(sorted(records_by_domain.items())),
        "domain_controls_by_domain": dict(sorted(controls_by_domain.items())),
        "pending_review_count": pending_review_count,
        "pending_domain_control_count": pending_domain_control_count,
        "closed_record_count": closed_record_count,
        "closed_domain_control_count": closed_domain_control_count,
        "confirmed_for_rerun_count": _count_records_with_true(reconciliation_records, "confirmed_for_rerun"),
        "domain_confirmed_for_rerun_count": _count_records_with_true(domain_controls, "domain_confirmed_for_rerun"),
        "derived_metric_rerun_allowed_count": (
            _count_records_with_true(reconciliation_records, "derived_metric_rerun_allowed")
            + _count_records_with_true(domain_controls, "derived_metric_rerun_allowed")
        ),
        "formal_report_rerun_allowed_count": (
            _count_records_with_true(reconciliation_records, "formal_report_rerun_allowed")
            + _count_records_with_true(domain_controls, "formal_report_rerun_allowed")
        ),
        "public_amount_values_committed_count": (
            _count_records_with_true(reconciliation_records, "public_amount_values_committed")
            + _count_records_with_true(domain_controls, "public_amount_values_committed")
        ),
        "raw_layer_write_allowed_count": (
            _count_records_with_true(reconciliation_records, "raw_layer_write_allowed")
            + _count_records_with_true(domain_controls, "raw_layer_write_allowed")
        ),
        "record_public_amount_values_blocked_count": _count_records_with_false(
            reconciliation_records, "public_amount_values_committed"
        ),
        "domain_public_amount_values_blocked_count": _count_records_with_false(
            domain_controls, "public_amount_values_committed"
        ),
        "quality_gate_false_count": _count_false_values(legacy_manifest.get("quality_gate", {})),
        "public_safety_false_count": _count_false_values(legacy_manifest.get("public_repo_safety", {})),
        "record_public_safety_false_count": _count_nested_false_safety(reconciliation_records),
        "domain_public_safety_false_count": _count_nested_false_safety(domain_controls),
        "all_record_human_fields_present": _all_human_fields_present(reconciliation_records),
        "all_domain_human_fields_present": _all_human_fields_present(domain_controls),
        "stage_scope": legacy_manifest.get("stage_scope", {}),
        "quality_gate": legacy_manifest.get("quality_gate", {}),
        "rerun_policy": legacy_manifest.get("rerun_policy", {}),
        "public_repo_safety": legacy_manifest.get("public_repo_safety", {}),
        "reconciliation_status": legacy_manifest.get("reconciliation_status"),
        "mapping_version": legacy_manifest.get("mapping_version"),
        "formula_version": legacy_manifest.get("formula_version"),
        "artifact_refs": {
            "legacy_manifest": LEGACY_SCOPE_MANIFEST_PATH.as_posix(),
            "legacy_reconciliation_records": LEGACY_RECONCILIATION_RECORDS_PATH.as_posix(),
            "legacy_domain_controls": LEGACY_DOMAIN_CONTROLS_PATH.as_posix(),
            "legacy_stage_manifest": LEGACY_STAGE_MANIFEST_PATH.as_posix(),
        },
    }


def build_manifest() -> dict[str, Any]:
    s09_p2 = validate_s09_p2_dependency()
    legacy = validate_legacy_s09_p3_artifacts()
    hard_blocks = [
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "business_amount_values_remain_private_ref_or_hash_only",
        "pending_owner_or_authorized_difference_review_blocks_rerun",
        "confirmed_resolution_count_zero_blocks_derived_metric_rerun",
        "formal_report_rerun_blocked",
        "stage9_review_not_performed",
        "formal_report_release_blocked",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "github_upload_deferred_until_stage10_batch",
        "business_execution_blocked",
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S09",
        "phase_id": "S09-P3",
        "phase_name": "v0.1.3 scope reconciliation replay",
        "task_id": TASK_ID,
        "phase_scope": PHASE_SCOPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_scope_reconciliation_replayed",
        "completed_task_ids": ["S9PCT01", "S9PCT02", "S9PCT03"],
        "acceptance_ids": ["ACC-V013-S09-P3-SCOPE-RECONCILIATION-REPLAY"],
        "s09_p2_dependency_validated": True,
        "s09_p2_dependency_status": s09_p2["status"],
        "legacy_s09_p3_dependency_validated": True,
        "stage9_phase_progress": {
            "completed_phase_count": 3,
            "total_phase_count": 3,
            "derived_percent_bps": 10000,
            "derived_percent_label": "100.00%",
            "s09_p1_performed": True,
            "s09_p2_performed": True,
            "s09_p3_performed": True,
            "stage9_review_performed": False,
        },
        "legacy_s09_p3_summary": {
            "required_reconciliation_domain_count": legacy["required_reconciliation_domain_count"],
            "required_reconciliation_domains": legacy["required_reconciliation_domains"],
            "required_human_field_count": legacy["required_human_field_count"],
            "required_human_fields": legacy["required_human_fields"],
            "upstream_margin_record_count": legacy["upstream_margin_record_count"],
            "source_difference_summary_count": legacy["source_difference_summary_count"],
            "reconciliation_record_count": legacy["reconciliation_record_count"],
            "domain_control_count": legacy["domain_control_count"],
            "confirmed_resolution_count": legacy["confirmed_resolution_count"],
            "pending_resolution_count": legacy["pending_resolution_count"],
            "reconciliation_status": legacy["reconciliation_status"],
        },
        "scope_reconciliation_policy": {
            "mapping_version": legacy["mapping_version"],
            "formula_version": legacy["formula_version"],
            "reconciliation_records_by_domain": legacy["reconciliation_records_by_domain"],
            "domain_controls_by_domain": legacy["domain_controls_by_domain"],
            "pending_review_count": legacy["pending_review_count"],
            "pending_domain_control_count": legacy["pending_domain_control_count"],
            "closed_record_count": legacy["closed_record_count"],
            "closed_domain_control_count": legacy["closed_domain_control_count"],
            "confirmed_for_rerun_count": legacy["confirmed_for_rerun_count"],
            "domain_confirmed_for_rerun_count": legacy["domain_confirmed_for_rerun_count"],
            "derived_metric_rerun_allowed": False,
            "derived_metric_rerun_allowed_count": legacy["derived_metric_rerun_allowed_count"],
            "formal_report_rerun_allowed": False,
            "formal_report_rerun_allowed_count": legacy["formal_report_rerun_allowed_count"],
            "public_amount_values_committed_count": legacy["public_amount_values_committed_count"],
            "raw_layer_write_allowed_count": legacy["raw_layer_write_allowed_count"],
            "record_public_amount_values_blocked_count": legacy["record_public_amount_values_blocked_count"],
            "domain_public_amount_values_blocked_count": legacy["domain_public_amount_values_blocked_count"],
            "quality_gate_false_count": legacy["quality_gate_false_count"],
            "public_safety_false_count": legacy["public_safety_false_count"],
            "record_public_safety_false_count": legacy["record_public_safety_false_count"],
            "domain_public_safety_false_count": legacy["domain_public_safety_false_count"],
            "all_record_human_fields_present": legacy["all_record_human_fields_present"],
            "all_domain_human_fields_present": legacy["all_domain_human_fields_present"],
        },
        "phase_boundaries": {
            "s09_p2_dependency_included": True,
            "s09_p3_scope_reconciliation_scope_included": True,
            "s09_p1_project_cost_fact_layer_scope_included": False,
            "s09_p2_margin_cash_margin_scope_included": False,
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
            "derived_metric_rerun_allowed": False,
            "formal_report_rerun_allowed": False,
            "q5_formal_calculation_allowed": False,
            "formal_report_allowed": False,
            "business_decision_basis_allowed": False,
            "business_execution_allowed": False,
            "delivery_allowed": False,
            "raw_layer_write_allowed": False,
            "automatic_external_action_allowed": False,
        },
        "github_upload": {
            "github_upload_ready_next_gate": False,
            "github_upload_deferred_until_stage10_batch": True,
            "github_upload_performed": False,
            "github_upload_status": "not_uploaded_deferred_until_stage10_batch",
        },
        "raw_data_boundary": {
            "local_raw_data_dir": RAW_DIR,
            "local_raw_data_dir_role": "user_finance_raw_private_inbox",
            "codex_read_allowed_only_when_phase_requires": True,
            "codex_read_required_by_this_phase": False,
            "codex_read_performed_by_this_phase": False,
            "codex_list_performed_by_this_phase": False,
            "codex_modify_allowed": False,
            "codex_delete_allowed": False,
            "codex_move_allowed": False,
            "codex_rename_allowed": False,
            "codex_overwrite_allowed": False,
            "codex_generate_inside_allowed": False,
            "codex_create_extra_files_inside_allowed": False,
            "github_commit_allowed": False,
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
            "generator": "KMFA/tools/v013_s09_p3_scope_reconciliation_replay.py",
            "validator": "KMFA/tools/check_v013_s09_p3_scope_reconciliation_replay.py",
            "unit_test": "KMFA/tests/test_v013_s09_p3_scope_reconciliation_replay.py",
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s09_p3_scope_reconciliation_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s09_p3_scope_reconciliation_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s09_p3_scope_reconciliation_replay -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s09_p3_scope_reconciliation.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_project_scope_reconciliation -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s09_p2_margin_cash_margin_replay.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            "KMFA/tools/v013_s09_p3_scope_reconciliation_replay.py",
            "KMFA/tools/check_v013_s09_p3_scope_reconciliation_replay.py",
            "KMFA/tests/test_v013_s09_p3_scope_reconciliation_replay.py",
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["legacy_s09_p3_summary"]
    policy = manifest["scope_reconciliation_policy"]
    lines = [
        "# KMFA v0.1.3 S09-P3 Scope Reconciliation Replay",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        "- dependency: `v0.1.3 S09-P2 replay PASS`",
        "- legacy_s09_p3_dependency_validated: `true`",
        f"- reconciliation_record_count: `{summary['reconciliation_record_count']}`",
        f"- domain_control_count: `{summary['domain_control_count']}`",
        f"- required_reconciliation_domain_count: `{summary['required_reconciliation_domain_count']}`",
        f"- required_human_field_count: `{summary['required_human_field_count']}`",
        f"- upstream_margin_record_count: `{summary['upstream_margin_record_count']}`",
        f"- source_difference_summary_count: `{summary['source_difference_summary_count']}`",
        f"- confirmed_resolution_count: `{summary['confirmed_resolution_count']}`",
        f"- pending_resolution_count: `{summary['pending_resolution_count']}`",
        f"- reconciliation_status: `{summary['reconciliation_status']}`",
        f"- pending_review_count: `{policy['pending_review_count']}`",
        f"- pending_domain_control_count: `{policy['pending_domain_control_count']}`",
        f"- derived_metric_rerun_allowed_count: `{policy['derived_metric_rerun_allowed_count']}`",
        f"- formal_report_rerun_allowed_count: `{policy['formal_report_rerun_allowed_count']}`",
        f"- public_amount_values_committed_count: `{policy['public_amount_values_committed_count']}`",
        f"- raw_layer_write_allowed_count: `{policy['raw_layer_write_allowed_count']}`",
        "",
        "## Boundary",
        "",
        "- s09_p2_dependency_included: `true`",
        "- s09_p3_scope_reconciliation_scope_included: `true`",
        "- stage9_review_scope_included: `false`",
        "- derived_metric_rerun_allowed: `false`",
        "- formal_report_rerun_allowed: `false`",
        "- formal_report_allowed: `false`",
        "- github_upload_deferred_until_stage10_batch: `true`",
        "- github_upload_performed: `false`",
        "- business_decision_basis_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Raw Data Boundary",
        "",
        f"- local_raw_data_dir: `{RAW_DIR}`",
        "- local_raw_data_dir_role: `user_finance_raw_private_inbox`",
        "- codex_read_required_by_this_phase: `false`",
        "- codex_read_performed_by_this_phase: `false`",
        "- codex_list_performed_by_this_phase: `false`",
        "- codex_modify_allowed: `false`",
        "- codex_delete_allowed: `false`",
        "- codex_move_allowed: `false`",
        "- codex_rename_allowed: `false`",
        "- codex_generate_inside_allowed: `false`",
        "- codex_create_extra_files_inside_allowed: `false`",
        "- github_commit_allowed: `false`",
        "",
        (
            "This phase did not enumerate, copy, modify, move, rename, delete, overwrite, "
            "or write generated files inside the local finance inbox. It only replayed "
            "public-safe aggregate and hash/ref evidence already present in the repository."
        ),
        "",
        "## Public Safety",
        "",
        (
            "Evidence contains only aggregate counts, reconciliation domain identifiers, "
            "human-readable status categories, quality blockers, validator references, and governance paths."
        ),
        (
            "It does not contain source filenames, source hashes from the private inbox, tab labels, "
            "ZIP member names, field/header plaintext, row values, business amount values, credentials, "
            "contracts, payroll, tax filings, or bank statements."
        ),
        "",
        "## Next Step",
        "",
        manifest["next_required_step"],
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_test_results() -> None:
    lines = [
        "# KMFA v0.1.3 S09-P3 Scope Reconciliation Replay Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `pending_final_validation_local_only`",
        "- github_upload_performed: `false`",
        "- raw_dir_read_performed_by_this_phase: `false`",
        "- raw_dir_mutation_performed: `false`",
        "- stage9_review_performed: `false`",
        "- derived_metric_rerun_allowed: `false`",
        "- formal_report_rerun_allowed: `false`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Command Results",
        "",
        "- PENDING: final validation results will be recorded before local commit.",
        "",
    ]
    TEST_RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


def generate() -> dict[str, Any]:
    (PUBLIC_OUTPUT_DIR / "machine").mkdir(parents=True, exist_ok=True)
    (PUBLIC_OUTPUT_DIR / "human").mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(manifest)
    write_test_results()
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["legacy_s09_p3_summary"]
    print(
        "PASS: KMFA v0.1.3 S09-P3 scope reconciliation replay generated "
        f"(reconciliation_records={summary['reconciliation_record_count']}, "
        f"domain_controls={summary['domain_control_count']}, "
        f"pending_resolutions={summary['pending_resolution_count']}, "
        "stage9_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
