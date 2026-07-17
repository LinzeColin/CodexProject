#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S12-P1."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s12_p1_project_cost_facts as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "2b16f56c63314b7f2ee86963b29d1b96aaf07695"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "legacy_fact_layer_regression",
    "amount_precision_regression",
    "s11_stage_review_regression",
    "s11_stage_review_dependency",
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

MANIFEST_PATH = MACHINE_ROOT / "s12_p1_project_cost_facts_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VERIFICATION_PATH = MACHINE_ROOT / "fact_layer_verification_public_safe.json"
CONSERVATION_PATH = MACHINE_ROOT / "cost_conservation_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

INCOME_CONTRACT_PATH = PROJECT_ROOT / "metadata/lineage/v015_s12_p1_income_fact_contract_public_safe.json"
COST_CONTRACT_PATH = PROJECT_ROOT / "metadata/lineage/v015_s12_p1_cost_fact_contract_public_safe.json"
POOL_CONTRACT_PATH = PROJECT_ROOT / "metadata/lineage/v015_s12_p1_unallocated_cost_pool_contract_public_safe.json"

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
FACT_GUIDE_PATH = HUMAN_ROOT / "fact_layer_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_MANIFEST_PATH = PROJECT_ROOT / "stage_artifacts/V015_S11_STAGE_REVIEW/machine/s11_stage_review_manifest.json"
DEPENDENCY_RECEIPTS_PATH = PROJECT_ROOT / "stage_artifacts/V015_S11_STAGE_REVIEW/machine/validation_results.jsonl"


