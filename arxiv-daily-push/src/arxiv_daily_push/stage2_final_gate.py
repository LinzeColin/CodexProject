"""S2PL/S2PM fail-closed final production gate precheck helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


S2PMT07_FINAL_GATE_MODEL_ID = "adp-s2pmt07-final-gate-precheck-v1"
S2PMT07_ACCEPTANCE_ID = "ACC-S2PMT07-FINAL-REVIEW"
S2PMT07_TASK_ID = "S2PMT07"
S2PMT07_SCHEMA_VERSION = 1
S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS = 8
S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS = 37
S2PMT07_REQUIRED_REVIEWER_INDEPENDENCE = "not_involved_in_S2PMT01_T06_implementation"
S2PMT07_REQUIRED_ZERO_FINDING_SEVERITIES = ("P0", "P1")
S2PMT07_REQUIRED_DEPENDENCIES = (
    "S2PMT01",
    "S2PMT02",
    "S2PMT03",
    "S2PMT04",
    "S2PMT05",
    "S2PMT06",
    "S2PLT04",
)
S2PMT07_REQUIRED_EVIDENCE = (
    "FINAL_ACCEPTANCE_BUNDLE/",
    "HANDOFF/00_下一Agent先读.md",
    "independent_review_signoff.yaml",
)
S2PMT07_REQUIRED_TEST_COMMANDS = (
    "python tools/validate_task_pack.py --root .",
    "python -m pytest -q",
    "python tools/verify_acceptance_bundle.py --require-zero P0 P1",
)
S2PMT07_FORBIDDEN_PASS_FLAGS = (
    "integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_send_enabled",
    "scheduler_install_enabled",
    "release_packaging_enabled",
    "production_restore_enabled",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PMT07_BLOCKING_REASONS = (
    "reviewer_independence_not_proven",
    "inherited_v7_1_p0_findings_open",
    "inherited_v7_1_p1_findings_open",
    "s2plt04_not_completed",
    "final_acceptance_bundle_missing",
    "independent_review_signoff_missing",
)
S2PLT04_INTEGRATION_CANDIDATE_MODEL_ID = "adp-s2plt04-integration-candidate-precheck-v1"
S2PLT04_ACCEPTANCE_ID = "ACC-S2PLT04-INTEGRATION-CANDIDATE"
S2PLT04_TASK_ID = "S2PLT04"
S2PLT04_SCHEMA_VERSION = 1
S2PLT04_REQUIRED_DEPENDENCIES = (
    "S2PLT01",
    "S2PLT02",
    "S2PLT03",
)
S2PLT04_AVAILABLE_LOCAL_EVIDENCE = (
    "S2PLT01-INDEPENDENT-REPLAY-REVIEW",
    "S2PMT01",
    "S2PMT02",
    "S2PMT03",
    "S2PMT04",
    "S2PMT05",
    "S2PMT06",
    "S2PMT07",
)
S2PLT04_REQUIRED_EVIDENCE = (
    "S2PLT01_ACCEPTED",
    "S2PLT02_2D_REAL_RUN",
    "S2PLT03_RESILIENCE_DRILL",
    "STATE_CONSISTENCY_EVIDENCE",
    "CONTENT_EVIDENCE",
    "FINAL_ACCEPTANCE_BUNDLE/",
)
S2PLT04_FORBIDDEN_FLAGS = (
    "s2_integration_candidate_ready",
    "s2plt04_completed",
    "integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_sent",
    "scheduler_enabled",
    "release_uploaded",
    "production_restore_executed",
    "production_queue_mutated",
    "public_schema_changed",
    "db_migration_executed",
    "source_adapter_changed",
    "ranking_algorithm_changed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PLT04_BLOCKING_REASONS = (
    "s2plt01_not_accepted",
    "s2plt02_not_completed",
    "s2plt03_not_completed",
    "final_acceptance_bundle_missing",
    "inherited_v7_1_p0_findings_open",
    "inherited_v7_1_p1_findings_open",
)


def build_s2plt04_dependency_state() -> dict[str, Any]:
    """Build current S2PLT04 dependency state without accepting upstream tasks."""

    available_local_evidence = {
        task_id: "local_evidence_present_not_terminal_acceptance"
        for task_id in S2PLT04_AVAILABLE_LOCAL_EVIDENCE
    }
    return {
        "status": "blocked",
        "required_dependencies": list(S2PLT04_REQUIRED_DEPENDENCIES),
        "completed_dependencies": {},
        "unmet_dependencies": list(S2PLT04_REQUIRED_DEPENDENCIES),
        "available_local_evidence": available_local_evidence,
        "s2plt01_acceptance_status": "blocked_by_inherited_p0_p1_and_final_gates",
        "s2plt02_status": "missing_authoritative_completion_evidence",
        "s2plt03_status": "missing_authoritative_completion_evidence",
    }


def build_s2plt04_evidence_state() -> dict[str, Any]:
    """Build current S2PLT04 evidence state from local governance facts."""

    available = {
        "S2PLT01_ACCEPTED": False,
        "S2PLT02_2D_REAL_RUN": False,
        "S2PLT03_RESILIENCE_DRILL": False,
        "STATE_CONSISTENCY_EVIDENCE": True,
        "CONTENT_EVIDENCE": True,
        "FINAL_ACCEPTANCE_BUNDLE/": False,
    }
    return {
        "status": "blocked",
        "required_evidence": list(S2PLT04_REQUIRED_EVIDENCE),
        "available_evidence": available,
        "missing_evidence": [item for item, present in available.items() if not present],
        "state_consistency_basis": "S2PMT02_through_S2PMT06_local_validation",
        "content_evidence_basis": "S2PHT05_S2PIT04_S2PKT05_local_validation",
        "production_evidence_basis": "not_present",
    }


def build_s2plt04_integration_candidate_report(*, generated_at: str) -> dict[str, Any]:
    """Build a deterministic fail-closed S2PLT04 integration-candidate precheck."""

    dependencies = build_s2plt04_dependency_state()
    evidence = build_s2plt04_evidence_state()
    audit_blockers = build_audit_blocker_state()
    s2pmt07 = build_s2pmt07_precheck_report(generated_at=generated_at)
    gates = {
        "dependencies_complete": dependencies["status"] == "pass",
        "s2plt01_accepted": "S2PLT01" in dependencies["completed_dependencies"],
        "s2plt02_completed": "S2PLT02" in dependencies["completed_dependencies"],
        "s2plt03_completed": "S2PLT03" in dependencies["completed_dependencies"],
        "state_consistency_evidence_present": evidence["available_evidence"]["STATE_CONSISTENCY_EVIDENCE"],
        "content_evidence_present": evidence["available_evidence"]["CONTENT_EVIDENCE"],
        "final_acceptance_bundle_present": evidence["available_evidence"]["FINAL_ACCEPTANCE_BUNDLE/"],
        "p0_zero": audit_blockers["checks"]["P0_zero"],
        "p1_zero": audit_blockers["checks"]["P1_zero"],
        "s2pmt07_precheck_passed": s2pmt07["status"] == "pass",
        "no_production_side_effect": True,
    }
    blocking_reasons: list[str] = []
    if not gates["s2plt01_accepted"]:
        blocking_reasons.append("s2plt01_not_accepted")
    if not gates["s2plt02_completed"]:
        blocking_reasons.append("s2plt02_not_completed")
    if not gates["s2plt03_completed"]:
        blocking_reasons.append("s2plt03_not_completed")
    if not gates["final_acceptance_bundle_present"]:
        blocking_reasons.append("final_acceptance_bundle_missing")
    if not gates["p0_zero"]:
        blocking_reasons.append("inherited_v7_1_p0_findings_open")
    if not gates["p1_zero"]:
        blocking_reasons.append("inherited_v7_1_p1_findings_open")
    if not gates["s2pmt07_precheck_passed"]:
        blocking_reasons.append("s2pmt07_final_gate_precheck_blocked")
    report = {
        "model_id": S2PLT04_INTEGRATION_CANDIDATE_MODEL_ID,
        "schema_version": S2PLT04_SCHEMA_VERSION,
        "task_id": S2PLT04_TASK_ID,
        "acceptance_id": S2PLT04_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": "pass" if not blocking_reasons and all(gates.values()) else "blocked",
        "scope": "no_production_integration_candidate_precheck_only",
        "gates": gates,
        "dependencies": dependencies,
        "evidence": evidence,
        "audit_blockers": audit_blockers,
        "s2pmt07_precheck": s2pmt07,
        "blocking_reasons": blocking_reasons,
        "production_acceptance_claimed": False,
        "inherited_p0_p1_closed": False,
        "candidate_hash": "",
        **{flag: False for flag in S2PLT04_FORBIDDEN_FLAGS},
    }
    report["candidate_hash"] = _stable_hash({key: value for key, value in report.items() if key != "candidate_hash"})
    return report


def validate_s2plt04_integration_candidate_report(report: Mapping[str, Any]) -> list[str]:
    """Validate S2PLT04 integration-candidate precheck reports."""

    errors: list[str] = []
    if report.get("model_id") != S2PLT04_INTEGRATION_CANDIDATE_MODEL_ID:
        errors.append("S2PLT04 report model_id is invalid")
    if report.get("schema_version") != S2PLT04_SCHEMA_VERSION:
        errors.append("S2PLT04 report schema_version must be 1")
    if report.get("task_id") != S2PLT04_TASK_ID:
        errors.append("S2PLT04 report task_id is invalid")
    if report.get("acceptance_id") != S2PLT04_ACCEPTANCE_ID:
        errors.append("S2PLT04 report acceptance_id is invalid")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PLT04 report status must be pass or blocked")
    if report.get("production_acceptance_claimed") is not False:
        errors.append("S2PLT04 precheck must not claim production acceptance")
    if report.get("inherited_p0_p1_closed") is not False:
        errors.append("S2PLT04 precheck must not close inherited P0/P1")
    for flag in S2PLT04_FORBIDDEN_FLAGS:
        if report.get(flag) is not False:
            errors.append(f"{flag} must be false")

    dependencies = _mapping(report.get("dependencies"))
    for task_id in S2PLT04_REQUIRED_DEPENDENCIES:
        if task_id not in dependencies.get("required_dependencies", []):
            errors.append(f"dependencies.required_dependencies must include {task_id}")
    evidence = _mapping(report.get("evidence"))
    for item in S2PLT04_REQUIRED_EVIDENCE:
        if item not in evidence.get("required_evidence", []):
            errors.append(f"evidence.required_evidence must include {item}")
    s2pmt07 = _mapping(report.get("s2pmt07_precheck"))
    s2pmt07_errors = validate_s2pmt07_precheck_report(s2pmt07)
    if s2pmt07_errors:
        errors.append("S2PLT04 embedded S2PMT07 precheck is invalid")
    if report.get("status") == "pass":
        gates = _mapping(report.get("gates"))
        if not all(gates.values()):
            errors.append("passing S2PLT04 report requires every gate true")
        if report.get("blocking_reasons"):
            errors.append("passing S2PLT04 report must not have blocking reasons")
    else:
        for reason in S2PLT04_BLOCKING_REASONS:
            if reason not in report.get("blocking_reasons", []):
                errors.append(f"blocked S2PLT04 precheck must include {reason}")
    expected_hash = _stable_hash({key: value for key, value in report.items() if key != "candidate_hash"})
    if report.get("candidate_hash") != expected_hash:
        errors.append("S2PLT04 candidate_hash does not match report content")
    return errors


def build_dependency_state() -> dict[str, Any]:
    """Build the current dependency state from authoritative governance facts."""

    completed = {
        "S2PMT01": "completed_local_validation",
        "S2PMT02": "completed_local_validation",
        "S2PMT03": "completed_local_validation",
        "S2PMT04": "completed_local_validation",
        "S2PMT05": "completed_local_validation",
        "S2PMT06": "completed_local_validation",
    }
    missing = [task_id for task_id in S2PMT07_REQUIRED_DEPENDENCIES if task_id not in completed]
    return {
        "status": "blocked",
        "required_dependencies": list(S2PMT07_REQUIRED_DEPENDENCIES),
        "completed_dependencies": completed,
        "missing_dependencies": missing,
        "s2plt04_status": "missing_authoritative_completion_evidence",
    }


def build_audit_blocker_state(
    *,
    inherited_p0: int = S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS,
    inherited_p1: int = S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS,
) -> dict[str, Any]:
    """Build the inherited V7.1 P0/P1 blocker state."""

    checks = {
        "P0_zero": inherited_p0 == 0,
        "P1_zero": inherited_p1 == 0,
    }
    return {
        "status": "pass" if all(checks.values()) else "blocked",
        "required_zero_severities": list(S2PMT07_REQUIRED_ZERO_FINDING_SEVERITIES),
        "inherited_v7_1_open_p0_findings": inherited_p0,
        "inherited_v7_1_open_p1_findings": inherited_p1,
        "checks": checks,
    }


def build_reviewer_independence_state(*, reviewer_involved_in_s2pmt01_t06: bool = True) -> dict[str, Any]:
    """Build reviewer independence state without self-certifying final review."""

    independent = not reviewer_involved_in_s2pmt01_t06
    return {
        "status": "pass" if independent else "blocked",
        "requirement": S2PMT07_REQUIRED_REVIEWER_INDEPENDENCE,
        "reviewer_involved_in_s2pmt01_t06": reviewer_involved_in_s2pmt01_t06,
        "independent_reviewer_proven": independent,
    }


def build_evidence_bundle_state() -> dict[str, Any]:
    """Build the required evidence bundle state."""

    available = {
        "FINAL_ACCEPTANCE_BUNDLE/": False,
        "HANDOFF/00_下一Agent先读.md": False,
        "independent_review_signoff.yaml": False,
    }
    missing = [item for item, present in available.items() if not present]
    return {
        "status": "blocked",
        "required_evidence": list(S2PMT07_REQUIRED_EVIDENCE),
        "available_evidence": available,
        "missing_evidence": missing,
    }


def build_test_gate_state() -> dict[str, Any]:
    """Build required S2PMT07 command coverage without pretending final execution."""

    return {
        "status": "blocked",
        "required_test_commands": list(S2PMT07_REQUIRED_TEST_COMMANDS),
        "executed_as_final_reviewer": False,
        "full_pytest_executed_by_independent_reviewer": False,
        "acceptance_bundle_zero_p0_p1_verified": False,
    }


def build_s2pmt07_precheck_report(*, generated_at: str) -> dict[str, Any]:
    """Build a deterministic fail-closed S2PMT07 precheck report."""

    dependencies = build_dependency_state()
    audit_blockers = build_audit_blocker_state()
    reviewer = build_reviewer_independence_state()
    evidence = build_evidence_bundle_state()
    tests = build_test_gate_state()
    gates = {
        "reviewer_independence": reviewer["status"] == "pass",
        "p0_zero": audit_blockers["checks"]["P0_zero"],
        "p1_zero": audit_blockers["checks"]["P1_zero"],
        "s2pmt01_t06_completed": all(task_id in dependencies["completed_dependencies"] for task_id in S2PMT07_REQUIRED_DEPENDENCIES[:6]),
        "s2plt04_completed": "S2PLT04" in dependencies["completed_dependencies"],
        "final_acceptance_bundle_present": evidence["available_evidence"]["FINAL_ACCEPTANCE_BUNDLE/"],
        "independent_review_signoff_present": evidence["available_evidence"]["independent_review_signoff.yaml"],
        "required_final_commands_executed": tests["executed_as_final_reviewer"],
        "no_production_side_effect": True,
    }
    blocking_reasons = []
    if not gates["reviewer_independence"]:
        blocking_reasons.append("reviewer_independence_not_proven")
    if not gates["p0_zero"]:
        blocking_reasons.append("inherited_v7_1_p0_findings_open")
    if not gates["p1_zero"]:
        blocking_reasons.append("inherited_v7_1_p1_findings_open")
    if not gates["s2plt04_completed"]:
        blocking_reasons.append("s2plt04_not_completed")
    if not gates["final_acceptance_bundle_present"]:
        blocking_reasons.append("final_acceptance_bundle_missing")
    if not gates["independent_review_signoff_present"]:
        blocking_reasons.append("independent_review_signoff_missing")
    status = "pass" if not blocking_reasons and all(gates.values()) else "blocked"
    report = {
        "model_id": S2PMT07_FINAL_GATE_MODEL_ID,
        "schema_version": S2PMT07_SCHEMA_VERSION,
        "task_id": S2PMT07_TASK_ID,
        "acceptance_id": S2PMT07_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": status,
        "blocking_reasons": blocking_reasons,
        "scope": "fail_closed_final_gate_precheck_only",
        "gates": gates,
        "dependencies": dependencies,
        "audit_blockers": audit_blockers,
        "reviewer_independence": reviewer,
        "evidence_bundle": evidence,
        "test_gates": tests,
        "production_acceptance_claimed": False,
        "inherited_p0_p1_closed": False,
        "report_hash": "",
        "integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "current_pointer_changed": False,
        "v7_1_baseline_changed": False,
        "v7_2_contract_files_changed": False,
    }
    report["report_hash"] = _stable_hash({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_s2pmt07_precheck_report(report: Mapping[str, Any]) -> list[str]:
    """Validate S2PMT07 fail-closed precheck reports."""

    errors: list[str] = []
    if report.get("model_id") != S2PMT07_FINAL_GATE_MODEL_ID:
        errors.append("S2PMT07 report model_id is invalid")
    if report.get("schema_version") != S2PMT07_SCHEMA_VERSION:
        errors.append("S2PMT07 report schema_version must be 1")
    if report.get("task_id") != S2PMT07_TASK_ID:
        errors.append("S2PMT07 report task_id is invalid")
    if report.get("acceptance_id") != S2PMT07_ACCEPTANCE_ID:
        errors.append("S2PMT07 report acceptance_id is invalid")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PMT07 report status must be pass or blocked")
    if report.get("production_acceptance_claimed") is not False:
        errors.append("S2PMT07 precheck must not claim production acceptance")
    if report.get("inherited_p0_p1_closed") is not False:
        errors.append("S2PMT07 precheck must not close inherited P0/P1")
    for flag in S2PMT07_FORBIDDEN_PASS_FLAGS:
        if report.get(flag) is not False:
            errors.append(f"{flag} must be false")
    dependencies = _mapping(report.get("dependencies"))
    for task_id in S2PMT07_REQUIRED_DEPENDENCIES:
        if task_id not in dependencies.get("required_dependencies", []):
            errors.append(f"dependencies.required_dependencies must include {task_id}")
    evidence = _mapping(report.get("evidence_bundle"))
    for item in S2PMT07_REQUIRED_EVIDENCE:
        if item not in evidence.get("required_evidence", []):
            errors.append(f"evidence_bundle.required_evidence must include {item}")
    tests = _mapping(report.get("test_gates"))
    for command in S2PMT07_REQUIRED_TEST_COMMANDS:
        if command not in tests.get("required_test_commands", []):
            errors.append(f"test_gates.required_test_commands must include {command}")
    if report.get("status") == "pass":
        gates = _mapping(report.get("gates"))
        if not all(gates.values()):
            errors.append("passing S2PMT07 report requires every gate true")
        if report.get("blocking_reasons"):
            errors.append("passing S2PMT07 report must not have blocking reasons")
    else:
        for reason in S2PMT07_BLOCKING_REASONS[:4]:
            if reason not in report.get("blocking_reasons", []):
                errors.append(f"blocked S2PMT07 precheck must include {reason}")
    return errors


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _stable_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
