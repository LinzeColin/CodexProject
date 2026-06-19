from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from .config_setup import build_config_setup
from .web_search import search_provider_status


PROVIDER_LABELS = {
    "bing": "Bing Web Search",
    "serpapi": "SerpAPI Google",
    "google": "Google CSE",
}

BUSINESS_VALUE = {
    "bing": "快速补齐中文和全球公开网页解读，优先解决 5 份外部参考不足。",
    "serpapi": "补充 Google 公开索引，覆盖券商、律所、智库、媒体和长尾机构文章。",
    "google": "可控搜索范围和稳定 API 入口；适合长期自动化和跨国家扩展。",
}

IMPORT_SOURCE_HINT = {
    "bing": "/path/to/bing_search_api_key.txt",
    "serpapi": "/path/to/serpapi_api_key.txt",
    "google": "/path/to/google_search_api_key.txt",
}


def build_search_secret_intake(
    *,
    secure_dir: str | Path | None = None,
    search_secrets_file: str | Path | None = None,
) -> dict[str, Any]:
    setup = build_config_setup(secure_dir=secure_dir, search_secrets_path=search_secrets_file)
    search_path = str(search_secrets_file or setup["search_secrets_path"])
    providers = [_provider_row(item, search_path) for item in search_provider_status(search_path)]
    ready_count = sum(1 for row in providers if row["ready"])
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "search_secrets_path": _path_label(Path(search_path).expanduser()),
        "summary": {
            "total": len(providers),
            "ready_count": ready_count,
            "missing_count": sum(1 for row in providers if not row["ready"]),
            "p0_minimum_ready": ready_count >= 1,
            "p0_complete": ready_count == len(providers),
        },
        "providers": providers,
        "commands": {
            "bulk_import_keys": _bulk_import_command(search_path),
            "import_bing_key": _import_command("bing", search_path),
            "import_serpapi_key": _import_command("serpapi", search_path),
            "import_google_cse": _import_command("google", search_path),
            "offline_validate": (
                "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-validate "
                f"--search-secrets-file {_tilde(search_path)} --offline"
            ),
            "online_validate": (
                "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-validate "
                f"--search-secrets-file {_tilde(search_path)}"
            ),
        },
        "security_boundary": (
            "只展示搜索 provider 状态、缺失字段、导入命令和验证命令；不展示 API key、secret 或完整敏感路径。"
        ),
    }


