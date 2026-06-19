from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .artifacts import sanitize_public_payload
from .io import atomic_write_json, atomic_write_text
from .partial_daily_research import partial_daily_research_status
from .report_store import connect_report_db
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


ACTIVE_TIMELINE_REPORT_JSON_LATEST = "active_timeline_report_latest.json"
ACTIVE_TIMELINE_REPORT_MD_LATEST = "active_timeline_report_latest.md"
ACTIVE_TIMELINE_REPORT_PDF_LATEST = "active_timeline_report_latest.pdf"
REPORT_TZ = ZoneInfo("Australia/Sydney")


def write_active_timeline_report_bundle(output_dir: Path, db_path: Path | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    db_path = Path(db_path or output_dir / "tab_fifa_reports.sqlite3")
    payload = build_active_timeline_report(output_dir, db_path)
    json_path = output_dir / ACTIVE_TIMELINE_REPORT_JSON_LATEST
    md_path = output_dir / ACTIVE_TIMELINE_REPORT_MD_LATEST
    pdf_path = output_dir / ACTIVE_TIMELINE_REPORT_PDF_LATEST
    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_active_timeline_report_markdown(payload))
    pdf_summary = write_active_timeline_report_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    payload["storage"] = persist_active_timeline_report(db_path, payload)
    atomic_write_json(json_path, payload)
    return payload


def build_active_timeline_report(output_dir: Path, db_path: Path | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    db_path = Path(db_path or output_dir / "tab_fifa_reports.sqlite3")
    generated_at = datetime.now(REPORT_TZ).isoformat()
    timeline = load_json(output_dir / "active_timeline_latest.json")
    raw_health = load_json(output_dir / "raw_refresh_health_latest.json")
    backfill = load_json(output_dir / "active_backfill_latest.json")
    partial_research = build_partial_research_status(output_dir, backfill)
    days = normalize_days(timeline)
    queue = normalize_queue(timeline.get("backfill_queue") or [])
    slot_rows = build_slot_rows(timeline, days)
    audit_trend = read_audit_trend(db_path)
    summary = dict(timeline.get("summary") or empty_summary())
    comparison_rows = build_comparison_rows(summary, audit_trend)
    executive = executive_status(timeline, raw_health, backfill)
    recovery_plan = build_backfill_recovery_plan(summary, raw_health, backfill, queue, slot_rows, audit_trend)
    summary.update(
        {
            "safe_to_backfill_now": recovery_plan["safe_to_backfill_now"],
            "blocked_by_raw_refresh": recovery_plan["status"] == "blocked_by_raw_refresh",
            "blocked_backfill_queue_count": recovery_plan["blocked_queue_count"],
            "recovery_plan_status": recovery_plan["status"],
            "next_recovery_action": recovery_plan["next_unlock_action"],
            "max_safe_backfill_runs": recovery_plan["max_safe_backfill_runs"],
            "partial_daily_research_ready": bool(partial_research.get("ready")),
            "partial_daily_research_status": partial_research.get("status", "missing"),
            "partial_daily_research_execution_allowed": bool(partial_research.get("execution_allowed")),
            "partial_daily_research_new_stake_aud": int(partial_research.get("current_executable_new_stake_aud") or 0),
        }
    )
    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "snapshot_id": active_timeline_report_snapshot_id(generated_at),
        "mode": "active_timeline_dashboard",
        "purpose": "主动测试时间线 Dashboard：检查每天至少四次分析和一份正式日报，生成补跑优先队列；只生成研究报告，不自动下注。",
        "executive_status": executive,
        "summary": summary,
        "cadence_rule": timeline.get("cadence_rule") or {},
        "day_rows": days,
        "slot_rows": slot_rows,
        "backfill_queue_rows": queue,
        "backfill_recovery_plan": recovery_plan,
        "partial_daily_research": partial_research,
        "old_new_compare": {
            "status": "available" if comparison_rows else "missing_previous_audit",
            "rows": comparison_rows,
            "note": "新旧对比基于 active_timeline_audits 最近一次历史审计；若历史不足，则仅展示当前缺口。",
        },
        "audit_trend_rows": audit_trend[:7],
        "backfill_guard": {
            "allowed_now": bool(raw_health.get("ready")) and bool(queue),
            "raw_ready": bool(raw_health.get("ready")),
            "raw_status": raw_health.get("status", "missing"),
            "backfill_status": backfill.get("status", "not_run"),
            "safe_backfill_mode": "safe_no_latest_publish",
            "fail_closed_rule": "公开盘口 raw 未就绪时不执行补跑，不发布 latest_commit。",
        },
        "source_artifacts": {
            "active_timeline": "active_timeline_latest.json" if timeline else "",
            "active_backfill": "active_backfill_latest.json" if backfill else "",
            "partial_daily_research": "partial_daily_research_latest.json" if partial_research.get("source_artifact") else "",
            "raw_refresh_health": "raw_refresh_health_latest.json" if raw_health else "",
            "report_database": "tab_fifa_reports.sqlite3" if (output_dir / "tab_fifa_reports.sqlite3").exists() else "",
        },
        "truthfulness_note": "历史补跑只能用当前可用数据重建，不能冒充原时点盘口；raw 或门禁失败时保持 fail-closed。",
    }
    return sanitize_public_payload(payload)


