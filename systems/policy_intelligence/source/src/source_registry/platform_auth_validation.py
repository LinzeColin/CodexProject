from __future__ import annotations

import html
import json
import ssl
import time
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.request import Request, urlopen

from .platform_auth import platform_auth_state
from .readiness import CORE_PLATFORMS


BILIBILI_NAV_URL = "https://api.bilibili.com/x/web-interface/nav"
PLATFORM_LABELS = {
    "bilibili": "B站",
    "douyin": "抖音",
    "kuaishou": "快手",
    "weibo": "微博",
    "zhihu": "知乎",
    "wechat": "微信公众号",
    "xiaohongshu": "小红书",
    "toutiao": "今日头条",
}

BilibiliNavFetcher = Callable[[str, int, bool, int], tuple[Mapping[str, Any], str]]
GenericAuthPageFetcher = Callable[[str, str, int, bool, int], tuple[str, str]]


def build_platform_auth_validation(
    *,
    platform_auth_file: str | Path | None = None,
    platforms: list[str] | None = None,
    online: bool = False,
    timeout: int = 10,
    retries: int = 0,
    allow_insecure_tls: bool = False,
    bilibili_nav_fetcher: BilibiliNavFetcher | None = None,
    generic_page_fetcher: GenericAuthPageFetcher | None = None,
) -> dict[str, Any]:
    rows = []
    selected_platforms = platforms or CORE_PLATFORMS
    fetcher = bilibili_nav_fetcher or _fetch_bilibili_nav
    generic_fetcher = generic_page_fetcher or _fetch_auth_page
    for platform in selected_platforms:
        rows.append(
            _platform_row(
                platform,
                platform_auth_file=platform_auth_file,
                online=online,
                timeout=timeout,
                retries=retries,
                allow_insecure_tls=allow_insecure_tls,
                bilibili_nav_fetcher=fetcher,
                generic_page_fetcher=generic_fetcher,
            )
        )
    summary = {
        "total": len(rows),
        "configured_count": sum(1 for item in rows if item["configured"]),
        "available_count": sum(1 for item in rows if item["available"]),
        "online_checked_count": sum(1 for item in rows if item["online_checked"]),
        "passed_count": sum(1 for item in rows if item["status"] == "passed"),
        "failed_count": sum(
            1
            for item in rows
            if item["status"]
            in {"failed", "login_expired", "captcha_or_security_check", "login_state_uncertain"}
        ),
        "missing_count": sum(
            1
            for item in rows
            if item["status"] in {"missing_auth", "auth_file_missing", "auth_not_available"}
        ),
        "pending_validator_count": sum(1 for item in rows if item["status"] == "online_validator_pending"),
    }
    return {
        "mode": "online" if online else "offline",
        "summary": summary,
        "platforms": rows,
        "next_actions": _next_actions(rows, online),
        "security_boundary": (
            "验证过程只读取本地授权文件状态；在线模式只在用户显式开启时发起最小合规请求。"
            "不输出 cookie、session、账号密码或完整本地 cookie 路径；不绕过验证码、付费墙、访问控制或平台明确禁止的接口。"
        ),
    }


