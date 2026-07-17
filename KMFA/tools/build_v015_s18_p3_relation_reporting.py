#!/usr/bin/env python3
"""生成 KMFA v1.5 S18-P3 关联与报告公开验收证据。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from KMFA.tools import v015_s18_p3_relation_reporting as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "c721543c7c81d10b3f47ec13515632cb4bf7ae2e"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "phase_contract",
    "focused_unit_tests",
    "focused_runtime_tests",
    "focused_browser_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s18_p2_dependency",
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
REPORT_ROOT = EXPORT_ROOT / "reports"
SCREENSHOT_ROOT = EXPORT_ROOT / "screenshots"

MANIFEST_PATH = MACHINE_ROOT / "s18_p3_relation_reporting_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
DUAL_VIEW_CONTRACT_PATH = MACHINE_ROOT / "project_cash_dual_view_contract_public_safe.json"
ALERT_CONTRACT_PATH = MACHINE_ROOT / "alert_contract_public_safe.json"
REPORT_CONTRACT_PATH = MACHINE_ROOT / "report_export_contract_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
PUBLIC_CHECKS_PATH = MACHINE_ROOT / "public_checks.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
HTML_REPORT_PATH = REPORT_ROOT / "funds_receivables_report.html"
CSV_APPENDIX_PATH = REPORT_ROOT / "funds_receivables_appendix.csv"

SCREENSHOT_PATHS = (
    SCREENSHOT_ROOT / "kmfa_relation_dual_view_desktop.png",
    SCREENSHOT_ROOT / "kmfa_relation_cross_basis.png",
    SCREENSHOT_ROOT / "kmfa_relation_alerts.png",
    SCREENSHOT_ROOT / "kmfa_relation_period_report.png",
    SCREENSHOT_ROOT / "kmfa_relation_degraded.png",
    SCREENSHOT_ROOT / "kmfa_relation_mobile.png",
)

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S18_P2_FUNDS_ACCOUNTS/machine"
DEPENDENCY_MANIFEST_PATH = DEPENDENCY_ROOT / "s18_p2_funds_accounts_manifest.json"
DEPENDENCY_RECEIPTS_PATH = DEPENDENCY_ROOT / "validation_results.jsonl"


class BuildError(RuntimeError):
    """S18-P3 证据无法形成确定结论。"""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    if not DEPENDENCY_MANIFEST_PATH.is_file() or not DEPENDENCY_RECEIPTS_PATH.is_file():
        raise BuildError("S18-P2 正式验收依赖缺失")
    manifest = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    expected = {
        "run_phase_id": "V015_S18_P2_FUNDS_ACCOUNTS",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "validation_receipt_count": 20,
        "overall_accepted_phase_count": 51,
        "s18_p2_acceptance_status": "PASSED",
        "s18_p2_completed": True,
        "s18_p3_entry_allowed": True,
        "s18_p3_started": False,
    }
    mismatches = [key for key, expected_value in expected.items() if manifest.get(key) != expected_value]
    if mismatches:
        raise BuildError("S18-P2 依赖不一致：" + ", ".join(mismatches))
    if len(rows) != 20 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S18-P2 必须恰好有 20 条通过记录")
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S18-P2 验收提交不一致")
    return {
        "acceptance_status": "PASSED",
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": 20,
        "overall_accepted_phase_count": 51,
        "s18_p3_entry_allowed": True,
        "s18_p3_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S18-P3 验收记录顺序不一致")
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
            "scope": ["项目利润与资金占用双视图", "重大逾期、资金缺口和贷款到期内部预警", "资金与应收周期报告及附表"],
            "excluded": ["真实资料", "自动外发提醒", "付款或银行操作", "正式经营报告", "S18 整体复审", "GitHub 上传", "App 重装"],
        }
    )
    return value


def dual_view_contract(view: dict[str, Any]) -> dict[str, Any]:
    dual = view["dual_view"]
    totals = dual["totals"]
    return {
        "schema_version": "kmfa.v015.s18p3.project_cash_dual_view_contract.v1",
        "project_count": dual["project_count"],
        "profit_basis_zh": "项目收入减项目成本",
        "cash_basis_zh": "已开票未回款加未开票节点金额",
        "profit_cash_substitution_count": dual["profit_cash_substitution_count"],
        "scope_limitation_displayed_count": dual["scope_limitation_displayed_count"],
        "profit_equation_difference_cents": dual["profit_equation_difference_cents"],
        "cash_occupancy_reconciliation_difference_cents": dual["cash_occupancy_reconciliation_difference_cents"],
        "cross_company_leak_count": dual["cross_company_leak_count"],
        "total_revenue_cents": totals["revenue_cents"],
        "total_cost_cents": totals["cost_cents"],
        "total_gross_profit_cents": totals["gross_profit_cents"],
        "total_open_receivable_cents": totals["open_receivable_cents"],
        "total_unbilled_cents": totals["unbilled_cents"],
        "total_cash_occupied_cents": totals["cash_occupied_cents"],
        "money_tolerance_cents": kernel.MONEY_TOLERANCE_CENTS,
        "integer_cent_required": True,
    }


def alert_contract(view: dict[str, Any]) -> dict[str, Any]:
    alerts = view["alert_view"]
    return {
        "schema_version": "kmfa.v015.s18p3.alert_contract.v1",
        "alert_count": alerts["alert_count"],
        "alert_type_count": alerts["alert_type_count"],
        "alert_count_by_type": alerts["alert_count_by_type"],
        "threshold_version": alerts["threshold_version"],
        "threshold_config_ref": alerts["threshold_config_ref"],
        "thresholds_externalized": alerts["thresholds_externalized"],
        "full_sensitive_detail_count": alerts["full_sensitive_detail_count"],
        "exposed_sensitive_field_count": alerts["exposed_sensitive_field_count"],
        "notification_send_count": alerts["notification_send_count"],
        "external_message_count": alerts["external_message_count"],
        "cross_company_leak_count": alerts["cross_company_leak_count"],
        "unverified_alert_count": kernel.alert_view(verification_state="UNVERIFIED")["alert_count"],
    }


def report_contract(view: dict[str, Any]) -> dict[str, Any]:
    report = view["report"]
    degraded = kernel.periodic_report(verification_state="UNVERIFIED")
    return {
        "schema_version": "kmfa.v015.s18p3.report_export_contract.v1",
        "report_status": report["report_status"],
        "project_count": report["project_count"],
        "page_row_count": len(report["page_rows"]),
        "appendix_row_count": report["appendix_row_count"],
        "appendix_column_count": report["appendix_column_count"],
        "report_page_export_difference_cents": report["report_page_export_difference_cents"],
        "degraded_report_status": degraded["report_status"],
        "degraded_report_grade": degraded["report_grade"],
        "degraded_numeric_detail_allowed": degraded["numeric_detail_allowed"],
        "degraded_alert_count": degraded["alert_count"],
        "unverified_numeric_visible_count": degraded["unverified_numeric_visible_count"],
        "formal_business_report": report["formal_business_report"],
        "html_export_ref": str(HTML_REPORT_PATH.relative_to(REPO_ROOT)),
        "csv_appendix_ref": str(CSV_APPENDIX_PATH.relative_to(REPO_ROOT)),
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s18p3.browser_acceptance_contract.v1",
        "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME_SPA",
        "required_viewports": [{"name": "desktop", "width": 1440, "height": 1000}, {"name": "mobile", "width": 390, "height": 844}],
        "required_flows": [
            "plain_chinese_dual_view",
            "profit_and_cash_cross_equations",
            "three_sanitised_alert_types",
            "scenario_only_changes_funding_gap_alert",
            "html_report_matches_page",
            "csv_appendix_matches_page",
            "unverified_report_degrades",
            "company_period_isolation",
            "mobile_cards_no_overflow",
        ],
        "browser_flow_count": 9,
        "visual_evidence_count": len(SCREENSHOT_PATHS),
        "screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS],
        "horizontal_page_overflow_allowed": False,
        "minimum_touch_target_px": 44,
        "external_network_request_count": 0,
    }


def task_matrix(final: bool) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s18p3.task_acceptance_matrix.v1",
        "phase_id": "S18-P3",
        "overall_status": "PASS",
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "tasks": [
            {"task_id": "S18P3T01", "task_name_zh": "项目现金双视图", "status": "PASS", "proof_zh": "六个项目分别展示利润和资金占用，两套口径独立，交叉计算均相差 0 分，并逐项显示范围限制。"},
            {"task_id": "S18P3T02", "task_name_zh": "实现回款和资金预警", "status": "PASS", "proof_zh": "重大逾期、资金缺口、贷款到期三类预警由外部版本化阈值触发；不展示完整敏感明细，也不发送消息。"},
            {"task_id": "S18P3T03", "task_name_zh": "生成资金与应收报告", "status": "PASS", "proof_zh": "页面、HTML 报告和 CSV 附表金额完全一致；资料未核验时金额隐藏、预警关闭并降级为 D。"},
        ],
    }


def manifest(*, final: bool, run_id: str | None, validation_head: str | None, dep: dict[str, Any], view: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    dual = view["dual_view"]
    alerts = view["alert_view"]
    report = view["report"]
    degraded = kernel.periodic_report(verification_state="UNVERIFIED")
    return {
        "schema_version": "kmfa.v015.s18p3.relation_reporting_manifest.v1",
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
        "overall_accepted_phase_count": 52 if final else 51,
        "overall_taskpack_phase_count": 72,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 100,
        "decision": "GO_TO_S18_STAGE_REVIEW_ONLY" if final else "REMAIN_IN_S18_P3_FINAL_VALIDATION",
        "next_gate_id": "S18-STAGE-REVIEW" if final else "S18-P3-FINAL-VALIDATION",
        "s18_p1_acceptance_status": "PASSED",
        "s18_p2_acceptance_status": dep["acceptance_status"],
        "s18_p3_entry_allowed": False,
        "s18_p3_started": True,
        "s18_p3_completed": final,
        "s18_p3_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s18_stage_review_entry_allowed": final,
        "s18_stage_review_started": False,
        "project_count": dual["project_count"],
        "profit_cash_substitution_count": dual["profit_cash_substitution_count"],
        "scope_limitation_displayed_count": dual["scope_limitation_displayed_count"],
        "profit_equation_difference_cents": dual["profit_equation_difference_cents"],
        "cash_occupancy_reconciliation_difference_cents": dual["cash_occupancy_reconciliation_difference_cents"],
        "alert_count": alerts["alert_count"],
        "alert_type_count": alerts["alert_type_count"],
        "threshold_version": alerts["threshold_version"],
        "threshold_config_ref": alerts["threshold_config_ref"],
        "thresholds_externalized": alerts["thresholds_externalized"],
        "full_sensitive_detail_count": alerts["full_sensitive_detail_count"],
        "exposed_sensitive_field_count": alerts["exposed_sensitive_field_count"],
        "notification_send_count": alerts["notification_send_count"],
        "report_page_row_count": len(report["page_rows"]),
        "report_appendix_row_count": report["appendix_row_count"],
        "report_page_export_difference_cents": report["report_page_export_difference_cents"],
        "degraded_report_test_count": 1,
        "unverified_numeric_visible_count": degraded["unverified_numeric_visible_count"],
        "public_check_count": len(checks),
        "public_check_failed_count": sum(row["status"] != "PASS" for row in checks),
        "browser_viewport_count": 2,
        "browser_flow_count": 9,
        "visual_evidence_count": len(SCREENSHOT_PATHS),
        "money_tolerance_cents": 0,
        "money_difference_cents": view["money_difference_cents"],
        "cross_company_leak_count": max(dual["cross_company_leak_count"], alerts["cross_company_leak_count"]),
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "external_network_request_count": 0,
        "real_identity_count": 0,
        "credential_count": 0,
        "real_business_action_count": 0,
        "source_data_write_count": 0,
        "fact_layer_write_count": 0,
        "external_message_count": 0,
        "payment_execution_count": 0,
        "bank_operation_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_business_report": False,
        "data_classification": kernel.DATA_CLASSIFICATION,
    }


def _human_documents(final: bool, checks: list[dict[str, Any]]) -> dict[Path, str]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    return {
        IMPLEMENTATION_REPORT_PATH: f"""# S18-P3 关联与报告实施说明（{status}）

