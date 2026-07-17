#!/usr/bin/env python3
"""Build deterministic receipt-bound evidence for KMFA v1.5 S09 review."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import zipfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s09_stage_review_contract as contract


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S09_STAGE_REVIEW"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
MANIFEST_PATH = MACHINE_ROOT / "s09_stage_review_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
GOVERNANCE_EVENTS_PATH = PROJECT_ROOT / "docs/governance/events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"

RUN_PHASE_ID = contract.RUN_PHASE_ID
TASK_ID = contract.TASK_ID
ACCEPTANCE_ID = contract.ACCEPTANCE_ID
VERSION = contract.VERSION
REVIEW_BASE_COMMIT = "f8044a62e052a27fd12d8072c2d7eaeabfdb067f"
SOURCE_PACKAGE = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
SOURCE_PACKAGE_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

PHASES = {
    "S09-P1": {
        "phase_id": "V015_S09_P1_SCOPE_RULE_MODELING",
        "manifest_ref": "KMFA/stage_artifacts/V015_S09_P1_SCOPE_RULE_MODELING/machine/s09_p1_scope_rule_modeling_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S09_P1_SCOPE_RULE_MODELING/machine/validation_results.jsonl",
        "receipt_count": 20,
    },
    "S09-P2": {
        "phase_id": "V015_S09_P2_CONVERSION_RECONCILIATION_ENGINE",
        "manifest_ref": "KMFA/stage_artifacts/V015_S09_P2_CONVERSION_RECONCILIATION_ENGINE/machine/s09_p2_conversion_reconciliation_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S09_P2_CONVERSION_RECONCILIATION_ENGINE/machine/validation_results.jsonl",
        "receipt_count": 20,
    },
    "S09-P3": {
        "phase_id": "V015_S09_P3_HUMAN_READABLE_AUDIT",
        "manifest_ref": "KMFA/stage_artifacts/V015_S09_P3_HUMAN_READABLE_AUDIT/machine/s09_p3_human_readable_audit_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S09_P3_HUMAN_READABLE_AUDIT/machine/validation_results.jsonl",
        "receipt_count": 20,
    },
}

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "stage_contract_tests",
    "stage_review_tests",
    "stage_review_governance_tests",
    "s09_predecessor_regression",
    "s09_p1_builder",
    "s09_p2_builder",
    "s09_p3_builder",
    "s08_stage_review_dependency",
    "builder_exact_rebuild",
    "stage_checker_pre_final",
    "roadmap_governance_tests",
    "roadmap_sync_pending",
    "metadata_protocol",
    "project_governance",
    "lean_governance",
    "governance_sync",
    "no_float_money",
    "no_omission",
    "public_boundary",
    "git_diff_check",
)


class BuildError(RuntimeError):
    pass


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _jsonl_bytes(values: Iterable[Mapping[str, Any]]) -> bytes:
    return b"".join((json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n").encode() for row in values)


def _csv_bytes(headers: list[str], rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode()


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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    stage = next((row for row in roadmap["stages"] if row.get("id") == "S09"), None)
    if not stage or len(stage.get("phases") or []) != 3:
        raise BuildError("TaskPack S09 Phase count drift")
    tasks = [task for phase in stage["phases"] for task in phase.get("tasks") or []]
    if len(tasks) != 9:
        raise BuildError("TaskPack S09 Task count drift")
    return {
        "schema_version": "kmfa.v015.s09_stage_review.source_contract.v1",
        "source_package_file": SOURCE_PACKAGE.name,
        "source_package_sha256": SOURCE_PACKAGE_SHA256,
        "roadmap_member": members[0],
        "roadmap_counts": {"stages": 24, "phases": 72, "tasks": 216},
        "s09_counts": {"phases": 3, "tasks": 9},
        "s09_goal": stage["goal"],
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
        count = int(spec["receipt_count"])
        if manifest.get("run_phase_id") != spec["phase_id"] or manifest.get("roadmap_phase_id") != roadmap_phase_id:
            raise BuildError(f"predecessor identity drift: {roadmap_phase_id}")
        if manifest.get("phase_acceptance_status") != "PASSED" or manifest.get("phase_task_accepted_count") != 3:
            raise BuildError(f"predecessor not accepted: {roadmap_phase_id}")
        if len(receipts) != count or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
            raise BuildError(f"predecessor receipt failure: {roadmap_phase_id}")
        run_ids = {row.get("validation_run_id") for row in receipts}
        heads = {row.get("validation_head") for row in receipts}
        if len(run_ids) != 1 or None in run_ids or len(heads) != 1 or None in heads:
            raise BuildError(f"predecessor receipts do not share one head/run: {roadmap_phase_id}")
        run_id, head = next(iter(run_ids)), next(iter(heads))
        if manifest.get("validation_run_id") != run_id or manifest.get("validation_head") != head:
            raise BuildError(f"predecessor receipt binding drift: {roadmap_phase_id}")
        rows.append(
            {
                "roadmap_phase_id": roadmap_phase_id,
                "phase_id": spec["phase_id"],
                "manifest_ref": spec["manifest_ref"],
                "manifest_sha256": _sha256(manifest_path),
                "validation_ref": spec["validation_ref"],
                "validation_head": head,
                "validation_run_id": run_id,
                "validation_receipt_count": count,
                "task_accepted_count": 3,
                "acceptance_status": "PASSED",
            }
        )
        total_receipts += count
    return {
        "schema_version": "kmfa.v015.s09_stage_review.phase_evidence.v1",
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
    verification = contract.public_verification()
    checks = {row["check_id"]: row["status"] for row in verification["checks"]}
    p1_manifest = _read_json(REPO_ROOT / PHASES["S09-P1"]["manifest_ref"])
    p2_manifest = _read_json(REPO_ROOT / PHASES["S09-P2"]["manifest_ref"])
    p3_manifest = _read_json(REPO_ROOT / PHASES["S09-P3"]["manifest_ref"])
    specs = (
        ("S09REV-C01", "TaskPack source and S09 3/9 accounting remain exact", source_contract()["source_integrity_status"] == "PASS"),
        ("S09REV-C02", "S09-P1 manifest and 20 receipts remain accepted", evidence["phases"][0]["acceptance_status"] == "PASSED"),
        ("S09REV-C03", "S09-P2 manifest and 20 receipts remain accepted", evidence["phases"][1]["acceptance_status"] == "PASSED"),
        ("S09REV-C04", "S09-P3 manifest and 20 receipts remain accepted", evidence["phases"][2]["acceptance_status"] == "PASSED"),
        ("S09REV-C05", "Predecessor receipt total is exactly 60", evidence["accounting"]["predecessor_receipt_count"] == 60),
        ("S09REV-C06", "All nine Roadmap tasks remain accepted", evidence["accounting"]["task_accepted_count"] == 9),
        ("S09REV-C07", "P1 keeps one legal ledger and five derived views", p1_manifest["legal_ledger_count"] == 1 and p1_manifest["derived_view_count"] == 5),
        ("S09REV-C08", "P1 keeps all eight difference types", p1_manifest["difference_type_count"] == 8 and checks["P1_P3_DICTIONARY_LANGUAGE_ALIGNED"] == "PASS"),
        ("S09REV-C09", "P1 keeps adjustment chain and immutable source gates", p1_manifest["adjustment_event_roundtrip_exact"] and p1_manifest["direct_ledger_mutation_rejected"]),
        ("S09REV-C10", "P2 keeps exact-cent conservation", p2_manifest["conservation_passed"] and p2_manifest["conservation_residual_cents"] == 0),
        ("S09REV-C11", "P2 keeps differences separate without silent offset", p2_manifest["opposite_differences_retained_separately"] and p2_manifest["silent_offset_count"] == 0),
        ("S09REV-C12", "P2 full-chain rerun remains four layers", p2_manifest["rerun_chain_layer_count"] == 4 and p2_manifest["chain_state_consistent"]),
        ("S09REV-C13", "P2 cross-source disagreement stays human-confirmed", p2_manifest["cross_source_status"] == "PENDING_HUMAN_CONFIRMATION" and p2_manifest["cross_source_automatic_winner"] is None),
        ("S09REV-C14", "P3 keeps ten human-readable rules", p3_manifest["human_rule_count"] == 10 and p3_manifest["unexplained_rule_count"] == 0),
        ("S09REV-C15", "P3 business sample excludes technical internals", p3_manifest["report_technical_term_occurrence_count"] == 0 and p3_manifest["report_debug_field_count"] == 0),
        ("S09REV-C16", "P3 six-step closure remains complete and queryable", p3_manifest["closure_event_count"] == 6 and p3_manifest["history_queryable"]),
        ("S09REV-C17", "All thirty live cross-phase checks pass", verification["accounting"] == {"total": 30, "passed": 30, "failed": 0}),
        ("S09REV-C18", "P1 adjustments bind exactly before P2 conversion", checks["ACTIVE_ADJUSTMENT_BOUND_EXACTLY_ONCE"] == checks["UNBOUND_ACTIVE_ADJUSTMENT_REJECTED"] == "PASS"),
        ("S09REV-C19", "Every P2 decision difference binds into P3 summary", checks["ALL_DECISION_DIFFERENCES_INCLUDED"] == checks["SUMMARY_BINDING_COUNT_EXACT"] == "PASS"),
        ("S09REV-C20", "Closure and recalculation bind to exact difference version", checks["RECALCULATION_BOUND_TO_VERSION"] == checks["STALE_RECALCULATION_REJECTED"] == "PASS"),
        ("S09REV-C21", "Cross-case closure and report update are rejected", checks["CROSS_DIFFERENCE_EVENT_REJECTED"] == checks["REPORT_UPDATE_BOUND_TO_RECALCULATION"] == "PASS"),
        ("S09REV-C22", "Tampered difference cannot reach management summary", checks["TAMPERED_DIFFERENCE_REJECTED"] == "PASS"),
        ("S09REV-C23", "Unresolved cross-source queue stays blocking", checks["UNRESOLVED_CROSS_SOURCE_BLOCKS_DOWNSTREAM"] == checks["CROSS_SOURCE_AUTO_WINNER_FORBIDDEN"] == "PASS"),
        ("S09REV-C24", "Raw, report, upload, App and business actions stay closed", all(row["raw_root_access_count"] == 0 and row["raw_business_content_read"] is False and row["formal_report_generated"] is False and row["github_upload_performed"] is False and row["app_reinstall_performed"] is False and row["business_execution_performed"] is False for row in (p1_manifest, p2_manifest, p3_manifest)) and verification["raw_root_access_count"] == 0),
    )
    rows = [
        {"contract_id": contract_id, "name": name, "status": "PASS" if passed else "FAIL", "blocks_stage_acceptance": not passed}
        for contract_id, name, passed in specs
    ]
    failed = sum(row["status"] != "PASS" for row in rows)
    return {
        "schema_version": "kmfa.v015.s09_stage_review.contracts.v1",
        "contracts": rows,
        "accounting": {"total": len(rows), "passed": len(rows) - failed, "failed": failed, "blocking_failed": failed},
    }


def findings() -> list[dict[str, Any]]:
    return [
        {
            "finding_id": "S09REV-F001",
            "severity": "P1",
            "finding": "第 2 部分原接口可接收调用方拼装的已审批调整，未强制来自第 1 部分的追加式事件链。",
            "status": "FIXED_VALIDATED",
            "fix_ref": "KMFA/tools/v015_s09_stage_review_contract.py",
            "validation_ref": "KMFA/tests/test_v015_s09_stage_review_contract.py",
            "blocks_stage_acceptance": "false",
        },
        {
            "finding_id": "S09REV-F002",
            "severity": "P1",
            "finding": "第 3 部分经营摘要原接口允许调用方自行决定是否展示差异，可能漏掉或改写第 2 部分差异。",
            "status": "FIXED_VALIDATED",
            "fix_ref": "KMFA/tools/v015_s09_stage_review_contract.py",
            "validation_ref": "KMFA/tests/test_v015_s09_stage_review_contract.py",
            "blocks_stage_acceptance": "false",
        },
        {
            "finding_id": "S09REV-F003",
            "severity": "P1",
            "finding": "差异闭环、重新计算和摘要更新原先只按差异编号连接，未绑定完整核对版本与内容指纹。",
            "status": "FIXED_VALIDATED",
            "fix_ref": "KMFA/tools/v015_s09_stage_review_contract.py",
            "validation_ref": "KMFA/tests/test_v015_s09_stage_review_contract.py",
            "blocks_stage_acceptance": "false",
        },
    ]


def risks() -> list[dict[str, Any]]:
    return [
        {"risk_id": "RISK-KMFA-V015-S09-001", "risk": "128 项待确认事项和 6 项跨来源冲突仍未在真实业务资料中关闭。", "route": "S10P1_ONLY_NEXT_RUN", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s09_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S09-002", "risk": "本轮只用公开合成数据验证跨部分衔接，不代表真实业务核对已完成。", "route": "LATER_AUTHORIZED_PRIVATE_VALIDATION", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s09_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S09-003", "risk": "第 1 部分事件本身不含来源行，产品接入时必须始终经过本次新增的绑定层。", "route": "S10P1_INTEGRATION_CONTRACT", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s09_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S09-004", "risk": "本地完整回归通过不等于远端 CI 已执行同一门禁。", "route": "LATER_ENGINEERING_CI_GATE", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s09_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S09-005", "risk": "S10-P1 尚未开始。", "route": "S10P1_ONLY_NEXT_RUN", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s09_stage_acceptance": "false"},
    ]


def manifest(*, final_validation: bool, receipts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    receipts = receipts or []
    passed = bool(final_validation and receipts and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in receipts))
    head = receipts[0].get("validation_head") if passed else None
    run_id = receipts[0].get("validation_run_id") if passed else None
    if passed and ({row.get("validation_head") for row in receipts} != {head} or {row.get("validation_run_id") for row in receipts} != {run_id}):
        raise BuildError("review receipts do not share one head and run")
    return {
        "schema_version": "kmfa.v015.s09_stage_review.manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S09",
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
        "decision": "GO_TO_S10_P1_ONLY" if passed else "REMAIN_IN_S09_STAGE_REVIEW",
        "phase_accounting": phase_evidence()["accounting"],
        "cross_phase_accounting": cross_phase_contracts()["accounting"],
        "binding_check_accounting": contract.public_verification()["accounting"],
        "review_findings": {"total": 3, "fixed_validated": 3, "open": 0, "blocking_open": 0},
        "open_risks": {"total": 5, "routed": 5, "plan_gap_count": 0, "blocking": 0},
        "overall_accepted_phase_count": 25,
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
        "s09_stage_review_started": True,
        "s09_stage_review_performed": passed,
        "s09_stage_review_acceptance_status": "PASSED" if passed else "PENDING_FINAL_VALIDATION",
        "s10_entry_allowed": passed,
        "s10_p1_entry_allowed": passed,
        "s10_p1_started": False,
        "s10_p2_plus_entry_allowed": False,
        "product_implementation_allowed": passed,
        "validation_run_id": run_id,
        "validation_head": head,
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
    "KMFA/stage_artifacts/V015_S09_STAGE_REVIEW/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s09_stage_review.py",
    "KMFA/tests/test_v015_s09_stage_review_contract.py",
    "KMFA/tests/test_v015_s09_stage_review_governance.py",
    "KMFA/tools/build_v015_s09_stage_review.py",
    "KMFA/tools/check_v015_s09_stage_review.py",
    "KMFA/tools/run_v015_s09_stage_review_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s09_stage_review_contract.py",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
]


def governance_records(*, final_validation: bool, receipts: list[dict[str, Any]] | None = None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    receipts = receipts or []
    final = bool(final_validation and receipts)
    suffix = "FINAL" if final else "EXECUTION"
    timestamp = "2026-07-15T21:40:00+10:00" if final else "2026-07-15T21:20:00+10:00"
    common: dict[str, Any] = {
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S09",
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
        "predecessor_receipt_count": 60,
        "cross_phase_contract_count": 24,
        "binding_check_count": 30,
        "fixed_review_finding_count": 3,
        "open_review_finding_count": 0,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "decision": "GO_TO_S10_P1_ONLY" if final else "REMAIN_IN_S09_STAGE_REVIEW",
        "s09_stage_review_started": True,
        "s09_stage_review_performed": final,
        "s09_stage_review_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s10_entry_allowed": final,
        "s10_p1_entry_allowed": final,
        "s10_p1_started": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_generated": False,
        "business_execution_performed": False,
        "evidence_ref": "KMFA/stage_artifacts/V015_S09_STAGE_REVIEW/",
        "event_time": timestamp,
        "updated_at": timestamp,
        "version": VERSION,
        "status": "completed_validated_local_only_s09_stage_review_s10_p1_entry_only" if final else "stage_review_execution_complete_pending_final_validation_s10_closed",
    }
    if final:
        common.update(
            {
                "validation_run_id": receipts[0]["validation_run_id"],
                "validation_head": receipts[0]["validation_head"],
                "validation_receipt_count": len(receipts),
                "validation_pass_count": len(receipts),
                "validation_failed_count": 0,
            }
        )
    summary = "S09 整体复审通过精确验证，只开放 S10-P1。" if final else "S09 整体复审已修复三个跨部分绑定漏洞，等待最终验证。"
    development = {
        "schema_version": "kmfa.development_event.v1",
        "event_id": f"DEV-KMFA-20260715-V015-S09-STAGE-REVIEW-{suffix}",
        "event_type": "final_validation" if final else "stage_review_execution",
        "summary": summary,
        "iteration_id": "ITER-20260715-KMFA-V015-S09-STAGE-REVIEW",
        "result_commit": "recorded_by_commit_containing_this_file" if final else "pending_implementation_commit",
        "files_changed": CHANGED_FILES,
        **common,
    }
    governance = {
        "schema_version": "kmfa.governance_event.v1",
        "event_id": f"EVENT-KMFA-20260715-V015-S09-STAGE-REVIEW-{suffix}",
        "event_type": development["event_type"],
        "summary": summary,
        **common,
    }
    stage = {
        "schema_version": "kmfa.stage_status.v1",
        "status_record_id": f"STATUS-KMFA-20260715-V015-S09-STAGE-REVIEW-{suffix}",
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
            "event_id": "DEV-KMFA-20260715-V015-S09-STAGE-REVIEW-COVERAGE",
            "event_type": "governance_coverage",
            "summary": "Records exact generated evidence paths for S09 Stage Review changed-file coverage.",
            "iteration_id": "ITER-20260715-KMFA-V015-S09-STAGE-REVIEW",
            "result_commit": "pending_implementation_commit",
            "project_id": "KMFA",
            "target_release": "v1.5",
            "stage_id": "S09",
            "phase_id": RUN_PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "fact_level": "EXTRACTED",
            "files_changed": [
                "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
                "KMFA/docs/governance/OWNER_STATUS.md",
                "KMFA/docs/governance/STATUS.md",
                "KMFA/docs/governance/delivery_tasks.yaml",
                "KMFA/stage_artifacts/V015_S09_STAGE_REVIEW/human/open_risks_zh.md",
                "KMFA/stage_artifacts/V015_S09_STAGE_REVIEW/human/rollback_plan_zh.md",
                "KMFA/stage_artifacts/V015_S09_STAGE_REVIEW/human/stage9_review_report_zh.md",
                "KMFA/stage_artifacts/V015_S09_STAGE_REVIEW/human/test_results_zh.md",
                "KMFA/stage_artifacts/V015_S09_STAGE_REVIEW/machine/cross_phase_binding_verification_public_safe.json",
                "KMFA/stage_artifacts/V015_S09_STAGE_REVIEW/machine/cross_phase_contracts_public_safe.json",
                "KMFA/stage_artifacts/V015_S09_STAGE_REVIEW/machine/open_risk_register_public_safe.csv",
                "KMFA/stage_artifacts/V015_S09_STAGE_REVIEW/machine/phase_evidence_public_safe.json",
                "KMFA/stage_artifacts/V015_S09_STAGE_REVIEW/machine/s09_stage_review_manifest.json",
                "KMFA/stage_artifacts/V015_S09_STAGE_REVIEW/machine/source_contract_public_safe.json",
                "KMFA/stage_artifacts/V015_S09_STAGE_REVIEW/machine/stage9_review_findings_public_safe.csv",
                "KMFA/stage_artifacts/V015_S09_STAGE_REVIEW/machine/validation_results.jsonl",
            ],
            "event_time": "2026-07-15T21:21:00+10:00",
            "updated_at": "2026-07-15T21:21:00+10:00",
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
        MACHINE_ROOT / "cross_phase_binding_verification_public_safe.json": _json_bytes(contract.public_verification()),
        MACHINE_ROOT / "stage9_review_findings_public_safe.csv": _csv_bytes(list(finding_rows[0]), finding_rows),
        MACHINE_ROOT / "open_risk_register_public_safe.csv": _csv_bytes(list(risk_rows[0]), risk_rows),
        HUMAN_ROOT / "stage9_review_report_zh.md": (
            "# KMFA v1.5 第 9 阶段整体复审\n\n"
            "- 三个部分、9 项任务、60 条原始验证记录全部复核通过。\n"
            "- 修复 3 个衔接问题：调整不能伪造后进入计算；经营摘要不能漏掉或改写核对差异；闭环、重算和摘要更新不能串单或使用旧版本。\n"
            "- 24 项跨部分检查和 30 项实时运行检查必须全部通过。\n"
            "- 128 项待确认事项和 6 项冲突仍未关闭，当前报告继续显示‘暂不可使用’。\n"
            "- 本轮未读取原始财务资料，未生成正式报告，未上传 GitHub，未重装 App，也未开始 S10-P1。\n"
        ).encode(),
        HUMAN_ROOT / "test_results_zh.md": (
            "# 测试结果\n\n最终结果以机器回执和严格检查器为准：60 条前序回执、24 项跨部分检查、30 项实时检查、3 个已修复问题和 5 项风险路径必须完全一致。\n"
        ).encode(),
        HUMAN_ROOT / "rollback_plan_zh.md": (
            "# 回滚方案\n\n只回滚本次第 9 阶段复审新增的绑定代码、测试、证据和状态登记；不得改写三个已验收部分，不得触碰原始资料、GitHub、已安装 App 或任何第 10 阶段文件。\n"
        ).encode(),
        HUMAN_ROOT / "open_risks_zh.md": (
            "# 开放风险\n\n5 项剩余风险均有后续路径。它们不阻断第 9 阶段复审，但真实业务待确认事项和冲突继续阻止正式报告发布。\n"
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
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            mismatches = check_outputs()
            if mismatches:
                raise BuildError("artifact drift: " + ", ".join(mismatches))
            print("PASS: S09 Stage Review public-safe artifacts match deterministic builder")
        else:
            write_outputs()
            print("UPDATED: S09 Stage Review public-safe artifacts")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, zipfile.BadZipFile, BuildError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
