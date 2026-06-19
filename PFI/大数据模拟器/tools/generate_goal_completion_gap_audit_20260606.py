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
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "reports/goal_completion_gap_audit_20260606"
READINESS = ROOT / "runs/goal_readiness_audit_quantlab_ack_20260605_from_quantlab_thread/goal_readiness_audit.json"
CURRENT_SUMMARY = ROOT / "runs/current_stage_bw99_3candidates_200symbols_20windows_exact_20260605/strategy_summary.csv"
CURRENT_REPORT = ROOT / "reports/current_stage_20260606/Current_Stage_Strategy_Report_20260606.pdf"
CURRENT_BUNDLE = ROOT / "handoff/quantlab_bundle_current_stage_bw99_3candidates_200symbols_20windows_20260605"


def pct(value: float, digits: int = 2) -> str:
    return f"{float(value) * 100:.{digits}f}%"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    readiness = json.loads(READINESS.read_text(encoding="utf-8"))
    current = pd.read_csv(CURRENT_SUMMARY)
    primary = current[current["strategy_id"].eq("bw99_boll_or_rsi_none_ma_trend_full_none")].iloc[0].to_dict()

    requirements = build_requirements(readiness, primary)
    requirements_frame = pd.DataFrame(requirements)
    requirements_frame.to_csv(OUTPUT_DIR / "goal_completion_gap_audit.csv", index=False)

    audit = {
        "schema_version": "qbvs-goal-completion-gap-audit-v1",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "overall_status": "active_not_complete",
        "blocked": False,
        "readiness_percent": readiness["score"]["readiness_percent"],
        "current_stage_primary_candidate": "bw99_boll_or_rsi_none_ma_trend_full_none",
        "current_stage_primary_evidence": {
            "samples": int(primary["samples"]),
            "pass_rate": float(primary["pass_rate"]),
            "avg_total_gap": float(primary["avg_total_gap"]),
            "avg_annualized_gap": float(primary["avg_annualized_gap"]),
            "avg_drawdown_improvement": float(primary["avg_drawdown_improvement"]),
            "passes_user_total_floor": bool(float(primary["avg_total_gap"]) >= -0.08),
            "passes_user_annualized_floor": bool(float(primary["avg_annualized_gap"]) >= -0.03),
        },
        "key_artifacts": {
            "readiness_audit": str(READINESS.relative_to(ROOT)),
            "current_stage_report_pdf": str(CURRENT_REPORT.relative_to(ROOT)),
            "current_stage_summary": str(CURRENT_SUMMARY.relative_to(ROOT)),
            "current_stage_quantlab_bundle": str(CURRENT_BUNDLE.relative_to(ROOT)),
        },
        "requirements": requirements,
        "next_shortest_path": [
            "Keep current-stage primary candidate in ReviewOnly state.",
            "Use the 12,000 exact sample report and bundle for QuantLab-side display/review.",
            "When OpenD historical quota recovers, probe US.BRK.B single-symbol history first, then replacement-to-200; do not blindly rerun batch81-140.",
            "Collect Alipay fund NAV/proxy mapping and subscription/redemption rules, then rerun fund-rule exact validation.",
            "Only after data gates are stable, schedule distributed/resumable scale campaigns toward the million-test target.",
        ],
        "writes_quantlab_database": False,
        "writes_quantlab_source": False,
        "live_trading": False,
    }
    (OUTPUT_DIR / "goal_completion_gap_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    markdown = build_markdown(audit, requirements_frame)
    (OUTPUT_DIR / "goal_completion_gap_audit.md").write_text(markdown, encoding="utf-8")
    build_pdf(audit, requirements_frame, OUTPUT_DIR / "Goal_Completion_Gap_Audit_20260606.pdf")


def build_requirements(readiness: dict, primary: dict) -> list[dict[str, str]]:
    return [
        row("读取 QuantLab 原版支付宝策略", "完成", "已读取原版 AlipayStrategy / AlipayEnhancedStrategy，并用本地场景验证用户诊断。", "保持只读；后续只做 ReviewOnly 候选。"),
        row("交易行为策略而非投资组合策略", "完成", "候选以 target-weight 行为规则表达：基础仓位、RSI/BOLL 补仓、MA 趋势参与、不因上涨自动卖出。", "QuantLab 展示时继续标注为 behavior strategy。"),
        row("平均总收益差不低于 -8%", "完成", f"主候选 12,000 exact run 中 avg_total_gap={pct(primary['avg_total_gap'], 4)}。", "基金 NAV 口径补齐后复核。"),
        row("平均年化差不低于 -3%", "完成", f"主候选 12,000 exact run 中 avg_annualized_gap={pct(primary['avg_annualized_gap'], 4)}。", "基金 NAV 口径补齐后复核。"),
        row("下跌保护/回撤改善", "完成", f"主候选 avg_drawdown_improvement={pct(primary['avg_drawdown_improvement'], 4)}，为正。", "在真实基金和 Moomoo 200 标的上继续复核。"),
        row("至少 200 个有效策略族", "完成", "readiness audit 显示 200 unique strategy_id，且目录反凑数审计已建立。", "后续不盲目扩充低价值目录。"),
        row("至少 200 个标的", "完成", "readiness audit 显示 200 unique symbols；current-stage 也覆盖 200 Yahoo 公开行情标的。", "替换为 Moomoo/Alipay confirmed tradable symbols。"),
        row("QuantLab 互通", "完成", "QuantLab ACK valid；当前 bundle 为 external_evidence_only，可供 ReviewOnly 读取。", "QuantLab 侧审批/展示由 QuantLab 主导。"),
        row("不修改数据库/只读边界", "完成", "所有新增产物位于 QBVS outputs；bundle 标记 writes_quantlab_database=false。", "策略库写入必须另行用户批准。"),
        row("支付宝真实基金口径", "部分完成", "已有交易行为画像和 proxy sensitivity；但真实基金 NAV、申赎规则、费率和到账延迟仍不完整。", "补齐 NAV/proxy mapping 后 rerun fund-rule exact validation。"),
        row("Moomoo/OpenD 真实 200 标的", "部分完成", "BRK-B provider code 已 snapshot-confirmed；但 OpenD 历史 K 线 quota 仍限制扩展。", "quota 恢复后先单标的 probe，再 replacement-to-200。"),
        row("每策略百万级/极限规模", "未完成", readiness["items"][7]["evidence"], "需要 distributed/resumable campaign；当前不应伪造生产级完成。"),
        row("100 年跨周期", "部分完成", "已做跨窗口公开历史验证；但受真实数据历史长度限制，不能把不足百年的资产伪装成 100 年验证。", "用可得长历史资产、事件窗口和随机压力测试补强。"),
        row("最终完整结论与成长报告", "部分完成", "已有 current-stage 中文 PDF、规则卡、QuantLab bundle；最终报告需等真实 NAV/OpenD/scale gates。", "保持阶段性报告，待数据门解除后生成最终生产级报告。"),
    ]


def row(requirement: str, status: str, evidence: str, next_action: str) -> dict[str, str]:
    return {
        "requirement": requirement,
        "status": status,
        "evidence": evidence,
        "next_action": next_action,
    }


def build_markdown(audit: dict, requirements: pd.DataFrame) -> str:
    lines = [
        "# QBVS 目标完成度缺口审计",
        "",
        f"生成时间：{audit['created_at']}",
        "",
        "## 当前结论",
        "",
        f"- 状态：{audit['overall_status']}；不严格 blocked。",
        f"- readiness：{audit['readiness_percent']:.2f}%。",
        "- 当前阶段主候选：`bw99_boll_or_rsi_none_ma_trend_full_none`。",
        "- 当前不能标记目标 complete：真实基金 NAV、OpenD 历史 quota、百万级规模仍未闭合。",
        "",
        "## 逐项审计",
        "",
        "| 需求 | 状态 | 证据 | 下一步 |",
        "|---|---|---|---|",
    ]
    for _, item in requirements.iterrows():
        lines.append(f"| {item['requirement']} | {item['status']} | {item['evidence']} | {item['next_action']} |")
    lines.extend([
        "",
        "## 下一步最短路径",
        "",
        "1. 当前主候选保持 ReviewOnly，不写策略库，不接实盘。",
        "2. QuantLab 读取 12,000 exact 样本 bundle 和当前阶段 PDF 进行展示/审批流对齐。",
        "3. OpenD quota 恢复后，只先做 `US.BRK.B` 单标的历史 K 线 probe，再做 replacement-to-200。",
        "4. 补齐支付宝基金真实 NAV/proxy 和申赎规则后，重跑基金口径。",
        "5. 数据门稳定后再排百万级分片 campaign。",
    ])
    return "\n".join(lines) + "\n"


def build_pdf(audit: dict, requirements: pd.DataFrame, output: Path) -> None:
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    styles = getSampleStyleSheet()
    base = ParagraphStyle("CN", parent=styles["BodyText"], fontName="STSong-Light", fontSize=8.5, leading=12)
    title = ParagraphStyle("CNTitle", parent=styles["Title"], fontName="STSong-Light", fontSize=17, leading=22, textColor=colors.HexColor("#111827"))
    h2 = ParagraphStyle("CNH2", parent=styles["Heading2"], fontName="STSong-Light", fontSize=12, leading=16, textColor=colors.HexColor("#1F2937"))
    doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=12 * mm, leftMargin=12 * mm, topMargin=12 * mm, bottomMargin=12 * mm)
    story = [
        Paragraph("QBVS 目标完成度缺口审计", title),
        Paragraph(f"生成时间：{audit['created_at']}", base),
        Spacer(1, 6),
        Paragraph("当前结论", h2),
        Paragraph(f"readiness {audit['readiness_percent']:.2f}%；当前不严格 blocked，但不能标记 complete：真实基金 NAV、OpenD 历史 quota、百万级规模仍未闭合。", base),
        Spacer(1, 8),
        Paragraph("逐项审计", h2),
    ]
    table_data = [["需求", "状态", "证据", "下一步"]]
    for _, item in requirements.iterrows():
        table_data.append([
            Paragraph(str(item["requirement"]), base),
            Paragraph(str(item["status"]), base),
            Paragraph(str(item["evidence"]), base),
            Paragraph(str(item["next_action"]), base),
        ])
    table = Table(table_data, colWidths=[34 * mm, 18 * mm, 74 * mm, 58 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
    ]))
    story.append(table)
    story.append(Spacer(1, 8))
    story.append(Paragraph("下一步最短路径", h2))
    story.append(Paragraph("保持 ReviewOnly；QuantLab 读取 12,000 exact bundle；OpenD quota 恢复后单标的 probe 再 replacement-to-200；补齐支付宝 NAV 后重跑基金口径；数据门稳定后再排百万级 campaign。", base))
    doc.build(story)


if __name__ == "__main__":
    main()
