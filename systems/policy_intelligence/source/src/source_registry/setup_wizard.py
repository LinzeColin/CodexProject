from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from .config_setup import build_config_setup
from .platform_coverage import build_platform_coverage
from .readiness import build_readiness_status


def build_setup_wizard(
    *,
    content_conn=None,
    secure_dir: str | Path | None = None,
    search_secrets_file: str | Path | None = None,
    platform_auth_file: str | Path | None = None,
    interpretation_source_file: str | Path | None = "config/interpretation_sources.json",
) -> dict[str, Any]:
    setup = build_config_setup(secure_dir=secure_dir)
    effective_search_file = str(search_secrets_file or setup["search_secrets_path"])
    effective_auth_file = str(platform_auth_file or setup["platform_auth_path"])
    readiness = build_readiness_status(
        content_conn=content_conn,
        search_secrets_file=effective_search_file,
        platform_auth_file=effective_auth_file,
        interpretation_source_file=interpretation_source_file,
    )
    coverage = build_platform_coverage(
        content_conn=content_conn,
        search_secrets_file=effective_search_file,
        platform_auth_file=effective_auth_file,
        interpretation_source_file=interpretation_source_file,
    )
    templates_ready = _templates_ready(effective_search_file, effective_auth_file)
    steps = _steps(readiness, coverage, templates_ready=templates_ready)
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "overall_status": readiness.get("overall_status"),
        "setup_paths": {
            "secure_dir": _tilde(setup["secure_dir"]),
            "search_secrets_path": _tilde(effective_search_file),
            "platform_auth_path": _tilde(effective_auth_file),
            "search_api_bundle_example_path": _tilde(setup["search_api_bundle_example_path"]),
            "platform_auth_bundle_example_path": _tilde(setup["platform_auth_bundle_example_path"]),
            "cookie_dir": _tilde(setup["cookie_dir"]),
        },
        "commands": _commands(_tilde(effective_search_file), _tilde(effective_auth_file)),
        "readiness_summary": {
            "search_api_ready": int((readiness.get("search_api") or {}).get("ready_count") or 0),
            "platform_auth_configured": int((readiness.get("platform_auth") or {}).get("configured_count") or 0),
            "platform_auth_available": int((readiness.get("platform_auth") or {}).get("available_count") or 0),
            "chinese_search_entries": int((readiness.get("chinese_search_entries") or {}).get("configured_count") or 0),
            "pending_gaps": int((readiness.get("external_reference_gaps") or {}).get("pending_count") or 0),
        },
        "coverage_summary": coverage.get("summary") or {},
        "next_actions": readiness.get("next_actions") or [],
        "input_matrix": _input_matrix(),
        "steps": steps,
        "security_boundary": (
            "不要在聊天中发送账号密码、API key 或 cookie 内容；"
            "本向导只生成本地路径、命令和状态，不绕过验证码、付费墙或访问控制。"
        ),
    }


