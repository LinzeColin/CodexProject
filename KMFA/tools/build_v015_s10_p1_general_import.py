#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S10-P1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s10_p1_general_import as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "eb79ca67847c3bffe8749883840a286280b8dff0"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s09_stage_review_regression",
    "deterministic_evidence",
    "pre_final_phase_checker",
    "s09_stage_review_dependency",
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

OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / kernel.RUN_PHASE_ID
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
MANIFEST_PATH = MACHINE_ROOT / "s10_p1_general_import_manifest.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
FORMAT_MATRIX_PATH = MACHINE_ROOT / "format_matrix_public_safe.json"
PREVIEW_CONTRACT_PATH = MACHINE_ROOT / "import_preview_contract_public_safe.json"
RECOVERY_VERIFICATION_PATH = MACHINE_ROOT / "recovery_verification_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

POLICY_PATH = PROJECT_ROOT / "metadata" / "imports" / "v015_s10_p1_general_import_policy_public_safe.json"
PREVIEW_PROTOCOL_PATH = PROJECT_ROOT / "metadata" / "protocol" / "v015_s10_p1_import_preview_protocol_public_safe.json"
RESUME_PROTOCOL_PATH = PROJECT_ROOT / "metadata" / "protocol" / "v015_s10_p1_import_resume_protocol_public_safe.json"

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
PREVIEW_EXAMPLE_PATH = HUMAN_ROOT / "import_preview_example_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_MANIFEST_PATH = (
    PROJECT_ROOT
    / "stage_artifacts"
    / "V015_S09_STAGE_REVIEW"
    / "machine"
    / "s09_stage_review_manifest.json"
)
DEPENDENCY_RECEIPTS_PATH = (
    PROJECT_ROOT
    / "stage_artifacts"
    / "V015_S09_STAGE_REVIEW"
    / "machine"
    / "validation_results.jsonl"
)


class BuildError(RuntimeError):
    pass


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    manifest = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    receipts = [
        json.loads(line)
        for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    expected = {
        "run_phase_id": "V015_S09_STAGE_REVIEW",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "decision": "GO_TO_S10_P1_ONLY",
        "s09_stage_review_performed": True,
        "s09_stage_review_acceptance_status": "PASSED",
        "s10_p1_entry_allowed": True,
        "s10_p1_started": False,
        "validation_receipt_count": 21,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S09 review dependency mismatch: " + ", ".join(mismatches))
    if len(receipts) != 21 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
        raise BuildError("S09 review receipts are not exactly 21 PASS records")
    if {row.get("validation_head") for row in receipts} != {manifest.get("validation_head")}:
        raise BuildError("S09 review validation head mismatch")
    if {row.get("validation_run_id") for row in receipts} != {manifest.get("validation_run_id")}:
        raise BuildError("S09 review validation run mismatch")
    return {
        "acceptance_status": "PASSED",
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": len(receipts),
        "s10_p1_entry_allowed": True,
        "s10_p1_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [
        json.loads(line)
        for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S10-P1 validation receipt order mismatch")
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
        "schema_version": "kmfa.v015.s10p1.source_contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": "S10",
        "stage_name_zh": "文件型数据源适配与导入管线",
        "roadmap_phase_id": "S10-P1",
        "phase_name_zh": "通用导入",
        "task_count": 3,
        "task_ids": ["S10P1T01", "S10P1T02", "S10P1T03"],
        "scope": ["安全登记与隔离", "导入预览与明确确认", "幂等与断点恢复"],
        "excluded": ["S10-P2 来源适配", "S10-P3 自动接入预留", "S10 Stage Review", "GitHub 上传", "App 重装"],
    }


def _format_matrix() -> dict[str, Any]:
    rows = []
    extensions = {
        "ZIP": [".zip"],
        "EXCEL_XLSX": [".xlsx"],
        "EXCEL_XLS": [".xls"],
        "CSV": [".csv"],
        "PDF": [".pdf"],
        "WPS_OLE": [".wps", ".et", ".dps"],
    }
    for code in kernel.FORMAT_LABELS_ZH:
        rows.append(
            {
                "format_code": code,
                "label_zh": kernel.FORMAT_LABELS_ZH[code],
                "extensions": extensions[code],
                "guidance_zh": kernel.FORMAT_GUIDANCE_ZH[code],
                "read_only_inspection": True,
                "confirmation_required_before_processing": True,
            }
        )
    return {
        "schema_version": "kmfa.v015.s10p1.format_matrix.v1",
        "format_category_count": len(rows),
        "extension_count": sum(len(row["extensions"]) for row in rows),
        "formats": rows,
        "archive_rejections": [
            "path traversal",
            "absolute path",
            "symbolic link",
            "special file",
            "encryption",
            "compression bomb",
            "size or count limit",
            "corruption",
        ],
    }


def _preview_protocol() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s10p1.import_preview_protocol.v1",
        "preview_schema": kernel.PREVIEW_SCHEMA,
        "confirmation_schema": kernel.CONFIRMATION_SCHEMA,
        "human_visible_fields": list(kernel.REQUIRED_PREVIEW_FIELDS),
        "source_identity_fields": ["source_id", "file_id", "import_run_id", "file_hash", "period", "parser_version"],
        "confirmation_binding": ["preview_id", "preview_fingerprint", "decision", "operator_role", "occurred_at"],
        "processing_before_confirmation_allowed": False,
        "preview_mutates_source": False,
        "preview_writes_raw": False,
        "changed_source_requires_new_preview": True,
        "missing_context_fails_closed": True,
    }


def _resume_protocol() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s10p1.import_resume_protocol.v1",
        "idempotency_key_fields": ["source_id", "file_hash", "period", "parser_version"],
        "checkpoint_states": ["STAGED_NOT_VISIBLE", "OBJECT_NOT_VISIBLE", "COMMITTED_VISIBLE"],
        "visibility_point": "atomic committed_index replacement",
        "content_addressed_objects": True,
        "exact_replay_reuses_record": True,
        "parser_version_change_may_coexist": True,
        "partial_commit_visible": False,
        "corrupt_committed_object_fails_closed": True,
        "source_mutation_allowed": False,
        "raw_write_allowed": False,
    }


