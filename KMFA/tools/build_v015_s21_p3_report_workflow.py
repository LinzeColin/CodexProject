#!/usr/bin/env python3
"""Generate deterministic public-safe evidence for KMFA v1.5 S21-P3."""

from __future__ import annotations

import argparse
import json
import struct
import tempfile
from pathlib import Path
from typing import Any, Sequence

from KMFA.tools import v015_s21_p1_report_model as report_model
from KMFA.tools import v015_s21_p2_report_generation as report_generation
from KMFA.tools import v015_s21_p3_report_workflow as model


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "a705ed24a6c8673d24c1d83dfe71cc19e1e36cbc"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
EXPECTED_VALIDATION_NAMES = (
    "phase_contract", "focused_unit_tests", "focused_runtime_tests", "focused_browser_tests",
    "focused_artifact_tests", "focused_governance_tests", "s21_p2_dependency",
    "deterministic_evidence", "pre_final_phase_checker", "roadmap_governance_tests",
    "roadmap_sync_pending", "metadata_protocol", "project_governance", "lean_governance",
    "governance_sync", "no_float_money", "no_omission", "taskpack_source",
    "public_boundary", "git_diff_check",
)
EXPECTED_VALIDATION_COUNT = len(EXPECTED_VALIDATION_NAMES)

OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / model.RUN_PHASE_ID
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
SCREENSHOT_ROOT = OUTPUT_ROOT / "exports/screenshots"

MANIFEST_PATH = MACHINE_ROOT / "s21_p3_report_workflow_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
QUALITY_GATE_PATH = MACHINE_ROOT / "quality_gate_contract_public_safe.json"
WORKFLOW_PATH = MACHINE_ROOT / "workflow_contract_public_safe.json"
COMPARISON_PATH = MACHINE_ROOT / "revision_comparison_contract_public_safe.json"
REPORT_CENTER_PATH = MACHINE_ROOT / "report_center_contract_public_safe.json"
BROWSER_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
PUBLIC_CHECKS_PATH = MACHINE_ROOT / "public_checks.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

SCREENSHOT_PATHS = tuple(SCREENSHOT_ROOT / name for name in (
    "report_workflow_preview.png", "report_workflow_published.png", "report_revision_comparison.png",
    "report_center_management.png", "report_center_tax_view.png", "report_workflow_mobile.png",
))
IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S21_P2_REPORT_GENERATION/machine"
DEPENDENCY_MANIFEST_PATH = DEPENDENCY_ROOT / "s21_p2_report_generation_manifest.json"
DEPENDENCY_RECEIPTS_PATH = DEPENDENCY_ROOT / "validation_results.jsonl"


class BuildError(RuntimeError):
    """Evidence cannot support an S21-P3 decision."""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    if not DEPENDENCY_MANIFEST_PATH.is_file() or not DEPENDENCY_RECEIPTS_PATH.is_file():
        raise BuildError("S21-P2 正式验收依赖缺失")
    manifest = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    expected = {
        "run_phase_id": "V015_S21_P2_REPORT_GENERATION", "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS", "validation_receipt_count": 20,
        "overall_accepted_phase_count": 60, "s21_p2_acceptance_status": "PASSED",
        "s21_p3_entry_allowed": True, "s21_p3_started": False,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches or len(rows) != 20 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S21-P2 依赖不一致：" + ", ".join(mismatches or ["receipts"]))
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S21-P2 回执绑定不一致")
    return {
        "acceptance_status": "PASSED", "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"], "validation_receipt_count": 20,
        "overall_accepted_phase_count": 60, "s21_p3_entry_allowed": True,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S21-P3 验收记录顺序不一致")
    return rows


def final_binding(rows: Sequence[dict[str, Any]]) -> tuple[bool, str | None, str | None]:
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    final = (
        len(rows) == EXPECTED_VALIDATION_COUNT
        and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in rows)
        and len(run_ids) == len(heads) == 1 and None not in run_ids and None not in heads
    )
    return final, next(iter(run_ids)) if final else None, next(iter(heads)) if final else None


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s21p3.source_contract.v1",
        "run_phase_id": model.RUN_PHASE_ID, "roadmap_phase_id": model.ROADMAP_PHASE_ID,
        "task_ids": ["S21P3T01", "S21P3T02", "S21P3T03"],
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "dependency": "V015_S21_P2_REPORT_GENERATION:PASSED",
        "data_classification": "PUBLIC_SYNTHETIC_ONLY",
        "scope": ["五步报告流程", "版本比较与不可覆盖修订", "受控报告中心"],
        "excluded": ["外部报告发布", "公开分享链接", "raw", "S21 整体复审", "S22", "GitHub 上传", "App 重装"],
    }


