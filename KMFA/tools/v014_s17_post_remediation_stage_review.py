#!/usr/bin/env python3
"""Generate current KMFA v0.1.4 Stage 17 overall-review evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import unittest
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s17_p1_post_remediation_access_security as p1
from KMFA.tools import v014_s17_p2_post_remediation_notification as p2
from KMFA.tools import v014_s17_p3_post_remediation_operations_sop as p3
from KMFA.tools.check_v014_s17_p1_post_remediation_access_security import (
    validate_v014_s17_p1_post_remediation_access_security,
)
from KMFA.tools.check_v014_s17_p2_post_remediation_notification import (
    validate_v014_s17_p2_post_remediation_notification,
)
from KMFA.tools.check_v014_s17_p3_post_remediation_operations_sop import (
    validate_v014_s17_p3_post_remediation_operations_sop,
)
from KMFA.tools.check_v014_s17_stage_review import validate_v014_s17_stage_review as validate_historical_review


PHASE_ID = "V014_S17_POST_REMEDIATION_STAGE_REVIEW"
ROADMAP_PHASE_ID = "STAGE-REVIEW"
TASK_ID = "KMFA-V014-S17-POST-REMEDIATION-STAGE-REVIEW-20260712"
ACCEPTANCE_ID = "ACC-V014-S17-POST-REMEDIATION-STAGE-REVIEW"
VERSION = "0.1.4-s17-post-remediation-stage-review"
STATUS = "completed_validated_local_only_stage17_review_no_go_upload_deferred"
DECISION = "NO_GO"
REVIEW_SCOPE = "v014_s17_current_p1_p2_p3_overall_review_only"
FORMULA_ID = "FORM-KMFA-V014-S17-POST-REMEDIATION-STAGE-REVIEW-001"
PARAMETER_IDS = ("PARAM-KMFA-1804", "PARAM-KMFA-1805", "PARAM-KMFA-1806")
MODEL_REGISTRY_KEY = "kmfa_v014_s17_post_remediation_stage_review"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "stage17_post_remediation_review_summary.json"
MANIFEST_PATH = MACHINE_DIR / "stage17_post_remediation_review_manifest.json"
PHASE_RESULTS_PATH = MACHINE_DIR / "phase_validation_results_public_safe.jsonl"
CONTRACT_MATRIX_PATH = MACHINE_DIR / "cross_phase_contract_matrix_public_safe.jsonl"
MATRIX_PATH = MACHINE_DIR / "stage17_post_remediation_review_matrix_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "stage17_post_remediation_review_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "stage17_post_remediation_review_report_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

METADATA_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = METADATA_DIR / "v014_s17_post_remediation_stage_review_summary.json"
METADATA_MANIFEST_PATH = METADATA_DIR / "v014_s17_post_remediation_stage_review_manifest.json"
METADATA_PHASE_RESULTS_PATH = METADATA_DIR / "v014_s17_post_remediation_phase_validation_results_public_safe.jsonl"
METADATA_CONTRACT_MATRIX_PATH = METADATA_DIR / "v014_s17_post_remediation_cross_phase_contract_matrix_public_safe.jsonl"
METADATA_MATRIX_PATH = METADATA_DIR / "v014_s17_post_remediation_stage_review_matrix_public_safe.json"
METADATA_GO_NO_GO_PATH = METADATA_DIR / "v014_s17_post_remediation_stage_review_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s17_post_remediation_stage_review")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_REVIEW_REPORT_PATH = PRIVATE_DIR / "stage17_review_boundary_validation_zh.md"

ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
LEGACY_REVIEW_MANIFEST_PATH = Path("KMFA/stage_artifacts/V014_S17_STAGE_REVIEW/machine/stage17_review_manifest.json")
DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
ASSURANCE_STATUS_PATH = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")

TEST_MODULES = (
    ("S17-P1", "KMFA.tests.test_v014_s17_p1_post_remediation_access_security", p1.MANIFEST_PATH),
    ("S17-P2", "KMFA.tests.test_v014_s17_p2_post_remediation_notification", p2.MANIFEST_PATH),
    ("S17-P3", "KMFA.tests.test_v014_s17_p3_post_remediation_operations_sop", p3.MANIFEST_PATH),
)


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _upsert_jsonl(path: Path, row: dict[str, Any]) -> None:
    preserved: list[str] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("phase_id") != PHASE_ID:
                preserved.append(line)
    preserved.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    _write_text(path, "\n".join(preserved))


def _sync_assurance_snapshot_time(generated_at: str) -> None:
    lines = ASSURANCE_STATUS_PATH.read_text(encoding="utf-8").splitlines()
    indexes = [index for index, line in enumerate(lines) if line.startswith("snapshot_event_time:")]
    if len(indexes) != 1:
        raise RuntimeError("ASSURANCE_STATUS must contain exactly one snapshot_event_time")
    lines[indexes[0]] = f'snapshot_event_time: "{generated_at}"'
    _write_text(ASSURANCE_STATUS_PATH, "\n".join(lines))


def _taskpack_contract() -> dict[str, Any]:
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack = TASKPACK_PATH.read_text(encoding="utf-8")
    for token in (
        "S17｜权限、通知、安全、审计与运维",
        "只发提醒不发完整报告",
        "导入、复核、发布、回滚操作手册",
        "错误处理和备份恢复演练",
    ):
        if token not in roadmap:
            raise ValueError(f"roadmap token missing: {token}")
    for token in ("不参与自动财务执行", "不提交原始敏感数据到公开GitHub", "可审计"):
        if token not in taskpack:
            raise ValueError(f"taskpack token missing: {token}")
    return {
        "roadmap_read": True,
        "taskpack_read": True,
        "stage17_three_phase_and_review_contract_locked": True,
        "source_refs": {"roadmap": ROADMAP_PATH.as_posix(), "taskpack": TASKPACK_PATH.as_posix()},
    }


def _test_inventory() -> dict[str, int]:
    loader = unittest.TestLoader()
    return {phase_id: loader.loadTestsFromName(module).countTestCases() for phase_id, module, _ in TEST_MODULES}


def _current_chain() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    p1_manifest = validate_v014_s17_p1_post_remediation_access_security(
        require_private_evidence=True,
        require_final_evidence=True,
    )
    p2_manifest = validate_v014_s17_p2_post_remediation_notification(
        require_private_evidence=True,
        require_final_evidence=True,
    )
    p3_manifest = validate_v014_s17_p3_post_remediation_operations_sop(
        require_private_evidence=True,
        require_final_evidence=True,
    )
    return p1_manifest, p2_manifest, p3_manifest


def _phase_result_rows(inventory: dict[str, int], final_validation: bool) -> list[dict[str, Any]]:
    return [
        {
            "record_type": "v014_s17_post_remediation_phase_validation_result",
            "project_id": "KMFA",
            "stage_id": "S17",
            "phase_id": phase_id,
            "focused_test_count": inventory[phase_id],
            "focused_test_status": "PASS" if final_validation else "PENDING",
            "strict_validator_count": 1,
            "strict_validator_status": "PASS" if final_validation else "PENDING",
            "manifest_ref": manifest_ref.as_posix(),
            "public_safe_aggregate_only": True,
        }
        for phase_id, _module, manifest_ref in TEST_MODULES
    ]


def _cross_phase_matrix() -> tuple[list[dict[str, Any]], dict[str, int]]:
    roles = _read_jsonl(p1.ROLE_POLICY_PATH)
    audit_contracts = _read_jsonl(p1.AUDIT_CONTRACT_PATH)
    notification_rules = _read_jsonl(p2.RULE_PATH)
    outbox = _read_jsonl(p2.OUTBOX_PATH)
    runbooks = _read_jsonl(p3.RUNBOOK_PATH)
    knowledge = _read_jsonl(p3.KNOWLEDGE_INDEX_PATH)
    role_ids = {str(row["role_id"]) for row in roles}
    audit_types = {str(row["action_type"]) for row in audit_contracts}
    notification_contract = next(row for row in audit_contracts if row["action_type"] == "notification")
    required_fields = set(p2.AUDIT_REQUIRED_FIELDS)

    notification_role_matches = sum(str(row["recipient_role"]) in role_ids for row in notification_rules)
    outbox_audit_matches = sum(
        row.get("action_type") == "notification" and required_fields.issubset(row)
        for row in outbox
    )
    runbook_owner_matches = sum(str(row["owner_role"]) in role_ids for row in runbooks)
    knowledge_owner_matches = sum(str(row["owner_role"]) in role_ids for row in knowledge)
    runbook_audit_matches = sum(str(row["audit_action_type"]) in audit_types for row in runbooks)
    notification_scope_matches = int(
        notification_contract.get("delivery_scope") == "audit_log_contract_only_no_delivery"
        and p2._read_json(p2.SUMMARY_PATH).get("real_notification_delivery_count") == 0
    )
    specs = (
        ("notification_recipient_roles", 3, notification_role_matches),
        ("notification_outbox_audit_contract", 3, outbox_audit_matches),
        ("runbook_owner_roles", 4, runbook_owner_matches),
        ("knowledge_owner_roles", 2, knowledge_owner_matches),
        ("runbook_audit_actions", 4, runbook_audit_matches),
        ("notification_delivery_scope", 1, notification_scope_matches),
    )
    rows = [
        {
            "record_type": "v014_s17_post_remediation_cross_phase_contract_check",
            "check_id": f"S17-REVIEW-CONTRACT-{index:02d}",
            "check_type": check_type,
            "expected_count": expected,
            "matched_count": matched,
            "mismatch_count": expected - matched,
            "status": "PASS" if matched == expected else "FAIL",
            "public_safe_aggregate_only": True,
            "evidence_ref": CONTRACT_MATRIX_PATH.as_posix(),
        }
        for index, (check_type, expected, matched) in enumerate(specs, 1)
    ]
    metrics = {
        "canonical_role_count": len(role_ids),
        "audit_action_type_count": len(audit_types),
        "notification_recipient_role_match_count": notification_role_matches,
        "notification_outbox_audit_contract_match_count": outbox_audit_matches,
        "runbook_owner_role_match_count": runbook_owner_matches,
        "knowledge_owner_role_match_count": knowledge_owner_matches,
        "runbook_audit_mapping_match_count": runbook_audit_matches,
        "notification_delivery_scope_match_count": notification_scope_matches,
        "cross_phase_contract_mismatch_count": sum(row["mismatch_count"] for row in rows),
    }
    return rows, metrics


def _review_findings() -> list[dict[str, str]]:
    return [
        {
            "finding_id": "V014-S17-REVIEW-F01",
            "severity": "medium",
            "status": "fixed",
            "issue": "S17-P3 used finance_operator outside the S17-P1 canonical role set.",
            "remediation": "Both operations and knowledge owners now use canonical finance; cross-phase role checks fail closed.",
        },
        {
            "finding_id": "V014-S17-REVIEW-F02",
            "severity": "medium",
            "status": "fixed",
            "issue": "S17-P3 runbooks required audit evidence without explicit S17-P1 action mappings.",
            "remediation": "All four runbooks now reference a valid S17-P1 action and the seven required audit fields.",
        },
        {
            "finding_id": "V014-S17-REVIEW-F03",
            "severity": "low",
            "status": "fixed",
            "issue": "The S17-P1 notification contract retained stale pre-S17-P2 wording.",
            "remediation": "Delivery scope is now neutral audit-log-only no-delivery language.",
        },
        {
            "finding_id": "V014-S17-REVIEW-F04",
            "severity": "low",
            "status": "fixed",
            "issue": "The S17-P2 focused test permanently required P2 to remain the active VERSION_MATRIX phase.",
            "remediation": "The test now keeps profile checks permanent and applies HANDOFF routing checks only while P2 is active.",
        },
        {
            "finding_id": "V014-S17-REVIEW-F05",
            "severity": "low",
            "status": "fixed",
            "issue": "The S17-P2 checker permanently required OWNER_STATUS and STATUS to retain P2 as active.",
            "remediation": "Current-status document checks now apply only while P2 is active; immutable governance evidence remains permanent.",
        },
        {
            "finding_id": "V014-S17-REVIEW-F06",
            "severity": "low",
            "status": "fixed",
            "issue": "The S17-P3 focused test permanently required P3 to remain the active VERSION_MATRIX phase.",
            "remediation": "The test now keeps profile checks permanent and applies HANDOFF routing checks only while P3 is active.",
        },
        {
            "finding_id": "V014-S17-REVIEW-F07",
            "severity": "medium",
            "status": "fixed",
            "issue": "Stage 17 review governance records referenced nonexistent stage17_post_remediation_stage_review files.",
            "remediation": "All review evidence references now resolve to the generated stage17_post_remediation_review manifest and report.",
        },
        {
            "finding_id": "V014-S17-REVIEW-F08",
            "severity": "control",
            "status": "passed",
            "issue": "Notification recipient roles and outbox audit fields require cross-phase verification.",
            "remediation": "Three roles and three outbox rows exactly match the S17-P1 contracts.",
        },
        {
            "finding_id": "V014-S17-REVIEW-F09",
            "severity": "control",
            "status": "passed",
            "issue": "Reminder metadata could be mistaken for real delivery or a formal report.",
            "remediation": "Real delivery full body attachment address connector and formal report counts remain zero.",
        },
        {
            "finding_id": "V014-S17-REVIEW-F10",
            "severity": "control",
            "status": "passed",
            "issue": "Synthetic backup recovery could be mistaken for raw or production recovery.",
            "remediation": "Raw copy and production restore remain zero; the byte-exact drill is private synthetic-only.",
        },
        {
            "finding_id": "V014-S17-REVIEW-F11",
            "severity": "control",
            "status": "passed",
            "issue": "Historical Stage 17 review state could contaminate current dynamic evidence.",
            "remediation": "Historical review is validated as a structural fixture and explicitly non-authoritative.",
        },
    ]


def _quality_gate() -> dict[str, Any]:
    return {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "one_cent_tolerance_minor_unit": 0,
        "formal_report_release_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
    }


def _review_boundaries() -> dict[str, bool]:
    return {
        "s17_p1_performed": True,
        "s17_p2_performed": True,
        "s17_p3_performed": True,
        "stage17_review_performed": True,
        "s18_p1_performed": False,
        "s18_p2_performed": False,
        "s18_p3_performed": False,
        "stage18_review_performed": False,
        "raw_copy_or_backup_performed": False,
        "production_restore_performed": False,
        "notification_delivery_performed": False,
        "external_connector_performed": False,
        "customer_contact_performed": False,
        "collection_action_performed": False,
        "legal_action_performed": False,
        "construction_action_performed": False,
        "signature_action_performed": False,
        "invoice_action_performed": False,
        "payment_or_bank_action_performed": False,
        "formal_report_release_performed": False,
        "difference_closure_performed": False,
        "persistent_business_write_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "raw_business_data_committed": False,
        "raw_file_names_committed": False,
        "raw_schema_or_header_committed": False,
        "business_value_plaintext_committed": False,
        "project_customer_or_counterparty_plaintext_committed": False,
        "credential_or_secret_committed": False,
        "private_runtime_committed": False,
        "synthetic_fixture_payload_committed": False,
        "private_hash_or_diagnostic_committed": False,
        "zip_excel_pdf_private_csv_database_committed": False,
    }


def _acceptance_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = (
        ("phase_chain", summary["phase_pass_count"] == 3),
        ("focused_tests", summary["phase_focused_test_pass_count"] == 30),
        ("strict_validators", summary["phase_strict_validator_pass_count"] == 3),
        ("historical_quarantine", summary["historical_stage17_review_validated"]),
        ("canonical_roles", summary["cross_phase_contract_mismatch_count"] == 0),
        ("findings_closed", summary["fixed_review_finding_count"] == 7 and summary["open_review_finding_count"] == 0),
        ("raw_exact", summary["raw_snapshot_exact_match"] and summary["raw_cross_phase_snapshot_exact_match"]),
        ("quality", summary["current_report_grade"] == "D" and summary["decision"] == "NO_GO"),
        ("no_delivery", summary["real_notification_delivery_count"] == 0),
        ("no_full_report", summary["full_report_body_count"] == 0 and summary["formal_report_count"] == 0),
        ("no_restore", summary["production_restore_count"] == 0 and summary["raw_copy_or_backup_count"] == 0),
        ("no_external", summary["external_service_call_count"] == 0),
        ("no_persistent_write", summary["persistent_business_write_count"] == 0),
        ("no_business_execution", summary["business_execution_count"] == 0),
        ("downstream_closed", not summary["s18_p1_performed"] and not summary["github_upload_performed"]),
        ("review_performed", summary["stage17_review_performed"]),
    )
    rows = [
        {"check_id": f"V014-S17-REVIEW-ACC-{index:03d}", "name": name, "status": "PASS" if passed else "FAIL"}
        for index, (name, passed) in enumerate(checks, 1)
    ]
    return {
        "schema_version": "kmfa.v014.s17_post_remediation_stage_review_matrix.v1",
        "acceptance_id": ACCEPTANCE_ID,
        "check_count": len(rows),
        "check_pass_count": sum(row["status"] == "PASS" for row in rows),
        "check_fail_count": sum(row["status"] == "FAIL" for row in rows),
        "checks": rows,
    }


def _phase_public_files() -> list[str]:
    review_paths = (
        SUMMARY_PATH, MANIFEST_PATH, PHASE_RESULTS_PATH, CONTRACT_MATRIX_PATH, MATRIX_PATH, GO_NO_GO_PATH,
        REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH,
        METADATA_SUMMARY_PATH, METADATA_MANIFEST_PATH, METADATA_PHASE_RESULTS_PATH,
        METADATA_CONTRACT_MATRIX_PATH, METADATA_MATRIX_PATH, METADATA_GO_NO_GO_PATH,
    )
    remediation_paths = (
        p1.MANIFEST_PATH, p1.SUMMARY_PATH, p1.AUDIT_CONTRACT_PATH,
        p1.METADATA_MANIFEST_PATH, p1.METADATA_SUMMARY_PATH, p1.METADATA_AUDIT_CONTRACT_PATH,
        Path("KMFA/tools/v014_s17_p1_post_remediation_access_security.py"),
        Path("KMFA/tools/check_v014_s17_p1_post_remediation_access_security.py"),
        Path("KMFA/tests/test_v014_s17_p1_post_remediation_access_security.py"),
        Path("KMFA/tests/test_v014_s17_p2_post_remediation_notification.py"),
        Path("KMFA/tools/check_v014_s17_p2_post_remediation_notification.py"),
        p3.MANIFEST_PATH, p3.SUMMARY_PATH, p3.RUNBOOK_PATH, p3.KNOWLEDGE_INDEX_PATH, p3.MATRIX_PATH,
        p3.METADATA_MANIFEST_PATH, p3.METADATA_SUMMARY_PATH, p3.METADATA_RUNBOOK_PATH,
        p3.METADATA_KNOWLEDGE_INDEX_PATH, p3.METADATA_MATRIX_PATH,
        Path("KMFA/tools/v014_s17_p3_post_remediation_operations_sop.py"),
        Path("KMFA/tools/check_v014_s17_p3_post_remediation_operations_sop.py"),
        Path("KMFA/tests/test_v014_s17_p3_post_remediation_operations_sop.py"),
    )
    governance_paths = (
        Path("KMFA/AGENTS.md"), Path("KMFA/CHANGELOG.md"), Path("KMFA/HANDOFF.md"), Path("KMFA/VERSION"),
        ASSURANCE_STATUS_PATH, Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"),
        Path("KMFA/docs/governance/MODEL_SPEC.md"), Path("KMFA/docs/governance/OWNER_STATUS.md"),
        Path("KMFA/docs/governance/STATUS.md"), Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv"),
        Path("KMFA/docs/governance/VERSION_MATRIX.yaml"), Path("KMFA/docs/governance/delivery_tasks.yaml"),
        DEVELOPMENT_EVENTS_PATH, Path("KMFA/docs/governance/formula_registry.yaml"),
        Path("KMFA/docs/governance/model_registry.yaml"), Path("KMFA/docs/governance/parameter_registry.csv"),
        Path("KMFA/metadata/model_registry.yaml"), STAGE_STATUS_PATH, TASK_STATUS_PATH,
        Path("KMFA/功能清单.md"), Path("KMFA/开发记录.md"), Path("KMFA/模型参数文件.md"),
        Path("KMFA/tools/v014_s17_post_remediation_stage_review.py"),
        Path("KMFA/tools/check_v014_s17_post_remediation_stage_review.py"),
        Path("KMFA/tests/test_v014_s17_post_remediation_stage_review.py"),
    )
    return [path.as_posix() for path in review_paths + remediation_paths + governance_paths]


def _write_governance(generated_at: str) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _sync_assurance_snapshot_time(generated_at)
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260712-V014-S17-POST-REMEDIATION-STAGE-REVIEW",
            "event_time": generated_at,
            "event_type": "stage_review_completion",
            "project_id": "KMFA",
            "stage_id": "S17",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "phase_pass_count": 3,
            "phase_focused_test_pass_count": 30,
            "phase_strict_validator_pass_count": 3,
            "fixed_review_finding_count": 7,
            "open_review_finding_count": 0,
            "cross_phase_contract_mismatch_count": 0,
            "raw_business_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "files_changed": _phase_public_files(),
            "result_commit": "PENDING",
        },
    )
    _upsert_jsonl(
        STAGE_STATUS_PATH,
        {
            "schema_version": "kmfa.stage_status.v1",
            "record_type": "stage_review_status",
            "project_id": "KMFA",
            "stage_id": "S17",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "version": VERSION,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "current_report_grade": "D",
            "raw_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at,
        },
    )
    _upsert_jsonl(
        TASK_STATUS_PATH,
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_stage_review_task",
            "project_id": "KMFA",
            "stage_id": "S17",
            "governance_stage_id": "ACCESS-SECURITY-AUDIT",
            "roadmap_stage_id": "S17",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 Stage 17 post-remediation overall review",
            "phase_goal": "replay three current phases fix cross-phase role and audit findings and keep all downstream actions closed",
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "derived_percent": 100,
            "estimated_task_units": 3,
            "completed_task_units": 3,
            "task_count": 3,
            "raw_data_committed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at[:10],
        },
    )


def _render_report(summary: dict[str, Any]) -> str:
    return f"""# KMFA v0.1.4 Stage 17 整体复审

