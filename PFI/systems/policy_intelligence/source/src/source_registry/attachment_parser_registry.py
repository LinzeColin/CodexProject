from __future__ import annotations

import html
import importlib.util
import json
import os
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping


DEFAULT_ATTACHMENT_PARSER_FILE = "config/attachment_parsers.json"


def load_attachment_parser_registry(path: str | Path | None = None) -> dict[str, Any]:
    registry_path = Path(path or DEFAULT_ATTACHMENT_PARSER_FILE)
    if not registry_path.exists():
        return {
            "last_refreshed": "",
            "source_note": "attachment parser config missing",
            "parsers": [],
            "capability_targets": [],
        }
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("attachment parser config must be a JSON object")
    parsers = payload.get("parsers") or []
    targets = payload.get("capability_targets") or []
    return {
        "last_refreshed": str(payload.get("last_refreshed") or ""),
        "source_note": str(payload.get("source_note") or ""),
        "parsers": [dict(item) for item in parsers if isinstance(item, Mapping)],
        "capability_targets": [dict(item) for item in targets if isinstance(item, Mapping)],
    }


def build_attachment_parser_status(
    path: str | Path | None = None,
    *,
    dependency_probe: Callable[[], list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    registry = load_attachment_parser_registry(path)
    parsers = registry["parsers"]
    targets = registry["capability_targets"]
    status_counts = Counter(str(parser.get("status") or "unknown") for parser in parsers)
    family_counts = Counter(str(parser.get("family") or "unknown") for parser in parsers)
    formats = sorted({str(fmt) for parser in parsers for fmt in parser.get("formats") or [] if fmt})
    capability_rows = _capability_rows(parsers, targets)
    dependency_rows = dependency_probe() if dependency_probe else probe_attachment_parser_dependencies()
    dependency_counts = Counter(str(row.get("status") or "unknown") for row in dependency_rows)
    summary = {
        "parser_count": len(parsers),
        "ready_count": int(status_counts.get("ready", 0)),
        "partial_count": int(status_counts.get("partial", 0)),
        "planned_count": int(status_counts.get("planned", 0)),
        "format_count": len(formats),
        "required_capability_count": sum(1 for target in targets if target.get("required_for_report_quality")),
        "acceptance_check_count": sum(1 for parser in parsers if parser.get("acceptance_check")),
        "dependency_ready_count": int(dependency_counts.get("ready", 0)),
        "dependency_missing_count": int(dependency_counts.get("missing", 0)),
        "dependency_configured_count": int(dependency_counts.get("configured_not_checked", 0)),
    }
    return {
        **registry,
        "summary": summary,
        "status_counts": dict(status_counts),
        "family_counts": dict(family_counts),
        "dependency_counts": dict(dependency_counts),
        "dependency_rows": dependency_rows,
        "formats": formats,
        "capability_rows": capability_rows,
        "parser_queue": sorted(parsers, key=lambda item: int(item.get("priority") or 0), reverse=True),
    }


def write_attachment_parser_dashboard(
    path: str | Path,
    *,
    parser_file: str | Path | None = None,
    title: str = "附件解析能力 dashboard",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    status = build_attachment_parser_status(parser_file)
    output.write_text(render_attachment_parser_dashboard(status, title=title), encoding="utf-8")
    return str(output)


def render_attachment_parser_dashboard(
    status: Mapping[str, Any],
    *,
    title: str = "附件解析能力 dashboard",
) -> str:
    summary = status.get("summary") or {}
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
      --blue: #155eef;
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
    .hero p {{ margin: 0; color: var(--muted); }}
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
    .bars {{ display: grid; gap: 8px; }}
    .bar {{ display: grid; grid-template-columns: minmax(120px, 210px) 1fr 48px; gap: 8px; align-items: center; font-size: 12px; }}
    .label {{ overflow-wrap: anywhere; }}
    .track {{ height: 10px; border: 1px solid #d5e2e6; background: #e7eef1; }}
    .fill {{ display: block; height: 100%; background: var(--teal); }}
    .fill.ready {{ background: var(--green); }}
    .fill.partial {{ background: var(--amber); }}
    .fill.planned {{ background: var(--blue); }}
    .value {{ color: #063f4b; font-weight: 700; text-align: right; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ border: 1px solid var(--line); padding: 7px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf4f7; color: #063f4b; }}
    td {{ background: var(--panel); }}
    .pill {{ display: inline-block; border: 1px solid var(--line); background: var(--soft); padding: 2px 7px; margin: 2px 3px 2px 0; }}
    .cmd {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; overflow-wrap: anywhere; font-size: 11px; }}
    @media (max-width: 980px) {{
      .metrics {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
      .panel {{ grid-column: 1 / -1; }}
    }}
    @media (max-width: 620px) {{
      .page {{ padding: 18px 12px 40px; }}
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .bar {{ grid-template-columns: 100px 1fr 40px; }}
      table {{ font-size: 11px; }}
      th, td {{ padding: 6px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <p>Attachment Parsing Capability Registry</p>
      <h1>{html.escape(title)}</h1>
      <p>刷新日期：{html.escape(str(status.get("last_refreshed") or ""))}｜只展示能力、缺口和验收标准，不展示正文、cookie、API key 或账号信息。</p>
    </section>
    <section class="metrics">
      {_metric("解析器", summary.get("parser_count", 0))}
      {_metric("ready", summary.get("ready_count", 0))}
      {_metric("partial", summary.get("partial_count", 0))}
      {_metric("planned", summary.get("planned_count", 0))}
      {_metric("格式覆盖", summary.get("format_count", 0))}
      {_metric("依赖 ready", summary.get("dependency_ready_count", 0))}
    </section>
    <section class="grid">
      {_counter_panel("落地状态", status.get("status_counts") or {})}
      {_counter_panel("解析器家族", status.get("family_counts") or {})}
      {_formats_panel(list(status.get("formats") or []))}
      {_dependency_panel(list(status.get("dependency_rows") or []))}
      {_capability_panel(list(status.get("capability_rows") or []))}
      {_parser_table(list(status.get("parser_queue") or []))}
      {_implementation_queue(list(status.get("parser_queue") or []))}
      {_boundary_panel(str(status.get("source_note") or ""))}
    </section>
  </main>
</body>
</html>
"""


def _capability_rows(parsers: list[Mapping[str, Any]], targets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    parser_by_capability: dict[str, list[str]] = {}
    for parser in parsers:
        for tag in parser.get("capability_tags") or []:
            parser_by_capability.setdefault(str(tag), []).append(str(parser.get("name") or ""))
    rows = []
    for target in targets:
        capability = str(target.get("capability") or "")
        names = parser_by_capability.get(capability, [])
        rows.append(
            {
                "capability": capability,
                "label": str(target.get("label") or capability),
                "required": bool(target.get("required_for_report_quality")),
                "parser_count": len(names),
                "parsers": names,
            }
        )
    return sorted(rows, key=lambda item: (not item["required"], -int(item["parser_count"]), item["label"]))


def probe_attachment_parser_dependencies(
    *,
    environ: Mapping[str, str] | None = None,
    module_available: Callable[[str], bool] | None = None,
    binary_available: Callable[[str], bool] | None = None,
) -> list[dict[str, Any]]:
    env = environ or os.environ
    module_check = module_available or _module_available
    binary_check = binary_available or _binary_available
    return [
        _dependency_row(
            "pypdf",
            "PDF 文本层",
            "python_module",
            "ready" if module_check("pypdf") else "missing",
            "PDF text-layer parser 首选引擎。",
            "安装 pypdf 或确认运行时可导入。",
        ),
        _dependency_row(
            "pymupdf",
            "PDF 文本/OCR 渲染",
            "python_module",
            "ready" if module_check("fitz") else "missing",
            "PDF 文本层 fallback 与扫描 PDF OCR 渲染引擎。",
            "安装 PyMuPDF；缺失时扫描 PDF OCR 不可用。",
        ),
        _dependency_row(
            "pillow",
            "图片读取",
            "python_module",
            "ready" if module_check("PIL") else "missing",
            "图片 OCR 和 PDF 页面图像读取前置依赖。",
            "安装 Pillow。",
        ),
        _dependency_row(
            "pytesseract",
            "OCR Python bridge",
            "python_module",
            "ready" if module_check("pytesseract") else "missing",
            "调用本地 tesseract OCR 的 Python bridge。",
            "安装 pytesseract。",
        ),
        _dependency_row(
            "tesseract_binary",
            "OCR engine",
            "system_binary",
            "ready" if binary_check("tesseract") else "missing",
            "真正执行 OCR 的系统二进制；仅有 pytesseract 不够。",
            "安装 tesseract 及中文语言包 chi_sim。",
        ),
        _dependency_row(
            "apache_tika",
            "旧 Office / 复杂附件",
            "external_service",
            "configured_not_checked" if env.get("TIKA_SERVER_URL") else "missing",
            "DOC/XLS/PPT/RTF/ODT 等旧格式外部服务入口。",
            "设置 TIKA_SERVER_URL 并单独做健康检查；当前不自动联网。",
        ),
        _dependency_row(
            "grobid",
            "研究 PDF 结构化",
            "external_service",
            "configured_not_checked" if env.get("GROBID_SERVER_URL") else "missing",
            "智库/论文型 PDF 的章节、作者和参考文献抽取入口。",
            "设置 GROBID_SERVER_URL 并单独做健康检查；当前不自动联网。",
        ),
    ]


def _dependency_row(
    dependency: str,
    label: str,
    kind: str,
    status: str,
    business_value: str,
    next_action: str,
) -> dict[str, Any]:
    return {
        "dependency": dependency,
        "label": label,
        "kind": kind,
        "status": status,
        "business_value": business_value,
        "next_action": "" if status == "ready" else next_action,
    }


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _binary_available(name: str) -> bool:
    return shutil.which(name) is not None


def _metric(label: str, value: object) -> str:
    return (
        '<article class="metric">'
        f"<span>{html.escape(str(label))}</span>"
        f"<strong>{html.escape(str(value))}</strong>"
        "</article>"
    )


def _counter_panel(title: str, values: Mapping[str, int]) -> str:
    rows = [(str(label), int(count)) for label, count in values.items()]
    if not rows:
        return f'<article class="panel"><h2>{html.escape(title)}</h2><p class="note">暂无数据。</p></article>'
    maximum = max([count for _, count in rows] + [1])
    return (
        f'<article class="panel"><h2>{html.escape(title)}</h2><section class="bars">'
        f'{"".join(_bar_row(label, count, maximum, label) for label, count in sorted(rows))}'
        "</section></article>"
    )


def _formats_panel(formats: list[str]) -> str:
    pills = "".join(f'<span class="pill">{html.escape(item)}</span>' for item in formats)
    return (
        '<article class="panel"><h2>格式覆盖</h2>'
        f"<p>{pills or '暂无格式。'}</p>"
        '<p class="note">ready/partial 格式可进入抽取或可审计失败；planned 格式不直接承诺交付。</p>'
        "</article>"
    )


def _dependency_panel(rows: list[Mapping[str, Any]]) -> str:
    rendered = []
    for row in rows:
        status = str(row.get("status") or "")
        rendered.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('label') or row.get('dependency') or ''))}</td>"
            f"<td>{html.escape(str(row.get('kind') or ''))}</td>"
            f"<td>{html.escape(status)}</td>"
            f"<td>{html.escape(str(row.get('business_value') or ''))}</td>"
            f"<td>{html.escape(str(row.get('next_action') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>运行依赖验收</h2>'
        '<table><thead><tr><th>依赖</th><th>类型</th><th>状态</th><th>用途</th><th>下一步</th></tr></thead>'
        f'<tbody>{"".join(rendered) if rendered else "<tr><td colspan=\"5\">暂无依赖信息。</td></tr>"}</tbody></table>'
        '<p class="note">外部服务只检查配置入口，不主动联网；避免在 dashboard 生成时触发不可控请求。</p></article>'
    )


def _capability_panel(rows: list[Mapping[str, Any]]) -> str:
    rendered = []
    for row in rows:
        rendered.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('label') or ''))}</td>"
            f"<td>{'是' if row.get('required') else '否'}</td>"
            f"<td>{html.escape(str(row.get('parser_count') or 0))}</td>"
            f"<td>{html.escape(', '.join(str(item) for item in row.get('parsers') or []))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>能力覆盖矩阵</h2>'
        '<table><thead><tr><th>能力</th><th>报告质量必需</th><th>解析器数</th><th>覆盖解析器</th></tr></thead>'
        f'<tbody>{"".join(rendered) if rendered else "<tr><td colspan=\"4\">暂无能力目标。</td></tr>"}</tbody></table></article>'
    )


def _parser_table(rows: list[Mapping[str, Any]]) -> str:
    rendered = []
    for row in rows:
        rendered.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('priority') or 0))}</td>"
            f"<td>{html.escape(str(row.get('name') or ''))}</td>"
            f"<td>{html.escape(str(row.get('status') or ''))}</td>"
            f"<td>{html.escape(', '.join(str(item) for item in row.get('formats') or []))}</td>"
            f"<td>{html.escape(str(row.get('business_value') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>解析器业务价值</h2>'
        '<table><thead><tr><th>优先级</th><th>解析器</th><th>状态</th><th>格式</th><th>业务价值</th></tr></thead>'
        f'<tbody>{"".join(rendered) if rendered else "<tr><td colspan=\"5\">暂无解析器。</td></tr>"}</tbody></table></article>'
    )


def _implementation_queue(rows: list[Mapping[str, Any]]) -> str:
    rendered = []
    for row in rows:
        rendered.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('parser_id') or ''))}</td>"
            f"<td>{html.escape(str(row.get('current_implementation') or ''))}</td>"
            f"<td>{html.escape(str(row.get('next_action') or ''))}</td>"
            f"<td>{html.escape(str(row.get('acceptance_check') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>实施队列与验收</h2>'
        '<table><thead><tr><th>parser_id</th><th>当前状态</th><th>下一步</th><th>验收标准</th></tr></thead>'
        f'<tbody>{"".join(rendered) if rendered else "<tr><td colspan=\"4\">暂无实施项。</td></tr>"}</tbody></table></article>'
    )


def _boundary_panel(note: str) -> str:
    return (
        '<article class="panel wide"><h2>合规边界</h2>'
        f"<p>{html.escape(note)}</p>"
        '<p class="note">附件解析只处理已合法取得的公开文件或用户授权文件；无法解析时进入缺口/复核，不臆造正文。</p>'
        "</article>"
    )


def _bar_row(label: str, value: int, maximum: int, klass: str) -> str:
    pct = 0 if maximum <= 0 else min(100, round(value / maximum * 100, 1))
    safe_class = "ready" if klass == "ready" else "partial" if klass == "partial" else "planned" if klass == "planned" else ""
    class_attr = f" {safe_class}" if safe_class else ""
    return (
        '<div class="bar">'
        f'<span class="label">{html.escape(label)}</span>'
        f'<span class="track"><span class="fill{html.escape(class_attr)}" style="width:{pct}%"></span></span>'
        f'<span class="value">{html.escape(str(value))}</span>'
        "</div>"
    )
