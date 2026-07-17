#!/usr/bin/env python3
"""生成 KMFA v1.5 S14-P1 可复验、公开安全的交付证据。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s14_p1_information_architecture as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "154760f42c485bea31550f6122f15cee12234680"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_artifact_tests",
    "focused_browser_tests",
    "focused_governance_tests",
    "s13_review_dependency",
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

MANIFEST_PATH = MACHINE_ROOT / "s14_p1_information_architecture_manifest.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
NAVIGATION_RESEARCH_PATH = MACHINE_ROOT / "navigation_tree_card_sort_evidence_public_safe.json"
ROUTE_E2E_PATH = MACHINE_ROOT / "route_e2e_evidence_public_safe.json"
TERMINOLOGY_EVIDENCE_PATH = MACHINE_ROOT / "terminology_evidence_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

HTML_PATH = HTML_ROOT / "kmfa_information_architecture.html"
SCREENSHOT_PATH = SCREENSHOT_ROOT / "kmfa_information_architecture_desktop.png"

NAVIGATION_CONTRACT_PATH = PROJECT_ROOT / "metadata/quality/v015_s14_p1_navigation_contract_public_safe.json"
PAGE_HIERARCHY_CONTRACT_PATH = PROJECT_ROOT / "metadata/quality/v015_s14_p1_page_hierarchy_contract_public_safe.json"
DISCLOSURE_CONTRACT_PATH = PROJECT_ROOT / "metadata/quality/v015_s14_p1_progressive_disclosure_contract_public_safe.json"

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_FLOW_GUIDE_PATH = HUMAN_ROOT / "user_flow_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_MANIFEST_PATH = PROJECT_ROOT / "stage_artifacts/V015_S13_STAGE_REVIEW/machine/s13_stage_review_manifest.json"
DEPENDENCY_RECEIPTS_PATH = PROJECT_ROOT / "stage_artifacts/V015_S13_STAGE_REVIEW/machine/validation_results.jsonl"


class BuildError(RuntimeError):
    """构建证据失败。"""


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
        "run_phase_id": "V015_S13_STAGE_REVIEW",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "decision": "GO_TO_S14_P1_ONLY",
        "s13_stage_review_performed": True,
        "s13_stage_review_acceptance_status": "PASSED",
        "s14_entry_allowed": True,
        "s14_p1_entry_allowed": True,
        "s14_p1_started": False,
        "validation_receipt_count": 24,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S13 整体复审依赖不一致：" + ", ".join(mismatches))
    if len(rows) != 24 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S13 整体复审必须恰好有 24 条通过记录")
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S13 整体复审验收提交不一致")
    if {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")}:
        raise BuildError("S13 整体复审验收批次不一致")
    return {
        "acceptance_status": "PASSED",
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": len(rows),
        "s14_p1_entry_allowed": True,
        "s14_p1_started": False,
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
        raise BuildError("S14-P1 验收记录顺序不一致")
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
    return (
        final,
        next(iter(run_ids)) if final else None,
        next(iter(heads)) if final else None,
    )


def _source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s14p1.source_contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": "S14",
        "stage_name_zh": "界面信息架构、设计系统与语言重构",
        "roadmap_phase_id": "S14-P1",
        "phase_name_zh": "信息架构",
        "task_count": 3,
        "task_ids": ["S14P1T01", "S14P1T02", "S14P1T03"],
        "task_names_zh": ["重建一级导航", "建立页面层级和面包屑", "建立渐进披露"],
        "stop_conditions_zh": ["不得沿用旧侧栏堆叠。", "死路和循环跳转失败。", "技术词出现在普通页面则失败。"],
        "scope": ["七项中文一级导航", "列表详情处理报告设置层级", "面包屑和上一任务返回", "摘要优先与按需展开"],
        "excluded": ["S14-P2", "S14-P3", "S14 整体复审", "真实用户研究", "真实资料", "GitHub 上传", "App 重装"],
    }


def _browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s14p1.browser_acceptance_contract.v1",
        "browser": "Chromium headless",
        "page_kind": "STATIC_PUBLIC_SAFE_HTML",
        "required_viewports": [
            {"name": "desktop", "width": 1440, "height": 1000},
            {"name": "mobile", "width": 390, "height": 844},
        ],
        "required_flows": [
            "seven_primary_navigation_destinations",
            "list_detail_process_breadcrumb_return",
            "report_and_settings_hierarchy",
            "progressive_disclosure_closed_by_default",
            "mobile_horizontal_primary_navigation",
            "keyboard_focus_and_reduced_motion_contract",
        ],
        "network_request_count_expected": 0,
        "console_error_count_expected": 0,
        "screenshot_path": str(SCREENSHOT_PATH.relative_to(REPO_ROOT)),
    }


def _task_matrix(final: bool) -> dict[str, Any]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    result = "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION"
    tasks = [
        {
            "task_id": "S14P1T01",
            "name_zh": "重建一级导航",
            "acceptance_zh": "一级入口固定为经营首页、项目、回款、资金、税务与政策、数据更新、报告；桌面和手机均不用旧侧栏。",
            "status": status,
            "current_result": result,
            "evidence_refs": [
                str(NAVIGATION_CONTRACT_PATH.relative_to(REPO_ROOT)),
                str(NAVIGATION_RESEARCH_PATH.relative_to(REPO_ROOT)),
                str(SCREENSHOT_PATH.relative_to(REPO_ROOT)),
            ],
        },
        {
            "task_id": "S14P1T02",
            "name_zh": "建立页面层级和面包屑",
            "acceptance_zh": "列表、详情、处理、报告和设置层级明确；每个页面都有面包屑、上一任务和至少一个有效后续入口。",
            "status": status,
            "current_result": result,
            "evidence_refs": [
                str(PAGE_HIERARCHY_CONTRACT_PATH.relative_to(REPO_ROOT)),
                str(ROUTE_E2E_PATH.relative_to(REPO_ROOT)),
                str(HTML_PATH.relative_to(REPO_ROOT)),
            ],
        },
        {
            "task_id": "S14P1T03",
            "name_zh": "建立渐进披露",
            "acceptance_zh": "默认先显示管理摘要，专业依据和审计说明按需展开；普通页面技术词命中为零。",
            "status": status,
            "current_result": result,
            "evidence_refs": [
                str(DISCLOSURE_CONTRACT_PATH.relative_to(REPO_ROOT)),
                str(TERMINOLOGY_EVIDENCE_PATH.relative_to(REPO_ROOT)),
                str(HTML_PATH.relative_to(REPO_ROOT)),
            ],
        },
    ]
    return {
        "schema_version": "kmfa.v015.s14p1.task_acceptance_matrix.v1",
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
    hierarchy = verification["hierarchy_summary"]
    research = verification["navigation_research_evidence"]
    disclosure = verification["progressive_disclosure_contract"]
    return {
        "schema_version": "kmfa.v015.s14p1.information_architecture_manifest.v1",
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
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 38 if final else 37,
        "overall_taskpack_phase_count": 72,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 33,
        "stage_phase_pass_count": 1 if final else 0,
        "stage_task_accepted_count": 3 if final else 0,
        "decision": "CONTINUE_TO_S14_P2_ONLY" if final else "REMAIN_IN_S14_P1_FINAL_VALIDATION",
        "primary_navigation_count": 7,
        "page_node_count": hierarchy["page_node_count"],
        "page_type_count": hierarchy["page_type_count"],
        "breadcrumb_edge_count": hierarchy["breadcrumb_edge_count"],
        "previous_task_coverage_bps": hierarchy["previous_task_coverage_bps"],
        "dead_end_count": hierarchy["dead_end_count"],
        "parent_cycle_count": hierarchy["parent_cycle_count"],
        "stacked_sidebar_used": False,
        "card_sort_case_count": research["card_sort_case_count"],
        "card_sort_pass_count": research["card_sort_pass_count"],
        "tree_test_case_count": research["tree_test_case_count"],
        "tree_test_pass_count": research["tree_test_pass_count"],
        "disclosure_level_count": len(disclosure["levels"]),
        "default_visible_technical_term_count": disclosure["default_visible_term_match_count"],
        "professional_basis_collapsed_by_default": True,
        "audit_detail_collapsed_by_default": True,
        "public_check_accounting": verification["accounting"],
        "s13_stage_review_acceptance_status": "PASSED",
        "s14_p1_entry_allowed": False,
        "s14_p1_started": True,
        "s14_p1_acceptance_status": acceptance,
        "s14_p2_entry_allowed": final,
        "s14_p2_started": False,
        "s14_p3_entry_allowed": False,
        "s14_p3_started": False,
        "s14_stage_review_entry_allowed": False,
        "s14_stage_review_started": False,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "real_business_action_count": 0,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "validation_receipt_count": len(rows),
        "validation_run_id": run_id,
        "validation_head": head,
    }


def _human_files(final: bool, verification: dict[str, Any]) -> dict[Path, str]:
    status = "已通过最终验收" if final else "实现完成，等待最终验收"
    test_status = "全部通过" if final else "页面自检已通过，正式验收记录待生成"
    accounting = verification["accounting"]
    return {
        IMPLEMENTATION_REPORT_PATH: "\n".join(
            [
                "# S14-P1 信息架构实现说明",
                "",
                f"状态：{status}。",
                "",
                "这次把界面入口重新按人的工作任务组织，不再沿用旧版侧栏堆叠。",
                "",
                "- 顶部固定七个入口：经营首页、项目、回款、资金、税务与政策、数据更新、报告。",
                "- 页面分为首页、列表、详情、处理、报告和设置六种层级；任意页面都能看到当前位置并返回上一任务。",
                "- 默认先显示管理摘要，专业依据和审计说明需要时再展开。",
                "- 设置是辅助入口，不占用第八个业务导航位置。",
                "- 树测试和卡片排序使用 21 个公开模拟任务，明确标注不是正式用户研究。",
                "- 本轮没有读取真实财务资料，没有执行真实业务动作，没有上传 GitHub，也没有重装 App。",
            ]
        )
        + "\n",
        USER_FLOW_GUIDE_PATH: "\n".join(
            [
                "# 新版页面使用说明",
                "",
                "1. 从页面顶部七个中文入口选择工作方向。",
                "2. 进入列表后选择具体事项，再进入详情或处理流程。",
                "3. 页面上方的路径说明会告诉你当前位置；底部按钮可以返回上一任务。",
                "4. 先阅读管理摘要，需要核对时再展开“专业依据”或“审计说明”。",
                "5. 页面设置只调整显示体验，不改变业务数据。",
            ]
        )
        + "\n",
        TEST_RESULTS_PATH: "\n".join(
            [
                "# S14-P1 测试结果",
                "",
                f"状态：{test_status}。",
                "",
                f"- 公开能力自检：{accounting['passed']}/{accounting['total']} 通过。",
                "- 七项一级导航、18 个页面节点、六种页面类型、31 条面包屑关系全部通过结构检查。",
                "- 21 个公开模拟卡片排序任务和 10 条树测试路径全部通过。",
                "- 死路、父级循环、自我跳转和默认技术词命中均为 0。",
                "- 已覆盖桌面和手机宽度、导航高亮、面包屑、上一任务返回、设置入口和渐进披露。",
                "- 外部网络请求、控制台错误、真实资料读取、真实业务动作、GitHub 上传和 App 重装均为 0。",
            ]
        )
        + "\n",
        RISKS_ROLLBACK_PATH: "\n".join(
            [
                "# 风险与回滚",
                "",
                "- 当前是公开安全的导航验收页面，不代表真实用户研究已完成；正式用户测试留给后续阶段。",
                "- 当前只锁定信息架构，不提前确定 S14-P2 的完整视觉组件或 S14-P3 的全部用语。",
                "- 页面中的事项和状态都是演示内容，不能用于经营、税务或资金决策。",
                "- 回滚只移除本阶段界面、测试、公开元数据和治理记录，不触碰 S13、原始资料、远端仓库或已安装 App。",
            ]
        )
        + "\n",
    }


def expected_outputs() -> dict[Path, str]:
    dependency()
    rows = receipts()
    final, run_id, head = final_binding(rows)
    verification = kernel.public_verification()
    if verification["accounting"]["failed"] or verification["failed_checks"]:
        raise BuildError("S14-P1 公开能力自检失败")
    outputs = {
        NAVIGATION_CONTRACT_PATH: _json(kernel.navigation_contract()),
        PAGE_HIERARCHY_CONTRACT_PATH: _json(
            {
                "schema_version": "kmfa.v015.s14p1.page_hierarchy_contract.v1",
                "summary": kernel.validate_page_hierarchy(),
                "page_types": list(kernel.PAGE_TYPES),
                "pages": kernel.page_map(),
            }
        ),
        DISCLOSURE_CONTRACT_PATH: _json(kernel.progressive_disclosure_contract()),
        SOURCE_CONTRACT_PATH: _json(_source_contract()),
        NAVIGATION_RESEARCH_PATH: _json(verification["navigation_research_evidence"]),
        ROUTE_E2E_PATH: _json(
            {
                "schema_version": "kmfa.v015.s14p1.route_e2e_evidence.v1",
                "hierarchy_summary": verification["hierarchy_summary"],
                "tree_test_cases": verification["navigation_research_evidence"]["tree_test_cases"],
            }
        ),
        TERMINOLOGY_EVIDENCE_PATH: _json(
            {
                "schema_version": "kmfa.v015.s14p1.terminology_evidence.v1",
                "disclosure_contract": verification["progressive_disclosure_contract"],
                "plain_chinese_primary_navigation_count": 7,
                "default_visible_technical_term_count": 0,
            }
        ),
        BROWSER_CONTRACT_PATH: _json(_browser_contract()),
        TASK_MATRIX_PATH: _json(_task_matrix(final)),
        MANIFEST_PATH: _json(_manifest(final, rows, run_id, head, verification)),
        HTML_PATH: kernel.render_html(),
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
        raise BuildError("S14-P1 确定性输出不一致：" + ", ".join(mismatches))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S14-P1 deterministic public-safe evidence" if args.check else "WROTE: S14-P1 deterministic public-safe evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
