from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Mapping

from .benchmark import benchmark_model_rows
from .interpretation import count_reference_items, is_reference_item, reference_items, reference_platforms
from .quality_gates import build_quality_gate_status
from .reference_gaps import (
    external_reference_gap_summary_for_items,
    gap_action_label,
    gap_type_label,
)


def write_policy_report(
    report_path: str | Path,
    run_id: str,
    stats: Mapping[str, int],
    documents: list[Mapping[str, Any]],
    interpretation_items: list[Mapping[str, Any]] | None = None,
    queue_items: list[Mapping[str, Any]] | None = None,
    timeline_items: list[Mapping[str, Any]] | None = None,
) -> dict[str, str]:
    pdf_path = Path(report_path)
    if pdf_path.suffix.lower() != ".pdf":
        pdf_path = pdf_path.with_suffix(".pdf")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    html_path = pdf_path.with_suffix(".html")
    markdown_path = pdf_path.with_suffix(".md")
    dashboard_path = pdf_path.with_name(f"{pdf_path.stem}_dashboard.html")

    materials = interpretation_items or []
    queue = queue_items or []
    timeline = timeline_items or []
    markdown_path.write_text(
        _render_markdown(run_id, stats, documents, materials, queue, timeline),
        encoding="utf-8",
    )
    html_path.write_text(
        _render_html(run_id, stats, documents, markdown_path.name, materials, queue, timeline),
        encoding="utf-8",
    )
    dashboard_path.write_text(
        _render_dashboard_html(run_id, stats, documents, materials, queue, timeline),
        encoding="utf-8",
    )
    _write_pdf_report(pdf_path, html_path, run_id, stats, documents, materials, queue, timeline)
    return {
        "pdf_path": str(pdf_path),
        "html_path": str(html_path),
        "markdown_path": str(markdown_path),
        "dashboard_path": str(dashboard_path),
    }


def write_markdown_report(
    report_path: str | Path,
    run_id: str,
    stats: Mapping[str, int],
    documents: list[Mapping[str, Any]],
    interpretation_items: list[Mapping[str, Any]] | None = None,
    queue_items: list[Mapping[str, Any]] | None = None,
    timeline_items: list[Mapping[str, Any]] | None = None,
) -> str:
    paths = write_policy_report(
        Path(report_path).with_suffix(".pdf"),
        run_id,
        stats,
        documents,
        interpretation_items,
        queue_items,
        timeline_items,
    )
    return paths["html_path"]


def report_file_name(run_id: str, documents: list[Mapping[str, Any]]) -> str:
    date_part = _run_date(run_id)
    if not documents:
        return f"{date_part}_政策监测空运行报告.pdf"
    title = _short_file_title(documents[0].get("title"))
    return f"{date_part}_{title}_研究报告.pdf"


def _write_pdf_report(
    pdf_path: Path,
    html_path: Path,
    run_id: str,
    stats: Mapping[str, int],
    documents: list[Mapping[str, Any]],
    interpretation_items: list[Mapping[str, Any]],
    queue_items: list[Mapping[str, Any]],
    timeline_items: list[Mapping[str, Any]],
) -> None:
    minimum_pages = _minimum_pdf_pages(documents)
    if os.environ.get("POLICY_REPORT_FORCE_REPORTLAB_PDF") != "1" and _write_pdf_with_chrome(pdf_path, html_path):
        if _pdf_page_count(pdf_path) >= minimum_pages:
            return
        pdf_path.unlink(missing_ok=True)
    try:
        _write_pdf_with_reportlab(
            pdf_path,
            run_id,
            stats,
            documents,
            interpretation_items,
            queue_items,
            timeline_items,
        )
        return
    except RuntimeError:
        if _write_pdf_with_chrome(pdf_path, html_path):
            return
        raise


def _write_pdf_with_chrome(pdf_path: Path, html_path: Path) -> bool:
    if os.environ.get("POLICY_REPORT_DISABLE_CHROME_PDF") == "1":
        return False
    chrome = _chrome_path()
    if not chrome:
        return False
    pdf_path.unlink(missing_ok=True)
    command = [
        chrome,
        "--headless",
        "--disable-gpu",
        "--disable-extensions",
        "--no-first-run",
        "--no-default-browser-check",
        f"--print-to-pdf={pdf_path.resolve()}",
        html_path.resolve().as_uri(),
    ]
    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=90,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False
    return pdf_path.exists() and pdf_path.stat().st_size > 1024


def _minimum_pdf_pages(documents: list[Mapping[str, Any]]) -> int:
    return 10 if documents else 1


def _pdf_page_count(pdf_path: Path) -> int:
    if not pdf_path.exists():
        return 0
    try:
        import pypdf  # type: ignore

        return len(pypdf.PdfReader(str(pdf_path)).pages)
    except Exception:
        data = pdf_path.read_bytes()
        return len(re.findall(rb"/Type\s*/Page\b", data))


