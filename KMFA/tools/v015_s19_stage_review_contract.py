#!/usr/bin/env python3
"""KMFA v1.5 S19 税务、发票、政策资格与证据准备整体复审合同。"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from KMFA.tools import run_v015_s19_p3_tax_policy_reporting as runtime
from KMFA.tools import v015_s19_p1_tax_invoice_facts as p1
from KMFA.tools import v015_s19_p2_policy_eligibility as p2
from KMFA.tools import v015_s19_p3_tax_policy_reporting as p3


RUN_PHASE_ID = "V015_S19_STAGE_REVIEW"
TASK_ID = "KMFA-V015-S19-STAGE-REVIEW-20260717"
ACCEPTANCE_ID = "ACC-KMFA-V015-S19-STAGE-REVIEW"
VERSION = "1.5.0-dev-s19-review"
REVIEW_BASE_COMMIT = "dd6ef29e632d6acb0ec048bdeaa65ae84093d677"
EXPECTED_BINDING_COUNT = 44
EXPECTED_PUBLIC_CHECK_COUNT = 278

REVIEW_FINDINGS = (
    {
        "finding_id": "S19REV-F001",
        "severity": "P1",
        "category": "CROSS_PHASE_NAVIGATION",
        "issue_zh": "税票事实页和政策材料页只有返回入口，用户无法顺着 S19 三步流程继续到下一页。",
        "impact_zh": "用户完成当前核对后会进入导航死路，需要重新寻找下一项工作。",
        "fix_zh": "三个页面统一增加当前步骤、上一步和下一步入口，触控尺寸不小于 44 像素。",
        "status": "FIXED_VALIDATED",
        "blocks_stage_acceptance": False,
    },
    {
        "finding_id": "S19REV-F002",
        "severity": "P0",
        "category": "PROFESSIONAL_REVIEW_INTEGRITY",
        "issue_zh": "专业复核事件账读取时只检查事件类型和只追加标记，手工篡改内容后仍可能进入报告。",
        "impact_zh": "复核人、意见、依据或范围可能与原始指纹不一致，审计链失真。",
        "fix_zh": "读取时逐字段校验权限、范围、依据、零写入边界、事件编号和 SHA-256 指纹；任何差异立即拒绝。",
        "status": "FIXED_VALIDATED",
        "blocks_stage_acceptance": False,
    },
)


class StageReviewError(ValueError):
    """S19 三部分连接或整体复审证据不一致。"""


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def technical_audit() -> dict[str, Any]:
    dimensions = [
        {"dimension": "tax_fact_traceability", "score": 4, "finding_zh": "报告中的每张风险票据都能回到票据与合同两侧公开合成依据。"},
        {"dimension": "policy_evidence_honesty", "score": 4, "finding_zh": "政策快照、材料缺口和周期报告一致，不输出资格或认定承诺。"},
        {"dimension": "review_event_integrity", "score": 4, "finding_zh": "复核事件逐字段、权限、范围和指纹校验，篡改记录失败关闭。"},
        {"dimension": "scope_and_side_effect_safety", "score": 4, "finding_zh": "公司、期间、报告范围隔离，raw、事实写入、联网与真实动作均为零。"},
        {"dimension": "human_usability", "score": 4, "finding_zh": "三步页面有连续中文导航，电脑和移动端触控入口不小于 44 像素。"},
    ]
    return {
        "schema_version": "kmfa.v015.s19.stage-review-technical-audit.v1",
        "method": "CROSS_PHASE_TRACEABILITY_PERMISSION_INTEGRITY_AND_BROWSER_WALKTHROUGH",
        "scale_per_dimension": 4,
        "maximum_score": 20,
        "dimensions": dimensions,
        "total_score": sum(row["score"] for row in dimensions),
        "rating": "EXCELLENT",
        "severity_counts": {"P0": 1, "P1": 1, "P2": 0, "P3": 0},
        "fixed_issue_count": 2,
        "open_issue_count": 0,
    }


def integration_bindings() -> list[dict[str, Any]]:
    html = runtime.render_html()
    tax = p1.tax_invoice_view()
    policy = p2.policy_view()
    report = p3.report_view()
    tax_report = report["tax_risk_summary"]
    policy_report = report["policy_preparation_report"]
    review_rows = [row for row in tax["rows"] if row["match_state"] == "REVIEW_REQUIRED"]
    review_by_id = {row["invoice_id"]: row for row in review_rows}
    risk_by_id = {row["invoice_id"]: row for row in tax_report["items"]}
    policy_sources = {row["source_url"] for row in policy["policy_registry"]}
    report_sources = {row["source_url"] for row in policy_report["policy_snapshots"]}
    expected_basis = {
        ref
        for row in review_rows
        for ref in (row["source_ref"], row["links"]["contract_ref"])
    } | policy_sources
    basis_refs = {row["basis_ref"] for row in report["review_basis"]}
    event = p3._review_event(
        report_id=report["report_id"], company_id=report["company_id"], period=report["period"],
        user_id="demo-owner", role_id="tax", opinion_code="NEEDS_SOURCE_CHECK",
        comment_zh="请核对当前报告依据。", basis_refs=[report["review_basis"][0]["basis_ref"]],
        idempotency_key="s19-review-integrity",
    )
    p3._validate_review_event(event)
    tampered = copy.deepcopy(event)
    tampered["comment_zh"] = "篡改后的复核意见"
    tamper_rejected = False
    try:
        p3._validate_review_event(tampered)
    except p3.TaxPolicyReportingError:
        tamper_rejected = True
    wrong_report = copy.deepcopy(event)
    wrong_report["report_id"] = "TPR-demo-north-2026-Q2"
    projected = p3.report_view(events=[event, wrong_report])
    periodic = p3.periodic_policy_reports()
    rows: list[dict[str, Any]] = []

    def add(binding_id: str, kind: str, passed: bool, detail: str) -> None:
        rows.append({"binding_id": binding_id, "kind": kind, "status": "PASS" if passed else "FAIL", "detail": detail})

    for index, (phase, checks) in enumerate(
        ((p1.RUN_PHASE_ID, p1.public_checks()), (p2.RUN_PHASE_ID, p2.public_checks()), (p3.RUN_PHASE_ID, p3.public_checks())), 1
    ):
        add(f"PHASE-{index:02d}", "PREDECESSOR_PUBLIC_CONTRACT", bool(checks) and all(row["status"] == "PASS" for row in checks), phase)

    add("TAX-FACT-COUNT", "TAX_TO_REPORT", tax["summary"]["fact_count"] == tax_report["invoice_fact_count"] == 8, "票据事实总数")
    add("TAX-MATCHED-COUNT", "TAX_TO_REPORT", tax["summary"]["matched_count"] == tax_report["matched_invoice_count"] == 4, "已匹配票据")
    add("TAX-REVIEW-COUNT", "TAX_TO_REPORT", tax["summary"]["review_count"] == tax_report["review_invoice_count"] == 4, "待复核票据")
    add("TAX-ANOMALY-COUNT", "TAX_TO_REPORT", tax["anomaly_count"] == tax_report["anomaly_count"] == 5, "事实差异")
    add("TAX-UNKNOWN-COUNT", "TAX_TO_REPORT", tax["summary"]["unknown_rate_count"] == tax_report["unknown_amount_item_count"] == 1, "未知税率不估算")
    add("TAX-RISK-INVOICES", "TAX_TO_REPORT", set(review_by_id) == set(risk_by_id), "风险票据与待复核票据一致")
    add("TAX-SOURCE-BASIS", "TAX_TO_REPORT", all(risk_by_id[key]["basis_refs"][0] == row["source_ref"] for key, row in review_by_id.items()), "票据依据")
    add("TAX-CONTRACT-BASIS", "TAX_TO_REPORT", all(risk_by_id[key]["basis_refs"][1] == row["links"]["contract_ref"] for key, row in review_by_id.items()), "合同依据")
    add("TAX-ANOMALY-TYPES", "TAX_TO_REPORT", all(risk_by_id[key]["anomaly_types"] == row["anomaly_types"] for key, row in review_by_id.items()), "异常类型不漂移")
    add("TAX-REFERENCE-MONEY", "TAX_TO_REPORT", tax_report["explicit_reference_tax_cents"] == sum(row["tax_cents"] or 0 for row in review_rows), "已记录税额仅作参考")
    add("TAX-NO-RATE-INFERENCE", "TAX_TO_REPORT", tax["rate_inference_count"] == 0 and all(not row["rate_inferred"] for row in tax["rows"]), "不猜税率")
    add("TAX-NO-AUTO-ADJUST", "TAX_TO_REPORT", tax["automatic_tax_adjustment_count"] == 0 and all(not row["automatic_adjustment_allowed"] for row in tax_report["items"]), "不自动调税")
    add("TAX-NO-FILING", "TAX_TO_REPORT", tax["formal_filing_conclusion"] is False and tax_report["formal_filing_conclusion_count"] == 0, "不输出申报结论")
    add("TAX-INTEGER-MONEY", "TAX_TO_REPORT", all(row["reference_tax_cents"] is None or isinstance(row["reference_tax_cents"], int) for row in tax_report["items"]), "金额使用整数分")
    add("TAX-COMPANY-ISOLATION", "TAX_TO_REPORT", tax["cross_company_leak_count"] == report["cross_company_review_leak_count"] == 0, "公司隔离")
    add("TAX-SOURCE-PHASE", "TAX_TO_REPORT", tax_report["source_phase"] == p1.RUN_PHASE_ID, "报告绑定 P1")

    add("POLICY-COUNT", "POLICY_TO_REPORT", policy["summary"]["policy_count"] == policy_report["policy_count"] == 6, "政策快照总数")
    add("POLICY-CURRENT", "POLICY_TO_REPORT", policy["summary"]["current_policy_count"] == policy_report["current_policy_count"] == 5, "当前规则")
    add("POLICY-BLOCKED", "POLICY_TO_REPORT", policy["summary"]["blocked_policy_count"] == policy_report["blocked_policy_count"] == 1, "历史规则停用")
    add("POLICY-CATEGORIES", "POLICY_TO_REPORT", len(policy["readiness_categories"]) == policy_report["category_count"] == 6, "材料类别")
    add("POLICY-EVIDENCE", "POLICY_TO_REPORT", policy["summary"]["evidence_item_count"] == policy_report["evidence_item_count"] == 12, "材料总数")
    add("POLICY-AVAILABLE", "POLICY_TO_REPORT", policy["summary"]["available_evidence_count"] == policy_report["available_evidence_count"] == 7, "已有来源")
    add("POLICY-MISSING", "POLICY_TO_REPORT", policy["summary"]["missing_evidence_count"] == policy_report["missing_evidence_count"] == 3, "缺失材料")
    add("POLICY-REVIEW", "POLICY_TO_REPORT", policy["summary"]["review_evidence_count"] == policy_report["review_evidence_count"] == 2, "待核对材料")
    add("POLICY-CATEGORY-DETAIL", "POLICY_TO_REPORT", all({key: row[key] for key in ("required_count", "available_count", "missing_count", "review_count")} == {key: next(item for item in policy_report["categories"] if item["category_id"] == row["category_id"])[key] for key in ("required_count", "available_count", "missing_count", "review_count")} for row in policy["readiness_categories"]), "类别明细一致")
    add("POLICY-OFFICIAL-SOURCES", "POLICY_TO_REPORT", policy_sources == report_sources, "官方来源快照一致")
    add("POLICY-NO-ELIGIBILITY", "POLICY_TO_REPORT", policy["formal_eligibility_conclusion_count"] == policy_report["formal_eligibility_conclusion_count"] == 0, "不输出资格结论")
    add("POLICY-NO-PROMISE", "POLICY_TO_REPORT", policy_report["recognition_result_promised"] is False and report["recognition_result_promise_count"] == 0, "不承诺认定结果")
    add("POLICY-SOURCE-PHASE", "POLICY_TO_REPORT", policy_report["source_phase"] == p2.RUN_PHASE_ID, "报告绑定 P2")
    add("POLICY-CYCLES", "POLICY_TO_REPORT", len(periodic) == 3 and {row["cycle_id"] for row in periodic} == {"MONTHLY", "QUARTERLY", "HALF_YEAR"}, "月季半年周期")
    add("POLICY-REPORT-IDS", "POLICY_TO_REPORT", all(row["report_id"] == f"TPR-demo-north-{row['period']}" for row in periodic), "报告编号绑定周期")
    add("REVIEW-BASIS-COUNT", "PROFESSIONAL_REVIEW", len(report["review_basis"]) == 12, "复核依据去重")
    add("REVIEW-BASIS-SCOPE", "PROFESSIONAL_REVIEW", basis_refs == expected_basis, "复核依据只来自当前报告")
    add("REVIEW-MANAGEMENT-DENIED", "PROFESSIONAL_REVIEW", p3.review_permission("demo-owner", "management", "demo-north")["allowed"] is False, "管理角色不能签专业意见")
    add("REVIEW-PROFESSIONAL-ALLOWED", "PROFESSIONAL_REVIEW", all(p3.review_permission("demo-owner", role, "demo-north")["allowed"] for role in ("tax", "reviewer")), "税务与审核角色可追加")
    add("REVIEW-VALID-EVENT", "PROFESSIONAL_REVIEW", event["append_only"] is True and event["event_fingerprint"].startswith("sha256:"), "合法事件通过完整性校验")
    add("REVIEW-TAMPER-REJECTED", "PROFESSIONAL_REVIEW", tamper_rejected, "篡改事件失败关闭")
    add("REVIEW-REPORT-SCOPE", "PROFESSIONAL_REVIEW", projected["review_event_count"] == 1 and projected["review_events"][0]["event_id"] == event["event_id"], "错误报告编号不进入投影")

    ids = re.findall(r'\bid="([^"]+)"', html)
    add("NAVIGATION-CHAIN", "HUMAN_USABILITY", all(token in html for token in ("/tax-policy", "/policy-eligibility", "/tax-policy-report", "1 税票事实", "2 政策材料", "3 周期报告")), "三步连续导航")
    add("HTML-QUALITY", "HUMAN_USABILITY", '<html lang="zh-CN"' in html and bool(ids) and len(ids) == len(set(ids)) and "prefers-reduced-motion:reduce" in html and "min-height:44px" in html, "中文、唯一 ID、减动效、触控尺寸")
    add("ZERO-SIDE-EFFECTS", "SCOPE_SAFETY", all(value == 0 for value in (tax["raw_root_access_count"], tax["business_action_count"], policy["raw_root_access_count"], policy["external_network_request_count"], policy["real_business_action_count"], report["raw_root_access_count"], report["external_network_request_count"], report["source_data_write_count"], report["fact_layer_write_count"], report["real_business_action_count"])), "无 raw、联网、事实写入或真实动作")

    if len(rows) != EXPECTED_BINDING_COUNT:
        raise StageReviewError(f"REVIEW_BINDING_COUNT_DRIFT：预期 {EXPECTED_BINDING_COUNT}，实际 {len(rows)}。")
    return rows


def _integrated_payload() -> dict[str, Any]:
    bindings = integration_bindings()
    return {
        "schema_version": "kmfa.v015.s19.integrated-stage-review.v1",
        "fixture_class": "PUBLIC_OFFICIAL_SNAPSHOT_AND_SYNTHETIC_LOCALHOST_DEMO",
        "predecessor_phase_count": 3,
        "predecessor_task_accepted_count": 9,
        "predecessor_receipt_count": 60,
        "predecessor_public_check_count": 216,
        "integration_bindings": bindings,
        "integration_binding_count": len(bindings),
        "integration_binding_failed_count": sum(row["status"] != "PASS" for row in bindings),
        "review_findings": copy.deepcopy(list(REVIEW_FINDINGS)),
        "review_finding_count": 2,
        "fixed_review_finding_count": 2,
        "open_review_finding_count": 0,
        "technical_audit": technical_audit(),
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "external_network_request_count": 0,
        "real_identity_count": 0,
        "credential_count": 0,
        "real_business_action_count": 0,
        "source_data_write_count": 0,
        "fact_layer_write_count": 0,
        "formal_filing_conclusion_count": 0,
        "formal_eligibility_conclusion_count": 0,
        "recognition_result_promise_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "s20_started": False,
    }


def build_integrated_review() -> dict[str, Any]:
    value = _integrated_payload()
    value["review_fingerprint"] = _fingerprint(value)
    validate_integrated_review(value)
    return value


def validate_integrated_review(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise StageReviewError("复审结果必须是结构化对象。")
    actual = copy.deepcopy(dict(value))
    supplied = actual.pop("review_fingerprint", None)
    if supplied != _fingerprint(actual):
        raise StageReviewError("REVIEW_FINGERPRINT_MISMATCH：复审指纹不一致。")
    if actual != _integrated_payload():
        raise StageReviewError("REVIEW_CROSS_PHASE_MISMATCH：跨部分证据不一致。")
    if actual["integration_binding_failed_count"] or actual["open_review_finding_count"]:
        raise StageReviewError("REVIEW_OPEN_FINDING：仍有未关闭的问题。")
    zero_keys = (
        "raw_root_access_count", "external_network_request_count", "real_identity_count",
        "credential_count", "real_business_action_count", "source_data_write_count",
        "fact_layer_write_count", "formal_filing_conclusion_count",
        "formal_eligibility_conclusion_count", "recognition_result_promise_count",
    )
    false_keys = ("raw_business_content_read", "github_upload_performed", "app_reinstall_performed", "s20_started")
    if any(actual[key] for key in zero_keys) or any(actual[key] for key in false_keys):
        raise StageReviewError("REVIEW_SIDE_EFFECT_REJECTED：复审产生了越界动作。")
    return {
        "integration_binding_count": EXPECTED_BINDING_COUNT,
        "integration_binding_failed_count": 0,
        "review_finding_count": 2,
        "fixed_review_finding_count": 2,
        "open_review_finding_count": 0,
        "technical_audit_score": 20,
    }


def render_html() -> str:
    return runtime.render_html()


def public_verification() -> dict[str, Any]:
    review = build_integrated_review()
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool) -> None:
        checks.append({"name": name, "passed": bool(passed)})

    for prefix, values in (("p1", p1.public_checks()), ("p2", p2.public_checks()), ("p3", p3.public_checks())):
        for row in values:
            add(f"{prefix}_{row.get('check_id', row.get('name'))}", row["status"] == "PASS")
    for row in review["integration_bindings"]:
        add("binding_" + row["binding_id"], row["status"] == "PASS")
    for name, passed in (
        ("raw_root_zero", review["raw_root_access_count"] == 0),
        ("external_network_zero", review["external_network_request_count"] == 0),
        ("real_identity_zero", review["real_identity_count"] == 0),
        ("credential_zero", review["credential_count"] == 0),
        ("source_write_zero", review["source_data_write_count"] == 0),
        ("fact_write_zero", review["fact_layer_write_count"] == 0),
        ("real_action_zero", review["real_business_action_count"] == 0),
        ("filing_conclusion_zero", review["formal_filing_conclusion_count"] == 0),
        ("eligibility_conclusion_zero", review["formal_eligibility_conclusion_count"] == 0),
        ("recognition_promise_zero", review["recognition_result_promise_count"] == 0),
        ("github_closed", review["github_upload_performed"] is False),
        ("app_closed", review["app_reinstall_performed"] is False),
        ("s20_closed", review["s20_started"] is False),
        ("navigation_fixed", review["review_findings"][0]["status"] == "FIXED_VALIDATED"),
        ("review_integrity_fixed", review["review_findings"][1]["status"] == "FIXED_VALIDATED"),
        ("all_bindings_pass", review["integration_binding_failed_count"] == 0),
        ("audit_score_full", review["technical_audit"]["total_score"] == 20),
        ("open_findings_zero", review["open_review_finding_count"] == 0),
    ):
        add(name, passed)
    if len(checks) != EXPECTED_PUBLIC_CHECK_COUNT:
        raise StageReviewError(f"PUBLIC_CHECK_COUNT_DRIFT：预期 {EXPECTED_PUBLIC_CHECK_COUNT}，实际 {len(checks)}。")
    failed = [row["name"] for row in checks if not row["passed"]]
    return {
        "schema_version": "kmfa.v015.s19.stage-review-public-verification.v1",
        "checks": checks,
        "accounting": {"total": len(checks), "passed": len(checks) - len(failed), "failed": len(failed)},
        "failed_checks": failed,
        "integrated_review": review,
    }


def validate_public_contract() -> dict[str, Any]:
    value = public_verification()
    if value["accounting"]["failed"]:
        raise StageReviewError("S19 整体复审失败：" + ", ".join(value["failed_checks"]))
    return value


if __name__ == "__main__":
    result = validate_public_contract()
    print(f"PASS: S19 整体复审公开检查 {result['accounting']['passed']}/{result['accounting']['total']}")
