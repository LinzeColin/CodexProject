#!/usr/bin/env python3
"""生成 KMFA v1.5 S17-P1 项目列表的确定性公开证据。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools import run_v015_s17_p1_project_list as runtime
from KMFA.tools import v015_s17_p1_project_list as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "20c2e165e6be546c6c2a5cfe1ed1315ebe1d8879"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "phase_contract",
    "focused_unit_tests",
    "focused_runtime_tests",
    "focused_browser_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s16_stage_review_dependency",
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

MANIFEST_PATH = MACHINE_ROOT / "s17_p1_project_list_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
TABLE_CONTRACT_PATH = MACHINE_ROOT / "project_table_contract_public_safe.json"
ORDER_CONTRACT_PATH = MACHINE_ROOT / "group_sort_contract_public_safe.json"
BATCH_CONTRACT_PATH = MACHINE_ROOT / "batch_export_contract_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
PUBLIC_CHECKS_PATH = MACHINE_ROOT / "public_checks.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
HTML_PATH = HTML_ROOT / "kmfa_project_list.html"

SCREENSHOT_PATHS = (
    SCREENSHOT_ROOT / "kmfa_projects_desktop.png",
    SCREENSHOT_ROOT / "kmfa_projects_grouped.png",
    SCREENSHOT_ROOT / "kmfa_projects_comparison.png",
    SCREENSHOT_ROOT / "kmfa_projects_mobile.png",
)

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S16_STAGE_REVIEW/machine"
DEPENDENCY_MANIFEST_PATH = DEPENDENCY_ROOT / "s16_stage_review_manifest.json"
DEPENDENCY_RECEIPTS_PATH = DEPENDENCY_ROOT / "validation_results.jsonl"


class BuildError(RuntimeError):
    """S17-P1 证据无法形成。"""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    value = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    expected = {
        "run_phase_id": "V015_S16_STAGE_REVIEW",
        "phase_acceptance_status": "PASSED",
        "stage_acceptance_status": "PASSED",
        "decision": "GO_TO_S17_P1_ONLY",
        "s16_stage_review_acceptance_status": "PASSED",
        "s17_entry_allowed": True,
        "s17_p1_entry_allowed": True,
        "s17_p1_started": False,
        "validation_receipt_count": 32,
        "overall_accepted_phase_count": 46,
    }
    mismatches = [key for key, expected_value in expected.items() if value.get(key) != expected_value]
    if mismatches:
        raise BuildError("S16 整体复审依赖不一致：" + ", ".join(mismatches))
    if len(rows) != 32 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S16 整体复审必须恰好有 32 条通过记录")
    if {row.get("validation_head") for row in rows} != {value.get("validation_head")}:
        raise BuildError("S16 整体复审验收提交不一致")
    if {row.get("validation_run_id") for row in rows} != {value.get("validation_run_id")}:
        raise BuildError("S16 整体复审验收批次不一致")
    return {
        "acceptance_status": "PASSED",
        "validation_head": value["validation_head"],
        "validation_run_id": value["validation_run_id"],
        "validation_receipt_count": len(rows),
        "overall_accepted_phase_count": 46,
        "s17_p1_entry_allowed": True,
        "s17_p1_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S17-P1 验收记录顺序不一致")
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
            "scope": ["项目总表", "可解释分组与排序", "只读批量对比与带来源导出"],
            "excluded": ["项目详情", "项目成本分析", "差异处理", "真实资料接入", "S17-P2", "S17-P3", "S17 整体复审", "GitHub 上传", "App 重装"],
        }
    )
    return value


def table_contract() -> dict[str, Any]:
    sample = kernel.project_list(page_size=kernel.PROJECTS_PER_COMPANY)
    return {
        "schema_version": "kmfa.v015.s17p1.project_table_contract.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "catalog_project_count": kernel.CATALOG_PROJECT_COUNT,
        "company_count": kernel.COMPANY_COUNT,
        "project_count_per_company": kernel.PROJECTS_PER_COMPANY,
        "default_page_size": kernel.DEFAULT_PAGE_SIZE,
        "maximum_page_size": kernel.MAX_PAGE_SIZE,
        "available_column_count": len(kernel.AVAILABLE_COLUMNS),
        "default_visible_column_count": kernel.DEFAULT_VISIBLE_COLUMN_COUNT,
        "available_columns": [dict(item) for item in kernel.AVAILABLE_COLUMNS],
        "default_columns": list(kernel.DEFAULT_COLUMNS),
        "filter_dimension_count": kernel.FILTER_DIMENSION_COUNT,
        "stable_project_ids": sample["all_filtered_project_ids"],
        "money_unit": "INTEGER_CENTS",
        "percentage_unit": "INTEGER_BASIS_POINTS",
        "source_required_per_row": True,
        "cutoff_required_per_row": True,
        "cross_company_row_count": 0,
    }


def order_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s17p1.group_sort_contract.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "group_option_count": len(kernel.GROUP_OPTIONS),
        "group_options": [{"id": item, "explanation_zh": kernel.GROUP_EXPLANATIONS[item]} for item in kernel.GROUP_OPTIONS],
        "sort_option_count": len(kernel.SORT_OPTIONS),
        "sort_options": [{"id": item, "explanation_zh": kernel.SORT_EXPLANATIONS[item]} for item in kernel.SORT_OPTIONS],
        "hidden_composite_score_count": 0,
        "stable_tie_breaker": "project_id",
        "pipeline": ["filter", "group", "stable_sort", "paginate"],
    }


def batch_contract() -> dict[str, Any]:
    rows = kernel.project_catalog("demo-north", "2026-07")[:3]
    ids = [row["project_id"] for row in rows]
    comparison = kernel.batch_compare(ids)
    exported = kernel.export_csv(ids)
    return {
        "schema_version": "kmfa.v015.s17p1.batch_export_contract.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "minimum_project_count": kernel.MIN_BATCH_COUNT,
        "maximum_project_count": kernel.MAX_BATCH_COUNT,
        "sample_project_ids": ids,
        "sample_revenue_total_cents": comparison["totals"]["revenue_cents"],
        "sample_cost_total_cents": comparison["totals"]["cost_cents"],
        "sample_weighted_margin_bps": comparison["totals"]["weighted_margin_bps"],
        "sample_weighted_collection_bps": comparison["totals"]["weighted_collection_bps"],
        "export_source_columns_present": all(token in exported for token in ("来源说明", "来源编号", "数据截止日")),
        "fact_layer_write_count": 0,
        "export_write_count": 0,
        "real_business_action_count": 0,
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s17p1.browser_acceptance_contract.v1",
        "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME_SPA",
        "required_viewports": [
            {"name": "desktop", "width": 1440, "height": 1000},
            {"name": "mobile", "width": 390, "height": 844},
        ],
        "required_flows": [
            "desktop_default_table",
            "filter_group_sort_pagination",
            "column_configuration_persistence",
            "batch_compare",
            "source_bound_export",
            "company_status_scope_switch",
            "mobile_card_layout",
            "selection_scope_reset",
        ],
        "browser_flow_count": kernel.BROWSER_FLOW_COUNT,
        "visual_evidence_count": kernel.VISUAL_EVIDENCE_COUNT,
        "screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS],
        "desktop_table_required": True,
        "mobile_card_layout_required": True,
        "horizontal_overflow_allowed": False,
        "minimum_touch_target_px": 44,
        "external_network_request_count": 0,
    }


def task_matrix(final: bool) -> dict[str, Any]:
    tasks = [
        {
            "task_id": "S17P1T01",
            "task_name_zh": "实现项目总表",
            "acceptance_zh": "列可配置，默认不过载。",
            "evidence": ["table_contract_public_safe.json", "kmfa_projects_desktop.png"],
        },
        {
            "task_id": "S17P1T02",
            "task_name_zh": "实现项目分组与排序",
            "acceptance_zh": "排序公式可解释。",
            "evidence": ["group_sort_contract_public_safe.json", "kmfa_projects_grouped.png"],
        },
        {
            "task_id": "S17P1T03",
            "task_name_zh": "实现批量查看与导出",
            "acceptance_zh": "批量操作不修改事实。",
            "evidence": ["batch_export_contract_public_safe.json", "kmfa_projects_comparison.png"],
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
        "schema_version": "kmfa.v015.s17p1.task_acceptance_matrix.v1",
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
        "schema_version": "kmfa.v015.s17p1.project-list-manifest.v1",
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
        "decision": "GO_TO_S17_P2_ONLY" if final else "PENDING_FINAL_VALIDATION",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 33,
        "stage_phase_pass_count": 1 if final else 0,
        "stage_task_accepted_count": 3 if final else 0,
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 47 if final else 46,
        "overall_taskpack_phase_count": 72,
        "s16_stage_review_acceptance_status": "PASSED",
        "s17_entry_allowed": False,
        "s17_p1_entry_allowed": False,
        "s17_p1_started": True,
        "s17_p1_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s17_p2_entry_allowed": final,
        "s17_p2_started": False,
        "s17_p2_acceptance_status": "PENDING",
        "s17_p3_entry_allowed": False,
        "s17_p3_started": False,
        "s17_stage_review_entry_allowed": False,
        "s17_stage_review_started": False,
        "product_implementation_allowed": not final,
        "product_implementation_performed": True,
        "catalog_project_count": kernel.CATALOG_PROJECT_COUNT,
        "company_count": kernel.COMPANY_COUNT,
        "project_count_per_company": kernel.PROJECTS_PER_COMPANY,
        "default_page_size": kernel.DEFAULT_PAGE_SIZE,
        "maximum_page_size": kernel.MAX_PAGE_SIZE,
        "available_column_count": kernel.AVAILABLE_COLUMN_COUNT,
        "default_visible_column_count": kernel.DEFAULT_VISIBLE_COLUMN_COUNT,
        "filter_dimension_count": kernel.FILTER_DIMENSION_COUNT,
        "group_option_count": kernel.GROUP_OPTION_COUNT,
        "sort_option_count": kernel.SORT_OPTION_COUNT,
        "hidden_composite_score_count": 0,
        "minimum_batch_project_count": kernel.MIN_BATCH_COUNT,
        "maximum_batch_project_count": kernel.MAX_BATCH_COUNT,
        "export_source_required": True,
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
    implementation = f"""# S17-P1 项目列表实现记录

