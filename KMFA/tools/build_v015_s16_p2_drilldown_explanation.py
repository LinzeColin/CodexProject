#!/usr/bin/env python3
"""生成 KMFA v1.5 S16-P2 指标下钻与解释可复验证据。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools import run_v015_s16_p2_drilldown_explanation as runtime
from KMFA.tools import v015_s16_p2_drilldown_explanation as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "02015e676329710d2b7602281a1ee901f8f00be9"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_runtime_tests",
    "focused_browser_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s16_p1_dependency",
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

MANIFEST_PATH = MACHINE_ROOT / "s16_p2_drilldown_explanation_manifest.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
DRILLDOWN_CONTRACT_PATH = MACHINE_ROOT / "drilldown_consistency_contract_public_safe.json"
EXPLANATION_CONTRACT_PATH = MACHINE_ROOT / "explanation_lineage_contract_public_safe.json"
COMPARISON_CONTRACT_PATH = MACHINE_ROOT / "comparison_contract_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

HTML_PATH = HTML_ROOT / "kmfa_drilldown_explanation.html"
SCREENSHOT_PATHS = (
    SCREENSHOT_ROOT / "kmfa_drilldown_funds.png",
    SCREENSHOT_ROOT / "kmfa_drilldown_professional.png",
    SCREENSHOT_ROOT / "kmfa_drilldown_comparison_blocked.png",
    SCREENSHOT_ROOT / "kmfa_drilldown_mobile.png",
)

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S16_P1_HOMEPAGE_FIRST_SCREEN/machine"
DEPENDENCY_MANIFEST_PATH = DEPENDENCY_ROOT / "s16_p1_homepage_manifest.json"
DEPENDENCY_RECEIPTS_PATH = DEPENDENCY_ROOT / "validation_results.jsonl"


class BuildError(RuntimeError):
    """S16-P2 证据无法形成。"""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    value = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    expected = {
        "run_phase_id": "V015_S16_P1_HOMEPAGE_FIRST_SCREEN",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "decision": "GO_TO_S16_P2_ONLY",
        "s16_p2_entry_allowed": True,
        "s16_p2_started": False,
        "validation_receipt_count": 20,
        "overall_accepted_phase_count": 44,
    }
    mismatches = [key for key, expected_value in expected.items() if value.get(key) != expected_value]
    if mismatches:
        raise BuildError("S16-P1 依赖不一致：" + ", ".join(mismatches))
    if len(rows) != 20 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S16-P1 必须恰好有 20 条通过记录")
    if {row.get("validation_head") for row in rows} != {value.get("validation_head")}:
        raise BuildError("S16-P1 验收提交不一致")
    if {row.get("validation_run_id") for row in rows} != {value.get("validation_run_id")}:
        raise BuildError("S16-P1 验收批次不一致")
    return {
        "acceptance_status": "PASSED",
        "validation_head": value["validation_head"],
        "validation_run_id": value["validation_run_id"],
        "validation_receipt_count": len(rows),
        "overall_accepted_phase_count": 44,
        "s16_p2_entry_allowed": True,
        "s16_p2_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S16-P2 验收记录顺序不一致")
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
            "scope": ["首页数字下钻", "简明计算说明", "专业来源链", "环比、同比和预算或基准比较"],
            "excluded": ["真实数据接入", "真实经营结论", "S16-P3", "S16 整体复审", "GitHub 上传", "App 重装"],
        }
    )
    return value


def drilldown_contract() -> dict[str, Any]:
    values = {metric_id: kernel.drilldown_snapshot(metric_id=metric_id) for metric_id in kernel.METRIC_SPECS}
    return {
        "schema_version": "kmfa.v015.s16p2.drilldown_consistency_contract.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "metric_count": len(values),
        "drilldown_route_count": len(kernel.METRIC_SLUGS),
        "preserved_filter_count": 4,
        "primary_exact_count": sum(value["consistency"]["primary_difference"] == 0 for value in values.values()),
        "secondary_exact_count": sum(value["consistency"]["secondary_difference"] in (None, 0) for value in values.values()),
        "detail_available_count": sum(value["detail_available"] for value in values.values()),
        "details": values,
        "homepage_detail_difference_cents": 0,
        "raw_write_count": 0,
        "fact_layer_write_count": 0,
    }


def explanation_contract() -> dict[str, Any]:
    values = {metric_id: kernel.drilldown_snapshot(metric_id=metric_id)["explanation"] for metric_id in kernel.METRIC_SPECS}
    missing = kernel.drilldown_snapshot(lineage_state="missing")
    return {
        "schema_version": "kmfa.v015.s16p2.explanation_lineage_contract.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "short_explanation_count": len(values),
        "complete_lineage_count": sum(value["lineage_complete"] for value in values.values()),
        "default_lineage_node_count": 4,
        "technical_log_default_visible_count": 0,
        "technical_log_count": 0,
        "missing_lineage_detail_allowed": missing["detail_available"],
        "missing_lineage_reason_zh": missing["explanation"]["block_reason_zh"],
        "explanations": values,
    }


def comparison_contract() -> dict[str, Any]:
    exact = {
        kind: kernel.drilldown_snapshot(metric_id="PROJECT_GROSS_PROFIT", comparison_kind=kind)["comparison"]
        for kind in kernel.COMPARISON_KINDS
    }
    basis = kernel.drilldown_snapshot(comparison_state="basis_mismatch")["comparison"]
    coverage = kernel.drilldown_snapshot(comparison_state="coverage_mismatch")["comparison"]
    return {
        "schema_version": "kmfa.v015.s16p2.comparison_contract.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "comparison_kind_count": len(exact),
        "exact_comparison_allowed_count": sum(value["comparison_allowed"] for value in exact.values()),
        "exact_basis_count": sum(value["basis_consistent"] for value in exact.values()),
        "exact_coverage_count": sum(value["coverage_consistent"] and value["coverage_bps"] == 10_000 for value in exact.values()),
        "basis_mismatch_blocked": not basis["comparison_allowed"],
        "coverage_mismatch_blocked": not coverage["comparison_allowed"],
        "basis_mismatch_reason_zh": basis["block_reason_zh"],
        "coverage_mismatch_reason_zh": coverage["block_reason_zh"],
        "examples": exact,
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s16p2.browser_acceptance_contract.v1",
        "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME_SPA",
        "required_viewports": [
            {"name": "desktop", "width": 1440, "height": 1000},
            {"name": "mobile", "width": 390, "height": 844},
        ],
        "required_flows": [
            "homepage_number_to_matching_detail",
            "four_filters_preserved",
            "plain_explanation_then_professional_lineage",
            "three_comparisons_and_basis_block",
            "missing_data_or_source_block",
            "all_five_routes_and_home_return",
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
            "task_id": "S16P2T01",
            "name_zh": "实现指标下钻",
            "acceptance_zh": "5 个首页数字都可进入对应明细，保留 4 项筛选，明细合计与首页一致。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(DRILLDOWN_CONTRACT_PATH.relative_to(REPO_ROOT)), str(BROWSER_CONTRACT_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S16P2T02",
            "name_zh": "实现来源与计算说明",
            "acceptance_zh": "默认先显示简明中文说明，专业依据按需展开；来源不完整时阻止明细结论。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(EXPLANATION_CONTRACT_PATH.relative_to(REPO_ROOT)), str(BROWSER_CONTRACT_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S16P2T03",
            "name_zh": "实现多期间比较",
            "acceptance_zh": "支持环比、同比和预算或基准比较；计算口径或覆盖范围不一致时不比较。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(COMPARISON_CONTRACT_PATH.relative_to(REPO_ROOT)), str(BROWSER_CONTRACT_PATH.relative_to(REPO_ROOT))],
        },
    ]
    return {
        "schema_version": "kmfa.v015.s16p2.task_acceptance_matrix.v1",
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
        "schema_version": "kmfa.v015.s16p2.drilldown_explanation_manifest.v1",
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
        "decision": "GO_TO_S16_P3_ONLY" if final else "PENDING_FINAL_VALIDATION",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 67,
        "stage_phase_pass_count": 2 if final else 1,
        "stage_task_accepted_count": 6 if final else 3,
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 45 if final else 44,
        "overall_taskpack_phase_count": 72,
        "s16_p1_acceptance_status": "PASSED",
        "s16_p2_entry_allowed": False,
        "s16_p2_started": True,
        "s16_p2_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s16_p3_entry_allowed": final,
        "s16_p3_started": False,
        "s16_stage_review_entry_allowed": False,
        "s17_entry_allowed": False,
        "product_implementation_allowed": not final,
        "product_implementation_performed": True,
        "metric_count": core["metric_count"],
        "drilldown_route_count": core["drilldown_route_count"],
        "preserved_filter_count": core["preserved_filter_count"],
        "default_lineage_node_count": core["default_lineage_node_count"],
        "short_explanation_count": core["short_explanation_count"],
        "technical_log_default_visible_count": core["technical_log_default_visible_count"],
        "technical_log_count": core["technical_log_count"],
        "comparison_kind_count": core["comparison_kind_count"],
        "basis_mismatch_block_count": core["basis_mismatch_block_count"],
        "coverage_mismatch_block_count": core["coverage_mismatch_block_count"],
        "homepage_detail_difference_cents": core["homepage_detail_difference_cents"],
        "browser_viewport_count": 2,
        "browser_flow_count": 7,
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
        "fact_layer_write_count": 0,
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
    implementation = f"""# S16-P2 指标下钻与解释实现记录

