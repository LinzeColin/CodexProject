from __future__ import annotations

import html
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from .platform_auth import platform_auth_state
from .platform_parser_registry import load_platform_parser_registry
from .web_search import search_provider_status


SEARCH_API_PLATFORM = "serpapi_bing_google"


def build_platform_parser_validation(
    *,
    parser_file: str | Path | None = "config/platform_parsers.json",
    search_secrets_file: str | Path | None = None,
    platform_auth_file: str | Path | None = None,
) -> dict[str, Any]:
    registry = load_platform_parser_registry(parser_file)
    search_status = search_provider_status(search_secrets_file)
    ready_search = [str(item.get("provider") or "") for item in search_status if item.get("ready")]
    rows = [
        _validation_row(
            parser,
            ready_search=ready_search,
            platform_auth_file=platform_auth_file,
        )
        for parser in registry["parsers"]
    ]
    counts = Counter(str(row.get("validation_status") or "unknown") for row in rows)
    summary = {
        "parser_count": len(rows),
        "current_ready_count": int(counts.get("current_ready", 0)),
        "current_partial_count": int(counts.get("current_partial", 0)),
        "missing_search_key_count": int(counts.get("missing_search_key", 0)),
        "missing_platform_auth_count": int(counts.get("missing_platform_auth", 0)),
        "implementation_pending_count": int(counts.get("implementation_pending", 0))
        + int(counts.get("implementation_pending_auth_ready", 0)),
        "ready_search_provider_count": len(ready_search),
        "platform_auth_available_count": sum(1 for row in rows if row.get("auth_available")),
    }
    return {
        "last_refreshed": registry.get("last_refreshed") or "",
        "summary": summary,
        "status_counts": dict(counts),
        "rows": sorted(rows, key=lambda item: int(item.get("priority") or 0), reverse=True),
        "next_actions": _next_actions(rows, ready_search),
        "security_boundary": (
            "本验收只读取脱敏配置状态；不展示 API key、cookie、session、账号密码或完整本地路径。"
            "在线平台访问仍必须通过显式验证命令执行，且不绕过验证码、付费墙或访问控制。"
        ),
    }


