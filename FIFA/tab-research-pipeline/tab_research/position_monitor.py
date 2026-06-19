from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .artifacts import sanitize_public_payload
from .io import atomic_write_json, atomic_write_text
from .my_bets import load_snapshot
from .my_bets_bootstrap import build_private_position_bootstrap_status, private_dir_for_output
from .preflight import validate_private_position_snapshot
from .report_store import connect_report_db
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


POSITION_MONITOR_JSON_LATEST = "position_monitor_latest.json"
POSITION_MONITOR_MD_LATEST = "position_monitor_latest.md"
POSITION_MONITOR_PDF_LATEST = "position_monitor_latest.pdf"
REPORT_TZ = ZoneInfo("Australia/Sydney")


def write_position_monitor_bundle(output_dir: Path, db_path: Path | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    db_path = Path(db_path or output_dir / "tab_fifa_reports.sqlite3")
    payload = build_position_monitor(output_dir)
    json_path = output_dir / POSITION_MONITOR_JSON_LATEST
    md_path = output_dir / POSITION_MONITOR_MD_LATEST
    pdf_path = output_dir / POSITION_MONITOR_PDF_LATEST

    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_position_monitor_markdown(payload))
    pdf_summary = write_position_monitor_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    payload["storage"] = persist_position_monitor(db_path, payload)
    atomic_write_json(json_path, payload)
    return payload


def build_position_monitor(output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    readiness = load_json(output_dir / "automation_readiness_latest.json")
    preflight = load_json(output_dir / "automation_preflight_latest.json")
    latest_commit = load_json(output_dir / "latest_commit.json")
    report_date = position_report_date(preflight, readiness, latest_commit)
    private_dir = private_dir_for_output(output_dir)
    bootstrap = build_private_position_bootstrap_status(private_dir, report_date) if report_date else {}
    preflight = bootstrap.get("preflight") or {}
    snapshot_public = snapshot_public_summary(private_dir, report_date) if report_date else empty_snapshot_summary()
    raw_health = load_json(output_dir / "raw_refresh_health_latest.json")
    timeline = load_json(output_dir / "active_timeline_latest.json")
    previous = latest_position_monitor(output_dir / "tab_fifa_reports.sqlite3")
    rows = build_monitor_rows(bootstrap, snapshot_public, raw_health, timeline)
    status = monitor_status(bootstrap, snapshot_public)
    generated_at = datetime.now(REPORT_TZ).isoformat()
    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "monitor_id": monitor_id(generated_at),
        "mode": "position_monitor_dashboard",
        "purpose": "持仓、余额与累计收益率监控 Dashboard：只输出公开安全的聚合状态和下一步，不泄露私有下注明细，不自动下注。",
        "executive_status": {
            "status": status,
            "decision": status_decision(status),
            "public_report_action": public_report_action(status),
            "private_metrics_available": bool(snapshot_public.get("ready")),
            "recommended_next_action": recommended_next_action(bootstrap, raw_health),
        },
        "summary": {
            "report_date": report_date,
            "snapshot_ready": bool(snapshot_public.get("ready")),
            "snapshot_status": snapshot_public.get("status", "missing"),
            "snapshot_issue_count": len(snapshot_public.get("issues") or []),
            "raw_text_exists": bool((bootstrap.get("files") or {}).get("raw_text_exists")),
            "snapshot_exists": bool((bootstrap.get("files") or {}).get("snapshot_exists")),
            "diagnostics_exists": bool((bootstrap.get("files") or {}).get("diagnostics_exists")),
            "profile_exists": bool((bootstrap.get("profile") or {}).get("exists")),
            "preflight_status": preflight.get("status", ""),
            "preflight_blocking_reason": preflight.get("blocking_reason", ""),
            "preflight_next_safe_action": preflight.get("next_safe_action", ""),
            "login_window_required": bool(preflight.get("login_window_required")),
            "manual_step_required": bool(preflight.get("manual_step_required")),
            "wait_for_login_seconds": int(preflight.get("wait_for_login_seconds") or 0),
            "capture_mode": preflight.get("capture_mode", ""),
            "credential_policy": preflight.get("credential_policy", ""),
            "automation_boundary": preflight.get("automation_boundary", ""),
            "public_visible_balance": "account-update-pending",
            "public_visible_open_exposure": "account-update-pending",
            "public_visible_realized_roi": "account-update-pending",
            "raw_refresh_ready": bool(raw_health.get("ready")),
            "active_backfill_queue_count": int((timeline.get("summary") or {}).get("backfill_queue_count") or 0),
        },
        "monitor_rows": rows,
        "private_preflight": preflight,
        "private_metric_policy": {
            "public_outputs": "只展示 ready/blocked、文件存在性、校验问题数量和下一步；不展示账户余额、逐笔下注或私有路径。",
            "private_storage": "当日快照通过后，明细继续留在本机私有存储；公开报告只引用聚合状态。",
            "amount_display_until_ready": "account-update-pending",
            "credential_policy": preflight.get("credential_policy", ""),
            "automation_boundary": preflight.get("automation_boundary", ""),
        },
        "old_new_compare": old_new_compare(previous, status, snapshot_public),
        "source_artifacts": {
            "automation_readiness": "automation_readiness_latest.json" if readiness else "",
            "automation_preflight": "automation_preflight_latest.json" if preflight else "",
            "latest_commit": "latest_commit.json" if latest_commit else "",
            "raw_refresh_health": "raw_refresh_health_latest.json" if raw_health else "",
            "active_timeline": "active_timeline_latest.json" if timeline else "",
        },
        "truthfulness_note": "持仓监控不会自动下注；当私有快照缺失、过期或校验失败时，余额、持仓金额和累计收益率保持 account-update-pending。",
    }
    return sanitize_public_payload(payload)


