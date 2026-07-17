#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S04-P3."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

from KMFA.tools import v015_s04_p3_audit_recovery as kernel


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
OUTPUT_ROOT_RELATIVE = Path("stage_artifacts/V015_S04_P3_AUDIT_RECOVERY")
OUTPUT_ROOT = PROJECT_ROOT / OUTPUT_ROOT_RELATIVE
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
MANIFEST_PATH = MACHINE_ROOT / "s04_p3_audit_recovery_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _jsonl_bytes(values: Iterable[Mapping[str, Any]]) -> bytes:
    return b"".join(
        (json.dumps(dict(value), ensure_ascii=False, sort_keys=True) + "\n").encode()
        for value in values
    )


def _ref(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def event_protocol() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s04p3.event_protocol.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "required_action_types": list(kernel.ACTION_TYPES),
        "required_action_type_count": len(kernel.ACTION_TYPES),
        "append_only_required": True,
        "in_place_update_allowed": False,
        "correction_requires_new_event": True,
        "correction_target_must_precede_correction": True,
        "chain_digest_algorithm": "SHA-256",
        "event_chain_break_action": "BLOCK_PUBLICATION",
        "public_projection_uses_opaque_refs_only": True,
        "raw_root_access_required": False,
    }


def snapshot_protocol() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s04p3.snapshot_recovery_protocol.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "critical_snapshot_subject_types": list(kernel.SNAPSHOT_SUBJECT_TYPES),
        "critical_snapshot_subject_type_count": len(kernel.SNAPSHOT_SUBJECT_TYPES),
        "restore_allowed_approval_statuses": ["APPROVED"],
        "restore_validation_dimensions": list(kernel.RESTORE_VALIDATION_DIMENSIONS),
        "restore_validation_dimension_count": len(kernel.RESTORE_VALIDATION_DIMENSIONS),
        "digest_or_dependency_mismatch_action": "FAIL_RESTORE",
        "draft_restore_allowed": False,
        "production_restore_authorized": False,
        "raw_root_access_required": False,
    }


def health_protocol() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s04p3.metadata_health_protocol.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "required_finding_types": list(kernel.HEALTH_FINDING_TYPES),
        "required_finding_type_count": len(kernel.HEALTH_FINDING_TYPES),
        "every_finding_requires_repair_path": True,
        "critical_broken_link_action": "BLOCK_PUBLICATION",
        "repair_execution_in_phase": False,
        "periodic_inspection_report_required": True,
        "formal_report_gate_independent": True,
        "raw_root_access_required": False,
    }


def append_only_verification() -> dict[str, Any]:
    events = kernel.synthetic_event_log()
    summary = kernel.validate_event_chain(events)
    tampered = copy.deepcopy(events)
    tampered[2]["payload_ref"] = "PAYLOAD::SYNTHETIC-TAMPER"
    tamper_blocked = False
    try:
        kernel.validate_event_chain(tampered)
    except kernel.AuditRecoveryError:
        tamper_blocked = True
    replacement_blocked = False
    try:
        kernel.AppendOnlyEventLog().replace_event("EVENT::SYNTHETIC", {})
    except kernel.AuditRecoveryError:
        replacement_blocked = True
    return {
        "schema_version": "kmfa.v015.s04p3.append_only_verification.v1",
        **summary,
        "events": events,
        "tamper_blocked": tamper_blocked,
        "in_place_replacement_blocked": replacement_blocked,
        "all_required_actions_covered": set(summary["action_types_covered"]) == set(kernel.ACTION_TYPES),
        "event_chain_break_publication_allowed": False,
        "production_event_write_performed": False,
        "raw_root_access_count": 0,
    }


def recovery_verification() -> dict[str, Any]:
    drill = kernel.run_synthetic_recovery_drill()
    registry = kernel.synthetic_snapshot_registry()
    draft = next(row for row in registry["snapshots"] if row["approval_status"] == "DRAFT")
    draft_restore_blocked = False
    try:
        kernel.restore_snapshot(
            draft,
            payload=registry["payloads"][draft["snapshot_id"]],
            expected_version_ref=draft["version_ref"],
            available_version_refs=draft["dependency_version_refs"],
        )
    except kernel.AuditRecoveryError:
        draft_restore_blocked = True
    mismatch_restore_blocked = False
    approved = next(row for row in registry["snapshots"] if row["approval_status"] == "APPROVED")
    try:
        kernel.restore_snapshot(
            approved,
            payload={"synthetic_ref": "PAYLOAD::TAMPER"},
            expected_version_ref=approved["version_ref"],
            available_version_refs=approved["dependency_version_refs"],
        )
    except kernel.AuditRecoveryError:
        mismatch_restore_blocked = True
    return {
        "schema_version": "kmfa.v015.s04p3.recovery_verification.v1",
        **drill,
        "draft_restore_blocked": draft_restore_blocked,
        "mismatch_restore_blocked": mismatch_restore_blocked,
        "production_snapshot_created": False,
        "raw_root_access_count": 0,
    }


