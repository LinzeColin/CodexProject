from __future__ import annotations

import html
import json
import ssl
import urllib.error
import urllib.request
from urllib import robotparser
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from .db import list_sources


DEFAULT_CRAWL_POLICY_FILE = "config/crawl_policies.json"


def load_crawl_policy_registry(path: str | Path | None = None) -> dict[str, Any]:
    policy_path = Path(path or DEFAULT_CRAWL_POLICY_FILE)
    if not policy_path.exists():
        return _fallback_registry()
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("crawl policy config must be a JSON object")
    default_policy = dict(payload.get("default_policy") or _fallback_registry()["default_policy"])
    profiles = {
        str(key): dict(value)
        for key, value in (payload.get("profiles") or {}).items()
        if isinstance(value, Mapping)
    }
    return {
        "last_refreshed": str(payload.get("last_refreshed") or ""),
        "operator_contact": str(payload.get("operator_contact") or ""),
        "default_user_agent": str(payload.get("default_user_agent") or ""),
        "default_policy": default_policy,
        "profiles": profiles,
    }


def build_crawl_policy_status(
    conn: sqlite3.Connection,
    *,
    policy_file: str | Path | None = None,
    enabled_only: bool = True,
    limit: int = 300,
    check_robots: bool = False,
    robots_timeout: int = 8,
    allow_insecure_tls: bool = False,
) -> dict[str, Any]:
    registry = load_crawl_policy_registry(policy_file)
    sources = list_sources(conn, crawl_enabled=True if enabled_only else None)
    user_agent = str(registry.get("default_user_agent") or "PolicyIntelligenceBot/0.1")
    rows = [
        _source_policy_row(
            source,
            registry,
            check_robots=check_robots,
            robots_timeout=robots_timeout,
            allow_insecure_tls=allow_insecure_tls,
            user_agent=user_agent,
        )
        for source in sources[:limit]
    ]
    profile_counts = Counter(str(row.get("profile") or "unknown") for row in rows)
    status_counts = Counter(str(row.get("policy_status") or "unknown") for row in rows)
    blocked_counts = Counter(str(row.get("blocked_handling") or "unknown") for row in rows)
    robots_counts = Counter(str(row.get("robots_check_status") or "not_checked") for row in rows)
    summary = {
        "source_count": len(rows),
        "crawl_enabled_only": bool(enabled_only),
        "policy_ready": int(status_counts.get("ready", 0)),
        "needs_review": int(status_counts.get("needs_review", 0)),
        "respect_robots_count": sum(1 for row in rows if row.get("respect_robots")),
        "rate_limited_count": sum(1 for row in rows if float(row.get("min_delay_seconds") or 0) > 0),
        "long_retention_count": sum(1 for row in rows if int(row.get("snapshot_retention_days") or 0) >= 365),
        "robots_checked_count": sum(1 for row in rows if row.get("robots_check_status") != "not_checked"),
        "robots_allowed_count": sum(1 for row in rows if row.get("robots_allowed") is True),
        "robots_disallowed_count": sum(1 for row in rows if row.get("robots_allowed") is False),
    }
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "last_refreshed": registry.get("last_refreshed") or "",
        "operator_contact": _contact_label(str(registry.get("operator_contact") or "")),
        "default_user_agent": _user_agent_label(str(registry.get("default_user_agent") or "")),
        "summary": summary,
        "robots_check_options": {
            "check_robots": bool(check_robots),
            "allow_insecure_tls": bool(allow_insecure_tls),
            "robots_timeout": int(robots_timeout),
        },
        "profile_counts": dict(profile_counts),
        "status_counts": dict(status_counts),
        "blocked_handling_counts": dict(blocked_counts),
        "robots_check_counts": dict(robots_counts),
        "rows": rows,
        "compliance_boundary": (
            "抓取前必须具备 policy profile、robots/nofollow 策略、限速、重试、超时、快照保留和受限页面处理规则；"
            "不绕过验证码、付费墙、登录访问控制或平台明确禁止的接口。"
        ),
    }


