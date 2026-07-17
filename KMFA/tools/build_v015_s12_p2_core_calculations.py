#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S12-P2."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s12_p2_core_calculations as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "ab65ca3b666c835a1b25ff6bb2664c8adf6ca366"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "legacy_margin_regression",
    "amount_precision_regression",
    "s12_p1_kernel_regression",
    "s12_p1_dependency",
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

MANIFEST_PATH = MACHINE_ROOT / "s12_p2_core_calculations_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VERIFICATION_PATH = MACHINE_ROOT / "core_calculation_verification_public_safe.json"
MARGIN_BASELINE_PATH = MACHINE_ROOT / "margin_golden_baseline_public_safe.json"
CASH_CHAIN_PATH = MACHINE_ROOT / "cash_chain_verification_public_safe.json"
RISK_RULE_PATH = MACHINE_ROOT / "cost_risk_verification_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

MARGIN_CONTRACT_PATH = PROJECT_ROOT / "metadata/lineage/v015_s12_p2_margin_basis_contract_public_safe.json"
CASH_CONTRACT_PATH = PROJECT_ROOT / "metadata/lineage/v015_s12_p2_cash_metrics_contract_public_safe.json"
RISK_POLICY_PATH = PROJECT_ROOT / "metadata/quality/v015_s12_p2_cost_risk_policy_public_safe.json"

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
CALCULATION_GUIDE_PATH = HUMAN_ROOT / "calculation_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_MANIFEST_PATH = PROJECT_ROOT / "stage_artifacts/V015_S12_P1_PROJECT_COST_FACTS/machine/s12_p1_project_cost_facts_manifest.json"
DEPENDENCY_RECEIPTS_PATH = PROJECT_ROOT / "stage_artifacts/V015_S12_P1_PROJECT_COST_FACTS/machine/validation_results.jsonl"


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
        "run_phase_id": "V015_S12_P1_PROJECT_COST_FACTS",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 33,
        "decision": "CONTINUE_TO_S12_P2_ONLY",
        "s12_p1_acceptance_status": "PASSED",
        "s12_p2_entry_allowed": True,
        "s12_p2_started": False,
        "s12_p3_entry_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "validation_receipt_count": 21,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S12-P1 dependency mismatch: " + ", ".join(mismatches))
    if len(rows) != 21 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S12-P1 receipts are not exactly 21 PASS records")
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S12-P1 validation head mismatch")
    if {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")}:
        raise BuildError("S12-P1 validation run mismatch")
    head = str(manifest.get("validation_head") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise BuildError("S12-P1 validation head invalid")
    if subprocess.run(["git", "merge-base", "--is-ancestor", head, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise BuildError("S12-P1 validation head is not reachable")
    return {
        "acceptance_status": "PASSED",
        "validation_head": head,
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": 21,
        "s12_p2_entry_allowed": True,
        "s12_p2_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S12-P2 validation receipt order mismatch")
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
        "schema_version": "kmfa.v015.s12p2.source_contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": "S12",
        "stage_name_zh": "项目成本事实层与计算引擎",
        "roadmap_phase_id": "S12-P2",
        "phase_name_zh": "核心计算",
        "task_count": 3,
        "task_ids": ["S12P2T01", "S12P2T02", "S12P2T03"],
        "scope": ["合同结算管理毛利", "现金毛利与资金占用", "成本完整度与异常"],
        "stop_conditions": ["任一分差异失败", "账户或主体不明则降级", "缺数据不得生成确定性结论"],
        "excluded": ["S12-P3 工程行业逻辑", "S12 整体复审", "真实业务计算", "正式报告", "GitHub 上传", "App 重装"],
    }


def _task_matrix(final: bool) -> dict[str, Any]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    result = "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION"
    tasks = [
        {
            "task_id": "S12P2T01",
            "name_zh": "实现合同、结算和管理毛利",
            "acceptance_zh": "三个毛利视图使用明确且不同的收入、成本口径；整数分计算；与公开黄金基准零分差异。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(MARGIN_CONTRACT_PATH.relative_to(REPO_ROOT)), str(MARGIN_BASELINE_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S12P2T02",
            "name_zh": "实现现金毛利和资金占用",
            "acceptance_zh": "现金收入只取银行确认回款；未回款发票和应收不计现金；账户或主体不明时降级并禁止业务决策。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(CASH_CONTRACT_PATH.relative_to(REPO_ROOT)), str(CASH_CHAIN_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S12P2T03",
            "name_zh": "实现成本完整度和异常",
            "acceptance_zh": "四项阈值位于外置版本化规则中且可调整；缺少比较期成本或管理毛利时只返回资料不足。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(RISK_POLICY_PATH.relative_to(REPO_ROOT)), str(RISK_RULE_PATH.relative_to(REPO_ROOT))],
        },
    ]
    return {
        "schema_version": "kmfa.v015.s12p2.task_acceptance_matrix.v1",
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
    margin = verification["margin_results"]
    cash = verification["cash_results"]
    risk = verification["risk_results"]
    return {
        "schema_version": "kmfa.v015.s12p2.core_calculations_manifest.v1",
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
        "overall_accepted_phase_count": 33 if final else 32,
        "overall_taskpack_phase_count": 72,
        "decision": "CONTINUE_TO_S12_P3_ONLY" if final else "REMAIN_IN_S12_P2_FINAL_VALIDATION",
        "margin_view_count": len(margin["views"]),
        "margin_golden_difference_cents": 0,
        "margin_money_tolerance_cents": 0,
        "contract_gross_profit_cents": margin["views"]["contract"]["gross_profit_cents"],
        "settlement_gross_profit_cents": margin["views"]["settlement"]["gross_profit_cents"],
        "management_gross_profit_cents": margin["views"]["management"]["gross_profit_cents"],
        "cash_gross_profit_cents": cash["cash_gross_profit_cents"],
        "capital_occupied_cents": cash["capital_occupied_cents"],
        "uncollected_amount_counted_as_cash_cents": cash["uncollected_amount_counted_as_cash_cents"],
        "degraded_cash_case_count": 1,
        "risk_policy_threshold_count": 4,
        "default_risk_trigger_count": len(risk["triggered_rule_codes"]),
        "relaxed_risk_trigger_count": len(verification["relaxed_risk_results"]["triggered_rule_codes"]),
        "insufficient_data_case_count": 1,
        "public_check_accounting": verification["accounting"],
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "s12_p1_started": True,
        "s12_p1_acceptance_status": "PASSED",
        "s12_p2_started": True,
        "s12_p2_acceptance_status": acceptance,
        "s12_p3_entry_allowed": final,
        "s12_p3_started": False,
        "s12_stage_review_entry_allowed": False,
        "s12_stage_review_started": False,
        "core_calculation_implemented": True,
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
    cash = verification["cash_results"]
    return {
        IMPLEMENTATION_REPORT_PATH: "\n".join([
            "# S12-P2 核心计算实现说明",
            "",
            f"状态：{status}。",
            "",
            "这次完成的是项目经营计算的核心，不接触真实财务资料。合同毛利、结算毛利和管理毛利分别计算，系统不会把三种口径混成一个数。",
            "",
            "- 所有金额都用整数分计算，公开黄金样例的三个毛利结果差额均为 0 分。",
            "- 现金毛利只认银行已经确认的回款和付款；开了票但没收到的钱、普通应收都不会冒充现金。",
            "- 资金占用同时考虑已付款、质保金、未结算应收和已回款。账户或公司主体不清时，结果自动降级，不能用于业务决策。",
            "- 成本完整度、未归集比例、成本波动和低毛利使用外置阈值；缺资料时只返回“资料不足”，不会假装给出确定结论。",
            "- 本轮没有读取原始财务资料，没有执行真实业务计算，也没有上传 GitHub 或重装 App。",
        ]) + "\n",
        CALCULATION_GUIDE_PATH: "\n".join([
            "# 核心计算怎么理解",
            "",
            "合同毛利回答“按合同和目标成本预计能赚多少”；结算毛利回答“按已确认结算和匹配成本能赚多少”；管理毛利回答“按管理口径本期确认收入和成本能赚多少”。三者用途不同，必须分开看。",
            "",
            "现金毛利只看已经收到和已经付出的现金。资金占用为已付款、质保金和未结算应收合计，再减已确认回款；结果为负时显示现金净结余。",
            "",
            "风险判断只有资料齐全时才会明确显示正常或预警。比较期成本、管理毛利等关键资料缺失时，系统只显示资料不足。",
        ]) + "\n",
        TEST_RESULTS_PATH: "\n".join([
            "# S12-P2 测试结果",
            "",
            f"状态：{test_status}。",
            "",
            f"- 能力自检：{verification['accounting']['passed']}/{verification['accounting']['total']} 通过。",
            "- 三个毛利视图：合同 30000 分、结算 20000 分、管理 15000 分；黄金基准差额 0 分。",
            f"- 现金链：现金毛利 {cash['cash_gross_profit_cents']} 分，资金占用 {cash['capital_occupied_cents']} 分，未回款计入现金 0 分。",
            "- 降级测试：账户不明时禁止业务决策。",
            "- 风险规则：默认阈值触发四项预警；调整外置阈值后可变为无预警；缺少比较期资料时只返回资料不足。",
            "- 原始资料访问次数：0；真实来源读取次数：0；真实业务计算次数：0。",
        ]) + "\n",
        RISKS_ROLLBACK_PATH: "\n".join([
            "# 风险与回滚",
            "",
            "- 本阶段只实现计算规则并使用公开模拟样例，不代表已对真实项目生成经营结论。",
            "- 三类毛利口径必须由调用方明确提供；未知口径会被拒绝，不由系统猜测。",
            "- 风险阈值可以调整，但每次结果都绑定规则版本；缺少关键资料时不得改成确定性预警或正常。",
            "- 回滚只移除本阶段代码、测试、公开规则和公开证据；不触碰 S12-P1、原始资料、远端仓库或已安装 App。",
        ]) + "\n",
    }


def expected_outputs() -> dict[Path, str]:
    dependency()
    rows = receipts()
    final, run_id, head = final_binding(rows)
    verification = kernel.public_verification()
    if verification["accounting"]["failed"]:
        raise BuildError("S12-P2 public verification failed")
    outputs = {
        MARGIN_CONTRACT_PATH: _json({
            **kernel.margin_contract(),
            "raw_root_access_count": 0,
            "live_source_read_count": 0,
        }),
        CASH_CONTRACT_PATH: _json({
            **kernel.cash_contract(),
            "raw_root_access_count": 0,
            "live_source_read_count": 0,
        }),
        RISK_POLICY_PATH: _json({
            **kernel.validate_risk_policy(kernel.DEFAULT_RISK_POLICY),
            "thresholds_external_and_adjustable": True,
            "missing_data_deterministic_conclusion_allowed": False,
            "raw_root_access_count": 0,
            "live_source_read_count": 0,
        }),
        SOURCE_CONTRACT_PATH: _json(_source_contract()),
        TASK_MATRIX_PATH: _json(_task_matrix(final)),
        VERIFICATION_PATH: _json(verification),
        MARGIN_BASELINE_PATH: _json({
            "schema_version": "kmfa.v015.s12p2.margin_golden_baseline.v1",
            "fixture_class": "PUBLIC_SAFE_SYNTHETIC",
            "results": verification["margin_results"],
            "comparison": verification["margin_golden_comparison"],
        }),
        CASH_CHAIN_PATH: _json({
            "schema_version": "kmfa.v015.s12p2.cash_chain_verification.v1",
            "fixture_class": "PUBLIC_SAFE_SYNTHETIC",
            "confirmed_case": verification["cash_results"],
            "unresolved_account_case": verification["degraded_cash_results"],
        }),
        RISK_RULE_PATH: _json({
            "schema_version": "kmfa.v015.s12p2.cost_risk_verification.v1",
            "fixture_class": "PUBLIC_SAFE_SYNTHETIC",
            "default_policy_case": verification["risk_results"],
            "adjusted_policy_case": verification["relaxed_risk_results"],
            "missing_data_case": verification["missing_data_risk_results"],
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
    print("PASS: S12-P2 deterministic public-safe evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
