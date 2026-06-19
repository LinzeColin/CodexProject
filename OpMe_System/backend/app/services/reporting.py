from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.config import APP_NAME, REPORT_DIR, ensure_runtime_dirs


def _register_fonts() -> str:
    font_name = "STSong-Light"
    try:
        pdfmetrics.registerFont(UnicodeCIDFont(font_name))
        return font_name
    except Exception:  # noqa: BLE001
        return "Helvetica"


def _styles() -> Dict[str, ParagraphStyle]:
    font_name = _register_fonts()
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "cn-title",
            parent=base["Title"],
            fontName=font_name,
            fontSize=20,
            leading=26,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=12,
        ),
        "h2": ParagraphStyle(
            "cn-h2",
            parent=base["Heading2"],
            fontName=font_name,
            fontSize=13,
            leading=18,
            textColor=colors.HexColor("#0f766e"),
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "cn-body",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#1f2937"),
        ),
        "small": ParagraphStyle(
            "cn-small",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#475569"),
        ),
    }


def _p(text: Any, style: ParagraphStyle) -> Paragraph:
    safe = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(safe, style)


def _kv_table(data: Dict[str, Any], style: ParagraphStyle) -> Table:
    rows = [[_p("指标", style), _p("值", style)]]
    for key, value in data.items():
        rows.append([_p(key, style), _p(value, style)])
    table = Table(rows, colWidths=[55 * mm, 115 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _list_table(title: str, values: List[str], styles: Dict[str, ParagraphStyle]) -> List[Any]:
    flow: List[Any] = [_p(title, styles["h2"])]
    rows = [[_p("序号", styles["body"]), _p("内容", styles["body"])]]
    for index, value in enumerate(values, start=1):
        rows.append([_p(index, styles["body"]), _p(value, styles["body"])])
    table = Table(rows, colWidths=[18 * mm, 152 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    flow.append(table)
    return flow


def generate_case_report(case_data: Dict[str, Any]) -> Path:
    ensure_runtime_dirs()
    result = case_data["result"]
    output_path = REPORT_DIR / f"case_{case_data['id']:04d}_{case_data['module']}.pdf"
    styles = _styles()
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"{result['title']} - {case_data['id']}",
    )
    flow: List[Any] = []
    flow.append(_p(APP_NAME, styles["title"]))
    flow.append(_p(result["title"], styles["h2"]))
    flow.append(_p(f"案例编号：{case_data['id']} | 模块：{case_data['module']} | 报告状态：{case_data['report_status']}", styles["small"]))
    flow.append(Spacer(1, 6))
    flow.append(_kv_table({"摘要": result["summary"], "风险等级": result["risk_level"], "风险评分": f"{result['risk_score']}/100", "模型状态": result.get("model_status", {}).get("message", "")}, styles["body"]))
    flow.append(_p("关键指标", styles["h2"]))
    flow.append(_kv_table(result.get("metrics", {}), styles["body"]))
    flow.extend(_list_table("工程建议", result.get("suggestions", []), styles))
    flow.append(_p("可视化图表摘要", styles["h2"]))
    chart_rows = [[_p("图表", styles["body"]), _p("类型", styles["body"]), _p("说明", styles["body"])]]
    for viz in result.get("visualizations", []):
        chart_rows.append([_p(viz.get("title"), styles["body"]), _p(viz.get("kind"), styles["body"]), _p(viz.get("description"), styles["body"])])
    chart_table = Table(chart_rows, colWidths=[45 * mm, 25 * mm, 100 * mm])
    chart_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ecfeff")),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    flow.append(chart_table)
    flow.extend(_list_table("证据与参考", result.get("evidence", []), styles))
    flow.append(_p("风险边界", styles["h2"]))
    flow.append(
        _p(
            "本报告为工业运维技术建议，不替代现场检测、施工方案审批和专业工程师签字确认。涉及停机、焊接、热处理、起吊和设备改造时，应按企业安全规程执行。",
            styles["body"],
        )
    )
    doc.build(flow)
    return output_path

