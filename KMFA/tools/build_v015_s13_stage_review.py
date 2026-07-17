#!/usr/bin/env python3
"""生成 KMFA v1.5 S13 整体复审的确定性公开证据。"""

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

from KMFA.tools import v015_s13_p1_indicator_registry as p1
from KMFA.tools import v015_s13_p2_business_health_model as p2
from KMFA.tools import v015_s13_p3_action_priority as p3
from KMFA.tools import v015_s13_stage_review_contract as contract


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S13_STAGE_REVIEW"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
MANIFEST_PATH = MACHINE_ROOT / "s13_stage_review_manifest.json"
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
    "s13_p1_dependency",
    "s13_p2_dependency",
    "s13_p3_dependency",
    "s13_p1_kernel_regression",
    "s13_p2_kernel_regression",
    "s13_p3_kernel_regression",
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


def _csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise BuildError(f"JSONL rows must be objects: {path}")
    return rows


def source_contract() -> dict[str, Any]:
    source_manifest = json.loads((PROJECT_ROOT / "taskpack/v1_5/source_manifest.json").read_text(encoding="utf-8"))
    roadmap = json.loads((PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json").read_text(encoding="utf-8"))
    stage = next((row for row in roadmap.get("stages", []) if row.get("id") == "S13"), None)
    package = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    integrity = (
        package.is_file()
        and _sha256(package) == TASKPACK_SHA256
        and source_manifest.get("source_package_sha256") == TASKPACK_SHA256
        and (source_manifest.get("stage_count"), source_manifest.get("phase_count"), source_manifest.get("task_count")) == (24, 72, 216)
        and (stage or {}).get("name") == "经营指标、健康模型与行动优先级"
        and (stage or {}).get("goal") == "外置公式、权重、阈值和参数，输出可解释且不夸大的经营判断。"
        and len((stage or {}).get("phases", [])) == 3
        and sum(len(row.get("tasks", [])) for row in (stage or {}).get("phases", [])) == 9
    )
    return {
        "schema_version": "kmfa.v015.s13.stage-review-source-contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": "S13",
        "stage_name_zh": "经营指标、健康模型与行动优先级",
        "stage_goal_zh": (stage or {}).get("goal"),
        "phase_count": 3,
        "task_count": 9,
        "review_overlay_counted_as_taskpack_phase": False,
        "review_overlay_counted_as_taskpack_task": False,
        "source_integrity_status": "PASS" if integrity else "FAIL",
        "excluded": ["S14", "原始资料", "真实经营判断", "真实行动", "GitHub 上传", "App 重装"],
    }


def _predecessor_specs() -> list[dict[str, Any]]:
    return [
        {
            "roadmap_phase_id": "S13-P1",
            "run_phase_id": p1.RUN_PHASE_ID,
            "manifest": PROJECT_ROOT / "stage_artifacts/V015_S13_P1_INDICATOR_REGISTRY/machine/s13_p1_indicator_registry_manifest.json",
            "receipts": PROJECT_ROOT / "stage_artifacts/V015_S13_P1_INDICATOR_REGISTRY/machine/validation_results.jsonl",
            "receipt_count": 20,
            "public_check_count": 78,
        },
        {
            "roadmap_phase_id": "S13-P2",
            "run_phase_id": p2.RUN_PHASE_ID,
            "manifest": PROJECT_ROOT / "stage_artifacts/V015_S13_P2_BUSINESS_HEALTH_MODEL/machine/s13_p2_business_health_model_manifest.json",
            "receipts": PROJECT_ROOT / "stage_artifacts/V015_S13_P2_BUSINESS_HEALTH_MODEL/machine/validation_results.jsonl",
            "receipt_count": 20,
            "public_check_count": 88,
        },
        {
            "roadmap_phase_id": "S13-P3",
            "run_phase_id": p3.RUN_PHASE_ID,
            "manifest": PROJECT_ROOT / "stage_artifacts/V015_S13_P3_ACTION_PRIORITY/machine/s13_p3_action_priority_manifest.json",
            "receipts": PROJECT_ROOT / "stage_artifacts/V015_S13_P3_ACTION_PRIORITY/machine/validation_results.jsonl",
            "receipt_count": 20,
            "public_check_count": 88,
        },
    ]


def phase_evidence() -> dict[str, Any]:
    phases = []
    for spec in _predecessor_specs():
        manifest = json.loads(spec["manifest"].read_text(encoding="utf-8"))
        receipts = _jsonl(spec["receipts"])
        if (
            manifest.get("run_phase_id") != spec["run_phase_id"]
            or manifest.get("phase_acceptance_status") != "PASSED"
            or manifest.get("phase_task_accepted_count") != 3
            or manifest.get("validation_receipt_count") != spec["receipt_count"]
            or len(receipts) != spec["receipt_count"]
            or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts)
            or {row.get("validation_head") for row in receipts} != {manifest.get("validation_head")}
            or {row.get("validation_run_id") for row in receipts} != {manifest.get("validation_run_id")}
            or not re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("validation_head") or ""))
        ):
            raise BuildError(f"predecessor acceptance drift: {spec['roadmap_phase_id']}")
        phases.append(
            {
                "roadmap_phase_id": spec["roadmap_phase_id"],
                "run_phase_id": spec["run_phase_id"],
                "acceptance_status": "PASSED",
                "task_count": 3,
                "task_accepted_count": 3,
                "public_check_count": spec["public_check_count"],
                "validation_receipt_count": spec["receipt_count"],
                "validation_run_id": manifest["validation_run_id"],
                "validation_head": manifest["validation_head"],
                "manifest_sha256": "sha256:" + _sha256(spec["manifest"]),
                "receipts_sha256": "sha256:" + _sha256(spec["receipts"]),
                "manifest_ref": str(spec["manifest"].relative_to(REPO_ROOT)),
                "receipt_ref": str(spec["receipts"].relative_to(REPO_ROOT)),
            }
        )
    return {
        "schema_version": "kmfa.v015.s13.stage-review-phase-evidence.v1",
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
    predecessor = phase_evidence()["accounting"]
    p1v = p1.public_verification()
    p2v = p2.public_verification()
    p3v = p3.public_verification()
    review = contract.public_verification()
    integrated = review["integrated_review"]
    health = integrated["health_result"]
    candidates = integrated["health_action_candidates"]
    ranked = integrated["ranked_actions"]
    focus = integrated["focus_selection"]
    checks = {row["name"]: row["passed"] for row in review["checks"]}
    rows: list[dict[str, Any]] = []

    def add(number: int, description_zh: str, condition: bool) -> None:
        rows.append({"contract_id": f"S13-X{number:02d}", "description_zh": description_zh, "status": "PASS" if condition else "FAIL", "blocking": True})

    add(1, "三个部分均已通过验收", predecessor["phase_passed_count"] == 3)
    add(2, "九项任务全部验收", predecessor["task_accepted_count"] == 9)
    add(3, "60 条前序正式验收记录完整", predecessor["predecessor_receipt_count"] == 60)
    add(4, "254 项前序公开检查完整", predecessor["predecessor_public_check_count"] == 254)
    add(5, "P1 的 78 项公开检查全部通过", p1v["accounting"] == {"total": 78, "passed": 78, "failed": 0})
    add(6, "P2 的 88 项公开检查全部通过", p2v["accounting"] == {"total": 88, "passed": 88, "failed": 0})
    add(7, "P3 的 88 项公开检查全部通过", p3v["accounting"] == {"total": 88, "passed": 88, "failed": 0})
    add(8, "八个指标领域完整登记", checks["indicator_count"] and checks["indicator_domain_count"])
    add(9, "健康维度必须绑定指标来源", checks["all_health_sources_registered"])
    add(10, "指标参数定义不允许前端或生产直接改写", all(not row["frontend_write_allowed"] and not row["production_direct_write_allowed"] for row in p1.parameter_versions()))
    add(11, "健康模型正好包含六个维度", checks["health_dimension_count"])
    add(12, "健康维度权重合计 10000 基点", checks["health_weight_total"])
    add(13, "七个健康来源全部来自 P1 登记", checks["source_binding_count"] and checks["all_health_sources_registered"])
    add(14, "正常公开样例可以显示健康判断", checks["health_score_displayed"] and checks["health_state_explained"])
    add(15, "硬门禁状态对用户可见", health["hard_gate_override_applied"] is False and all("hard_gate_passed" in row for row in health["dimension_results"]))
    add(16, "资料新鲜度对用户可见", checks["health_freshness_visible"])
    add(17, "行动排序正好使用六项因素", p3.validate_ranking_contract(p3.ranking_contract())["factor_count"] == 6)
    add(18, "行动排序权重合计 10000 基点", p3.validate_ranking_contract(p3.ranking_contract())["weight_total_bps"] == 10_000)
    add(19, "每个健康维度生成一个行动候选", len(candidates) == 6)
    add(20, "每个行动候选直接绑定 P2 维度", checks["candidates_bind_p2"])
    add(21, "每个行动候选直接绑定 P1 指标", checks["candidates_bind_p1"])
    add(22, "来源指纹与健康结果完全一致", checks["candidate_fingerprints_exact"])
    add(23, "行动排序结果可以确定性重建", checks["ranking_deterministic"])
    add(24, "本期重点事项严格限制为三至五项", checks["focus_bounds"] and focus["focus_item_count"] == 5)
    add(25, "单一领域最多占两项", checks["focus_domain_cap"])
    add(26, "硬门禁失败候选不能进入重点事项", checks["hard_gate_not_focus"])
    add(27, "过期资料候选不能进入重点事项", checks["stale_not_focus"])
    add(28, "建议不会被写成事实", checks["recommendation_not_fact"])
    add(29, "未知结果保持明确未知", checks["review_unknown_explicit"])
    add(30, "参数校准只允许形成提案", checks["calibration_insufficient"] and checks["no_auto_parameter_change"])
    add(31, "行动不会自动执行", integrated["automatic_execution_count"] == 0)
    add(32, "建议不会写入事实层", integrated["recommendation_fact_write_count"] == 0)
    add(33, "参数不会自动修改", integrated["automatic_parameter_change_count"] == 0)
    add(34, "复审未读取原始或真实来源", integrated["raw_root_access_count"] == integrated["live_source_read_count"] == 0)
    add(35, "复审未执行发布或真实业务动作", integrated["real_business_action_count"] == 0 and not integrated["github_upload_performed"] and not integrated["app_reinstall_performed"])
    add(36, "复审结果确定且来源链不可静默漂移", contract.validate_integrated_review(integrated)["explanation_mismatch_count"] == 0 and ranked == p3.rank_actions(candidates))
    failed = sum(row["status"] != "PASS" for row in rows)
    return {
        "schema_version": "kmfa.v015.s13.cross-phase-contracts.v1",
        "accounting": {"total": len(rows), "passed": len(rows) - failed, "failed": failed, "blocking_failed": failed},
        "contracts": rows,
        "integrated_review_fingerprint": integrated["review_fingerprint"],
    }


def findings() -> list[dict[str, str]]:
    root = "KMFA/stage_artifacts/V015_S13_STAGE_REVIEW/machine/"
    test = "KMFA/tests/test_v015_s13_stage_review_contract.py"
    values = (
        ("S13REV-F001", "HIGH", "P1 指标与 P2 健康来源此前分别测试，但缺少同一条正式复审链。", "分别验收没有证明每个健康维度仍精确引用登记指标。", "新增七个精确指标绑定和登记指纹核验。"),
        ("S13REV-F002", "HIGH", "P3 公开样例来源只是领域标签，不能直接证明来自某个 P2 健康结果。", "行动样例与健康样例独立，来源引用和结果指纹没有连接。", "新增六个健康到行动适配器，逐项绑定 P2 维度、P1 指标和结果指纹。"),
        ("S13REV-F003", "HIGH", "硬门禁和过期状态此前未完成 P2 到 P3 的端到端证明。", "两个部分各自有边界测试，但缺少跨部分反例。", "新增硬门禁和过期资料反例，证明不计分且不进入重点事项。"),
        ("S13REV-F004", "MEDIUM", "建议复盘、事实层和参数校准的隔离此前未跨三个部分统一证明。", "复盘只在 P3 内部验证，没有与 P1/P2 来源链同证。", "新增五项未知结果复盘，确认事实写入、自动执行和自动改参数均为零。"),
    )
    return [
        {
            "finding_id": finding_id,
            "severity": severity,
            "finding_zh": finding,
            "root_cause_zh": cause,
            "fix_zh": fix,
            "evidence_ref": root + "integrated_review_public_safe.json",
            "validation_ref": test,
            "status": "FIXED_VALIDATED",
            "blocks_stage_acceptance": "false",
        }
        for finding_id, severity, finding, cause, fix in values
    ]


def risks() -> list[dict[str, str]]:
    values = (
        ("001", "本轮只用公开模拟资料，没有读取真实财务资料。", "LATER_AUTHORIZED_PRIVATE_VALIDATION"),
        ("002", "真实权重和阈值仍需授权人员批准。", "LATER_PARAMETER_APPROVAL_GATE"),
        ("003", "建议成效在真实人工执行前保持未知。", "LATER_OUTCOME_REVIEW"),
        ("004", "任何真实行动仍须人工授权。", "HUMAN_ACTION_AUTHORIZATION_GATE"),
        ("005", "S14 界面实现尚未开始。", "S14P1_ONLY_NEXT_RUN"),
        ("006", "GitHub 与 App 一致性只在 v1.5 最终总验收处理。", "FINAL_OVERALL_GITHUB_AND_APP_PARITY_GATE"),
    )
    return [
        {
            "risk_id": f"RISK-KMFA-V015-S13-{number}",
            "risk": risk,
            "route": route,
            "status": "ROUTED_RESIDUAL",
            "plan_complete": "true",
            "blocks_s13_stage_acceptance": "false",
        }
        for number, risk, route in values
    ]


def receipts() -> list[dict[str, Any]]:
    rows = _jsonl(VALIDATION_RESULTS_PATH)
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S13 review validation receipt order drift")
    return rows


def final_binding(rows: list[dict[str, Any]]) -> tuple[bool, str | None, str | None]:
    if not rows:
        return False, None, None
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    final = (
        len(rows) == len(EXPECTED_VALIDATION_NAMES)
        and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in rows)
        and len(run_ids) == len(heads) == 1
        and None not in run_ids
        and None not in heads
    )
    return final, next(iter(run_ids)) if final else None, next(iter(heads)) if final else None