def write_crawl_policy_dashboard(
    path: str | Path,
    conn: sqlite3.Connection,
    *,
    policy_file: str | Path | None = None,
    enabled_only: bool = True,
    limit: int = 300,
    check_robots: bool = False,
    robots_timeout: int = 8,
    allow_insecure_tls: bool = False,
    title: str = "抓取策略与合规边界",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    status = build_crawl_policy_status(
        conn,
        policy_file=policy_file,
        enabled_only=enabled_only,
        limit=limit,
        check_robots=check_robots,
        robots_timeout=robots_timeout,
        allow_insecure_tls=allow_insecure_tls,
    )
    output.write_text(render_crawl_policy_dashboard(status, title=title), encoding="utf-8")
    return str(output)


def render_crawl_policy_dashboard(
    status: Mapping[str, Any],
    *,
    title: str = "抓取策略与合规边界",
) -> str:
    summary = status.get("summary") or {}
    rows = list(status.get("rows") or [])
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
    .metric strong {{ display: block; color: #063f4b; font-size: 22px; overflow-wrap: anywhere; }}
    .grid {{ display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 12px; }}
    .panel {{ grid-column: span 6; background: var(--panel); border: 1px solid var(--line); padding: 13px 14px; }}
    .panel.wide {{ grid-column: 1 / -1; }}
    .panel h2 {{ margin: 0 0 10px; color: #063f4b; font-size: 16px; }}
    .note {{ margin: 8px 0 0; color: var(--muted); font-size: 12px; }}
    .bars {{ display: grid; gap: 8px; }}
    .bar {{ display: grid; grid-template-columns: minmax(130px, 210px) 1fr 44px; gap: 8px; align-items: center; font-size: 12px; }}
    .track {{ height: 10px; border: 1px solid #d5e2e6; background: #e7eef1; }}
    .fill {{ display: block; height: 100%; background: var(--teal); }}
    .fill.ready {{ background: var(--green); }}
    .fill.needs_review {{ background: var(--amber); }}
    .value {{ font-weight: 700; text-align: right; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ border: 1px solid var(--line); padding: 7px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf4f7; color: #063f4b; }}
    td {{ background: var(--panel); }}
    .ready {{ color: var(--green); font-weight: 700; }}
    .needs_review {{ color: var(--amber); font-weight: 700; }}
    .cmd {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; overflow-wrap: anywhere; font-size: 11px; }}
    @media (max-width: 920px) {{
      .metrics {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
      .panel {{ grid-column: 1 / -1; }}
    }}
    @media (max-width: 620px) {{
      .page {{ padding: 18px 12px 40px; }}
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .bar {{ grid-template-columns: 105px 1fr 38px; }}
      table {{ font-size: 11px; }}
      th, td {{ padding: 6px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <p>Crawl Policy Registry</p>
      <h1>{html.escape(title)}</h1>
      <p>生成时间：{html.escape(str(status.get("generated_at") or ""))}｜联系人：{html.escape(str(status.get("operator_contact") or ""))}｜不展示 secret。</p>
    </section>
    <section class="metrics">
      {_metric("来源数", summary.get("source_count", 0))}
      {_metric("策略 ready", summary.get("policy_ready", 0))}
      {_metric("需复核", summary.get("needs_review", 0))}
      {_metric("尊重 robots", summary.get("respect_robots_count", 0))}
      {_metric("限速来源", summary.get("rate_limited_count", 0))}
      {_metric("Robots 通过", summary.get("robots_allowed_count", 0))}
    </section>
    <section class="grid">
      {_bar_panel("Profile 分布", status.get("profile_counts") or {})}
      {_bar_panel("受限页面处理", status.get("blocked_handling_counts") or {})}
      {_bar_panel("Robots 在线检查", status.get("robots_check_counts") or {})}
      {_policy_note_panel(status)}
      {_policy_table(rows)}
    </section>
  </main>
</body>
</html>
"""


def _source_policy_row(
    source: Mapping[str, Any],
    registry: Mapping[str, Any],
    *,
    check_robots: bool = False,
    robots_timeout: int = 8,
    allow_insecure_tls: bool = False,
    user_agent: str = "PolicyIntelligenceBot/0.1",
) -> dict[str, Any]:
    profile_name, policy = _match_policy(source, registry)
    domain = str(source.get("canonical_domain") or _domain_from_url(str(source.get("official_url") or "")))
    target_url = str(source.get("official_url") or "")
    respect_robots = bool(policy.get("respect_robots", True))
    min_delay = float(policy.get("min_delay_seconds") or 0)
    max_retries = int(policy.get("max_retries") or 0)
    timeout = int(policy.get("timeout_seconds") or 0)
    retention = int(policy.get("snapshot_retention_days") or 0)
    status = "ready" if domain and respect_robots and min_delay > 0 and timeout > 0 else "needs_review"
    robots_url = f"https://{domain}/robots.txt" if domain else ""
    row = {
        "source_id": source.get("source_id") or "",
        "name": source.get("name") or "",
        "domain": domain,
        "target_url": target_url,
        "source_type": source.get("source_type") or "",
        "administrative_level": source.get("administrative_level") or "",
        "crawl_priority": source.get("crawl_priority") or "",
        "profile": profile_name,
        "policy_status": status,
        "respect_robots": respect_robots,
        "respect_nofollow": bool(policy.get("respect_nofollow", True)),
        "robots_url": robots_url,
        "min_delay_seconds": min_delay,
        "max_retries": max_retries,
        "timeout_seconds": timeout,
        "snapshot_retention_days": retention,
        "allowed_content_types": list(policy.get("allowed_content_types") or []),
        "blocked_handling": policy.get("blocked_handling") or "record_gap_only",
        "compliance": policy.get("compliance") or "",
        "robots_check_status": "not_checked",
        "robots_allowed": None,
        "robots_error": "",
    }
    if check_robots and respect_robots and robots_url:
        row.update(
            _check_robots(
                robots_url,
                target_url or f"https://{domain}/",
                user_agent,
                robots_timeout,
                allow_insecure_tls=allow_insecure_tls,
            )
        )
    return row


def _check_robots(
    robots_url: str,
    target_url: str,
    user_agent: str,
    timeout: int,
    *,
    allow_insecure_tls: bool = False,
) -> dict[str, Any]:
    try:
        request = urllib.request.Request(robots_url, headers={"User-Agent": user_agent})
        kwargs: dict[str, Any] = {"timeout": max(1, int(timeout))}
        if allow_insecure_tls:
            kwargs["context"] = ssl._create_unverified_context()
        with urllib.request.urlopen(request, **kwargs) as response:
            status_code = int(getattr(response, "status", 200) or 200)
            body = response.read(512_000).decode("utf-8", errors="replace")
        if status_code >= 400:
            return {
                "robots_check_status": "robots_missing" if status_code == 404 else "fetch_failed",
                "robots_allowed": True if status_code == 404 else None,
                "robots_error": f"http_status:{status_code}",
            }
        parser = robotparser.RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(body.splitlines())
        allowed = bool(parser.can_fetch(user_agent, target_url))
        return {
            "robots_check_status": "allowed" if allowed else "disallowed",
            "robots_allowed": allowed,
            "robots_error": "",
        }
    except urllib.error.HTTPError as exc:
        status = int(getattr(exc, "code", 0) or 0)
        return {
            "robots_check_status": "robots_missing" if status == 404 else "fetch_failed",
            "robots_allowed": True if status == 404 else None,
            "robots_error": f"http_status:{status}",
        }
    except Exception as exc:
        return {
            "robots_check_status": "fetch_failed",
            "robots_allowed": None,
            "robots_error": _error_label(exc),
        }


def _error_label(exc: Exception) -> str:
    if isinstance(exc, urllib.error.URLError):
        reason = getattr(exc, "reason", None)
        if isinstance(reason, ssl.SSLCertVerificationError):
            return "ssl_cert_verification_failed"
        if reason is not None:
            return type(reason).__name__
    return type(exc).__name__


def _match_policy(source: Mapping[str, Any], registry: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    default_policy = dict(registry.get("default_policy") or {})
    source_type = str(source.get("source_type") or "")
    domain = str(source.get("canonical_domain") or _domain_from_url(str(source.get("official_url") or "")))
    for name, profile in (registry.get("profiles") or {}).items():
        source_types = {str(item) for item in profile.get("match_source_types") or []}
        domains = {str(item) for item in profile.get("match_domains") or []}
        if source_type in source_types or _domain_matches(domain, domains):
            merged = {**default_policy, **dict(profile), "profile": str(name)}
            return str(name), merged
    return str(default_policy.get("profile") or "default_public"), default_policy


def _domain_matches(domain: str, candidates: set[str]) -> bool:
    return any(domain == candidate or domain.endswith(f".{candidate}") for candidate in candidates)


def _domain_from_url(url: str) -> str:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    return parsed.netloc.lower().split(":")[0]


def _metric(label: str, value: object) -> str:
    return (
        '<article class="metric">'
        f"<span>{html.escape(str(label))}</span>"
        f"<strong>{html.escape(str(value))}</strong>"
        "</article>"
    )


def _bar_panel(title: str, counts: Mapping[str, int]) -> str:
    rows = sorted(counts.items(), key=lambda item: int(item[1]), reverse=True)
    if not rows:
        return f'<article class="panel"><h2>{html.escape(title)}</h2><p class="note">暂无数据。</p></article>'
    maximum = max([int(value) for _, value in rows] + [1])
    bars = "".join(_bar(str(label), int(value), maximum, str(label)) for label, value in rows)
    return f'<article class="panel"><h2>{html.escape(title)}</h2><section class="bars">{bars}</section></article>'


def _policy_note_panel(status: Mapping[str, Any]) -> str:
    return (
        '<article class="panel wide"><h2>全局抓取边界</h2>'
        f'<p>{html.escape(str(status.get("compliance_boundary") or ""))}</p>'
        f'<p class="note">User-Agent：{html.escape(str(status.get("default_user_agent") or ""))}；Robots 检查选项：{html.escape(json.dumps(status.get("robots_check_options") or {}, ensure_ascii=False))}</p>'
        "</article>"
    )


def _policy_table(rows: list[Mapping[str, Any]]) -> str:
    rendered = []
    for row in rows[:80]:
        rendered.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('crawl_priority') or ''))}</td>"
            f"<td>{html.escape(str(row.get('name') or ''))}</td>"
            f"<td>{html.escape(str(row.get('domain') or ''))}</td>"
            f"<td>{html.escape(str(row.get('profile') or ''))}</td>"
            f"<td class=\"{html.escape(str(row.get('policy_status') or ''))}\">{html.escape(str(row.get('policy_status') or ''))}</td>"
            f"<td>{html.escape('是' if row.get('respect_robots') else '否')}</td>"
            f"<td>{html.escape(str(row.get('min_delay_seconds') or 0))}s</td>"
            f"<td>{html.escape(str(row.get('max_retries') or 0))}</td>"
            f"<td>{html.escape(str(row.get('snapshot_retention_days') or 0))}d</td>"
            f"<td>{html.escape(str(row.get('blocked_handling') or ''))}</td>"
            f"<td>{html.escape(_robots_label(row))}</td>"
            f"<td class=\"cmd\">{html.escape(str(row.get('robots_url') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>来源抓取策略明细</h2>'
        '<table><thead><tr><th>优先级</th><th>来源</th><th>域名</th><th>Profile</th><th>状态</th><th>Robots</th><th>限速</th><th>重试</th><th>快照</th><th>受限处理</th><th>在线结果</th><th>robots_url</th></tr></thead>'
        f'<tbody>{"".join(rendered) if rendered else "<tr><td colspan=\"12\">暂无来源。</td></tr>"}</tbody></table>'
        '<p class="note">默认是离线抓取准入策略；显式加 --check-robots 后，会联网读取 robots.txt 并检查当前 User-Agent 是否可抓取来源首页。</p></article>'
    )


def _robots_label(row: Mapping[str, Any]) -> str:
    status = str(row.get("robots_check_status") or "not_checked")
    allowed = row.get("robots_allowed")
    if status == "not_checked":
        return "未检查"
    if allowed is True:
        return f"{status} / 允许"
    if allowed is False:
        return f"{status} / 禁止"
    error = str(row.get("robots_error") or "")
    return f"{status}{(' / ' + error) if error else ''}"


def _bar(label: str, value: int, maximum: int, klass: str = "") -> str:
    pct = 0 if maximum <= 0 else min(100, round(value / maximum * 100, 1))
    class_attr = f" {klass}" if klass in {"ready", "needs_review"} else ""
    return (
        '<div class="bar">'
        f'<span>{html.escape(label)}</span>'
        f'<span class="track"><span class="fill{html.escape(class_attr)}" style="width:{pct}%"></span></span>'
        f'<span class="value">{html.escape(str(value))}</span>'
        "</div>"
    )


def _contact_label(contact: str) -> str:
    if not contact:
        return "未配置"
    if "@" in contact and contact.endswith(".invalid"):
        return "本地占位联系人"
    return contact


def _user_agent_label(user_agent: str) -> str:
    if not user_agent:
        return "未配置"
    return user_agent.replace(str(Path.home()), "~")


def _fallback_registry() -> dict[str, Any]:
    return {
        "last_refreshed": "",
        "operator_contact": "",
        "default_user_agent": "PolicyIntelligenceBot/0.1",
        "default_policy": {
            "profile": "default_public",
            "respect_robots": True,
            "respect_nofollow": True,
            "min_delay_seconds": 1.0,
            "max_retries": 2,
            "timeout_seconds": 20,
            "snapshot_retention_days": 365,
            "allowed_content_types": ["text/html", "application/pdf"],
            "blocked_handling": "record_gap_only",
            "compliance": "只抓取公开或授权来源。",
        },
        "profiles": {},
    }
