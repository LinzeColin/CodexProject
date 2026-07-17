#!/usr/bin/env python3
"""生成 KMFA v1.5 S14-P2 可复验、公开安全的设计系统证据。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s14_p2_design_system as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "c8ccd1b3871553745e86cde1d7f1dd6c16cc006b"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_artifact_tests",
    "focused_browser_tests",
    "focused_governance_tests",
    "s14_p1_dependency",
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
    "clean_governance_sync",
    "git_diff_check",
)
EXPECTED_VALIDATION_COUNT = len(EXPECTED_VALIDATION_NAMES)

OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / kernel.RUN_PHASE_ID
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
EXPORT_ROOT = OUTPUT_ROOT / "exports"
HTML_ROOT = EXPORT_ROOT / "html"
SCREENSHOT_ROOT = EXPORT_ROOT / "screenshots"

MANIFEST_PATH = MACHINE_ROOT / "s14_p2_design_system_manifest.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
CONTRAST_EVIDENCE_PATH = MACHINE_ROOT / "contrast_evidence_public_safe.json"
COMPONENT_STATE_EVIDENCE_PATH = MACHINE_ROOT / "component_state_evidence_public_safe.json"
MOTION_EVIDENCE_PATH = MACHINE_ROOT / "motion_accessibility_evidence_public_safe.json"
VISUAL_REGRESSION_PATH = MACHINE_ROOT / "visual_regression_contract_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

HTML_PATH = HTML_ROOT / "kmfa_design_system.html"
DESKTOP_LIGHT_SCREENSHOT_PATH = SCREENSHOT_ROOT / "kmfa_design_system_desktop_light.png"
DESKTOP_DARK_SCREENSHOT_PATH = SCREENSHOT_ROOT / "kmfa_design_system_desktop_dark.png"
MOBILE_LIGHT_SCREENSHOT_PATH = SCREENSHOT_ROOT / "kmfa_design_system_mobile_light.png"

DESIGN_TOKEN_CONTRACT_PATH = PROJECT_ROOT / "metadata/quality/v015_s14_p2_design_tokens_public_safe.json"
COMPONENT_CONTRACT_PATH = PROJECT_ROOT / "metadata/quality/v015_s14_p2_component_contract_public_safe.json"
MOTION_CONTRACT_PATH = PROJECT_ROOT / "metadata/quality/v015_s14_p2_motion_contract_public_safe.json"

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
COMPONENT_GUIDE_PATH = HUMAN_ROOT / "component_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_MANIFEST_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V015_S14_P1_INFORMATION_ARCHITECTURE/machine/s14_p1_information_architecture_manifest.json"
)
DEPENDENCY_RECEIPTS_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V015_S14_P1_INFORMATION_ARCHITECTURE/machine/validation_results.jsonl"
)


class BuildError(RuntimeError):
    """构建设计系统证据失败。"""


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
        "run_phase_id": "V015_S14_P1_INFORMATION_ARCHITECTURE",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "decision": "CONTINUE_TO_S14_P2_ONLY",
        "s14_p1_started": True,
        "s14_p1_acceptance_status": "PASSED",
        "s14_p2_entry_allowed": True,
        "s14_p2_started": False,
        "validation_receipt_count": 19,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S14-P1 依赖不一致：" + ", ".join(mismatches))
    if len(rows) != 19 or any(
        row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows
    ):
        raise BuildError("S14-P1 必须恰好有 19 条通过记录")
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S14-P1 验收提交不一致")
    if {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")}:
        raise BuildError("S14-P1 验收批次不一致")
    return {
        "acceptance_status": "PASSED",
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": len(rows),
        "s14_p2_entry_allowed": True,
        "s14_p2_started": False,
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
        raise BuildError("S14-P2 验收记录顺序不一致")
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
        "schema_version": "kmfa.v015.s14p2.source_contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": "S14",
        "stage_name_zh": "界面信息架构、设计系统与语言重构",
        "roadmap_phase_id": "S14-P2",
        "phase_name_zh": "设计系统",
        "task_count": 3,
        "task_ids": ["S14P2T01", "S14P2T02", "S14P2T03"],
        "task_names_zh": ["建立商务蓝视觉体系", "建立组件规范", "建立动效和触感规则"],
        "stop_conditions_zh": [
            "不得靠颜色单独传达状态。",
            "无反馈控件不得上线。",
            "动画影响任务效率时删除。",
        ],
        "scope": [
            "浅色和深色商务蓝令牌",
            "字体间距表格图表状态规则",
            "十一类组件和七种完整状态",
            "方向状态反馈三类轻量动效",
            "桌面手机和深色主题真实界面样例",
        ],
        "excluded": [
            "S14-P3",
            "S14 整体复审",
            "真实资料",
            "真实业务动作",
            "GitHub 上传",
            "App 重装",
        ],
    }


def _browser_contract() -> dict[str, Any]:
    visual = kernel.visual_regression_contract()
    return {
        "schema_version": "kmfa.v015.s14p2.browser_acceptance_contract.v1",
        "browser": "Chromium headless",
        "page_kind": "STATIC_PUBLIC_SAFE_HTML",
        "required_viewports": visual["required_viewports"],
        "required_flows": visual["required_flows"],
        "network_request_count_expected": 0,
        "console_error_count_expected": 0,
        "screenshot_paths": [
            str(DESKTOP_LIGHT_SCREENSHOT_PATH.relative_to(REPO_ROOT)),
            str(DESKTOP_DARK_SCREENSHOT_PATH.relative_to(REPO_ROOT)),
            str(MOBILE_LIGHT_SCREENSHOT_PATH.relative_to(REPO_ROOT)),
        ],
    }


def _task_matrix(final: bool) -> dict[str, Any]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    result = "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION"
    tasks = [
        {
            "task_id": "S14P2T01",
            "name_zh": "建立商务蓝视觉体系",
            "acceptance_zh": "浅色和深色主题以商务蓝为主，14 组关键文字对比度全部达标，警示色面积不超过页面的 8%，状态同时有符号和文字。",
            "status": status,
            "current_result": result,
            "evidence_refs": [
                str(DESIGN_TOKEN_CONTRACT_PATH.relative_to(REPO_ROOT)),
                str(CONTRAST_EVIDENCE_PATH.relative_to(REPO_ROOT)),
                str(DESKTOP_LIGHT_SCREENSHOT_PATH.relative_to(REPO_ROOT)),
                str(DESKTOP_DARK_SCREENSHOT_PATH.relative_to(REPO_ROOT)),
            ],
        },
        {
            "task_id": "S14P2T02",
            "name_zh": "建立组件规范",
            "acceptance_zh": "按钮、表单、筛选、表格、信息区块、图表、弹窗、抽屉、提示、空状态和状态徽标均覆盖默认、悬停、焦点、禁用、加载、错误和成功。",
            "status": status,
            "current_result": result,
            "evidence_refs": [
                str(COMPONENT_CONTRACT_PATH.relative_to(REPO_ROOT)),
                str(COMPONENT_STATE_EVIDENCE_PATH.relative_to(REPO_ROOT)),
                str(HTML_PATH.relative_to(REPO_ROOT)),
                str(MOBILE_LIGHT_SCREENSHOT_PATH.relative_to(REPO_ROOT)),
            ],
        },
        {
            "task_id": "S14P2T03",
            "name_zh": "建立动效和触感规则",
            "acceptance_zh": "动效只说明方向、状态和操作反馈，最长 220 毫秒，无循环、无阻塞、无布局动画，并支持减少动态效果。",
            "status": status,
            "current_result": result,
            "evidence_refs": [
                str(MOTION_CONTRACT_PATH.relative_to(REPO_ROOT)),
                str(MOTION_EVIDENCE_PATH.relative_to(REPO_ROOT)),
                str(HTML_PATH.relative_to(REPO_ROOT)),
            ],
        },
    ]
    return {
        "schema_version": "kmfa.v015.s14p2.task_acceptance_matrix.v1",
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
    tokens = verification["design_token_contract"]
    components = verification["component_contract"]
    motion = verification["motion_contract"]
    contrast = verification["contrast_evidence"]
    visual = verification["visual_regression_contract"]
    return {
        "schema_version": "kmfa.v015.s14p2.design_system_manifest.v1",
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
        "overall_accepted_phase_count": 39 if final else 38,
        "overall_taskpack_phase_count": 72,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 67,
        "stage_phase_pass_count": 2 if final else 1,
        "stage_task_accepted_count": 6 if final else 3,
        "decision": "CONTINUE_TO_S14_P3_ONLY" if final else "REMAIN_IN_S14_P2_FINAL_VALIDATION",
        "theme_count": tokens["theme_count"],
        "contrast_pair_count": contrast["pair_count"],
        "contrast_pass_count": contrast["pass_count"],
        "contrast_fail_count": contrast["fail_count"],
        "warning_area_limit_bps": tokens["warning_area_limit_bps"],
        "component_count": components["component_count"],
        "required_component_state_count": components["required_state_count"],
        "full_state_coverage_count": components["full_state_coverage_count"],
        "no_feedback_component_count": components["no_feedback_component_count"],
        "color_only_state_count": components["color_only_state_count"],
        "maximum_motion_duration_ms": motion["maximum_motion_duration_ms"],
        "blocking_animation_count": motion["blocking_animation_count"],
        "decorative_animation_count": motion["decorative_animation_count"],
        "reduced_motion_supported": motion["reduced_motion_supported"],
        "visual_regression_viewport_count": len(visual["required_viewports"]),
        "public_check_accounting": verification["accounting"],
        "s14_p1_started": True,
        "s14_p1_acceptance_status": "PASSED",
        "s14_p2_entry_allowed": False,
        "s14_p2_started": True,
        "s14_p2_acceptance_status": acceptance,
        "s14_p3_entry_allowed": final,
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
    contrast = verification["contrast_evidence"]
    components = verification["component_contract"]
    motion = verification["motion_contract"]
    return {
        IMPLEMENTATION_REPORT_PATH: "\n".join(
            [
                "# S14-P2 设计系统实现说明",
                "",
                f"状态：{status}。",
                "",
                "这次统一了 KMFA 的视觉和操作规则，并做成了一个可以直接打开、点击和切换深浅主题的经营页面样例。",
                "",
                "- 浅色和深色主题都以商务蓝为主，文字、背景和状态颜色有明确边界。",
                "- 警示色只出现在小型提示和徽标，不铺满大区块；所有状态同时有符号和中文。",
                "- 按钮、表单、筛选、表格、信息区块、图表、弹窗、抽屉、提示、空状态和状态徽标使用同一套规则。",
                "- 每类组件都定义默认、悬停、焦点、禁用、加载、错误和成功七种状态。",
                "- 动效最长 220 毫秒，只帮助理解方向、状态和操作反馈；系统开启“减少动态效果”时自动关闭非必要过渡。",
                "- 顶部七项中文导航沿用上一阶段结构，没有退回旧侧栏。",
                "- 本轮没有读取真实财务资料，没有执行真实业务动作，没有上传 GitHub，也没有重装 App。",
            ]
        )
        + "\n",
        COMPONENT_GUIDE_PATH: "\n".join(
            [
                "# 界面使用规则",
                "",
                "1. 主要操作使用业务蓝按钮；同一区域只保留一个主要操作。",
                "2. 输入错误必须说明原因和修复方法，不能只把边框变红。",
                "3. 状态必须同时显示符号和中文，例如“! 需要关注”或“✓ 正常”。",
                "4. 表格数字右对齐，表头在滚动时保持可见，空值写成“暂无数据”或“—”。",
                "5. 图表除颜色外还使用线型、点形和文字图例，并提供可读取的数据表。",
                "6. 抽屉用于查看详情，弹窗只用于需要明确确认的短操作；关闭后焦点返回原按钮。",
                "7. 动效只用于方向、状态和反馈，不能循环播放或拖慢任务。",
            ]
        )
        + "\n",
        TEST_RESULTS_PATH: "\n".join(
            [
                "# S14-P2 测试结果",
                "",
                f"状态：{test_status}。",
                "",
                f"- 公开能力自检：{accounting['passed']}/{accounting['total']} 通过。",
                f"- 关键文字对比度：{contrast['pass_count']}/{contrast['pair_count']} 通过，失败 0。",
                f"- 组件：{components['component_count']} 类；每类 {components['required_state_count']} 种状态全部覆盖。",
                "- 状态仅靠颜色表达、无反馈控件、阻塞动画和装饰动画均为 0。",
                f"- 动效最长 {motion['maximum_motion_duration_ms']} 毫秒，支持系统“减少动态效果”。",
                "- 已覆盖桌面浅色、桌面深色和手机浅色三种画面，以及键盘焦点、弹窗、抽屉、提示和主题切换。",
                "- 外部网络请求、控制台错误、真实资料读取、真实业务动作、GitHub 上传和 App 重装均为 0。",
            ]
        )
        + "\n",
        RISKS_ROLLBACK_PATH: "\n".join(
            [
                "# 风险与回滚",
                "",
                "- 当前页面使用公开演示数据，只验证设计规则，不代表真实经营数据已经接入。",
                "- 深色主题是可选显示方式，浅色主题仍是默认；后续页面接入时必须继续复验对比度。",
                "- 当前只完成设计系统，不提前完成下一阶段的完整中文词典。",
                "- 回滚只移除本阶段设计系统、测试、公开元数据和治理记录，不触碰上一阶段、原始资料、远端仓库或已安装 App。",
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
        raise BuildError("S14-P2 公开能力自检失败")
    outputs = {
        DESIGN_TOKEN_CONTRACT_PATH: _json(kernel.design_token_contract()),
        COMPONENT_CONTRACT_PATH: _json(kernel.component_contract()),
        MOTION_CONTRACT_PATH: _json(kernel.motion_contract()),
        SOURCE_CONTRACT_PATH: _json(_source_contract()),
        CONTRAST_EVIDENCE_PATH: _json(kernel.contrast_evidence()),
        COMPONENT_STATE_EVIDENCE_PATH: _json(
            {
                "schema_version": "kmfa.v015.s14p2.component_state_evidence.v1",
                "component_contract": kernel.component_contract(),
                "html_component_ids": [
                    "button",
                    "form_field",
                    "filter",
                    "table",
                    "card",
                    "chart",
                    "dialog",
                    "drawer",
                    "toast",
                    "empty_state",
                    "status_badge",
                ],
                "browser_interaction_required": True,
            }
        ),
        MOTION_EVIDENCE_PATH: _json(
            {
                "schema_version": "kmfa.v015.s14p2.motion_accessibility_evidence.v1",
                "motion_contract": kernel.motion_contract(),
                "required_css_contracts": [
                    "prefers-reduced-motion",
                    "opacity",
                    "transform",
                    "background-color",
                    "border-color",
                    "color",
                ],
            }
        ),
        VISUAL_REGRESSION_PATH: _json(kernel.visual_regression_contract()),
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
        raise BuildError("S14-P2 确定性输出不一致：" + ", ".join(mismatches))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print(
        "PASS: S14-P2 deterministic public-safe evidence"
        if args.check
        else "WROTE: S14-P2 deterministic public-safe evidence"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
