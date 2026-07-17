#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S11-P3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s11_p3_check_board_interface as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "72795987584621064122930eda836b4147a6ca96"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_artifact_tests",
    "focused_browser_tests",
    "focused_governance_tests",
    "s11_p2_dependency",
    "deterministic_evidence",
    "pre_final_phase_checker",
    "legacy_board_runtime_regression",
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

MANIFEST_PATH = MACHINE_ROOT / "s11_p3_check_board_interface_manifest.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
INTERACTION_EVIDENCE_PATH = MACHINE_ROOT / "interaction_evidence_public_safe.json"
VISUAL_EVIDENCE_PATH = MACHINE_ROOT / "visual_accessibility_evidence_public_safe.json"
ACTION_FLOW_EVIDENCE_PATH = MACHINE_ROOT / "action_return_flow_evidence_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

HTML_PATH = HTML_ROOT / "kmfa_check_board_interface.html"
SCREENSHOT_PATH = SCREENSHOT_ROOT / "kmfa_check_board_desktop.png"

INTERFACE_CONTRACT_PATH = PROJECT_ROOT / "metadata/quality/v015_s11_p3_interface_contract_public_safe.json"
ACTION_CONTRACT_PATH = PROJECT_ROOT / "metadata/quality/v015_s11_p3_action_flow_contract_public_safe.json"
ACCESSIBILITY_CONTRACT_PATH = PROJECT_ROOT / "metadata/quality/v015_s11_p3_accessibility_contract_public_safe.json"

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_FLOW_GUIDE_PATH = HUMAN_ROOT / "user_flow_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_MANIFEST_PATH = PROJECT_ROOT / "stage_artifacts/V015_S11_P2_CHECK_BOARD_DATA_MODEL/machine/s11_p2_check_board_data_model_manifest.json"
DEPENDENCY_RECEIPTS_PATH = PROJECT_ROOT / "stage_artifacts/V015_S11_P2_CHECK_BOARD_DATA_MODEL/machine/validation_results.jsonl"


class BuildError(RuntimeError):
    pass


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    manifest = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    expected = {
        "run_phase_id": "V015_S11_P2_CHECK_BOARD_DATA_MODEL",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "decision": "CONTINUE_TO_S11_P3_ONLY",
        "s11_p2_started": True,
        "s11_p2_acceptance_status": "PASSED",
        "s11_p3_entry_allowed": True,
        "s11_p3_started": False,
        "validation_receipt_count": 19,
    }
    mismatches = [key for key, expected_value in expected.items() if manifest.get(key) != expected_value]
    if mismatches:
        raise BuildError("S11-P2 dependency mismatch: " + ", ".join(mismatches))
    if len(rows) != 19 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S11-P2 receipts are not exactly 19 PASS records")
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S11-P2 validation head mismatch")
    if {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")}:
        raise BuildError("S11-P2 validation run mismatch")
    return {
        "acceptance_status": "PASSED",
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": len(rows),
        "s11_p3_entry_allowed": True,
        "s11_p3_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S11-P3 validation receipt order mismatch")
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
        "schema_version": "kmfa.v015.s11p3.source_contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "stage_id": "S11",
        "stage_name_zh": "数据质量、完整性与数据源检查板",
        "roadmap_phase_id": "S11-P3",
        "phase_name_zh": "检查板界面",
        "task_count": 3,
        "task_ids": ["S11P3T01", "S11P3T02", "S11P3T03"],
        "task_names_zh": ["设计紧凑可读矩阵", "设计文件详情与处理入口", "实现数据更新联动"],
        "stop_conditions_zh": ["颜色影响阅读时失败。", "没有明确下一步不得通过。", "返回丢失上下文则失败。"],
        "scope": ["商务蓝紧凑矩阵", "中文资料详情", "上传同步确认入口", "返回上下文保留"],
        "excluded": ["S11 整体复审", "真实上传或同步", "正式报告", "GitHub 上传", "App 重装", "真实来源读取"],
    }


def _interface_contract(verification: dict[str, Any]) -> dict[str, Any]:
    payload = verification["payload"]
    return {
        "schema_version": "kmfa.v015.s11p3.interface_contract.v1",
        "data_model_schema": "kmfa.v015.s11p2.board_model.v1",
        "row_count": payload["row_count"],
        "leaf_count": payload["leaf_count"],
        "root_count": len(payload["root_node_ids"]),
        "default_expanded_root_count": len(payload["default_expanded_node_ids"]),
        "matrix_columns_zh": ["检查项目", "状态", "影响报告", "更新时间", "负责人", "下一步"],
        "filters_zh": ["搜索", "负责人", "状态", "只看需要处理"],
        "details_zh": ["资料", "来源与板块", "当前问题", "影响", "负责人", "最近检查", "建议下一步"],
        "status_labels_zh": list(kernel.STATUS_ORDER),
        "business_blue_primary": True,
        "status_color_badge_only": True,
        "large_yellow_surface_count": 0,
        "internal_field_names_visible_by_default": False,
        "frontend_status_mutation_allowed": False,
    }


