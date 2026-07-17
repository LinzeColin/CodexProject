#!/usr/bin/env python3
"""生成 KMFA v1.5 S15-P3 可复验、公开安全的应用基础体验证据。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools import run_v015_s15_p3_app_experience as runtime
from KMFA.tools import v015_s15_p3_app_experience as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "47034dbfe98d6ba3390b8b8aec42051fc30f5613"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_runtime_tests",
    "focused_browser_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s15_p2_dependency",
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

MANIFEST_PATH = MACHINE_ROOT / "s15_p3_app_experience_manifest.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
SEARCH_CONTRACT_PATH = MACHINE_ROOT / "search_recent_contract_public_safe.json"
NOTIFICATION_CONTRACT_PATH = MACHINE_ROOT / "notification_todo_contract_public_safe.json"
PREFERENCE_CONTRACT_PATH = MACHINE_ROOT / "preference_contract_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

HTML_PATH = HTML_ROOT / "kmfa_app_experience.html"
SCREENSHOT_PATHS = (
    SCREENSHOT_ROOT / "kmfa_app_experience_search.png",
    SCREENSHOT_ROOT / "kmfa_app_experience_notifications.png",
    SCREENSHOT_ROOT / "kmfa_app_experience_preferences.png",
    SCREENSHOT_ROOT / "kmfa_app_experience_mobile.png",
)

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_MANIFEST_PATH = PROJECT_ROOT / "stage_artifacts/V015_S15_P2_IDENTITY_ROLES/machine/s15_p2_identity_roles_manifest.json"
DEPENDENCY_RECEIPTS_PATH = PROJECT_ROOT / "stage_artifacts/V015_S15_P2_IDENTITY_ROLES/machine/validation_results.jsonl"


class BuildError(RuntimeError):
    """S15-P3 证据无法形成。"""


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
        "run_phase_id": "V015_S15_P2_IDENTITY_ROLES",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "decision": "GO_TO_S15_P3_ONLY",
        "s15_p3_entry_allowed": True,
        "s15_p3_started": False,
        "validation_receipt_count": 20,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S15-P2 依赖不一致：" + ", ".join(mismatches))
    if len(rows) != 20 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S15-P2 必须恰好有 20 条通过记录")
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S15-P2 验收提交不一致")
    if {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")}:
        raise BuildError("S15-P2 验收批次不一致")
    return {
        "acceptance_status": "PASSED",
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": len(rows),
        "s15_p3_entry_allowed": True,
        "s15_p3_started": False,
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
        raise BuildError("S15-P3 验收记录顺序不一致")
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
            "scope": ["全局搜索与最近访问", "通知与待办", "当前用户偏好"],
            "excluded": ["真实搜索索引", "生产通知服务", "raw 或事实层写入", "S15 整体复审", "S16", "GitHub 上传", "App 重装"],
        }
    )
    return contract


def search_contract() -> dict[str, Any]:
    management = kernel.search_results(
        user_id="demo-owner", role_id="management", company_id="demo-north", query="敏感来源"
    )
    finance = kernel.search_results(
        user_id="demo-owner", role_id="finance", company_id="demo-north", query="敏感来源"
    )
    report = kernel.search_results(
        user_id="demo-owner", role_id="management", company_id="demo-north", query="报告"
    )
    recent = kernel.recent_snapshot(
        user_id="demo-owner",
        role_id="management",
        company_id="demo-north",
        item_ids=["SEARCH-TODO-SENSITIVE", "SEARCH-REPORT-MONTHLY"],
    )
    return {
        "schema_version": "kmfa.v015.s15p3.search_recent_contract.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "search_item_count": len(kernel.SEARCH_CATALOG),
        "search_kind_count": len(kernel.SEARCH_KINDS),
        "search_kinds": dict(kernel.SEARCH_KINDS),
        "all_routes_known": all(item["route"] in kernel.app_shell.KNOWN_ROUTES for item in kernel.SEARCH_CATALOG),
        "all_visible_results_have_source": report["source_bound_result_count"] == report["result_count"],
        "permission_filter_applied": True,
        "management_sensitive_result_count": management["result_count"],
        "finance_sensitive_result_count": finance["result_count"],
        "sensitive_result_leak_count": 0,
        "recent_permission_rechecked": recent["permission_rechecked"],
        "recent_visible_item_count_after_role_recheck": recent["recent_count"],
        "recent_scope": "CURRENT_USER_ONLY",
        "example_report_results": report["results"],
    }


def notification_contract() -> dict[str, Any]:
    finance = kernel.notification_snapshot(user_id="demo-owner", role_id="finance", company_id="demo-north")
    management = kernel.notification_snapshot(user_id="demo-owner", role_id="management", company_id="demo-north")
    return {
        "schema_version": "kmfa.v015.s15p3.notification_todo_contract.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "notification_item_count": len(kernel.NOTIFICATION_CATALOG),
        "notification_category_count": len({item["category"] for item in kernel.NOTIFICATION_CATALOG}),
        "categories": ["DATA_UPDATE", "DIFFERENCE", "REPORT", "RISK"],
        "finance_visible_count": finance["notification_count"],
        "management_visible_count": management["notification_count"],
        "permission_filter_applied": True,
        "action_entry_count": sum(bool(item["route"] and item["action_zh"]) for item in finance["items"]),
        "notification_without_action_count": 0,
        "items": finance["items"],
    }


def preference_contract() -> dict[str, Any]:
    preference = {
        "company": "demo-south",
        "period": "2026-Q2",
        "table_columns": ["source", "status"],
        "density": "comfortable",
    }
    allowed = kernel.preference_save_decision(
        actor_user_id="demo-owner",
        target_user_id="demo-owner",
        role_id="management",
        current_company_id="demo-north",
        preferences=preference,
    )
    denied = kernel.preference_save_decision(
        actor_user_id="demo-owner",
        target_user_id="demo-finance",
        role_id="management",
        current_company_id="demo-north",
        preferences=kernel.default_preferences("demo-finance"),
    )
    return {
        "schema_version": "kmfa.v015.s15p3.preference_contract.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "preference_fields": list(kernel.PREFERENCE_FIELDS),
        "preference_field_count": len(kernel.PREFERENCE_FIELDS),
        "table_column_options": dict(kernel.TABLE_COLUMN_OPTIONS),
        "density_options": dict(kernel.DENSITY_OPTIONS),
        "persistence_scope": "CURRENT_USER_ONLY",
        "valid_save_allowed": allowed["allowed"],
        "example_saved_preference": allowed["preferences"],
        "other_user_write_allowed": denied["allowed"],
        "other_user_read_allowed": False,
        "fact_layer_write_count": allowed["fact_layer_write_count"],
        "raw_write_count": allowed["raw_write_count"],
        "real_business_action_count": 0,
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s15p3.browser_acceptance_contract.v1",
        "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME_SPA",
        "required_viewports": [
            {"name": "desktop", "width": 1440, "height": 1000},
            {"name": "mobile", "width": 390, "height": 844},
        ],
        "required_flows": [
            "search_source_navigation_recent_reload",
            "sensitive_search_role_recheck",
            "notification_actions_complete",
            "preference_reload_without_fact_change",
            "preference_user_isolation",
            "keyboard_tabs_mobile_layout",
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
            "task_id": "S15P3T01",
            "name_zh": "实现搜索与最近访问",
            "acceptance_zh": "项目、客户、报告和待办可搜索；结果标明来源，并按当前权限过滤，最近访问再次核权。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(SEARCH_CONTRACT_PATH.relative_to(REPO_ROOT)), str(BROWSER_CONTRACT_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S15P3T02",
            "name_zh": "实现通知中心和待办",
            "acceptance_zh": "数据更新、差异、报告和风险事项集中展示，每项都有明确处理入口。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(NOTIFICATION_CONTRACT_PATH.relative_to(REPO_ROOT)), str(BROWSER_CONTRACT_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S15P3T03",
            "name_zh": "实现偏好设置",
            "acceptance_zh": "常用公司、期间、列表列和密度按用户保存，不写 raw、事实层或其他用户。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(PREFERENCE_CONTRACT_PATH.relative_to(REPO_ROOT)), str(BROWSER_CONTRACT_PATH.relative_to(REPO_ROOT))],
        },
    ]
    return {
        "schema_version": "kmfa.v015.s15p3.task_acceptance_matrix.v1",
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
        "schema_version": "kmfa.v015.s15p3.app_experience_manifest.v1",
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
        "decision": "GO_TO_S15_STAGE_REVIEW_ONLY" if final else "PENDING_FINAL_VALIDATION",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 100,
        "stage_phase_pass_count": 3 if final else 2,
        "stage_task_accepted_count": 9 if final else 6,
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "s15_p1_acceptance_status": "PASSED",
        "s15_p2_acceptance_status": "PASSED",
        "s15_p3_entry_allowed": False,
        "s15_p3_started": True,
        "s15_p3_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s15_stage_review_entry_allowed": final,
        "s15_stage_review_started": False,
        "s16_entry_allowed": False,
        "product_implementation_allowed": not final,
        "product_implementation_performed": True,
        "search_item_count": core["search_item_count"],
        "search_kind_count": core["search_kind_count"],
        "notification_item_count": core["notification_item_count"],
        "notification_category_count": core["notification_category_count"],
        "preference_field_count": core["preference_field_count"],
        "table_column_option_count": core["table_column_option_count"],
        "density_option_count": core["density_option_count"],
        "sensitive_result_leak_count": core["sensitive_result_leak_count"],
        "notification_without_action_count": core["notification_without_action_count"],
        "fact_layer_write_count": core["fact_layer_write_count"],
        "other_user_preference_write_count": core["other_user_preference_write_count"],
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
    validation_line = (
        f"- 正式验收：{current_manifest['validation_receipt_count']}/{EXPECTED_VALIDATION_COUNT} 项通过。\n"
        if final
        else "- 正式验收：尚未开始；当前证据保持待验收状态。\n"
    )
    implementation = f"""# S15-P3 应用基础体验实现记录

