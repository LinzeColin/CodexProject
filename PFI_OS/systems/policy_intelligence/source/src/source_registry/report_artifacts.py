from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any, Mapping


REFERENCE_PAGE_CHAR_TARGET = 2200
BUSINESS_VALUE_DENSITY_TARGET = 95
LOW_VALUE_PATTERNS = [
    r"暂无(信息|综合研判|自动摘要|历史事件|数据)",
    r"待(识别|分析|研判|分类)",
    r"未知(来源|时间|平台|类型)",
    r"正文条款尚未完整抽取",
    r"影响路径需要结合行业与地区配套政策继续拆解",
    r"当前未形成足够可计入的外部参考标题",
]


def inspect_report_artifacts(report_path: str | Path | None) -> dict[str, Any]:
    if not report_path:
        return _empty_report_check("")
    pdf_path = Path(report_path)
    html_path = pdf_path.with_suffix(".html")
    markdown_path = pdf_path.with_suffix(".md")
    dashboard_path = pdf_path.with_name(f"{pdf_path.stem}_dashboard.html")
    html_text = _read_text(html_path)
    markdown_text = _read_text(markdown_path)
    pdf_page_count = _pdf_page_count(pdf_path)
    pdf_text_char_count = _pdf_text_char_count(pdf_path)
    html_visible_text_char_count = len(_visible_text(html_text))
    reference_text = _reference_section_text(html_text or markdown_text)
    value_density = _business_value_density(html_text or markdown_text)
    report_document_count = _report_document_count(html_text, markdown_text)
    deep_chapter_count = _deep_chapter_count(html_text, markdown_text)
    toc_anchor_count = len(re.findall(r'href="#[^"]+"', html_text))
    result = {
        "report_path": str(pdf_path),
        "report_exists": pdf_path.exists(),
        "primary_report_suffix": pdf_path.suffix,
        "pdf_size_bytes": pdf_path.stat().st_size if pdf_path.exists() else 0,
        "pdf_page_count": pdf_page_count,
        "html_path": str(html_path),
        "html_exists": html_path.exists(),
        "html_size_bytes": html_path.stat().st_size if html_path.exists() else 0,
        "html_visible_text_char_count": html_visible_text_char_count,
        "business_value_density_score": value_density["score"],
        "business_value_low_value_units": value_density["low_value_units"],
        "business_value_total_units": value_density["total_units"],
        "business_value_repeated_units": value_density["repeated_units"],
        "markdown_path": str(markdown_path),
        "markdown_exists": markdown_path.exists(),
        "dashboard_path": str(dashboard_path),
        "dashboard_exists": dashboard_path.exists(),
        "pdf_text_char_count": pdf_text_char_count,
        "report_document_count": report_document_count,
        "deep_chapter_count": deep_chapter_count,
        "toc_present": "<nav class=\"toc\"" in html_text,
        "toc_anchor_count": toc_anchor_count,
        "quality_rules_panel_present": "规则化质量门槛" in html_text,
        "visual_dashboard_present": "研究质量与交付状态" in html_text
        or "运行可视化仪表盘" in html_text
        or "政策监测运营仪表盘" in html_text
        or dashboard_path.exists(),
        "reference_section_present": bool(reference_text.strip()),
        "reference_section_char_count": len(reference_text.strip()),
        "reference_section_estimated_pages": round(len(reference_text.strip()) / REFERENCE_PAGE_CHAR_TARGET, 2)
        if reference_text.strip()
        else 0,
        "reference_section_compact": len(reference_text.strip()) <= REFERENCE_PAGE_CHAR_TARGET
        if reference_text.strip()
        else False,
        "blank_risk": _blank_risk(
            pdf_path,
            html_path,
            pdf_text_char_count=pdf_text_char_count,
            html_visible_text_char_count=html_visible_text_char_count,
        ),
    }
    result["checks"] = _checks(result)
    result["summary"] = {
        "check_count": len(result["checks"]),
        "passed_count": sum(1 for item in result["checks"] if item["status"] == "passed"),
        "failed_count": sum(1 for item in result["checks"] if item["status"] == "failed"),
        "warning_count": sum(1 for item in result["checks"] if item["status"] == "warning"),
    }
    return result