def _action_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s11p3.action_flow_contract.v1",
        "action_kinds": [
            {"kind": "UPLOAD_SOURCE", "label_zh": "补充或重新提交资料", "backend_recheck_required": True},
            {"kind": "SYNC_SOURCE", "label_zh": "获取最新资料", "backend_recheck_required": True},
            {"kind": "CONFIRM_QUALITY", "label_zh": "确认处理办法", "backend_recheck_required": True},
            {"kind": "VIEW_EVIDENCE", "label_zh": "查看通过依据", "backend_recheck_required": False},
        ],
        "context_fields": list(kernel.CONTEXT_KEYS),
        "preserve_search": True,
        "preserve_status_filters": True,
        "preserve_owner_filter": True,
        "preserve_alert_filter": True,
        "preserve_expanded_nodes": True,
        "preserve_page_scroll": True,
        "preserve_table_scroll": True,
        "restore_keyboard_focus": True,
        "frontend_status_write_count": 0,
        "status_change_requested": False,
        "real_upload_or_sync_performed": False,
    }


def _browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s11p3.browser_acceptance_contract.v1",
        "browser": "Chromium headless",
        "page_kind": "STATIC_PUBLIC_SAFE_HTML",
        "required_viewports": [
            {"name": "desktop", "width": 1440, "height": 1000},
            {"name": "mobile", "width": 390, "height": 844},
        ],
        "required_flows": [
            "search_and_filter",
            "expand_and_collapse",
            "open_plain_chinese_detail",
            "upload_sync_confirm_entry",
            "complete_and_return_to_original_context",
            "keyboard_focus_restore",
            "status_unchanged_after_frontend_flow",
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
            "task_id": "S11P3T01",
            "name_zh": "设计紧凑可读矩阵",
            "acceptance_zh": "商务蓝为主，状态色只用于徽标与图标；无大面积黄色，正文和控件对比达到 WCAG AA。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(HTML_PATH.relative_to(REPO_ROOT)), str(VISUAL_EVIDENCE_PATH.relative_to(REPO_ROOT)), str(SCREENSHOT_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S11P3T02",
            "name_zh": "设计文件详情与处理入口",
            "acceptance_zh": "点击状态可查看资料、质量问题、报告影响、负责人和处理建议，默认界面不用内部字段名。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(HTML_PATH.relative_to(REPO_ROOT)), str(INTERACTION_EVIDENCE_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S11P3T03",
            "name_zh": "实现数据更新联动",
            "acceptance_zh": "可进入上传、同步或确认流程，完成后恢复搜索、筛选、展开项、滚动和焦点；前端不改写状态。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(ACTION_FLOW_EVIDENCE_PATH.relative_to(REPO_ROOT)), str(ACTION_CONTRACT_PATH.relative_to(REPO_ROOT))],
        },
    ]
    return {
        "schema_version": "kmfa.v015.s11p3.task_acceptance_matrix.v1",
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
    visual = verification["visual_contract"]
    payload = verification["payload"]
    return {
        "schema_version": "kmfa.v015.s11p3.check_board_interface_manifest.v1",
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
        "overall_accepted_phase_count": 31 if final else 30,
        "overall_taskpack_phase_count": 72,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 100,
        "stage_phase_pass_count": 3 if final else 2,
        "stage_task_accepted_count": 9 if final else 6,
        "decision": "CONTINUE_TO_S11_STAGE_REVIEW_ONLY" if final else "REMAIN_IN_S11_P3_FINAL_VALIDATION",
        "interface_row_count": payload["row_count"],
        "interface_leaf_count": payload["leaf_count"],
        "matrix_column_count": 6,
        "filter_control_count": 4,
        "action_kind_count": len(kernel.ACTION_KINDS),
        "context_preservation_field_count": len(kernel.CONTEXT_KEYS),
        "visual_contrast_pair_count": len(visual["contrast_pairs"]),
        "visual_contrast_all_pass": visual["contrast_all_pass"],
        "large_yellow_surface_count": visual["large_yellow_surface_count"],
        "large_status_color_surface_count": visual["large_status_color_surface_count"],
        "public_check_accounting": verification["accounting"],
        "frontend_status_mutation_allowed": False,
        "frontend_status_write_count": 0,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "s11_p1_acceptance_status": "PASSED",
        "s11_p2_acceptance_status": "PASSED",
        "s11_p3_started": True,
        "s11_p3_acceptance_status": acceptance,
        "s11_stage_review_entry_allowed": final,
        "s11_stage_review_started": False,
        "s12_entry_allowed": False,
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
    test_status = "全部通过" if final else "界面能力自检已通过，最终收据待生成"
    accounting = verification["accounting"]
    return {
        IMPLEMENTATION_REPORT_PATH: "\n".join([
            "# S11-P3 数据检查板界面实现说明",
            "",
            f"状态：{status}。",
            "",
            "这次完成的是人真正会使用的数据检查板界面。页面用商务蓝和白色为主，异常颜色只出现在小型状态徽标里，不再用大块黄色或红色干扰阅读。",
            "",
            "- 检查项按六层关系展开，默认只显示必要层级，可以搜索、按负责人和状态筛选，也可只看需要处理的项目。",
            "- 点击状态会显示资料、当前问题、报告影响、负责人和建议下一步，普通用户不需要看内部字段名。",
            "- 缺资料、过期和需确认项目分别进入补充资料、获取最新资料或确认处理流程。",
            "- 完成流程后会回到原来的搜索、筛选、展开位置、页面滚动、表格横向位置和键盘焦点。",
            "- 页面只提交处理请求，不能把失败直接改成已通过；状态仍由后端导入和质量检查决定。",
            "- 本轮使用公开模拟状态验收，没有读取真实资料，没有执行真实上传、同步、GitHub 上传或 App 重装。",
        ]) + "\n",
        USER_FLOW_GUIDE_PATH: "\n".join([
            "# 数据检查板使用说明",
            "",
            "1. 先看顶部四种状态数量，再按需要搜索或筛选。",
            "2. 用每行左侧的加号展开来源、板块、文件包、主体、账户和报表层级。",
            "3. 点击状态徽标查看问题、影响、负责人和建议下一步。",
            "4. 对缺资料、过期或需确认项目，进入对应处理流程并提交请求。",
            "5. 点击“完成并返回原位置”，系统会恢复进入流程前的搜索、筛选、展开和滚动位置。",
            "6. 提交请求不会直接改变状态；系统重新导入和检查通过后，状态才会自动更新。",
        ]) + "\n",
        TEST_RESULTS_PATH: "\n".join([
            "# S11-P3 测试结果",
            "",
            f"状态：{test_status}。",
            "",
            f"- 界面能力自检：{accounting['passed']}/{accounting['total']} 通过。",
            "- 7 组文字与背景对比全部达到 WCAG AA；状态同时使用符号、文字和小型徽标。",
            "- 已覆盖桌面和手机宽度、搜索筛选、展开折叠、中文详情、上传/同步/确认入口、完成后返回原位置和键盘焦点恢复。",
            "- 已验证处理流程前后后端状态指纹不变，前端状态写入次数为 0。",
            "- 原始资料读取、真实来源连接、真实上传同步、GitHub 上传、App 重装和业务执行均为 0。",
        ]) + "\n",
        RISKS_ROLLBACK_PATH: "\n".join([
            "# 风险与回滚",
            "",
            "- 当前页面是公开安全验收样板，真实文件选择、真实平台同步和真实确认提交仍需在最终 App 接入时连接受控后端。",
            "- 页面缓存只保存搜索、筛选、展开和滚动位置，不保存真实财务内容。",
            "- 前端不得新增任何直接状态写入；如需扩展动作，必须继续经过后端重新检查。",
            "- 回滚只移除本阶段界面、测试、公开元数据、设计基准和证据，不影响 S11-P1/P2 已通过内容。",
        ]) + "\n",
    }


def expected_outputs() -> dict[Path, str]:
    dependency()
    rows = receipts()
    final, run_id, head = final_binding(rows)
    verification = kernel.public_verification()
    if verification["accounting"]["failed"]:
        raise BuildError("S11-P3 public verification failed")
    outputs = {
        INTERFACE_CONTRACT_PATH: _json(_interface_contract(verification)),
        ACTION_CONTRACT_PATH: _json(_action_contract()),
        ACCESSIBILITY_CONTRACT_PATH: _json(kernel.accessibility_contract()),
        SOURCE_CONTRACT_PATH: _json(_source_contract()),
        INTERACTION_EVIDENCE_PATH: _json({
            "schema_version": "kmfa.v015.s11p3.interaction_evidence.v1",
            "accounting": verification["accounting"],
            "interface_contract": _interface_contract(verification),
            "payload_fingerprint": verification["payload"]["payload_fingerprint"],
        }),
        VISUAL_EVIDENCE_PATH: _json({
            "schema_version": "kmfa.v015.s11p3.visual_accessibility_evidence.v1",
            "visual_contract": verification["visual_contract"],
            "accessibility_contract": verification["accessibility_contract"],
        }),
        ACTION_FLOW_EVIDENCE_PATH: _json({
            "schema_version": "kmfa.v015.s11p3.action_return_flow_evidence.v1",
            "flows": verification["action_return_flows"],
            "context_field_count": len(kernel.CONTEXT_KEYS),
            "frontend_status_write_count": 0,
        }),
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
    print("PASS: deterministic S11-P3 evidence" if args.check else "BUILT: deterministic S11-P3 evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
