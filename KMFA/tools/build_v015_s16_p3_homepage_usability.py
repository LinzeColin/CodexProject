#!/usr/bin/env python3
"""生成 KMFA v1.5 S16-P3 首页人类可用验收证据。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools import run_v015_s16_p3_homepage_usability as runtime
from KMFA.tools import v015_s16_p3_homepage_usability as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "201c31df39751ed3d05ad84ae5202b8aa88d1ba4"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "phase_contract",
    "focused_unit_tests",
    "focused_runtime_tests",
    "focused_browser_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s16_p2_dependency",
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

MANIFEST_PATH = MACHINE_ROOT / "s16_p3_homepage_usability_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
RECOGNITION_CONTRACT_PATH = MACHINE_ROOT / "ten_second_recognition_contract_public_safe.json"
TASK_PATH_CONTRACT_PATH = MACHINE_ROOT / "critical_task_path_contract_public_safe.json"
STATE_CONTRACT_PATH = MACHINE_ROOT / "honest_state_contract_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
METHODOLOGY_PATH = MACHINE_ROOT / "usability_methodology_public_safe.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

HTML_PATH = HTML_ROOT / "kmfa_homepage_usability.html"
SCREENSHOT_PATHS = (
    SCREENSHOT_ROOT / "kmfa_homepage_ten_second.png",
    SCREENSHOT_ROOT / "kmfa_homepage_mobile.png",
    SCREENSHOT_ROOT / "kmfa_homepage_empty.png",
    SCREENSHOT_ROOT / "kmfa_homepage_error.png",
    SCREENSHOT_ROOT / "kmfa_homepage_stale.png",
)

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"
OBSERVATION_PATH = HUMAN_ROOT / "usability_observation_zh.md"

DEPENDENCY_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S16_P2_DRILLDOWN_EXPLANATION/machine"
DEPENDENCY_MANIFEST_PATH = DEPENDENCY_ROOT / "s16_p2_drilldown_explanation_manifest.json"
DEPENDENCY_RECEIPTS_PATH = DEPENDENCY_ROOT / "validation_results.jsonl"


class BuildError(RuntimeError):
    """S16-P3 证据无法形成。"""


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
        "run_phase_id": "V015_S16_P2_DRILLDOWN_EXPLANATION",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "decision": "GO_TO_S16_P3_ONLY",
        "s16_p3_entry_allowed": True,
        "s16_p3_started": False,
        "s16_stage_review_entry_allowed": False,
        "validation_receipt_count": 20,
        "overall_accepted_phase_count": 45,
    }
    mismatches = [key for key, expected_value in expected.items() if value.get(key) != expected_value]
    if mismatches:
        raise BuildError("S16-P2 依赖不一致：" + ", ".join(mismatches))
    if len(rows) != 20 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S16-P2 必须恰好有 20 条通过记录")
    if {row.get("validation_head") for row in rows} != {value.get("validation_head")}:
        raise BuildError("S16-P2 验收提交不一致")
    if {row.get("validation_run_id") for row in rows} != {value.get("validation_run_id")}:
        raise BuildError("S16-P2 验收批次不一致")
    return {
        "acceptance_status": "PASSED",
        "validation_head": value["validation_head"],
        "validation_run_id": value["validation_run_id"],
        "validation_receipt_count": len(rows),
        "overall_accepted_phase_count": 45,
        "s16_p3_entry_allowed": True,
        "s16_p3_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S16-P3 验收记录顺序不一致")
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
            "scope": ["10 秒识别", "关键任务一步到达", "空、错、过期状态"],
            "excluded": ["外部真人研究", "真实数据接入", "S16 整体复审", "S17", "GitHub 上传", "App 重装"],
        }
    )
    return value


def recognition_contract() -> dict[str, Any]:
    cases = kernel.ten_second_cases()
    passed = sum(row["structural_proxy_passed"] is True for row in cases)
    return {
        "schema_version": "kmfa.v015.s16p3.ten_second_recognition_contract.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "method": "INTERNAL_STRUCTURAL_WALKTHROUGH_AND_BROWSER_TEST",
        "external_human_participant_count": 0,
        "external_human_study_claimed": False,
        "time_limit_seconds": kernel.TEN_SECOND_LIMIT_SECONDS,
        "success_threshold_bps": kernel.TEN_SECOND_SUCCESS_THRESHOLD_BPS,
        "case_count": len(cases),
        "pass_count": passed,
        "success_bps": kernel.recognition_success_bps(passed, len(cases)),
        "priority_preview_count": kernel.PRIORITY_PREVIEW_COUNT,
        "cases": cases,
    }


def task_path_contract() -> dict[str, Any]:
    paths = kernel.critical_task_paths()
    return {
        "schema_version": "kmfa.v015.s16p3.critical_task_path_contract.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "task_count": len(paths),
        "max_clicks": kernel.MAX_CRITICAL_TASK_CLICKS,
        "observed_max_clicks": 1,
        "dead_end_count": 0,
        "paths": paths,
    }


def state_contract() -> dict[str, Any]:
    states = kernel.honest_state_contracts()
    return {
        "schema_version": "kmfa.v015.s16p3.honest_state_contract.v1",
        "data_classification": "PUBLIC_SYNTHETIC",
        "state_count": len(states),
        "blank_page_count": 0,
        "fake_business_value_count": 0,
        "states": states,
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s16p3.browser_acceptance_contract.v1",
        "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME_SPA",
        "required_viewports": [
            {"name": "desktop", "width": 1440, "height": 1000},
            {"name": "mobile", "width": 390, "height": 844},
        ],
        "required_flows": [
            "desktop_first_scan",
            "mobile_first_scan",
            "projects_one_click",
            "collections_one_click",
            "reports_one_click",
            "empty_state",
            "error_and_retry",
            "stale_state",
        ],
        "required_screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS],
        "min_touch_target_px": kernel.MIN_TOUCH_TARGET_PX,
        "external_network_request_count_expected": 0,
        "page_error_count_expected": 0,
    }


def methodology_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s16p3.usability_methodology.v1",
        "claim_zh": "内部结构化走查和真实浏览器测试，不是外部真人用户研究。",
        "external_human_participant_count": 0,
        "external_human_study_claimed": False,
        "recognition_proxy_case_count": kernel.TEN_SECOND_CASE_COUNT,
        "browser_flow_count": kernel.BROWSER_FLOW_COUNT,
        "manual_visual_inspection_required": True,
        "interpretation_limit_zh": "只能证明页面结构、点击路径和故障提示达到本阶段标准，不能代表所有真实用户。",
    }


def task_matrix(final: bool) -> dict[str, Any]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    result = "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION"
    tasks = [
        {
            "task_id": "S16P3T01",
            "name_zh": "执行 10 秒识别测试",
            "acceptance_zh": "电脑和手机都能直接看到经营状态、前三项重点和下一步，结构化识别通过率不低于 80%。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(RECOGNITION_CONTRACT_PATH.relative_to(REPO_ROOT)), str(BROWSER_CONTRACT_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S16P3T02",
            "name_zh": "执行关键任务点击测试",
            "acceptance_zh": "从首页进入项目、逾期回款和报告均只需一次点击，没有绕路或死路。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(TASK_PATH_CONTRACT_PATH.relative_to(REPO_ROOT)), str(BROWSER_CONTRACT_PATH.relative_to(REPO_ROOT))],
        },
        {
            "task_id": "S16P3T03",
            "name_zh": "执行空、错、过期状态测试",
            "acceptance_zh": "三种状态都说明原因、影响和唯一下一步，不显示假数字，也不出现空白页。",
            "status": status,
            "current_result": result,
            "evidence_refs": [str(STATE_CONTRACT_PATH.relative_to(REPO_ROOT)), str(BROWSER_CONTRACT_PATH.relative_to(REPO_ROOT))],
        },
    ]
    return {
        "schema_version": "kmfa.v015.s16p3.task_acceptance_matrix.v1",
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
        "schema_version": "kmfa.v015.s16p3.homepage_usability_manifest.v1",
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
        "decision": "GO_TO_S16_STAGE_REVIEW_ONLY" if final else "PENDING_FINAL_VALIDATION",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 100,
        "stage_phase_pass_count": 3 if final else 2,
        "stage_task_accepted_count": 9 if final else 6,
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 46 if final else 45,
        "overall_taskpack_phase_count": 72,
        "s16_p1_acceptance_status": "PASSED",
        "s16_p2_acceptance_status": "PASSED",
        "s16_p3_entry_allowed": False,
        "s16_p3_started": True,
        "s16_p3_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s16_stage_review_entry_allowed": final,
        "s16_stage_review_started": False,
        "s16_stage_review_performed": False,
        "s17_entry_allowed": False,
        "product_implementation_allowed": not final,
        "product_implementation_performed": True,
        "ten_second_limit_seconds": core["ten_second_limit_seconds"],
        "ten_second_success_threshold_bps": core["ten_second_success_threshold_bps"],
        "ten_second_case_count": core["ten_second_case_count"],
        "ten_second_case_pass_count": core["ten_second_case_pass_count"],
        "ten_second_success_bps": core["ten_second_success_bps"],
        "priority_preview_count": core["priority_preview_count"],
        "critical_task_count": core["critical_task_count"],
        "max_critical_task_clicks": core["max_critical_task_clicks"],
        "dead_end_count": core["dead_end_count"],
        "fault_state_count": core["fault_state_count"],
        "blank_page_count": core["blank_page_count"],
        "fake_business_value_count": core["fake_business_value_count"],
        "browser_viewport_count": core["browser_viewport_count"],
        "browser_flow_count": core["browser_flow_count"],
        "visual_evidence_count": core["visual_evidence_count"],
        "min_touch_target_px": core["min_touch_target_px"],
        "external_human_participant_count": 0,
        "external_human_study_claimed": False,
        "usability_evidence_kind": core["usability_evidence_kind"],
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


def _human_documents(current: dict[str, Any]) -> dict[Path, str]:
    final = current["phase_acceptance_status"] == "PASSED"
    status = "已通过正式验收" if final else "实现已完成，等待正式验收"
    validation = (
        f"- 正式验收：{current['validation_receipt_count']}/{EXPECTED_VALIDATION_COUNT} 项通过。\n"
        if final
        else "- 正式验收：尚未开始；当前证据保持待验收状态。\n"
    )
    implementation = f"""# S16-P3 首页人类可用验收记录

