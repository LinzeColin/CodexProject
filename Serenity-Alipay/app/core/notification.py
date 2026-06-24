from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from app.adapters.mail_notifier import send_with_apple_mail, write_mail_ready_draft
from app.adapters.macos_notifier import send_local_notification, write_local_notification_script
from app.config import Settings
from app.core.mail_policy import should_send_mail_for_run, suppressed_no_material_change_message
from app.core.reporting import (
    _notification_deadline,
    _notification_next_step,
    _notification_subject,
    _recommendation_line,
    _zh_action,
    _zh_reason,
    render_notification_html,
)
from app.core.time_display import format_display_time
from app.db import connect, init_db


@dataclass(frozen=True)
class NotificationRender:
    run_id: str
    severity: str
    title: str
    body: str
    html_body: str
    draft_path: Path
    html_path: Path
    local_script_path: Path


def _rows(conn: sqlite3.Connection, query: str, params: tuple[object, ...]) -> list[sqlite3.Row]:
    return list(conn.execute(query, params).fetchall())


def _severity_for_run(conn: sqlite3.Connection, run_id: str) -> str:
    hard = conn.execute(
        """
        SELECT COUNT(*) AS n
        FROM recommendation_snapshot r
        JOIN score_snapshot s ON s.run_id=r.run_id AND s.asset_id=r.asset_id
        WHERE r.run_id=? AND s.grade='Block'
        """,
        (run_id,),
    ).fetchone()["n"]
    alerts = conn.execute(
        "SELECT COUNT(*) AS n FROM rebalance_event_log WHERE run_id=? AND severity='Alert'",
        (run_id,),
    ).fetchone()["n"]
    manual = conn.execute(
        """
        SELECT COUNT(*) AS n
        FROM manual_review_queue m
        JOIN recommendation_snapshot r ON r.run_id=m.run_id AND r.asset_id=m.asset_id
        WHERE m.run_id=? AND COALESCE(r.rank, 999) <= 5
        """,
        (run_id,),
    ).fetchone()["n"]
    if hard:
        return "Urgent"
    if alerts:
        return "Alert"
    if manual:
        return "Warn"
    return "Info"


def render_notification_for_run(settings: Settings, run_id: str, severity: str | None = None) -> NotificationRender:
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        run = conn.execute("SELECT * FROM run_log WHERE run_id=?", (run_id,)).fetchone()
        if not run:
            raise ValueError(f"run not found: {run_id}")
        severity = severity or _severity_for_run(conn, run_id)
        recs = _rows(
            conn,
            """
            SELECT r.*, a.asset_code, a.asset_name, s.grade, s.hard_block_reason
            FROM recommendation_snapshot r
            JOIN asset_master a ON a.asset_id=r.asset_id
            JOIN score_snapshot s ON s.run_id=r.run_id AND s.asset_id=r.asset_id
            WHERE r.run_id=?
            ORDER BY r.rank ASC
            """,
            (run_id,),
        )
        events = _rows(
            conn,
            "SELECT trigger_reason, severity FROM rebalance_event_log WHERE run_id=? ORDER BY id ASC",
            (run_id,),
        )
        manual = _rows(
            conn,
            """
            SELECT m.asset_id, a.asset_code, a.asset_name, m.reason, m.action_blocked
            FROM manual_review_queue m
            LEFT JOIN asset_master a ON a.asset_id=m.asset_id
            WHERE m.run_id=?
            ORDER BY m.id ASC
            """,
            (run_id,),
        )

    rec_dicts = [dict(row) for row in recs]
    top5 = rec_dicts[:5]
    execution_locked = str(run["data_quality_status"]) != "pass"
    urgent = severity == "Urgent" or any(row.get("action_label") in {"Clear", "Block"} for row in top5)
    actionable = [row for row in top5 if str(row.get("action_label")) not in {"Maintain"}]
    actionable_count = len(actionable)
    title = _notification_subject(severity, execution_locked, urgent, actionable_count)
    primary_action = "禁止新增" if execution_locked else (_zh_action(actionable[0]["action_label"]) if actionable else "维持")
    event_reason = events[0]["trigger_reason"] if events else (
        actionable[0]["trigger_reason"] if actionable else (top5[0]["trigger_reason"] if top5 else "")
    )
    body_lines = [
        f"# {title}",
        "",
        "## 结论",
        f"- 本轮运行：{format_display_time(str(run['run_time_bj']), 'Asia/Shanghai')} / {format_display_time(str(run['run_time_au']), 'Australia/Sydney')}",
        f"- 当前结论：{primary_action}",
        f"- 处理截止：{_notification_deadline(execution_locked, actionable_count)}",
        f"- 执行锁：{'ON' if execution_locked else 'OFF'}",
        f"- 当前禁止动作：{'禁止新增（No-New-Order）' if execution_locked else '禁止自动下单；必须人工确认'}",
    ]
    if execution_locked:
        body_lines.extend(["- 建议金额：0.00", "- 建议份额：0"])

    body_lines.extend(
        [
            "",
            "## 需要你做什么",
            f"- {_notification_next_step(execution_locked, urgent, actionable_count)}",
            "- 系统只给纪律建议，不会自动交易、不提交申购或赎回。",
            "",
            "## 持仓动作清单",
        ]
    )
    if top5:
        body_lines.extend(_recommendation_line(index, row, execution_locked) for index, row in enumerate(top5, start=1))
    else:
        body_lines.append("- 本轮没有可用候选。")

    manual_items: list[str] = []
    body_lines.extend(["", "## 风控兜底", f"- 关键原因：{_zh_reason(event_reason)}"])
    if manual:
        manual_items = [
            f"{row['asset_name'] or row['asset_code'] or row['asset_id']}：{_zh_reason(row['reason'])}"
            for row in manual[:5]
        ]
        body_lines.append(
            "- 人工复核："
            + "；".join(manual_items)
        )
    body_lines.extend(
        [
            (
                "- 数据缺失、冲突或执行状态异常时，一律暂停新增并等待下一轮复核。"
                if execution_locked
                else "- 观察池复核不阻断当前 Top5；满足 Serenity 条件后再进入持仓建议。"
            ),
            "",
        ]
    )
    body = "\n".join(body_lines)
    html_body = render_notification_html(
        title,
        run_id,
        severity,
        top5,
        str(run["run_time_bj"]),
        str(run["run_time_au"]),
        data_quality_status=str(run["data_quality_status"]),
        event_reason=event_reason,
        manual_review_items=manual_items,
        execution_locked=execution_locked,
    )
    draft_path = settings.notifications_dir / f"{run_id}_{severity.lower()}_mail.md"
    html_path = draft_path.with_suffix(".html")
    local_script_path = settings.notifications_dir / f"{run_id}_{severity.lower()}_local_notification.applescript"
    write_mail_ready_draft(draft_path, title, body, settings.recipient_email, html_body=html_body)
    write_local_notification_script(local_script_path, title, body)
    return NotificationRender(run_id, severity, title, body, html_body, draft_path, html_path, local_script_path)


