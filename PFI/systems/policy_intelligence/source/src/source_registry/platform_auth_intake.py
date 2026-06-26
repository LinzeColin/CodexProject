from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from .config_setup import build_config_setup
from .platform_auth import DEFAULT_CAPABILITIES, platform_auth_state
from .platform_auth_validation import PLATFORM_LABELS
from .readiness import CORE_PLATFORMS


PRIORITY_BY_PLATFORM = {
    "bilibili": "P0",
    "wechat": "P1",
    "zhihu": "P1",
    "weibo": "P1",
    "douyin": "P2",
    "kuaishou": "P2",
    "xiaohongshu": "P2",
    "toutiao": "P2",
}

BUSINESS_VALUE_BY_PLATFORM = {
    "bilibili": "政策解读视频、字幕、作者页、评论/弹幕线索。",
    "wechat": "公众号深度文章、官方媒体和机构解读。",
    "zhihu": "专家回答、长文分析、观点分歧。",
    "weibo": "政策传播、机构账号和舆情信号。",
    "douyin": "短视频解读与传播热度线索。",
    "kuaishou": "短视频解读与区域传播线索。",
    "xiaohongshu": "消费、医疗、教育等民生政策讨论线索。",
    "toutiao": "媒体文章、评论和热点传播线索。",
}

ACQUISITION_BY_PLATFORM = {
    "bilibili": "导出已登录会话的 cookie 文本到本地目标文件。",
    "wechat": "使用已登录浏览器会话或公开可访问文章链接；遇到验证码则记录缺口。",
    "zhihu": "导出已登录会话的 cookie 文本到本地目标文件。",
    "weibo": "导出已登录会话的 cookie 文本到本地目标文件。",
    "douyin": "优先使用已登录 Chrome 会话或本地 cookie 文件。",
    "kuaishou": "优先使用已登录 Chrome 会话或本地 cookie 文件。",
    "xiaohongshu": "优先使用已登录 Chrome 会话或本地 cookie 文件。",
    "toutiao": "导出已登录会话的 cookie 文本到本地目标文件。",
}


def build_platform_auth_intake(
    *,
    secure_dir: str | Path | None = None,
    platform_auth_file: str | Path | None = None,
) -> dict[str, Any]:
    setup = build_config_setup(secure_dir=secure_dir, platform_auth_path=platform_auth_file)
    auth_path = str(platform_auth_file or setup["platform_auth_path"])
    rows = [_platform_row(platform, auth_path=auth_path, cookie_dir=Path(str(setup["cookie_dir"]))) for platform in CORE_PLATFORMS]
    summary = {
        "total": len(rows),
        "p0_total": sum(1 for row in rows if row["priority"] == "P0"),
        "p0_ready": sum(1 for row in rows if row["priority"] == "P0" and row["collector_ready"]),
        "configured_count": sum(1 for row in rows if row["configured"]),
        "available_count": sum(1 for row in rows if row["available"]),
        "collector_ready_count": sum(1 for row in rows if row["collector_ready"]),
        "session_only_count": sum(1 for row in rows if row["session_only"]),
        "missing_file_count": sum(1 for row in rows if row["auth_status"] in {"auth_cookie_file_missing", "auth_session_file_missing"}),
    }
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "platform_auth_path": _path_label(Path(auth_path).expanduser()),
        "cookie_dir": _path_label(Path(str(setup["cookie_dir"])).expanduser()),
        "summary": summary,
        "platforms": rows,
        "commands": {
            "bundle_import_cookies": (
                "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-bundle-import "
                f"--source-file /path/to/platform_auth_bundle.json --platform-auth-file {_tilde(auth_path)}"
            ),
            "bulk_import_cookies": (
                "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-bulk-import "
                f"--source-dir /path/to/exported_cookie_dir --platform-auth-file {_tilde(auth_path)}"
            ),
            "import_chrome_session_reference": (
                "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-session-import "
                f"--platform bilibili --session-file /path/to/chrome_profile_or_storage_state --platform-auth-file {_tilde(auth_path)}"
            ),
            "import_bilibili_cookie": (
                "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-import "
                f"--platform bilibili --source-file /path/to/exported_bilibili_cookie.txt --platform-auth-file {_tilde(auth_path)}"
            ),
            "doctor": (
                "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite credential-doctor "
                f"--platform-auth-file {_tilde(auth_path)}"
            ),
            "offline_validate": (
                "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-validate "
                f"--platform-auth-file {_tilde(auth_path)}"
            ),
            "online_bilibili": (
                "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-validate "
                f"--platform-auth-file {_tilde(auth_path)} --platform bilibili --online"
            ),
        },
        "security_boundary": (
            "只接受你授权的本地 cookie/session 文件或公开页面；不在聊天、报告、dashboard 或日志中展示 cookie、"
            "session、账号密码或完整敏感路径；不绕过验证码、付费墙、访问控制或平台禁止接口。"
        ),
    }


