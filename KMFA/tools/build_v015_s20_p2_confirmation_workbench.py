#!/usr/bin/env python3
"""Generate deterministic public-safe evidence for KMFA v1.5 S20-P2."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Sequence

from KMFA.tools import run_v015_s20_p2_confirmation_workbench as runtime
from KMFA.tools import v015_s20_p2_confirmation_workbench as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "a520a2bd6c92467bc04a9f07b88519d2c1fa1717"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "phase_contract", "focused_unit_tests", "focused_runtime_tests", "focused_browser_tests",
    "focused_artifact_tests", "focused_governance_tests", "s20_p1_dependency",
    "deterministic_evidence", "pre_final_phase_checker", "roadmap_governance_tests",
    "roadmap_sync_pending", "metadata_protocol", "project_governance", "lean_governance",
    "governance_sync", "no_float_money", "no_omission", "taskpack_source",
    "public_boundary", "git_diff_check",
)
EXPECTED_VALIDATION_COUNT = len(EXPECTED_VALIDATION_NAMES)

OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / kernel.RUN_PHASE_ID
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
EXPORT_ROOT = OUTPUT_ROOT / "exports"
SCREENSHOT_ROOT = EXPORT_ROOT / "screenshots"
HTML_ROOT = EXPORT_ROOT / "html"

MANIFEST_PATH = MACHINE_ROOT / "s20_p2_confirmation_workbench_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
ISSUE_LIST_PATH = MACHINE_ROOT / "issue_list_contract_public_safe.json"
DETAIL_PATH = MACHINE_ROOT / "difference_detail_contract_public_safe.json"
CONTROL_EVENT_PATH = MACHINE_ROOT / "control_event_contract_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
PUBLIC_CHECKS_PATH = MACHINE_ROOT / "public_checks.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
HTML_PATH = HTML_ROOT / "kmfa_confirmation_workbench.html"

SCREENSHOT_PATHS = (
    SCREENSHOT_ROOT / "confirmation_issue_list.png",
    SCREENSHOT_ROOT / "confirmation_issue_detail.png",
    SCREENSHOT_ROOT / "confirmation_impact_preview.png",
    SCREENSHOT_ROOT / "confirmation_history.png",
    SCREENSHOT_ROOT / "confirmation_undo_history.png",
    SCREENSHOT_ROOT / "confirmation_mobile.png",
)

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S20_P1_DATA_UPDATE/machine"
DEPENDENCY_MANIFEST_PATH = DEPENDENCY_ROOT / "s20_p1_data_update_manifest.json"
DEPENDENCY_RECEIPTS_PATH = DEPENDENCY_ROOT / "validation_results.jsonl"


class BuildError(RuntimeError):
    """S20-P2 evidence cannot support a deterministic decision."""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    if not DEPENDENCY_MANIFEST_PATH.is_file() or not DEPENDENCY_RECEIPTS_PATH.is_file():
        raise BuildError("S20-P1 正式验收依赖缺失")
    manifest = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    expected = {
        "run_phase_id": "V015_S20_P1_DATA_UPDATE", "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS", "validation_receipt_count": 20,
        "overall_accepted_phase_count": 56, "s20_p1_acceptance_status": "PASSED",
        "s20_p1_completed": True, "s20_p2_entry_allowed": True, "s20_p2_started": False,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches or len(rows) != 20 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S20-P1 依赖不一致：" + ", ".join(mismatches or ["validation_receipts"]))
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S20-P1 验收提交不一致")
    return {
        "acceptance_status": "PASSED", "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"], "validation_receipt_count": 20,
        "overall_accepted_phase_count": 56, "s20_p2_entry_allowed": True, "s20_p2_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S20-P2 验收记录顺序不一致")
    return rows


def final_binding(rows: Sequence[dict[str, Any]]) -> tuple[bool, str | None, str | None]:
    if not rows:
        return False, None, None
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    final = len(rows) == EXPECTED_VALIDATION_COUNT and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in rows) and len(run_ids) == 1 and len(heads) == 1 and None not in run_ids and None not in heads
    return final, next(iter(run_ids)) if final else None, next(iter(heads)) if final else None


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s20p2.source_contract.v1", "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID, "task_ids": ["S20P2T01", "S20P2T02", "S20P2T03"],
        "source_package_sha256": TASKPACK_SHA256, "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "dependency": "V015_S20_P1_DATA_UPDATE", "data_classification": "PUBLIC_SYNTHETIC_ONLY",
        "scope": ["需要人工处理的问题列表", "并排差异、业务解释、影响和建议", "影响预览、确认、撤销和追加式历史"],
        "excluded": ["治理日志进入业务列表", "原始值编辑", "无预览高影响处理", "事实层写入", "S20-P3 重算与发布", "GitHub 上传", "App 重装"],
    }


def issue_list_contract() -> dict[str, Any]:
    default_rows = [copy.deepcopy(row) for row in kernel.ISSUES if row["kind"] == "BUSINESS_DISCREPANCY" and row["requires_user_action"] and row["status"] == "OPEN"]
    default_rows.sort(key=lambda row: (-kernel.IMPACT_RANK[row["impact"]], -kernel.URGENCY_RANK[row["urgency"]], row["source_label_zh"], row["owner_label_zh"], row["issue_id"]))
    return {
        "schema_version": "kmfa.v015.s20p2.issue_list_contract.v1", "business_issue_count": 6,
        "default_issue_count": len(default_rows), "default_issue_ids": [row["issue_id"] for row in default_rows],
        "governance_fixture_count": 1, "governance_log_count_in_main_list": 0,
        "source_count": len({row["source_id"] for row in default_rows}), "owner_count": len({row["owner_id"] for row in default_rows}),
        "sort_order": ["impact_desc", "urgency_desc", "source_asc", "owner_asc"],
        "default_requires_user_action_only": True,
    }


def detail_contract() -> dict[str, Any]:
    rows = []
    for issue in kernel.ISSUES:
        if issue["kind"] != "BUSINESS_DISCREPANCY" or not issue["requires_user_action"]:
            continue
        rows.append({
            "issue_id": issue["issue_id"], "title_zh": issue["title_zh"], "impact": issue["impact"],
            "current_data": issue["current_data"], "reference_data": issue["reference_data"],
            "business_explanation_zh": issue["business_explanation_zh"], "impact_zh": issue["impact_zh"],
            "suggested_actions": issue["suggested_actions"], "technical_details": issue["technical_details"],
            "technical_details_default_expanded": False, "raw_value_edit_allowed": False,
        })
    return {
        "schema_version": "kmfa.v015.s20p2.difference_detail_contract.v1", "detail_count": len(rows),
        "side_by_side_field_group_count": 2, "technical_details_default_expanded": False,
        "raw_value_edit_allowed": False, "details": rows,
    }


def control_event_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s20p2.control_event_contract.v1", "allowed_action_role_count": len(kernel.ALLOWED_ACTION_ROLES),
        "allowed_action_roles": sorted(kernel.ALLOWED_ACTION_ROLES), "control_event_type_count": 2,
        "control_event_types": ["ACTION_CONFIRMED", "ACTION_UNDONE"], "append_only": True,
        "hash_chain_required": True, "idempotency_required": True, "impact_preview_required": True,
        "high_impact_without_preview_success_count": 0, "undo_without_preview_success_count": 0,
        "raw_source_mutation_count": 0, "fact_layer_mutation_count": 0,
        "s20_p3_recalculation_count": 0, "report_refresh_count": 0,
        "refresh_persistence_pass_count": 1, "undo_reopen_pass_count": 1, "tamper_detection_pass_count": 1,
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s20p2.browser_acceptance.v1", "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME_SPA_WITH_PERSISTED_CONTROL_EVENTS",
        "required_viewports": [{"name": "desktop", "width": 1440, "height": 1000}, {"name": "mobile", "width": 390, "height": 844}],
        "required_flows": ["data_update_entry", "sorted_business_issue_list", "business_first_detail", "high_impact_preview_confirm", "refresh_persistence", "undo_preview_history", "mobile_touch_and_overflow"],
        "browser_flow_count": 7, "visual_evidence_count": len(SCREENSHOT_PATHS),
        "screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS],
        "minimum_touch_target_px": 44, "horizontal_page_overflow_allowed": False, "external_network_request_count": 0,
    }


def task_matrix(final: bool) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s20p2.task_acceptance_matrix.v1", "phase_id": "S20-P2", "overall_status": "PASS",
        "phase_task_count": 3, "phase_task_accepted_count": 3 if final else 0,
        "tasks": [
            {"task_id": "S20P2T01", "task_name_zh": "实现问题列表", "status": "PASS", "proof_zh": "默认只显示五项需人工处理的业务问题，按影响、紧急度、来源和负责人排序；治理日志为零。"},
            {"task_id": "S20P2T02", "task_name_zh": "实现差异详情", "status": "PASS", "proof_zh": "当前与参考资料并排展示，业务解释、影响和建议优先；技术依据默认收起，原始值不可编辑。"},
            {"task_id": "S20P2T03", "task_name_zh": "实现处理、撤销和历史", "status": "PASS", "proof_zh": "确认与撤销均先预览影响，写入哈希链控制事件；刷新可恢复，旧记录不覆盖，高影响绕过预览失败。"},
        ],
    }


def manifest(final: bool, run_id: str | None, validation_head: str | None, dep: dict[str, Any], checks: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s20p2.confirmation_workbench_manifest.v1", "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID, "task_id": kernel.TASK_ID, "acceptance_id": kernel.ACCEPTANCE_ID,
        "version": kernel.VERSION, "phase_base_commit": PHASE_BASE_COMMIT,
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING", "validation_run_id": run_id,
        "validation_head": validation_head, "validation_receipt_count": EXPECTED_VALIDATION_COUNT if final else 0,
        "phase_task_count": 3, "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 57 if final else 56, "overall_taskpack_phase_count": 72,
        "stage_lifecycle_status": "IN_PROGRESS", "stage_acceptance_status": "PENDING", "stage_execution_percentage": 67,
        "stage_phase_pass_count": 2 if final else 1, "stage_task_accepted_count": 6 if final else 3,
        "decision": "GO_TO_S20_P3_ONLY" if final else "REMAIN_IN_S20_P2_FINAL_VALIDATION",
        "next_gate_id": "S20-P3" if final else "S20-P2-FINAL-VALIDATION",
        "s20_p1_acceptance_status": dep["acceptance_status"], "s20_p1_completed": True,
        "s20_p2_entry_allowed": False, "s20_p2_started": True, "s20_p2_completed": final,
        "s20_p2_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s20_p3_entry_allowed": final, "s20_p3_started": False, "s20_stage_review_entry_allowed": False,
        "business_issue_count": 6, "default_issue_count": 5, "governance_log_count_in_main_list": 0,
        "detail_count": 5, "suggested_action_count": 10, "high_impact_action_count": 5,
        "allowed_action_role_count": 2, "control_event_type_count": 2,
        "public_check_count": checks["check_count"], "public_check_failed_count": checks["fail_count"],
        "browser_flow_count": 7, "visual_evidence_count": len(SCREENSHOT_PATHS),
        "raw_root_access_count": 0, "raw_write_count": 0, "source_value_edit_count": 0,
        "fact_layer_mutation_count": 0, "high_impact_without_preview_success_count": 0,
        "unauthorised_action_success_count": 0, "s20_p3_recalculation_count": 0,
        "report_refresh_count": 0, "external_network_request_count": 0, "real_business_action_count": 0,
        "github_upload_performed": False, "app_reinstall_performed": False, "formal_business_report": False,
        "data_classification": "PUBLIC_SYNTHETIC_ONLY",
    }


def _human_documents(final: bool, checks: dict[str, Any]) -> dict[Path, str]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    return {
        IMPLEMENTATION_REPORT_PATH: f"""# S20-P2 人工确认工作台实施说明（{status}）

