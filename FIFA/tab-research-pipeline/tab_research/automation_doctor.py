from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .artifact_compare import build_artifact_old_new_compare
from .artifacts import sanitize_public_payload
from .io import atomic_write_json, atomic_write_text
from .my_bets_bootstrap import build_private_position_bootstrap_status, private_dir_for_output
from .report_store import connect_report_db
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


AUTOMATION_DOCTOR_JSON_LATEST = "automation_doctor_latest.json"
AUTOMATION_DOCTOR_MD_LATEST = "automation_doctor_latest.md"
AUTOMATION_DOCTOR_PDF_LATEST = "automation_doctor_latest.pdf"
REPORT_TZ = ZoneInfo("Australia/Sydney")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def write_automation_doctor_bundle(output_dir: Path, db_path: Path | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    db_path = Path(db_path or output_dir / "tab_fifa_reports.sqlite3")
    payload = build_automation_doctor(output_dir)
    json_path = output_dir / AUTOMATION_DOCTOR_JSON_LATEST
    md_path = output_dir / AUTOMATION_DOCTOR_MD_LATEST
    pdf_path = output_dir / AUTOMATION_DOCTOR_PDF_LATEST
    payload["old_new_compare"] = build_artifact_old_new_compare(json_path, payload, automation_doctor_compare_metrics())
    atomic_write_json(json_path, payload)
    markdown = render_automation_doctor_markdown(payload)
    atomic_write_text(md_path, markdown)
    pdf_summary = write_automation_doctor_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    payload["storage"] = persist_automation_doctor(db_path, payload)
    atomic_write_json(json_path, payload)
    return payload


def build_automation_doctor(output_dir: Path) -> dict[str, Any]:
    readiness = load_json(output_dir / "automation_readiness_latest.json")
    intelligence = load_json(output_dir / "report_intelligence_latest.json")
    timeline = load_json(output_dir / "active_timeline_latest.json")
    latest_commit = load_json(output_dir / "latest_commit.json")
    raw_health = load_json(output_dir / "raw_refresh_health_latest.json")
    position_monitor = load_json(output_dir / "position_monitor_latest.json")
    bootstrap = current_private_position_bootstrap(output_dir, readiness, position_monitor)
    timeline_summary = timeline.get("summary") or {}
    timeline_health = intelligence.get("timeline_health") or {}
    automation_trend = build_automation_trend(timeline, timeline_health)
    gates = build_gate_rows(readiness, intelligence, timeline_summary, latest_commit, raw_health, bootstrap)
    commands = build_command_queue(readiness, timeline_summary, bootstrap, raw_health, automation_trend)
    blockers = build_blockers(readiness, timeline_summary, bootstrap, raw_health, automation_trend)
    ready_to_enter = all(item["ready"] for item in gates if item["required_for_entry"])
    doctor_dashboard = build_doctor_dashboard(gates, blockers, commands, timeline_summary, automation_trend, raw_health, bootstrap, ready_to_enter)
    summary = build_doctor_summary(
        gates=gates,
        blockers=blockers,
        commands=commands,
        timeline_summary=timeline_summary,
        automation_trend=automation_trend,
        raw_health=raw_health,
        bootstrap=bootstrap,
        dashboard=doctor_dashboard,
        readiness=readiness,
        latest_commit=latest_commit,
        ready_to_enter=ready_to_enter,
    )
    generated_at = datetime.now(REPORT_TZ).isoformat()
    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "snapshot_id": snapshot_id(generated_at),
        "mode": "automation_doctor",
        "purpose": "Automation Doctor Dashboard：进入每日自动化前的本地诊断、缺口修复计划和命令队列；只生成报告，不自动下注。",
        "summary": summary,
        "executive_status": {
            "ready_to_enter_recurring_automation": ready_to_enter,
            "formal_report_publish_ready": bool(readiness.get("formal_report_publish_ready")),
            "recurring_automation_ready": bool(readiness.get("recurring_automation_ready")),
            "trusted_report_date": latest_commit.get("report_date", ""),
            "trusted_run_id": latest_commit.get("run_id", ""),
            "primary_blocker": blockers[0]["title"] if blockers else "无阻塞项",
            "recommended_sequence": [item["title"] for item in commands[:4]],
        },
        "gate_rows": gates,
        "blockers": blockers,
        "command_queue": commands,
        "automation_trend": automation_trend,
        "doctor_dashboard": doctor_dashboard,
        "timeline_summary": {
            "day_count": int(timeline_summary.get("day_count") or 0),
            "complete_day_count": int(timeline_summary.get("complete_day_count") or 0),
            "missing_analysis_day_count": int(timeline_summary.get("missing_analysis_day_count") or 0),
            "missing_report_day_count": int(timeline_summary.get("missing_report_day_count") or 0),
            "backfill_queue_count": int(timeline_summary.get("backfill_queue_count") or 0),
        },
        "raw_refresh": {
            "ready": bool((readiness.get("raw_refresh") or {}).get("ready", raw_health.get("ready"))),
            "status": (readiness.get("raw_refresh") or {}).get("status", raw_health.get("status", "")),
            "ready_required": (readiness.get("raw_refresh") or {}).get("ready_required", ""),
            "blocker_codes": (readiness.get("raw_refresh") or {}).get("blocker_codes", raw_health.get("blocker_codes", [])),
            "recommended_next_action": (readiness.get("raw_refresh") or {}).get("recommended_next_action", raw_health.get("recommended_next_action", "")),
        },
        "private_position_bootstrap": {
            "ready": bool(bootstrap.get("ready")),
            "report_date": bootstrap.get("report_date", ""),
            "status": bootstrap.get("status", ""),
            "profile_exists": bool((bootstrap.get("profile") or {}).get("exists")),
            "snapshot_exists": bool((bootstrap.get("files") or {}).get("snapshot_exists")),
            "raw_text_exists": bool((bootstrap.get("files") or {}).get("raw_text_exists")),
            "diagnostics_exists": bool((bootstrap.get("files") or {}).get("diagnostics_exists")),
        },
        "source_artifacts": {
            "automation_readiness": "automation_readiness_latest.json" if readiness else "",
            "report_intelligence": "report_intelligence_latest.json" if intelligence else "",
            "active_timeline": "active_timeline_latest.json" if timeline else "",
            "latest_commit": "latest_commit.json" if latest_commit else "",
            "raw_refresh_health": "raw_refresh_health_latest.json" if raw_health else "",
            "position_monitor": "position_monitor_latest.json" if position_monitor else "",
        },
    }
    return payload


