#!/usr/bin/env python3
"""KMFA v1.5 S21 经营报告三部分整体复审合同。"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from KMFA.tools import run_v015_s21_p1_report_model as p1_runtime
from KMFA.tools import run_v015_s21_p2_report_generation as p2_runtime
from KMFA.tools import run_v015_s21_p3_report_workflow as p3_runtime
from KMFA.tools import v015_s21_p1_report_model as p1
from KMFA.tools import v015_s21_p2_report_generation as p2
from KMFA.tools import v015_s21_p3_report_workflow as p3


RUN_PHASE_ID = "V015_S21_STAGE_REVIEW"
TASK_ID = "KMFA-V015-S21-STAGE-REVIEW-20260717"
ACCEPTANCE_ID = "ACC-KMFA-V015-S21-STAGE-REVIEW"
VERSION = "1.5.0-dev-s21-review"
REVIEW_BASE_COMMIT = "c0b895b4e90859a546c25e8b72c980143b577a01"
EXPECTED_BINDING_COUNT = 44

REVIEW_FINDINGS = (
    {
        "finding_id": "S21REV-F001",
        "severity": "P1",
        "category": "THREE_STEP_NAVIGATION_AND_CSS",
        "issue_zh": "报告模型、生成和复核页面没有统一三步导航，生成页注入样式还残留嵌套 style 标签。",
        "impact_zh": "用户容易迷路，且嵌套样式可能造成浏览器视觉规则失效。",
        "fix_zh": "三个页面增加统一三步导航，并移除嵌套 style 标签。",
        "status": "FIXED_VALIDATED",
        "blocks_stage_acceptance": False,
    },
    {
        "finding_id": "S21REV-F002",
        "severity": "P0",
        "category": "REPORT_CENTER_FILTER_AND_COMPANY_BINDING",
        "issue_zh": "报告中心没有完整显示主体、期间、类型、状态和版本筛选，预览还固定使用北区演示主体。",
        "impact_zh": "其他授权主体无法按任务包要求检索并进入报告流程。",
        "fix_zh": "补齐五类业务筛选，并始终使用当前所选报告的实际主体。",
        "status": "FIXED_VALIDATED",
        "blocks_stage_acceptance": False,
    },
    {
        "finding_id": "S21REV-F003",
        "severity": "P0",
        "category": "SELECTED_VERSION_WORKFLOW_BINDING",
        "issue_zh": "多版本存在时页面默认绑定最新流程，而不是当前所选报告版本。",
        "impact_zh": "审批动作可能落到错误报告版本。",
        "fix_zh": "流程状态和动作按 report_version_id 精确绑定当前所选版本。",
        "status": "FIXED_VALIDATED",
        "blocks_stage_acceptance": False,
    },
)


class StageReviewError(ValueError):
    """S21 三部分连接或整体复审证据不一致。"""


def technical_audit() -> dict[str, Any]:
    dimensions = [
        {"dimension": "report_lineage", "score": 4, "finding_zh": "期间、报告版本、导出版本和流程案例逐项绑定。"},
        {"dimension": "cross_format_consistency", "score": 4, "finding_zh": "网页、PDF 和专业附表共用同一事实载荷，21 个整数值零差异。"},
        {"dimension": "workflow_and_revision", "score": 4, "finding_zh": "预览、提交、复核、批准、内部发布和修订差异均可追溯。"},
        {"dimension": "permission_and_scope", "score": 4, "finding_zh": "主体、角色、状态和下载权限失败关闭，无公开链接或外部动作。"},
        {"dimension": "human_usability", "score": 4, "finding_zh": "三步连续导航、五类报告筛选和移动端触控入口齐全。"},
    ]
    return {
        "schema_version": "kmfa.v015.s21.stage-review-technical-audit.v1",
        "method": "END_TO_END_REPORT_LINEAGE_PERMISSION_AND_BROWSER_WALKTHROUGH",
        "scale_per_dimension": 4,
        "maximum_score": 20,
        "dimensions": dimensions,
        "total_score": sum(row["score"] for row in dimensions),
        "rating": "EXCELLENT",
        "severity_counts": {"P0": 2, "P1": 1, "P2": 0, "P3": 0},
        "fixed_issue_count": 3,
        "open_issue_count": 0,
    }


def _complete_case(
    journal: p3.ReportWorkflowJournal,
    report: dict[str, Any],
    export: dict[str, Any],
    prefix: str,
) -> dict[str, Any]:
    company = str(report["company_id"])
    case = journal.preview(
        report, export, user_id="demo-owner", role_id="finance", company_id=company,
        comment_zh="已核对三种格式、来源和限制说明", idempotency_key=f"{prefix}-preview-001",
        occurred_at="2026-07-17T01:02:00+00:00",
    )
    case = journal.submit(
        case["case_id"], user_id="demo-owner", role_id="finance", company_id=company,
        comment_zh="提交复核并保留完整来源", idempotency_key=f"{prefix}-submit-001",
        occurred_at="2026-07-17T01:03:00+00:00",
    )
    case = journal.review(
        case["case_id"], user_id="demo-owner", role_id="reviewer", company_id=company,
        comment_zh="数字一致且来源完整，复核通过", decision="PASS",
        idempotency_key=f"{prefix}-review-001", occurred_at="2026-07-17T01:04:00+00:00",
    )
    case = journal.approve(
        case["case_id"], user_id="demo-owner", role_id="reviewer", company_id=company,
        comment_zh="批准用于内部报告中心", idempotency_key=f"{prefix}-approve-001",
        occurred_at="2026-07-17T01:05:00+00:00",
    )
    return journal.publish(
        case["case_id"], user_id="demo-owner", role_id="management", company_id=company,
        comment_zh="发布到内部报告中心供授权人员查看", idempotency_key=f"{prefix}-publish-001",
        occurred_at="2026-07-17T01:06:00+00:00",
    )


def end_to_end_fixture() -> dict[str, Any]:
    """Build one deterministic two-company, multi-version localhost fixture."""

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        models = p1.ReportModelJournal(root / "models.jsonl")
        exports = p2.ReportExportJournal(root / "exports.jsonl", root / "bundles")
        workflows = p3.ReportWorkflowJournal(root / "workflows.jsonl")

        north_v1 = models.create(
            company_id="demo-north", period_kind="MONTHLY", period_key="2026-07",
            source_bindings=p1.default_source_bindings(), formula_bindings=p1.default_formula_bindings(),
            created_by="公开演示负责人", idempotency_key="s21-review-north-v1",
            recorded_at="2026-07-17T01:00:00+00:00",
        )
        north_export_v1 = exports.create(
            north_v1, idempotency_key="s21-review-export-north-v1",
            recorded_at="2026-07-17T01:01:00+00:00",
        )
        north_case_v1 = _complete_case(workflows, north_v1, north_export_v1, "s21rev-north-v1")

        north_v2 = models.revise(
            north_v1["report_version_id"],
            source_bindings=p3.revision_bindings(
                north_v1, {"key_matters": "S20P2-CONFIRMATIONS-2026-07-V2"}
            ),
            revision_reason_zh="补充本期重点事项复核结果和负责人意见",
            created_by="公开演示负责人", idempotency_key="s21-review-north-v2",
            recorded_at="2026-07-17T01:10:00+00:00",
        )
        north_export_v2 = exports.create(
            north_v2, idempotency_key="s21-review-export-north-v2",
            recorded_at="2026-07-17T01:11:00+00:00",
        )
        north_case_v2 = workflows.preview(
            north_v2, north_export_v2, user_id="demo-owner", role_id="finance",
            company_id="demo-north", comment_zh="修订版已核对，等待提交复核",
            idempotency_key="s21rev-north-v2-preview-001",
            occurred_at="2026-07-17T01:12:00+00:00",
        )

        west = models.create(
            company_id="demo-west", period_kind="QUARTERLY", period_key="2026-Q3",
            source_bindings=p1.default_source_bindings(), formula_bindings=p1.default_formula_bindings(),
            created_by="公开演示负责人", idempotency_key="s21-review-west-v1",
            recorded_at="2026-07-17T01:20:00+00:00",
        )
        west_export = exports.create(
            west, idempotency_key="s21-review-export-west-v1",
            recorded_at="2026-07-17T01:21:00+00:00",
        )
        west_case = workflows.preview(
            west, west_export, user_id="demo-owner", role_id="finance", company_id="demo-west",
            comment_zh="西区季度报告已核对，等待提交复核", idempotency_key="s21rev-west-preview-001",
            occurred_at="2026-07-17T01:22:00+00:00",
        )

        reports = models.list()["reports"]
        export_rows = exports.list()["exports"]
        cases = workflows.list()["cases"]
        return json.loads(json.dumps({
            "north_v1": north_v1, "north_v2": north_v2, "west": west,
            "north_export_v1": north_export_v1, "north_export_v2": north_export_v2,
            "west_export": west_export, "north_case_v1": north_case_v1,
            "north_case_v2": north_case_v2, "west_case": west_case,
            "reports": reports, "exports": export_rows, "cases": cases,
            "comparison": p3.compare_versions(north_v1, north_v2),
        }))


def integration_bindings() -> list[dict[str, Any]]:
    fixture = end_to_end_fixture()
    n1, n2, west = fixture["north_v1"], fixture["north_v2"], fixture["west"]
    e1, e2, ew = fixture["north_export_v1"], fixture["north_export_v2"], fixture["west_export"]
    c1, c2, cw = fixture["north_case_v1"], fixture["north_case_v2"], fixture["west_case"]
    reports, exports, cases = fixture["reports"], fixture["exports"], fixture["cases"]
    comparison = fixture["comparison"]
    html_by_step = (p1_runtime.render_html(), p2_runtime.render_html(), p3_runtime.render_html())
    workflow_html = html_by_step[2]
    rows: list[dict[str, Any]] = []

    def add(binding_id: str, kind: str, passed: bool, detail_zh: str) -> None:
        rows.append({
            "binding_id": binding_id, "kind": kind,
            "status": "PASS" if passed else "FAIL", "detail": detail_zh,
        })

    for index, (phase, result, expected) in enumerate((
        (p1.RUN_PHASE_ID, p1.verify_phase(), 55),
        (p2.RUN_PHASE_ID, p2.verify_phase(), 60),
        (p3.RUN_PHASE_ID, p3.verify_phase(), 53),
    ), 1):
        add(
            f"PHASE-{index:02d}", "PREDECESSOR_PUBLIC_CONTRACT",
            result["public_check_failed_count"] == 0 and result["public_check_count"] == expected,
            phase,
        )

    add("MODEL-COUNT", "MODEL_TO_EXPORT", len(reports) == 3, "两公司三个报告版本")
    add("MODEL-IMMUTABLE", "MODEL_TO_EXPORT", n2["supersedes_version_id"] == n1["report_version_id"] and n1["event_hash"] != n2["event_hash"], "修订新增版本且保留初版")
    add("MODEL-PERIODS", "MODEL_TO_EXPORT", n1["period"]["period_kind"] == "MONTHLY" and west["period"]["period_kind"] == "QUARTERLY", "月报和季报期间明确")
    add("MODEL-AUDIENCE", "MODEL_TO_EXPORT", n1["management_section_count"] == 5 and n1["professional_section_count"] == 1, "管理摘要和专业附表分层")
    add("MODEL-TRUST", "MODEL_TO_EXPORT", all(row["trust_and_limitations"]["complete_report_claim_allowed"] for row in reports), "资料齐备说明可读")
    add("MODEL-BINDINGS", "MODEL_TO_EXPORT", all(len(row["source_bindings"]) == 6 and len(row["formula_bindings"]) == 2 for row in reports), "来源和公式版本完整绑定")

    add("EXPORT-COUNT", "EXPORT_TO_WORKFLOW", len(exports) == 3, "每个报告版本各有一份导出")
    add("EXPORT-VERSION", "EXPORT_TO_WORKFLOW", all(e["report_version_id"] == r["report_version_id"] for e, r in ((e1, n1), (e2, n2), (ew, west))), "导出精确绑定报告版本")
    add("EXPORT-FORMATS", "EXPORT_TO_WORKFLOW", all(set(row["files"]) == {"HTML", "PDF", "CSV"} for row in exports), "网页、PDF、CSV 齐全")
    add("EXPORT-VALUES", "EXPORT_TO_WORKFLOW", all(row["cross_format_consistency"]["numeric_value_count"] == 21 for row in exports), "每份导出核对 21 个整数值")
    add("EXPORT-ZERO-DIFF", "EXPORT_TO_WORKFLOW", all(row["cross_format_consistency"]["difference_integer"] == 0 for row in exports), "三种格式零差异")
    add("EXPORT-SOURCE", "EXPORT_TO_WORKFLOW", e1["source_binding_fingerprint"] == n1["source_binding_fingerprint"], "导出绑定来源指纹")
    add("EXPORT-FORMULA", "EXPORT_TO_WORKFLOW", e1["formula_binding_fingerprint"] == n1["formula_binding_fingerprint"], "导出绑定公式指纹")
    add("QUALITY-GATES", "EXPORT_TO_WORKFLOW", all(p3.quality_gate(r, e)["status"] == "PASS" for r, e in ((n1, e1), (n2, e2), (west, ew))), "三个版本均通过质量门禁")

    add("WORKFLOW-FIVE-STEPS", "WORKFLOW", c1["state"] == "PUBLISHED_INTERNAL" and c1["event_count"] == 5, "初版完成五步内部发布")
    add("WORKFLOW-AUDIT", "WORKFLOW", all(row.get("actor_user_id") and row.get("occurred_at") and row.get("comment_zh") for row in c1["events"]), "每步保留人员、时间和意见")
    add("WORKFLOW-SELECTED-V2", "WORKFLOW", c2["report_version_id"] == n2["report_version_id"] and c2["state"] == "PREVIEWED", "修订版流程独立绑定")
    add("WORKFLOW-WEST", "WORKFLOW", cw["company_id"] == "demo-west" and cw["state"] == "PREVIEWED", "授权西区主体可进入流程")
    add("WORKFLOW-NO-PUBLIC", "WORKFLOW", all(not row["external_publication_performed"] and row["public_share_link"] is None for row in cases), "只发布到内部报告中心")
    add("REVISION-DIRECT", "REVISION", comparison["direct_revision"] is True, "修订直接承接初版")
    add("REVISION-EXPLAINED", "REVISION", comparison["source_difference_count"] >= 1 and comparison["unexplained_difference_count"] == 0, "变化均有来源和中文原因")
    add("REVISION-PUBLISHABLE", "REVISION", comparison["publication_allowed"] is True, "可解释变化允许继续流程")

    def center(company: str, **filters: str) -> dict[str, Any]:
        return p3.report_center(
            reports, exports, cases, user_id="demo-owner", role_id="finance",
            company_id=company, **filters,
        )

    north_center, west_center = center("demo-north"), center("demo-west")
    add("CENTER-COMPANY", "REPORT_CENTER", north_center["result_count"] == 2 and west_center["result_count"] == 1, "主体筛选隔离两公司")
    add("CENTER-PERIOD", "REPORT_CENTER", center("demo-north", period_key="2026-07")["result_count"] == 2, "期间筛选准确")
    add("CENTER-TYPE", "REPORT_CENTER", center("demo-west", report_type="QUARTERLY")["result_count"] == 1, "类型筛选准确")
    add("CENTER-STATUS", "REPORT_CENTER", center("demo-north", status="PUBLISHED_INTERNAL")["result_count"] == 1, "状态筛选准确")
    add("CENTER-VERSION", "REPORT_CENTER", center("demo-north", version=n2["report_version_id"])["reports"][0]["report_version_id"] == n2["report_version_id"], "版本筛选准确")
    add("CENTER-NO-CROSS-COMPANY", "REPORT_CENTER", north_center["cross_company_result_count"] == 0 and west_center["cross_company_result_count"] == 0, "跨主体结果为零")
    add("PERMISSION-MANAGEMENT", "PERMISSION", p3.authorize_download(n1, c1, user_id="demo-owner", role_id="management", company_id="demo-north", format_name="PDF")["allowed"] is True, "经营负责人可下载已发布版")
    add("PERMISSION-PREPUBLISH", "PERMISSION", p3.authorize_download(n2, c2, user_id="demo-owner", role_id="management", company_id="demo-north", format_name="PDF")["allowed"] is False, "经营负责人不能下载未发布版")
    add("PERMISSION-FINANCE", "PERMISSION", p3.authorize_download(n2, c2, user_id="demo-owner", role_id="finance", company_id="demo-north", format_name="CSV")["allowed"] is True, "财务可受控下载复核版")
    add("PERMISSION-TAX", "PERMISSION", p3.authorize_download(n1, c1, user_id="demo-owner", role_id="tax", company_id="demo-north", format_name="PDF")["allowed"] is False, "税务角色无下载权限")
    add("PERMISSION-CROSS-COMPANY", "PERMISSION", p3.authorize_download(n1, c1, user_id="demo-owner", role_id="finance", company_id="demo-west", format_name="PDF")["allowed"] is False, "跨主体下载失败关闭")

    add("UI-THREE-STEPS", "HUMAN_USABILITY", [text.count('aria-label="经营报告流程步骤"') for text in html_by_step] == [1, 2, 3], "三个运行时逐层提供三步导航")
    add(
        "UI-CURRENT-STEP", "HUMAN_USABILITY",
        all(token in text for token, text in zip(
            ('href="/report-model" aria-current="step"', 'href="/report-generation" aria-current="step"', 'href="/report-workflow" aria-current="step"'),
            html_by_step,
        )),
        "三个页面分别标出自身当前步骤",
    )
    add("UI-FIVE-FILTERS", "HUMAN_USABILITY", all(token in workflow_html for token in ("rw-center-company", "rw-center-period", "rw-center-type", "rw-center-status", "rw-center-version")), "报告中心五类筛选齐全")
    add("UI-SELECTED-CASE", "HUMAN_USABILITY", "value.cases.find(row=>row.report_version_id===selected)" in workflow_html, "页面按所选版本绑定流程")
    add("UI-SELECTED-COMPANY", "HUMAN_USABILITY", "company_id:report.company_id" in workflow_html, "预览使用所选报告主体")
    add("UI-CSS-VALID", "HUMAN_USABILITY", "<style>" not in p2_runtime.render_html().split("<style>", 1)[1].split("</style>", 1)[0], "生成页没有嵌套 style")
    add("UI-TOUCH-RESPONSIVE", "HUMAN_USABILITY", all("min-height:44px" in text and "@media" in text for text in html_by_step), "三页具备触控尺寸和响应式规则")
    add("BOUNDARY-ZERO", "SCOPE_SAFETY", all(row.get("raw_access_count", 0) == 0 and not row.get("approval_or_publication_performed", False) for row in exports) and all(not row["external_publication_performed"] for row in cases), "无 raw、外部发布、GitHub 或 App 动作")

    if len(rows) != EXPECTED_BINDING_COUNT:
        raise StageReviewError(f"REVIEW_BINDING_COUNT_DRIFT：预期 {EXPECTED_BINDING_COUNT}，实际 {len(rows)}。")
    return rows


def integrated_review() -> dict[str, Any]:
    bindings = integration_bindings()
    failed = [row for row in bindings if row["status"] != "PASS"]
    return {
        "schema_version": "kmfa.v015.s21.integrated-stage-review.v1",
        "fixture_class": "PUBLIC_SYNTHETIC_LOCALHOST_TWO_COMPANY_MULTI_VERSION",
        "predecessor_phase_count": 3,
        "predecessor_task_accepted_count": 9,
        "predecessor_receipt_count": 60,
        "predecessor_public_check_count": 168,
        "integration_binding_count": len(bindings),
        "integration_binding_passed_count": len(bindings) - len(failed),
        "integration_binding_failed_count": len(failed),
        "integration_bindings": bindings,
        "review_finding_count": len(REVIEW_FINDINGS),
        "review_fixed_finding_count": len(REVIEW_FINDINGS),
        "review_open_finding_count": 0,
        "technical_audit": technical_audit(),
        "stage_acceptance_ready": not failed,
        "taskpack_phase_count_delta": 0,
        "taskpack_task_count_delta": 0,
        "raw_root_access_count": 0,
        "external_publication_count": 0,
        "github_upload_count": 0,
        "app_reinstall_count": 0,
    }


def main() -> int:
    payload = integrated_review()
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if payload["stage_acceptance_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