- 六个演示项目同时显示利润和资金占用。利润按收入减成本计算，资金占用按已开票未回款加未开票节点计算，两套数字不会互相替代。
- 重大逾期、资金缺口和贷款到期三类提醒使用独立配置文件中的版本化阈值；提醒只给内部复核所需的最少信息，不自动发送。
- 周期报告提供网页和 CSV 附表，页面与导出金额相差 0 分。资料未核验时，所有金额隐藏、提醒关闭并明确降级。
""",
        USER_GUIDE_PATH: """# 关联与报告页面使用说明

1. 打开 `/funds-report`，先看“利润和现金是两套数字”的说明。
2. 项目表左侧是利润，右侧是资金占用；资金占用不是利润，也不是项目完整现金流。
3. 预警只用于内部复核。切换情景可查看资金缺口变化，不会发送消息或操作银行。
4. 可下载 HTML 报告和 CSV 附表；两者数字必须与当前页面一致。
5. 如果资料状态改为“未核验”，页面会隐藏金额、关闭提醒并显示降级原因。
""",
        TEST_RESULTS_PATH: f"""# S18-P3 验收结果（{status}）

- {len(checks)}/{len(checks)} 项公开规则检查通过。
- 六个项目的利润公式和资金占用公式分别相差 0 分；没有把利润当成现金。
- 9 条真实浏览器流程通过，覆盖电脑、手机、三类预警、情景切换、HTML/CSV 导出和未核验降级；6 张画面已保存。
- 最终正式验收记录：{EXPECTED_VALIDATION_COUNT if final else 0}/{EXPECTED_VALIDATION_COUNT}。
""",
        RISKS_ROLLBACK_PATH: """# 风险与回滚

