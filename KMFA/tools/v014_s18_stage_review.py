#!/usr/bin/env python3
"""Generate KMFA v0.1.4 Stage 18 review evidence.

This review closes S18-P1, S18-P2 and S18-P3 locally. It does not upload to
GitHub, release a formal report, complete lineage full check, read the raw
inbox, call external services, invoke live connectors, reinstall the app, or
execute business actions.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.check_v014_s18_p1_precision_stress import validate_v014_s18_p1_precision_stress  # noqa: E402
from KMFA.tools.check_v014_s18_p2_full_regression_acceptance import validate_v014_s18_p2_full_regression_acceptance  # noqa: E402
from KMFA.tools.check_v014_s18_p3_integration_preparation import validate_v014_s18_p3_integration_preparation  # noqa: E402


TASK_ID = "KMFA-V014-S18-STAGE-REVIEW-20260705"
ACCEPTANCE_ID = "ACC-V014-S18-STAGE-REVIEW"
SCHEMA_VERSION = "kmfa.v014_s18_stage_review.v1"
REVIEW_SCOPE = "v014_s18_stage_review_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S18_STAGE_REVIEW")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "stage18_review_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "stage18_review_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "stage18_review_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_MANIFEST_PATH = Path("KMFA/metadata/quality/v014_s18_stage_review_manifest.json")
METADATA_GO_NO_GO_PATH = Path("KMFA/metadata/quality/v014_s18_stage_review_go_no_go_report.json")

V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_PHASE = "V014_STAGE1_18_OVERALL_REVIEW"
NEXT_REQUIRED_STEP = (
    "Run v0.1.4 Stage 1-18 overall review as a separate run after user instruction. "
    "Do not perform GitHub upload, app reinstall, lineage full-check completion, formal report release, "
    "production restore, live connector calls, external services, raw inbox access, OpMe deep coupling, "
    "or business execution in Stage 18 review."
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_v14_taskpack_baseline() -> dict[str, Any]:
    taskpack_text = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    roadmap_text = V14_ROADMAP_PATH.read_text(encoding="utf-8")
    for token in ("精度与压力测试", "全量回归和验收", "后续接入准备"):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing Stage 18 marker {token}")
    for token in ("不提交原始敏感数据到公开GitHub", "不把缺数据报告伪装成完整报告", "Go/No-Go评审通过"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing Stage 18 safety marker {token}")
    return {
        "taskpack_read": True,
        "roadmap_read": True,
        "roadmap_includes_stage18_requirements": True,
        "taskpack_includes_stage18_public_safe_safety_boundary": True,
        "source_refs": {
            "taskpack": V14_TASKPACK_PATH.as_posix(),
            "roadmap": V14_ROADMAP_PATH.as_posix(),
        },
    }


def _raw_all_false(manifest: dict[str, Any]) -> bool:
    raw = manifest.get("raw_data_boundary", {})
    return isinstance(raw, dict) and all(
        value is False for key, value in raw.items() if key.startswith("raw_inbox_") and isinstance(value, bool)
    )


def _raw_boundary(p1: dict[str, Any], p2: dict[str, Any], p3: dict[str, Any]) -> dict[str, Any]:
    return {
        "raw_inbox_ref": RAW_INBOX_REF,
        "raw_inbox_read_required_by_this_review": False,
        "raw_inbox_read_by_this_review": False,
        "raw_inbox_listed_by_this_review": False,
        "raw_inbox_inventory_by_this_review": False,
        "raw_inbox_stat_by_this_review": False,
        "raw_inbox_hashed_by_this_review": False,
        "raw_inbox_modified_by_this_review": False,
        "raw_inbox_deleted_by_this_review": False,
        "raw_inbox_moved_by_this_review": False,
        "raw_inbox_renamed_by_this_review": False,
        "raw_inbox_overwritten_by_this_review": False,
        "raw_inbox_written_by_this_review": False,
        "raw_inbox_mutated_by_this_review": False,
        "s18_p1_raw_inbox_all_false": _raw_all_false(p1),
        "s18_p2_raw_inbox_all_false": _raw_all_false(p2),
        "s18_p3_raw_inbox_all_false": _raw_all_false(p3),
        "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
    }


def _public_repo_safety() -> dict[str, bool]:
    return {
        "protected_source_payload_committed": False,
        "compressed_raw_package_committed": False,
        "office_workbook_committed": False,
        "source_document_committed": False,
        "raw_or_private_table_committed": False,
        "local_database_committed": False,
        "auth_material_committed": False,
        "connector_auth_material_committed": False,
        "field_plaintext_committed": False,
        "source_header_plaintext_committed": False,
        "raw_file_names_committed": False,
        "raw_file_hashes_committed": False,
        "source_record_payload_committed": False,
        "normalized_source_values_committed": False,
        "business_amount_values_committed": False,
        "public_numeric_values_committed": False,
        "project_or_customer_plaintext_committed": False,
        "full_report_committed": False,
        "business_decision_basis_committed": False,
        "formal_release_artifact_committed": False,
        "production_restore_artifact_committed": False,
        "external_service_artifact_committed": False,
        "live_connector_artifact_committed": False,
        "app_reinstall_artifact_committed": False,
    }


def _release_state() -> dict[str, Any]:
    return {
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "external_connector_allowed": False,
        "production_restore_allowed": False,
        "live_connector_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "github_main_upload_allowed": False,
        "current_go_no_go": "NO_GO",
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "blocking_reason": "stage18_review_passed_but_lineage_full_check_official_report_release_and_github_upload_remain_blocked",
    }


def _stage_gate(p1: dict[str, Any], p2: dict[str, Any], p3: dict[str, Any]) -> dict[str, Any]:
    p1s = p1["precision_stress_summary"]
    p2s = p2["full_regression_summary"]
    p3s = p3["integration_preparation_summary"]
    p2_quality = p2["quality_gate"]
    return {
        "precision_scenario_count": p1s["scenario_count"],
        "precision_scenario_type_count": p1s["scenario_type_count"],
        "consecutive_import_run_count": p1s["consecutive_import_run_count"],
        "unique_import_result_hash_count": p1s["unique_import_result_hash_count"],
        "large_batch_file_count": p1s["large_batch_file_count"],
        "error_report_count": p1s["error_report_count"],
        "full_regression_check_category_count": p2s["check_category_count"],
        "stage_evidence_count": p2s["stage_evidence_count"],
        "html_audit_file_count": p2s["html_audit_file_count"],
        "html_audit_row_count": p2s["html_audit_row_count"],
        "html_audit_pass_count": p2s["html_audit_pass_count"],
        "html_audit_warn_count": p2s["html_audit_warn_count"],
        "html_audit_fail_count": p2s["html_audit_fail_count"],
        "connector_plan_count": p3s["connector_plan_count"],
        "read_only_connector_count": p3s["read_only_connector_count"],
        "opme_entry_surface_count": p3s["opme_entry_surface_count"],
        "next_stage_backlog_item_count": p3s["backlog_item_count"],
        "live_connector_call_count": p3s["live_connector_call_count"],
        "external_service_call_count": p3s["external_service_call_count"],
        "source_mutation_allowed_count": p3s["source_mutation_allowed_count"],
        "lineage_full_check_complete": False,
        "official_report_release_allowed": False,
        "pending_reconciliation_count": p2_quality["s09_pending_reconciliation_count"],
        "current_go_no_go": "NO_GO",
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
    }


def _review_go_no_go() -> dict[str, Any]:
    return {
        "record_type": "v014_s18_stage_review_go_no_go_report",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S18",
        "phase_id": "S18_STAGE_REVIEW",
        "task_id": "S18REVT03",
        "decision": "NO_GO",
        "decision_reason": "Stage 18 review passed locally, but lineage full check, official report release and GitHub main upload remain blocked.",
        "stage18_review_performed": True,
        "lineage_full_check_complete": False,
        "official_report_release_allowed": False,
        "delivery_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "github_upload_allowed": False,
        "github_upload_performed": False,
        "blocker_ids": [
            "LINEAGE_FULL_CHECK_NOT_COMPLETE",
            "OFFICIAL_REPORT_RELEASE_NOT_ALLOWED",
            "S09_PENDING_RECONCILIATION_12",
            "GITHUB_UPLOAD_DEFERRED_UNTIL_V014_STAGE1_18_COMPLETE",
        ],
        "resolved_blocker_ids": [
            "S18_P3_PENDING",
            "STAGE18_REVIEW_PENDING",
        ],
        "next_required_phase": NEXT_PHASE,
    }


def _review_findings() -> list[dict[str, str]]:
    return [
        {
            "finding_id": "KMFA-V014-S18-REV-F01",
            "severity": "P1",
            "status": "fixed",
            "summary": "S18-P3 evidence kept final validation fields as pending after local replay.",
            "fix": "Stage 18 review reruns S18-P3 validator and records the stale pending validation status as a fixed review finding.",
            "evidence": "KMFA/stage_artifacts/V014_S18_P3_INTEGRATION_PREPARATION/human/test_results.md",
        },
        {
            "finding_id": "KMFA-V014-S18-REV-F02",
            "severity": "P1",
            "status": "passed",
            "summary": "S18-P1, S18-P2 and S18-P3 validators pass with public-safe local-only evidence.",
            "fix": "No code fix required.",
            "evidence": MANIFEST_PATH.as_posix(),
        },
        {
            "finding_id": "KMFA-V014-S18-REV-F03",
            "severity": "P1",
            "status": "passed",
            "summary": "Stage 18 review resolves S18 pending blockers but preserves NO_GO release and upload blocks.",
            "fix": "No release or upload action is permitted in this review.",
            "evidence": GO_NO_GO_PATH.as_posix(),
        },
    ]


def build_manifest(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or datetime.now().isoformat(timespec="seconds")
    p1 = validate_v014_s18_p1_precision_stress()
    p2 = validate_v014_s18_p2_full_regression_acceptance()
    p3 = validate_v014_s18_p3_integration_preparation()
    findings = _review_findings()
    go_no_go = _review_go_no_go()
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s18_stage_review_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S18",
        "phase_id": "S18_STAGE_REVIEW",
        "review_scope": REVIEW_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S18REVT01", "S18REVT02", "S18REVT03"],
        "status": "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete",
        "generated_at": generated_at,
        "branch": git_output(["branch", "--show-current"]),
        "git_head": git_output(["rev-parse", "HEAD"]),
        "stage_review_performed": True,
        "phase_results": {"S18-P1": "PASS", "S18-P2": "PASS", "S18-P3": "PASS"},
        "stage18_phase_progress": {
            "completed_phase_count": 3,
            "total_phase_count": 3,
            "derived_percent_bps": 10000,
            "derived_percent_label": "100.00%",
            "s18_p1_performed": True,
            "s18_p2_performed": True,
            "s18_p3_performed": True,
            "stage18_review_performed": True,
        },
        "stage_gate": _stage_gate(p1, p2, p3),
        "stage_review_go_no_go": go_no_go,
        "release_state": _release_state(),
        "review_findings": findings,
        "review_findings_summary": {
            "open_finding_count": sum(1 for finding in findings if finding["status"] == "open"),
            "fixed_finding_count": sum(1 for finding in findings if finding["status"] == "fixed"),
            "passed_finding_count": sum(1 for finding in findings if finding["status"] == "passed"),
        },
        "raw_data_boundary": _raw_boundary(p1, p2, p3),
        "public_repo_safety": _public_repo_safety(),
        "v14_taskpack_baseline": load_v14_taskpack_baseline(),
        "upstream_phase_refs": {
            "s18_p1_manifest": "KMFA/stage_artifacts/V014_S18_P1_PRECISION_STRESS/machine/precision_stress_manifest.json",
            "s18_p2_manifest": "KMFA/stage_artifacts/V014_S18_P2_FULL_REGRESSION_ACCEPTANCE/machine/full_regression_acceptance_manifest.json",
            "s18_p3_manifest": "KMFA/stage_artifacts/V014_S18_P3_INTEGRATION_PREPARATION/machine/integration_preparation_manifest.json",
        },
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "go_no_go": GO_NO_GO_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "go_no_go_record": GO_NO_GO_RECORD_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
        },
        "metadata_outputs": {
            "manifest": METADATA_MANIFEST_PATH.as_posix(),
            "go_no_go": METADATA_GO_NO_GO_PATH.as_posix(),
        },
        "validation_summary": {
            "py_compile": "PENDING_FINAL_VALIDATION",
            "s18_p1_validator": "PASS",
            "s18_p2_validator": "PASS",
            "s18_p3_validator": "PASS",
            "stage18_review_validator": "PENDING_FINAL_VALIDATION",
            "focused_unit_test": "PENDING_FINAL_VALIDATION",
            "governance_validator": "PENDING_FINAL_VALIDATION",
            "lean_governance_validator": "PENDING_FINAL_VALIDATION",
            "governance_sync_validator": "PENDING_FINAL_VALIDATION",
            "no_float_money_check": "PENDING_FINAL_VALIDATION",
            "no_omission_check": "PENDING_FINAL_VALIDATION",
            "structured_parse": "PENDING_FINAL_VALIDATION",
            "ruby_yaml_parse": "PENDING_FINAL_VALIDATION",
            "raw_private_suffix_scan": "PENDING_FINAL_VALIDATION",
            "high_signal_secret_scan": "PENDING_FINAL_VALIDATION",
            "public_artifact_boundary_scan": "PENDING_FINAL_VALIDATION",
            "diff_check": "PENDING_FINAL_VALIDATION",
        },
        "hard_blocks": [
            "stage18_review_public_safe_only",
            "report_grade_d_only",
            "data_quality_q4_only",
            "raw_data_mutation_forbidden",
            "raw_publication_forbidden",
            "field_header_plaintext_publication_forbidden",
            "formal_report_release_blocked",
            "business_decision_basis_blocked",
            "production_restore_blocked",
            "external_service_call_blocked",
            "live_connector_blocked",
            "app_reinstall_blocked",
            "lineage_full_check_not_complete",
            "protected_source_matching_not_performed",
            "github_upload_deferred_until_v014_stage1_18_complete",
            "business_execution_blocked",
        ],
        "legacy_stage18_upload_artifacts_current_gate": False,
        "github_upload_performed": False,
        "github_upload_ready_next_gate": False,
        "github_upload_deferred_until_v014_stage1_18_complete": True,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "next_phase": NEXT_PHASE,
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_artifacts(manifest: dict[str, Any]) -> None:
    write_json(MANIFEST_PATH, manifest)
    write_json(METADATA_MANIFEST_PATH, manifest)
    write_json(GO_NO_GO_PATH, manifest["stage_review_go_no_go"])
    write_json(METADATA_GO_NO_GO_PATH, manifest["stage_review_go_no_go"])
    gate = manifest["stage_gate"]
    write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 18 Review",
                "",
                "- phase_results: `S18-P1=PASS; S18-P2=PASS; S18-P3=PASS`",
                f"- open_findings: `{manifest['review_findings_summary']['open_finding_count']}`",
                f"- fixed_findings: `{manifest['review_findings_summary']['fixed_finding_count']}`",
                f"- precision_scenario_count: `{gate['precision_scenario_count']}`",
                f"- full_regression_check_category_count: `{gate['full_regression_check_category_count']}`",
                f"- stage_evidence_count: `{gate['stage_evidence_count']}`",
                f"- html_audit_fail_count: `{gate['html_audit_fail_count']}`",
                f"- connector_plan_count: `{gate['connector_plan_count']}`",
                f"- read_only_connector_count: `{gate['read_only_connector_count']}`",
                f"- opme_entry_surface_count: `{gate['opme_entry_surface_count']}`",
                f"- next_stage_backlog_item_count: `{gate['next_stage_backlog_item_count']}`",
                f"- live_connector_call_count: `{gate['live_connector_call_count']}`",
                f"- external_service_call_count: `{gate['external_service_call_count']}`",
                f"- source_mutation_allowed_count: `{gate['source_mutation_allowed_count']}`",
                f"- current_go_no_go: `{gate['current_go_no_go']}`",
                f"- github_upload_status: `{manifest['github_upload_status']}`",
                "",
                "Stage 18 review is local-only and public-safe. It does not perform GitHub upload, formal report release, lineage full-check completion, raw inbox access, production restore, app reinstall, live connector call, external service call, OpMe deep coupling or business execution.",
                "",
            ]
        ),
    )
    write_text(
        GO_NO_GO_RECORD_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 18 Review Go/No-Go",
                "",
                "- decision: `NO_GO`",
                "- resolved_blockers: `S18_P3_PENDING; STAGE18_REVIEW_PENDING`",
                "- remaining_blockers: `LINEAGE_FULL_CHECK_NOT_COMPLETE; OFFICIAL_REPORT_RELEASE_NOT_ALLOWED; S09_PENDING_RECONCILIATION_12; GITHUB_UPLOAD_DEFERRED_UNTIL_V014_STAGE1_18_COMPLETE`",
                "- delivery_allowed: `false`",
                "- github_upload_allowed: `false`",
                "",
            ]
        ),
    )
    write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 18 Review Test Results",
                "",
                "- generator: pending final validation replay",
                "- validator: pending final validation replay",
                "- focused_unittest: pending final validation replay",
                "- governance_validation: pending final validation replay",
                "- raw_secret_scan: pending final validation replay",
                "",
            ]
        ),
    )
    write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 18 Review Risk Register",
                "",
                "- risk: Stage 18 review could be misread as release approval.",
                "  mitigation: Review keeps decision as NO_GO and blocks delivery, formal report, upload and business execution.",
                "- risk: Future connector plan could be mistaken as live integration.",
                "  mitigation: Review locks live connector, external service and source mutation counts at zero.",
                "",
            ]
        ),
    )
    write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 18 Review Rollback Plan",
                "",
                "- Remove only `KMFA/stage_artifacts/V014_S18_STAGE_REVIEW/` and paired v014 S18 review governance entries if rollback is required.",
                "- Do not touch upstream S18-P1/P2/P3 phase evidence or raw/private inbox contents.",
                "",
            ]
        ),
    )


def generate(generated_at: str | None = None) -> dict[str, Any]:
    manifest = build_manifest(generated_at=generated_at)
    write_artifacts(manifest)
    return manifest


def main() -> int:
    manifest = generate()
    gate = manifest["stage_gate"]
    print(
        "PASS: KMFA v0.1.4 Stage 18 review generated "
        f"(phase_results={manifest['phase_results']}, open_findings={manifest['review_findings_summary']['open_finding_count']}, "
        f"checks={gate['full_regression_check_category_count']}, stages={gate['stage_evidence_count']}, "
        f"connectors={gate['connector_plan_count']}, opme_surfaces={gate['opme_entry_surface_count']}, "
        f"backlog={gate['next_stage_backlog_item_count']}, go_no_go={gate['current_go_no_go']}, "
        f"github_upload={manifest['github_upload_performed']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