def active_timeline_report_snapshot_id(generated_at: str) -> str:
    safe = generated_at.replace(":", "").replace("-", "").replace("+", "_").replace(".", "_")
    return f"active_timeline_report_{safe}"


def build_partial_research_status(output_dir: Path, backfill: dict[str, Any]) -> dict[str, Any]:
    status = dict(partial_daily_research_status(output_dir))
    backfill_status = backfill.get("partial_daily_research") if isinstance(backfill.get("partial_daily_research"), dict) else {}
    if backfill_status:
        for key, value in backfill_status.items():
            if value is not None and value != "" and value != []:
                status[key] = value
        status["source"] = "active_backfill_latest.partial_daily_research"
    else:
        status["source"] = "partial_daily_research_latest"
    status["source_artifact"] = "partial_daily_research_latest.json" if status.get("status") != "missing" else ""
    status["backfill_status"] = backfill.get("status") or backfill.get("mode") or "not_run"
    status["report_usage"] = (
        "raw blocked 时用于每日 research-only 诊断补写；不能替代正式日报，不能解锁新增下注。"
        if status.get("ready")
        else "尚未形成可用 research-only 诊断日报。"
    )
    return status


def empty_summary() -> dict[str, Any]:
    return {
        "day_count": 0,
        "complete_day_count": 0,
        "missing_analysis_day_count": 0,
        "missing_report_day_count": 0,
        "backfill_queue_count": 0,
        "formal_report_ready_for_all_days": False,
        "cadence_ready_for_all_days": False,
    }


def executive_status(timeline: dict[str, Any], raw_health: dict[str, Any], backfill: dict[str, Any]) -> dict[str, Any]:
    summary = timeline.get("summary") or empty_summary()
    raw_ready = bool(raw_health.get("ready"))
    queue_count = int(summary.get("backfill_queue_count") or 0)
    cadence_ready = bool(summary.get("cadence_ready_for_all_days"))
    reports_ready = bool(summary.get("formal_report_ready_for_all_days"))
    automation_ready = raw_ready and cadence_ready and reports_ready
    if automation_ready:
        primary_gap = "无主动测试缺口"
        action = "主动测试已满足 cadence 和日报要求；继续重跑日报门禁并等待用户授权 recurring automation。"
        status = "ready"
    elif not raw_ready:
        primary_gap = "公开盘口 raw 未就绪"
        action = "先接入授权 raw 或导入用户导出快照；成功后主动测试才能安全补跑缺失日期。"
        status = "blocked"
    elif queue_count:
        primary_gap = "存在分析/日报缺口"
        action = "按补跑优先队列执行 safe_no_latest_publish 补跑，补齐后再发布新日报。"
        status = "blocked"
    else:
        primary_gap = str(backfill.get("status") or "日报门禁待复核")
        action = "重跑日报门禁，确认 latest_commit 是否可以推进。"
        status = "watch"
    return {
        "status": status,
        "ready_for_recurring_automation": automation_ready,
        "primary_gap": primary_gap,
        "recommended_next_action": action,
        "raw_ready": raw_ready,
        "safe_to_backfill_now": raw_ready and queue_count > 0,
    }


