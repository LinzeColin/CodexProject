from __future__ import annotations

import html
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from .interpretation import is_reference_item
from .platform_parser_registry import load_platform_parser_registry


SECRET_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"SESSDATA\s*=",
        r"API_KEY\s*=",
        r"api_key\s*=",
        r"sk-[A-Za-z0-9_-]{8,}",
        r"cookie\s*[:=]\s*[^,;\s]{8,}",
        r"session\s*[:=]\s*[^,;\s]{8,}",
    )
]

SEARCH_API_SAMPLE_PLATFORMS = {"bing", "google", "google_cse", "serpapi", "serpapi_google"}
PUBLIC_MEDIA_SOURCE_PLATFORMS = {"public_media_sites", "public_site_search", "public_search_html"}


def build_platform_parser_sample_acceptance(
    conn: sqlite3.Connection,
    *,
    parser_file: str | Path | None = "config/platform_parsers.json",
    limit: int = 200,
) -> dict[str, Any]:
    registry = load_platform_parser_registry(parser_file)
    rows = [_sample_row(parser, _samples_for_parser(conn, parser, limit=limit)) for parser in registry["parsers"]]
    counts = Counter(str(row.get("sample_status") or "unknown") for row in rows)
    summary = {
        "parser_count": len(rows),
        "sample_passed_count": int(counts.get("sample_passed", 0)),
        "partial_sample_count": int(counts.get("partial_sample", 0)),
        "no_sample_count": int(counts.get("no_samples", 0)),
        "secret_leak_count": sum(int(row.get("secret_leak_count") or 0) for row in rows),
        "reference_item_count": sum(int(row.get("reference_count") or 0) for row in rows),
        "sample_item_count": sum(int(row.get("sample_count") or 0) for row in rows),
    }
    return {
        "last_refreshed": registry.get("last_refreshed") or "",
        "summary": summary,
        "status_counts": dict(counts),
        "rows": sorted(rows, key=lambda item: int(item.get("priority") or 0), reverse=True),
        "next_actions": _next_actions(rows),
        "security_boundary": "本页只验收本地已入库样本；不联网、不读取账号密码、不输出 API key/cookie/session。",
    }


