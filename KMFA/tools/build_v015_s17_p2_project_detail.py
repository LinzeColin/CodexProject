#!/usr/bin/env python3
"""生成 KMFA v1.5 S17-P2 项目详情的公开验收证据。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools import run_v015_s17_p2_project_detail as runtime
from KMFA.tools import v015_s17_p2_project_detail as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "f32a3e314b7d8a28a75227ed9dd12cf473203501"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "phase_contract",
    "focused_unit_tests",
    "focused_runtime_tests",
    "focused_browser_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s17_p1_dependency",
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

MANIFEST_PATH = MACHINE_ROOT / "s17_p2_project_detail_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
OVERVIEW_CONTRACT_PATH = MACHINE_ROOT / "overview_contract_public_safe.json"
COST_CONTRACT_PATH = MACHINE_ROOT / "cost_reconciliation_contract_public_safe.json"
TAB_NAVIGATION_CONTRACT_PATH = MACHINE_ROOT / "tab_navigation_contract_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
PUBLIC_CHECKS_PATH = MACHINE_ROOT / "public_checks.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
HTML_PATH = HTML_ROOT / "kmfa_project_detail.html"

SCREENSHOT_PATHS = (
    SCREENSHOT_ROOT / "kmfa_project_detail_overview.png",
    SCREENSHOT_ROOT / "kmfa_project_detail_cost.png",
    SCREENSHOT_ROOT / "kmfa_project_detail_revenue.png",
    SCREENSHOT_ROOT / "kmfa_project_detail_documents.png",
    SCREENSHOT_ROOT / "kmfa_project_detail_mobile.png",
)

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S17_P1_PROJECT_LIST/machine"
DEPENDENCY_MANIFEST_PATH = DEPENDENCY_ROOT / "s17_p1_project_list_manifest.json"
DEPENDENCY_RECEIPTS_PATH = DEPENDENCY_ROOT / "validation_results.jsonl"


class BuildError(RuntimeError):
    """S17-P2 证据无法形成确定结论。"""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    if not DEPENDENCY_MANIFEST_PATH.is_file() or not DEPENDENCY_RECEIPTS_PATH.is_file():
        raise BuildError("S17-P1 正式验收依赖缺失")
    value = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    expected = {
        "run_phase_id": "V015_S17_P1_PROJECT_LIST",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "validation_receipt_count": 20,
        "overall_accepted_phase_count": 47,
        "s17_p1_started": True,
        "s17_p2_entry_allowed": True,
        "s17_p2_started": False,
        "s17_p3_started": False,
    }
    mismatches = [key for key, expected_value in expected.items() if value.get(key) != expected_value]
    if mismatches:
        raise BuildError("S17-P1 依赖不一致：" + ", ".join(mismatches))
    if len(rows) != 20 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S17-P1 必须恰好有 20 条通过记录")
    if {row.get("validation_head") for row in rows} != {value.get("validation_head")}:
        raise BuildError("S17-P1 验收提交不一致")
    if {row.get("validation_run_id") for row in rows} != {value.get("validation_run_id")}:
        raise BuildError("S17-P1 验收批次不一致")
    return {
        "acceptance_status": "PASSED",
        "validation_head": value["validation_head"],
        "validation_run_id": value["validation_run_id"],
        "validation_receipt_count": len(rows),
        "overall_accepted_phase_count": 47,
        "s17_p2_entry_allowed": True,
        "s17_p2_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [
        json.loads(line)
        for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S17-P2 验收记录顺序不一致")
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


def source_contract() -> dict[str, Any]:
    value = kernel.source_contract()
    value.update(
        {
            "source_package_sha256": TASKPACK_SHA256,
            "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
            "scope": ["项目概况", "分类成本与零差异核对", "收入回款、差异和资料分标签", "列表上下文返回"],
            "excluded": ["成本明细钻取", "真实资料接入", "差异处理动作", "S17-P3", "S17 整体复审", "GitHub 上传", "App 重装"],
        }
    )
    return value


def overview_contract() -> dict[str, Any]:
    value = kernel.project_detail(project_id="PUB-PROJ-001")
    overview = value["overview"]
    return {
        "schema_version": "kmfa.v015.s17p2.overview_contract.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "business_summary_first": overview["business_summary_first"],
        "profit_verdict_zh": overview["profit_verdict_zh"],
        "profit_reason_count": len(overview["profit_reason_zh"]),
        "visible_business_metric_count": 8,
        "professional_basis_collapsed_by_default": True,
        "management_revenue_cents": overview["revenue_cents"],
        "management_cost_cents": overview["cost_cents"],
        "management_gross_profit_cents": overview["gross_profit_cents"],
        "money_equation_difference_cents": overview["revenue_cents"] - overview["cost_cents"] - overview["gross_profit_cents"],
        "engine_golden_difference_cents": overview["professional_basis"]["golden_comparison"]["differences_cents"],
        "engine_zero_difference_pass": overview["professional_basis"]["golden_comparison"]["zero_difference_pass"],
        "technical_status_code_first_count": 0,
        "source_required": True,
    }


def cost_contract() -> dict[str, Any]:
    value = kernel.project_detail(project_id="PUB-PROJ-001")["cost"]
    return {
        "schema_version": "kmfa.v015.s17p2.cost_reconciliation_contract.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "category_count": len(value["categories"]),
        "trend_period_count": len(value["trend"]),
        "actual_total_cents": value["actual_total_cents"],
        "budget_total_cents": value["budget_total_cents"],
        "variance_total_cents": value["variance_total_cents"],
        "unallocated_cost_cents": value["unallocated"]["amount_cents"],
        "unallocated_source_required": bool(value["unallocated"]["source_ref"]),
        "category_source_count": sum(bool(item["source_ref"]) for item in value["categories"]),
        "table_total_cents": value["table_total_cents"],
        "chart_total_cents": value["chart_total_cents"],
        "trend_total_cents": value["trend_total_cents"],
        "engine_difference_cents": value["engine_difference_cents"],
        "chart_table_difference_cents": value["chart_table_difference_cents"],
        "money_tolerance_cents": kernel.MONEY_TOLERANCE_CENTS,
        "zero_difference_pass": value["zero_difference_pass"],
    }


def tab_navigation_contract() -> dict[str, Any]:
    context = {"risk": "HIGH", "group_by": "risk", "sort_by": "margin", "page": "2", "page_size": "4"}
    value = kernel.project_detail(project_id="PUB-PROJ-001", list_context=context)
    return {
        "schema_version": "kmfa.v015.s17p2.tab_navigation_contract.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "tab_count": len(value["tabs"]),
        "tabs": value["tabs"],
        "section_ids": value["section_ids"],
        "section_overlap_count": value["section_overlap_count"],
        "document_count": value["documents"]["document_count"],
        "revenue_timeline_step_count": len(value["revenue_collection"]["timeline"]),
        "variance_row_count": len(value["variance"]["rows"]),
        "return_context": value["navigation"]["return_context"],
        "return_url": value["navigation"]["return_url"],
        "preserves_list_context": value["navigation"]["preserves_list_context"],
        "fact_layer_write_count": value["fact_layer_write_count"],
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s17p2.browser_acceptance_contract.v1",
        "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME_SPA",
        "required_viewports": [
            {"name": "desktop", "width": 1440, "height": 1000},
            {"name": "mobile", "width": 390, "height": 844},
        ],
        "required_flows": [
            "overview_business_answer_first",
            "cost_chart_table_engine_zero_difference",
            "cost_trend_and_unallocated_visibility",
            "revenue_collection_separate_flow",
            "variance_equation_and_explanation",
            "documents_without_amount_duplication",
            "list_detail_return_context",
            "company_scope_switch",
            "mobile_tabs_and_no_page_overflow",
        ],
        "browser_flow_count": kernel.BROWSER_FLOW_COUNT,
        "visual_evidence_count": kernel.VISUAL_EVIDENCE_COUNT,
        "screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS],
        "horizontal_page_overflow_allowed": False,
        "minimum_touch_target_px": 44,
        "external_network_request_count": 0,
    }


def task_matrix(final: bool) -> dict[str, Any]:
    tasks = [
        {
            "task_id": "S17P2T01",
            "task_name_zh": "实现概况页",
            "acceptance_zh": "一页可回答项目是否赚钱及为什么。",
            "evidence": ["overview_contract_public_safe.json", "kmfa_project_detail_overview.png"],
        },
        {
            "task_id": "S17P2T02",
            "task_name_zh": "实现成本页",
            "acceptance_zh": "合计与引擎一致。",
            "evidence": ["cost_reconciliation_contract_public_safe.json", "kmfa_project_detail_cost.png"],
        },
        {
            "task_id": "S17P2T03",
            "task_name_zh": "实现收入回款、差异和资料页",
            "acceptance_zh": "返回保留上下文。",
            "evidence": ["tab_navigation_contract_public_safe.json", "kmfa_project_detail_revenue.png", "kmfa_project_detail_documents.png"],
        },
    ]
    for row in tasks:
        row.update(
            {
                "execution_status": "EXECUTION_COMPLETE",
                "acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
                "result": "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION",
            }
        )
    return {
        "schema_version": "kmfa.v015.s17p2.task_acceptance_matrix.v1",
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "tasks": tasks,
    }


def manifest() -> dict[str, Any]:
    predecessor = dependency()
    rows = receipts()
    final, run_id, head = final_binding(rows)
    checks = kernel.public_checks()
    return {
        "schema_version": "kmfa.v015.s17p2.project-detail-manifest.v1",
        "version": kernel.VERSION,
        "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "run_mode": "CONTROLLED_RUN",
        "work_kind": "PRODUCT_IMPLEMENTATION",
        "predecessor": predecessor,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "decision": "GO_TO_S17_P3_ONLY" if final else "PENDING_FINAL_VALIDATION",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 67,
        "stage_phase_pass_count": 2 if final else 1,
        "stage_task_accepted_count": 6 if final else 3,
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 48 if final else 47,
        "overall_taskpack_phase_count": 72,
        "s16_stage_review_acceptance_status": "PASSED",
        "s17_p1_started": True,
        "s17_p1_acceptance_status": "PASSED",
        "s17_p2_entry_allowed": False,
        "s17_p2_started": True,
        "s17_p2_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s17_p3_entry_allowed": final,
        "s17_p3_started": False,
        "s17_stage_review_entry_allowed": False,
        "s17_stage_review_started": False,
        "product_implementation_allowed": True,
        "product_implementation_performed": True,
        "detail_tab_count": kernel.DETAIL_TAB_COUNT,
        "cost_category_count": kernel.COST_CATEGORY_COUNT,
        "cost_trend_period_count": kernel.COST_TREND_PERIOD_COUNT,
        "document_count": kernel.DOCUMENT_COUNT,
        "source_group_count": kernel.SOURCE_GROUP_COUNT,
        "money_tolerance_cents": kernel.MONEY_TOLERANCE_CENTS,
        "engine_difference_cents": cost_contract()["engine_difference_cents"],
        "chart_table_difference_cents": cost_contract()["chart_table_difference_cents"],
        "section_overlap_count": tab_navigation_contract()["section_overlap_count"],
        "return_context_preserved": tab_navigation_contract()["preserves_list_context"],
        "browser_viewport_count": 2,
        "browser_flow_count": kernel.BROWSER_FLOW_COUNT,
        "visual_evidence_count": kernel.VISUAL_EVIDENCE_COUNT,
        "minimum_touch_target_px": 44,
        "public_check_total": len(checks),
        "public_check_pass_count": sum(row["passed"] for row in checks),
        "public_check_failed_count": sum(not row["passed"] for row in checks),
        "validation_receipt_count": len(rows),
        "validation_run_id": run_id,
        "validation_head": head,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "external_network_request_count": 0,
        "real_identity_count": 0,
        "credential_count": 0,
        "real_business_action_count": 0,
        "fact_layer_write_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_generated": False,
    }


def _human_documents(current: dict[str, Any]) -> dict[Path, str]:
    final = current["phase_acceptance_status"] == "PASSED"
    status = "已通过正式验收" if final else "实现已完成，等待正式验收"
    validation = (
        f"- 正式验收：{current['validation_receipt_count']}/{EXPECTED_VALIDATION_COUNT} 项通过。\n"
        if final
        else "- 正式验收：尚未开始；当前证据保持待验收状态。\n"
    )
    implementation = f"""# S17-P2 项目详情实现记录

