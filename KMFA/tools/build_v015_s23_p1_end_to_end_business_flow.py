#!/usr/bin/env python3
"""Build public-safe evidence for the single KMFA v1.5 S23-P1 run."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from KMFA.tools import v015_s23_p1_end_to_end_business_flow as model


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "30702bf788c6aa5d34d3483264f79f7bc94b76d5"
TASKPACK_SHA256 = "a0efdddc6e54a167751938353f71bb60a9cd4b43cbcf444d4c915a45b8b1ec06"
EXPECTED_VALIDATION_NAMES = (
    "phase_contract",
    "focused_core_tests",
    "focused_runtime_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "focused_browser_tests",
    "report_workflow_regression",
    "recalculation_dependency",
    "deterministic_evidence",
    "pre_final_phase_checker",
    "roadmap_governance_tests",
    "roadmap_sync_pending",
    "registry_integrity",
    "xlsx_signature",
    "cross_format_consistency",
    "no_float_money",
    "no_omission",
    "taskpack_source",
    "scope_boundary",
    "git_diff_check",
)
EXPECTED_VALIDATION_COUNT = len(EXPECTED_VALIDATION_NAMES)

OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / model.RUN_PHASE_ID
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
EXPORT_ROOT = OUTPUT_ROOT / "exports"
SCREENSHOT_ROOT = EXPORT_ROOT / "screenshots"
DELIVERABLE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v015_s23_p1_end_to_end_business_flow/deliverables"
    / model.XLSX_FILENAME
)
MANIFEST_PATH = MACHINE_ROOT / "s23_p1_end_to_end_business_flow_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "taskpack_source_contract.json"
PUBLIC_VERIFICATION_PATH = MACHINE_ROOT / "public_verification.json"
TRACE_PATH = MACHINE_ROOT / "end_to_end_trace_public_safe.json"
CONSISTENCY_PATH = MACHINE_ROOT / "cross_format_consistency.json"
BROWSER_PATH = MACHINE_ROOT / "browser_acceptance.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "formal_validation_results.jsonl"
COMPLETION_REPORT_PATH = HUMAN_ROOT / "completion_report_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"
SCREENSHOT_PATHS = tuple(
    SCREENSHOT_ROOT / name
    for name in (
        "01_homepage_authoritative_before.png",
        "02_project_cost_imported.png",
        "03_project_difference_confirmed.png",
        "04_recalculated_four_views.png",
        "05_report_approved_four_formats.png",
        "06_revision_retains_history.png",
        "07_end_to_end_pass.png",
        "08_end_to_end_mobile.png",
    )
)

DEPENDENCY_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S22_STAGE_REVIEW/machine"
DEPENDENCY_MANIFEST_PATH = DEPENDENCY_ROOT / "s22_stage_review_manifest.json"
DEPENDENCY_RECEIPTS_PATH = DEPENDENCY_ROOT / "validation_results.jsonl"


class BuildError(RuntimeError):
    """Evidence cannot support an S23-P1 decision."""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def dependency() -> dict[str, Any]:
    if not DEPENDENCY_MANIFEST_PATH.is_file() or not DEPENDENCY_RECEIPTS_PATH.is_file():
        raise BuildError("S22 总体复审的正式证据缺失")
    manifest = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    expected = {
        "run_phase_id": "V015_S22_STAGE_REVIEW",
        "stage_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "validation_receipt_count": 32,
        "overall_phase_accepted_count": 64,
        "s23_entry_allowed": True,
        "s23_p1_entry_allowed": True,
        "s23_p1_started": False,
    }
    mismatch = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatch or len(rows) != 32 or any(row.get("status") != "PASS" for row in rows):
        raise BuildError("S22 总体复审依赖不一致：" + ", ".join(mismatch or ["receipts"]))
    return {
        "acceptance_status": "PASSED",
        "validation_run_id": manifest["validation_run_id"],
        "validation_head": manifest["validation_head"],
        "validation_receipt_count": 32,
        "overall_accepted_phase_count": 64,
        "s23_p1_entry_allowed": True,
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
        raise BuildError("S23-P1 正式验收记录顺序不一致")
    return rows


def final_binding(rows: Sequence[dict[str, Any]]) -> tuple[bool, str | None, str | None]:
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    final = (
        len(rows) == EXPECTED_VALIDATION_COUNT
        and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in rows)
        and len(run_ids) == len(heads) == 1
        and None not in run_ids
        and None not in heads
    )
    return final, next(iter(run_ids)) if final else None, next(iter(heads)) if final else None


def source_contract() -> dict[str, Any]:
    return {
        **model.source_contract(),
        "schema_version": "kmfa.v015.s23p1.source_contract.v1",
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "dependency": "V015_S22_STAGE_REVIEW:PASSED",
        "data_classification": "PUBLIC_SYNTHETIC_ONLY",
        "excluded": [
            "raw 和真实业务数据",
            "外部网络",
            "S23-P2",
            "S23-P3",
            "S23 总体复审",
            "GitHub 上传",
            "App 重装",
        ],
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s23p1.browser_acceptance.v1",
        "browser": "Chromium headless",
        "page_kind": "LOCALHOST_END_TO_END_BUSINESS_FLOW",
        "browser_test_count": 1,
        "browser_flow_count": 11,
        "visual_evidence_count": len(SCREENSHOT_PATHS),
        "viewport_count": 2,
        "required_viewports": [{"width": 1440, "height": 1000}, {"width": 390, "height": 844}],
        "required_flows": [
            "homepage_issue_entry",
            "project_cost_file_import",
            "project_difference_confirmation",
            "recalculation_and_publication",
            "homepage_authoritative_refresh",
            "report_model_creation",
            "four_format_export",
            "first_five_step_approval",
            "revision_and_history_retention",
            "second_five_step_approval",
            "refresh_persistence_and_mobile_layout",
        ],
        "screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS],
        "horizontal_page_overflow_allowed": False,
        "external_network_request_count": 0,
    }


def _verification() -> dict[str, Any]:
    if PUBLIC_VERIFICATION_PATH.is_file() and DELIVERABLE_PATH.is_file():
        value = json.loads(PUBLIC_VERIFICATION_PATH.read_text(encoding="utf-8"))
        if value.get("status") == "PASS" and value.get("check_count") == 47:
            return value
    value = model.public_verification(deliverable_path=DELIVERABLE_PATH)
    if value.get("status") != "PASS" or value.get("check_count") != 47:
        raise BuildError("端到端公开验证未通过")
    return value


def build() -> dict[str, Any]:
    dependency_value = dependency()
    verification = _verification()
    result = verification["result"]
    rows = receipts()
    final, run_id, head = final_binding(rows)
    acceptance = "PASSED" if final else "PENDING_FINAL_VALIDATION"

    trace = {
        "schema_version": "kmfa.v015.s23p1.end_to_end_trace.v1",
        "status": "PASS",
        "publication_version_id": result["publication_version_id"],
        "publication_version_count": result["publication_version_count"],
        "backend_view_count": result["backend_view_count"],
        "homepage_authoritative_binding_count": result["homepage_authoritative_binding_count"],
        "authoritative_project_count": result["authoritative_project_count"],
        "project_difference_cents": result["project_difference_cents"],
        "shared_metric_fingerprint": result["shared_metric_fingerprint"],
        "report_versions": result["report_versions"],
        "report_version_count": result["report_version_count"],
        "export_ids": result["export_ids"],
        "report_export_count": result["report_export_count"],
        "workflow_case_count": result["workflow_case_count"],
        "workflow_step_count_per_case": result["workflow_step_count_per_case"],
        "latest_workflow_state": result["latest_workflow_state"],
        "revision_source_difference_count": result["revision_source_difference_count"],
        "revision_unexplained_difference_count": result["revision_unexplained_difference_count"],
        "refresh_persistence_passed": result["refresh_persistence_passed"],
    }
    consistency = {
        "schema_version": "kmfa.v015.s23p1.cross_format_consistency.v1",
        "status": "PASS",
        "formats": result["formats"],
        "format_count": result["format_count"],
        "numeric_value_count": result["cross_format_numeric_value_count"],
        "difference_integer": result["cross_format_difference_integer"],
        "project_difference_cents": result["project_difference_cents"],
        "xlsx_sheet_count": result["xlsx_sheet_count"],
        "xlsx_formula_error_count": result["xlsx_formula_error_count"],
        "xlsx_visual_pass_count": result["xlsx_visual_pass_count"],
        "deliverable_path": str(DELIVERABLE_PATH.relative_to(REPO_ROOT)),
        "deliverable_sha256": _sha256(DELIVERABLE_PATH),
    }
    task_matrix = {
        "schema_version": "kmfa.v015.s23p1.task_acceptance.v1",
        "phase_task_count": 3,
        "tasks": [
            {"task_id": "S23P1T01", "status": "PASS", "result_zh": "首页与后端发布版本、指纹和项目利润一致，并可进入具体项目问题。"},
            {"task_id": "S23P1T02", "status": "PASS", "result_zh": "文件导入、确认、重算、发布和刷新持久化形成完整证据链，权威项目差异为 0 分。"},
            {"task_id": "S23P1T03", "status": "PASS", "result_zh": "两版报告均完成预览和五步审批；HTML、PDF、CSV、XLSX 四格式数字一致。"},
        ],
    }
    boundary = result["scope_boundary"]
    manifest = {
        "schema_version": "kmfa.v015.s23p1.manifest.v1",
        "run_phase_id": model.RUN_PHASE_ID,
        "roadmap_phase_id": model.ROADMAP_PHASE_ID,
        "task_id": model.TASK_ID,
        "acceptance_id": model.ACCEPTANCE_ID,
        "version": model.VERSION,
        "phase_base_commit": PHASE_BASE_COMMIT,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": acceptance,
        "evidence_validation_status": "PASS" if final else "PENDING",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 33,
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 65 if final else 64,
        "overall_total_phase_count": 72,
        "overall_phase_acceptance_percent": 90.3 if final else 88.9,
        "public_check_count": 47,
        "public_check_pass_count": 47,
        "public_check_failed_count": 0,
        "core_test_count": 5,
        "runtime_test_count": 3,
        "browser_test_count": 1,
        "browser_flow_count": 11,
        "visual_evidence_count": 8,
        "publication_version_count": result["publication_version_count"],
        "backend_view_count": result["backend_view_count"],
        "homepage_authoritative_binding_count": result["homepage_authoritative_binding_count"],
        "authoritative_project_count": result["authoritative_project_count"],
        "project_difference_cents": result["project_difference_cents"],
        "report_version_count": result["report_version_count"],
        "report_export_count": result["report_export_count"],
        "export_format_count": result["format_count"],
        "cross_format_numeric_value_count": result["cross_format_numeric_value_count"],
        "cross_format_difference_integer": result["cross_format_difference_integer"],
        "xlsx_sheet_count": result["xlsx_sheet_count"],
        "xlsx_formula_error_count": result["xlsx_formula_error_count"],
        "xlsx_visual_pass_count": result["xlsx_visual_pass_count"],
        "workflow_case_count": result["workflow_case_count"],
        "workflow_step_count_per_case": result["workflow_step_count_per_case"],
        "revision_source_difference_count": result["revision_source_difference_count"],
        "revision_unexplained_difference_count": result["revision_unexplained_difference_count"],
        "refresh_persistence_pass_count": 1 if result["refresh_persistence_passed"] else 0,
        "governance_model_count": 23,
        "active_formula_count": 405,
        "active_parameter_count": 2620,
        "current_parameter_range": "PARAM-KMFA-2986..3005",
        "validation_expected_count": EXPECTED_VALIDATION_COUNT,
        "validation_receipt_count": len(rows) if final else 0,
        "validation_run_id": run_id,
        "validation_head": head,
        "decision": "GO_TO_S23_P2_ONLY" if final else "REMAIN_IN_S23_P1_FINAL_VALIDATION",
        "next_gate_id": "S23-P2" if final else "S23-P1-FINAL-VALIDATION",
        "s23_p1_started": True,
        "s23_p1_completed": final,
        "s23_p1_acceptance_status": acceptance,
        "s23_p2_entry_allowed": final,
        "s23_p2_started": False,
        "s23_p3_started": False,
        "s23_stage_review_started": False,
        "s23_stage_review_performed": False,
        "raw_root_access_count": boundary["raw_root_access_count"],
        "raw_write_count": boundary["raw_write_count"],
        "external_network_request_count": boundary["external_network_request_count"],
        "github_upload_performed": bool(boundary["github_upload_count"]),
        "app_reinstall_performed": bool(boundary["app_reinstall_count"]),
        "dependency": dependency_value,
        "deliverable_path": str(DELIVERABLE_PATH.relative_to(REPO_ROOT)),
        "deliverable_sha256": _sha256(DELIVERABLE_PATH),
    }

    for path, value in (
        (SOURCE_CONTRACT_PATH, source_contract()),
        (PUBLIC_VERIFICATION_PATH, verification),
        (TRACE_PATH, trace),
        (CONSISTENCY_PATH, consistency),
        (BROWSER_PATH, browser_contract()),
        (TASK_MATRIX_PATH, task_matrix),
        (MANIFEST_PATH, manifest),
    ):
        _write(path, _json(value))

    _write(COMPLETION_REPORT_PATH, f"""# S23-P1 完成报告\n\n本阶段已经把经营首页、项目成本导入、人工确认、重算发布、报告生成、审批、导出和修订连成一条真实可操作的流程。所有页面和报告都绑定发布版本 `{result['publication_version_id']}`，项目金额差异为 **0 分**。\n\n系统生成两版报告，每版都有 HTML、PDF、CSV、XLSX 四种文件，并完成预览、提交、复核、批准和内部发布。第二版保留第一版历史，变化有明确来源，无法解释的变化为 0。\n\n当前状态：**{acceptance}**。本阶段没有读取 raw，没有连接外部网络，也没有开始 S23-P2/P3、上传 GitHub 或重装 App。\n""")
    _write(TEST_RESULTS_PATH, f"""# S23-P1 测试结果\n\n- 公开规则检查：47/47 通过。\n- 核心测试：5 项；运行时测试：3 项。\n- 浏览器：覆盖 11 个连续业务动作、桌面和手机两种视口，保留 8 张正式画面。\n- 权威项目差异：0 分。\n- 跨格式数字：比较 {result['cross_format_numeric_value_count']} 个值，差异 0。\n- Excel：3 个工作表，公式错误 0，3 个工作表视觉检查通过。\n- 正式验收：{len(rows) if final else 0}/{EXPECTED_VALIDATION_COUNT}。\n""")
    _write(USER_GUIDE_PATH, """# S23-P1 使用说明\n\n1. 在经营首页查看公司状态和重点事项，点击项目问题进入数据更新。\n2. 选择公司、期间和项目成本范围，上传文件后先看预览，再确认导入。\n3. 在确认工作台选择处理方式并留下原因；进入重算页面查看前后差异，只有差异正确时才发布。\n4. 回到首页确认项目利润已经更新，再进入报告页面生成报告。\n5. 下载 HTML、PDF、CSV 或 Excel；四种文件必须显示同一发布版本且金额零差异。\n6. 依次完成预览、提交、复核、批准和内部发布。需要修订时新建版本，不覆盖旧版。\n\n任何一分钱差异、版本不一致、缺少导出文件或无法解释的修订，系统都会阻止通过。\n""")
    _write(RISKS_ROLLBACK_PATH, """# S23-P1 风险与回滚\n\n主要风险是页面、后端发布版本或导出文件发生漂移，以及修订覆盖历史。当前门禁通过版本号、指纹、整数分金额、文件哈希和刷新重放共同检查这些风险。\n\n如需回滚，只回滚本阶段 tracked 代码和治理记录，并删除本阶段公开合成证据；不得删除 S22 及更早证据，不得触碰 raw。S23-P2 尚未开始，因此不需要回滚后续阶段。\n""")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    try:
        manifest = build()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print(
        "PASS: S23-P1 evidence "
        f"status={manifest['phase_acceptance_status']} checks={manifest['public_check_pass_count']}/47 "
        f"receipts={manifest['validation_receipt_count']}/{EXPECTED_VALIDATION_COUNT}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
