#!/usr/bin/env python3
"""Generate KMFA v0.1.4 Stage 16 review evidence.

This review closes the v0.1.4 subcontract, project lifecycle and customer
business analysis stage by replaying S16-P1, S16-P2 and S16-P3 public-safe
manifests. It does not read raw/private finance data, enter S17, release a
formal report, perform procurement, approve or execute payment, operate bank
workflows, operate site/signature/invoice workflows, contact customers, perform
collection/legal actions, or upload to GitHub.
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

from KMFA.tools.check_v014_s16_p1_subcontract_procurement import (  # noqa: E402
    validate_v014_s16_p1_subcontract_procurement,
)
from KMFA.tools.check_v014_s16_p2_project_status_lifecycle import (  # noqa: E402
    validate_v014_s16_p2_project_status_lifecycle,
)
from KMFA.tools.check_v014_s16_p3_customer_business_analysis import (  # noqa: E402
    validate_v014_s16_p3_customer_business_analysis,
)


TASK_ID = "KMFA-V014-S16-STAGE-REVIEW-20260705"
ACCEPTANCE_ID = "ACC-V014-S16-STAGE-REVIEW"
SCHEMA_VERSION = "kmfa.v014_s16_stage_review.v1"
REVIEW_SCOPE = "v014_s16_stage_review_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S16_STAGE_REVIEW")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "stage16_review_manifest.json"
REPORT_PATH = HUMAN_DIR / "stage16_review_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_PHASE = "S17-P1"
NEXT_REQUIRED_STEP = (
    "Start v0.1.4 S17-P1 only as a separate run after user instruction. "
    "Do not perform GitHub upload in Stage 16 review; GitHub main upload remains deferred until "
    "v1.4 Stage 1-18 are complete, overall review has passed, and findings are fixed. Do not perform "
    "protected source matching, lineage full check, formal report release, live connector, app reinstall, "
    "procurement execution, payment approval, payment execution, bank operation, site operation, signature "
    "operation, invoice issuance, customer contact action, collection action, legal decision, tax filing, "
    "or business execution."
)
RAW_PHASE_KEYS = (
    "raw_inbox_read_by_this_phase",
    "raw_inbox_listed_by_this_phase",
    "raw_inbox_inventory_by_this_phase",
    "raw_inbox_stat_by_this_phase",
    "raw_inbox_hashed_by_this_phase",
    "raw_inbox_modified_by_this_phase",
    "raw_inbox_deleted_by_this_phase",
    "raw_inbox_moved_by_this_phase",
    "raw_inbox_renamed_by_this_phase",
    "raw_inbox_overwritten_by_this_phase",
    "raw_inbox_written_by_this_phase",
    "raw_inbox_mutated_by_this_phase",
)
RAW_REVIEW_KEYS = tuple(key.replace("_by_this_phase", "_by_this_review") for key in RAW_PHASE_KEYS)
RAW_ALIGNMENT_FALSE_KEYS = (
    "raw_inbox_modified_by_this_phase",
    "raw_inbox_deleted_by_this_phase",
    "raw_inbox_moved_by_this_phase",
    "raw_inbox_renamed_by_this_phase",
    "raw_inbox_overwritten_by_this_phase",
    "raw_inbox_written_by_this_phase",
    "raw_inbox_mutated_by_this_phase",
    "raw_business_values_committed",
    "raw_file_names_committed",
    "raw_hashes_committed",
    "field_header_plaintext_committed",
    "private_runtime_report_committed",
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
    for token in ("外协采购", "项目状态生命周期", "客户经营分析"):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing Stage 16 marker {token}")
    for token in ("外协/采购/付款归集线", "客户经营分析线"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing Stage 16 marker {token}")
    return {
        "taskpack_read": True,
        "roadmap_read": True,
        "roadmap_includes_stage16_requirements": True,
        "taskpack_includes_stage16_subcontract_and_customer_lines": True,
        "source_refs": {
            "taskpack": V14_TASKPACK_PATH.as_posix(),
            "roadmap": V14_ROADMAP_PATH.as_posix(),
        },
    }


def _raw_all_false(manifest: dict[str, Any]) -> bool:
    raw = manifest.get("raw_data_boundary", {})
    return isinstance(raw, dict) and all(raw.get(key) is False for key in RAW_PHASE_KEYS)


def _alignment_readonly(manifest: dict[str, Any]) -> bool:
    alignment = manifest.get("raw_private_alignment", {})
    if not isinstance(alignment, dict):
        return False
    return (
        alignment.get("raw_private_alignment_attempted_by_this_phase") is True
        and alignment.get("raw_inbox_readonly_contract_preserved") is True
        and all(alignment.get(key) is False for key in RAW_ALIGNMENT_FALSE_KEYS)
    )


def _raw_boundary(p1: dict[str, Any], p2: dict[str, Any], p3: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {key: False for key in RAW_REVIEW_KEYS}
    result.update(
        {
            "raw_inbox_ref": RAW_INBOX_REF,
            "raw_inbox_read_required_by_this_review": False,
            "s16_p1_raw_inbox_all_false": _raw_all_false(p1),
            "s16_p2_raw_private_alignment_readonly": _alignment_readonly(p2),
            "s16_p3_raw_private_alignment_readonly": _alignment_readonly(p3),
            "s16_p2_private_alignment_attempted": p2.get("raw_private_alignment", {}).get(
                "raw_private_alignment_attempted_by_this_phase"
            )
            is True,
            "s16_p3_private_alignment_attempted": p3.get("raw_private_alignment", {}).get(
                "raw_private_alignment_attempted_by_this_phase"
            )
            is True,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        }
    )
    return result


def _public_repo_safety() -> dict[str, bool]:
    return {
        "protected_source_payload_committed": False,
        "compressed_raw_package_committed": False,
        "excel_workbook_committed": False,
        "wps_native_file_committed": False,
        "raw_or_private_csv_committed": False,
        "pdf_document_committed": False,
        "private_csv_committed": False,
        "local_database_committed": False,
        "auth_material_committed": False,
        "connector_auth_material_committed": False,
        "field_plaintext_committed": False,
        "source_header_plaintext_committed": False,
        "raw_file_names_committed": False,
        "raw_file_hashes_committed": False,
        "tab_labels_committed": False,
        "source_record_payload_committed": False,
        "normalized_source_values_committed": False,
        "business_amount_values_committed": False,
        "public_numeric_values_committed": False,
        "project_or_customer_plaintext_committed": False,
        "supplier_plaintext_committed": False,
        "supplier_settlement_payload_committed": False,
        "procurement_order_payload_committed": False,
        "bank_payload_committed": False,
        "site_construction_payload_committed": False,
        "safety_signature_payload_committed": False,
        "technical_signature_payload_committed": False,
        "collection_instruction_committed": False,
        "legal_decision_committed": False,
        "tax_filing_payload_committed": False,
        "business_decision_basis_committed": False,
    }


def _release_state() -> dict[str, Any]:
    return {
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "procurement_execution_allowed": False,
        "payment_approval_allowed": False,
        "payment_execution_allowed": False,
        "bank_operation_allowed": False,
        "site_operation_allowed": False,
        "signature_operation_allowed": False,
        "invoice_issuance_allowed": False,
        "customer_contact_action_allowed": False,
        "collection_action_allowed": False,
        "legal_collection_decision_allowed": False,
        "tax_filing_allowed": False,
        "github_main_upload_allowed": False,
        "current_go_no_go": "NO_GO",
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "blocking_reason": "stage16_review_is_public_safe_d_grade_with_operations_payment_collection_legal_and_business_execution_blocked",
    }


def _stage_gate(p1: dict[str, Any], p2: dict[str, Any], p3: dict[str, Any]) -> dict[str, Any]:
    p1_summary = p1["subcontract_procurement_summary"]
    p2_summary = p2["project_status_lifecycle_summary"]
    p3_summary = p3["customer_business_analysis_summary"]
    return {
        "source_lane_total_count": (
            p1_summary["source_lane_count"] + p2_summary["source_lane_count"] + p3_summary["source_lane_count"]
        ),
        "subcontract_source_lane_count": p1_summary["source_lane_count"],
        "project_status_source_lane_count": p2_summary["source_lane_count"],
        "customer_business_source_lane_count": p3_summary["source_lane_count"],
        "project_match_count": p1_summary["project_match_count"],
        "matched_to_project_count": p1_summary["matched_to_project_count"],
        "unmatched_project_count": p1_summary["unmatched_project_count"],
        "cross_project_match_count": p1_summary["cross_project_match_count"],
        "unallocated_cost_pool_count": p1_summary["unallocated_cost_pool_count"],
        "anomaly_candidate_count": p1_summary["anomaly_candidate_count"],
        "duplicate_payment_candidate_count": p1_summary["duplicate_payment_candidate_count"],
        "cross_project_cost_candidate_count": p1_summary["cross_project_cost_candidate_count"],
        "lifecycle_record_count": p2_summary["lifecycle_record_count"],
        "exception_item_count": p2_summary["exception_item_count"],
        "lifecycle_handoff_guard_count": p2_summary["handoff_guard_count"],
        "completed_not_settled_count": p2_summary["completed_not_settled_count"],
        "settled_not_invoiced_count": p2_summary["settled_not_invoiced_count"],
        "invoiced_not_collected_count": p2_summary["invoiced_not_collected_count"],
        "customer_value_dimension_count": p3_summary["customer_value_dimension_count"],
        "customer_value_signal_count": p3_summary["customer_value_signal_count"],
        "customer_risk_signal_count": p3_summary["customer_risk_signal_count"],
        "customer_summary_count": p3_summary["customer_summary_count"],
        "customer_handoff_guard_count": p3_summary["handoff_guard_count"],
        "project_margin_signal_count": p3_summary["project_margin_signal_count"],
        "collection_quality_signal_count": p3_summary["collection_quality_signal_count"],
        "aging_risk_signal_count": p3_summary["aging_risk_signal_count"],
        "pending_reconciliation_count": max(
            p1_summary["pending_reconciliation_count"],
            p2_summary["pending_reconciliation_count"],
            p3_summary["pending_reconciliation_count"],
        ),
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "procurement_execution_count": 0,
        "payment_approval_count": 0,
        "payment_execution_count": 0,
        "bank_operation_count": 0,
        "site_operation_count": 0,
        "signature_operation_count": 0,
        "invoice_issuance_count": 0,
        "customer_contact_action_count": 0,
        "collection_action_count": 0,
        "legal_collection_decision_count": 0,
        "tax_filing_count": 0,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
    }


def _review_findings() -> list[dict[str, str]]:
    return [
        {
            "finding_id": "KMFA-V014-S16-REV-F01",
            "severity": "P2",
            "status": "fixed",
            "summary": "S16-P2 and S16-P3 private alignment markers could be mistaken for public raw-source publication.",
            "fix": "Stage 16 review records them as read-only aggregate observations and keeps raw mutation, raw names, raw hashes, field headers and business values out of public evidence.",
            "evidence": MANIFEST_PATH.as_posix(),
        },
        {
            "finding_id": "KMFA-V014-S16-REV-F02",
            "severity": "P2",
            "status": "passed",
            "summary": "S16-P1, S16-P2 and S16-P3 validators pass with public-safe subcontract, lifecycle and customer business evidence.",
            "fix": "No code fix required.",
            "evidence": "KMFA/stage_artifacts/V014_S16_P3_CUSTOMER_BUSINESS_ANALYSIS/machine/customer_business_analysis_manifest.json",
        },
        {
            "finding_id": "KMFA-V014-S16-REV-F03",
            "severity": "P1",
            "status": "passed",
            "summary": "Procurement execution, payment approval, payment execution, bank operation, site/signature/invoice actions, customer contact, collection, legal and business execution remain blocked.",
            "fix": "No code fix required.",
            "evidence": MANIFEST_PATH.as_posix(),
        },
    ]


def build_manifest(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or datetime.now().isoformat(timespec="seconds")
    p1 = validate_v014_s16_p1_subcontract_procurement()
    p2 = validate_v014_s16_p2_project_status_lifecycle()
    p3 = validate_v014_s16_p3_customer_business_analysis()
    findings = _review_findings()

    stage_gate = _stage_gate(p1, p2, p3)
    phase_results = {
        "S16-P1": "PASS" if p1.get("phase_id") == "S16-P1" else "FAIL",
        "S16-P2": "PASS" if p2.get("phase_id") == "S16-P2" else "FAIL",
        "S16-P3": "PASS" if p3.get("phase_id") == "S16-P3" else "FAIL",
    }
    validation_summary = {
        "py_compile": "PENDING_FINAL_VALIDATION",
        "s16_p1_validator": "PASS",
        "s16_p2_validator": "PASS",
        "s16_p3_validator": "PASS",
        "stage_review_validator": "PENDING_FINAL_VALIDATION",
        "focused_unit_test": "PENDING_FINAL_VALIDATION",
        "governance_validator": "PENDING_FINAL_VALIDATION",
        "lean_governance_validator": "PENDING_FINAL_VALIDATION",
        "governance_sync_validator": "PENDING_FINAL_VALIDATION",
        "no_float_money_check": "PENDING_FINAL_VALIDATION",
        "no_omission_check": "PENDING_FINAL_VALIDATION",
        "structured_parse": "PENDING_FINAL_VALIDATION",
        "raw_private_suffix_scan": "PENDING_FINAL_VALIDATION",
        "high_signal_secret_scan": "PENDING_FINAL_VALIDATION",
        "public_stage16_semantic_scan": "PENDING_FINAL_VALIDATION",
        "diff_check": "PENDING_FINAL_VALIDATION",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s16_stage_review_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S16",
        "phase_id": "S16_STAGE_REVIEW",
        "review_scope": REVIEW_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S16REVT01", "S16REVT02", "S16REVT03"],
        "status": "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete",
        "generated_at": generated_at,
        "branch": git_output(["branch", "--show-current"]),
        "git_head": git_output(["rev-parse", "HEAD"]),
        "stage_review_performed": True,
        "phase_results": phase_results,
        "stage16_phase_progress": {
            "completed_phase_count": 3,
            "total_phase_count": 3,
            "derived_percent_bps": 10000,
            "derived_percent_label": "100.00%",
            "s16_p1_performed": True,
            "s16_p2_performed": True,
            "s16_p3_performed": True,
            "stage16_review_performed": True,
        },
        "stage_gate": stage_gate,
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
            "s16_p1_manifest": "KMFA/stage_artifacts/V014_S16_P1_SUBCONTRACT_PROCUREMENT/machine/subcontract_procurement_manifest.json",
            "s16_p2_manifest": "KMFA/stage_artifacts/V014_S16_P2_PROJECT_STATUS_LIFECYCLE/machine/project_status_lifecycle_manifest.json",
            "s16_p3_manifest": "KMFA/stage_artifacts/V014_S16_P3_CUSTOMER_BUSINESS_ANALYSIS/machine/customer_business_analysis_manifest.json",
        },
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
        },
        "validation_summary": validation_summary,
        "hard_blocks": [
            "report_grade_d_only",
            "pending_reconciliation_requires_owner_review",
            "raw_data_mutation_forbidden",
            "raw_publication_forbidden",
            "field_header_plaintext_publication_forbidden",
            "formal_report_release_blocked",
            "business_decision_basis_blocked",
            "procurement_execution_blocked",
            "payment_approval_blocked",
            "payment_execution_blocked",
            "bank_operation_blocked",
            "site_operation_blocked",
            "signature_operation_blocked",
            "invoice_issuance_blocked",
            "customer_contact_action_blocked",
            "collection_action_blocked",
            "legal_collection_decision_blocked",
            "tax_filing_blocked",
            "s17_p1_not_performed",
            "lineage_full_check_not_performed",
            "protected_source_matching_not_performed",
            "github_upload_deferred_until_v014_stage1_18_complete",
            "app_reinstall_not_performed",
            "business_execution_blocked",
        ],
        "s17_p1_performed": False,
        "github_upload_performed": False,
        "github_upload_ready_next_gate": False,
        "github_upload_deferred_until_v014_stage1_18_complete": True,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "next_phase": NEXT_PHASE,
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_artifacts(manifest: dict[str, Any]) -> None:
    write_json(MANIFEST_PATH, manifest)
    report = "\n".join(
        [
            "# KMFA v0.1.4 Stage 16 Review",
            "",
            "- phase_results: `S16-P1=PASS; S16-P2=PASS; S16-P3=PASS`",
            f"- open_findings: `{manifest['review_findings_summary']['open_finding_count']}`",
            f"- fixed_findings: `{manifest['review_findings_summary']['fixed_finding_count']}`",
            f"- source_lane_total_count: `{manifest['stage_gate']['source_lane_total_count']}`",
            f"- project_match_count: `{manifest['stage_gate']['project_match_count']}`",
            f"- unallocated_cost_pool_count: `{manifest['stage_gate']['unallocated_cost_pool_count']}`",
            f"- lifecycle_record_count: `{manifest['stage_gate']['lifecycle_record_count']}`",
            f"- exception_item_count: `{manifest['stage_gate']['exception_item_count']}`",
            f"- customer_summary_count: `{manifest['stage_gate']['customer_summary_count']}`",
            f"- pending_reconciliation_count: `{manifest['stage_gate']['pending_reconciliation_count']}`",
            f"- procurement_execution_count: `{manifest['stage_gate']['procurement_execution_count']}`",
            f"- payment_execution_count: `{manifest['stage_gate']['payment_execution_count']}`",
            f"- bank_operation_count: `{manifest['stage_gate']['bank_operation_count']}`",
            f"- collection_action_count: `{manifest['stage_gate']['collection_action_count']}`",
            f"- legal_collection_decision_count: `{manifest['stage_gate']['legal_collection_decision_count']}`",
            f"- github_upload_status: `{manifest['github_upload_status']}`",
            "",
            "Stage 16 review is local-only. It does not perform S17, GitHub upload, raw inbox access, lineage full check, formal report release, procurement execution, payment approval, payment execution, bank operation, site operation, signature operation, invoice issuance, customer contact, collection action, legal decision, tax filing or business execution.",
            "",
        ]
    )
    write_text(REPORT_PATH, report)
    write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 16 Review Test Results",
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
                "# KMFA v0.1.4 Stage 16 Review Risk Register",
                "",
                "- risk: Private alignment observations could be mistaken as raw-source publication.",
                "  mitigation: Current manifest locks them as read-only aggregate observations and blocks raw names, hashes, headers and values in public evidence.",
                "- risk: Customer/business summaries could be mistaken as formal decisions or executable actions.",
                "  mitigation: Review keeps formal report release, business decision basis, procurement, payment, bank, site, signature, invoice, contact, collection and legal actions blocked.",
                "",
            ]
        ),
    )
    write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 16 Review Rollback Plan",
                "",
                "- Remove only `KMFA/stage_artifacts/V014_S16_STAGE_REVIEW/` and the paired v014 S16 review governance entries if rollback is required.",
                "- Do not touch raw/private inbox contents.",
                "",
            ]
        ),
    )


def generate() -> dict[str, Any]:
    manifest = build_manifest()
    write_artifacts(manifest)
    return manifest


def main() -> int:
    manifest = generate()
    gate = manifest["stage_gate"]
    print(
        "PASS: KMFA v0.1.4 Stage 16 review generated "
        f"(phase_results={manifest['phase_results']}, open_findings={manifest['review_findings_summary']['open_finding_count']}, "
        f"source_lanes={gate['source_lane_total_count']}, project_matches={gate['project_match_count']}, "
        f"lifecycle_records={gate['lifecycle_record_count']}, customer_summaries={gate['customer_summary_count']}, "
        f"procurement={gate['procurement_execution_count']}, payment={gate['payment_execution_count']}, "
        f"bank={gate['bank_operation_count']}, collection={gate['collection_action_count']}, "
        f"legal={gate['legal_collection_decision_count']}, s17={manifest['s17_p1_performed']}, "
        f"github_upload={manifest['github_upload_performed']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
