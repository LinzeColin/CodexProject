#!/usr/bin/env python3
"""生成 KMFA v1.5 S16-P1 经营首页可复验证据。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools import run_v015_s16_p1_homepage as runtime
from KMFA.tools import v015_s16_p1_homepage as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "1b7c397ebdbc6c3f6ebe172e5699bbb09cd7b7c0"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_runtime_tests",
    "focused_browser_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s15_stage_review_dependency",
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

MANIFEST_PATH = MACHINE_ROOT / "s16_p1_homepage_manifest.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
SUMMARY_CONTRACT_PATH = MACHINE_ROOT / "business_summary_contract_public_safe.json"
FOCUS_CONTRACT_PATH = MACHINE_ROOT / "focus_items_contract_public_safe.json"
VISUAL_CONTRACT_PATH = MACHINE_ROOT / "trend_portfolio_contract_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

HTML_PATH = HTML_ROOT / "kmfa_homepage.html"
SCREENSHOT_PATHS = (
    SCREENSHOT_ROOT / "kmfa_homepage_desktop.png",
    SCREENSHOT_ROOT / "kmfa_homepage_partial.png",
    SCREENSHOT_ROOT / "kmfa_homepage_portfolio.png",
    SCREENSHOT_ROOT / "kmfa_homepage_mobile.png",
)

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_MANIFEST_PATH = PROJECT_ROOT / "stage_artifacts/V015_S15_STAGE_REVIEW/machine/s15_stage_review_manifest.json"
DEPENDENCY_RECEIPTS_PATH = PROJECT_ROOT / "stage_artifacts/V015_S15_STAGE_REVIEW/machine/validation_results.jsonl"


class BuildError(RuntimeError):
    """S16-P1 证据无法形成。"""


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
        "run_phase_id": "V015_S15_STAGE_REVIEW",
        "phase_acceptance_status": "PASSED",
        "stage_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "decision": "GO_TO_S16_P1_ONLY",
        "s16_entry_allowed": True,
        "s16_p1_entry_allowed": True,
        "s16_p1_started": False,
        "validation_receipt_count": 28,
        "overall_accepted_phase_count": 43,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S15 整体复审依赖不一致：" + ", ".join(mismatches))
    if len(rows) != 28 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S15 整体复审必须恰好有 28 条通过记录")
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S15 整体复审验收提交不一致")
    if {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")}:
        raise BuildError("S15 整体复审验收批次不一致")
    return {
        "acceptance_status": "PASSED",
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": len(rows),
        "overall_accepted_phase_count": 43,
        "s16_p1_entry_allowed": True,
        "s16_p1_started": False,
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
        raise BuildError("S16-P1 验收记录顺序不一致")
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
    contract = kernel.source_contract()
    contract.update(
        {
            "source_package_sha256": TASKPACK_SHA256,
            "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
            "scope": ["核心经营摘要", "本期重点事项", "近四期趋势", "项目组合"],
            "excluded": ["真实数据接入", "真实经营结论", "S16-P2", "S16-P3", "S16 整体复审", "GitHub 上传", "App 重装"],
        }
    )
    return contract


def summary_contract() -> dict[str, Any]:
    complete = kernel.homepage_snapshot()
    partial = kernel.homepage_snapshot(data_state="partial")
    return {
        "schema_version": "kmfa.v015.s16p1.business_summary_contract.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "metric_count": complete["summary_metric_count"],
        "source_bound_metric_count": sum(bool(row["source_zh"] and row["source_ref"]) for row in complete["summary_metrics"]),
        "cutoff_bound_metric_count": sum(bool(row["cutoff_date"]) for row in complete["summary_metrics"]),
        "completeness_bound_metric_count": sum(bool(row["completeness_zh"]) for row in complete["summary_metrics"]),
        "complete_example": {
            "overall_completeness": complete["overall_completeness"],
            "real_business_conclusion_allowed": complete["real_business_conclusion_allowed"],
            "metrics": complete["summary_metrics"],
        },
        "partial_example": {
            "overall_completeness": partial["overall_completeness"],
            "complete_management_conclusion_available": partial["complete_management_conclusion_available"],
            "honest_summary_zh": partial["honest_summary_zh"],
            "metrics": partial["summary_metrics"],
        },
        "missing_as_zero_count": 0,
        "raw_write_count": 0,
        "fact_layer_write_count": 0,
    }


def focus_contract() -> dict[str, Any]:
    value = kernel.homepage_snapshot()
    return {
        "schema_version": "kmfa.v015.s16p1.focus_items_contract.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "focus_item_count": value["focus_item_count"],
        "primary_action_count": value["primary_action_count"],
        "one_primary_action_each": all(row["primary_action_count"] == 1 for row in value["focus_items"]),
        "automatic_execution_count": value["automatic_execution_count"],
        "items": value["focus_items"],
    }


def visual_contract() -> dict[str, Any]:
    value = kernel.homepage_snapshot()
    return {
        "schema_version": "kmfa.v015.s16p1.trend_portfolio_contract.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "trend_series_count": value["trend_series_count"],
        "trend_period_count": kernel.TREND_PERIOD_COUNT,
        "trend_table_alternative_count": value["trend_table_alternative_count"],
        "project_portfolio_count": value["project_portfolio_count"],
        "project_matrix_columns": ["项目", "收入", "毛利率", "回款进度", "状态", "下一步"],
        "decorative_radar_chart_count": 0,
        "trend_series": value["trend_series"],
        "project_portfolio": value["project_portfolio"],
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s16p1.browser_acceptance_contract.v1",
        "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME_SPA",
        "required_viewports": [
            {"name": "desktop", "width": 1440, "height": 1000},
            {"name": "mobile", "width": 390, "height": 844},
        ],
        "required_flows": [
            "summary_source_cutoff_completeness",
            "partial_data_honest_state",
            "five_focus_items_one_action_navigation",
            "trend_table_and_project_matrix",
            "company_period_permission_refresh",
            "mobile_no_overflow_touch_targets",
        ],
        "required_screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS],
        "external_network_request_count_expected": 0,
        "page_error_count_expected": 0,
    }


def task_matrix(final: bool) -> dict[str, Any]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    result = "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION"
    tasks = [
        {
            "task_id": "S16P1T01",
            "name_zh": "实现核心经营摘要",
            "acceptance_zh": "可用资金、预计收付款、项目毛利、逾期应收和需确认事项均显示来源、截止日与完整性；缺资料不伪造结论。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(SUMMARY_CONTRACT_PATH.relative_to(REPO_ROOT)), str(BROWSER_CONTRACT_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S16P1T02",
            "name_zh": "实现本期重点事项",
            "acceptance_zh": "只突出 5 项重点，每项只有一个清晰主动作，不自动执行。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(FOCUS_CONTRACT_PATH.relative_to(REPO_ROOT)), str(BROWSER_CONTRACT_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S16P1T03",
            "name_zh": "实现趋势和项目组合",
            "acceptance_zh": "3 条趋势均有表格替代，4 个项目形成可读矩阵，不使用装饰性雷达图。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(VISUAL_CONTRACT_PATH.relative_to(REPO_ROOT)), str(BROWSER_CONTRACT_PATH.relative_to(REPO_ROOT))],
        },
    ]
    return {
        "schema_version": "kmfa.v015.s16p1.task_acceptance_matrix.v1",
        "run_phase_id": kernel.RUN_PHASE_ID,
        "phase_acceptance_status": status,
        "phase_task_count": len(tasks),
        "phase_task_accepted_count": len(tasks) if final else 0,
        "tasks": tasks,
    }


def manifest() -> dict[str, Any]:
    predecessor = dependency()
    rows = receipts()
    final, run_id, head = final_binding(rows)
    core = kernel.build_contract()
    return {
        "schema_version": "kmfa.v015.s16p1.homepage_manifest.v1",
        "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "version": kernel.VERSION,
        "run_mode": "CONTROLLED_RUN",
        "work_kind": "PRODUCT_IMPLEMENTATION",
        "predecessor": predecessor,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "decision": "GO_TO_S16_P2_ONLY" if final else "PENDING_FINAL_VALIDATION",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 33,
        "stage_phase_pass_count": 1 if final else 0,
        "stage_task_accepted_count": 3 if final else 0,
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 44 if final else 43,
        "overall_taskpack_phase_count": 72,
        "s16_p1_entry_allowed": False,
        "s16_p1_started": True,
        "s16_p1_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s16_p2_entry_allowed": final,
        "s16_p2_started": False,
        "s16_p3_entry_allowed": False,
        "s16_p3_started": False,
        "s16_stage_review_entry_allowed": False,
        "s17_entry_allowed": False,
        "product_implementation_allowed": not final,
        "product_implementation_performed": True,
        "summary_metric_count": core["summary_metric_count"],
        "source_bound_metric_count": core["source_bound_metric_count"],
        "cutoff_bound_metric_count": core["cutoff_bound_metric_count"],
        "completeness_bound_metric_count": core["completeness_bound_metric_count"],
        "partial_missing_metric_count": core["partial_missing_metric_count"],
        "missing_as_zero_count": core["missing_as_zero_count"],
        "focus_item_count": core["focus_item_count"],
        "primary_action_count": core["primary_action_count"],
        "automatic_execution_count": core["automatic_execution_count"],
        "trend_series_count": core["trend_series_count"],
        "trend_period_count": core["trend_period_count"],
        "trend_table_alternative_count": core["trend_table_alternative_count"],
        "project_portfolio_count": core["project_portfolio_count"],
        "browser_viewport_count": 2,
        "browser_flow_count": 6,
        "visual_evidence_count": len(SCREENSHOT_PATHS),
        "public_check_total": core["public_check_total"],
        "public_check_pass_count": core["public_check_pass_count"],
        "public_check_failed_count": core["public_check_failed_count"],
        "validation_receipt_count": len(rows),
        "validation_run_id": run_id,
        "validation_head": head,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "external_network_request_count": 0,
        "real_identity_count": 0,
        "credential_count": 0,
        "real_business_action_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_generated": False,
    }


def _human_documents(current_manifest: dict[str, Any]) -> dict[Path, str]:
    final = current_manifest["phase_acceptance_status"] == "PASSED"
    status = "已通过正式验收" if final else "实现已完成，等待正式验收"
    validation = (
        f"- 正式验收：{current_manifest['validation_receipt_count']}/{EXPECTED_VALIDATION_COUNT} 项通过。\n"
        if final
        else "- 正式验收：尚未开始；当前证据保持待验收状态。\n"
    )
    implementation = f"""# S16-P1 经营首页实现记录