def build_doctor_summary(
    *,
    gates: list[dict[str, Any]],
    blockers: list[dict[str, str]],
    commands: list[dict[str, Any]],
    timeline_summary: dict[str, Any],
    automation_trend: dict[str, Any],
    raw_health: dict[str, Any],
    bootstrap: dict[str, Any],
    dashboard: dict[str, Any],
    readiness: dict[str, Any],
    latest_commit: dict[str, Any],
    ready_to_enter: bool,
) -> dict[str, Any]:
    required_gates = [row for row in gates if row.get("required_for_entry")]
    ready_required = [row for row in required_gates if row.get("ready")]
    p0_blockers = [row for row in blockers if row.get("priority") == "P0"]
    p1_blockers = [row for row in blockers if row.get("priority") == "P1"]
    p0_commands = [row for row in commands if row.get("priority") == "P0"]
    p1_commands = [row for row in commands if row.get("priority") == "P1"]
    raw_section = readiness.get("raw_refresh") or {}
    return {
        "entry_decision": dashboard.get("entry_decision", ""),
        "ready_to_enter_recurring_automation": bool(ready_to_enter),
        "automation_entry_status": "ready" if ready_to_enter else "blocked",
        "readiness_score": float(dashboard.get("readiness_score") or 0),
        "required_gate_ready_count": len(ready_required),
        "required_gate_count": len(required_gates),
        "blocked_required_gate_count": max(0, len(required_gates) - len(ready_required)),
        "p0_blocker_count": len(p0_blockers),
        "p1_blocker_count": len(p1_blockers),
        "blocker_count": len(blockers),
        "p0_command_count": len(p0_commands),
        "p1_command_count": len(p1_commands),
        "command_count": len(commands),
        "primary_blocker": blockers[0]["title"] if blockers else "无阻塞项",
        "next_best_action": dashboard.get("next_best_action", ""),
        "raw_refresh_ready": bool(raw_section.get("ready", raw_health.get("ready"))),
        "raw_refresh_status": raw_section.get("status", raw_health.get("status", "")),
        "raw_refresh_blocker_codes": raw_section.get("blocker_codes", raw_health.get("blocker_codes", [])),
        "private_position_ready": bool(bootstrap.get("ready")),
        "private_position_status": bootstrap.get("status", ""),
        "private_position_report_date": bootstrap.get("report_date", ""),
        "formal_report_publish_ready": bool(readiness.get("formal_report_publish_ready")),
        "recurring_automation_ready": bool(readiness.get("recurring_automation_ready")),
        "trusted_report_date": latest_commit.get("report_date", ""),
        "trusted_run_id": latest_commit.get("run_id", ""),
        "missing_analysis_day_count": int(timeline_summary.get("missing_analysis_day_count") or 0),
        "missing_report_day_count": int(timeline_summary.get("missing_report_day_count") or 0),
        "backfill_queue_count": int(timeline_summary.get("backfill_queue_count") or 0),
        "automation_trend_direction": automation_trend.get("trend_direction", "insufficient_history"),
        "repair_focus": automation_trend.get("repair_focus", ""),
        "repeated_missing_slot_count": len(automation_trend.get("repeated_missing_slots") or []),
        "repeated_missing_date_count": len(automation_trend.get("repeated_missing_dates") or []),
        "blocker_titles": [row.get("title", "") for row in blockers[:6]],
        "command_titles": [row.get("title", "") for row in commands[:6]],
        "decision_sentence": (
            "可进入每日自动报告；仍需保持不自动下注边界。"
            if ready_to_enter
            else f"暂不进入每日自动化：{blockers[0]['title'] if blockers else '存在未确认门禁'}；下一步 {dashboard.get('next_best_action', '复核门禁')}。"
        ),
        "safety_boundary": "只生成研究报告、诊断和人工复核队列；不自动下注、不点击赔率、不添加投注单。",
    }