def write_setup_wizard_dashboard(
    path: str | Path,
    *,
    content_conn=None,
    secure_dir: str | Path | None = None,
    search_secrets_file: str | Path | None = None,
    platform_auth_file: str | Path | None = None,
    interpretation_source_file: str | Path | None = "config/interpretation_sources.json",
    title: str = "本地接入验收向导",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    wizard = build_setup_wizard(
        content_conn=content_conn,
        secure_dir=secure_dir,
        search_secrets_file=search_secrets_file,
        platform_auth_file=platform_auth_file,
        interpretation_source_file=interpretation_source_file,
    )
    output.write_text(render_setup_wizard_dashboard(wizard, title=title), encoding="utf-8")
    return str(output)


def render_setup_wizard_dashboard(
    wizard: Mapping[str, Any],
    *,
    title: str = "本地接入验收向导",
) -> str:
    summary = wizard.get("readiness_summary") or {}
    coverage = wizard.get("coverage_summary") or {}
    commands = wizard.get("commands") or {}
    steps = list(wizard.get("steps") or [])
    input_matrix = list(wizard.get("input_matrix") or [])
    generated_at = str(wizard.get("generated_at") or "")
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
    .steps {{ display: grid; gap: 10px; }}
    .step {{ border: 1px solid var(--line); background: var(--soft); padding: 10px 12px; display: grid; grid-template-columns: 42px 1fr 150px; gap: 10px; align-items: start; }}
    .num {{ width: 30px; height: 30px; border: 1px solid var(--line); display: inline-flex; align-items: center; justify-content: center; font-weight: 700; background: white; }}
    .badge {{ display: inline-block; padding: 3px 8px; border: 1px solid var(--line); background: #fff; font-size: 12px; font-weight: 700; text-align: center; }}
    .priority {{ display: inline-block; min-width: 28px; text-align: center; font-weight: 800; color: #063f4b; }}
    .done {{ color: var(--green); }}
    .todo {{ color: var(--amber); }}
    .blocked {{ color: var(--red); }}
    .cmd {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; overflow-wrap: anywhere; font-size: 11px; }}
    button {{ border: 1px solid #bed7df; background: #edf4f7; color: #063f4b; border-radius: 6px; min-height: 32px; padding: 6px 10px; font: inherit; font-size: 12px; font-weight: 700; cursor: pointer; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ border: 1px solid var(--line); padding: 7px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf4f7; color: #063f4b; }}
    td {{ background: var(--panel); }}
    @media (max-width: 920px) {{
      .metrics {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
      .panel {{ grid-column: 1 / -1; }}
      .step {{ grid-template-columns: 38px 1fr; }}
      .step .badge {{ grid-column: 2; width: max-content; }}
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
      <p>Local Secrets And Platform Authorization Onboarding</p>
      <h1>{html.escape(title)}</h1>
      <p>生成时间：{html.escape(generated_at)}｜该页面不展示 API key、cookie、账号密码或本地文件内容。</p>
    </section>
    <section class="metrics">
      {_metric("搜索 API ready", summary.get("search_api_ready", 0))}
      {_metric("授权路径配置", summary.get("platform_auth_configured", 0))}
      {_metric("平台授权可用", summary.get("platform_auth_available", 0))}
      {_metric("中文搜索入口", summary.get("chinese_search_entries", 0))}
      {_metric("平台 blocked", coverage.get("blocked", 0))}
      {_metric("待处理缺口", summary.get("pending_gaps", 0))}
    </section>
    <section class="grid">
      <article class="panel wide">
        <h2>接入步骤</h2>
        <section class="steps">
          {"".join(_step_card(step) for step in steps)}
        </section>
      </article>
      {_input_matrix_panel(input_matrix)}
      {_commands_panel(commands)}
      {_paths_panel(wizard.get("setup_paths") or {})}
      {_next_actions_panel(wizard.get("next_actions") or [])}
      {_security_panel(str(wizard.get("security_boundary") or ""))}
    </section>
  </main>
  <script>
    document.querySelectorAll('[data-copy]').forEach((button) => {{
      button.addEventListener('click', () => {{
        const target = document.getElementById(button.getAttribute('data-copy'));
        const value = target ? target.textContent : '';
        if (navigator.clipboard && navigator.clipboard.writeText) {{
          navigator.clipboard.writeText(value);
        }}
      }});
    }});
  </script>
</body>
</html>
"""


def _steps(readiness: Mapping[str, Any], coverage: Mapping[str, Any], *, templates_ready: bool = False) -> list[dict[str, Any]]:
    search_ready = int((readiness.get("search_api") or {}).get("ready_count") or 0)
    auth_available = int((readiness.get("platform_auth") or {}).get("available_count") or 0)
    pending_gaps = int((readiness.get("external_reference_gaps") or {}).get("pending_count") or 0)
    coverage_summary = coverage.get("summary") or {}
    blocked = int(coverage_summary.get("blocked") or 0)
    return [
        {
            "number": 1,
            "title": "生成本地模板",
            "status": "done" if templates_ready else "todo",
            "body": "创建搜索 key 模板、平台授权模板和 cookie/session 目录；模板为空字段，不包含密码。",
            "command_key": "setup_config",
        },
        {
            "number": 2,
            "title": "补搜索 API",
            "status": "done" if search_ready else "blocked",
            "body": f"当前 ready {search_ready}/3；优先用搜索 API 接入清单或 bulk import 一次性补 SerpAPI、Bing、Google CSE。",
            "command_key": "search_intake",
        },
        {
            "number": 3,
            "title": "补平台授权",
            "status": "done" if auth_available else "blocked",
            "body": f"当前可用授权 {auth_available}/8；先看平台授权接入清单，再优先放入 B站本地登录态文件。",
            "command_key": "auth_intake",
        },
        {
            "number": 4,
            "title": "体检本地文件",
            "status": "todo",
            "body": "检查 key/auth 文件格式、空值、占位符、权限、cookie 文件是否为空或过旧；不输出 secret 内容。",
            "command_key": "credential_doctor",
        },
        {
            "number": 5,
            "title": "验证平台授权连通性",
            "status": "todo",
            "body": "默认离线检查授权文件；如需在线验证，手动加 --online，目前只对 B站做最小登录态验证。",
            "command_key": "platform_auth_validate",
        },
        {
            "number": 6,
            "title": "验证搜索 API 连通性",
            "status": "todo",
            "body": "补 key 后发起最小公开搜索请求，确认 provider 可用；在线模式会消耗少量 API 配额。",
            "command_key": "search_validate",
        },
        {
            "number": 7,
            "title": "验证 readiness",
            "status": "done" if search_ready or auth_available else "todo",
            "body": "验证 key 是否存在、授权文件是否可读、中文搜索入口是否启用；不输出 secret 内容。",
            "command_key": "readiness",
        },
        {
            "number": 8,
            "title": "刷新平台覆盖矩阵",
            "status": "done" if blocked == 0 else "todo",
            "body": f"当前 blocked {blocked}；用于判断是缺 key、缺授权，还是缺平台解析器。",
            "command_key": "platform_coverage",
        },
        {
            "number": 9,
            "title": "检查平台解析器能力",
            "status": "todo",
            "body": "确认 B站、抖音、快手、微博、知乎、公众号、小红书、头条的正文、作者页、评论、字幕、弹幕和互动数据解析状态。",
            "command_key": "platform_parsers",
        },
        {
            "number": 10,
            "title": "验收平台解析器前置条件",
            "status": "todo",
            "body": "把平台 parser 台账、搜索 API key 和本地授权状态合并验收，判断下一步是补 key、补授权还是实现详情解析器。",
            "command_key": "platform_parser_validate",
        },
        {
            "number": 11,
            "title": "验收平台解析样本",
            "status": "todo",
            "body": "只读本地已入库解读样本，确认 parser 是否真正产出正文、视频、作者、互动和可计入参考证据。",
            "command_key": "platform_parser_samples",
        },
        {
            "number": 12,
            "title": "检查抓取策略",
            "status": "todo",
            "body": "确认来源抓取前具备 robots/nofollow、限速、重试、超时、快照保留和受限页面处理规则。",
            "command_key": "crawl_policy",
        },
        {
            "number": 13,
            "title": "检查附件解析能力",
            "status": "todo",
            "body": "确认 PDF、DOCX、XLSX、OCR、Tika/GROBID 可选服务能力；无法解析的附件进入可审计缺口，不生成空白正文。",
            "command_key": "attachment_parsers",
        },
        {
            "number": 14,
            "title": "复核缺口并运行报告",
            "status": "done" if pending_gaps == 0 else "todo",
            "body": f"当前 pending gaps {pending_gaps}；先用 gap dashboard dry-run，再运行报告流水线。",
            "command_key": "gap_dashboard",
        },
    ]


def _input_matrix() -> list[dict[str, str]]:
    return [
        {
            "priority": "P0",
            "target": "搜索 API",
            "provide": "SerpAPI / Bing / Google CSE 的本地 key 文件，或一个 search_api_bundle.json",
            "verify": "search-validate 通过至少 1 个 provider",
            "value": "解决外部研究解读不足；优先补齐每份报告 5 份以上参考。",
        },
        {
            "priority": "P0",
            "target": "B站",
            "provide": "本地登录态文件路径，或 platform_auth_bundle.json；不要在聊天中发送内容",
            "verify": "platform-auth-validate --online 登录态通过",
            "value": "获取公开视频详情、字幕、解读视频线索；补足外部平台覆盖。",
        },
        {
            "priority": "P1",
            "target": "微信公众号 / 知乎 / 微博",
            "provide": "本地会话或 cookie 路径，以及验证页面标记",
            "verify": "授权文件存在，在线验证未触发登录或安全验证",
            "value": "提高政策研究深度：专家文章、官方媒体解读、机构观点。",
        },
        {
            "priority": "P2",
            "target": "抖音 / 快手 / 小红书 / 头条",
            "provide": "本地授权路径；按平台限速和合规边界接入",
            "verify": "可访问公开内容，验证码/付费墙自动记录为缺口",
            "value": "扩展短视频、社交讨论和传播热度信号；不作为政府原文权威。",
        },
    ]


def _commands(search_path: str, auth_path: str) -> dict[str, str]:
    return {
        "setup_config": "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite setup-config",
        "edit_search": f"open {search_path}",
        "bulk_import_search": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-secret-bulk-import "
            f"--source-file /path/to/search_api_bundle.json --search-secrets-file {search_path}"
        ),
        "import_bing_key": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-secret-import "
            f"--provider bing --value-file /path/to/bing_search_api_key.txt --search-secrets-file {search_path}"
        ),
        "import_serpapi_key": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-secret-import "
            f"--provider serpapi --value-file /path/to/serpapi_api_key.txt --search-secrets-file {search_path}"
        ),
        "import_google_cse": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-secret-import "
            f"--provider google --value-file /path/to/google_search_api_key.txt --engine-id-file /path/to/google_cse_id.txt --search-secrets-file {search_path}"
        ),
        "search_intake": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-secret-intake "
            f"--search-secrets-file {search_path}"
        ),
        "edit_auth": f"open {auth_path}",
        "auth_intake": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-intake "
            f"--platform-auth-file {auth_path}"
        ),
        "bundle_import_cookies": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-bundle-import "
            f"--source-file /path/to/platform_auth_bundle.json --platform-auth-file {auth_path}"
        ),
        "bulk_import_cookies": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-bulk-import "
            f"--source-dir /path/to/exported_cookie_dir --platform-auth-file {auth_path}"
        ),
        "import_chrome_session_reference": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-session-import "
            f"--platform bilibili --session-file /path/to/chrome_profile_or_storage_state --platform-auth-file {auth_path}"
        ),
        "import_bilibili_cookie": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-import "
            f"--platform bilibili --source-file /path/to/exported_bilibili_cookie.txt --platform-auth-file {auth_path}"
        ),
        "credential_doctor": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite credential-doctor "
            f"--search-secrets-file {search_path} --platform-auth-file {auth_path}"
        ),
        "platform_auth_validate": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-validate "
            f"--platform-auth-file {auth_path}"
        ),
        "search_validate": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-validate "
            f"--search-secrets-file {search_path}"
        ),
        "readiness": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite readiness "
            f"--search-secrets-file {search_path} --platform-auth-file {auth_path}"
        ),
        "access_readiness": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite access-readiness "
            f"--search-secrets-file {search_path} --platform-auth-file {auth_path}"
        ),
        "platform_coverage": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-coverage "
            f"--search-secrets-file {search_path} --platform-auth-file {auth_path}"
        ),
        "platform_parsers": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-parsers "
            "--parser-file config/platform_parsers.json"
        ),
        "platform_parser_validate": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-parser-validate "
            f"--parser-file config/platform_parsers.json --search-secrets-file {search_path} --platform-auth-file {auth_path}"
        ),
        "platform_parser_samples": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-parser-samples "
            "--content-db data/policy_documents.sqlite --parser-file config/platform_parsers.json"
        ),
        "crawl_policy": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite crawl-policy "
            "--policy-file config/crawl_policies.json"
        ),
        "attachment_parsers": (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite attachment-parsers "
            "--parser-file config/attachment_parsers.json"
        ),
        "gap_dashboard": "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite gap-dashboard",
        "run_pipeline": (
            f"SEARCH_SECRETS_FILE={search_path} PLATFORM_AUTH_FILE={auth_path} "
            "bash scripts/run_policy_report.sh"
        ),
    }


def _metric(label: str, value: object) -> str:
    return (
        '<article class="metric">'
        f"<span>{html.escape(str(label))}</span>"
        f"<strong>{html.escape(str(value))}</strong>"
        "</article>"
    )


def _step_card(step: Mapping[str, Any]) -> str:
    status = str(step.get("status") or "todo")
    return (
        '<article class="step">'
        f'<span class="num">{html.escape(str(step.get("number") or ""))}</span>'
        '<div>'
        f'<strong>{html.escape(str(step.get("title") or ""))}</strong>'
        f'<p class="note">{html.escape(str(step.get("body") or ""))}</p>'
        f'<p class="cmd">命令键：{html.escape(str(step.get("command_key") or ""))}</p>'
        '</div>'
        f'<span class="badge {html.escape(status)}">{html.escape(status)}</span>'
        '</article>'
    )


def _input_matrix_panel(rows: list[Mapping[str, str]]) -> str:
    if not rows:
        return ""
    rendered = []
    for row in rows:
        rendered.append(
            "<tr>"
            f"<td><span class=\"priority\">{html.escape(str(row.get('priority') or ''))}</span></td>"
            f"<td>{html.escape(str(row.get('target') or ''))}</td>"
            f"<td>{html.escape(str(row.get('provide') or ''))}</td>"
            f"<td>{html.escape(str(row.get('verify') or ''))}</td>"
            f"<td>{html.escape(str(row.get('value') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>接入优先级矩阵</h2>'
        '<table><thead><tr><th>优先级</th><th>对象</th><th>你需要提供</th><th>验收标准</th><th>业务价值</th></tr></thead>'
        f'<tbody>{"".join(rendered)}</tbody></table>'
        '<p class="note">矩阵只保留会直接提升报告质量的输入；账号密码、API key 和本地授权内容不进入页面。</p>'
        '</article>'
    )


def _commands_panel(commands: Mapping[str, str]) -> str:
    rows = []
    for idx, (key, command) in enumerate(commands.items()):
        element_id = f"cmd-{idx}"
        rows.append(
            "<tr>"
            f"<td>{html.escape(key)}</td>"
            f'<td class="cmd" id="{element_id}">{html.escape(command)}</td>'
            f'<td><button type="button" data-copy="{element_id}">复制</button></td>'
            "</tr>"
        )
    return (
        '<article class="panel wide"><h2>命令矩阵</h2>'
        '<table><thead><tr><th>步骤</th><th>命令</th><th>操作</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></article>'
    )


def _paths_panel(paths: Mapping[str, str]) -> str:
    rows = []
    for label, value in paths.items():
        rows.append(f"<tr><td>{html.escape(label)}</td><td class=\"cmd\">{html.escape(str(value))}</td></tr>")
    return (
        '<article class="panel"><h2>本地文件位置</h2>'
        '<table><tbody>'
        f'{"".join(rows)}'
        '</tbody></table>'
        '<p class="note">这些是本地路径；文件内容不进入报告、日志或聊天。</p></article>'
    )


def _next_actions_panel(actions: list[Mapping[str, Any]]) -> str:
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
        f'<tbody>{"".join(rows) if rows else "<tr><td colspan=\"3\">暂无动作。</td></tr>"}</tbody></table></article>'
    )


def _security_panel(text: str) -> str:
    return (
        '<article class="panel wide"><h2>安全与合规边界</h2>'
        f'<p>{html.escape(text)}</p>'
        '<p class="note">如果平台要求验证码、会员、付费墙或显式禁止自动化访问，系统记录缺口，不尝试绕过。</p>'
        "</article>"
    )


def _tilde(path: str | Path) -> str:
    value = str(path)
    home = str(Path.home())
    if value.startswith(home):
        return "~" + value[len(home) :]
    return value


def _templates_ready(search_file: str | Path, auth_file: str | Path) -> bool:
    return Path(search_file).expanduser().exists() and Path(auth_file).expanduser().exists()
