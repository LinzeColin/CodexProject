from __future__ import annotations

import html
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .config_setup import SEARCH_SECRET_KEYS, build_config_setup
from .platform_auth import DEFAULT_CAPABILITIES
from .readiness import CORE_PLATFORMS


PLACEHOLDERS = {"", "todo", "change_me", "changeme", "your_key_here", "your-api-key", "xxx", "xxxx"}
STALE_DAYS = 30


def build_credential_doctor(
    *,
    secure_dir: str | Path | None = None,
    search_secrets_file: str | Path | None = None,
    platform_auth_file: str | Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    setup = build_config_setup(secure_dir=secure_dir)
    search_path = Path(search_secrets_file or setup["search_secrets_path"]).expanduser()
    auth_path = Path(platform_auth_file or setup["platform_auth_path"]).expanduser()
    search = _search_secret_report(search_path)
    platform = _platform_auth_report(auth_path, now=now)
    summary = _summary(search, platform)
    p0_gate = _p0_gate(search, platform)
    return {
        "generated_at": (now or datetime.now(timezone.utc)).isoformat(),
        "overall_status": _overall_status(summary),
        "summary": summary,
        "p0_gate": p0_gate,
        "search_secrets": search,
        "platform_auth": platform,
        "next_actions": _next_actions(summary, p0_gate),
        "security_boundary": (
            "只检查文件存在性、格式、权限、字段状态和文件年龄；"
            "不打印 API key、cookie、session 内容或完整本地 cookie 路径。"
        ),
    }


def write_credential_doctor_dashboard(
    path: str | Path,
    *,
    secure_dir: str | Path | None = None,
    search_secrets_file: str | Path | None = None,
    platform_auth_file: str | Path | None = None,
    title: str = "本地凭据体检",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    report = build_credential_doctor(
        secure_dir=secure_dir,
        search_secrets_file=search_secrets_file,
        platform_auth_file=platform_auth_file,
    )
    output.write_text(render_credential_doctor_dashboard(report, title=title), encoding="utf-8")
    return str(output)


def render_credential_doctor_dashboard(
    report: Mapping[str, Any],
    *,
    title: str = "本地凭据体检",
) -> str:
    summary = report.get("summary") or {}
    search = report.get("search_secrets") or {}
    platform = report.get("platform_auth") or {}
    p0_gate = report.get("p0_gate") or {}
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
    .ok {{ color: var(--green); font-weight: 700; }}
    .warning {{ color: var(--amber); font-weight: 700; }}
    .error {{ color: var(--red); font-weight: 700; }}
    .pill {{ display: inline-block; border: 1px solid var(--line); background: var(--soft); padding: 2px 7px; margin: 2px 3px 2px 0; }}
    .cmd {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; overflow-wrap: anywhere; font-size: 11px; }}
    @media (max-width: 920px) {{
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
      <p>Local Credential Doctor</p>
      <h1>{html.escape(title)}</h1>
      <p>生成时间：{html.escape(str(report.get("generated_at") or ""))}｜该页面不展示 API key、cookie、session 内容或完整本地 cookie 路径。</p>
    </section>
    <section class="metrics">
      {_metric("搜索文件", search.get("status", "unknown"))}
      {_metric("搜索 key ready", summary.get("search_ready", 0))}
      {_metric("授权文件", platform.get("status", "unknown"))}
      {_metric("平台可用", summary.get("platform_available", 0))}
      {_metric("警告", summary.get("warnings", 0))}
      {_metric("错误", summary.get("errors", 0))}
    </section>
    <section class="grid">
      {_p0_gate_panel(p0_gate)}
      {_search_panel(search)}
      {_platform_panel(platform)}
      {_next_actions_panel(report.get("next_actions") or [])}
      {_security_panel(str(report.get("security_boundary") or ""))}
    </section>
  </main>
</body>
</html>
"""


def _search_secret_report(path: Path) -> dict[str, Any]:
    base = _file_report(path)
    values, format_status = _load_secret_values(path)
    providers = [
        _search_provider_row("serpapi", ["SERPAPI_API_KEY"], values),
        _search_provider_row("bing", ["BING_SEARCH_API_KEY", "AZURE_BING_SEARCH_KEY"], values),
        _search_provider_row("google", ["GOOGLE_SEARCH_API_KEY", "GOOGLE_API_KEY", "GOOGLE_CSE_ID"], values),
    ]
    ready_count = sum(1 for item in providers if item["ready"])
    base.update(
        {
            "status": _file_status(base, format_status, ready_count > 0),
            "format_status": format_status,
            "providers": providers,
            "ready_count": ready_count,
        }
    )
    return base


def _platform_auth_report(path: Path, now: datetime | None = None) -> dict[str, Any]:
    base = _file_report(path)
    payload, format_status = _load_json(path)
    platform_config = payload.get("platforms") if isinstance(payload, Mapping) else {}
    rows = []
    for platform in CORE_PLATFORMS:
        raw = platform_config.get(platform) if isinstance(platform_config, Mapping) else None
        config = raw if isinstance(raw, Mapping) else {}
        rows.append(_platform_row(platform, config, now=now))
    available = sum(1 for item in rows if item["available"])
    base.update(
        {
            "status": _file_status(base, format_status, available > 0),
            "format_status": format_status,
            "platforms": rows,
            "available_count": available,
            "configured_count": sum(1 for item in rows if item["configured"]),
        }
    )
    return base


def _file_report(path: Path) -> dict[str, Any]:
    exists = path.exists()
    mode = _mode(path) if exists else ""
    return {
        "path_label": _path_label(path),
        "exists": exists,
        "mode": mode,
        "permission_status": _permission_status(path) if exists else "missing",
        "size_status": _size_status(path) if exists else "missing",
    }


def _search_provider_row(provider: str, key_names: list[str], values: Mapping[str, str]) -> dict[str, Any]:
    states = [_secret_state(values.get(name, "")) for name in key_names]
    if provider == "google":
        key_ready = any(_secret_state(values.get(name, "")) == "present" for name in ["GOOGLE_SEARCH_API_KEY", "GOOGLE_API_KEY"])
        engine_ready = _secret_state(values.get("GOOGLE_CSE_ID", "")) == "present"
        ready = key_ready and engine_ready
        missing = [
            name
            for name in ["GOOGLE_SEARCH_API_KEY", "GOOGLE_CSE_ID"]
            if _secret_state(values.get(name, "")) != "present"
        ]
    else:
        ready = any(state == "present" for state in states)
        missing = [key_names[0]] if not ready else []
    return {
        "provider": provider,
        "ready": ready,
        "required": key_names,
        "missing_or_placeholder": missing,
        "status": "ready" if ready else "missing_or_placeholder",
    }


def _platform_row(platform: str, config: Mapping[str, Any], now: datetime | None = None) -> dict[str, Any]:
    cookie_file = str(config.get("cookie_file") or "").strip()
    session_file = str(
        config.get("chrome_session_file")
        or config.get("session_file")
        or config.get("chrome_profile_dir")
        or config.get("chrome_user_data_dir")
        or ""
    ).strip()
    auth_method = str(config.get("auth_method") or "").strip()
    allowed = list(config.get("allowed_capabilities") or DEFAULT_CAPABILITIES.get(platform, []))
    file_kind = "cookie" if cookie_file else "session" if session_file else ""
    credential_path = Path(cookie_file or session_file).expanduser() if (cookie_file or session_file) else None
    file_status = _credential_file_status(credential_path, now=now) if credential_path else "not_configured"
    available = file_status == "ok"
    configured = bool(cookie_file or session_file or auth_method)
    return {
        "platform": platform,
        "configured": configured,
        "available": available,
        "auth_method": auth_method or file_kind,
        "file_kind": file_kind,
        "file_status": file_status,
        "permission_status": _permission_status(credential_path) if credential_path and credential_path.exists() else file_status,
        "age_status": _age_status(credential_path, now=now) if credential_path and credential_path.exists() else file_status,
        "allowed_capabilities": allowed,
    }


def _credential_file_status(path: Path | None, now: datetime | None = None) -> str:
    if not path:
        return "not_configured"
    if not path.exists():
        return "missing_file"
    if path.is_dir():
        return "ok"
    if path.stat().st_size <= 0:
        return "empty_file"
    permission = _permission_status(path)
    if permission == "too_open":
        return "permission_too_open"
    age = _age_status(path, now=now)
    if age == "stale":
        return "stale"
    return "ok"


def _load_secret_values(path: Path) -> tuple[dict[str, str], str]:
    if not path.exists():
        return {}, "missing"
    text = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        values = {}
        for line in text.splitlines():
            clean = line.strip()
            if not clean or clean.startswith("#") or "=" not in clean:
                continue
            key, value = clean.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
        return values, "dotenv" if values else "invalid"
    if not isinstance(payload, Mapping):
        return {}, "invalid"
    return {str(key): str(value) for key, value in payload.items()}, "json"


def _load_json(path: Path) -> tuple[dict[str, Any], str]:
    if not path.exists():
        return {}, "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}, "invalid"
    return (dict(payload), "json") if isinstance(payload, Mapping) else ({}, "invalid")


def _secret_state(value: str) -> str:
    clean = str(value or "").strip()
    if not clean:
        return "empty"
    normalized = clean.lower().replace(" ", "_")
    if normalized in PLACEHOLDERS or normalized.startswith("your_") or normalized.startswith("replace_"):
        return "placeholder"
    return "present"


def _permission_status(path: Path | None) -> str:
    if not path:
        return "not_configured"
    if not path.exists():
        return "missing"
    mode = stat.S_IMODE(path.stat().st_mode)
    return "ok" if mode & 0o077 == 0 else "too_open"


def _size_status(path: Path) -> str:
    if not path.exists():
        return "missing"
    return "empty" if path.stat().st_size <= 0 else "nonempty"


def _age_status(path: Path, now: datetime | None = None) -> str:
    timestamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return "stale" if (current - timestamp).days > STALE_DAYS else "fresh"


def _mode(path: Path) -> str:
    return oct(stat.S_IMODE(path.stat().st_mode))


def _file_status(base: Mapping[str, Any], format_status: str, ready: bool) -> str:
    if not base.get("exists"):
        return "missing"
    if base.get("size_status") == "empty":
        return "empty"
    if format_status == "invalid":
        return "invalid"
    if base.get("permission_status") == "too_open":
        return "permission_warning"
    return "ready" if ready else "needs_values"


def _summary(search: Mapping[str, Any], platform: Mapping[str, Any]) -> dict[str, int]:
    warnings = 0
    errors = 0
    for status in [search.get("status"), platform.get("status")]:
        if status in {"missing", "empty", "invalid"}:
            errors += 1
        if status == "permission_warning":
            warnings += 1
    for row in platform.get("platforms") or []:
        if row.get("file_status") in {"missing_file", "empty_file"}:
            errors += 1
        if row.get("file_status") in {"permission_too_open", "stale"}:
            warnings += 1
    return {
        "search_ready": int(search.get("ready_count") or 0),
        "platform_available": int(platform.get("available_count") or 0),
        "platform_configured": int(platform.get("configured_count") or 0),
        "warnings": warnings,
        "errors": errors,
    }


def _p0_gate(search: Mapping[str, Any], platform: Mapping[str, Any]) -> dict[str, Any]:
    providers = list(search.get("providers") or [])
    search_ready = [str(item.get("provider") or "") for item in providers if item.get("ready")]
    platform_rows = {str(item.get("platform") or ""): item for item in platform.get("platforms") or []}
    bilibili = platform_rows.get("bilibili") or {}
    checks = [
        {
            "item": "搜索 API 最小可用",
            "status": "pass" if len(search_ready) >= 1 else "fail",
            "current": f"{len(search_ready)}/3",
            "required": "至少 1 个 provider",
            "business_value": "扩大公开网页研究入口，减少外部参考不足。",
        },
        {
            "item": "搜索 API 完整覆盖",
            "status": "pass" if len(search_ready) >= 3 else "partial" if search_ready else "fail",
            "current": f"{len(search_ready)}/3",
            "required": "SerpAPI、Bing、Google CSE",
            "business_value": "提高召回率，降低单一搜索源遗漏。",
        },
        {
            "item": "B站授权最小可用",
            "status": "pass" if bilibili.get("available") else "fail",
            "current": str(bilibili.get("file_status") or "not_configured"),
            "required": "本地授权文件存在、非空、权限安全、未过期",
            "business_value": "解锁政策解读视频、字幕、作者页、评论/弹幕线索。",
        },
    ]
    minimum_ready = checks[0]["status"] == "pass" and checks[2]["status"] == "pass"
    complete = checks[1]["status"] == "pass" and checks[2]["status"] == "pass"
    if complete:
        status = "p0_complete"
    elif minimum_ready:
        status = "p0_minimum_ready"
    else:
        status = "p0_blocked"
    return {
        "status": status,
        "minimum_ready": minimum_ready,
        "complete": complete,
        "checks": checks,
        "recommended_order": ["搜索 API", "B站", "微信公众号/知乎/微博", "抖音/快手/小红书/头条"],
    }


def _overall_status(summary: Mapping[str, int]) -> str:
    if int(summary.get("errors") or 0) > 0:
        return "needs_fix"
    if int(summary.get("warnings") or 0) > 0:
        return "warning"
    if int(summary.get("search_ready") or 0) or int(summary.get("platform_available") or 0):
        return "ready_partial"
    return "not_configured"


def _next_actions(summary: Mapping[str, int], p0_gate: Mapping[str, Any]) -> list[dict[str, Any]]:
    actions = []
    checks = {str(item.get("item") or ""): item for item in p0_gate.get("checks") or []}
    if checks.get("搜索 API 最小可用", {}).get("status") != "pass":
        actions.append({"priority": 100, "action": "fill_one_search_api", "label": "先补 SerpAPI/Bing/Google CSE 任一可用 key"})
    if checks.get("B站授权最小可用", {}).get("status") != "pass":
        actions.append({"priority": 98, "action": "provide_bilibili_auth", "label": "先放入 B站本地登录态文件并保持 0600 权限"})
    if int(summary.get("search_ready") or 0) < 3:
        actions.append({"priority": 95, "action": "fill_search_keys", "label": "补齐 SerpAPI/Bing/Google CSE key"})
    if int(summary.get("platform_available") or 0) < len(CORE_PLATFORMS):
        actions.append({"priority": 90, "action": "provide_platform_auth", "label": "补平台 cookie/session 文件"})
    if int(summary.get("warnings") or 0) > 0:
        actions.append({"priority": 80, "action": "tighten_file_permissions", "label": "修复权限过宽或过旧文件"})
    return actions


def _p0_gate_panel(gate: Mapping[str, Any]) -> str:
    rows = []
    for check in gate.get("checks") or []:
        status = str(check.get("status") or "")
        css = "ok" if status == "pass" else "warning" if status == "partial" else "error"
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(check.get('item') or ''))}</td>"
            f"<td class=\"{css}\">{html.escape(status)}</td>"
            f"<td>{html.escape(str(check.get('current') or ''))}</td>"
            f"<td>{html.escape(str(check.get('required') or ''))}</td>"
            f"<td>{html.escape(str(check.get('business_value') or ''))}</td>"
            "</tr>"
        )
    order = " → ".join(str(item) for item in gate.get("recommended_order") or [])
    return (
        '<article class="panel wide"><h2>P0 接入门槛</h2>'
        f'<p class="note">状态：{html.escape(str(gate.get("status") or ""))}；推荐顺序：{html.escape(order)}</p>'
        '<table><thead><tr><th>检查项</th><th>状态</th><th>当前</th><th>要求</th><th>业务价值</th></tr></thead>'
        f'<tbody>{"".join(rows) if rows else "<tr><td colspan=\"5\">暂无检查项。</td></tr>"}</tbody></table></article>'
    )


def _search_panel(search: Mapping[str, Any]) -> str:
    rows = []
    for provider in search.get("providers") or []:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(provider.get('provider') or ''))}</td>"
            f"<td class=\"{'ok' if provider.get('ready') else 'error'}\">{html.escape(str(provider.get('status') or ''))}</td>"
            f"<td>{_chips(provider.get('missing_or_placeholder') or [])}</td>"
            "</tr>"
        )
    return (
        '<article class="panel"><h2>搜索 API 体检</h2>'
        f'<p class="note">文件：{html.escape(str(search.get("path_label") or ""))}；格式：{html.escape(str(search.get("format_status") or ""))}；权限：{html.escape(str(search.get("permission_status") or ""))}</p>'
        '<table><thead><tr><th>Provider</th><th>状态</th><th>缺失/占位字段</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></article>'
    )


def _platform_panel(platform: Mapping[str, Any]) -> str:
    rows = []
    for row in platform.get("platforms") or []:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('platform') or ''))}</td>"
            f"<td>{html.escape(str(row.get('file_kind') or ''))}</td>"
            f"<td class=\"{'ok' if row.get('available') else 'error'}\">{html.escape(str(row.get('file_status') or ''))}</td>"
            f"<td>{html.escape(str(row.get('permission_status') or ''))}</td>"
            f"<td>{html.escape(str(row.get('age_status') or ''))}</td>"
            f"<td>{_chips(row.get('allowed_capabilities') or [])}</td>"
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>平台授权体检</h2>'
        f'<p class="note">文件：{html.escape(str(platform.get("path_label") or ""))}；格式：{html.escape(str(platform.get("format_status") or ""))}；权限：{html.escape(str(platform.get("permission_status") or ""))}</p>'
        '<table><thead><tr><th>平台</th><th>文件类型</th><th>状态</th><th>权限</th><th>年龄</th><th>能力</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></article>'
    )


def _next_actions_panel(actions: list[Mapping[str, Any]]) -> str:
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


def _security_panel(text: str) -> str:
    return (
        '<article class="panel"><h2>安全边界</h2>'
        f'<p>{html.escape(text)}</p>'
        '<p class="note">体检结果适合发给我；真实 key、cookie、session 内容不要发。</p></article>'
    )


def _metric(label: str, value: object) -> str:
    return (
        '<article class="metric">'
        f"<span>{html.escape(str(label))}</span>"
        f"<strong>{html.escape(str(value))}</strong>"
        "</article>"
    )


def _chips(values: list[Any]) -> str:
    if not values:
        return '<span class="pill">无</span>'
    return "".join(f'<span class="pill">{html.escape(str(value))}</span>' for value in values)


def _path_label(path: Path) -> str:
    home = str(Path.home())
    value = str(path)
    if value.startswith(home):
        value = "~" + value[len(home) :]
    if ".policy-intelligence/cookies/" in value:
        return "~/.policy-intelligence/cookies/<redacted>"
    return value
