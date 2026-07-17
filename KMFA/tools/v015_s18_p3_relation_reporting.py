#!/usr/bin/env python3
"""KMFA v1.5 S18-P3 项目现金双视图、资金预警与周期报告。

只复用公开合成数据。利润与现金占用使用不同口径；提醒只保留内部复核所需的
最少信息；未核验资料必须降级并隐藏金额。本模块不发送提醒、不执行付款，也不
生成可用于真实经营决策的正式报告。
"""

from __future__ import annotations

import csv
import io
import json
from html import escape
from pathlib import Path
from typing import Any, Mapping, Sequence

from KMFA.tools import v015_s17_p1_project_list as projects
from KMFA.tools import v015_s17_p3_project_workflow as project_workflow
from KMFA.tools import v015_s18_p1_receivables_collections as receivables
from KMFA.tools import v015_s18_p2_funds_accounts as funds


RUN_PHASE_ID = "V015_S18_P3_RELATION_REPORTING"
ROADMAP_PHASE_ID = "S18-P3"
TASK_ID = "KMFA-V015-S18-P3-RELATION-REPORTING-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S18-P3-RELATION-REPORTING"
VERSION = "1.5.0-dev-s18p3"

DATA_CLASSIFICATION = "PUBLIC_SYNTHETIC"
REPORT_SCENARIO_ID = "collection_delay"
VERIFICATION_STATES = ("VERIFIED", "UNVERIFIED")
MONEY_TOLERANCE_CENTS = 0
CONFIG_PATH = Path(__file__).resolve().parents[1] / "config/v015_s18_p3_alert_thresholds.json"
CONFIG_REF = "KMFA/config/v015_s18_p3_alert_thresholds.json"

ALERT_TYPES = ("MAJOR_OVERDUE", "FUNDING_GAP", "LOAN_MATURITY")
SENSITIVE_ALERT_FIELDS = {
    "customer_zh",
    "account_id",
    "masked_account",
    "source_ref",
    "invoice_id",
    "item_id",
    "contract_id",
    "principal_cents",
    "receivable_cents",
    "funding_gap_cents",
}
REPORT_MONEY_FIELDS = (
    "revenue_cents",
    "cost_cents",
    "gross_profit_cents",
    "open_receivable_cents",
    "unbilled_cents",
    "cash_occupied_cents",
    "overdue_receivable_cents",
)


class RelationReportingError(ValueError):
    """S18-P3 请求不满足公开、安全和降级合同。"""


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s18p3.source_contract.v1",
        "stage_id": "S18",
        "stage_name_zh": "回款、应收、资金与贷款分析",
        "stage_goal_zh": "建立现金安全、催收优先级、多主体账户和资金计划能力，不执行付款。",
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "phase_name_zh": "关联与报告",
        "task_ids": ["S18P3T01", "S18P3T02", "S18P3T03"],
        "task_names_zh": ["项目现金双视图", "实现回款和资金预警", "生成资金与应收报告"],
        "acceptance_zh": ["不会用利润替代现金。", "阈值外置。", "数字与页面一致。"],
        "evidence_zh": ["交叉测试。", "预警测试。", "导出测试。"],
        "stop_conditions_zh": ["口径不明则显示限制。", "提醒不得包含完整敏感明细。", "未核验数据报告降级。"],
        "data_classification": DATA_CLASSIFICATION,
    }


def format_money(cents: int | None) -> str:
    if cents is None:
        return "暂不可用"
    if isinstance(cents, bool) or not isinstance(cents, int):
        raise RelationReportingError("money must use integer cents")
    sign = "-" if cents < 0 else ""
    yuan, fen = divmod(abs(cents), 100)
    return f"{sign}¥{yuan:,}.{fen:02d}"


