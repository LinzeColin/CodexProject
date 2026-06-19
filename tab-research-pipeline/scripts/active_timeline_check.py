#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_ROOT))

from tab_research.report_store import connect_report_db
from tab_research.paths import resolve_output_dir, resolve_private_dir, resolve_workspace_root
from tab_research.partial_daily_research import (
    partial_daily_research_status_from_payload,
    write_partial_daily_research_bundle,
)

WORKSPACE_ROOT = resolve_workspace_root(Path(__file__))
OUTPUT_DIR = resolve_output_dir(Path(__file__))
REPORT_DIR = Path.home() / "Downloads" / "FIFA Report"
BACKFILL_REPORT_DIR = REPORT_DIR / "backfill"
PRIVATE_LOG_DIR = resolve_private_dir(Path(__file__), "active_backfill_logs")
DB_PATH = OUTPUT_DIR / "tab_fifa_reports.sqlite3"
LATEST_JSON = OUTPUT_DIR / "active_timeline_latest.json"
BACKFILL_LATEST_JSON = OUTPUT_DIR / "active_backfill_latest.json"
RAW_REFRESH_HEALTH_JSON = OUTPUT_DIR / "raw_refresh_health_latest.json"
REPORT_TZ = ZoneInfo(os.getenv("TAB_FIFA_REPORT_TZ", "Australia/Sydney"))
RUN_TIME_SLOTS = [
    ("00:00-05:00", time(0, 0), time(5, 0)),
    ("05:00-10:00", time(5, 0), time(10, 0)),
    ("10:00-15:00", time(10, 0), time(15, 0)),
    ("15:00-20:00", time(15, 0), time(20, 0)),
    ("20:00-24:00", time(20, 0), time(23, 59, 59)),
]
DEFAULT_MIN_ANALYSES_PER_DAY = 4
EFFECTIVE_STATUSES = {
    "ready_for_manual_report",
    "blocked_by_gate",
    "ready_no_latest_publish",
    "backfill_ready_no_latest_publish",
}


@dataclass(frozen=True)
class ReportRun:
    run_id: str
    report_date: str
    status: str
    started_at: str
    finished_at: str
    time_adjusted_new_exposure_aud: float

    @property
    def started_local(self) -> datetime | None:
        return parse_datetime(self.started_at)

    @property
    def effective(self) -> bool:
        return self.status in EFFECTIVE_STATUSES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit TAB FIFA report cadence and optionally run safe no-latest-publish backfills."
    )
    parser.add_argument("--lookback-days", type=int, default=8)
    parser.add_argument("--min-analyses-per-day", type=int, default=DEFAULT_MIN_ANALYSES_PER_DAY)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-latest", action="store_true", default=True)
    parser.add_argument("--backfill-missing", action="store_true")
    parser.add_argument("--max-backfill-runs", type=int, default=3)
    parser.add_argument("--since-date", default="", help="Optional DDMMYYYY start date.")
    return parser.parse_args()


def parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(REPORT_TZ)


def ddmmyyyy(day: date) -> str:
    return day.strftime("%d%m%Y")


def display_date(report_date: str) -> str:
    if len(report_date) == 8 and report_date.isdigit():
        return f"{report_date[:2]}/{report_date[2:4]}/{report_date[4:]}"
    return report_date


def date_from_ddmmyyyy(value: str) -> date:
    return datetime.strptime(value, "%d%m%Y").date()


