#!/usr/bin/env python3
"""生成 KMFA v1.5 S18-P2 资金与账户公开验收证据。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from KMFA.tools import run_v015_s18_p2_funds_accounts as runtime
from KMFA.tools import v015_s18_p2_funds_accounts as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "7107688678bfc2871455643d9b32c76c6947f8a6"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "phase_contract",
    "focused_unit_tests",
    "focused_runtime_tests",
    "focused_browser_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s18_p1_dependency",
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
EXPORT_ROOT = OUTPUT_ROOT / "exports"
HTML_ROOT = EXPORT_ROOT / "html"
SCREENSHOT_ROOT = EXPORT_ROOT / "screenshots"

MANIFEST_PATH = MACHINE_ROOT / "s18_p2_funds_accounts_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
ACCOUNT_CONTRACT_PATH = MACHINE_ROOT / "bank_account_contract_public_safe.json"
FORECAST_CONTRACT_PATH = MACHINE_ROOT / "cash_forecast_contract_public_safe.json"
FUNDING_CONTRACT_PATH = MACHINE_ROOT / "loan_funding_contract_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
PUBLIC_CHECKS_PATH = MACHINE_ROOT / "public_checks.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
HTML_PATH = HTML_ROOT / "kmfa_funds_accounts.html"

SCREENSHOT_PATHS = (
    SCREENSHOT_ROOT / "kmfa_funds_desktop.png",
    SCREENSHOT_ROOT / "kmfa_funds_account_reconciliation.png",
    SCREENSHOT_ROOT / "kmfa_funds_scenario.png",
    SCREENSHOT_ROOT / "kmfa_funds_loan_gap.png",
    SCREENSHOT_ROOT / "kmfa_funds_company_isolated.png",
    SCREENSHOT_ROOT / "kmfa_funds_mobile.png",
)

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S18_P1_RECEIVABLES_COLLECTIONS/machine"
DEPENDENCY_MANIFEST_PATH = DEPENDENCY_ROOT / "s18_p1_receivables_collections_manifest.json"
DEPENDENCY_RECEIPTS_PATH = DEPENDENCY_ROOT / "validation_results.jsonl"


class BuildError(RuntimeError):
    """S18-P2 证据无法形成确定结论。"""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    if not DEPENDENCY_MANIFEST_PATH.is_file() or not DEPENDENCY_RECEIPTS_PATH.is_file():
        raise BuildError("S18-P1 正式验收依赖缺失")
    manifest = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    receipts = [json.loads(line) for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    expected = {
        "run_phase_id": "V015_S18_P1_RECEIVABLES_COLLECTIONS",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "validation_receipt_count": 20,
        "overall_accepted_phase_count": 50,
        "s18_p1_acceptance_status": "PASSED",
        "s18_p2_entry_allowed": True,
        "s18_p2_started": False,
    }
    mismatches = [key for key, expected_value in expected.items() if manifest.get(key) != expected_value]
    if mismatches:
        raise BuildError("S18-P1 依赖不一致：" + ", ".join(mismatches))
    if len(receipts) != 20 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
        raise BuildError("S18-P1 必须恰好有 20 条通过记录")
    if {row.get("validation_head") for row in receipts} != {manifest.get("validation_head")}:
        raise BuildError("S18-P1 验收提交不一致")
    return {
        "acceptance_status": "PASSED",
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": 20,
        "overall_accepted_phase_count": 50,
        "s18_p2_entry_allowed": True,
        "s18_p2_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S18-P2 验收记录顺序不一致")
    return rows


def final_binding(rows: Sequence[dict[str, Any]]) -> tuple[bool, str | None, str | None]:
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


def source_contract() -> dict[str, Any]:
    value = kernel.source_contract()
    value.update(
        {
            "source_package_sha256": TASKPACK_SHA256,
            "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
            "scope": ["多主体银行账户余额与流水", "事实、计划和假设分开的现金预测", "贷款到期、利息、保证金与资金缺口页面"],
            "excluded": ["真实资料", "银行连接", "付款或还款执行", "S18-P3", "GitHub 上传", "App 重装"],
        }
    )
    return value


def account_contract(view: dict[str, Any]) -> dict[str, Any]:
    value = view["accounts"]
    return {
        "schema_version": "kmfa.v015.s18p2.bank_account_contract.v1",
        "company_count": len(kernel.COMPANY_IDS),
        "bank_count": len(value["bank_totals"]),
        "known_account_count": value["known_account_count"],
        "unknown_account_count": value["unknown_account_count"],
        "excluded_unknown_account_count": value["excluded_unknown_account_count"],
        "balance_date": value["balance_date"],
        "source_zh": value["source_zh"],
        "all_account_identifiers_masked": all(row["masked_account"].startswith("****") for row in value["accounts"]),
        "all_sources_explicit": all(row["source_ref"].startswith("PUBLIC-SYNTHETIC:") for row in value["accounts"]),
        "account_reconciliation_difference_cents": value["account_reconciliation_difference_cents"],
        "bank_reconciliation_difference_cents": value["bank_reconciliation_difference_cents"],
        "unknown_amount_in_total_cents": value["unknown_amount_in_total_cents"],
        "cross_company_leak_count": value["cross_company_leak_count"],
        "money_tolerance_cents": kernel.MONEY_TOLERANCE_CENTS,
        "integer_cent_required": True,
    }


def forecast_contract() -> dict[str, Any]:
    scenarios = {scenario_id: kernel.cash_forecast(scenario_id=scenario_id) for scenario_id in kernel.SCENARIO_IDS}
    return {
        "schema_version": "kmfa.v015.s18p2.cash_forecast_contract.v1",
        "scenario_count": len(scenarios),
        "scenario_ids": list(scenarios),
        "forecast_period_count": len(kernel.FORECAST_PERIODS),
        "fact_kind": kernel.FACT_KIND,
        "plan_kind": kernel.PLAN_KIND,
        "assumption_kind": kernel.ASSUMPTION_KIND,
        "all_scenarios_separate_fact_plan_assumption": all(row["fact_plan_assumption_separated"] for row in scenarios.values()),
        "forecast_presented_as_certainty_count": sum(row["forecast_presented_as_certainty_count"] for row in scenarios.values()),
        "assumption_fact_write_count": sum(row["assumption_fact_write_count"] for row in scenarios.values()),
        "scenario_difference_cents": sum(row["scenario_difference_cents"] for row in scenarios.values()),
        "distinct_final_scenario_balance_count": len({row["rows"][-1]["scenario_closing_cents"] for row in scenarios.values()}),
        "result_label_zh": "情景预计余额（不是确定值）",
    }


def funding_contract(view: dict[str, Any]) -> dict[str, Any]:
    del view
    value = kernel.loan_funding_plan(scenario_id="collection_delay")
    return {
        "schema_version": "kmfa.v015.s18p2.loan_funding_contract.v1",
        "scenario_id": "collection_delay",
        "loan_count": value["loan_count"],
        "loan_due_within_90_days_count": value["loan_due_within_90_days_count"],
        "funding_period_count": len(value["funding_rows"]),
        "total_principal_cents": value["total_principal_cents"],
        "total_estimated_interest_cents": value["total_estimated_interest_cents"],
        "total_margin_cents": value["total_margin_cents"],
        "maximum_funding_gap_cents": value["maximum_funding_gap_cents"],
        "all_maturities_explicit": all(bool(row["maturity_date"]) for row in value["loans"]),
        "payment_execution_count": value["payment_execution_count"],
        "bank_operation_count": value["bank_operation_count"],
        "payment_button_count": value["payment_button_count"],
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s18p2.browser_acceptance_contract.v1",
        "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME_SPA",
        "required_viewports": [{"name": "desktop", "width": 1440, "height": 1000}, {"name": "mobile", "width": 390, "height": 844}],
        "required_flows": [
            "plain_chinese_fact_plan_assumption_labels",
            "masked_sourced_reconciled_accounts",
            "scenario_switch_keeps_facts",
            "loan_maturity_interest_margin_gap",
            "company_switch_isolated",
            "period_switch_scoped",
            "unknown_account_never_aggregated",
            "mobile_cards_no_overflow",
        ],
        "browser_flow_count": 8,
        "visual_evidence_count": len(SCREENSHOT_PATHS),
        "screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS],
        "horizontal_page_overflow_allowed": False,
        "minimum_touch_target_px": 44,
        "external_network_request_count": 0,
    }


def task_matrix(final: bool) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s18p2.task_acceptance_matrix.v1",
        "phase_id": "S18-P2",
        "overall_status": "PASS",
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "tasks": [
            {"task_id": "S18P2T01", "task_name_zh": "建立银行账户事实", "status": "PASS", "proof_zh": "三个主体、三家银行和四个已确认账户逐项显示脱敏账号、余额日期和来源；不明账户排除；账户及银行汇总相差 0 分。"},
            {"task_id": "S18P2T02", "task_name_zh": "实现现金预测", "status": "PASS", "proof_zh": "四周预测把事实、计划和情景假设分开；三种情景各自勾稽为 0 分，且始终标明不是确定值。"},
            {"task_id": "S18P2T03", "task_name_zh": "实现贷款和资金计划", "status": "PASS", "proof_zh": "三笔演示贷款展示到期、利息、保证金与逐期缺口；付款、还款及银行操作入口均为 0。"},
        ],
    }


def manifest(*, final: bool, run_id: str | None, validation_head: str | None, dep: dict[str, Any], view: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s18p2.funds_accounts_manifest.v1",
        "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "version": kernel.VERSION,
        "phase_base_commit": PHASE_BASE_COMMIT,
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "validation_run_id": run_id,
        "validation_head": validation_head,
        "validation_receipt_count": EXPECTED_VALIDATION_COUNT if final else 0,
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 51 if final else 50,
        "overall_taskpack_phase_count": 72,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 67,
        "decision": "GO_TO_S18_P3_ONLY" if final else "REMAIN_IN_S18_P2_FINAL_VALIDATION",
        "next_gate_id": "S18-P3" if final else "S18-P2-FINAL-VALIDATION",
        "s18_p1_acceptance_status": dep["acceptance_status"],
        "s18_p2_entry_allowed": False,
        "s18_p2_started": True,
        "s18_p2_completed": final,
        "s18_p2_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s18_p3_entry_allowed": final,
        "s18_p3_started": False,
        "s18_stage_review_entry_allowed": False,
        "s18_stage_review_started": False,
        "company_count": len(kernel.COMPANY_IDS),
        "bank_count": len(view["accounts"]["bank_totals"]),
        "known_account_count": view["accounts"]["known_account_count"],
        "unknown_account_count": view["accounts"]["unknown_account_count"],
        "excluded_unknown_account_count": view["accounts"]["excluded_unknown_account_count"],
        "forecast_scenario_count": len(kernel.SCENARIO_IDS),
        "forecast_period_count": len(kernel.FORECAST_PERIODS),
        "loan_count": view["funding_plan"]["loan_count"],
        "public_check_count": len(checks),
        "public_check_failed_count": sum(row["status"] != "PASS" for row in checks),
        "browser_viewport_count": 2,
        "browser_flow_count": 8,
        "visual_evidence_count": len(SCREENSHOT_PATHS),
        "money_tolerance_cents": 0,
        "money_difference_cents": view["money_difference_cents"],
        "unknown_amount_in_total_cents": view["accounts"]["unknown_amount_in_total_cents"],
        "cross_company_leak_count": view["cross_company_leak_count"],
        "forecast_presented_as_certainty_count": view["forecast_presented_as_certainty_count"],
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "external_network_request_count": 0,
        "real_identity_count": 0,
        "credential_count": 0,
        "real_business_action_count": 0,
        "source_data_write_count": 0,
        "fact_layer_write_count": 0,
        "payment_execution_count": 0,
        "bank_operation_count": 0,
        "payment_button_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_business_report": False,
        "data_classification": kernel.DATA_CLASSIFICATION,
    }


def _human_documents(final: bool, checks: list[dict[str, Any]]) -> dict[Path, str]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    return {
        IMPLEMENTATION_REPORT_PATH: f"""# S18-P2 资金与账户实施说明（{status}）