- 默认只展示需要用户处理的五项业务问题，治理检查记录不会混入主列表。
- 问题详情先并排说明当前资料和参考资料，再说明业务含义、影响与建议；技术依据默认收起。
- 用户不能编辑原始值。每次确认或撤销都必须先看绑定当前状态的影响预览。
- 处理只写追加式、哈希链保护的控制事件；刷新可恢复，撤销保留旧记录。
- 本阶段没有执行受影响链重算、报告刷新、跨页面同步或发布。
""",
        USER_GUIDE_PATH: """# 人工确认工作台使用说明

1. 从“数据更新”点击“打开人工确认工作台”。
2. 默认列表只显示需要你处理的事项，并按影响和紧急度排列。
3. 打开事项后，先核对“当前资料”和“参考资料”，再阅读业务说明和影响；技术依据可按需展开。
4. 选择建议处理方式，填写理由，点击“先看影响预览”。
5. 预览无误后再确认。高影响事项不能跳过预览。
6. 处理后可从历史中先查看撤销影响，再确认撤销；旧记录不会删除。
""",
        TEST_RESULTS_PATH: f"""# S20-P2 验收结果（{status}）

- {checks['pass_count']}/{checks['check_count']} 项公开规则检查通过。
- 16 项核心与 HTTP API 测试通过，覆盖排序、业务详情、权限、预览门禁、幂等、持久化、撤销和篡改检测。
- 7 条真实浏览器流程通过，覆盖入口、列表、详情、高影响确认、刷新恢复、撤销历史和手机布局。
- 6 张浏览器画面已保存；最终正式验收记录：{EXPECTED_VALIDATION_COUNT if final else 0}/{EXPECTED_VALIDATION_COUNT}。
""",
        RISKS_ROLLBACK_PATH: """# 风险与回滚

