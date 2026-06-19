from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


VALID_STATUSES = {"running", "completed", "failed", "skipped"}


def record_automation_step(
    *,
    data_dir: str | Path,
    run_id: str,
    step_key: str,
    step_label: str,
    status: str,
    exit_code: int | None = None,
    error_summary: str | None = None,
) -> dict[str, Any]:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid automation step status: {status}")
    root = Path(data_dir) / "automation"
    run_path = root / "runs" / f"{run_id}.json"
    latest_path = root / "latest_run.json"
    root.mkdir(parents=True, exist_ok=True)
    run_path.parent.mkdir(parents=True, exist_ok=True)
    payload = _load_payload(run_path, run_id)
    now = _utc_now()
    payload["updated_at"] = now
    step = _step(payload, step_key, step_label)
    step["label"] = step_label
    step["status"] = status
    step["updated_at"] = now
    if status == "running" and not step.get("started_at"):
        step["started_at"] = now
    if status in {"completed", "failed", "skipped"}:
        step["completed_at"] = now
        step["duration_seconds"] = _duration_seconds(step.get("started_at"), now)
    if exit_code is not None:
        step["exit_code"] = int(exit_code)
    if error_summary:
        step["error_summary"] = _safe_text(error_summary, limit=500)
    payload["status"] = _overall_status(payload["steps"])
    payload["summary"] = _summary(payload["steps"])
    _write_json(run_path, payload)
    _write_json(latest_path, payload)
    return {**payload, "run_path": str(run_path), "latest_path": str(latest_path)}


def load_latest_automation_run(data_dir: str | Path) -> dict[str, Any]:
    path = Path(data_dir) / "automation" / "latest_run.json"
    if not path.exists():
        return {
            "run_id": "",
            "status": "not_started",
            "steps": [],
            "summary": {"step_count": 0, "completed_count": 0, "failed_count": 0, "running_count": 0},
        }
    return json.loads(path.read_text(encoding="utf-8"))


