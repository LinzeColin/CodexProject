#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S11-P1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s11_p1_quality_rules as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "87794b7ecbff77dc478b550b88addaf4165a410f"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "legacy_quality_gate_regression",
    "s10_stage_review_dependency",
    "deterministic_evidence",
    "pre_final_phase_checker",
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

MANIFEST_PATH = MACHINE_ROOT / "s11_p1_quality_rules_manifest.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
COVERAGE_PATH = MACHINE_ROOT / "quality_rule_coverage_public_safe.json"
SCENARIO_RESULTS_PATH = MACHINE_ROOT / "quality_scenario_results_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

RULE_CATALOG_PATH = PROJECT_ROOT / "metadata/quality/v015_s11_p1_quality_rule_catalog_public_safe.json"
STATUS_MODEL_PATH = PROJECT_ROOT / "metadata/quality/v015_s11_p1_quality_status_model_public_safe.json"
SCORE_POLICY_PATH = PROJECT_ROOT / "metadata/quality/v015_s11_p1_quality_score_policy_public_safe.json"

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
STATUS_GUIDE_PATH = HUMAN_ROOT / "quality_status_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_MANIFEST_PATH = PROJECT_ROOT / "stage_artifacts/V015_S10_STAGE_REVIEW/machine/s10_stage_review_manifest.json"
DEPENDENCY_RECEIPTS_PATH = PROJECT_ROOT / "stage_artifacts/V015_S10_STAGE_REVIEW/machine/validation_results.jsonl"


class BuildError(RuntimeError):
    pass


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    manifest = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    expected = {
        "run_phase_id": "V015_S10_STAGE_REVIEW",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "decision": "GO_TO_S11_P1_ONLY",
        "s10_stage_review_performed": True,
        "s10_stage_review_acceptance_status": "PASSED",
        "s11_p1_entry_allowed": True,
        "s11_p1_started": False,
        "validation_receipt_count": 22,
    }
    mismatches = [key for key, expected_value in expected.items() if manifest.get(key) != expected_value]
    if mismatches:
        raise BuildError("S10 review dependency mismatch: " + ", ".join(mismatches))
    if len(rows) != 22 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S10 review receipts are not exactly 22 PASS records")
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S10 review validation head mismatch")
    if {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")}:
        raise BuildError("S10 review validation run mismatch")
    return {
        "acceptance_status": "PASSED",
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": len(rows),
        "s11_p1_entry_allowed": True,
        "s11_p1_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S11-P1 validation receipt order mismatch")
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
        "schema_version": "kmfa.v015.s11p1.source_contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": "S11",
        "stage_name_zh": "数据质量、完整性与数据源检查板",
        "roadmap_phase_id": "S11-P1",
        "phase_name_zh": "质量规则",
        "task_count": 3,
        "task_ids": ["S11P1T01", "S11P1T02", "S11P1T03"],
        "scope": ["八类质量规则", "四种人类状态", "硬门禁优先的整数评分"],
        "excluded": ["S11-P2 检查板数据模型", "S11-P3 检查板界面", "S11 整体复审", "GitHub 上传", "App 重装"],
    }