def manifest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    final, run_id, head = final_binding(rows)
    verification = contract.public_verification()
    integrated = verification["integrated_review"]
    summary = contract.validate_integrated_review(integrated)
    return {
        "schema_version": "kmfa.v015.s13_stage_review.manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S13",
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
        "decision": "GO_TO_S14_P1_ONLY" if final else "REMAIN_IN_S13_STAGE_REVIEW",
        "phase_accounting": phase_evidence()["accounting"],
        "cross_phase_accounting": cross_phase_contracts()["accounting"],
        "live_check_accounting": verification["accounting"],
        "review_findings": {"total": 4, "fixed_validated": 4, "open": 0, "blocking_open": 0},
        "open_risks": {"total": 6, "routed": 6, "plan_gap_count": 0, "blocking": 0},
        "review_explanation_count": summary["explanation_count"],
        "review_explanation_mismatch_count": summary["explanation_mismatch_count"],
        "source_binding_count": summary["source_binding_count"],
        "generated_action_candidate_count": summary["candidate_count"],
        "focus_item_count": summary["focus_item_count"],
        "automatic_execution_count": integrated["automatic_execution_count"],
        "recommendation_fact_write_count": integrated["recommendation_fact_write_count"],
        "automatic_parameter_change_count": integrated["automatic_parameter_change_count"],
        "overall_accepted_phase_count": 37,
        "overall_taskpack_phase_count": 72,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "real_business_action_count": 0,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "s13_stage_review_started": True,
        "s13_stage_review_performed": final,
        "s13_stage_review_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s14_entry_allowed": final,
        "s14_p1_entry_allowed": final,
        "s14_p1_started": False,
        "s14_p2_plus_entry_allowed": False,
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
        HUMAN_ROOT / "stage13_review_report_zh.md": (
            "# KMFA v1.5 第 13 阶段整体复审\n\n"
            f"状态：{status}。\n\n"
            "- 三个部分、9 项任务、254 项公开检查和 60 条前序验收记录均已复核。\n"
            "- 修复 4 个衔接问题：指标来源绑定、健康结果到行动来源、硬门禁/过期状态传递、建议与事实/参数隔离。\n"
            "- 六个健康维度生成六个可解释行动候选，其中五项进入重点清单；所有行动仍须人工决定。\n"
            "- 36 项跨部分合同和 72 项反例检查全部通过，开放复审问题为 0。\n"
            f"- {validation}\n"
            "- 本轮未读取原始资料、执行真实业务动作、启动 S14、上传 GitHub 或重装 App。\n"
        ).encode("utf-8"),
        HUMAN_ROOT / "test_results_zh.md": (
            "# 测试结果\n\n"
            f"状态：{status}。\n\n"
            f"60 条前序验收记录、36 项跨部分合同、72 项实时检查、4 个已修复问题和 6 项剩余风险保持一致；{validation}\n"
        ).encode("utf-8"),
        HUMAN_ROOT / "rollback_plan_zh.md": (
            "# 回滚方案\n\n只回滚本次 S13 整体复审新增的连接合同、测试、证据和状态登记；不改写 S13-P1/P2/P3 既有验收，不触碰原始资料、GitHub、App 或 S14。\n"
        ).encode("utf-8"),
        HUMAN_ROOT / "open_risks_zh.md": (
            "# 开放风险\n\n6 项剩余风险已有后续路径：真实资料验证、权重审批、结果复盘、人工授权、S14 界面实现以及最终 GitHub/App 一致性。S13 通过不代表这些动作已经执行。\n"
        ).encode("utf-8"),
    }