def write_platform_auth_validation_dashboard(
    path: str | Path,
    *,
    platform_auth_file: str | Path | None = None,
    platforms: list[str] | None = None,
    online: bool = False,
    timeout: int = 10,
    retries: int = 0,
    allow_insecure_tls: bool = False,
    title: str = "平台授权连通性验证",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    report = build_platform_auth_validation(
        platform_auth_file=platform_auth_file,
        platforms=platforms,
        online=online,
        timeout=timeout,
        retries=retries,
        allow_insecure_tls=allow_insecure_tls,
    )
    output.write_text(render_platform_auth_validation_dashboard(report, title=title), encoding="utf-8")
    return str(output)


def render_platform_auth_validation_dashboard(
    report: Mapping[str, Any],
    *,
    title: str = "平台授权连通性验证",
) -> str:
    summary = report.get("summary") or {}
    platforms = list(report.get("platforms") or [])
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
    .passed {{ color: var(--green); font-weight: 700; }}
    .available_offline, .configured_not_checked, .online_validator_pending {{ color: var(--amber); font-weight: 700; }}
    .missing_auth, .auth_file_missing, .auth_not_available, .login_expired, .failed, .captcha_or_security_check, .login_state_uncertain {{ color: var(--red); font-weight: 700; }}
    .pill {{ display: inline-block; border: 1px solid var(--line); background: var(--soft); padding: 2px 7px; margin: 2px 3px 2px 0; }}
    @media (max-width: 820px) {{
      .metrics {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
      table {{ font-size: 11px; }}
      th, td {{ padding: 6px; }}
    }}
    @media (max-width: 560px) {{
      .page {{ padding: 18px 12px 40px; }}
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <p>Platform Authorization Connectivity Validation</p>
      <h1>{html.escape(title)}</h1>
      <p>模式：{html.escape(str(report.get("mode") or ""))}｜该页面不展示 cookie、session、账号密码或完整本地路径。</p>
    </section>
    <section class="metrics">
      {_metric("平台总数", summary.get("total", 0))}
      {_metric("已配置", summary.get("configured_count", 0))}
      {_metric("本地可用", summary.get("available_count", 0))}
      {_metric("在线验证", summary.get("online_checked_count", 0))}
      {_metric("通过", summary.get("passed_count", 0))}
      {_metric("待接验证器", summary.get("pending_validator_count", 0))}
    </section>
    {_platform_panel(platforms)}
    {_next_action_panel(report.get("next_actions") or [])}
    <article class="panel"><h2>安全与合规边界</h2><p>{html.escape(str(report.get("security_boundary") or ""))}</p></article>
  </main>
</body>
</html>
"""


def _platform_row(
    platform: str,
    *,
    platform_auth_file: str | Path | None,
    online: bool,
    timeout: int,
    retries: int,
    allow_insecure_tls: bool,
    bilibili_nav_fetcher: BilibiliNavFetcher,
    generic_page_fetcher: GenericAuthPageFetcher,
) -> dict[str, Any]:
    state = platform_auth_state(platform, platform_auth_file)
    row = {
        "platform": state.platform,
        "label": PLATFORM_LABELS.get(state.platform, state.platform),
        "configured": state.configured,
        "available": state.available,
        "auth_method": state.auth_method,
        "credential_type": "cookie_file" if state.cookie_file else "session_file" if state.session_file else "",
        "online_checked": False,
        "status": _offline_status(state.status, state.available),
        "validation_scope": "local_file_presence",
        "allowed_capabilities": list(state.allowed_capabilities),
        "error_class": "",
    }
    if not online:
        return row
    if not state.available:
        row["validation_scope"] = "online_skipped_missing_auth"
        return row
    if state.platform != "bilibili":
        if not state.cookie_file:
            row["status"] = "online_validator_pending"
            row["validation_scope"] = "cookie_file_required_for_generic_validation"
            return row
        if not state.validation_url:
            row["status"] = "online_validator_pending"
            row["validation_scope"] = "validation_url_not_configured"
            return row
        body, fetch_status = generic_page_fetcher(
            state.cookie_file,
            state.validation_url,
            timeout,
            allow_insecure_tls,
            retries,
        )
        row["online_checked"] = True
        row["validation_scope"] = "configured_validation_url"
        row["status"] = _generic_auth_page_status(
            body,
            fetch_status,
            success_markers=state.success_markers,
            login_required_markers=state.login_required_markers,
            captcha_markers=state.captcha_markers,
        )
        row["error_class"] = "" if fetch_status == "ok" else _error_class(fetch_status)
        return row
    if not state.cookie_file:
        row["status"] = "online_validator_pending"
        row["validation_scope"] = "bilibili_cookie_file_required"
        return row
    payload, fetch_status = bilibili_nav_fetcher(state.cookie_file, timeout, allow_insecure_tls, retries)
    row["online_checked"] = True
    row["validation_scope"] = "bilibili_nav_login_state"
    row["status"] = _bilibili_status(payload, fetch_status)
    row["error_class"] = "" if fetch_status == "ok" else _error_class(fetch_status)
    return row


def _offline_status(source_status: str, available: bool) -> str:
    if available:
        return "available_offline"
    if source_status in {"auth_cookie_file_missing", "auth_session_file_missing"}:
        return "auth_file_missing"
    if source_status == "auth_not_configured":
        return "missing_auth"
    return "auth_not_available"


def _bilibili_status(payload: Mapping[str, Any], fetch_status: str) -> str:
    if fetch_status != "ok":
        return "failed"
    if int(payload.get("code") or 0) != 0:
        return "failed"
    data = payload.get("data") or {}
    if isinstance(data, Mapping) and data.get("isLogin") is True:
        return "passed"
    return "login_expired"


def _fetch_bilibili_nav(
    cookie_file: str,
    timeout: int,
    allow_insecure_tls: bool,
    retries: int,
) -> tuple[Mapping[str, Any], str]:
    cookie = Path(cookie_file).expanduser().read_text(encoding="utf-8").strip()
    headers = {
        "User-Agent": "PolicyIntelligenceBot/0.1 (+local research automation)",
        "Accept": "application/json",
        "Cookie": cookie,
    }
    request = Request(BILIBILI_NAV_URL, headers=headers)
    context = ssl._create_unverified_context() if allow_insecure_tls else None
    body = ""
    for attempt in range(max(1, retries + 1)):
        try:
            with urlopen(request, timeout=timeout, context=context) as response:
                body = response.read(500_000).decode("utf-8", "replace")
            return json.loads(body), "ok"
        except Exception as exc:
            if attempt >= retries:
                return {}, f"request_failed:{type(exc).__name__}"
            time.sleep(min(2.0, 0.4 * (attempt + 1)))
    return {}, "request_failed"


def _fetch_auth_page(
    cookie_file: str,
    url: str,
    timeout: int,
    allow_insecure_tls: bool,
    retries: int,
) -> tuple[str, str]:
    cookie = Path(cookie_file).expanduser().read_text(encoding="utf-8").strip()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
        ),
        "Accept": "text/html,application/json,text/plain,*/*",
        "Cookie": cookie,
    }
    request = Request(url, headers=headers)
    context = ssl._create_unverified_context() if allow_insecure_tls else None
    for attempt in range(max(1, retries + 1)):
        try:
            with urlopen(request, timeout=timeout, context=context) as response:
                body = response.read(500_000).decode("utf-8", "replace")
            return body, "ok"
        except Exception as exc:
            if attempt >= retries:
                return "", f"request_failed:{type(exc).__name__}"
            time.sleep(min(2.0, 0.4 * (attempt + 1)))
    return "", "request_failed"


def _generic_auth_page_status(
    body: str,
    fetch_status: str,
    *,
    success_markers: tuple[str, ...],
    login_required_markers: tuple[str, ...],
    captcha_markers: tuple[str, ...],
) -> str:
    if fetch_status != "ok":
        return "failed"
    lower = body.lower()
    if any(marker.lower() in lower for marker in captcha_markers):
        return "captcha_or_security_check"
    if any(marker.lower() in lower for marker in login_required_markers):
        return "login_expired"
    if success_markers and any(marker.lower() in lower for marker in success_markers):
        return "passed"
    if success_markers:
        return "login_state_uncertain"
    return "online_validator_pending"


def _error_class(status: str) -> str:
    if status.startswith("request_failed:"):
        return status.split(":")[-1]
    return status


def _next_actions(rows: list[Mapping[str, Any]], online: bool) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    missing = [item["platform"] for item in rows if item["status"] in {"missing_auth", "auth_file_missing", "auth_not_available"}]
    if missing:
        actions.append({"priority": 95, "action": "provide_platform_auth", "label": "补充或修复本地平台授权文件", "targets": missing})
    if not online and any(item["available"] for item in rows):
        actions.append({"priority": 88, "action": "run_online_platform_validation", "label": "手动运行在线平台授权验证", "targets": ["bilibili"]})
    pending = [item["platform"] for item in rows if item["status"] == "online_validator_pending"]
    if pending:
        actions.append({"priority": 82, "action": "implement_platform_auth_validator", "label": "补齐平台在线授权验证器", "targets": pending})
    expired = [item["platform"] for item in rows if item["status"] == "login_expired"]
    if expired:
        actions.append({"priority": 80, "action": "refresh_platform_cookie", "label": "刷新已过期平台 cookie/session", "targets": expired})
    failed = [item["platform"] for item in rows if item["status"] in {"failed", "captcha_or_security_check", "login_state_uncertain"}]
    if failed:
        actions.append({"priority": 75, "action": "inspect_platform_validation_error", "label": "检查网络、平台接口或授权文件格式", "targets": failed})
    return sorted(actions, key=lambda item: int(item.get("priority") or 0), reverse=True)


def _platform_panel(platforms: list[Mapping[str, Any]]) -> str:
    rows = []
    for platform in platforms:
        status = str(platform.get("status") or "")
        caps = "".join(
            f'<span class="pill">{html.escape(str(item))}</span>'
            for item in platform.get("allowed_capabilities") or []
        )
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(platform.get('label') or platform.get('platform') or ''))}</td>"
            f'<td class="{html.escape(status)}">{html.escape(status)}</td>'
            f"<td>{html.escape('yes' if platform.get('configured') else 'no')}</td>"
            f"<td>{html.escape('yes' if platform.get('available') else 'no')}</td>"
            f"<td>{html.escape(str(platform.get('auth_method') or ''))}</td>"
            f"<td>{html.escape(str(platform.get('credential_type') or ''))}</td>"
            f"<td>{html.escape('yes' if platform.get('online_checked') else 'no')}</td>"
            f"<td>{html.escape(str(platform.get('validation_scope') or ''))}</td>"
            f"<td>{caps}</td>"
            f"<td>{html.escape(str(platform.get('error_class') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel"><h2>平台授权验证明细</h2>'
        '<table><thead><tr><th>平台</th><th>状态</th><th>配置</th><th>本地可用</th><th>授权方式</th><th>凭据类型</th><th>在线</th><th>验证范围</th><th>允许能力</th><th>错误类</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table>'
        '<p class="note">本地可用只代表 cookie/session 文件存在；是否能计入报告，还取决于在线验证、解析器和外部参考质量门槛。</p></article>'
    )


def _next_action_panel(actions: list[Mapping[str, Any]]) -> str:
    rows = []
    for action in actions:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(action.get('priority') or ''))}</td>"
            f"<td>{html.escape(str(action.get('action') or ''))}</td>"
            f"<td>{html.escape(str(action.get('label') or ''))}</td>"
            f"<td>{html.escape(', '.join(str(item) for item in action.get('targets') or []))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel"><h2>下一步动作</h2>'
        '<table><thead><tr><th>优先级</th><th>动作</th><th>说明</th><th>目标</th></tr></thead>'
        f'<tbody>{"".join(rows) if rows else "<tr><td colspan=\"4\">暂无动作。</td></tr>"}</tbody></table></article>'
    )


def _metric(label: str, value: object) -> str:
    return (
        '<article class="metric">'
        f"<span>{html.escape(str(label))}</span>"
        f"<strong>{html.escape(str(value))}</strong>"
        "</article>"
    )