def position_report_date(
    preflight: dict[str, Any],
    readiness: dict[str, Any],
    latest_commit: dict[str, Any],
    default_date: str | None = None,
) -> str:
    default_date = default_date or datetime.now(REPORT_TZ).strftime("%d%m%Y")
    for candidate in [
        preflight.get("report_date"),
        readiness.get("report_date"),
    ]:
        value = str(candidate or "")
        if len(value) == 8 and value.isdigit():
            return value
    return default_date


def snapshot_public_summary(private_dir: Path, report_date: str) -> dict[str, Any]:
    snapshot_ref = f"private_position_snapshot_{report_date}.json"
    snapshot_path = Path(private_dir) / f"tab_my_bets_positions_{report_date}.json"
    if not snapshot_path.exists():
        return {
            "ready": False,
            "status": "missing",
            "snapshot_ref": snapshot_ref,
            "issues": ["current-day private position snapshot missing"],
        }
    snapshot = load_snapshot(snapshot_path)
    issues = validate_private_position_snapshot(snapshot, report_date)
    summary = snapshot.get("summary") if isinstance(snapshot.get("summary"), dict) else {}
    return {
        "ready": not issues,
        "status": "ready" if not issues else "invalid",
        "snapshot_ref": snapshot_ref,
        "issues": issues[:8],
        "bet_count": int(summary.get("bet_count") or 0) if not issues else 0,
        "pending_count": int(summary.get("pending_count") or 0) if not issues else 0,
        "settled_count": int(summary.get("settled_count") or 0) if not issues else 0,
        "position_statuses_valid": bool(summary.get("position_statuses_valid")) if not issues else False,
        "private_metric_fields_available": [
            "open_stake_aud",
            "estimated_return_if_all_win_aud",
            "realized_pnl_aud",
            "realized_roi",
        ]
        if not issues
        else [],
    }


def empty_snapshot_summary() -> dict[str, Any]:
    return {"ready": False, "status": "missing", "issues": ["report_date missing"]}


def monitor_status(bootstrap: dict[str, Any], snapshot: dict[str, Any]) -> str:
    if snapshot.get("ready"):
        return "ready"
    if (bootstrap.get("files") or {}).get("raw_text_exists") or (bootstrap.get("files") or {}).get("snapshot_exists"):
        return "partial"
    return "blocked"


def status_decision(status: str) -> str:
    if status == "ready":
        return "私有快照已通过校验，可以把余额、持仓金额和累计收益率用于下一次日报门禁。"
    if status == "partial":
        return "已有部分私有读取材料，但尚不能公开展示余额/收益率；继续导入或刷新快照。"
    return "持仓监控未就绪；余额、持仓金额和累计收益率保持 account-update-pending。"


def public_report_action(status: str) -> str:
    if status == "ready":
        return "允许在私有报告链中更新聚合指标；公开入口仍不展示逐笔下注。"
    return "公开报告只显示状态和下一步，不展示真实金额。"


