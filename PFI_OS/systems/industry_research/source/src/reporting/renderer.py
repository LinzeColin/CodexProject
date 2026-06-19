from __future__ import annotations

import json
import re
import hashlib
from pathlib import Path
from typing import Any

from src.models import Source
from src.reporting.paths import markdown_path, pdf_path, source_log_path

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Image, LongTable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, TableStyle
except ImportError:  # pragma: no cover - exercised only when optional dependency is missing.
    colors = None


def render_template(template_path: str | Path, values: dict[str, Any]) -> str:
    content = Path(template_path).read_text(encoding="utf-8")
    for key, value in values.items():
        content = content.replace("{{ " + key + " }}", str(value))
    return content


def source_list(sources: list[Source]) -> str:
    count = len({(source.source_name, source.source_url) for source in sources})
    if count == 0:
        return "来源核验：无新增来源；详细 source log 已保留为空记录。"
    return f"来源核验：已记录 {count} 个去重来源；详细 source_name/source_url/fetch_time/data_version 保存在 source log。"


def table(rows: list[dict[str, object]], columns: list[str], headers: list[str] | None = None) -> str:
    if not rows:
        return "暂无数据"
    headers = headers or columns
    header = "| " + " | ".join(headers) + " |"
    divider = "| " + " | ".join(["---"] * len(headers)) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(_format(row.get(column, ""), column) for column in columns) + " |")
    return "\n".join([header, divider, *body])


def _format(value: object, column: str = "") -> str:
    if value == "":
        return ""
    if column.endswith("_pct") or column in {"change", "momentum_5d", "daily_change_pct", "suggested_weight", "target_weight", "risk_adjusted_weight", "cash_weight", "current_weight", "Volume"}:
        try:
            return format_percent(float(value))
        except (TypeError, ValueError):
            return str(value)
    if column in {
        "amount",
        "holding_amount",
        "holding_return_amount",
        "pending_order_amount",
        "total_holding_amount",
        "total_holding_return_amount",
        "daily_return_amount",
        "accumulated_return_amount",
        "order_amount",
        "confirmed_amount",
    }:
        try:
            return f"{float(value):,.2f}"
        except (TypeError, ValueError):
            return str(value)
    if column in {"volume", "turnover"}:
        try:
            return f"{float(value):,.0f}"
        except (TypeError, ValueError):
            return str(value)
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def format_percent(value: float) -> str:
    return f"{value * 100:.3f}%"


def write_markdown_report(name: str, content: str) -> Path:
    path = markdown_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def write_report_bundle(name: str, content: str) -> dict[str, Path]:
    markdown_path = write_markdown_report(name + ".md", content)
    pdf_path = write_pdf_report(name + ".pdf", content)
    return {"markdown": markdown_path, "pdf": pdf_path}


def write_source_log(name: str, sources: list[Source], extra: dict[str, Any] | None = None) -> Path:
    path = source_log_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "report_name": name,
        "sources": [
            {
                "source_name": source.source_name,
                "source_url": source.source_url,
                "fetch_time": source.fetch_time,
                "data_version": source.data_version,
            }
            for source in sources
        ],
        "extra": extra or {},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_pdf_report(name: str, markdown_content: str) -> Path:
    if colors is None:
        raise RuntimeError("PDF export requires reportlab. Install with: python3 -m pip install reportlab")
    path = pdf_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    _register_font()
    doc = SimpleDocTemplate(
        str(path),
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
        title=name.replace(".pdf", ""),
    )
    story = _markdown_to_story(markdown_content)
    doc.build(story)
    return path


def heading_anchor(text: str) -> str:
    normalized = re.sub(r"\s+", " ", str(text).strip())
    digest = hashlib.md5(normalized.encode("utf-8")).hexdigest()[:10]
    return f"h-{digest}"


def toc_for(headings: list[str]) -> str:
    rows = ["## 目录"]
    rows.extend(f"- [{heading}](#{heading_anchor(heading)})" for heading in headings)
    return "\n".join(rows)


