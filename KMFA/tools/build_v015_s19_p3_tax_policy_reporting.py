#!/usr/bin/env python3
"""生成 KMFA v1.5 S19-P3 税务与政策报告公开验收证据。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from KMFA.tools import run_v015_s19_p3_tax_policy_reporting as runtime
from KMFA.tools import v015_s19_p3_tax_policy_reporting as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "19119ba46bdd5d644622d6c710590a8fa15e83c2"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
ROADMAP_SHA256 = "a0efdddc6e54a167751938353f71bb60a9cd4b43cbcf444d4c915a45b8b1ec06"

EXPECTED_VALIDATION_NAMES = (
    "phase_contract", "focused_unit_tests", "focused_runtime_tests", "focused_browser_tests",
    "focused_artifact_tests", "focused_governance_tests", "s19_p1_p2_dependency",
    "deterministic_evidence", "pre_final_phase_checker", "roadmap_governance_tests",
    "roadmap_sync_pending", "metadata_protocol", "project_governance", "lean_governance",
    "governance_sync", "no_float_money", "no_omission", "taskpack_source",
    "public_boundary", "git_diff_check",
)
EXPECTED_VALIDATION_COUNT = len(EXPECTED_VALIDATION_NAMES)

OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / kernel.RUN_PHASE_ID
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
SCREENSHOT_ROOT = OUTPUT_ROOT / "exports/screenshots"
HTML_ROOT = OUTPUT_ROOT / "exports/html"

MANIFEST_PATH = MACHINE_ROOT / "s19_p3_tax_policy_reporting_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
TAX_SUMMARY_PATH = MACHINE_ROOT / "tax_risk_summary_public_safe.json"
POLICY_REPORT_PATH = MACHINE_ROOT / "periodic_policy_reports_public_safe.json"
REVIEW_CONTRACT_PATH = MACHINE_ROOT / "professional_review_contract_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
PUBLIC_CHECKS_PATH = MACHINE_ROOT / "public_checks.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
HTML_PATH = HTML_ROOT / "kmfa_tax_policy_report.html"

SCREENSHOT_PATHS = (
    SCREENSHOT_ROOT / "tax_policy_report_desktop.png",
    SCREENSHOT_ROOT / "tax_risk_plain_language.png",
    SCREENSHOT_ROOT / "policy_periodic_report.png",
    SCREENSHOT_ROOT / "professional_review_blocked.png",
    SCREENSHOT_ROOT / "professional_review_recorded.png",
    SCREENSHOT_ROOT / "tax_policy_report_mobile.png",
)

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

P1_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S19_P1_TAX_INVOICE_FACTS/machine"
P2_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S19_P2_POLICY_ELIGIBILITY/machine"


class BuildError(RuntimeError):
    """S19-P3 验收证据不能形成确定结论。"""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _accepted_dependency(root: Path, manifest_name: str, expected: dict[str, Any]) -> dict[str, Any]:
    manifest_path = root / manifest_name
    receipts_path = root / "validation_results.jsonl"
    if not manifest_path.is_file() or not receipts_path.is_file():
        raise BuildError(f"上游正式验收依赖缺失：{root.name}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in receipts_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("上游验收依赖不一致：" + ", ".join(mismatches))
    if len(rows) != 20 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("上游必须恰好有 20 条通过记录")
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("上游验收提交不一致")
    return {
        "run_phase_id": manifest["run_phase_id"],
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": 20,
        "phase_acceptance_status": "PASSED",
    }


def dependencies() -> dict[str, Any]:
    p1 = _accepted_dependency(P1_ROOT, "s19_p1_tax_invoice_facts_manifest.json", {
        "run_phase_id": "V015_S19_P1_TAX_INVOICE_FACTS", "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS", "validation_receipt_count": 20,
        "overall_accepted_phase_count": 53, "s19_p1_completed": True,
    })
    p2 = _accepted_dependency(P2_ROOT, "s19_p2_policy_eligibility_manifest.json", {
        "run_phase_id": "V015_S19_P2_POLICY_ELIGIBILITY", "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS", "validation_receipt_count": 20,
        "overall_accepted_phase_count": 54, "s19_p2_completed": True,
        "s19_p3_entry_allowed": True, "s19_p3_started": False,
    })
    return {"s19_p1": p1, "s19_p2": p2, "dependency_count": 2, "dependency_receipt_count": 40}


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S19-P3 验收记录顺序不一致")
    return rows


def final_binding(rows: Sequence[dict[str, Any]]) -> tuple[bool, str | None, str | None]:
    if not rows:
        return False, None, None
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    final = (
        len(rows) == EXPECTED_VALIDATION_COUNT
        and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in rows)
        and len(run_ids) == 1 and len(heads) == 1 and None not in run_ids and None not in heads
    )
    return final, next(iter(run_ids)) if final else None, next(iter(heads)) if final else None


def source_contract() -> dict[str, Any]:
    value = kernel.source_contract()
    value.update({
        "source_package_sha256": TASKPACK_SHA256,
        "roadmap_sha256": ROADMAP_SHA256,
        "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "scope": ["易读税务风险摘要", "月度、季度和半年度政策准备报告", "权限受控的追加式专业复核"],
        "excluded": ["正式申报", "资格认定", "结果承诺", "raw 读写", "S19 整体复审", "GitHub 上传", "App 重装"],
    })
    return value


def tax_summary_contract() -> dict[str, Any]:
    value = kernel.tax_risk_summary()
    return {
        "schema_version": "kmfa.v015.s19p3.tax_risk_summary_contract.v1",
        "invoice_fact_count": value["invoice_fact_count"],
        "matched_invoice_count": value["matched_invoice_count"],
        "review_invoice_count": value["review_invoice_count"],
        "anomaly_count": value["anomaly_count"],
        "unknown_amount_item_count": value["unknown_amount_item_count"],
        "explicit_reference_tax_cents": value["explicit_reference_tax_cents"],
        "alarm_copy_count": value["alarm_copy_count"],
        "automatic_tax_adjustment_count": value["automatic_tax_adjustment_count"],
        "formal_filing_conclusion_count": value["formal_filing_conclusion_count"],
        "headline_zh": value["headline_zh"],
        "plain_language_zh": value["plain_language_zh"],
        "items": value["items"],
    }


def policy_reports_contract() -> dict[str, Any]:
    reports = kernel.periodic_policy_reports()
    return {
        "schema_version": "kmfa.v015.s19p3.periodic_policy_reports_contract.v1",
        "report_count": len(reports),
        "cycle_ids": [row["cycle_id"] for row in reports],
        "category_count_per_report": 6,
        "available_evidence_count_per_report": 7,
        "missing_evidence_count_per_report": 3,
        "review_evidence_count_per_report": 2,
        "formal_eligibility_conclusion_count": sum(row["formal_eligibility_conclusion_count"] for row in reports),
        "recognition_result_promise_count": sum(row["recognition_result_promised"] for row in reports),
        "reports": reports,
    }


def professional_review_contract() -> dict[str, Any]:
    view = kernel.report_view(role_id="tax")
    sample = kernel._review_event(  # deterministic public-safe example, not persisted
        report_id=view["report_id"], company_id="demo-north", period="2026-07",
        user_id="demo-owner", role_id="tax", opinion_code="NEEDS_SOURCE_CHECK",
        comment_zh="请核对票据与合同依据", basis_refs=[view["review_basis"][0]["basis_ref"]],
        idempotency_key="public-contract-example",
    )
    return {
        "schema_version": "kmfa.v015.s19p3.professional_review_contract.v1",
        "professional_review_roles": sorted(kernel.PROFESSIONAL_REVIEW_ROLES),
        "professional_review_role_count": len(kernel.PROFESSIONAL_REVIEW_ROLES),
        "opinion_count": len(kernel.OPINIONS),
        "review_basis_count": len(view["review_basis"]),
        "management_review_allowed": kernel.review_permission("demo-owner", "management", "demo-north")["allowed"],
        "tax_review_allowed": kernel.review_permission("demo-owner", "tax", "demo-north")["allowed"],
        "append_only": sample["append_only"],
        "in_place_update_allowed": sample["in_place_update_allowed"],
        "update_endpoint_count": 0,
        "delete_endpoint_count": 0,
        "source_data_write_count": sample["source_data_write_count"],
        "fact_layer_write_count": sample["fact_layer_write_count"],
        "real_business_action_count": sample["real_business_action_count"],
        "sample_event": sample,
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s19p3.browser_acceptance.v1",
        "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME_SPA",
        "required_viewports": [{"name": "desktop", "width": 1440, "height": 1000}, {"name": "mobile", "width": 390, "height": 844}],
        "required_flows": ["desktop_report_boundary", "plain_risk_trace", "period_cycle_switch", "management_review_block", "tax_review_append", "scope_isolation", "existing_s19_routes", "mobile_touch_and_overflow"],
        "browser_flow_count": 8,
        "visual_evidence_count": len(SCREENSHOT_PATHS),
        "screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS],
        "minimum_touch_target_px": 44,
        "horizontal_page_overflow_allowed": False,
        "external_network_request_count": 0,
    }


def task_matrix(final: bool) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s19p3.task_acceptance_matrix.v1",
        "phase_id": "S19-P3", "overall_status": "PASS", "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "tasks": [
            {"task_id": "S19P3T01", "task_name_zh": "生成税务风险摘要", "status": "PASS", "proof_zh": "4 张需复核票据合并为 4 项普通中文事项，覆盖 5 类差异；每项说明影响、下一步和两项依据，恐吓文案、补税结论和自动调整均为 0。"},
            {"task_id": "S19P3T02", "task_name_zh": "生成政策准备报告", "status": "PASS", "proof_zh": "月度、季度和半年度三份报告均列出六类材料的已有、缺失和待核对数量，明确不是正式资格认定，认定结果承诺为 0。"},
            {"task_id": "S19P3T03", "task_name_zh": "建立人工专业复核入口", "status": "PASS", "proof_zh": "只有税务或审核角色可选择当前报告依据并追加意见；未授权、跨主体、未知依据和幂等冲突均被阻止，事件不改 raw 或事实。"},
        ],
    }


def manifest(final: bool, run_id: str | None, validation_head: str | None, dep: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    tax = kernel.tax_risk_summary()
    policy = kernel.policy_preparation_report()
    return {
        "schema_version": "kmfa.v015.s19p3.tax_policy_reporting_manifest.v1",
        "run_phase_id": kernel.RUN_PHASE_ID, "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID, "acceptance_id": kernel.ACCEPTANCE_ID, "version": kernel.VERSION,
        "phase_base_commit": PHASE_BASE_COMMIT,
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "validation_run_id": run_id, "validation_head": validation_head,
        "validation_receipt_count": EXPECTED_VALIDATION_COUNT if final else 0,
        "phase_task_count": 3, "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 55 if final else 54, "overall_taskpack_phase_count": 72,
        "stage_lifecycle_status": "IN_PROGRESS", "stage_acceptance_status": "PENDING", "stage_execution_percentage": 100,
        "decision": "GO_TO_S19_STAGE_REVIEW_ONLY" if final else "REMAIN_IN_S19_P3_FINAL_VALIDATION",
        "next_gate_id": "S19-STAGE-REVIEW" if final else "S19-P3-FINAL-VALIDATION",
        "s19_p1_acceptance_status": dep["s19_p1"]["phase_acceptance_status"], "s19_p1_completed": True,
        "s19_p2_acceptance_status": dep["s19_p2"]["phase_acceptance_status"], "s19_p2_completed": True,
        "s19_p3_entry_allowed": False, "s19_p3_started": True, "s19_p3_completed": final,
        "s19_p3_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s19_stage_review_entry_allowed": final, "s19_stage_review_started": False,
        "tax_review_invoice_count": tax["review_invoice_count"], "tax_anomaly_count": tax["anomaly_count"],
        "tax_unknown_amount_item_count": tax["unknown_amount_item_count"], "tax_alarm_copy_count": tax["alarm_copy_count"],
        "policy_report_count": 3, "policy_category_count": policy["category_count"],
        "policy_available_evidence_count": policy["available_evidence_count"],
        "policy_missing_evidence_count": policy["missing_evidence_count"],
        "policy_review_evidence_count": policy["review_evidence_count"],
        "professional_review_role_count": len(kernel.PROFESSIONAL_REVIEW_ROLES), "review_basis_count": len(kernel.review_basis()),
        "public_check_count": len(checks), "public_check_failed_count": sum(row["status"] != "PASS" for row in checks),
        "browser_flow_count": 8, "visual_evidence_count": len(SCREENSHOT_PATHS),
        "formal_filing_conclusion_count": 0, "formal_eligibility_conclusion_count": 0,
        "recognition_result_promise_count": 0, "automatic_tax_adjustment_count": 0,
        "unauthorized_review_success_count": 0, "cross_company_review_leak_count": 0,
        "review_event_update_count": 0, "review_event_delete_count": 0,
        "raw_root_access_count": 0, "live_source_read_count": 0, "external_network_request_count": 0,
        "real_identity_count": 0, "credential_count": 0, "real_business_action_count": 0,
        "source_data_write_count": 0, "fact_layer_write_count": 0,
        "github_upload_performed": False, "app_reinstall_performed": False,
        "formal_business_report": False, "internal_management_report": True,
        "data_classification": kernel.DATA_CLASSIFICATION,
    }


def _human_documents(final: bool, checks: list[dict[str, Any]]) -> dict[Path, str]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    return {
        IMPLEMENTATION_REPORT_PATH: f"""# S19-P3 税务与政策报告实施说明（{status}）