def write_search_secret_intake_dashboard(
    path: str | Path,
    *,
    secure_dir: str | Path | None = None,
    search_secrets_file: str | Path | None = None,
    title: str = "搜索 API 接入清单",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    report = build_search_secret_intake(secure_dir=secure_dir, search_secrets_file=search_secrets_file)
    output.write_text(render_search_secret_intake_dashboard(report, title=title), encoding="utf-8")
    return str(output)


def render_search_secret_intake_dashboard(report: Mapping[str, Any], *, title: str = "搜索 API 接入清单") -> str:
    summary = report.get("summary") or {}
    providers = list(report.get("providers") or [])
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
    .page {{ max-width: 1280px; margin: 0 auto; padding: 24px 20px 52px; }}
    .hero {{ background: var(--panel); border-top: 5px solid var(--teal); border-bottom: 1px solid var(--line); padding: 18px 0 16px; }}
    .hero h1 {{ margin: 2px 0 8px; color: #063f4b; font-size: 28px; line-height: 1.22; }}
    .hero p {{ margin: 0; color: var(--muted); }}
    .metrics {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); border: 1px solid var(--line); background: var(--panel); margin: 14px 0; }}
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
    .ready {{ color: var(--green); font-weight: 700; }}
    .missing {{ color: var(--red); font-weight: 700; }}
    .partial {{ color: var(--amber); font-weight: 700; }}
    .cmd {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; overflow-wrap: anywhere; font-size: 11px; }}
    .pill {{ display: inline-block; border: 1px solid var(--line); background: var(--soft); padding: 2px 7px; margin: 2px 3px 2px 0; }}
    @media (max-width: 820px) {{
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      table {{ font-size: 11px; }}
      th, td {{ padding: 6px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <p>Search API Intake Checklist</p>
      <h1>{html.escape(title)}</h1>
      <p>生成时间：{html.escape(str(report.get("generated_at") or ""))}｜只展示接入状态和命令，不展示 API key。</p>
    </section>
    <section class="metrics">
      {_metric("Provider", summary.get("total", 0))}
      {_metric("Ready", summary.get("ready_count", 0))}
      {_metric("缺失", summary.get("missing_count", 0))}
      {_metric("P0 最小可用", "是" if summary.get("p0_minimum_ready") else "否")}
      {_metric("配置文件", report.get("search_secrets_path", ""))}
    </section>
    {_provider_table(providers)}
    {_commands_panel(report.get("commands") or {})}
    <article class="panel"><h2>安全与合规边界</h2><p>{html.escape(str(report.get("security_boundary") or ""))}</p></article>
  </main>
</body>
</html>
"""


def _provider_row(item: Mapping[str, Any], search_path: str) -> dict[str, Any]:
    provider = str(item.get("provider") or "")
    missing = []
    if not item.get("key_present"):
        required = list(item.get("required") or [])
        missing.extend(required[:1])
    if provider == "google" and not item.get("engine_present"):
        missing.append("GOOGLE_CSE_ID")
    state = "ready" if item.get("ready") else "missing"
    if provider == "google" and item.get("key_present") and not item.get("engine_present"):
        state = "partial"
    return {
        "provider": provider,
        "label": PROVIDER_LABELS.get(provider, provider),
        "ready": bool(item.get("ready")),
        "state": state,
        "status": item.get("status") or "",
        "missing_fields": missing,
        "business_value": BUSINESS_VALUE.get(provider, "补充外部公开搜索来源。"),
        "import_command": _import_command(provider, search_path),
        "offline_validation": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-validate "
            f"--search-secrets-file {_tilde(search_path)} --offline"
        ),
    }


def _import_command(provider: str, search_path: str) -> str:
    if provider == "google":
        return (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-secret-import "
            f"--provider google --value-file {IMPORT_SOURCE_HINT['google']} --engine-id-file /path/to/google_cse_id.txt "
            f"--search-secrets-file {_tilde(search_path)}"
        )
    return (
        "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-secret-import "
        f"--provider {provider} --value-file {IMPORT_SOURCE_HINT.get(provider, '/path/to/search_api_key.txt')} "
        f"--search-secrets-file {_tilde(search_path)}"
    )


def _bulk_import_command(search_path: str) -> str:
    return (
        "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-secret-bulk-import "
        f"--source-file /path/to/search_api_bundle.json --search-secrets-file {_tilde(search_path)}"
    )


def _provider_table(rows: list[Mapping[str, Any]]) -> str:
    body = []
    for row in rows:
        state = str(row.get("state") or "missing")
        body.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('label') or row.get('provider') or ''))}</td>"
            f"<td class=\"{html.escape(state)}\">{html.escape(str(row.get('status') or state))}</td>"
            f"<td>{_chips(row.get('missing_fields') or [])}</td>"
            f"<td>{html.escape(str(row.get('business_value') or ''))}</td>"
            f"<td class=\"cmd\">{html.escape(str(row.get('import_command') or ''))}</td>"
            f"<td class=\"cmd\">{html.escape(str(row.get('offline_validation') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel"><h2>Provider 接入清单</h2>'
        '<table><thead><tr><th>Provider</th><th>状态</th><th>缺失字段</th><th>业务价值</th><th>导入命令</th><th>离线验收</th></tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></article>'
    )


def _commands_panel(commands: Mapping[str, str]) -> str:
    rows = []
    for key, command in commands.items():
        rows.append("<tr>" f"<td>{html.escape(str(key))}</td>" f"<td class=\"cmd\">{html.escape(str(command))}</td>" "</tr>")
    return (
        '<article class="panel"><h2>全局命令</h2>'
        '<table><thead><tr><th>动作</th><th>命令</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></article>'
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
    value = str(path)
    home = str(Path.home())
    if value.startswith(home):
        value = "~" + value[len(home) :]
    if Path(value).name == "policy-search-secrets.json":
        return "~/.policy-intelligence/policy-search-secrets.json" if ".policy-intelligence/" in value else "<secure_dir>/policy-search-secrets.json"
    return value


def _tilde(path: str | Path) -> str:
    value = str(path)
    home = str(Path.home())
    if value.startswith(home):
        return "~" + value[len(home) :]
    if Path(value).name == "policy-search-secrets.json":
        return _path_label(Path(value))
    return value