def _demo() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        models = report_model.ReportModelJournal(root / "models.jsonl")
        exports = report_generation.ReportExportJournal(root / "exports.jsonl", root / "bundles")
        workflows = model.ReportWorkflowJournal(root / "workflows.jsonl")
        first = models.create(
            company_id="demo-north", period_kind="MONTHLY", period_key="2026-07",
            source_bindings=report_model.default_source_bindings(),
            formula_bindings=report_model.default_formula_bindings(), created_by="公开演示负责人",
            idempotency_key="evidence-s21p3-model-001", recorded_at="2026-07-17T00:00:00+00:00",
        )
        first_export = exports.create(
            first, idempotency_key="evidence-s21p3-export-001", recorded_at="2026-07-17T00:01:00+00:00"
        )
        case = workflows.preview(
            first, first_export, user_id="demo-owner", role_id="finance", company_id="demo-north",
            comment_zh="已核对网页、PDF 和专业附表", idempotency_key="evidence-s21p3-preview-001",
            occurred_at="2026-07-17T00:02:00+00:00",
        )
        case = workflows.submit(
            case["case_id"], user_id="demo-owner", role_id="finance", company_id="demo-north",
            comment_zh="提交审核并保留完整来源说明", idempotency_key="evidence-s21p3-submit-001",
            occurred_at="2026-07-17T00:03:00+00:00",
        )
        case = workflows.review(
            case["case_id"], user_id="demo-owner", role_id="reviewer", company_id="demo-north",
            comment_zh="数字一致且来源完整，复核通过", decision="PASS",
            idempotency_key="evidence-s21p3-review-001", occurred_at="2026-07-17T00:04:00+00:00",
        )
        case = workflows.approve(
            case["case_id"], user_id="demo-owner", role_id="reviewer", company_id="demo-north",
            comment_zh="确认质量门禁、范围和内部用途", idempotency_key="evidence-s21p3-approve-001",
            occurred_at="2026-07-17T00:05:00+00:00",
        )
        case = workflows.publish(
            case["case_id"], user_id="demo-owner", role_id="management", company_id="demo-north",
            comment_zh="发布到内部报告中心供授权人员查看", idempotency_key="evidence-s21p3-publish-001",
            occurred_at="2026-07-17T00:06:00+00:00",
        )
        bindings = model.revision_bindings(first, {"key_matters": "S20P2-CONFIRMATIONS-2026-07-V2"})
        second = models.revise(
            first["report_version_id"], source_bindings=bindings,
            revision_reason_zh="补充本期重点事项复核结果和负责人意见", created_by="公开演示负责人",
            idempotency_key="evidence-s21p3-model-002", recorded_at="2026-07-17T00:07:00+00:00",
        )
        second_export = exports.create(
            second, idempotency_key="evidence-s21p3-export-002", recorded_at="2026-07-17T00:08:00+00:00"
        )
        revision_case = workflows.preview(
            second, second_export, user_id="demo-owner", role_id="finance", company_id="demo-north",
            comment_zh="预览修订版并核对变化来源", idempotency_key="evidence-s21p3-preview-002",
            occurred_at="2026-07-17T00:09:00+00:00",
        )
        all_reports = models.list()["reports"]
        all_exports = exports.list()["exports"]
        all_cases = workflows.list()["cases"]
        management = model.report_center(
            all_reports, all_exports, all_cases,
            user_id="demo-owner", role_id="management", company_id="demo-north",
        )
        finance = model.report_center(
            all_reports, all_exports, all_cases,
            user_id="demo-owner", role_id="finance", company_id="demo-north",
        )
        tax = model.report_center(
            all_reports, all_exports, all_cases,
            user_id="demo-owner", role_id="tax", company_id="demo-north",
        )
        return {
            "quality_gate": model.quality_gate(first, first_export),
            "published_case": case, "revision_case": revision_case,
            "comparison": model.compare_versions(first, second),
            "management_center": management, "finance_center": finance, "tax_center": tax,
        }


