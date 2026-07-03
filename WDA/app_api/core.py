from __future__ import annotations

import html
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DATA_CORE = Path(
    "/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r2/full_auto_workspace/"
    "data_core/wda_v0_2_r2.sqlite"
)
DEFAULT_SOURCE_WORKSPACE = Path(
    "/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r2/full_auto_workspace"
)
DEFAULT_RUNTIME_ROOT = Path(
    "/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r3_app_runtime"
)
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 18730

STATE_DIR = "state"
LOG_DIR = "logs"
REPORT_DIR = "reports"
DASHBOARD_DIR = "dashboard"

REPORT_SOURCES = [
    ("today_briefing", "今日简报", "reports/today_briefing.md", "今天先看什么。"),
    ("actions", "行动中心", "reports/todo_action_center.md", "需要推进、确认、回复的事项。"),
    ("contacts", "联系人雷达", "reports/contact_radar/index.md", "高频联系人与关系强度入口。"),
    ("work_handoff", "工作交接", "reports/work_handoff_summary.md", "交接线索与未闭环信息。"),
    ("work_info", "工作信息总结", "reports/work_information_summary.md", "工作信息结构化摘要。"),
    ("work_optimization", "工作优化", "reports/work_optimization.md", "可优化的协作方式。"),
    ("risks", "风险中心", "reports/risk_center.md", "阻塞、延期、投诉和风险线索。"),
    ("opportunities", "机会中心", "reports/opportunity_center.md", "可推进项目和合作线索。"),
    ("behavior", "个人行为优化", "reports/personal_behavior_review.md", "沟通节奏和行为模式复盘。"),
    ("evidence", "证据索引", "reports/evidence_index.md", "可追溯证据入口。"),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    mkdir(path.parent)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def utc_from_ms(value: int | None) -> str | None:
    if not value:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat()


def open_data_core(data_core_path: Path) -> sqlite3.Connection:
    if not data_core_path.exists():
        raise FileNotFoundError(f"Data Core not found: {data_core_path}")
    con = sqlite3.connect(f"file:{data_core_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def scalar(cur: sqlite3.Cursor, sql: str, default: Any = 0) -> Any:
    try:
        row = cur.execute(sql).fetchone()
    except sqlite3.Error:
        return default
    if row is None:
        return default
    return row[0]


def table_count(cur: sqlite3.Cursor, table_name: str) -> int:
    return int(scalar(cur, f'select count(*) from "{table_name}"', 0) or 0)


def integrity_check(cur: sqlite3.Cursor) -> str:
    try:
        return str(cur.execute("pragma integrity_check").fetchone()[0])
    except sqlite3.Error as exc:
        return f"error: {exc}"


def build_status(
    data_core_path: Path = DEFAULT_DATA_CORE,
    source_workspace: Path = DEFAULT_SOURCE_WORKSPACE,
    runtime_root: Path = DEFAULT_RUNTIME_ROOT,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    counts = {
        "message_count": 0,
        "conversation_count": 0,
        "contact_count": 0,
        "media_count": 0,
    }
    import_run: dict[str, Any] = {}
    integrity = "not_checked"

    try:
        con = open_data_core(data_core_path)
        cur = con.cursor()
        counts = {
            "message_count": table_count(cur, "messages"),
            "conversation_count": table_count(cur, "conversations"),
            "contact_count": table_count(cur, "contacts"),
            "media_count": table_count(cur, "media_index"),
        }
        integrity = integrity_check(cur)
        row = cur.execute(
            """
            select created_at, raw_gate_status, total_messages, total_conversations,
                   failed_conversations, first_timestamp_ms, last_timestamp_ms
            from import_runs
            order by created_at desc
            limit 1
            """
        ).fetchone()
        if row:
            import_run = dict(row)
        con.close()
    except (FileNotFoundError, sqlite3.Error) as exc:
        errors.append(str(exc))

    if integrity != "ok":
        warnings.append(f"SQLite integrity_check={integrity}")

    state = read_json(runtime_root / STATE_DIR / "status.json", {})
    last_run = read_json(runtime_root / STATE_DIR / "last_run.json", {})
    service = "ready" if not errors else "degraded"

    status = {
        "service": service,
        "app_version": "v0.2-R3",
        "runtime_root": str(runtime_root),
        "data_core_path": str(data_core_path),
        "source_workspace": str(source_workspace),
        "data_core_exists": data_core_path.exists(),
        "source_workspace_exists": source_workspace.exists(),
        "sqlite_integrity": integrity,
        "external_drive_required": False,
        "wechat_exporter_run_required": False,
        "cloud_upload_enabled": False,
        "last_export_at": import_run.get("created_at"),
        "last_import_at": import_run.get("created_at"),
        "last_analysis_at": state.get("last_analysis_at"),
        "last_report_build_at": state.get("last_report_build_at"),
        "last_run_id": last_run.get("run_id"),
        "last_run_status": last_run.get("status"),
        "next_scheduled_update_at": state.get("next_scheduled_update_at"),
        "raw_gate_status": import_run.get("raw_gate_status", "UNKNOWN"),
        "first_message_at": utc_from_ms(import_run.get("first_timestamp_ms")),
        "last_message_at": utc_from_ms(import_run.get("last_timestamp_ms")),
        "warnings": warnings,
        "errors": errors,
    }
    status.update(counts)
    return status


def build_dashboard_payload(status: dict[str, Any]) -> dict[str, Any]:
    messages = status.get("message_count", 0)
    conversations = status.get("conversation_count", 0)
    contacts = status.get("contact_count", 0)
    freshness = status.get("last_report_build_at") or status.get("last_import_at") or "尚未生成 R3 报告"
    return {
        "title": "WDA 今日工作台",
        "hero_label": "本地可用工作入口",
        "hero_summary": "先看行动、风险、机会和联系人，再进入证据索引。技术计数保留在系统状态页。",
        "primary_action": "立即更新",
        "freshness": freshness,
        "system_state": status.get("service", "unknown"),
        "top_sections": [
            {
                "id": "actions",
                "title": "行动中心",
                "summary": "集中查看需要确认、回复、推进、复盘的事项。",
                "href": "/reports/actions",
            },
            {
                "id": "risks",
                "title": "风险中心",
                "summary": "优先处理阻塞、延期、投诉、失败和争议线索。",
                "href": "/reports/risks",
            },
            {
                "id": "opportunities",
                "title": "机会中心",
                "summary": "识别可推进的项目、客户、方案和合作窗口。",
                "href": "/reports/opportunities",
            },
            {
                "id": "contacts",
                "title": "联系人雷达",
                "summary": "从联系人和群聊维度进入高价值关系。",
                "href": "/reports/contacts",
            },
            {
                "id": "work",
                "title": "工作交接",
                "summary": "把工作信息、交接点和未闭环事项拆开看。",
                "href": "/reports/work_handoff",
            },
            {
                "id": "behavior",
                "title": "个人行为优化",
                "summary": "复盘沟通节奏、响应模式和可模板化动作。",
                "href": "/reports/behavior",
            },
        ],
        "metrics": [
            {"label": "消息", "value": messages},
            {"label": "会话", "value": conversations},
            {"label": "联系人", "value": contacts},
            {"label": "媒体", "value": status.get("media_count", 0)},
        ],
        "warnings": status.get("warnings", []),
        "errors": status.get("errors", []),
    }


def runtime_dirs(runtime_root: Path) -> list[Path]:
    return [
        runtime_root / LOG_DIR,
        runtime_root / STATE_DIR,
        runtime_root / REPORT_DIR,
        runtime_root / DASHBOARD_DIR,
    ]


def initialize_runtime(
    runtime_root: Path = DEFAULT_RUNTIME_ROOT,
    data_core_path: Path = DEFAULT_DATA_CORE,
    source_workspace: Path = DEFAULT_SOURCE_WORKSPACE,
) -> dict[str, Any]:
    for path in runtime_dirs(runtime_root):
        mkdir(path)
    status = build_status(data_core_path, source_workspace, runtime_root)
    write_json(runtime_root / STATE_DIR / "status.json", status)
    return {
        "runtime_root": str(runtime_root),
        "status_path": str(runtime_root / STATE_DIR / "status.json"),
        "service": status["service"],
    }


def report_index(source_workspace: Path = DEFAULT_SOURCE_WORKSPACE) -> dict[str, Any]:
    reports = []
    for report_id, title, rel_path, summary in REPORT_SOURCES:
        source_path = source_workspace / rel_path
        reports.append(
            {
                "id": report_id,
                "title": title,
                "summary": summary,
                "source_path": str(source_path),
                "exists": source_path.exists(),
                "api_href": f"/api/reports/{report_id}",
                "page_href": f"/reports/{report_id}",
            }
        )
    return {
        "generated_at": now_iso(),
        "source_workspace": str(source_workspace),
        "reports": reports,
    }


def load_report(report_id: str, source_workspace: Path = DEFAULT_SOURCE_WORKSPACE) -> dict[str, Any]:
    index = report_index(source_workspace)
    match = next((item for item in index["reports"] if item["id"] == report_id), None)
    if not match:
        raise KeyError(f"Unknown report_id: {report_id}")
    source_path = Path(match["source_path"])
    content = source_path.read_text(encoding="utf-8") if source_path.exists() else ""
    return {**match, "content": content}


def write_report_runtime_files(runtime_root: Path, source_workspace: Path) -> dict[str, Any]:
    index = report_index(source_workspace)
    write_json(runtime_root / REPORT_DIR / "report_index.json", index)
    lines = ["# WDA v0.2-R3 本地报告入口", ""]
    for item in index["reports"]:
        state = "可用" if item["exists"] else "缺失"
        lines.append(f"- [{item['title']}]({item['source_path']})：{item['summary']}（{state}）")
    write_text(runtime_root / REPORT_DIR / "README.md", "\n".join(lines))
    return index


def dashboard_html(payload: dict[str, Any]) -> str:
    section_cards = "\n".join(
        f"""
        <a class=\"section-card\" href=\"{html.escape(item['href'])}\">
          <strong>{html.escape(item['title'])}</strong>
          <span>{html.escape(item['summary'])}</span>
        </a>
        """
        for item in payload["top_sections"]
    )
    metric_cards = "\n".join(
        f"""
        <div class=\"metric\">
          <span>{html.escape(str(item['label']))}</span>
          <strong>{html.escape(format_number(item['value']))}</strong>
        </div>
        """
        for item in payload["metrics"]
    )
    warnings = payload.get("warnings") or []
    errors = payload.get("errors") or []
    alerts = "\n".join(
        f"<li>{html.escape(str(item))}</li>" for item in [*warnings, *errors]
    ) or "<li>当前没有阻塞性告警。</li>"
    return f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{html.escape(payload['title'])}</title>
  <style>
    :root {{
      --bg: oklch(1 0 0);
      --surface: oklch(0.965 0.006 40);
      --panel: oklch(0.985 0.002 40);
      --ink: oklch(0.22 0.025 40);
      --muted: oklch(0.46 0.028 40);
      --primary: oklch(0.58 0.16 38);
      --accent: oklch(0.34 0.09 165);
      --border: oklch(0.88 0.012 40);
      --warning: oklch(0.62 0.16 65);
      font-family: -apple-system, BlinkMacSystemFont, \"SF Pro Text\", \"PingFang SC\", \"Hiragino Sans GB\", \"Microsoft YaHei\", sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--bg);
      min-width: 320px;
    }}
    .shell {{
      display: grid;
      grid-template-columns: 248px minmax(0, 1fr);
      min-height: 100vh;
    }}
    nav {{
      background: var(--surface);
      border-right: 1px solid var(--border);
      padding: 22px 18px;
    }}
    nav h1 {{
      font-size: 20px;
      margin: 0 0 18px;
      letter-spacing: 0;
    }}
    nav a {{
      display: flex;
      color: var(--ink);
      text-decoration: none;
      padding: 10px 12px;
      border-radius: 8px;
      margin: 3px 0;
      font-size: 14px;
    }}
    nav a:hover, nav a:focus {{ background: oklch(0.93 0.018 40); outline: none; }}
    main {{ padding: 28px; }}
    .topbar {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 18px;
      margin-bottom: 24px;
    }}
    .eyeline {{ color: var(--muted); font-size: 14px; margin: 0 0 8px; }}
    h2 {{ font-size: 28px; line-height: 1.2; margin: 0 0 10px; letter-spacing: 0; text-wrap: balance; }}
    .summary {{ margin: 0; max-width: 72ch; color: var(--muted); line-height: 1.7; }}
    button {{
      border: 0;
      background: var(--primary);
      color: white;
      border-radius: 8px;
      padding: 11px 16px;
      font-weight: 700;
      cursor: pointer;
      min-width: 112px;
    }}
    button:hover {{ filter: brightness(0.96); }}
    button:focus {{ outline: 3px solid oklch(0.78 0.08 38); outline-offset: 2px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 12px;
      margin: 18px 0 26px;
    }}
    .section-card, .metric, .status {{
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--panel);
      padding: 16px;
    }}
    .section-card {{
      display: flex;
      flex-direction: column;
      min-height: 118px;
      text-decoration: none;
      color: var(--ink);
      gap: 10px;
    }}
    .section-card:hover, .section-card:focus {{ border-color: var(--primary); outline: none; }}
    .section-card strong {{ font-size: 17px; }}
    .section-card span, .status, .metric span {{ color: var(--muted); line-height: 1.55; }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(128px, 1fr)); gap: 10px; }}
    .metric strong {{ display: block; font-size: 22px; margin-top: 6px; letter-spacing: 0; }}
    .status h3 {{ color: var(--ink); font-size: 16px; margin: 0 0 10px; }}
    .status ul {{ padding-left: 18px; margin: 0; }}
    @media (max-width: 760px) {{
      .shell {{ grid-template-columns: 1fr; }}
      nav {{ border-right: 0; border-bottom: 1px solid var(--border); }}
      main {{ padding: 20px; }}
      .topbar {{ flex-direction: column; }}
    }}
  </style>