def build_backfill_recovery_plan(
    summary: dict[str, Any],
    raw_health: dict[str, Any],
    backfill: dict[str, Any],
    queue: list[dict[str, Any]],
    slot_rows: list[dict[str, Any]],
    audit_trend: list[dict[str, Any]],
) -> dict[str, Any]:
    raw_ready = bool(raw_health.get("ready"))
    raw_status = str(raw_health.get("status") or "missing")
    actionable_queue_count = len(queue)
    queue_count = max(len(queue), int(summary.get("backfill_queue_count") or 0))
    blocker_codes = [str(item) for item in (raw_health.get("blocker_codes") or [])]
    latest_audit = audit_trend[0] if audit_trend else {}
    if raw_ready and queue_count:
        status = "ready_to_backfill"
        next_action = "执行最多 3 个 safe_no_latest_publish 补跑；补齐后重跑日报门禁，再决定是否发布新报告。"
        blocked_reason = ""
        max_runs = min(3, actionable_queue_count or queue_count)
    elif queue_count:
        status = "blocked_by_raw_refresh"
        next_action = "先接入授权 raw 或导入用户导出快照；raw 通过后按日期优先级补跑，补跑过程不发布 latest_commit。"
        blocked_reason = "公开盘口 raw 未就绪，历史补跑会使用不可靠盘口输入。"
        max_runs = 0
    else:
        status = "no_backfill_needed"
        next_action = "保持每4-5小时主动测试；若后续出现缺口，再进入 safe_no_latest_publish 补跑。"
        blocked_reason = ""
        max_runs = 0
    date_priority_rows = []
    for item in queue[:8]:
        date_priority_rows.append(
            {
                "rank": item.get("rank", ""),
                "display_date": item.get("display_date", ""),
                "priority_score": item.get("priority_score", 0),
                "reason": item.get("reason", ""),
                "mode": item.get("mode", "safe_no_latest_publish"),
                "action": "可立即补跑" if raw_ready else "等待 raw 刷新后补跑",
            }
        )
    slot_priority_rows = []
    for item in sorted(slot_rows, key=lambda row: int(row.get("missing_day_count") or 0), reverse=True)[:5]:
        missing = int(item.get("missing_day_count") or 0)
        slot_priority_rows.append(
            {
                "slot": item.get("slot", ""),
                "missing_day_count": missing,
                "coverage_ratio": item.get("coverage_ratio", 0),
                "action": "优先补齐此时段" if missing else "观察",
            }
        )
    return {
        "status": status,
        "safe_to_backfill_now": raw_ready and queue_count > 0,
        "raw_ready": raw_ready,
        "raw_status": raw_status,
        "raw_blocker_codes": blocker_codes,
        "queue_count": queue_count,
        "actionable_queue_count": actionable_queue_count,
        "blocked_queue_count": 0 if raw_ready else queue_count,
        "max_safe_backfill_runs": max_runs,
        "next_unlock_action": next_action,
        "blocked_reason": blocked_reason,
        "date_priority_rows": date_priority_rows,
        "slot_priority_rows": slot_priority_rows,
        "audit_basis": {
            "latest_audit_generated_at": latest_audit.get("generated_at", ""),
            "latest_audit_backfill_status": latest_audit.get("backfill_status", ""),
            "latest_audit_raw_status": latest_audit.get("raw_refresh_status", ""),
            "latest_backfill_status": backfill.get("status") or backfill.get("mode") or "not_run",
        },
        "decision_sentence": f"{next_action} 安全边界：只生成研究报告，不自动下注、不点击赔率、不加入投注单。",
        "safety_boundary": "只生成研究报告和补跑审计，不自动下注、不点击赔率、不加入投注单；raw/private 门禁失败时新下注金额保持 AUD 0。",
    }


def normalize_days(timeline: dict[str, Any]) -> list[dict[str, Any]]:
    rule = timeline.get("cadence_rule") or {}
    min_required = int(rule.get("min_analyses_per_day") or 4)
    rows = []
    for item in timeline.get("days") or []:
        covered = item.get("covered_slots") or []
        missing = item.get("missing_slots") or []
        needs_backfill = bool(item.get("needs_backfill") or item.get("backfill_reasons"))
        rows.append(
            {
                "report_date": item.get("report_date", ""),
                "display_date": item.get("display_date", ""),
                "status": "缺口" if needs_backfill else "完整",
                "effective_analysis_count": int(item.get("effective_analysis_count") or 0),
                "min_required_analysis_count": min_required,
                "covered_slot_count": len(covered),
                "missing_slot_count": len(missing),
                "formal_report_exists": bool(item.get("formal_report_exists")),
                "latest_status": item.get("latest_status", "missing"),
                "needs_backfill": needs_backfill,
                "backfill_reasons": item.get("backfill_reasons") or [],
                "covered_slots": covered,
                "missing_slots": missing,
            }
        )
    return rows


