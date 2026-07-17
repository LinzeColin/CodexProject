#!/usr/bin/env python3
"""KMFA v1.5 S21-P2 deterministic HTML, PDF and CSV report generation.

The phase consumes an immutable S21-P1 report version and renders three views
from one public-synthetic, integer-cents payload.  It does not approve,
publish, read raw business files, upload to GitHub, or reinstall the app.
"""

from __future__ import annotations

import csv
import fcntl
import hashlib
import html
import io
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from KMFA.tools import v015_s21_p1_report_model as report_model


RUN_PHASE_ID = "V015_S21_P2_REPORT_GENERATION"
ROADMAP_PHASE_ID = "S21-P2"
TASK_ID = "KMFA-V015-S21-P2-REPORT-GENERATION-20260717"
ACCEPTANCE_ID = "ACC-KMFA-V015-S21-P2-REPORT-GENERATION"
VERSION = "1.5.0-dev-s21p2"
DATA_CLASSIFICATION = "PUBLIC_SYNTHETIC"
DEFAULT_RUNTIME_ROOT = Path(__file__).resolve().parents[1] / ".codex_private_runtime/v015_s21_p2_report_generation"
DEFAULT_EVENT_PATH = DEFAULT_RUNTIME_ROOT / "report_exports.jsonl"
DEFAULT_BUNDLE_ROOT = DEFAULT_RUNTIME_ROOT / "bundles"
HTML_FILENAME = "kmfa_management_report.html"
PDF_FILENAME = "kmfa_management_report.pdf"
CSV_FILENAME = "kmfa_professional_appendix.csv"
FORMATS = ("HTML", "PDF", "CSV")


class ReportGenerationError(ValueError):
    """Generation input, history, or output violates the S21-P2 contract."""

    def __init__(self, code: str, message_zh: str, *, status: int = 400) -> None:
        super().__init__(message_zh)
        self.code = code
        self.message_zh = message_zh
        self.status = status


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _file_digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: Any, field: str, *, minimum: int = 1, maximum: int = 200) -> str:
    text_value = str(value or "").strip()
    if len(text_value) < minimum or len(text_value) > maximum:
        raise ReportGenerationError("INVALID_TEXT", f"{field}不完整或过长")
    return text_value


