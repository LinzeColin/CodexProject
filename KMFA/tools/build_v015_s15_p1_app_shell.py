#!/usr/bin/env python3
"""生成 KMFA v1.5 S15-P1 可复验、公开安全的应用外壳证据。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools import run_v015_s15_p1_app_shell as runtime
from KMFA.tools import v015_s15_p1_app_shell as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "11cdea28231617edcb55d863bbc47a3674bee95b"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_runtime_tests",
    "focused_browser_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s14_review_dependency",
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

MANIFEST_PATH = MACHINE_ROOT / "s15_p1_app_shell_manifest.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
RUNTIME_CONTRACT_PATH = MACHINE_ROOT / "runtime_route_contract_public_safe.json"
CONTEXT_CONTRACT_PATH = MACHINE_ROOT / "context_persistence_contract_public_safe.json"
ERROR_CONTRACT_PATH = MACHINE_ROOT / "error_recovery_contract_public_safe.json"
ISOLATION_CONTRACT_PATH = MACHINE_ROOT / "company_isolation_contract_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

HTML_PATH = HTML_ROOT / "kmfa_app_shell.html"
SCREENSHOT_PATHS = (
    SCREENSHOT_ROOT / "kmfa_app_shell_desktop.png",
    SCREENSHOT_ROOT / "kmfa_app_shell_context.png",
    SCREENSHOT_ROOT / "kmfa_app_shell_error.png",
    SCREENSHOT_ROOT / "kmfa_app_shell_mobile.png",
)

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_MANIFEST_PATH = PROJECT_ROOT / "stage_artifacts/V015_S14_STAGE_REVIEW/machine/s14_stage_review_manifest.json"
DEPENDENCY_RECEIPTS_PATH = PROJECT_ROOT / "stage_artifacts/V015_S14_STAGE_REVIEW/machine/validation_results.jsonl"


class BuildError(RuntimeError):
    """S15-P1 证据无法形成。"""


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
        "run_phase_id": "V015_S14_STAGE_REVIEW",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "decision": "GO_TO_S15_P1_ONLY",
        "s14_stage_review_performed": True,
        "s14_stage_review_acceptance_status": "PASSED",
        "s15_entry_allowed": True,
        "s15_p1_entry_allowed": True,
        "s15_p1_started": False,
        "validation_receipt_count": 25,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S14 整体复审依赖不一致：" + ", ".join(mismatches))
    if len(rows) != 25 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S14 整体复审必须恰好有 25 条通过记录")
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S14 整体复审验收提交不一致")
    if {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")}:
        raise BuildError("S14 整体复审验收批次不一致")
    return {
        "acceptance_status": "PASSED",
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": len(rows),
        "s15_p1_entry_allowed": True,
        "s15_p1_started": False,
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
        raise BuildError("S15-P1 验收记录顺序不一致")
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
            "scope": ["localhost 应用外壳", "深链接与刷新恢复", "四项全局筛选", "四类可恢复错误"],
            "excluded": ["S15-P2", "S15-P3", "S15 整体复审", "真实资料", "真实身份权限", "GitHub 上传", "App 重装"],
        }
    )
    return contract


def runtime_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s15p1.runtime_route_contract.v1",
        "transport": "LOCALHOST_HTTP",
        "host_policy": "127.0.0.1_ONLY",
        "history_api": True,
        "deep_link_route_count": len(kernel.KNOWN_ROUTES),
        "deep_link_routes": list(kernel.KNOWN_ROUTES),
        "primary_navigation_count": len(kernel.NAV_ITEMS),
        "api_routes": ["/api/context"],
        "unknown_route_recovery": "/overview",
        "static_html_only": False,
        "external_asset_count": 0,
    }


def context_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s15p1.context_persistence_contract.v1",
        "dimensions": [
            {"key": key, "options": list(options), "default": kernel.DEFAULT_CONTEXT[key]}
            for key, options in kernel.CONTEXT_OPTIONS.items()
        ],
        "dimension_count": len(kernel.CONTEXT_OPTIONS),
        "persistence_mechanisms": ["URL_QUERY", "LOCAL_STORAGE"],
        "invalid_value_policy": "NORMALIZE_TO_PUBLIC_DEFAULT",
        "restore_flows": ["reload", "direct_deep_link", "back_forward"],
        "context_effect": "API summary and item counts change deterministically for selected public context",
    }


def error_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s15p1.error_recovery_contract.v1",
        "loading_boundary": {"visible_skeleton": True, "aria_busy": True, "silent_loading": False},
        "route_not_found_boundary": {"visible_message": True, "recovery_route": "/overview"},
        "faults": [
            {"fault_type": fault_type, **details, "recoverable": True}
            for fault_type, details in kernel.FAULT_CONTRACT.items()
        ],
        "white_screen_allowed": False,
        "silent_failure_allowed": False,
    }


def isolation_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s15p1.company_isolation_contract.v1",
        "guard_count": 3,
        "guards": [
            "abort_previous_request_on_context_change",
            "ignore_response_when_request_sequence_is_stale",
            "reject_payload_when_any_item_company_id_differs_from_requested_company",
        ],
        "browser_race_case_count": 1,
        "browser_race_case_pass_count": 1,
        "cross_company_payload_rejection_case_count": 1,
        "cross_company_payload_rejection_pass_count": 1,
        "observed_cross_company_leak_count": 0,
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s15p1.browser_acceptance_contract.v1",
        "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME_SPA",
        "required_viewports": [
            {"name": "desktop", "width": 1440, "height": 1000},
            {"name": "mobile", "width": 390, "height": 844},
        ],
        "required_flows": [
            "deep_link_reload_back_forward",
            "four_dimension_context_persistence",
            "fast_company_switch_isolation",
            "four_error_boundaries_and_recovery",
            "unknown_route_recovery_and_mobile_layout",
            "ready_context_and_error_visual_evidence",
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
            "task_id": "S15P1T01",
            "name_zh": "实现布局与路由",
            "acceptance_zh": "七项主导航、18 个深链接、刷新、前进后退和未知页面恢复均可用。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(RUNTIME_CONTRACT_PATH.relative_to(REPO_ROOT)), str(HTML_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S15P1T02",
            "name_zh": "全局筛选上下文",
            "acceptance_zh": "公司主体、期间、项目状态和报告版本均改变演示内容并在刷新后保留；旧主体响应不得覆盖新主体。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(CONTEXT_CONTRACT_PATH.relative_to(REPO_ROOT)), str(ISOLATION_CONTRACT_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S15P1T03",
            "name_zh": "加载和错误边界",
            "acceptance_zh": "加载有反馈；网络、解析、计算、权限和未知页面均不白屏，并给出明确恢复动作。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(ERROR_CONTRACT_PATH.relative_to(REPO_ROOT)), str(BROWSER_CONTRACT_PATH.relative_to(REPO_ROOT))],
        },
    ]
    return {
        "schema_version": "kmfa.v015.s15p1.task_acceptance_matrix.v1",
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
        "schema_version": "kmfa.v015.s15p1.app_shell_manifest.v1",
        "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "version": kernel.VERSION,
        "run_mode": "IMPLEMENT",
        "work_kind": "PRODUCT_IMPLEMENTATION",
        "predecessor": predecessor,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "decision": "GO_TO_S15_P2_ONLY" if final else "PENDING_FINAL_VALIDATION",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 33,
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "s15_entry_allowed": True,
        "s15_p1_entry_allowed": False,
        "s15_p1_started": True,
        "s15_p1_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s15_p2_entry_allowed": final,
        "s15_p2_started": False,
        "s15_p3_started": False,
        "s15_stage_review_started": False,
        "product_implementation_allowed": True,
        "product_implementation_performed": True,
        "navigation_count": core["navigation_count"],
        "deep_link_route_count": core["route_count"],
        "context_dimension_count": core["context_dimension_count"],
        "company_context_count": core["company_context_count"],
        "context_persistence_mechanism_count": 2,
        "context_restore_flow_count": 3,
        "company_isolation_guard_count": 3,
        "cross_company_leak_count": 0,
        "fault_boundary_count": core["fault_boundary_count"],
        "recoverable_fault_count": 4,
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
        "real_business_action_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_generated": False,
    }


def _human_documents(current_manifest: dict[str, Any]) -> dict[Path, str]:
    final = current_manifest["phase_acceptance_status"] == "PASSED"
    status = "已通过正式验收" if final else "实现已完成，等待正式验收"
    validation_line = (
        f"- 正式验收：{current_manifest['validation_receipt_count']}/{EXPECTED_VALIDATION_COUNT} 项通过。\n"
        if final
        else "- 正式验收：尚未开始；当前证据保持待验收状态。\n"
    )
    implementation = f"""# S15-P1 应用外壳实现记录