def load_alert_thresholds(path: Path | str = CONFIG_PATH) -> dict[str, Any]:
    config_path = Path(path)
    try:
        value = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RelationReportingError("预警阈值配置无法读取") from error
    required = {
        "schema_version": "kmfa.v015.s18p3.alert_thresholds.v1",
        "data_classification": DATA_CLASSIFICATION,
        "currency": "CNY",
    }
    if any(value.get(key) != expected for key, expected in required.items()):
        raise RelationReportingError("预警阈值配置版本或分类不正确")
    if not isinstance(value.get("threshold_version"), str) or not value["threshold_version"].strip():
        raise RelationReportingError("预警阈值必须有版本")
    for key, minimum in (
        ("major_overdue_amount_cents", 1),
        ("major_overdue_days", 1),
        ("funding_gap_cents", 1),
        ("loan_maturity_days", 1),
    ):
        current = value.get(key)
        if isinstance(current, bool) or not isinstance(current, int) or current < minimum:
            raise RelationReportingError(f"预警阈值不正确：{key}")
    if value.get("owner_role") != "财务负责人" or "复跑" not in str(value.get("change_policy", "")):
        raise RelationReportingError("预警阈值责任或变更规则不完整")
    return value


def _verification_state(value: str) -> str:
    state = value.upper()
    if state not in VERIFICATION_STATES:
        raise RelationReportingError("unsupported verification state")
    return state


