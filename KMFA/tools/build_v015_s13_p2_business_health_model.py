#!/usr/bin/env python3
"""生成 KMFA v1.5 S13-P2 的确定性公开安全证据。"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s13_p2_business_health_model as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "dc609d7990f14330bee8c27340a6ec1909add1a4"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s13_p1_regression",
    "s13_p1_dependency",
    "health_model_self_check",
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

MANIFEST_PATH = MACHINE_ROOT / "s13_p2_business_health_model_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VERIFICATION_PATH = MACHINE_ROOT / "business_health_model_verification_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

DIMENSION_REGISTRY_PATH = PROJECT_ROOT / "metadata/quality/v015_s13_p2_health_dimension_registry_public_safe.json"
SCORING_CONTRACT_PATH = PROJECT_ROOT / "metadata/quality/v015_s13_p2_health_scoring_contract_public_safe.json"
SCENARIO_CONTRACT_PATH = PROJECT_ROOT / "metadata/quality/v015_s13_p2_scenario_contract_public_safe.json"

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
HEALTH_GUIDE_PATH = HUMAN_ROOT / "health_score_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_MANIFEST_PATH = PROJECT_ROOT / "stage_artifacts/V015_S13_P1_INDICATOR_REGISTRY/machine/s13_p1_indicator_registry_manifest.json"
DEPENDENCY_RECEIPTS_PATH = PROJECT_ROOT / "stage_artifacts/V015_S13_P1_INDICATOR_REGISTRY/machine/validation_results.jsonl"


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
        "run_phase_id": "V015_S13_P1_INDICATOR_REGISTRY",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 33,
        "decision": "CONTINUE_TO_S13_P2_ONLY",
        "s13_p1_started": True,
        "s13_p1_acceptance_status": "PASSED",
        "s13_p2_entry_allowed": True,
        "s13_p2_started": False,
        "validation_receipt_count": 20,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S13-P1 dependency mismatch: " + ", ".join(mismatches))
    if len(rows) != 20 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S13-P1 receipts are not exactly 20 PASS records")
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S13-P1 validation head mismatch")
    if {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")}:
        raise BuildError("S13-P1 validation run mismatch")
    head = str(manifest.get("validation_head") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise BuildError("S13-P1 validation head invalid")
    if subprocess.run(["git", "merge-base", "--is-ancestor", head, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise BuildError("S13-P1 validation head is not reachable")
    return {
        "acceptance_status": "PASSED",
        "validation_head": head,
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": 20,
        "s13_p2_entry_allowed": True,
        "s13_p2_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S13-P2 validation receipt order mismatch")
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
        "schema_version": "kmfa.v015.s13p2.source_contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": "S13",
        "stage_name_zh": "经营指标、健康模型与行动优先级",
        "roadmap_phase_id": "S13-P2",
        "phase_name_zh": "经营健康模型",
        "task_count": 3,
        "task_ids": ["S13P2T01", "S13P2T02", "S13P2T03"],
        "scope": ["六个健康维度", "分项解释与数据新鲜度", "三类情景和敏感性分析"],
        "stop_conditions": ["评分不能替代硬门禁", "无法解释的分数不显示", "假设不得写回事实层"],
        "excluded": ["S13-P3 行动优先级", "S13 整体复审", "真实经营结论", "业务动作", "正式报告", "GitHub 上传", "App 重装"],
    }


def _task_matrix(final: bool) -> dict[str, Any]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    result = "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION"
    tasks = [
        {
            "task_id": "S13P2T01",
            "name_zh": "实现健康维度",
            "acceptance_zh": "现金安全、项目利润、回款质量、税务政策、合同履约和数据完整度六维权重合计 10000，分数范围为 0 至 10000，硬门禁优先。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(DIMENSION_REGISTRY_PATH.relative_to(REPO_ROOT)), str(VERIFICATION_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S13P2T02",
            "name_zh": "实现分项解释",
            "acceptance_zh": "每个分数都绑定主要贡献因素、来源指纹和数据新鲜度，当前与比较期的变化可以逐项解释；无法解释时不显示。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(SCORING_CONTRACT_PATH.relative_to(REPO_ROOT)), str(VERIFICATION_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S13P2T03",
            "name_zh": "实现情景和敏感性分析",
            "acceptance_zh": "回款延迟、成本上涨和收入下降三类情景全部把事实、假设和投影分开，事实层写入为 0。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(SCENARIO_CONTRACT_PATH.relative_to(REPO_ROOT)), str(VERIFICATION_PATH.relative_to(REPO_ROOT))],
        },
    ]
    return {
        "schema_version": "kmfa.v015.s13p2.task_acceptance_matrix.v1",
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
    summary = verification["summary"]
    return {
        "schema_version": "kmfa.v015.s13p2.business_health_model_manifest.v1",
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
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 67,
        "stage_phase_pass_count": 2 if final else 1,
        "stage_task_accepted_count": 6 if final else 3,
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 36 if final else 35,
        "overall_taskpack_phase_count": 72,
        "decision": "CONTINUE_TO_S13_P3_ONLY" if final else "REMAIN_IN_S13_P2_FINAL_VALIDATION",
        "health_dimension_count": summary["dimension_count"],
        "health_weight_total_bps": summary["weight_total_bps"],
        "hard_gate_count": summary["hard_gate_count"],
        "health_state_count": summary["health_state_count"],
        "freshness_state_count": summary["freshness_state_count"],
        "scenario_count": summary["scenario_count"],
        "unexplained_change_count": summary["unexplained_change_count"],
        "fact_layer_write_count": summary["fact_layer_write_count"],
        "public_check_accounting": verification["accounting"],
        "hard_gate_overrides_score": True,
        "unexplained_score_display_allowed": False,
        "fact_and_assumption_separated": True,
        "health_model_implemented": True,
        "synthetic_health_score_computed": True,
        "real_business_health_score_computed": False,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "s13_p1_started": True,
        "s13_p1_acceptance_status": "PASSED",
        "s13_p2_started": True,
        "s13_p2_acceptance_status": acceptance,
        "s13_p3_entry_allowed": final,
        "s13_p3_started": False,
        "s13_stage_review_entry_allowed": False,
        "s13_stage_review_started": False,
        "action_priority_computed": False,
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
    test_status = "全部通过" if final else "能力自检已通过，最终验收记录待生成"
    accounting = verification["accounting"]
    return {
        IMPLEMENTATION_REPORT_PATH: "\n".join([
            "# S13-P2 经营健康模型",
            "",
            f"状态：{status}。",
            "",
            "这一步建立的是判断规则，不是对你的真实企业作出健康结论。",
            "",
            "- 健康模型分为现金安全、项目利润、回款质量、税务政策、合同履约和数据完整度六部分，权重合计 10000。",
            "- 硬门禁优先于分数；数据完整度等关键条件失败时，即使其他项目高分也不会显示综合分。",
            "- 每个分项都说明主要贡献因素、资料日期和新鲜度，并能解释与比较期相比为什么上升或下降。",
            "- 回款延迟、成本上涨和收入下降三类情景都明确标记为假设，只生成投影，不改写事实。",
            "- 本轮只使用公开模拟值，没有读取原始财务资料，也没有生成行动排序或执行任何业务动作。",
        ]) + "\n",
        HEALTH_GUIDE_PATH: "\n".join([
            "# 健康分怎么理解",
            "",
            "综合分只是六个分项的加权摘要，不能代替关键门禁。如果资料过期、缺少解释或关键条件失败，系统会直接隐藏综合分并说明原因。",
            "",
            "情景分析不是事实。例如“回款延迟 30 天”只是在一份独立假设里观察现金和应收可能怎样变化，不会修改已经确认的回款、收入或成本。",
            "",
            "本阶段不生成行动建议。行动排序属于下一次独立工作 S13-P3。",
        ]) + "\n",
        TEST_RESULTS_PATH: "\n".join([
            "# S13-P2 测试结果",
            "",
            f"状态：{test_status}。",
            "",
            f"- 公开模拟自检：{accounting['passed']}/{accounting['total']} 通过。",
            "- 六个维度权重合计 10000，所有分项和综合分均限制在 0 至 10000。",
            "- 已验证高分不能覆盖硬门禁、过期资料不显示综合分、无法解释的分数会被拒绝。",
            "- 已验证所有分数变化均能定位到贡献因素和来源，未解释变化数为 0。",
            "- 三类敏感性情景均保持事实不变，事实层写入次数为 0。",
            "- 原始资料访问次数：0；真实来源读取次数：0；业务执行次数：0。",
        ]) + "\n",
        RISKS_ROLLBACK_PATH: "\n".join([
            "# 风险与回滚",
            "",
            "- 当前结果只证明模型规则在公开模拟值下正确，不代表真实企业健康状况。",
            "- 权重、阈值和硬门禁都需要未来用真实但受控的验收资料校准；校准必须形成新版本，不能覆盖历史。",
            "- 税务政策维度只提供风险信号，不构成税务、申报或法律结论。",
            "- 回滚只移除本阶段代码、测试、公开规则和证据，不触碰原始资料、S13-P1、远端仓库或已安装 App。",
        ]) + "\n",
    }


def expected_outputs() -> dict[Path, str]:
    dependency()
    rows = receipts()
    final, run_id, head = final_binding(rows)
    dimensions = kernel.health_dimensions()
    dimension_summary = kernel.validate_health_dimensions(dimensions)
    verification = kernel.public_verification()
    if verification["accounting"] != {"total": 88, "passed": 88, "failed": 0} or verification["failed_checks"]:
        raise BuildError("S13-P2 public verification failed")
    outputs = {
        DIMENSION_REGISTRY_PATH: _json({
            "schema_version": "kmfa.v015.s13p2.health_dimension_registry.v1",
            "dimensions": dimensions,
            "registry_summary": dimension_summary,
            "hard_gate_overrides_score": True,
            "raw_root_access_count": 0,
            "live_source_read_count": 0,
        }),
        SCORING_CONTRACT_PATH: _json({
            "schema_version": "kmfa.v015.s13p2.health_scoring_contract.v1",
            "health_states": list(kernel.HEALTH_STATES),
            "freshness_states": list(kernel.FRESHNESS_STATES),
            "score_range_bps": [0, 10_000],
            "weight_total_bps": 10_000,
            "hard_gate_overrides_score": True,
            "unexplained_score_display_allowed": False,
            "sample_health_result": verification["sample_health_result"],
            "sample_change_explanation": verification["sample_change_explanation"],
        }),
        SCENARIO_CONTRACT_PATH: _json({
            "schema_version": "kmfa.v015.s13p2.scenario_contract.v1",
            "scenario_types": list(kernel.SCENARIO_TYPES),
            "fact_and_assumption_separated": True,
            "assumption_written_to_fact_layer": False,
            "sample_sensitivity_analysis": verification["sample_sensitivity_analysis"],
        }),
        SOURCE_CONTRACT_PATH: _json(_source_contract()),
        TASK_MATRIX_PATH: _json(_task_matrix(final)),
        VERIFICATION_PATH: _json(verification),
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
    print("PASS: S13-P2 deterministic public-safe evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