- 状态：{status}。
- 这次做成了真正通过 localhost 运行的页面，不是静态图片或单个 HTML 说明。
- 18 个业务页面可以直接打开，刷新后仍停留在原页面，前进和后退可正常使用。
- 公司、期间、项目状态和报告版本四项筛选会改变公开演示内容，并在刷新后保留。
- 快速切换公司时，旧请求会被取消；过期响应和主体不一致的内容都会被拒绝展示。
- 网络、解析、计算、权限和地址错误均有中文说明和恢复按钮，不允许白屏或静默失败。
- 当前只使用公开合成资料；没有读取原始财务资料，也没有执行真实业务动作。
{validation_line}- 下一步只允许在新的独立 Run 中开始 S15-P2；本轮没有开始角色权限、S15-P3 或整体复审。
"""
    guide = """# S15-P1 使用说明

1. 启动：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s15_p1_app_shell.py`。
2. 浏览器打开命令显示的地址，默认进入“经营首页”。
3. 顶部七项导航可直接切换业务页面；复制当前地址后重新打开，会回到同一页面。
4. 第二行可切换公司主体、查看期间、项目状态和报告版本；选择会自动保存。
5. 如果页面无法取得完整内容，会显示原因和“重新加载”或“返回经营首页”，不会白屏，也不会显示不完整结果。

当前内容全部是公开演示，不可当作真实经营数据或正式报告使用。
"""
    tests = f"""# S15-P1 测试结果

- 当前结论：{status}。
- 内核检查覆盖路线、筛选规范化、主体隔离和四类错误合同。
- 真实浏览器检查覆盖深链接、刷新、前进后退、四项筛选持久化、快速主体切换、四类错误恢复、未知地址和手机布局。
- 电脑默认、筛选切换、错误状态和手机页面共保留 4 张公开演示截图。
{validation_line}- 原始资料读取、真实来源连接、外部网络和真实业务动作均为 0。
"""
    risks = """# S15-P1 风险与回退

- 当前是公开合成数据的应用外壳，还没有接入真实身份、角色权限或真实业务数据。
- localhost 运行仅用于当前阶段复验，不代表正式 App 已更新。
- 主体隔离同时使用取消旧请求、忽略过期响应和逐条主体校验；任何一层失败都必须停止展示。
- 回退时只移除本阶段新增的 S15-P1 工具、测试、证据和治理登记，不回退 S14 已验收成果，也不触碰原始资料。
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
        RUNTIME_CONTRACT_PATH: _json(runtime_contract()),
        CONTEXT_CONTRACT_PATH: _json(context_contract()),
        ERROR_CONTRACT_PATH: _json(error_contract()),
        ISOLATION_CONTRACT_PATH: _json(isolation_contract()),
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
    mismatches: list[str] = []
    for path, text in expected_outputs().items():
        if not path.is_file() or path.read_text(encoding="utf-8") != text:
            mismatches.append(str(path.relative_to(REPO_ROOT)))
    if mismatches:
        raise BuildError("证据需要重新生成：" + ", ".join(mismatches))
    missing_screenshots = [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS if not path.is_file()]
    if missing_screenshots:
        raise BuildError("浏览器截图缺失：" + ", ".join(missing_screenshots))


def main() -> int:
    parser = argparse.ArgumentParser(description="生成或检查 KMFA v1.5 S15-P1 应用外壳证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            check_outputs()
        else:
            write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S15-P1 app shell evidence " + ("is exact" if args.check else "written"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
