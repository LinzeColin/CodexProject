from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple
from xml.sax.saxutils import escape as xml_escape

from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .io import atomic_publish_file


FONT_REGULAR = "STHeiti-Light-Sidecar"
FONT_BOLD = "STHeiti-Medium-Sidecar"


def register_fonts() -> None:
    global FONT_REGULAR, FONT_BOLD
    try:
        pdfmetrics.registerFont(TTFont(FONT_REGULAR, "/System/Library/Fonts/STHeiti Light.ttc"))
        pdfmetrics.registerFont(TTFont(FONT_BOLD, "/System/Library/Fonts/STHeiti Medium.ttc"))
    except Exception:
        FONT_REGULAR = "Helvetica"
        FONT_BOLD = "Helvetica-Bold"


register_fonts()
STYLES = getSampleStyleSheet()
STYLES.add(
    ParagraphStyle(
        name="SidecarTitle",
        fontName=FONT_BOLD,
        fontSize=19,
        leading=25,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0B1F3A"),
        spaceAfter=5 * mm,
    )
)
STYLES.add(
    ParagraphStyle(
        name="SidecarSubtitle",
        fontName=FONT_REGULAR,
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#526070"),
    )
)
STYLES.add(
    ParagraphStyle(
        name="SidecarH2",
        fontName=FONT_BOLD,
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0B1F3A"),
    )
)
STYLES.add(
    ParagraphStyle(
        name="SidecarBody",
        fontName=FONT_REGULAR,
        fontSize=8.8,
        leading=12,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#1F2937"),
    )
)
STYLES.add(
    ParagraphStyle(
        name="SidecarTableCell",
        fontName=FONT_REGULAR,
        fontSize=7.1,
        leading=9.0,
        textColor=colors.HexColor("#111827"),
    )
)


def render_sidecar_pdf(
    output_path: Path,
    *,
    title: str,
    subtitle: str,
    summary_rows: Sequence[Tuple[str, str]],
    charts: Sequence[Dict],
    table_headers: Sequence[str],
    table_rows: Sequence[Sequence[str]],
    extra_tables: Sequence[Dict] | None = None,
) -> Dict:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    story: List = [
        Paragraph(pdf_escape(title), STYLES["SidecarTitle"]),
        Paragraph(pdf_escape(subtitle), STYLES["SidecarSubtitle"]),
        Spacer(1, 7 * mm),
        Paragraph("Executive Summary", STYLES["SidecarH2"]),
        Spacer(1, 2 * mm),
        sidecar_table([["Metric", "Value"], *[[key, value] for key, value in summary_rows]], [62 * mm, 118 * mm]),
        Spacer(1, 6 * mm),
        Paragraph("Visual Summary", STYLES["SidecarH2"]),
        Spacer(1, 2 * mm),
    ]
    for index in range(0, len(charts), 2):
        left = pdf_chart(charts[index])
        right = pdf_chart(charts[index + 1]) if index + 1 < len(charts) else ""
        story.append(sidecar_table([[left, right]], [92 * mm, 92 * mm], header=False))
        story.append(Spacer(1, 3 * mm))
    story.extend([Spacer(1, 4 * mm), Paragraph("Detail Table", STYLES["SidecarH2"]), Spacer(1, 2 * mm)])
    if table_rows:
        story.append(sidecar_table([list(table_headers), *[list(row) for row in table_rows]], table_widths(len(table_headers))))
    else:
        story.append(Paragraph("No detail rows available.", STYLES["SidecarBody"]))
    extra_detail_row_count = 0
    for table in extra_tables or []:
        headers = [str(value) for value in table.get("headers", [])]
        rows = [[str(cell) for cell in row] for row in table.get("rows", [])]
        if not headers:
            continue
        extra_detail_row_count += len(rows)
        story.extend([Spacer(1, 5 * mm), Paragraph(pdf_escape(table.get("title") or "Additional Table"), STYLES["SidecarH2"]), Spacer(1, 2 * mm)])
        if rows:
            story.append(sidecar_table([headers, *rows], table_widths(len(headers))))
        else:
            story.append(Paragraph("No detail rows available.", STYLES["SidecarBody"]))
    fd, tmp_name = tempfile.mkstemp(prefix=f".{output_path.name}.", suffix=".tmp", dir=str(output_path.parent))
    os.close(fd)
    try:
        SimpleDocTemplate(
            tmp_name,
            pagesize=A4,
            rightMargin=12 * mm,
            leftMargin=12 * mm,
            topMargin=12 * mm,
            bottomMargin=12 * mm,
        ).build(story)
        atomic_publish_file(Path(tmp_name), output_path)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise
    return {
        "path": output_path.name,
        "page_size": "A4",
        "chart_count": len(charts),
        "detail_row_count": len(table_rows),
        "extra_table_count": len(extra_tables or []),
        "extra_detail_row_count": extra_detail_row_count,
    }