def expected_outputs() -> dict[Path, bytes]:
    source = source_contract()
    if source["source_integrity_status"] != "PASS":
        raise BuildError("S13 TaskPack source integrity failed")
    predecessor = phase_evidence()
    cross = cross_phase_contracts()
    verification = contract.public_verification()
    if cross["accounting"]["failed"] or verification["accounting"]["failed"]:
        raise BuildError("S13 review verification failed")
    rows = receipts()
    final, _, _ = final_binding(rows)
    integrated = verification["integrated_review"]
    outputs = {
        MACHINE_ROOT / "source_contract_public_safe.json": _json_bytes(source),
        MACHINE_ROOT / "phase_evidence_public_safe.json": _json_bytes(predecessor),
        MACHINE_ROOT / "integrated_review_public_safe.json": _json_bytes(integrated),
        MACHINE_ROOT / "cross_phase_contracts_public_safe.json": _json_bytes(cross),
        MACHINE_ROOT / "cross_phase_verification_public_safe.json": _json_bytes(verification),
        MACHINE_ROOT / "review_explanations_public_safe.json": _json_bytes({"explanations": integrated["link_explanations"], "explanation_count": 6, "mismatch_count": 0}),
        MACHINE_ROOT / "stage13_review_findings_public_safe.csv": _csv_bytes(findings()),
        MACHINE_ROOT / "open_risk_register_public_safe.csv": _csv_bytes(risks()),
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
    mismatches = []
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
            print("PASS: deterministic S13 stage-review evidence")
        else:
            write_outputs()
            print(f"WROTE: {OUTPUT_ROOT.relative_to(REPO_ROOT)}")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