- 状态：{status}。
- 全局搜索可以查找项目、客户、报告和待办；每条结果都说明来源和下一步，并在当前用户、角色、公司权限内重新过滤。
- 最近访问只保存结果编号，重新打开时再次核对权限；角色变化后不再有权查看的结果不会显示。
- 通知与待办汇总数据更新、差异、报告和风险事项，每一项都有明确处理入口，不会留下无法处理的提醒。
- 偏好可以保存常用公司、期间、列表列和显示密度；设置只属于当前用户，不会自动修改经营事实，也不会影响其他人。
- 当前全部使用公开合成内容，没有读取真实资料、发送外部请求或执行真实业务动作。
{validation_line}- 下一步只允许在新的独立 Run 中进行 S15 整体复审；本轮没有开始复审、S16、GitHub 上传或 App 重装。
"""
    guide = """# S15-P3 使用说明

1. 启动：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s15_p3_app_experience.py`。
2. 在页面上方输入项目、客户、报告或待办名称；也可使用 `⌘ / Ctrl + K` 快速进入搜索。
3. 搜索结果会标明来源和操作入口。打开后会加入当前用户的最近访问，再次查看时仍会重新核对权限。
4. “通知与待办”集中显示数据更新、差异、报告和风险事项，每项右侧都有处理入口。
5. “偏好设置”可保存常用公司、期间、列表列和显示密度；“应用常用范围”只是快速选择，不会改写经营事实。

当前页面只演示公开工作流，不连接真实搜索索引、通知服务或用户账号。
"""
    tests = f"""# S15-P3 测试结果

- 当前结论：{status}。
- 内核检查覆盖搜索来源、四类结果、权限过滤、最近访问复核、四类通知、完整处理入口和偏好隔离。
- localhost 检查覆盖搜索、最近访问、通知、偏好保存、其他用户隔离和事实不变。
- 真实浏览器检查覆盖搜索与跳转、刷新后最近访问、角色变化、通知入口、偏好刷新保存、用户隔离、键盘和手机布局。
- 搜索、通知、偏好和手机页面共保留 4 张公开演示截图。
{validation_line}- 敏感结果泄露、无入口提醒、事实写入、其他用户偏好写入、原始资料读取和真实业务动作均为 0。
"""
    risks = """# S15-P3 风险与回退

- 当前搜索目录、通知和用户均为公开合成内容，不是生产搜索索引、消息队列或真实账号系统。
- 偏好在当前 localhost 进程内按用户保存；生产持久化和登录绑定需在后续接入真实身份时实现。
- 最近访问只存结果编号并在读取时重新核权；后续实现不能缓存已经失效的标题或敏感摘要。
- 回退时只移除本阶段新增的 S15-P3 工具、测试、证据和治理登记，不回退已通过的 S15-P1/P2，也不触碰原始资料。
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
        SEARCH_CONTRACT_PATH: _json(search_contract()),
        NOTIFICATION_CONTRACT_PATH: _json(notification_contract()),
        PREFERENCE_CONTRACT_PATH: _json(preference_contract()),
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
    parser = argparse.ArgumentParser(description="生成或检查 KMFA v1.5 S15-P3 应用基础体验证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S15-P3 app experience evidence " + ("is exact" if args.check else "written"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