</head>
<body>
  <div class=\"shell\">
    <nav aria-label=\"WDA navigation\">
      <h1>WDA</h1>
      <a href=\"/\">今日工作台</a>
      <a href=\"/reports/actions\">行动中心</a>
      <a href=\"/reports/contacts\">联系人雷达</a>
      <a href=\"/reports/work_handoff\">工作交接</a>
      <a href=\"/reports/risks\">风险中心</a>
      <a href=\"/reports/opportunities\">机会中心</a>
      <a href=\"/reports/behavior\">个人行为优化</a>
      <a href=\"/reports/evidence\">证据索引</a>
      <a href=\"/system\">系统状态</a>
    </nav>
    <main>
      <section class=\"topbar\">
        <div>
          <p class=\"eyeline\">{html.escape(payload['hero_label'])} · {html.escape(str(payload['freshness']))}</p>
          <h2>{html.escape(payload['title'])}</h2>
          <p class=\"summary\">{html.escape(payload['hero_summary'])}</p>
        </div>
        <button id=\"run-update\" type=\"button\">{html.escape(payload['primary_action'])}</button>
      </section>
      <section class=\"grid\" aria-label=\"主要入口\">{section_cards}</section>
      <section class=\"metrics\" aria-label=\"数据概况\">{metric_cards}</section>
      <section class=\"status\" aria-label=\"系统状态\">
        <h3>运行状态：{html.escape(str(payload['system_state']))}</h3>
        <ul>{alerts}</ul>
      </section>
    </main>
  </div>
  <script>
    const button = document.getElementById('run-update');
    button.addEventListener('click', async () => {{
      button.disabled = true;
      button.textContent = '更新中';
      try {{
        const response = await fetch('/api/update/run', {{ method: 'POST' }});
        if (!response.ok) throw new Error(await response.text());
        button.textContent = '已触发';
        setTimeout(() => location.reload(), 900);
      }} catch (error) {{
        button.textContent = '更新失败';
        alert(String(error));
      }} finally {{
        setTimeout(() => {{
          button.disabled = false;
          button.textContent = '{html.escape(payload['primary_action'])}';
        }}, 1800);
      }}
    }});
  </script>
