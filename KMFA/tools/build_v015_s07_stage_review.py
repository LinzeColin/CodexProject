#!/usr/bin/env python3
"""Build deterministic receipt-bound evidence for KMFA v1.5 S07 review."""

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

from KMFA.tools import v015_s07_stage_review_contract as binding_contract


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S07_STAGE_REVIEW"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
MANIFEST_PATH = MACHINE_ROOT / "s07_stage_review_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
GOVERNANCE_EVENTS_PATH = PROJECT_ROOT / "docs/governance/events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"

RUN_PHASE_ID = binding_contract.RUN_PHASE_ID
TASK_ID = binding_contract.TASK_ID
ACCEPTANCE_ID = binding_contract.ACCEPTANCE_ID
VERSION = binding_contract.VERSION
REVIEW_BASE_COMMIT = "17e06e8817e8886eb051978ffbe12b60f9e364e8"
SOURCE_PACKAGE = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
SOURCE_PACKAGE_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

PHASES = {
    "S07-P1": {
        "phase_id": "V015_S07_P1_ZERO_DELTA_VALIDATOR",
        "manifest_ref": "KMFA/stage_artifacts/V015_S07_P1_ZERO_DELTA_VALIDATOR/machine/s07_p1_zero_delta_validator_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S07_P1_ZERO_DELTA_VALIDATOR/machine/validation_results.jsonl",
        "receipt_count": 18,
    },
    "S07-P2": {
        "phase_id": "V015_S07_P2_CONFLICT_CLASSIFICATION",
        "manifest_ref": "KMFA/stage_artifacts/V015_S07_P2_CONFLICT_CLASSIFICATION/machine/s07_p2_conflict_classification_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S07_P2_CONFLICT_CLASSIFICATION/machine/validation_results.jsonl",
        "receipt_count": 18,
    },
    "S07-P3": {
        "phase_id": "V015_S07_P3_RELEASE_GATE",
        "manifest_ref": "KMFA/stage_artifacts/V015_S07_P3_RELEASE_GATE/machine/s07_p3_release_gate_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S07_P3_RELEASE_GATE/machine/validation_results.jsonl",
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
    timestamp = "2026-07-15T10:20:00+10:00" if final else "2026-07-15T10:00:00+10:00"
    common = {
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S07",
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
        "predecessor_receipt_count": 54,
        "cross_phase_contract_count": 20,
        "binding_check_count": 16,
        "fixed_review_finding_count": 2,
        "open_review_finding_count": 0,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "decision": "GO_TO_S08_P1_ONLY" if final else "REMAIN_IN_S07_STAGE_REVIEW",
        "s07_stage_review_started": True,
        "s07_stage_review_performed": final,
        "s07_stage_review_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s08_entry_allowed": final,
        "s08_p1_entry_allowed": final,
        "s08_p1_started": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_generated": False,
        "business_execution_performed": False,
        "evidence_ref": "KMFA/stage_artifacts/V015_S07_STAGE_REVIEW/",
        "event_time": timestamp,
        "updated_at": timestamp,
        "version": VERSION,
        "status": "completed_validated_local_only_s07_stage_review_s08_p1_entry_only" if final else "stage_review_execution_complete_pending_final_validation_s08_closed",
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
        "event_id": f"DEV-KMFA-20260715-V015-S07-STAGE-REVIEW-{suffix}",
        "event_type": event_type,
        "summary": "S07 Stage review passed exact receipts and opens only S08-P1." if final else "S07 Stage review fixed two boundary findings; final receipts remain pending.",
        "iteration_id": "ITER-20260715-KMFA-V015-S07-STAGE-REVIEW",
        "result_commit": "recorded_by_commit_containing_this_file" if final else "pending_implementation_commit",
        "files_changed": [
            "KMFA/tools/v015_s07_stage_review_contract.py",
            "KMFA/tools/build_v015_s07_stage_review.py",
            "KMFA/tools/check_v015_s07_stage_review.py",
            "KMFA/stage_artifacts/V015_S07_STAGE_REVIEW/",
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
        "event_id": f"EVENT-KMFA-20260715-V015-S07-STAGE-REVIEW-{suffix}",
        "event_type": event_type,
        "summary": development["summary"],
        **common,
    }
    stage = {
        "schema_version": "kmfa.stage_status.v1",
        "status_record_id": f"STATUS-KMFA-20260715-V015-S07-STAGE-REVIEW-{suffix}",
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
            "event_id": "DEV-KMFA-20260715-V015-S07-STAGE-REVIEW-COVERAGE",
            "event_type": "governance_coverage",
            "summary": "Completes exact changed-file coverage for the S07 Stage Review implementation event without rewriting the append-only execution record.",
            "iteration_id": "ITER-20260715-KMFA-V015-S07-STAGE-REVIEW",
            "result_commit": "pending_implementation_commit",
            "project_id": "KMFA",
            "target_release": "v1.5",
            "stage_id": "S07",
            "phase_id": RUN_PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "fact_level": "EXTRACTED",
            "files_changed": [
                "KMFA/metadata/model_registry.yaml",
                "KMFA/stage_artifacts/V015_S07_STAGE_REVIEW/human/open_risks_zh.md",
                "KMFA/stage_artifacts/V015_S07_STAGE_REVIEW/machine/cross_phase_binding_verification_public_safe.json",
                "KMFA/stage_artifacts/V015_S07_STAGE_REVIEW/machine/cross_phase_contracts_public_safe.json",
                "KMFA/stage_artifacts/V015_S07_STAGE_REVIEW/machine/open_risk_register_public_safe.csv",
                "KMFA/stage_artifacts/V015_S07_STAGE_REVIEW/machine/phase_evidence_public_safe.json",
                "KMFA/stage_artifacts/V015_S07_STAGE_REVIEW/machine/s07_stage_review_manifest.json",
                "KMFA/stage_artifacts/V015_S07_STAGE_REVIEW/machine/source_contract_public_safe.json",
                "KMFA/tests/test_v015_roadmap_governance_sync.py",
                "KMFA/tests/test_v015_s07_stage_review.py",
                "KMFA/tests/test_v015_s07_stage_review_contract.py",
                "KMFA/tests/test_v015_s07_stage_review_governance.py",
                "KMFA/tools/run_v015_s07_stage_review_validations.py",
                "KMFA/tools/v015_roadmap_governance_sync.py",
                "KMFA/HANDOFF.md",
                "KMFA/docs/governance/project.yaml",
                "KMFA/metadata/project/project.yaml",
            ],
            "event_time": "2026-07-15T10:01:00+10:00",
            "updated_at": "2026-07-15T10:01:00+10:00",
            "version": VERSION,
            "status": "coverage_complete_pending_implementation_commit",
        }
        _append_jsonl_once(DEVELOPMENT_EVENTS_PATH, coverage, key="event_id")
        supplemental = {
            "schema_version": "kmfa.development_event.v1",
            "event_id": "DEV-KMFA-20260715-V015-S07-STAGE-REVIEW-COVERAGE-2",
            "event_type": "governance_coverage",
            "summary": "Records the S07 review checker and governance surfaces omitted from the primary coverage row.",
            "iteration_id": "ITER-20260715-KMFA-V015-S07-STAGE-REVIEW",
            "result_commit": "pending_implementation_commit",
            "project_id": "KMFA",
            "target_release": "v1.5",
            "stage_id": "S07",
            "phase_id": RUN_PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "fact_level": "EXTRACTED",
            "files_changed": [
                "KMFA/tools/check_v015_s07_stage_review.py",
                "KMFA/stage_artifacts/V015_S07_STAGE_REVIEW/machine/stage7_review_findings_public_safe.csv",
                "KMFA/stage_artifacts/V015_S07_STAGE_REVIEW/human/stage7_review_report_zh.md",
                "KMFA/stage_artifacts/V015_S07_STAGE_REVIEW/human/test_results_zh.md",
                "KMFA/stage_artifacts/V015_S07_STAGE_REVIEW/human/rollback_plan_zh.md",
            ],
            "event_time": "2026-07-15T10:02:00+10:00",
            "updated_at": "2026-07-15T10:02:00+10:00",
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
    stage = next((row for row in roadmap["stages"] if row.get("id") == "S07"), None)
    if not stage or len(stage.get("phases") or []) != 3:
        raise BuildError("TaskPack S07 Phase count drift")
    tasks = [task for phase in stage["phases"] for task in phase.get("tasks") or []]
    if len(tasks) != 9:
        raise BuildError("TaskPack S07 Task count drift")
    return {
        "schema_version": "kmfa.v015.s07_stage_review.source_contract.v1",
        "source_package_file": SOURCE_PACKAGE.name,
        "source_package_sha256": SOURCE_PACKAGE_SHA256,
        "roadmap_member": members[0],
        "roadmap_counts": {"stages": 24, "phases": 72, "tasks": 216},
        "s07_counts": {"phases": 3, "tasks": 9},
        "s07_goal": stage["goal"],
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
        receipt_run_ids = {row.get("validation_run_id") for row in receipts}
        receipt_heads = {row.get("validation_head") for row in receipts}
        if len(receipt_run_ids) != 1 or None in receipt_run_ids or len(receipt_heads) != 1 or None in receipt_heads:
            raise BuildError(f"predecessor receipts do not share one head/run: {roadmap_phase_id}")
        receipt_run_id = next(iter(receipt_run_ids))
        receipt_head = next(iter(receipt_heads))
        if manifest.get("validation_run_id") is not None and manifest.get("validation_run_id") != receipt_run_id:
            raise BuildError(f"predecessor run binding drift: {roadmap_phase_id}")
        if manifest.get("validation_head") is not None and manifest.get("validation_head") != receipt_head:
            raise BuildError(f"predecessor head binding drift: {roadmap_phase_id}")
        rows.append({
            "roadmap_phase_id": roadmap_phase_id,
            "phase_id": spec["phase_id"],
            "manifest_ref": spec["manifest_ref"],
            "manifest_sha256": _sha256(manifest_path),
            "validation_ref": spec["validation_ref"],
            "validation_head": receipt_head,
            "validation_run_id": receipt_run_id,
            "validation_receipt_count": expected_count,
            "task_accepted_count": 3,
            "acceptance_status": "PASSED",
        })
        total_receipts += expected_count
    return {
        "schema_version": "kmfa.v015.s07_stage_review.phase_evidence.v1",
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
    p1 = _read_json(REPO_ROOT / PHASES["S07-P1"]["manifest_ref"])
    p2 = _read_json(REPO_ROOT / PHASES["S07-P2"]["manifest_ref"])
    p3 = _read_json(REPO_ROOT / PHASES["S07-P3"]["manifest_ref"])
    privacy_keys = {
        "p1": (
            "private_project_identity_count_public",
            "private_money_value_count_public",
            "private_source_locator_count_public",
            "private_digest_count_public",
        ),
        "p2": (
            "private_identity_count_public",
            "private_value_count_public",
            "private_source_locator_count_public",
            "private_digest_count_public",
        ),
        "p3": (
            "private_identity_count_public",
            "private_money_value_count_public",
            "private_source_locator_count_public",
            "private_digest_count_public",
        ),
    }
    contracts = (
        ("S07REV-C01", "TaskPack source and S07 3/9 accounting remain exact", source_contract()["source_integrity_status"] == "PASS"),
        ("S07REV-C02", "S07-P1 manifest and 18 receipts remain accepted", evidence["phases"][0]["acceptance_status"] == "PASSED"),
        ("S07REV-C03", "S07-P2 manifest and 18 receipts remain accepted", evidence["phases"][1]["acceptance_status"] == "PASSED"),
        ("S07REV-C04", "S07-P3 manifest and 18 receipts remain accepted", evidence["phases"][2]["acceptance_status"] == "PASSED"),
        ("S07REV-C05", "Predecessor receipt total is exactly 54", evidence["accounting"]["predecessor_receipt_count"] == 54),
        ("S07REV-C06", "All nine Roadmap tasks remain accepted", evidence["accounting"]["task_accepted_count"] == 9),
        ("S07REV-C07", "P1 private golden scope is exact and zero-difference", p1["private_project_count"] == 8 and p1["private_accepted_field_count"] == 92 and p1["private_formula_fail_count"] == 0 and p1["private_zero_difference"] is True),
        ("S07REV-C08", "Open-item count is stable across all three phases", p1["open_unconfirmed_item_count"] == p2["private_open_unconfirmed_item_count"] == p3["private_open_unconfirmed_item_count"] == 128),
        ("S07REV-C09", "Conflict count is stable from classification to release gate", p2["private_conflict_candidate_count"] == p3["current_private_conflict_candidate_count"] == 6),
        ("S07REV-C10", "No private conflict source was auto-selected", p2["private_conflict_auto_selected_count"] == p3["current_private_conflict_auto_selected_count"] == 0),
        ("S07REV-C11", "Eight golden projects equal the eight selected historical regressions", p1["private_project_count"] == p3["private_historical_project_count"] == p3["private_selected_for_rerun_count"] == 8),
        ("S07REV-C12", "Zero-difference golden scope and 8/8 historical regression both pass", p1["private_zero_difference"] is True and p3["private_regression_pass_count"] == 8 and p3["private_regression_fail_count"] == 0),
        ("S07REV-C13", "Persistent same-source mismatch is classified as system error", p2["persistent_same_source_mismatch_is_system_error"] is True and p2["same_source_persistent_system_error_count"] == 1),
        ("S07REV-C14", "System problems are never assigned to the user", p2["system_problem_assigned_to_user_count"] == 0),
        ("S07REV-C15", "The UI exposes exactly three Chinese status labels and no technical abbreviation", p3["status_labels_zh"] == ["可内部使用", "需确认", "暂不可使用"] and p3["ui_technical_abbreviation_count"] == 0),
        ("S07REV-C16", "All four closure paths require successful closure", p3["closure_kind_count"] == p3["closure_success_count"] == 4),
        ("S07REV-C17", "Status-only and no-recalculation closure attempts are rejected", p3["status_only_closure_rejected"] is True and p3["missing_recalculation_rejected"] is True),
        ("S07REV-C18", "Current report remains unavailable and formal release stays closed", p3["current_report_display_label_zh"] == "暂不可使用" and p3["current_formal_report_release_allowed"] is False and p3["formal_report_generated"] is False),
        ("S07REV-C19", "All public projections remain aggregate-only and raw mutation stays zero", all(row[key] == 0 for row, keys in ((p1, privacy_keys["p1"]), (p2, privacy_keys["p2"]), (p3, privacy_keys["p3"])) for key in keys) and all(row["raw_root_access_count"] == 0 and row["raw_mutation_performed"] is False for row in (p1, p2, p3))),
        ("S07REV-C20", "Sixteen live checks pass and release boundaries stay closed", binding["accounting"] == {"total": 16, "passed": 16, "failed": 0} and all(not row[key] for row in (p1, p2, p3) for key in ("github_upload_performed", "app_reinstall_performed", "business_execution_performed")) and p3["s08_p1_entry_allowed"] is False),
    )
    rows = [
        {"contract_id": contract_id, "name": name, "status": "PASS" if passed else "FAIL", "blocks_stage_acceptance": not passed}
        for contract_id, name, passed in contracts
    ]
    failed = sum(row["status"] != "PASS" for row in rows)
    return {
        "schema_version": "kmfa.v015.s07_stage_review.contracts.v1",
        "contracts": rows,
        "accounting": {"total": len(rows), "passed": len(rows) - failed, "failed": failed, "blocking_failed": failed},
    }


def findings() -> list[dict[str, Any]]:
    return [
        {
            "finding_id": "S07REV-F001",
            "severity": "P2",
            "finding": "HANDOFF 首页仍指向旧的 S07-P2 状态，当前 S07-P3 交接被埋在历史段落中。",
            "status": "FIXED_VALIDATED",
            "fix_ref": "KMFA/HANDOFF.md",
            "validation_ref": "KMFA/tests/test_v015_s07_stage_review_governance.py",
            "blocks_stage_acceptance": "false",
        },
        {
            "finding_id": "S07REV-F002",
            "severity": "P2",
            "finding": "两份项目治理文件的 next_gate_id 仍是 S07-P3，未指向正在执行的 S07 整体复审。",
            "status": "FIXED_VALIDATED",
            "fix_ref": "KMFA/docs/governance/project.yaml;KMFA/metadata/project/project.yaml",
            "validation_ref": "KMFA/tools/check_v015_s07_stage_review.py",
            "blocks_stage_acceptance": "false",
        },
    ]


def risks() -> list[dict[str, Any]]:
    return [
        {"risk_id": "RISK-KMFA-V015-S07-001", "risk": "128 项仍缺少充分证据，当前报告不能使用。", "route": "S09P3T03_DIFFERENCE_CLOSURE", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s07_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S07-002", "risk": "6 项跨来源冲突仍需人工判断，禁止自动择源。", "route": "S09P3T03_DIFFERENCE_CLOSURE", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s07_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S07-003", "risk": "三种中文状态尚未进入最终 UI 集成验收。", "route": "S14P3T03_LANGUAGE_REVIEW", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s07_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S07-004", "risk": "本地回归通过不等于远端 CI 已实施同一门禁。", "route": "LATER_ENGINEERING_CI_GATE", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s07_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S07-005", "risk": "S08 的实体匹配工作尚未开始。", "route": "S08P1_ONLY_NEXT_RUN", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s07_stage_acceptance": "false"},
    ]


def manifest(*, final_validation: bool, receipts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    receipts = receipts or []
    passed = bool(final_validation and receipts and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in receipts))
    validation_head = receipts[0].get("validation_head") if passed else None
    validation_run_id = receipts[0].get("validation_run_id") if passed else None
    if passed and ({row.get("validation_head") for row in receipts} != {validation_head} or {row.get("validation_run_id") for row in receipts} != {validation_run_id}):
        raise BuildError("review receipts do not share one head and run")
    return {
        "schema_version": "kmfa.v015.s07_stage_review.manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S07",
        "run_phase_id": RUN_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "review_base_commit": REVIEW_BASE_COMMIT,
        "counted_as_taskpack_phase": False,
        "counted_as_taskpack_task": False,
        "review_execution_status": "COMPLETED" if passed else "EXECUTION_COMPLETE",
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if passed else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if passed else "PENDING",
        "stage_lifecycle_status": "COMPLETED" if passed else "IN_PROGRESS",
        "stage_acceptance_status": "PASSED" if passed else "PENDING",
        "stage_execution_percentage": 100,
        "decision": "GO_TO_S08_P1_ONLY" if passed else "REMAIN_IN_S07_STAGE_REVIEW",
        "phase_accounting": phase_evidence()["accounting"],
        "cross_phase_accounting": cross_phase_contracts()["accounting"],
        "binding_check_accounting": binding_contract.public_verification()["accounting"],
        "review_findings": {"total": 2, "fixed_validated": 2, "open": 0, "blocking_open": 0},
        "open_risks": {"total": 5, "routed": 5, "plan_gap_count": 0, "blocking": 0},
        "overall_accepted_phase_count": 19,
        "overall_taskpack_phase_count": 72,
        "current_private_open_unconfirmed_item_count": 128,
        "current_private_conflict_candidate_count": 6,
        "current_private_conflict_auto_selected_count": 0,
        "current_report_display_label_zh": "暂不可使用",
        "current_formal_report_release_allowed": False,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "s07_stage_review_started": True,
        "s07_stage_review_performed": passed,
        "s07_stage_review_acceptance_status": "PASSED" if passed else "PENDING_FINAL_VALIDATION",
        "s08_entry_allowed": passed,
        "s08_p1_entry_allowed": passed,
        "s08_p1_started": False,
        "s08_p2_plus_entry_allowed": False,
        "product_implementation_allowed": passed,
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
        MACHINE_ROOT / "stage7_review_findings_public_safe.csv": _csv_bytes(list(finding_rows[0]), finding_rows),
        MACHINE_ROOT / "open_risk_register_public_safe.csv": _csv_bytes(list(risk_rows[0]), risk_rows),
        HUMAN_ROOT / "stage7_review_report_zh.md": (
            "# KMFA v1.5 S07 整体复审\n\n"
            "- S07 三个阶段、9 项任务、54 条原始验证记录全部复核通过。\n"
            "- 20 项跨阶段一致性检查和 16 项实时检查全部通过。\n"
            "- 发现的 2 个记录问题已修复：首页交接回到当前状态，下一步入口不再指向旧阶段。\n"
            "- 8 个历史项目全部回归通过；系统问题不会被错误归责给用户。\n"
            "- 128 项待确认事项和 6 项冲突仍未关闭，因此当前报告仍为“暂不可使用”。\n"
            "- 本轮未读取或修改 raw inbox，未生成正式报告，未上传 GitHub，未重装 App，也未开始 S08。\n"
        ).encode(),
        HUMAN_ROOT / "test_results_zh.md": (
            "# 测试结果\n\n最终结果以 `machine/validation_results.jsonl` 和 strict checker 为准；"
            "前序 54 条验证记录、20 项跨阶段合同、16 项可执行检查、2 项已修复问题与 5 项风险路由均受强校验。\n"
        ).encode(),
        HUMAN_ROOT / "rollback_plan_zh.md": (
            "# 回滚方案\n\n只回滚本 S07 整体复审的工具、测试、证据和治理登记；"
            "不得改写三个已验收 Phase，不得触碰 raw inbox、GitHub、已安装 App 或任何 S08 文件。\n"
        ).encode(),
        HUMAN_ROOT / "open_risks_zh.md": (
            "# 开放风险\n\n5 项剩余风险已有明确后续路径；它们不阻断 S07 复审本身，"
            "但 128 项待确认事项与 6 项冲突仍会继续阻止正式报告发布。\n"
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
            print("PASS: S07 Stage Review public-safe artifacts match deterministic builder")
        else:
            write_outputs()
            print("UPDATED: S07 Stage Review public-safe artifacts")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, zipfile.BadZipFile, BuildError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