def write_platform_auth_intake_dashboard(
    path: str | Path,
    *,
    secure_dir: str | Path | None = None,
    platform_auth_file: str | Path | None = None,
    title: str = "平台授权接入清单",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    report = build_platform_auth_intake(secure_dir=secure_dir, platform_auth_file=platform_auth_file)
    output.write_text(render_platform_auth_intake_dashboard(report, title=title), encoding="utf-8")
    return str(output)


def render_platform_auth_intake_dashboard(report: Mapping[str, Any], *, title: str = "平台授权接入清单") -> str:
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
    .ready {{ color: var(--green); font-weight: 700; }}
    .blocked {{ color: var(--red); font-weight: 700; }}
    .pending {{ color: var(--amber); font-weight: 700; }}
    .session_only {{ color: var(--amber); font-weight: 700; }}
    .cmd {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; overflow-wrap: anywhere; font-size: 11px; }}
    .pill {{ display: inline-block; border: 1px solid var(--line); background: var(--soft); padding: 2px 7px; margin: 2px 3px 2px 0; }}
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
      <p>Platform Auth Intake Checklist</p>
      <h1>{html.escape(title)}</h1>
      <p>生成时间：{html.escape(str(report.get("generated_at") or ""))}｜只展示目标文件位置和状态，不展示 cookie、session、账号密码或完整敏感路径。</p>
    </section>
    <section class="metrics">
      {_metric("平台总数", summary.get("total", 0))}
      {_metric("P0 ready", f"{summary.get('p0_ready', 0)}/{summary.get('p0_total', 0)}")}
      {_metric("已配置路径", summary.get("configured_count", 0))}
      {_metric("授权可用", summary.get("available_count", 0))}
      {_metric("可直接采集", summary.get("collector_ready_count", 0))}
      {_metric("缺文件", summary.get("missing_file_count", 0))}
      {_metric("session-only", summary.get("session_only_count", 0))}
    </section>
    <section class="grid">
      {_intake_table(platforms)}
      {_commands_panel(report.get("commands") or {})}
      {_security_panel(str(report.get("security_boundary") or ""))}
    </section>
  </main>