def _money(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    yuan, remainder = divmod(abs(int(cents)), 100)
    return f"{sign}¥{yuan:,}.{remainder:02d}"


def _percent_bps(bps: int) -> str:
    sign = "-" if bps < 0 else ""
    whole, remainder = divmod(abs(int(bps)), 100)
    return f"{sign}{whole}.{remainder:02d}%"


def _safe_csv_text(value: Any) -> str:
    text_value = str(value or "")
    return "'" + text_value if text_value[:1] in {"=", "+", "-", "@"} else text_value


def demo_report_model() -> dict[str, Any]:
    """Build the deterministic S21-P1 predecessor used by tests and evidence."""

    with tempfile.TemporaryDirectory() as folder:
        journal = report_model.ReportModelJournal(Path(folder) / "models.jsonl")
        return journal.create(
            company_id="demo-north",
            period_kind="MONTHLY",
            period_key="2026-07",
            source_bindings=report_model.default_source_bindings(),
            formula_bindings=report_model.default_formula_bindings(),
            created_by="公开演示负责人",
            idempotency_key="s21p2-demo-report-001",
            recorded_at="2026-07-17T00:00:00+00:00",
        )


def build_report_payload(report: Mapping[str, Any]) -> dict[str, Any]:
    """Create the single canonical fact payload used by every output format."""

    report_version_id = _text(report.get("report_version_id"), "报告版本", maximum=180)
    if report.get("data_classification") != DATA_CLASSIFICATION:
        raise ReportGenerationError("REPORT_CLASSIFICATION_BLOCKED", "只允许生成公开合成报告")
    trust = report.get("trust_and_limitations")
    if not isinstance(trust, Mapping) or trust.get("complete_report_claim_allowed") is not True:
        raise ReportGenerationError("REPORT_INPUTS_INCOMPLETE", "关键资料不完整，不能生成完整报告", status=409)
    sources = report.get("source_bindings")
    if not isinstance(sources, Sequence) or len(sources) != 6 or any(row.get("state") != "AVAILABLE" for row in sources):
        raise ReportGenerationError("REPORT_SOURCE_BINDING_INVALID", "报告资料绑定不完整", status=409)

    projects = [
        {
            "project_id": "DEMO-PROJECT-A",
            "project_name_zh": "示例项目 A",
            "revenue_cents": 52_000_000,
            "cost_cents": 39_000_000,
            "gross_profit_cents": 13_000_000,
            "collection_cents": 41_500_000,
            "receivable_cents": 10_500_000,
            "source_ref": "S17P3-PROJECT-2026-07-V1:A",
            "status_zh": "按计划推进",
        },
        {
            "project_id": "DEMO-PROJECT-B",
            "project_name_zh": "示例项目 B",
            "revenue_cents": 43_250_000,
            "cost_cents": 31_910_000,
            "gross_profit_cents": 11_340_000,
            "collection_cents": 35_800_000,
            "receivable_cents": 7_450_000,
            "source_ref": "S17P3-PROJECT-2026-07-V1:B",
            "status_zh": "回款需跟进",
        },
        {
            "project_id": "DEMO-PROJECT-C",
            "project_name_zh": "示例项目 C",
            "revenue_cents": 33_200_000,
            "cost_cents": 25_700_000,
            "gross_profit_cents": 7_500_000,
            "collection_cents": 23_500_000,
            "receivable_cents": 9_700_000,
            "source_ref": "S17P3-PROJECT-2026-07-V1:C",
            "status_zh": "材料待补齐",
        },
    ]
    totals = {
        key: sum(int(row[key]) for row in projects)
        for key in ("revenue_cents", "cost_cents", "gross_profit_cents", "collection_cents", "receivable_cents")
    }
    if totals["revenue_cents"] - totals["cost_cents"] != totals["gross_profit_cents"]:
        raise ReportGenerationError("PROJECT_RECONCILIATION_FAILED", "项目收入、成本和毛利无法核对", status=409)
    if totals["revenue_cents"] - totals["collection_cents"] != totals["receivable_cents"]:
        raise ReportGenerationError("COLLECTION_RECONCILIATION_FAILED", "收入、回款和应收无法核对", status=409)
    gross_margin_bps = (totals["gross_profit_cents"] * 10_000 + totals["revenue_cents"] // 2) // totals["revenue_cents"]
    metrics = [
        {"metric_id": "revenue", "label_zh": "确认收入", "value_integer": totals["revenue_cents"], "unit": "CENTS", "display_value": _money(totals["revenue_cents"]), "formula_zh": "三个示例项目确认收入之和", "source_ref": "PUB-S20P3-0001:revenue", "difference_integer": 0},
        {"metric_id": "cost", "label_zh": "确认成本", "value_integer": totals["cost_cents"], "unit": "CENTS", "display_value": _money(totals["cost_cents"]), "formula_zh": "三个示例项目确认成本之和", "source_ref": "PUB-S20P3-0001:cost", "difference_integer": 0},
        {"metric_id": "gross_profit", "label_zh": "毛利", "value_integer": totals["gross_profit_cents"], "unit": "CENTS", "display_value": _money(totals["gross_profit_cents"]), "formula_zh": "确认收入减确认成本", "source_ref": "FORM-KMFA-V015-S20-P3-RECALCULATION-PUBLICATION-001", "difference_integer": 0},
        {"metric_id": "gross_margin", "label_zh": "毛利率", "value_integer": gross_margin_bps, "unit": "BPS", "display_value": _percent_bps(gross_margin_bps), "formula_zh": "毛利除以确认收入，四舍五入到一个基点", "source_ref": "FORM-KMFA-V015-S21-P2-REPORT-GENERATION-001", "difference_integer": 0},
        {"metric_id": "cash_balance", "label_zh": "期末现金", "value_integer": 46_200_000, "unit": "CENTS", "display_value": _money(46_200_000), "formula_zh": "本期公开合成资金余额", "source_ref": "S18P3-FUNDS-2026-07-V1:cash", "difference_integer": 0},
        {"metric_id": "receivables", "label_zh": "期末应收", "value_integer": totals["receivable_cents"], "unit": "CENTS", "display_value": _money(totals["receivable_cents"]), "formula_zh": "确认收入减本期回款", "source_ref": "S18P1-RECEIVABLES-2026-07-V1:ending", "difference_integer": 0},
    ]
    payload: dict[str, Any] = {
        "schema_version": "kmfa.v015.s21p2.report_payload.v1",
        "report_version_id": report_version_id,
        "report_family_id": report.get("report_family_id"),
        "report_title_zh": "KMFA 月度经营报告（公开合成演示）",
        "company_id": report.get("company_id"),
        "company_name_zh": "北区示例公司",
        "period": dict(report.get("period") or {}),
        "source_binding_fingerprint": report.get("source_binding_fingerprint"),
        "formula_binding_fingerprint": report.get("formula_binding_fingerprint"),
        "source_bindings": [dict(row) for row in sources],
        "metrics": metrics,
        "projects": projects,
        "headline": {
            **totals,
            "gross_margin_bps": gross_margin_bps,
            "cash_balance_cents": 46_200_000,
            "tax_review_count": 4,
            "key_matter_count": 3,
        },
        "key_matters": [
            {"matter_id": "MATTER-001", "matter_zh": "跟进示例项目 B 回款", "owner_zh": "财务负责人", "next_step_zh": "本周核对回款计划", "source_ref": "S20P2-CONFIRMATIONS-2026-07-V1:001"},
            {"matter_id": "MATTER-002", "matter_zh": "补齐示例项目 C 材料", "owner_zh": "项目负责人", "next_step_zh": "下周一前完成复核", "source_ref": "S20P2-CONFIRMATIONS-2026-07-V1:002"},
            {"matter_id": "MATTER-003", "matter_zh": "完成四项税务资料复核", "owner_zh": "税务负责人", "next_step_zh": "按适用范围逐项确认", "source_ref": "S19P3-TAX-POLICY-2026-07-V1:review"},
        ],
        "trust_and_limitations": dict(trust),
        "data_classification": DATA_CLASSIFICATION,
        "formal_business_report": False,
        "approval_or_publication_performed": False,
        "raw_access_count": 0,
    }
    payload["report_payload_fingerprint"] = _digest(payload)
    return payload


def canonical_numeric_values(payload: Mapping[str, Any]) -> dict[str, int]:
    values = {str(row["metric_id"]): int(row["value_integer"]) for row in payload["metrics"]}
    for project in payload["projects"]:
        for field in ("revenue_cents", "cost_cents", "gross_profit_cents", "collection_cents", "receivable_cents"):
            values[f"{project['project_id']}:{field}"] = int(project[field])
    return values


def render_report_html(payload: Mapping[str, Any]) -> str:
    """Render a responsive, printable standalone report with source entry."""

    esc = lambda value: html.escape(str(value), quote=True)
    cards = "".join(
        f'<article class="metric"><span>{esc(row["label_zh"])}</span><strong data-value-id="{esc(row["metric_id"])}" data-raw-integer="{row["value_integer"]}">{esc(row["display_value"])}</strong><small>{esc(row["formula_zh"])}</small></article>'
        for row in payload["metrics"]
    )
    project_rows = "".join(
        "<tr>"
        f'<th scope="row">{esc(row["project_name_zh"])}</th>'
        + "".join(
            f'<td data-value-id="{esc(row["project_id"])}:{field}" data-raw-integer="{row[field]}">{esc(_money(row[field]))}</td>'
            for field in ("revenue_cents", "cost_cents", "gross_profit_cents", "collection_cents", "receivable_cents")
        )
        + f'<td>{esc(row["status_zh"])}</td></tr>'
        for row in payload["projects"]
    )
    max_revenue = max(int(row["revenue_cents"]) for row in payload["projects"])
    chart_rows = "".join(
        f'<div class="bar-row"><span>{esc(row["project_name_zh"])}</span><div class="bar-track"><i style="width:{int(row["revenue_cents"]) * 100 // max_revenue}%"></i></div><strong>{esc(_money(row["revenue_cents"]))}</strong></div>'
        for row in payload["projects"]
    )
    matters = "".join(
        f'<li><strong>{esc(row["matter_zh"])}</strong><span>{esc(row["owner_zh"])} · {esc(row["next_step_zh"])}</span></li>'
        for row in payload["key_matters"]
    )
    sources = "".join(
        f'<tr><td>{esc(row["domain_label_zh"])}</td><td>{esc(row["version_ref"])}</td><td>{esc(row["state"])}</td></tr>'
        for row in payload["source_bindings"]
    )
    raw_tokens = "".join(
        f'<li><code>{esc(key)}</code><span>{value}</span></li>'
        for key, value in canonical_numeric_values(payload).items()
    )
    limitations = "".join(f"<li>{esc(item)}</li>" for item in payload["trust_and_limitations"]["limitations_zh"])
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(payload["report_title_zh"])}</title>
<style>
:root{{--ink:#173d57;--muted:#607684;--line:#d8e2e8;--paper:#fff;--wash:#f3f7f9;--blue:#246c83;--teal:#2d8b78;--amber:#a86a17}}*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--wash);color:#263b49;font:14px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}}a{{color:var(--blue)}}.shell{{display:grid;grid-template-columns:230px minmax(0,1fr);max-width:1440px;margin:auto;background:var(--paper);min-height:100vh}}nav{{position:sticky;top:0;height:100vh;padding:28px 22px;background:#16394f;color:#fff}}nav strong{{display:block;font-size:18px}}nav small{{display:block;margin:4px 0 24px;color:#bad1df}}nav a{{display:block;min-height:44px;padding:10px 0;color:#eaf4f8;text-decoration:none;border-bottom:1px solid #31566c}}main{{min-width:0;padding:44px 54px 72px}}.cover{{padding-bottom:28px;border-bottom:3px solid var(--blue)}}.eyebrow{{color:var(--teal);font-weight:800;letter-spacing:.08em}}h1{{max-width:850px;margin:8px 0 10px;color:var(--ink);font-size:40px;line-height:1.18}}h2{{margin:0 0 14px;color:var(--ink);font-size:24px}}.meta{{color:var(--muted)}}.notice{{margin-top:20px;padding:13px 15px;border-left:4px solid var(--amber);background:#fff9ee}}section{{scroll-margin-top:16px;padding-top:34px}}.metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}.metric{{padding:18px;border:1px solid var(--line);border-radius:10px;background:#fff}}.metric span,.metric small{{display:block;color:var(--muted)}}.metric strong{{display:block;margin:5px 0;color:var(--ink);font-size:24px}}.table-wrap{{max-width:100%;overflow:auto;border:1px solid var(--line);border-radius:9px}}table{{width:100%;border-collapse:collapse;white-space:nowrap}}th,td{{padding:12px 13px;border-bottom:1px solid var(--line);text-align:right}}thead th{{background:#eaf4f8;color:var(--ink)}}th:first-child,td:first-child{{text-align:left}}.bar-row{{display:grid;grid-template-columns:110px minmax(120px,1fr) 130px;gap:12px;align-items:center;margin:12px 0}}.bar-track{{height:14px;border-radius:7px;background:#e4edf1;overflow:hidden}}.bar-track i{{display:block;height:100%;background:linear-gradient(90deg,var(--blue),var(--teal))}}.matters{{display:grid;gap:9px;padding:0;list-style:none}}.matters li{{display:flex;justify-content:space-between;gap:16px;padding:14px;border:1px solid var(--line);border-radius:8px}}.matters span{{color:var(--muted)}}.raw-values{{columns:2;list-style:none;padding:0}}.raw-values li{{display:flex;min-width:0;justify-content:space-between;gap:10px;padding:6px 0;border-bottom:1px dotted var(--line)}}.raw-values code,footer{{overflow-wrap:anywhere;word-break:break-word}}footer{{margin-top:44px;padding-top:20px;border-top:1px solid var(--line);color:var(--muted)}}
@media(max-width:800px){{.shell{{display:block}}nav{{position:static;height:auto}}nav a{{display:inline-flex;align-items:center;margin-right:14px}}main{{padding:28px 18px 52px}}h1{{font-size:31px}}.metrics{{grid-template-columns:1fr 1fr}}.matters li{{display:grid}}.raw-values{{columns:1}}.raw-values li{{display:grid;grid-template-columns:minmax(0,1fr) auto}}}}
@media(max-width:480px){{.metrics{{grid-template-columns:1fr}}.bar-row{{grid-template-columns:80px 1fr}}.bar-row strong{{grid-column:2}}}}
@media print{{@page{{size:A4;margin:15mm 13mm}}body{{background:#fff;font-size:9pt}}.shell{{display:block}}nav{{display:none}}main{{padding:0}}h1{{font-size:24pt}}section{{break-before:page;padding-top:0}}#summary{{break-before:auto}}.metric,.table-wrap,.bar-row,.matters li{{break-inside:avoid}}.metrics{{grid-template-columns:repeat(3,1fr)}}a{{color:inherit;text-decoration:none}}footer{{break-before:page}}}}
</style></head><body><div class="shell"><nav aria-label="章节导航"><strong>KMFA 经营报告</strong><small>{esc(payload["period"]["period_label_zh"])}</small><a href="#summary">经营摘要</a><a href="#projects">项目经营</a><a href="#funds">财务与资金</a><a href="#tax">税务与政策</a><a href="#matters">重点事项</a><a href="#sources">来源与专业附表</a></nav><main>
<header class="cover"><span class="eyebrow">内部管理复核 · 公开合成演示</span><h1>{esc(payload["report_title_zh"])}</h1><p class="meta">{esc(payload["company_name_zh"])} · {esc(payload["period"]["period_label_zh"])} · 报告版本 {esc(payload["report_version_id"])}</p><div class="notice"><strong>{esc(payload["trust_and_limitations"]["status_zh"])}</strong><br>{esc(payload["trust_and_limitations"]["explanation_zh"])}</div></header>
<section id="summary"><h2>经营摘要</h2><div class="metrics">{cards}</div></section>
<section id="projects"><h2>项目经营</h2><div class="table-wrap"><table><thead><tr><th>项目</th><th>收入</th><th>成本</th><th>毛利</th><th>回款</th><th>应收</th><th>状态</th></tr></thead><tbody>{project_rows}</tbody></table></div><div aria-label="项目收入图">{chart_rows}</div></section>
<section id="funds"><h2>财务与资金</h2><p>期末现金 <strong>{_money(payload["headline"]["cash_balance_cents"])}</strong>；期末应收 <strong>{_money(payload["headline"]["receivable_cents"])}</strong>。金额均来自同一份整数分事实数据。</p></section>
<section id="tax"><h2>税务与政策</h2><p>本期共有 <strong>{payload["headline"]["tax_review_count"]}</strong> 项公开合成税务资料需要按适用范围复核；本报告不替代专业判断。</p></section>
<section id="matters"><h2>重点事项</h2><ol class="matters">{matters}</ol></section>
<section id="sources"><h2>来源与专业附表</h2><div class="table-wrap"><table><thead><tr><th>资料</th><th>绑定版本</th><th>状态</th></tr></thead><tbody>{sources}</tbody></table></div><h3>跨格式核对值（整数）</h3><ul class="raw-values">{raw_tokens}</ul><p><strong>限制说明</strong></p><ul>{limitations}</ul></section>
<footer>报告指纹：{esc(payload["report_payload_fingerprint"])}<br>本文件由 S21-P2 生成；未执行审批、发布、GitHub 上传或 App 重装。</footer>
</main></div></body></html>\n'''


def render_appendix_csv(payload: Mapping[str, Any]) -> str:
    """Render an Excel-compatible UTF-8 CSV without formulas or numeric coercion."""

    output = io.StringIO(newline="")
    columns = (
        "record_type", "record_id", "label_zh", "value_integer", "unit",
        "display_value", "formula_explanation_zh", "source_ref", "difference_integer",
        "report_version_id", "report_payload_fingerprint",
    )
    writer = csv.DictWriter(output, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in payload["metrics"]:
        writer.writerow({
            "record_type": "METRIC", "record_id": _safe_csv_text(row["metric_id"]),
            "label_zh": _safe_csv_text(row["label_zh"]), "value_integer": int(row["value_integer"]),
            "unit": row["unit"], "display_value": row["display_value"],
            "formula_explanation_zh": _safe_csv_text(row["formula_zh"]),
            "source_ref": _safe_csv_text(row["source_ref"]), "difference_integer": 0,
            "report_version_id": payload["report_version_id"],
            "report_payload_fingerprint": payload["report_payload_fingerprint"],
        })
    for project in payload["projects"]:
        for field, label in (
            ("revenue_cents", "收入"), ("cost_cents", "成本"),
            ("gross_profit_cents", "毛利"), ("collection_cents", "回款"),
            ("receivable_cents", "应收"),
        ):
            writer.writerow({
                "record_type": "PROJECT_FACT", "record_id": f"{project['project_id']}:{field}",
                "label_zh": f"{project['project_name_zh']} {label}", "value_integer": int(project[field]),
                "unit": "CENTS", "display_value": _money(project[field]),
                "formula_explanation_zh": "来源事实直接展示" if field not in {"gross_profit_cents", "receivable_cents"} else ("收入减成本" if field == "gross_profit_cents" else "收入减回款"),
                "source_ref": _safe_csv_text(project["source_ref"]), "difference_integer": 0,
                "report_version_id": payload["report_version_id"],
                "report_payload_fingerprint": payload["report_payload_fingerprint"],
            })
    return "\ufeff" + output.getvalue()


def render_report_pdf(payload: Mapping[str, Any], target: Path | str) -> None:
    """Create a paginated A4 PDF with repeated headers and readable tables."""

    from reportlab import rl_config
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    rl_config.invariant = 1
    font_name = "STSong-Light"
    for candidate in (
        Path("/System/Library/Fonts/STHeiti Medium.ttc"),
        Path("/System/Library/Fonts/STHeiti Light.ttc"),
        Path("/System/Library/Fonts/Supplemental/Songti.ttc"),
    ):
        if not candidate.is_file():
            continue
        try:
            font_name = "KMFAChinese"
            if font_name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(font_name, str(candidate)))
            break
        except Exception:  # pragma: no cover - fallback depends on host font support
            font_name = "STSong-Light"
    if font_name == "STSong-Light" and font_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(UnicodeCIDFont(font_name))
    styles = getSampleStyleSheet()
    title = ParagraphStyle("kmfa-title", parent=styles["Title"], fontName=font_name, fontSize=22, leading=28, textColor=colors.HexColor("#173D57"), alignment=TA_LEFT)
    h2 = ParagraphStyle("kmfa-h2", parent=styles["Heading2"], fontName=font_name, fontSize=14, leading=19, spaceBefore=7 * mm, spaceAfter=3 * mm, textColor=colors.HexColor("#214D68"))
    body = ParagraphStyle("kmfa-body", parent=styles["BodyText"], fontName=font_name, fontSize=8.5, leading=13, textColor=colors.HexColor("#263B49"))
    small = ParagraphStyle("kmfa-small", parent=body, fontSize=6.6, leading=9)
    right = ParagraphStyle("kmfa-right", parent=body, alignment=TA_RIGHT)
    center = ParagraphStyle("kmfa-center", parent=body, alignment=TA_CENTER)

    def paragraph(value: Any, style: Any = body) -> Any:
        return Paragraph(html.escape(str(value)), style)

    def page_frame(canvas: Any, document: Any) -> None:
        canvas.saveState()
        canvas.setFont(font_name, 7)
        canvas.setFillColor(colors.HexColor("#607684"))
        canvas.drawString(16 * mm, 286 * mm, f"KMFA 经营报告 · {payload['report_version_id']}")
        canvas.drawRightString(194 * mm, 11 * mm, f"第 {document.page} 页")
        canvas.setStrokeColor(colors.HexColor("#D8E2E8"))
        canvas.line(16 * mm, 282 * mm, 194 * mm, 282 * mm)
        canvas.restoreState()

    target_path = Path(target)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(target_path), pagesize=A4, rightMargin=16 * mm, leftMargin=16 * mm,
        topMargin=20 * mm, bottomMargin=18 * mm, title=str(payload["report_title_zh"]),
        author="KMFA", subject=f"S21-P2 {payload['report_version_id']}",
    )
    story: list[Any] = [
        paragraph(payload["report_title_zh"], title),
        paragraph(f"{payload['company_name_zh']} · {payload['period']['period_label_zh']} · {payload['report_version_id']}", small),
        Spacer(1, 4 * mm),
        Table(
            [[paragraph(payload["trust_and_limitations"]["status_zh"], body)], [paragraph(payload["trust_and_limitations"]["explanation_zh"], small)]],
            colWidths=[178 * mm], style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF9EE")), ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#D5B27C")), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8)]),
        ),
        paragraph("一、经营摘要", h2),
    ]
    metric_table = [[paragraph("指标", center), paragraph("本期值", center), paragraph("整数核对值", center), paragraph("口径", center)]]
    for row in payload["metrics"]:
        metric_table.append([paragraph(row["label_zh"]), paragraph(row["display_value"], right), paragraph(f"RAW_INTEGER:{row['metric_id']}={row['value_integer']}", small), paragraph(row["formula_zh"], small)])
    table = Table(metric_table, colWidths=[28 * mm, 34 * mm, 60 * mm, 56 * mm], repeatRows=1, splitByRow=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDEEF6")), ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#D8E2E8")), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFB")]), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story.extend([table, paragraph("二、项目经营", h2)])
    project_table = [[paragraph(value, center) for value in ("项目", "收入", "成本", "毛利", "回款", "应收")]]
    for row in payload["projects"]:
        project_table.append([paragraph(row["project_name_zh"]), *[paragraph(_money(row[field]), right) for field in ("revenue_cents", "cost_cents", "gross_profit_cents", "collection_cents", "receivable_cents")]])
    table = Table(project_table, colWidths=[28 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm], repeatRows=1, splitByRow=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDEEF6")), ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#D8E2E8")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story.extend([table, PageBreak(), paragraph("三、专业附表与来源", h2)])
    raw_table = [[paragraph("核对编号", center), paragraph("整数值", center), paragraph("来源", center)]]
    source_by_metric = {str(row["metric_id"]): str(row["source_ref"]) for row in payload["metrics"]}
    for key, value in canonical_numeric_values(payload).items():
        source = source_by_metric.get(key, next((str(row["source_ref"]) for row in payload["projects"] if key.startswith(str(row["project_id"]) + ":")), "REPORT_PAYLOAD"))
        raw_table.append([paragraph(f"RAW_INTEGER:{key}", small), paragraph(value, right), paragraph(source, small)])
    table = Table(raw_table, colWidths=[73 * mm, 34 * mm, 71 * mm], repeatRows=1, splitByRow=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDEEF6")), ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8E2E8")), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFB")]), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    source_rows = [[paragraph("资料类别", center), paragraph("绑定版本", center)]] + [[paragraph(row["domain_label_zh"]), paragraph(row["version_ref"], small)] for row in payload["source_bindings"]]
    source_table = Table(source_rows, colWidths=[55 * mm, 123 * mm], repeatRows=1)
    source_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDEEF6")), ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8E2E8")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    limitations = "；".join(payload["trust_and_limitations"]["limitations_zh"])
    story.extend([table, paragraph("四、数据来源", h2), source_table, Spacer(1, 4 * mm), KeepTogether([paragraph("限制说明", h2), paragraph(limitations, body)]), Spacer(1, 3 * mm), paragraph(f"报告指纹：{payload['report_payload_fingerprint']}", small), paragraph("未执行审批、发布、GitHub 上传或 App 重装。", small)])
    document.build(story, onFirstPage=page_frame, onLaterPages=page_frame)


def extract_pdf_text(path: Path | str) -> str:
    import pdfplumber

    with pdfplumber.open(str(path)) as document:
        return "\n".join(page.extract_text() or "" for page in document.pages)


def verify_cross_format(payload: Mapping[str, Any], html_text: str, pdf_path: Path | str, csv_text: str) -> dict[str, Any]:
    canonical = canonical_numeric_values(payload)
    html_values = {key: int(value) for key, value in re.findall(r'data-value-id="([^"]+)" data-raw-integer="(-?\d+)"', html_text)}
    csv_values: dict[str, int] = {}
    with io.StringIO(csv_text.lstrip("\ufeff")) as handle:
        for row in csv.DictReader(handle):
            csv_values[str(row["record_id"])] = int(row["value_integer"])
            if int(row["difference_integer"]) != 0:
                raise ReportGenerationError("CSV_DIFFERENCE_NONZERO", "专业附表存在非零差异", status=409)
    pdf_text = re.sub(r"\s+", "", extract_pdf_text(pdf_path))
    pdf_missing = [
        f"RAW_INTEGER:{key}={value}"
        for key, value in canonical.items()
        if f"RAW_INTEGER:{key}={value}" not in pdf_text
        and f"RAW_INTEGER:{key}{value}" not in pdf_text
    ]
    if html_values != canonical or csv_values != canonical or pdf_missing:
        raise ReportGenerationError("CROSS_FORMAT_DIFFERENCE", "HTML、PDF 与专业附表数字不一致", status=409)
    return {
        "schema_version": "kmfa.v015.s21p2.cross_format.v1",
        "numeric_value_count": len(canonical),
        "html_value_count": len(html_values),
        "pdf_value_count": len(canonical) - len(pdf_missing),
        "csv_value_count": len(csv_values),
        "difference_integer": 0,
        "status": "PASS",
    }


def generate_bundle(payload: Mapping[str, Any], output_dir: Path | str) -> dict[str, Any]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    html_text = render_report_html(payload)
    csv_text = render_appendix_csv(payload)
    html_path, pdf_path, csv_path = target / HTML_FILENAME, target / PDF_FILENAME, target / CSV_FILENAME
    html_path.write_text(html_text, encoding="utf-8")
    csv_path.write_text(csv_text, encoding="utf-8")
    render_report_pdf(payload, pdf_path)
    consistency = verify_cross_format(payload, html_text, pdf_path, csv_text)
    files = {
        "HTML": {"filename": HTML_FILENAME, "content_type": "text/html; charset=utf-8", "sha256": _file_digest(html_path.read_bytes()), "size_bytes": html_path.stat().st_size},
        "PDF": {"filename": PDF_FILENAME, "content_type": "application/pdf", "sha256": _file_digest(pdf_path.read_bytes()), "size_bytes": pdf_path.stat().st_size},
        "CSV": {"filename": CSV_FILENAME, "content_type": "text/csv; charset=utf-8", "sha256": _file_digest(csv_path.read_bytes()), "size_bytes": csv_path.stat().st_size},
    }
    return {"files": files, "cross_format_consistency": consistency}


class ReportExportJournal:
    """Append-only export history; bundle files are immutable by fingerprint."""

    def __init__(self, event_path: Path | str = DEFAULT_EVENT_PATH, bundle_root: Path | str = DEFAULT_BUNDLE_ROOT) -> None:
        self.path = Path(event_path)
        self.bundle_root = Path(bundle_root)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    def _locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.lock_path.open("a+", encoding="utf-8")
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        return handle

    def _read_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        previous = "GENESIS"
        for index, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ReportGenerationError("EXPORT_HISTORY_CORRUPTED", "报告导出历史无法读取", status=409) from error
            supplied = row.get("event_hash")
            expected = _digest({key: value for key, value in row.items() if key != "event_hash"})
            if row.get("sequence") != index or row.get("previous_event_hash") != previous or supplied != expected:
                raise ReportGenerationError("EXPORT_HISTORY_CORRUPTED", "报告导出历史完整性校验失败", status=409)
            rows.append(row)
            previous = str(supplied)
        return rows

    def read(self) -> list[dict[str, Any]]:
        lock = self._locked()
        try:
            return self._read_unlocked()
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def create(self, report: Mapping[str, Any], *, idempotency_key: str, recorded_at: str | None = None) -> dict[str, Any]:
        key = _text(idempotency_key, "请求编号", minimum=8, maximum=120)
        payload = build_report_payload(report)
        fingerprint = str(payload["report_payload_fingerprint"])
        lock = self._locked()
        try:
            rows = self._read_unlocked()
            existing = next((row for row in rows if row["idempotency_key"] == key), None)
            if existing:
                if existing["report_payload_fingerprint"] != fingerprint:
                    raise ReportGenerationError("IDEMPOTENCY_CONFLICT", "同一请求编号不能导出不同报告", status=409)
                return existing
            same_version = next((row for row in rows if row["report_version_id"] == report["report_version_id"]), None)
            if same_version:
                if same_version["report_payload_fingerprint"] != fingerprint:
                    raise ReportGenerationError("REPORT_VERSION_EXPORT_CONFLICT", "同一报告版本不能对应不同数字", status=409)
                return same_version
            export_id = "EXPORT-" + hashlib.sha256(fingerprint.encode()).hexdigest()[:16].upper()
            bundle_dir = self.bundle_root / export_id
            if bundle_dir.exists() and any(bundle_dir.iterdir()):
                raise ReportGenerationError("EXPORT_BUNDLE_CONFLICT", "导出目录已存在且无法安全覆盖", status=409)
            bundle = generate_bundle(payload, bundle_dir)
            row: dict[str, Any] = {
                "schema_version": "kmfa.v015.s21p2.report_export_event.v1",
                "event_type": "REPORT_EXPORT_CREATED",
                "export_id": export_id,
                "report_version_id": report["report_version_id"],
                "report_payload_fingerprint": fingerprint,
                "source_binding_fingerprint": payload["source_binding_fingerprint"],
                "formula_binding_fingerprint": payload["formula_binding_fingerprint"],
                "files": bundle["files"],
                "cross_format_consistency": bundle["cross_format_consistency"],
                "data_classification": DATA_CLASSIFICATION,
                "formal_business_report": False,
                "approval_or_publication_performed": False,
                "raw_access_count": 0,
                "idempotency_key": key,
                "recorded_at": recorded_at or _now(),
                "sequence": len(rows) + 1,
                "previous_event_hash": rows[-1]["event_hash"] if rows else "GENESIS",
            }
            row["event_hash"] = _digest(row)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            self._read_unlocked()
            return row
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def get(self, export_id: str) -> dict[str, Any]:
        key = _text(export_id, "导出编号", maximum=80)
        for row in self.read():
            if row["export_id"] == key:
                return row
        raise ReportGenerationError("EXPORT_NOT_FOUND", "没有找到这份报告导出", status=404)

    def list(self) -> dict[str, Any]:
        rows = list(reversed(self.read()))
        return {"schema_version": "kmfa.v015.s21p2.report_export_list.v1", "export_count": len(rows), "exports": rows}

    def file_path(self, export_id: str, format_name: str) -> tuple[Path, dict[str, Any]]:
        row = self.get(export_id)
        format_key = _text(format_name, "导出格式", maximum=8).upper()
        if format_key not in FORMATS:
            raise ReportGenerationError("EXPORT_FORMAT_NOT_FOUND", "没有找到这个导出格式", status=404)
        metadata = row["files"][format_key]
        path = self.bundle_root / row["export_id"] / metadata["filename"]
        if not path.is_file() or _file_digest(path.read_bytes()) != metadata["sha256"]:
            raise ReportGenerationError("EXPORT_FILE_CORRUPTED", "报告导出文件完整性校验失败", status=409)
        return path, metadata


def verify_phase() -> dict[str, Any]:
    """Run 60 deterministic checks, including real PDF extraction."""

    checks: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, detail: str) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "detail": detail})

    report = demo_report_model()
    payload = build_report_payload(report)
    values = canonical_numeric_values(payload)
    for key, expected in (
        ("project-count", len(payload["projects"]) == 3),
        ("metric-count", len(payload["metrics"]) == 6),
        ("source-count", len(payload["source_bindings"]) == 6),
        ("revenue", payload["headline"]["revenue_cents"] == 128_450_000),
        ("cost", payload["headline"]["cost_cents"] == 96_610_000),
        ("gross-profit", payload["headline"]["gross_profit_cents"] == 31_840_000),
        ("collection", payload["headline"]["collection_cents"] == 100_800_000),
        ("receivables", payload["headline"]["receivable_cents"] == 27_650_000),
        ("margin", payload["headline"]["gross_margin_bps"] == 2_479),
        ("fingerprint", str(payload["report_payload_fingerprint"]).startswith("sha256:")),
    ):
        add("PAYLOAD-" + key.upper(), bool(expected), key)
    for row in payload["projects"]:
        add("PROJECT-" + row["project_id"] + "-GP", row["revenue_cents"] - row["cost_cents"] == row["gross_profit_cents"], "income minus cost")
        add("PROJECT-" + row["project_id"] + "-AR", row["revenue_cents"] - row["collection_cents"] == row["receivable_cents"], "income minus collection")
    add("PAYLOAD-VALUE-COUNT", len(values) == 21, "21 exact integers")
    add("PAYLOAD-CLASSIFICATION", payload["data_classification"] == DATA_CLASSIFICATION, DATA_CLASSIFICATION)
    add("PAYLOAD-NO-APPROVAL", payload["approval_or_publication_performed"] is False, "closed")
    add("PAYLOAD-NO-RAW", payload["raw_access_count"] == 0, "zero")

    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        journal = ReportExportJournal(root / "exports.jsonl", root / "bundles")
        first = journal.create(report, idempotency_key="verify-export-001", recorded_at="2026-07-17T00:01:00+00:00")
        same = journal.create(report, idempotency_key="verify-export-001", recorded_at="2026-07-17T00:01:00+00:00")
        html_path, _ = journal.file_path(first["export_id"], "HTML")
        pdf_path, _ = journal.file_path(first["export_id"], "PDF")
        csv_path, _ = journal.file_path(first["export_id"], "CSV")
        html_text, csv_text, pdf_text = html_path.read_text(encoding="utf-8"), csv_path.read_text(encoding="utf-8"), extract_pdf_text(pdf_path)
        html_checks = (
            ("RESPONSIVE", "@media(max-width:800px)" in html_text), ("PRINT", "@media print" in html_text),
            ("NAV", 'aria-label="章节导航"' in html_text), ("SOURCE", 'id="sources"' in html_text),
            ("DESIGN", "--blue:#246c83" in html_text), ("VERSION", report["report_version_id"] in html_text),
            ("FINGERPRINT", payload["report_payload_fingerprint"] in html_text), ("VALUES", html_text.count("data-raw-integer=") == 21),
            ("TABLE", "<table>" in html_text), ("NO-PUBLISH", "未执行审批、发布" in html_text),
        )
        for name, passed in html_checks:
            add("HTML-" + name, passed, name)
        csv_rows = list(csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff"))))
        csv_checks = (
            ("BOM", csv_text.startswith("\ufeff")), ("ROWS", len(csv_rows) == 21),
            ("VALUES", {row["record_id"]: int(row["value_integer"]) for row in csv_rows} == values),
            ("DIFFERENCE", all(int(row["difference_integer"]) == 0 for row in csv_rows)),
            ("FORMULA-EXPLANATION", all(row["formula_explanation_zh"] for row in csv_rows)),
            ("SOURCE", all(row["source_ref"] for row in csv_rows)),
            ("VERSION", all(row["report_version_id"] == report["report_version_id"] for row in csv_rows)),
            ("FINGERPRINT", all(row["report_payload_fingerprint"] == payload["report_payload_fingerprint"] for row in csv_rows)),
            ("NO-FORMULA-CELL", not any(row["value_integer"].startswith("=") for row in csv_rows)),
            ("INTEGER", all(re.fullmatch(r"-?\d+", row["value_integer"]) is not None for row in csv_rows)),
        )
        for name, passed in csv_checks:
            add("CSV-" + name, bool(passed), name)
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        normalized_pdf = re.sub(r"\s+", "", pdf_text)
        pdf_checks = (
            ("PAGES", len(reader.pages) >= 2), ("TITLE", "KMFA月度经营报告" in normalized_pdf),
            ("VERSION", report["report_version_id"] in normalized_pdf), ("PAGE-NUMBER", "第1页" in normalized_pdf and "第2页" in normalized_pdf),
            ("METRIC-TABLE", "经营摘要" in normalized_pdf), ("PROJECT-TABLE", "项目经营" in normalized_pdf),
            ("APPENDIX", "专业附表与来源" in normalized_pdf), ("SOURCES", "数据来源" in normalized_pdf),
            ("RAW-VALUES", all(
                f"RAW_INTEGER:{key}={value}" in normalized_pdf
                or f"RAW_INTEGER:{key}{value}" in normalized_pdf
                for key, value in values.items()
            )),
            ("NO-PUBLISH", "未执行审批、发布" in normalized_pdf),
        )
        for name, passed in pdf_checks:
            add("PDF-" + name, bool(passed), name)
        bundle_checks = (
            ("FORMATS", set(first["files"]) == set(FORMATS)),
            ("CONSISTENCY", first["cross_format_consistency"]["status"] == "PASS"),
            ("ZERO-DIFFERENCE", first["cross_format_consistency"]["difference_integer"] == 0),
            ("IDEMPOTENT", same["event_hash"] == first["event_hash"]),
            ("HISTORY", journal.list()["export_count"] == 1),
            ("FILES", all((root / "bundles" / first["export_id"] / first["files"][name]["filename"]).is_file() for name in FORMATS)),
            ("HASHES", all(str(first["files"][name]["sha256"]).startswith("sha256:") for name in FORMATS)),
            ("NO-APPROVAL", first["approval_or_publication_performed"] is False),
            ("NO-RAW", first["raw_access_count"] == 0),
            ("PRIVATE-RUNTIME", ".codex_private_runtime" in str(DEFAULT_RUNTIME_ROOT)),
        )
        for name, passed in bundle_checks:
            add("BUNDLE-" + name, bool(passed), name)
    failed = [row for row in checks if row["status"] != "PASS"]
    return {
        "schema_version": "kmfa.v015.s21p2.public_verification.v1",
        "checks": checks,
        "public_check_count": len(checks),
        "public_check_pass_count": len(checks) - len(failed),
        "public_check_failed_count": len(failed),
        "status": "PASS" if not failed and len(checks) == 60 else "FAIL",
    }


def main() -> int:
    result = verify_phase()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