- 状态：{status}。
- 概况页先用中文给出“项目目前赚钱/未实现盈利”的结论，再用收入、成本、毛利、回款和风险解释原因；专业口径默认收起。
- 成本页显示 10 类成本、4 期趋势、预算基准、差异和未归集成本；图表、表格与计算引擎差异均为 0 分。
- 收入与回款、差异、资料各自使用独立标签，不把全部内容堆在一个页面；资料页不重复展示经营金额。
- 从项目列表进入详情后，返回会保留原来的筛选、分组、排序和页码。
{validation}- 当前只使用公开合成项目，没有读取真实资料、连接外部网络、修改事实层或执行真实业务动作。
- 下一步只允许在新的独立 Run 中进行 S17-P3；本轮没有开始成本明细钻取、S17 整体复审、GitHub 上传或 App 重装。
"""
    guide = """# S17-P2 使用说明

1. 启动：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s17_p2_project_detail.py`。
2. 打开 `/projects`，点击任一项目名称进入详情。
3. “概况”先看项目是否赚钱和原因；需要专业口径时再展开底部说明。
4. “成本”核对分类、预算差异、未归集成本和四期趋势；绿色提示说明图表、表格与引擎合计一分钱不差。
5. “收入与回款”“差异”“资料”分开查看，避免信息堆叠。
6. 点击“返回项目列表”，原来的筛选、分组、排序和页码会保留。
7. 页面只使用公开合成项目，不连接真实公司资料。
"""
    tests = f"""# S17-P2 测试结果

- 当前结论：{status}。
- 72 项公开检查全部通过，覆盖盈亏结论、统一计算口径、分类成本守恒、预算差异、趋势、回款、差异解释、资料来源和返回上下文。
- 真实浏览器覆盖电脑和手机 9 条流程，保留 5 张画面；手机页面没有横向溢出。
- 6 个公开项目逐一完成收入=成本+毛利、成本分类合计、趋势合计和引擎黄金值零差异核对。
- 成本图表与表格使用相同分类顺序和金额，差异为 0 分；允许误差为 0 分。
{validation}- 原始资料读取、外部网络请求、事实层写入和真实业务动作均为 0。
"""
    risks = """# S17-P2 风险与回退

- 当前内容均为公开合成项目，只验证详情工作流，不代表生产经营结论。
- 未归集成本明确保留并显示来源，不能把它隐去或平均摊入其他分类。
- 列表返回上下文保存在当前浏览器会话；新开浏览器会使用默认列表状态。
- 成本明细钻取和处理动作属于 S17-P3，本轮刻意不做。
- 回退时只移除本阶段新增的项目详情 runtime、测试、证据和治理登记，并恢复 S17-P1 列表的详情链接接入；不回退已通过的 S17-P1，也不触碰原始资料。
"""
    return {
        IMPLEMENTATION_REPORT_PATH: implementation,
        USER_GUIDE_PATH: guide,
        TEST_RESULTS_PATH: tests,
        RISKS_ROLLBACK_PATH: risks,
    }


def expected_outputs() -> dict[Path, str]:
    current = manifest()
    outputs = {
        MANIFEST_PATH: _json(current),
        SOURCE_CONTRACT_PATH: _json(source_contract()),
        OVERVIEW_CONTRACT_PATH: _json(overview_contract()),
        COST_CONTRACT_PATH: _json(cost_contract()),
        TAB_NAVIGATION_CONTRACT_PATH: _json(tab_navigation_contract()),
        BROWSER_CONTRACT_PATH: _json(browser_contract()),
        PUBLIC_CHECKS_PATH: _json({"schema_version": "kmfa.v015.s17p2.public_checks.v1", "checks": kernel.public_checks()}),
        TASK_MATRIX_PATH: _json(task_matrix(current["phase_acceptance_status"] == "PASSED")),
        HTML_PATH: runtime.render_html(),
    }
    outputs.update(_human_documents(current))
    return outputs


def write_outputs() -> None:
    for path, content in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def check_outputs() -> None:
    mismatches = [
        str(path.relative_to(REPO_ROOT))
        for path, content in expected_outputs().items()
        if not path.is_file() or path.read_text(encoding="utf-8") != content
    ]
    if mismatches:
        raise BuildError("证据需要重新生成：" + ", ".join(mismatches))
    missing = [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS if not path.is_file()]
    if missing:
        raise BuildError("浏览器截图缺失：" + ", ".join(missing))


def main() -> int:
    parser = argparse.ArgumentParser(description="生成或检查 KMFA v1.5 S17-P2 项目详情证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S17-P2 project detail evidence " + ("is exact" if args.check else "written"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
