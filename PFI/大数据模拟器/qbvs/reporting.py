from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _pct(value: object) -> str:
    try:
        return f"{float(value):.2%}"
    except Exception:
        return "-"


def build_pdf_report(
    output_path: Path | str,
    title: str,
    summary: pd.DataFrame,
    notes: list[str] | None = None,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = [Paragraph(title, styles["Title"])]
    story.append(Paragraph(f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    story.append(Spacer(1, 12))
    for note in notes or []:
        story.append(Paragraph(note, styles["BodyText"]))
        story.append(Spacer(1, 6))
    story.append(Paragraph("Top Strategy Summary", styles["Heading2"]))
    if summary.empty:
        story.append(Paragraph("No valid summary rows were generated.", styles["BodyText"]))
    else:
        cols = [
            "strategy_id",
            "samples",
            "pass_rate",
            "avg_total_gap",
            "avg_annualized_gap",
            "avg_drawdown_improvement",
            "avg_var_5",
            "avg_cvar_5",
        ]
        available = [c for c in cols if c in summary.columns]
        top = summary[available].head(12).copy()
        for c in top.columns:
            if c not in {"strategy_id", "samples"}:
                top[c] = top[c].map(_pct)
        table_data = [available] + top.astype(str).values.tolist()
        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(table)
    story.append(Spacer(1, 12))
    story.append(Paragraph("QuantLab Integration Boundary", styles["Heading2"]))
    story.append(
        Paragraph(
            "This system is standalone and read-only relative to QuantLab. QuantLab can later consume strategy_summary.csv, validation_results.csv, and this PDF as external evidence before approving a strategy.",
            styles["BodyText"],
        )
    )
    doc.build(story)
    return path