def chart_from_items(title: str, items: Iterable[Tuple[str, float]], color: str = "#1F4E79") -> Dict:
    rows = [(str(label), max(0.0, float(value or 0))) for label, value in items]
    max_value = max([value for _label, value in rows] + [0.0])
    return {
        "title": title,
        "items": [
            {
                "label": label,
                "display": display_value(value),
                "bar_fraction": value / max_value if max_value else 0.0,
                "color": color,
            }
            for label, value in rows[:7]
        ],
    }


def pdf_chart(chart: Dict, width: float = 86 * mm) -> Drawing:
    items = chart.get("items", [])[:7]
    row_height = 11
    title_height = 14
    height = max(34, title_height + len(items) * row_height + 5)
    drawing = Drawing(width, height)
    drawing.add(String(0, height - 10, truncate(chart.get("title"), 32), fontName=FONT_BOLD, fontSize=8, fillColor=colors.HexColor("#0B1F3A")))
    if not items:
        drawing.add(String(0, height - 25, "No data", fontName=FONT_REGULAR, fontSize=7, fillColor=colors.HexColor("#5F6B7A")))
        return drawing
    label_width = width * 0.45
    bar_width = width * 0.35
    value_x = label_width + bar_width + 4
    for index, item in enumerate(items):
        y = height - title_height - (index + 1) * row_height
        fraction = max(0.0, min(1.0, float(item.get("bar_fraction") or 0)))
        drawing.add(String(0, y + 2, truncate(item.get("label"), 24), fontName=FONT_REGULAR, fontSize=6.2, fillColor=colors.HexColor("#172033")))
        drawing.add(Rect(label_width, y + 1.5, bar_width, 5.5, fillColor=colors.HexColor("#EEF2F6"), strokeColor=None))
        drawing.add(Rect(label_width, y + 1.5, bar_width * fraction, 5.5, fillColor=colors.HexColor(str(item.get("color") or "#1F4E79")), strokeColor=None))
        drawing.add(String(value_x, y + 2, truncate(item.get("display"), 12), fontName=FONT_REGULAR, fontSize=6.2, fillColor=colors.HexColor("#5F6B7A")))
    return drawing


def sidecar_table(rows: List[List], widths: List[float], header: bool = True) -> Table:
    converted = [
        [cell if isinstance(cell, Flowable) else Paragraph(pdf_escape(cell), STYLES["SidecarTableCell"]) for cell in row]
        for row in rows
    ]
    tbl = Table(converted, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D8DEE9")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        style.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FBFCFE")),
                ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
            ]
        )
    for idx in range(1 if header else 0, len(rows)):
        if idx % 2 == 0:
            style.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#F5F7FA")))
    tbl.setStyle(TableStyle(style))
    return tbl


def table_widths(column_count: int) -> List[float]:
    if column_count <= 2:
        return [55 * mm, 125 * mm][:column_count]
    return [180 * mm / column_count] * column_count


def display_value(value: float) -> str:
    if value >= 100:
        return f"{value:,.0f}"
    if value >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"


def pdf_escape(value) -> str:
    return xml_escape("" if value is None else str(value), {"'": "&apos;", '"': "&quot;"})


def truncate(value, length: int) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= length else text[: max(0, length - 3)] + "..."