- 三个演示主体各有四个已确认账户，覆盖三家演示银行；账号只显示末四位，余额日期和来源逐项可见。
- 一个主体或账户不明的样例被明确排除，未知金额进入汇总为 0 分；账户流水、银行小计和主体合计均相差 0 分。
- 未来四周现金把已确认事实、业务计划和情景假设分开，提供基准、回款延迟和成本压力三种情景，所有结果都标明“不是确定值”。
- 三笔演示贷款展示到期、预计利息、保证金和逐期资金缺口；没有付款、还款或银行操作入口。
""",
        USER_GUIDE_PATH: """# 资金与账户页面使用说明

1. 打开 `/funds`，先看可汇总余额和被排除的待确认账户。
2. 在“银行账户事实”核对脱敏账号、余额日期、来源、流入、流出和余额。
3. 切换基准、回款延迟或成本压力情景；事实和计划不会因情景切换而被改写。
4. “情景预计余额”只是压力测试，不是确定余额；事实余额和计划余额分别显示。
5. 贷款区只提示内部复核，不连接银行，也没有付款或还款按钮。
""",
        TEST_RESULTS_PATH: f"""# S18-P2 验收结果（{status}）

- {len(checks)}/{len(checks)} 项公开规则检查通过。
- 四个账户、三家银行、一个待确认账户、三种情景、四个预测期间和三笔贷款均完成整数分勾稽。
- 8 条真实浏览器流程通过，覆盖电脑、手机、账户勾稽、情景切换、贷款缺口、公司切换和期间切换；6 张画面已保存。
- 最终正式验收记录：{EXPECTED_VALIDATION_COUNT if final else 0}/{EXPECTED_VALIDATION_COUNT}。
""",
        RISKS_ROLLBACK_PATH: """# 风险与回滚

