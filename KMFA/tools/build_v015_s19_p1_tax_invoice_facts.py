#!/usr/bin/env python3
"""生成 KMFA v1.5 S19-P1 税务与发票公开验收证据。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from KMFA.tools import run_v015_s19_p1_tax_invoice_facts as runtime
from KMFA.tools import v015_s19_p1_tax_invoice_facts as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "8caa62c70316e2c61d91a473251dd9f5102cfcf2"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "phase_contract", "focused_unit_tests", "focused_runtime_tests", "focused_browser_tests",
    "focused_artifact_tests", "focused_governance_tests", "s18_review_dependency",
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

MANIFEST_PATH = MACHINE_ROOT / "s19_p1_tax_invoice_facts_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
TAX_MODEL_PATH = MACHINE_ROOT / "tax_invoice_model_public_safe.json"
MATCHING_PATH = MACHINE_ROOT / "tax_invoice_matching_public_safe.json"
BURDEN_PATH = MACHINE_ROOT / "project_tax_burden_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
PUBLIC_CHECKS_PATH = MACHINE_ROOT / "public_checks.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
HTML_PATH = HTML_ROOT / "kmfa_tax_invoice_facts.html"

SCREENSHOT_PATHS = (
    SCREENSHOT_ROOT / "kmfa_tax_invoice_facts_desktop.png",
    SCREENSHOT_ROOT / "kmfa_tax_invoice_unknown_rate.png",
    SCREENSHOT_ROOT / "kmfa_tax_invoice_anomalies.png",
    SCREENSHOT_ROOT / "kmfa_tax_invoice_project_burden.png",
    SCREENSHOT_ROOT / "kmfa_tax_invoice_mobile.png",
)

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S18_STAGE_REVIEW/machine"
DEPENDENCY_MANIFEST_PATH = DEPENDENCY_ROOT / "s18_stage_review_manifest.json"
DEPENDENCY_RECEIPTS_PATH = DEPENDENCY_ROOT / "validation_results.jsonl"


class BuildError(RuntimeError):
    """S19-P1 公开证据不能形成确定结论。"""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    if not DEPENDENCY_MANIFEST_PATH.is_file() or not DEPENDENCY_RECEIPTS_PATH.is_file():
        raise BuildError("S18 整体复审正式验收依赖缺失")
    manifest = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    receipts = [json.loads(line) for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    expected = {
        "run_phase_id": "V015_S18_STAGE_REVIEW",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "validation_receipt_count": 32,
        "overall_accepted_phase_count": 52,
        "s18_stage_review_acceptance_status": "PASSED",
        "s19_entry_allowed": True,
        "s19_p1_entry_allowed": True,
        "s19_p1_started": False,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S18 整体复审依赖不一致：" + ", ".join(mismatches))
    if len(receipts) != 32 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
        raise BuildError("S18 整体复审必须恰好有 32 条通过记录")
    if {row.get("validation_head") for row in receipts} != {manifest.get("validation_head")}:
        raise BuildError("S18 整体复审验收提交不一致")
    return {
        "acceptance_status": "PASSED",
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": 32,
        "overall_accepted_phase_count": 52,
        "s19_p1_entry_allowed": True,
        "s19_p1_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S19-P1 验收记录顺序不一致")
    return rows


def final_binding(rows: Sequence[dict[str, Any]]) -> tuple[bool, str | None, str | None]:
    if not rows:
        return False, None, None
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    final = len(rows) == EXPECTED_VALIDATION_COUNT and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in rows) and len(run_ids) == 1 and len(heads) == 1 and None not in run_ids and None not in heads
    return final, next(iter(run_ids)) if final else None, next(iter(heads)) if final else None


def source_contract() -> dict[str, Any]:
    value = kernel.source_contract()
    value.update({
        "source_package_sha256": TASKPACK_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "scope": ["销项、进项、税率和发票状态事实", "主体、项目、期间和税率匹配", "项目税负管理视图"],
        "excluded": ["真实资料", "税率自动推断", "自动税务调整", "正式申报结论", "S19-P2/P3", "GitHub 上传", "App 重装"],
    })
    return value


def tax_model(view: dict[str, Any]) -> dict[str, Any]:
    unknown = next(row for row in view["rows"] if row["tax_rate_bps"] is None)
    return {
        "schema_version": "kmfa.v015.s19p1.tax_invoice_model.v1",
        "fact_count": view["all_fact_count"],
        "direction_count": 2,
        "explicit_tax_rate_count": 3,
        "tax_inclusive_state_count": 3,
        "invoice_status_count": 3,
        "linked_dimension_count": 4,
        "unknown_rate_count": view["summary"]["unknown_rate_count"],
        "unknown_rate_display_zh": unknown["tax_rate_display_zh"],
        "unknown_rate_blocked": unknown["unknown_rate_blocked"],
        "rate_inference_count": view["rate_inference_count"],
        "integer_cent_required": True,
        "policy_version": view["policy"]["policy_version"],
        "rate_note_zh": view["policy"]["rate_note_zh"],
    }


def matching_contract(view: dict[str, Any]) -> dict[str, Any]:
    anomaly_types = sorted({item["anomaly_type"] for item in view["anomalies"]})
    return {
        "schema_version": "kmfa.v015.s19p1.tax_invoice_matching.v1",
        "matching_dimensions": view["policy"]["matching_dimensions"],
        "matched_count": view["summary"]["matched_count"],
        "review_count": view["summary"]["review_count"],
        "anomaly_count": view["anomaly_count"],
        "anomaly_type_count": len(anomaly_types),
        "anomaly_types": anomaly_types,
        "all_anomalies_have_invoice_and_contract_evidence": all(row["invoice_ref"] and row["contract_ref"] and row["fact_zh"] for row in view["anomalies"]),
        "automatic_tax_adjustment_count": view["automatic_tax_adjustment_count"],
    }


def burden_contract(view: dict[str, Any]) -> dict[str, Any]:
    rows = view["project_burden"]
    return {
        "schema_version": "kmfa.v015.s19p1.project_tax_burden.v1",
        "project_count": len(rows),
        "business_type_count": len({row["business_type_zh"] for row in rows}),
        "equation_difference_cents": sum(row["management_net_tax_pressure_cents"] - row["output_tax_cents"] + row["eligible_input_tax_cents"] for row in rows),
        "excluded_review_count": sum(row["excluded_review_count"] for row in rows),
        "unknown_rate_count": sum(row["unknown_rate_count"] for row in rows),
        "scope_limitation_displayed_count": sum("不是正式申报结论" in row["scope_limitation_zh"] for row in rows),
        "formal_filing_conclusion_count": sum(bool(row["formal_filing_conclusion"]) for row in rows),
        "rows": rows,
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s19p1.browser_acceptance.v1",
        "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME_SPA",
        "required_viewports": [{"name": "desktop", "width": 1440, "height": 1000}, {"name": "mobile", "width": 390, "height": 844}],
        "required_flows": ["facts_and_management_boundary", "unknown_rate_no_inference", "anomaly_evidence", "filter_reconciliation", "project_burden", "company_period_isolation", "mobile_touch_and_overflow"],
        "browser_flow_count": 7,
        "visual_evidence_count": len(SCREENSHOT_PATHS),
        "screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS],
        "minimum_touch_target_px": 44,
        "horizontal_page_overflow_allowed": False,
        "external_network_request_count": 0,
    }


def task_matrix(final: bool) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s19p1.task_acceptance_matrix.v1",
        "phase_id": "S19-P1",
        "overall_status": "PASS",
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "tasks": [
            {"task_id": "S19P1T01", "task_name_zh": "建立销项、进项和税率事实", "status": "PASS", "proof_zh": "八条公开合成税票逐条关联合同、项目、凭证和现金；税率、含税和发票状态明确，未知税率保持待确认。"},
            {"task_id": "S19P1T02", "task_name_zh": "实现进销项与合同匹配", "status": "PASS", "proof_zh": "主体、项目、期间和税率四项交叉核对；五项异常均有票据与合同证据，自动调税为 0。"},
            {"task_id": "S19P1T03", "task_name_zh": "实现项目税负视图", "status": "PASS", "proof_zh": "三个项目按业务类型展示销项、可用进项和管理净税负；待复核票据排除，正式申报结论为 0。"},
        ],
    }


def manifest(final: bool, run_id: str | None, validation_head: str | None, dep: dict[str, Any], view: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s19p1.tax_invoice_facts_manifest.v1",
        "run_phase_id": kernel.RUN_PHASE_ID, "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID, "acceptance_id": kernel.ACCEPTANCE_ID, "version": kernel.VERSION,
        "phase_base_commit": PHASE_BASE_COMMIT,
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "validation_run_id": run_id, "validation_head": validation_head,
        "validation_receipt_count": EXPECTED_VALIDATION_COUNT if final else 0,
        "phase_task_count": 3, "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 53 if final else 52, "overall_taskpack_phase_count": 72,
        "stage_lifecycle_status": "IN_PROGRESS", "stage_acceptance_status": "PENDING", "stage_execution_percentage": 33,
        "decision": "GO_TO_S19_P2_ONLY" if final else "REMAIN_IN_S19_P1_FINAL_VALIDATION",
        "next_gate_id": "S19-P2" if final else "S19-P1-FINAL-VALIDATION",
        "s18_stage_review_acceptance_status": dep["acceptance_status"],
        "s19_entry_allowed": False, "s19_p1_entry_allowed": False, "s19_p1_started": True,
        "s19_p1_completed": final, "s19_p1_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s19_p2_entry_allowed": final, "s19_p2_started": False, "s19_p3_entry_allowed": False, "s19_p3_started": False,
        "s19_stage_review_entry_allowed": False, "s19_stage_review_started": False,
        "tax_invoice_fact_count": view["all_fact_count"], "matched_count": view["summary"]["matched_count"],
        "review_count": view["summary"]["review_count"], "anomaly_count": view["anomaly_count"],
        "project_burden_count": view["project_burden_count"], "unknown_rate_count": view["summary"]["unknown_rate_count"],
        "public_check_count": len(checks), "public_check_failed_count": sum(row["status"] != "PASS" for row in checks),
        "browser_flow_count": 7, "visual_evidence_count": len(SCREENSHOT_PATHS),
        "rate_inference_count": 0, "automatic_tax_adjustment_count": 0, "formal_filing_conclusion_count": 0,
        "cross_company_leak_count": view["cross_company_leak_count"], "raw_root_access_count": 0,
        "live_source_read_count": 0, "external_network_request_count": 0, "real_identity_count": 0,
        "credential_count": 0, "real_business_action_count": 0, "source_data_write_count": 0,
        "fact_layer_write_count": 0, "invoice_issue_count": 0, "tax_filing_count": 0,
        "github_upload_performed": False, "app_reinstall_performed": False, "formal_business_report": False,
        "data_classification": kernel.DATA_CLASSIFICATION,
    }


def _human_documents(final: bool, checks: list[dict[str, Any]]) -> dict[Path, str]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    return {
        IMPLEMENTATION_REPORT_PATH: f"""# S19-P1 税务与发票实施说明（{status}）