def _register_font() -> None:
    if "ReportCJK" in pdfmetrics.getRegisteredFontNames():
        return
    font_candidates = [
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for font_path in font_candidates:
        if Path(font_path).exists():
            pdfmetrics.registerFont(TTFont("ReportCJK", font_path))
            return
    raise FileNotFoundError("No CJK font found for PDF export.")


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="ReportCJK", fontSize=18, leading=24, spaceAfter=8),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="ReportCJK", fontSize=12, leading=16, textColor=colors.HexColor("#1f4e79"), spaceBefore=8, spaceAfter=5),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName="ReportCJK", fontSize=8.5, leading=12, alignment=TA_LEFT, spaceAfter=4),
        "cell": ParagraphStyle("cell", parent=base["BodyText"], fontName="ReportCJK", fontSize=6.2, leading=8),
        "cell_header": ParagraphStyle("cell_header", parent=base["BodyText"], fontName="ReportCJK", fontSize=6.5, leading=8, textColor=colors.white),
    }


def _markdown_to_story(content: str) -> list[Any]:
    styles = _styles()
    story: list[Any] = []
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line == "<!-- PAGEBREAK -->":
            story.append(PageBreak())
            i += 1
            continue
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            story.append(_pdf_table(table_lines, styles))
            story.append(Spacer(1, 5))
            continue
        image_match = re.match(r"!\[[^\]]*\]\(([^)]+)\)", line)
        if image_match:
            image_path = Path(image_match.group(1))
            if image_path.exists():
                story.append(_pdf_image(image_path))
                story.append(Spacer(1, 5))
            i += 1
            continue
        if line.startswith("# "):
            text = line[2:]
            story.append(Paragraph(f'<a name="{heading_anchor(text)}"/>' + _inline_markup(text), styles["h1"]))
        elif line.startswith("## "):
            text = line[3:]
            story.append(Paragraph(f'<a name="{heading_anchor(text)}"/>' + _inline_markup(text), styles["h2"]))
        elif line.startswith("- "):
            story.append(Paragraph("• " + _inline_markup(line[2:]), styles["body"]))
        else:
            story.append(Paragraph(_inline_markup(line), styles["body"]))
        i += 1
    return story


def _pdf_table(lines: list[str], styles: dict[str, ParagraphStyle]) -> LongTable:
    raw_rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(set(cell) <= {"-", " "} for cell in cells):
            continue
        raw_rows.append(cells)
    rows = []
    for idx, cells in enumerate(raw_rows):
        style = styles["cell_header"] if idx == 0 else styles["cell"]
        rows.append([Paragraph(_escape(cell), style) for cell in cells])
    col_widths = _auto_col_widths(raw_rows, 270 * mm)
    pdf_table = LongTable(rows, colWidths=col_widths, repeatRows=1)
    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d9e2ec")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#fbfdff")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    style_commands.extend(_position_row_style_commands(raw_rows))
    pdf_table.setStyle(TableStyle(style_commands))
    return pdf_table


def _position_row_style_commands(raw_rows: list[list[str]]) -> list[tuple[object, ...]]:
    if not raw_rows:
        return []
    headers = raw_rows[0]
    commands: list[tuple[object, ...]] = []
    for position_header in ["K线研究分组", "观察状态", "Position", "操作", "仓位动作", "操作建议"]:
        if position_header not in headers:
            continue
        pos_col = headers.index(position_header)
        for row_idx, raw_row in enumerate(raw_rows[1:], start=1):
            value = raw_row[pos_col] if pos_col < len(raw_row) else ""
            if any(token in value for token in ["买入", "补仓", "承接", "低仓位"]):
                commands.append(("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#f8d7da")))
                commands.append(("TEXTCOLOR", (0, row_idx), (-1, row_idx), colors.HexColor("#7f0018")))
            if any(token in value for token in ["卖出", "减仓", "减暴露", "降暴露"]):
                commands.append(("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#d8f3dc")))
                commands.append(("TEXTCOLOR", (0, row_idx), (-1, row_idx), colors.HexColor("#176f37")))
        break
    return commands


def _auto_col_widths(rows: list[list[str]], total_width: float) -> list[float]:
    if not rows:
        return [total_width]
    col_count = len(rows[0])
    widths = []
    for col_idx in range(col_count):
        header = rows[0][col_idx] if col_idx < len(rows[0]) else ""
        max_len = max((_display_len(row[col_idx]) for row in rows if col_idx < len(row)), default=4)
        widths.append(_desired_col_width(header, max_len))
    total = sum(widths)
    if total <= total_width:
        return widths
    fixed_headers = {"排序", "代码", "Symbol", "价格", "涨跌幅", "研究权重上限", "Volume", "Volume依据", "建议金额", "Confidence", "信号", "K线研究分组", "观察状态", "Position", "风控后仓位", "复合质量分", "说服力", "策略胜率代理", "概率等级", "最大回撤", "Walk-forward", "信号质量"}
    fixed_total = sum(width for width, header in zip(widths, rows[0]) if header in fixed_headers)
    flexible_indices = [idx for idx, header in enumerate(rows[0]) if header not in fixed_headers]
    flexible_total = sum(widths[idx] for idx in flexible_indices)
    remaining = max(total_width - fixed_total, len(flexible_indices) * 18 * mm)
    if flexible_indices and flexible_total > 0:
        scale = remaining / flexible_total
        for idx in flexible_indices:
            widths[idx] = max(18 * mm, widths[idx] * scale)
    if sum(widths) > total_width:
        scale = total_width / sum(widths)
        widths = [width * scale for width in widths]
    return widths


