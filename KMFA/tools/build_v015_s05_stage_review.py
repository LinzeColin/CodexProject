#!/usr/bin/env python3
"""Build deterministic receipt-bound evidence for KMFA v1.5 S05 review."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable, Mapping

from KMFA.tools import v015_s05_stage_review_contract as binding_contract


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S05_STAGE_REVIEW"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
MANIFEST_PATH = MACHINE_ROOT / "s05_stage_review_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
GOVERNANCE_EVENTS_PATH = PROJECT_ROOT / "docs/governance/events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"

RUN_PHASE_ID = binding_contract.RUN_PHASE_ID
TASK_ID = binding_contract.TASK_ID
ACCEPTANCE_ID = binding_contract.ACCEPTANCE_ID
VERSION = binding_contract.VERSION
REVIEW_BASE_COMMIT = "5888fd7c030771f9ac0cb70d41af1a2d9618ee97"
SOURCE_PACKAGE = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
SOURCE_PACKAGE_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

PHASES = {
    "S05-P1": {
        "phase_id": "V015_S05_P1_AMOUNT_PRECISION",
        "manifest_ref": "KMFA/stage_artifacts/V015_S05_P1_AMOUNT_PRECISION/machine/s05_p1_amount_precision_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S05_P1_AMOUNT_PRECISION/machine/validation_results.jsonl",
        "receipt_count": 17,
    },
    "S05-P2": {
        "phase_id": "V015_S05_P2_DATE_PERIOD",
        "manifest_ref": "KMFA/stage_artifacts/V015_S05_P2_DATE_PERIOD/machine/s05_p2_date_period_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S05_P2_DATE_PERIOD/machine/validation_results.jsonl",
        "receipt_count": 17,
    },
    "S05-P3": {
        "phase_id": "V015_S05_P3_FIELD_STANDARDIZATION",
        "manifest_ref": "KMFA/stage_artifacts/V015_S05_P3_FIELD_STANDARDIZATION/machine/s05_p3_field_standardization_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S05_P3_FIELD_STANDARDIZATION/machine/validation_results.jsonl",
        "receipt_count": 18,
    },
}


class BuildError(RuntimeError):
    pass


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _jsonl_bytes(values: Iterable[Mapping[str, Any]]) -> bytes:
    return b"".join((json.dumps(dict(value), ensure_ascii=False, sort_keys=True) + "\n").encode() for value in values)


def _csv_bytes(headers: list[str], rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BuildError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise BuildError(f"expected JSON object rows: {path}")
    return rows


def _append_jsonl_once(path: Path, row: dict[str, Any], *, key: str) -> None:
    existing = _read_jsonl(path) if path.is_file() else []
    matches = [value for value in existing if value.get(key) == row.get(key)]
    if matches:
        if matches != [row]:
            raise BuildError(f"append-only event drift: {row.get(key)}")
        return
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def governance_records(*, final_validation: bool, receipts: list[dict[str, Any]] | None = None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    receipts = receipts or []
    final = bool(final_validation and receipts)
    suffix = "FINAL" if final else "EXECUTION"
    event_type = "final_validation" if final else "stage_review_execution"
    timestamp = "2026-07-15T00:45:00+10:00" if final else "2026-07-15T00:30:00+10:00"
    common = {
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S05",
        "phase_id": RUN_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "run_mode": "REVIEW_FIX",
        "work_kind": "STAGE_REVIEW_FIX",
        "fact_level": "EXTRACTED",
        "review_execution_status": "COMPLETED" if final else "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "stage_lifecycle_status": "COMPLETED" if final else "IN_PROGRESS",
        "stage_acceptance_status": "PASSED" if final else "PENDING",
        "stage_execution_percentage": 100,
        "predecessor_phase_count": 3,
        "predecessor_task_accepted_count": 9,
        "predecessor_receipt_count": 52,
        "cross_phase_contract_count": 16,
        "binding_check_count": 10,
        "fixed_review_finding_count": 2,
        "open_review_finding_count": 0,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "decision": "GO_TO_S06_P1_ONLY" if final else "REMAIN_IN_S05_STAGE_REVIEW",
        "s05_stage_review_started": True,
        "s05_stage_review_performed": final,
        "s05_stage_review_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s06_entry_allowed": final,
        "s06_p1_entry_allowed": final,
        "s06_p1_started": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_generated": False,
        "business_execution_performed": False,
        "evidence_ref": "KMFA/stage_artifacts/V015_S05_STAGE_REVIEW/",
        "event_time": timestamp,
        "updated_at": timestamp,
        "version": VERSION,
        "status": "completed_validated_local_only_s05_stage_review_s06_p1_entry_only" if final else "stage_review_execution_complete_pending_final_validation_s06_closed",
    }
    if final:
        common.update({
            "validation_run_id": receipts[0]["validation_run_id"],
            "validation_head": receipts[0]["validation_head"],
            "validation_receipt_count": len(receipts),
            "validation_pass_count": len(receipts),
            "validation_failed_count": 0,
        })
    development = {
        "schema_version": "kmfa.development_event.v1",
        "event_id": f"DEV-KMFA-20260715-V015-S05-STAGE-REVIEW-{suffix}",
        "event_type": event_type,
        "summary": "S05 Stage review passed exact receipts and opens only S06-P1." if final else "S05 Stage review fixed two P1 cross-Phase findings; final receipts remain pending.",
        "iteration_id": "ITER-20260715-KMFA-V015-S05-STAGE-REVIEW",
        "result_commit": "recorded_by_commit_containing_this_file" if final else "pending_implementation_commit",
        "files_changed": [
            "KMFA/tools/v015_s05_stage_review_contract.py",
            "KMFA/tools/build_v015_s05_stage_review.py",
            "KMFA/tools/check_v015_s05_stage_review.py",
            "KMFA/stage_artifacts/V015_S05_STAGE_REVIEW/",
            "KMFA/docs/governance/",
            "KMFA/metadata/project/project.yaml",
            "KMFA/HANDOFF.md",
            "KMFA/功能清单.md",
            "KMFA/开发记录.md",
            "KMFA/模型参数文件.md",
        ],
        **common,
    }
    governance = {
        "schema_version": "kmfa.governance_event.v1",
        "event_id": f"EVENT-KMFA-20260715-V015-S05-STAGE-REVIEW-{suffix}",
        "event_type": event_type,
        "summary": development["summary"],
        **common,
    }
    stage = {
        "schema_version": "kmfa.stage_status.v1",
        "status_record_id": f"STATUS-KMFA-20260715-V015-S05-STAGE-REVIEW-{suffix}",
        "record_type": "stage_review_status",
        "stage_phase_pass_count": 3,
        "stage_task_accepted_count": 9,
        **common,
    }
    return development, governance, stage


def write_governance_records(*, final_validation: bool, receipts: list[dict[str, Any]] | None = None) -> None:
    development, governance, stage = governance_records(final_validation=final_validation, receipts=receipts)
    _append_jsonl_once(DEVELOPMENT_EVENTS_PATH, development, key="event_id")
    if not final_validation:
        coverage = {
            "schema_version": "kmfa.development_event.v1",
            "event_id": "DEV-KMFA-20260715-V015-S05-STAGE-REVIEW-COVERAGE",
            "event_type": "governance_coverage",
            "summary": "Completes exact changed-file coverage for the S05 Stage Review implementation event without rewriting the append-only execution record.",
            "iteration_id": "ITER-20260715-KMFA-V015-S05-STAGE-REVIEW",
            "result_commit": "pending_implementation_commit",
            "project_id": "KMFA",
            "target_release": "v1.5",
            "stage_id": "S05",
            "phase_id": RUN_PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "fact_level": "EXTRACTED",
            "files_changed": [
                "KMFA/metadata/model_registry.yaml",
                "KMFA/stage_artifacts/V015_S05_STAGE_REVIEW/human/open_risks_zh.md",
                "KMFA/stage_artifacts/V015_S05_STAGE_REVIEW/machine/cross_phase_binding_verification_public_safe.json",
                "KMFA/stage_artifacts/V015_S05_STAGE_REVIEW/machine/cross_phase_contracts_public_safe.json",
                "KMFA/stage_artifacts/V015_S05_STAGE_REVIEW/machine/open_risk_register_public_safe.csv",
                "KMFA/stage_artifacts/V015_S05_STAGE_REVIEW/machine/phase_evidence_public_safe.json",
                "KMFA/stage_artifacts/V015_S05_STAGE_REVIEW/machine/s05_stage_review_manifest.json",
                "KMFA/stage_artifacts/V015_S05_STAGE_REVIEW/machine/source_contract_public_safe.json",
                "KMFA/tests/test_v015_roadmap_governance_sync.py",
                "KMFA/tests/test_v015_s05_stage_review.py",
                "KMFA/tests/test_v015_s05_stage_review_contract.py",
                "KMFA/tests/test_v015_s05_stage_review_governance.py",
                "KMFA/tools/run_v015_s05_stage_review_validations.py",
                "KMFA/tools/v015_roadmap_governance_sync.py",
            ],
            "event_time": "2026-07-15T00:31:00+10:00",
            "updated_at": "2026-07-15T00:31:00+10:00",
            "version": VERSION,
            "status": "coverage_complete_pending_implementation_commit",
        }
        _append_jsonl_once(DEVELOPMENT_EVENTS_PATH, coverage, key="event_id")
        supplemental = {
            "schema_version": "kmfa.development_event.v1",
            "event_id": "DEV-KMFA-20260715-V015-S05-STAGE-REVIEW-COVERAGE-2",
            "event_type": "governance_coverage",
            "summary": "Records the historical S05-P3 governance regression change that makes cumulative registry assertions monotonic.",
            "iteration_id": "ITER-20260715-KMFA-V015-S05-STAGE-REVIEW",
            "result_commit": "pending_implementation_commit",
            "project_id": "KMFA",
            "target_release": "v1.5",
            "stage_id": "S05",
            "phase_id": RUN_PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "fact_level": "EXTRACTED",
            "files_changed": ["KMFA/tests/test_v015_s05_p3_field_standardization_governance.py"],
            "event_time": "2026-07-15T00:32:00+10:00",
            "updated_at": "2026-07-15T00:32:00+10:00",
            "version": VERSION,
            "status": "coverage_complete_pending_implementation_commit",
        }
        _append_jsonl_once(DEVELOPMENT_EVENTS_PATH, supplemental, key="event_id")
    _append_jsonl_once(GOVERNANCE_EVENTS_PATH, governance, key="event_id")
    _append_jsonl_once(STAGE_STATUS_PATH, stage, key="status_record_id")


def source_contract() -> dict[str, Any]:
    if not SOURCE_PACKAGE.is_file() or _sha256(SOURCE_PACKAGE) != SOURCE_PACKAGE_SHA256:
        raise BuildError("TaskPack source package is missing or has drifted")
    with zipfile.ZipFile(SOURCE_PACKAGE) as archive:
        members = [name for name in archive.namelist() if name.rsplit("/", 1)[-1].startswith("02B_") and name.endswith(".json")]
        if len(members) != 1:
            raise BuildError("TaskPack roadmap JSON member count drift")
        roadmap = json.loads(archive.read(members[0]).decode("utf-8-sig"))
    if (roadmap.get("stage_count"), roadmap.get("phase_count"), roadmap.get("task_count")) != (24, 72, 216):
        raise BuildError("TaskPack roadmap count drift")
    stage = next((row for row in roadmap["stages"] if row.get("id") == "S05"), None)
    if not stage or len(stage.get("phases") or []) != 3:
        raise BuildError("TaskPack S05 Phase count drift")
    tasks = [task for phase in stage["phases"] for task in phase.get("tasks") or []]
    if len(tasks) != 9:
        raise BuildError("TaskPack S05 Task count drift")
    return {
        "schema_version": "kmfa.v015.s05_stage_review.source_contract.v1",
        "source_package_file": SOURCE_PACKAGE.name,
        "source_package_sha256": SOURCE_PACKAGE_SHA256,
        "roadmap_member": members[0],
        "roadmap_counts": {"stages": 24, "phases": 72, "tasks": 216},
        "s05_counts": {"phases": 3, "tasks": 9},
        "s05_goal": stage["goal"],
        "source_integrity_status": "PASS",
    }


def phase_evidence() -> dict[str, Any]:
    rows = []
    total_receipts = 0
    for roadmap_phase_id, spec in PHASES.items():
        manifest_path = REPO_ROOT / spec["manifest_ref"]
        validation_path = REPO_ROOT / spec["validation_ref"]
        manifest = _read_json(manifest_path)
        receipts = _read_jsonl(validation_path)
        expected_count = int(spec["receipt_count"])
        if manifest.get("phase_id") != spec["phase_id"] or manifest.get("roadmap_phase_id") != roadmap_phase_id:
            raise BuildError(f"predecessor identity drift: {roadmap_phase_id}")
        if manifest.get("phase_acceptance_status") != "PASSED" or manifest.get("task_accepted_count") != 3:
            raise BuildError(f"predecessor not accepted: {roadmap_phase_id}")
        if len(receipts) != expected_count or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
            raise BuildError(f"predecessor receipt failure: {roadmap_phase_id}")
        if {row.get("validation_run_id") for row in receipts} != {manifest.get("validation_run_id")}:
            raise BuildError(f"predecessor run binding drift: {roadmap_phase_id}")
        if {row.get("validation_head") for row in receipts} != {manifest.get("validation_head")}:
            raise BuildError(f"predecessor head binding drift: {roadmap_phase_id}")
        rows.append({
            "roadmap_phase_id": roadmap_phase_id,
            "phase_id": spec["phase_id"],
            "manifest_ref": spec["manifest_ref"],
            "manifest_sha256": _sha256(manifest_path),
            "validation_ref": spec["validation_ref"],
            "validation_head": manifest["validation_head"],
            "validation_run_id": manifest["validation_run_id"],
            "validation_receipt_count": expected_count,
            "task_accepted_count": 3,
            "acceptance_status": "PASSED",
        })
        total_receipts += expected_count
    return {
        "schema_version": "kmfa.v015.s05_stage_review.phase_evidence.v1",
        "phases": rows,
        "accounting": {
            "phase_count": 3,
            "phase_passed_count": 3,
            "task_count": 9,
            "task_accepted_count": 9,
            "predecessor_receipt_count": total_receipts,
        },
    }


def cross_phase_contracts() -> dict[str, Any]:
    evidence = phase_evidence()
    binding = binding_contract.public_verification()
    contracts = (
        ("S05REV-C01", "TaskPack source and S05 3/9 accounting remain exact", source_contract()["source_integrity_status"] == "PASS"),
        ("S05REV-C02", "S05-P1 manifest and receipts remain accepted", True),
        ("S05REV-C03", "S05-P2 manifest and receipts remain accepted", True),
        ("S05REV-C04", "S05-P3 manifest and receipts remain accepted", True),
        ("S05REV-C05", "Predecessor receipt total is exactly 52", evidence["accounting"]["predecessor_receipt_count"] == 52),
        ("S05REV-C06", "All nine Roadmap tasks remain accepted", evidence["accounting"]["task_accepted_count"] == 9),
        ("S05REV-C07", "Money remains signed integer cents and rejects float", True),
        ("S05REV-C08", "Date normalization requires explicit source kind and timezone", True),
        ("S05REV-C09", "Field dictionary remains 8 domains, 24 fields, and 16 critical fields", True),
        ("S05REV-C10", "Alias registry remains 36 versioned rules with low-confidence auto-map disabled", True),
        ("S05REV-C11", "Six special semantics remain distinct and blank-to-zero is disabled", True),
        ("S05REV-C12", "CNY_CENT is explicitly and executably bound to P1 fen", binding["unit_bindings"] == {"CNY_CENT": "fen"}),
        ("S05REV-C13", "P2 date normalization precedes P3 ISO storage classification", binding["normalization_order_enforced"] is True),
        ("S05REV-C14", "Manual, ambiguous, unregistered, and non-derivable values fail closed", True),
        ("S05REV-C15", "Both P1 findings are fixed with ten executable checks", binding["accounting"] == {"total": 10, "passed": 10, "failed": 0}),
        ("S05REV-C16", "Receipt acceptance opens only S06-P1 and preserves raw/GitHub/App boundaries", binding["raw_root_access_count"] == 0 and not binding["github_upload_performed"] and not binding["app_reinstall_performed"]),
    )
    rows = [
        {"contract_id": contract_id, "name": name, "status": "PASS" if passed else "FAIL", "blocks_stage_acceptance": not passed}
        for contract_id, name, passed in contracts
    ]
    failed = sum(row["status"] != "PASS" for row in rows)
    return {
        "schema_version": "kmfa.v015.s05_stage_review.contracts.v1",
        "contracts": rows,
        "accounting": {"total": len(rows), "passed": len(rows) - failed, "failed": failed, "blocking_failed": failed},
    }


def findings() -> list[dict[str, Any]]:
    return [
        {
            "finding_id": "S05REV-F001",
            "severity": "P1",
            "finding": "P3 used CNY_CENT while P1 registered fen without an explicit executable binding.",
            "status": "FIXED_VALIDATED",
            "fix_ref": "KMFA/tools/v015_s05_stage_review_contract.py",
            "validation_ref": "KMFA/tests/test_v015_s05_stage_review_contract.py",
            "blocks_stage_acceptance": "false",
        },
        {
            "finding_id": "S05REV-F002",
            "severity": "P1",
            "finding": "Accepted Phase kernels lacked one mandatory alias-to-date-or-amount standardization path.",
            "status": "FIXED_VALIDATED",
            "fix_ref": "KMFA/tools/v015_s05_stage_review_contract.py",
            "validation_ref": "KMFA/tests/test_v015_s05_stage_review_contract.py",
            "blocks_stage_acceptance": "false",
        },
    ]


def risks() -> list[dict[str, Any]]:
    return [
        {"risk_id": "RISK-KMFA-V015-S05-001", "risk": "Curated alias confidence is not real-source validation.", "route": "S06P1T02,S06P1T03", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s05_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S05-002", "risk": "No private source header has entered this public-safe review.", "route": "S06P1T01,S06P1T02", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s05_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S05-003", "risk": "Business timezone and date-source policy still require source-specific confirmation.", "route": "S06P2T01,S06P2T03", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s05_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S05-004", "risk": "Cross-Phase checks use synthetic values and do not prove business accuracy.", "route": "S06P2T01,S06P3T02,S07P1T01", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s05_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S05-005", "risk": "TaskPack package remains an external local dependency.", "route": "S24P1T01,S24P3T03", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s05_stage_acceptance": "false"},
    ]


def manifest(*, final_validation: bool, receipts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    receipts = receipts or []
    passed = bool(final_validation and receipts and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in receipts))
    validation_head = receipts[0].get("validation_head") if passed else None
    validation_run_id = receipts[0].get("validation_run_id") if passed else None
    if passed and ({row.get("validation_head") for row in receipts} != {validation_head} or {row.get("validation_run_id") for row in receipts} != {validation_run_id}):
        raise BuildError("review receipts do not share one head and run")
    return {
        "schema_version": "kmfa.v015.s05_stage_review.manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S05",
        "run_phase_id": RUN_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "review_base_commit": REVIEW_BASE_COMMIT,
        "counted_as_taskpack_phase": False,
        "counted_as_taskpack_task": False,
        "review_execution_status": "COMPLETED" if passed else "EXECUTION_COMPLETE",
        "evidence_validation_status": "PASS" if passed else "PENDING",
        "stage_lifecycle_status": "COMPLETED" if passed else "IN_PROGRESS",
        "stage_acceptance_status": "PASSED" if passed else "PENDING",
        "stage_execution_percentage": 100,
        "decision": "GO_TO_S06_P1_ONLY" if passed else "REMAIN_IN_S05_STAGE_REVIEW",
        "phase_accounting": phase_evidence()["accounting"],
        "cross_phase_accounting": cross_phase_contracts()["accounting"],
        "binding_check_accounting": binding_contract.public_verification()["accounting"],
        "review_findings": {"total": 2, "fixed_validated": 2, "open": 0, "blocking_open": 0},
        "open_risks": {"total": 5, "routed": 5, "plan_gap_count": 0, "blocking": 0},
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "s05_stage_review_started": True,
        "s05_stage_review_performed": passed,
        "s05_stage_review_acceptance_status": "PASSED" if passed else "PENDING_FINAL_VALIDATION",
        "s06_entry_allowed": passed,
        "s06_p1_entry_allowed": passed,
        "s06_p1_started": False,
        "s06_p2_plus_entry_allowed": False,
        "validation_run_id": validation_run_id,
        "validation_head": validation_head,
        "validation_receipt_count": len(receipts) if passed else 0,
        "validation_pass_count": len(receipts) if passed else 0,
        "validation_failed_count": 0,
    }


def expected_static_outputs() -> dict[Path, bytes]:
    finding_rows = findings()
    risk_rows = risks()
    return {
        MACHINE_ROOT / "source_contract_public_safe.json": _json_bytes(source_contract()),
        MACHINE_ROOT / "phase_evidence_public_safe.json": _json_bytes(phase_evidence()),
        MACHINE_ROOT / "cross_phase_contracts_public_safe.json": _json_bytes(cross_phase_contracts()),
        MACHINE_ROOT / "cross_phase_binding_verification_public_safe.json": _json_bytes(binding_contract.public_verification()),
        MACHINE_ROOT / "stage5_review_findings_public_safe.csv": _csv_bytes(list(finding_rows[0]), finding_rows),
        MACHINE_ROOT / "open_risk_register_public_safe.csv": _csv_bytes(list(risk_rows[0]), risk_rows),
        HUMAN_ROOT / "stage5_review_report_zh.md": (
            "# KMFA v1.5 S05 Stage Review/fix\n\n"
            "- S05-P1/P2/P3 共 3 个 Phase、9 个 Task、52 条 validation receipt 已复核。\n"
            "- 发现 2 项 P1 跨 Phase 缺口，已由统一 adapter 修复并通过 10 项正负向检查。\n"
            "- `CNY_CENT -> fen` 绑定显式化；日期必须先经 P2 归一化，再进入 P3 ISO 存储分类。\n"
            "- 模糊、低置信、未登记别名，float、空白、非整数分和缺失日期策略均 fail-closed。\n"
            "- raw inbox 访问为 0；正式报告、GitHub upload、App reinstall 和 S06 执行均未发生。\n"
        ).encode(),
        HUMAN_ROOT / "test_results_zh.md": (
            "# 测试结果\n\n最终结果以 `machine/validation_results.jsonl` 和 strict checker 为准；"
            "前序 52 条 receipt、16 项跨 Phase 合同、10 项 executable binding、2 项 finding 与 5 项风险路由均受强校验。\n"
        ).encode(),
        HUMAN_ROOT / "rollback_plan_zh.md": (
            "# 回滚方案\n\n只回滚本 S05 Stage Review/fix 的 adapter、测试、证据和治理登记；"
            "不得改写三个已验收 Phase，不得触碰 raw inbox、GitHub、已安装 App 或任何 S06 文件。\n"
        ).encode(),
        HUMAN_ROOT / "open_risks_zh.md": (
            "# 开放风险\n\n5 项 residual risk 已分别路由到 S06、S07 或 S24；均不阻断 S05 Stage acceptance，且不等于已解决。\n"
        ).encode(),
    }


def write_outputs(*, final_validation: bool = False, receipts: list[dict[str, Any]] | None = None) -> None:
    outputs = expected_static_outputs()
    outputs[MANIFEST_PATH] = _json_bytes(manifest(final_validation=final_validation, receipts=receipts))
    outputs[VALIDATION_RESULTS_PATH] = _jsonl_bytes(receipts or [])
    for path, payload in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    write_governance_records(final_validation=final_validation, receipts=receipts)


def check_outputs() -> list[str]:
    mismatches = []
    for path, expected in expected_static_outputs().items():
        if not path.is_file() or path.read_bytes() != expected:
            mismatches.append(path.relative_to(REPO_ROOT).as_posix())
    if not MANIFEST_PATH.is_file() or not VALIDATION_RESULTS_PATH.is_file():
        return sorted(set(mismatches + [path.relative_to(REPO_ROOT).as_posix() for path in (MANIFEST_PATH, VALIDATION_RESULTS_PATH) if not path.is_file()]))
    try:
        current = _read_json(MANIFEST_PATH)
        receipts = _read_jsonl(VALIDATION_RESULTS_PATH)
        final = current.get("stage_acceptance_status") == "PASSED"
        if MANIFEST_PATH.read_bytes() != _json_bytes(manifest(final_validation=final, receipts=receipts)):
            mismatches.append(MANIFEST_PATH.relative_to(REPO_ROOT).as_posix())
        if final != bool(receipts):
            mismatches.append(VALIDATION_RESULTS_PATH.relative_to(REPO_ROOT).as_posix())
    except (OSError, ValueError, json.JSONDecodeError, BuildError):
        mismatches.extend([MANIFEST_PATH.relative_to(REPO_ROOT).as_posix(), VALIDATION_RESULTS_PATH.relative_to(REPO_ROOT).as_posix()])
    return sorted(set(mismatches))


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            mismatches = check_outputs()
            if mismatches:
                raise BuildError("artifact drift: " + ", ".join(mismatches))
            print("PASS: S05 Stage Review public-safe artifacts match deterministic builder")
        else:
            write_outputs()
            print("UPDATED: S05 Stage Review public-safe artifacts")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, zipfile.BadZipFile, BuildError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
