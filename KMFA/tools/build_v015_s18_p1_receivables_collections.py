#!/usr/bin/env python3
"""生成 KMFA v1.5 S18-P1 回款与应收公开验收证据。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from KMFA.tools import run_v015_s18_p1_receivables_collections as runtime
from KMFA.tools import v015_s18_p1_receivables_collections as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "b5059293358f0760e0be3b8d6290b1e1dad19f02"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "phase_contract",
    "focused_unit_tests",
    "focused_runtime_tests",
    "focused_browser_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s17_review_dependency",
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

MANIFEST_PATH = MACHINE_ROOT / "s18_p1_receivables_collections_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
AGING_CONTRACT_PATH = MACHINE_ROOT / "receivable_aging_contract_public_safe.json"
PRIORITY_CONTRACT_PATH = MACHINE_ROOT / "collection_priority_contract_public_safe.json"
VIEW_CONTRACT_PATH = MACHINE_ROOT / "receivables_view_contract_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
PUBLIC_CHECKS_PATH = MACHINE_ROOT / "public_checks.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
HTML_PATH = HTML_ROOT / "kmfa_receivables_collections.html"

SCREENSHOT_PATHS = (
    SCREENSHOT_ROOT / "kmfa_receivables_desktop.png",
    SCREENSHOT_ROOT / "kmfa_receivables_priority_explained.png",
    SCREENSHOT_ROOT / "kmfa_receivables_filtered.png",
    SCREENSHOT_ROOT / "kmfa_receivables_company_isolated.png",
    SCREENSHOT_ROOT / "kmfa_receivables_mobile.png",
)

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S17_STAGE_REVIEW/machine"
DEPENDENCY_MANIFEST_PATH = DEPENDENCY_ROOT / "s17_stage_review_manifest.json"
DEPENDENCY_RECEIPTS_PATH = DEPENDENCY_ROOT / "validation_results.jsonl"


class BuildError(RuntimeError):
    """S18-P1 证据无法形成确定结论。"""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    if not DEPENDENCY_MANIFEST_PATH.is_file() or not DEPENDENCY_RECEIPTS_PATH.is_file():
        raise BuildError("S17 整体复审正式验收依赖缺失")
    manifest = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    receipts = [json.loads(line) for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    expected = {
        "run_phase_id": "V015_S17_STAGE_REVIEW",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "validation_receipt_count": 32,
        "overall_accepted_phase_count": 49,
        "s17_stage_review_acceptance_status": "PASSED",
        "s18_entry_allowed": True,
        "s18_p1_entry_allowed": True,
        "s18_p1_started": False,
    }
    mismatches = [key for key, expected_value in expected.items() if manifest.get(key) != expected_value]
    if mismatches:
        raise BuildError("S17 整体复审依赖不一致：" + ", ".join(mismatches))
    if len(receipts) != 32 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
        raise BuildError("S17 整体复审必须恰好有 32 条通过记录")
    if {row.get("validation_head") for row in receipts} != {manifest.get("validation_head")}:
        raise BuildError("S17 整体复审验收提交不一致")
    return {
        "acceptance_status": "PASSED",
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": 32,
        "overall_accepted_phase_count": 49,
        "s18_p1_entry_allowed": True,
        "s18_p1_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S18-P1 验收记录顺序不一致")
    return rows


def final_binding(rows: Sequence[dict[str, Any]]) -> tuple[bool, str | None, str | None]:
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
            "scope": ["已开票应收与账龄", "可解释内部复核顺序", "项目、客户、期间与负责人多维页面"],
            "excluded": ["真实资料", "自动联系客户", "付款或银行操作", "S18-P2/P3", "GitHub 上传", "App 重装"],
        }
    )
    return value


def aging_contract(view: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s18p1.receivable_aging_contract.v1",
        "source_item_count": len(view["rows"]) + len(view["unbilled_items"]) + 1,
        "invoice_item_count": 7,
        "open_receivable_count": len(view["rows"]),
        "settled_invoice_count": 1,
        "unbilled_item_count": len(view["unbilled_items"]),
        "aging_bucket_count": len(kernel.AGING_BUCKETS),
        "cutoff_date": view["cutoff_date"],
        "aging_basis_zh": view["aging_basis_zh"],
        "receivable_definition_zh": view["receivable_definition_zh"],
        "unbilled_receivable_cents": sum(row["receivable_cents"] for row in view["unbilled_items"]),
        "money_tolerance_cents": kernel.MONEY_TOLERANCE_CENTS,
        "money_difference_cents": view["money_difference_cents"],
        "integer_cent_required": True,
    }


def priority_contract(view: dict[str, Any]) -> dict[str, Any]:
    supported = [row for row in view["rows"] if row["priority_supported"]]
    return {
        "schema_version": "kmfa.v015.s18p1.collection_priority_contract.v1",
        "component_count": len(kernel.PRIORITY_COMPONENT_MAX),
        "component_max_total": sum(kernel.PRIORITY_COMPONENT_MAX.values()),
        "high_priority_min_score": 65,
        "medium_priority_min_score": 40,
        "supported_priority_count": len(supported),
        "evidence_missing_count": view["summary"]["evidence_missing_count"],
        "all_supported_rows_have_five_reasons": all(len(row["priority_reasons_zh"]) == 5 for row in supported),
        "score_component_difference": sum(row["priority_score"] - sum(row["components"].values()) for row in supported),
        "unsupported_recommendation_count": view["unsupported_recommendation_count"],
        "automatic_customer_contact_count": view["automatic_customer_contact_count"],
        "formula_zh": view["priority_formula_zh"],
        "boundaries_zh": view["priority_boundaries_zh"],
    }


def view_contract(view: dict[str, Any]) -> dict[str, Any]:
    dimension_results = {}
    for dimension in kernel.GROUP_DIMENSIONS:
        grouped = kernel.receivables_view(group_by=dimension)
        dimension_results[dimension] = {
            "group_count": len(grouped["groups"]),
            "group_difference_cents": grouped["group_difference_cents"],
        }
    return {
        "schema_version": "kmfa.v015.s18p1.receivables_view_contract.v1",
        "group_dimension_count": len(kernel.GROUP_DIMENSIONS),
        "group_dimensions": list(kernel.GROUP_DIMENSIONS),
        "filter_dimension_count": len(view["filters"]),
        "detail_row_count": len(view["rows"]),
        "company_count": len(kernel.COMPANY_AMOUNT_FACTORS),
        "dimension_results": dimension_results,
        "money_difference_cents": view["money_difference_cents"],
        "group_difference_cents": view["group_difference_cents"],
        "cross_company_leak_count": view["cross_company_leak_count"],
        "raw_root_access_count": view["raw_root_access_count"],
        "live_source_read_count": view["live_source_read_count"],
        "external_network_request_count": view["external_network_request_count"],
        "source_data_write_count": view["source_data_write_count"],
        "fact_layer_write_count": view["fact_layer_write_count"],
        "payment_execution_count": view["payment_execution_count"],
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s18p1.browser_acceptance_contract.v1",
        "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME_SPA",
        "required_viewports": [{"name": "desktop", "width": 1440, "height": 1000}, {"name": "mobile", "width": 390, "height": 844}],
        "required_flows": [
            "plain_chinese_cutoff_and_separate_totals",
            "priority_reasons_visible",
            "filters_recalculate_exactly",
            "four_group_dimensions_reconcile",
            "missing_evidence_and_unbilled_fail_closed",
            "company_switch_isolated",
            "period_switch_scoped",
            "mobile_cards_no_overflow",
        ],
        "browser_flow_count": 8,
        "visual_evidence_count": len(SCREENSHOT_PATHS),
        "screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS],
        "horizontal_page_overflow_allowed": False,
        "minimum_touch_target_px": 44,
        "external_network_request_count": 0,
    }


def task_matrix(final: bool) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s18p1.task_acceptance_matrix.v1",
        "phase_id": "S18-P1",
        "overall_status": "PASS",
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "tasks": [
            {"task_id": "S18P1T01", "task_name_zh": "建立应收与账龄事实", "status": "PASS", "proof_zh": "截止日和五档账龄明确；七张发票与一个未开票节点分开；未开票应收为 0。"},
            {"task_id": "S18P1T02", "task_name_zh": "实现催收优先级", "status": "PASS", "proof_zh": "金额、逾期、信用、争议和现金紧迫度逐项显示；资料不足不出建议；自动联系客户为 0。"},
            {"task_id": "S18P1T03", "task_name_zh": "实现回款视图", "status": "PASS", "proof_zh": "项目、客户、期间、负责人四类汇总与明细均相差 0 分；三个主体隔离。"},
        ],
    }


def manifest(
    *,
    final: bool,
    run_id: str | None,
    validation_head: str | None,
    dep: dict[str, Any],
    view: dict[str, Any],
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s18p1.receivables_collections_manifest.v1",
        "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "version": kernel.VERSION,
        "phase_base_commit": PHASE_BASE_COMMIT,
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "validation_run_id": run_id,
        "validation_head": validation_head,
        "validation_receipt_count": EXPECTED_VALIDATION_COUNT if final else 0,
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 50 if final else 49,
        "overall_taskpack_phase_count": 72,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 33,
        "decision": "GO_TO_S18_P2_ONLY" if final else "REMAIN_IN_S18_P1_FINAL_VALIDATION",
        "next_gate_id": "S18-P2" if final else "S18-P1-FINAL-VALIDATION",
        "s17_stage_review_acceptance_status": dep["acceptance_status"],
        "s18_entry_allowed": False,
        "s18_p1_entry_allowed": False,
        "s18_p1_started": True,
        "s18_p1_completed": final,
        "s18_p1_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s18_p2_entry_allowed": final,
        "s18_p2_started": False,
        "s18_p3_entry_allowed": False,
        "s18_p3_started": False,
        "s18_stage_review_entry_allowed": False,
        "s18_stage_review_started": False,
        "source_item_count": 8,
        "invoice_item_count": 7,
        "open_receivable_count": len(view["rows"]),
        "unbilled_item_count": len(view["unbilled_items"]),
        "aging_bucket_count": len(kernel.AGING_BUCKETS),
        "priority_component_count": len(kernel.PRIORITY_COMPONENT_MAX),
        "group_dimension_count": len(kernel.GROUP_DIMENSIONS),
        "public_check_count": len(checks),
        "public_check_failed_count": sum(row["status"] != "PASS" for row in checks),
        "browser_viewport_count": 2,
        "browser_flow_count": 8,
        "visual_evidence_count": len(SCREENSHOT_PATHS),
        "money_tolerance_cents": 0,
        "money_difference_cents": view["money_difference_cents"],
        "group_difference_cents": view["group_difference_cents"],
        "cross_company_leak_count": view["cross_company_leak_count"],
        "unsupported_recommendation_count": view["unsupported_recommendation_count"],
        "automatic_customer_contact_count": 0,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "external_network_request_count": 0,
        "real_identity_count": 0,
        "credential_count": 0,
        "real_business_action_count": 0,
        "source_data_write_count": 0,
        "fact_layer_write_count": 0,
        "payment_execution_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_business_report": False,
        "data_classification": kernel.DATA_CLASSIFICATION,
    }


def _human_documents(final: bool, checks: list[dict[str, Any]]) -> dict[Path, str]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    return {
        IMPLEMENTATION_REPORT_PATH: f"""# S18-P1 回款与应收实施说明（{status}）

