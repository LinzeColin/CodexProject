from __future__ import annotations

from src.config import ROOT
from src.llm_router import LLMRouter
from src.models import Source
from src.reporting.account_dashboard import account_dashboard
from src.reporting.analysis import account_overview
from src.reporting.renderer import render_template, table, write_report_bundle, write_source_log


def generate_industry_report(
    industry: str,
    as_of: str,
    factors: list[dict[str, object]],
    events: list[dict[str, str]],
    sources: list[Source],
    account_summary: dict[str, object] | None = None,
) -> str:
    safe_industry = industry.replace("/", "_")
    industry_factors = [item for item in factors if item.get("industry") == industry]
    industry_events = [item for item in events if item.get("industry") == industry and item["date"] <= as_of]
    router = LLMRouter.from_config()
    view = router.generate(
        prompt=(ROOT / "00_prompts" / "行业周报_prompt.md").read_text(encoding="utf-8"),
        context={"factors": industry_factors, "events": industry_events, "signals": []},
    )
    report = render_template(
        ROOT / "01_templates" / "行业周报模板.md",
        {
            "industry": industry,
            "date": as_of,
            "account_overview": account_overview(account_summary or {}),
            "account_dashboard": account_dashboard(as_of, f"industry_{safe_industry}", account_summary or {}, []),
            "view": view,
            "industry_performance": table(
                industry_factors,
                ["symbol", "name", "close", "momentum_5d", "volatility_5d", "volume_ratio_5d"],
            ),
            "supply_demand": table(industry_events, ["type", "title", "summary", "impact"]),
            "valuation": table(industry_factors, ["symbol", "pe", "pb", "roe", "revenue_growth", "net_profit_growth"]),
            "risks": "- 估值高位回落风险\n- 订单兑现低于预期风险\n- 行业政策或贸易限制变化风险",
            "strategy_review": "- 当前报告需结合 PFIOS 验证、纸面跟踪和后续事实复盘持续校验；证据不足时只保留为研究观察。",
        },
    )
    report_name = f"行业报告_{safe_industry}_{as_of}"
    write_source_log(report_name, sources, {"report_type": "industry", "industry": industry})
    return str(write_report_bundle(report_name, report)["pdf"])