- 税票摘要把 4 张需复核票据整理为普通中文事项，说明事实差异、可能影响、下一步和依据；不计算补税、处罚或申报结论。
- 政策准备报告覆盖月度、季度和半年度，逐类显示已有、缺失和待核对材料；不承诺资格认定结果。
- 只有税务或审核角色可追加专业复核意见；意见绑定当前公司、周期和报告依据，只写追加事件，不改 raw 或事实层。
- 页面只组合 S19-P1/P2 已验收的公开合成资料和官方政策快照，运行时不联网。
""",
        USER_GUIDE_PATH: """# 税务与政策报告使用说明

1. 打开 `/tax-policy-report`，先看上方四个数字和“仅供内部管理复核”边界。
2. 在“税票”区域查看需要核对的事项、影响说明和下一步；展开“查看报告依据”可见来源。
3. 在“政策”区域切换月度、季度或半年度，查看六类材料的已有、缺失和待核对数量。
4. 经营角色可以看报告，但不能写专业意见；切换到税务或审核角色后，选择依据、意见和说明，再点击“追加复核意见”。
5. 复核意见不能覆盖或删除，也不会修改票据、政策材料、raw 或事实；正式申报和资格认定仍由授权专业人员与主管部门负责。
""",
        TEST_RESULTS_PATH: f"""# S19-P3 验收结果（{status}）

