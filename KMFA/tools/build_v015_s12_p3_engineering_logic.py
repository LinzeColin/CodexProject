#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S12-P3."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s12_p3_engineering_logic as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "c70fc4903e21638ec3c4d9e2dc005b0d7a254a68"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s12_p1_kernel_regression",
    "s12_p2_kernel_regression",
    "s12_p2_dependency",
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
    "explanation_consistency",
    "git_diff_check",
)
EXPECTED_VALIDATION_COUNT = len(EXPECTED_VALIDATION_NAMES)

OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / kernel.RUN_PHASE_ID
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"

MANIFEST_PATH = MACHINE_ROOT / "s12_p3_engineering_logic_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VERIFICATION_PATH = MACHINE_ROOT / "engineering_logic_verification_public_safe.json"
CHANGE_CHAIN_PATH = MACHINE_ROOT / "change_settlement_chain_public_safe.json"
COST_CHAIN_PATH = MACHINE_ROOT / "external_cost_chain_public_safe.json"
EXPLANATION_PATH = MACHINE_ROOT / "result_explanation_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

CHANGE_CONTRACT_PATH = PROJECT_ROOT / "metadata/lineage/v015_s12_p3_change_chain_contract_public_safe.json"
COST_CONTRACT_PATH = PROJECT_ROOT / "metadata/lineage/v015_s12_p3_external_cost_chain_contract_public_safe.json"
EXPLANATION_CONTRACT_PATH = PROJECT_ROOT / "metadata/lineage/v015_s12_p3_explanation_contract_public_safe.json"
LINK_POLICY_PATH = PROJECT_ROOT / "metadata/quality/v015_s12_p3_cost_link_policy_public_safe.json"

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
ENGINEERING_GUIDE_PATH = HUMAN_ROOT / "engineering_logic_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_MANIFEST_PATH = PROJECT_ROOT / "stage_artifacts/V015_S12_P2_CORE_CALCULATIONS/machine/s12_p2_core_calculations_manifest.json"
DEPENDENCY_RECEIPTS_PATH = PROJECT_ROOT / "stage_artifacts/V015_S12_P2_CORE_CALCULATIONS/machine/validation_results.jsonl"


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
        "run_phase_id": "V015_S12_P2_CORE_CALCULATIONS",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 67,
        "decision": "CONTINUE_TO_S12_P3_ONLY",
        "s12_p1_acceptance_status": "PASSED",
        "s12_p2_acceptance_status": "PASSED",
        "s12_p3_entry_allowed": True,
        "s12_p3_started": False,
        "s12_stage_review_entry_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "validation_receipt_count": 21,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S12-P2 dependency mismatch: " + ", ".join(mismatches))
    if len(rows) != 21 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S12-P2 receipts are not exactly 21 PASS records")
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S12-P2 validation head mismatch")
    if {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")}:
        raise BuildError("S12-P2 validation run mismatch")
    head = str(manifest.get("validation_head") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise BuildError("S12-P2 validation head invalid")
    if subprocess.run(["git", "merge-base", "--is-ancestor", head, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise BuildError("S12-P2 validation head is not reachable")
    return {
        "acceptance_status": "PASSED",
        "validation_head": head,
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": 21,
        "s12_p3_entry_allowed": True,
        "s12_p3_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S12-P3 validation receipt order mismatch")
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
        "schema_version": "kmfa.v015.s12p3.source_contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": "S12",
        "stage_name_zh": "项目成本事实层与计算引擎",
        "roadmap_phase_id": "S12-P3",
        "phase_name_zh": "工程行业逻辑",
        "task_count": 3,
        "task_ids": ["S12P3T01", "S12P3T02", "S12P3T03"],
        "scope": ["签证变更与结算链", "委外采购库存付款成本链", "项目成本解释层"],
        "stop_conditions": ["变更无依据不得计收入", "自动归集低置信需确认", "解释与计算不一致失败"],
        "excluded": ["S12 整体复审", "S13", "真实业务计算", "正式报告", "GitHub 上传", "App 重装"],
    }


def _task_matrix(final: bool) -> dict[str, Any]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    result = "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION"
    tasks = [
        {
            "task_id": "S12P3T01",
            "name_zh": "实现签证变更与结算链",
            "acceptance_zh": "合同、项目、变更、结算、发票和回款全部同链；无依据变更不计收入；未确认变更、结算差异和回收率可见。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(CHANGE_CONTRACT_PATH.relative_to(REPO_ROOT)), str(CHANGE_CHAIN_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S12P3T02",
            "name_zh": "实现委外与采购关联",
            "acceptance_zh": "外协、采购、领料、库存和付款按项目关联；重复、未归集和跨项目异常均可识别；低置信不自动归集。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(COST_CONTRACT_PATH.relative_to(REPO_ROOT)), str(LINK_POLICY_PATH.relative_to(REPO_ROOT)), str(COST_CHAIN_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S12P3T03",
            "name_zh": "实现项目成本解释层",
            "acceptance_zh": "每个结果都能重算到事实和公式；专业用户看逐层追溯，普通用户看中文摘要；任何不一致都会失败。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(EXPLANATION_CONTRACT_PATH.relative_to(REPO_ROOT)), str(EXPLANATION_PATH.relative_to(REPO_ROOT))],
        },
    ]
    return {
        "schema_version": "kmfa.v015.s12p3.task_acceptance_matrix.v1",
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
    change = verification["change_settlement_result"]
    cost = verification["external_cost_result"]
    explanations = verification["explanation_result"]
    consistency = verification["explanation_consistency"]
    return {
        "schema_version": "kmfa.v015.s12p3.engineering_logic_manifest.v1",
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
        "stage_execution_percentage": 100,
        "stage_phase_pass_count": 3 if final else 2,
        "stage_task_accepted_count": 9 if final else 6,
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 34 if final else 33,
        "overall_taskpack_phase_count": 72,
        "decision": "GO_TO_S12_STAGE_REVIEW_ONLY" if final else "REMAIN_IN_S12_P3_FINAL_VALIDATION",
        "change_chain_node_count": change["chain_node_count"],
        "confirmed_change_count": change["confirmed_change_count"],
        "unconfirmed_change_count": change["unconfirmed_change_count"],
        "confirmed_change_amount_cents": change["confirmed_change_amount_cents"],
        "unconfirmed_change_amount_cents": change["unconfirmed_change_amount_cents"],
        "unsupported_change_recognized_cents": change["unsupported_change_recognized_cents"],
        "settlement_difference_cents": change["settlement_difference_cents"],
        "invoice_collection_rate_bps": change["invoice_collection_rate_bps"],
        "external_cost_record_count": cost["record_count"],
        "duplicate_record_count": cost["duplicate_record_count"],
        "requires_confirmation_count": cost["requires_confirmation_count"],
        "cross_project_anomaly_count": cost["cross_project_anomaly_count"],
        "automatic_low_confidence_allocation_count": cost["automatic_low_confidence_allocation_count"],
        "recognized_project_cost_cents": cost["recognized_project_cost_cents"],
        "inventory_conservation_delta_cents": cost["inventory_conservation_delta_cents"],
        "explanation_count": explanations["explanation_count"],
        "explanation_match_count": consistency["matched_result_count"],
        "explanation_mismatch_count": consistency["mismatch_count"],
        "public_check_accounting": verification["accounting"],
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "s12_p1_started": True,
        "s12_p1_acceptance_status": "PASSED",
        "s12_p2_started": True,
        "s12_p2_acceptance_status": "PASSED",
        "s12_p3_started": True,
        "s12_p3_acceptance_status": acceptance,
        "s12_stage_review_entry_allowed": final,
        "s12_stage_review_started": False,
        "engineering_logic_implemented": True,
        "real_business_calculation_performed": False,
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
    change = verification["change_settlement_result"]
    cost = verification["external_cost_result"]
    consistency = verification["explanation_consistency"]
    return {
        IMPLEMENTATION_REPORT_PATH: "\n".join([
            "# S12-P3 工程行业逻辑实现说明",
            "",
            f"状态：{status}。",
            "",
            "这次完成的是工程项目里最容易出错的三条链：变更和结算、委外采购和库存付款、计算结果解释。全部使用公开模拟数据，不接触真实财务资料。",
            "",
            "- 只有已经确认且有依据的变更才进入收入；未确认变更会单独保留，不会被悄悄算进去。",
            "- 合同、项目、变更、结算、发票和回款必须全部对得上；公开样例结算差异为 -5000 分，开票回收率为 77.78%。",
            "- 外协、采购、入库、领料、库存和付款分别记录；重复记录不重复计算，未归集和跨项目异常会直接暴露。",
            "- 低置信关联必须人工确认，自动归集次数固定为 0。",
            "- 每个主要结果都有专业追溯和普通中文摘要；解释与重算结果不一致时立即失败。",
            "- 本轮没有执行 S12 整体复审、真实业务计算、GitHub 上传或 App 重装。",
        ]) + "\n",
        ENGINEERING_GUIDE_PATH: "\n".join([
            "# 工程行业逻辑怎么理解",
            "",
            "签证或变更只有在已经确认并且有依据时，才可以进入合同收入。未确认变更仍会展示，便于继续催办，但不会被当成已经赚到的钱。",
            "",
            "外协、采购、材料入库、材料领用、库存余额和付款代表不同业务动作，不能因为金额相同就混成一笔成本。系统会识别重复、未归集、跨项目和低置信关联。",
            "",
            "普通用户看到的是一句话摘要；专业用户可以继续展开，查看输入事实、计算公式和逐步重算过程。两层内容来自同一个计算结果。",
        ]) + "\n",
        TEST_RESULTS_PATH: "\n".join([
            "# S12-P3 测试结果",
            "",
            f"状态：{test_status}。",
            "",
            f"- 能力自检：{verification['accounting']['passed']}/{verification['accounting']['total']} 通过。",
            f"- 变更结算链：确认变更 {change['confirmed_change_amount_cents']} 分，未确认变更 {change['unconfirmed_change_amount_cents']} 分，无依据变更计收入 0 分。",
            f"- 结算与回款：结算差异 {change['settlement_difference_cents']} 分，开票回收率 {change['invoice_collection_rate_bps']} 基点。",
            f"- 委外采购链：识别重复 {cost['duplicate_record_count']} 项、待确认 {cost['requires_confirmation_count']} 项、跨项目异常 {cost['cross_project_anomaly_count']} 项，低置信自动归集 0 项。",
            f"- 解释一致性：{consistency['matched_result_count']}/{consistency['expected_result_count']} 项一致，不一致 {consistency['mismatch_count']} 项；篡改样例已被拦截。",
            "- 原始资料访问次数：0；真实来源读取次数：0；真实业务计算次数：0。",
        ]) + "\n",
        RISKS_ROLLBACK_PATH: "\n".join([
            "# 风险与回滚",
            "",
            "- 本阶段只验证规则和公开模拟链路，不代表已对真实项目确认收入、成本或回收率。",
            "- 无依据变更、低置信归集和跨项目关联都保持关闭，必须由后续真实证据和人工确认处理。",
            "- 解释层只能展示计算结果，不能覆盖或改写事实；任何不一致都使本阶段验收失败。",
            "- 回滚只移除本阶段代码、测试、公开规则和公开证据；不触碰 S12-P1/P2、原始资料、远端仓库或已安装 App。",
        ]) + "\n",
    }


def expected_outputs() -> dict[Path, str]:
    dependency()
    rows = receipts()
    final, run_id, head = final_binding(rows)
    verification = kernel.public_verification()
    if verification["accounting"]["failed"]:
        raise BuildError("S12-P3 public verification failed")
    outputs = {
        CHANGE_CONTRACT_PATH: _json({**kernel.change_chain_contract(), "raw_root_access_count": 0, "live_source_read_count": 0}),
        COST_CONTRACT_PATH: _json({**kernel.external_cost_chain_contract(), "raw_root_access_count": 0, "live_source_read_count": 0}),
        EXPLANATION_CONTRACT_PATH: _json({**kernel.explanation_contract(), "raw_root_access_count": 0, "live_source_read_count": 0}),
        LINK_POLICY_PATH: _json({**kernel.validate_link_policy(kernel.DEFAULT_LINK_POLICY), "threshold_external_and_adjustable": True, "raw_root_access_count": 0, "live_source_read_count": 0}),
        SOURCE_CONTRACT_PATH: _json(_source_contract()),
        TASK_MATRIX_PATH: _json(_task_matrix(final)),
        VERIFICATION_PATH: _json(verification),
        CHANGE_CHAIN_PATH: _json({
            "schema_version": "kmfa.v015.s12p3.change_chain_verification.v1",
            "fixture_class": "PUBLIC_SAFE_SYNTHETIC",
            "confirmed_case": verification["change_settlement_result"],
            "unresolved_collection_case": verification["degraded_change_result"],
        }),
        COST_CHAIN_PATH: _json({
            "schema_version": "kmfa.v015.s12p3.external_cost_chain_verification.v1",
            "fixture_class": "PUBLIC_SAFE_SYNTHETIC",
            "result": verification["external_cost_result"],
        }),
        EXPLANATION_PATH: _json({
            "schema_version": "kmfa.v015.s12p3.result_explanation_verification.v1",
            "fixture_class": "PUBLIC_SAFE_SYNTHETIC",
            "result": verification["explanation_result"],
            "consistency": verification["explanation_consistency"],
            "tampered_case_consistency": verification["tampered_explanation_consistency"],
        }),
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
    print("PASS: S12-P3 deterministic public-safe evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