def health_verification() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s04p3.health_verification.v1",
        **kernel.synthetic_health_verification(),
    }


def task_matrix(*, accepted: bool) -> list[dict[str, Any]]:
    return [
        {
            "task_id": "S04P3T01",
            "name": "建立追加式事件日志",
            "execution_status": "EXECUTION_COMPLETE",
            "acceptance_status": "PASSED" if accepted else "PENDING_FINAL_VALIDATION",
            "evidence_refs": [
                _ref(PROJECT_ROOT / "metadata/audit/v015_s04_p3_event_protocol_public_safe.json"),
                _ref(MACHINE_ROOT / "append_only_event_verification_public_safe.json"),
            ],
        },
        {
            "task_id": "S04P3T02",
            "name": "建立快照与恢复",
            "execution_status": "EXECUTION_COMPLETE",
            "acceptance_status": "PASSED" if accepted else "PENDING_FINAL_VALIDATION",
            "evidence_refs": [
                _ref(PROJECT_ROOT / "metadata/audit/v015_s04_p3_snapshot_recovery_protocol_public_safe.json"),
                _ref(MACHINE_ROOT / "snapshot_recovery_drill_public_safe.json"),
            ],
        },
        {
            "task_id": "S04P3T03",
            "name": "建立元数据健康检查",
            "execution_status": "EXECUTION_COMPLETE",
            "acceptance_status": "PASSED" if accepted else "PENDING_FINAL_VALIDATION",
            "evidence_refs": [
                _ref(PROJECT_ROOT / "metadata/audit/v015_s04_p3_metadata_health_protocol_public_safe.json"),
                _ref(MACHINE_ROOT / "metadata_health_inspection_public_safe.json"),
            ],
        },
    ]


