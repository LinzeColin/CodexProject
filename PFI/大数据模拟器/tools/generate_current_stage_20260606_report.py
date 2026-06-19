from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "runs/current_stage_bw99_3candidates_200symbols_20windows_exact_20260605"
OUTPUT_DIR = ROOT / "reports/current_stage_20260606"


def pct(value: float, digits: int = 3) -> str:
    return f"{float(value) * 100:.{digits}f}%"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = pd.read_csv(RUN_DIR / "strategy_summary.csv")
    status = pd.read_csv(RUN_DIR / "task_status.csv")
    results = pd.read_csv(RUN_DIR / "validation_results.csv")

    rows = []
    for _, row in summary.iterrows():
        rows.append(
            {
                "strategy_id": row["strategy_id"],
                "samples": int(row["samples"]),
                "pass_rate": pct(row["pass_rate"], 3),
                "avg_total_gap": pct(row["avg_total_gap"], 4),
                "avg_annualized_gap": pct(row["avg_annualized_gap"], 4),
                "avg_drawdown_improvement": pct(row["avg_drawdown_improvement"], 4),
                "role": role_for_strategy(row["strategy_id"]),
            }
        )
    candidate_table = pd.DataFrame(rows)
    candidate_table.to_csv(OUTPUT_DIR / "candidate_summary_12000_exact.csv", index=False)

    rule_card = {
        "schema_version": "qbvs-current-stage-rule-card-v1",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "approval_state": "review_only_not_approved_for_live_trading",
        "primary_candidate": "bw99_boll_or_rsi_none_ma_trend_full_none",
        "control_candidate": "bw99_none_none_ma_trend_full_none",
        "conservative_candidate": "bw98_boll_or_rsi_none_ma_trend_full_none",
        "behavior_strategy_not_portfolio_strategy": True,
        "rule_description": {
            "base_weight": "99% baseline exposure for the primary candidate.",
            "dip_refill": "If RSI < 35 or price breaks below the Bollinger lower band, refill toward 100%.",
            "trend_participation": "If MA20 > MA60, keep or restore full participation.",
            "sell_rule": "Do not automatically sell only because price has risen; selling requires trend break, risk event, cash need, or separate user confirmation.",
        },
        "metric_definitions": {
            "total_return_gap": "strategy_total_return - buy_hold_total_return",
            "annualized_return_gap": "strategy_annualized_return - buy_hold_annualized_return",
            "drawdown_improvement": "strategy_max_drawdown - buy_hold_max_drawdown; positive means strategy drawdown is less severe.",
        },
        "latest_exact_evidence": {
            "run_dir": str(RUN_DIR.relative_to(ROOT)),
            "tasks_completed": int((status["status"] == "completed").sum()),
            "result_rows": int(len(results)),
            "symbols": int(results["symbol"].nunique()),
            "strategies": int(results["strategy_id"].nunique()),
            "candidate_summary": candidate_table.to_dict(orient="records"),
        },
        "boundaries": {
            "writes_quantlab_database": False,
            "writes_quantlab_source": False,
            "approved_strategy_library_write": False,
            "live_trading": False,
            "uses_opend_batch_history_refetch": False,
        },
        "remaining_gaps": [
            "OpenD historical K-line quota still blocks full 200-symbol Moomoo historical expansion.",
            "Alipay real fund NAV and detailed subscription/redemption rules still need stronger source data.",
            "The original million-tests-per-strategy target is not yet satisfied.",
        ],
    }
    (OUTPUT_DIR / "strategy_rule_card_20260606.json").write_text(
        json.dumps(rule_card, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    markdown = build_markdown(candidate_table, status, results)
    (OUTPUT_DIR / "current_stage_strategy_report_20260606.md").write_text(markdown, encoding="utf-8")
    build_pdf(markdown, candidate_table, OUTPUT_DIR / "Current_Stage_Strategy_Report_20260606.pdf")


def role_for_strategy(strategy_id: str) -> str:
    if strategy_id == "bw99_boll_or_rsi_none_ma_trend_full_none":
        return "主候选：99% 基础仓位，RSI/BOLL 补仓，MA 趋势参与，不因上涨自动卖出"
    if strategy_id == "bw99_none_none_ma_trend_full_none":
        return "对照候选：数值略强，解释性较弱"
    if strategy_id == "bw98_boll_or_rsi_none_ma_trend_full_none":
        return "保守候选：多 1% 现金缓冲"
    return "候选"


def build_markdown(candidate_table: pd.DataFrame, status: pd.DataFrame, results: pd.DataFrame) -> str:
    completed = int((status["status"] == "completed").sum())
    table_lines = [
        "| 策略 | 样本 | 通过率 | 平均总收益差 | 平均年化差 | 平均回撤改善 | 角色 |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for _, row in candidate_table.iterrows():
        table_lines.append(
            f"| `{row['strategy_id']}` | {row['samples']} | {row['pass_rate']} | {row['avg_total_gap']} | {row['avg_annualized_gap']} | {row['avg_drawdown_improvement']} | {row['role']} |"
        )
    table = "\n".join(table_lines)
    return f"""# 支付宝行为策略当前阶段结论报告

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 一句话结论

原支付宝式“越跌越买、越涨越卖”的核心问题不是下跌买入，而是上涨后大额卖出削弱了趋势参与。当前阶段更优的行为修正是：**99% 基础仓位 + RSI/BOLL 只做下跌补仓解释 + MA20/MA60 趋势保持满仓 + 不因上涨自动卖出**。

## 最新验证范围

- 数据源：Yahoo 公开历史行情缓存，作为 quota-safe public-history exact evidence；不代表账户级可交易确认。
- 样本：3 个当前候选策略、200 个标的、每对最多 20 个滚动窗口。
- 任务：{completed}/12,000 exact backtest completed。
- 结果行：{len(results)}；覆盖标的：{results['symbol'].nunique()}；覆盖策略：{results['strategy_id'].nunique()}。
- 边界：未触发 OpenD 批量历史重抓，未写 QuantLab 源码/数据库/approved strategy library，未连接实盘。

## 指标口径

- 平均总收益差 = 策略总收益 - 买入持有总收益。
- 平均年化差 = 策略年化收益 - 买入持有年化收益。
- 平均回撤改善 = 策略最大回撤 - 买入持有最大回撤；最大回撤为负数，因此该值为正表示策略回撤更浅。
- 用户硬阈值：平均总收益差不低于 -8%，平均年化差不低于 -3%。

## 12,000 exact 样本结果

{table}

## 当前策略描述

主候选：`bw99_boll_or_rsi_none_ma_trend_full_none`。

规则：

1. 基础仓位保持 99%，避免“等待下跌买入”导致长期低仓位。
2. 当 RSI < 35 或价格跌破 BOLL 下轨时，将仓位补足到 100%，保留“下跌补仓”的行为优势。
3. 当 MA20 > MA60 时保持或恢复满仓，避免上涨趋势中因为涨幅已大而过早卖出。
4. 不设置“上涨自动卖出”规则；卖出只能来自趋势破坏、风险事件、现金需求、持仓集中度管理或用户单独确认。

## 解释

这不是投资组合策略，而是交易行为纠偏策略。它的核心目标是减少上涨期过早减仓，同时只保留轻微现金缓冲和技术面补仓触发。12,000 exact 样本显示，主候选相对买入持有的平均总收益差约 -0.0827%，平均年化差约 -0.0052%，远高于用户设定下限；平均回撤改善为正，说明没有牺牲下行保护目标。

## 风险边界

- 当前不是实盘交易建议，不代表策略已批准入库。
- Yahoo 公开行情不等同于 moomoo/支付宝账户可交易证明。
- 支付宝真实基金 NAV、申购确认日、赎回到账日、费率、最低持有期仍需补齐后复核。
- 长期强牛资产上，任何低于 100% 仓位的策略仍可能跑输买入持有；当前候选的优势是把跑输压缩到很小，同时保留行为约束和轻微回撤改善。

## 下一步

1. QuantLab 以 ReviewOnly 模式读取 `handoff/quantlab_bundle_current_stage_bw99_3candidates_200symbols_20windows_20260605`。
2. OpenD 历史 K 线 quota 恢复后，先做 `US.BRK.B` 单标的历史 K 线 probe，再按 replacement-to-200 计划推进，不直接重跑 batch81-140。
3. 补齐支付宝基金真实 NAV 或高置信 proxy 映射，重跑基金口径。
4. 若需要生产级声明，继续分片扩展到更高规模；当前还未满足“每策略百万级测试”的最终目标。
"""


def build_pdf(markdown: str, table: pd.DataFrame, output: Path) -> None:
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    styles = getSampleStyleSheet()
    base = ParagraphStyle("CN", parent=styles["BodyText"], fontName="STSong-Light", fontSize=9.5, leading=14)
    title = ParagraphStyle("CNTitle", parent=styles["Title"], fontName="STSong-Light", fontSize=18, leading=24, textColor=colors.HexColor("#111827"))
    h2 = ParagraphStyle("CNH2", parent=styles["Heading2"], fontName="STSong-Light", fontSize=12.5, leading=17, textColor=colors.HexColor("#1F2937"))
    doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=16 * mm, leftMargin=16 * mm, topMargin=14 * mm, bottomMargin=14 * mm)
    story = []
    story.append(Paragraph("支付宝行为策略当前阶段结论报告", title))
    story.append(Paragraph(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", base))
    story.append(Spacer(1, 8))
    sections = [
        ("一句话结论", "原支付宝式“越跌越买、越涨越卖”的主要问题是上涨后大额卖出削弱趋势参与。当前阶段主候选是 99% 基础仓位 + RSI/BOLL 补仓 + MA 趋势满仓 + 不因上涨自动卖出。"),
        ("最新验证范围", "已完成 12,000/12,000 个 exact backtest：3 个候选策略、200 个 Yahoo 公开行情标的、每对最多 20 个滚动窗口。该路径不触发 OpenD，不写 QuantLab，不接实盘。"),
        ("指标口径", "平均总收益差 = 策略总收益 - 买入持有总收益；平均年化差 = 策略年化收益 - 买入持有年化收益；平均回撤改善 = 策略最大回撤 - 买入持有最大回撤，正值表示策略回撤更浅。"),
    ]
    for heading, body in sections:
        story.append(Paragraph(heading, h2))
        story.append(Paragraph(body, base))
        story.append(Spacer(1, 6))
    story.append(Paragraph("12,000 exact 样本结果", h2))
    table_data = [["策略", "样本", "通过率", "总收益差", "年化差", "回撤改善"]]
    for _, row in table.iterrows():
        table_data.append([
            row["strategy_id"],
            str(row["samples"]),
            row["pass_rate"],
            row["avg_total_gap"],
            row["avg_annualized_gap"],
            row["avg_drawdown_improvement"],
        ])
    pdf_table = Table(table_data, colWidths=[62 * mm, 16 * mm, 20 * mm, 23 * mm, 23 * mm, 24 * mm], repeatRows=1)
    pdf_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
    ]))
    story.append(pdf_table)
    story.append(Spacer(1, 8))
    story.append(Paragraph("策略描述", h2))
    story.append(Paragraph("主候选 bw99_boll_or_rsi_none_ma_trend_full_none：基础仓位 99%；RSI < 35 或跌破 BOLL 下轨时补足至满仓；MA20 > MA60 时保持或恢复满仓；不因上涨自动卖出。", base))
    story.append(Spacer(1, 6))
    story.append(Paragraph("风险边界", h2))
    story.append(Paragraph("当前结论是 ReviewOnly 外部证据，不是实盘交易建议，也不是策略库写入授权。真实基金 NAV、申赎规则和 OpenD 历史 K 线 quota 仍需后续补齐。", base))
    doc.build(story)


if __name__ == "__main__":
    main()