</body>
</html>
"""


def _platform_row(platform: str, *, auth_path: str, cookie_dir: Path) -> dict[str, Any]:
    state = platform_auth_state(platform, auth_path)
    expected = cookie_dir / f"{platform}_cookie.txt"
    collector_ready = bool(state.available and state.cookie_file)
    session_only = bool(state.available and state.session_file and not state.cookie_file)
    status = "ready" if collector_ready else "session_only" if session_only else "blocked" if state.configured else "pending"
    return {
        "platform": platform,
        "label": PLATFORM_LABELS.get(platform, platform),
        "priority": PRIORITY_BY_PLATFORM.get(platform, "P2"),
        "configured": state.configured,
        "available": state.available,
        "collector_ready": collector_ready,
        "session_only": session_only,
        "status": status,
        "auth_status": state.status,
        "target_file": _path_label(expected),
        "acquisition": ACQUISITION_BY_PLATFORM.get(platform, "放入你授权的本地会话文件。"),
        "import_command": _import_command(platform, auth_path),
        "session_command": _session_command(platform, auth_path),
        "validation": _validation_command(platform, auth_path),
        "capabilities": list(state.allowed_capabilities or DEFAULT_CAPABILITIES.get(platform, [])),
        "business_value": BUSINESS_VALUE_BY_PLATFORM.get(platform, "补充外部解读与传播线索。"),
    }


def _validation_command(platform: str, auth_path: str) -> str:
    online = " --online" if platform == "bilibili" else ""
    return (
        "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-validate "
        f"--platform-auth-file {_tilde(auth_path)} --platform {platform}{online}"
    )


def _import_command(platform: str, auth_path: str) -> str:
    return (
        "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-import "
        f"--platform {platform} --source-file /path/to/exported_{platform}_cookie.txt --platform-auth-file {_tilde(auth_path)}"
    )


def _session_command(platform: str, auth_path: str) -> str:
    return (
        "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-session-import "
        f"--platform {platform} --session-file /path/to/chrome_profile_or_storage_state --platform-auth-file {_tilde(auth_path)}"
    )


def _intake_table(rows: list[Mapping[str, Any]]) -> str:
    ordered = sorted(rows, key=lambda row: (str(row.get("priority") or "P9"), str(row.get("label") or "")))
    body = []
    for row in ordered:
        status = str(row.get("status") or "pending")
        body.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('priority') or ''))}</td>"
            f"<td>{html.escape(str(row.get('label') or row.get('platform') or ''))}</td>"
            f"<td class=\"{html.escape(status)}\">{html.escape(str(row.get('auth_status') or status))}</td>"
            f"<td class=\"cmd\">{html.escape(str(row.get('target_file') or ''))}</td>"
            f"<td>{html.escape(str(row.get('acquisition') or ''))}</td>"
            f"<td>{html.escape(str(row.get('business_value') or ''))}</td>"
            f"<td>{_chips(row.get('capabilities') or [])}</td>"
            f"<td class=\"cmd\">{html.escape(str(row.get('import_command') or ''))}<br>{html.escape(str(row.get('session_command') or ''))}</td>"
            f"<td class=\"cmd\">{html.escape(str(row.get('validation') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>接入清单</h2>'
        '<table><thead><tr><th>优先级</th><th>平台</th><th>状态</th><th>目标文件</th><th>接入方式</th><th>业务价值</th><th>能力</th><th>导入命令</th><th>验收命令</th></tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></article>'
    )


def _commands_panel(commands: Mapping[str, str]) -> str:
    rows = []
    for key, command in commands.items():
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(key))}</td>"
            f"<td class=\"cmd\">{html.escape(str(command))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>全局验收命令</h2>'
        '<table><thead><tr><th>动作</th><th>命令</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></article>'
    )


def _security_panel(text: str) -> str:
    return (
        '<article class="panel wide"><h2>安全与合规边界</h2>'
        f'<p>{html.escape(text)}</p>'
        '<p class="note">不要把真实账号密码、API key、cookie 或 session 内容发到聊天里。</p></article>'
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
        return '<span class="pill">未声明</span>'
    return "".join(f'<span class="pill">{html.escape(str(value))}</span>' for value in values)


def _path_label(path: Path) -> str:
    value = str(path)
    home = str(Path.home())
    if value.startswith(home):
        value = "~" + value[len(home) :]
    if ".policy-intelligence/cookies/" in value:
        return "~/.policy-intelligence/cookies/" + Path(value).name
    if Path(value).parent.name == "cookies":
        return "<cookie_dir>/" + Path(value).name
    return value


def _tilde(path: str | Path) -> str:
    value = str(path)
    home = str(Path.home())
    if value.startswith(home):
        return "~" + value[len(home) :]
    return value
