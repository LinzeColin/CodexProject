#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S10-P3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s10_p3_automatic_ingestion_reserve as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S10_P3_AUTOMATIC_INGESTION_RESERVE"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"

TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
PHASE_BASE_COMMIT = "ca88fafa3fddc5ac3021fb187ee4f941dd56e148"

CONNECTOR_CONTRACT_PATH = PROJECT_ROOT / "metadata/integration/v015_s10_p3_read_only_connector_contract_public_safe.json"
SCHEDULE_POLICY_PATH = PROJECT_ROOT / "metadata/integration/v015_s10_p3_schedule_freshness_policy_public_safe.json"
ACTIVATION_GATE_PATH = PROJECT_ROOT / "metadata/integration/v015_s10_p3_activation_gate_public_safe.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
INTERFACE_VERIFICATION_PATH = MACHINE_ROOT / "connector_interface_verification_public_safe.json"
SCHEDULE_VERIFICATION_PATH = MACHINE_ROOT / "schedule_freshness_verification_public_safe.json"
ACTIVATION_MATRIX_PATH = MACHINE_ROOT / "activation_gate_matrix_public_safe.json"
MANIFEST_PATH = MACHINE_ROOT / "s10_p3_automatic_ingestion_reserve_manifest.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
CONNECTOR_FLOW_PATH = HUMAN_ROOT / "connector_flow_zh.md"
SCHEDULE_FRESHNESS_PATH = HUMAN_ROOT / "schedule_and_freshness_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s10_p2_regression",
    "deterministic_evidence",
    "pre_final_phase_checker",
    "s10_p2_dependency",
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
EXPECTED_VALIDATION_COUNT = len(EXPECTED_VALIDATION_NAMES)


class BuildError(RuntimeError):
    pass


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BuildError(f"JSON object required: {path}")
    return value


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise BuildError(f"JSONL object rows required: {path}")
    return rows


def dependency() -> dict[str, Any]:
    root = PROJECT_ROOT / "stage_artifacts/V015_S10_P2_SOURCE_ADAPTERS/machine"
    manifest = _json(root / "s10_p2_source_adapters_manifest.json")
    receipts = _jsonl(root / "validation_results.jsonl")
    expected = {
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "decision": "CONTINUE_TO_S10_P3_ONLY",
        "s10_p2_acceptance_status": "PASSED",
        "s10_p3_entry_allowed": True,
        "s10_p3_started": False,
        "validation_receipt_count": 19,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S10-P2 dependency mismatch: " + ", ".join(mismatches))
    if len(receipts) != 19 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
        raise BuildError("S10-P2 receipts are not exactly 19 PASS records")
    if {row.get("validation_head") for row in receipts} != {manifest.get("validation_head")}:
        raise BuildError("S10-P2 validation head mismatch")
    if {row.get("validation_run_id") for row in receipts} != {manifest.get("validation_run_id")}:
        raise BuildError("S10-P2 validation run mismatch")
    return {
        "acceptance_status": "PASSED",
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": 19,
        "final_evidence_commit": PHASE_BASE_COMMIT,
        "s10_p3_entry_allowed": True,
        "s10_p3_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    rows = _jsonl(VALIDATION_RESULTS_PATH)
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S10-P3 validation receipt order mismatch")
    return rows


def final_binding(rows: list[dict[str, Any]]) -> tuple[bool, str | None, str | None]:
    if not rows:
        return False, None, None
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    final = (
        len(rows) == EXPECTED_VALIDATION_COUNT
        and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in rows)
        and len(run_ids) == 1
        and len(heads) == 1
        and None not in run_ids
        and None not in heads
    )
    return final, next(iter(run_ids)) if final else None, next(iter(heads)) if final else None


def _source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s10p3.source_contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": "S10",
        "stage_name_zh": "文件型数据源适配与导入管线",
        "roadmap_phase_id": "S10-P3",
        "phase_name_zh": "自动接入预留",
        "task_count": 3,
        "task_ids": ["S10P3T01", "S10P3T02", "S10P3T03"],
        "scope": ["只读连接器接口合同", "调度与新鲜度规则", "五类来源独立启用门禁"],
        "excluded": ["真实平台连接", "明文凭据", "原始资料访问", "S10 Stage Review", "GitHub 上传", "App 重装"],
    }


def _interface_verification(verification: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s10p3.interface_verification.v1",
        "accounting": verification["accounting"],
        "checks": verification["checks"],
        "future_source_count": verification["future_source_count"],
        "connector_operation_count": verification["connector_operation_count"],
        "official_authorization_required": True,
        "read_only_scope_required": True,
        "plaintext_credential_storage_allowed": False,
        "hash_increment_idempotency_revoke_required": True,
        "live_connector_call_count": 0,
        "credential_read_count": 0,
        "source_mutation_performed": False,
    }


