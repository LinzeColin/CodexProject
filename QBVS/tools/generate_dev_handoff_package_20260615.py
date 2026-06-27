from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports/dev_handoff_package_20260615"
EVIDENCE_DIR = OUT_DIR / "evidence"
RUN_DIR = ROOT / "runs/current_stage_bw99_random_stress_20260606"
READINESS_DIR = ROOT / "runs/goal_readiness_audit_random_stress_50k_20260606"
RANDOM_REPORT_DIR = ROOT / "reports/random_stress_progress_20260606"
CURRENT_STAGE_DIR = ROOT / "reports/current_stage_20260606"
BUNDLE_DIR = ROOT / "handoff/quantlab_bundle_current_stage_bw99_3candidates_200symbols_20windows_20260605"


def pct(value: float, digits: int = 4) -> str:
    return f"{float(value) * 100:.{digits}f}%"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    status = read_json(RUN_DIR / "campaign_status.json")
    readiness = read_json(READINESS_DIR / "goal_readiness_audit.json")
    progress_report = read_json(RANDOM_REPORT_DIR / "random_stress_progress_report.json")
    summary = pd.read_csv(RUN_DIR / "strategy_summary.csv")
    regime = pd.read_csv(RANDOM_REPORT_DIR / "random_stress_regime_summary.csv")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_samples = min(status["per_strategy_samples"].values())
    progress = current_samples / status["target_paths_per_strategy"]
    primary_id = "bw99_boll_or_rsi_none_ma_trend_full_none"
    primary = summary.loc[summary["strategy_id"] == primary_id].iloc[0].to_dict()
    readiness_score = readiness["score"]
    regime_min = float(regime["mean"].min())

    context = {
        "created_at": now,
        "root": str(ROOT),
        "out_dir": rel(OUT_DIR),
        "status": status,
        "readiness_score": readiness_score,
        "primary_strategy_id": primary_id,
        "primary": primary,
        "progress": progress,
        "regime_min_pass_rate": regime_min,
    }

    docs = build_docs(context, summary, readiness)
    for filename, text in docs.items():
        (OUT_DIR / filename).write_text(text, encoding="utf-8")

    copied = copy_evidence()
    manifest = {
        "schema_version": "qbvs-dev-handoff-package-v1",
        "created_at": now,
        "package_dir": str(OUT_DIR),
        "zip_path": str(OUT_DIR.with_suffix(".zip")),
        "source_root": str(ROOT),
        "audience": ["ChatGPT review", "new developers", "users/operators"],
        "current_status": {
            "random_stress_batches": status["completed_batches"],
            "random_stress_needed_batches": status["needed_batches"],
            "samples_per_strategy": status["per_strategy_samples"],
            "random_stress_progress": progress,
            "readiness_percent": readiness_score["readiness_percent"],
            "readiness_passed": readiness_score["passed"],
            "readiness_partial": readiness_score["partial"],
            "readiness_blocked": readiness_score["blocked"],
            "readiness_missing": readiness_score["missing"],
            "writes_quantlab_database": status["writes_quantlab_database"],
            "writes_quantlab_source": status["writes_quantlab_source"],
            "live_trading": status["live_trading"],
            "uses_opend": status["uses_opend"],
        },
        "core_documents": sorted(docs),
        "copied_evidence": copied,
        "next_recommended_action": "Continue resumable synthetic stress from 100/200 to 200/200 batches, then produce final full report; do not run OpenD batch history until quota is confirmed.",
    }
    (OUT_DIR / "package_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    build_pdf(context, summary, readiness, OUT_DIR / "QBVS_Development_Handoff_Package_20260615.pdf")
    write_zip(OUT_DIR, OUT_DIR.with_suffix(".zip"))
    print(json.dumps({"package_dir": str(OUT_DIR), "zip_path": str(OUT_DIR.with_suffix(".zip"))}, ensure_ascii=False, indent=2))


def build_docs(context: dict, summary: pd.DataFrame, readiness: dict) -> dict[str, str]:
    status = context["status"]
    primary = context["primary"]
    readiness_score = context["readiness_score"]
    common_header = (
        "# QBVS 独立交易行为验证系统交接包\n\n"
        f"生成时间：{context['created_at']}\n\n"
        f"项目根目录：`{context['root']}`\n\n"
    )

    executive = common_header + "\n".join([
        "## 一句话结论",
        "",
        "QBVS 已形成可独立运行的交易行为策略验证层，并与 QuantLab 建立 ReviewOnly 外部证据互通；当前 synthetic random stress 已完成 50%，整体 readiness 为 95%，尚未达到最终完成条件。",
        "",
        "## 当前核心状态",
        "",
        f"- 随机压力测试：{status['completed_batches']}/{status['needed_batches']} batch。",
        f"- 当前每策略随机路径：{min(status['per_strategy_samples'].values()):,}/{status['target_paths_per_strategy']:,}，进度 {context['progress']:.1%}。",
        f"- 总随机压力结果行数：{status['result_rows']:,}。",
        f"- readiness：{readiness_score['readiness_percent']:.2f}%；passed={readiness_score['passed']}，partial={readiness_score['partial']}，blocked={readiness_score['blocked']}，missing={readiness_score['missing']}。",
        f"- 主候选策略：`{context['primary_strategy_id']}`。",
        f"- 主候选当前表现：通过率 {pct(primary['pass_rate'])}，平均总收益差 {pct(primary['avg_total_gap'])}，平均年化差 {pct(primary['avg_annualized_gap'])}，平均回撤改善 {pct(primary['avg_drawdown_improvement'])}。",
        "",
        "## 边界",
        "",
        "- 不写 QuantLab 源码。",
        "- 不写 QuantLab 数据库。",
        "- 不写 approved strategy library。",
        "- 不接实盘、不下单。",
        "- OpenD 历史 K 线 quota 未确认前，不运行批量历史补抓。",
        "",
        "## 给 ChatGPT/审核者的审核重点",
        "",
        "1. 检查当前结论是否只被表述为 ReviewOnly research evidence，而不是投资建议或实盘指令。",
        "2. 检查 synthetic stress 与真实可交易市场验证之间是否被清楚区分。",
        "3. 检查 remaining gaps 是否覆盖百万级规模、支付宝真实基金 NAV、Moomoo/OpenD 真实历史数据、100 年跨周期和最终报告。",
        "4. 检查主候选规则是否解决原始问题：减少下跌亏损，同时不过度牺牲上涨参与。",
        "",
    ])

    dev = common_header + "\n".join([
        "## 新开发者接手指南",
        "",
        "### 主要目录",
        "",
        "- `qbvs/`：核心验证库，含策略、指标、回测、数据、质量、bundle、handshake、CLI。",
        "- `tools/`：一次性或阶段性报告/验证脚本。",
        "- `runs/current_stage_bw99_random_stress_20260606/`：当前随机压力测试 campaign 状态。",
        "- `reports/random_stress_progress_20260606/`：当前随机压力阶段报告。",
        "- `runs/goal_readiness_audit_random_stress_50k_20260606/`：最新 readiness audit。",
        "- `handoff/`：QuantLab ReviewOnly 证据包与握手文件。",
        "",
        "### 推荐续跑命令",
        "",
        "```bash",
        "cd /Users/linzezhang/Documents/Codex/2026-06-02/new-chat-2/outputs/quant_behavior_validation_system",
        "PYTHONPATH=. python3 tools/run_current_stage_random_stress_campaign.py --target-paths 100000 --batch-paths 500 --max-batches 20 --days 252 --output-dir runs/current_stage_bw99_random_stress_20260606",
        "PYTHONPATH=. python3 tools/generate_random_stress_progress_report_20260606.py",
        "PYTHONPATH=. python3 -m qbvs.cli verify-handshake --ack handoff/quantlab_handshake_ack.json",
        "PYTHONPATH=. python3 -m qbvs.cli verify-quantlab-bundle --bundle-dir handoff/quantlab_bundle_current_stage_bw99_3candidates_200symbols_20windows_20260605",
        "```",
        "",
        "### 不要做",
        "",
        "- 不要把 synthetic stress 结果写进 QuantLab 已审批策略库。",
        "- 不要在 OpenD quota 未确认时运行批量历史 K 线 refetch。",
        "- 不要把 Yahoo 公开行情等同于用户账户可交易证明。",
        "- 不要把候选策略表述为可直接执行的投资建议。",
        "",
    ])

    functions = common_header + "## 功能清单\n\n" + "\n".join([
        "- 交易行为策略族生成：已覆盖 200+ 个有意义的行为策略变体。",
        "- 技术指标结合：RSI/BOLL/MA/MACD/ATR 等用于补仓、趋势持有、风控和过滤。",
        "- exact public-history backtest：已完成 200 标的 x 200 策略的 40,000 pair 基线。",
        "- finalist 深度验证：当前主候选及对照组完成 200 标的、多窗口验证。",
        "- synthetic random stress：当前 3 个候选策略各 50,000 条随机路径。",
        "- 多市场/多资产候选 universe：含 Yahoo 公开行情、Moomoo/支付宝可交易模板。",
        "- Moomoo/OpenD 探测与 symbol alias：BRK-B provider symbol 已 snapshot-confirmed 为 US.BRK.B。",
        "- QuantLab 外部证据包：支持 ReviewOnly bundle、manifest、candidate strategy CSV、校验命令。",
        "- readiness audit：将用户目标拆成 passed/partial/blocked/missing。",
        "- PDF-first 报告：当前阶段报告、随机压力报告、readiness audit PDF。",
    ]) + "\n"

    task_rows = [
        ("已完成", "QuantLab ACK 握手", "valid=true，errors=[]"),
        ("已完成", "200 策略 x 200 标的 public-history 基线", "40,000 exact rows"),
        ("已完成", "主候选 20-window exact 验证", "12,000 exact tasks"),
        ("进行中", "synthetic random stress", "50,000/100,000 paths per strategy"),
        ("部分完成", "Moomoo/OpenD 真实历史数据", "snapshot/SDK/probe 层已做，历史 quota 未闭合"),
        ("部分完成", "支付宝真实基金 NAV", "已具备 CSV 标准化/规则口径，真实数据仍需补齐"),
        ("未完成", "百万级/极限规模", "readiness 中唯一 partial"),
        ("未完成", "最终完整报告", "需等 synthetic stress 与真实数据缺口收敛"),
    ]
    tasks = common_header + "## 任务清单与步骤环节\n\n| 状态 | 任务 | 当前证据/说明 |\n|---|---|---|\n"
    for row in task_rows:
        tasks += f"| {row[0]} | {row[1]} | {row[2]} |\n"
    tasks += "\n## 下一阶段推荐步骤\n\n1. 继续 synthetic stress 到 200/200 batch。\n2. 刷新随机压力 PDF/JSON/CSV 报告。\n3. 复跑 readiness audit。\n4. 若 OpenD quota 恢复，先做单标的历史 K 线确认，再做 quota-friendly replacement/200-symbol plan。\n5. 整合最终报告，保持 ReviewOnly 边界。\n"

    user = common_header + "\n".join([
        "## 使用者说明",
        "",
        "这个系统目前不是自动交易软件，也不是直接给买卖指令的策略库。它是一个外部验证系统，用来检验“越跌越买、越涨越卖”等交易行为规则在不同市场状态和压力环境下是否比买入持有更稳定。",
        "",
        "当前较强的候选方向是：保留低位补仓/回撤保护，但通过 MA 趋势持有和 RSI/BOLL 条件过滤，减少上涨阶段过早卖出的问题。",
        "",
        "使用者应看三类结果：",
        "",
        "- 收益差：平均总收益和年化收益不能明显落后买入持有。",
        "- 回撤改善：下跌或高波动时亏损应少于买入持有或至少不显著变差。",
        "- 通过率/压力测试：不同 regime 下是否稳定满足用户硬阈值。",
        "",
        "当前结论仍是阶段性研究结果，不能用于实盘下单。",
        "",
    ])

    risk = common_header + "\n".join([
        "## 风险与边界",
        "",
        "### 数据风险",
        "",
        "- Yahoo 公开行情不能证明用户账户真实可交易。",
        "- synthetic random stress 不能替代真实基金 NAV、真实股票/ETF/外汇/商品历史行情。",
        "- OpenD 历史 K 线 quota 未确认，真实 Moomoo 200 标的验证不能宣称完成。",
        "",
        "### 策略风险",
        "",
        "- 当前主候选是行为规则候选，不是投资组合建议。",
        "- 结果依赖成本模型、交易频率和可交易性假设。",
        "- 高通过率不等于未来收益保证。",
        "",
        "### 工程边界",
        "",
        "- 当前互通边界是 QuantLab ReviewOnly external evidence ingestion。",
        "- 任何写入 QuantLab 策略库、数据库、审批库或生产环境的动作都需要单独确认。",
        "",
    ])

    evidence = common_header + "\n".join([
        "## 证据索引",
        "",
        "| 类型 | 路径 | 用途 |",
        "|---|---|---|",
        f"| 当前状态 | `{rel(RUN_DIR / 'campaign_status.json')}` | random stress batch/sample 状态 |",
        f"| 策略摘要 | `{rel(RUN_DIR / 'strategy_summary.csv')}` | 当前 3 个候选指标 |",
        f"| 随机压力正式报告 | `{rel(RANDOM_REPORT_DIR / 'Random_Stress_Progress_Report_20260606.pdf')}` | PDF 正式进度报告 |",
        f"| readiness audit | `{rel(READINESS_DIR / 'Goal_Readiness_Audit_Report.pdf')}` | 目标完成度审计 |",
        f"| 当前阶段报告 | `{rel(CURRENT_STAGE_DIR / 'Current_Stage_Strategy_Report_20260606.pdf')}` | 主候选规则和 exact 结果 |",
        f"| 规则卡 | `{rel(CURRENT_STAGE_DIR / 'strategy_rule_card_20260606.json')}` | 主候选规则机器可读说明 |",
        f"| QuantLab ACK | `handoff/quantlab_handshake_ack.json` | QuantLab 只读握手确认 |",
        f"| QuantLab bundle | `{rel(BUNDLE_DIR)}` | ReviewOnly 外部证据包 |",
        f"| HANDOFF | `HANDOFF.md` | 长线程/换人续接入口 |",
        "",
    ])

    return {
        "00_README_FOR_CHATGPT_AND_REVIEWERS.md": executive,
        "01_DEVELOPER_HANDOFF.md": dev,
        "02_FUNCTION_INVENTORY.md": functions,
        "03_TASK_LIST_AND_ROADMAP.md": tasks,
        "04_USER_GUIDE.md": user,
        "05_RISKS_AND_BOUNDARIES.md": risk,
        "06_EVIDENCE_INDEX.md": evidence,
    }


def copy_evidence() -> list[str]:
    files = [
        ROOT / "HANDOFF.md",
        ROOT / "QUANTLAB_INTEGRATION_CONTRACT.json",
        ROOT / "HANDSHAKE_PROTOCOL.json",
        ROOT / "handoff/quantlab_handshake_ack.json",
        RANDOM_REPORT_DIR / "Random_Stress_Progress_Report_20260606.pdf",
        RANDOM_REPORT_DIR / "random_stress_progress_report.json",
        RANDOM_REPORT_DIR / "random_stress_strategy_summary.csv",
        RANDOM_REPORT_DIR / "random_stress_regime_summary.csv",
        READINESS_DIR / "Goal_Readiness_Audit_Report.pdf",
        READINESS_DIR / "goal_readiness_audit.json",
        READINESS_DIR / "goal_readiness_audit.csv",
        CURRENT_STAGE_DIR / "Current_Stage_Strategy_Report_20260606.pdf",
        CURRENT_STAGE_DIR / "strategy_rule_card_20260606.json",
        CURRENT_STAGE_DIR / "candidate_summary_12000_exact.csv",
        RUN_DIR / "campaign_status.json",
        RUN_DIR / "strategy_summary.csv",
        BUNDLE_DIR / "quantlab_bundle_manifest.json",
        BUNDLE_DIR / "quantlab_ingestion_payload.json",
        BUNDLE_DIR / "quantlab_candidate_strategies.csv",
    ]
    copied = []
    for source in files:
        if not source.exists():
            continue
        dest = EVIDENCE_DIR / source.name
        if dest.exists():
            dest.unlink()
        shutil.copy2(source, dest)
        copied.append(rel(dest))
    return copied


def build_pdf(context: dict, summary: pd.DataFrame, readiness: dict, output: Path) -> None:
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    styles = {
        "title": ParagraphStyle("title", fontName="STSong-Light", fontSize=18, leading=24, textColor=colors.HexColor("#111827"), spaceAfter=8),
        "h1": ParagraphStyle("h1", fontName="STSong-Light", fontSize=13, leading=18, textColor=colors.HexColor("#111827"), spaceBefore=8, spaceAfter=6),
        "body": ParagraphStyle("body", fontName="STSong-Light", fontSize=9.5, leading=14, textColor=colors.HexColor("#1f2937")),
        "small": ParagraphStyle("small", fontName="STSong-Light", fontSize=8, leading=11, textColor=colors.HexColor("#374151")),
    }
    doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=14 * mm, leftMargin=14 * mm, topMargin=14 * mm, bottomMargin=14 * mm)
    story = []
    story.append(Paragraph("QBVS 独立交易行为验证系统开发交接包", styles["title"]))
    story.append(Paragraph(f"生成时间：{context['created_at']}", styles["body"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("一页摘要", styles["h1"]))
    bullets = [
        "系统定位：QuantLab 外部 ReviewOnly 策略验证层，验证交易行为规则，不做实盘。",
        f"当前进度：random stress {context['status']['completed_batches']}/{context['status']['needed_batches']} batch；每策略 {min(context['status']['per_strategy_samples'].values()):,}/{context['status']['target_paths_per_strategy']:,} 条随机路径。",
        f"readiness：{context['readiness_score']['readiness_percent']:.2f}%，passed={context['readiness_score']['passed']}，partial={context['readiness_score']['partial']}，blocked={context['readiness_score']['blocked']}。",
        f"主候选：{context['primary_strategy_id']}；通过率 {pct(context['primary']['pass_rate'])}；平均总收益差 {pct(context['primary']['avg_total_gap'])}；年化差 {pct(context['primary']['avg_annualized_gap'])}；回撤改善 {pct(context['primary']['avg_drawdown_improvement'])}。",
        "核心边界：不写 QuantLab 源码/数据库/approved strategy library，不接实盘，不触发 OpenD 批量历史补抓。",
    ]
    for item in bullets:
        story.append(Paragraph("• " + item, styles["body"]))
    story.append(Paragraph("策略当前指标", styles["h1"]))
    table_data = [["策略", "样本", "通过率", "总收益差", "年化差", "回撤改善"]]
    for _, row in summary.iterrows():
        table_data.append([
            str(row["strategy_id"]),
            f"{int(row['samples']):,}",
            pct(row["pass_rate"]),
            pct(row["avg_total_gap"]),
            pct(row["avg_annualized_gap"]),
            pct(row["avg_drawdown_improvement"]),
        ])
    story.append(make_table(table_data, [64 * mm, 20 * mm, 22 * mm, 24 * mm, 24 * mm, 24 * mm]))
    story.append(Paragraph("功能清单", styles["h1"]))
    for item in [
        "200+ 交易行为策略族生成与反凑数审计。",
        "RSI/BOLL/MA/MACD/ATR 等技术指标组合验证。",
        "200 标的 x 200 策略 public-history exact baseline。",
        "候选策略多窗口 exact 验证与 synthetic random stress。",
        "QuantLab ReviewOnly handshake、bundle 导出与校验。",
        "PDF/JSON/CSV 报告和 readiness audit。",
    ]:
        story.append(Paragraph("• " + item, styles["body"]))
    story.append(PageBreak())
    story.append(Paragraph("任务清单与下一步", styles["h1"]))
    task_table = [
        ["状态", "任务", "说明"],
        ["完成", "QuantLab ACK 握手", "valid=true，errors=[]"],
        ["完成", "200x200 public-history 基线", "40,000 exact rows"],
        ["进行中", "synthetic random stress", "50,000/100,000 paths per strategy"],
        ["部分完成", "Moomoo/OpenD 真实历史数据", "历史 K 线 quota 未闭合"],
        ["部分完成", "支付宝真实基金 NAV", "需要补齐真实数据"],
        ["未完成", "最终完整报告", "需等主要缺口收敛"],
    ]
    story.append(make_table(task_table, [24 * mm, 50 * mm, 104 * mm]))
    story.append(Paragraph("风险与边界", styles["h1"]))
    for item in [
        "Yahoo 公开行情不能证明用户账户真实可交易。",
        "synthetic stress 不能替代真实基金 NAV 或真实 Moomoo/OpenD 历史行情。",
        "高通过率不等于未来收益保证。",
        "所有候选策略仍为研究证据，不是实盘投资建议。",
    ]:
        story.append(Paragraph("• " + item, styles["body"]))
    story.append(Paragraph("证据索引", styles["h1"]))
    for item in [
        "HANDOFF.md",
        "reports/random_stress_progress_20260606/Random_Stress_Progress_Report_20260606.pdf",
        "runs/goal_readiness_audit_random_stress_50k_20260606/Goal_Readiness_Audit_Report.pdf",
        "reports/current_stage_20260606/Current_Stage_Strategy_Report_20260606.pdf",
        "handoff/quantlab_bundle_current_stage_bw99_3candidates_200symbols_20windows_20260605/",
    ]:
        story.append(Paragraph("• " + item, styles["small"]))
    doc.build(story)


def make_table(data: list[list[str]], widths: list[float]) -> Table:
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def write_zip(source_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in source_dir.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(source_dir.parent))


if __name__ == "__main__":
    main()