def _chrome_path() -> str | None:
    candidates = [
        os.environ.get("CHROME_PATH"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        shutil.which("google-chrome"),
        shutil.which("chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    return next((path for path in candidates if path and Path(path).exists()), None)


def _write_pdf_with_reportlab(
    pdf_path: Path,
    run_id: str,
    stats: Mapping[str, int],
    documents: list[Mapping[str, Any]],
    interpretation_items: list[Mapping[str, Any]],
    queue_items: list[Mapping[str, Any]],
    timeline_items: list[Mapping[str, Any]],
) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            ListFlowable,
            ListItem,
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    except ImportError as exc:
        raise RuntimeError(
            "PDF generation requires Google Chrome headless or the reportlab package."
        ) from exc

    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    except Exception:
        pass

    styles = getSampleStyleSheet()
    base_font = "STSong-Light"
    styles.add(
        ParagraphStyle(
            name="ChineseTitle",
            parent=styles["Title"],
            fontName=base_font,
            fontSize=19,
            leading=25,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0a3f52"),
            wordWrap="CJK",
        )
    )
    styles.add(
        ParagraphStyle(
            name="ChineseHeading",
            parent=styles["Heading2"],
            fontName=base_font,
            fontSize=14,
            leading=20,
            spaceBefore=12,
            spaceAfter=8,
            textColor=colors.HexColor("#0a3f52"),
            wordWrap="CJK",
        )
    )
    styles.add(
        ParagraphStyle(
            name="ChineseBody",
            parent=styles["BodyText"],
            fontName=base_font,
            fontSize=10.5,
            leading=17,
            spaceAfter=6,
            wordWrap="CJK",
        )
    )
    styles.add(
        ParagraphStyle(
            name="ChineseSmall",
            parent=styles["BodyText"],
            fontName=base_font,
            fontSize=8.5,
            leading=13,
            textColor=colors.HexColor("#5f6b7a"),
            wordWrap="CJK",
        )
    )

    story: list[Any] = [
        Paragraph("中国政策文件单文件研究分析报告", styles["ChineseTitle"]),
        Spacer(1, 5 * mm),
    ]
    metrics = [
        ["运行编号", run_id],
        ["研究文件", str(len(documents))],
        ["发现线索", str(stats.get("documents_discovered", 0))],
        ["有效参考", f"{_reference_count(stats, interpretation_items)}/{_reference_min(stats)}"],
        ["外部平台", f"{_platform_count(interpretation_items)}/{_platform_min(stats)}"],
    ]
    table = Table(metrics, colWidths=[28 * mm, 120 * mm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), base_font),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#edf4f7")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d9e1ea")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([table, Spacer(1, 4 * mm)])
    _pdf_heading(story, styles, "一、执行摘要")
    story.append(Paragraph(_escape_pdf_text(_executive_summary(stats, documents)), styles["ChineseBody"]))
    _pdf_heading(story, styles, "二、重点文件深度研判")
    if not documents:
        story.append(Paragraph("本次运行未发现符合条件的政策文件线索。", styles["ChineseBody"]))
    material_map = _materials_by_document(reference_items(interpretation_items))
    for index, doc in enumerate(documents, start=1):
        title = _clean_title(doc.get("title"))
        story.append(Paragraph(f"{index}. {_escape_pdf_text(title)}", styles["ChineseHeading"]))
        source_line = (
            f"来源权威：{doc.get('authority_tier_snapshot') or '?'} / "
            f"{doc.get('authority_score_snapshot') or 'NA'} / {doc.get('source_name') or '未知来源'}"
        )
        story.append(Paragraph(_escape_pdf_text(source_line), styles["ChineseSmall"]))
        story.append(
            Paragraph(
                _escape_pdf_text(_report_summary(doc, material_map.get(str(doc.get("document_id")), []))),
                styles["ChineseBody"],
            )
        )
        for section_title, value in (
            ("核心要点", doc.get("policy_points_json")),
            ("商业影响", doc.get("business_impacts_json")),
            ("风险与不确定性", doc.get("risks_json")),
            ("建议行动", doc.get("actions_json")),
        ):
            _pdf_list(story, styles, section_title, _json_items(value))
        url = str(doc.get("canonical_url") or doc.get("url") or "")
        if url:
            story.append(Paragraph(_escape_pdf_text(f"原文链接：{url}"), styles["ChineseSmall"]))
        for chapter in _deep_analysis_chapters(doc, material_map.get(str(doc.get("document_id")), [])):
            _pdf_heading(story, styles, chapter["title"])
            for paragraph in chapter["paragraphs"]:
                story.append(Paragraph(_escape_pdf_text(paragraph), styles["ChineseBody"]))
            story.append(PageBreak())

    _pdf_heading(story, styles, "三、外部研究与解读资料来源")
    refs = reference_items(interpretation_items)
    if refs:
        for item in refs[:12]:
            text = f"{item.get('title') or '外部参考'}｜{_material_meta_text(item)}｜{item.get('url') or ''}"
            story.append(Paragraph(_escape_pdf_text(text), styles["ChineseSmall"]))
    else:
        story.append(Paragraph("本次运行未生成可计入门槛的外部参考。", styles["ChineseBody"]))

    _pdf_heading(story, styles, "四、待生产研究报告队列")
    for index, item in enumerate(queue_items[:12], start=1):
        text = (
            f"{index}. {item.get('primary_industry') or item.get('industry') or '待研判行业'}｜"
            f"{item.get('sort_time') or item.get('published_date') or item.get('discovered_at') or '未知时间'}｜"
            f"{item.get('administrative_level') or 'unknown'}｜{item.get('source_name') or '未知来源'}｜"
            f"{_clean_title(item.get('title'))}"
        )
        story.append(Paragraph(_escape_pdf_text(text), styles["ChineseSmall"]))
    if not queue_items:
        story.append(Paragraph("当前没有待生产研究报告，或本次尚未同步到候选文件。", styles["ChineseBody"]))

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title="中国政策文件单文件研究分析报告",
    )
    doc.build(story)


def _pdf_heading(story: list[Any], styles: Mapping[str, Any], title: str) -> None:
    from reportlab.platypus import Paragraph

    story.append(Paragraph(title, styles["ChineseHeading"]))


def _pdf_list(story: list[Any], styles: Mapping[str, Any], title: str, items: list[object]) -> None:
    from reportlab.platypus import ListFlowable, ListItem, Paragraph

    if not items:
        return
    story.append(Paragraph(title, styles["ChineseSmall"]))
    story.append(
        ListFlowable(
            [
                ListItem(Paragraph(_escape_pdf_text(str(item)), styles["ChineseBody"]))
                for item in items
            ],
            bulletType="bullet",
            leftIndent=14,
        )
    )


def _escape_pdf_text(value: object) -> str:
    return html.escape(str(value or ""), quote=False).replace("\n", "<br/>")


def _run_date(run_id: str) -> str:
    match = re.search(r"run_(\d{8})", run_id)
    if match:
        return match.group(1)
    match = re.search(r"^(\d{8})\d{2}$", run_id)
    if match:
        return match.group(1)
    return "report"


def _short_file_title(value: object) -> str:
    text = _clean_title(value)
    quoted = re.search(r"[《「](.+?)[》」]", text)
    if quoted:
        text = quoted.group(1)
    text = text.split()[0] if len(text.split()) > 1 and len(text.split()[0]) >= 8 else text
    text = re.sub(r"(政策解读|一图读懂)$", "", text)
    text = re.sub(r"^(国务院办公厅|国务院|[\u4e00-\u9fff]{2,12}人民政府办公厅|[\u4e00-\u9fff]{2,12}人民政府)关于", "", text)
    text = re.sub(r"^(关于|进一步优化|进一步加强|推进|促进)", "", text)
    text = re.sub(r"的(意见|通知|批复|公告|规划|办法|方案|条例|规定)$", r"\1", text)
    text = re.sub(r"[\s/\\:*?\"<>|,，。；;：:！!？?、]+", "", text)
    text = re.sub(r"_{2,}", "_", text).strip("._- ")
    if "留用地" in text and "高效开发利用" in text:
        text = "农村集体土地留用地高效开发利用意见"
    elif "粤港澳大湾区" in text and "行政法规" in text:
        text = "粤港澳大湾区九市行政法规调整批复"
    elif "香港机动车" in text and "港珠澳大桥" in text:
        text = "香港机动车经港珠澳大桥入出内地办法"
    if not text:
        text = "未命名政策文件"
    return text[:24]


def _render_markdown(
    run_id: str,
    stats: Mapping[str, int],
    documents: list[Mapping[str, Any]],
    interpretation_items: list[Mapping[str, Any]],
    queue_items: list[Mapping[str, Any]],
    timeline_items: list[Mapping[str, Any]],
) -> str:
    material_map = _materials_by_document(interpretation_items)
    lines = [
        "# 中国政策文件单文件研究分析报告",
        "",
        f"- 运行编号：`{run_id}`",
        f"- 本报告研究文件数：{len(documents)}",
        f"- 覆盖来源数：{stats.get('sources_considered', 0)}",
        f"- 抓取页面数：{stats.get('pages_fetched', 0)}",
        f"- 发现文件线索：{stats.get('documents_discovered', 0)}",
        f"- 新增文件：{stats.get('new_documents', 0)}",
        f"- 已分析文件：{stats.get('analyzed_documents', 0)}",
        f"- 外部研究/解读资料：{stats.get('interpretation_items', len(interpretation_items))}",
        f"- 有效外部参考：{_reference_count(stats, interpretation_items)} / {_reference_min(stats)}",
        f"- 外部参考缺口队列：{stats.get('external_reference_gaps', external_reference_gap_summary_for_items(interpretation_items).get('pending_count', 0))}",
        f"- 外部参考达标：{_reference_status(stats, interpretation_items)}",
        f"- 外部采集健康度：尝试 {stats.get('interpretation_attempts', len(interpretation_items))}，计入 {stats.get('interpretation_reference_successes', _reference_count(stats, interpretation_items))}，缺 key {stats.get('interpretation_missing_api_keys', 0)}，需授权 {stats.get('interpretation_auth_required', 0)}，已配授权 {stats.get('interpretation_auth_configured', 0)}，待接解析器 {stats.get('interpretation_auth_parser_pending', 0)}，失败 {stats.get('interpretation_failed_requests', 0)}。",
        f"- 公开网页正文：站内搜索 {stats.get('public_site_searches', 0)}，站内结果 {stats.get('public_site_results', 0)}，中文公开搜索 {stats.get('public_search_html_searches', 0)}，中文搜索结果 {stats.get('public_search_html_results', 0)}，抓取 {stats.get('article_pages_fetched', 0)}，摘录 {stats.get('article_excerpts_extracted', 0)}，受限 {stats.get('article_pages_blocked', 0)}，失败 {stats.get('article_pages_failed', 0)}。",
        f"- 视频解析：详情增强 {stats.get('video_details_enriched', 0)}，作者页 {stats.get('video_author_profiles_enriched', 0)}，字幕摘录 {stats.get('video_subtitles_extracted', 0)}，评论摘录 {stats.get('video_comments_extracted', 0)}，弹幕摘录 {stats.get('video_danmaku_extracted', 0)}。",
        f"- 附件解析：成功 {stats.get('attachments_parsed', 0)}，失败 {stats.get('attachment_parse_failures', 0)}。",
        "",
        "## 目录",
        "",
        "- [研究质量与交付状态](#研究质量与交付状态)",
        "- [一、执行摘要](#一执行摘要)",
        "- [二、重点文件深度研判](#二重点文件深度研判)",
        "- [三、外部研究与解读资料来源](#三外部研究与解读资料来源)",
        "- [四、待生产研究报告队列](#四待生产研究报告队列)",
        "",
        "## 研究质量与交付状态",
        "",
        f"- 质量门槛：有效参考 {_reference_count(stats, interpretation_items)} / {_reference_min(stats)}，外部平台 {_platform_count(interpretation_items)} / {_platform_min(stats)}。",
        f"- 外部参考缺口：待处理 {stats.get('external_reference_gaps', external_reference_gap_summary_for_items(interpretation_items).get('pending_count', 0))} 项。",
        f"- 平台覆盖：{', '.join(reference_platforms(interpretation_items)) or '暂无可计入平台'}。",
        f"- 附件解析：成功 {stats.get('attachments_parsed', 0)}，失败 {stats.get('attachment_parse_failures', 0)}。",
        f"- 队列状态：待生产报告 {stats.get('queued_reports', len(queue_items))}，当前行业：{stats.get('active_industry_name', '待识别')}。",
        "",
        "## 一、执行摘要",
        "",
        _executive_summary(stats, documents),
        "",
        "## 二、重点文件深度研判",
        "",
    ]
    if not documents:
        lines.append("本次运行未发现符合条件的政策文件线索。")
    for index, doc in enumerate(documents, start=1):
        tier = doc.get("authority_tier_snapshot") or "?"
        score = doc.get("authority_score_snapshot") or "NA"
        lines.extend(
            [
                f"### {index}. {_clean_title(doc.get('title'))}",
                "",
                f"- 来源权威：{tier} / {score} / {doc.get('source_name')}",
                f"- 重要性评分：{doc.get('importance_score') or '待分析'}",
                f"- 文件类型：{_doc_type(doc.get('document_type'))}",
                f"- 原文链接：{doc.get('canonical_url') or doc.get('url')}",
                "",
            ]
        )
        lines.extend(["**综合研判**", "", _report_summary(doc, material_map.get(str(doc.get("document_id")), [])), ""])
        _json_section(lines, "核心要点", doc.get("policy_points_json"))
        _json_section(lines, "商业影响", doc.get("business_impacts_json"))
        _json_section(lines, "风险与不确定性", doc.get("risks_json"))
        _json_section(lines, "建议行动", doc.get("actions_json"))
    lines.extend(["## 三、外部研究与解读资料来源", ""])
    if interpretation_items:
        refs = reference_items(interpretation_items)
        if refs:
            lines.extend(["**计入本报告分析的外部参考**", ""])
        for item in refs:
            meta = _material_meta_text(item)
            lines.append(
                f"- [{item.get('title')}]({item.get('url')})"
                f"｜{meta}｜状态：{item.get('evidence_status')}"
            )
        gap_summary = external_reference_gap_summary_for_items(interpretation_items)
        gaps = gap_summary.get("preview", [])
        if gaps:
            lines.extend(
                [
                    "",
                    f"补充线索和缺口队列已进入运营 dashboard；本报告正文仅保留正式参考清单。当前待处理缺口：{gap_summary.get('pending_count', 0)}。",
                ]
            )
    else:
        lines.append("本次运行未生成外部研究/解读资料入口。")
    lines.extend(["", "## 四、待生产研究报告队列", ""])
    if queue_items:
        for index, item in enumerate(queue_items, start=1):
            lines.append(
                f"{index}. {item.get('primary_industry') or item.get('industry') or '待研判行业'}"
                f"｜{item.get('sort_time') or item.get('published_date') or item.get('discovered_at') or '未知时间'}"
                f"｜{item.get('administrative_level') or 'unknown'}"
                f"｜{item.get('source_name') or '未知来源'}"
                f"｜{_clean_title(item.get('title'))}"
            )
    else:
        lines.append("当前没有待生产研究报告，或本次尚未同步到候选文件。")
    return "\n".join(lines).rstrip() + "\n"


def _render_html(
    run_id: str,
    stats: Mapping[str, int],
    documents: list[Mapping[str, Any]],
    markdown_name: str,
    interpretation_items: list[Mapping[str, Any]],
    queue_items: list[Mapping[str, Any]],
    timeline_items: list[Mapping[str, Any]],
) -> str:
    material_map = _materials_by_document(interpretation_items)
    subject = _clean_title(documents[0].get("title")) if documents else "本次运行未生成单文件研究对象"
    cards = "\n".join(
        _document_card(index, doc, material_map.get(str(doc.get("document_id")), []))
        for index, doc in enumerate(documents, start=1)
    )
    if not cards:
        cards = '<section class="empty">本次运行未发现符合条件的政策文件线索。</section>'
    toc = _toc(documents, bool(interpretation_items))
    material_section = _interpretation_section(interpretation_items)
    queue_section = _queue_section(queue_items)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>中国政策文件单文件研究分析报告</title>
  <style>
    :root {{
      --ink: #182230;
      --muted: #667085;
      --line: #d0d5dd;
      --paper: #f4f6f8;
      --panel: #ffffff;
      --brand: #0b5c6b;
      --brand-dark: #063f4b;
      --accent: #9a4a13;
      --risk: #9b2c2c;
      --ok: #176345;
      --soft: #f8fafc;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--paper);
      font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", Arial, sans-serif;
      line-height: 1.72;
      letter-spacing: 0;
    }}
    .page {{ max-width: 980px; margin: 0 auto; padding: 34px 28px 64px; }}
    .hero {{
      background: var(--panel);
      border-top: 5px solid var(--brand-dark);
      border-bottom: 1px solid var(--line);
      padding: 26px 0 22px;
    }}
    .hero .kicker {{
      margin: 0 0 8px;
      color: var(--brand);
      font-size: 13px;
      font-weight: 700;
    }}
    .hero h1 {{ margin: 0 0 12px; font-size: 28px; line-height: 1.25; font-weight: 750; }}
    .hero p {{ margin: 0; color: var(--muted); font-size: 15px; }}
    .meta {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 0;
      margin: 14px 0 18px;
      border: 1px solid var(--line);
      background: var(--panel);
    }}
    .metric {{
      min-height: 44px;
      padding: 7px 9px;
      border-right: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
    }}
    .metric span {{ display: block; color: var(--muted); font-size: 10px; }}
    .metric strong {{ display: block; margin-top: 1px; font-size: 14px; line-height: 1.25; color: var(--brand-dark); overflow-wrap: anywhere; }}
    .section-title {{
      margin: 30px 0 12px;
      padding-left: 11px;
      border-left: 4px solid var(--brand);
      font-size: 20px;
      line-height: 1.35;
      color: var(--brand-dark);
    }}
    .sub-title {{ margin: 20px 0 8px; font-size: 16px; color: var(--brand-dark); }}
    .summary, .doc-card {{
      background: var(--panel);
      border: 1px solid var(--line);
    }}
    .summary {{ padding: 16px 18px; color: #263446; }}
    .summary.warning {{ border-color: #e5b26d; background: #fff8ec; color: #60400f; }}
    .viz-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin: 16px 0 22px;
    }}
    .viz-panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      padding: 13px 14px;
      min-height: 184px;
    }}
    .viz-panel.wide {{ grid-column: 1 / -1; }}
    .viz-panel h3 {{ margin: 0 0 9px; color: var(--brand-dark); font-size: 15px; line-height: 1.32; }}
    .viz-note {{ margin: 8px 0 0; color: var(--muted); font-size: 11px; line-height: 1.45; }}
    .viz-bars {{ display: grid; gap: 8px; }}
    .viz-row {{ display: grid; grid-template-columns: 92px 1fr 44px; gap: 8px; align-items: center; font-size: 11px; }}
    .viz-label {{ color: #344054; overflow-wrap: anywhere; }}
    .viz-track {{ height: 10px; background: #e7eef1; border: 1px solid #d5e2e6; }}
    .viz-fill {{ height: 100%; background: var(--brand); }}
    .viz-fill.warn {{ background: var(--accent); }}
    .viz-fill.risk {{ background: var(--risk); }}
    .viz-fill.ok {{ background: var(--ok); }}
    .viz-value {{ color: var(--brand-dark); font-weight: 700; text-align: right; }}
    .viz-svg {{ display: block; width: 100%; height: auto; }}
    .viz-legend {{ display: flex; flex-wrap: wrap; gap: 7px; margin-top: 8px; }}
    .viz-chip {{ border: 1px solid var(--line); background: var(--soft); padding: 2px 7px; font-size: 11px; color: #344054; }}
    .capability-grid {{
      display: grid;
      grid-template-columns: 1.2fr 1fr 1fr;
      border: 1px solid var(--line);
      background: var(--panel);
    }}
    .capability-grid div {{ padding: 7px 8px; border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); font-size: 11px; line-height: 1.42; }}
    .capability-grid .head {{ background: #edf4f7; color: var(--brand-dark); font-weight: 700; }}
    .capability-grid .status {{ color: var(--accent); font-weight: 700; }}
    .toc {{
      background: var(--panel);
      border: 1px solid var(--line);
      margin: 22px 0;
      padding: 15px 18px;
    }}
    .toc h2 {{ margin: 0 0 8px; color: var(--brand-dark); font-size: 17px; }}
    .toc ol {{ margin: 0; padding-left: 20px; columns: 1; }}
    .toc li {{ break-inside: avoid; margin: 6px 0; }}
    .doc-card {{ margin: 16px 0; overflow: hidden; }}
    .doc-head {{
      display: block;
      padding: 18px 20px 15px;
      border-bottom: 1px solid var(--line);
      background: var(--soft);
    }}
    .rank {{
      display: inline-block;
      margin-bottom: 8px;
      color: var(--brand);
      background: transparent;
      font-weight: 750;
      font-size: 13px;
    }}
    .rank::before {{ content: "文件 "; }}
    .doc-title {{ margin: 0 0 10px; font-size: 21px; line-height: 1.38; }}
    .badges {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .badge {{
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 2px 8px;
      background: #eef6f7;
      color: var(--brand);
      border: 1px solid #d5e8eb;
      font-size: 12px;
      font-weight: 600;
    }}
    .badge.hot {{ background: #fff2e8; color: var(--accent); border-color: #f2c7a7; }}
    .doc-body {{ padding: 18px 20px 22px; }}
    .analysis {{ margin: 0 0 16px; font-size: 15px; color: #25364a; }}
    .grid {{
      display: block;
    }}
    .block {{
      border-top: 1px solid var(--line);
      padding: 13px 0 10px;
      background: #fff;
    }}
    .block h3 {{ margin: 0 0 7px; font-size: 15px; color: var(--brand-dark); }}
    .block.risk h3 {{ color: var(--risk); }}
    .block.action h3 {{ color: var(--ok); }}
    .deep-analysis {{
      margin-top: 18px;
      border-top: 2px solid var(--brand-dark);
    }}
    .deep-chapter {{
      padding: 18px 0 8px;
      border-top: 1px solid var(--line);
    }}
    .deep-chapter h3 {{
      margin: 0 0 10px;
      font-size: 18px;
      color: var(--brand-dark);
    }}
    .deep-chapter p {{
      margin: 0 0 10px;
      font-size: 15px;
      color: #25364a;
    }}
    .page-break {{
      display: block;
      height: 1px;
    }}
    ul {{ margin: 0; padding-left: 19px; }}
    li {{ margin: 4px 0; }}
    a {{ color: var(--brand); text-decoration: none; word-break: break-all; }}
    a:hover {{ text-decoration: underline; }}
    @page {{ size: A4; margin: 14mm; }}
    @media print {{
      body {{ background: #fff; }}
      .page {{ max-width: none; padding: 0; }}
      .material, .block {{ break-inside: avoid; }}
      .doc-card, .doc-body, .deep-analysis {{ overflow: visible !important; }}
      .doc-card, .deep-analysis {{ break-inside: auto; page-break-inside: auto; }}
      .deep-chapter {{
        display: block;
        box-sizing: border-box;
        min-height: auto;
        break-before: page;
        page-break-before: always;
      }}
      .deep-chapter:not(:last-child) {{ break-after: page; page-break-after: always; }}
      .page-break {{ display: none !important; }}
      .viz-grid {{ grid-template-columns: 1fr 1fr; gap: 7px; }}
      .viz-panel {{ break-inside: avoid; min-height: 0; padding: 8px 9px; }}
      .viz-panel h3 {{ font-size: 11px; }}
      .viz-row {{ grid-template-columns: 68px 1fr 34px; font-size: 8px; gap: 4px; }}
      .capability-grid div {{ font-size: 7px; padding: 4px 5px; }}
      .reference-section {{ break-before: page; page-break-before: always; }}
      .reference-section .material-list {{ gap: 4px; }}
      .reference-section .material {{ padding: 5px 7px; }}
      .reference-section .material strong {{ font-size: 9px; margin-bottom: 2px; }}
      .reference-section .material span {{ font-size: 8px; line-height: 1.22; }}
      a {{ color: var(--brand-dark); }}
    }}
    .source-link {{ margin-top: 14px; font-size: 12px; color: var(--muted); }}
    .related {{
      margin-top: 16px;
      border-top: 1px solid var(--line);
      padding-top: 12px;
    }}
    .related h3 {{ margin: 0 0 8px; color: var(--brand-dark); font-size: 15px; }}
    .material-list {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 8px;
    }}
    .material {{
      background: var(--panel);
      border: 1px solid var(--line);
      padding: 10px 12px;
    }}
    .material strong {{ display: block; margin-bottom: 4px; color: var(--brand-dark); }}
    .material span {{ display: block; color: var(--muted); font-size: 12px; line-height: 1.58; }}
    .reference-section .material-list {{
      gap: 6px;
    }}
    .reference-section .material {{
      padding: 8px 10px;
    }}
    .reference-section .material strong {{
      font-size: 12px;
    }}
    .reference-section .material span {{
      font-size: 10px;
      line-height: 1.35;
    }}
    .empty {{ border: 1px solid var(--line); background: var(--panel); padding: 14px 16px; color: var(--muted); }}
    .footer {{ margin-top: 28px; color: var(--muted); font-size: 13px; }}
    @media (max-width: 860px) {{
      .page {{ padding: 20px 15px 40px; }}
      .hero h1 {{ font-size: 24px; }}
      .meta {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .viz-grid {{ grid-template-columns: 1fr; }}
      .capability-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <p class="kicker">单文件政策研究报告</p>
      <h1>中国政策文件单文件研究分析报告</h1>
      <p>研究对象：{html.escape(subject)}</p>
    </section>
    <section class="meta">
      {_metric("运行编号", run_id)}
      {_metric("研究文件", len(documents))}
      {_metric("覆盖来源", stats.get("sources_considered", 0))}
      {_metric("抓取页面", stats.get("pages_fetched", 0))}
      {_metric("发现线索", stats.get("documents_discovered", 0))}
      {_metric("新增文件", stats.get("new_documents", 0))}
      {_metric("已分析", stats.get("analyzed_documents", 0))}
      {_metric("外部解读", stats.get("interpretation_items", len(interpretation_items)))}
      {_metric("有效参考", f"{_reference_count(stats, interpretation_items)}/{_reference_min(stats)}")}
      {_metric("外部平台", f"{_platform_count(interpretation_items)}/{_platform_min(stats)}")}
    </section>
    {_reference_quality_banner(stats, interpretation_items)}
    {toc}
    <h2 id="quality" class="section-title">研究质量与交付状态</h2>
    {_report_quality_dashboard(stats, documents, interpretation_items, queue_items)}
    <h2 id="summary" class="section-title">一、执行摘要</h2>
    <section class="summary">{html.escape(_executive_summary(stats, documents))}</section>
    <h2 id="documents" class="section-title">二、重点文件深度研判</h2>
    {cards}
    {material_section}
    {queue_section}
    <p class="footer">同目录保留 Markdown 版本：{html.escape(markdown_name)}；同名 dashboard sidecar 保留运行复盘、benchmark 和采集细节。正式报告正文只保留政策研究、有效外部参考、质量门槛和生产队列。</p>
  </main>
</body>
	</html>
	"""


def _render_dashboard_html(
    run_id: str,
    stats: Mapping[str, int],
    documents: list[Mapping[str, Any]],
    interpretation_items: list[Mapping[str, Any]],
    queue_items: list[Mapping[str, Any]],
    timeline_items: list[Mapping[str, Any]],
) -> str:
    subject = _clean_title(documents[0].get("title")) if documents else "本次运行未生成单文件研究对象"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>政策监测运营仪表盘 - {html.escape(run_id)}</title>
  <style>
    :root {{
      --ink: #182230;
      --muted: #667085;
      --line: #d0d5dd;
      --paper: #f4f6f8;
      --panel: #ffffff;
      --brand: #0b5c6b;
      --brand-dark: #063f4b;
      --accent: #9a4a13;
      --risk: #9b2c2c;
      --ok: #176345;
      --soft: #f8fafc;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--paper);
      font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", Arial, sans-serif;
      line-height: 1.62;
    }}
    .page {{ max-width: 1180px; margin: 0 auto; padding: 28px 22px 54px; }}
    .hero {{ border-top: 5px solid var(--brand-dark); background: var(--panel); padding: 22px 0 18px; border-bottom: 1px solid var(--line); }}
    .hero p {{ margin: 0; color: var(--muted); }}
    .hero h1 {{ margin: 3px 0 8px; font-size: 28px; line-height: 1.22; color: var(--brand-dark); }}
    .section-title {{ margin: 24px 0 12px; padding-left: 11px; border-left: 4px solid var(--brand); font-size: 20px; color: var(--brand-dark); }}
    .summary {{ background: var(--panel); border: 1px solid var(--line); padding: 14px 16px; }}
    .viz-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin: 16px 0 22px; }}
    .viz-panel {{ background: var(--panel); border: 1px solid var(--line); padding: 13px 14px; min-height: 184px; }}
    .viz-panel.wide {{ grid-column: 1 / -1; }}
    .viz-panel h3 {{ margin: 0 0 9px; color: var(--brand-dark); font-size: 15px; }}
    .viz-note {{ margin: 8px 0 0; color: var(--muted); font-size: 12px; }}
    .viz-bars {{ display: grid; gap: 8px; }}
    .viz-row {{ display: grid; grid-template-columns: 108px 1fr 48px; gap: 8px; align-items: center; font-size: 12px; }}
    .viz-label {{ color: #344054; overflow-wrap: anywhere; }}
    .viz-track {{ height: 10px; background: #e7eef1; border: 1px solid #d5e2e6; }}
    .viz-fill {{ height: 100%; background: var(--brand); }}
    .viz-fill.warn {{ background: var(--accent); }}
    .viz-fill.risk {{ background: var(--risk); }}
    .viz-fill.ok {{ background: var(--ok); }}
    .viz-value {{ color: var(--brand-dark); font-weight: 700; text-align: right; }}
    .viz-svg {{ display: block; width: 100%; height: auto; }}
    .viz-legend {{ display: flex; flex-wrap: wrap; gap: 7px; margin-top: 8px; }}
    .viz-chip {{ border: 1px solid var(--line); background: var(--soft); padding: 2px 7px; font-size: 12px; color: #344054; }}
    .capability-grid {{ display: grid; grid-template-columns: 1.2fr 1fr 1fr; border: 1px solid var(--line); background: var(--panel); }}
    .capability-grid div {{ padding: 7px 8px; border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); font-size: 12px; }}
    .capability-grid .head {{ background: #edf4f7; color: var(--brand-dark); font-weight: 700; }}
    .capability-grid .status {{ color: var(--accent); font-weight: 700; }}
    @media (max-width: 860px) {{
      .page {{ padding: 20px 15px 40px; }}
      .viz-grid {{ grid-template-columns: 1fr; }}
      .capability-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <p>Policy Intelligence Operations Dashboard</p>
      <h1>政策监测运营仪表盘</h1>
      <p>运行编号：{html.escape(run_id)}｜研究对象：{html.escape(subject)}</p>
    </section>
    <h2 class="section-title">当前运行概览</h2>
    <section class="summary">{html.escape(_executive_summary(stats, documents))}</section>
    {_visual_dashboard(stats, documents, interpretation_items, queue_items, timeline_items)}
  </main>
</body>
</html>
"""


def _document_card(index: int, doc: Mapping[str, Any], materials: list[Mapping[str, Any]]) -> str:
    tier = html.escape(str(doc.get("authority_tier_snapshot") or "?"))
    score = html.escape(str(doc.get("authority_score_snapshot") or "NA"))
    title = html.escape(_clean_title(doc.get("title")))
    source = html.escape(str(doc.get("source_name") or "未知来源"))
    importance = html.escape(str(doc.get("importance_score") or "待分析"))
    url = html.escape(str(doc.get("canonical_url") or doc.get("url") or ""))
    related = _related_materials(materials)
    return f"""
    <article id="doc-{index}" class="doc-card">
      <header class="doc-head">
        <div class="rank">{index}</div>
        <div>
          <h2 class="doc-title">{title}</h2>
          <div class="badges">
            <span class="badge">来源权威 {tier}/{score}</span>
            <span class="badge hot">重要性 {importance}</span>
            <span class="badge">{source}</span>
            <span class="badge">{html.escape(_doc_type(doc.get("document_type")))}</span>
          </div>
        </div>
      </header>
      <div class="doc-body">
        <p class="analysis">{html.escape(_report_summary(doc, materials))}</p>
        <div class="grid">
          {_html_block("核心要点", doc.get("policy_points_json"))}
          {_html_block("商业影响", doc.get("business_impacts_json"))}
          {_html_block("风险与不确定性", doc.get("risks_json"), "risk")}
          {_html_block("建议行动", doc.get("actions_json"), "action")}
        </div>
        <p class="source-link">原文链接：<a href="{url}">{url}</a></p>
        {_deep_analysis_html(doc, materials)}
        {related}
      </div>
    </article>
    """


def _report_summary(doc: Mapping[str, Any], materials: list[Mapping[str, Any]]) -> str:
    summary = _strip_external_reference_claims(str(doc.get("chinese_summary") or "").strip())
    if not summary:
        summary = "暂无综合研判。"
    refs = reference_items(materials)
    platforms = reference_platforms(materials)
    if refs:
        suffix = (
            f"当前可计入质量门槛的同主题外部参考为{len(refs)}条，"
            f"覆盖{'、'.join(platforms) or '多个公开平台'}；这些资料只作为辅助解读，正式结论仍以官方原文、附件和主管部门解释为准。"
        )
    else:
        suffix = (
            "当前没有形成可计入质量门槛的同主题外部参考；本报告只能作为质量缺口版，"
            "不得标记为成熟完整研究报告。"
        )
    return f"{summary} {suffix}"


def _strip_external_reference_claims(value: str) -> str:
    text = re.sub(
        r"本次已同步参考\d+条网络公开研究/解读资料[^。]*。",
        "",
        value,
    )
    text = re.sub(
        r"本次已同步参考\d+条[^。]*用于补充市场观点、专家表达和传播热度。",
        "",
        text,
    )
    return re.sub(r"\s+", " ", text).strip()


def _metric(label: str, value: object) -> str:
    return f'<div class="metric"><span>{html.escape(str(label))}</span><strong>{html.escape(str(value))}</strong></div>'


def _visual_dashboard(
    stats: Mapping[str, int],
    documents: list[Mapping[str, Any]],
    interpretation_items: list[Mapping[str, Any]],
    queue_items: list[Mapping[str, Any]],
    timeline_items: list[Mapping[str, Any]],
) -> str:
    return (
        '<section class="viz-grid" aria-label="政策监测运行可视化">'
        f'{_quality_panel(stats, interpretation_items)}'
        f'{_quality_rules_panel(stats, documents)}'
        f'{_funnel_panel(stats)}'
        f'{_platform_panel(interpretation_items)}'
        f'{_interpretation_health_panel(stats, interpretation_items)}'
        f'{_reference_gap_panel(stats, interpretation_items)}'
        f'{_queue_panel(queue_items)}'
        f'{_timeline_panel(timeline_items)}'
        f'{_capability_matrix_panel()}'
        '</section>'
    )


def _report_quality_dashboard(
    stats: Mapping[str, int],
    documents: list[Mapping[str, Any]],
    interpretation_items: list[Mapping[str, Any]],
    queue_items: list[Mapping[str, Any]],
) -> str:
    return (
        '<section class="viz-grid" aria-label="研究质量与交付状态">'
        f'{_quality_panel(stats, interpretation_items)}'
        f'{_quality_rules_panel(stats, documents)}'
        f'{_platform_panel(interpretation_items)}'
        f'{_reference_gap_panel(stats, interpretation_items)}'
        f'{_queue_panel(queue_items)}'
        '</section>'
    )


def _quality_panel(stats: Mapping[str, int], items: list[Mapping[str, Any]]) -> str:
    ref_count = _reference_count(stats, items)
    ref_min = _reference_min(stats)
    platform_count = _platform_count(items)
    platform_min = _platform_min(stats)
    gate = ref_count >= ref_min and platform_count >= platform_min
    rows = [
        ("有效参考", ref_count, max(ref_min, ref_count, 1), "ok" if ref_count >= ref_min else "warn"),
        ("外部平台", platform_count, max(platform_min, platform_count, 1), "ok" if platform_count >= platform_min else "warn"),
        ("质量门槛", int(gate), 1, "ok" if gate else "risk"),
    ]
    note = "达标，可进入完成队列。" if gate else _reference_status(stats, items)
    return (
        '<article class="viz-panel"><h3>质量门槛</h3>'
        f'{_bar_rows(rows)}'
        f'<p class="viz-note">{html.escape(note)}</p></article>'
    )


def _quality_rules_panel(stats: Mapping[str, int], documents: list[Mapping[str, Any]]) -> str:
    metrics: dict[str, Any] = {
        "external_reference_count": int(stats.get("external_reference_count", 0) or 0),
        "external_platform_count": int(stats.get("external_platform_count", 0) or 0),
        "report_document_count": len(documents),
        "primary_report_suffix": ".pdf",
        "deep_chapter_count": 10 if documents else 0,
    }
    status = build_quality_gate_status(metrics=metrics)
    results = list(status.get("gate_results") or [])
    counts = {
        "passed": sum(1 for item in results if item.get("status") == "passed"),
        "failed": sum(1 for item in results if item.get("status") == "failed"),
        "not_checked": sum(1 for item in results if item.get("status") == "not_checked"),
    }
    rows = [
        ("通过", counts["passed"], max(1, len(results)), "ok"),
        ("失败", counts["failed"], max(1, len(results)), "risk" if counts["failed"] else ""),
        ("未验证", counts["not_checked"], max(1, len(results)), "warn" if counts["not_checked"] else ""),
    ]
    chips = "".join(
        f'<span class="viz-chip">{html.escape(str(item.get("label") or item.get("id") or ""))}：{html.escape(str(item.get("status") or ""))}</span>'
        for item in results[:5]
    )
    return (
        '<article class="viz-panel wide"><h3>规则化质量门槛</h3>'
        f'{_bar_rows(rows)}<section class="viz-legend">{chips}</section>'
        '<p class="viz-note">规则来自 rules/quality_gates.json；not_checked 表示需要 PDF 页数或最终产物等生成后证据。</p></article>'
    )


def _funnel_panel(stats: Mapping[str, int]) -> str:
    rows = [
        ("来源", int(stats.get("sources_considered", 0) or 0)),
        ("页面", int(stats.get("pages_fetched", 0) or 0)),
        ("线索", int(stats.get("documents_discovered", 0) or 0)),
        ("新增", int(stats.get("new_documents", 0) or 0)),
        ("附件", int(stats.get("attachments_parsed", 0) or 0)),
        ("分析", int(stats.get("analyzed_documents", 0) or 0)),
    ]
    maximum = max([value for _, value in rows] + [1])
    return (
        '<article class="viz-panel"><h3>采集漏斗</h3>'
        f'{_bar_rows([(label, value, maximum, "ok" if label == "分析" and value else "") for label, value in rows])}'
        '<p class="viz-note">对应 Monity/PolicyInsight 的持续监测视图：来源进入、页面抓取、线索发现、报告生产。</p></article>'
    )


def _platform_panel(items: list[Mapping[str, Any]]) -> str:
    counts: dict[str, dict[str, int]] = {}
    for item in items:
        platform = str(item.get("platform") or "未知平台")
        bucket = counts.setdefault(platform, {"total": 0, "reference": 0})
        bucket["total"] += 1
        bucket["reference"] += int(is_reference_item(item))
    if not counts:
        return (
            '<article class="viz-panel"><h3>外部平台覆盖</h3>'
            '<section class="empty">本次仅生成搜索入口或未取得可计入外部参考。</section>'
            '<p class="viz-note">下一步需要接入搜索 API、Chrome 登录态或平台开放接口。</p></article>'
        )
    ordered = sorted(counts.items(), key=lambda pair: (pair[1]["reference"], pair[1]["total"]), reverse=True)[:8]
    maximum = max([data["total"] for _, data in ordered] + [1])
    rows = [(platform, data["total"], maximum, "ok" if data["reference"] else "warn") for platform, data in ordered]
    chips = "".join(
        f'<span class="viz-chip">{html.escape(platform)}：计入 {data["reference"]}/{data["total"]}</span>'
        for platform, data in ordered
    )
    return (
        '<article class="viz-panel"><h3>外部平台覆盖</h3>'
        f'{_bar_rows(rows)}<section class="viz-legend">{chips}</section>'
        '<p class="viz-note">区分“搜索入口”和“可计入参考”，避免把未授权平台误算为研究依据。</p></article>'
    )


def _interpretation_health_panel(stats: Mapping[str, int], items: list[Mapping[str, Any]]) -> str:
    attempts = int(stats.get("interpretation_attempts", len(items)) or 0)
    successes = int(stats.get("interpretation_reference_successes", count_reference_items(items)) or 0)
    missing_keys = int(stats.get("interpretation_missing_api_keys", 0) or 0)
    auth_required = int(stats.get("interpretation_auth_required", 0) or 0)
    auth_configured = int(stats.get("interpretation_auth_configured", 0) or 0)
    auth_parser_pending = int(stats.get("interpretation_auth_parser_pending", 0) or 0)
    failed = int(stats.get("interpretation_failed_requests", 0) or 0)
    landings = int(stats.get("interpretation_search_landings", 0) or 0)
    public_site_searches = int(stats.get("public_site_searches", 0) or 0)
    public_site_results = int(stats.get("public_site_results", 0) or 0)
    public_search_html_searches = int(stats.get("public_search_html_searches", 0) or 0)
    public_search_html_results = int(stats.get("public_search_html_results", 0) or 0)
    authorized_public_searches = int(stats.get("authorized_public_searches", 0) or 0)
    authorized_public_results = int(stats.get("authorized_public_results", 0) or 0)
    authorized_public_blocked = int(stats.get("authorized_public_blocked", 0) or 0)
    article_fetched = int(stats.get("article_pages_fetched", 0) or 0)
    article_extracted = int(stats.get("article_excerpts_extracted", 0) or 0)
    article_blocked = int(stats.get("article_pages_blocked", 0) or 0)
    article_failed = int(stats.get("article_pages_failed", 0) or 0)
    details = int(stats.get("video_details_enriched", 0) or 0)
    authors = int(stats.get("video_author_profiles_enriched", 0) or 0)
    subtitles = int(stats.get("video_subtitles_extracted", 0) or 0)
    comments = int(stats.get("video_comments_extracted", 0) or 0)
    danmaku = int(stats.get("video_danmaku_extracted", 0) or 0)
    maximum = max(
        attempts,
        successes,
        missing_keys,
        auth_required,
        auth_configured,
        auth_parser_pending,
        public_site_searches,
        public_site_results,
        public_search_html_searches,
        public_search_html_results,
        authorized_public_searches,
        authorized_public_results,
        authorized_public_blocked,
        article_fetched,
        article_extracted,
        article_blocked,
        article_failed,
        failed,
        landings,
        details,
        authors,
        subtitles,
        comments,
        danmaku,
        1,
    )
    rows = [
        ("尝试", attempts, maximum, ""),
        ("计入", successes, maximum, "ok" if successes else "warn"),
        ("详情", details, maximum, "ok" if details else ""),
        ("作者", authors, maximum, "ok" if authors else ""),
        ("字幕", subtitles, maximum, "ok" if subtitles else ""),
        ("评论", comments, maximum, "ok" if comments else ""),
        ("弹幕", danmaku, maximum, "ok" if danmaku else ""),
        ("缺key", missing_keys, maximum, "risk" if missing_keys else ""),
        ("需授权", auth_required, maximum, "warn" if auth_required else ""),
        ("已授权", auth_configured, maximum, "ok" if auth_configured else ""),
        ("待解析", auth_parser_pending, maximum, "warn" if auth_parser_pending else ""),
        ("站搜", public_site_searches, maximum, "ok" if public_site_searches else ""),
        ("站果", public_site_results, maximum, "ok" if public_site_results else ""),
        ("中搜", public_search_html_searches, maximum, "ok" if public_search_html_searches else ""),
        ("中果", public_search_html_results, maximum, "ok" if public_search_html_results else ""),
        ("授权搜", authorized_public_searches, maximum, "ok" if authorized_public_searches else ""),
        ("授权果", authorized_public_results, maximum, "ok" if authorized_public_results else ""),
        ("授权受限", authorized_public_blocked, maximum, "warn" if authorized_public_blocked else ""),
        ("网页", article_fetched, maximum, "ok" if article_fetched else ""),
        ("摘录", article_extracted, maximum, "ok" if article_extracted else ""),
        ("受限", article_blocked, maximum, "warn" if article_blocked else ""),
        ("页失败", article_failed, maximum, "risk" if article_failed else ""),
        ("失败", failed, maximum, "risk" if failed else ""),
        ("入口", landings, maximum, "warn" if landings else ""),
    ]
    if successes:
        note = "已有可计入外部参考；继续补足平台覆盖和正文摘录。"
    elif missing_keys or auth_required or failed:
        note = "当前主要缺口可定位到搜索 API key、平台授权或请求失败。"
    else:
        note = "当前仅形成候选线索，后续需要解析公开正文或接入授权。"
    return (
        '<article class="viz-panel"><h3>外部采集健康度</h3>'
        f'{_bar_rows(rows)}'
        f'<p class="viz-note">{html.escape(note)}</p></article>'
    )


def _reference_gap_panel(stats: Mapping[str, int], items: list[Mapping[str, Any]]) -> str:
    summary = external_reference_gap_summary_for_items(items)
    total = int(stats.get("external_reference_gaps", summary.get("pending_count", 0)) or 0)
    by_action = summary.get("by_action") or {}
    if not total:
        return (
            '<article class="viz-panel"><h3>外部参考缺口队列</h3>'
            '<section class="empty">当前没有外部参考缺口待办。</section></article>'
        )
    ordered = sorted(by_action.items(), key=lambda pair: int(pair[1] or 0), reverse=True)[:6]
    maximum = max([int(value or 0) for _, value in ordered] + [1])
    rows = [
        (gap_action_label(str(action)), int(value or 0), maximum, "risk" if "provide" in str(action) else "warn")
        for action, value in ordered
    ]
    preview = "".join(
        '<span class="viz-chip">'
        f'{html.escape(gap_type_label(str(gap.get("gap_type"))))}｜'
        f'{html.escape(str(gap.get("platform") or "unknown"))}｜'
        f'{html.escape(str(gap.get("priority_score") or 0))}'
        '</span>'
        for gap in summary.get("preview", [])[:4]
    )
    return (
        '<article class="viz-panel"><h3>外部参考缺口队列</h3>'
        f'{_bar_rows(rows)}<section class="viz-legend">{preview}</section>'
        '<p class="viz-note">把未计入参考的入口、授权、API、解析器和抓取失败问题沉淀为 automation 可处理的待办。</p></article>'
    )


def _queue_panel(items: list[Mapping[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for item in items:
        industry = str(item.get("primary_industry") or item.get("industry") or item.get("industry_bucket") or "待研判")
        counts[industry] = counts.get(industry, 0) + 1
    if not counts:
        return '<article class="viz-panel"><h3>待生产队列</h3><section class="empty">当前没有待生产报告。</section></article>'
    ordered = sorted(counts.items(), key=lambda pair: pair[1], reverse=True)[:8]
    maximum = max([value for _, value in ordered] + [1])
    return (
        '<article class="viz-panel"><h3>待生产队列：行业分布</h3>'
        f'{_bar_rows([(label, value, maximum, "") for label, value in ordered])}'
        '<p class="viz-note">队列仍按行业优先级、时间、中央到地方排序；图表用于识别积压板块。</p></article>'
    )


def _timeline_panel(items: list[Mapping[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for item in items:
        event_type = str(item.get("event_type") or "generated")
        counts[event_type] = counts.get(event_type, 0) + 1
    if not counts:
        return '<article class="viz-panel"><h3>报告时间线</h3><section class="empty">暂无历史事件。</section></article>'
    ordered = sorted(counts.items(), key=lambda pair: pair[1], reverse=True)
    maximum = max([value for _, value in ordered] + [1])
    rows = [
        (label, value, maximum, "ok" if label == "generated" else "warn" if label == "quality_gap" else "")
        for label, value in ordered
    ]
    recent = "".join(
        f'<span class="viz-chip">{html.escape(str(item.get("created_at") or ""))}｜{html.escape(str(item.get("event_type") or ""))}</span>'
        for item in items[:4]
    )
    return (
        '<article class="viz-panel"><h3>报告时间线事件</h3>'
        f'{_bar_rows(rows)}<section class="viz-legend">{recent}</section>'
        '<p class="viz-note">借鉴 GRC 审计日志：每次生成、缺口和跳过都要可追溯。</p></article>'
    )


def _capability_matrix_panel() -> str:
    rows = benchmark_model_rows(limit=8)
    cells = [
        '<div class="head">参考模型</div><div class="head">应吸收能力</div><div class="head">当前落地状态</div>'
    ]
    for name, capability, status in rows:
        cells.append(f'<div>{html.escape(name)}</div><div>{html.escape(capability)}</div><div class="status">{html.escape(status)}</div>')
    return (
        '<article class="viz-panel wide"><h3>开源/商业参考能力矩阵</h3>'
        f'<section class="capability-grid">{"".join(cells)}</section>'
        '<p class="viz-note">该矩阵来自 benchmark registry、GitHub/官网资料和后续 PDF 对标文件，用于把“接近全网”拆成可实施能力。</p></article>'
    )


def _bar_rows(rows: list[tuple[str, int, int, str]]) -> str:
    rendered = []
    for label, value, maximum, klass in rows:
        pct = 0 if maximum <= 0 else min(100, round(value / maximum * 100, 1))
        klass_attr = f" {klass}" if klass else ""
        rendered.append(
            '<div class="viz-row">'
            f'<span class="viz-label">{html.escape(str(label))}</span>'
            f'<span class="viz-track"><span class="viz-fill{klass_attr}" style="width:{pct}%"></span></span>'
            f'<span class="viz-value">{html.escape(str(value))}</span>'
            '</div>'
        )
    return f'<section class="viz-bars">{"".join(rendered)}</section>'


def _deep_analysis_html(doc: Mapping[str, Any], materials: list[Mapping[str, Any]]) -> str:
    chapters = _deep_analysis_chapters(doc, materials)
    rendered = []
    for chapter in chapters:
        paragraphs = "".join(
            f"<p>{html.escape(paragraph)}</p>" for paragraph in chapter["paragraphs"]
        )
        rendered.append(
            f'<section class="deep-chapter"><h3>{html.escape(chapter["title"])}</h3>{paragraphs}</section>'
            '<div class="page-break" style="break-after: page; page-break-after: always;"></div>'
        )
    return f'<section class="deep-analysis">{"".join(rendered)}</section>'


def _deep_analysis_chapters(
    doc: Mapping[str, Any],
    materials: list[Mapping[str, Any]],
) -> list[dict[str, list[str] | str]]:
    title = _clean_title(doc.get("title"))
    source = str(doc.get("source_name") or "未知来源")
    tier = str(doc.get("authority_tier_snapshot") or "?")
    score = str(doc.get("authority_score_snapshot") or "NA")
    doc_type = _doc_type(doc.get("document_type"))
    url = str(doc.get("canonical_url") or doc.get("url") or "")
    summary = _report_summary(doc, materials)
    points = [str(item) for item in _json_items(doc.get("policy_points_json"))]
    impacts = [str(item) for item in _json_items(doc.get("business_impacts_json"))]
    risks = [str(item) for item in _json_items(doc.get("risks_json"))]
    actions = [str(item) for item in _json_items(doc.get("actions_json"))]
    ref_titles = [_clean_title(item.get("title")) for item in reference_items(materials)]
    ref_line = "；".join(ref_titles[:5]) if ref_titles else "当前未形成足够可计入的外部参考标题。"
    point_line = "；".join(points[:6]) if points else "正文条款尚未完整抽取，需回看原文和附件。"
    impact_line = "；".join(impacts[:5]) if impacts else "影响路径需要结合行业与地区配套政策继续拆解。"
    risk_line = "；".join(risks[:5]) if risks else "主要风险来自正文缺失、执行细则未出和外部解读可信度差异。"
    action_line = "；".join(actions[:6]) if actions else "后续应补全文、补附件、补专家解读并进入人工复核。"
    chapters = [
        {
            "title": "1. 原文定位、权威性与研究边界",
            "paragraphs": [
                f"本报告只研究一份文件：《{title}》。文件来源为{source}，当前来源权威快照为{tier}/{score}，文件类型识别为{doc_type}。原文链接为：{url}。",
                "研究边界上，本报告把官方原文作为最高证据层级，把主管部门解释、官方媒体、智库、财经媒体和视频平台解读作为外部参考层。任何涉及投资、交易、合规、补贴申报或法律责任的判断，都必须回到原文、附件和主管部门正式解释逐条复核。",
                f"自动摘要给出的初步判断为：{summary}",
            ],
        },
        {
            "title": "2. 政策背景、问题导向与出台动因",
            "paragraphs": [
                f"从标题和来源看，《{title}》反映的政策议题需要放在当前宏观政策、行业治理、地方执行和市场预期变化中理解。其核心不是孤立信息发布，而是主管部门对某类问题、某类产业或某类区域治理任务的正式回应。",
                "分析时需要区分三类动因：第一，中央或地方已有政策的延续和细化；第二，现实执行中出现的新问题需要通过通知、意见、规划或批复进行修正；第三，政策希望通过公开发布形成市场预期、约束地方执行或引导社会资本。",
                f"当前系统抽取到的核心证据包括：{point_line}",
            ],
        },
        {
            "title": "3. 文件属性、适用范围与约束强度",
            "paragraphs": [
                f"文件属性会直接影响解读方式。当前识别的类型为{doc_type}，如果其性质是规划或意见，则更偏中长期方向和政策预期；如果是通知、批复、办法或规定，则更可能形成具体执行约束。",
                "适用范围需要从发布机关、标题对象、地区词、行业词和原文链接共同判断。国家级来源通常具有更强的政策指引性，省市级来源通常更接近落地执行和项目机会。",
                "约束强度应分层判断：法规则强于规章，规章强于规范性文件，规范性文件强于新闻稿，新闻稿和解读稿不能替代原文条款。",
            ],
        },
        {
            "title": "4. 核心条款与政策工具拆解",
            "paragraphs": [
                "正式深度解读需要把原文拆成目标、任务、对象、工具、时间、责任部门、监督评估和配套政策八类信息。本轮自动分析已先建立条款拆解框架，后续需要在全文和附件解析后逐条填充。",
                f"当前可用的核心要点为：{point_line}",
                "政策工具上，应重点识别是否涉及财政资金、税费减免、行政审批、许可准入、监管处罚、试点示范、标准制定、数据报送、项目清单、政府采购、金融支持或区域协调机制。",
            ],
        },
        {
            "title": "5. 产业链、供应链与商业模式影响",
            "paragraphs": [
                f"商业影响初步指向：{impact_line}",
                "产业链分析应沿上游资源和设备、中游生产和服务、下游客户和应用场景展开。若政策涉及规划、标准、财政资金或许可条件，则可能改变行业进入门槛、项目建设节奏、订单释放路径和企业合规成本。",
                "对企业而言，需要判断政策是扩大需求、重塑供给、提高门槛、鼓励并购整合，还是加强监管。不同类型会对应完全不同的经营和投资含义。",
            ],
        },
        {
            "title": "6. 区域、部门与实施主体影响",
            "paragraphs": [
                "区域影响需要结合发布机关和文件对象判断。中央文件通常需要观察各部委和地方配套；地方文件更要关注省、市、区县三级执行差异，以及财政承受能力、土地、审批、项目储备和招商方向。",
                "实施主体可能包括政府部门、事业单位、国企、平台公司、行业协会、科研机构、园区、企业和居民。不同主体的义务、收益和风险并不相同，报告应避免把所有影响笼统写成“利好”。",
                f"本文件当前来源为{source}，因此后续应优先跟踪同源网站、主管部门栏目、地方实施细则和新闻发布会。",
            ],
        },
        {
            "title": "7. 企业机会、受益方向与交易观察价值",
            "paragraphs": [
                "企业机会不应直接等同于股票买卖建议。更稳健的做法是识别潜在受益环节、订单来源、政策补贴、合规成本下降、试点资格、行业集中度变化和长期需求改善。",
                "交易观察价值应限定为研究观察：关注政策是否带来主题催化、订单预期、财政资金、项目清单、地方跟进、行业会议和上市公司公告。没有原文条款和资金安排验证前，不输出买卖指令。",
                "可跟踪对象包括相关上市公司公告、行业协会解读、券商研报标题、地方项目库、招投标数据和主管部门问答。企业名单需要在后续专门步骤中基于行业映射和公开经营数据生成。",
            ],
        },
        {
            "title": "8. 历史政策、既有研究与外部解读对照",
            "paragraphs": [
                f"本报告纳入的外部参考包括：{ref_line}",
                "外部参考的作用是补充观点差异、市场关注点和传播热度，而不是替代官方原文。对于 B 站、短视频、公众号、媒体和智库观点，需要明确标注其来源层级、作者身份、发布时间和是否有原文引用。",
                "历史政策对照应优先比较同一部门、同一主题、同一地区在过去 1-3 年内发布的文件，重点看措辞变化、任务新增、时间节点变化、责任部门变化和监管力度变化。",
            ],
        },
        {
            "title": "9. 风险、不确定性与反向验证",
            "paragraphs": [
                f"当前识别的风险包括：{risk_line}",
                "反向验证需要检查三件事：第一，该文件是否为正式原文或只是转载/解读；第二，是否存在附件、细则、名单或预算尚未抓取；第三，外部解读是否过度演绎、断章取义或把长期规划当成立即订单。",
                "如果文件涉及财政、税费、金融、土地、环保、安全生产、许可审批或个人信息处理，还需要单独做法律、合规和财务假设复核。",
            ],
        },
        {
            "title": "10. 后续任务队列、监测指标与结论",
            "paragraphs": [
                f"建议行动为：{action_line}",
                "后续任务队列应包括：抓取和解析全文附件；补充至少 5 份外部参考且覆盖至少 2 个平台；检索主管部门问答和新闻发布会；比对历史政策；建立受影响行业和企业候选清单；跟踪地方配套和项目落地。",
                f"综合判断，《{title}》应继续保留在单文件深度研究体系中。当前自动化版本已经完成来源识别、初步分类、外部参考采集和报告生成，但成熟结论仍需全文解析、跨平台资料补充和人工复核。",
            ],
        },
    ]
    for chapter in chapters:
        chapter["paragraphs"].extend(
            _chapter_depth_paragraphs(
                str(chapter["title"]),
                title=title,
                source=source,
                point_line=point_line,
                impact_line=impact_line,
                risk_line=risk_line,
                ref_line=ref_line,
            )
        )
    return chapters


def _chapter_depth_paragraphs(
    chapter_title: str,
    *,
    title: str,
    source: str,
    point_line: str,
    impact_line: str,
    risk_line: str,
    ref_line: str,
) -> list[str]:
    common_evidence = (
        "证据处理上，应把标题、发文机关、发布日期、正文任务、附件、政策解读和外部观点拆开记录；"
        "其中标题只能提示方向，正文和附件才是判断执行责任、时间节点、资金安排和约束强度的核心依据。"
    )
    common_output = (
        "报告落地时建议形成三层结论：第一层写清楚原文事实；第二层说明可能影响的行业、区域和主体；"
        "第三层列出仍需验证的假设，避免把传播热度、市场情绪或单一平台观点直接写成确定性结论。"
    )
    if chapter_title.startswith("1."):
        return [
            f"对《{title}》的研究不能只看页面标题。应进一步确认该页面是政策原文、政策解读、新闻稿还是转载入口；若来源为{source}，仍需追溯到具体发文机关、文号、附件和主管部门说明，避免把门户转发与原始发布混同。",
            common_evidence,
        ]
    if chapter_title.startswith("2."):
        return [
            "政策背景需要放在五年规划、年度重点工作、部门专项规划和地方配套政策之间观察。若同一主题在多个层级连续出现，通常意味着政策正在从方向性表述进入任务清单或项目落地阶段。",
            f"当前可见证据包括：{point_line}。这些证据只构成自动化初筛，后续还需要检索同主题历史文件，判断本次表述是新增、延续、强化还是口径调整。",
        ]
    if chapter_title.startswith("3."):
        return [
            "约束强度的判断应同时看文件名称和条款措辞。带有“规划”“意见”的文件往往偏目标和政策工具组合，带有“办法”“规定”“通知”“批复”的文件更可能直接影响审批、监管、申报或执行流程。",
            "适用范围还应识别是否存在隐含对象，例如地方政府、主管部门、国有企业、园区平台、金融机构、行业协会、科研机构或具体企业。不同对象承担的义务不同，商业含义也不同。",
        ]
    if chapter_title.startswith("4."):
        return [
            "条款拆解需要逐条抽取“谁负责、对谁适用、做什么、何时完成、资金从哪里来、如何验收、违反后果是什么”。没有这些字段，报告只能停留在方向性解读，不能进入执行或投资判断。",
            f"当前自动抽取的核心线索为：{point_line}。下一步应把这些线索映射到政策工具表，分别标注为财政、金融、土地、审批、标准、监管、试点、政府采购或数据报送。",
        ]
    if chapter_title.startswith("5."):
        return [
            f"产业影响不能笼统写成利好。当前影响线索为：{impact_line}。应继续区分需求扩张、供给约束、成本上升、准入门槛变化、项目审批加速、财政资金倾斜和标准升级几类路径。",
            "供应链分析还要识别传导速度：规划类文件传导较慢，通常先影响地方预算和项目储备；监管类文件传导较快，可能直接改变企业合规成本；标准类文件则会影响设备、检测、认证和替换周期。",
        ]
    if chapter_title.startswith("6."):
        return [
            "中央到地方的执行链条应拆成部委解释、省级实施、市县项目和基层执行四层。报告队列排序虽然按行业优先，但同一文件后续仍要跟踪地方配套，因为真正的项目、资金和监管动作多在地方层面出现。",
            f"由于本文件来源为{source}，后续应优先监测同源站点、主管部门网站、新闻发布会实录和地方政府公报，判断是否出现可执行的时间表、责任单位和项目清单。",
        ]
    if chapter_title.startswith("7."):
        return [
            "企业机会应按“直接受益、间接受益、合规受压、观察名单”四类输出。直接受益通常来自资金、订单、牌照、试点或采购；间接受益通常来自需求预期、标准升级和基础设施建设；合规受压则来自监管、报送、环保、安全或数据要求。",
            "交易观察只能作为研究线索。若要进一步连接上市公司或行业标的，需要另建企业映射表，使用主营业务、区域收入、项目公告、招投标、财报披露和历史政策敏感度做交叉验证。",
        ]
    if chapter_title.startswith("8."):
        return [
            f"外部参考当前包括：{ref_line}。这些参考的价值在于补充市场关注点和公众传播口径，但必须标注平台、作者、发布时间、内容摘录和与原文的对应关系。",
            "历史对照应至少比较三个维度：同一主题过去文件的措辞变化，同一部门近年政策工具的使用频率，以及外部研究对该主题的长期判断是否发生转向。",
        ]
    if chapter_title.startswith("9."):
        return [
            f"风险线索包括：{risk_line}。报告应把信息不完整、执行不确定、资金不确定、地方差异、平台观点偏差和市场过度演绎分别列出，而不是合并成一句笼统风险。",
            "反向验证还需要检查是否存在标题党式解读、断章取义、跨行业误配、过度交易化解释或把政策目标误读为短期订单的情况。任何重大判断都应给出可回查链接和证据层级。",
        ]
    if chapter_title.startswith("10."):
        return [
            "后续自动化应先补齐同一文件的外部平台覆盖，再决定是否进入成熟报告。当前质量门槛要求至少 5 份有效外部参考和至少 2 个外部平台，缺任一项都只能生成质量缺口版，不能标为完成。",
            common_output,
        ]
    return [common_evidence, common_output]


def _toc(documents: list[Mapping[str, Any]], has_materials: bool) -> str:
    items = [
        '<li><a href="#quality">研究质量与交付状态</a></li>',
        '<li><a href="#summary">一、执行摘要</a></li>',
        '<li><a href="#documents">二、重点文件深度研判</a></li>',
    ]
    for index, doc in enumerate(documents[:30], start=1):
        items.append(
            f'<li><a href="#doc-{index}">{index}. {html.escape(_clean_title(doc.get("title")))}</a></li>'
        )
    if has_materials:
        items.append('<li><a href="#interpretations">三、外部研究与解读资料来源</a></li>')
    items.append('<li><a href="#queue">四、待生产研究报告队列</a></li>')
    return f'<nav class="toc"><h2>目录</h2><ol>{"".join(items)}</ol></nav>'


def _materials_by_document(items: list[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for item in items:
        grouped.setdefault(str(item.get("document_id") or ""), []).append(item)
    return grouped


def _related_materials(materials: list[Mapping[str, Any]]) -> str:
    if not materials:
        return ""
    links = "".join(_material_card(item) for item in materials[:4])
    return f'<section class="related"><h3>相关外部研究/解读资料</h3><div class="material-list">{links}</div></section>'


def _interpretation_section(items: list[Mapping[str, Any]]) -> str:
    if not items:
        return ""
    refs = reference_items(items)
    ref_cards = "".join(_reference_card(item) for item in refs)
    sections = [
        '<section id="interpretations" class="reference-section"><h2 class="section-title">三、外部研究与解读资料来源</h2>'
    ]
    if ref_cards:
        sections.append('<h3 class="sub-title">计入本报告分析的外部参考</h3>')
        sections.append(f'<section class="material-list">{ref_cards}</section>')
    gap_summary = external_reference_gap_summary_for_items(items)
    if int(gap_summary.get("pending_count", 0) or 0):
        sections.append(
            '<p class="empty">候选线索和缺口见运营 dashboard；'
            f'当前待处理缺口 {html.escape(str(gap_summary.get("pending_count", 0)))} 个。'
            'PDF 仅保留正式参考。</p>'
        )
    sections.append("</section>")
    return "".join(sections)


def _queue_section(items: list[Mapping[str, Any]]) -> str:
    if not items:
        body = '<section class="empty">当前没有待生产研究报告，或本次尚未同步到候选文件。</section>'
    else:
        cards = "".join(_queue_card(index, item) for index, item in enumerate(items, start=1))
        body = f'<section class="material-list">{cards}</section>'
    return f'<h2 id="queue" class="section-title">四、待生产研究报告队列</h2>{body}'


def _queue_card(index: int, item: Mapping[str, Any]) -> str:
    title = html.escape(_clean_title(item.get("title")))
    source = html.escape(str(item.get("source_name") or "未知来源"))
    industry = html.escape(str(item.get("primary_industry") or item.get("industry") or "待研判行业"))
    sort_time = html.escape(
        str(item.get("sort_time") or item.get("published_date") or item.get("discovered_at") or "未知时间")
    )
    level = html.escape(str(item.get("administrative_level") or "unknown"))
    score = html.escape(str(item.get("priority_score") or item.get("authority_score_snapshot") or "NA"))
    rank = html.escape(str(item.get("industry_rank") or "NA"))
    return (
        '<article class="material">'
        f'<strong>{index}. {title}</strong>'
        f'<span>行业：{industry}｜行业序号：{rank}｜时间：{sort_time}｜层级：{level}｜优先级：{score}</span>'
        f'<span>来源：{source}</span>'
        '</article>'
    )


def _material_card(item: Mapping[str, Any]) -> str:
    title = html.escape(_truncate(str(item.get("title") or "外部研究/解读资料"), 56))
    url = html.escape(str(item.get("url") or ""))
    platform = html.escape(str(item.get("platform") or "未知平台"))
    status = html.escape(str(item.get("evidence_status") or "待验证"))
    summary = html.escape(_truncate(str(item.get("content_excerpt") or item.get("summary") or ""), 120))
    meta = html.escape(_material_meta_text(item))
    return (
        '<article class="material">'
        f'<strong><a href="{url}">{title}</a></strong>'
        f'<span>{meta}｜状态：{status}</span>'
        f'<span>{summary}</span>'
        '</article>'
    )


def _reference_card(item: Mapping[str, Any]) -> str:
    title = html.escape(_truncate(str(item.get("title") or "外部研究/解读资料"), 64))
    url = html.escape(str(item.get("url") or ""))
    status = html.escape(_truncate(str(item.get("evidence_status") or "待验证"), 42))
    meta = html.escape(_material_meta_text(item))
    return (
        '<article class="material">'
        f'<strong><a href="{url}">{title}</a></strong>'
        f'<span>{meta}｜状态：{status}</span>'
        '</article>'
    )


def _gap_card(gap: Mapping[str, Any]) -> str:
    title = html.escape(_truncate(_clean_title(gap.get("title")), 56))
    url = html.escape(str(gap.get("url") or ""))
    platform = html.escape(str(gap.get("platform") or "未知平台"))
    gap_type = html.escape(gap_type_label(str(gap.get("gap_type") or "")))
    action = html.escape(gap_action_label(str(gap.get("required_action") or "")))
    score = html.escape(str(gap.get("priority_score") or 0))
    evidence = html.escape(_truncate(str(gap.get("evidence_status") or ""), 90))
    link_title = f'<a href="{url}">{title}</a>' if url else title
    return (
        '<article class="material">'
        f'<strong>{link_title}</strong>'
        f'<span>平台：{platform}｜缺口：{gap_type}｜建议动作：{action}｜优先级：{score}</span>'
        f'<span>状态：{evidence}</span>'
        '</article>'
    )


def _material_meta_text(item: Mapping[str, Any]) -> str:
    parts = [f"平台：{item.get('platform') or '未知平台'}"]
    metadata = item.get("raw_metadata") if isinstance(item.get("raw_metadata"), Mapping) else {}
    if item.get("author_name"):
        parts.append(f"作者/UP主：{item.get('author_name')}")
    if metadata.get("author_verified_desc"):
        parts.append(f"作者认证：{metadata.get('author_verified_desc')}")
    if metadata.get("author_follower_count") is not None:
        parts.append(f"粉丝：{_format_count(metadata.get('author_follower_count'))}")
    if item.get("view_count") is not None:
        parts.append(f"播放/阅读：{_format_count(item.get('view_count'))}")
    if item.get("relevance_score"):
        parts.append(f"相关度：{item.get('relevance_score')}")
    parts.append("计入参考" if is_reference_item(item) else "补充线索")
    return "｜".join(parts)


def _reference_min(stats: Mapping[str, int]) -> int:
    return int(stats.get("min_external_references", 5) or 5)


def _platform_min(stats: Mapping[str, int]) -> int:
    return int(stats.get("min_external_platforms", 2) or 2)


def _reference_count(stats: Mapping[str, int], items: list[Mapping[str, Any]]) -> int:
    return int(stats.get("external_reference_count", count_reference_items(items)) or 0)


def _platform_count(items: list[Mapping[str, Any]]) -> int:
    return len(reference_platforms(items))


def _reference_status(stats: Mapping[str, int], items: list[Mapping[str, Any]]) -> str:
    count = _reference_count(stats, items)
    minimum = _reference_min(stats)
    platforms = reference_platforms(items)
    platform_min = _platform_min(stats)
    platform_count = len(platforms)
    if count >= minimum and platform_count >= platform_min:
        return f"达标，{count}份参考，覆盖{platform_count}个平台：{'、'.join(platforms) or '未识别'}"
    deficits = []
    if count < minimum:
        deficits.append(f"缺少{minimum - count}份可计入参考")
    if platform_count < platform_min:
        deficits.append(f"缺少{platform_min - platform_count}个外部平台")
    return "未达标，" + "，".join(deficits)


def _reference_quality_banner(stats: Mapping[str, int], items: list[Mapping[str, Any]]) -> str:
    count = _reference_count(stats, items)
    minimum = _reference_min(stats)
    status = html.escape(_reference_status(stats, items))
    klass = "summary" if count >= minimum else "summary warning"
    return f'<section class="{klass}">外部参考质量门槛：{status}。单纯搜索入口、需登录/验证码来源不计入达标数。</section>'


def _format_count(value: object) -> str:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return str(value or "未知")
    if number >= 10000:
        return f"{number / 10000:.1f}万"
    return str(number)


def _truncate(value: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _html_block(title: str, value: object, extra_class: str = "") -> str:
    items = _json_items(value)
    if not items:
        items = ["暂无信息。"]
    lis = "".join(f"<li>{html.escape(str(item))}</li>" for item in items)
    klass = f"block {extra_class}".strip()
    return f'<section class="{klass}"><h3>{html.escape(title)}</h3><ul>{lis}</ul></section>'


def _json_section(lines: list[str], title: str, value: object) -> None:
    items = _json_items(value)
    if not items:
        return
    lines.extend([f"**{title}**", ""])
    for item in items:
        lines.append(f"- {item}")
    lines.append("")


def _json_items(value: object) -> list[object]:
    if not value:
        return []
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        cleaned = _clean_report_item(str(value))
        return [cleaned] if cleaned else []
    if isinstance(parsed, list):
        cleaned_items: list[object] = []
        for item in parsed:
            if isinstance(item, str):
                cleaned = _clean_report_item(item)
                if cleaned:
                    cleaned_items.append(cleaned)
            else:
                cleaned_items.append(item)
        return cleaned_items
    return [parsed]


def _clean_report_item(value: str) -> str:
    text = _strip_external_reference_claims(value)
    if "外部解读资料当前集中出现的主题" in text:
        return ""
    if "本次已同步参考" in text:
        return ""
    return text


def _executive_summary(stats: Mapping[str, int], documents: list[Mapping[str, Any]]) -> str:
    analyzed = stats.get("analyzed_documents", 0)
    discovered = stats.get("documents_discovered", 0)
    new_docs = stats.get("new_documents", 0)
    if not documents:
        return "本次运行未发现可纳入分析的政策文件线索。建议检查来源库、抓取入口和网络状态。"
    doc = documents[0]
    return (
        f"本次运行共发现{discovered}条政策文件线索，其中新增{new_docs}条；"
        f"本报告只研究 1 份文件：《{_clean_title(doc.get('title'))}》。"
        f"该文件来源为{doc.get('source_name')}，权威等级{doc.get('authority_tier_snapshot')}/{doc.get('authority_score_snapshot')}，"
        f"重要性评分{doc.get('importance_score') or '待分析'}。"
        f"本轮自动分析文件数为{analyzed}；其余候选文件进入待生产队列，等待后续自动化或提前生成。"
    )


def _doc_type(value: object) -> str:
    if value == "attachment":
        return "附件"
    if value == "webpage":
        return "网页正文"
    return str(value or "未知类型")


def _clean_title(value: object) -> str:
    text = str(value or "未命名文件").strip()
    suffixes = (
        "_国务院办公厅政府信息公开指南（试行）_信息公开_政策_中国政府网",
        "_其他_中国政府网",
        "__中国政府网",
        "_中国政府网",
        "_其他",
    )
    for suffix in suffixes:
        if text.endswith(suffix):
            text = text[: -len(suffix)]
    return text.strip(" _-")
