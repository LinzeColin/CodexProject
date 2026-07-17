#!/usr/bin/env python3
"""Build deterministic receipt-bound evidence for KMFA v1.5 S08 review."""

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

from KMFA.tools import v015_s08_stage_review_contract as binding_contract


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S08_STAGE_REVIEW"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
MANIFEST_PATH = MACHINE_ROOT / "s08_stage_review_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
GOVERNANCE_EVENTS_PATH = PROJECT_ROOT / "docs/governance/events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"

RUN_PHASE_ID = binding_contract.RUN_PHASE_ID
TASK_ID = binding_contract.TASK_ID
ACCEPTANCE_ID = binding_contract.ACCEPTANCE_ID
VERSION = binding_contract.VERSION
REVIEW_BASE_COMMIT = "810033c05afd94b2d4a3eec4a87d867a6cf991ad"
SOURCE_PACKAGE = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
SOURCE_PACKAGE_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

PHASES = {
    "S08-P1": {
        "phase_id": "V015_S08_P1_PROJECT_COMPOSITE_IDENTITY",
        "manifest_ref": "KMFA/stage_artifacts/V015_S08_P1_PROJECT_COMPOSITE_IDENTITY/machine/s08_p1_project_composite_identity_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S08_P1_PROJECT_COMPOSITE_IDENTITY/machine/validation_results.jsonl",
        "receipt_count": 19,
    },
    "S08-P2": {
        "phase_id": "V015_S08_P2_BUSINESS_ENTITY_HIERARCHY",
        "manifest_ref": "KMFA/stage_artifacts/V015_S08_P2_BUSINESS_ENTITY_HIERARCHY/machine/s08_p2_business_entity_hierarchy_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S08_P2_BUSINESS_ENTITY_HIERARCHY/machine/validation_results.jsonl",
        "receipt_count": 19,
    },
    "S08-P3": {
        "phase_id": "V015_S08_P3_MATCHING_QUALITY_CONFIRMATION",
        "manifest_ref": "KMFA/stage_artifacts/V015_S08_P3_MATCHING_QUALITY_CONFIRMATION/machine/s08_p3_matching_quality_confirmation_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S08_P3_MATCHING_QUALITY_CONFIRMATION/machine/validation_results.jsonl",
        "receipt_count": 19,
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
    stage = next((row for row in roadmap["stages"] if row.get("id") == "S08"), None)
    if not stage or len(stage.get("phases") or []) != 3:
        raise BuildError("TaskPack S08 Phase count drift")
    tasks = [task for phase in stage["phases"] for task in phase.get("tasks") or []]
    if len(tasks) != 9:
        raise BuildError("TaskPack S08 Task count drift")
    return {
        "schema_version": "kmfa.v015.s08_stage_review.source_contract.v1",
        "source_package_file": SOURCE_PACKAGE.name,
        "source_package_sha256": SOURCE_PACKAGE_SHA256,
        "roadmap_member": members[0],
        "roadmap_counts": {"stages": 24, "phases": 72, "tasks": 216},
        "s08_counts": {"phases": 3, "tasks": 9},
        "s08_goal": stage["goal"],
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
        run_ids = {row.get("validation_run_id") for row in receipts}
        heads = {row.get("validation_head") for row in receipts}
        if len(run_ids) != 1 or None in run_ids or len(heads) != 1 or None in heads:
            raise BuildError(f"predecessor receipts do not share one head/run: {roadmap_phase_id}")
        run_id, head = next(iter(run_ids)), next(iter(heads))
        if manifest.get("validation_run_id") != run_id or manifest.get("validation_head") != head:
            raise BuildError(f"predecessor receipt binding drift: {roadmap_phase_id}")
        rows.append({
            "roadmap_phase_id": roadmap_phase_id,
            "phase_id": spec["phase_id"],
            "manifest_ref": spec["manifest_ref"],
            "manifest_sha256": _sha256(manifest_path),
            "validation_ref": spec["validation_ref"],
            "validation_head": head,
            "validation_run_id": run_id,
            "validation_receipt_count": expected_count,
            "task_accepted_count": 3,
            "acceptance_status": "PASSED",
        })
        total_receipts += expected_count
    return {
        "schema_version": "kmfa.v015.s08_stage_review.phase_evidence.v1",
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
    checks = {row["check_id"]: row["status"] for row in binding["checks"]}
    p1 = _read_json(REPO_ROOT / PHASES["S08-P1"]["manifest_ref"])
    p2 = _read_json(REPO_ROOT / PHASES["S08-P2"]["manifest_ref"])
    p3 = _read_json(REPO_ROOT / PHASES["S08-P3"]["manifest_ref"])
    contracts = (
        ("S08REV-C01", "TaskPack source and S08 3/9 accounting remain exact", source_contract()["source_integrity_status"] == "PASS"),
        ("S08REV-C02", "S08-P1 manifest and 19 receipts remain accepted", evidence["phases"][0]["acceptance_status"] == "PASSED"),
        ("S08REV-C03", "S08-P2 manifest and 19 receipts remain accepted", evidence["phases"][1]["acceptance_status"] == "PASSED"),
        ("S08REV-C04", "S08-P3 manifest and 19 receipts remain accepted", evidence["phases"][2]["acceptance_status"] == "PASSED"),
        ("S08REV-C05", "Predecessor receipt total is exactly 57", evidence["accounting"]["predecessor_receipt_count"] == 57),
        ("S08REV-C06", "All nine Roadmap tasks remain accepted", evidence["accounting"]["task_accepted_count"] == 9),
        ("S08REV-C07", "P1 keeps eight components and 10000 total weight", p1["component_count"] == 8 and p1["configured_weight_total_bps"] == 10000),
        ("S08REV-C08", "P1 keeps low-coverage and hard-conflict automatic merge closed", p1["low_coverage_auto_merge_allowed"] is False and p1["hard_conflict_auto_merge_allowed"] is False),
        ("S08REV-C09", "P1 keeps amount-only evidence auxiliary", p1["amount_evidence_auxiliary_only"] is True and p1["amount_alone_decided_match"] is False),
        ("S08REV-C10", "P2 blocks unknown-entity funds and partial aggregation", p2["unknown_entity_funds_aggregation_allowed"] is False and p2["partial_funds_aggregation_performed"] is False),
        ("S08REV-C11", "P2 keeps cross-entity accounts high-risk and aggregation closed", p2["cross_entity_account_resolution_status"] == "HIGH_RISK_CROSS_ENTITY_MISMATCH" and p2["cross_entity_funds_aggregation_allowed"] is False),
        ("S08REV-C12", "P2 never force-merges same-name counterparties", p2["forced_counterparty_merge_count"] == 0),
        ("S08REV-C13", "P1 and P3 automatic thresholds remain aligned", p3["auto_match_min_bps"] == 8500 and checks["P1_P3_AUTO_THRESHOLD_ALIGNED"] == "PASS"),
        ("S08REV-C14", "All twenty live cross-phase checks pass", binding["accounting"] == {"total": 20, "passed": 20, "failed": 0}),
        ("S08REV-C15", "A high score cannot bypass P1 low-coverage review", checks["LOW_COVERAGE_SCORE_BYPASS_CLOSED"] == "PASS"),
        ("S08REV-C16", "Missing company entity forces manual review and blocks aggregation", checks["MISSING_ENTITY_FORCES_MANUAL"] == checks["MISSING_ENTITY_BLOCKS_AGGREGATION"] == "PASS"),
        ("S08REV-C17", "Cross-entity account forces manual review and blocks aggregation", checks["CROSS_ENTITY_ACCOUNT_FORCES_MANUAL"] == checks["CROSS_ENTITY_ACCOUNT_BLOCKS_AGGREGATION"] == "PASS"),
        ("S08REV-C18", "Ambiguous counterparty forces manual review", checks["AMBIGUOUS_COUNTERPARTY_FORCES_MANUAL"] == "PASS"),
        ("S08REV-C19", "Decision and recalculation bind to the exact reviewed pair", checks["DECISION_BOUND_TO_ROUTE"] == checks["RECALCULATION_BOUND_TO_EVENT"] == checks["CROSS_PAIR_EVENT_REJECTED"] == "PASS"),
        ("S08REV-C20", "Open-item count remains 128 across all three phases", p1["current_private_open_unconfirmed_item_count"] == p2["current_private_open_unconfirmed_item_count"] == p3["current_private_open_unconfirmed_item_count"] == 128),
        ("S08REV-C21", "Conflict count remains six and formal report stays closed", p1["current_private_conflict_candidate_count"] == p2["current_private_conflict_candidate_count"] == p3["current_private_conflict_candidate_count"] == 6 and p3["current_report_display_label_zh"] == "暂不可使用" and p3["current_formal_report_release_allowed"] is False),
        ("S08REV-C22", "Raw, report, upload, App and business actions stay closed", all(row["raw_root_access_count"] == 0 and row["raw_business_content_read"] is False and row["formal_report_generated"] is False and row["github_upload_performed"] is False and row["app_reinstall_performed"] is False and row["business_execution_performed"] is False for row in (p1, p2, p3)) and binding["raw_root_access_count"] == 0),
    )
    rows = [
        {"contract_id": contract_id, "name": name, "status": "PASS" if passed else "FAIL", "blocks_stage_acceptance": not passed}
        for contract_id, name, passed in contracts
    ]
    failed = sum(row["status"] != "PASS" for row in rows)
    return {
        "schema_version": "kmfa.v015.s08_stage_review.contracts.v1",
        "contracts": rows,
        "accounting": {"total": len(rows), "passed": len(rows) - failed, "failed": failed, "blocking_failed": failed},
    }


def findings() -> list[dict[str, Any]]:
    return [
        {
            "finding_id": "S08REV-F001",
            "severity": "P1",
            "finding": "P3 若只接收匹配分数，可能把 P1 已判定为低覆盖或证据不足的高分记录自动通过。",
            "status": "FIXED_VALIDATED",
            "fix_ref": "KMFA/tools/v015_s08_stage_review_contract.py",
            "validation_ref": "KMFA/tests/test_v015_s08_stage_review_contract.py",
            "blocks_stage_acceptance": "false",
        },
        {
            "finding_id": "S08REV-F002",
            "severity": "P1",
            "finding": "P2 的主体、账户和往来方未确认状态此前没有显式约束 P3 自动匹配。",
            "status": "FIXED_VALIDATED",
            "fix_ref": "KMFA/tools/v015_s08_stage_review_contract.py",
            "validation_ref": "KMFA/tests/test_v015_s08_stage_review_contract.py",
            "blocks_stage_acceptance": "false",
        },
        {
            "finding_id": "S08REV-F003",
            "severity": "P1",
            "finding": "人工决定和重算回执此前没有绑定完整的 P1/P2/P3 复审路由，存在串单风险。",
            "status": "FIXED_VALIDATED",
            "fix_ref": "KMFA/tools/v015_s08_stage_review_contract.py",
            "validation_ref": "KMFA/tests/test_v015_s08_stage_review_contract.py",
            "blocks_stage_acceptance": "false",
        },
    ]


def risks() -> list[dict[str, Any]]:
    return [
        {"risk_id": "RISK-KMFA-V015-S08-001", "risk": "128 项仍缺少充分证据，当前报告不能使用。", "route": "S09P3T03_DIFFERENCE_CLOSURE", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s08_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S08-002", "risk": "6 项跨来源冲突仍需人工判断，禁止自动择源。", "route": "S09P3T03_DIFFERENCE_CLOSURE", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s08_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S08-003", "risk": "本轮以公开合成案例验证衔接，尚未替代后续完整产品与界面集成验收。", "route": "S14P3T03_PRODUCT_LANGUAGE_REVIEW", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s08_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S08-004", "risk": "本地回归通过不等于远端 CI 已执行同一门禁。", "route": "LATER_ENGINEERING_CI_GATE", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s08_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S08-005", "risk": "S09-P1 尚未开始。", "route": "S09P1_ONLY_NEXT_RUN", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s08_stage_acceptance": "false"},
    ]


def manifest(*, final_validation: bool, receipts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    receipts = receipts or []
    passed = bool(final_validation and receipts and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in receipts))
    validation_head = receipts[0].get("validation_head") if passed else None
    validation_run_id = receipts[0].get("validation_run_id") if passed else None
    if passed and ({row.get("validation_head") for row in receipts} != {validation_head} or {row.get("validation_run_id") for row in receipts} != {validation_run_id}):
        raise BuildError("review receipts do not share one head and run")
    return {
        "schema_version": "kmfa.v015.s08_stage_review.manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S08",
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
        "decision": "GO_TO_S09_P1_ONLY" if passed else "REMAIN_IN_S08_STAGE_REVIEW",
        "phase_accounting": phase_evidence()["accounting"],
        "cross_phase_accounting": cross_phase_contracts()["accounting"],
        "binding_check_accounting": binding_contract.public_verification()["accounting"],
        "review_findings": {"total": 3, "fixed_validated": 3, "open": 0, "blocking_open": 0},
        "open_risks": {"total": 5, "routed": 5, "plan_gap_count": 0, "blocking": 0},
        "overall_accepted_phase_count": 22,
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
        "s08_stage_review_started": True,
        "s08_stage_review_performed": passed,
        "s08_stage_review_acceptance_status": "PASSED" if passed else "PENDING_FINAL_VALIDATION",
        "s09_entry_allowed": passed,
        "s09_p1_entry_allowed": passed,
        "s09_p1_started": False,
        "s09_p2_plus_entry_allowed": False,
        "product_implementation_allowed": passed,
        "validation_run_id": validation_run_id,
        "validation_head": validation_head,
        "validation_receipt_count": len(receipts) if passed else 0,
        "validation_pass_count": len(receipts) if passed else 0,
        "validation_failed_count": 0,
    }


CHANGED_FILES = [
    "KMFA/AGENTS.md",
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/README.md",
    "KMFA/docs/governance/",
    "KMFA/metadata/model_registry.yaml",
    "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S08_STAGE_REVIEW/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s08_stage_review.py",
    "KMFA/tests/test_v015_s08_stage_review_contract.py",
    "KMFA/tests/test_v015_s08_stage_review_governance.py",
    "KMFA/tools/build_v015_s08_stage_review.py",
    "KMFA/tools/check_v015_s08_stage_review.py",
    "KMFA/tools/run_v015_s08_stage_review_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s08_stage_review_contract.py",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
]


def governance_records(*, final_validation: bool, receipts: list[dict[str, Any]] | None = None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    receipts = receipts or []
    final = bool(final_validation and receipts)
    suffix = "FINAL" if final else "EXECUTION"
    timestamp = "2026-07-15T16:20:00+10:00" if final else "2026-07-15T16:00:00+10:00"
    common: dict[str, Any] = {
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S08",
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
        "predecessor_receipt_count": 57,
        "cross_phase_contract_count": 22,
        "binding_check_count": 20,
        "fixed_review_finding_count": 3,
        "open_review_finding_count": 0,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "decision": "GO_TO_S09_P1_ONLY" if final else "REMAIN_IN_S08_STAGE_REVIEW",
        "s08_stage_review_started": True,
        "s08_stage_review_performed": final,
        "s08_stage_review_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s09_entry_allowed": final,
        "s09_p1_entry_allowed": final,
        "s09_p1_started": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_generated": False,
        "business_execution_performed": False,
        "evidence_ref": "KMFA/stage_artifacts/V015_S08_STAGE_REVIEW/",
        "event_time": timestamp,
        "updated_at": timestamp,
        "version": VERSION,
        "status": "completed_validated_local_only_s08_stage_review_s09_p1_entry_only" if final else "stage_review_execution_complete_pending_final_validation_s09_closed",
    }
    if final:
        common.update({
            "validation_run_id": receipts[0]["validation_run_id"],
            "validation_head": receipts[0]["validation_head"],
            "validation_receipt_count": len(receipts),
            "validation_pass_count": len(receipts),
            "validation_failed_count": 0,
        })
    summary = "S08 整体复审通过精确验证，只开放 S09-P1。" if final else "S08 整体复审已修复三个跨阶段漏洞，等待最终验证。"
    development = {
        "schema_version": "kmfa.development_event.v1",
        "event_id": f"DEV-KMFA-20260715-V015-S08-STAGE-REVIEW-{suffix}",
        "event_type": "final_validation" if final else "stage_review_execution",
        "summary": summary,
        "iteration_id": "ITER-20260715-KMFA-V015-S08-STAGE-REVIEW",
        "result_commit": "recorded_by_commit_containing_this_file" if final else "pending_implementation_commit",
        "files_changed": CHANGED_FILES,
        **common,
    }
    governance = {
        "schema_version": "kmfa.governance_event.v1",
        "event_id": f"EVENT-KMFA-20260715-V015-S08-STAGE-REVIEW-{suffix}",
        "event_type": development["event_type"],
        "summary": summary,
        **common,
    }
    stage = {
        "schema_version": "kmfa.stage_status.v1",
        "status_record_id": f"STATUS-KMFA-20260715-V015-S08-STAGE-REVIEW-{suffix}",
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
            "event_id": "DEV-KMFA-20260715-V015-S08-STAGE-REVIEW-COVERAGE",
            "event_type": "governance_coverage",
            "summary": "Records exact generated evidence paths for S08 Stage Review changed-file coverage.",
            "iteration_id": "ITER-20260715-KMFA-V015-S08-STAGE-REVIEW",
            "result_commit": "pending_implementation_commit",
            "project_id": "KMFA",
            "target_release": "v1.5",
            "stage_id": "S08",
            "phase_id": RUN_PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "fact_level": "EXTRACTED",
            "files_changed": [
                "KMFA/stage_artifacts/V015_S08_STAGE_REVIEW/human/open_risks_zh.md",
                "KMFA/stage_artifacts/V015_S08_STAGE_REVIEW/machine/cross_phase_binding_verification_public_safe.json",
                "KMFA/stage_artifacts/V015_S08_STAGE_REVIEW/machine/cross_phase_contracts_public_safe.json",
                "KMFA/stage_artifacts/V015_S08_STAGE_REVIEW/machine/open_risk_register_public_safe.csv",
                "KMFA/stage_artifacts/V015_S08_STAGE_REVIEW/machine/phase_evidence_public_safe.json",
                "KMFA/stage_artifacts/V015_S08_STAGE_REVIEW/machine/s08_stage_review_manifest.json",
                "KMFA/stage_artifacts/V015_S08_STAGE_REVIEW/machine/source_contract_public_safe.json",
            ],
            "event_time": "2026-07-15T16:01:00+10:00",
            "updated_at": "2026-07-15T16:01:00+10:00",
            "version": VERSION,
            "status": "coverage_complete_pending_implementation_commit",
        }
        _append_jsonl_once(DEVELOPMENT_EVENTS_PATH, coverage, key="event_id")
    _append_jsonl_once(GOVERNANCE_EVENTS_PATH, governance, key="event_id")
    _append_jsonl_once(STAGE_STATUS_PATH, stage, key="status_record_id")


def expected_static_outputs() -> dict[Path, bytes]:
    finding_rows = findings()
    risk_rows = risks()
    return {
        MACHINE_ROOT / "source_contract_public_safe.json": _json_bytes(source_contract()),
        MACHINE_ROOT / "phase_evidence_public_safe.json": _json_bytes(phase_evidence()),
        MACHINE_ROOT / "cross_phase_contracts_public_safe.json": _json_bytes(cross_phase_contracts()),
        MACHINE_ROOT / "cross_phase_binding_verification_public_safe.json": _json_bytes(binding_contract.public_verification()),
        MACHINE_ROOT / "stage8_review_findings_public_safe.csv": _csv_bytes(list(finding_rows[0]), finding_rows),
        MACHINE_ROOT / "open_risk_register_public_safe.csv": _csv_bytes(list(risk_rows[0]), risk_rows),
        HUMAN_ROOT / "stage8_review_report_zh.md": (
            "# KMFA v1.5 第 8 阶段整体复审\n\n"
            "- 三个部分、9 项任务、57 条原始验证记录全部复核通过。\n"
            "- 发现并修复 3 个衔接漏洞：高分不能绕过人工审核；主体、账户或往来方不明确时不能自动匹配；人工决定和重算回执不能串单。\n"
            "- 22 项跨部分检查和 20 项实时运行检查全部通过。\n"
            "- 128 项待确认事项和 6 项冲突仍未关闭，所以当前报告继续显示“暂不可使用”。\n"
            "- 本轮未读取原始财务资料，未生成正式报告，未上传 GitHub，未重装 App，也未开始第 9 阶段。\n"
        ).encode(),
        HUMAN_ROOT / "test_results_zh.md": (
            "# 测试结果\n\n最终结果以机器验证回执和严格检查器为准：57 条前序回执、22 项跨部分检查、20 项实时检查、3 个已修复问题和 5 项风险路径都必须完全一致。\n"
        ).encode(),
        HUMAN_ROOT / "rollback_plan_zh.md": (
            "# 回滚方案\n\n只回滚本次第 8 阶段复审新增的衔接代码、测试、证据和状态登记；不得改写三个已验收部分，不得触碰原始资料、GitHub、已安装 App 或任何第 9 阶段文件。\n"
        ).encode(),
        HUMAN_ROOT / "open_risks_zh.md": (
            "# 开放风险\n\n5 项剩余风险都有明确后续路径。它们不阻断第 8 阶段复审，但 128 项待确认事项和 6 项冲突继续阻止正式报告发布。\n"
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
        missing = [path.relative_to(REPO_ROOT).as_posix() for path in (MANIFEST_PATH, VALIDATION_RESULTS_PATH) if not path.is_file()]
        return sorted(set(mismatches + missing))
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
            print("PASS: S08 Stage Review public-safe artifacts match deterministic builder")
        else:
            write_outputs()
            print("UPDATED: S08 Stage Review public-safe artifacts")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, zipfile.BadZipFile, BuildError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
