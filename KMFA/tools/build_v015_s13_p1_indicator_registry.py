#!/usr/bin/env python3
"""生成 KMFA v1.5 S13-P1 的确定性公开安全证据。"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s13_p1_indicator_registry as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "e121d922c3550b091a54cace86d1a551a635f4f2"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s12_stage_review_regression",
    "s12_stage_review_dependency",
    "function_boundary_self_check",
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

MANIFEST_PATH = MACHINE_ROOT / "s13_p1_indicator_registry_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VERIFICATION_PATH = MACHINE_ROOT / "indicator_registry_verification_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

INDICATOR_REGISTRY_PATH = PROJECT_ROOT / "metadata/lineage/v015_s13_p1_indicator_registry_public_safe.json"
PARAMETER_VERSIONS_PATH = PROJECT_ROOT / "metadata/quality/v015_s13_p1_parameter_versions_public_safe.json"
FUNCTION_CONTRACT_PATH = PROJECT_ROOT / "metadata/quality/v015_s13_p1_function_contract_public_safe.json"

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
INDICATOR_GUIDE_PATH = HUMAN_ROOT / "indicator_rules_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_MANIFEST_PATH = PROJECT_ROOT / "stage_artifacts/V015_S12_STAGE_REVIEW/machine/s12_stage_review_manifest.json"
DEPENDENCY_RECEIPTS_PATH = PROJECT_ROOT / "stage_artifacts/V015_S12_STAGE_REVIEW/machine/validation_results.jsonl"


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
        "run_phase_id": "V015_S12_STAGE_REVIEW",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "stage_lifecycle_status": "COMPLETED",
        "stage_acceptance_status": "PASSED",
        "decision": "GO_TO_S13_P1_ONLY",
        "s12_stage_review_performed": True,
        "s12_stage_review_acceptance_status": "PASSED",
        "s13_entry_allowed": True,
        "s13_p1_entry_allowed": True,
        "s13_p1_started": False,
        "validation_receipt_count": 24,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S12 Stage Review dependency mismatch: " + ", ".join(mismatches))
    if len(rows) != 24 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S12 Stage Review receipts are not exactly 24 PASS records")
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S12 Stage Review validation head mismatch")
    if {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")}:
        raise BuildError("S12 Stage Review validation run mismatch")
    head = str(manifest.get("validation_head") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise BuildError("S12 Stage Review validation head invalid")
    if subprocess.run(["git", "merge-base", "--is-ancestor", head, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise BuildError("S12 Stage Review validation head is not reachable")
    return {
        "acceptance_status": "PASSED",
        "validation_head": head,
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": 24,
        "s13_p1_entry_allowed": True,
        "s13_p1_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S13-P1 validation receipt order mismatch")
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
        "schema_version": "kmfa.v015.s13p1.source_contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": "S13",
        "stage_name_zh": "经营指标、健康模型与行动优先级",
        "roadmap_phase_id": "S13-P1",
        "phase_name_zh": "指标注册表",
        "task_count": 3,
        "task_ids": ["S13P1T01", "S13P1T02", "S13P1T03"],
        "scope": ["指标定义", "参数与阈值版本", "函数库与边界条件"],
        "stop_conditions": ["无来源指标不得显示", "前端不得直接改生产参数", "异常不得被默默吞掉"],
        "excluded": ["S13-P2 经营健康模型", "S13-P3 行动优先级", "S13 整体复审", "真实经营计算", "正式报告", "GitHub 上传", "App 重装"],
    }


def _task_matrix(final: bool) -> dict[str, Any]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    result = "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION"
    tasks = [
        {
            "task_id": "S13P1T01",
            "name_zh": "建立指标定义",
            "acceptance_zh": "收入、成本、毛利、回款、现金、税务、履约和数据质量均有公式、单位、期间、来源与限制；无来源不得显示。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(INDICATOR_REGISTRY_PATH.relative_to(REPO_ROOT)), str(VERIFICATION_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S13P1T02",
            "name_zh": "建立参数与阈值版本",
            "acceptance_zh": "每个外置参数都有版本、生效日、变更理由、审批引用和回归用例；前端和生产环境均不得直接改写。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(PARAMETER_VERSIONS_PATH.relative_to(REPO_ROOT)), str(VERIFICATION_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S13P1T03",
            "name_zh": "建立函数库与边界条件",
            "acceptance_zh": "比率、趋势、桥接、排序、缺失处理统一；除零、负数、小样本和缺失返回明确状态，异常不被静默吞掉。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(FUNCTION_CONTRACT_PATH.relative_to(REPO_ROOT)), str(VERIFICATION_PATH.relative_to(REPO_ROOT))],
        },
    ]
    return {
        "schema_version": "kmfa.v015.s13p1.task_acceptance_matrix.v1",
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
        "schema_version": "kmfa.v015.s13p1.indicator_registry_manifest.v1",
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
        "stage_execution_percentage": 33,
        "stage_phase_pass_count": 1 if final else 0,
        "stage_task_accepted_count": 3 if final else 0,
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 35 if final else 34,
        "overall_taskpack_phase_count": 72,
        "decision": "CONTINUE_TO_S13_P2_ONLY" if final else "REMAIN_IN_S13_P1_FINAL_VALIDATION",
        "indicator_count": summary["indicator_count"],
        "indicator_domain_count": summary["domain_count"],
        "parameter_version_count": summary["parameter_count"],
        "function_contract_count": summary["function_count"],
        "result_status_count": summary["result_status_count"],
        "public_check_accounting": verification["accounting"],
        "source_required_for_display": True,
        "frontend_parameter_write_allowed": False,
        "production_direct_parameter_write_allowed": False,
        "silent_exception_allowed": False,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "s13_p1_started": True,
        "s13_p1_acceptance_status": acceptance,
        "s13_p2_entry_allowed": final,
        "s13_p2_started": False,
        "s13_p3_entry_allowed": False,
        "s13_p3_started": False,
        "s13_stage_review_entry_allowed": False,
        "s13_stage_review_started": False,
        "health_score_computed": False,
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
            "# S13-P1 经营指标统一规则",
            "",
            f"状态：{status}。",
            "",
            "这一步没有计算你的真实经营结果，而是先把以后所有经营分析必须遵守的规则统一起来。",
            "",
            "- 已登记收入、成本、毛利、回款、现金、税务、履约和数据质量八类指标。每一项都写清公式、单位、期间、来源和局限。",
            "- 没有来源的指标一律不显示，缺失值也不能被系统偷换成 0。",
            "- 参数修改必须有新版本、理由、审批引用和回归测试；前端不能直接修改生产参数。",
            "- 分母为 0、负分母、小样本、缺失和非法类型都有明确结果，不会被静默忽略。",
            "- 本轮只使用公开模拟值，没有读取原始财务资料，也没有生成健康分或行动建议。",
        ]) + "\n",
        INDICATOR_GUIDE_PATH: "\n".join([
            "# 指标规则怎么理解",
            "",
            "一个指标只有在“公式、单位、期间、来源、限制”全部齐全时才有资格显示。例如回款率必须说明分子是已确认回款、分母是已开票金额；分母为 0 时显示“无法计算”，不能显示成 0%。",
            "",
            "参数不是界面里随手可改的设置。每次改动都必须形成新版本，并留下原因、审批依据和回归测试。这样以后看到结果变化时，可以追溯到底是业务数据变了，还是规则变了。",
            "",
            "本阶段只统一定义和计算边界。经营健康分属于下一次独立工作 S13-P2，行动优先级属于 S13-P3。",
        ]) + "\n",
        TEST_RESULTS_PATH: "\n".join([
            "# S13-P1 测试结果",
            "",
            f"状态：{test_status}。",
            "",
            f"- 公开模拟自检：{accounting['passed']}/{accounting['total']} 通过。",
            "- 指标：8 类领域全部覆盖，所有指标均有来源和限制，无来源显示被拒绝。",
            "- 参数：8 个外置参数均有版本、理由、审批引用和回归用例，直接改写被拒绝。",
            "- 函数：比率、趋势、桥接、排序和缺失处理 5 类规则均已登记。",
            "- 已验证除零、负分母、负数、小样本、缺失、float、布尔值、重复版本冲突和私有路径都会得到明确处理。",
            "- 原始资料访问次数：0；真实来源读取次数：0；业务执行次数：0。",
        ]) + "\n",
        RISKS_ROLLBACK_PATH: "\n".join([
            "# 风险与回滚",
            "",
            "- 这些规则目前只通过公开模拟值验收，不代表真实经营数据已经接入或经营结论已经生成。",
            "- 负数在不同业务语境可能有不同含义；当前默认保留符号，负分母必须单独授权，避免误读。",
            "- 小样本下限是外置规则，后续健康模型如需不同下限，必须新建参数版本并回归，不能覆盖现有版本。",
            "- 回滚只移除本阶段代码、测试、公开规则和证据，不触碰原始资料、S12 证据、远端仓库或已安装 App。",
        ]) + "\n",
    }


def expected_outputs() -> dict[Path, str]:
    dependency()
    rows = receipts()
    final, run_id, head = final_binding(rows)
    indicators = kernel.indicator_registry()
    parameters = kernel.parameter_versions()
    functions = kernel.function_contracts()
    verification = kernel.public_verification()
    if verification["accounting"]["failed"]:
        raise BuildError("S13-P1 public verification failed")
    outputs = {
        INDICATOR_REGISTRY_PATH: _json({
            "schema_version": "kmfa.v015.s13p1.indicator_registry.v1",
            "indicators": indicators,
            "registry_summary": kernel.validate_indicator_registry(indicators),
            "raw_root_access_count": 0,
            "live_source_read_count": 0,
        }),
        PARAMETER_VERSIONS_PATH: _json({
            "schema_version": "kmfa.v015.s13p1.parameter_versions.v1",
            "parameters": parameters,
            "registry_summary": kernel.validate_parameter_versions(parameters),
            "frontend_write_allowed": False,
            "production_direct_write_allowed": False,
        }),
        FUNCTION_CONTRACT_PATH: _json({
            "schema_version": "kmfa.v015.s13p1.function_contracts.v1",
            "functions": functions,
            "registry_summary": kernel.validate_function_contracts(functions),
            "silent_exception_allowed": False,
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
    print("PASS: S13-P1 deterministic public-safe evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
