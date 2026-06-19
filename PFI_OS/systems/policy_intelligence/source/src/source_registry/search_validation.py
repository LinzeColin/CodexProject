from __future__ import annotations

import html
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import quote, urlparse

from . import interpretation
from .web_search import SearchResult, collect_search_results, search_provider_status


SearchCollector = Callable[..., tuple[list[SearchResult], str]]


def build_search_validation(
    *,
    search_secrets_file: str | Path | None = None,
    query: str = "中国 政策 解读",
    timeout: int = 10,
    retries: int = 0,
    allow_insecure_tls: bool = False,
    online: bool = True,
    collector: SearchCollector = collect_search_results,
) -> dict[str, Any]:
    config = search_provider_status(search_secrets_file)
    providers = []
    for item in config:
        provider = str(item.get("provider") or "")
        row = {
            "provider": provider,
            "configured": bool(item.get("ready")),
            "key_present": bool(item.get("key_present")),
            "engine_present": bool(item.get("engine_present")),
            "online_checked": False,
            "status": "missing_secret" if not item.get("ready") else "configured_not_checked",
            "result_count": 0,
            "sample_domain": "",
            "error_class": "",
        }
        if online and item.get("ready"):
            results, status = collector(
                provider=provider,
                query=query,
                max_results=1,
                timeout=timeout,
                allow_insecure_tls=allow_insecure_tls,
                secrets_file=search_secrets_file,
                retries=retries,
            )
            row["online_checked"] = True
            row["status"] = _validation_status(status, results)
            row["result_count"] = len(results)
            row["sample_domain"] = _sample_domain(results)
            row["error_class"] = _error_class(status)
        providers.append(row)
    public_entrances = _public_search_entrance_validation(query)
    summary = {
        "configured_count": sum(1 for item in providers if item["configured"]),
        "online_checked_count": sum(1 for item in providers if item["online_checked"]),
        "passed_count": sum(1 for item in providers if item["status"] == "passed"),
        "failed_count": sum(1 for item in providers if item["status"] in {"failed", "no_results"}),
        "missing_count": sum(1 for item in providers if item["status"] == "missing_secret"),
        "public_entrance_count": len(public_entrances),
        "public_entrance_passed_count": sum(1 for item in public_entrances if item["status"] == "parser_ready"),
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "mode": "online" if online else "offline",
        "summary": summary,
        "providers": providers,
        "public_entrances": public_entrances,
        "next_actions": _next_actions(providers, online),
        "security_boundary": "验证过程不输出 API key；在线模式会消耗少量搜索 API 配额。",
    }