def _task_matrix(final: bool) -> dict[str, Any]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    result = "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION"
    tasks = [
        {
            "task_id": "S10P1T01",
            "name_zh": "安全登记 ZIP、Excel、CSV、WPS/OLE 与 PDF",
            "acceptance_zh": "坏文件独立隔离；路径穿越和压缩炸弹在解压前拒绝。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(FORMAT_MATRIX_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S10P1T02",
            "name_zh": "生成导入预览并等待明确确认",
            "acceptance_zh": "预览显示文件、期间、来源、主体、板块与识别结果；确认前不处理。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(PREVIEW_CONTRACT_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S10P1T03",
            "name_zh": "幂等处理与断点恢复",
            "acceptance_zh": "同一登记不重复入账；中断后安全续跑；部分提交始终不可见。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(RECOVERY_VERIFICATION_PATH.relative_to(REPO_ROOT))],
        },
    ]
    return {
        "schema_version": "kmfa.v015.s10p1.task_acceptance_matrix.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "task_count": 3,
        "task_accepted_count": 3 if final else 0,
        "phase_acceptance_status": status,
        "tasks": tasks,
    }


def _manifest(final: bool, rows: list[dict[str, Any]], run_id: str | None, head: str | None, verification: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s10p1.general_import_manifest.v1",
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
        "overall_accepted_phase_count": 26 if final else 25,
        "overall_taskpack_phase_count": 72,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 33,
        "decision": "CONTINUE_TO_S10_P2_ONLY" if final else "REMAIN_IN_S10_P1_FINAL_VALIDATION",
        "supported_format_category_count": verification["supported_format_category_count"],
        "supported_extension_count": verification["supported_extension_count"],
        "preview_required_field_count": verification["preview_required_field_count"],
        "live_check_accounting": verification["accounting"],
        "bad_file_isolation_validated": True,
        "archive_path_traversal_rejected": True,
        "archive_compression_bomb_rejected": True,
        "confirmation_required_before_processing": True,
        "idempotent_replay_validated": True,
        "interruption_resume_validated": True,
        "partial_commit_visible": False,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "s10_p1_started": True,
        "s10_p1_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s10_p2_entry_allowed": final,
        "s10_p2_started": False,
        "s10_p3_entry_allowed": False,
        "s10_stage_review_entry_allowed": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "validation_receipt_count": len(rows),
        "validation_run_id": run_id,
        "validation_head": head,
    }