class BuildError(RuntimeError):
    pass


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        raise BuildError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def dependency() -> dict[str, Any]:
    manifest = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    expected = {
        "run_phase_id": "V015_S11_STAGE_REVIEW",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "stage_lifecycle_status": "COMPLETED",
        "stage_acceptance_status": "PASSED",
        "decision": "GO_TO_S12_P1_ONLY",
        "s11_stage_review_performed": True,
        "s11_stage_review_acceptance_status": "PASSED",
        "s12_p1_entry_allowed": True,
        "s12_p1_started": False,
        "validation_receipt_count": 24,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S11 Stage Review dependency mismatch: " + ", ".join(mismatches))
    if len(rows) != 24 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S11 Stage Review receipts are not exactly 24 PASS records")
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S11 Stage Review validation head mismatch")
    if {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")}:
        raise BuildError("S11 Stage Review validation run mismatch")
    head = str(manifest.get("validation_head") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise BuildError("S11 Stage Review validation head invalid")
    if subprocess.run(["git", "merge-base", "--is-ancestor", head, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise BuildError("S11 Stage Review validation head is not reachable")
    return {
        "acceptance_status": "PASSED",
        "validation_head": head,
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": 24,
        "s12_p1_entry_allowed": True,
        "s12_p1_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S12-P1 validation receipt order mismatch")
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
        "schema_version": "kmfa.v015.s12p1.source_contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": "S12",
        "stage_name_zh": "项目成本事实层与计算引擎",
        "roadmap_phase_id": "S12-P1",
        "phase_name_zh": "事实层",
        "task_count": 3,
        "task_ids": ["S12P1T01", "S12P1T02", "S12P1T03"],
        "scope": ["项目收入事实", "项目成本事实", "未归集成本池"],
        "stop_conditions": ["口径未知不得合并", "未知成本进入未归集池", "总成本不守恒即失败"],
        "excluded": ["S12-P2 核心计算", "S12-P3 工程行业逻辑", "S12 整体复审", "正式报告", "GitHub 上传", "App 重装"],
    }


def _task_matrix(final: bool) -> dict[str, Any]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    result = "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION"
    tasks = [
        {
            "task_id": "S12P1T01",
            "name_zh": "建立项目收入事实",
            "acceptance_zh": "合同、变更、结算、开票和回款分层保存；含税或不含税及期间明确；未知口径不得合并。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(INCOME_CONTRACT_PATH.relative_to(REPO_ROOT)), str(VERIFICATION_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S12P1T02",
            "name_zh": "建立项目成本事实",
            "acceptance_zh": "至少十类工程成本可登记；来源、项目、主体、期间和分类可追溯；未知成本进入未归集池。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(COST_CONTRACT_PATH.relative_to(REPO_ROOT)), str(VERIFICATION_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S12P1T03",
            "name_zh": "建立未归集成本池",
            "acceptance_zh": "无法分配的成本显式保留；不丢失、不平均摊、不静默归类；总成本按整数分零差异守恒。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(POOL_CONTRACT_PATH.relative_to(REPO_ROOT)), str(CONSERVATION_PATH.relative_to(REPO_ROOT))],
        },
    ]
    return {
        "schema_version": "kmfa.v015.s12p1.task_acceptance_matrix.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "task_count": 3,
        "task_accepted_count": 3 if final else 0,
        "phase_acceptance_status": status,
        "tasks": tasks,
    }


def _conservation(verification: dict[str, Any]) -> dict[str, Any]:
    summary = verification["summary"]
    return {
        "schema_version": "kmfa.v015.s12p1.cost_conservation.v1",
        "fixture_class": "PUBLIC_SAFE_SYNTHETIC",
        "input_cost_fact_count": summary["input_cost_fact_count"],
        "allocated_cost_fact_count": summary["allocated_cost_fact_count"],
        "unallocated_cost_pool_count": summary["unallocated_cost_pool_count"],
        "input_cost_cents": summary["input_cost_cents"],
        "allocated_cost_cents": summary["allocated_cost_cents"],
        "unallocated_cost_cents": summary["unallocated_cost_cents"],
        "conservation_delta_cents": summary["conservation_delta_cents"],
        "dropped_cost_fact_count": summary["dropped_cost_fact_count"],
        "average_allocation_count": summary["average_allocation_count"],
        "silent_classification_count": summary["silent_classification_count"],
        "money_tolerance_cents": 0,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
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
        "schema_version": "kmfa.v015.s12p1.project_cost_facts_manifest.v1",
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
        "overall_accepted_phase_count": 32 if final else 31,
        "overall_taskpack_phase_count": 72,
        "decision": "CONTINUE_TO_S12_P2_ONLY" if final else "REMAIN_IN_S12_P1_FINAL_VALIDATION",
        "income_layer_count": verification["income_layer_count"],
        "income_fact_count": summary["income_fact_count"],
        "income_merge_eligible_count": summary["income_merge_eligible_count"],
        "income_unknown_basis_count": summary["income_unknown_basis_count"],
        "unknown_income_merge_allowed": verification["unknown_income_merge_allowed"],
        "cross_layer_income_merge_allowed": verification["cross_layer_income_merge_allowed"],
        "cost_category_count": verification["cost_category_count"],
        "traceability_field_count": verification["traceability_field_count"],
        "allocated_cost_fact_count": summary["allocated_cost_fact_count"],
        "unallocated_cost_pool_count": summary["unallocated_cost_pool_count"],
        "unallocated_reason_code_count": verification["unallocated_reason_code_count"],
        "input_cost_cents": summary["input_cost_cents"],
        "allocated_cost_cents": summary["allocated_cost_cents"],
        "unallocated_cost_cents": summary["unallocated_cost_cents"],
        "conservation_delta_cents": summary["conservation_delta_cents"],
        "dropped_cost_fact_count": summary["dropped_cost_fact_count"],
        "average_allocation_count": summary["average_allocation_count"],
        "silent_classification_count": summary["silent_classification_count"],
        "money_tolerance_cents": 0,
        "public_check_accounting": verification["accounting"],
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "s12_p1_started": True,
        "s12_p1_acceptance_status": acceptance,
        "s12_p2_entry_allowed": final,
        "s12_p2_started": False,
        "s12_p3_entry_allowed": False,
        "s12_p3_started": False,
        "s12_stage_review_entry_allowed": False,
        "s12_stage_review_started": False,
        "formal_calculation_performed": False,
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
    summary = verification["summary"]
    return {
        IMPLEMENTATION_REPORT_PATH: "\n".join([
            "# S12-P1 项目成本事实层实现说明",
            "",
            f"状态：{status}。",
            "",
            "这次建立的是项目收入和成本的底账。收入按合同、变更、结算、开票和回款分别保存，不会把不同含义、税口径或期间的数字混成一个数。",
            "",
            "- 收入事实必须写清项目、公司主体、期间、来源版本以及含税或不含税。口径未知时保留记录，但禁止合并。",
            "- 成本支持人工、材料、机械、外协、运输、差旅、税费、现场管理、返工和质保十类。",
            "- 项目、期间或分类无法确认的成本会进入未归集池，不会被平均摊到其他项目，也不会被系统猜成某一类。",
            "- 所有金额只用整数分；模拟成本输入、已归集和未归集之间的差额为 0 分。",
            "- 本轮只使用公开模拟记录，没有读取原始财务资料或真实来源。",
        ]) + "\n",
        FACT_GUIDE_PATH: "\n".join([
            "# 项目收入与成本怎么保存",
            "",
            "收入不会只保存一个“收入合计”，而是分别保留合同、变更、结算、开票和回款。只有项目、公司、期间、收入层和含税口径完全一致时，才允许在同一层内小计。",
            "",
            "成本先按十类登记。只要项目、公司、期间或分类有一项不能确认，就进入未归集池，并明确写出原因。未归集池中的金额仍计入总成本守恒检查，因此不会消失。",
            "",
            "本阶段不计算毛利、现金毛利或成本完整度；这些属于下一次独立 Run 的 S12-P2。",
        ]) + "\n",
        TEST_RESULTS_PATH: "\n".join([
            "# S12-P1 测试结果",
            "",
            f"状态：{test_status}。",
            "",
            f"- 能力自检：{verification['accounting']['passed']}/{verification['accounting']['total']} 通过。",
            f"- 收入事实：{summary['income_fact_count']} 条模拟记录，完整覆盖 5 个收入层；1 条未知口径记录被禁止合并。",
            f"- 成本事实：{summary['allocated_cost_fact_count']} 条已归集记录，覆盖 10 类成本；{summary['unallocated_cost_pool_count']} 条进入未归集池。",
            f"- 守恒：输入 {summary['input_cost_cents']} 分 = 已归集 {summary['allocated_cost_cents']} 分 + 未归集 {summary['unallocated_cost_cents']} 分；差额 {summary['conservation_delta_cents']} 分。",
            "- 已验证 float、布尔金额、猜测分类、私有路径、静默覆盖、跨层合并和未知口径合并都会被拒绝。",
            "- 原始资料访问次数：0；真实来源读取次数：0；业务执行次数：0。",
        ]) + "\n",
        RISKS_ROLLBACK_PATH: "\n".join([
            "# 风险与回滚",
            "",
            "- 本阶段只建立事实底账，不计算合同毛利、结算毛利、现金毛利或成本完整度，也不生成正式报告。",
            "- 当前验收使用公开模拟记录；后续接入真实来源时必须沿用同一字段、整数分、来源版本和守恒规则。",
            "- 未归集成本只是诚实保留，不能冒充已归属成本；后续分配必须经过独立的人工确认流程。",
            "- 回滚只移除本阶段代码、测试、公开规则和公开证据；不触碰原始资料、S11 证据、远端仓库或已安装 App。",
        ]) + "\n",
    }


def expected_outputs() -> dict[Path, str]:
    dependency()
    rows = receipts()
    final, run_id, head = final_binding(rows)
    contracts = kernel.public_schema_contracts()
    verification = kernel.public_verification()
    if verification["accounting"]["failed"]:
        raise BuildError("S12-P1 public verification failed")
    outputs = {
        INCOME_CONTRACT_PATH: _json({
            "schema_version": "kmfa.v015.s12p1.income_fact_contract.v1",
            "fact_contract": contracts["income_fact"],
            "raw_root_access_count": 0,
            "live_source_read_count": 0,
        }),
        COST_CONTRACT_PATH: _json({
            "schema_version": "kmfa.v015.s12p1.cost_fact_contract.v1",
            "fact_contract": contracts["cost_fact"],
            "raw_root_access_count": 0,
            "live_source_read_count": 0,
        }),
        POOL_CONTRACT_PATH: _json({
            "schema_version": "kmfa.v015.s12p1.unallocated_cost_pool_contract.v1",
            "pool_contract": contracts["unallocated_cost_pool"],
            "raw_root_access_count": 0,
            "live_source_read_count": 0,
        }),
        SOURCE_CONTRACT_PATH: _json(_source_contract()),
        TASK_MATRIX_PATH: _json(_task_matrix(final)),
        VERIFICATION_PATH: _json(verification),
        CONSERVATION_PATH: _json(_conservation(verification)),
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
    print("PASS: S12-P1 deterministic public-safe evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