- 状态：{status}。
- 首屏用 5 个数字回答可用资金、预计收付款、项目毛利、逾期应收和需确认事项；每项都显示来源、截止日和资料完整性。
- 资料缺失时显示“资料不足”，并明确先补资料，绝不把缺失值写成 0 或伪造完整结论。
- 本期重点固定为 5 项，每项只有一个主动作，全部只提供人工处理入口，不自动执行。
- 近四期只保留 3 条趋势，并提供表格；项目组合保留 4 个项目矩阵，不使用装饰性雷达图。
- 电脑与手机均使用现有 KMFA 应用外壳、身份权限和公司/期间切换。
{validation}- 当前全部为公开演示内容，没有读取真实资料、连接外部网络或执行真实业务动作。
- 下一步只允许在新的独立 Run 中进行 S16-P2；本轮没有开始下钻与解释、S16-P3、整体复审、GitHub 上传或 App 重装。
"""
    guide = """# S16-P1 使用说明

1. 启动：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s16_p1_homepage.py`。
2. 打开“经营首页”，先看 5 个核心数字；每个数字下方都写明来源、截止日和资料是否齐全。
3. “本期重点事项”只显示 5 项，点击右侧唯一按钮进入对应的回款、资金、税务、项目或数据更新页面。
4. “近四期趋势”同时提供小趋势图和数据表；“项目组合”可横向查看项目收入、毛利率、回款进度和状态。
5. 页面当前使用公开演示内容，不连接真实公司数据。
"""
    tests = f"""# S16-P1 测试结果

- 当前结论：{status}。
- 内核检查共 50 项，覆盖数字来源、截止日、完整性、缺失值、重点事项、趋势表格、项目矩阵、权限与公开边界。
- localhost 检查覆盖完整资料、缺失资料、不同公司和期间、未授权公司以及原有深链接。
- 真实浏览器检查覆盖电脑与手机 6 条流程，并保留完整、缺失、项目组合和手机 4 张画面。
{validation}- 缺失值伪装为 0、自动业务动作、事实层写入、原始资料读取和外部网络请求均为 0。
"""
    risks = """# S16-P1 风险与回退

- 当前数字、趋势和项目均为公开合成内容，只验证首页结构与交互，不代表生产经营结果。
- S16-P2 才负责正式的指标下钻、计算说明和多期间比较；本阶段的详情入口复用现有页面，不宣称已完成数据一致性下钻。
- 回退时只移除本阶段新增的 S16-P1 工具、测试、证据和治理登记，不回退已通过的 S15，也不触碰原始资料。
"""
    return {
        IMPLEMENTATION_REPORT_PATH: implementation,
        USER_GUIDE_PATH: guide,
        TEST_RESULTS_PATH: tests,
        RISKS_ROLLBACK_PATH: risks,
    }


def expected_outputs() -> dict[Path, str]:
    current_manifest = manifest()
    outputs = {
        MANIFEST_PATH: _json(current_manifest),
        TASK_MATRIX_PATH: _json(task_matrix(current_manifest["phase_acceptance_status"] == "PASSED")),
        SOURCE_CONTRACT_PATH: _json(source_contract()),
        SUMMARY_CONTRACT_PATH: _json(summary_contract()),
        FOCUS_CONTRACT_PATH: _json(focus_contract()),
        VISUAL_CONTRACT_PATH: _json(visual_contract()),
        BROWSER_CONTRACT_PATH: _json(browser_contract()),
        HTML_PATH: runtime.render_html(),
    }
    outputs.update(_human_documents(current_manifest))
    return outputs


def write_outputs() -> None:
    for path, text in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def check_outputs() -> None:
    mismatches = [
        str(path.relative_to(REPO_ROOT))
        for path, text in expected_outputs().items()
        if not path.is_file() or path.read_text(encoding="utf-8") != text
    ]
    if mismatches:
        raise BuildError("证据需要重新生成：" + ", ".join(mismatches))
    missing = [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS if not path.is_file()]
    if missing:
        raise BuildError("浏览器截图缺失：" + ", ".join(missing))


def main() -> int:
    parser = argparse.ArgumentParser(description="生成或检查 KMFA v1.5 S16-P1 经营首页证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S16-P1 homepage evidence " + ("is exact" if args.check else "written"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