def manifest(*, final_validation: bool, receipts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    receipts = receipts or []
    passed = bool(final_validation and receipts and all(row.get("status") == "PASS" for row in receipts))
    validation_head = receipts[0].get("validation_head") if passed else None
    validation_run_id = receipts[0].get("validation_run_id") if passed else None
    if passed and any(row.get("validation_head") != validation_head for row in receipts):
        raise ValueError("validation receipts do not share one validation_head")
    if passed and any(row.get("validation_run_id") != validation_run_id for row in receipts):
        raise ValueError("validation receipts do not share one validation_run_id")
    event_summary = kernel.validate_event_chain(kernel.synthetic_event_log())
    recovery = kernel.run_synthetic_recovery_drill()
    health = kernel.synthetic_health_verification()
    return {
        "schema_version": "kmfa.v015.s04p3.audit_recovery_manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S04",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": "S04-P3",
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "version": kernel.VERSION,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if passed else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if passed else "PENDING",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 100,
        "phase_task_count": 3,
        "task_execution_complete_count": 3,
        "task_accepted_count": 3 if passed else 0,
        "required_action_type_count": len(kernel.ACTION_TYPES),
        "synthetic_event_count": event_summary["event_count"],
        "correction_event_count": event_summary["correction_event_count"],
        "event_chain_valid": event_summary["chain_valid"],
        "critical_snapshot_subject_type_count": len(kernel.SNAPSHOT_SUBJECT_TYPES),
        "approved_snapshot_recovery_case_count": recovery["approved_snapshot_recovery_case_count"],
        "restore_validation_dimension_count": len(kernel.RESTORE_VALIDATION_DIMENSIONS),
        "required_health_finding_type_count": len(kernel.HEALTH_FINDING_TYPES),
        "healthy_metadata_finding_count": health["healthy_case"]["finding_count"],
        "faulty_fixture_finding_type_count": health["faulty_case"]["finding_type_count"],
        "critical_break_blocks_publication": health["critical_break_blocks_publication"],
        "actual_business_lineage_record_count": 0,
        "production_event_write_performed": False,
        "production_restore_performed": False,
        "production_metadata_repair_performed": False,
        "formal_report_allowed": False,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "decision": "CONTINUE_TO_S04_STAGE_REVIEW_ONLY" if passed else "REMAIN_IN_S04_P3",
        "s04_p1_acceptance_status": "PASSED",
        "s04_p2_acceptance_status": "PASSED",
        "s04_p3_started": True,
        "s04_p3_acceptance_status": "PASSED" if passed else "PENDING_FINAL_VALIDATION",
        "s04_stage_review_entry_allowed": bool(passed),
        "s04_stage_review_started": False,
        "s04_stage_review_performed": False,
        "s05_entry_allowed": False,
        "validation_run_id": validation_run_id,
        "validation_head": validation_head,
        "validation_receipt_count": len(receipts) if passed else 0,
        "validation_pass_count": len(receipts) if passed else 0,
        "validation_failed_count": 0,
        "evidence_refs": [
            _ref(MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"),
            _ref(MACHINE_ROOT / "append_only_event_verification_public_safe.json"),
            _ref(MACHINE_ROOT / "snapshot_recovery_drill_public_safe.json"),
            _ref(MACHINE_ROOT / "metadata_health_inspection_public_safe.json"),
            _ref(VALIDATION_RESULTS_PATH),
        ],
    }


def expected_static_outputs() -> dict[Path, bytes]:
    return {
        PROJECT_ROOT / "metadata/audit/v015_s04_p3_event_protocol_public_safe.json": _json_bytes(event_protocol()),
        PROJECT_ROOT / "metadata/audit/v015_s04_p3_snapshot_recovery_protocol_public_safe.json": _json_bytes(snapshot_protocol()),
        PROJECT_ROOT / "metadata/audit/v015_s04_p3_metadata_health_protocol_public_safe.json": _json_bytes(health_protocol()),
        MACHINE_ROOT / "append_only_event_verification_public_safe.json": _json_bytes(append_only_verification()),
        MACHINE_ROOT / "snapshot_recovery_drill_public_safe.json": _json_bytes(recovery_verification()),
        MACHINE_ROOT / "metadata_health_inspection_public_safe.json": _json_bytes(health_verification()),
        HUMAN_ROOT / "completion_record_zh.md": (
            "# v1.5 S04-P3 审计与恢复完成记录\n\n"
            "- 建立六类操作的追加式事件链；禁止原位改写，更正只能追加 correction event，链断裂即阻断发布。\n"
            "- 建立关键事实与已发布报告的不可变快照；三个已批准 synthetic 版本全部恢复并通过摘要、版本、依赖三维校验。\n"
            "- 建立元数据健康检查；正常夹具 0 finding，故障夹具覆盖孤立、断链、重复版本、未闭合事件四类并提供修复路径。\n"
            "- 本 Phase 未执行生产事件写入、真实恢复或元数据修复，未访问 raw inbox；正式报告仍关闭。\n"
            "- S04 Stage review、S05、GitHub、App 和业务执行均未在本 Run 启动。\n"
        ).encode(),
        HUMAN_ROOT / "test_results_zh.md": (
            "# 测试结果\n\n"
            "最终结果以 `machine/validation_results.jsonl` 与 strict checker 为准；覆盖追加性、更正事件、链篡改拒绝、"
            "批准版本恢复、草稿/摘要/依赖失败、四类健康 finding 与关键断链发布阻断。\n"
        ).encode(),
        HUMAN_ROOT / "rollback_plan_zh.md": (
            "# 回滚方案\n\n"
            "仅回滚本 Phase 新增的 audit metadata、工具、测试、证据和对应治理登记；"
            "不得触碰 raw inbox、S04-P1/P2 证据、已安装 App 或远端分支。\n"
        ).encode(),
        HUMAN_ROOT / "open_risks_zh.md": (
            "# 未解决风险\n\n"
            "- `S04P3-RISK-001`：本 Phase 只完成 public-safe synthetic 恢复演练，未证明生产私有快照已存在或完成灾难恢复。\n"
            "- `S04P3-RISK-002`：真实业务血缘记录仍为 0；即使 metadata 健康门通过，也不得据此生成正式经营报告。\n"
        ).encode(),
    }


def write_outputs(*, final_validation: bool = False, receipts: list[dict[str, Any]] | None = None) -> None:
    outputs = expected_static_outputs()
    outputs[TASK_MATRIX_PATH] = _json_bytes(task_matrix(accepted=bool(final_validation and receipts)))
    outputs[MANIFEST_PATH] = _json_bytes(manifest(final_validation=final_validation, receipts=receipts))
    outputs[VALIDATION_RESULTS_PATH] = _jsonl_bytes(receipts or [])
    for path, payload in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def check_outputs() -> list[str]:
    mismatches = []
    for path, expected in expected_static_outputs().items():
        if not path.is_file() or path.read_bytes() != expected:
            mismatches.append(_ref(path))
    for path in (MANIFEST_PATH, VALIDATION_RESULTS_PATH, TASK_MATRIX_PATH):
        if not path.is_file():
            mismatches.append(_ref(path))
    if MANIFEST_PATH.is_file() and TASK_MATRIX_PATH.is_file():
        try:
            current_manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            expected_matrix = _json_bytes(
                task_matrix(accepted=current_manifest.get("phase_acceptance_status") == "PASSED")
            )
            if TASK_MATRIX_PATH.read_bytes() != expected_matrix:
                mismatches.append(_ref(TASK_MATRIX_PATH))
        except (OSError, json.JSONDecodeError):
            mismatches.append(_ref(TASK_MATRIX_PATH))
    return mismatches


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
                raise ValueError("artifact drift: " + ", ".join(mismatches))
            print("PASS: S04-P3 public-safe artifacts match deterministic builder")
        else:
            write_outputs()
            print("UPDATED: S04-P3 public-safe artifacts")
    except (OSError, ValueError, kernel.AuditRecoveryError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