def write_report_artifact_dashboard(
    path: str | Path,
    *,
    report_path: str | Path | None,
    title: str = "报告产物自检 dashboard",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    check = inspect_report_artifacts(report_path)
    output.write_text(render_report_artifact_dashboard(check, title=title), encoding="utf-8")
    return str(output)


def render_report_artifact_dashboard(
    check: Mapping[str, Any],
    *,
    title: str = "报告产物自检 dashboard",
) -> str:
    summary = check.get("summary") or {}
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --ink: #172033;
      --muted: #667085;
      --line: #d0d5dd;
      --paper: #f4f6f8;
      --panel: #ffffff;
      --teal: #0b6477;
      --green: #177245;
      --amber: #9a4a13;
      --red: #9b2c2c;
      --soft: #f8fafc;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--paper);
      font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", Arial, sans-serif;
      line-height: 1.55;
    }}
    .page {{ max-width: 1320px; margin: 0 auto; padding: 24px 20px 52px; }}
    .hero {{ background: var(--panel); border-top: 5px solid var(--teal); border-bottom: 1px solid var(--line); padding: 18px 0 16px; }}
    .hero h1 {{ margin: 2px 0 8px; color: #063f4b; font-size: 28px; line-height: 1.22; }}
    .hero p {{ margin: 0; color: var(--muted); overflow-wrap: anywhere; }}
    .metrics {{ display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); border: 1px solid var(--line); background: var(--panel); margin: 14px 0; }}
    .metric {{ padding: 10px 12px; border-right: 1px solid var(--line); min-height: 70px; }}
    .metric:last-child {{ border-right: 0; }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; }}
    .metric strong {{ display: block; color: #063f4b; font-size: 22px; }}
    .grid {{ display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 12px; }}
    .panel {{ grid-column: span 6; background: var(--panel); border: 1px solid var(--line); padding: 13px 14px; }}
    .panel.wide {{ grid-column: 1 / -1; }}
    .panel h2 {{ margin: 0 0 10px; color: #063f4b; font-size: 16px; }}
    .note {{ margin: 8px 0 0; color: var(--muted); font-size: 12px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ border: 1px solid var(--line); padding: 7px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf4f7; color: #063f4b; }}
    td {{ background: var(--panel); }}
    .passed {{ color: var(--green); font-weight: 700; }}
    .failed {{ color: var(--red); font-weight: 700; }}
    .warning {{ color: var(--amber); font-weight: 700; }}
    .cmd {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; overflow-wrap: anywhere; font-size: 11px; }}
    @media (max-width: 900px) {{
      .metrics {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
      .panel {{ grid-column: 1 / -1; }}
    }}
    @media (max-width: 620px) {{
      .page {{ padding: 18px 12px 40px; }}
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      table {{ font-size: 11px; }}
      th, td {{ padding: 6px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <p>Report Artifact Verification</p>
      <h1>{html.escape(title)}</h1>
      <p>{html.escape(str(check.get("report_path") or ""))}</p>
    </section>
    <section class="metrics">
      {_metric("检查项", summary.get("check_count", 0))}
      {_metric("通过", summary.get("passed_count", 0))}
      {_metric("失败", summary.get("failed_count", 0))}
      {_metric("警告", summary.get("warning_count", 0))}
      {_metric("PDF 页数", check.get("pdf_page_count", 0))}
      {_metric("深度章节", check.get("deep_chapter_count", 0))}
    </section>
    <section class="grid">
      {_check_table(list(check.get("checks") or []))}
      {_metric_table(check)}
    </section>
  </main>
</body>
</html>
"""


def _empty_report_check(report_path: str) -> dict[str, Any]:
    return {
        "report_path": report_path,
        "report_exists": False,
        "primary_report_suffix": "",
        "pdf_page_count": 0,
        "report_document_count": 0,
        "deep_chapter_count": 0,
        "checks": [{"id": "report_path", "label": "报告路径", "status": "failed", "actual": "", "expected": "非空 PDF 路径"}],
        "summary": {"check_count": 1, "passed_count": 0, "failed_count": 1, "warning_count": 0},
    }


def _checks(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    checks = [
        _check("pdf_exists", "PDF 存在", bool(result.get("report_exists")), result.get("report_path"), "文件存在"),
        _check("pdf_not_blank", "PDF 非空", int(result.get("pdf_size_bytes") or 0) > 1024, result.get("pdf_size_bytes"), "> 1024 bytes"),
        _check("pdf_page_count", "PDF 页数不少于 10", int(result.get("pdf_page_count") or 0) >= 10, result.get("pdf_page_count"), ">= 10"),
        _check(
            "visible_content_density",
            "可见内容密度",
            int(result.get("pdf_text_char_count") or 0) >= 500
            or int(result.get("html_visible_text_char_count") or 0) >= 1200,
            f"pdf_text={result.get('pdf_text_char_count', 0)}, html_text={result.get('html_visible_text_char_count', 0)}",
            "PDF text >= 500 or HTML visible text >= 1200",
        ),
        _check("html_exists", "HTML sidecar 存在", bool(result.get("html_exists")), result.get("html_path"), "文件存在"),
        _check("markdown_exists", "Markdown sidecar 存在", bool(result.get("markdown_exists")), result.get("markdown_path"), "文件存在"),
        _check("dashboard_exists", "Dashboard sidecar 存在", bool(result.get("dashboard_exists")), result.get("dashboard_path"), "文件存在"),
        _check("single_document", "每份报告 1 份文件", int(result.get("report_document_count") or 0) == 1, result.get("report_document_count"), "== 1"),
        _check("deep_chapters", "10 个深度章节", int(result.get("deep_chapter_count") or 0) >= 10, result.get("deep_chapter_count"), ">= 10"),
        _check("toc_present", "可点击目录存在", bool(result.get("toc_present")) and int(result.get("toc_anchor_count") or 0) > 0, result.get("toc_anchor_count"), "> 0 anchors"),
        _check("quality_rules_panel", "规则化质量门槛面板", bool(result.get("quality_rules_panel_present")), result.get("quality_rules_panel_present"), "present"),
        _check("visual_dashboard", "研究质量/仪表盘面板", bool(result.get("visual_dashboard_present")), result.get("visual_dashboard_present"), "present"),
        _check("not_blank", "文件不是空白", not bool(result.get("blank_risk")), result.get("blank_risk"), "False"),
        _check(
            "business_value_density",
            "商务高价值信息密度",
            float(result.get("business_value_density_score") or 0) >= BUSINESS_VALUE_DENSITY_TARGET,
            result.get("business_value_density_score"),
            f">= {BUSINESS_VALUE_DENSITY_TARGET}",
        ),
    ]
    reference_present = bool(result.get("reference_section_present"))
    checks.append(
        {
            "id": "reference_section",
            "label": "Reference 区域存在",
            "status": "passed" if reference_present else "warning",
            "actual": result.get("reference_section_char_count", 0),
            "expected": "存在；目标紧凑",
        }
    )
    compact = bool(result.get("reference_section_compact"))
    if reference_present:
        checks.append(
            {
                "id": "reference_section_compact",
                "label": "Reference 区域约 1 页内",
                "status": "passed" if compact else "warning",
                "actual": result.get("reference_section_estimated_pages", 0),
                "expected": "<= 1 estimated page",
            }
        )
    return checks


def _check(id_: str, label: str, passed: bool, actual: Any, expected: str) -> dict[str, Any]:
    return {
        "id": id_,
        "label": label,
        "status": "passed" if passed else "failed",
        "actual": actual,
        "expected": expected,
    }


def _pdf_page_count(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        import pypdf  # type: ignore

        return len(pypdf.PdfReader(str(path)).pages)
    except Exception:
        try:
            data = path.read_bytes()
        except OSError:
            return 0
        return max(0, len(re.findall(rb"/Type\s*/Page\b", data)))


def _pdf_text_char_count(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        import fitz  # type: ignore

        with fitz.open(path) as doc:
            return len("".join(page.get_text() for page in doc))
    except Exception:
        pass
    try:
        import pypdf  # type: ignore

        reader = pypdf.PdfReader(str(path))
        return len("".join(page.extract_text() or "" for page in reader.pages))
    except Exception:
        return 0


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _report_document_count(html_text: str, markdown_text: str) -> int:
    for text in (html_text, markdown_text):
        match = re.search(r"本报告研究文件数[：:]\s*(\d+)", text)
        if match:
            return int(match.group(1))
    doc_cards = len(re.findall(r'class="doc-card"', html_text))
    return doc_cards


def _deep_chapter_count(html_text: str, markdown_text: str) -> int:
    html_count = len(re.findall(r'class="deep-chapter"', html_text))
    if html_count:
        return html_count
    return len(re.findall(r"^#{2,4}\s*\d+\.", markdown_text, flags=re.MULTILINE))


def _reference_section_text(text: str) -> str:
    if not text:
        return ""
    section_match = re.search(
        r'<section[^>]*\bid=["\']interpretations["\'][^>]*>(.*?)(?=<(?:section|h[1-6])[^>]*\bid=["\']queue["\']|<(?:section|h[1-6])[^>]*\bid=["\']timeline["\']|</body>)',
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if section_match:
        return _visible_text(section_match.group(1))
    start = text.find("外部研究与解读资料来源")
    if start >= 0 and "<nav" in text[:start].lower():
        later_start = text.find("外部研究与解读资料来源", start + 1)
        if later_start >= 0:
            start = later_start
    if start < 0:
        return ""
    endings = [
        text.find(marker, start + 1)
        for marker in ["待生产研究报告队列", "免责声明", "附录"]
        if text.find(marker, start + 1) > start
    ]
    end = min(endings) if endings else min(len(text), start + 5000)
    cleaned = re.sub(r"<[^>]+>", " ", text[start:end])
    return re.sub(r"\s+", " ", cleaned).strip()


def _visible_text(html_text: str) -> str:
    if not html_text:
        return ""
    without_hidden = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html_text, flags=re.IGNORECASE | re.DOTALL)
    visible = re.sub(r"<[^>]+>", " ", without_hidden)
    return re.sub(r"\s+", " ", html.unescape(visible)).strip()


def _business_value_density(text: str) -> dict[str, Any]:
    units = _business_value_units(text)
    if not units:
        return {"score": 0, "low_value_units": 0, "total_units": 0, "repeated_units": 0}
    seen: set[str] = set()
    low_value = 0
    repeated = 0
    for unit in units:
        normalized = re.sub(r"\d+", "#", unit)
        if normalized in seen and len(normalized) >= 18:
            repeated += 1
            low_value += 1
            continue
        seen.add(normalized)
        if _is_low_value_unit(unit):
            low_value += 1
    score = round(max(0, 100 * (1 - low_value / len(units))), 1)
    return {
        "score": score,
        "low_value_units": low_value,
        "total_units": len(units),
        "repeated_units": repeated,
    }


def _business_value_units(text: str) -> list[str]:
    if not text:
        return []
    if "<" in text and ">" in text:
        candidates = re.findall(
            r"<(?:p|li|td|th|h[1-6])[^>]*>(.*?)</(?:p|li|td|th|h[1-6])>",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        units = [_visible_text(candidate) for candidate in candidates]
    else:
        visible = _visible_text(text)
        units = re.split(r"[。！？!?]\s*|\n+", visible)
    return [unit.strip() for unit in units if len(unit.strip()) >= 6]


def _is_low_value_unit(unit: str) -> bool:
    text = re.sub(r"\s+", " ", unit).strip()
    if any(re.search(pattern, text) for pattern in LOW_VALUE_PATTERNS):
        return True
    if len(text) > 360 and not re.search(r"\d|%|：|:|http|www\.|《|》", text):
        return True
    return False


def _blank_risk(
    pdf_path: Path,
    html_path: Path,
    *,
    pdf_text_char_count: int,
    html_visible_text_char_count: int,
) -> bool:
    if not pdf_path.exists() or pdf_path.stat().st_size <= 1024:
        return True
    if pdf_text_char_count < 100 and html_visible_text_char_count < 500:
        return True
    if html_path.exists() and html_visible_text_char_count < 500:
        return True
    return False


def _metric(label: str, value: object) -> str:
    return (
        '<article class="metric">'
        f"<span>{html.escape(str(label))}</span>"
        f"<strong>{html.escape(str(value))}</strong>"
        "</article>"
    )


def _check_table(checks: list[Mapping[str, Any]]) -> str:
    rows = []
    for item in checks:
        status = str(item.get("status") or "")
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('label') or item.get('id') or ''))}</td>"
            f'<td class="{html.escape(status)}">{html.escape(status)}</td>'
            f"<td>{html.escape(str(item.get('actual') or ''))}</td>"
            f"<td>{html.escape(str(item.get('expected') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>自检结果</h2>'
        '<table><thead><tr><th>检查项</th><th>状态</th><th>当前值</th><th>期望</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></article>'
    )


def _metric_table(check: Mapping[str, Any]) -> str:
    keys = [
        "report_path",
        "pdf_size_bytes",
        "pdf_page_count",
        "pdf_text_char_count",
        "html_size_bytes",
        "html_visible_text_char_count",
        "report_document_count",
        "deep_chapter_count",
        "toc_anchor_count",
        "reference_section_char_count",
        "reference_section_estimated_pages",
        "business_value_density_score",
        "business_value_low_value_units",
        "business_value_total_units",
        "business_value_repeated_units",
        "blank_risk",
    ]
    rows = "".join(
        f"<tr><td>{html.escape(key)}</td><td class=\"cmd\">{html.escape(str(check.get(key, '')))}</td></tr>"
        for key in keys
    )
    return (
        '<article class="panel wide"><h2>产物指标</h2>'
        f'<table><tbody>{rows}</tbody></table>'
        '<p class="note">Reference 页数为字符数估算，主要用于发现明显过长，不用于删除参考数量。</p></article>'
    )