def _schedule_verification(verification: dict[str, Any]) -> dict[str, Any]:
    policy = kernel.schedule_policy_public_safe()
    return {
        "schema_version": "kmfa.v015.s10p3.schedule_verification.v1",
        "timezone": policy["timezone"],
        "schedule_frequency_count": verification["schedule_frequency_count"],
        "frequency_types": policy["frequency_types"],
        "retry_budget": verification["retry_budget"],
        "retry_delays_minutes": policy["retry_delays_minutes"],
        "no_data_retry_count": verification["no_data_retry_count"],
        "manual_import_available": True,
        "scheduled_failure_blocks_manual_import": False,
        "freshness_states": policy["freshness_states"],
    }


def _task_matrix(final: bool) -> dict[str, Any]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    result = "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION"
    return {
        "schema_version": "kmfa.v015.s10p3.task_acceptance_matrix.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "task_count": 3,
        "task_accepted_count": 3 if final else 0,
        "phase_acceptance_status": status,
        "tasks": [
            {
                "task_id": "S10P3T01",
                "name_zh": "定义只读连接器接口",
                "acceptance_zh": "未经官方授权不能连接；接口不接收或保存明文凭据。",
                "status": status,
                "current_result": result,
                "evidence_refs": [str(INTERFACE_VERIFICATION_PATH.relative_to(REPO_ROOT))],
            },
            {
                "task_id": "S10P3T02",
                "name_zh": "定义调度与新鲜度",
                "acceptance_zh": "无数据视为检查完成，不无限重试；调度失败不影响手工导入。",
                "status": status,
                "current_result": result,
                "evidence_refs": [str(SCHEDULE_VERIFICATION_PATH.relative_to(REPO_ROOT))],
            },
            {
                "task_id": "S10P3T03",
                "name_zh": "定义后期接入门禁",
                "acceptance_zh": "红圈、金蝶、WPS、银行、税务逐个验收；安全评审前均不启用。",
                "status": status,
                "current_result": result,
                "evidence_refs": [str(ACTIVATION_MATRIX_PATH.relative_to(REPO_ROOT))],
            },
        ],
    }


def _manifest(
    final: bool,
    rows: list[dict[str, Any]],
    run_id: str | None,
    head: str | None,
    verification: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s10p3.automatic_ingestion_reserve_manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "version": kernel.VERSION,
        "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "phase_base_commit": PHASE_BASE_COMMIT,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 28 if final else 27,
        "overall_taskpack_phase_count": 72,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 100,
        "stage_phase_pass_count": 3 if final else 2,
        "stage_task_accepted_count": 9 if final else 6,
        "decision": "CONTINUE_TO_S10_STAGE_REVIEW_ONLY" if final else "REMAIN_IN_S10_P3_FINAL_VALIDATION",
        "future_source_count": verification["future_source_count"],
        "connector_operation_count": verification["connector_operation_count"],
        "schedule_frequency_count": verification["schedule_frequency_count"],
        "retry_budget": verification["retry_budget"],
        "no_data_retry_count": verification["no_data_retry_count"],
        "activation_gate_count": verification["activation_gate_count"],
        "activation_criteria_count": verification["activation_criteria_count"],
        "automatic_connector_enabled_count": 0,
        "manual_import_available": True,
        "live_check_count": verification["accounting"]["total"],
        "live_check_failed_count": verification["accounting"]["failed"],
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "source_mutation_performed": False,
        "live_connector_call_count": 0,
        "credential_read_count": 0,
        "s10_p1_acceptance_status": "PASSED",
        "s10_p2_acceptance_status": "PASSED",
        "s10_p3_started": True,
        "s10_p3_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s10_stage_review_entry_allowed": final,
        "s10_stage_review_started": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "validation_run_id": run_id,
        "validation_head": head,
        "validation_receipt_count": len(rows) if final else 0,
        "validation_pass_count": len(rows) if final else 0,
        "validation_failed_count": 0,
    }