</body>
</html>"""


def format_number(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def write_dashboard(runtime_root: Path, payload: dict[str, Any]) -> Path:
    dashboard_path = runtime_root / DASHBOARD_DIR / "index.html"
    write_text(dashboard_path, dashboard_html(payload))
    write_json(runtime_root / DASHBOARD_DIR / "dashboard_payload.json", payload)
    return dashboard_path


def run_update(
    runtime_root: Path = DEFAULT_RUNTIME_ROOT,
    data_core_path: Path = DEFAULT_DATA_CORE,
    source_workspace: Path = DEFAULT_SOURCE_WORKSPACE,
) -> dict[str, Any]:
    initialize_runtime(runtime_root, data_core_path, source_workspace)
    run_id = "r3-" + now_iso().replace(":", "").replace("+", "z")
    started_at = now_iso()
    run_record: dict[str, Any] = {
        "run_id": run_id,
        "started_at": started_at,
        "status": "running",
        "steps": [
            "read_data_core_status",
            "refresh_report_index",
            "render_dashboard_snapshot",
        ],
    }
    write_json(runtime_root / STATE_DIR / "last_run.json", run_record)

    status = build_status(data_core_path, source_workspace, runtime_root)
    report_data = write_report_runtime_files(runtime_root, source_workspace)
    status["last_analysis_at"] = now_iso()
    status["last_report_build_at"] = now_iso()
    write_json(runtime_root / STATE_DIR / "status.json", status)
    payload = build_dashboard_payload(status)
    dashboard_path = write_dashboard(runtime_root, payload)

    completed = {
        **run_record,
        "completed_at": now_iso(),
        "status": "completed",
        "message_count": status["message_count"],
        "conversation_count": status["conversation_count"],
        "contact_count": status["contact_count"],
        "report_count": len(report_data["reports"]),
        "dashboard_path": str(dashboard_path),
    }
    write_json(runtime_root / STATE_DIR / "last_run.json", completed)
    write_text(
        runtime_root / LOG_DIR / f"{run_id}.log",
        "\n".join(
            [
                f"run_id={run_id}",
                f"status=completed",
                f"message_count={status['message_count']}",
                f"dashboard_path={dashboard_path}",
            ]
        ),
    )
    return completed


def list_update_runs(runtime_root: Path = DEFAULT_RUNTIME_ROOT) -> list[dict[str, Any]]:
    last_run = read_json(runtime_root / STATE_DIR / "last_run.json", {})
    return [last_run] if last_run else []


def top_contacts(
    data_core_path: Path = DEFAULT_DATA_CORE,
    limit: int = 20,
) -> list[dict[str, Any]]:
    con = open_data_core(data_core_path)
    cur = con.cursor()
    rows = cur.execute(
        """
        select c.contact_id, c.display_name, c.contact_type, c.last_seen_ms,
               count(m.message_id) as message_count
        from contacts c
        left join messages m on m.sender_id = c.contact_id
        group by c.contact_id, c.display_name, c.contact_type, c.last_seen_ms
        order by message_count desc, c.last_seen_ms desc
        limit ?
        """,
        (limit,),
    ).fetchall()
    con.close()
    return [
        {
            "contact_id": row["contact_id"],
            "display_name": row["display_name"],
            "contact_type": row["contact_type"],
            "last_seen_at": utc_from_ms(row["last_seen_ms"]),
            "message_count": row["message_count"],
        }
        for row in rows
    ]


def contact_detail(contact_id: str, data_core_path: Path = DEFAULT_DATA_CORE) -> dict[str, Any]:
    con = open_data_core(data_core_path)
    cur = con.cursor()
    contact = cur.execute(
        """
        select contact_id, display_name, contact_type, first_seen_ms, last_seen_ms
        from contacts
        where contact_id = ?
        """,
        (contact_id,),
    ).fetchone()
    if contact is None:
        con.close()
        raise KeyError(f"Unknown contact_id: {contact_id}")
    message_count = cur.execute(
        "select count(*) from messages where sender_id = ?",
        (contact_id,),
    ).fetchone()[0]
    con.close()
    return {
        "contact_id": contact["contact_id"],
        "display_name": contact["display_name"],
        "contact_type": contact["contact_type"],
        "first_seen_at": utc_from_ms(contact["first_seen_ms"]),
        "last_seen_at": utc_from_ms(contact["last_seen_ms"]),
        "message_count": message_count,
    }


def launcher_url(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> str:
    return f"http://{host}:{port}/"


def environment() -> dict[str, str]:
    return {
        "WDA_R3_RUNTIME_ROOT": str(
            Path(os.environ.get("WDA_R3_RUNTIME_ROOT", str(DEFAULT_RUNTIME_ROOT)))
        ),
        "WDA_R3_DATA_CORE": str(
            Path(os.environ.get("WDA_R3_DATA_CORE", str(DEFAULT_DATA_CORE)))
        ),
        "WDA_R3_SOURCE_WORKSPACE": str(
            Path(os.environ.get("WDA_R3_SOURCE_WORKSPACE", str(DEFAULT_SOURCE_WORKSPACE)))
        ),
    }