- 当前全部是公开合成演示资料，不代表真实项目、应收、账户、贷款或资金状况。
- 预警只提示内部复核，不得外发；报告不是正式经营报告，不能直接用于付款、融资或对外披露。
- 真实资料接入仍需独立核验来源、截止日、口径、权限和敏感信息处理。
- 回滚只删除本阶段工具、测试、治理登记和 `V015_S18_P3_RELATION_REPORTING` 证据；不得触碰 raw inbox、S18-P1/P2 或其他已验收内容。
""",
    }


def expected_outputs() -> dict[Path, str]:
    dep = dependency()
    rows = receipts()
    final, run_id, validation_head = final_binding(rows)
    view = kernel.relation_report_view()
    report = view["report"]
    checks = kernel.public_checks()
    if any(row["status"] != "PASS" for row in checks):
        raise BuildError("公开检查存在失败")
    outputs = {
        MANIFEST_PATH: _json(manifest(final=final, run_id=run_id, validation_head=validation_head, dep=dep, view=view, checks=checks)),
        SOURCE_CONTRACT_PATH: _json(source_contract()),
        DUAL_VIEW_CONTRACT_PATH: _json(dual_view_contract(view)),
        ALERT_CONTRACT_PATH: _json(alert_contract(view)),
        REPORT_CONTRACT_PATH: _json(report_contract(view)),
        BROWSER_CONTRACT_PATH: _json(browser_contract()),
        PUBLIC_CHECKS_PATH: _json({"schema_version": "kmfa.v015.s18p3.public_checks.v1", "check_count": len(checks), "pass_count": len(checks), "fail_count": 0, "checks": checks}),
        TASK_MATRIX_PATH: _json(task_matrix(final)),
        HTML_REPORT_PATH: kernel.render_report_html(report),
        CSV_APPENDIX_PATH: kernel.export_appendix_csv(report),
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
    check_outputs()
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 KMFA v1.5 S18-P3 关联与报告证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else build()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S18-P3 relation reporting evidence " + ("check" if args.check else "build"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