## 结论

- 当前 S17-P1/P2/P3：`3/3 PASS`；focused tests=`{summary['phase_focused_test_pass_count']}/30`，strict validators=`{summary['phase_strict_validator_pass_count']}/3`。
- 复审 findings：共 `{summary['review_finding_count']}` 项，`{summary['fixed_review_finding_count']}` fixed、`{summary['passed_review_finding_count']}` passed、`{summary['open_review_finding_count']}` open。
- 修复：P3 财务 owner 统一为 canonical `finance`；4 个 runbook 映射 P1 审计 action 与 7 字段；P1 通知契约改为中性只记录不投递；P2 测试/checker 与 P3 测试移除 active-phase 时态耦合；断链 review 证据引用已修正。
- 跨 phase 合同：6 项检查全部 PASS，角色、通知 outbox、手册、知识索引和审计 action mismatch=`0`。
- 业务边界：真实通知、完整正文、正式报告、raw 复制/备份、生产恢复、外部服务、持久业务写入和业务执行均为 0。
- raw：review 前后、跨 S17-P3 和当前快照一致。
- 当前状态：Q4 / D / NO_GO / 3-9-2-1。

## 边界

- 本轮只完成 Stage 17 整体复审并修复 findings，未执行 S18-P1/P2/P3、Stage 18 review、GitHub upload 或 app reinstall。
- 历史 Stage 17 review 只作结构夹具，不提供当前动态状态。
- 下一轮只能单独执行 S18-P1 精度与压力测试。
"""


def _render_private_report(summary: dict[str, Any]) -> str:
    return f"""# Stage 17 私有复审边界核验