def _human_files(final: bool, verification: dict[str, Any]) -> dict[Path, str]:
    status = "已通过最终验收" if final else "实现完成，等待最终验收"
    test_status = "全部通过" if final else "32 项能力自检已通过，最终收据待生成"
    return {
        IMPLEMENTATION_REPORT_PATH: "\n".join(
            [
                "# S10-P1 通用文件导入实现说明",
                "",
                f"状态：{status}。",
                "",
                "这次完成的是文件进入 KMFA 前的安全入口：先识别并检查文件，再把期间、来源、主体和板块展示给人确认；只有明确确认后才进入处理。",
                "",
                "- 支持 ZIP、Excel、CSV、PDF 和 WPS/OLE，共 6 类、8 个扩展名。",
                "- 单个坏文件只会被隔离，不会拖垮同批其他文件。",
                "- 路径穿越、符号链接、压缩炸弹、损坏压缩包会在解压前拒绝。",
                "- 重复导入复用同一登记；中断产生的半成品不会被用户看到，可安全续跑。",
                "- 本轮只使用临时模拟文件，没有访问原始财务资料。",
            ]
        ) + "\n",
        PREVIEW_EXAMPLE_PATH: "\n".join(
            [
                "# 导入预览示例",
                "",
                "在真正处理前，用户会看到：文件名、期间、来源、主体、业务板块、识别结果和格式提示。",
                "",
                "系统默认显示“等待确认”，不会因打开预览而修改源文件或写入 raw。任何字段缺失、预览被改写或文件在预览后变化，都必须重新确认。",
            ]
        ) + "\n",
        TEST_RESULTS_PATH: "\n".join(
            [
                "# S10-P1 测试结果",
                "",
                f"状态：{test_status}。",
                "",
                f"- 能力自检：{verification['accounting']['passed']}/{verification['accounting']['total']} 通过。",
                "- 格式、危险压缩包、坏文件隔离、确认门禁、文件变化、重复导入、中断恢复和不可见半提交均已覆盖。",
                "- 原始资料访问次数：0；业务执行次数：0。",
            ]
        ) + "\n",
        RISKS_ROLLBACK_PATH: "\n".join(
            [
                "# 风险与回滚",
                "",
                "- 当前阶段只负责安全登记与提交，不负责理解各来源的业务字段；来源适配留到 S10-P2。",
                "- WPS/OLE 与旧版 Excel 当前只完成容器识别，不在本阶段猜测表内字段。",
                "- 默认压缩包阈值是安全上限；如未来调整，必须重跑压缩炸弹和大文件回归测试。",
                "- 回滚只删除本阶段代码、测试、公开证据和私有派生导入目录；绝不删除或修改源文件。",
            ]
        ) + "\n",
    }


def expected_outputs() -> dict[Path, str]:
    dependency()
    rows = receipts()
    final, run_id, head = final_binding(rows)
    verification = kernel.public_verification()
    if verification["accounting"]["failed"]:
        raise BuildError("S10-P1 public verification failed")
    task_matrix = _task_matrix(final)
    outputs = {
        POLICY_PATH: _json(
            {
                "schema_version": "kmfa.v015.s10p1.general_import_policy.v1",
                "run_phase_id": kernel.RUN_PHASE_ID,
                "supported_extensions": list(kernel.SUPPORTED_EXTENSIONS),
                "archive_policy": {
                    "max_member_count": kernel.DEFAULT_ARCHIVE_POLICY.max_member_count,
                    "max_total_uncompressed_bytes": kernel.DEFAULT_ARCHIVE_POLICY.max_total_uncompressed_bytes,
                    "max_member_uncompressed_bytes": kernel.DEFAULT_ARCHIVE_POLICY.max_member_uncompressed_bytes,
                    "max_compression_ratio": kernel.DEFAULT_ARCHIVE_POLICY.max_compression_ratio,
                    "max_path_depth": kernel.DEFAULT_ARCHIVE_POLICY.max_path_depth,
                    "max_member_name_bytes": kernel.DEFAULT_ARCHIVE_POLICY.max_member_name_bytes,
                },
                "bad_file_isolated": True,
                "source_read_only": True,
                "private_derived_storage_only": True,
            }
        ),
        PREVIEW_PROTOCOL_PATH: _json(_preview_protocol()),
        RESUME_PROTOCOL_PATH: _json(_resume_protocol()),
        SOURCE_CONTRACT_PATH: _json(_source_contract()),
        FORMAT_MATRIX_PATH: _json(_format_matrix()),
        PREVIEW_CONTRACT_PATH: _json(_preview_protocol()),
        RECOVERY_VERIFICATION_PATH: _json(verification),
        TASK_MATRIX_PATH: _json(task_matrix),
        MANIFEST_PATH: _json(_manifest(final, rows, run_id, head, verification)),
    }
    outputs.update(_human_files(final, verification))
    return outputs


def write_outputs() -> None:
    for path, content in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    VALIDATION_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not VALIDATION_RESULTS_PATH.exists():
        VALIDATION_RESULTS_PATH.touch()


def check_outputs() -> None:
    mismatches = []
    for path, content in expected_outputs().items():
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            mismatches.append(str(path.relative_to(REPO_ROOT)))
    if mismatches:
        raise BuildError("deterministic output drift: " + ", ".join(mismatches))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S10-P1 deterministic public-safe evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
