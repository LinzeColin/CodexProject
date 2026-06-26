from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from .credential_doctor import build_credential_doctor
from .platform_auth import platform_auth_state
from .platform_parser_validation import build_platform_parser_validation
from .readiness import CORE_PLATFORMS, build_readiness_status


P1_PLATFORMS = ["wechat", "zhihu", "weibo"]
P2_PLATFORMS = ["douyin", "kuaishou", "xiaohongshu", "toutiao"]


def build_access_readiness(
    *,
    content_conn=None,
    search_secrets_file: str | Path | None = None,
    platform_auth_file: str | Path | None = None,
    parser_file: str | Path | None = "config/platform_parsers.json",
    interpretation_source_file: str | Path | None = "config/interpretation_sources.json",
) -> dict[str, Any]:
    credential = build_credential_doctor(
        search_secrets_file=search_secrets_file,
        platform_auth_file=platform_auth_file,
    )
    readiness = build_readiness_status(
        content_conn=content_conn,
        search_secrets_file=search_secrets_file,
        platform_auth_file=platform_auth_file,
        interpretation_source_file=interpretation_source_file,
    )
    parser_validation = build_platform_parser_validation(
        parser_file=parser_file,
        search_secrets_file=search_secrets_file,
        platform_auth_file=platform_auth_file,
    )
    tiers = _tiers(credential, readiness, parser_validation, platform_auth_file)
    summary = _summary(credential, readiness, parser_validation, tiers)
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "overall_status": summary["overall_status"],
        "summary": summary,
        "tiers": tiers,
        "commands": _commands(search_secrets_file, platform_auth_file, parser_file),
        "next_actions": _next_actions(tiers, parser_validation),
        "security_boundary": (
            "本页只汇总脱敏状态和下一步命令；不展示 API key、cookie、session、账号密码、bundle 内容或完整敏感路径。"
            "在线验收仍必须遵守不绕过验证码、付费墙、访问控制和平台禁止接口。"
        ),
    }