def _coverage(catalog: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for dimension in catalog["dimensions"]:
        rules = [row for row in catalog["rules"] if row["dimension"] == dimension["code"]]
        rows.append({
            "dimension": dimension["code"],
            "label_zh": dimension["label_zh"],
            "rule_count": len(rules),
            "hard_gate_count": sum(rule["hard_gate"] for rule in rules),
            "weight_bps": sum(rule["weight_bps"] for rule in rules),
            "rule_ids": [rule["rule_id"] for rule in rules],
            "severities": sorted({rule["severity"] for rule in rules}),
            "process_impacts": sorted({rule["process_impact"] for rule in rules}),
        })
    return {
        "schema_version": "kmfa.v015.s11p1.quality_rule_coverage.v1",
        "dimension_count": len(rows),
        "rule_count": len(catalog["rules"]),
        "hard_gate_count": sum(rule["hard_gate"] for rule in catalog["rules"]),
        "rule_weight_total_bps": sum(rule["weight_bps"] for rule in catalog["rules"]),
        "dimensions": rows,
        "all_rules_bind_severity": all(bool(rule["severity"]) for rule in catalog["rules"]),
        "all_rules_bind_process_impact": all(bool(rule["process_impact"]) for rule in catalog["rules"]),
    }


def _task_matrix(final: bool) -> dict[str, Any]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    result = "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION"
    tasks = [
        {
            "task_id": "S11P1T01",
            "name_zh": "建立字段和跨表质量规则",
            "acceptance_zh": "完整覆盖八类检查；每条规则绑定严重度和流程影响；关键失败阻止发布。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(COVERAGE_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S11P1T02",
            "name_zh": "建立质量结果模型",
            "acceptance_zh": "只向普通用户显示已通过、需确认、不可使用、已过期；颜色不是唯一信息。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(STATUS_MODEL_PATH.relative_to(REPO_ROOT)), str(SCENARIO_RESULTS_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S11P1T03",
            "name_zh": "建立质量评分与可信状态",
            "acceptance_zh": "权重和阈值外置；评分仅辅助；关键失败不能被高分掩盖。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(SCORE_POLICY_PATH.relative_to(REPO_ROOT)), str(SCENARIO_RESULTS_PATH.relative_to(REPO_ROOT))],
        },
    ]
    return {
        "schema_version": "kmfa.v015.s11p1.task_acceptance_matrix.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "task_count": 3,
        "task_accepted_count": 3 if final else 0,
        "phase_acceptance_status": status,
        "tasks": tasks,
    }


def _manifest(
    final: bool,
    rows: list[dict[str, Any]],
    run_id: str | None,
    head: str | None,
    verification: dict[str, Any],
) -> dict[str, Any]:
    acceptance = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    return {
        "schema_version": "kmfa.v015.s11p1.quality_rules_manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "version": kernel.VERSION,
        "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "phase_base_commit": PHASE_BASE_COMMIT,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": acceptance,
        "evidence_validation_status": "PASS" if final else "PENDING",
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 29 if final else 28,
        "overall_taskpack_phase_count": 72,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 33,
        "decision": "CONTINUE_TO_S11_P2_ONLY" if final else "REMAIN_IN_S11_P1_FINAL_VALIDATION",
        "quality_dimension_count": verification["dimension_count"],
        "quality_rule_count": verification["rule_count"],
        "quality_hard_gate_count": verification["hard_gate_count"],
        "quality_status_count": verification["status_count"],
        "quality_rule_weight_total_bps": verification["rule_weight_total_bps"],
        "quality_pass_min_bps": 9500,
        "quality_not_usable_below_bps": 7500,
        "live_check_accounting": verification["accounting"],
        "high_score_critical_failure_blocked": verification["scenario_results"]["high_score_critical_failure"]["display"]["label_zh"] == "不可使用",
        "human_status_labels": list(kernel.STATUS_LABELS_ZH),
        "technical_status_top_level_exposed": False,
        "color_used_as_only_information": False,
        "score_can_override_hard_gate": False,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "s11_p1_started": True,
        "s11_p1_acceptance_status": acceptance,
        "s11_p2_entry_allowed": final,
        "s11_p2_started": False,
        "s11_p3_entry_allowed": False,
        "s11_p3_started": False,
        "s11_stage_review_entry_allowed": False,
        "s11_stage_review_started": False,
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
    test_status = "全部通过" if final else "能力自检已通过，最终收据待生成"
    return {
        IMPLEMENTATION_REPORT_PATH: "\n".join([
            "# S11-P1 质量规则实现说明",
            "",
            f"状态：{status}。",
            "",
            "这次完成的是数据进入后续流程前的质量门卫。系统检查完整性、唯一性、范围、格式、关系、勾稽、新鲜度和一致性，并把结果翻译成普通人能直接理解的四种状态。",
            "",
            "- 16 条规则完整覆盖 8 类问题，每条都说明严重程度、会影响哪个流程、为什么失败和下一步怎么做。",
            "- 普通界面只需显示“已通过、需确认、不可使用、已过期”；技术编号放在专业详情中。",
            "- 颜色只是辅助，文字、符号、原因和下一步必须同时存在。",
            "- 总分仅用于辅助判断；任何关键门禁失败都会直接阻止使用。",
            "- 本轮只运行公开模拟计数，没有读取原始财务资料。",
        ]) + "\n",
        STATUS_GUIDE_PATH: "\n".join([
            "# 质量状态说明",
            "",
            "- 已通过：没有发现阻塞问题，可以继续质量流程。",
            "- 需确认：发现非关键问题，需要人工确认，确认前不正式发布。",
            "- 不可使用：关键问题失败，或未解决问题过多，必须先修复。",
            "- 已过期：来源超过允许更新时间，需要先获取最新数据。",
            "",
            "每个状态都必须同时显示文字、符号、原因、流程影响和下一步，不能只靠红黄绿颜色表达。",
        ]) + "\n",
        TEST_RESULTS_PATH: "\n".join([
            "# S11-P1 测试结果",
            "",
            f"状态：{test_status}。",
            "",
            f"- 能力自检：{verification['accounting']['passed']}/{verification['accounting']['total']} 通过。",
            "- 已覆盖全通过、高分但关键失败、需确认、已过期、低分但无关键失败五种场景。",
            "- 已证明 9375 分的关键失败仍显示“不可使用”，总分不能掩盖硬门禁。",
            "- 原始资料访问次数：0；真实来源读取次数：0；业务执行次数：0。",
        ]) + "\n",
        RISKS_ROLLBACK_PATH: "\n".join([
            "# 风险与回滚",
            "",
            "- 本阶段只建立规则和结果模型，不负责 S11-P2 的检查板数据层，也不负责 S11-P3 界面。",
            "- 当前规则使用汇总计数；未来接入真实来源时，必须由来源适配层提供这些计数，不能由界面伪造。",
            "- 权重或阈值变更会影响所有状态，任何调整都必须重跑五类场景和历史质量门禁回归。",
            "- 回滚只移除本阶段代码、测试、公开元数据和公开证据；不触碰原始文件，也不影响已通过的 S10。",
        ]) + "\n",
    }


def expected_outputs() -> dict[Path, str]:
    dependency()
    rows = receipts()
    final, run_id, head = final_binding(rows)
    catalog = kernel.default_rule_catalog()
    status_model = kernel.default_status_model()
    score_policy = kernel.default_score_policy()
    verification = kernel.public_verification()
    if verification["accounting"]["failed"]:
        raise BuildError("S11-P1 public verification failed")
    scenario_results = {
        "schema_version": "kmfa.v015.s11p1.quality_scenario_results.v1",
        "scenario_count": len(verification["scenario_results"]),
        "scenarios": verification["scenario_results"],
        "accounting": verification["accounting"],
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
    }
    outputs = {
        RULE_CATALOG_PATH: _json(catalog),
        STATUS_MODEL_PATH: _json(status_model),
        SCORE_POLICY_PATH: _json(score_policy),
        SOURCE_CONTRACT_PATH: _json(_source_contract()),
        COVERAGE_PATH: _json(_coverage(catalog)),
        SCENARIO_RESULTS_PATH: _json(scenario_results),
        TASK_MATRIX_PATH: _json(_task_matrix(final)),
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
    print("PASS: S11-P1 deterministic public-safe evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