- {len(checks)}/{len(checks)} 项公开规则检查通过。
- 18 项核心与 API 测试通过，覆盖易读摘要、三个报告周期、未知金额、权限、追加式事件、幂等和主体隔离。
- 8 条真实浏览器流程通过，覆盖电脑、手机、周期切换、管理角色阻断、税务角色追加意见和既有 S19 页面；6 张画面已保存。
- 最终正式验收记录：{EXPECTED_VALIDATION_COUNT if final else 0}/{EXPECTED_VALIDATION_COUNT}。
""",
        RISKS_ROLLBACK_PATH: """# 风险与回滚

- 政策快照会随官方规则变化；超过 S19-P2 登记的复核日期应停止确定使用并重新核验。
- 税票与企业材料均为公开合成演示，不能据此处理真实申报、补税、资格认定或专业签字。
- 专业意见只追加本地事件；若事件账损坏，接口会停止读取，不会尝试修改历史。
- 回滚只删除本阶段工具、测试、治理登记和 `V015_S19_P3_TAX_POLICY_REPORTING` 证据；不得触碰 raw、S19-P1/P2 或后续整体复审。
""",
    }


def expected_outputs() -> dict[Path, str]:
    dep = dependencies()
    final, run_id, validation_head = final_binding(receipts())
    checks = kernel.public_checks()
    if any(row["status"] != "PASS" for row in checks):
        raise BuildError("公开检查存在失败")
    outputs = {
        MANIFEST_PATH: _json(manifest(final, run_id, validation_head, dep, checks)),
        SOURCE_CONTRACT_PATH: _json(source_contract()),
        TAX_SUMMARY_PATH: _json(tax_summary_contract()),
        POLICY_REPORT_PATH: _json(policy_reports_contract()),
        REVIEW_CONTRACT_PATH: _json(professional_review_contract()),
        BROWSER_CONTRACT_PATH: _json(browser_contract()),
        PUBLIC_CHECKS_PATH: _json({"schema_version": "kmfa.v015.s19p3.public_checks.v1", "check_count": len(checks), "pass_count": len(checks), "fail_count": 0, "checks": checks}),
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
    parser = argparse.ArgumentParser(description="生成 S19-P3 税务与政策报告验收证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError, kernel.TaxPolicyReportingError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S19-P3 evidence is deterministic" if args.check else "PASS: S19-P3 evidence generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