def write_platform_parser_sample_dashboard(
    path: str | Path,
    conn: sqlite3.Connection,
    *,
    parser_file: str | Path | None = "config/platform_parsers.json",
    limit: int = 200,
    title: str = "平台解析样本验收 dashboard",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    report = build_platform_parser_sample_acceptance(conn, parser_file=parser_file, limit=limit)
    output.write_text(render_platform_parser_sample_dashboard(report, title=title), encoding="utf-8")
    return str(output)


def render_platform_parser_sample_dashboard(
    report: Mapping[str, Any],
    *,
    title: str = "平台解析样本验收 dashboard",
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
      line-height: 1.5;
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
    .fill.sample_passed {{ background: var(--green); }}
    .fill.partial_sample {{ background: var(--amber); }}
    .fill.no_samples {{ background: var(--blue); }}
    .fill.secret_leak {{ background: var(--red); }}
    .value {{ color: #063f4b; font-weight: 700; text-align: right; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ border: 1px solid var(--line); padding: 7px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf4f7; color: #063f4b; }}
    td {{ background: var(--panel); }}
    .sample_passed {{ color: var(--green); font-weight: 700; }}
    .partial_sample {{ color: var(--amber); font-weight: 700; }}
    .no_samples {{ color: var(--blue); font-weight: 700; }}
    .secret_leak {{ color: var(--red); font-weight: 700; }}
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
      <p>Platform Parser Sample Acceptance</p>
      <h1>{html.escape(title)}</h1>
      <p>刷新日期：{html.escape(str(report.get("last_refreshed") or ""))}｜用本地已入库解读样本验收 parser 是否真正产出高价值证据。</p>
    </section>
    <section class="metrics">
      {_metric("解析器", summary.get("parser_count", 0))}
      {_metric("样本通过", summary.get("sample_passed_count", 0))}
      {_metric("样本部分通过", summary.get("partial_sample_count", 0))}
      {_metric("无样本", summary.get("no_sample_count", 0))}
      {_metric("可计入参考", summary.get("reference_item_count", 0))}
      {_metric("secret 泄漏", summary.get("secret_leak_count", 0))}
    </section>
    <section class="grid">
      {_status_panel(report.get("status_counts") or {})}
      {_next_action_panel(list(report.get("next_actions") or []))}
      {_sample_table(rows)}
      <article class="panel wide"><h2>安全边界</h2><p>{html.escape(str(report.get("security_boundary") or ""))}</p></article>
    </section>
  </main>
</body>
</html>
"""


def _samples_for_parser(conn: sqlite3.Connection, parser: Mapping[str, Any], *, limit: int) -> list[dict[str, Any]]:
    platform = str(parser.get("platform") or "")
    rows = conn.execute(
        """
        SELECT ii.*, src.platform AS source_platform, src.collector_type AS source_collector_type
        FROM interpretation_items ii
        JOIN interpretation_sources src
            ON src.interpretation_source_id = ii.interpretation_source_id
        ORDER BY ii.created_at DESC, ii.relevance_score DESC
        LIMIT ?
        """,
        (max(limit, 1),),
    ).fetchall()
    return [dict(row) for row in rows if _matches_parser_platform(dict(row), platform)]


def _matches_parser_platform(item: Mapping[str, Any], parser_platform: str) -> bool:
    item_platform = str(item.get("platform") or "")
    source_platform = str(item.get("source_platform") or "")
    if parser_platform == item_platform or parser_platform == source_platform:
        return True
    if parser_platform == "serpapi_bing_google":
        return item_platform in SEARCH_API_SAMPLE_PLATFORMS or source_platform in SEARCH_API_SAMPLE_PLATFORMS
    if parser_platform == "public_media_sites":
        return (
            source_platform in PUBLIC_MEDIA_SOURCE_PLATFORMS
            or item_platform in PUBLIC_MEDIA_SOURCE_PLATFORMS
            or "." in item_platform
        )
    return False


def _sample_row(parser: Mapping[str, Any], samples: list[dict[str, Any]]) -> dict[str, Any]:
    evidence = _evidence_counts(samples)
    reference_count = sum(1 for item in samples if is_reference_item(item))
    secret_leaks = sum(1 for item in samples if _has_secret_leak(item))
    critical = _critical_capabilities(parser, evidence)
    missing_critical = [cap for cap, passed in critical.items() if not passed]
    missing_implemented = _missing_implemented_capabilities(parser, evidence)
    if secret_leaks:
        sample_status = "secret_leak"
    elif not samples:
        sample_status = "no_samples"
    elif reference_count > 0 and not missing_critical and not missing_implemented:
        sample_status = "sample_passed"
    else:
        sample_status = "partial_sample"
    return {
        "parser_id": parser.get("parser_id"),
        "platform": parser.get("platform"),
        "name": parser.get("name"),
        "priority": parser.get("priority"),
        "parser_status": parser.get("status"),
        "sample_status": sample_status,
        "sample_count": len(samples),
        "reference_count": reference_count,
        "secret_leak_count": secret_leaks,
        "article_body_count": evidence["article_body"],
        "video_metadata_count": evidence["video_metadata"],
        "subtitle_count": evidence["subtitle_extraction"],
        "comment_count": evidence["comment_extraction"],
        "danmaku_count": evidence["danmaku_extraction"],
        "author_count": evidence["author_profile"],
        "interaction_count": evidence["interaction_metrics"],
        "failure_audit_count": evidence["failure_audit"],
        "missing_critical": missing_critical,
        "missing_implemented": missing_implemented,
        "next_action": _row_next_action(sample_status, parser, missing_critical or missing_implemented),
    }


def _evidence_counts(samples: list[Mapping[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for item in samples:
        raw = _metadata(item)
        excerpt = str(item.get("content_excerpt") or item.get("summary") or "")
        item_type = str(item.get("item_type") or "")
        if item.get("title") and item.get("url"):
            counts["public_search"] += 1
        if len(excerpt.strip()) >= 80 or raw.get("article_fetch_status") == "article_excerpt_extracted":
            counts["article_body"] += 1
        if item_type == "video" and item.get("title") and item.get("url") and (item.get("author_name") or item.get("view_count") or raw.get("detail_enriched")):
            counts["video_metadata"] += 1
        if raw.get("subtitle_excerpt"):
            counts["subtitle_extraction"] += 1
        if raw.get("comment_excerpt") or raw.get("comment_count"):
            counts["comment_extraction"] += 1
        if raw.get("danmaku_excerpt") or raw.get("danmaku"):
            counts["danmaku_extraction"] += 1
        if item.get("author_name") or item.get("author_url") or raw.get("author_profile_enriched"):
            counts["author_profile"] += 1
        if item.get("view_count") or item.get("engagement_count") or _has_interaction_metadata(raw):
            counts["interaction_metrics"] += 1
        if item.get("evidence_status") and _metadata_parses(item):
            counts["failure_audit"] += 1
        if not _has_secret_leak(item):
            counts["no_secret_logging"] += 1
    return counts


def _critical_capabilities(parser: Mapping[str, Any], evidence: Mapping[str, int]) -> dict[str, bool]:
    implemented = set(parser.get("implemented_capabilities") or [])
    critical: dict[str, bool] = {"public_search": bool(evidence.get("public_search")), "failure_audit": bool(evidence.get("failure_audit")), "no_secret_logging": True}
    if "article_body" in implemented:
        critical["article_body"] = bool(evidence.get("article_body"))
    if "video_metadata" in implemented:
        critical["video_metadata"] = bool(evidence.get("video_metadata"))
    if "author_profile" in implemented and str(parser.get("status") or "") == "ready":
        critical["author_profile"] = bool(evidence.get("author_profile"))
    return critical


def _missing_implemented_capabilities(parser: Mapping[str, Any], evidence: Mapping[str, int]) -> list[str]:
    tracked = {
        "article_body",
        "video_metadata",
        "subtitle_extraction",
        "comment_extraction",
        "danmaku_extraction",
        "author_profile",
        "interaction_metrics",
    }
    missing: list[str] = []
    for capability in parser.get("implemented_capabilities") or []:
        if capability in tracked and not evidence.get(str(capability)):
            missing.append(str(capability))
    return missing


def _row_next_action(status: str, parser: Mapping[str, Any], missing: list[str]) -> str:
    if status == "sample_passed":
        return "可计入报告质量证据；继续扩大样本覆盖。"
    if status == "secret_leak":
        return "立即停用该样本链路，清理输出并修复脱敏。"
    if status == "no_samples":
        return str(parser.get("next_action") or "先运行采集，再做样本验收。")
    if missing:
        return "补齐关键证据：" + "、".join(missing)
    return "样本有线索但不可计入参考；提高相关性、正文长度或解析稳定性。"


def _next_actions(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(str(row.get("sample_status") or "") for row in rows)
    actions: list[dict[str, Any]] = []
    if counts.get("secret_leak"):
        actions.append({"priority": 100, "label": "处理 secret 泄漏", "count": int(counts["secret_leak"])})
    if counts.get("no_samples"):
        targets = [str(row.get("platform")) for row in rows if row.get("sample_status") == "no_samples"][:6]
        actions.append({"priority": 85, "label": "补采集样本", "count": int(counts["no_samples"]), "targets": targets})
    if counts.get("partial_sample"):
        targets = [str(row.get("platform")) for row in rows if row.get("sample_status") == "partial_sample"][:6]
        actions.append({"priority": 75, "label": "修复样本质量", "count": int(counts["partial_sample"]), "targets": targets})
    if not actions:
        actions.append({"priority": 60, "label": "扩大跨平台样本", "count": int(counts.get("sample_passed", 0))})
    return actions


def _metadata(item: Mapping[str, Any]) -> dict[str, Any]:
    raw = item.get("raw_metadata")
    if isinstance(raw, Mapping):
        return dict(raw)
    raw_json = item.get("raw_metadata_json")
    if not raw_json:
        return {}
    try:
        parsed = json.loads(str(raw_json))
    except json.JSONDecodeError:
        return {}
    return dict(parsed) if isinstance(parsed, Mapping) else {}


def _metadata_parses(item: Mapping[str, Any]) -> bool:
    raw_json = item.get("raw_metadata_json")
    if not raw_json:
        return True
    try:
        json.loads(str(raw_json))
    except json.JSONDecodeError:
        return False
    return True


def _has_interaction_metadata(raw: Mapping[str, Any]) -> bool:
    keys = {"view", "views", "view_count", "play", "play_count", "like", "likes", "comment_count", "review", "danmaku", "favorites", "share", "share_count"}
    return any(raw.get(key) for key in keys)


def _has_secret_leak(item: Mapping[str, Any]) -> bool:
    probe = json.dumps(
        {
            "title": item.get("title"),
            "url": item.get("url"),
            "summary": item.get("summary"),
            "content_excerpt": item.get("content_excerpt"),
            "raw_metadata_json": item.get("raw_metadata_json"),
        },
        ensure_ascii=False,
    )
    return any(pattern.search(probe) for pattern in SECRET_PATTERNS)


def _metric(label: str, value: object) -> str:
    return (
        '<article class="metric">'
        f"<span>{html.escape(str(label))}</span>"
        f"<strong>{html.escape(str(value))}</strong>"
        "</article>"
    )


def _status_panel(values: Mapping[str, int]) -> str:
    if not values:
        return '<article class="panel"><h2>样本状态</h2><p class="note">暂无数据。</p></article>'
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
    return f'<article class="panel"><h2>样本状态</h2><section class="bars">{"".join(rows)}</section></article>'


def _next_action_panel(actions: list[Mapping[str, Any]]) -> str:
    rows = []
    for action in actions:
        targets = ", ".join(str(item) for item in action.get("targets") or [])
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(action.get('priority') or ''))}</td>"
            f"<td>{html.escape(str(action.get('label') or ''))}</td>"
            f"<td>{html.escape(targets or str(action.get('count') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel"><h2>下一步动作</h2>'
        '<table><thead><tr><th>优先级</th><th>动作</th><th>目标</th></tr></thead>'
        f'<tbody>{"".join(rows) if rows else "<tr><td colspan=\"3\">暂无动作。</td></tr>"}</tbody></table></article>'
    )


def _sample_table(rows: list[Mapping[str, Any]]) -> str:
    body = []
    for row in rows:
        body.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('priority') or 0))}</td>"
            f"<td>{html.escape(str(row.get('platform') or ''))}</td>"
            f"<td>{html.escape(str(row.get('name') or ''))}</td>"
            f"<td class=\"{html.escape(str(row.get('sample_status') or ''))}\">{html.escape(str(row.get('sample_status') or ''))}</td>"
            f"<td>{html.escape(str(row.get('sample_count') or 0))}</td>"
            f"<td>{html.escape(str(row.get('reference_count') or 0))}</td>"
            f"<td>{html.escape(str(row.get('article_body_count') or 0))}</td>"
            f"<td>{html.escape(str(row.get('video_metadata_count') or 0))}</td>"
            f"<td>{html.escape(str(row.get('author_count') or 0))}</td>"
            f"<td>{html.escape(str(row.get('interaction_count') or 0))}</td>"
            f"<td>{html.escape(str(row.get('next_action') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>解析样本验收明细</h2>'
        '<table><thead><tr><th>优先级</th><th>平台</th><th>解析器</th><th>样本状态</th><th>样本</th><th>可参考</th><th>正文</th><th>视频</th><th>作者</th><th>互动</th><th>下一步</th></tr></thead>'
        f'<tbody>{"".join(body) if body else "<tr><td colspan=\"11\">暂无样本。</td></tr>"}</tbody></table>'
        '<p class="note">sample_passed 表示该 parser 已有可计入报告质量门槛的本地样本；partial_sample 表示只有线索或关键证据不足。</p></article>'
    )
