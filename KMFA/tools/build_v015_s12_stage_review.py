#!/usr/bin/env python3
"""Build deterministic public-safe evidence for the KMFA v1.5 S12 review."""

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

from KMFA.tools import v015_s12_p1_project_cost_facts as p1
from KMFA.tools import v015_s12_p2_core_calculations as p2
from KMFA.tools import v015_s12_p3_engineering_logic as p3
from KMFA.tools import v015_s12_stage_review_contract as contract


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S12_STAGE_REVIEW"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
MANIFEST_PATH = MACHINE_ROOT / "s12_stage_review_manifest.json"
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
    "s12_p1_dependency",
    "s12_p2_dependency",
    "s12_p3_dependency",
    "s12_p1_kernel_regression",
    "s12_p2_kernel_regression",
    "s12_p3_kernel_regression",
    "integrated_review_consistency",
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
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _csv_bytes(fieldnames: list[str], rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


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
    source_manifest = json.loads((PROJECT_ROOT / "taskpack/v1_5/source_manifest.json").read_text(encoding="utf-8"))
    roadmap = json.loads((PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json").read_text(encoding="utf-8"))
    stage = next((row for row in roadmap.get("stages", []) if row.get("id") == "S12"), None)
    package = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    integrity = (
        package.is_file()
        and _sha256(package) == TASKPACK_SHA256
        and source_manifest.get("source_package_sha256") == TASKPACK_SHA256
        and (source_manifest.get("stage_count"), source_manifest.get("phase_count"), source_manifest.get("task_count")) == (24, 72, 216)
        and (stage or {}).get("name") == "项目成本事实层与计算引擎"
        and (stage or {}).get("goal") == "构建符合工程项目制特点的收入、成本、毛利、现金毛利和成本完整度模型。"
        and len((stage or {}).get("phases", [])) == 3
        and sum(len(row.get("tasks", [])) for row in (stage or {}).get("phases", [])) == 9
    )
    return {
        "schema_version": "kmfa.v015.s12.stage-review-source-contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": "S12",
        "stage_name_zh": "项目成本事实层与计算引擎",
        "stage_goal_zh": (stage or {}).get("goal"),
        "phase_count": 3,
        "task_count": 9,
        "review_overlay_counted_as_taskpack_phase": False,
        "review_overlay_counted_as_taskpack_task": False,
        "source_integrity_status": "PASS" if integrity else "FAIL",
        "excluded": [
            "S13",
            "原始资料",
            "真实业务计算",
            "正式报告",
            "GitHub 上传",
            "App 重装",
            "业务执行",
        ],
    }


def _predecessor_specs() -> list[dict[str, Any]]:
    return [
        {
            "roadmap_phase_id": "S12-P1",
            "run_phase_id": p1.RUN_PHASE_ID,
            "manifest": PROJECT_ROOT / "stage_artifacts/V015_S12_P1_PROJECT_COST_FACTS/machine/s12_p1_project_cost_facts_manifest.json",
            "receipts": PROJECT_ROOT / "stage_artifacts/V015_S12_P1_PROJECT_COST_FACTS/machine/validation_results.jsonl",
            "receipt_count": 21,
            "public_check_count": 63,
        },
        {
            "roadmap_phase_id": "S12-P2",
            "run_phase_id": p2.RUN_PHASE_ID,
            "manifest": PROJECT_ROOT / "stage_artifacts/V015_S12_P2_CORE_CALCULATIONS/machine/s12_p2_core_calculations_manifest.json",
            "receipts": PROJECT_ROOT / "stage_artifacts/V015_S12_P2_CORE_CALCULATIONS/machine/validation_results.jsonl",
            "receipt_count": 21,
            "public_check_count": 48,
        },
        {
            "roadmap_phase_id": "S12-P3",
            "run_phase_id": p3.RUN_PHASE_ID,
            "manifest": PROJECT_ROOT / "stage_artifacts/V015_S12_P3_ENGINEERING_LOGIC/machine/s12_p3_engineering_logic_manifest.json",
            "receipts": PROJECT_ROOT / "stage_artifacts/V015_S12_P3_ENGINEERING_LOGIC/machine/validation_results.jsonl",
            "receipt_count": 21,
            "public_check_count": 63,
        },
    ]


def phase_evidence() -> dict[str, Any]:
    phases: list[dict[str, Any]] = []
    for spec in _predecessor_specs():
        manifest = json.loads(spec["manifest"].read_text(encoding="utf-8"))
        receipts = _jsonl(spec["receipts"])
        expected = spec["receipt_count"]
        if (
            manifest.get("run_phase_id") != spec["run_phase_id"]
            or manifest.get("phase_acceptance_status") != "PASSED"
            or manifest.get("phase_task_accepted_count") != 3
            or manifest.get("validation_receipt_count") != expected
            or len(receipts) != expected
            or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts)
            or {row.get("validation_head") for row in receipts} != {manifest.get("validation_head")}
            or {row.get("validation_run_id") for row in receipts} != {manifest.get("validation_run_id")}
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
            "public_check_count": spec["public_check_count"],
            "validation_receipt_count": expected,
            "validation_run_id": manifest["validation_run_id"],
            "validation_head": manifest["validation_head"],
            "manifest_sha256": "sha256:" + _sha256(spec["manifest"]),
            "receipts_sha256": "sha256:" + _sha256(spec["receipts"]),
            "manifest_ref": str(spec["manifest"].relative_to(REPO_ROOT)),
            "receipt_ref": str(spec["receipts"].relative_to(REPO_ROOT)),
        })
    return {
        "schema_version": "kmfa.v015.s12.stage-review-phase-evidence.v1",
        "accounting": {
            "phase_count": 3,
            "phase_passed_count": 3,
            "task_count": 9,
            "task_accepted_count": 9,
            "predecessor_public_check_count": sum(row["public_check_count"] for row in phases),
            "predecessor_receipt_count": sum(row["validation_receipt_count"] for row in phases),
        },
        "phases": phases,
    }


def cross_phase_contracts() -> dict[str, Any]:
    predecessor = phase_evidence()
    p1_check = p1.public_verification()
    p2_check = p2.public_verification()
    p3_check = p3.public_verification()
    review_check = contract.public_verification()
    integrated = review_check["integrated_review"]
    fact = integrated["fact_projection"]
    margins = integrated["calculation_projection"]["margin_results"]["views"]
    cash = integrated["calculation_projection"]["cash_results"]
    risk = integrated["calculation_projection"]["risk_results"]
    change = integrated["change_settlement_result"]
    external = integrated["external_cost_result"]
    check_map = {row["check_id"]: row["status"] == "PASS" for row in review_check["checks"]}
    rows: list[dict[str, Any]] = []

    def add(contract_id: str, description_zh: str, condition: bool) -> None:
        rows.append({
            "contract_id": contract_id,
            "description_zh": description_zh,
            "status": "PASS" if condition else "FAIL",
            "blocking": True,
        })

    add("S12-X01", "三个部分均已通过验收", predecessor["accounting"]["phase_passed_count"] == 3)
    add("S12-X02", "九项任务全部验收", predecessor["accounting"]["task_accepted_count"] == 9)
    add("S12-X03", "63 条前序正式验收记录完整", predecessor["accounting"]["predecessor_receipt_count"] == 63)
    add("S12-X04", "174 项前序公开检查完整", predecessor["accounting"]["predecessor_public_check_count"] == 174)
    add("S12-X05", "P1 公开检查 63 项全部通过", p1_check["accounting"] == {"total": 63, "passed": 63, "failed": 0})
    add("S12-X06", "P1 五层收入事实保持独立", check_map.get("p1_income_layer_count_exact", False))
    add("S12-X07", "P1 成本守恒且没有丢失", check_map.get("p1_cost_conservation_zero", False) and check_map.get("p1_no_dropped_cost", False))
    add("S12-X08", "P1 不平均分摊或静默分类", check_map.get("p1_no_average_allocation", False) and check_map.get("p1_no_silent_classification", False))
    add("S12-X09", "P2 公开检查 48 项全部通过", p2_check["accounting"] == {"total": 48, "passed": 48, "failed": 0})
    add("S12-X10", "P2 三类毛利口径明确", len(p2.margin_contract()["views"]) == 3)
    add("S12-X11", "P2 未回款不计现金", cash["uncollected_amount_counted_as_cash_cents"] == 0)
    add("S12-X12", "P2 风险阈值来自外置版本", risk["policy_version"] == p2.DEFAULT_RISK_POLICY["policy_version"])
    add("S12-X13", "P3 公开检查 63 项全部通过", p3_check["accounting"] == {"total": 63, "passed": 63, "failed": 0})
    add("S12-X14", "P3 变更、结算、发票和回款全部同链", change["chain_node_count"] == change["linked_node_count"] == 6)
    add("S12-X15", "P3 无依据变更计收入为零", change["unsupported_change_recognized_cents"] == 0)
    add("S12-X16", "P3 低置信自动归集为零", external["automatic_low_confidence_allocation_count"] == 0)
    add("S12-X17", "P3 重复成本已排除", external["duplicate_excluded_amount_cents"] == 25000)
    add("S12-X18", "P3 跨项目成本已排除", external["cross_project_anomaly_amount_cents"] == 7000)
    add("S12-X19", "确认变更是 P1 唯一变更收入来源", check_map.get("p1_supported_change_only", False))
    add("S12-X20", "未确认变更没有进入 P1 收入", check_map.get("p1_unconfirmed_change_excluded", False))
    add("S12-X21", "P3 已确认项目成本等于 P1 已归集成本", fact["allocated_project_cost_cents"] == external["recognized_project_cost_cents"])
    add("S12-X22", "低置信候选进入 P1 未归集池", fact["unallocated_project_cost_cents"] == external["unallocated_candidate_amount_cents"])
    add("S12-X23", "重复与跨项目候选没有泄漏进目标项目", fact["excluded_candidate_leak_count"] == 0)
    add("S12-X24", "合同毛利收入绑定合同及有依据变更", margins["contract"]["revenue_cents"] == change["contract_and_supported_change_cents"])
    add("S12-X25", "结算毛利收入绑定确认结算", margins["settlement"]["revenue_cents"] == change["settlement"]["confirmed_amount_cents"])
    add("S12-X26", "管理毛利成本保留未归集成本", margins["management"]["cost_cents"] == fact["target_cost_input_cents"])
    add("S12-X27", "现金毛利回款绑定 P3 已确认回款", cash["confirmed_collection_cents"] == change["confirmed_collection_cents"])
    add("S12-X28", "现金毛利付款绑定 P3 已确认付款", cash["confirmed_cash_paid_cost_cents"] == external["confirmed_paid_cash_cents"])
    add("S12-X29", "风险总成本绑定 P1 守恒总额", risk["metrics"]["unallocated_cost_ratio_bps"] == 1064)
    add("S12-X30", "P3 六项工程解释全部一致", integrated["p3_explanation_consistency"]["consistency_pass"] is True)
    add("S12-X31", "复审六项计算解释全部一致", integrated["review_explanation_consistency"]["consistency_pass"] is True)
    add("S12-X32", "篡改解释被拒绝", check_map.get("tampered_review_explanation_rejected", False))
    add("S12-X33", "篡改跨部分毛利被拒绝", check_map.get("tampered_margin_cross_binding_rejected", False))
    add("S12-X34", "跨项目范围输入被拒绝", check_map.get("cross_scope_input_rejected", False))
    add("S12-X35", "复审结果确定且输入未被改写", check_map.get("review_deterministic", False) and check_map.get("review_input_not_mutated", False))
    add("S12-X36", "复审未读取 raw、真实来源或执行发布动作", integrated["raw_root_access_count"] == 0 and integrated["live_source_read_count"] == 0 and integrated["github_upload_performed"] is False and integrated["app_reinstall_performed"] is False)
    failed = sum(row["status"] != "PASS" for row in rows)
    return {
        "schema_version": "kmfa.v015.s12.cross-phase-contracts.v1",
        "accounting": {
            "total": len(rows),
            "passed": len(rows) - failed,
            "failed": failed,
            "blocking_failed": failed,
        },
        "contracts": rows,
        "integrated_review_fingerprint": integrated["review_fingerprint"],
    }


def findings() -> list[dict[str, str]]:
    root = "KMFA/stage_artifacts/V015_S12_STAGE_REVIEW/machine/"
    test = "KMFA/tests/test_v015_s12_stage_review_contract.py"
    return [
        {
            "finding_id": "S12REV-F001",
            "severity": "HIGH",
            "finding_zh": "P1 变更事实没有直接证明只来自 P3 有依据确认变更。",
            "root_cause_zh": "三个部分分别验收，缺少从工程变更链到收入事实层的统一投影。",
            "fix_zh": "新增确认变更投影，只写入有依据金额；未确认和无依据金额保持排除并单独留痕。",
            "evidence_ref": root + "integrated_review_public_safe.json",
            "validation_ref": test,
            "status": "FIXED_VALIDATED",
            "blocks_stage_acceptance": "false",
        },
        {
            "finding_id": "S12REV-F002",
            "severity": "HIGH",
            "finding_zh": "重复、低置信和跨项目成本没有与 P1 成本守恒形成统一证明。",
            "root_cause_zh": "P1 与 P3 使用独立公开样例，排除项和未归集池没有同源核对。",
            "fix_zh": "新增目标项目成本投影：已确认成本进入已归集层，低置信进入未归集池，重复和跨项目候选明确排除。",
            "evidence_ref": root + "integrated_review_public_safe.json",
            "validation_ref": test,
            "status": "FIXED_VALIDATED",
            "blocks_stage_acceptance": "false",
        },
        {
            "finding_id": "S12REV-F003",
            "severity": "HIGH",
            "finding_zh": "P2 独立黄金样例不能证明毛利与现金指标使用 P1/P3 同一项目数据。",
            "root_cause_zh": "核心计算函数已验收，但缺少跨部分输入映射和来源绑定。",
            "fix_zh": "新增统一计算投影，三类毛利、现金毛利和风险全部从同一 P1/P3 结果构造并逐项核对。",
            "evidence_ref": root + "integrated_review_public_safe.json",
            "validation_ref": test,
            "status": "FIXED_VALIDATED",
            "blocks_stage_acceptance": "false",
        },
        {
            "finding_id": "S12REV-F004",
            "severity": "MEDIUM",
            "finding_zh": "P3 解释层未覆盖复审新增的跨部分毛利、现金和成本完整度结果。",
            "root_cause_zh": "P3 只解释本部分六项结果，跨部分结果此前尚未存在。",
            "fix_zh": "新增六项复审解释并绑定来源计算；任一公式、金额或指纹变化都会失败。",
            "evidence_ref": root + "review_explanations_public_safe.json",
            "validation_ref": test,
            "status": "FIXED_VALIDATED",
            "blocks_stage_acceptance": "false",
        },
    ]


def risks() -> list[dict[str, str]]:
    rows = (
        ("001", "本轮只用公开模拟资料复审，没有读取真实财务文件。", "LATER_AUTHORIZED_PRIVATE_VALIDATION"),
        ("002", "未确认变更、低置信成本和跨项目异常仍需真实业务人员处理。", "LATER_CONTROLLED_HUMAN_RESOLUTION"),
        ("003", "含税与不含税转换仍需明确税务和期间口径后才能启用。", "LATER_TAX_BASIS_AND_PERIOD_GATE"),
        ("004", "真实比较期成本必须来自已登记版本，不能沿用复审模拟值。", "S13_REPORT_INPUT_VERSION_GATE"),
        ("005", "本地复审通过不等于 GitHub 和已安装 App 已更新。", "FINAL_OVERALL_GITHUB_AND_APP_PARITY_GATE"),
        ("006", "S13-P1 尚未开始。", "S13P1_ONLY_NEXT_RUN"),
    )
    return [
        {
            "risk_id": f"RISK-KMFA-V015-S12-{number}",
            "risk": risk,
            "route": route,
            "status": "ROUTED_RESIDUAL",
            "plan_complete": "true",
            "blocks_s12_stage_acceptance": "false",
        }
        for number, risk, route in rows
    ]


def receipts() -> list[dict[str, Any]]:
    rows = _jsonl(VALIDATION_RESULTS_PATH)
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S12 review validation receipt order drift")
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
    integrated = verification["integrated_review"]
    return {
        "schema_version": "kmfa.v015.s12_stage_review.manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S12",
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
        "decision": "GO_TO_S13_P1_ONLY" if final else "REMAIN_IN_S12_STAGE_REVIEW",
        "phase_accounting": phase_evidence()["accounting"],
        "cross_phase_accounting": cross_phase_contracts()["accounting"],
        "live_check_accounting": verification["accounting"],
        "review_findings": {"total": 4, "fixed_validated": 4, "open": 0, "blocking_open": 0},
        "open_risks": {"total": 6, "routed": 6, "plan_gap_count": 0, "blocking": 0},
        "review_explanation_count": integrated["review_explanations"]["explanation_count"],
        "review_explanation_mismatch_count": integrated["review_explanation_consistency"]["mismatch_count"],
        "target_cost_conservation_delta_cents": integrated["fact_projection"]["cost_conservation_delta_cents"],
        "excluded_candidate_leak_count": integrated["excluded_candidate_leak_count"],
        "overall_accepted_phase_count": 34,
        "overall_taskpack_phase_count": 72,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "real_business_calculation_performed": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "s12_stage_review_started": True,
        "s12_stage_review_performed": final,
        "s12_stage_review_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s13_entry_allowed": final,
        "s13_p1_entry_allowed": final,
        "s13_p1_started": False,
        "s13_p2_plus_entry_allowed": False,
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
        HUMAN_ROOT / "stage12_review_report_zh.md": (
            "# KMFA v1.5 第 12 阶段整体复审\n\n"
            f"状态：{status}。\n\n"
            "- 三个部分、9 项任务、174 项公开检查和 63 条前序正式验收记录均已复核。\n"
            "- 修复 4 个衔接问题：变更收入来源、成本候选去向、毛利现金同源计算、跨部分结果解释。\n"
            "- 目标项目成本 47000 分完整守恒：已归集 42000 分、未归集 5000 分、差额 0 分；重复 25000 分和跨项目 7000 分均未泄漏。\n"
            "- 36 项跨部分合同和 68 项反例检查全部通过，开放复审问题为 0。\n"
            f"- {validation}\n"
            "- 本轮没有读取原始资料、执行真实业务计算、启动 S13、上传 GitHub 或重装 App。\n"
        ).encode("utf-8"),
        HUMAN_ROOT / "test_results_zh.md": (
            "# 测试结果\n\n"
            f"状态：{status}。\n\n"
            "63 条前序验收记录、36 项跨部分合同、68 项实时检查、4 个已修复问题、6 项复审解释和 6 项后续风险必须完全一致；"
            f"{validation}\n"
        ).encode("utf-8"),
        HUMAN_ROOT / "rollback_plan_zh.md": (
            "# 回滚方案\n\n"
            "只回滚本次 S12 整体复审新增的投影合同、测试、证据和状态登记；不得改写 S12-P1/P2/P3 的既有验收证据，不得触碰原始资料、GitHub、已安装 App 或 S13。\n"
        ).encode("utf-8"),
        HUMAN_ROOT / "open_risks_zh.md": (
            "# 开放风险\n\n"
            "6 项剩余风险均有后续路径。真实资料、人工确认、税务口径、比较期成本、最终 GitHub/App 一致性和 S13-P1 都必须在后续独立 Run 处理；本轮通过不代表这些动作已经执行。\n"
        ).encode("utf-8"),
    }


def expected_outputs() -> dict[Path, bytes]:
    source = source_contract()
    if source["source_integrity_status"] != "PASS":
        raise BuildError("S12 TaskPack source integrity failed")
    predecessor = phase_evidence()
    cross = cross_phase_contracts()
    verification = contract.public_verification()
    if cross["accounting"]["failed"] or verification["accounting"]["failed"]:
        raise BuildError("S12 review verification failed")
    rows = receipts()
    final, _, _ = final_binding(rows)
    integrated = verification["integrated_review"]
    outputs = {
        MACHINE_ROOT / "source_contract_public_safe.json": _json_bytes(source),
        MACHINE_ROOT / "phase_evidence_public_safe.json": _json_bytes(predecessor),
        MACHINE_ROOT / "integrated_review_public_safe.json": _json_bytes(integrated),
        MACHINE_ROOT / "cross_phase_contracts_public_safe.json": _json_bytes(cross),
        MACHINE_ROOT / "cross_phase_verification_public_safe.json": _json_bytes(verification),
        MACHINE_ROOT / "review_explanations_public_safe.json": _json_bytes({
            "p3_explanations": integrated["p3_explanations"],
            "p3_consistency": integrated["p3_explanation_consistency"],
            "review_explanations": integrated["review_explanations"],
            "review_consistency": integrated["review_explanation_consistency"],
        }),
        MACHINE_ROOT / "stage12_review_findings_public_safe.csv": _csv_bytes(list(findings()[0]), findings()),
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
            print("PASS: deterministic S12 stage-review evidence")
        else:
            write_outputs()
            print(f"WROTE: {OUTPUT_ROOT.relative_to(REPO_ROOT)}")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
