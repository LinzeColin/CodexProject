#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S10-P2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s10_p2_source_adapters as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S10_P2_SOURCE_ADAPTERS"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"

TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
PHASE_BASE_COMMIT = "ba92bc0aac157be378a0ed25fc54bd09a17eb72d"

REGISTRY_PATH = PROJECT_ROOT / "metadata/schema_maps/v015_s10_p2_source_adapter_registry_public_safe.json"
MAPPING_POLICY_PATH = PROJECT_ROOT / "metadata/schema_maps/v015_s10_p2_mapping_version_policy_public_safe.json"
HIERARCHY_POLICY_PATH = PROJECT_ROOT / "metadata/sources/v015_s10_p2_source_hierarchy_policy_public_safe.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
ADAPTER_COVERAGE_PATH = MACHINE_ROOT / "adapter_coverage_matrix_public_safe.json"
MAPPING_CONTRACT_PATH = MACHINE_ROOT / "mapping_version_contract_public_safe.json"
HIERARCHY_VERIFICATION_PATH = MACHINE_ROOT / "source_hierarchy_verification_public_safe.json"
MANIFEST_PATH = MACHINE_ROOT / "s10_p2_source_adapters_manifest.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
ADAPTER_EXAMPLE_PATH = HUMAN_ROOT / "adapter_examples_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s10_p1_regression",
    "deterministic_evidence",
    "pre_final_phase_checker",
    "s10_p1_dependency",
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
    root = PROJECT_ROOT / "stage_artifacts/V015_S10_P1_GENERAL_IMPORT/machine"
    manifest = _json(root / "s10_p1_general_import_manifest.json")
    receipts = _jsonl(root / "validation_results.jsonl")
    expected = {
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "decision": "CONTINUE_TO_S10_P2_ONLY",
        "s10_p1_acceptance_status": "PASSED",
        "s10_p2_entry_allowed": True,
        "s10_p2_started": False,
        "validation_receipt_count": 19,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S10-P1 dependency mismatch: " + ", ".join(mismatches))
    if len(receipts) != 19 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
        raise BuildError("S10-P1 receipts are not exactly 19 PASS records")
    if {row.get("validation_head") for row in receipts} != {manifest.get("validation_head")}:
        raise BuildError("S10-P1 validation head mismatch")
    if {row.get("validation_run_id") for row in receipts} != {manifest.get("validation_run_id")}:
        raise BuildError("S10-P1 validation run mismatch")
    return {
        "acceptance_status": "PASSED",
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": 19,
        "final_evidence_commit": PHASE_BASE_COMMIT,
        "s10_p2_entry_allowed": True,
        "s10_p2_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    rows = _jsonl(VALIDATION_RESULTS_PATH)
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S10-P2 validation receipt order mismatch")
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
        "schema_version": "kmfa.v015.s10p2.source_contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": "S10",
        "stage_name_zh": "文件型数据源适配与导入管线",
        "roadmap_phase_id": "S10-P2",
        "phase_name_zh": "来源适配",
        "task_count": 3,
        "task_ids": ["S10P2T01", "S10P2T02", "S10P2T03"],
        "scope": ["红圈四类文件导出", "金蝶四类可配置模板", "WPS、银行、税票和合同台账多层级适配"],
        "excluded": ["自动登录", "实时连接器", "S10-P3 自动接入预留", "S10 Stage Review", "GitHub 上传", "App 重装"],
    }


def _adapter_coverage() -> dict[str, Any]:
    registry = kernel.template_registry_public_safe()
    return {
        "schema_version": "kmfa.v015.s10p2.adapter_coverage.v1",
        "source_system_count": registry["source_system_count"],
        "adapter_template_count": registry["adapter_template_count"],
        "mapping_versioned_template_count": registry["mapping_versioned_template_count"],
        "redcircle_template_count": kernel.TEMPLATE_COUNTS["REDCIRCLE"],
        "kingdee_template_count": kernel.TEMPLATE_COUNTS["KINGDEE"],
        "wps_template_count": kernel.TEMPLATE_COUNTS["WPS"],
        "auxiliary_template_count": 3,
        "source_systems": [
            {
                "source_system": system,
                "label_zh": kernel.SOURCE_SYSTEM_LABELS_ZH[system],
                "template_count": kernel.TEMPLATE_COUNTS[system],
                "template_ids": [row.template_id for row in kernel.TEMPLATES if row.source_system == system],
            }
            for system in kernel.SOURCE_SYSTEM_LABELS_ZH
        ],
        "automatic_login_allowed": False,
        "live_connector_call_allowed": False,
    }


def _hierarchy_verification(verification: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s10p2.hierarchy_verification.v1",
        "accounting": verification["accounting"],
        "checks": verification["checks"],
        "multi_sheet_supported": True,
        "multi_entity_supported": True,
        "multi_bank_supported": True,
        "multi_account_supported": True,
        "unknown_account_quarantined": True,
        "account_binding_mismatch_quarantined": True,
        "ambiguous_or_unknown_mapping_rejected": True,
        "raw_root_access_count": verification["raw_root_access_count"],
        "raw_business_content_read": verification["raw_business_content_read"],
        "source_mutation_performed": verification["source_mutation_performed"],
        "automatic_login_performed": verification["automatic_login_performed"],
        "live_connector_call_count": verification["live_connector_call_count"],
        "credential_read_count": verification["credential_read_count"],
    }


def _task_matrix(final: bool) -> dict[str, Any]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    result = "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION"
    return {
        "schema_version": "kmfa.v015.s10p2.task_acceptance_matrix.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "task_count": 3,
        "task_accepted_count": 3 if final else 0,
        "phase_acceptance_status": status,
        "tasks": [
            {
                "task_id": "S10P2T01",
                "name_zh": "适配红圈文件导出",
                "acceptance_zh": "经营、合同、回款、财务四类模板字段映射均有明确版本。",
                "status": status,
                "current_result": result,
                "evidence_refs": [str(ADAPTER_COVERAGE_PATH.relative_to(REPO_ROOT))],
            },
            {
                "task_id": "S10P2T02",
                "name_zh": "适配金蝶财务导出",
                "acceptance_zh": "余额、凭证、往来、报表模板可配置；未知版本不猜字段。",
                "status": status,
                "current_result": result,
                "evidence_refs": [str(MAPPING_CONTRACT_PATH.relative_to(REPO_ROOT))],
            },
            {
                "task_id": "S10P2T03",
                "name_zh": "适配 WPS、银行、税票和合同台账",
                "acceptance_zh": "多主体、多银行、多账户、多工作表保留完整来源层级和期间；账户不明即隔离。",
                "status": status,
                "current_result": result,
                "evidence_refs": [str(HIERARCHY_VERIFICATION_PATH.relative_to(REPO_ROOT))],
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
        "schema_version": "kmfa.v015.s10p2.source_adapters_manifest.v1",
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
        "overall_accepted_phase_count": 27 if final else 26,
        "overall_taskpack_phase_count": 72,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 67,
        "stage_phase_pass_count": 2 if final else 1,
        "stage_task_accepted_count": 6 if final else 3,
        "decision": "CONTINUE_TO_S10_P3_ONLY" if final else "REMAIN_IN_S10_P2_FINAL_VALIDATION",
        "source_system_count": verification["source_system_count"],
        "adapter_template_count": verification["adapter_template_count"],
        "redcircle_template_count": verification["redcircle_template_count"],
        "kingdee_template_count": verification["kingdee_template_count"],
        "wps_template_count": verification["wps_template_count"],
        "auxiliary_template_count": verification["auxiliary_template_count"],
        "mapping_versioned_template_count": verification["mapping_versioned_template_count"],
        "live_check_count": verification["accounting"]["total"],
        "live_check_failed_count": verification["accounting"]["failed"],
        "ambiguous_or_unknown_mapping_rejected": True,
        "unknown_account_quarantined": True,
        "source_hierarchy_complete": True,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "source_mutation_performed": False,
        "automatic_login_performed": False,
        "live_connector_call_count": 0,
        "credential_read_count": 0,
        "s10_p1_acceptance_status": "PASSED",
        "s10_p2_started": True,
        "s10_p2_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s10_p3_entry_allowed": final,
        "s10_p3_started": False,
        "s10_stage_review_entry_allowed": False,
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
        f"- 最终验收：{EXPECTED_VALIDATION_COUNT}/{EXPECTED_VALIDATION_COUNT} 通过；批次 `{run_id}`，绑定实现版本 `{head}`。\n"
        if final
        else f"- 最终验收：尚未生成 {EXPECTED_VALIDATION_COUNT} 条正式记录。\n"
    )
    return {
        IMPLEMENTATION_REPORT_PATH: (
            "# S10-P2 来源适配实现说明\n\n"
            f"状态：{state}。\n\n"
            "这次完成的是不同系统导出文件进入 KMFA 后的字段翻译层。系统不会根据相似词自行猜字段，而是要求明确选择来源模板和版本。\n\n"
            "- 红圈覆盖经营、合同、回款、财务四类导出。\n"
            "- 金蝶覆盖余额、凭证、往来、报表四类可配置模板。\n"
            "- WPS、银行、数电票和合同台账支持多工作表与多公司；银行账户必须先确认归属。\n"
            "- 本轮没有自动登录、没有连接真实平台、没有访问原始财务资料。\n"
        ),
        ADAPTER_EXAMPLE_PATH: (
            "# 来源适配示例\n\n"
            "1. 先选择“红圈-回款-1.0.0”或其他已登记模板。\n"
            "2. 系统检查必需表头，并保留公司、期间、工作表、银行和账户层级。\n"
            "3. 未登记列不会被猜测；未知模板、重复含义或缺少必需字段会隔离。\n"
            "4. 银行账户没有确认所属公司和银行时，只隔离该工作表，不影响其他工作表。\n"
        ),
        RISKS_ROLLBACK_PATH: (
            "# 风险与回退\n\n"
            "- 具体金蝶或红圈版本未知：新增明确模板版本，不改写旧版本，也不自动套用。\n"
            "- 同名表头含义不同：停止并要求选择正确模板，不以相似度猜测。\n"
            "- 公司、银行或账户归属不清：隔离对应工作表，待确认后重新导入。\n"
            "- 回退方式：撤回本阶段本地提交；S10-P1 已验收成果和原始文件不受影响。\n"
            "- 来源适配只处理文件；自动登录和实时连接留到后续独立阶段。\n"
        ),
        TEST_RESULTS_PATH: (
            "# S10-P2 测试结果\n\n"
            f"状态：{state}。\n\n"
            "- 能力自检：42/42 通过。\n"
            "- 覆盖15个模板、未知版本、歧义表头、缺失字段、多公司、多银行、多账户、多工作表和隔离恢复。\n"
            "- 原始资料访问、自动登录、真实平台连接、凭据读取和业务执行均为 0。\n"
            + validation_line
        ),
    }


def desired_files() -> dict[Path, str]:
    dependency()
    rows = receipts()
    final, run_id, head = final_binding(rows)
    verification = kernel.public_verification()
    if verification["accounting"]["failed"]:
        raise BuildError("S10-P2 public verification failed")
    objects = {
        REGISTRY_PATH: kernel.template_registry_public_safe(),
        MAPPING_POLICY_PATH: kernel.mapping_version_policy_public_safe(),
        HIERARCHY_POLICY_PATH: kernel.source_hierarchy_policy_public_safe(),
        SOURCE_CONTRACT_PATH: _source_contract(),
        ADAPTER_COVERAGE_PATH: _adapter_coverage(),
        MAPPING_CONTRACT_PATH: kernel.mapping_version_policy_public_safe(),
        HIERARCHY_VERIFICATION_PATH: _hierarchy_verification(verification),
        MANIFEST_PATH: _manifest(final, rows, run_id, head, verification),
        TASK_MATRIX_PATH: _task_matrix(final),
    }
    files = {path: json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n" for path, value in objects.items()}
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
            print("PASS: S10-P2 deterministic evidence")
        else:
            write_outputs()
            print("UPDATED")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