def recommended_next_action(bootstrap: dict[str, Any], raw_health: dict[str, Any]) -> str:
    private_ready = bootstrap.get("ready") is True
    raw_ready = raw_health.get("ready") is True
    private_action = str(bootstrap.get("next_action") or "启动只读持仓读取，导入当日私有快照后重跑日报门禁。")
    if not private_ready and not raw_ready:
        return f"并行处理两个门禁：{private_action} 同时恢复公开盘口 raw；两者都 ready 后重跑日报门禁。"
    if not private_ready:
        return private_action
    if not raw_ready:
        return "私有持仓已就绪；继续恢复公开盘口 raw，raw ready 后重跑日报门禁。"
    return "私有持仓和公开盘口 raw 均已就绪；重跑日报门禁。"


def build_monitor_rows(
    bootstrap: dict[str, Any],
    snapshot: dict[str, Any],
    raw_health: dict[str, Any],
    timeline: dict[str, Any],
) -> list[dict[str, Any]]:
    files = bootstrap.get("files") or {}
    profile = bootstrap.get("profile") or {}
    preflight = bootstrap.get("preflight") or {}
    return [
        row("position_snapshot", "持仓快照", snapshot.get("status", "missing"), snapshot.get("ready"), "当日私有快照必须存在并通过状态校验。", "导入或刷新当日只读快照。"),
        row("raw_text", "只读原文读取", "present" if files.get("raw_text_exists") else "missing", files.get("raw_text_exists"), "只读文本用于生成私有快照，不进入公开报告。", "如果缺失，从 .app 启动只读持仓读取。"),
        row("profile", "TAB 专用 profile", "present" if profile.get("exists") else "missing", profile.get("exists"), "专用 profile 用于保留授权，不保存到公开产物。", "必要时重新完成 TAB 授权。"),
        row("private_preflight", "只读授权 Preflight", str(preflight.get("status") or "missing"), preflight.get("ready"), str(preflight.get("blocking_reason") or "需要只读授权状态检查。"), str(preflight.get("next_safe_action") or "启动只读持仓读取。")),
        row("public_raw", "公开盘口 raw", str(raw_health.get("status") or "missing"), raw_health.get("ready"), "公开盘口必须先通过，持仓结果才进入日报门禁。", "接入授权 raw 或导入用户导出快照。"),
        row("cadence", "主动测试缺口", str((timeline.get("summary") or {}).get("backfill_queue_count", 0)), not (timeline.get("summary") or {}).get("backfill_queue_count"), "持仓变化会影响后续预算，缺口需先补齐。", "raw 恢复后执行 safe_no_latest_publish 补跑。"),
        row("roi", "余额/收益率显示", "account-update-pending" if not snapshot.get("ready") else "private-ready", snapshot.get("ready"), "公开报告不展示账户余额；私有快照 ready 后可供日报门禁使用。", "快照 ready 后重跑日报。"),
    ]


def row(
    item_id: str,
    label: str,
    status: str,
    ready: Any,
    evidence: str,
    next_action: str,
) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "label": label,
        "status": str(status),
        "ready": bool(ready),
        "evidence": evidence,
        "next_action": "保持自动审计。" if ready else next_action,
    }


def old_new_compare(previous: dict[str, Any] | None, status: str, snapshot: dict[str, Any]) -> dict[str, Any]:
    if not previous:
        return {
            "status": "no_previous_snapshot",
            "previous_generated_at": "",
            "status_changed": False,
            "summary": "首次生成持仓监控快照。",
        }
    previous_status = str(previous.get("status") or "")
    previous_ready = bool(previous.get("snapshot_ready"))
    current_ready = bool(snapshot.get("ready"))
    return {
        "status": "compared_with_previous_snapshot",
        "previous_generated_at": previous.get("generated_at", ""),
        "previous_status": previous_status,
        "current_status": status,
        "status_changed": previous_status != status,
        "snapshot_ready_delta": int(current_ready) - int(previous_ready),
        "summary": "持仓监控状态改善。" if current_ready and not previous_ready else "持仓监控状态未改善。" if not current_ready else "持仓监控保持 ready。",
    }