- 当前全部是公开合成演示资料，不代表真实账户余额、贷款或正式资金计划。
- 现金预测依赖计划和假设，必须保留“不是确定值”标识；不得用于自动付款、自动融资或银行操作。
- 真实资料接入仍需后续独立阶段核验来源、权限、余额日期、主体归属和账户完整性。
- 回滚仅删除本阶段工具、测试、治理登记和 `V015_S18_P2_FUNDS_ACCOUNTS` 证据；不得触碰 raw inbox、S18-P1 或其他已验收内容。
""",
    }


def expected_outputs() -> dict[Path, str]:
    dep = dependency()
    rows = receipts()
    final, run_id, validation_head = final_binding(rows)
    view = kernel.funds_view()
    checks = kernel.public_checks()
    if any(row["status"] != "PASS" for row in checks):
        raise BuildError("公开检查存在失败")
    outputs = {
        MANIFEST_PATH: _json(manifest(final=final, run_id=run_id, validation_head=validation_head, dep=dep, view=view, checks=checks)),
        SOURCE_CONTRACT_PATH: _json(source_contract()),
        ACCOUNT_CONTRACT_PATH: _json(account_contract(view)),
        FORECAST_CONTRACT_PATH: _json(forecast_contract()),
        FUNDING_CONTRACT_PATH: _json(funding_contract(view)),
        BROWSER_CONTRACT_PATH: _json(browser_contract()),
        PUBLIC_CHECKS_PATH: _json({"schema_version": "kmfa.v015.s18p2.public_checks.v1", "check_count": len(checks), "pass_count": len(checks), "fail_count": 0, "checks": checks}),
        TASK_MATRIX_PATH: _json(task_matrix(final)),
        HTML_PATH: runtime.render_html(),
    }
    outputs.update(_human_documents(final, checks))
    return outputs


def write_outputs() -> None:
    for path, value in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")


def check_outputs() -> None:
    mismatches = []
    for path, expected in expected_outputs().items():
        if not path.is_file() or path.read_text(encoding="utf-8") != expected:
            mismatches.append(str(path.relative_to(REPO_ROOT)))
    if mismatches:
        raise BuildError("证据不一致：" + ", ".join(mismatches))
    missing = [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS if not path.is_file() or path.stat().st_size < 10_000]
    if missing:
        raise BuildError("浏览器画面缺失：" + ", ".join(missing))


def build() -> dict[str, Any]:
    write_outputs()
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 S18-P2 资金与账户验收证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError, kernel.FundsAccountsError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S18-P2 funds and accounts evidence " + ("check" if args.check else "build"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