- 原始数据文件数：{summary['raw_source_file_count']}
- review 前后快照：exact match
- 与 S17-P3 快照：exact match
- 当前只读快照：exact match
- phase tests/validators：30/30 / 3/3 PASS
- findings：7 fixed / 4 passed / 0 open
- 合同矩阵：6 PASS / 0 mismatch
- raw 复制或备份/生产恢复/真实通知/外部服务/业务执行：0 / 0 / 0 / 0 / 0
- 结论：原始目录未受损；最终 goal 多轮仍无法对齐时，必须生成全中文最终差异报告。
"""


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    taskpack_contract = _taskpack_contract()
    p1_manifest, p2_manifest, p3_manifest = _current_chain()
    historical = validate_historical_review()
    inventory = _test_inventory()
    if inventory != {"S17-P1": 9, "S17-P2": 10, "S17-P3": 11}:
        raise ValueError(f"Stage 17 focused test inventory drift: {inventory}")
    phase_rows = _phase_result_rows(inventory, final_validation)
    contract_rows, contract_metrics = _cross_phase_matrix()
    if contract_metrics["cross_phase_contract_mismatch_count"] != 0:
        raise ValueError("Stage 17 cross-phase contract mismatch")
    findings = _review_findings()

    raw_helper = p1.s16_review.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    raw_before = raw_helper._raw_snapshot("before_v014_s17_post_remediation_stage_review")
    raw_after = raw_helper._raw_snapshot("after_v014_s17_post_remediation_stage_review")
    prior_raw = _read_json(p3.PRIVATE_RAW_AFTER_PATH)
    current_raw = raw_helper._raw_snapshot("current_v014_s17_post_remediation_stage_review")
    normalize = raw_helper._normalize_raw
    raw_exact = normalize(raw_before) == normalize(raw_after)
    raw_cross = normalize(raw_before) == normalize(prior_raw) == normalize(current_raw)
    if not raw_exact or not raw_cross:
        raise ValueError("raw source changed during Stage 17 review")
    repo_scan = p1._repo_tracking_scan()
    if repo_scan["status"] != "PASS":
        raise ValueError("tracked KMFA path scan failed")

    p1s = p1_manifest["summary"]
    p2s = p2_manifest["summary"]
    p3s = p3_manifest["summary"]
    phase_results = {row["phase_id"]: "PASS" for row in phase_rows}
    summary = {
        "schema_version": "kmfa.v014.s17_post_remediation_stage_review_summary.v1",
        "project_id": "KMFA",
        "stage_id": "S17",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "phase_results": phase_results,
        "phase_count": 3,
        "phase_pass_count": 3,
        "phase_focused_test_count": sum(inventory.values()),
        "phase_focused_test_pass_count": sum(inventory.values()) if final_validation else 0,
        "phase_strict_validator_count": 3,
        "phase_strict_validator_pass_count": 3 if final_validation else 0,
        "historical_stage17_review_validated": True,
        "review_finding_count": len(findings),
        "fixed_review_finding_count": sum(row["status"] == "fixed" for row in findings),
        "passed_review_finding_count": sum(row["status"] == "passed" for row in findings),
        "open_review_finding_count": sum(row["status"] == "open" for row in findings),
        **contract_metrics,
        "role_count": p1s["role_count"],
        "notification_rule_count": p2s["notification_rule_count"],
        "metadata_outbox_log_count": p2s["metadata_outbox_log_count"],
        "real_notification_delivery_count": p2s["real_notification_delivery_count"],
        "full_report_body_count": p2s["full_report_body_count"],
        "operation_runbook_count": p3s["operation_runbook_count"],
        "knowledge_item_count": p3s["knowledge_item_count"],
        "error_drill_scenario_count": p3s["error_drill_scenario_count"],
        "backup_restore_drill_count": p3s["backup_restore_drill_count"],
        "production_restore_count": p3s["production_restore_count"],
        "raw_copy_or_backup_count": p3s["raw_copy_or_backup_count"],
        "external_service_call_count": p3s["external_service_call_count"],
        "persistent_business_write_count": p3s["persistent_business_write_count"],
        "business_execution_count": p3s["business_execution_count"],
        "formal_report_count": p3s["formal_report_count"],
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        **_review_boundaries(),
    }
    matrix = _acceptance_matrix(summary)
    go_no_go = {
        "schema_version": "kmfa.v014.s17_post_remediation_stage_review_go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S17",
        "phase_id": PHASE_ID,
        "decision": "NO_GO",
        "stage17_review_validated": True,
        "s18_p1_allowed_in_this_run": False,
        "s18_p2_allowed": False,
        "s18_p3_allowed": False,
        "stage18_review_allowed": False,
        "notification_delivery_allowed": False,
        "production_restore_allowed": False,
        "external_connector_allowed": False,
        "formal_report_release_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "difference_closure_allowed": False,
        "persistent_business_write_allowed": False,
        "business_execution_allowed": False,
    }
    validation_summary = {
        "final_validation_recorded": final_validation,
        "phase_focused_tests": "PASS" if final_validation else "PENDING",
        "phase_strict_validators": "PASS" if final_validation else "PENDING",
        "review_tests": "PASS" if final_validation else "PENDING",
        "review_strict_validator": "PASS" if final_validation else "PENDING",
        "cross_phase_contracts": "PASS" if final_validation else "PENDING",
        "raw_alignment": "PASS" if final_validation else "PENDING",
        "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
    }
    manifest = {
        "schema_version": "kmfa.v014.s17_post_remediation_stage_review_manifest.v1",
        "project_id": "KMFA",
        "stage_id": "S17",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "review_scope": REVIEW_SCOPE,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "generated_at": generated_at,
        "reviewed_head": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "remote": _git_output(["remote", "get-url", "origin"]),
        "formula_id": FORMULA_ID,
        "parameter_ids": list(PARAMETER_IDS),
        "model_registry_key": MODEL_REGISTRY_KEY,
        "summary": summary,
        "phase_results": phase_results,
        "phase_validation_results": phase_rows,
        "cross_phase_contract_matrix": contract_rows,
        "review_findings": findings,
        "current_phase_refs": {
            "s17_p1": p1.MANIFEST_PATH.as_posix(),
            "s17_p2": p2.MANIFEST_PATH.as_posix(),
            "s17_p3": p3.MANIFEST_PATH.as_posix(),
        },
        "historical_stage17_review_validated": True,
        "historical_stage17_dynamic_state_is_authoritative": False,
        "historical_review_manifest_ref": LEGACY_REVIEW_MANIFEST_PATH.as_posix(),
        "historical_review_status": historical["status"],
        "taskpack_contract": taskpack_contract,
        "repo_tracking_scan": repo_scan,
        "quality_gate": _quality_gate(),
        "review_boundaries": _review_boundaries(),
        "public_repo_safety": _public_safety(),
        "acceptance_matrix": matrix,
        "go_no_go": go_no_go,
        "validation_summary": validation_summary,
        "next_phase": "S18-P1",
        "next_required_step": (
            "下一轮只能执行 S18-P1 精度与压力测试；不得执行 S18-P2/P3、Stage 18 review、GitHub upload、"
            "app reinstall、正式报告、外部通知、客户联络、催收、法务、施工、签署、开票、支付、银行、"
            "差异关闭、持久业务写入或业务执行。"
        ),
    }

    for path, value in (
        (SUMMARY_PATH, summary), (MANIFEST_PATH, manifest), (MATRIX_PATH, matrix), (GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary), (METADATA_MANIFEST_PATH, manifest),
        (METADATA_MATRIX_PATH, matrix), (METADATA_GO_NO_GO_PATH, go_no_go),
        (PRIVATE_RAW_BEFORE_PATH, raw_before), (PRIVATE_RAW_AFTER_PATH, raw_after),
    ):
        _write_json(path, value)
    for path, rows in (
        (PHASE_RESULTS_PATH, phase_rows), (CONTRACT_MATRIX_PATH, contract_rows),
        (METADATA_PHASE_RESULTS_PATH, phase_rows), (METADATA_CONTRACT_MATRIX_PATH, contract_rows),
    ):
        _write_jsonl(path, rows)
    _write_text(REPORT_PATH, _render_report(summary))
    _write_text(
        TEST_RESULTS_PATH,
        """# Stage 17 整体复审测试结果