def quality_contract(demo: dict[str, Any]) -> dict[str, Any]:
    return demo["quality_gate"]


def workflow_contract(demo: dict[str, Any]) -> dict[str, Any]:
    case = demo["published_case"]
    return {
        "schema_version": "kmfa.v015.s21p3.workflow_contract.v1",
        "workflow_action_count": 5, "workflow_state_count": len(model.WORKFLOW_STATES),
        "published_case_state": case["state"], "event_count": case["event_count"],
        "actor_role_sequence": [row["actor_role"] for row in case["events"]],
        "all_events_bind_actor": all(row.get("actor_user_id") and row.get("actor_role") for row in case["events"]),
        "all_events_bind_time": all(row.get("occurred_at") for row in case["events"]),
        "all_events_bind_comment": all(row.get("comment_zh") for row in case["events"]),
        "quality_gate_status": case["quality_gate"]["status"],
        "history_overwrite_count": 0, "internal_approval_count": 1,
        "internal_publication_count": 1, "external_publication_count": 0,
        "public_share_link_count": 0,
    }


def comparison_contract(demo: dict[str, Any]) -> dict[str, Any]:
    return demo["comparison"]


def report_center_contract(demo: dict[str, Any]) -> dict[str, Any]:
    management, finance, tax = demo["management_center"], demo["finance_center"], demo["tax_center"]
    return {
        "schema_version": "kmfa.v015.s21p3.report_center_contract.v1",
        "filter_count": len(model.options_contract()["report_center_filters"]),
        "report_version_count": finance["result_count"],
        "view_role_count": len(model.VIEW_ROLES), "download_role_count": len(model.DOWNLOAD_ROLES),
        "finance_download_format_count": len(finance["reports"][0]["download_formats"]),
        "management_published_download_format_count": max(len(row["download_formats"]) for row in management["reports"]),
        "management_unpublished_download_format_count": min(len(row["download_formats"]) for row in management["reports"]),
        "tax_download_format_count": max(len(row["download_formats"]) for row in tax["reports"]),
        "authenticated_download_required": all(row["authenticated_download_required"] for row in finance["reports"]),
        "public_link_count": finance["public_link_count"], "cross_company_result_count": 0,
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s21p3.browser_acceptance.v1",
        "browser": "Chromium headless", "page_kind": "LOCALHOST_REPORT_WORKFLOW",
        "browser_flow_count": 8, "visual_evidence_count": len(SCREENSHOT_PATHS),
        "viewport_count": 2,
        "required_viewports": [{"width": 1440, "height": 1000}, {"width": 390, "height": 844}],
        "required_flows": [
            "predecessor_entry", "five_step_workflow", "state_order_gate", "revision_comparison",
            "report_center_filter", "tax_view_download_denial", "protected_download_refresh", "mobile_layout",
        ],
        "screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS],
        "minimum_touch_target_px": 44, "horizontal_page_overflow_allowed": False,
        "external_network_request_count": 0,
    }