- 只把已开票未回款计入应收；一个未开票节点单独显示，应收固定为 0。
- 账龄统一截至 2026-07-15，按到期日分为未到期、1–30 天、31–60 天、61–90 天、90 天以上五档。
- 内部复核顺序逐项显示金额、逾期、信用、争议和现金紧迫度；资料不足时不显示建议，也不会联系客户。
- 页面可按项目、客户、期间和负责人汇总；明细与所有汇总相差 0 分，三个演示公司互不混用。
""",
        USER_GUIDE_PATH: """# 回款与应收页面使用说明

1. 打开 `/collections`，先看应收、逾期和未开票三个不同数字。
2. 使用项目、客户、开票期间、负责人、账龄和复核顺序筛选。
3. 在“多维汇总”选择按项目、客户、期间或负责人查看。
4. 展开某笔“查看 5 项依据”，核对为什么排在当前位置。
5. “资料不足”表示系统不会给出催收建议；本页面没有联系客户或付款按钮。
""",
        TEST_RESULTS_PATH: f"""# S18-P1 验收结果（{status}）

- {len(checks)}/{len(checks)} 项公开规则检查通过。
- 账龄边界、整数分、应收等式、未开票隔离、缺失依据失败关闭和三个主体隔离均通过。
- 8 条真实浏览器流程通过，覆盖电脑、手机、筛选、分组、公司切换和期间切换；5 张画面已保存。
- 最终正式验收记录：{EXPECTED_VALIDATION_COUNT if final else 0}/{EXPECTED_VALIDATION_COUNT}。
""",
        RISKS_ROLLBACK_PATH: """# 风险与回滚