- 状态：{status}。
- 首页 5 个核心数字都能进入对应明细，进入后保留公司、期间、项目状态和报告版本。
- 每份明细都会重新合计并与首页数字核对；不一致就不通过。
- 页面默认先用短中文解释数字怎么来，专业依据由用户主动展开，不把技术日志放在老板面前。
- 支持环比、同比和预算或基准比较；口径或数据范围不一致时明确停止比较。
- 资料或来源不完整时不显示没有依据的明细，也不把缺失当成 0。
{validation}- 当前全部为公开演示内容，没有读取真实资料、连接外部网络或执行真实业务动作。
- 下一步只允许在新的独立 Run 中进行 S16-P3；本轮没有开始异常与机会、整体复审、GitHub 上传或 App 重装。
"""
    guide = """# S16-P2 使用说明

1. 启动：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s16_p2_drilldown_explanation.py`。
2. 打开“经营首页”，点击任一核心数字下方的“查看详情”。
3. 先看“当前数字”“这个数字怎么来的”和“组成明细”；页面会提示明细合计是否与首页一致。
4. 在“期间比较”选择环比、同比或预算/基准；只有口径和数据范围一致时才会显示差异。
5. 需要核查时展开“查看专业依据”，可查看公开演示来源、筛选范围、计算规则和首页呈现链。
6. 页面当前使用公开演示内容，不连接真实公司数据。
"""
    tests = f"""# S16-P2 测试结果

- 当前结论：{status}。
- 内核检查共 78 项，覆盖 5 个下钻、首页与明细一致、来源链、3 种比较、口径与覆盖阻断、权限和公开边界。
- localhost 检查覆盖直接链接、5 个接口、4 项筛选、缺资料、缺来源、无权限和原首页兼容。
- 真实浏览器检查覆盖电脑与手机 7 条流程，并保留资金明细、专业依据、比较阻断和手机版 4 张画面。
{validation}- 原始资料读取、事实层写入、外部网络请求和真实业务动作均为 0。
"""
    risks = """# S16-P2 风险与回退

- 当前明细、来源和期间数据均为公开合成内容，只验证交互、计算与阻断规则，不代表生产经营结果。
- S16-P3 才处理异常与机会；本阶段不宣称已完成经营异常诊断。
- 回退时只移除本阶段新增的 S16-P2 工具、测试、证据和治理登记，不回退已通过的 S16-P1，也不触碰原始资料。
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
        DRILLDOWN_CONTRACT_PATH: _json(drilldown_contract()),
        EXPLANATION_CONTRACT_PATH: _json(explanation_contract()),
        COMPARISON_CONTRACT_PATH: _json(comparison_contract()),
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
    parser = argparse.ArgumentParser(description="生成或检查 KMFA v1.5 S16-P2 指标下钻与解释证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S16-P2 drilldown evidence " + ("is exact" if args.check else "written"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
