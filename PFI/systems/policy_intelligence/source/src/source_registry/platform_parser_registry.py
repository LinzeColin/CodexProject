from __future__ import annotations

import html
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping


DEFAULT_PLATFORM_PARSER_FILE = "config/platform_parsers.json"


def load_platform_parser_registry(path: str | Path | None = None) -> dict[str, Any]:
    registry_path = Path(path or DEFAULT_PLATFORM_PARSER_FILE)
    if not registry_path.exists():
        return {"last_refreshed": "", "source_note": "platform parser config missing", "parsers": [], "capability_targets": []}
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("platform parser config must be a JSON object")
    parsers = payload.get("parsers") or []
    targets = payload.get("capability_targets") or []
    return {
        "last_refreshed": str(payload.get("last_refreshed") or ""),
        "source_note": str(payload.get("source_note") or ""),
        "parsers": [dict(item) for item in parsers if isinstance(item, Mapping)],
        "capability_targets": [dict(item) for item in targets if isinstance(item, Mapping)],
    }


def build_platform_parser_status(path: str | Path | None = None) -> dict[str, Any]:
    registry = load_platform_parser_registry(path)
    parsers = registry["parsers"]
    targets = registry["capability_targets"]
    status_counts = Counter(str(parser.get("status") or "unknown") for parser in parsers)
    platform_counts = Counter(str(parser.get("platform") or "unknown") for parser in parsers)
    capability_rows = _capability_rows(parsers, targets)
    summary = {
        "parser_count": len(parsers),
        "ready_count": int(status_counts.get("ready", 0)),
        "partial_count": int(status_counts.get("partial", 0)),
        "planned_count": int(status_counts.get("planned", 0)),
        "platform_count": len(platform_counts),
        "required_capability_count": sum(1 for target in targets if target.get("required_for_full_web")),
        "acceptance_check_count": sum(1 for parser in parsers if parser.get("acceptance_check")),
    }
    return {
        **registry,
        "summary": summary,
        "status_counts": dict(status_counts),
        "platform_counts": dict(platform_counts),
        "capability_rows": capability_rows,
        "parser_queue": sorted(parsers, key=lambda item: int(item.get("priority") or 0), reverse=True),
        "platform_rows": _platform_rows(parsers),
    }