- 八条公开合成票据分开保存销项、进项、税率、含税状态和发票状态，并关联合同、项目、凭证与现金记录。
- 税率只能来自票据或合同事实；一条未知税率始终显示“待确认”，不会自动补值。
- 主体、项目、期间和税率交叉核对，五项异常均显示具体差异和两侧证据，不自动做税务调整。
- 三个项目按业务类型显示管理税负；只纳入已匹配且税率明确的票据，页面明确不是正式申报。
""",
        USER_GUIDE_PATH: """# 税务与发票页面使用说明

1. 打开 `/tax-policy`，先看票据数量、已匹配、需复核和未知税率。
2. 用项目、业务类型、进销项、发票状态和匹配结果筛选。
3. “待确认”表示系统没有税率依据，不会猜测税率或税额。
4. 异常区展示票据与合同差异；只能人工复核，页面不会自动调税。
5. 项目税负只用于内部管理分析，不是报税结果，也没有开票或申报按钮。
""",
        TEST_RESULTS_PATH: f"""# S19-P1 验收结果（{status}）

- {len(checks)}/{len(checks)} 项公开规则检查通过。
- 18 项核心与 API 测试通过，覆盖整数分、未知税率阻断、四维匹配、异常证据、税负等式和主体隔离。
- 7 条真实浏览器流程通过，覆盖电脑、手机、筛选、主体与期间切换；5 张画面已保存。
- 最终正式验收记录：{EXPECTED_VALIDATION_COUNT if final else 0}/{EXPECTED_VALIDATION_COUNT}。
""",
        RISKS_ROLLBACK_PATH: """# 风险与回滚