def build_slot_rows(timeline: dict[str, Any], days: list[dict[str, Any]]) -> list[dict[str, Any]]:
    target_slots = (timeline.get("cadence_rule") or {}).get("target_slots") or []
    day_count = max(1, len(days))
    rows = []
    for slot in target_slots:
        covered = sum(1 for day in days if slot in (day.get("covered_slots") or []))
        missing = sum(1 for day in days if slot in (day.get("missing_slots") or []))
        rows.append(
            {
                "slot": slot,
                "covered_day_count": covered,
                "missing_day_count": missing,
                "coverage_ratio": round(covered / day_count, 4),
                "status": "完整" if missing == 0 and days else "缺口",
            }
        )
    return rows


def normalize_queue(queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in queue[:10]:
        rows.append(
            {
                "rank": int(item.get("repair_rank") or len(rows) + 1),
                "report_date": item.get("report_date", ""),
                "display_date": item.get("display_date", ""),
                "priority_score": int(item.get("priority_score") or 0),
                "reason": item.get("reason", ""),
                "priority_reason": item.get("priority_reason", ""),
                "operation": item.get("operation", ""),
                "mode": item.get("mode", "safe_no_latest_publish"),
                "truthfulness_note": item.get("truthfulness_note", ""),
            }
        )
    return rows


def read_audit_trend(db_path: Path) -> list[dict[str, Any]]:
    if not db_path.exists():
        return []
    uri = f"file:{db_path.resolve()}?mode=ro&immutable=1"
    try:
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT generated_at, day_count, complete_day_count, missing_analysis_day_count,
                   missing_report_day_count, backfill_queue_count, backfill_status,
                   raw_refresh_ready, raw_refresh_status
            FROM active_timeline_audits
            ORDER BY generated_at DESC
            LIMIT 8
            """
        ).fetchall()
        conn.close()
    except sqlite3.Error:
        return []
    return [
        {
            "generated_at": str(row["generated_at"] or ""),
            "day_count": int(row["day_count"] or 0),
            "complete_day_count": int(row["complete_day_count"] or 0),
            "missing_analysis_day_count": int(row["missing_analysis_day_count"] or 0),
            "missing_report_day_count": int(row["missing_report_day_count"] or 0),
            "backfill_queue_count": int(row["backfill_queue_count"] or 0),
            "backfill_status": str(row["backfill_status"] or ""),
            "raw_refresh_ready": bool(row["raw_refresh_ready"]),
            "raw_refresh_status": str(row["raw_refresh_status"] or ""),
        }
        for row in rows
    ]


def build_comparison_rows(current_summary: dict[str, Any], trend: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(trend) < 2:
        return []
    previous = trend[1]
    metrics = [
        ("complete_day_count", "完整天数"),
        ("missing_analysis_day_count", "分析缺口日"),
        ("missing_report_day_count", "日报缺口日"),
        ("backfill_queue_count", "补跑队列"),
    ]
    rows = []
    for key, label in metrics:
        current = int(current_summary.get(key) or 0)
        old = int(previous.get(key) or 0)
        rows.append(
            {
                "metric": label,
                "current": current,
                "previous": old,
                "delta": current - old,
                "direction": "改善" if key != "complete_day_count" and current < old else "改善" if key == "complete_day_count" and current > old else "持平" if current == old else "恶化",
            }
        )
    return rows


def render_active_timeline_report_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    partial = payload.get("partial_daily_research") or {}
    lines = [
        "# TAB FIFA 主动测试时间线 Dashboard",
        "",
        "本报告检查 automation cadence：每天至少四次分析、每天一份正式日报，并给出补跑优先级。它只生成研究与补跑报告，不自动下注。",
        "",
        "## Executive Summary",
        "",
        f"- status: `{executive.get('status', '')}`",
        f"- ready_for_recurring_automation: `{bool(executive.get('ready_for_recurring_automation'))}`",
        f"- checked days: `{summary.get('day_count', 0)}`",
        f"- complete days: `{summary.get('complete_day_count', 0)}`",
        f"- missing analysis days: `{summary.get('missing_analysis_day_count', 0)}`",
        f"- missing report days: `{summary.get('missing_report_day_count', 0)}`",
        f"- backfill queue: `{summary.get('backfill_queue_count', 0)}`",
        f"- recovery_plan_status: `{summary.get('recovery_plan_status', '')}`",
        f"- safe_to_backfill_now: `{bool(summary.get('safe_to_backfill_now'))}`",
        f"- partial_daily_research: `{partial.get('status', 'missing')}` / ready `{bool(partial.get('ready'))}` / stake `AUD {partial.get('current_executable_new_stake_aud', 0)}`",
        f"- primary_gap: `{executive.get('primary_gap', '')}`",
        f"- recommended_next_action: {executive.get('recommended_next_action', '')}",
        "",
        "## Visual Summary",
        "",
        "```mermaid",
        "pie showData",
        f"  \"完整天数\" : {summary.get('complete_day_count', 0)}",
        f"  \"缺口天数\" : {max(0, int(summary.get('day_count') or 0) - int(summary.get('complete_day_count') or 0))}",
        "```",
        "",
        "## 补缺恢复计划",
        "",
        f"- status: `{(payload.get('backfill_recovery_plan') or {}).get('status', '')}`",
        f"- raw_status: `{(payload.get('backfill_recovery_plan') or {}).get('raw_status', '')}`",
        f"- blocked_queue_count: `{(payload.get('backfill_recovery_plan') or {}).get('blocked_queue_count', 0)}`",
        f"- next_unlock_action: {(payload.get('backfill_recovery_plan') or {}).get('next_unlock_action', '')}",
        f"- safety_boundary: {(payload.get('backfill_recovery_plan') or {}).get('safety_boundary', '')}",
        "",
        "| 顺序 | 日期 | 分数 | 缺口 | 动作 | 模式 |",
        "|---:|---|---:|---|---|---|",
    ]
    for row in ((payload.get("backfill_recovery_plan") or {}).get("date_priority_rows") or []):
        lines.append(
            f"| {row.get('rank', '')} | {md(row.get('display_date'))} | {row.get('priority_score', 0)} | {md(row.get('reason'))} | {md(row.get('action'))} | {md(row.get('mode'))} |"
        )
    if not ((payload.get("backfill_recovery_plan") or {}).get("date_priority_rows") or []):
        lines.append("| 0 | 无 | 0 | 当前无补跑队列 | 观察 | safe_no_latest_publish |")
    lines.extend(
        [
            "",
            "## 研究诊断日报补写",
            "",
            "| 状态 | Ready | 来源 | PDF | 日期版 PDF | 执行金额 | 用途 |",
            "|---|---:|---|---|---|---:|---|",
            "| {status} | {ready} | {source} | {pdf} | {dated_pdf} | AUD {stake} | {usage} |".format(
                status=md(partial.get("status")),
                ready="是" if partial.get("ready") else "否",
                source=md(partial.get("source")),
                pdf=md(partial.get("pdf")),
                dated_pdf=md(partial.get("dated_pdf")),
                stake=str(partial.get("current_executable_new_stake_aud", 0)),
                usage=md(partial.get("report_usage")),
            ),
        ]
    )
    lines.extend([
        "",
        "## 每日时间线",
        "",
        "| 日期 | 状态 | 有效分析 | 覆盖时段 | 缺失时段 | 日报 | 补跑原因 |",
        "|---|---|---:|---:|---:|---|---|",
    ])
    for row in payload.get("day_rows") or []:
        lines.append(
            f"| {md(row.get('display_date'))} | {md(row.get('status'))} | {row.get('effective_analysis_count', 0)}/{row.get('min_required_analysis_count', 4)} | {row.get('covered_slot_count', 0)} | {row.get('missing_slot_count', 0)} | {yes_no(row.get('formal_report_exists'))} | {md('；'.join(row.get('backfill_reasons') or []) or '无需补跑')} |"
        )
    lines.extend(["", "## 时段覆盖", "", "| 时段 | 覆盖天数 | 缺失天数 | 覆盖率 | 状态 |", "|---|---:|---:|---:|---|"])
    for row in payload.get("slot_rows") or []:
        lines.append(
            f"| {md(row.get('slot'))} | {row.get('covered_day_count', 0)} | {row.get('missing_day_count', 0)} | {pct(row.get('coverage_ratio'))} | {md(row.get('status'))} |"
        )
    lines.extend(["", "## 补跑优先队列", "", "| 顺序 | 日期 | 分数 | 缺口 | 排序依据 | 模式 |", "|---:|---|---:|---|---|---|"])
    for row in payload.get("backfill_queue_rows") or []:
        lines.append(
            f"| {row.get('rank', '')} | {md(row.get('display_date'))} | {row.get('priority_score', 0)} | {md(row.get('reason'))} | {md(row.get('priority_reason'))} | {md(row.get('mode'))} |"
        )
    lines.extend(["", "## 新旧对比", "", "| 指标 | 当前 | 上次 | 变化 | 方向 |", "|---|---:|---:|---:|---|"])
    for row in (payload.get("old_new_compare") or {}).get("rows") or []:
        lines.append(
            f"| {md(row.get('metric'))} | {row.get('current', 0)} | {row.get('previous', 0)} | {row.get('delta', 0):+} | {md(row.get('direction'))} |"
        )
    if not (payload.get("old_new_compare") or {}).get("rows"):
        lines.append("| 暂无上次审计 | 0 | 0 | +0 | 观察 |")
    lines.extend(["", f"> {payload.get('truthfulness_note', '')}"])
    return "\n".join(lines)


def write_active_timeline_report_pdf(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    day_rows = payload.get("day_rows") or []
    slot_rows = payload.get("slot_rows") or []
    queue = payload.get("backfill_queue_rows") or []
    compare_rows = (payload.get("old_new_compare") or {}).get("rows") or []
    recovery = payload.get("backfill_recovery_plan") or {}
    partial = payload.get("partial_daily_research") or {}
    charts = [
        chart_from_items(
            "每日完整度",
            [
                ("完整", summary.get("complete_day_count", 0)),
                ("缺口", max(0, int(summary.get("day_count") or 0) - int(summary.get("complete_day_count") or 0))),
            ],
            "#1F4E79",
        ),
        chart_from_items(
            "缺口类型",
            [
                ("分析缺口日", summary.get("missing_analysis_day_count", 0)),
                ("日报缺口日", summary.get("missing_report_day_count", 0)),
                ("补跑队列", summary.get("backfill_queue_count", 0)),
            ],
            "#C62828",
        ),
        chart_from_items("时段覆盖率", [(row.get("slot", ""), float(row.get("coverage_ratio") or 0) * 100) for row in slot_rows], "#247A5A"),
        chart_from_items("补跑优先级", [(row.get("display_date", ""), float(row.get("priority_score") or 0)) for row in queue], "#6A4C93"),
        chart_from_items("新旧变化", [(row.get("metric", ""), abs(float(row.get("delta") or 0))) for row in compare_rows], "#A56710"),
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA 主动测试时间线 Dashboard",
        subtitle="检查每4-5小时一次分析、每日正式报告和安全补跑队列；只生成研究报告，不自动下注。",
        summary_rows=[
            ("status", str(executive.get("status", ""))),
            ("ready_for_automation", str(bool(executive.get("ready_for_recurring_automation")))),
            ("checked days", str(summary.get("day_count", 0))),
            ("complete days", str(summary.get("complete_day_count", 0))),
            ("missing analysis days", str(summary.get("missing_analysis_day_count", 0))),
            ("missing report days", str(summary.get("missing_report_day_count", 0))),
            ("backfill queue", str(summary.get("backfill_queue_count", 0))),
            ("recovery plan", str(recovery.get("status", ""))),
            ("safe to backfill now", str(bool(recovery.get("safe_to_backfill_now")))),
            ("partial daily research", str(partial.get("status", "missing"))),
            ("partial new stake", f"AUD {partial.get('current_executable_new_stake_aud', 0)}"),
            ("primary gap", str(executive.get("primary_gap", ""))),
        ],
        charts=charts,
        table_headers=["日期", "状态", "有效分析", "覆盖", "缺失", "日报", "原因"],
        table_rows=[
            [
                str(row.get("display_date", "")),
                str(row.get("status", "")),
                f"{row.get('effective_analysis_count', 0)}/{row.get('min_required_analysis_count', 4)}",
                str(row.get("covered_slot_count", 0)),
                str(row.get("missing_slot_count", 0)),
                yes_no(row.get("formal_report_exists")),
                "；".join(row.get("backfill_reasons") or []) or "无需补跑",
            ]
            for row in day_rows
        ],
        extra_tables=[
            {
                "title": "时段覆盖",
                "headers": ["时段", "覆盖天数", "缺失天数", "覆盖率", "状态"],
                "rows": [
                    [
                        str(row.get("slot", "")),
                        str(row.get("covered_day_count", 0)),
                        str(row.get("missing_day_count", 0)),
                        pct(row.get("coverage_ratio")),
                        str(row.get("status", "")),
                    ]
                    for row in slot_rows
                ],
            },
            {
                "title": "补跑优先队列",
                "headers": ["顺序", "日期", "分数", "缺口", "模式"],
                "rows": [
                    [
                        str(row.get("rank", "")),
                        str(row.get("display_date", "")),
                        str(row.get("priority_score", 0)),
                        str(row.get("reason", "")),
                        str(row.get("mode", "")),
                    ]
                    for row in queue
                ],
            },
            {
                "title": "补缺恢复计划",
                "headers": ["顺序", "日期", "分数", "缺口", "动作", "模式"],
                "rows": [
                    [
                        str(row.get("rank", "")),
                        str(row.get("display_date", "")),
                        str(row.get("priority_score", 0)),
                        str(row.get("reason", "")),
                        str(row.get("action", "")),
                        str(row.get("mode", "")),
                    ]
                    for row in recovery.get("date_priority_rows", [])
                ],
            },
            {
                "title": "研究诊断日报补写",
                "headers": ["状态", "Ready", "来源", "PDF", "日期版PDF", "执行金额", "用途"],
                "rows": [
                    [
                        str(partial.get("status", "")),
                        "是" if partial.get("ready") else "否",
                        str(partial.get("source", "")),
                        str(partial.get("pdf", "")),
                        str(partial.get("dated_pdf", "")),
                        f"AUD {partial.get('current_executable_new_stake_aud', 0)}",
                        str(partial.get("report_usage", "")),
                    ]
                ],
            },
            {
                "title": "新旧审计对比",
                "headers": ["指标", "当前", "上次", "变化", "方向"],
                "rows": [
                    [
                        str(row.get("metric", "")),
                        str(row.get("current", 0)),
                        str(row.get("previous", 0)),
                        f"{int(row.get('delta') or 0):+}",
                        str(row.get("direction", "")),
                    ]
                    for row in compare_rows
                ],
            },
        ],
    )


def persist_active_timeline_report(db_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    public_payload = sanitize_public_payload(payload)
    summary = public_payload.get("summary") or {}
    executive = public_payload.get("executive_status") or {}
    recovery = public_payload.get("backfill_recovery_plan") or {}
    try:
        with connect_report_db(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS active_timeline_report_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    generated_at TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT '',
                    day_count INTEGER NOT NULL DEFAULT 0,
                    missing_analysis_day_count INTEGER NOT NULL DEFAULT 0,
                    missing_report_day_count INTEGER NOT NULL DEFAULT 0,
                    backfill_queue_count INTEGER NOT NULL DEFAULT 0,
                    safe_to_backfill_now INTEGER NOT NULL DEFAULT 0,
                    recovery_plan_status TEXT NOT NULL DEFAULT '',
                    raw_status TEXT NOT NULL DEFAULT '',
                    payload_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO active_timeline_report_snapshots(
                    snapshot_id, generated_at, status, day_count, missing_analysis_day_count,
                    missing_report_day_count, backfill_queue_count, safe_to_backfill_now,
                    recovery_plan_status, raw_status, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(public_payload.get("snapshot_id") or ""),
                    str(public_payload.get("generated_at") or ""),
                    str(executive.get("status") or ""),
                    int(summary.get("day_count") or 0),
                    int(summary.get("missing_analysis_day_count") or 0),
                    int(summary.get("missing_report_day_count") or 0),
                    int(summary.get("backfill_queue_count") or 0),
                    1 if recovery.get("safe_to_backfill_now") else 0,
                    str(recovery.get("status") or ""),
                    str(recovery.get("raw_status") or ""),
                    json.dumps(public_payload, ensure_ascii=False, sort_keys=True),
                ),
            )
            conn.commit()
        return {
            "status": "stored",
            "database": Path(db_path).name,
            "table": "active_timeline_report_snapshots",
            "snapshot_id": str(public_payload.get("snapshot_id") or ""),
        }
    except sqlite3.Error as exc:
        return {"status": "failed", "database": Path(db_path).name, "table": "active_timeline_report_snapshots", "error": str(exc)}


def load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def yes_no(value: Any) -> str:
    return "有" if bool(value) else "缺"


def pct(value: Any) -> str:
    try:
        return f"{float(value or 0) * 100:.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


def md(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")