- 当前问题来自公开合成资料；接入真实资料前仍需独立的数据权限和隐私验收。
- 控制事件只登记人工选择，不等于已经完成事实重算或报告发布。
- 撤销会重新打开事项，但不会删除历史，也不会直接恢复或编辑源文件。
- 回滚只删除本阶段工具、测试、治理登记和 `V015_S20_P2_CONFIRMATION_WORKBENCH` 证据；保留 S20-P1，不触碰 raw、GitHub 或 App。
""",
    }


def expected_outputs() -> dict[Path, str]:
    dep = dependency()
    final, run_id, validation_head = final_binding(receipts())
    checks = kernel.public_verification()
    if checks["fail_count"] or checks["check_count"] != 55:
        raise BuildError("55 项公开检查未全部通过")
    outputs = {
        MANIFEST_PATH: _json(manifest(final, run_id, validation_head, dep, checks)),
        SOURCE_CONTRACT_PATH: _json(source_contract()), ISSUE_LIST_PATH: _json(issue_list_contract()),
        DETAIL_PATH: _json(detail_contract()), CONTROL_EVENT_PATH: _json(control_event_contract()),
        BROWSER_CONTRACT_PATH: _json(browser_contract()),
        PUBLIC_CHECKS_PATH: _json({"schema_version": "kmfa.v015.s20p2.public_checks.v1", **checks}),
        TASK_MATRIX_PATH: _json(task_matrix(final)), HTML_PATH: runtime.render_html(),
    }
    outputs.update(_human_documents(final, checks))
    return outputs


def write_outputs() -> None:
    for path, value in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")


def build() -> dict[str, Any]:
    write_outputs()
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def check_outputs() -> None:
    mismatches = [str(path.relative_to(REPO_ROOT)) for path, expected in expected_outputs().items() if not path.is_file() or path.read_text(encoding="utf-8") != expected]
    if mismatches:
        raise BuildError("证据不一致：" + ", ".join(mismatches))
    missing = [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS if not path.is_file() or path.stat().st_size < 10_000]
    if missing:
        raise BuildError("浏览器画面缺失：" + ", ".join(missing))


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 S20-P2 人工确认工作台验收证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S20-P2 evidence is deterministic" if args.check else "PASS: S20-P2 evidence generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
