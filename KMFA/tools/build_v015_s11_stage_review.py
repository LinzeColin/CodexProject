#!/usr/bin/env python3
"""Build public-safe evidence for the KMFA v1.5 S11 stage review."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s11_p1_quality_rules as quality
from KMFA.tools import v015_s11_p2_check_board_data_model as board
from KMFA.tools import v015_s11_p3_check_board_interface as interface
from KMFA.tools import v015_s11_stage_review_contract as contract


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S11_STAGE_REVIEW"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
MANIFEST_PATH = MACHINE_ROOT / "s11_stage_review_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

RUN_PHASE_ID = contract.RUN_PHASE_ID
TASK_ID = contract.TASK_ID
ACCEPTANCE_ID = contract.ACCEPTANCE_ID
VERSION = contract.VERSION
REVIEW_BASE_COMMIT = contract.REVIEW_BASE_COMMIT
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_contract_tests",
    "focused_review_tests",
    "focused_governance_tests",
    "s11_p1_dependency",
    "s11_p2_dependency",
    "s11_p3_dependency",
    "s11_p3_browser_regression",
    "s11_p1_kernel_regression",
    "s11_p2_kernel_regression",
    "s11_p3_kernel_regression",
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


def _csv_bytes(fieldnames: list[str], rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode()


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise BuildError(f"JSONL object rows required: {path}")
    return rows


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_contract() -> dict[str, Any]:
    manifest = json.loads((PROJECT_ROOT / "taskpack/v1_5/source_manifest.json").read_text(encoding="utf-8"))
    roadmap = json.loads((PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json").read_text(encoding="utf-8"))
    stage = next((row for row in roadmap.get("stages", []) if row.get("id") == "S11"), None)
    package = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    integrity = (
        package.is_file()
        and _sha256(package) == TASKPACK_SHA256
        and manifest.get("source_package_sha256") == TASKPACK_SHA256
        and (manifest.get("stage_count"), manifest.get("phase_count"), manifest.get("task_count")) == (24, 72, 216)
        and (stage or {}).get("name") == "数据质量、完整性与数据源检查板"
        and len((stage or {}).get("phases", [])) == 3
        and sum(len(row.get("tasks", [])) for row in (stage or {}).get("phases", [])) == 9
    )
    return {
        "schema_version": "kmfa.v015.s11.stage-review-source-contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": "S11",
        "stage_name_zh": "数据质量、完整性与数据源检查板",
        "stage_goal_zh": (stage or {}).get("goal"),
        "phase_count": 3,
        "task_count": 9,
        "review_overlay_counted_as_taskpack_phase": False,
        "review_overlay_counted_as_taskpack_task": False,
        "source_integrity_status": "PASS" if integrity else "FAIL",
        "excluded": ["S12", "真实资料", "真实上传或同步", "正式报告", "GitHub 上传", "App 重装", "业务执行"],
    }


def _predecessor_specs() -> list[dict[str, Any]]:
    return [
        {
            "roadmap_phase_id": "S11-P1",
            "run_phase_id": quality.RUN_PHASE_ID,
            "manifest": PROJECT_ROOT / "stage_artifacts/V015_S11_P1_QUALITY_RULES/machine/s11_p1_quality_rules_manifest.json",
            "receipts": PROJECT_ROOT / "stage_artifacts/V015_S11_P1_QUALITY_RULES/machine/validation_results.jsonl",
            "receipt_count": 19,
        },
        {
            "roadmap_phase_id": "S11-P2",
            "run_phase_id": board.RUN_PHASE_ID,
            "manifest": PROJECT_ROOT / "stage_artifacts/V015_S11_P2_CHECK_BOARD_DATA_MODEL/machine/s11_p2_check_board_data_model_manifest.json",
            "receipts": PROJECT_ROOT / "stage_artifacts/V015_S11_P2_CHECK_BOARD_DATA_MODEL/machine/validation_results.jsonl",
            "receipt_count": 19,
        },
        {
            "roadmap_phase_id": "S11-P3",
            "run_phase_id": interface.RUN_PHASE_ID,
            "manifest": PROJECT_ROOT / "stage_artifacts/V015_S11_P3_CHECK_BOARD_INTERFACE/machine/s11_p3_check_board_interface_manifest.json",
            "receipts": PROJECT_ROOT / "stage_artifacts/V015_S11_P3_CHECK_BOARD_INTERFACE/machine/validation_results.jsonl",
            "receipt_count": 20,
        },
    ]


def phase_evidence() -> dict[str, Any]:
    phases: list[dict[str, Any]] = []
    for spec in _predecessor_specs():
        manifest = json.loads(spec["manifest"].read_text(encoding="utf-8"))
        rows = _jsonl(spec["receipts"])
        expected = spec["receipt_count"]
        if (
            manifest.get("run_phase_id") != spec["run_phase_id"]
            or manifest.get("phase_acceptance_status") != "PASSED"
            or manifest.get("phase_task_accepted_count") != 3
            or manifest.get("validation_receipt_count") != expected
            or len(rows) != expected
            or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows)
            or {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}
            or {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")}
        ):
            raise BuildError(f"predecessor acceptance drift: {spec['roadmap_phase_id']}")
        if not re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("validation_head") or "")):
            raise BuildError(f"predecessor validation head invalid: {spec['roadmap_phase_id']}")
        phases.append({
            "roadmap_phase_id": spec["roadmap_phase_id"],
            "run_phase_id": spec["run_phase_id"],
            "acceptance_status": "PASSED",
            "task_count": 3,
            "task_accepted_count": 3,
            "validation_receipt_count": expected,
            "validation_run_id": manifest["validation_run_id"],
            "validation_head": manifest["validation_head"],
            "manifest_ref": str(spec["manifest"].relative_to(REPO_ROOT)),
        })
    return {
        "schema_version": "kmfa.v015.s11.stage-review-phase-evidence.v1",
        "accounting": {
            "phase_count": 3,
            "phase_passed_count": 3,
            "task_count": 9,
            "task_accepted_count": 9,
            "predecessor_receipt_count": sum(row["validation_receipt_count"] for row in phases),
        },
        "phases": phases,
    }


def cross_phase_contracts() -> dict[str, Any]:
    verification = contract.public_verification()
    checks = {row["check_id"]: row["status"] == "PASS" for row in verification["checks"]}
    p1 = quality.public_verification()
    p2 = board.public_verification()
    p3 = interface.public_verification()
    evidence = phase_evidence()
    quality_binding = contract.quality_contract_binding()
    reviewed = verification["reviewed_projection"]
    rows: list[dict[str, Any]] = []

    def add(contract_id: str, description_zh: str, condition: bool) -> None:
        rows.append({
            "contract_id": contract_id,
            "description_zh": description_zh,
            "status": "PASS" if condition else "FAIL",
            "blocking": True,
        })

    add("S11-X01", "三个部分均已通过验收", evidence["accounting"]["phase_passed_count"] == 3)
    add("S11-X02", "九项任务全部验收", evidence["accounting"]["task_accepted_count"] == 9)
    add("S11-X03", "58 条前序验收记录完整", evidence["accounting"]["predecessor_receipt_count"] == 58)
    add("S11-X04", "P1 公开检查全部通过", p1["accounting"] == {"total": 51, "passed": 51, "failed": 0})
    add("S11-X05", "P1 规则数量固定为 16", len(quality.default_rule_catalog()["rules"]) == 16)
    add("S11-X06", "P1 关键门禁数量固定为 7", sum(row["hard_gate"] for row in quality.default_rule_catalog()["rules"]) == 7)
    add("S11-X07", "P1 四种中文状态精确绑定", quality_binding["status_labels_zh"] == list(quality.STATUS_LABELS_ZH))
    add("S11-X08", "P1 关键门禁优先于评分", quality_binding["hard_gate_precedence"] is True)
    add("S11-X09", "P2 公开检查全部通过", p2["accounting"] == {"total": 83, "passed": 83, "failed": 0})
    add("S11-X10", "P2 六层结构保持完整", p2["model"]["hierarchy_contract"]["level_count"] == 6)
    add("S11-X11", "P2 六个末级检查项保持完整", p2["model"]["leaf_count"] == 6)
    add("S11-X12", "P2 状态只来自后端事实", p2["model"]["backend_fact_only"] is True)
    add("S11-X13", "P2 禁止前端改写状态", p2["model"]["frontend_status_mutation_allowed"] is False)
    add("S11-X14", "P3 公开检查全部通过", p3["accounting"] == {"total": 65, "passed": 65, "failed": 0})
    add("S11-X15", "P3 34 行与 6 个末级项复用 P2", (p3["payload"]["row_count"], p3["payload"]["leaf_count"]) == (34, 6))
    add("S11-X16", "P3 八类返回上下文完整", len(interface.CONTEXT_KEYS) == 8)
    add("S11-X17", "P3 视觉对比全部通过", p3["visual_contract"]["contrast_all_pass"] is True)
    add("S11-X18", "P3 没有大面积黄色或状态色", p3["visual_contract"]["large_yellow_surface_count"] == 0 and p3["visual_contract"]["large_status_color_surface_count"] == 0)
    add("S11-X19", "质量规则版本贯穿检查板与界面", checks.get("QUALITY_BINDING_VALID", False))
    add("S11-X20", "所有事实版本均进入处理绑定", checks.get("ALL_FACT_REVISIONS_BOUND", False))
    add("S11-X21", "所有状态指纹均进入处理绑定", checks.get("ALL_STATE_FINGERPRINTS_BOUND", False))
    add("S11-X22", "已导入资料绑定 P1 评估结果", checks.get("IMPORTED_EVALUATIONS_BOUND", False))
    add("S11-X23", "关键错误路由到修复而非普通确认", checks.get("HARD_GATE_ROUTES_REMEDIATION", False))
    add("S11-X24", "旧处理请求在资料更新后被拒绝", checks.get("STALE_ACTION_REJECTED", False))
    add("S11-X25", "错误处理入口被拒绝", checks.get("HARD_GATE_CONFIRMATION_REJECTED", False))
    add("S11-X26", "前端状态写入被拒绝", checks.get("FRONTEND_STATUS_WRITE_REJECTED", False))
    add("S11-X27", "状态仅在更高版本后端复查后更新", checks.get("BACKEND_RECHECK_CHANGES_STATUS", False) and checks.get("NON_INCREMENTAL_RECHECK_REJECTED", False))
    add("S11-X28", "复审证据不读取原始或真实来源", verification["raw_root_access_count"] == 0 and verification["live_source_read_count"] == 0)
    failed = sum(row["status"] != "PASS" for row in rows)
    return {
        "schema_version": "kmfa.v015.s11.cross-phase-contracts.v1",
        "accounting": {"total": len(rows), "passed": len(rows) - failed, "failed": failed, "blocking_failed": failed},
        "contracts": rows,
        "reviewed_projection_fingerprint": reviewed["projection_fingerprint"],
    }


def findings() -> list[dict[str, str]]:
    return [
        {
            "finding_id": "S11REV-F001",
            "severity": "HIGH",
            "finding_zh": "P1 质量规则版本未完整绑定到 P2/P3 处理请求。",
            "root_cause_zh": "各部分单独验收时只复用当前默认配置，没有形成跨部分口径指纹。",
            "fix_zh": "新增质量规则、状态和评分三类指纹及统一绑定，任何漂移均失败关闭。",
            "evidence_ref": "KMFA/stage_artifacts/V015_S11_STAGE_REVIEW/machine/reviewed_binding_sample_public_safe.json",
            "validation_ref": "KMFA/tests/test_v015_s11_stage_review_contract.py",
            "status": "FIXED_VALIDATED",
            "blocks_stage_acceptance": "false",
        },
        {
            "finding_id": "S11REV-F002",
            "severity": "HIGH",
            "finding_zh": "关键错误与普通需确认共用处理入口。",
            "root_cause_zh": "P3 只按中文状态粗略路由，未区分 P1 关键门禁和普通人工确认。",
            "fix_zh": "新增复审动作策略：关键失败只能进入修复，普通需确认才进入确认。",
            "evidence_ref": "KMFA/stage_artifacts/V015_S11_STAGE_REVIEW/machine/reviewed_action_policy_public_safe.json",
            "validation_ref": "KMFA/tests/test_v015_s11_stage_review_contract.py",
            "status": "FIXED_VALIDATED",
            "blocks_stage_acceptance": "false",
        },
        {
            "finding_id": "S11REV-F003",
            "severity": "HIGH",
            "finding_zh": "处理请求缺少单条资料版本绑定，旧请求可能在资料更新后重放。",
            "root_cause_zh": "P3 只绑定页面级状态摘要，没有同时绑定事实版本、事实指纹、节点指纹和质量评估。",
            "fix_zh": "请求精确绑定单条资料与全部指纹；版本或状态变化即拒绝，只有更高版本后端复查可更新状态。",
            "evidence_ref": "KMFA/stage_artifacts/V015_S11_STAGE_REVIEW/machine/cross_phase_verification_public_safe.json",
            "validation_ref": "KMFA/tests/test_v015_s11_stage_review_contract.py",
            "status": "FIXED_VALIDATED",
            "blocks_stage_acceptance": "false",
        },
    ]


def risks() -> list[dict[str, str]]:
    return [
        {"risk_id": "RISK-KMFA-V015-S11-001", "risk": "本轮只用公开模拟资料复审，没有处理真实财务文件。", "route": "LATER_AUTHORIZED_PRIVATE_VALIDATION", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s11_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S11-002", "risk": "真实上传、同步和确认仍需受控后端实现。", "route": "LATER_AUTHORIZED_BACKEND_ACTION_IMPLEMENTATION", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s11_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S11-003", "risk": "最终 App 接入时仍需使用原子版本比较拒绝并发旧请求。", "route": "FINAL_APP_INTEGRATION_COMPARE_AND_SWAP_GATE", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s11_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S11-004", "risk": "本地完整回归通过不等于远端 CI 已执行同一门禁。", "route": "FINAL_GITHUB_MAIN_UPLOAD_GATE", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s11_stage_acceptance": "false"},
        {"risk_id": "RISK-KMFA-V015-S11-005", "risk": "S12-P1 尚未开始。", "route": "S12P1_ONLY_NEXT_RUN", "status": "ROUTED_RESIDUAL", "plan_complete": "true", "blocks_s11_stage_acceptance": "false"},
    ]


def receipts() -> list[dict[str, Any]]:
    rows = _jsonl(VALIDATION_RESULTS_PATH)
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S11 review validation receipt order drift")
    return rows


def final_binding(rows: list[dict[str, Any]]) -> tuple[bool, str | None, str | None]:
    if not rows:
        return False, None, None
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    final = (
        len(rows) == len(EXPECTED_VALIDATION_NAMES)
        and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in rows)
        and len(run_ids) == 1
        and len(heads) == 1
        and None not in run_ids
        and None not in heads
    )
    return final, next(iter(run_ids)) if final else None, next(iter(heads)) if final else None


def manifest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    final, run_id, head = final_binding(rows)
    verification = contract.public_verification()
    return {
        "schema_version": "kmfa.v015.s11_stage_review.manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S11",
        "run_phase_id": RUN_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "review_base_commit": REVIEW_BASE_COMMIT,
        "counted_as_taskpack_phase": False,
        "counted_as_taskpack_task": False,
        "review_execution_status": "COMPLETED" if final else "EXECUTION_COMPLETE",
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "stage_lifecycle_status": "COMPLETED" if final else "IN_PROGRESS",
        "stage_acceptance_status": "PASSED" if final else "PENDING",
        "stage_execution_percentage": 100,
        "decision": "GO_TO_S12_P1_ONLY" if final else "REMAIN_IN_S11_STAGE_REVIEW",
        "phase_accounting": phase_evidence()["accounting"],
        "cross_phase_accounting": cross_phase_contracts()["accounting"],
        "live_check_accounting": verification["accounting"],
        "review_findings": {"total": 3, "fixed_validated": 3, "open": 0, "blocking_open": 0},
        "open_risks": {"total": 5, "routed": 5, "plan_gap_count": 0, "blocking": 0},
        "reviewed_action_kind_count": len(contract.REVIEW_ACTION_KINDS),
        "stale_action_rejection_count": 1,
        "overall_accepted_phase_count": 31,
        "overall_taskpack_phase_count": 72,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "s11_stage_review_started": True,
        "s11_stage_review_performed": final,
        "s11_stage_review_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s12_entry_allowed": final,
        "s12_p1_entry_allowed": final,
        "s12_p1_started": False,
        "s12_p2_plus_entry_allowed": False,
        "product_implementation_allowed": final,
        "validation_run_id": run_id,
        "validation_head": head,
        "validation_receipt_count": len(rows) if final else 0,
        "validation_pass_count": len(rows) if final else 0,
        "validation_failed_count": 0,
    }


def _human_outputs(final: bool) -> dict[Path, bytes]:
    status = "已通过最终验收" if final else "已完成复审与修复，等待最终验收"
    validation = "24/24 项正式验收通过。" if final else "24 项正式验收尚待执行。"
    return {
        HUMAN_ROOT / "stage11_review_report_zh.md": (
            "# KMFA v1.5 第 11 阶段整体复审\n\n"
            f"状态：{status}。\n\n"
            "- 三个部分、9 项任务和 58 条前序验收记录均已复核。\n"
            "- 修复 3 个衔接问题：质量规则版本贯穿绑定；关键错误必须进入修复而非普通确认；旧处理请求在资料更新后立即失效。\n"
            "- 28 项跨部分合同和 45 项实时反例检查全部通过。\n"
            f"- {validation}\n"
            "- 本轮没有读取原始资料，没有执行真实上传或同步，没有上传 GitHub，也没有重装 App。\n"
        ).encode(),
        HUMAN_ROOT / "test_results_zh.md": (
            "# 测试结果\n\n"
            f"状态：{status}。\n\n"
            "58 条前序验收记录、28 项跨部分合同、45 项实时反例检查、3 个已修复问题和 5 项后续风险必须完全一致；"
            f"{validation}\n"
        ).encode(),
        HUMAN_ROOT / "rollback_plan_zh.md": (
            "# 回滚方案\n\n只回滚本次 S11 整体复审新增的绑定合同、测试、证据和状态登记；不得改写三个已验收部分，不得触碰原始资料、GitHub、已安装 App 或 S12。\n"
        ).encode(),
        HUMAN_ROOT / "open_risks_zh.md": (
            "# 开放风险\n\n5 项剩余风险均有后续路径。真实资料与真实上传同步仍需授权后单独接入；最终 App 必须使用原子版本比较拒绝并发旧请求。本轮通过不代表 GitHub 或 App 已更新。\n"
        ).encode(),
    }


def expected_outputs() -> dict[Path, bytes]:
    source = source_contract()
    if source["source_integrity_status"] != "PASS":
        raise BuildError("S11 TaskPack source integrity failed")
    phase = phase_evidence()
    cross = cross_phase_contracts()
    verification = contract.public_verification()
    if cross["accounting"]["failed"] or verification["accounting"]["failed"]:
        raise BuildError("S11 review verification failed")
    rows = receipts()
    final, _, _ = final_binding(rows)
    outputs = {
        MACHINE_ROOT / "source_contract_public_safe.json": _json_bytes(source),
        MACHINE_ROOT / "phase_evidence_public_safe.json": _json_bytes(phase),
        MACHINE_ROOT / "cross_phase_contracts_public_safe.json": _json_bytes(cross),
        MACHINE_ROOT / "cross_phase_verification_public_safe.json": _json_bytes(verification),
        MACHINE_ROOT / "reviewed_binding_sample_public_safe.json": _json_bytes(verification["reviewed_projection"]),
        MACHINE_ROOT / "reviewed_action_policy_public_safe.json": _json_bytes({
            "schema_version": contract.ACTION_POLICY_VERSION,
            "action_kinds": list(contract.REVIEW_ACTION_KINDS),
            "routes": {row["fact_id"]: row["reviewed_action"] for row in verification["reviewed_projection"]["leaves"]},
            "frontend_status_write_count": 0,
        }),
        MACHINE_ROOT / "stage11_review_findings_public_safe.csv": _csv_bytes(list(findings()[0]), findings()),
        MACHINE_ROOT / "open_risk_register_public_safe.csv": _csv_bytes(list(risks()[0]), risks()),
        MANIFEST_PATH: _json_bytes(manifest(rows)),
    }
    outputs.update(_human_outputs(final))
    return outputs


def write_outputs() -> None:
    for path, payload in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    if not VALIDATION_RESULTS_PATH.exists():
        VALIDATION_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        VALIDATION_RESULTS_PATH.write_text("", encoding="utf-8")


def check_outputs() -> list[str]:
    mismatches: list[str] = []
    for path, expected in expected_outputs().items():
        if not path.is_file() or path.read_bytes() != expected:
            mismatches.append(str(path.relative_to(REPO_ROOT)))
    if not VALIDATION_RESULTS_PATH.is_file():
        mismatches.append(str(VALIDATION_RESULTS_PATH.relative_to(REPO_ROOT)))
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            mismatches = check_outputs()
            if mismatches:
                raise BuildError("deterministic output drift: " + ", ".join(mismatches))
            print("PASS: deterministic S11 stage-review evidence")
        else:
            write_outputs()
            print(f"WROTE: {OUTPUT_ROOT.relative_to(REPO_ROOT)}")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
