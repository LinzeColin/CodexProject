from __future__ import annotations

import html
import json
import plistlib
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


DEFAULT_LABEL = "com.source-registry.policy-report"
DEFAULT_SCHEDULE_TIMES = ["09:00", "21:00"]


def write_automation_scheduler_plan(
    output_dir: str | Path,
    *,
    workspace: str | Path = ".",
    data_dir: str | Path = "data",
    label: str = DEFAULT_LABEL,
    schedule_times: list[str] | None = None,
    timezone_name: str = "Australia/Sydney",
    entrypoint: str = "bash scripts/run_policy_report.sh",
    title: str = "每日两次政策报告调度计划",
) -> dict[str, Any]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    root = Path(workspace).resolve()
    data_root = Path(data_dir)
    times = schedule_times or DEFAULT_SCHEDULE_TIMES

    plist_path = out / f"{label}.plist"
    manifest_example_path = out / "scheduler_manifest.example.json"
    dashboard_path = out / "automation_scheduler_plan.html"
    plan_path = out / "automation_scheduler_plan.json"

    plist_payload = build_launchd_plist(
        workspace=root,
        data_dir=data_root,
        label=label,
        schedule_times=times,
        entrypoint=entrypoint,
    )
    plist_path.write_bytes(plistlib.dumps(plist_payload, sort_keys=False))

    manifest = build_scheduler_manifest(
        label=label,
        scheduler_type="launchd",
        schedule_times=times,
        timezone_name=timezone_name,
        entrypoint=entrypoint,
    )
    manifest_example_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "planned_not_installed",
        "label": label,
        "workspace": str(root),
        "schedule_times": times,
        "timezone": timezone_name,
        "entrypoint": entrypoint,
        "artifacts": {
            "launchd_plist": str(plist_path),
            "scheduler_manifest_example": str(manifest_example_path),
            "dashboard": str(dashboard_path),
            "plan_json": str(plan_path),
        },
        "install_steps": build_install_steps(label=label, plist_path=plist_path),
        "rollback_steps": build_rollback_steps(label=label),
        "security_boundary": (
            "该计划文件不保存 API key、cookie、session、账号密码或完整 secret 内容；"
            "只记录调度类型、入口脚本、运行时间和安装/回滚步骤。"
        ),
    }
    plan_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    dashboard_path.write_text(render_scheduler_plan_dashboard(result, title=title), encoding="utf-8")
    return result


def build_launchd_plist(
    *,
    workspace: Path,
    data_dir: Path,
    label: str,
    schedule_times: list[str],
    entrypoint: str,
) -> dict[str, Any]:
    command = f"cd {shlex.quote(str(workspace))} && {entrypoint}"
    log_dir = workspace / data_dir / "run_logs"
    return {
        "Label": label,
        "ProgramArguments": ["/bin/bash", "-lc", command],
        "WorkingDirectory": str(workspace),
        "StartCalendarInterval": [_calendar_interval(item) for item in schedule_times],
        "StandardOutPath": str(log_dir / "launchd.out.log"),
        "StandardErrorPath": str(log_dir / "launchd.err.log"),
        "RunAtLoad": False,
    }


def build_scheduler_manifest(
    *,
    label: str,
    scheduler_type: str,
    schedule_times: list[str],
    timezone_name: str,
    entrypoint: str,
) -> dict[str, Any]:
    return {
        "enabled": True,
        "scheduler_type": scheduler_type,
        "label": label,
        "entrypoint": entrypoint,
        "schedule_times": schedule_times,
        "timezone": timezone_name,
        "installed_plist": f"~/Library/LaunchAgents/{label}.plist",
        "notes": "Only create data/automation/scheduler.json after launchd or another scheduler is actually installed.",
    }


def build_install_steps(*, label: str, plist_path: Path) -> list[str]:
    target = f"~/Library/LaunchAgents/{label}.plist"
    return [
        "mkdir -p data/run_logs data/automation",
        "mkdir -p ~/Library/LaunchAgents",
        f"cp {shlex.quote(str(plist_path))} {target}",
        f"launchctl bootstrap gui/$(id -u) {target}",
        f"launchctl enable gui/$(id -u)/{label}",
        f"launchctl print gui/$(id -u)/{label}",
        "cp reports/scheduler_manifest.example.json data/automation/scheduler.json",
        "python3 -m source_registry --db data/source_registry.sqlite automation-readiness --content-db data/policy_documents.sqlite --data-dir data --schedule-time 09:00 --schedule-time 21:00 --json",
    ]