def persist_position_monitor(db_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    public_payload = sanitize_public_payload(payload)
    summary = public_payload.get("summary") or {}
    executive = public_payload.get("executive_status") or {}
    try:
        with connect_report_db(db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO position_monitor_snapshots(
                    monitor_id, generated_at, status, report_date, snapshot_ready,
                    raw_text_exists, public_metrics_available, payload_json
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    public_payload.get("monitor_id", ""),
                    public_payload.get("generated_at", ""),
                    executive.get("status", ""),
                    summary.get("report_date", ""),
                    1 if summary.get("snapshot_ready") else 0,
                    1 if summary.get("raw_text_exists") else 0,
                    1 if executive.get("private_metrics_available") else 0,
                    json.dumps(public_payload, ensure_ascii=False),
                ),
            )
            conn.commit()
        return {"status": "stored", "database": Path(db_path).name, "table": "position_monitor_snapshots"}
    except sqlite3.Error as exc:
        return {"status": "failed", "database": Path(db_path).name, "table": "position_monitor_snapshots", "error": str(exc)}


def latest_position_monitor(db_path: Path) -> dict[str, Any] | None:
    if not Path(db_path).exists():
        return None
    try:
        uri = f"file:{Path(db_path).resolve()}?mode=ro&immutable=1"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        row_data = conn.execute(
            """
            SELECT generated_at, status, report_date, snapshot_ready, payload_json
            FROM position_monitor_snapshots
            ORDER BY generated_at DESC
            LIMIT 1
            """
        ).fetchone()
        conn.close()
    except sqlite3.Error:
        return None
    if not row_data:
        return None
    return {
        "generated_at": str(row_data["generated_at"] or ""),
        "status": str(row_data["status"] or ""),
        "report_date": str(row_data["report_date"] or ""),
        "snapshot_ready": bool(row_data["snapshot_ready"]),
        "payload": load_json_text(row_data["payload_json"]),
    }


def render_position_monitor_markdown(payload: dict[str, Any]) -> str:
    executive = payload.get("executive_status") or {}
    summary = payload.get("summary") or {}
    compare = payload.get("old_new_compare") or {}
    lines = [
        "# TAB FIFA 持仓监控 Dashboard",
        "",
        "本报告监控持仓快照、余额/收益率更新条件和日报门禁。公开版本只展示聚合状态，不展示账户余额、逐笔下注或私有路径。",
        "",
        "## Executive Summary",
        "",
        f"- status: `{executive.get('status', '')}`",
        f"- decision: {md(executive.get('decision'))}",
        f"- report_date: `{summary.get('report_date', '')}`",
        f"- snapshot_ready: `{bool(summary.get('snapshot_ready'))}`",
        f"- public_visible_balance: `{summary.get('public_visible_balance', '')}`",
        f"- public_visible_open_exposure: `{summary.get('public_visible_open_exposure', '')}`",
        f"- public_visible_realized_roi: `{summary.get('public_visible_realized_roi', '')}`",
        f"- preflight_status: `{summary.get('preflight_status', '')}`",
        f"- login_window_required: `{bool(summary.get('login_window_required'))}`",
        f"- credential_policy: {md(summary.get('credential_policy'))}",
        f"- automation_boundary: {md(summary.get('automation_boundary'))}",
        f"- next_action: {md(executive.get('recommended_next_action'))}",
        "",
        "## Visual Summary",
        "",
        "```mermaid",
        "pie showData",
        f"  \"ready\" : {sum(1 for row in payload.get('monitor_rows') or [] if row.get('ready'))}",
        f"  \"blocked\" : {sum(1 for row in payload.get('monitor_rows') or [] if not row.get('ready'))}",
        "```",
        "",
        "## 新旧变化",
        "",
        f"- compare_status: `{compare.get('status', '')}`",
        f"- previous_generated_at: `{compare.get('previous_generated_at', '')}`",
        f"- summary: {md(compare.get('summary'))}",
        "",
        "## 监控矩阵",
        "",
        "| 项目 | 状态 | Ready | 证据 | 下一步 |",
        "|---|---|---|---|---|",
    ]
    for item in payload.get("monitor_rows") or []:
        lines.append(
            "| {label} | {status} | {ready} | {evidence} | {next_action} |".format(
                label=md(item.get("label")),
                status=md(item.get("status")),
                ready="是" if item.get("ready") else "否",
                evidence=md(item.get("evidence")),
                next_action=md(item.get("next_action")),
            )
        )
    lines.extend(["", f"> {payload.get('truthfulness_note', '')}"])
    return "\n".join(lines)


def write_position_monitor_pdf(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    executive = payload.get("executive_status") or {}
    summary = payload.get("summary") or {}
    rows = payload.get("monitor_rows") or []
    ready_count = sum(1 for row in rows if row.get("ready"))
    blocked_count = len(rows) - ready_count
    charts = [
        chart_from_items("持仓监控状态", [("ready", ready_count), ("blocked", blocked_count)], "#1F4E79"),
        chart_from_items("快照链路", [(row.get("label", ""), 1 if row.get("ready") else 0) for row in rows], "#247A5A"),
        chart_from_items(
            "公开显示策略",
            [
                ("余额待更新", 0 if summary.get("snapshot_ready") else 1),
                ("持仓待更新", 0 if summary.get("snapshot_ready") else 1),
                ("收益率待更新", 0 if summary.get("snapshot_ready") else 1),
            ],
            "#C62828",
        ),
        chart_from_items(
            "门禁依赖",
            [
                ("raw", 1 if summary.get("raw_refresh_ready") else 0),
                ("snapshot", 1 if summary.get("snapshot_ready") else 0),
                ("profile", 1 if summary.get("profile_exists") else 0),
                ("cadence", 0 if summary.get("active_backfill_queue_count") else 1),
            ],
            "#A56710",
        ),
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA 持仓监控 Dashboard",
        subtitle="公开安全的持仓、余额和收益率监控状态；只生成报告，不自动下注。",
        summary_rows=[
            ("状态", str(executive.get("status", ""))),
            ("报告日期", str(summary.get("report_date", ""))),
            ("快照 ready", yes_no(summary.get("snapshot_ready"))),
            ("余额显示", str(summary.get("public_visible_balance", ""))),
            ("持仓显示", str(summary.get("public_visible_open_exposure", ""))),
            ("收益率显示", str(summary.get("public_visible_realized_roi", ""))),
            ("Preflight", str(summary.get("preflight_status", ""))),
            ("登录窗口", yes_no(summary.get("login_window_required"))),
            ("授权等待秒数", str(summary.get("wait_for_login_seconds", ""))),
            ("下一步", str(executive.get("recommended_next_action", ""))),
        ],
        charts=charts,
        table_headers=["项目", "状态", "Ready", "下一步"],
        table_rows=[
            [
                str(row.get("label", "")),
                str(row.get("status", "")),
                yes_no(row.get("ready")),
                str(row.get("next_action", "")),
            ]
            for row in rows
        ],
        extra_tables=[
            {
                "title": "公开安全显示策略",
                "headers": ["指标", "公开显示", "原因"],
                "rows": [
                    ["余额", str(summary.get("public_visible_balance", "")), "账户余额属于私有状态"],
                    ["持仓金额", str(summary.get("public_visible_open_exposure", "")), "逐笔和金额明细留在私有快照"],
                    ["累计收益率", str(summary.get("public_visible_realized_roi", "")), "快照未 ready 前不更新"],
                ],
            },
            {
                "title": "新旧变化",
                "headers": ["指标", "值"],
                "rows": [[key, str(value)] for key, value in (payload.get("old_new_compare") or {}).items() if key != "payload"],
            },
            {
                "title": "只读持仓读取 Preflight",
                "headers": ["字段", "值"],
                "rows": [
                    ["状态", str(summary.get("preflight_status", ""))],
                    ["阻塞原因", str(summary.get("preflight_blocking_reason", ""))],
                    ["下一步", str(summary.get("preflight_next_safe_action", ""))],
                    ["登录窗口", yes_no(summary.get("login_window_required"))],
                    ["授权等待秒数", str(summary.get("wait_for_login_seconds", ""))],
                    ["读取模式", str(summary.get("capture_mode", ""))],
                    ["凭据策略", str(summary.get("credential_policy", ""))],
                    ["自动化边界", str(summary.get("automation_boundary", ""))],
                ],
            },
        ],
    )


def monitor_id(generated_at: str) -> str:
    return "position_monitor_" + generated_at.replace("-", "").replace(":", "").replace("+", "_").replace(".", "_")


def load_json(path: Path) -> dict[str, Any]:
    try:
        if not Path(path).exists():
            return {}
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def load_json_text(value: Any) -> dict[str, Any]:
    try:
        payload = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def yes_no(value: Any) -> str:
    return "是" if bool(value) else "否"


def md(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")