def _display_len(text: str) -> int:
    return sum(2 if ord(char) > 127 else 1 for char in str(text))


def _desired_col_width(header: str, max_len: int) -> float:
    fixed = {
        "排序": 9,
        "代码": 16,
        "Symbol": 16,
        "价格": 16,
        "涨跌幅": 16,
        "研究权重上限": 18,
        "Volume": 17,
        "Volume依据": 30,
        "建议金额": 18,
        "Confidence": 16,
        "信号": 18,
        "K线研究分组": 26,
        "观察状态": 26,
        "Position": 24,
        "风控后仓位": 19,
        "复合质量分": 19,
        "说服力": 28,
        "策略胜率代理": 20,
        "概率等级": 22,
        "信号质量": 18,
        "最大回撤": 18,
        "Walk-forward": 20,
        "影响": 13,
        "类型": 18,
    }
    if header in fixed:
        return fixed[header] * mm
    preferred = {
        "Name": (24, 42),
        "名称": (24, 42),
        "研究分组": (18, 30),
        "成交量": (20, 26),
        "成交额": (22, 32),
        "数据来源": (24, 38),
        "事件时间（来源当地时间）": (30, 38),
        "事件时间（含年月日/来源当地时间）": (36, 46),
        "时间（含年月日/来源当地时区）": (36, 48),
        "标题": (45, 78),
        "交易理由": (38, 62),
        "失效/风控": (42, 70),
        "Entry Condition": (45, 76),
        "Exit Condition": (45, 76),
        "数据说明": (48, 82),
        "执行价值": (42, 68),
        "风险触发": (38, 62),
        "交易判断": (42, 70),
        "来源": (24, 40),
        "现仓口径": (34, 58),
        "风险点": (42, 76),
        "依据": (42, 72),
        "执行窗口": (28, 40),
        "操作结论": (40, 72),
        "准确性依据": (34, 56),
        "高概率盈利条件": (48, 86),
        "风险闸门": (34, 56),
        "量价证据": (42, 70),
        "事件原文核验": (42, 76),
        "政策/事件支持": (48, 80),
        "操作策略": (48, 82),
        "失败动作": (48, 82),
        "检查时间": (28, 42),
        "账户闸门": (42, 76),
        "成立条件": (48, 86),
        "不成立动作": (46, 82),
        "证据缺口": (46, 82),
        "PFIOS闸门": (38, 68),
        "最终规则": (46, 82),
        "来源链路": (38, 62),
        "后续指标": (40, 70),
        "操作影响": (44, 78),
        "训练题答案": (34, 62),
        "分析逻辑/思考过程": (52, 90),
        "满足时操作": (40, 72),
        "不满足时操作": (40, 72),
        "当前操作行为": (42, 76),
    }
    min_mm, max_mm = preferred.get(header, (18, 46))
    estimated = max(min_mm, min(max_mm, max_len * 1.25))
    return estimated * mm


def _pdf_image(path: Path) -> Image:
    image = Image(str(path))
    max_width = 250 * mm
    max_height = 90 * mm
    scale = min(max_width / image.imageWidth, max_height / image.imageHeight, 1)
    image.drawWidth = image.imageWidth * scale
    image.drawHeight = image.imageHeight * scale
    return image


def _escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )


def _inline_markup(text: str) -> str:
    raw = str(text)
    parts = []
    cursor = 0
    for match in re.finditer(r"\[([^\]]+)\]\(#([^)]+)\)", raw):
        parts.append(_escape(raw[cursor : match.start()]))
        label = _escape(match.group(1))
        anchor = _escape(match.group(2))
        parts.append(f'<a href="#{anchor}" color="blue"><u>{label}</u></a>')
        cursor = match.end()
    parts.append(_escape(raw[cursor:]))
    return "".join(parts)