def write_access_readiness_dashboard(
    path: str | Path,
    *,
    content_conn=None,
    search_secrets_file: str | Path | None = None,
    platform_auth_file: str | Path | None = None,
    parser_file: str | Path | None = "config/platform_parsers.json",
    interpretation_source_file: str | Path | None = "config/interpretation_sources.json",
    title: str = "全网接入 readiness",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    report = build_access_readiness(
        content_conn=content_conn,
        search_secrets_file=search_secrets_file,
        platform_auth_file=platform_auth_file,
        parser_file=parser_file,
        interpretation_source_file=interpretation_source_file,
    )
    output.write_text(render_access_readiness_dashboard(report, title=title), encoding="utf-8")
    return str(output)


def render_access_readiness_dashboard(report: Mapping[str, Any], *, title: str = "全网接入 readiness") -> str:
    summary = report.get("summary") or {}
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
    .hero p {{ margin: 0; color: var(--muted); }}
    .metrics {{ display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); border: 1px solid var(--line); background: var(--panel); margin: 14px 0; }}
    .metric {{ padding: 10px 12px; border-right: 1px solid var(--line); min-height: 70px; }}
    .metric:last-child {{ border-right: 0; }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; }}
    .metric strong {{ display: block; color: #063f4b; font-size: 22px; overflow-wrap: anywhere; }}
    .panel {{ background: var(--panel); border: 1px solid var(--line); padding: 13px 14px; margin-top: 12px; }}
    .panel h2 {{ margin: 0 0 10px; color: #063f4b; font-size: 16px; }}
    .note {{ margin: 8px 0 0; color: var(--muted); font-size: 12px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ border: 1px solid var(--line); padding: 7px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf4f7; color: #063f4b; }}
    td {{ background: var(--panel); }}
    .pass {{ color: var(--green); font-weight: 700; }}
    .warn {{ color: var(--amber); font-weight: 700; }}
    .fail {{ color: var(--red); font-weight: 700; }}
    .cmd {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; overflow-wrap: anywhere; font-size: 11px; }}
    @media (max-width: 920px) {{
      .metrics {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
      table {{ font-size: 11px; }}
    }}
    @media (max-width: 560px) {{
      .page {{ padding: 18px 12px 40px; }}
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      th, td {{ padding: 6px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <p>Full Web Access Readiness</p>
      <h1>{html.escape(title)}</h1>
      <p>生成时间：{html.escape(str(report.get("generated_at") or ""))}｜状态：{html.escape(str(report.get("overall_status") or ""))}｜只展示脱敏证据。</p>
    </section>
    <section class="metrics">
      {_metric("搜索 ready", summary.get("search_ready", 0))}
      {_metric("平台可用", summary.get("platform_available", 0))}
      {_metric("B站", summary.get("bilibili_status", ""))}
      {_metric("中文入口", summary.get("chinese_search_ready", 0))}
      {_metric("缺搜索", summary.get("missing_search_key", 0))}
      {_metric("缺授权", summary.get("missing_platform_auth", 0))}
      {_metric("P0", summary.get("p0_status", ""))}
    </section>
    {_tier_table(list(report.get("tiers") or []))}
    {_commands_panel(report.get("commands") or {})}
    {_next_actions_panel(list(report.get("next_actions") or []))}
    <article class="panel"><h2>安全与合规边界</h2><p>{html.escape(str(report.get("security_boundary") or ""))}</p></article>
  </main>
</body>
</html>
"""


def _tiers(
    credential: Mapping[str, Any],
    readiness: Mapping[str, Any],
    parser_validation: Mapping[str, Any],
    platform_auth_file: str | Path | None,
) -> list[dict[str, Any]]:
    search_ready = int(((readiness.get("search_api") or {}).get("ready_count") or 0))
    chinese_ready = int(((readiness.get("chinese_search_entries") or {}).get("configured_count") or 0))
    bilibili = platform_auth_state("bilibili", platform_auth_file)
    bilibili_collector_ready = bool(bilibili.available and bilibili.cookie_file)
    bilibili_session_only = bool(bilibili.available and bilibili.session_file and not bilibili.cookie_file)
    p1_ready = sum(1 for platform in P1_PLATFORMS if platform_auth_state(platform, platform_auth_file).available)
    p2_ready = sum(1 for platform in P2_PLATFORMS if platform_auth_state(platform, platform_auth_file).available)
    parser_summary = parser_validation.get("summary") or {}
    return [
        {
            "tier": "P0",
            "area": "搜索 API",
            "status": "pass" if search_ready >= 1 else "fail",
            "evidence": f"ready {search_ready}/3",
            "business_value": "满足每份报告至少 5 份外部公开参考的最低检索入口。",
            "next_action": "运行 search-secret-bulk-import 后执行 search-validate。",
        },
        {
            "tier": "P0",
            "area": "B站授权",
            "status": "pass" if bilibili_collector_ready else "warn" if bilibili_session_only else "fail",
            "evidence": f"{bilibili.status}; collector_ready={str(bilibili_collector_ready).lower()}",
            "business_value": "获取政策解读视频、字幕、作者和互动线索。",
            "next_action": "优先导入 B站 cookie 文件；Chrome/session 引用可先登记，但直接采集仍需 cookie 或专用验证器。",
        },
        {
            "tier": "P0",
            "area": "中文公开搜索入口",
            "status": "pass" if chinese_ready >= 3 else "warn",
            "evidence": f"ready {chinese_ready}/3",
            "business_value": "百度、搜狗、360 公开入口作为中文长尾线索，不替代 API key。",
            "next_action": "保持离线 parser 自检；遇验证码只记录缺口。",
        },
        {
            "tier": "P1",
            "area": "公众号/知乎/微博授权",
            "status": "pass" if p1_ready == len(P1_PLATFORMS) else "warn" if p1_ready else "fail",
            "evidence": f"ready {p1_ready}/{len(P1_PLATFORMS)}",
            "business_value": "补足深度文章、专家观点、官方媒体和机构解读。",
            "next_action": "导入 wechat/zhihu/weibo cookie 后执行 platform-auth-validate。",
        },
        {
            "tier": "P2",
            "area": "短视频/社媒扩展授权",
            "status": "pass" if p2_ready == len(P2_PLATFORMS) else "warn" if p2_ready else "fail",
            "evidence": f"ready {p2_ready}/{len(P2_PLATFORMS)}",
            "business_value": "扩展传播热度、评论和民生影响线索。",
            "next_action": "导入 douyin/kuaishou/xiaohongshu/toutiao cookie 后执行平台验收。",
        },
        {
            "tier": "Gate",
            "area": "平台解析器前置条件",
            "status": "pass"
            if not parser_summary.get("missing_search_key_count") and not parser_summary.get("missing_platform_auth_count")
            else "fail",
            "evidence": (
                f"missing_search_key {parser_summary.get('missing_search_key_count', 0)}, "
                f"missing_platform_auth {parser_summary.get('missing_platform_auth_count', 0)}"
            ),
            "business_value": "判断下一步是补 key、补授权，还是实现详情解析器。",
            "next_action": "运行 platform-parser-validate，并优先解决缺 key/缺授权。",
        },
    ]


def _summary(
    credential: Mapping[str, Any],
    readiness: Mapping[str, Any],
    parser_validation: Mapping[str, Any],
    tiers: list[Mapping[str, Any]],
) -> dict[str, Any]:
    search_ready = int(((readiness.get("search_api") or {}).get("ready_count") or 0))
    platform_available = int(((readiness.get("platform_auth") or {}).get("available_count") or 0))
    chinese_ready = int(((readiness.get("chinese_search_entries") or {}).get("configured_count") or 0))
    parser_summary = parser_validation.get("summary") or {}
    p0_status = str((credential.get("p0_gate") or {}).get("status") or "unknown")
    failed = sum(1 for item in tiers if item.get("status") == "fail")
    warned = sum(1 for item in tiers if item.get("status") == "warn")
    overall = "ready_for_online_validation" if p0_status in {"p0_minimum_ready", "p0_complete"} else "blocked"
    if overall != "blocked" and (failed or warned):
        overall = "partial"
    return {
        "overall_status": overall,
        "p0_status": p0_status,
        "search_ready": search_ready,
        "platform_available": platform_available,
        "bilibili_status": _bilibili_summary_status(tiers),
        "chinese_search_ready": chinese_ready,
        "missing_search_key": int(parser_summary.get("missing_search_key_count") or 0),
        "missing_platform_auth": int(parser_summary.get("missing_platform_auth_count") or 0),
        "failed_tiers": failed,
        "warning_tiers": warned,
    }


def _bilibili_summary_status(tiers: list[Mapping[str, Any]]) -> str:
    row = next((item for item in tiers if item.get("area") == "B站授权"), {})
    if row.get("status") == "pass":
        return "ready"
    if row.get("status") == "warn":
        return "session_only"
    return "missing"


def _commands(
    search_secrets_file: str | Path | None,
    platform_auth_file: str | Path | None,
    parser_file: str | Path | None,
) -> dict[str, str]:
    search_path = _path_arg(search_secrets_file or "~/.policy-intelligence/policy-search-secrets.json")
    auth_path = _path_arg(platform_auth_file or "~/.policy-intelligence/policy-platform-auth.json")
    parser_path = _path_arg(parser_file or "config/platform_parsers.json")
    return {
        "import_search_bundle": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-secret-bulk-import "
            f"--source-file /path/to/search_api_bundle.json --search-secrets-file {search_path}"
        ),
        "import_platform_bundle": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-bundle-import "
            f"--source-file /path/to/platform_auth_bundle.json --platform-auth-file {auth_path}"
        ),
        "credential_doctor": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite credential-doctor "
            f"--search-secrets-file {search_path} --platform-auth-file {auth_path}"
        ),
        "search_validate": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-validate "
            f"--search-secrets-file {search_path}"
        ),
        "platform_auth_validate_bilibili": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-validate "
            f"--platform-auth-file {auth_path} --platform bilibili --online"
        ),
        "platform_parser_validate": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-parser-validate "
            f"--parser-file {parser_path} --search-secrets-file {search_path} --platform-auth-file {auth_path}"
        ),
        "automation_readiness": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite automation-readiness "
            f"--search-secrets-file {search_path} --platform-auth-file {auth_path}"
        ),
    }


def _next_actions(tiers: list[Mapping[str, Any]], parser_validation: Mapping[str, Any]) -> list[dict[str, Any]]:
    actions = []
    for tier in tiers:
        if tier.get("status") == "pass":
            continue
        actions.append(
            {
                "priority": 95 if tier.get("tier") == "P0" else 80 if tier.get("tier") == "P1" else 70,
                "area": tier.get("area"),
                "status": tier.get("status"),
                "action": tier.get("next_action"),
            }
        )
    for action in parser_validation.get("next_actions") or []:
        if str(action.get("action")) in {"provide_search_api_key", "provide_platform_auth"}:
            continue
        actions.append(
            {
                "priority": int(action.get("priority") or 60),
                "area": action.get("label") or action.get("action"),
                "status": "warn",
                "action": action.get("action"),
            }
        )
    return sorted(actions, key=lambda item: int(item.get("priority") or 0), reverse=True)[:10]


def _tier_table(rows: list[Mapping[str, Any]]) -> str:
    body = []
    for row in rows:
        status = str(row.get("status") or "")
        body.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('tier') or ''))}</td>"
            f"<td>{html.escape(str(row.get('area') or ''))}</td>"
            f"<td class=\"{html.escape(status)}\">{html.escape(status)}</td>"
            f"<td>{html.escape(str(row.get('evidence') or ''))}</td>"
            f"<td>{html.escape(str(row.get('business_value') or ''))}</td>"
            f"<td>{html.escape(str(row.get('next_action') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel"><h2>分层接入验收</h2>'
        '<table><thead><tr><th>层级</th><th>对象</th><th>状态</th><th>证据</th><th>业务价值</th><th>下一步</th></tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></article>'
    )


def _commands_panel(commands: Mapping[str, str]) -> str:
    rows = []
    for key, command in commands.items():
        rows.append("<tr>" f"<td>{html.escape(str(key))}</td>" f"<td class=\"cmd\">{html.escape(str(command))}</td>" "</tr>")
    return (
        '<article class="panel"><h2>验收命令矩阵</h2>'
        '<table><thead><tr><th>动作</th><th>命令</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></article>'
    )


def _next_actions_panel(actions: list[Mapping[str, Any]]) -> str:
    rows = []
    for action in actions:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(action.get('priority') or ''))}</td>"
            f"<td>{html.escape(str(action.get('area') or ''))}</td>"
            f"<td>{html.escape(str(action.get('status') or ''))}</td>"
            f"<td>{html.escape(str(action.get('action') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel"><h2>下一步</h2>'
        '<table><thead><tr><th>优先级</th><th>对象</th><th>状态</th><th>动作</th></tr></thead>'
        f'<tbody>{"".join(rows) if rows else "<tr><td colspan=\"4\">暂无动作。</td></tr>"}</tbody></table></article>'
    )


def _metric(label: str, value: object) -> str:
    return (
        '<article class="metric">'
        f"<span>{html.escape(str(label))}</span>"
        f"<strong>{html.escape(str(value))}</strong>"
        "</article>"
    )


def _path_arg(path: str | Path) -> str:
    value = str(path)
    home = str(Path.home())
    if value.startswith(home):
        return "~" + value[len(home) :]
    return value
