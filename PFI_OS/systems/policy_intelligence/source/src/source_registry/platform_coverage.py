from __future__ import annotations

import html
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from .readiness import CHINESE_SEARCH_ENTRIES, CORE_PLATFORMS, build_readiness_status


SEARCH_PROVIDERS = ["serpapi", "bing", "google"]

IMPLEMENTED_BY_COLLECTOR = {
    "bilibili_api": [
        "public_video_search",
        "video_detail",
        "author_profile",
        "public_subtitle",
        "public_comments",
        "public_danmaku",
    ],
    "search_api_serpapi": ["search_api_results", "public_article_extraction"],
    "search_api_bing": ["search_api_results", "public_article_extraction"],
    "search_api_google": ["search_api_results", "public_article_extraction"],
    "public_site_search": ["site_search_results", "public_article_extraction"],
    "public_search_html": ["public_search_results", "public_article_extraction"],
    "authorized_public_search": [
        "authorized_public_search",
        "public_article_extraction",
        "author_profile",
        "interaction_metrics",
        "failure_audit",
    ],
    "local_related_documents": ["local_related_public_documents", "context_reference_linking"],
    "search_landing": ["search_landing"],
}

COMPLIANCE_BOUNDARY = (
    "不绕过验证码、付费墙、登录访问控制或平台明确禁止的接口；"
    "仅使用公开可访问信息、已授权 cookie/session/API，且不在报告中展示 secret。"
)


def build_platform_coverage(
    *,
    content_conn=None,
    search_secrets_file: str | Path | None = None,
    platform_auth_file: str | Path | None = None,
    interpretation_source_file: str | Path | None = "config/interpretation_sources.json",
) -> dict[str, Any]:
    readiness = build_readiness_status(
        content_conn=content_conn,
        search_secrets_file=search_secrets_file,
        platform_auth_file=platform_auth_file,
        interpretation_source_file=interpretation_source_file,
    )
    sources = _interpretation_sources(interpretation_source_file)
    by_platform: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for source in sources:
        by_platform[str(source.get("platform") or "unknown")].append(source)
    rows = []
    rows.extend(_search_rows(readiness, by_platform))
    rows.extend(_chinese_search_rows(readiness, by_platform))
    rows.extend(_core_platform_rows(readiness, by_platform))
    rows.extend(_other_source_rows(rows, by_platform))
    summary = _coverage_summary(rows, readiness)
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "overall_status": readiness.get("overall_status"),
        "summary": summary,
        "rows": rows,
        "next_actions": readiness.get("next_actions") or [],
        "compliance_boundary": COMPLIANCE_BOUNDARY,
    }