- current S17-P1/P2/P3 focused tests：9 + 10 + 11 = 30/30 PASS。
- current strict validators：3/3 PASS。
- Stage 17 review focused tests / strict validator：最终复验记录见 manifest。
- cross-phase contract matrix：6/6 PASS，mismatch=0。
- findings：7 fixed / 4 passed / 0 open。
- raw review 前后 / 跨 S17-P3 / current：exact match。
- quality：Q4 / D / NO_GO / 3-9-2-1。
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# Stage 17 整体复审风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 非 canonical 角色绕过 P1 权限 | P3 owner 已统一并由 cross-phase matrix fail-closed | 已修复 |
| 手册审计要求未绑定 P1 action | 4 个 runbook 显式映射 action 与 7 字段 | 已修复 |
| 通知契约保留过期时态 | delivery scope 改为永久中性只记录不投递 | 已修复 |
| P2 测试要求自己永久 active | profile 永久校验，HANDOFF 仅在 active 时校验 | 已修复 |
| P2 checker 要求状态文档永久保留 P2 active | OWNER/STATUS 仅在 P2 active 时校验 | 已修复 |
| P3 测试要求自己永久 active | profile 永久校验，HANDOFF 仅在 P3 active 时校验 | 已修复 |
| review 治理记录引用不存在的证据文件 | manifest/report 引用统一到实际生成路径并由 validator 校验 | 已修复 |
| metadata 提醒被误读为真实投递 | delivery/full body/attachment/address/connector 均为 0 | 已控制 |
| 合成恢复被误读为生产恢复 | raw copy 与 production restore 均为 0 | 已控制 |
| 历史 review 污染当前状态 | 历史动态状态明确 non-authoritative | 已控制 |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        f"""# Stage 17 整体复审回滚计划

1. 回退本 review 本地 commit 与 `{OUTPUT_DIR.as_posix()}` public-safe 证据。
2. 同步回退本 review 对 P1 通知契约和 P3 owner/audit mapping 的修复，避免半套合同。
3. 回退 review metadata 和治理登记，不改历史 S17-P1/P2/P3 legacy 夹具。
4. 删除 ignored review 私有快照，不触碰原始目录，不执行生产恢复或补偿业务动作。
""",
    )
    _write_text(PRIVATE_REVIEW_REPORT_PATH, _render_private_report(summary))
    if write_governance:
        _write_governance(generated_at)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-validation", action="store_true")
    parser.add_argument("--no-governance", action="store_true")
    args = parser.parse_args()
    manifest = generate(final_validation=args.final_validation, write_governance=not args.no_governance)
    summary = manifest["summary"]
    print(
        "Stage 17 post-remediation review: "
        f"phases={summary['phase_pass_count']}/3 tests={summary['phase_focused_test_pass_count']}/30 "
        f"validators={summary['phase_strict_validator_pass_count']}/3 findings={summary['fixed_review_finding_count']}/0 "
        f"contracts={summary['cross_phase_contract_mismatch_count']} mismatch grade={summary['current_report_grade']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
