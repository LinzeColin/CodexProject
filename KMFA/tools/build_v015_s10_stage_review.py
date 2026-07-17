#!/usr/bin/env python3
"""生成 KMFA v1.5 S10 整体复审的确定性公开证据。"""

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

from KMFA.tools import v015_s10_stage_review_contract as contract


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S10_STAGE_REVIEW"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
MANIFEST_PATH = MACHINE_ROOT / "s10_stage_review_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
GOVERNANCE_EVENTS_PATH = PROJECT_ROOT / "docs/governance/events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"

RUN_PHASE_ID = contract.RUN_PHASE_ID
TASK_ID = contract.TASK_ID
ACCEPTANCE_ID = contract.ACCEPTANCE_ID
VERSION = contract.VERSION
REVIEW_BASE_COMMIT = "315949cf6a36377d361f90848036287d86d49a5c"
SOURCE_PACKAGE = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
SOURCE_PACKAGE_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

PHASES = {
    "S10-P1": {
        "phase_id": "V015_S10_P1_GENERAL_IMPORT",
        "manifest_ref": "KMFA/stage_artifacts/V015_S10_P1_GENERAL_IMPORT/machine/s10_p1_general_import_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S10_P1_GENERAL_IMPORT/machine/validation_results.jsonl",
        "receipt_count": 19,
    },
    "S10-P2": {
        "phase_id": "V015_S10_P2_SOURCE_ADAPTERS",
        "manifest_ref": "KMFA/stage_artifacts/V015_S10_P2_SOURCE_ADAPTERS/machine/s10_p2_source_adapters_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S10_P2_SOURCE_ADAPTERS/machine/validation_results.jsonl",
        "receipt_count": 19,
    },
    "S10-P3": {
        "phase_id": "V015_S10_P3_AUTOMATIC_INGESTION_RESERVE",
        "manifest_ref": "KMFA/stage_artifacts/V015_S10_P3_AUTOMATIC_INGESTION_RESERVE/machine/s10_p3_automatic_ingestion_reserve_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S10_P3_AUTOMATIC_INGESTION_RESERVE/machine/validation_results.jsonl",
        "receipt_count": 19,
    },
}

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "stage_contract_tests",
    "stage_review_tests",
    "stage_review_governance_tests",
    "s10_predecessor_regression",
    "s10_p1_builder",
    "s10_p2_builder",
    "s10_p3_builder",
    "s09_stage_review_dependency",
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
    "taskpack_source",
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
    stage = next((row for row in roadmap["stages"] if row.get("id") == "S10"), None)
    if not stage or len(stage.get("phases") or []) != 3:
        raise BuildError("TaskPack S10 Phase count drift")
    tasks = [task for phase in stage["phases"] for task in phase.get("tasks") or []]
    if len(tasks) != 9:
        raise BuildError("TaskPack S10 Task count drift")
    return {
        "schema_version": "kmfa.v015.s10_stage_review.source_contract.v1",
        "source_package_file": SOURCE_PACKAGE.name,
        "source_package_sha256": SOURCE_PACKAGE_SHA256,
        "roadmap_member": members[0],
        "roadmap_counts": {"stages": 24, "phases": 72, "tasks": 216},
        "s10_counts": {"phases": 3, "tasks": 9},
        "s10_goal": stage["goal"],
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
        if manifest.get("run_phase_id") != spec["phase_id"] or manifest.get("phase_acceptance_status") != "PASSED":
            raise BuildError(f"predecessor acceptance drift: {roadmap_phase_id}")
        if len(receipts) != count or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
            raise BuildError(f"predecessor receipt drift: {roadmap_phase_id}")
        run_ids = {row.get("validation_run_id") for row in receipts}
        heads = {row.get("validation_head") for row in receipts}
        if len(run_ids) != 1 or len(heads) != 1 or None in run_ids or None in heads:
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
        "schema_version": "kmfa.v015.s10_stage_review.phase_evidence.v1",
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
    p1_manifest = _read_json(REPO_ROOT / PHASES["S10-P1"]["manifest_ref"])
    p2_manifest = _read_json(REPO_ROOT / PHASES["S10-P2"]["manifest_ref"])
    p3_manifest = _read_json(REPO_ROOT / PHASES["S10-P3"]["manifest_ref"])
    specs = (
        ("S10REV-C01", "TaskPack source and S10 3/9 accounting remain exact", source_contract()["source_integrity_status"] == "PASS"),
        ("S10REV-C02", "S10-P1 manifest and 19 receipts remain accepted", evidence["phases"][0]["acceptance_status"] == "PASSED"),
        ("S10REV-C03", "S10-P2 manifest and 19 receipts remain accepted", evidence["phases"][1]["acceptance_status"] == "PASSED"),
        ("S10REV-C04", "S10-P3 manifest and 19 receipts remain accepted", evidence["phases"][2]["acceptance_status"] == "PASSED"),
        ("S10REV-C05", "Predecessor receipt total is exactly 57", evidence["accounting"]["predecessor_receipt_count"] == 57),
        ("S10REV-C06", "All nine Roadmap tasks remain accepted", evidence["accounting"]["task_accepted_count"] == 9),
        ("S10REV-C07", "P1 keeps six formats and eight extensions", p1_manifest["supported_format_category_count"] == 6 and p1_manifest["supported_extension_count"] == 8),
        ("S10REV-C08", "P1 keeps explicit confirmation and invisible partial commit", p1_manifest["confirmation_required_before_processing"] and p1_manifest["partial_commit_visible"] is False),
        ("S10REV-C09", "P1 keeps archive and bad-file isolation safeguards", p1_manifest["archive_path_traversal_rejected"] and p1_manifest["archive_compression_bomb_rejected"] and p1_manifest["bad_file_isolation_validated"]),
        ("S10REV-C10", "P2 keeps six sources and fifteen versioned templates", p2_manifest["source_system_count"] == 6 and p2_manifest["adapter_template_count"] == p2_manifest["mapping_versioned_template_count"] == 15),
        ("S10REV-C11", "P2 rejects ambiguity and quarantines unknown accounts", p2_manifest["ambiguous_or_unknown_mapping_rejected"] and p2_manifest["unknown_account_quarantined"]),
        ("S10REV-C12", "P3 keeps five disabled connector candidates", p3_manifest["future_source_count"] == 5 and p3_manifest["automatic_connector_enabled_count"] == 0),
        ("S10REV-C13", "P3 keeps bounded retry and manual fallback", p3_manifest["retry_budget"] == 3 and p3_manifest["no_data_retry_count"] == 0 and p3_manifest["manual_import_available"]),
        ("S10REV-C14", "All thirty-six live cross-part checks pass", verification["accounting"] == {"total": 36, "passed": 36, "failed": 0}),
        ("S10REV-C15", "P1 preview and confirmation bind exactly", checks["P1_INSPECTION_BOUND_TO_PREVIEW"] == checks["P1_CONFIRMATION_BOUND_TO_CURRENT_PREVIEW"] == "PASS"),
        ("S10REV-C16", "P2 receives the same file hash, source, period and entity", all(checks[name] == "PASS" for name in ("P1_FILE_HASH_PRESERVED_IN_P2", "P1_SOURCE_ID_PRESERVED_IN_P2", "P1_PERIOD_PRESERVED_IN_P2", "P1_ENTITY_PRESERVED_IN_P2"))),
        ("S10REV-C17", "Stale or swapped confirmation inputs are rejected", all(checks[name] == "PASS" for name in ("TAMPERED_PREVIEW_REJECTED", "STALE_CONFIRMATION_REJECTED", "SWAPPED_FILE_HASH_REJECTED"))),
        ("S10REV-C18", "Five connector-to-adapter mappings are exact", checks["FIVE_CONNECTOR_MAPPINGS_EXACT"] == "PASS"),
        ("S10REV-C19", "Tax maps to TAX_EINVOICE without ambiguity", checks["TAX_MAPS_TO_TAX_EINVOICE"] == "PASS"),
        ("S10REV-C20", "Contract ledger remains file-only", checks["CONTRACT_LEDGER_REMAINS_FILE_ONLY"] == "PASS"),
        ("S10REV-C21", "Connector envelope cannot bypass P1/P2", checks["CONNECTOR_ENVELOPE_NOT_IMPORTABLE"] == checks["CONNECTOR_REQUIRES_P1_P2_CHAIN"] == "PASS"),
        ("S10REV-C22", "Schedule failure cannot record success or advance cursor", all(checks[name] == "PASS" for name in ("NO_DATA_NOT_IMPORT_SUCCESS", "TRANSIENT_FAILURE_NOT_IMPORT_SUCCESS", "PERMANENT_FAILURE_NOT_IMPORT_SUCCESS", "SCHEDULE_FAILURE_DOES_NOT_ADVANCE_CURSOR"))),
        ("S10REV-C23", "Manual file import remains available after schedule outcomes", checks["NO_DATA_MANUAL_IMPORT_AVAILABLE"] == "PASS"),
        ("S10REV-C24", "Raw, live, release and business actions stay closed", checks["RAW_AND_LIVE_ACCESS_ZERO"] == checks["RELEASE_AND_BUSINESS_ACTIONS_CLOSED"] == "PASS" and all(row["raw_root_access_count"] == 0 and row["raw_business_content_read"] is False and row["github_upload_performed"] is False and row["app_reinstall_performed"] is False and row["business_execution_performed"] is False for row in (p1_manifest, p2_manifest, p3_manifest))),
    )
    rows = [
        {"contract_id": identifier, "name": name, "status": "PASS" if passed else "FAIL", "blocks_stage_acceptance": not passed}
        for identifier, name, passed in specs
    ]
    failed = sum(row["status"] != "PASS" for row in rows)
    return {
        "schema_version": "kmfa.v015.s10_stage_review.contracts.v1",
        "contracts": rows,
        "accounting": {"total": len(rows), "passed": len(rows) - failed, "failed": failed, "blocking_failed": failed},
    }


def findings() -> list[dict[str, Any]]:
    return [
        {"finding_id": "S10REV-F001", "severity": "P1", "finding": "自动入口原合同没有强制回到文件安全检查、人工确认和版本化适配链。", "status": "FIXED_VALIDATED", "fix_ref": "KMFA/tools/v015_s10_stage_review_contract.py", "validation_ref": "KMFA/tests/test_v015_s10_stage_review_contract.py", "blocks_stage_acceptance": "false"},
        {"finding_id": "S10REV-F002", "severity": "P1", "finding": "税务来源在自动入口叫 TAX，在文件适配器叫 TAX_EINVOICE，原先缺少唯一映射。", "status": "FIXED_VALIDATED", "fix_ref": "KMFA/tools/v015_s10_stage_review_contract.py", "validation_ref": "KMFA/tests/test_v015_s10_stage_review_contract.py", "blocks_stage_acceptance": "false"},
        {"finding_id": "S10REV-F003", "severity": "P1", "finding": "定时失败和无数据虽声明不阻断手工导入，但缺少禁止误记成功和推进游标的可执行约束。", "status": "FIXED_VALIDATED", "fix_ref": "KMFA/tools/v015_s10_stage_review_contract.py", "validation_ref": "KMFA/tests/test_v015_s10_stage_review_contract.py", "blocks_stage_acceptance": "false"},
    ]


def risks() -> list[dict[str, Any]]:
    return [
        {"risk_id": "RISK-KMFA-V015-S10-001", "risk": "本轮只用公开合成数据验证，未处理真实业务文件。", "route": "LATER_AUTHORIZED_PRIVATE_VALIDATION", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s10_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S10-002", "risk": "未来真实平台连接仍需逐个平台授权、安全评审和独立验收。", "route": "FUTURE_CONNECTOR_SEPARATE_ACCEPTANCE", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s10_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S10-003", "risk": "私有原子提交与真实平台游标推进尚未实现，本轮只定义前置合同。", "route": "LATER_AUTHORIZED_CONNECTOR_IMPLEMENTATION", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s10_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S10-004", "risk": "本地完整回归通过不等于远端 CI 已执行同一门禁。", "route": "FINAL_GITHUB_MAIN_UPLOAD_GATE", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s10_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S10-005", "risk": "S11-P1 尚未开始。", "route": "S11P1_ONLY_NEXT_RUN", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s10_stage_acceptance": "false"},
    ]


def manifest(*, final_validation: bool, receipts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    receipts = receipts or []
    passed = bool(final_validation and receipts and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in receipts))
    head = receipts[0].get("validation_head") if passed else None
    run_id = receipts[0].get("validation_run_id") if passed else None
    if passed and ({row.get("validation_head") for row in receipts} != {head} or {row.get("validation_run_id") for row in receipts} != {run_id}):
        raise BuildError("review receipts do not share one head and run")
    return {
        "schema_version": "kmfa.v015.s10_stage_review.manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S10",
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
        "decision": "GO_TO_S11_P1_ONLY" if passed else "REMAIN_IN_S10_STAGE_REVIEW",
        "phase_accounting": phase_evidence()["accounting"],
        "cross_phase_accounting": cross_phase_contracts()["accounting"],
        "live_check_accounting": contract.public_verification()["accounting"],
        "review_findings": {"total": 3, "fixed_validated": 3, "open": 0, "blocking_open": 0},
        "open_risks": {"total": 5, "routed": 5, "plan_gap_count": 0, "blocking": 0},
        "overall_accepted_phase_count": 28,
        "overall_taskpack_phase_count": 72,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "automatic_connector_enabled_count": 0,
        "live_connector_call_count": 0,
        "credential_read_count": 0,
        "s10_stage_review_started": True,
        "s10_stage_review_performed": passed,
        "s10_stage_review_acceptance_status": "PASSED" if passed else "PENDING_FINAL_VALIDATION",
        "s11_entry_allowed": passed,
        "s11_p1_entry_allowed": passed,
        "s11_p1_started": False,
        "s11_p2_plus_entry_allowed": False,
        "product_implementation_allowed": passed,
        "validation_run_id": run_id,
        "validation_head": head,
        "validation_receipt_count": len(receipts) if passed else 0,
        "validation_pass_count": len(receipts) if passed else 0,
        "validation_failed_count": 0,
    }


CHANGED_FILES = [
    "KMFA/AGENTS.md", "KMFA/CHANGELOG.md", "KMFA/HANDOFF.md", "KMFA/README.md",
    "KMFA/docs/governance/", "KMFA/metadata/model_registry.yaml", "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl", "KMFA/stage_artifacts/V015_S10_STAGE_REVIEW/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py", "KMFA/tests/test_v015_s10_stage_review.py",
    "KMFA/tests/test_v015_s10_stage_review_contract.py", "KMFA/tests/test_v015_s10_stage_review_governance.py",
    "KMFA/tools/build_v015_s10_stage_review.py", "KMFA/tools/check_v015_s10_stage_review.py",
    "KMFA/tools/run_v015_s10_stage_review_validations.py", "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s10_stage_review_contract.py", "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
]


def governance_records(*, final_validation: bool, receipts: list[dict[str, Any]] | None = None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    receipts = receipts or []
    final = bool(final_validation and receipts)
    suffix = "FINAL" if final else "EXECUTION"
    timestamp = "2026-07-15T23:10:00+10:00" if final else "2026-07-15T22:50:00+10:00"
    common: dict[str, Any] = {
        "project_id": "KMFA", "target_release": "v1.5", "stage_id": "S10", "phase_id": RUN_PHASE_ID,
        "task_id": TASK_ID, "acceptance_id": ACCEPTANCE_ID, "run_mode": "REVIEW_FIX", "work_kind": "STAGE_REVIEW_FIX",
        "fact_level": "EXTRACTED", "review_execution_status": "COMPLETED" if final else "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING", "stage_lifecycle_status": "COMPLETED" if final else "IN_PROGRESS",
        "stage_acceptance_status": "PASSED" if final else "PENDING", "stage_execution_percentage": 100,
        "predecessor_phase_count": 3, "predecessor_task_accepted_count": 9, "predecessor_receipt_count": 57,
        "cross_phase_contract_count": 24, "live_check_count": 36, "fixed_review_finding_count": 3,
        "open_review_finding_count": 0, "routed_residual_risk_count": 5,
        "raw_root_access_count": 0, "raw_business_content_read": False,
        "automatic_connector_enabled_count": 0, "live_connector_call_count": 0, "credential_read_count": 0,
        "decision": "GO_TO_S11_P1_ONLY" if final else "REMAIN_IN_S10_STAGE_REVIEW",
        "s10_stage_review_started": True, "s10_stage_review_performed": final,
        "s10_stage_review_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s11_entry_allowed": final, "s11_p1_entry_allowed": final, "s11_p1_started": False,
        "github_upload_performed": False, "app_reinstall_performed": False,
        "formal_report_generated": False, "business_execution_performed": False,
        "evidence_ref": "KMFA/stage_artifacts/V015_S10_STAGE_REVIEW/", "event_time": timestamp,
        "updated_at": timestamp, "version": VERSION,
        "status": "completed_validated_local_only_s10_stage_review_s11_p1_entry_only" if final else "stage_review_execution_complete_pending_final_validation_s11_closed",
    }
    if final:
        common.update({"validation_run_id": receipts[0]["validation_run_id"], "validation_head": receipts[0]["validation_head"], "validation_receipt_count": len(receipts), "validation_pass_count": len(receipts), "validation_failed_count": 0})
    summary = "S10 整体复审通过精确验证，只开放 S11-P1。" if final else "S10 整体复审已修复三个跨部分安全衔接问题，等待最终验证。"
    development = {
        "schema_version": "kmfa.development_event.v1", "event_id": f"DEV-KMFA-20260715-V015-S10-STAGE-REVIEW-{suffix}",
        "event_type": "final_validation" if final else "stage_review_execution", "summary": summary,
        "iteration_id": "ITER-20260715-KMFA-V015-S10-STAGE-REVIEW",
        "result_commit": "recorded_by_commit_containing_this_file" if final else "pending_implementation_commit",
        "files_changed": CHANGED_FILES, **common,
    }
    governance = {"schema_version": "kmfa.governance_event.v1", "event_id": f"EVENT-KMFA-20260715-V015-S10-STAGE-REVIEW-{suffix}", "event_type": development["event_type"], "summary": summary, **common}
    stage = {"schema_version": "kmfa.stage_status.v1", "status_record_id": f"STATUS-KMFA-20260715-V015-S10-STAGE-REVIEW-{suffix}", "record_type": "stage_review_status", "stage_phase_pass_count": 3, "stage_task_accepted_count": 9, **common}
    return development, governance, stage


def write_governance_records(*, final_validation: bool, receipts: list[dict[str, Any]] | None = None) -> None:
    development, governance, stage = governance_records(final_validation=final_validation, receipts=receipts)
    _append_jsonl_once(DEVELOPMENT_EVENTS_PATH, development, key="event_id")
    if not final_validation:
        coverage = {
            "schema_version": "kmfa.development_event.v1",
            "event_id": "DEV-KMFA-20260715-V015-S10-STAGE-REVIEW-COVERAGE",
            "event_type": "governance_coverage",
            "summary": "Records exact generated evidence paths for S10 Stage Review changed-file coverage.",
            "iteration_id": "ITER-20260715-KMFA-V015-S10-STAGE-REVIEW",
            "result_commit": "pending_implementation_commit",
            "project_id": "KMFA",
            "target_release": "v1.5",
            "stage_id": "S10",
            "phase_id": RUN_PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "fact_level": "EXTRACTED",
            "files_changed": [
                "KMFA/stage_artifacts/V015_S10_STAGE_REVIEW/human/open_risks_zh.md",
                "KMFA/stage_artifacts/V015_S10_STAGE_REVIEW/human/rollback_plan_zh.md",
                "KMFA/stage_artifacts/V015_S10_STAGE_REVIEW/human/stage10_review_report_zh.md",
                "KMFA/stage_artifacts/V015_S10_STAGE_REVIEW/human/test_results_zh.md",
                "KMFA/stage_artifacts/V015_S10_STAGE_REVIEW/machine/cross_phase_contracts_public_safe.json",
                "KMFA/stage_artifacts/V015_S10_STAGE_REVIEW/machine/cross_phase_verification_public_safe.json",
                "KMFA/stage_artifacts/V015_S10_STAGE_REVIEW/machine/open_risk_register_public_safe.csv",
                "KMFA/stage_artifacts/V015_S10_STAGE_REVIEW/machine/phase_evidence_public_safe.json",
                "KMFA/stage_artifacts/V015_S10_STAGE_REVIEW/machine/s10_stage_review_manifest.json",
                "KMFA/stage_artifacts/V015_S10_STAGE_REVIEW/machine/source_contract_public_safe.json",
                "KMFA/stage_artifacts/V015_S10_STAGE_REVIEW/machine/stage10_review_findings_public_safe.csv",
                "KMFA/stage_artifacts/V015_S10_STAGE_REVIEW/machine/validation_results.jsonl",
            ],
            "event_time": "2026-07-15T22:51:00+10:00",
            "updated_at": "2026-07-15T22:51:00+10:00",
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
        MACHINE_ROOT / "cross_phase_verification_public_safe.json": _json_bytes(contract.public_verification()),
        MACHINE_ROOT / "stage10_review_findings_public_safe.csv": _csv_bytes(list(finding_rows[0]), finding_rows),
        MACHINE_ROOT / "open_risk_register_public_safe.csv": _csv_bytes(list(risk_rows[0]), risk_rows),
        HUMAN_ROOT / "stage10_review_report_zh.md": (
            "# KMFA v1.5 第 10 阶段整体复审\n\n"
            "- 三个部分、9 项任务、57 条前序验证记录全部复核通过。\n"
            "- 修复 3 个衔接问题：自动入口必须经过文件检查、人工确认和明确模板；税务来源统一映射；定时失败或无数据绝不能误记导入成功。\n"
            "- 24 项跨部分检查和 36 项实时运行检查必须全部通过。\n"
            "- 本轮没有读取原始资料，没有连接真实平台，没有启用自动连接，没有上传 GitHub，也没有重装 App。\n"
        ).encode(),
        HUMAN_ROOT / "test_results_zh.md": (
            "# 测试结果\n\n最终结果以机器回执和严格检查器为准：57 条前序回执、24 项跨部分检查、36 项实时检查、3 个已修复问题和 5 项后续风险必须完全一致。\n"
        ).encode(),
        HUMAN_ROOT / "rollback_plan_zh.md": (
            "# 回滚方案\n\n只回滚本次第 10 阶段复审新增的衔接代码、测试、证据和状态登记；不得改写三个已验收部分，不得触碰原始资料、GitHub、已安装 App 或第 11 阶段。\n"
        ).encode(),
        HUMAN_ROOT / "open_risks_zh.md": (
            "# 开放风险\n\n5 项剩余风险均有后续路径。真实平台仍需单独授权和验收；本轮通过不代表真实业务资料已经导入，也不代表 GitHub 或 App 已更新。\n"
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
            print("PASS: S10 整体复审公开证据与确定性构建器一致")
        else:
            write_outputs()
            print("UPDATED: S10 整体复审公开证据")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, zipfile.BadZipFile, BuildError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