def write_search_validation_dashboard(
    path: str | Path,
    *,
    search_secrets_file: str | Path | None = None,
    query: str = "中国 政策 解读",
    timeout: int = 10,
    retries: int = 0,
    allow_insecure_tls: bool = False,
    online: bool = True,
    title: str = "搜索 API 连通性验证",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    report = build_search_validation(
        search_secrets_file=search_secrets_file,
        query=query,
        timeout=timeout,
        retries=retries,
        allow_insecure_tls=allow_insecure_tls,
        online=online,
    )
    output.write_text(render_search_validation_dashboard(report, title=title), encoding="utf-8")
    return str(output)


def render_search_validation_dashboard(
    report: Mapping[str, Any],
    *,
    title: str = "搜索 API 连通性验证",
) -> str:
    summary = report.get("summary") or {}
    providers = list(report.get("providers") or [])
    public_entrances = list(report.get("public_entrances") or [])
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
    .page {{ max-width: 1240px; margin: 0 auto; padding: 24px 20px 52px; }}
    .hero {{ background: var(--panel); border-top: 5px solid var(--teal); border-bottom: 1px solid var(--line); padding: 18px 0 16px; }}
    .hero h1 {{ margin: 2px 0 8px; color: #063f4b; font-size: 28px; line-height: 1.22; }}
    .hero p {{ margin: 0; color: var(--muted); }}
    .metrics {{ display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); border: 1px solid var(--line); background: var(--panel); margin: 14px 0; }}
    .metric {{ padding: 10px 12px; border-right: 1px solid var(--line); min-height: 70px; }}
    .metric:last-child {{ border-right: 0; }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; }}
    .metric strong {{ display: block; color: #063f4b; font-size: 22px; }}
    .panel {{ background: var(--panel); border: 1px solid var(--line); padding: 13px 14px; margin-top: 12px; }}
    .panel h2 {{ margin: 0 0 10px; color: #063f4b; font-size: 16px; }}
    .note {{ margin: 8px 0 0; color: var(--muted); font-size: 12px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ border: 1px solid var(--line); padding: 7px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf4f7; color: #063f4b; }}
    td {{ background: var(--panel); }}
    .passed, .parser_ready {{ color: var(--green); font-weight: 700; }}
    .configured_not_checked, .no_results {{ color: var(--amber); font-weight: 700; }}
    .missing_secret, .failed, .parser_failed {{ color: var(--red); font-weight: 700; }}
    .pill {{ display: inline-block; border: 1px solid var(--line); background: var(--soft); padding: 2px 7px; margin: 2px 3px 2px 0; }}
    @media (max-width: 760px) {{
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      table {{ font-size: 11px; }}
      th, td {{ padding: 6px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <p>Search API Connectivity Validation</p>
      <h1>{html.escape(title)}</h1>
      <p>生成时间：{html.escape(str(report.get("generated_at") or ""))}｜模式：{html.escape(str(report.get("mode") or ""))}｜查询：{html.escape(str(report.get("query") or ""))}｜不展示 API key。</p>
    </section>
    <section class="metrics">
      {_metric("已配置", summary.get("configured_count", 0))}
      {_metric("已在线验证", summary.get("online_checked_count", 0))}
      {_metric("通过", summary.get("passed_count", 0))}
      {_metric("失败", summary.get("failed_count", 0))}
      {_metric("缺失", summary.get("missing_count", 0))}
      {_metric("中文入口解析", f"{summary.get('public_entrance_passed_count', 0)}/{summary.get('public_entrance_count', 0)}")}
    </section>
    {_provider_panel(providers)}
    {_public_entrance_panel(public_entrances)}
    {_next_action_panel(report.get("next_actions") or [])}
    <article class="panel"><h2>安全边界</h2><p>{html.escape(str(report.get("security_boundary") or ""))}</p></article>
  </main>
</body>
</html>
"""


def _validation_status(status: str, results: list[SearchResult]) -> str:
    if status == "ok" and results:
        return "passed"
    if status == "ok":
        return "no_results"
    if status.startswith("missing_"):
        return "missing_secret"
    return "failed"


def _error_class(status: str) -> str:
    if status.startswith("request_failed:"):
        parts = status.split(":")
        return parts[-1] if parts else "request_failed"
    if status.startswith("unsupported_provider"):
        return "unsupported_provider"
    if status.startswith("missing_"):
        return status
    return ""


def _sample_domain(results: list[SearchResult]) -> str:
    if not results:
        return ""
    host = urlparse(results[0].url).netloc
    return host.lower()


def _next_actions(providers: list[Mapping[str, Any]], online: bool) -> list[dict[str, Any]]:
    actions = []
    if any(item["status"] == "missing_secret" for item in providers):
        actions.append({"priority": 95, "action": "fill_search_keys", "label": "补齐缺失搜索 API key / Google CSE ID"})
    if not online and any(item["configured"] for item in providers):
        actions.append({"priority": 90, "action": "run_online_validation", "label": "运行在线连通性验证，确认 key 可用"})
    if any(item["status"] == "failed" for item in providers):
        actions.append({"priority": 85, "action": "inspect_provider_error", "label": "检查 provider 权限、配额、网络或 API 版本"})
    if any(item["status"] == "no_results" for item in providers):
        actions.append({"priority": 70, "action": "adjust_validation_query", "label": "调整验证查询词或检查搜索引擎配置范围"})
    return actions


def _public_search_entrance_validation(query: str) -> list[dict[str, Any]]:
    rows = []
    for spec in _public_search_entrance_specs():
        search_url = spec["search_url"].format(query=quote(query), raw_query=query)
        links = interpretation._public_search_result_links(spec["sample_html"], search_url, query)
        sample_domain = _sample_domain_from_links(links)
        rows.append(
            {
                "provider": spec["provider"],
                "configured": True,
                "online_checked": False,
                "status": "parser_ready" if sample_domain else "parser_failed",
                "result_count": len(links),
                "sample_domain": sample_domain,
                "error_class": "" if sample_domain else "offline_parser_no_result",
                "boundary": "公开搜索 HTML 解析自检；不联网、不绕过验证码、不计入有效参考。",
            }
        )
    return rows


def _public_search_entrance_specs() -> list[dict[str, str]]:
    return [
        {
            "provider": "baidu_public_html",
            "search_url": "https://www.baidu.com/s?wd={query}",
            "sample_html": """
            <html><body>
              <a href="/s?wd=政策解读">百度搜索自身</a>
              <a href="/link?url=opaque" data-url="https://research.example.cn/ai/policy-analysis.html">人工智能政策解读：产业影响分析</a>
            </body></html>
            """,
        },
        {
            "provider": "sogou_public_html",
            "search_url": "https://www.sogou.com/web?query={query}",
            "sample_html": """
            <html><body>
              <a href="/web?query=政策解读">搜狗搜索自身</a>
              <a href="/link?url=https%3A%2F%2Fthinktank.example.cn%2Fchip-policy.html">半导体政策解读：投资与产业链影响</a>
            </body></html>
            """,
        },
        {
            "provider": "so360_public_html",
            "search_url": "https://www.so.com/s?q={query}",
            "sample_html": """
            <html><body>
              <a href="/s?q=政策解读">360 搜索自身</a>
              <a href="/link?u=https%3A%2F%2Fmedia.example.cn%2Frobot-policy.html">机器人政策解读：应用场景与企业机会</a>
            </body></html>
            """,
        },
    ]


def _sample_domain_from_links(links: list[Mapping[str, str]]) -> str:
    if not links:
        return ""
    return urlparse(str(links[0].get("url") or "")).netloc.lower()


def _provider_panel(providers: list[Mapping[str, Any]]) -> str:
    rows = []
    for provider in providers:
        status = str(provider.get("status") or "")
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(provider.get('provider') or ''))}</td>"
            f'<td class="{html.escape(status)}">{html.escape(status)}</td>'
            f"<td>{html.escape('yes' if provider.get('key_present') else 'no')}</td>"
            f"<td>{html.escape('yes' if provider.get('engine_present') else 'no')}</td>"
            f"<td>{html.escape('yes' if provider.get('online_checked') else 'no')}</td>"
            f"<td>{html.escape(str(provider.get('result_count') or 0))}</td>"
            f"<td>{html.escape(str(provider.get('sample_domain') or ''))}</td>"
            f"<td>{html.escape(str(provider.get('error_class') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel"><h2>Provider 验证明细</h2>'
        '<table><thead><tr><th>Provider</th><th>状态</th><th>key</th><th>engine</th><th>在线</th><th>结果数</th><th>样例域名</th><th>错误类</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table>'
        '<p class="note">样例域名来自公开搜索结果；不会保存或显示 key。</p></article>'
    )


def _public_entrance_panel(entrances: list[Mapping[str, Any]]) -> str:
    rows = []
    for item in entrances:
        status = str(item.get("status") or "")
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('provider') or ''))}</td>"
            f'<td class="{html.escape(status)}">{html.escape(status)}</td>'
            f"<td>{html.escape('yes' if item.get('configured') else 'no')}</td>"
            f"<td>{html.escape('yes' if item.get('online_checked') else 'no')}</td>"
            f"<td>{html.escape(str(item.get('result_count') or 0))}</td>"
            f"<td>{html.escape(str(item.get('sample_domain') or ''))}</td>"
            f"<td>{html.escape(str(item.get('error_class') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel"><h2>中文公开入口解析自检</h2>'
        '<table><thead><tr><th>入口</th><th>状态</th><th>配置</th><th>在线</th><th>样本结果数</th><th>样例域名</th><th>错误类</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table>'
        '<p class="note">覆盖百度、搜狗、360 的公开 HTML 结果解析；该自检不联网，只证明基础解析器可用。</p></article>'
    )


def _next_action_panel(actions: list[Mapping[str, Any]]) -> str:
    rows = []
    for action in actions:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(action.get('priority') or ''))}</td>"
            f"<td>{html.escape(str(action.get('action') or ''))}</td>"
            f"<td>{html.escape(str(action.get('label') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel"><h2>下一步动作</h2>'
        '<table><thead><tr><th>优先级</th><th>动作</th><th>说明</th></tr></thead>'
        f'<tbody>{"".join(rows) if rows else "<tr><td colspan=\"3\">暂无动作。</td></tr>"}</tbody></table></article>'
    )


def _metric(label: str, value: object) -> str:
    return (
        '<article class="metric">'
        f"<span>{html.escape(str(label))}</span>"
        f"<strong>{html.escape(str(value))}</strong>"
        "</article>"
    )