def write_platform_coverage_dashboard(
    path: str | Path,
    *,
    content_conn=None,
    search_secrets_file: str | Path | None = None,
    platform_auth_file: str | Path | None = None,
    interpretation_source_file: str | Path | None = "config/interpretation_sources.json",
    title: str = "平台覆盖矩阵",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    coverage = build_platform_coverage(
        content_conn=content_conn,
        search_secrets_file=search_secrets_file,
        platform_auth_file=platform_auth_file,
        interpretation_source_file=interpretation_source_file,
    )
    output.write_text(render_platform_coverage_dashboard(coverage, title=title), encoding="utf-8")
    return str(output)


def render_platform_coverage_dashboard(
    coverage: Mapping[str, Any],
    *,
    title: str = "平台覆盖矩阵",
) -> str:
    summary = coverage.get("summary") or {}
    rows = list(coverage.get("rows") or [])
    status_counts = Counter(str(row.get("status") or "unknown") for row in rows)
    type_counts = Counter(str(row.get("source_group") or "unknown") for row in rows)
    generated_at = str(coverage.get("generated_at") or "")
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
    .bar {{ display: grid; grid-template-columns: minmax(112px, 170px) 1fr 44px; gap: 8px; align-items: center; font-size: 12px; }}
    .track {{ height: 10px; border: 1px solid #d5e2e6; background: #e7eef1; }}
    .fill {{ display: block; height: 100%; background: var(--teal); }}
    .fill.ready {{ background: var(--green); }}
    .fill.partial {{ background: var(--blue); }}
    .fill.blocked {{ background: var(--red); }}
    .fill.lead_only, .fill.needs_parser {{ background: var(--amber); }}
    .value {{ font-weight: 700; text-align: right; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ border: 1px solid var(--line); padding: 7px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf4f7; color: #063f4b; }}
    td {{ background: var(--panel); }}
    .pill {{ display: inline-block; border: 1px solid var(--line); background: var(--soft); padding: 2px 7px; margin: 2px 3px 2px 0; }}
    .ready {{ color: var(--green); font-weight: 700; }}
    .partial {{ color: var(--blue); font-weight: 700; }}
    .blocked {{ color: var(--red); font-weight: 700; }}
    .lead_only, .needs_parser {{ color: var(--amber); font-weight: 700; }}
    .cmd {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; overflow-wrap: anywhere; font-size: 11px; }}
    @media (max-width: 920px) {{
      .metrics {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
      .panel {{ grid-column: 1 / -1; }}
    }}
    @media (max-width: 620px) {{
      .page {{ padding: 18px 12px 40px; }}
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .bar {{ grid-template-columns: 96px 1fr 36px; }}
      table {{ font-size: 11px; }}
      th, td {{ padding: 6px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <p>Full-Web Coverage Readiness</p>
      <h1>{html.escape(title)}</h1>
      <p>生成时间：{html.escape(generated_at)}｜该页面只展示配置状态，不展示 API key、cookie、账号密码或本地 secret 路径。</p>
    </section>
    <section class="metrics">
      {_metric("覆盖对象", summary.get("total", 0))}
      {_metric("可计入/可抓取", summary.get("ready", 0))}
      {_metric("部分可用", summary.get("partial", 0))}
      {_metric("线索入口", summary.get("lead_only", 0))}
      {_metric("待解析器", summary.get("needs_parser", 0))}
      {_metric("阻塞", summary.get("blocked", 0))}
    </section>
    <section class="grid">
      {_bar_panel("覆盖状态", [(k, v, k) for k, v in status_counts.most_common()])}
      {_bar_panel("来源类型", [(k, v, "") for k, v in type_counts.most_common()])}
      {_next_action_panel(coverage.get("next_actions") or [])}
      {_compliance_panel(str(coverage.get("compliance_boundary") or ""))}
      {_coverage_table(rows)}
      {_command_panel()}
    </section>
  </main>
</body>
</html>
"""


def _search_rows(readiness: Mapping[str, Any], by_platform: Mapping[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    providers = {item["provider"]: item for item in (readiness.get("search_api") or {}).get("providers", [])}
    rows = []
    provider_to_platform = {"serpapi": "serpapi_google", "bing": "bing", "google": "google_cse"}
    for provider in SEARCH_PROVIDERS:
        source_platform = provider_to_platform[provider]
        source_items = by_platform.get(source_platform, [])
        ready = bool((providers.get(provider) or {}).get("ready"))
        rows.append(
            {
                "platform": provider,
                "display_name": _display_name(provider),
                "source_group": "search_api",
                "configured": ready,
                "available": ready,
                "implemented_capabilities": _capabilities_for_sources(source_items),
                "allowed_capabilities": ["search_api_results", "public_article_extraction"],
                "status": "ready" if ready else "blocked",
                "blocker": "" if ready else "missing_search_api_key",
                "next_action": "补充本地搜索 API key 文件；不要在聊天中发送 key。",
                "compliance": "只调用公开搜索 API；不保存 key 明文到报告。",
            }
        )
    return rows


def _chinese_search_rows(readiness: Mapping[str, Any], by_platform: Mapping[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    entries = (readiness.get("chinese_search_entries") or {}).get("entries") or {}
    platform_aliases = {"360": "so.com"}
    rows = []
    for entry in CHINESE_SEARCH_ENTRIES:
        platform = platform_aliases.get(entry, entry)
        source_items = by_platform.get(platform, [])
        enabled = bool(entries.get(entry))
        rows.append(
            {
                "platform": entry,
                "display_name": _display_name(entry),
                "source_group": "chinese_search_entry",
                "configured": enabled,
                "available": enabled,
                "implemented_capabilities": _capabilities_for_sources(source_items),
                "allowed_capabilities": ["public_search_results", "public_article_extraction", "search_landing"],
                "status": "lead_only" if enabled else "blocked",
                "blocker": "" if enabled else "source_entry_disabled",
                "next_action": "复核公开结果质量；后续可接合规 API 或站点级解析器。",
                "compliance": "只抓取可公开访问的结果页正文；不绕过验证码或反爬；入口本身不计入有效参考。",
            }
        )
    return rows


def _core_platform_rows(readiness: Mapping[str, Any], by_platform: Mapping[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    auth_by_platform = {
        item["platform"]: item for item in (readiness.get("platform_auth") or {}).get("platforms", [])
    }
    rows = []
    for platform in CORE_PLATFORMS:
        auth = auth_by_platform.get(platform) or {}
        source_items = by_platform.get(platform, [])
        implemented = _capabilities_for_sources(source_items)
        allowed = list(auth.get("allowed_capabilities") or [])
        available = bool(auth.get("available"))
        configured = bool(auth.get("configured"))
        status = _core_status(platform, implemented, available)
        rows.append(
            {
                "platform": platform,
                "display_name": _display_name(platform),
                "source_group": "external_platform",
                "configured": configured,
                "available": available,
                "implemented_capabilities": implemented,
                "allowed_capabilities": allowed,
                "status": status,
                "blocker": _core_blocker(status, auth),
                "next_action": _core_next_action(platform, status),
                "compliance": "仅使用公开页面、平台开放 API 或你授权的本地 cookie/session；遇到验证码、付费墙或访问控制即记录缺口。",
            }
        )
    return rows


def _other_source_rows(
    existing_rows: list[Mapping[str, Any]],
    by_platform: Mapping[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    known = {str(row.get("platform")) for row in existing_rows}
    rows = []
    for platform, sources in sorted(by_platform.items()):
        if platform in known or platform in {"serpapi_google", "google_cse", "so.com"}:
            continue
        caps = _capabilities_for_sources(sources)
        rows.append(
            {
                "platform": platform,
                "display_name": platform,
                "source_group": "public_site_or_media",
                "configured": True,
                "available": True,
                "implemented_capabilities": caps,
                "allowed_capabilities": caps,
                "status": "partial" if "public_article_extraction" in caps else "lead_only",
                "blocker": "" if "public_article_extraction" in caps else "landing_only",
                "next_action": "补站点级解析规则，提高公开文章正文抽取稳定性。",
                "compliance": "只抓取公开网页；登录、验证码、付费墙或受限内容不计入有效参考。",
            }
        )
    return rows


def _core_status(platform: str, implemented: list[str], auth_available: bool) -> str:
    if platform == "bilibili" and "public_video_search" in implemented:
        return "partial" if auth_available else "partial"
    if "authorized_public_search" in implemented and not auth_available and "public_search_results" not in implemented:
        return "blocked"
    if "public_article_extraction" in implemented or "authorized_public_search" in implemented:
        return "partial"
    if "search_landing" in implemented and auth_available:
        return "needs_parser"
    if "search_landing" in implemented:
        return "blocked"
    return "blocked"


def _core_blocker(status: str, auth: Mapping[str, Any]) -> str:
    if status == "partial":
        return "detail_gaps_remain" if auth.get("available") else "auth_optional_for_deeper_data"
    if status == "needs_parser":
        return "platform_parser_pending"
    if not auth.get("available"):
        return str(auth.get("status") or "auth_not_configured")
    return "unknown"


def _core_next_action(platform: str, status: str) -> str:
    if status == "partial":
        if platform == "bilibili":
            return "优先补 B 站 cookie 后验证字幕、评论、弹幕和作者页稳定性。"
        return "补平台授权后继续验证详情解析。"
    if status == "needs_parser":
        return "授权已可用时，接入平台详情解析器。"
    return "提供本地授权文件或开放 API 凭据；不要在聊天中发送账号密码。"


def _capabilities_for_sources(sources: list[Mapping[str, Any]]) -> list[str]:
    caps: list[str] = []
    for source in sources:
        collector = str(source.get("collector_type") or "search_landing")
        for cap in IMPLEMENTED_BY_COLLECTOR.get(collector, ["search_landing"]):
            if cap not in caps:
                caps.append(cap)
    return caps


def _interpretation_sources(path: str | Path | None) -> list[dict[str, Any]]:
    if not path:
        return []
    file_path = Path(path)
    if not file_path.exists():
        return []
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    sources = payload.get("sources", payload if isinstance(payload, list) else [])
    return [dict(source) for source in sources if isinstance(source, Mapping) and source.get("enabled", True)]


def _coverage_summary(rows: list[Mapping[str, Any]], readiness: Mapping[str, Any]) -> dict[str, Any]:
    counts = Counter(str(row.get("status") or "unknown") for row in rows)
    return {
        "total": len(rows),
        "ready": int(counts.get("ready", 0)),
        "partial": int(counts.get("partial", 0)),
        "lead_only": int(counts.get("lead_only", 0)),
        "needs_parser": int(counts.get("needs_parser", 0)),
        "blocked": int(counts.get("blocked", 0)),
        "search_api_ready": int((readiness.get("search_api") or {}).get("ready_count") or 0),
        "platform_auth_available": int((readiness.get("platform_auth") or {}).get("available_count") or 0),
        "pending_gaps": int((readiness.get("external_reference_gaps") or {}).get("pending_count") or 0),
    }


def _metric(label: str, value: object) -> str:
    return (
        '<article class="metric">'
        f"<span>{html.escape(str(label))}</span>"
        f"<strong>{html.escape(str(value))}</strong>"
        "</article>"
    )


def _bar_panel(title: str, rows: list[tuple[str, int, str]]) -> str:
    if not rows:
        return f'<article class="panel"><h2>{html.escape(title)}</h2><p class="note">暂无数据。</p></article>'
    maximum = max([value for _, value, _ in rows] + [1])
    return (
        f'<article class="panel"><h2>{html.escape(title)}</h2><section class="bars">'
        f'{"".join(_bar_row(label, value, maximum, klass) for label, value, klass in rows)}'
        "</section></article>"
    )


def _bar_row(label: str, value: int, maximum: int, klass: str) -> str:
    pct = 0 if maximum <= 0 else min(100, round(value / maximum * 100, 1))
    class_attr = f" {klass}" if klass else ""
    return (
        '<div class="bar">'
        f'<span>{html.escape(str(label))}</span>'
        f'<span class="track"><span class="fill{html.escape(class_attr)}" style="width:{pct}%"></span></span>'
        f'<span class="value">{html.escape(str(value))}</span>'
        "</div>"
    )


def _next_action_panel(actions: list[Mapping[str, Any]]) -> str:
    if not actions:
        return '<article class="panel"><h2>下一步动作</h2><p class="note">暂无动作。</p></article>'
    rows = []
    for action in actions[:8]:
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


def _compliance_panel(text: str) -> str:
    return (
        '<article class="panel"><h2>合规边界</h2>'
        f'<p>{html.escape(text)}</p>'
        '<p class="note">授权文件只作为本地可用性状态；系统不输出 cookie 内容和 secret 路径。</p>'
        "</article>"
    )


def _coverage_table(rows: list[Mapping[str, Any]]) -> str:
    body = []
    for row in rows:
        body.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('display_name') or row.get('platform') or ''))}</td>"
            f"<td>{html.escape(str(row.get('source_group') or ''))}</td>"
            f"<td class=\"{html.escape(str(row.get('status') or ''))}\">{html.escape(str(row.get('status') or ''))}</td>"
            f"<td>{_chips(row.get('implemented_capabilities') or [])}</td>"
            f"<td>{_chips(row.get('allowed_capabilities') or [])}</td>"
            f"<td>{html.escape(str(row.get('blocker') or ''))}</td>"
            f"<td>{html.escape(str(row.get('next_action') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>平台覆盖明细</h2>'
        '<table><thead><tr><th>平台</th><th>类型</th><th>状态</th><th>已实现</th><th>授权能力</th><th>阻塞</th><th>下一步</th></tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></article>'
    )


def _command_panel() -> str:
    commands = [
        "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite setup-config",
        "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-coverage --json",
        "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite readiness --json",
    ]
    return (
        '<article class="panel wide"><h2>验收命令</h2>'
        + "".join(f'<p class="cmd">{html.escape(command)}</p>' for command in commands)
        + '<p class="note">先生成模板，补本地 key/auth 文件，再用 readiness 和 platform-coverage 验证。</p></article>'
    )


def _chips(values: list[Any]) -> str:
    if not values:
        return '<span class="pill">未接入</span>'
    return "".join(f'<span class="pill">{html.escape(str(value))}</span>' for value in values)


def _display_name(platform: str) -> str:
    labels = {
        "bilibili": "B站",
        "douyin": "抖音",
        "kuaishou": "快手",
        "weibo": "微博",
        "zhihu": "知乎",
        "wechat": "微信公众号",
        "xiaohongshu": "小红书",
        "toutiao": "今日头条",
        "serpapi": "SerpAPI",
        "bing": "Bing",
        "google": "Google CSE",
        "baidu": "百度",
        "sogou": "搜狗",
        "360": "360",
    }
    return labels.get(platform, platform)