def fetch_report_runs() -> list[ReportRun]:
    if not DB_PATH.exists():
        return []
    uri = f"file:{DB_PATH.resolve()}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT run_id, report_date, status, started_at, finished_at,
                   time_adjusted_new_exposure_aud
            FROM report_runs
            ORDER BY started_at ASC
            """
        ).fetchall()
    finally:
        conn.close()
    return [
        ReportRun(
            run_id=str(row["run_id"] or ""),
            report_date=str(row["report_date"] or ""),
            status=str(row["status"] or ""),
            started_at=str(row["started_at"] or ""),
            finished_at=str(row["finished_at"] or ""),
            time_adjusted_new_exposure_aud=float(row["time_adjusted_new_exposure_aud"] or 0),
        )
        for row in rows
        if str(row["report_date"] or "")
    ]


def date_range(args: argparse.Namespace, runs: list[ReportRun]) -> list[date]:
    today = datetime.now(REPORT_TZ).date()
    if args.since_date:
        start = date_from_ddmmyyyy(args.since_date)
    else:
        start = today - timedelta(days=max(args.lookback_days - 1, 0))
        if runs:
            latest_success = next((run for run in reversed(runs) if run.status == "ready_for_manual_report"), None)
            if latest_success:
                start = min(start, date_from_ddmmyyyy(latest_success.report_date))
    if start > today:
        start = today
    return [start + timedelta(days=offset) for offset in range((today - start).days + 1)]


def slot_for(dt: datetime | None) -> str:
    if dt is None:
        return "未知"
    current = dt.time()
    for label, start, end in RUN_TIME_SLOTS:
        if start <= current <= end:
            return label
    return "未知"


def formal_pdf_exists(report_date: str) -> bool:
    return (REPORT_DIR / f"{report_date}.pdf").exists()


def run_scoped_pdf_count(report_date: str) -> int:
    return len(list(OUTPUT_DIR.glob(f"{report_date}_*.pdf")))


def summarize_day(day: date, runs: list[ReportRun], min_analyses: int) -> dict[str, Any]:
    report_date = ddmmyyyy(day)
    day_runs = [run for run in runs if run.report_date == report_date]
    effective_runs = [run for run in day_runs if run.effective]
    covered_slots = sorted({slot_for(run.started_local) for run in effective_runs if slot_for(run.started_local) != "未知"})
    expected_slots = [slot[0] for slot in RUN_TIME_SLOTS]
    missing_slots = [slot for slot in expected_slots if slot not in covered_slots]
    formal_report = formal_pdf_exists(report_date)
    scoped_reports = run_scoped_pdf_count(report_date)
    needs_analysis_backfill = len(effective_runs) < min_analyses
    needs_report_backfill = not formal_report
    reasons = []
    if needs_analysis_backfill:
        reasons.append(f"有效分析 {len(effective_runs)}/{min_analyses}")
    if needs_report_backfill:
        reasons.append("Downloads 正式日报缺失")
    return {
        "report_date": report_date,
        "display_date": display_date(report_date),
        "run_count": len(day_runs),
        "effective_analysis_count": len(effective_runs),
        "failed_count": len([run for run in day_runs if run.status == "failed"]),
        "covered_slots": covered_slots,
        "missing_slots": missing_slots,
        "formal_report_exists": formal_report,
        "run_scoped_pdf_count": scoped_reports,
        "needs_backfill": bool(reasons),
        "backfill_reasons": reasons,
        "latest_status": day_runs[-1].status if day_runs else "missing",
        "latest_run_id": day_runs[-1].run_id if day_runs else "",
        "runs": [
            {
                "run_id": run.run_id,
                "status": run.status,
                "started_local": run.started_local.isoformat() if run.started_local else "",
                "slot": slot_for(run.started_local),
                "effective": run.effective,
            }
            for run in day_runs[-8:]
        ],
    }


def backfill_priority(item: dict[str, Any], min_analyses: int) -> tuple[int, list[str]]:
    missing_slot_count = len(item.get("missing_slots") or [])
    effective_count = int(item.get("effective_analysis_count") or 0)
    analysis_gap = max(min_analyses - effective_count, 0)
    missing_report = not bool(item.get("formal_report_exists"))
    latest_status = str(item.get("latest_status") or "missing")
    score = missing_slot_count * 20 + analysis_gap * 10 + (15 if missing_report else 0)
    if latest_status == "missing":
        score += 5
    reasons = [
        f"缺失时段 {missing_slot_count}/{len(RUN_TIME_SLOTS)}",
        f"有效分析 {effective_count}/{min_analyses}",
        "日报缺失" if missing_report else "日报存在",
        f"latest={latest_status}",
    ]
    return score, reasons


def build_backfill_queue(
    days: list[dict[str, Any]],
    max_items: int | None = None,
    min_analyses: int = DEFAULT_MIN_ANALYSES_PER_DAY,
) -> list[dict[str, Any]]:
    queue = []
    for item in days:
        if not item["needs_backfill"]:
            continue
        score, priority_reasons = backfill_priority(item, min_analyses)
        queue.append(
            {
                "report_date": item["report_date"],
                "display_date": item["display_date"],
                "reason": "；".join(item["backfill_reasons"]),
                "priority_score": score,
                "priority_reason": "；".join(priority_reasons),
                "missing_slot_count": len(item.get("missing_slots") or []),
                "effective_analysis_count": int(item.get("effective_analysis_count") or 0),
                "formal_report_exists": bool(item.get("formal_report_exists")),
                "latest_status": item.get("latest_status") or "missing",
                "operation": "补跑一次分析并生成 run-scoped PDF",
                "mode": "safe_no_latest_publish",
                "truthfulness_note": "历史缺口只能用当前可用数据重建，不能冒充原时点盘口。",
            }
        )
    queue.sort(key=lambda row: (-int(row["priority_score"]), backfill_sort_date(str(row.get("report_date") or ""))))
    for index, item in enumerate(queue, start=1):
        item["repair_rank"] = index
    return queue[:max_items] if max_items is not None else queue


def backfill_sort_date(report_date: str) -> date:
    try:
        return date_from_ddmmyyyy(report_date)
    except (TypeError, ValueError):
        return date.max


def build_timeline(args: argparse.Namespace) -> dict[str, Any]:
    runs = fetch_report_runs()
    days = [summarize_day(day, runs, args.min_analyses_per_day) for day in date_range(args, runs)]
    backfill_queue = build_backfill_queue(days, min_analyses=args.min_analyses_per_day)
    complete_days = [item for item in days if not item["needs_backfill"]]
    missing_report_days = [item for item in days if not item["formal_report_exists"]]
    missing_analysis_days = [item for item in days if item["effective_analysis_count"] < args.min_analyses_per_day]
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(REPORT_TZ).isoformat(),
        "timezone": str(REPORT_TZ),
        "cadence_rule": {
            "min_analyses_per_day": args.min_analyses_per_day,
            "target_slots": [slot[0] for slot in RUN_TIME_SLOTS],
            "report_per_day": 1,
            "safe_backfill_mode": "no_latest_publish_reconstruction",
        },
        "summary": {
            "day_count": len(days),
            "complete_day_count": len(complete_days),
            "missing_analysis_day_count": len(missing_analysis_days),
            "missing_report_day_count": len(missing_report_days),
            "backfill_queue_count": len(backfill_queue),
            "formal_report_ready_for_all_days": not missing_report_days,
            "cadence_ready_for_all_days": not missing_analysis_days,
        },
        "days": days,
        "backfill_queue": backfill_queue,
    }
    return payload


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def raw_refresh_backfill_blocker() -> dict[str, Any] | None:
    health = load_json(RAW_REFRESH_HEALTH_JSON)
    if health.get("ready") is True:
        return None
    return {
        "code": "raw_refresh_not_ready",
        "raw_status": health.get("status", "missing"),
        "ready_required_target_count": health.get("ready_required_target_count", 0),
        "blocker_codes": health.get("blocker_codes", ["missing_raw_refresh_health"]),
        "recommended_next_action": health.get("recommended_next_action", "先接入官方/授权 raw 或导入用户导出快照，再执行缺口补跑。"),
    }


def current_report_date() -> str:
    return datetime.now(REPORT_TZ).strftime("%d%m%Y")


def write_partial_daily_research_after_blocked_backfill() -> dict[str, Any]:
    try:
        payload = write_partial_daily_research_bundle(OUTPUT_DIR, report_date=current_report_date())
    except Exception as exc:
        return {
            "ready": False,
            "status": "failed",
            "error": str(exc).splitlines()[0][:180],
            "message": "raw blocked 时尝试生成研究诊断日报失败。",
        }
    status = partial_daily_research_status_from_payload(payload)
    status["message"] = partial_daily_research_backfill_message(status)
    return status


def partial_daily_research_backfill_message(status: dict[str, Any]) -> str:
    if status.get("ready"):
        return "已补写 research-only 研究诊断日报；正式补跑仍因 raw blocked 暂停。"
    if status.get("status") == "failed":
        return "尝试生成 research-only 研究诊断日报失败；正式补跑仍因 raw blocked 暂停。"
    return "已尝试生成 research-only 研究诊断日报，但当前未达到 ready；正式补跑仍因 raw blocked 暂停。"


def run_safe_backfill(report_date: str) -> dict[str, Any]:
    PRIVATE_LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stdout_log = PRIVATE_LOG_DIR / f"active_backfill_{report_date}_{stamp}.stdout.log"
    stderr_log = PRIVATE_LOG_DIR / f"active_backfill_{report_date}_{stamp}.stderr.log"
    env = os.environ.copy()
    env.update(
        {
            "TAB_FIFA_REPORT_DATE": report_date,
            "TAB_FIFA_REFRESH_RAW": "reuse_fresh",
            "TAB_FIFA_NO_LATEST_PUBLISH": "1",
            "TAB_FIFA_BACKFILL_RECONSTRUCTION": "1",
        }
    )
    with stdout_log.open("w", encoding="utf-8") as stdout, stderr_log.open("w", encoding="utf-8") as stderr:
        proc = subprocess.run(
            [sys.executable, "run_daily_report.py"],
            cwd=PIPELINE_ROOT,
            env=env,
            stdout=stdout,
            stderr=stderr,
            timeout=1800,
            check=False,
        )
    response = parse_stdout_json(stdout_log)
    copied_pdf = copy_backfill_pdf(response, report_date)
    return {
        "report_date": report_date,
        "exit_code": proc.returncode,
        "status": response.get("status") or ("completed" if proc.returncode == 0 else "failed"),
        "run_id": response.get("run_id", ""),
        "pdf_run_copy": Path(str(response.get("pdf_run_copy") or "")).name,
        "backfill_pdf": copied_pdf.name if copied_pdf else "",
        "stdout_log": stdout_log.name,
        "stderr_log": stderr_log.name,
        "latest_publish_disabled": bool(response.get("latest_publish_disabled")),
        "backfill_reconstruction": True,
    }


def parse_stdout_json(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def copy_backfill_pdf(response: dict[str, Any], report_date: str) -> Path | None:
    raw_path = response.get("pdf_run_copy")
    if not raw_path:
        return None
    source = Path(str(raw_path))
    if not source.exists():
        source = OUTPUT_DIR / Path(str(raw_path)).name
    if not source.exists():
        return None
    BACKFILL_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    run_id = str(response.get("run_id") or source.stem)
    target = BACKFILL_REPORT_DIR / f"{report_date}_{run_id}.pdf"
    shutil.copy2(source, target)
    return target


def run_backfills(args: argparse.Namespace, payload: dict[str, Any]) -> dict[str, Any]:
    cadence_rule = payload.get("cadence_rule") or {}
    min_analyses = int(cadence_rule.get("min_analyses_per_day") or DEFAULT_MIN_ANALYSES_PER_DAY)
    full_queue = build_backfill_queue(payload["days"], min_analyses=min_analyses)
    max_runs = max(args.max_backfill_runs, 0)
    queue = full_queue[:max_runs]
    started_at = datetime.now(REPORT_TZ).isoformat()
    raw_blocker = raw_refresh_backfill_blocker()
    if raw_blocker:
        partial_daily = write_partial_daily_research_after_blocked_backfill()
        backfill_payload = {
            "schema_version": 1,
            "started_at": started_at,
            "finished_at": datetime.now(REPORT_TZ).isoformat(),
            "mode": "safe_no_latest_publish",
            "status": "blocked_by_raw_refresh",
            "requested_count": 0,
            "completed_count": 0,
            "blocked_queue_count": len(queue),
            "total_backfill_queue_count": len(full_queue),
            "max_backfill_runs": max_runs,
            "blocker": raw_blocker,
            "partial_daily_research": partial_daily,
            "results": [],
            "truthfulness_note": "公开盘口 raw 未就绪时不执行历史补跑，避免用 stale/blocked 数据生成误导性报告。",
        }
        atomic_write_json(BACKFILL_LATEST_JSON, backfill_payload)
        return backfill_payload
    results = []
    for item in queue:
        results.append(run_safe_backfill(item["report_date"]))
    backfill_payload = {
        "schema_version": 1,
        "started_at": started_at,
        "finished_at": datetime.now(REPORT_TZ).isoformat(),
        "mode": "safe_no_latest_publish",
        "requested_count": len(queue),
        "completed_count": len(results),
        "total_backfill_queue_count": len(full_queue),
        "max_backfill_runs": max_runs,
        "results": results,
        "truthfulness_note": "补跑报告为当前数据重建版本，不替代原时点真实盘口快照。",
    }
    atomic_write_json(BACKFILL_LATEST_JSON, backfill_payload)
    return backfill_payload


def persist_timeline_audit(payload: dict[str, Any]) -> dict[str, Any]:
    generated_at = str(payload.get("generated_at") or datetime.now(REPORT_TZ).isoformat())
    audit_id = f"active_timeline_{generated_at.replace(':', '').replace('-', '').replace('+', '_').replace('.', '_')}_{os.getpid()}"
    summary = payload.get("summary") or {}
    raw_health = load_json(RAW_REFRESH_HEALTH_JSON)
    backfill_result = payload.get("backfill_result") or load_json(BACKFILL_LATEST_JSON)
    raw_blocker = raw_health.get("blocker_codes") or []
    try:
        with connect_report_db(DB_PATH) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO active_timeline_audits(
                    audit_id, generated_at, timezone, day_count, complete_day_count,
                    missing_analysis_day_count, missing_report_day_count, backfill_queue_count,
                    cadence_ready_for_all_days, formal_report_ready_for_all_days,
                    backfill_status, raw_refresh_ready, raw_refresh_status, raw_blocker_json, payload_json
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    generated_at,
                    str(payload.get("timezone") or REPORT_TZ),
                    int(summary.get("day_count") or 0),
                    int(summary.get("complete_day_count") or 0),
                    int(summary.get("missing_analysis_day_count") or 0),
                    int(summary.get("missing_report_day_count") or 0),
                    int(summary.get("backfill_queue_count") or 0),
                    1 if summary.get("cadence_ready_for_all_days") else 0,
                    1 if summary.get("formal_report_ready_for_all_days") else 0,
                    str(backfill_result.get("status") or backfill_result.get("mode") or "not_run"),
                    1 if raw_health.get("ready") is True else 0,
                    str(raw_health.get("status") or "missing"),
                    json.dumps(raw_blocker, ensure_ascii=False),
                    json.dumps(payload, ensure_ascii=False),
                ),
            )
            conn.commit()
        return {"status": "stored", "database": DB_PATH.name, "table": "active_timeline_audits", "audit_id": audit_id}
    except Exception as exc:
        return {
            "status": "failed",
            "database": DB_PATH.name,
            "table": "active_timeline_audits",
            "error": str(exc).splitlines()[0][:180],
        }


def main() -> None:
    args = parse_args()
    payload = build_timeline(args)
    if args.backfill_missing:
        payload["backfill_result"] = run_backfills(args, payload)
        payload = build_timeline(args)
        payload["backfill_result"] = json.loads(BACKFILL_LATEST_JSON.read_text(encoding="utf-8"))
    payload["history_persistence"] = persist_timeline_audit(payload)
    if args.write_latest:
        atomic_write_json(LATEST_JSON, payload)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        summary = payload["summary"]
        print(
            f"active timeline: days={summary['day_count']} missing_analysis_days={summary['missing_analysis_day_count']} "
            f"missing_report_days={summary['missing_report_day_count']} backfill_queue={summary['backfill_queue_count']}"
        )


if __name__ == "__main__":
    main()