def current_private_position_bootstrap(output_dir: Path, readiness: dict[str, Any], position_monitor: dict[str, Any]) -> dict[str, Any]:
    bootstrap = readiness.get("private_position_bootstrap") or {}
    current_report_date = str((position_monitor.get("summary") or {}).get("report_date") or "")
    bootstrap_report_date = str(bootstrap.get("report_date") or "")
    if current_report_date and current_report_date != bootstrap_report_date:
        return build_private_position_bootstrap_status(private_dir_for_output(output_dir), current_report_date)
    return bootstrap


def persist_automation_doctor(db_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    public_payload = sanitize_public_payload(payload)
    executive = public_payload.get("executive_status") or {}
    dashboard = public_payload.get("doctor_dashboard") or {}
    try:
        with connect_report_db(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS automation_doctor_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    generated_at TEXT NOT NULL DEFAULT '',
                    ready_to_enter_recurring_automation INTEGER NOT NULL DEFAULT 0,
                    formal_report_publish_ready INTEGER NOT NULL DEFAULT 0,
                    recurring_automation_ready INTEGER NOT NULL DEFAULT 0,
                    readiness_score REAL NOT NULL DEFAULT 0,
                    required_gate_ready_count INTEGER NOT NULL DEFAULT 0,
                    required_gate_count INTEGER NOT NULL DEFAULT 0,
                    p0_blocker_count INTEGER NOT NULL DEFAULT 0,
                    p1_blocker_count INTEGER NOT NULL DEFAULT 0,
                    backfill_queue_count INTEGER NOT NULL DEFAULT 0,
                    raw_status TEXT NOT NULL DEFAULT '',
                    private_position_status TEXT NOT NULL DEFAULT '',
                    primary_blocker TEXT NOT NULL DEFAULT '',
                    payload_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO automation_doctor_snapshots(
                    snapshot_id, generated_at, ready_to_enter_recurring_automation,
                    formal_report_publish_ready, recurring_automation_ready, readiness_score,
                    required_gate_ready_count, required_gate_count, p0_blocker_count,
                    p1_blocker_count, backfill_queue_count, raw_status,
                    private_position_status, primary_blocker, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(public_payload.get("snapshot_id") or ""),
                    str(public_payload.get("generated_at") or ""),
                    int(bool(executive.get("ready_to_enter_recurring_automation"))),
                    int(bool(executive.get("formal_report_publish_ready"))),
                    int(bool(executive.get("recurring_automation_ready"))),
                    float(dashboard.get("readiness_score") or 0),
                    int(dashboard.get("required_gate_ready_count") or 0),
                    int(dashboard.get("required_gate_count") or 0),
                    int(dashboard.get("p0_blocker_count") or 0),
                    int(dashboard.get("p1_blocker_count") or 0),
                    int(dashboard.get("backfill_queue_count") or 0),
                    str(dashboard.get("raw_status") or ""),
                    str(dashboard.get("private_position_status") or ""),
                    str(executive.get("primary_blocker") or ""),
                    json.dumps(public_payload, ensure_ascii=False, sort_keys=True),
                ),
            )
            conn.commit()
        return {"status": "stored", "database": Path(db_path).name, "table": "automation_doctor_snapshots"}
    except sqlite3.Error as exc:
        return {"status": "failed", "database": Path(db_path).name, "error": str(exc)}


def automation_doctor_compare_metrics() -> list[tuple[str, str]]:
    return [
        ("ready_to_enter_recurring_automation", "executive_status.ready_to_enter_recurring_automation"),
        ("formal_report_publish_ready", "executive_status.formal_report_publish_ready"),
        ("recurring_automation_ready", "executive_status.recurring_automation_ready"),
        ("primary_blocker", "executive_status.primary_blocker"),
        ("readiness_score", "doctor_dashboard.readiness_score"),
        ("required_gate_ready_count", "doctor_dashboard.required_gate_ready_count"),
        ("p0_blocker_count", "doctor_dashboard.p0_blocker_count"),
        ("p1_blocker_count", "doctor_dashboard.p1_blocker_count"),
        ("backfill_queue_count", "doctor_dashboard.backfill_queue_count"),
        ("raw_status", "doctor_dashboard.raw_status"),
        ("private_position_status", "doctor_dashboard.private_position_status"),
    ]


def build_doctor_dashboard(
    gates: list[dict[str, Any]],
    blockers: list[dict[str, str]],
    commands: list[dict[str, Any]],
    timeline_summary: dict[str, Any],
    automation_trend: dict[str, Any],
    raw_health: dict[str, Any],
    bootstrap: dict[str, Any],
    ready_to_enter: bool,
) -> dict[str, Any]:
    required_gates = [row for row in gates if row.get("required_for_entry")]
    ready_required = [row for row in required_gates if row.get("ready")]
    p0_blockers = [row for row in blockers if row.get("priority") == "P0"]
    p1_blockers = [row for row in blockers if row.get("priority") == "P1"]
    p0_commands = [row for row in commands if row.get("priority") == "P0"]
    return {
        "title": "Automation Doctor Dashboard",
        "entry_decision": "可进入每日自动化" if ready_to_enter else "暂不进入每日自动化",
        "readiness_score": round(len(ready_required) / len(required_gates), 4) if required_gates else 0.0,
        "required_gate_ready_count": len(ready_required),
        "required_gate_count": len(required_gates),
        "p0_blocker_count": len(p0_blockers),
        "p1_blocker_count": len(p1_blockers),
        "p0_command_count": len(p0_commands),
        "backfill_queue_count": int(timeline_summary.get("backfill_queue_count") or 0),
        "raw_status": raw_health.get("status", ""),
        "private_position_status": bootstrap.get("status", ""),
        "repair_focus": automation_trend.get("repair_focus", ""),
        "next_best_action": commands[0]["title"] if commands else "保持观察",
        "reading_path": [
            "先看 entry_decision 和 p0_blocker_count。",
            "再看 next_best_action 执行哪个只读修复动作。",
            "最后看 repeated missing slots/dates 判断 4 小时节奏缺口。",
        ],
    }


def build_automation_trend(timeline: dict[str, Any], timeline_health: dict[str, Any]) -> dict[str, Any]:
    trend_summary = timeline_health.get("audit_trend_summary") or {}
    slot_heatmap = timeline_health.get("slot_heatmap") or build_slot_heatmap_from_timeline(timeline)
    slot_counts: dict[str, int] = {}
    date_rows = []
    for row in slot_heatmap:
        missing_cells = [cell for cell in row.get("cells") or [] if cell.get("status") == "missing"]
        missing_count = len(missing_cells)
        if missing_count:
            date_rows.append(
                {
                    "date": row.get("date", ""),
                    "missing_slot_count": missing_count,
                    "effective_analysis_count": int(row.get("effective_analysis_count") or 0),
                    "formal_report_exists": bool(row.get("formal_report_exists")),
                    "reason": row.get("reason", ""),
                }
            )
        for cell in missing_cells:
            label = str(cell.get("label") or short_slot_label(str(cell.get("slot") or "")))
            slot_counts[label] = slot_counts.get(label, 0) + 1
    repeated_slots = [
        {"slot": slot, "missing_count": count}
        for slot, count in sorted(slot_counts.items(), key=lambda item: (-item[1], item[0]))
    ]
    repeated_dates = sorted(date_rows, key=lambda item: (-int(item.get("missing_slot_count") or 0), item.get("date") or ""))
    backfill_queue_preview = build_backfill_queue_preview(timeline.get("backfill_queue") or [])
    return {
        "audit_count": int(trend_summary.get("audit_count") or timeline_health.get("audit_history_count") or 0),
        "latest_complete_ratio": float(trend_summary.get("latest_complete_ratio") or 0),
        "latest_gap_count": int(trend_summary.get("latest_gap_count") or 0),
        "raw_ready_audit_count": int(trend_summary.get("raw_ready_audit_count") or 0),
        "trend_direction": trend_summary.get("trend_direction") or "insufficient_history",
        "repeated_missing_slots": repeated_slots[:5],
        "repeated_missing_dates": repeated_dates[:5],
        "backfill_queue_preview": backfill_queue_preview,
        "repair_focus": build_repair_focus(repeated_slots, repeated_dates),
    }


def build_backfill_queue_preview(queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in queue[:5]:
        rows.append(
            {
                "rank": int(item.get("repair_rank") or len(rows) + 1),
                "date": item.get("display_date", ""),
                "score": int(item.get("priority_score") or 0),
                "reason": item.get("reason", ""),
                "priority_reason": item.get("priority_reason", ""),
            }
        )
    return rows


def build_slot_heatmap_from_timeline(timeline: dict[str, Any]) -> list[dict[str, Any]]:
    slots = [str(slot) for slot in (timeline.get("cadence_rule") or {}).get("target_slots") or []]
    rows = []
    for item in (timeline.get("days") or [])[-8:]:
        covered = set(item.get("covered_slots") or [])
        missing = set(item.get("missing_slots") or [])
        cells = []
        for slot in slots:
            cells.append(
                {
                    "slot": slot,
                    "label": short_slot_label(slot),
                    "status": "covered" if slot in covered else "missing" if slot in missing else "unknown",
                }
            )
        rows.append(
            {
                "date": item.get("display_date", ""),
                "effective_analysis_count": int(item.get("effective_analysis_count") or 0),
                "formal_report_exists": bool(item.get("formal_report_exists")),
                "reason": "；".join(item.get("backfill_reasons") or []),
                "cells": cells,
            }
        )
    return rows


def short_slot_label(slot: str) -> str:
    return str(slot or "").replace(":00", "").replace("-", "-")


def build_repair_focus(repeated_slots: list[dict[str, Any]], repeated_dates: list[dict[str, Any]]) -> str:
    slot_text = "、".join(f"{row['slot']}({row['missing_count']})" for row in repeated_slots[:3]) or "暂无时段缺口"
    date_text = "、".join(f"{row['date']}({row['missing_slot_count']})" for row in repeated_dates[:3]) or "暂无日期缺口"
    return f"优先补齐日期：{date_text}；重点时段：{slot_text}。"


def build_gate_rows(
    readiness: dict[str, Any],
    intelligence: dict[str, Any],
    timeline_summary: dict[str, Any],
    latest_commit: dict[str, Any],
    raw_health: dict[str, Any],
    bootstrap: dict[str, Any],
) -> list[dict[str, Any]]:
    raw_section = readiness.get("raw_refresh") or {}
    public_safety = readiness.get("public_safety") or {}
    technical = readiness.get("technical_preflight") or {}
    candidate = readiness.get("automation_candidate") or {}
    return [
        gate("可信最新报告", bool(latest_commit.get("public_artifact_safety_ready")), "latest_commit.json 可用且公开安全", True),
        gate("公开盘口 freshness", bool(raw_section.get("ready", raw_health.get("ready"))), raw_section.get("recommended_next_action") or raw_health.get("recommended_next_action", ""), True),
        gate("私有持仓快照", bool(bootstrap.get("ready")), bootstrap.get("next_action", "补齐私有持仓快照。"), True),
        gate("当前日报发布门禁", bool(readiness.get("formal_report_publish_ready")), "formal report publish gate", True),
        gate("主动测试节奏", not bool(timeline_summary.get("backfill_queue_count")), "每日 4 次分析且 1 份日报", True),
        gate("公开产物安全", bool(public_safety.get("output_safety_ready")) and bool(public_safety.get("artifact_safety_ready", True)), "public-safety gate", True),
        gate("技术预检", bool(technical.get("publication_clear")), "technical preflight publication_clear", True),
        gate("研究智能层", bool(intelligence.get("executive_status")), "report intelligence latest bundle", False),
        gate("调度候选配置", bool(candidate.get("ready")), candidate.get("status", ""), False),
        gate("用户调度授权", bool(readiness.get("recurring_automation_ready")), "未授权前保持手动报告生成", True),
    ]


def gate(name: str, ready: bool, evidence: str, required_for_entry: bool) -> dict[str, Any]:
    return {
        "name": name,
        "ready": bool(ready),
        "status": "ready" if ready else "blocked",
        "evidence": evidence or "",
        "required_for_entry": bool(required_for_entry),
    }


def build_blockers(
    readiness: dict[str, Any],
    timeline_summary: dict[str, Any],
    bootstrap: dict[str, Any],
    raw_health: dict[str, Any],
    automation_trend: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    trend = automation_trend or {}
    raw_ready = bool((readiness.get("raw_refresh") or {}).get("ready", raw_health.get("ready")))
    if not raw_ready:
        blockers.append(blocker("P0", "公开盘口 raw 不新鲜或不可用", "先完成只读公开盘口刷新，再允许生成当日正式报告。"))
    if not bootstrap.get("ready"):
        blockers.append(blocker("P0", "私有持仓快照缺失", "完成本地只读私有持仓 capture/import，之后重跑日报。"))
    if not readiness.get("formal_report_publish_ready"):
        blockers.append(blocker("P0", "当前 attempted run 未过发布门禁", "修复 P0 阻塞后重跑日报，不推进 latest 成功指针。"))
    if int(timeline_summary.get("backfill_queue_count") or 0) > 0:
        focus = trend.get("repair_focus") or "运行安全补跑，补齐每日分析/日报缺口；补跑不发布 latest。"
        blockers.append(blocker("P1", "主动测试存在缺口", f"{focus} 补跑不发布 latest。"))
    if not readiness.get("recurring_automation_ready"):
        blockers.append(blocker("P1", "调度入口尚未进入 ready 状态", "在所有技术门禁通过后再等待用户授权 recurring automation。"))
    return blockers


def blocker(priority: str, title: str, impact: str) -> dict[str, str]:
    return {"priority": priority, "title": title, "impact": impact}


def build_command_queue(
    readiness: dict[str, Any],
    timeline_summary: dict[str, Any],
    bootstrap: dict[str, Any],
    raw_health: dict[str, Any],
    automation_trend: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    report_date = str(bootstrap.get("report_date") or (readiness.get("latest_commit") or {}).get("report_date") or "DDMMYYYY")
    raw_ready = bool((readiness.get("raw_refresh") or {}).get("ready", raw_health.get("ready")))
    trend = automation_trend or {}
    commands: list[dict[str, Any]] = []
    if not raw_ready:
        commands.append(
            command(
                "P0",
                "恢复公开盘口 raw 数据源",
                "接入官方/授权 feed 或导入用户导出的 public raw snapshot",
                "TAB 拒绝 AI controlled access；不要使用 headed fallback、验证码绕过、指纹伪装或 stealth browser。raw 未恢复前日报继续 fail-closed。",
                False,
            )
        )
    if not bootstrap.get("ready"):
        commands.append(
            command(
                "P0",
                "建立私有持仓读取 profile",
                f"TAB_FIFA_HEADLESS=0 node scripts/capture_tab_my_bets_readonly.mjs --report-date {report_date} --wait-for-login-ms 600000",
                "打开本地只读 capture 窗口，用户完成 TAB 授权后保存私有 raw text；不保存密码、不下注。",
                True,
            )
        )
        commands.append(
            command(
                "P0",
                "导入私有持仓快照",
                f"python3 import_my_bets_snapshot.py --source <private_raw_text_{report_date}.txt> --report-date {report_date}",
                "把私有 raw text 转成 private snapshot，供 technical preflight 使用。",
                False,
            )
        )
    if int(timeline_summary.get("backfill_queue_count") or 0) > 0:
        commands.append(
            command(
                "P1",
                "补齐主动测试缺口",
                "python3 scripts/app_backfill_worker.py --max-backfill-runs 3",
                f"安全补跑缺失日报/分析并刷新 Downloads app；不会发布 latest。{trend.get('repair_focus') or ''}",
                False,
            )
        )
    commands.extend(
        [
            command(
                "P1",
                "重跑正式日报",
                "TAB_FIFA_REFRESH_RAW=reuse_fresh python3 run_daily_report.py",
                "在 raw 与私有持仓都就绪后生成正式中文 PDF、入库、对比旧报告并更新 latest。",
                False,
            ),
            command(
                "P1",
                "复核 automation readiness",
                "scripts/run_tab_fifa_daily_automation.sh --verify-only",
                "跑 hermetic verifier 与 readiness sidecars，确认进入调度前的离线门禁。",
                False,
            ),
            command(
                "P2",
                "刷新本地入口",
                "python3 scripts/build_downloads_app_entry.py",
                "复制最新公开资产到 Downloads app。",
                False,
            ),
        ]
    )
    return commands


def command(priority: str, title: str, shell: str, expected_effect: str, needs_user_presence: bool) -> dict[str, Any]:
    return {
        "priority": priority,
        "title": title,
        "command": shell,
        "expected_effect": expected_effect,
        "needs_user_presence": bool(needs_user_presence),
        "safety": "只读报告/诊断；不自动下注，不点击赔率，不提交投注单。",
    }


def render_automation_doctor_markdown(payload: dict[str, Any]) -> str:
    status = payload.get("executive_status") or {}
    summary = payload.get("summary") or {}
    trend = payload.get("automation_trend") or {}
    dashboard = payload.get("doctor_dashboard") or {}
    compare = payload.get("old_new_compare") or {}
    lines = [
        "# TAB FIFA Automation Doctor Dashboard",
        "",
        "本报告给出进入每日自动化前的本地诊断和命令队列。它只生成报告与诊断，不自动下注。",
        "",
        "## Executive Summary",
        "",
        f"- ready_to_enter_recurring_automation: `{bool(status.get('ready_to_enter_recurring_automation'))}`",
        f"- formal_report_publish_ready: `{bool(status.get('formal_report_publish_ready'))}`",
        f"- recurring_automation_ready: `{bool(status.get('recurring_automation_ready'))}`",
        f"- trusted_report_date: `{status.get('trusted_report_date', '')}`",
        f"- primary_blocker: {status.get('primary_blocker', '')}",
        f"- summary_decision: {summary.get('decision_sentence', '')}",
        "",
        "## Summary For Aggregation",
        "",
        "| 指标 | 值 |",
        "|---|---:|",
        f"| automation_entry_status | {md(summary.get('automation_entry_status'))} |",
        f"| readiness_score | {float(summary.get('readiness_score') or 0) * 100:.2f}% |",
        f"| required gates | {int(summary.get('required_gate_ready_count') or 0)}/{int(summary.get('required_gate_count') or 0)} |",
        f"| P0/P1 blockers | {int(summary.get('p0_blocker_count') or 0)}/{int(summary.get('p1_blocker_count') or 0)} |",
        f"| raw_refresh_status | {md(summary.get('raw_refresh_status'))} |",
        f"| private_position_status | {md(summary.get('private_position_status'))} |",
        f"| missing analysis/report days | {int(summary.get('missing_analysis_day_count') or 0)}/{int(summary.get('missing_report_day_count') or 0)} |",
        f"| backfill queue | {int(summary.get('backfill_queue_count') or 0)} |",
        f"| next_best_action | {md(summary.get('next_best_action'))} |",
        "",
        "## Automation Doctor Dashboard",
        "",
        f"- 入场判断：`{dashboard.get('entry_decision', '')}`",
        f"- 入场门禁得分：`{float(dashboard.get('readiness_score') or 0) * 100:.2f}%`",
        f"- P0 阻塞：`{dashboard.get('p0_blocker_count', 0)}`；P1 阻塞：`{dashboard.get('p1_blocker_count', 0)}`",
        f"- 下一步动作：`{dashboard.get('next_best_action', '')}`",
        f"- 修复焦点：{dashboard.get('repair_focus', '')}",
        "",
        "```mermaid",
        "pie showData",
        f'  "ready gates" : {int(dashboard.get("required_gate_ready_count") or 0)}',
        f'  "blocked gates" : {max(0, int(dashboard.get("required_gate_count") or 0) - int(dashboard.get("required_gate_ready_count") or 0))}',
        "```",
        "",
        "| Dashboard 指标 | 值 |",
        "|---|---:|",
        f"| required gate ready | {int(dashboard.get('required_gate_ready_count') or 0)}/{int(dashboard.get('required_gate_count') or 0)} |",
        f"| P0 commands | {int(dashboard.get('p0_command_count') or 0)} |",
        f"| backfill queue | {int(dashboard.get('backfill_queue_count') or 0)} |",
        f"| raw status | {md(dashboard.get('raw_status'))} |",
        f"| private position | {md(dashboard.get('private_position_status'))} |",
        "",
        "## Gate Matrix",
        "",
        "| Gate | Status | Required | Evidence |",
        "|---|---|---:|---|",
    ]
    for row in payload.get("gate_rows") or []:
        lines.append(
            f"| {md(row.get('name'))} | {md(row.get('status'))} | {int(bool(row.get('required_for_entry')))} | {md(row.get('evidence'))} |"
        )
    lines.extend(["", "## Command Queue", "", "| 优先级 | 动作 | 命令 | 效果 | 需要人在场 |", "|---|---|---|---|---:|"])
    for item in payload.get("command_queue") or []:
        lines.append(
            f"| {md(item.get('priority'))} | {md(item.get('title'))} | `{md(item.get('command'))}` | {md(item.get('expected_effect'))} | {int(bool(item.get('needs_user_presence')))} |"
        )
    lines.extend(["", "## Blockers", "", "| 优先级 | 阻塞 | 影响 |", "|---|---|---|"])
    for item in payload.get("blockers") or []:
        lines.append(f"| {md(item.get('priority'))} | {md(item.get('title'))} | {md(item.get('impact'))} |")
    lines.extend(
        [
            "",
            "## 修复优先级趋势",
            "",
            f"- 历史审计次数：`{trend.get('audit_count', 0)}`",
            f"- 最新完整率：`{float(trend.get('latest_complete_ratio') or 0) * 100:.2f}%`",
            f"- 最新缺口数：`{trend.get('latest_gap_count', 0)}`",
            f"- 趋势方向：`{trend.get('trend_direction', 'insufficient_history')}`",
            f"- 修复焦点：{trend.get('repair_focus', '')}",
            "",
            "| 补跑顺序 | 日期 | 分数 | 原因 | 排序依据 |",
            "|---:|---|---:|---|---|",
        ]
    )
    for row in trend.get("backfill_queue_preview") or []:
        lines.append(
            f"| {int(row.get('rank') or 0)} | {md(row.get('date'))} | {int(row.get('score') or 0)} | {md(row.get('reason'))} | {md(row.get('priority_reason'))} |"
        )
    lines.extend(
        [
            "",
            "| 缺失时段 | 缺失次数 |",
            "|---|---:|",
        ]
    )
    for row in trend.get("repeated_missing_slots") or []:
        lines.append(f"| {md(row.get('slot'))} | {int(row.get('missing_count') or 0)} |")
    lines.extend(["", "| 缺失日期 | 缺失时段数 | 有效分析 | 日报 | 原因 |", "|---|---:|---:|---|---|"])
    for row in trend.get("repeated_missing_dates") or []:
        lines.append(
            f"| {md(row.get('date'))} | {int(row.get('missing_slot_count') or 0)} | {int(row.get('effective_analysis_count') or 0)} | {'有' if row.get('formal_report_exists') else '缺失'} | {md(row.get('reason'))} |"
        )
    lines.extend(
        [
            "",
            "## old_new_compare / 新旧诊断变化",
            "",
            f"- compare_status: `{compare.get('status', '')}`",
            f"- previous_generated_at: `{compare.get('previous_generated_at', '')}`",
            f"- changed_count: `{compare.get('changed_count', 0)}/{compare.get('metric_count', 0)}`",
            f"- summary: {md(compare.get('summary'))}",
            "",
            "| 指标 | 当前 | 上一版 | 变化 |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in compare.get("rows") or []:
        lines.append(f"| {md(row.get('metric'))} | {md(row.get('current'))} | {md(row.get('previous'))} | {md(row.get('delta'))} |")
    return "\n".join(lines)


def write_automation_doctor_pdf(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    status = payload.get("executive_status") or {}
    summary = payload.get("summary") or {}
    timeline = payload.get("timeline_summary") or {}
    trend = payload.get("automation_trend") or {}
    dashboard = payload.get("doctor_dashboard") or {}
    compare = payload.get("old_new_compare") or {}
    charts = [
        chart_from_items("Automation Doctor Dashboard", doctor_dashboard_items(dashboard), "#1F4E79"),
        chart_from_items("入场门禁", gate_items(payload.get("gate_rows") or [], required_only=True), "#1F4E79"),
        chart_from_items("全部门禁", gate_items(payload.get("gate_rows") or [], required_only=False), "#247A5A"),
        chart_from_items("缺口回测", timeline_items(timeline), "#A56710"),
        chart_from_items("反复缺失时段", missing_slot_items(trend), "#C62828"),
        chart_from_items("反复缺失日期", missing_date_items(trend), "#A56710"),
        chart_from_items("命令优先级", command_priority_items(payload.get("command_queue") or []), "#C62828"),
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA Automation Doctor Dashboard",
        subtitle="进入每日自动化前的诊断、阻塞项、命令队列和 4 小时节奏修复视图；只生成报告，不自动下注。",
        summary_rows=[
            ("entry_decision", str(dashboard.get("entry_decision", ""))),
            ("readiness_score", f"{float(dashboard.get('readiness_score') or 0) * 100:.2f}%"),
            ("ready_to_enter", str(bool(status.get("ready_to_enter_recurring_automation")))),
            ("formal_publish", str(bool(status.get("formal_report_publish_ready")))),
            ("recurring_ready", str(bool(status.get("recurring_automation_ready")))),
            ("trusted_report_date", str(status.get("trusted_report_date", ""))),
            ("primary_blocker", str(status.get("primary_blocker", ""))),
            ("next_best_action", str(summary.get("next_best_action", ""))),
        ],
        charts=charts,
        table_headers=["Gate", "Status", "Required", "Evidence"],
        table_rows=[
            [str(row.get("name", "")), str(row.get("status", "")), str(int(bool(row.get("required_for_entry")))), str(row.get("evidence", ""))]
            for row in (payload.get("gate_rows") or [])
        ],
        extra_tables=[
            {
                "title": "Automation Doctor Dashboard",
                "headers": ["Metric", "Value"],
                "rows": [
                    ["Entry decision", str(dashboard.get("entry_decision", ""))],
                    ["Required gates", f"{dashboard.get('required_gate_ready_count', 0)}/{dashboard.get('required_gate_count', 0)}"],
                    ["P0 blockers", str(int(dashboard.get("p0_blocker_count") or 0))],
                    ["P1 blockers", str(int(dashboard.get("p1_blocker_count") or 0))],
                    ["Next action", str(dashboard.get("next_best_action", ""))],
                    ["Repair focus", str(dashboard.get("repair_focus", ""))],
                ],
            },
            {
                "title": "Command Queue",
                "headers": ["Priority", "Action", "Command", "Needs User"],
                "rows": [
                    [item.get("priority", ""), item.get("title", ""), item.get("command", ""), str(int(bool(item.get("needs_user_presence"))))]
                    for item in (payload.get("command_queue") or [])[:8]
                ],
            },
            {
                "title": "Repeated Missing Slots",
                "headers": ["Slot", "Missing Count"],
                "rows": [
                    [row.get("slot", ""), str(int(row.get("missing_count") or 0))]
                    for row in (trend.get("repeated_missing_slots") or [])[:8]
                ],
            },
            {
                "title": "Repeated Missing Dates",
                "headers": ["Date", "Missing Slots", "Effective Analyses", "Report", "Reason"],
                "rows": [
                    [
                        row.get("date", ""),
                        str(int(row.get("missing_slot_count") or 0)),
                        str(int(row.get("effective_analysis_count") or 0)),
                        "有" if row.get("formal_report_exists") else "缺失",
                        row.get("reason", ""),
                    ]
                    for row in (trend.get("repeated_missing_dates") or [])[:8]
                ],
            },
            {
                "title": "Backfill Queue Priority",
                "headers": ["Rank", "Date", "Score", "Reason", "Priority Basis"],
                "rows": [
                    [
                        str(int(row.get("rank") or 0)),
                        row.get("date", ""),
                        str(int(row.get("score") or 0)),
                        row.get("reason", ""),
                        row.get("priority_reason", ""),
                    ]
                    for row in (trend.get("backfill_queue_preview") or [])[:8]
                ],
            },
            {
                "title": "新旧诊断变化",
                "headers": ["指标", "当前", "上一版", "变化"],
                "rows": [
                    [str(row.get("metric", "")), str(row.get("current", "")), str(row.get("previous", "")), str(row.get("delta", ""))]
                    for row in (compare.get("rows") or [])
                ],
            }
        ],
    )


def gate_items(rows: list[dict[str, Any]], required_only: bool) -> list[tuple[str, float]]:
    items = []
    for row in rows:
        if required_only and not row.get("required_for_entry"):
            continue
        items.append((str(row.get("name", "")), 1.0 if row.get("ready") else 0.0))
    return items


def doctor_dashboard_items(dashboard: dict[str, Any]) -> list[tuple[str, float]]:
    return [
        ("ready gates", float(dashboard.get("required_gate_ready_count") or 0)),
        ("blocked gates", max(0.0, float(dashboard.get("required_gate_count") or 0) - float(dashboard.get("required_gate_ready_count") or 0))),
        ("P0 blockers", float(dashboard.get("p0_blocker_count") or 0)),
        ("backfill queue", float(dashboard.get("backfill_queue_count") or 0)),
    ]


def timeline_items(timeline: dict[str, Any]) -> list[tuple[str, float]]:
    return [
        ("完整日", float(timeline.get("complete_day_count") or 0)),
        ("分析缺口日", float(timeline.get("missing_analysis_day_count") or 0)),
        ("日报缺口日", float(timeline.get("missing_report_day_count") or 0)),
        ("待补队列", float(timeline.get("backfill_queue_count") or 0)),
    ]


def command_priority_items(commands: list[dict[str, Any]]) -> list[tuple[str, float]]:
    scores = {"P0": 100.0, "P1": 70.0, "P2": 40.0}
    return [(str(item.get("title", "")), scores.get(str(item.get("priority")), 10.0)) for item in commands[:7]]


def missing_slot_items(trend: dict[str, Any]) -> list[tuple[str, float]]:
    return [
        (str(row.get("slot", "")), float(row.get("missing_count") or 0))
        for row in (trend.get("repeated_missing_slots") or [])
    ]


def missing_date_items(trend: dict[str, Any]) -> list[tuple[str, float]]:
    return [
        (str(row.get("date", "")), float(row.get("missing_slot_count") or 0))
        for row in (trend.get("repeated_missing_dates") or [])
    ]


def md(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")


def snapshot_id(generated_at: str) -> str:
    return "automation-doctor-" + generated_at.replace(":", "").replace("+", "-").replace(".", "-")