def build_rollback_steps(*, label: str) -> list[str]:
    target = f"~/Library/LaunchAgents/{label}.plist"
    return [
        f"launchctl bootout gui/$(id -u) {target}",
        f"rm {target}",
        "rm data/automation/scheduler.json",
    ]


def render_scheduler_plan_dashboard(report: Mapping[str, Any], *, title: str) -> str:
    artifacts = report.get("artifacts") or {}
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
      --amber: #9a4a13;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--paper);
      font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", Arial, sans-serif;
      line-height: 1.55;
    }}
    .page {{ max-width: 1120px; margin: 0 auto; padding: 24px 20px 52px; }}
    .hero {{ background: var(--panel); border-top: 5px solid var(--teal); border-bottom: 1px solid var(--line); padding: 18px 0 16px; }}
    .hero h1 {{ margin: 2px 0 8px; color: #063f4b; font-size: 28px; line-height: 1.22; }}
    .hero p, .note {{ margin: 0; color: var(--muted); }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); border: 1px solid var(--line); background: var(--panel); margin: 14px 0; }}
    .metric {{ padding: 10px 12px; border-right: 1px solid var(--line); min-height: 70px; }}
    .metric:last-child {{ border-right: 0; }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; }}
    .metric strong {{ display: block; color: #063f4b; font-size: 18px; overflow-wrap: anywhere; }}
    .panel {{ background: var(--panel); border: 1px solid var(--line); padding: 13px 14px; margin-top: 12px; }}
    .panel h2 {{ margin: 0 0 10px; color: #063f4b; font-size: 16px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ border: 1px solid var(--line); padding: 7px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf4f7; color: #063f4b; }}
    .cmd {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; overflow-wrap: anywhere; }}
    .warn {{ color: var(--amber); font-weight: 700; }}
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
      <p>Launchd Scheduler Plan</p>
      <h1>{html.escape(title)}</h1>
      <p>状态：<span class="warn">{html.escape(str(report.get("status") or ""))}</span>。该页面是安装计划，不代表调度已经启用。</p>
    </section>
    <section class="metrics">
      {_metric("Label", report.get("label", ""))}
      {_metric("运行时间", ", ".join(str(item) for item in report.get("schedule_times") or []))}
      {_metric("时区", report.get("timezone", ""))}
      {_metric("入口", report.get("entrypoint", ""))}
    </section>
    {_path_table(artifacts)}
    {_steps_table("安装步骤", list(report.get("install_steps") or []))}
    {_steps_table("回滚步骤", list(report.get("rollback_steps") or []))}
    <article class="panel"><h2>安全边界</h2><p class="note">{html.escape(str(report.get("security_boundary") or ""))}</p></article>
  </main>
</body>
</html>
"""


def _calendar_interval(value: str) -> dict[str, int]:
    try:
        hour_text, minute_text = str(value).split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
    except (ValueError, TypeError):
        raise ValueError(f"invalid schedule time: {value!r}") from None
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError(f"invalid schedule time: {value!r}")
    return {"Hour": hour, "Minute": minute}


def _metric(label: str, value: object) -> str:
    return (
        '<article class="metric">'
        f"<span>{html.escape(str(label))}</span>"
        f"<strong>{html.escape(str(value))}</strong>"
        "</article>"
    )


def _path_table(paths: Mapping[str, Any]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(key))}</td>"
        f"<td class=\"cmd\">{html.escape(str(value))}</td>"
        "</tr>"
        for key, value in paths.items()
    )
    return (
        '<article class="panel"><h2>生成文件</h2>'
        '<table><thead><tr><th>文件</th><th>路径</th></tr></thead>'
        f"<tbody>{rows}</tbody></table></article>"
    )


def _steps_table(title: str, steps: list[str]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{index}</td>"
        f"<td class=\"cmd\">{html.escape(step)}</td>"
        "</tr>"
        for index, step in enumerate(steps, start=1)
    )
    return (
        f'<article class="panel"><h2>{html.escape(title)}</h2>'
        '<table><thead><tr><th>#</th><th>命令</th></tr></thead>'
        f"<tbody>{rows}</tbody></table></article>"
    )