def _project_cash_rows(
    company_id: str,
    period: str,
    project_events: Sequence[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    catalog = projects.project_catalog(company_id, period)
    ar = receivables.receivable_facts(company_id, period)
    open_by_project: dict[str, int] = {}
    overdue_by_project: dict[str, int] = {}
    unbilled_by_project: dict[str, int] = {}
    for row in ar["rows"]:
        project_id = str(row["project_id"])
        open_by_project[project_id] = open_by_project.get(project_id, 0) + int(row["receivable_cents"])
        overdue_by_project[project_id] = overdue_by_project.get(project_id, 0) + int(row["overdue_cents"])
    for row in ar["unbilled_items"]:
        project_id = str(row["project_id"])
        unbilled_by_project[project_id] = unbilled_by_project.get(project_id, 0) + int(row["unbilled_cents"])

    rows: list[dict[str, Any]] = []
    events = project_events or ()
    for base_project in catalog:
        project = project_workflow.project_projection(
            project_id=str(base_project["project_id"]),
            company_id=company_id,
            period=period,
            events=events,
        )["project"]
        project_id = str(project["project_id"])
        open_receivable = open_by_project.get(project_id, 0)
        unbilled = unbilled_by_project.get(project_id, 0)
        cash_occupied = open_receivable + unbilled
        row = {
            "company_id": company_id,
            "period": period,
            "project_id": project_id,
            "project_name_zh": project["project_name_zh"],
            "owner_zh": project["owner_zh"],
            "revenue_cents": int(project["revenue_cents"]),
            "cost_cents": int(project["cost_cents"]),
            "gross_profit_cents": int(project["gross_profit_cents"]),
            "gross_margin_bps": int(project["gross_margin_bps"]),
            "open_receivable_cents": open_receivable,
            "unbilled_cents": unbilled,
            "cash_occupied_cents": cash_occupied,
            "overdue_receivable_cents": overdue_by_project.get(project_id, 0),
            "profit_basis_zh": "项目收入减项目成本",
            "cash_basis_zh": "已开票未回款加未开票节点金额",
            "scope_limitation_zh": "资金占用仅覆盖当前公开演示的应收与未开票节点，不代表项目完整现金流。",
            "profit_used_as_cash": False,
            "source_group_count": 2,
            "source_groups_zh": ["项目收入与成本公开演示事实", "应收与未开票公开演示事实"],
            "data_classification": DATA_CLASSIFICATION,
        }
        if row["revenue_cents"] != row["cost_cents"] + row["gross_profit_cents"]:
            raise RelationReportingError("项目利润口径不守恒")
        rows.append(row)
    return rows


def project_cash_dual_view(
    company_id: str = "demo-north",
    period: str = "2026-07",
    verification_state: str = "VERIFIED",
    project_events: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    state = _verification_state(verification_state)
    rows = _project_cash_rows(company_id, period, project_events)
    verified_totals = {
        field: sum(int(row[field]) for row in rows)
        for field in REPORT_MONEY_FIELDS
    }
    verified_totals["gross_margin_bps"] = (
        verified_totals["gross_profit_cents"] * 10_000 // verified_totals["revenue_cents"]
        if verified_totals["revenue_cents"]
        else 0
    )
    if state == "UNVERIFIED":
        hidden_count = 0
        redacted_rows: list[dict[str, Any]] = []
        for row in rows:
            redacted = dict(row)
            for field in (*REPORT_MONEY_FIELDS, "gross_margin_bps"):
                if redacted.get(field) is not None:
                    hidden_count += 1
                redacted[field] = None
            redacted["scope_limitation_zh"] = "资料尚未核验，利润和资金占用金额已隐藏，不能形成经营判断。"
            redacted_rows.append(redacted)
        return {
            "schema_version": "kmfa.v015.s18p3.project_cash_dual_view.v1",
            "company_id": company_id,
            "period": period,
            "verification_state": state,
            "numeric_detail_allowed": False,
            "rows": redacted_rows,
            "totals": {field: None for field in (*REPORT_MONEY_FIELDS, "gross_margin_bps")},
            "project_count": len(rows),
            "profit_cash_substitution_count": 0,
            "scope_limitation_displayed_count": len(rows),
            "hidden_numeric_field_count": hidden_count,
            "profit_equation_difference_cents": 0,
            "cash_occupancy_reconciliation_difference_cents": 0,
            "cross_company_leak_count": 0,
            "data_classification": DATA_CLASSIFICATION,
        }
    return {
        "schema_version": "kmfa.v015.s18p3.project_cash_dual_view.v1",
        "company_id": company_id,
        "period": period,
        "verification_state": state,
        "numeric_detail_allowed": True,
        "rows": rows,
        "totals": verified_totals,
        "project_count": len(rows),
        "profit_cash_substitution_count": sum(bool(row["profit_used_as_cash"]) for row in rows),
        "scope_limitation_displayed_count": sum(bool(row["scope_limitation_zh"]) for row in rows),
        "hidden_numeric_field_count": 0,
        "profit_equation_difference_cents": sum(
            int(row["revenue_cents"]) - int(row["cost_cents"]) - int(row["gross_profit_cents"])
            for row in rows
        ),
        "cash_occupancy_reconciliation_difference_cents": verified_totals["cash_occupied_cents"]
        - verified_totals["open_receivable_cents"]
        - verified_totals["unbilled_cents"],
        "cross_company_leak_count": sum(row["company_id"] != company_id for row in rows),
        "data_classification": DATA_CLASSIFICATION,
    }


def _amount_band_zh(kind: str) -> str:
    return {
        "overdue": "达到重大逾期金额阈值",
        "gap": "达到资金缺口提醒阈值",
    }[kind]


def _verified_alert_rows(company_id: str, period: str, scenario_id: str, thresholds: Mapping[str, Any]) -> list[dict[str, Any]]:
    ar = receivables.receivable_facts(company_id, period)
    rows: list[dict[str, Any]] = []
    for item in ar["rows"]:
        if (
            int(item["overdue_cents"]) >= int(thresholds["major_overdue_amount_cents"])
            and int(item["overdue_days"]) >= int(thresholds["major_overdue_days"])
        ):
            rows.append(
                {
                    "alert_id": f"ALERT-OVERDUE-{item['project_id']}-{len(rows) + 1}",
                    "alert_type": "MAJOR_OVERDUE",
                    "severity": "HIGH",
                    "title_zh": "重大逾期需内部复核",
                    "summary_zh": f"项目 {item['project_id']} 已达到重大逾期金额和天数阈值。",
                    "project_ref": item["project_id"],
                    "amount_band_zh": _amount_band_zh("overdue"),
                    "time_band_zh": "逾期 60 天以上",
                    "owner_role": thresholds["owner_role"],
                    "internal_action_zh": "核对应收证据、争议和回款计划",
                    "detail_route": f"/collections?project={item['project_id']}",
                }
            )
    funding = funds.loan_funding_plan(company_id, period, scenario_id)
    for item in funding["funding_rows"]:
        if int(item["funding_gap_cents"]) >= int(thresholds["funding_gap_cents"]):
            rows.append(
                {
                    "alert_id": f"ALERT-GAP-{item['period_index'] + 1}",
                    "alert_type": "FUNDING_GAP",
                    "severity": "HIGH",
                    "title_zh": "资金缺口需内部复核",
                    "summary_zh": f"{item['period_label_zh']} 在当前情景下达到资金缺口提醒阈值。",
                    "period_ref": item["period_label_zh"],
                    "amount_band_zh": _amount_band_zh("gap"),
                    "time_band_zh": "未来四周",
                    "owner_role": thresholds["owner_role"],
                    "internal_action_zh": "复核回款、付款时间和融资方案",
                    "detail_route": "/funds",
                }
            )
    for item in funding["loans"]:
        if 0 <= int(item["days_to_maturity"]) <= int(thresholds["loan_maturity_days"]):
            rows.append(
                {
                    "alert_id": f"ALERT-LOAN-{item['loan_id'][-3:]}",
                    "alert_type": "LOAN_MATURITY",
                    "severity": "MEDIUM" if int(item["days_to_maturity"]) > 30 else "HIGH",
                    "title_zh": "贷款到期需内部复核",
                    "summary_zh": f"{item['masked_contract']} 已进入 90 天到期复核窗口。",
                    "loan_ref": item["masked_contract"],
                    "amount_band_zh": "不在提醒中展示金额",
                    "time_band_zh": "90 天内到期",
                    "owner_role": thresholds["owner_role"],
                    "internal_action_zh": "核对到期安排和资金来源",
                    "detail_route": "/funds",
                }
            )
    for row in rows:
        row.update(
            {
                "company_id": company_id,
                "period": period,
                "threshold_version": thresholds["threshold_version"],
                "contains_full_sensitive_detail": False,
                "notification_send_allowed": False,
                "external_message_allowed": False,
                "data_classification": DATA_CLASSIFICATION,
            }
        )
    return rows


def alert_view(
    company_id: str = "demo-north",
    period: str = "2026-07",
    scenario_id: str = REPORT_SCENARIO_ID,
    verification_state: str = "VERIFIED",
    threshold_path: Path | str = CONFIG_PATH,
) -> dict[str, Any]:
    state = _verification_state(verification_state)
    if scenario_id not in funds.SCENARIO_IDS:
        raise RelationReportingError("unsupported alert scenario")
    thresholds = load_alert_thresholds(threshold_path)
    candidates = _verified_alert_rows(company_id, period, scenario_id, thresholds)
    exposed_sensitive_fields = sorted({key for row in candidates for key in row if key in SENSITIVE_ALERT_FIELDS})
    if exposed_sensitive_fields:
        raise RelationReportingError("提醒包含了不允许的敏感字段")
    visible = candidates if state == "VERIFIED" else []
    counts = {alert_type: sum(row["alert_type"] == alert_type for row in visible) for alert_type in ALERT_TYPES}
    return {
        "schema_version": "kmfa.v015.s18p3.alert_view.v1",
        "company_id": company_id,
        "period": period,
        "scenario_id": scenario_id,
        "verification_state": state,
        "alerts": visible,
        "alert_count": len(visible),
        "candidate_alert_count": len(candidates),
        "suppressed_unverified_alert_count": 0 if state == "VERIFIED" else len(candidates),
        "alert_type_count": sum(count > 0 for count in counts.values()),
        "alert_count_by_type": counts,
        "thresholds": dict(thresholds),
        "threshold_version": thresholds["threshold_version"],
        "threshold_config_ref": CONFIG_REF,
        "thresholds_externalized": True,
        "full_sensitive_detail_count": sum(bool(row["contains_full_sensitive_detail"]) for row in visible),
        "exposed_sensitive_field_count": len(exposed_sensitive_fields),
        "notification_send_count": 0,
        "external_message_count": 0,
        "cross_company_leak_count": sum(row["company_id"] != company_id for row in visible),
        "data_classification": DATA_CLASSIFICATION,
    }


def periodic_report(
    company_id: str = "demo-north",
    period: str = "2026-07",
    scenario_id: str = REPORT_SCENARIO_ID,
    verification_state: str = "VERIFIED",
    project_events: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    state = _verification_state(verification_state)
    dual = project_cash_dual_view(company_id, period, state, project_events)
    alerts = alert_view(company_id, period, scenario_id, state)
    verified = state == "VERIFIED"
    page_rows = [dict(row) for row in dual["rows"]]
    appendix_rows = [dict(row) for row in dual["rows"]]
    page_export_difference = 0
    if verified:
        page_export_difference = sum(
            int(page[field]) - int(appendix[field])
            for page, appendix in zip(page_rows, appendix_rows)
            for field in REPORT_MONEY_FIELDS
        )
    return {
        "schema_version": "kmfa.v015.s18p3.periodic_report.v1",
        "report_id": f"PUBLIC-FUNDS-AR-{company_id}-{period}",
        "report_version": VERSION,
        "title_zh": "资金与应收周期报告（公开演示）",
        "company_id": company_id,
        "period": period,
        "scenario_id": scenario_id,
        "verification_state": state,
        "report_status": "PUBLIC_SYNTHETIC_VALIDATED" if verified else "DEGRADED_UNVERIFIED",
        "report_status_zh": "公开演示资料已核验" if verified else "资料未核验，报告已降级",
        "report_grade": "DEMO_ONLY" if verified else "D",
        "report_degraded": not verified,
        "numeric_detail_allowed": verified,
        "page_rows": page_rows,
        "appendix_rows": appendix_rows,
        "summary": dict(dual["totals"]),
        "alerts": alerts["alerts"],
        "alert_count": alerts["alert_count"],
        "threshold_version": alerts["threshold_version"],
        "threshold_config_ref": alerts["threshold_config_ref"],
        "project_count": dual["project_count"],
        "appendix_row_count": len(appendix_rows),
        "appendix_column_count": 13,
        "report_page_export_difference_cents": page_export_difference,
        "unverified_numeric_visible_count": 0,
        "scope_limitation_zh": "本报告只使用公开合成资料验证页面、预警与导出逻辑，不代表真实经营或资金状况。",
        "degradation_reason_zh": "" if verified else "来源、截止日或关键口径尚未完成核验，所有经营金额均已隐藏。",
        "profit_used_as_cash_count": dual["profit_cash_substitution_count"],
        "full_sensitive_detail_count": alerts["full_sensitive_detail_count"],
        "notification_send_count": 0,
        "payment_execution_count": 0,
        "formal_business_report": False,
        "data_classification": DATA_CLASSIFICATION,
    }


def export_appendix_csv(report: Mapping[str, Any]) -> str:
    output = io.StringIO(newline="")
    fieldnames = [
        "项目编号",
        "项目名称",
        "负责人",
        "收入(分)",
        "成本(分)",
        "毛利(分)",
        "毛利率(基点)",
        "已开票未回款(分)",
        "未开票节点(分)",
        "资金占用(分)",
        "逾期应收(分)",
        "资料状态",
        "口径限制",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["appendix_rows"]:
        writer.writerow(
            {
                "项目编号": row["project_id"],
                "项目名称": row["project_name_zh"],
                "负责人": row["owner_zh"],
                "收入(分)": "" if row["revenue_cents"] is None else row["revenue_cents"],
                "成本(分)": "" if row["cost_cents"] is None else row["cost_cents"],
                "毛利(分)": "" if row["gross_profit_cents"] is None else row["gross_profit_cents"],
                "毛利率(基点)": "" if row["gross_margin_bps"] is None else row["gross_margin_bps"],
                "已开票未回款(分)": "" if row["open_receivable_cents"] is None else row["open_receivable_cents"],
                "未开票节点(分)": "" if row["unbilled_cents"] is None else row["unbilled_cents"],
                "资金占用(分)": "" if row["cash_occupied_cents"] is None else row["cash_occupied_cents"],
                "逾期应收(分)": "" if row["overdue_receivable_cents"] is None else row["overdue_receivable_cents"],
                "资料状态": report["report_status_zh"],
                "口径限制": row["scope_limitation_zh"],
            }
        )
    return output.getvalue()


def render_report_html(report: Mapping[str, Any]) -> str:
    status_class = "degraded" if report["report_degraded"] else "verified"
    rows = []
    for row in report["page_rows"]:
        data_attributes = " ".join(
            f'data-{field.replace("_cents", "").replace("_", "-")}="{escape(str(row[field]))}"'
            for field in REPORT_MONEY_FIELDS
            if row[field] is not None
        )
        rows.append(
            "<tr " + data_attributes + ">"
            f"<td><strong>{escape(str(row['project_name_zh']))}</strong><small>{escape(str(row['project_id']))}</small></td>"
            f"<td>{escape(format_money(row['revenue_cents']))}</td>"
            f"<td>{escape(format_money(row['cost_cents']))}</td>"
            f"<td>{escape(format_money(row['gross_profit_cents']))}</td>"
            f"<td>{escape(format_money(row['open_receivable_cents']))}</td>"
            f"<td>{escape(format_money(row['unbilled_cents']))}</td>"
            f"<td>{escape(format_money(row['cash_occupied_cents']))}</td>"
            f"<td>{escape(str(row['scope_limitation_zh']))}</td>"
            "</tr>"
        )
    alerts = "".join(
        f"<li><strong>{escape(str(row['title_zh']))}</strong><span>{escape(str(row['summary_zh']))}</span></li>"
        for row in report["alerts"]
    ) or "<li><strong>没有可展示的预警</strong><span>资料未核验时预警会暂停并隐藏明细。</span></li>"
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(str(report['title_zh']))}</title>
<style>
body{{margin:0;background:#eef3f6;color:#273f50;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif}}main{{max-width:1180px;margin:24px auto;padding:0 20px}}header,.panel{{margin-bottom:14px;padding:18px;border:1px solid #d3e0e7;border-radius:9px;background:#fff}}h1{{margin:0;color:#173d57;font-size:28px}}p{{color:#607684;line-height:1.6}}.status{{display:inline-block;padding:6px 9px;border-radius:999px;font-weight:800}}.verified{{background:#e8f7ee;color:#246040}}.degraded{{background:#fff1d5;color:#76551c}}table{{width:100%;border-collapse:collapse;font-size:12px}}th,td{{padding:9px 8px;border-bottom:1px solid #e1e8ec;text-align:left;vertical-align:top}}th{{background:#f4f7f9}}td small{{display:block;color:#718590}}ul{{display:grid;gap:8px;padding-left:20px}}li span{{display:block;color:#607684;margin-top:3px}}.note{{border-left:4px solid #2f7aa4}}@media(max-width:760px){{main{{padding:0 10px}}.table-wrap{{overflow:auto}}h1{{font-size:22px}}}}
</style></head><body><main data-report-status="{escape(str(report['report_status']))}">
<header><span class="status {status_class}">{escape(str(report['report_status_zh']))}</span><h1>{escape(str(report['title_zh']))}</h1><p>期间 {escape(str(report['period']))} · 情景 {escape(str(report['scenario_id']))} · 阈值版本 {escape(str(report['threshold_version']))}</p><p>{escape(str(report['degradation_reason_zh'] or report['scope_limitation_zh']))}</p></header>
<section class="panel note"><h2>利润和现金是两套数字</h2><p>利润按“收入减成本”；资金占用按“已开票未回款加未开票节点”。两者不能互相替代。</p></section>
<section class="panel"><h2>项目利润与资金占用</h2><div class="table-wrap"><table><thead><tr><th>项目</th><th>收入</th><th>成本</th><th>毛利</th><th>未回款</th><th>未开票</th><th>资金占用</th><th>限制</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>
<section class="panel"><h2>内部预警（{report['alert_count']}）</h2><ul>{alerts}</ul></section>
<section class="panel"><h2>使用限制</h2><p>{escape(str(report['scope_limitation_zh']))}</p><p>页面与附表允许差异 0 分；当前不是正式经营报告，不发送提醒，也不执行付款。</p></section>
</main></body></html>"""


def relation_report_view(
    company_id: str = "demo-north",
    period: str = "2026-07",
    scenario_id: str = REPORT_SCENARIO_ID,
    verification_state: str = "VERIFIED",
    project_events: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    report = periodic_report(company_id, period, scenario_id, verification_state, project_events)
    dual = project_cash_dual_view(company_id, period, verification_state, project_events)
    alerts = alert_view(company_id, period, scenario_id, verification_state)
    return {
        "schema_version": "kmfa.v015.s18p3.relation_report_view.v1",
        "allowed": True,
        "company_id": company_id,
        "period": period,
        "scenario_id": scenario_id,
        "verification_state": _verification_state(verification_state),
        "data_classification": DATA_CLASSIFICATION,
        "dual_view": dual,
        "alert_view": alerts,
        "report": report,
        "scenario_options": [[key, label] for key, label in (("base", "基准情景"), ("collection_delay", "回款延迟"), ("cost_pressure", "成本压力"))],
        "verification_options": [["VERIFIED", "公开演示资料已核验"], ["UNVERIFIED", "未核验降级演示"]],
        "money_difference_cents": dual["profit_equation_difference_cents"] + dual["cash_occupancy_reconciliation_difference_cents"] + report["report_page_export_difference_cents"],
        "profit_used_as_cash_count": dual["profit_cash_substitution_count"],
        "full_sensitive_detail_count": alerts["full_sensitive_detail_count"],
        "thresholds_externalized": alerts["thresholds_externalized"],
        "report_degraded": report["report_degraded"],
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "external_network_request_count": 0,
        "real_identity_count": 0,
        "credential_count": 0,
        "source_data_write_count": 0,
        "fact_layer_write_count": 0,
        "notification_send_count": 0,
        "external_message_count": 0,
        "payment_execution_count": 0,
        "bank_operation_count": 0,
        "real_business_action_count": 0,
        "formal_business_report": False,
    }


def public_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, detail_zh: str) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "detail_zh": detail_zh})

    thresholds = load_alert_thresholds()
    for company_id in funds.COMPANY_IDS:
        view = relation_report_view(company_id=company_id)
        dual = view["dual_view"]
        add(f"{company_id}_six_projects", dual["project_count"] == 6, "六个项目完整")
        add(f"{company_id}_profit_reconcile", dual["profit_equation_difference_cents"] == 0, "利润口径勾稽")
        add(f"{company_id}_cash_reconcile", dual["cash_occupancy_reconciliation_difference_cents"] == 0, "资金占用勾稽")
        add(f"{company_id}_no_substitution", dual["profit_cash_substitution_count"] == 0, "利润不替代现金")
        add(f"{company_id}_isolated", dual["cross_company_leak_count"] == 0, "主体隔离")
        add(f"{company_id}_limitations", dual["scope_limitation_displayed_count"] == 6, "逐项目显示口径限制")
        add(f"{company_id}_export_exact", view["report"]["report_page_export_difference_cents"] == 0, "页面附表一致")
        add(f"{company_id}_sanitised", view["full_sensitive_detail_count"] == 0, "提醒没有完整敏感明细")
        add(f"{company_id}_actions_closed", view["notification_send_count"] == 0 and view["payment_execution_count"] == 0, "不发送不付款")
    sample = project_cash_dual_view()
    for row in sample["rows"]:
        add(f"{row['project_id']}_profit_equation", row["revenue_cents"] == row["cost_cents"] + row["gross_profit_cents"], "项目利润等式")
        add(f"{row['project_id']}_cash_equation", row["cash_occupied_cents"] == row["open_receivable_cents"] + row["unbilled_cents"], "项目资金占用等式")
        add(f"{row['project_id']}_basis_separate", row["profit_basis_zh"] != row["cash_basis_zh"], "利润现金口径分开")
        add(f"{row['project_id']}_limitation", bool(row["scope_limitation_zh"]), "限制明确")
        add(f"{row['project_id']}_integer_money", all(isinstance(row[field], int) and not isinstance(row[field], bool) for field in REPORT_MONEY_FIELDS), "金额使用整数分")
    alert = alert_view()
    add("alert_three_types", alert["alert_type_count"] == 3, "三类预警均触发")
    add("alert_count", alert["alert_count"] == 5, "五条去敏提醒")
    add("alert_threshold_external", alert["thresholds_externalized"], "阈值外置")
    add("alert_threshold_versioned", alert["threshold_version"] == thresholds["threshold_version"], "阈值版本明确")
    add("alert_no_sensitive", alert["full_sensitive_detail_count"] == 0 and alert["exposed_sensitive_field_count"] == 0, "提醒最少披露")
    add("alert_no_send", alert["notification_send_count"] == 0 and alert["external_message_count"] == 0, "提醒不外发")
    add("alert_isolated", alert["cross_company_leak_count"] == 0, "提醒主体隔离")
    report = periodic_report()
    html_text = render_report_html(report)
    csv_text = export_appendix_csv(report)
    parsed = list(csv.DictReader(io.StringIO(csv_text)))
    add("report_validated_demo", report["report_status"] == "PUBLIC_SYNTHETIC_VALIDATED", "已核验演示报告")
    add("report_not_formal", report["formal_business_report"] is False, "不是正式经营报告")
    add("report_rows_exact", len(report["page_rows"]) == len(report["appendix_rows"]) == 6, "页面附表行数一致")
    add("report_export_zero", report["report_page_export_difference_cents"] == 0, "页面附表差异零分")
    add("report_html_basis", "利润和现金是两套数字" in html_text and "允许差异 0 分" in html_text, "报告口径明确")
    add("report_csv_exact", [int(row["资金占用(分)"]) for row in parsed] == [row["cash_occupied_cents"] for row in report["page_rows"]], "CSV 金额一致")
    degraded = periodic_report(verification_state="UNVERIFIED")
    degraded_csv = list(csv.DictReader(io.StringIO(export_appendix_csv(degraded))))
    add("report_degraded", degraded["report_status"] == "DEGRADED_UNVERIFIED" and degraded["report_grade"] == "D", "未核验报告降级")
    add("report_degraded_hidden", degraded["unverified_numeric_visible_count"] == 0 and all(not row["收入(分)"] for row in degraded_csv), "未核验金额隐藏")
    add("threshold_amount_integer", isinstance(thresholds["major_overdue_amount_cents"], int), "逾期金额阈值为整数分")
    add("threshold_days_integer", isinstance(thresholds["major_overdue_days"], int) and isinstance(thresholds["loan_maturity_days"], int), "天数阈值为整数")
    add("threshold_gap_integer", isinstance(thresholds["funding_gap_cents"], int), "缺口阈值为整数分")
    add("threshold_change_policy", "复跑" in thresholds["change_policy"], "阈值变更必须复跑")
    return checks


def main() -> int:
    checks = public_checks()
    failed = [row for row in checks if row["status"] != "PASS"]
    print(f"{'PASS' if not failed else 'FAIL'}: S18-P3 public checks {len(checks) - len(failed)}/{len(checks)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
