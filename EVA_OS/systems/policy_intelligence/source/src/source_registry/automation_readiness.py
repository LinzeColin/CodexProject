from __future__ import annotations

import html
import os
import json
import plistlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .automation_status import load_latest_automation_run
from .credential_doctor import build_credential_doctor
from .monitor import build_monitor_status


DEFAULT_SCHEDULE_TIMES = ["09:00", "21:00"]


def build_automation_readiness(
    *,
    content_conn=None,
    data_dir: str | Path = "data",
    analysis_mode: str = "template",
    search_secrets_file: str | Path | None = None,
    platform_auth_file: str | Path | None = None,
    quality_rules_file: str | Path | None = "rules/quality_gates.json",
    schedule_times: list[str] | None = None,
    scheduler_file: str | Path | None = None,
    max_running_minutes: int = 180,
    runtime_policy: Mapping[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = now or datetime.now(timezone.utc)
    root = Path(".")
    data_root = Path(data_dir)
    entrypoint = root / "scripts" / "run_policy_report.sh"
    lock_path = data_root / "pipeline.lock"
    latest_automation = load_latest_automation_run(data_root)
    credential = build_credential_doctor(
        search_secrets_file=search_secrets_file,
        platform_auth_file=platform_auth_file,
        now=current,
    )
    runtime = _runtime_policy_from_env(max_running_minutes=max_running_minutes)
    if runtime_policy:
        runtime.update({str(key): value for key, value in runtime_policy.items()})
    runtime_check = _runtime_policy_check(runtime)
    expected_schedule = schedule_times or DEFAULT_SCHEDULE_TIMES
    scheduler_check = _scheduler_persistence_check(
        data_root,
        expected_schedule,
        scheduler_file=scheduler_file,
    )
    latest_success_check = _latest_completed_run_check(
        content_conn,
        current,
        expected_schedule,
    )
    monitor_status = (
        build_monitor_status(
            content_conn,
            data_root,
            analysis_mode,
            quality_rules_file=quality_rules_file,
        )
        if content_conn is not None
        else {}
    )
    checks = [
        _check("entrypoint", "自动化入口脚本", entrypoint.exists(), "脚本存在，可由 launchd/cron/外部 automation 调用。", "缺少 scripts/run_policy_report.sh。"),
        _check("data_dir", "数据目录", data_root.exists(), "数据目录存在。", "数据目录不存在，首次运行前需创建。"),
        _lock_check(lock_path),
        _latest_automation_check(latest_automation, current, max_running_minutes),
        latest_success_check,
        _latest_report_check(monitor_status),
        _queue_check(monitor_status),
        _quality_check(monitor_status),
        _p0_check(credential),
        _schedule_check(expected_schedule),
        scheduler_check,
        runtime_check,
    ]
    summary = {
        "check_count": len(checks),
        "passed_count": sum(1 for item in checks if item["status"] == "pass"),
        "warning_count": sum(1 for item in checks if item["status"] == "warn"),
        "failed_count": sum(1 for item in checks if item["status"] == "fail"),
        "schedule_runs_per_day": len(expected_schedule),
        "pending_queue": int(((monitor_status.get("queue") or {}).get("pending_count") or 0)),
        "pending_gaps": int(((monitor_status.get("external_reference_gaps") or {}).get("pending_count") or 0)),
        "p0_status": str((credential.get("p0_gate") or {}).get("status") or ""),
        "runtime_policy_status": runtime_check["status"],
        "scheduler_status": scheduler_check["status"],
        "latest_success_status": latest_success_check["status"],
    }
    overall = "ready" if summary["failed_count"] == 0 and summary["warning_count"] == 0 else "attention"
    if summary["failed_count"] > 0:
        overall = "blocked"
    return {
        "generated_at": current.isoformat(timespec="seconds"),
        "overall_status": overall,
        "schedule": {
            "times": expected_schedule,
            "runs_per_day": len(expected_schedule),
            "recommended_entrypoint": "bash scripts/run_policy_report.sh",
            "scheduler_evidence": scheduler_check.get("evidence") or {},
        },
        "runtime_policy": runtime,
        "summary": summary,
        "checks": checks,
        "next_actions": _next_actions(checks),
        "security_boundary": (
            "就绪检查只读取文件存在性、状态摘要、队列和质量门；不读取或输出 API key、cookie、session、账号密码。"
        ),
    }


def write_automation_readiness_dashboard(
    path: str | Path,
    *,
    content_conn=None,
    data_dir: str | Path = "data",
    analysis_mode: str = "template",
    search_secrets_file: str | Path | None = None,
    platform_auth_file: str | Path | None = None,
    quality_rules_file: str | Path | None = "rules/quality_gates.json",
    schedule_times: list[str] | None = None,
    scheduler_file: str | Path | None = None,
    max_running_minutes: int = 180,
    runtime_policy: Mapping[str, Any] | None = None,
    title: str = "自动化运行就绪检查",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    report = build_automation_readiness(
        content_conn=content_conn,
        data_dir=data_dir,
        analysis_mode=analysis_mode,
        search_secrets_file=search_secrets_file,
        platform_auth_file=platform_auth_file,
        quality_rules_file=quality_rules_file,
        schedule_times=schedule_times,
        scheduler_file=scheduler_file,
        max_running_minutes=max_running_minutes,
        runtime_policy=runtime_policy,
    )
    output.write_text(render_automation_readiness_dashboard(report, title=title), encoding="utf-8")
    return str(output)


def render_automation_readiness_dashboard(report: Mapping[str, Any], *, title: str = "自动化运行就绪检查") -> str:
    summary = report.get("summary") or {}
    schedule = report.get("schedule") or {}
    runtime = report.get("runtime_policy") or {}
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
    .metrics {{ display: grid; grid-template-columns: repeat(8, minmax(0, 1fr)); border: 1px solid var(--line); background: var(--panel); margin: 14px 0; }}
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
    @media (max-width: 820px) {{
      .metrics {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
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
      <p>Automation Readiness</p>
      <h1>{html.escape(title)}</h1>
      <p>生成时间：{html.escape(str(report.get("generated_at") or ""))}｜状态：{html.escape(str(report.get("overall_status") or ""))}｜该页面不展示 secret。</p>
    </section>
    <section class="metrics">
      {_metric("通过", summary.get("passed_count", 0))}
      {_metric("警告", summary.get("warning_count", 0))}
      {_metric("阻塞", summary.get("failed_count", 0))}
      {_metric("每日运行", summary.get("schedule_runs_per_day", 0))}
      {_metric("调度", summary.get("scheduler_status", ""))}
      {_metric("新鲜度", summary.get("latest_success_status", ""))}
      {_metric("待生产", summary.get("pending_queue", 0))}
      {_metric("P0", summary.get("p0_status", ""))}
    </section>
    <article class="panel"><h2>调度建议</h2><p>建议每日运行 {html.escape(str(schedule.get("runs_per_day") or 0))} 次：{html.escape(", ".join(str(item) for item in schedule.get("times") or []))}。</p><p class="cmd">{html.escape(str(schedule.get("recommended_entrypoint") or ""))}</p></article>
    {_runtime_policy_panel(runtime)}
    {_checks_table(list(report.get("checks") or []))}
    {_next_actions_panel(list(report.get("next_actions") or []))}
    <article class="panel"><h2>安全与合规边界</h2><p>{html.escape(str(report.get("security_boundary") or ""))}</p></article>
  </main>
</body>
</html>
"""


def _check(key: str, label: str, ok: bool, pass_detail: str, fail_detail: str) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "status": "pass" if ok else "fail",
        "detail": pass_detail if ok else fail_detail,
        "action": "" if ok else fail_detail,
    }


def _lock_check(path: Path) -> dict[str, Any]:
    state = inspect_pipeline_lock(path)
    if state["status"] == "absent":
        return {"key": "pipeline_lock", "label": "pipeline lock", "status": "pass", "detail": "未发现锁文件，可启动新运行。", "action": ""}
    if state["status"] == "invalid":
        return {"key": "pipeline_lock", "label": "pipeline lock", "status": "warn", "detail": "锁文件内容不是 pid。", "action": "人工复核 data/pipeline.lock。"}
    alive = state["status"] == "running"
    return {
        "key": "pipeline_lock",
        "label": "pipeline lock",
        "status": "warn" if alive else "pass",
        "detail": "检测到已有运行进程。" if alive else "发现 stale lock；可由 automation-lock-clean 安全清理。",
        "action": "等待当前运行结束。" if alive else "运行 automation-lock-clean 或直接启动 pipeline 触发安全清理。",
    }


def inspect_pipeline_lock(path: str | Path) -> dict[str, Any]:
    lock_path = Path(path)
    if not lock_path.exists():
        return {"path": str(lock_path), "exists": False, "status": "absent", "pid": None, "can_cleanup": False}
    raw = lock_path.read_text(encoding="utf-8", errors="replace").strip()
    try:
        pid = int(raw)
    except ValueError:
        return {"path": str(lock_path), "exists": True, "status": "invalid", "pid": None, "can_cleanup": False}
    alive = _pid_alive(pid)
    return {
        "path": str(lock_path),
        "exists": True,
        "status": "running" if alive else "stale",
        "pid": pid,
        "can_cleanup": not alive,
    }


def cleanup_stale_pipeline_lock(path: str | Path) -> dict[str, Any]:
    lock_path = Path(path)
    state = inspect_pipeline_lock(lock_path)
    removed = False
    if state.get("status") == "stale":
        try:
            lock_path.unlink()
            removed = True
        except FileNotFoundError:
            removed = False
    return {**state, "removed": removed, "final_status": "absent" if removed else state.get("status")}


def _latest_automation_check(payload: Mapping[str, Any], now: datetime, max_running_minutes: int) -> dict[str, Any]:
    status = str(payload.get("status") or "not_started")
    if status == "not_started":
        return {"key": "latest_automation", "label": "自动化步骤状态", "status": "warn", "detail": "尚无自动化步骤记录。", "action": "运行一次 bash scripts/run_policy_report.sh。"}
    if status == "failed":
        return {"key": "latest_automation", "label": "自动化步骤状态", "status": "fail", "detail": "自动化步骤失败。", "action": "查看 reports/automation_run_dashboard.html 和 data/run_logs。"}
    if status == "running":
        started = _parse_dt(payload.get("started_at"))
        if started and (now - started).total_seconds() > max_running_minutes * 60:
            return {"key": "latest_automation", "label": "自动化步骤状态", "status": "fail", "detail": "自动化运行超时未完成。", "action": "检查锁文件、进程和 run log。"}
        return {"key": "latest_automation", "label": "自动化步骤状态", "status": "warn", "detail": "当前有自动化步骤运行中。", "action": "等待运行结束后复查。"}
    return {"key": "latest_automation", "label": "自动化步骤状态", "status": "pass", "detail": "自动化步骤已完成。", "action": ""}


def _latest_completed_run_check(content_conn: Any, now: datetime, schedule_times: list[str]) -> dict[str, Any]:
    if content_conn is None:
        return {
            "key": "latest_success_freshness",
            "label": "最近成功运行新鲜度",
            "status": "warn",
            "detail": "未连接正文库，无法核验最近成功运行。",
            "action": "传入 --content-db 后复查 automation-readiness。",
        }
    try:
        row = content_conn.execute(
            """
            SELECT run_id, completed_at, report_path
            FROM pipeline_runs
            WHERE status = 'completed'
            ORDER BY completed_at DESC
            LIMIT 1
            """
        ).fetchone()
    except Exception:
        return {
            "key": "latest_success_freshness",
            "label": "最近成功运行新鲜度",
            "status": "warn",
            "detail": "正文库无法查询最近成功运行。",
            "action": "检查 data/policy_documents.sqlite schema 后复查。",
        }
    if not row:
        return {
            "key": "latest_success_freshness",
            "label": "最近成功运行新鲜度",
            "status": "warn",
            "detail": "没有成功完成的 pipeline_runs 记录。",
            "action": "先运行一次 bash scripts/run_policy_report.sh 并确认质量门通过。",
        }
    completed_at = _parse_dt(row["completed_at"])
    if not completed_at:
        return {
            "key": "latest_success_freshness",
            "label": "最近成功运行新鲜度",
            "status": "warn",
            "detail": f"最近成功运行 {row['run_id']} 缺少可解析 completed_at。",
            "action": "复核 pipeline_runs.completed_at。",
        }
    age_hours = max(0.0, (now - completed_at).total_seconds() / 3600)
    threshold_hours = _freshness_threshold_hours(schedule_times)
    fresh = age_hours <= threshold_hours
    return {
        "key": "latest_success_freshness",
        "label": "最近成功运行新鲜度",
        "status": "pass" if fresh else "warn",
        "detail": (
            f"最近成功运行 {row['run_id']}，完成于 {completed_at.isoformat(timespec='seconds')}，"
            f"距今 {age_hours:.1f} 小时；阈值 {threshold_hours:.1f} 小时。"
        ),
        "action": "" if fresh else "最近一次成功运行已过期；检查调度是否触发，或手动运行 bash scripts/run_policy_report.sh。",
    }


def _latest_report_check(monitor: Mapping[str, Any]) -> dict[str, Any]:
    report = monitor.get("report") or {}
    if report.get("exists"):
        return {"key": "latest_report", "label": "完成报告产物", "status": "pass", "detail": "最新完成报告 PDF 存在。", "action": ""}
    return {"key": "latest_report", "label": "完成报告产物", "status": "warn", "detail": "未找到完成报告 PDF。", "action": "运行 pipeline 或检查 report_path。"}


def _queue_check(monitor: Mapping[str, Any]) -> dict[str, Any]:
    pending = int(((monitor.get("queue") or {}).get("pending_count") or 0))
    return {
        "key": "report_queue",
        "label": "待生产队列",
        "status": "pass" if pending > 0 else "warn",
        "detail": f"待生产报告 {pending} 份。" if pending > 0 else "待生产队列为空。",
        "action": "" if pending > 0 else "先运行采集或复核队列规则。",
    }


def _quality_check(monitor: Mapping[str, Any]) -> dict[str, Any]:
    quality = monitor.get("quality_gate") or {}
    if quality.get("met"):
        return {"key": "quality_gate", "label": "报告质量门", "status": "pass", "detail": "最新完成报告满足 5 参考 / 2 平台质量门。", "action": ""}
    return {"key": "quality_gate", "label": "报告质量门", "status": "warn", "detail": "完成报告未满足外部参考质量门。", "action": "补搜索 API / 平台授权或复核缺口队列。"}


def _p0_check(credential: Mapping[str, Any]) -> dict[str, Any]:
    gate = credential.get("p0_gate") or {}
    status = str(gate.get("status") or "")
    if gate.get("minimum_ready"):
        return {"key": "p0_credentials", "label": "P0 全网接入", "status": "pass", "detail": f"P0 状态 {status}。", "action": ""}
    return {
        "key": "p0_credentials",
        "label": "P0 全网接入",
        "status": "fail",
        "detail": f"P0 状态 {status or 'unknown'}；搜索 API 或 B站授权仍缺失。",
        "action": "补至少 1 个搜索 API key，并放入 B站本地授权文件。",
    }


def _schedule_check(times: list[str]) -> dict[str, Any]:
    ok = len(times) >= 2
    return {
        "key": "schedule_cadence",
        "label": "每日两次调度",
        "status": "pass" if ok else "warn",
        "detail": f"目标运行时间：{', '.join(times)}。",
        "action": "" if ok else "配置两个每日运行时间。",
    }


def _scheduler_persistence_check(
    data_root: Path,
    schedule_times: list[str],
    *,
    scheduler_file: str | Path | None = None,
) -> dict[str, Any]:
    evidence = _scheduler_evidence(data_root, scheduler_file=scheduler_file)
    if not evidence.get("exists"):
        return {
            "key": "scheduler_persistence",
            "label": "调度持久化",
            "status": "warn",
            "detail": "未发现调度落地证据文件；当前只能证明目标时间，不能证明 launchd/cron/外部 automation 已安装。",
            "action": "创建 data/automation/scheduler.json 或传入 --scheduler-file，记录调度类型、入口脚本和每日运行时间。",
            "evidence": evidence,
        }
    enabled = bool(evidence.get("enabled"))
    entrypoint_ok = bool(evidence.get("entrypoint_ok"))
    schedule_ok = _schedule_matches(evidence.get("schedule_times") or [], schedule_times)
    if enabled and entrypoint_ok and schedule_ok:
        return {
            "key": "scheduler_persistence",
            "label": "调度持久化",
            "status": "pass",
            "detail": (
                f"发现 {evidence.get('scheduler_type') or 'scheduler'} 调度证据；"
                f"入口脚本匹配，运行时间 {', '.join(str(item) for item in evidence.get('schedule_times') or [])}。"
            ),
            "action": "",
            "evidence": evidence,
        }
    warnings = []
    if not enabled:
        warnings.append("调度未启用或未声明 enabled=true。")
    if not entrypoint_ok:
        warnings.append("入口脚本未指向 run_policy_report.sh。")
    if not schedule_ok:
        warnings.append("运行时间与目标每日调度不匹配。")
    return {
        "key": "scheduler_persistence",
        "label": "调度持久化",
        "status": "warn",
        "detail": "发现调度证据但不完整。" + " ".join(warnings),
        "action": "补全调度证据文件，或修正 launchd/cron 配置后复查。",
        "evidence": evidence,
    }


def _scheduler_evidence(data_root: Path, *, scheduler_file: str | Path | None = None) -> dict[str, Any]:
    candidates: list[Path] = []
    if scheduler_file:
        candidates.append(Path(scheduler_file))
    env_path = os.environ.get("POLICY_AUTOMATION_SCHEDULER_FILE")
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            data_root / "automation" / "scheduler.json",
            data_root / "automation" / "scheduler_manifest.json",
            Path.home() / "Library" / "LaunchAgents" / "com.source-registry.policy-report.plist",
            Path.home() / "Library" / "LaunchAgents" / "com.policy-intelligence.report.plist",
        ]
    )
    for path in candidates:
        if path.exists():
            return _read_scheduler_evidence(path)
    return {"exists": False, "checked": [path.name for path in candidates]}


def _read_scheduler_evidence(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    try:
        raw_bytes = path.read_bytes()
    except OSError:
        return {"exists": True, "file": path.name, "enabled": False, "entrypoint_ok": False, "schedule_times": []}
    if suffix == ".json":
        try:
            payload = json.loads(raw_bytes.decode("utf-8"))
        except json.JSONDecodeError:
            payload = {}
        times = [str(item) for item in payload.get("schedule_times") or payload.get("times") or []]
        entrypoint = str(payload.get("entrypoint") or payload.get("command") or "")
        return {
            "exists": True,
            "file": path.name,
            "scheduler_type": str(payload.get("scheduler_type") or payload.get("type") or "external"),
            "enabled": payload.get("enabled") is not False,
            "entrypoint_ok": "run_policy_report.sh" in entrypoint,
            "schedule_times": times,
            "timezone": str(payload.get("timezone") or ""),
        }
    if suffix == ".plist":
        return _read_launchd_plist_evidence(path, raw_bytes)
    clipped = raw_bytes.decode("utf-8", errors="replace")[:8000]
    return {
        "exists": True,
        "file": path.name,
        "scheduler_type": "launchd" if suffix == ".plist" else "text",
        "enabled": True,
        "entrypoint_ok": "run_policy_report.sh" in clipped,
        "schedule_times": _extract_times(clipped),
        "timezone": "",
    }


def _read_launchd_plist_evidence(path: Path, raw_bytes: bytes) -> dict[str, Any]:
    try:
        payload = plistlib.loads(raw_bytes)
    except Exception:
        text = raw_bytes.decode("utf-8", errors="replace")[:8000]
        return {
            "exists": True,
            "file": path.name,
            "scheduler_type": "launchd",
            "enabled": True,
            "entrypoint_ok": "run_policy_report.sh" in text,
            "schedule_times": _extract_times(text),
            "timezone": "",
        }
    args = payload.get("ProgramArguments") or []
    command_text = " ".join(str(item) for item in args)
    intervals = payload.get("StartCalendarInterval") or []
    if isinstance(intervals, Mapping):
        intervals = [intervals]
    times = []
    for item in intervals:
        if not isinstance(item, Mapping):
            continue
        try:
            hour = int(item.get("Hour"))
            minute = int(item.get("Minute", 0))
        except (TypeError, ValueError):
            continue
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            value = f"{hour:02d}:{minute:02d}"
            if value not in times:
                times.append(value)
    return {
        "exists": True,
        "file": path.name,
        "scheduler_type": "launchd",
        "label": str(payload.get("Label") or ""),
        "enabled": not bool(payload.get("Disabled", False)),
        "entrypoint_ok": "run_policy_report.sh" in command_text,
        "schedule_times": times,
        "timezone": "",
    }


def _schedule_matches(actual: list[Any], expected: list[str]) -> bool:
    actual_set = {_normalize_time(item) for item in actual}
    expected_set = {_normalize_time(item) for item in expected}
    actual_set.discard("")
    expected_set.discard("")
    return bool(expected_set and expected_set.issubset(actual_set))


def _normalize_time(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        hour_text, minute_text = text.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
    except ValueError:
        return ""
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return ""
    return f"{hour:02d}:{minute:02d}"


def _extract_times(text: str) -> list[str]:
    import re

    found = []
    for match in re.finditer(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", text):
        value = f"{int(match.group(1)):02d}:{match.group(2)}"
        if value not in found:
            found.append(value)
    return found


def _freshness_threshold_hours(schedule_times: list[str]) -> float:
    runs_per_day = max(1, len(schedule_times))
    return max(18.0, 24.0 / runs_per_day + 6.0)


def _runtime_policy_from_env(*, max_running_minutes: int) -> dict[str, Any]:
    return {
        "max_sources": _env_int("MAX_SOURCES", 3),
        "max_pages_per_source": _env_int("MAX_PAGES_PER_SOURCE", 2),
        "max_links_per_page": _env_int("MAX_LINKS_PER_PAGE", 20),
        "max_interpretation_documents": _env_int("MAX_INTERPRETATION_DOCUMENTS", 10),
        "interpretation_request_timeout": _env_int("INTERPRETATION_REQUEST_TIMEOUT", 20),
        "interpretation_request_retries": _env_int("INTERPRETATION_REQUEST_RETRIES", 1),
        "interpretation_request_delay_seconds": _env_float("INTERPRETATION_REQUEST_DELAY_SECONDS", 0.2),
        "max_running_minutes": int(max_running_minutes),
    }


def _runtime_policy_check(policy: Mapping[str, Any]) -> dict[str, Any]:
    timeout = int(float(policy.get("interpretation_request_timeout") or 0))
    retries = int(float(policy.get("interpretation_request_retries") or 0))
    delay = float(policy.get("interpretation_request_delay_seconds") or 0)
    max_sources = int(float(policy.get("max_sources") or 0))
    max_pages = int(float(policy.get("max_pages_per_source") or 0))
    max_links = int(float(policy.get("max_links_per_page") or 0))
    max_runtime = int(float(policy.get("max_running_minutes") or 0))
    warnings: list[str] = []
    if timeout < 5 or timeout > 90:
        warnings.append("请求超时建议保持 5-90 秒。")
    if retries < 1:
        warnings.append("无人值守运行建议至少 1 次重试。")
    if delay < 0.2:
        warnings.append("外部搜索/平台请求建议至少 0.2 秒限速。")
    if max_sources < 1 or max_pages < 1 or max_links < 5:
        warnings.append("采集规模过低，可能无法发现足够候选。")
    if max_runtime < 30:
        warnings.append("最大运行时长过短，可能误判长报告生成为超时。")
    detail = (
        f"来源 {max_sources}，每源页面 {max_pages}，每页链接 {max_links}，"
        f"超时 {timeout}s，重试 {retries}，限速 {delay:.2f}s，最大运行 {max_runtime}min。"
    )
    return {
        "key": "runtime_policy",
        "label": "运行策略",
        "status": "warn" if warnings else "pass",
        "detail": detail if not warnings else detail + " " + " ".join(warnings),
        "action": "" if not warnings else "调整运行环境变量或脚本默认值后复查 automation-readiness。",
    }


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _next_actions(checks: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in checks:
        if item.get("status") in {"fail", "warn"} and item.get("action"):
            rows.append({"severity": item.get("status"), "action": item.get("action"), "source": item.get("label")})
    return rows


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _metric(label: str, value: object) -> str:
    return (
        '<article class="metric">'
        f"<span>{html.escape(str(label))}</span>"
        f"<strong>{html.escape(str(value))}</strong>"
        "</article>"
    )


def _checks_table(checks: list[Mapping[str, Any]]) -> str:
    rows = []
    for item in checks:
        status = str(item.get("status") or "")
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('label') or ''))}</td>"
            f"<td class=\"{html.escape(status)}\">{html.escape(status)}</td>"
            f"<td>{html.escape(str(item.get('detail') or ''))}</td>"
            f"<td>{html.escape(str(item.get('action') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel"><h2>就绪检查</h2>'
        '<table><thead><tr><th>检查项</th><th>状态</th><th>证据</th><th>下一步</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></article>'
    )


def _runtime_policy_panel(policy: Mapping[str, Any]) -> str:
    rows = [
        ("来源数", policy.get("max_sources", "")),
        ("每源页面", policy.get("max_pages_per_source", "")),
        ("每页链接", policy.get("max_links_per_page", "")),
        ("解读文件", policy.get("max_interpretation_documents", "")),
        ("请求超时", f"{policy.get('interpretation_request_timeout', '')}s"),
        ("重试", policy.get("interpretation_request_retries", "")),
        ("限速", f"{float(policy.get('interpretation_request_delay_seconds') or 0):.2f}s"),
        ("最大运行", f"{policy.get('max_running_minutes', '')}min"),
    ]
    cells = "".join(
        "<tr>"
        f"<td>{html.escape(str(label))}</td>"
        f"<td>{html.escape(str(value))}</td>"
        "</tr>"
        for label, value in rows
    )
    return (
        '<article class="panel"><h2>运行策略</h2>'
        '<table><thead><tr><th>参数</th><th>当前值</th></tr></thead>'
        f"<tbody>{cells}</tbody></table>"
        '<p class="note">用于检查无人值守运行的采集规模、超时、重试和限速；具体值来自环境变量或脚本默认值。</p></article>'
    )


def _next_actions_panel(actions: list[Mapping[str, Any]]) -> str:
    if not actions:
        return '<article class="panel"><h2>下一步动作</h2><p class="note">暂无动作。</p></article>'
    rows = []
    for item in actions[:8]:
        rows.append(
            "<tr>"
            f"<td class=\"{html.escape(str(item.get('severity') or ''))}\">{html.escape(str(item.get('severity') or ''))}</td>"
            f"<td>{html.escape(str(item.get('source') or ''))}</td>"
            f"<td>{html.escape(str(item.get('action') or ''))}</td>"
            "</tr>"
        )
    return (
        '<article class="panel"><h2>下一步动作</h2>'
        '<table><thead><tr><th>级别</th><th>来源</th><th>动作</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></article>'
    )
