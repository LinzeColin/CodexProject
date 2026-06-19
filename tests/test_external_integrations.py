from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from quantlab.integrations import (
    build_personal_profile,
    collect_industry_reports,
    external_system_status,
    filter_industry_reports,
    holdings_summary,
    load_holdings_frame,
)


def test_industry_reports_are_indexed_and_filtered_by_date_and_keyword():
    with TemporaryDirectory() as tmp:
        root = Path(tmp) / "行研报告" / "6月第1周 0106-0706"
        root.mkdir(parents=True)
        (root / "1. 盘前报告_03062026.pdf").write_bytes(b"%PDF-1.4")
        (root / "4. K线分析报告_03062026.pdf").write_bytes(b"%PDF-1.4")

        reports = collect_industry_reports(root.parent)
        filtered = filter_industry_reports(reports, "2026-06-03", "2026-06-03", "K线")

        assert len(reports) == 2
        assert len(filtered) == 1
        assert filtered.iloc[0]["category"] == "K线"
        assert filtered.iloc[0]["report_date"] == "2026-06-03"


def test_holdings_are_loaded_from_consumer_and_quantlab_sources():
    with TemporaryDirectory() as tmp:
        consumer = Path(tmp) / "consumer"
        quantlab = Path(tmp) / "quantlab"
        consumer.mkdir()
        quantlab.mkdir()
        pd.DataFrame(
            [
                {"代码": "600519.SH", "名称": "贵州茅台", "市场": "CN", "持仓金额": 70000, "权重": 0.70},
            ]
        ).to_csv(consumer / "holdings.csv", index=False)
        pd.DataFrame(
            [
                {"symbol": "AAPL", "name": "Apple", "market": "US", "position_value": 30000, "weight": 0.30},
            ]
        ).to_excel(quantlab / "holdings.xlsx", index=False)

        holdings = load_holdings_frame(consumer_dirs=[consumer], quantlab_dirs=[quantlab])
        summary = holdings_summary(holdings)

        assert len(holdings) == 2
        assert set(holdings["source_system"]) == {"消费行为分析系统", "量化回测系统"}
        assert summary["holding_count"] == 2
        assert round(summary["top1_weight"], 2) == 0.70


def test_personal_profile_marks_missing_holdings_and_evidence_risk():
    runs = pd.DataFrame(
        [
            {"research_status": "NeedsMoreEvidence", "missing_evidence_count": 2},
            {"research_status": "ContinueResearch", "missing_evidence_count": 0},
        ]
    )
    reviews = pd.DataFrame([{"executed_as_planned": False, "news_impulse": True, "discipline_violation": True}])
    tasks = pd.DataFrame([{"status": "待验证"}, {"status": "待验证"}, {"status": "待验证"}])

    profile = build_personal_profile(pd.DataFrame(), runs=runs, reviews=reviews, validation_tasks=tasks)

    risk_text = " ".join(item["风险"] for item in profile["risks"])
    suggestion_text = " ".join(item["建议"] for item in profile["suggestions"])
    assert "持仓数据缺失" in risk_text
    assert "证据链不完整" in risk_text
    assert "配置持仓数据" in suggestion_text


def test_external_system_status_reports_ready_and_needs_config():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        industry = root / "industry"
        consumer = root / "consumer"
        quantlab = root / "quantlab"
        industry.mkdir()
        consumer.mkdir()
        (industry / "盘前报告_03062026.pdf").write_bytes(b"%PDF-1.4")
        pd.DataFrame([{"symbol": "AAPL", "position_value": 1}]).to_csv(consumer / "holdings.csv", index=False)

        status = external_system_status(industry_report_root=industry, consumer_dirs=[consumer], quantlab_dirs=[quantlab])

        assert set(status["status"]) == {"Ready", "NeedsConfig"}