def write_automation_dashboard(
    path: str | Path,
    *,
    data_dir: str | Path = "data",
    title: str = "自动化运行状态 dashboard",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = load_latest_automation_run(data_dir)
    output.write_text(render_automation_dashboard(payload, title=title), encoding="utf-8")
    return str(output)


def render_automation_dashboard(payload: Mapping[str, Any], *, title: str = "自动化运行状态 dashboard") -> str:
    summary = payload.get("summary") or {}
    steps = list(payload.get("steps") or [])
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
    .metrics {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); border: 1px solid var(--line); background: var(--panel); margin: 14px 0; }}
    .metric {{ padding: 10px 12px; border-right: 1px solid var(--line); min-height: 70px; }}
    .metric:last-child {{ border-right: 0; }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; }}
    .metric strong {{ display: block; color: #063f4b; font-size: 22px; }}
    .panel {{ background: var(--panel); border: 1px solid var(--line); padding: 13px 14px; margin-top: 12px; }}
    .panel h2 {{ margin: 0 0 10px; color: #063f4b; font-size: 16px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ border: 1px solid var(--line); padding: 7px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf4f7; color: #063f4b; }}
    td {{ background: var(--panel); }}
    .completed {{ color: var(--green); font-weight: 700; }}
    .running, .skipped {{ color: var(--amber); font-weight: 700; }}
    .failed {{ color: var(--red); font-weight: 700; }}
    .note {{ color: var(--muted); font-size: 12px; }}
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
      <p>Automation Step Run Status</p>
      <h1>{html.escape(title)}</h1>
      <p>运行编号：{html.escape(str(payload.get("run_id") or "-"))}｜状态：{html.escape(str(payload.get("status") or "-"))}｜更新时间：{html.escape(str(payload.get("updated_at") or ""))}</p>
    </section>
    <section class="metrics">
      {_metric("步骤总数", summary.get("step_count", 0))}
      {_metric("完成", summary.get("completed_count", 0))}
      {_metric("失败", summary.get("failed_count", 0))}
      {_metric("运行中", summary.get("running_count", 0))}
      {_metric("总耗时秒", summary.get("duration_seconds", 0))}
    </section>
    {_step_table(steps)}
    <article class="panel"><h2>合规边界</h2><p class="note">该页面只记录步骤名、状态、耗时和错误摘要；不记录命令参数中的 API key、cookie、账号密码或完整 secret 文件内容。</p></article>
  </main>
</body>
</html>
"""


def _load_payload(path: Path, run_id: str) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    now = _utc_now()
    return {
        "run_id": run_id,
        "status": "running",
        "started_at": now,
        "updated_at": now,
        "steps": [],
        "summary": {"step_count": 0, "completed_count": 0, "failed_count": 0, "running_count": 0},
    }


def _step(payload: dict[str, Any], step_key: str, step_label: str) -> dict[str, Any]:
    for step in payload["steps"]:
        if step.get("step_key") == step_key:
            return step
    step = {
        "step_key": step_key,
        "label": step_label,
        "status": "running",
        "started_at": "",
        "completed_at": "",
        "duration_seconds": 0,
        "exit_code": None,
        "error_summary": "",
    }
    payload["steps"].append(step)
    return step


def _overall_status(steps: list[Mapping[str, Any]]) -> str:
    if any(step.get("status") == "failed" for step in steps):
        return "failed"
    if steps and all(step.get("status") in {"completed", "skipped"} for step in steps):
        return "completed"
    return "running"


def _summary(steps: list[Mapping[str, Any]]) -> dict[str, int]:
    durations = [int(step.get("duration_seconds") or 0) for step in steps]
    return {
        "step_count": len(steps),
        "completed_count": sum(1 for step in steps if step.get("status") == "completed"),
        "failed_count": sum(1 for step in steps if step.get("status") == "failed"),
        "running_count": sum(1 for step in steps if step.get("status") == "running"),
        "skipped_count": sum(1 for step in steps if step.get("status") == "skipped"),
        "duration_seconds": sum(durations),
    }


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _duration_seconds(start: Any, end: str) -> int:
    if not start:
        return 0
    try:
        start_dt = datetime.fromisoformat(str(start))
        end_dt = datetime.fromisoformat(end)
    except ValueError:
        return 0
    return max(0, int((end_dt - start_dt).total_seconds()))


def _safe_text(value: str, limit: int) -> str:
    text = " ".join(str(value).split())
    return text[:limit]


def _metric(label: str, value: object) -> str:
    return (
        '<article class="metric">'
        f"<span>{html.escape(str(label))}</span>"
        f"<strong>{html.escape(str(value))}</strong>"
        "</article>"
    )


def _step_table(steps: list[Mapping[str, Any]]) -> str:
    rows = []
    for index, step in enumerate(steps, start=1):
        status = str(step.get("status") or "")
        rows.append(
            "<tr>"
            f"<td>{index}</td>"
            f"<td>{html.escape(str(step.get('label') or step.get('step_key') or ''))}</td>"
            f'<td class="{html.escape(status)}">{html.escape(status)}</td>'
            f"<td>{html.escape(str(step.get('duration_seconds') or 0))}</td>"
            f"<td>{html.escape(str(step.get('exit_code') if step.get('exit_code') is not None else ''))}</td>"
            f"<td>{html.escape(str(step.get('started_at') or ''))}</td>"
            f"<td>{html.escape(str(step.get('completed_at') or ''))}</td>"
            f"<td>{html.escape(str(step.get('error_summary') or ''))}</td>"
            "</tr>"
        )
    if not rows:
        rows.append('<tr><td colspan="8">暂无自动化步骤记录。</td></tr>')
    return (
        '<article class="panel"><h2>步骤明细</h2>'
        '<table><thead><tr><th>#</th><th>步骤</th><th>状态</th><th>耗时秒</th><th>退出码</th><th>开始</th><th>结束</th><th>错误摘要</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></article>'
    )