def _human_files(final: bool, run_id: str | None, head: str | None) -> dict[Path, str]:
    state = "已通过最终验收" if final else "已完成实现，等待最终验收"
    validation_line = (
        f"- 正式验收：{EXPECTED_VALIDATION_COUNT}/{EXPECTED_VALIDATION_COUNT} 通过；批次 `{run_id}`，绑定实现版本 `{head}`。\n"
        if final
        else f"- 正式验收：尚未生成 {EXPECTED_VALIDATION_COUNT} 条正式记录。\n"
    )
    return {
        IMPLEMENTATION_REPORT_PATH: (
            "# S10-P3 自动接入安全预留\n\n"
            f"状态：{state}。\n\n"
            "这一步没有连接任何真实平台，只是先把未来自动接入必须遵守的安全规则固定下来。\n\n"
            "- 红圈、金蝶、WPS、银行、税务都必须有正式授权，而且只能读取，不能回写。\n"
            "- 系统接口不接收或保存密码、令牌等明文凭据，只允许引用私有凭据库中的编号。\n"
            "- 无新数据算一次正常检查完成，不会无限重试；自动检查失败时仍可手工导入文件。\n"
            "- 五类来源必须逐个通过安全评审，任何一类通过都不会连带开启其他来源。\n"
            "- 当前自动连接数量为 0；本轮没有访问原始财务资料。\n"
        ),
        CONNECTOR_FLOW_PATH: (
            "# 未来只读连接流程\n\n"
            "1. 负责人提交该来源的正式授权，并限定为只读。\n"
            "2. 系统只保存授权编号和私有凭据库引用，不保存明文密码或令牌。\n"
            "3. 拉取前检查授权是否仍有效；撤销后立即停止。\n"
            "4. 每批内容先核对 hash，再按只增不减的游标处理；重复批次只记一次。\n"
            "5. 任一安全条件不满足就停止该来源，不影响文件导入。\n"
        ),
        SCHEDULE_FRESHNESS_PATH: (
            "# 自动检查与数据新鲜度\n\n"
            "- 不同来源可以按每日、每周或每月检查，统一使用 Australia/Sydney 时区。\n"
            "- 数据状态分为：新鲜、到期、过期、从未检查。\n"
            "- 临时故障最多重试 3 次，间隔 15、60、240 分钟；之后停止并保留手工导入。\n"
            "- 没有新数据时不重试，也不报成故障。\n"
        ),
        RISKS_ROLLBACK_PATH: (
            "# 风险与回退\n\n"
            "- 未获官方授权：不建立连接。\n"
            "- 只读范围无法证明：不启用。\n"
            "- 安全评审、撤销演练或来源字段映射未通过：只阻断该来源。\n"
            "- 调度故障：停止自动重试，继续允许手工文件导入。\n"
            "- 回退方式：撤回本阶段本地提交；S10-P1/P2 已验收的文件导入能力不受影响。\n"
        ),
        TEST_RESULTS_PATH: (
            "# S10-P3 测试结果\n\n"
            f"状态：{state}。\n\n"
            "- 安全规则自检：48/48 通过。\n"
            "- 已覆盖授权、只读、明文凭据拒绝、hash、增量、去重、撤销、调度、新鲜度、有限重试和五类独立门禁。\n"
            "- 真实平台连接、凭据读取、原始资料访问、来源回写和业务执行均为 0。\n"
            + validation_line
        ),
    }


def desired_files() -> dict[Path, str]:
    dependency()
    rows = receipts()
    final, run_id, head = final_binding(rows)
    verification = kernel.public_verification()
    if verification["accounting"]["failed"]:
        raise BuildError("S10-P3 public verification failed")
    objects = {
        CONNECTOR_CONTRACT_PATH: kernel.connector_contract_public_safe(),
        SCHEDULE_POLICY_PATH: kernel.schedule_policy_public_safe(),
        ACTIVATION_GATE_PATH: kernel.activation_matrix_public_safe(),
        SOURCE_CONTRACT_PATH: _source_contract(),
        INTERFACE_VERIFICATION_PATH: _interface_verification(verification),
        SCHEDULE_VERIFICATION_PATH: _schedule_verification(verification),
        ACTIVATION_MATRIX_PATH: kernel.activation_matrix_public_safe(),
        MANIFEST_PATH: _manifest(final, rows, run_id, head, verification),
        TASK_MATRIX_PATH: _task_matrix(final),
    }
    files = {
        path: json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        for path, value in objects.items()
    }
    files.update(_human_files(final, run_id, head))
    return files


def write_outputs() -> None:
    for path, content in desired_files().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    VALIDATION_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not VALIDATION_RESULTS_PATH.exists():
        VALIDATION_RESULTS_PATH.write_text("", encoding="utf-8")


def check_outputs() -> None:
    mismatches = []
    for path, expected in desired_files().items():
        actual = path.read_text(encoding="utf-8") if path.is_file() else None
        if actual != expected:
            mismatches.append(str(path.relative_to(REPO_ROOT)))
    if mismatches:
        raise BuildError("generated evidence drift: " + ", ".join(mismatches))
    _jsonl(VALIDATION_RESULTS_PATH)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            check_outputs()
            print("PASS: S10-P3 deterministic evidence")
        else:
            write_outputs()
            print("UPDATED")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