def notify_run(
    settings: Settings,
    run_id: str,
    dry_run: bool = True,
    send_mail: bool = False,
    local: bool = False,
) -> dict[str, object]:
    rendered = render_notification_for_run(settings, run_id)
    send_status = "drafted"
    error = None
    if send_mail and not dry_run:
        notification_rows = _notification_recommendations(settings, run_id)
        should_send_mail = should_send_mail_for_run(
            rendered.severity,
            notification_rows,
            data_quality_status=_run_quality(settings, run_id),
        )
        if not should_send_mail:
            send_status = "suppressed_no_material_change"
            error = suppressed_no_material_change_message()
        elif settings.mail_send_enabled:
            result = send_with_apple_mail(
                rendered.title,
                rendered.body,
                settings.recipient_email,
                html_body=rendered.html_body,
            )
            send_status = result["status"]
            error = result["error"] or None
        else:
            send_status = "blocked_by_config"
            error = "SERENITY_MAIL_SEND_ENABLED is false"
    local_status = "scripted"
    local_error = None
    if local and not dry_run:
        result = send_local_notification(rendered.title, rendered.body)
        local_status = result["status"]
        local_error = result["error"] or None

    with connect(settings.db_path) as conn:
        notification_id = (
            f"{run_id}_{rendered.severity.lower()}_draft_preview"
            if dry_run
            else f"{run_id}_{rendered.severity.lower()}_notify"
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO notification_log (
              notification_id, run_id, channel, severity, title, body_path,
              send_status, sent_at, error_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, CASE WHEN ? THEN datetime('now') ELSE NULL END, ?)
            """,
            (
                notification_id,
                run_id,
                "macos_mail_and_local",
                rendered.severity,
                rendered.title,
                str(rendered.draft_path),
                send_status if local_status == "scripted" else f"{send_status};local={local_status}",
                0 if dry_run or send_status != "sent" else 1,
                error or local_error,
            ),
        )
        if not dry_run:
            conn.execute(
                "UPDATE run_log SET notification_status=? WHERE run_id=?",
                (send_status, run_id),
            )

    return {
        "run_id": run_id,
        "severity": rendered.severity,
        "title": rendered.title,
        "draft_path": str(rendered.draft_path),
        "html_path": str(rendered.html_path),
        "local_script_path": str(rendered.local_script_path),
        "send_status": send_status,
        "local_status": local_status,
        "error": error or local_error,
    }


def _run_quality(settings: Settings, run_id: str) -> str:
    with connect(settings.db_path) as conn:
        row = conn.execute("SELECT data_quality_status FROM run_log WHERE run_id=?", (run_id,)).fetchone()
    return str(row["data_quality_status"]) if row else "missing"


def _notification_recommendations(settings: Settings, run_id: str) -> list[dict[str, object]]:
    with connect(settings.db_path) as conn:
        rows = _rows(
            conn,
            """
            SELECT r.*, a.asset_code, a.asset_name, s.grade, s.hard_block_reason
            FROM recommendation_snapshot r
            JOIN asset_master a ON a.asset_id=r.asset_id
            JOIN score_snapshot s ON s.run_id=r.run_id AND s.asset_id=r.asset_id
            WHERE r.run_id=?
            ORDER BY r.rank ASC
            """,
            (run_id,),
        )
    return [dict(row) for row in rows[:5]]
