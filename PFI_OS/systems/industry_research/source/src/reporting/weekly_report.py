from __future__ import annotations

from src.config import ROOT
from src.models import Source
from src.reporting.account_dashboard import account_dashboard
from src.reporting.charts import market_structure_charts
from src.reporting.analysis import (
    catalyst_risk_event_table,
    counter_thesis,
    decision_signal_quality_matrix,
    discipline_check,
    fact_inference_opinion,
    position_action_recommendations,
    pfi_os_validation_queue,
    report_meta,
    research_confidence_table,
    strategy_sizing_basis,
    volume_explanation,
    weekly_composite_strategy_table,
    weekly_multi_dimensional_analysis,
    weekly_operation_synthesis,
    weekly_review,
)
from src.reporting.naming import weekly_report_name
from src.reporting.renderer import render_template, toc_for, write_report_bundle, write_source_log


WEEKLY_SESSIONS = {
    "monday_pre_open": {
        "name": "周一开盘前",
    },
    "friday_post_close": {
        "name": "周五关盘后",
    },
}


def generate_watchlist_weekly_report(
    as_of: str,
    session: str,
    watchlist: list[dict[str, str]],
    factors: list[dict[str, object]],
    events: list[dict[str, str]],
    advice: list[dict[str, object]],
    sources: list[Source],
    account_update_summary: str = "",
    account_summary: dict[str, object] | None = None,
) -> str:
    session_config = WEEKLY_SESSIONS[session]
    sorted_factors = sorted(
        factors,
        key=lambda item: float(item.get("daily_change_pct") or -999),
        reverse=True,
    )
    report = render_template(
        ROOT / "01_templates" / "自选周报模板.md",
        {
            "date": as_of,
            "week_session_name": session_config["name"],
            "report_meta": report_meta(as_of, session),
            "toc": toc_for(
                [
                    "一、仓位操作建议",
                    "二、周度对比复盘与优化结论",
                    "三、关键事实、事件与市场结构",
                    "四、研究可信度与 PFIOS 验证",
                    "五、操作纪律与反方校验",
                    "六、技术面、基本面、价值面综合结论",
                    "七、复合判断质量、策略胜率与风险清单",
                    "八、持仓与支付宝历史交易附图",
                ]
            ),
            "account_dashboard": account_dashboard(as_of, f"weekly_{session}", account_summary or {}, advice),
            "fact_inference_opinion": fact_inference_opinion(factors, events, advice, account_summary or {}),
            "research_confidence": research_confidence_table(factors, advice, events, as_of),
            "catalyst_risk_events": catalyst_risk_event_table(events, factors, as_of),
            "weekly_view": weekly_operation_synthesis(factors, events, advice, as_of),
            "performance_table": weekly_composite_strategy_table(sorted_factors, advice, events, as_of),
            "market_structure_charts": market_structure_charts(factors, as_of, f"weekly_{session}"),
            "weekly_multi_dimensional_analysis": weekly_multi_dimensional_analysis(factors, events),
            "advice_table": position_action_recommendations(session, advice, factors, account_summary or {}, events, as_of),
            "signal_quality_matrix": decision_signal_quality_matrix(factors, advice, as_of),
            "volume_explanation": volume_explanation(),
            "sizing_basis": strategy_sizing_basis(),
            "weekly_review": weekly_review(session, factors, advice, as_of),
            "discipline_check": discipline_check(account_summary or {}, advice, {}),
            "counter_thesis": counter_thesis(advice, factors),
            "pfi_os_queue": pfi_os_validation_queue(factors, advice, as_of),
            "risks": (
                "- 当前周报主要基于 moomoo 自选池、OpenD 行情快照和外部事件线索，A股部分标的受行情权限限制。\n"
                f"- 支付宝账户更新状态：{account_update_summary or '未提供。'}\n"
                "- 美股、A股、港股 ETF 和汇率类标的混合在同一自选池，需分别考虑交易时段、汇率和市场制度。\n"
                "- 缺行情标的仅列入观察，不升级为高可信研究。"
            ),
        },
    )
    report_name = weekly_report_name(session, as_of)
    write_source_log(report_name, sources, {"session": session, "report_type": "weekly", "event_sources": _event_sources(events)})
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