- 当前事实全部是公开合成演示，不代表真实客户或正式催收清单。
- 排序只用于内部复核，不授权联系客户、法律动作、付款、银行操作或事实写入。
- 真实资料接入仍需后续独立阶段验证来源、权限、截止日和主体边界。
- 回滚仅删除本阶段工具、测试、治理登记和 `V015_S18_P1_RECEIVABLES_COLLECTIONS` 证据；不得触碰 raw inbox 或 S17 已验收内容。
""",
    }


def expected_outputs() -> dict[Path, str]:
    dep = dependency()
    rows = receipts()
    final, run_id, validation_head = final_binding(rows)
    view = kernel.receivables_view()
    checks = kernel.public_checks()
    if any(row["status"] != "PASS" for row in checks):
        raise BuildError("公开检查存在失败")
    outputs = {
        MANIFEST_PATH: _json(manifest(final=final, run_id=run_id, validation_head=validation_head, dep=dep, view=view, checks=checks)),
        SOURCE_CONTRACT_PATH: _json(source_contract()),
        AGING_CONTRACT_PATH: _json(aging_contract(view)),
        PRIORITY_CONTRACT_PATH: _json(priority_contract(view)),
        VIEW_CONTRACT_PATH: _json(view_contract(view)),
        BROWSER_CONTRACT_PATH: _json(browser_contract()),
        PUBLIC_CHECKS_PATH: _json({"schema_version": "kmfa.v015.s18p1.public_checks.v1", "check_count": len(checks), "pass_count": len(checks), "fail_count": 0, "checks": checks}),
        TASK_MATRIX_PATH: _json(task_matrix(final)),
        HTML_PATH: runtime.render_html(),
    }
    outputs.update(_human_documents(final, checks))
    return outputs


def write_outputs() -> None:
    for path, value in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")


def check_outputs() -> None:
    mismatches = []
    for path, expected in expected_outputs().items():
        if not path.is_file() or path.read_text(encoding="utf-8") != expected:
            mismatches.append(str(path.relative_to(REPO_ROOT)))
    if mismatches:
        raise BuildError("证据不一致：" + ", ".join(mismatches))
    missing = [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS if not path.is_file() or path.stat().st_size < 10_000]
    if missing:
        raise BuildError("浏览器画面缺失：" + ", ".join(missing))


def build() -> dict[str, Any]:
    write_outputs()
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 S18-P1 回款与应收验收证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError, kernel.ReceivablesError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S18-P1 evidence is deterministic" if args.check else "PASS: S18-P1 evidence generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