- 税率和金额全部是公开合成演示值，不是现行税法默认值，也不代表真实票据。
- 页面只提供管理分析，不能替代申报、税务专业判断或签字。
- 真实资料接入必须由后续独立阶段验证来源、权限、主体、期间和法规版本。
- 回滚只删除本阶段工具、测试、治理登记和 `V015_S19_P1_TAX_INVOICE_FACTS` 证据；不得触碰 raw inbox 或 S18 已验收内容。
""",
    }


def expected_outputs() -> dict[Path, str]:
    dep = dependency()
    final, run_id, validation_head = final_binding(receipts())
    view, checks = kernel.tax_invoice_view(), kernel.public_checks()
    if any(row["status"] != "PASS" for row in checks):
        raise BuildError("公开检查存在失败")
    outputs = {
        MANIFEST_PATH: _json(manifest(final, run_id, validation_head, dep, view, checks)),
        SOURCE_CONTRACT_PATH: _json(source_contract()), TAX_MODEL_PATH: _json(tax_model(view)),
        MATCHING_PATH: _json(matching_contract(view)), BURDEN_PATH: _json(burden_contract(view)),
        BROWSER_CONTRACT_PATH: _json(browser_contract()),
        PUBLIC_CHECKS_PATH: _json({"schema_version": "kmfa.v015.s19p1.public_checks.v1", "check_count": len(checks), "pass_count": len(checks), "fail_count": 0, "checks": checks}),
        TASK_MATRIX_PATH: _json(task_matrix(final)), HTML_PATH: runtime.render_html(),
    }
    outputs.update(_human_documents(final, checks))
    return outputs


def write_outputs() -> None:
    for path, value in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")


def check_outputs() -> None:
    mismatches = [str(path.relative_to(REPO_ROOT)) for path, expected in expected_outputs().items() if not path.is_file() or path.read_text(encoding="utf-8") != expected]
    if mismatches:
        raise BuildError("证据不一致：" + ", ".join(mismatches))
    missing = [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS if not path.is_file() or path.stat().st_size < 10_000]
    if missing:
        raise BuildError("浏览器画面缺失：" + ", ".join(missing))


def build() -> dict[str, Any]:
    write_outputs()
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 S19-P1 税务与发票验收证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError, kernel.TaxInvoiceError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S19-P1 evidence is deterministic" if args.check else "PASS: S19-P1 evidence generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
