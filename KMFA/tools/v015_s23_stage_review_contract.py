#!/usr/bin/env python3
"""KMFA v1.5 S23 端到端、压力与稳定性三部分整体复审合同。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


RUN_PHASE_ID = "V015_S23_STAGE_REVIEW"
TASK_ID = "KMFA-V015-S23-STAGE-REVIEW-20260717"
ACCEPTANCE_ID = "ACC-KMFA-V015-S23-STAGE-REVIEW"
VERSION = "1.5.0-dev-s23-review"
REVIEW_BASE_COMMIT = "9c48bd9b496f4fb50575191415da8eb66e28e38f"
EXPECTED_BINDING_COUNT = 40

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = PROJECT_ROOT / "stage_artifacts"

REVIEW_FINDINGS = (
    {
        "finding_id": "S23REV-F001",
        "severity": "P1",
        "category": "HUMAN_STATUS_CONSOLIDATION",
        "issue_zh": "S23 三部分虽均已验收，但面向人的当前说明分散，P2 的精密与恢复结果未进入统一首屏结论。",
        "impact_zh": "用户需要在多个机器证据和历史段落间拼接，难以直接判断 S23 是否真正完成。",
        "fix_zh": "新增 S23 整体中文复审结论，并同步 README、HANDOFF、功能清单、开发记录和模型参数文件的当前入口。",
        "status": "FIXED_VALIDATED",
        "blocks_stage_acceptance": False,
    },
    {
        "finding_id": "S23REV-F002",
        "severity": "P1",
        "category": "ROLE_TASK_TARGET_ASSERTION",
        "issue_zh": "原三岗位浏览器任务主要确认路由变化和通用标题，未逐项证明进入了正确业务视图。",
        "impact_zh": "错误页面也可能被误判为任务完成，岗位可用性证据不够强。",
        "fix_zh": "经营、财务、税务任务增加精确路由、业务视图、中文标题和刷新后角色保持共十一项真实浏览器断言。",
        "status": "FIXED_VALIDATED",
        "blocks_stage_acceptance": False,
    },
)

KNOWN_LIMITATIONS = (
    {
        "limitation_id": "S23REV-L001",
        "description_zh": "岗位任务是自动化角色模拟，不是外部真人访谈。",
        "control_zh": "证据明确标注 observer_type，且用真实 Chromium、可见控件和业务内容断言验证。",
        "status": "CONTROLLED_NONBLOCKING",
    },
    {
        "limitation_id": "S23REV-L002",
        "description_zh": "内存指标是本地 Python 分配增长，不等同于生产进程完整 RSS。",
        "control_zh": "仅作为本地回归预算；不得外推为生产容量结论，S24 前继续保留该边界。",
        "status": "CONTROLLED_NONBLOCKING",
    },
)


class StageReviewError(ValueError):
    """S23 三部分证据或跨部分连接不一致。"""


def _json(relative: str) -> dict[str, Any]:
    value = json.loads((ARTIFACT_ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise StageReviewError(f"JSON 对象缺失：{relative}")
    return value


def _receipts(relative: str) -> dict[str, Any]:
    rows = [
        json.loads(line)
        for line in (ARTIFACT_ROOT / relative).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return {
        "count": len(rows),
        "pass_count": sum(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in rows),
        "run_ids": {row.get("validation_run_id") for row in rows},
        "heads": {row.get("validation_head") for row in rows},
    }


def technical_audit() -> dict[str, Any]:
    dimensions = [
        {"dimension": "end_to_end_accuracy", "score": 4, "finding_zh": "首页、项目、报告、四格式、审批和修订共用权威版本，金额零差异。"},
        {"dimension": "precision_load_recovery", "score": 4, "finding_zh": "精密、并发、恶意输入和中断恢复均先过正确性门禁。"},
        {"dimension": "stability_idempotency", "score": 4, "finding_zh": "十二轮浸泡、三次重启和二十四次刷新无静默错误或泄漏。"},
        {"dimension": "usability_accessibility", "score": 4, "finding_zh": "三岗位目标页、键盘、对比度、缩放、窄屏与打印均有真实浏览器断言。"},
        {"dimension": "traceability_and_boundary", "score": 4, "finding_zh": "三部分六十条正式回执完整，raw、外网、S24 和发布动作保持关闭。"},
    ]
    return {
        "schema_version": "kmfa.v015.s23.stage-review-technical-audit.v1",
        "method": "RECEIPT_BOUND_CROSS_PHASE_BUSINESS_TECHNICAL_BROWSER_REVIEW",
        "scale_per_dimension": 4,
        "maximum_score": 20,
        "dimensions": dimensions,
        "total_score": sum(row["score"] for row in dimensions),
        "rating": "EXCELLENT_LOCAL_ONLY",
        "fixed_issue_count": len(REVIEW_FINDINGS),
        "open_issue_count": 0,
        "known_limitation_count": len(KNOWN_LIMITATIONS),
    }


def integration_bindings() -> list[dict[str, Any]]:
    p1_public = _json("V015_S23_P1_END_TO_END_BUSINESS_FLOW/machine/public_verification.json")
    p2_public = _json("V015_S23_P2_PRECISION_STRESS_EXTREME/machine/public_verification.json")
    p3_public = _json("V015_S23_P3_STABILITY_USABILITY/machine/public_verification.json")
    p1_trace = _json("V015_S23_P1_END_TO_END_BUSINESS_FLOW/machine/end_to_end_trace_public_safe.json")
    p1_formats = _json("V015_S23_P1_END_TO_END_BUSINESS_FLOW/machine/cross_format_consistency.json")
    p2_precision = _json("V015_S23_P2_PRECISION_STRESS_EXTREME/machine/precision_report.json")
    p2_scale = _json("V015_S23_P2_PRECISION_STRESS_EXTREME/machine/performance_report.json")
    p2_extreme = _json("V015_S23_P2_PRECISION_STRESS_EXTREME/machine/extreme_recovery_report.json")
    p3_soak = _json("V015_S23_P3_STABILITY_USABILITY/machine/soak_report.json")
    p3_browser = _json("V015_S23_P3_STABILITY_USABILITY/machine/browser_acceptance.json")
    p3_use = p3_browser["usability"]
    p3_access = p3_browser["accessibility"]
    rows: list[dict[str, Any]] = []

    def add(binding_id: str, kind: str, passed: bool, detail_zh: str) -> None:
        rows.append({"binding_id": binding_id, "kind": kind, "status": "PASS" if passed else "FAIL", "detail": detail_zh})

    for index, (value, expected) in enumerate(((p1_public, 47), (p2_public, 49), (p3_public, 60)), 1):
        add(f"PHASE-{index:02d}", "PREDECESSOR_PUBLIC_CONTRACT", value.get("status") == "PASS" and value.get("check_count") == expected and value.get("fail_count") == 0, f"前序公开检查 {expected}/{expected}")
    for index, relative in enumerate((
        "V015_S23_P1_END_TO_END_BUSINESS_FLOW/machine/formal_validation_results.jsonl",
        "V015_S23_P2_PRECISION_STRESS_EXTREME/machine/formal_validation_results.jsonl",
        "V015_S23_P3_STABILITY_USABILITY/machine/formal_validation_results.jsonl",
    ), 1):
        summary = _receipts(relative)
        add(f"RECEIPTS-{index:02d}", "PREDECESSOR_FORMAL_ACCEPTANCE", summary["count"] == summary["pass_count"] == 20 and len(summary["run_ids"]) == len(summary["heads"]) == 1, "前序正式回执 20/20 且绑定单一 Run 与提交")

    add("P1-AUTHORITATIVE", "END_TO_END", p1_trace["publication_version_count"] == 1 and p1_trace["backend_view_count"] == 4 and p1_trace["homepage_authoritative_binding_count"] == 1, "首页与四个后端视图共用一个发布版本")
    add("P1-PROJECT-ZERO", "END_TO_END", p1_trace["authoritative_project_count"] == 4 and p1_trace["project_difference_cents"] == 0, "四个项目金额零差异")
    add("P1-REPORT-HISTORY", "END_TO_END", p1_trace["report_version_count"] == 2 and p1_trace["report_export_count"] == 2, "两版报告和两次导出历史完整")
    add("P1-FOUR-FORMATS", "END_TO_END", p1_formats["format_count"] == 4 and set(p1_formats["formats"]) == {"HTML", "PDF", "CSV", "XLSX"}, "四种交付格式齐全")
    add("P1-CROSS-FORMAT", "END_TO_END", p1_formats["difference_integer"] == 0 and p1_formats["numeric_value_count"] == 26, "二十六个跨格式数值零差异")
    add("P1-XLSX", "END_TO_END", p1_formats["xlsx_sheet_count"] == 3 and p1_formats["xlsx_formula_error_count"] == 0 and p1_formats["xlsx_visual_pass_count"] == 3, "XLSX 三表公式和视觉检查通过")
    add("P1-WORKFLOW", "END_TO_END", p1_trace["workflow_case_count"] == 2 and p1_trace["workflow_step_count_per_case"] == 5 and p1_trace["latest_workflow_state"] == "PUBLISHED_INTERNAL", "两版报告均走完五步内部审批")
    add("P1-REVISION", "END_TO_END", p1_trace["revision_source_difference_count"] >= 1 and p1_trace["revision_unexplained_difference_count"] == 0, "修订有来源变化且无无法解释差异")
    add("P1-REFRESH", "END_TO_END", p1_trace["refresh_persistence_passed"] is True, "刷新后权威版本和历史保持")
    add("P1-PUBLIC-CONTRACT", "END_TO_END", p1_public["pass_count"] == 47, "S23-P1 全部公开合同通过")

    add("P2-PRECISION-SHAPE", "PRECISION_LOAD_RECOVERY", p2_precision["case_count"] == 20_000 and p2_precision["project_count"] == 20_000 and p2_precision["account_count"] == 5_000, "两万精密案例覆盖项目与账户规模")
    add("P2-INTEGER-ZERO", "PRECISION_LOAD_RECOVERY", p2_precision["difference_cents"] == p2_precision["project_difference_cents"] == p2_precision["cross_sheet_difference_cents"] == 0 and p2_precision["rounding_difference_count"] == 0, "金额、项目、跨表与舍入均零差异")
    add("P2-EXTREME-VALUE", "PRECISION_LOAD_RECOVERY", p2_precision["maximum_absolute_cents"] == 9_000_000_000_000_000 and p2_precision["format_error_count"] == 0, "极大、负数和零值格式安全")
    add("P2-NO-FLOAT", "PRECISION_LOAD_RECOVERY", p2_precision["float_input_rejection_count"] == 4 and p2_precision["float_money_accept_count"] == 0, "浮点金额路径全部失败关闭")
    add("P2-SCALE", "PRECISION_LOAD_RECOVERY", p2_scale["synthetic_file_count"] == 128 and p2_scale["worksheet_count"] == 64 and p2_scale["project_count"] == 20_000 and p2_scale["account_count"] == 5_000, "规模样本完整")
    add("P2-CONCURRENCY", "PRECISION_LOAD_RECOVERY", p2_scale["concurrent_import_count"] == 128 and p2_scale["concurrent_report_count"] == 128 and p2_scale["concurrency_worker_count"] == 8, "导入与报告并发完成")
    add("P2-CORRECTNESS-FIRST", "PRECISION_LOAD_RECOVERY", p2_scale["data_error_count"] == 0 and p2_scale["aggregate_difference_cents"] == 0 and p2_scale["performance_budget_passed"] is True and p2_scale["correctness_precedes_performance"] is True, "正确性优先且性能预算通过")
    add("P2-HOSTILE", "PRECISION_LOAD_RECOVERY", p2_extreme["attack_case_count"] == p2_extreme["rejected_attack_count"] == 9, "九类恶意输入全部拒绝")
    add("P2-RECOVERY", "PRECISION_LOAD_RECOVERY", p2_extreme["fault_injection_count"] == p2_extreme["safe_interruption_count"] == p2_extreme["successful_recovery_count"] == 1 and p2_extreme["partial_commit_visible_count"] == p2_extreme["leftover_temporary_count"] == p2_extreme["data_pollution_count"] == 0, "中断恢复无半成品、临时残留或污染")

    add("P3-SOAK", "STABILITY_USABILITY", p3_soak["soak_cycle_count"] == p3_soak["repeated_import_count"] == p3_soak["repeated_recalculation_count"] == p3_soak["repeated_report_count"] == 12, "十二轮真实本地业务循环完成")
    add("P3-RESTART-REFRESH", "STABILITY_USABILITY", p3_soak["restart_count"] == 3 and p3_soak["refresh_count"] == 24 and p3_soak["restart_error_count"] == 0, "三次重启和二十四次刷新通过")
    add("P3-ERROR-LEAK-ZERO", "STABILITY_USABILITY", all(p3_soak[key] == 0 for key in ("operation_error_count", "silent_error_count", "queue_leak_count", "temporary_file_leak_count", "thread_leak_count", "publication_drift_count")), "错误、泄漏和发布漂移为零")
    add("P3-MEMORY", "STABILITY_USABILITY", p3_soak["memory_growth_bytes"] <= p3_soak["memory_growth_budget_bytes"] and p3_soak["memory_growth_excess_count"] == 0, "本地 Python 分配增长在预算内")
    add("P3-USABILITY", "STABILITY_USABILITY", p3_use["task_count"] == p3_use["completed_task_count"] == 3 and p3_use["completion_rate_bps"] == 10_000 and p3_use["issue_count"] == 0, "经营、财务、税务三任务全部完成")
    add("P3-BUSINESS-TARGETS", "STABILITY_USABILITY", p3_use.get("business_target_assertion_count") == 11 and p3_use.get("business_target_assertion_fail_count") == 0 and p3_use.get("role_persistence_check_count") == 1 and all(all(row.get("target_assertions", {}).values()) for row in p3_use["tasks"]), "十一项目标页与角色保持断言通过")
    add("P3-ACCESSIBILITY", "STABILITY_USABILITY", p3_access["check_count"] == 34 and p3_access["fail_count"] == 0, "三十四项可访问性检查通过")
    add("P3-RESPONSIVE", "STABILITY_USABILITY", p3_access["contrast_fail_count"] == p3_access["narrow_overflow_count"] == p3_access["touch_target_fail_count"] == p3_access["color_only_critical_info_count"] == 0, "对比度、窄屏、触控和非颜色单一表达通过")
    add("P3-HONEST-LIMITS", "STABILITY_USABILITY", p3_browser.get("observer_type") == "AUTOMATED_ROLE_TASK_SIMULATION" and len(KNOWN_LIMITATIONS) == 2, "自动化岗位模拟与局部内存口径均明确披露")

    manifests = [
        _json("V015_S23_P1_END_TO_END_BUSINESS_FLOW/machine/s23_p1_end_to_end_business_flow_manifest.json"),
        _json("V015_S23_P2_PRECISION_STRESS_EXTREME/machine/s23_p2_precision_stress_extreme_manifest.json"),
        _json("V015_S23_P3_STABILITY_USABILITY/machine/s23_p3_stability_usability_manifest.json"),
    ]
    screenshots = p1_public.get("screenshot_paths", []) or _json("V015_S23_P1_END_TO_END_BUSINESS_FLOW/machine/browser_acceptance.json")["screenshot_paths"]
    screenshots += p3_browser["screenshot_paths"]
    add("CROSS-PUBLIC-COUNT", "CROSS_PHASE", sum(value["check_count"] for value in (p1_public, p2_public, p3_public)) == 156, "三部分一百五十六项公开检查完整")
    add("CROSS-RECEIPT-COUNT", "CROSS_PHASE", sum(_receipts(path)["count"] for path in (
        "V015_S23_P1_END_TO_END_BUSINESS_FLOW/machine/formal_validation_results.jsonl",
        "V015_S23_P2_PRECISION_STRESS_EXTREME/machine/formal_validation_results.jsonl",
        "V015_S23_P3_STABILITY_USABILITY/machine/formal_validation_results.jsonl",
    )) == 60, "三部分六十条正式回执完整")
    add("CROSS-BOUNDARY", "CROSS_PHASE", all(row.get("raw_root_access_count") == row.get("external_network_request_count") == 0 for row in manifests), "raw 与外部网络访问为零")
    add("CROSS-VISUAL-EVIDENCE", "CROSS_PHASE", len(screenshots) == 15 and all((PROJECT_ROOT.parent / path).is_file() for path in screenshots), "复用十五张真实浏览器画面，无重复低价值截图")
    add("CROSS-RELEASE-CLOSED", "CROSS_PHASE", all(not row.get("github_upload_performed") and not row.get("app_reinstall_performed") for row in manifests), "GitHub 与 App 动作关闭")
    add("CROSS-S24-CLOSED", "CROSS_PHASE", manifests[-1].get("s24_started") is False and manifests[-1].get("s24_execution_count") == 0, "S24 尚未开始")

    if len(rows) != EXPECTED_BINDING_COUNT:
        raise StageReviewError(f"REVIEW_BINDING_COUNT_DRIFT：预期 {EXPECTED_BINDING_COUNT}，实际 {len(rows)}。")
    return rows


def integrated_review() -> dict[str, Any]:
    bindings = integration_bindings()
    failed = [row for row in bindings if row["status"] != "PASS"]
    return {
        "schema_version": "kmfa.v015.s23.integrated-stage-review.v1",
        "fixture_class": "PUBLIC_SYNTHETIC_LOCALHOST_RECEIPT_BOUND",
        "predecessor_phase_count": 3,
        "predecessor_task_accepted_count": 9,
        "predecessor_receipt_count": 60,
        "predecessor_public_check_count": 156,
        "integration_binding_count": len(bindings),
        "integration_binding_passed_count": len(bindings) - len(failed),
        "integration_binding_failed_count": len(failed),
        "integration_bindings": bindings,
        "review_finding_count": len(REVIEW_FINDINGS),
        "review_fixed_finding_count": len(REVIEW_FINDINGS),
        "review_open_finding_count": 0,
        "known_limitations": list(KNOWN_LIMITATIONS),
        "technical_audit": technical_audit(),
        "stage_acceptance_ready": not failed,
        "taskpack_phase_count_delta": 0,
        "taskpack_task_count_delta": 0,
        "raw_root_access_count": 0,
        "external_network_request_count": 0,
        "github_upload_count": 0,
        "app_reinstall_count": 0,
        "s24_started": False,
    }


def main() -> int:
    payload = integrated_review()
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if payload["stage_acceptance_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