def write_platform_parser_validation_dashboard(
    path: str | Path,
    *,
    parser_file: str | Path | None = "config/platform_parsers.json",
    search_secrets_file: str | Path | None = None,
    platform_auth_file: str | Path | None = None,
    title: str = "平台解析器验收 dashboard",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    report = build_platform_parser_validation(
        parser_file=parser_file,
        search_secrets_file=search_secrets_file,
        platform_auth_file=platform_auth_file,
    )
    output.write_text(render_platform_parser_validation_dashboard(report, title=title), encoding="utf-8")
    return str(output)


def render_platform_parser_validation_dashboard(
    report: Mapping[str, Any],
    *,
    title: str = "平台解析器验收 dashboard",
) -> str:
    summary = report.get("summary") or {}
    rows = list(report.get("rows") or [])
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
    .bar {{ display: grid; grid-template-columns: minmax(150px, 230px) 1fr 48px; gap: 8px; align-items: center; font-size: 12px; }}
    .track {{ height: 10px; border: 1px solid #d5e2e6; background: #e7eef1; }}
    .fill {{ display: block; height: 100%; background: var(--teal); }}
    .fill.current_ready {{ background: var(--green); }}
    .fill.current_partial, .fill.implementation_pending_auth_ready {{ background: var(--amber); }}
    .fill.missing_search_key, .fill.missing_platform_auth {{ background: var(--red); }}
    .fill.implementation_pending {{ background: var(--blue); }}
    .value {{ color: #063f4b; font-weight: 700; text-align: right; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ border: 1px solid var(--line); padding: 7px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf4f7; color: #063f4b; }}
    td {{ background: var(--panel); }}
    .current_ready {{ color: var(--green); font-weight: 700; }}
    .current_partial, .implementation_pending_auth_ready {{ color: var(--amber); font-weight: 700; }}
    .missing_search_key, .missing_platform_auth {{ color: var(--red); font-weight: 700; }}
    .implementation_pending {{ color: var(--blue); font-weight: 700; }}
    .pill {{ display: inline-block; border: 1px solid var(--line); background: var(--soft); padding: 2px 7px; margin: 2px 3px 2px 0; }}
    @media (max-width: 980px) {{
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
      <p>Platform Parser Acceptance Validation</p>
      <h1>{html.escape(title)}</h1>
      <p>刷新日期：{html.escape(str(report.get("last_refreshed") or ""))}｜合并 parser 台账、搜索 key、本地授权状态；不展示 secret。</p>
    </section>
    <section class="metrics">
      {_metric("解析器", summary.get("parser_count", 0))}
      {_metric("当前 ready", summary.get("current_ready_count", 0))}
      {_metric("当前 partial", summary.get("current_partial_count", 0))}
      {_metric("缺搜索 key", summary.get("missing_search_key_count", 0))}
      {_metric("缺平台授权", summary.get("missing_platform_auth_count", 0))}
      {_metric("待实现", summary.get("implementation_pending_count", 0))}
    </section>
    <section class="grid">
      {_status_panel(report.get("status_counts") or {})}
      {_next_action_panel(list(report.get("next_actions") or []))}
      {_validation_table(rows)}
      <article class="panel wide"><h2>安全与合规边界</h2><p>{html.escape(str(report.get("security_boundary") or ""))}</p></article>
    </section>
  </main>
</body>
</html>
"""


def _validation_row(
    parser: Mapping[str, Any],
    *,
    ready_search: list[str],
    platform_auth_file: str | Path | None,
) -> dict[str, Any]:
    platform = str(parser.get("platform") or "")
    parser_status = str(parser.get("status") or "")
    auth_required = bool(parser.get("auth_required"))
    auth_available = False
    auth_status = ""
    prereq = "none"
    if platform == SEARCH_API_PLATFORM:
        prereq = "search_api"
        if not ready_search:
            validation_status = "missing_search_key"
        elif parser_status == "ready":
            validation_status = "current_ready"
        elif parser_status == "partial":
            validation_status = "current_partial"
        else:
            validation_status = "implementation_pending_auth_ready"
    elif auth_required:
        prereq = "platform_auth"
        state = platform_auth_state(platform, platform_auth_file)
        auth_available = bool(state.available)
        auth_status = state.status
        if parser_status == "planned":
            validation_status = "implementation_pending_auth_ready" if auth_available else "missing_platform_auth"
        elif not auth_available:
            validation_status = "missing_platform_auth"
        elif parser_status == "ready":
            validation_status = "current_ready"
        else:
            validation_status = "current_partial"
    elif parser_status == "ready":
        validation_status = "current_ready"
    elif parser_status == "partial":
        validation_status = "current_partial"
    else:
        validation_status = "implementation_pending"
    return {
        "parser_id": parser.get("parser_id"),
        "platform": platform,
        "name": parser.get("name"),
        "priority": parser.get("priority"),
        "parser_status": parser_status,
        "auth_required": auth_required,
        "auth_available": auth_available,
        "auth_status": auth_status,
        "prerequisite": prereq,
        "validation_status": validation_status,
        "ready_search_providers": ready_search if platform == SEARCH_API_PLATFORM else [],
        "business_value": parser.get("business_value") or "",
        "next_action": _validation_next_action(parser, validation_status),
        "acceptance_check": parser.get("acceptance_check") or "",
    }


def _validation_next_action(parser: Mapping[str, Any], status: str) -> str:
    if status == "missing_search_key":
        return "补至少 1 个搜索 API key，并运行 search-validate 在线验收。"
    if status == "missing_platform_auth":
        return f"补 {parser.get('platform')} 本地 cookie/session 文件，再运行 platform-auth-validate。"
    if status == "implementation_pending_auth_ready":
        return str(parser.get("next_action") or "授权已具备后接入平台详情解析器。")
    if status == "implementation_pending":
        return str(parser.get("next_action") or "实现解析器并补 fixture。")
    if status == "current_partial":
        return str(parser.get("next_action") or "补充缺失字段并扩大验收样本。")
    return "可进入在线样本验收；失败时记录缺口，不降低合规边界。"


def _next_actions(rows: list[Mapping[str, Any]], ready_search: list[str]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if not ready_search and any(row["validation_status"] == "missing_search_key" for row in rows):
        actions.append({"priority": 95, "action": "provide_search_api_key", "label": "补搜索 API key", "count": 1})
    missing_auth = sorted({str(row["platform"]) for row in rows if row["validation_status"] == "missing_platform_auth"})
    if missing_auth:
        actions.append(
            {
                "priority": 90,
                "action": "provide_platform_auth",
                "label": "补平台授权文件",
                "targets": missing_auth,
                "count": len(missing_auth),
            }
        )
    pending = [row for row in rows if str(row.get("validation_status")) in {"implementation_pending", "implementation_pending_auth_ready"}]
    if pending:
        actions.append(
            {
                "priority": 80,
                "action": "implement_platform_parser",
                "label": "实现平台详情解析器",
                "targets": [str(row.get("platform")) for row in pending[:6]],
                "count": len(pending),
            }
        )
    partial = [row for row in rows if str(row.get("validation_status")) == "current_partial"]
    if partial:
        actions.append(
            {
                "priority": 70,
                "action": "expand_parser_acceptance",
                "label": "扩大 partial parser 验收",
                "targets": [str(row.get("platform")) for row in partial[:6]],
                "count": len(partial),
            }
        )
    return actions


def _metric(label: str, value: object) -> str:
    return (
        '<article class="metric">'
        f"<span>{html.escape(str(label))}</span>"
        f"<strong>{html.escape(str(value))}</strong>"
        "</article>"
    )


def _status_panel(values: Mapping[str, int]) -> str:
    if not values:
        return '<article class="panel"><h2>验收状态</h2><p class="note">暂无数据。</p></article>'
    maximum = max([int(value) for value in values.values()] + [1])
    rows = []
    for label, value in sorted(values.items()):
        pct = min(100, round(int(value) / maximum * 100, 1))
        rows.append(
            '<div class="bar">'
            f'<span>{html.escape(str(label))}</span>'
            f'<span class="track"><span class="fill {html.escape(str(label))}" style="width:{pct}%"></span></span>'
            f'<span class="value">{html.escape(str(value))}</span>'
            "</div>"
        )
    return f'<article class="panel"><h2>验收状态</h2><section class="bars">{"".join(rows)}</section></article>'


def _next_action_panel(actions: list[Mapping[str, Any]]) -> str:
    if not actions:
        return '<article class="panel"><h2>下一步动作</h2><p class="note">暂无动作。</p></article>'
    rows = []
    for action in actions:
        targets = ", ".join(str(item) for item in action.get("targets") or [])
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(action.get('priority') or ''))}</td>"
            f"<td>{html.escape(str(action.get('label') or action.get('action') or ''))}</td>"
            f"<td>{html.escape(targets or str(action.get('count') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel"><h2>下一步动作</h2>'
        '<table><thead><tr><th>优先级</th><th>动作</th><th>目标</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></article>'
    )


def _validation_table(rows: list[Mapping[str, Any]]) -> str:
    body = []
    for row in rows:
        body.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('priority') or 0))}</td>"
            f"<td>{html.escape(str(row.get('platform') or ''))}</td>"
            f"<td>{html.escape(str(row.get('name') or ''))}</td>"
            f"<td>{html.escape(str(row.get('parser_status') or ''))}</td>"
            f"<td class=\"{html.escape(str(row.get('validation_status') or ''))}\">{html.escape(str(row.get('validation_status') or ''))}</td>"
            f"<td>{'是' if row.get('auth_required') else '否'}</td>"
            f"<td>{html.escape(str(row.get('next_action') or ''))}</td>"
            f"<td>{html.escape(str(row.get('acceptance_check') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>解析器验收明细</h2>'
        '<table><thead><tr><th>优先级</th><th>平台</th><th>解析器</th><th>parser 状态</th><th>验收状态</th><th>需授权</th><th>下一步</th><th>验收标准</th></tr></thead>'
        f'<tbody>{"".join(body) if body else "<tr><td colspan=\"8\">暂无解析器。</td></tr>"}</tbody></table></article>'
    )
