from __future__ import annotations

from src.config import ROOT
from src.models import Source
from src.reporting.account_dashboard import account_dashboard
from src.reporting.charts import market_structure_charts
from src.reporting.analysis import (
    catalyst_risk_event_table,
    comparison_backtest,
    counter_thesis,
    daily_operation_rule_checklist,
    daily_session_analysis,
    decision_signal_quality_matrix,
    discipline_check,
    fact_inference_opinion,
    multi_dimensional_analysis,
    position_action_recommendations,
    pfi_os_validation_queue,
    report_meta,
    research_confidence_table,
    risk_explanation,
    volume_explanation,
)
from src.reporting.naming import daily_report_name
from src.reporting.renderer import format_percent, render_template, toc_for, write_report_bundle, write_source_log


DAILY_SESSIONS = {
    "pre_open": {
        "name": "开盘前",
        "task": "- 目标：形成开盘后的事实核验与观察计划。\n- 重点：隔夜信息、自选池强弱、开盘后是否需要进一步验证。\n- 原则：只给研究计划，不把盘前推断写成事实或最终操作依据。",
    },
    "midday": {
        "name": "盘中停盘",
        "task": "- 目标：验证早盘观察，修正下午研究判断。\n- 重点：早盘线索是否兑现、成交/涨跌是否背离、下午是否需要等待收盘确认。\n- 原则：先复盘早盘，再给下午观察结论和验证缺口。",
    },
    "post_close": {
        "name": "盘后分析",
        "task": "- 目标：验证早盘与盘中判断，并沉淀改进规则。\n- 重点：命中/失效原因、误判来源、明日改进。\n- 原则：把复盘结论反馈到下一期开盘前报告。",
    },
}


def generate_daily_report(
    as_of: str,
    session: str,
    factors: list[dict[str, object]],
    events: list[dict[str, str]],
    advice: list[dict[str, object]],
    signals: list[dict[str, object]],
    positions: list[dict[str, object]],
    exposure: dict[str, object],
    risk_logs: list[str],
    health_logs: list[str],
    sources: list[Source],
    account_summary: dict[str, object],
) -> str:
    session_config = DAILY_SESSIONS[session]
    report = render_template(
        ROOT / "01_templates" / "每日市场更新模板.md",
        {
            "date": as_of,
            "session_name": session_config["name"],
            "report_meta": report_meta(as_of, session),
            "toc": toc_for(
                [
                    "一、仓位操作建议",
                    "二、盘前 / 盘中 / 盘后对比复盘",
                    "三、关键事实、事件与市场结构",
                    "四、研究可信度与 PFIOS 验证",
                    "五、操作纪律与反方校验",
                    "六、技术面、基本面、价值面综合结论",
                    "七、收盘执行规则与风控",
                    "八、持仓与支付宝历史交易附图",
                ]
            ),
            "position_action_recommendations": position_action_recommendations(session, advice, factors, account_summary, events, as_of),
            "signal_quality_matrix": decision_signal_quality_matrix(factors, advice, as_of),
            "account_dashboard": account_dashboard(as_of, f"daily_{session}", account_summary, advice),
            "fact_inference_opinion": fact_inference_opinion(factors, events, advice, account_summary),
            "research_confidence": research_confidence_table(factors, advice, events, as_of),
            "catalyst_risk_events": catalyst_risk_event_table(events, factors, as_of),
            "volume_explanation": volume_explanation(),
            "market_structure_charts": market_structure_charts(factors, as_of, f"daily_{session}"),
            "operation_rule_checklist": daily_operation_rule_checklist(session, factors, advice, account_summary, as_of),
            "session_analysis": daily_session_analysis(session, factors, advice),
            "comparison_backtest": comparison_backtest(session, factors, advice, as_of),
            "portfolio_risk": (
                f"- 行业暴露：{exposure['industry_exposure']}\n"
                f"- 现金权重：{format_percent(float(exposure['cash_weight']))}\n"
                f"{risk_explanation()}\n"
                f"- 风控日志：{'；'.join(risk_logs)}\n"
                f"- 监控日志：{'；'.join(health_logs)}"
            ),
            "discipline_check": discipline_check(account_summary, advice, exposure),
            "counter_thesis": counter_thesis(advice, factors),
            "pfi_os_queue": pfi_os_validation_queue(factors, advice, as_of),
            "multi_dimensional_analysis": multi_dimensional_analysis(factors, events),
        },
    )
    report_name = daily_report_name(session, as_of)
    write_source_log(report_name, sources, {"session": session, "report_type": "daily", "event_sources": _event_sources(events)})
    return str(write_report_bundle(report_name, report)["pdf"])


def _event_sources(events: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    rows = []
    for event in events:
        key = (event.get("source_name", ""), event.get("source_url", ""))
        if key in seen:
            continue
        seen.add(key)
        rows.append({"source_name": key[0], "source_url": key[1]})
    return rows


def _final_action_rows(advice: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        advice,
        key=lambda row: (
            0 if "卖" in str(row.get("Position", "")) or "止盈" in str(row.get("Position", "")) else 1 if "买" in str(row.get("Position", "")) else 2,
            -float(row.get("Volume") or 0),
        ),
    )