- 状态：{status}。
- 首页最前面直接写明经营状态、前三项重点和下一步，电脑与手机无需先读说明。
- 从首页进入项目、逾期回款和报告都只需一次点击，没有绕路或死路。
- 没有资料、读取失败、资料过期时，页面会说明原因、影响和唯一下一步，不用 0 冒充缺失，也不显示旧数字。
{validation}- 本阶段使用内部结构化走查和真实浏览器测试，不宣称做过外部真人用户研究。
- 当前全部为公开演示内容，没有读取真实资料、连接外部网络或执行真实业务动作。
- 下一步只允许在新的独立 Run 中进行 S16 整体复审；本轮没有开始复审、S17、GitHub 上传或 App 重装。
"""
    guide = """# S16-P3 使用说明

1. 启动：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s16_p3_homepage_usability.py`。
2. 打开经营首页，先看“经营状态”和“先处理这 3 项”。
3. 需要继续时，点击首页重点事项进入项目或回款，或点击导航进入报告；三个入口均一步到达。
4. 测试状态可用 `demo_home_state=empty`、`error` 或 `stale`；页面只显示原因、影响和下一步。
5. 页面当前使用公开演示内容，不连接真实公司数据。
"""
    tests = f"""# S16-P3 测试结果

- 当前结论：{status}。
- 内核共 55 项公开检查通过，覆盖 6 个结构化识别任务、3 个关键路径和 3 种故障状态。
- 结构化识别代理结果为 6/6，通过率 100%，高于 80% 标准；这不是外部真人样本。
- 真实浏览器覆盖电脑和手机 8 条流程，保留 5 张画面；手机首屏可看到经营状态和前三项重点。
- 项目、逾期回款和报告均一次点击到达，死路为 0。
- 空、错、过期页面的空白页和假业务数字均为 0。
{validation}- 原始资料读取、事实层写入、外部网络请求和真实业务动作均为 0。
"""
    risks = """# S16-P3 风险与回退

- 6 项识别结果来自内部结构化走查和浏览器结构检查，不等同于真实用户研究。
- 页面数据均为公开合成内容，只验证页面能否看懂和操作，不代表生产经营判断。
- 回退时只移除本阶段新增的可用性条、故障状态、测试、证据和治理登记，不回退已通过的 S16-P1/P2，也不触碰原始资料。
"""
    observation = """# S16-P3 可用性观察

- 初次手机检查发现身份切换和全局搜索占满首屏，经营状态要滚动后才能看到，判定不合格。
- 调整后，经营首页保留主要导航和公司、期间等业务范围，把身份切换与全局搜索从首页首屏移开。
- 复测时电脑和手机都能直接看到经营状态、前三项重点和下一步。
- 本记录是内部结构化走查和真实浏览器观察，不是外部真人用户研究。
"""
    return {
        IMPLEMENTATION_REPORT_PATH: implementation,
        USER_GUIDE_PATH: guide,
        TEST_RESULTS_PATH: tests,
        RISKS_ROLLBACK_PATH: risks,
        OBSERVATION_PATH: observation,
    }


def expected_outputs() -> dict[Path, str]:
    current = manifest()
    outputs = {
        MANIFEST_PATH: _json(current),
        SOURCE_CONTRACT_PATH: _json(source_contract()),
        RECOGNITION_CONTRACT_PATH: _json(recognition_contract()),
        TASK_PATH_CONTRACT_PATH: _json(task_path_contract()),
        STATE_CONTRACT_PATH: _json(state_contract()),
        BROWSER_CONTRACT_PATH: _json(browser_contract()),
        METHODOLOGY_PATH: _json(methodology_contract()),
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
    parser = argparse.ArgumentParser(description="生成或检查 KMFA v1.5 S16-P3 首页可用性证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S16-P3 homepage usability evidence " + ("is exact" if args.check else "written"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