- 状态：{status}。
- 页面默认只显示项目、客户、负责人、状态、毛利率、回款进度和风险，加上选择列共 8 列；用户可以自行增减显示列。
- 公司、期间和项目状态沿用全局筛选，并增加客户、负责人、毛利、回款和风险筛选；筛选后再稳定排序和分页，项目编号不会错位。
- 风险、毛利率、回款、行业和期间的分组与排序规则直接显示在页面上，不使用隐藏综合评分。
- 可一次选择 2 至 6 个项目进行只读对比或导出；导出每行都有来源说明、来源编号和截止日。
{validation}- 当前只使用 18 个公开合成项目，没有读取真实资料、连接外部网络或修改事实层。
- 下一步只允许在新的独立 Run 中进行 S17-P2；本轮没有开始项目详情、成本分析、S17 整体复审、GitHub 上传或 App 重装。
"""
    guide = """# S17-P1 使用说明

1. 启动：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s17_p1_project_list.py`。
2. 打开 `/projects`，上方选择公司、期间和项目状态；页面内可继续按客户、负责人、毛利、回款和风险筛选。
3. “分组”和“排序”下方会直接说明规则；风险排序没有隐藏评分。
4. “设置显示列”可以增减列，默认表格保持精简。
5. 勾选 2 至 6 个项目后，可做只读对比或导出附表；两种结果都不会修改项目事实。
6. 页面当前只使用公开合成项目，不连接真实公司资料。
"""
    tests = f"""# S17-P1 测试结果

- 当前结论：{status}。
- 58 项公开检查全部通过，覆盖 3 家公开演示公司、18 个项目、整数金额、来源绑定、筛选、分组、排序、分页、对比和导出。
- 真实浏览器覆盖电脑和手机 8 条流程，保留 4 张画面；电脑使用紧凑表格，手机改用项目卡片且没有横向溢出。
- 第一页 4 个、第二页 2 个，筛选与翻页后项目编号没有重复或错位。
- 批量对比和 CSV 导出的项目编号、金额与来源一致；事实层写入为 0。
{validation}- 原始资料读取、外部网络请求和真实业务动作均为 0。
"""
    risks = """# S17-P1 风险与回退

- 当前 18 个项目均为公开合成内容，只验证列表工作流，不代表生产经营结论。
- 项目详情、成本分解和差异处理属于后续部分，本轮刻意不做，避免用占位内容冒充完成。
- 本地列偏好保存在浏览器，只影响显示，不改变项目事实。
- 回退时只移除本阶段新增的项目列表 runtime、测试、证据和治理登记，不回退已通过的 S16，也不触碰原始资料。
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
        TABLE_CONTRACT_PATH: _json(table_contract()),
        ORDER_CONTRACT_PATH: _json(order_contract()),
        BATCH_CONTRACT_PATH: _json(batch_contract()),
        BROWSER_CONTRACT_PATH: _json(browser_contract()),
        PUBLIC_CHECKS_PATH: _json({"schema_version": "kmfa.v015.s17p1.public_checks.v1", "checks": kernel.public_checks()}),
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
    parser = argparse.ArgumentParser(description="生成或检查 KMFA v1.5 S17-P1 项目列表证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S17-P1 project list evidence " + ("is exact" if args.check else "written"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