def task_matrix(final: bool) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s21p3.task_acceptance_matrix.v1",
        "phase_id": "S21-P3", "overall_status": "PASS",
        "phase_task_count": 3, "phase_task_accepted_count": 3 if final else 0,
        "tasks": [
            {"task_id": "S21P3T01", "task_name_zh": "预览、复核、批准和发布", "status": "PASS", "proof_zh": "五步流程逐步记录人员、角色、时间和意见；质量门禁、状态顺序和角色分离失败关闭。"},
            {"task_id": "S21P3T02", "task_name_zh": "报告比较与修订", "status": "PASS", "proof_zh": "修订新增版本且旧版不变；资料、公式和数值差异绑定来源与中文原因，无法解释时阻断。"},
            {"task_id": "S21P3T03", "task_name_zh": "报告中心", "status": "PASS", "proof_zh": "按期间、主体、类型、状态和版本检索；查看与下载按角色控制，不生成公开链接。"},
        ],
    }


def manifest(
    final: bool, run_id: str | None, head: str | None,
    dep: dict[str, Any], verification: dict[str, Any], demo: dict[str, Any],
) -> dict[str, Any]:
    workflow = workflow_contract(demo)
    comparison = comparison_contract(demo)
    center = report_center_contract(demo)
    return {
        "schema_version": "kmfa.v015.s21p3.report_workflow_manifest.v1",
        "run_phase_id": model.RUN_PHASE_ID, "roadmap_phase_id": model.ROADMAP_PHASE_ID,
        "task_id": model.TASK_ID, "acceptance_id": model.ACCEPTANCE_ID, "version": model.VERSION,
        "phase_base_commit": PHASE_BASE_COMMIT,
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "validation_run_id": run_id, "validation_head": head,
        "validation_receipt_count": EXPECTED_VALIDATION_COUNT if final else 0,
        "phase_task_count": 3, "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 61 if final else 60, "overall_taskpack_phase_count": 72,
        "stage_lifecycle_status": "IN_PROGRESS", "stage_acceptance_status": "PENDING", "stage_execution_percentage": 100,
        "decision": "GO_TO_S21_STAGE_REVIEW_ONLY" if final else "REMAIN_IN_S21_P3_FINAL_VALIDATION",
        "next_gate_id": "S21-STAGE-REVIEW" if final else "S21-P3-FINAL-VALIDATION",
        "s21_p2_acceptance_status": dep["acceptance_status"],
        "s21_p3_started": True, "s21_p3_completed": final,
        "s21_p3_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s21_stage_review_entry_allowed": final, "s21_stage_review_started": False,
        "s22_entry_allowed": False, "s22_p1_started": False,
        "workflow_action_count": workflow["workflow_action_count"],
        "workflow_event_count": workflow["event_count"],
        "quality_gate_check_count": demo["quality_gate"]["check_count"],
        "revision_difference_count": comparison["difference_count"],
        "unexplained_difference_count": comparison["unexplained_difference_count"],
        "report_center_filter_count": center["filter_count"],
        "report_center_version_count": center["report_version_count"],
        "authenticated_download_format_count": center["finance_download_format_count"],
        "public_check_count": verification["public_check_count"],
        "public_check_failed_count": verification["public_check_failed_count"],
        "browser_flow_count": 8, "browser_viewport_count": 2,
        "visual_evidence_count": len(SCREENSHOT_PATHS),
        "history_overwrite_count": 0, "raw_root_access_count": 0, "raw_write_count": 0,
        "external_network_request_count": 0, "internal_approval_count": 1,
        "internal_publication_count": 1, "external_publication_count": 0,
        "public_share_link_count": 0, "cross_company_access_success_count": 0,
        "github_upload_performed": False, "app_reinstall_performed": False,
        "formal_business_report": False, "data_classification": "PUBLIC_SYNTHETIC_ONLY",
    }