def write_platform_parser_dashboard(
    path: str | Path,
    *,
    parser_file: str | Path | None = None,
    title: str = "平台解析器能力 dashboard",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    status = build_platform_parser_status(parser_file)
    output.write_text(render_platform_parser_dashboard(status, title=title), encoding="utf-8")
    return str(output)


def render_platform_parser_dashboard(
    status: Mapping[str, Any],
    *,
    title: str = "平台解析器能力 dashboard",
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
      <p>Platform Parser Capability Registry</p>
      <h1>{html.escape(title)}</h1>
      <p>刷新日期：{html.escape(str(status.get("last_refreshed") or ""))}｜只展示平台解析能力、业务价值和验收标准，不展示 API key、cookie、账号密码或本地 secret 路径。</p>
    </section>
    <section class="metrics">
      {_metric("解析器", summary.get("parser_count", 0))}
      {_metric("平台", summary.get("platform_count", 0))}
      {_metric("ready", summary.get("ready_count", 0))}
      {_metric("partial", summary.get("partial_count", 0))}
      {_metric("planned", summary.get("planned_count", 0))}
      {_metric("验收标准", summary.get("acceptance_check_count", 0))}
    </section>
    <section class="grid">
      {_counter_panel("落地状态", status.get("status_counts") or {})}
      {_counter_panel("平台覆盖", status.get("platform_counts") or {}, limit=8)}
      {_capability_panel(list(status.get("capability_rows") or []))}
      {_platform_table(list(status.get("platform_rows") or []))}
      {_parser_table(list(status.get("parser_queue") or []))}
      {_boundary_panel(str(status.get("source_note") or ""))}
    </section>
  </main>
</body>
</html>
"""


def _capability_rows(parsers: list[Mapping[str, Any]], targets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    parser_by_capability: dict[str, list[str]] = {}
    for parser in parsers:
        for tag in parser.get("implemented_capabilities") or []:
            parser_by_capability.setdefault(str(tag), []).append(str(parser.get("name") or ""))
    rows = []
    for target in targets:
        capability = str(target.get("capability") or "")
        names = parser_by_capability.get(capability, [])
        rows.append(
            {
                "capability": capability,
                "label": str(target.get("label") or capability),
                "required": bool(target.get("required_for_full_web")),
                "parser_count": len(names),
                "parsers": names,
            }
        )
    return sorted(rows, key=lambda item: (not item["required"], -int(item["parser_count"]), item["label"]))


def _platform_rows(parsers: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for parser in parsers:
        grouped[str(parser.get("platform") or "unknown")].append(parser)
    rows = []
    for platform, items in grouped.items():
        capabilities = sorted({str(cap) for item in items for cap in item.get("implemented_capabilities") or []})
        statuses = Counter(str(item.get("status") or "unknown") for item in items)
        rows.append(
            {
                "platform": platform,
                "parser_count": len(items),
                "status_summary": ", ".join(f"{key}:{value}" for key, value in sorted(statuses.items())),
                "capabilities": capabilities,
                "next_action": str(max(items, key=lambda item: int(item.get("priority") or 0)).get("next_action") or ""),
            }
        )
    return sorted(rows, key=lambda item: str(item["platform"]))


def _metric(label: str, value: object) -> str:
    return (
        '<article class="metric">'
        f"<span>{html.escape(str(label))}</span>"
        f"<strong>{html.escape(str(value))}</strong>"
        "</article>"
    )


def _counter_panel(title: str, values: Mapping[str, int], *, limit: int | None = None) -> str:
    rows = [(str(label), int(count)) for label, count in values.items()]
    if limit:
        rows = rows[:limit]
    if not rows:
        return f'<article class="panel"><h2>{html.escape(title)}</h2><p class="note">暂无数据。</p></article>'
    maximum = max([count for _, count in rows] + [1])
    return (
        f'<article class="panel"><h2>{html.escape(title)}</h2><section class="bars">'
        f'{"".join(_bar_row(label, count, maximum, label) for label, count in sorted(rows))}'
        "</section></article>"
    )


def _capability_panel(rows: list[Mapping[str, Any]]) -> str:
    body = []
    for row in rows:
        body.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('label') or ''))}</td>"
            f"<td>{'是' if row.get('required') else '否'}</td>"
            f"<td>{html.escape(str(row.get('parser_count') or 0))}</td>"
            f"<td>{html.escape(', '.join(str(item) for item in row.get('parsers') or []))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>能力覆盖矩阵</h2>'
        '<table><thead><tr><th>能力</th><th>全网目标必需</th><th>解析器数</th><th>覆盖解析器</th></tr></thead>'
        f'<tbody>{"".join(body) if body else "<tr><td colspan=\"4\">暂无能力目标。</td></tr>"}</tbody></table></article>'
    )


def _platform_table(rows: list[Mapping[str, Any]]) -> str:
    body = []
    for row in rows:
        body.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('platform') or ''))}</td>"
            f"<td>{html.escape(str(row.get('parser_count') or 0))}</td>"
            f"<td>{html.escape(str(row.get('status_summary') or ''))}</td>"
            f"<td>{_chips(row.get('capabilities') or [])}</td>"
            f"<td>{html.escape(str(row.get('next_action') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>平台能力摘要</h2>'
        '<table><thead><tr><th>平台</th><th>解析器数</th><th>状态</th><th>能力</th><th>下一步</th></tr></thead>'
        f'<tbody>{"".join(body) if body else "<tr><td colspan=\"5\">暂无平台解析器。</td></tr>"}</tbody></table></article>'
    )


def _parser_table(rows: list[Mapping[str, Any]]) -> str:
    body = []
    for row in rows:
        body.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('priority') or 0))}</td>"
            f"<td>{html.escape(str(row.get('platform') or ''))}</td>"
            f"<td>{html.escape(str(row.get('name') or ''))}</td>"
            f"<td>{html.escape(str(row.get('status') or ''))}</td>"
            f"<td>{'是' if row.get('auth_required') else '否'}</td>"
            f"<td>{html.escape(str(row.get('business_value') or ''))}</td>"
            f"<td>{html.escape(str(row.get('acceptance_check') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>解析器实施队列</h2>'
        '<table><thead><tr><th>优先级</th><th>平台</th><th>解析器</th><th>状态</th><th>需授权</th><th>业务价值</th><th>验收标准</th></tr></thead>'
        f'<tbody>{"".join(body) if body else "<tr><td colspan=\"7\">暂无解析器。</td></tr>"}</tbody></table></article>'
    )


def _boundary_panel(note: str) -> str:
    return (
        '<article class="panel wide"><h2>合规边界</h2>'
        f"<p>{html.escape(note)}</p>"
        '<p class="note">登录、验证码、付费墙、会员内容或平台禁止访问的接口只进入缺口队列；不做绕过。</p>'
        "</article>"
    )


def _bar_row(label: str, value: int, maximum: int, klass: str) -> str:
    pct = 0 if maximum <= 0 else min(100, round(value / maximum * 100, 1))
    safe_class = "ready" if klass == "ready" else "partial" if klass == "partial" else "planned" if klass == "planned" else ""
    class_attr = f" {safe_class}" if safe_class else ""
    return (
        '<div class="bar">'
        f'<span>{html.escape(str(label))}</span>'
        f'<span class="track"><span class="fill{html.escape(class_attr)}" style="width:{pct}%"></span></span>'
        f'<span class="value">{html.escape(str(value))}</span>'
        "</div>"
    )


def _chips(values: list[Any]) -> str:
    if not values:
        return '<span class="pill">未接入</span>'
    return "".join(f'<span class="pill">{html.escape(str(value))}</span>' for value in values)