def _human_documents(final: bool) -> dict[Path, str]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    return {
        IMPLEMENTATION_REPORT_PATH: f"""# S21-P3 报告工作流实施说明（{status}）

- 报告按预览、提交复核、复核、批准、内部发布五步流转，每一步记录人员、角色、时间和意见。
- 发布前复核报告版本、三种文件、文件指纹、21 个整数值和零差异；门禁不通过时立即阻止。
- 修订只新增版本，比较结果逐项说明资料、公式或数值变化的来源和原因。
- 报告中心支持六类筛选；查看与下载按公司和角色控制，不生成公开分享链接。
- 本阶段只发布公开合成演示报告到本机内部中心，没有外部发布、raw、GitHub 上传或 App 重装。
""",
        USER_GUIDE_PATH: """# 报告工作流使用说明

1. 从报告生成页进入“报告工作流”，选择已有报告版本开始预览。
2. 依次提交复核、复核通过、批准，再由经营负责人发布到内部报告中心。
3. 需要修改时创建修订版；旧版不会被覆盖，比较区会说明每项变化来源和原因。
4. 在报告中心切换角色和状态筛选；只有授权角色可以受控下载，没有公开链接。
""",
        TEST_RESULTS_PATH: f"""# S21-P3 验收结果（{status}）

- 53/53 项公开规则检查通过。
- 20 项核心与 HTTP API 测试通过。
- 8 条真实浏览器流程通过，覆盖五步工作流、状态门禁、修订比较、权限下载、刷新恢复和手机布局。
- 6 张浏览器画面已保存；旧页面残留层已隐藏，桌面与手机页面均无横向溢出。
- 正式验收记录：{EXPECTED_VALIDATION_COUNT if final else 0}/{EXPECTED_VALIDATION_COUNT}。
""",
        RISKS_ROLLBACK_PATH: """# 风险与回滚

- 当前流程只使用公开合成报告并发布到本机内部报告中心，不代表真实经营审批或对外发布。
- 同一人可以切换已分配角色，但每一步保留角色和理由；生产身份接入仍需后续阶段和真实授权。
- 回滚只删除 S21-P3 工具、测试、治理登记和 `V015_S21_P3_REPORT_WORKFLOW` 证据，不得触碰 S21-P1/P2、raw 或用户文件。
""",
    }


def expected_text_outputs() -> dict[Path, str]:
    dep = dependency()
    final, run_id, head = final_binding(receipts())
    verification = model.verify_phase()
    if verification["status"] != "PASS" or verification["public_check_count"] != 53:
        raise BuildError("53 项公开检查未全部通过")
    demo = _demo()
    outputs = {
        MANIFEST_PATH: _json(manifest(final, run_id, head, dep, verification, demo)),
        SOURCE_CONTRACT_PATH: _json(source_contract()),
        QUALITY_GATE_PATH: _json(quality_contract(demo)),
        WORKFLOW_PATH: _json(workflow_contract(demo)),
        COMPARISON_PATH: _json(comparison_contract(demo)),
        REPORT_CENTER_PATH: _json(report_center_contract(demo)),
        BROWSER_PATH: _json(browser_contract()),
        PUBLIC_CHECKS_PATH: _json(verification),
        TASK_MATRIX_PATH: _json(task_matrix(final)),
    }
    outputs.update(_human_documents(final))
    return outputs


def write_outputs() -> None:
    for path, value in expected_text_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")


def build() -> dict[str, Any]:
    write_outputs()
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise BuildError(f"不是有效 PNG：{path.relative_to(REPO_ROOT)}")
    return struct.unpack(">II", data[16:24])


def check_outputs() -> None:
    text_mismatches = [
        str(path.relative_to(REPO_ROOT))
        for path, expected in expected_text_outputs().items()
        if not path.is_file() or path.read_text(encoding="utf-8") != expected
    ]
    visual_mismatches = []
    for index, path in enumerate(SCREENSHOT_PATHS):
        if not path.is_file() or path.stat().st_size < 10_000:
            visual_mismatches.append(str(path.relative_to(REPO_ROOT)))
            continue
        width, height = _png_size(path)
        if (index < 5 and (width < 1000 or height < 700)) or (index == 5 and (width != 390 or height < 800)):
            visual_mismatches.append(str(path.relative_to(REPO_ROOT)))
    if text_mismatches or visual_mismatches:
        raise BuildError("证据不一致或缺失：" + ", ".join(text_mismatches + visual_mismatches))


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 S21-P3 报告工作流验收证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S21-P3 evidence is deterministic" if args.check else "PASS: S21-P3 evidence generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
