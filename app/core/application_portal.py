from __future__ import annotations

import html
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import Settings
from app.core.run_visibility import display_run_time_with_backfill_note
from app.core.time_display import format_display_time, parse_datetime
from app.db import connect, init_db


APP_BUNDLE_NAME = "Serenity 每日分析.app"
APP_ICON_BASENAME = "SerenityIcon"


@dataclass(frozen=True)
class PortalRun:
    run_id: str
    slot: str
    run_time_bj: str
    run_time_au: str
    created_at: str
    status: str
    quality: str
    notification_status: str | None
    report_path: str | None
    html_path: str | None


@dataclass(frozen=True)
class PortalHolding:
    rank: int
    code: str
    name: str
    grade: str
    score: float
    target_weight: float
    current_weight: float
    action_label: str
    trigger_reason: str


@dataclass(frozen=True)
class PortalFundInfo:
    code: str
    name: str
    first_top5_time_bj: str | None
    last_top5_entry_time_bj: str | None
    current_candidate_days: int | None
    candidate_status: str | None
    rule_snapshot_time_bj: str | None
    subscription_status: str | None
    redemption_status: str | None
    cutoff_time: str | None
    confirm_lag: str | None
    redeem_lag: str | None
    subscription_fee: float | None
    redemption_fee: float | None
    subscription_fee_schedule: str | None
    redemption_fee_schedule: str | None
    fee_schedule_as_of: str | None
    fee_schedule_note: str | None
    management_fee: float | None
    custody_fee: float | None
    sales_service_fee: float | None
    min_purchase_amount: float | None
    alipay_trade_status: str | None
    moomoo_trade_status: str | None
    platform_trade_note: str | None
    source_name: str | None
    source_type: str | None
    source_priority: int | None
    source_url: str | None


@dataclass(frozen=True)
class PortalTimelineEvent:
    slot: str
    run_time_bj: str
    run_time_au: str
    status: str
    quality: str
    direction: str
    buy_count: int
    sell_count: int
    top5_count: int
    summary: str
    detail: str


@dataclass(frozen=True)
class PortalManualReviewItem:
    review_id: int
    run_id: str
    code: str
    name: str
    reason: str
    action_blocked: str
    status: str
    created_at: str


def _pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value * 100:.2f}%"


def _pp(value: float | None) -> str:
    if value is None:
        return "无上轮"
    sign = "+" if value > 0 else ""
    return f"{sign}{value * 100:.2f}%"


def _fee(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value * 100:.2f}%"


def _amount(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}"


def _score(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}"


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _portal_relative_href(path_value: str | None, fallback: str) -> str:
    if not path_value:
        return fallback
    project_root = Path(__file__).resolve().parents[2]
    portal_dir = project_root / "outputs" / "application"
    raw_path = Path(path_value)
    target = raw_path if raw_path.is_absolute() else project_root / raw_path
    try:
        return Path(os.path.relpath(target.resolve(), portal_dir.resolve())).as_posix()
    except ValueError:
        return target.resolve().as_uri()


def _format_time(value: str | None, zone: str) -> str:
    return format_display_time(value, zone)


def _format_compact_time(value: str | None, zone: str) -> str:
    return format_display_time(value, zone)


def _beijing_date(value: str | None) -> date | None:
    if not value:
        return None
    parsed = parse_datetime(value)
    if not parsed:
        return None
    return parsed.astimezone(ZoneInfo("Asia/Shanghai")).date()


def _zh_status(value: str) -> str:
    return {
        "success": "成功",
        "degraded": "降级",
        "failed": "失败",
        "pass": "通过",
        "manual_review": "人工复核",
        "sent": "已发送",
        "drafted": "已生成草稿",
    }.get(value, value)


def _zh_grade(value: str) -> str:
    return {
        "Action-Ready": "可执行",
        "Watch": "观察",
        "Manual Review": "人工复核",
        "Block": "阻断",
    }.get(value, value)


def _zh_action(value: str) -> str:
    return {
        "Maintain": "维持",
        "Increase": "增配",
        "Reduce": "减配",
        "Pause New": "暂停新增",
        "Clear": "清仓/退出",
        "Block": "阻断",
        "Manual Review": "人工复核",
    }.get(value, value)


def _action_badge_class(value: str) -> str:
    return {
        "Maintain": "hold",
        "Increase": "buy",
        "Reduce": "sell",
        "Clear": "sell",
        "Pause New": "warn",
        "Block": "locked",
        "Manual Review": "warn",
    }.get(value, "")


def _operation_text(action: str) -> str:
    return {
        "Maintain": "无需新增交易；继续按下一时段复核。",
        "Increase": "候选增配；需人工在交易平台确认费率、限额和截止时间后执行。",
        "Reduce": "候选减配；需人工确认赎回规则和成本后执行。",
        "Pause New": "暂停新增；等待证据补齐或下一轮确认。",
        "Clear": "触发退出纪律；需人工确认后处理。",
        "Block": "禁止新增；进入人工复核。",
        "Manual Review": "暂停动作；先补充证据并人工复核。",
    }.get(action, "需人工复核后再行动。")


def _timeline_time_key(value: str | None) -> str:
    formatted = _format_time(value, "Asia/Shanghai")
    return formatted if formatted != "-" else str(value or "")


def _dedupe_runs_by_display_time(rows) -> list:
    seen: set[str] = set()
    unique_rows = []
    for row in rows:
        key = _timeline_time_key(row["run_time_bj"])
        if key in seen:
            continue
        seen.add(key)
        unique_rows.append(row)
    return unique_rows


def _latest_runs(conn, limit: int = 2) -> list[PortalRun]:
    fetch_limit = max(limit * 4, limit)
    rows = conn.execute(
        """
        SELECT run_id, schedule_slot, run_time_bj, run_time_au, created_at, status,
               data_quality_status, notification_status, report_path, offline_html_path
        FROM run_log
        WHERE schedule_slot LIKE 'R%'
          AND report_path IS NOT NULL
          AND status='success'
          AND data_quality_status='pass'
        ORDER BY created_at DESC, rowid DESC
        LIMIT ?
        """,
        (fetch_limit,),
    ).fetchall()
    rows = _dedupe_runs_by_display_time(rows)[:limit]
    if not rows:
        rows = conn.execute(
            """
            SELECT run_id, schedule_slot, run_time_bj, run_time_au, created_at, status,
                   data_quality_status, notification_status, report_path, offline_html_path
            FROM run_log
            WHERE schedule_slot LIKE 'R%'
              AND report_path IS NOT NULL
            ORDER BY created_at DESC, rowid DESC
            LIMIT ?
            """,
            (fetch_limit,),
        ).fetchall()
        rows = _dedupe_runs_by_display_time(rows)[:limit]
    return [
        PortalRun(
            run_id=row["run_id"],
            slot=row["schedule_slot"],
            run_time_bj=row["run_time_bj"],
            run_time_au=row["run_time_au"],
            created_at=row["created_at"],
            status=row["status"],
            quality=row["data_quality_status"],
            notification_status=row["notification_status"],
            report_path=row["report_path"],
            html_path=row["offline_html_path"],
        )
        for row in rows
    ]


def _holdings_for_run(conn, run_id: str) -> list[PortalHolding]:
    rows = conn.execute(
        """
        SELECT r.rank, a.asset_code, a.asset_name, s.grade, s.total_score,
               r.target_weight, r.current_weight, r.action_label, r.trigger_reason
        FROM recommendation_snapshot r
        JOIN asset_master a ON a.asset_id=r.asset_id
        JOIN score_snapshot s ON s.run_id=r.run_id AND s.asset_id=r.asset_id
        WHERE r.run_id=?
          AND r.rank BETWEEN 1 AND 5
        ORDER BY r.rank ASC
        """,
        (run_id,),
    ).fetchall()
    return [
        PortalHolding(
            rank=int(row["rank"]),
            code=row["asset_code"],
            name=row["asset_name"],
            grade=row["grade"],
            score=float(row["total_score"]),
            target_weight=float(row["target_weight"] or 0.0),
            current_weight=float(row["current_weight"] or 0.0),
            action_label=row["action_label"],
            trigger_reason=row["trigger_reason"],
        )
        for row in rows
    ]


def _manual_review_items(conn, run_id: str | None, limit: int = 12) -> list[PortalManualReviewItem]:
    params: list[object] = []
    where = "m.status='open'"
    order = "m.created_at DESC, m.id DESC"
    if run_id:
        where = "m.run_id=? AND m.status='open'"
        params.append(run_id)
    rows = conn.execute(
        f"""
        SELECT m.id, m.run_id, COALESCE(a.asset_code, '-') AS asset_code,
               COALESCE(a.asset_name, '未指定标的') AS asset_name,
               m.reason, m.action_blocked, m.status, m.created_at
        FROM manual_review_queue m
        LEFT JOIN asset_master a ON a.asset_id=m.asset_id
        WHERE {where}
        ORDER BY {order}
        LIMIT ?
        """,
        tuple(params + [limit]),
    ).fetchall()
    if not rows and run_id:
        rows = conn.execute(
            """
            SELECT m.id, m.run_id, COALESCE(a.asset_code, '-') AS asset_code,
                   COALESCE(a.asset_name, '未指定标的') AS asset_name,
                   m.reason, m.action_blocked, m.status, m.created_at
            FROM manual_review_queue m
            LEFT JOIN asset_master a ON a.asset_id=m.asset_id
            WHERE m.status='open'
            ORDER BY m.created_at DESC, m.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        PortalManualReviewItem(
            review_id=int(row["id"]),
            run_id=row["run_id"],
            code=row["asset_code"],
            name=row["asset_name"],
            reason=row["reason"],
            action_blocked=row["action_blocked"],
            status=row["status"],
            created_at=_format_time(row["created_at"], "Asia/Shanghai"),
        )
        for row in rows
    ]


def _candidate_pool_meta(
    conn,
    asset_codes: list[str],
    current_run_id: str | None,
) -> dict[str, dict[str, object]]:
    if not asset_codes:
        return {}

    current_row = None
    if current_run_id:
        current_row = conn.execute(
            "SELECT run_time_bj, created_at FROM run_log WHERE run_id=?",
            (current_run_id,),
        ).fetchone()
    current_run_time = current_row["run_time_bj"] if current_row else None
    current_created_at = current_row["created_at"] if current_row else None

    if current_created_at:
        run_rows = conn.execute(
            """
            SELECT run_id, run_time_bj, created_at
            FROM run_log
            WHERE schedule_slot LIKE 'R%'
              AND status='success'
              AND data_quality_status='pass'
              AND created_at <= ?
            ORDER BY run_time_bj ASC, created_at ASC, run_id ASC
            """,
            (current_created_at,),
        ).fetchall()
    else:
        run_rows = conn.execute(
            """
            SELECT run_id, run_time_bj, created_at
            FROM run_log
            WHERE schedule_slot LIKE 'R%'
              AND status='success'
              AND data_quality_status='pass'
            ORDER BY run_time_bj ASC, created_at ASC, run_id ASC
            """
        ).fetchall()

    placeholders = ",".join("?" for _ in asset_codes)
    occurrence_rows = conn.execute(
        f"""
        SELECT r.run_id, a.asset_code
        FROM recommendation_snapshot r
        JOIN asset_master a ON a.asset_id=r.asset_id
        WHERE r.rank BETWEEN 1 AND 5
          AND a.asset_code IN ({placeholders})
        """,
        tuple(asset_codes),
    ).fetchall()
    present_by_run: dict[str, set[str]] = {}
    for row in occurrence_rows:
        present_by_run.setdefault(row["run_id"], set()).add(row["asset_code"])

    current_present = present_by_run.get(current_run_id or "", set())
    meta: dict[str, dict[str, object]] = {}
    for code in asset_codes:
        first_seen: str | None = None
        last_seen: str | None = None
        last_entry: str | None = None
        was_present = False

        for run_row in run_rows:
            present = code in present_by_run.get(run_row["run_id"], set())
            if present:
                first_seen = first_seen or run_row["run_time_bj"]
                last_seen = run_row["run_time_bj"]
                if not was_present:
                    last_entry = run_row["run_time_bj"]
            was_present = present

        in_current_pool = code in current_present
        candidate_days: int | None = None
        if in_current_pool and last_entry and current_run_time:
            start_date = _beijing_date(last_entry)
            end_date = _beijing_date(current_run_time)
            if start_date and end_date:
                candidate_days = max((end_date - start_date).days + 1, 1)

        meta[code] = {
            "first_top5_time_bj": first_seen,
            "last_seen_time_bj": last_seen,
            "last_top5_entry_time_bj": last_entry,
            "current_candidate_days": candidate_days,
            "candidate_status": "在当前候选池" if in_current_pool else "不在当前候选池",
        }
    return meta


def _fund_library_for_run(
    conn,
    run_id: str | None,
    holdings: list[PortalHolding] | None = None,
) -> dict[str, PortalFundInfo]:
    asset_codes = sorted({row.code for row in holdings or []})
    if not run_id and not asset_codes:
        return {}

    candidate_meta = _candidate_pool_meta(conn, asset_codes, run_id)

    params: list[object] = []
    where = ""
    if asset_codes:
        placeholders = ",".join("?" for _ in asset_codes)
        where = f"a.asset_code IN ({placeholders})"
        params.extend(asset_codes)
    elif run_id:
        where = "f.run_id=?"
        params.append(run_id)

    rows = conn.execute(
        f"""
        SELECT a.asset_code, a.asset_name, f.subscription_status, f.redemption_status,
               f.cutoff_time, f.confirm_lag, f.redeem_lag, f.subscription_fee,
               f.redemption_fee, f.management_fee, f.custody_fee, f.sales_service_fee,
               f.subscription_fee_schedule, f.redemption_fee_schedule,
               f.fee_schedule_as_of, f.fee_schedule_note,
               f.alipay_trade_status, f.moomoo_trade_status, f.platform_trade_note,
               f.min_purchase_amount, s.source_name, s.source_type, s.source_priority,
               s.url_or_path, rl.run_time_bj AS rule_snapshot_time_bj
        FROM fund_rule_snapshot f
        JOIN asset_master a ON a.asset_id=f.asset_id
        LEFT JOIN source_log s ON s.source_id=f.source_id
        LEFT JOIN run_log rl ON rl.run_id=f.run_id
        WHERE {where}
        ORDER BY CASE WHEN ? IS NOT NULL AND f.run_id=? THEN 0 ELSE 1 END,
                 rl.run_time_bj DESC,
                 s.source_priority ASC,
                 a.asset_code
        """,
        tuple(params + [run_id, run_id]),
    ).fetchall()
    fund_library: dict[str, PortalFundInfo] = {}
    for row in rows:
        if row["asset_code"] in fund_library:
            continue
        meta = candidate_meta.get(row["asset_code"], {})
        fund_library[row["asset_code"]] = PortalFundInfo(
            code=row["asset_code"],
            name=row["asset_name"],
            first_top5_time_bj=meta.get("first_top5_time_bj"),
            last_top5_entry_time_bj=meta.get("last_top5_entry_time_bj"),
            current_candidate_days=meta.get("current_candidate_days"),
            candidate_status=meta.get("candidate_status"),
            rule_snapshot_time_bj=row["rule_snapshot_time_bj"],
            subscription_status=row["subscription_status"],
            redemption_status=row["redemption_status"],
            cutoff_time=row["cutoff_time"],
            confirm_lag=row["confirm_lag"],
            redeem_lag=row["redeem_lag"],
            subscription_fee=row["subscription_fee"],
            redemption_fee=row["redemption_fee"],
            subscription_fee_schedule=row["subscription_fee_schedule"],
            redemption_fee_schedule=row["redemption_fee_schedule"],
            fee_schedule_as_of=row["fee_schedule_as_of"],
            fee_schedule_note=row["fee_schedule_note"],
            management_fee=row["management_fee"],
            custody_fee=row["custody_fee"],
            sales_service_fee=row["sales_service_fee"],
            min_purchase_amount=row["min_purchase_amount"],
            alipay_trade_status=row["alipay_trade_status"],
            moomoo_trade_status=row["moomoo_trade_status"],
            platform_trade_note=row["platform_trade_note"],
            source_name=row["source_name"],
            source_type=row["source_type"],
            source_priority=row["source_priority"],
            source_url=row["url_or_path"],
        )
    return fund_library


def _baseline_reference_time(conn, run_id: str | None) -> str | None:
    if not run_id:
        return None
    row = conn.execute(
        """
        SELECT rr.run_time_bj AS reference_time, r.run_time_bj AS run_time
        FROM baseline_snapshot b
        LEFT JOIN run_log rr ON rr.run_id=b.reference_run_id
        LEFT JOIN run_log r ON r.run_id=b.run_id
        WHERE b.run_id=?
        ORDER BY b.id ASC
        LIMIT 1
        """,
        (run_id,),
    ).fetchone()
    if not row:
        return None
    return row["reference_time"] or row["run_time"]


def _run_change_details(
    current: list[PortalHolding],
    previous: list[PortalHolding],
) -> tuple[list[str], list[str]]:
    buy_details: list[str] = []
    sell_details: list[str] = []
    current_by_code = {row.code: row for row in current}
    previous_by_code = {row.code: row for row in previous}
    epsilon = 0.00005

    for row in current:
        previous_row = previous_by_code.get(row.code)
        if previous_row is None:
            buy_details.append(f"{row.name} 新增 {_pct(row.target_weight)}")
            continue
        delta = row.target_weight - previous_row.target_weight
        if delta > epsilon:
            buy_details.append(f"{row.name} 增加 {_pp(delta)}")
        elif delta < -epsilon:
            sell_details.append(f"{row.name} 减少 {_pp(delta)}")

    for row in previous:
        if row.code not in current_by_code:
            sell_details.append(f"{row.name} 移出 {_pct(row.target_weight)}")

    if not buy_details:
        for row in current:
            if row.action_label == "Increase":
                buy_details.append(f"{row.name} 动作标签增配")
    if not sell_details:
        for row in current:
            if row.action_label in {"Reduce", "Clear"}:
                sell_details.append(f"{row.name} 动作标签{_zh_action(row.action_label)}")
    return buy_details, sell_details


def _timeline_event_for_run(
    run: PortalRun,
    current: list[PortalHolding],
    previous: list[PortalHolding],
) -> PortalTimelineEvent:
    buy_details, sell_details = _run_change_details(current, previous)
    buy_count = len(buy_details)
    sell_count = len(sell_details)
    if buy_count and sell_count:
        direction = "mixed"
        summary = f"买 {buy_count} / 卖 {sell_count}"
    elif buy_count:
        direction = "buy"
        summary = f"买入/增加 {buy_count}"
    elif sell_count:
        direction = "sell"
        summary = f"卖出/减少 {sell_count}"
    else:
        direction = "flat"
        summary = "维持"
    detail_items = (buy_details + sell_details)[:4]
    detail = "；".join(detail_items) if detail_items else "Top5 目标权重无变化"
    return PortalTimelineEvent(
        slot=run.slot,
        run_time_bj=_format_time(run.run_time_bj, "Asia/Shanghai"),
        run_time_au=_format_time(run.run_time_au, "Australia/Sydney"),
        status=_zh_status(run.status),
        quality=_zh_status(run.quality),
        direction=direction,
        buy_count=buy_count,
        sell_count=sell_count,
        top5_count=len(current),
        summary=summary,
        detail=detail,
    )


def _run_timeline_events(conn, runs: list[PortalRun]) -> list[PortalTimelineEvent]:
    chronological_runs = list(reversed(runs))
    previous_holdings: list[PortalHolding] = []
    chronological_events: list[PortalTimelineEvent] = []
    for run in chronological_runs:
        current_holdings = _holdings_for_run(conn, run.run_id)
        chronological_events.append(_timeline_event_for_run(run, current_holdings, previous_holdings))
        previous_holdings = current_holdings
    return list(reversed(chronological_events))


def _change(current: float | None, previous: float | None) -> tuple[str, str, str, str]:
    if current is None and previous is None:
        return "flat", "-", "无变化", "无数据"
    if current is not None and previous is None:
        return "up", _pp(current), "新增/买入", "较上轮新增"
    if current is None and previous is not None:
        return "down", _pp(-previous), "减少/卖出", "较上轮移出"
    delta = float(current or 0.0) - float(previous or 0.0)
    if delta > 0.000001:
        return "up", _pp(delta), "增加/买入", "较上轮增加"
    if delta < -0.000001:
        return "down", _pp(delta), "减少/卖出", "较上轮减少"
    return "flat", _pp(0.0), "维持", "较上轮无变化"


def _relative_ratio(current: float | None, reference: float | None) -> tuple[str, str, str]:
    if current is None and reference is None:
        return "flat", "-", "无数据"
    current_value = float(current or 0.0)
    if reference is None or abs(float(reference or 0.0)) < 0.000001:
        if abs(current_value) < 0.000001:
            return "flat", "0.00%", "维持"
        return "up", "新增", "新增/买入"
    ratio = current_value / float(reference) - 1.0
    if ratio > 0.000001:
        return "up", f"+{ratio * 100:.2f}%", "增加/买入"
    if ratio < -0.000001:
        return "down", f"{ratio * 100:.2f}%", "减少/卖出"
    return "flat", "0.00%", "维持"


def _fund_button(row: PortalHolding) -> str:
    return (
        f'<button type="button" class="fund-link" data-fund-code="{_escape(row.code)}">'
        f"{_escape(row.name)}</button>"
    )


def _holding_rows(
    rows: list[PortalHolding],
    *,
    previous_by_code: dict[str, PortalHolding],
    target_time: str,
    baseline_time: str,
    previous_time: str,
) -> str:
    if not rows:
        return '<tr><td colspan="9">暂无可展示的持仓建议。</td></tr>'
    cells: list[str] = []
    for row in rows:
        previous = previous_by_code.get(row.code)
        previous_weight = previous.target_weight if previous else None
        initial_class, initial_ratio, initial_action = _relative_ratio(row.target_weight, row.current_weight)
        previous_class, previous_ratio, previous_action = _relative_ratio(row.target_weight, previous_weight)
        initial_value = _pct(row.current_weight)
        previous_value = _pct(previous_weight)
        cells.append(
            f'<tr class="row-{initial_class}" data-reference-row data-initial-class="{initial_class}" data-previous-class="{previous_class}">'
            f"<td>{row.rank}</td>"
            f"<td><strong>{_escape(row.code)}</strong>{_fund_button(row)}</td>"
            f"<td><span class=\"badge\">{_escape(_zh_grade(row.grade))}</span></td>"
            f"<td>{_score(row.score)}</td>"
            f"<td><strong>{_pct(row.target_weight)}</strong><span>目标时间：{_escape(target_time)}</span></td>"
            "<td>"
            f'<strong data-reference-weight data-initial-value="{_escape(initial_value)}" data-previous-value="{_escape(previous_value)}">{_escape(initial_value)}</strong>'
            f'<span data-reference-time data-initial-value="初始持仓权重时间：{_escape(baseline_time)}" data-previous-value="上轮对比权重时间：{_escape(previous_time)}">初始持仓权重时间：{_escape(baseline_time)}</span>'
            "</td>"
            "<td>"
            f'<span class="change {initial_class}" data-relative-ratio data-initial-value="{_escape(initial_ratio)}" data-previous-value="{_escape(previous_ratio)}" data-initial-class="{initial_class}" data-previous-class="{previous_class}">{_escape(initial_ratio)}</span>'
            f'<span data-relative-action data-initial-value="{_escape(initial_action)}" data-previous-value="{_escape(previous_action)}">{_escape(initial_action)}</span>'
            "</td>"
            f"<td><span class=\"badge {_escape(_action_badge_class(row.action_label))}\">{_escape(_zh_action(row.action_label))}</span></td>"
            f"<td>{_escape(_operation_text(row.action_label))}</td>"
            "</tr>"
        )
    return "\n".join(cells)


def _discipline_cards(
    current: list[PortalHolding],
    previous: list[PortalHolding],
    *,
    latest_time: str,
    comparison_time: str,
) -> str:
    previous_by_code = {row.code: row for row in previous}
    if not current:
        return '<div class="discipline-empty">暂无当前持仓建议数据。</div>'
    cards: list[str] = []
    for row in current:
        previous = previous_by_code.get(row.code)
        change_class, change_text, change_action, _ = _change(
            row.target_weight,
            previous.target_weight if previous else None,
        )
        cards.append(
            f'<article class="discipline-card {change_class}">'
            '<div class="recommendation-head">'
            f'<span class="recommendation-rank">#{row.rank}</span>'
            f"{_fund_button(row)}"
            "</div>"
            f'<strong class="change {change_class}">{_pct(row.target_weight)}</strong>'
            '<div class="recommendation-meta">'
            f"<span>最新更新时间 {_escape(latest_time)}</span>"
            f"<span>策略份额 · {_escape(change_action)} · {_escape(change_text)}</span>"
            f"<span>相较对比时间 {_escape(comparison_time)}</span>"
            "</div>"
            "</article>"
        )
    return "\n".join(cards)


def _timeline_badge(event: PortalTimelineEvent) -> str:
    return f'<span class="timeline-badge {event.direction}">{_escape(event.summary)}</span>'


def _dedupe_timeline_events(events: list[PortalTimelineEvent]) -> list[PortalTimelineEvent]:
    seen: set[str] = set()
    unique_events: list[PortalTimelineEvent] = []
    for event in events:
        key = event.run_time_bj
        if key in seen:
            continue
        seen.add(key)
        unique_events.append(event)
    return unique_events


def _timeline_detail_html(detail: str) -> str:
    parts = [part.strip() for part in detail.split("；") if part.strip()]
    if len(parts) <= 1:
        return f'<div class="timeline-detail-lines"><span>{_escape(detail)}</span></div>'
    lines = []
    for index, part in enumerate(parts):
        suffix = "；" if index < len(parts) - 1 else ""
        lines.append(f"<span>{_escape(part + suffix)}</span>")
    return f'<div class="timeline-detail-lines">{"".join(lines)}</div>'


def _run_timeline_panel(events: list[PortalTimelineEvent]) -> str:
    events = _dedupe_timeline_events(events)
    if not events:
        table_rows = '<tr><td colspan="7">暂无运行时间线数据。</td></tr>'
        visual_cards = '<div class="timeline-empty">暂无运行时间线数据。</div>'
    else:
        table_rows = "\n".join(
            "<tr class=\"timeline-row-{direction}\">"
            "<td><strong>{bj}</strong><span>澳洲：{au}</span></td>"
            "<td>{status}</td>"
            "<td>{quality}</td>"
            "<td>{badge}</td>"
            "<td><span class=\"timeline-count buy\">买 {buy}</span></td>"
            "<td><span class=\"timeline-count sell\">卖 {sell}</span></td>"
            "<td>{detail}</td>"
            "</tr>".format(
                direction=_escape(event.direction),
                bj=_escape(event.run_time_bj),
                au=_escape(event.run_time_au),
                status=_escape(event.status),
                quality=_escape(event.quality),
                badge=_timeline_badge(event),
                buy=event.buy_count,
                sell=event.sell_count,
                detail=_timeline_detail_html(event.detail),
            )
            for event in events
        )
        visual_cards = "\n".join(
            '<article class="timeline-node {direction}">'
            '<div class="timeline-dot {direction}" aria-hidden="true"></div>'
            '<div class="timeline-node-card">'
            '<strong>{bj}</strong>'
            '<span>{badge}</span>'
            '<small>{detail}</small>'
            "</div>"
            "</article>".format(
                direction=_escape(event.direction),
                bj=_escape(event.run_time_bj),
                badge=_timeline_badge(event),
                detail=_escape(event.detail),
            )
            for event in reversed(events)
        )
    return f"""
    <section class="panel run-timeline-panel" style="margin-top:16px;">
      <div class="section-head">
        <h2>运行时间线</h2>
        <div class="view-switch" aria-label="运行时间线视图切换">
          <button type="button" class="active" data-timeline-mode="table">表格</button>
          <button type="button" data-timeline-mode="visual">时间线</button>
        </div>
      </div>
      <div class="legend"><strong>买卖标记</strong><span class="change up">买入/增加</span><span class="change down">卖出/减少</span><span class="change flat">维持</span></div>
      <div data-timeline-view="table">
        <div class="table-wrap compact">
          <table class="run-timeline-table">
            <thead>
              <tr>
                <th>运行时间</th>
                <th>状态</th>
                <th>质量</th>
                <th>动作摘要</th>
                <th>买入侧</th>
                <th>卖出侧</th>
                <th>证据摘要</th>
              </tr>
            </thead>
            <tbody>{table_rows}</tbody>
          </table>
        </div>
      </div>
      <div class="timeline-visual" data-timeline-view="visual" hidden>
        <div class="timeline-axis" aria-hidden="true"></div>
        <div class="timeline-nodes">{visual_cards}</div>
      </div>
    </section>
    """


def _manual_review_modal(items: list[PortalManualReviewItem]) -> str:
    if not items:
        cards = '<div class="review-empty">当前没有打开状态的人工复核项。</div>'
    else:
        cards = "\n".join(
            f"""
            <article class="review-item" data-review-item data-review-id="{item.review_id}" data-review-run-id="{_escape(item.run_id)}">
              <div class="review-item-head">
                <div>
                  <strong>{_escape(item.code)} · {_escape(item.name)}</strong>
                  <span>{_escape(item.created_at)} · {_escape(item.status)} · {_escape(item.run_id)}</span>
                </div>
                <span class="badge locked">{_escape(item.action_blocked)}</span>
              </div>
              <div class="review-reason">{_escape(item.reason)}</div>
              <label>
                <span>复核动作</span>
                <select data-review-decision>
                  <option value="保持禁止新增">保持禁止新增</option>
                  <option value="需要补证据">需要补证据</option>
                  <option value="确认观察">确认观察</option>
                  <option value="已人工处理">已人工处理</option>
                </select>
              </label>
              <label>
                <span>备注</span>
                <textarea data-review-note rows="3" placeholder="记录你核对的来源、平台交易页、费率或暂不处理原因"></textarea>
              </label>
              <div class="review-item-actions">
                <button type="button" data-save-review>保存复核</button>
                <span data-review-state>未保存</span>
              </div>
            </article>
            """
            for item in items
        )
    return f"""
  <div class="modal" id="review-modal" hidden>
    <div class="modal-backdrop" data-close-review></div>
    <section class="modal-panel review-panel" role="dialog" aria-modal="true" aria-labelledby="review-modal-title">
      <div class="modal-top">
        <div>
          <h2 id="review-modal-title">人工复核</h2>
          <div class="subtitle">复核记录会保存到本机 SQLite 数据库；静态入口离线时临时缓存到浏览器。</div>
        </div>
        <button type="button" data-close-review>关闭</button>
      </div>
      <div class="review-toolbar">
        <button type="button" data-copy-review-log>复制复核记录</button>
        <button type="button" data-clear-review-log>清空复核记录</button>
      </div>
      <div class="review-list">{cards}</div>
    </section>
  </div>
    """


def _fund_library_modal() -> str:
    return """
  <div class="modal" id="fund-library-modal" hidden>
    <div class="modal-backdrop" data-close-fund-library></div>
    <section class="modal-panel fund-library-panel" role="dialog" aria-modal="true" aria-labelledby="fund-library-modal-title">
      <div class="modal-top">
        <div>
          <h2 id="fund-library-modal-title">基金库</h2>
          <div class="subtitle">展示当前已入库基金的申购、赎回、费率、管理费、运营费和来源信息。</div>
        </div>
        <button type="button" data-close-fund-library>关闭</button>
      </div>
      <div class="view-switch fund-library-view-switch" aria-label="基金库视图切换">
        <button type="button" class="active" data-fund-library-mode="gallery">Gallery</button>
        <button type="button" data-fund-library-mode="table">Table</button>
      </div>
      <div class="fund-library-grid" id="fund-library-body" data-fund-library-view="gallery"></div>
      <div class="table-wrap fund-library-table-view" data-fund-library-view="table" hidden>
        <table class="fund-library-table">
          <thead>
            <tr>
              <th>代码</th>
              <th>基金名称</th>
              <th>首次进入策略 Top5</th>
              <th>上次进入候选池时间</th>
              <th>当前进入候选池天数</th>
              <th>当前状态</th>
              <th>费用/状态快照时间</th>
              <th>申购状态</th>
              <th>赎回状态</th>
              <th>交易截止时间</th>
              <th>确认周期</th>
              <th>赎回到账</th>
              <th>申购费（基础/最高）</th>
              <th>申购费分档规则</th>
              <th>赎回费（基础/最高）</th>
              <th>赎回费分档规则</th>
              <th>费率规则时间</th>
              <th>费率口径说明</th>
              <th>管理费（年）</th>
              <th>托管费（年）</th>
              <th>销售服务费</th>
              <th>合计运营费（年）</th>
              <th>最低申购金额</th>
              <th>来源名称</th>
              <th>来源类型</th>
              <th>来源优先级</th>
              <th>来源链接</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody id="fund-library-table-body"></tbody>
        </table>
      </div>
    </section>
  </div>
    """


def _usage_guide_modal() -> str:
    return """
  <div class="modal" id="usage-guide-modal" hidden>
    <div class="modal-backdrop" data-close-usage-guide></div>
    <section class="modal-panel guide-panel" role="dialog" aria-modal="true" aria-labelledby="usage-guide-modal-title">
      <div class="modal-top">
        <div>
          <h2 id="usage-guide-modal-title">使用说明</h2>
          <div class="subtitle">说明 Skill 选股逻辑、策略口径、权重配置公式和持仓调整纪律；本说明不构成自动交易指令。</div>
        </div>
        <button type="button" data-close-usage-guide>关闭</button>
      </div>
      <div class="guide-grid">
        <article class="guide-section">
          <h3>Skill 选股逻辑</h3>
          <p>Serenity 不是先拿一张规则表机械筛选，而是先建立“未来 1-3 个月最可能获得资金和业绩弹性的高成长方向”假设，再用证据验证这个假设能否落到可执行的场外基金上。</p>
          <ul>
            <li>如何挑选：先看高成长主题是否仍有景气度、资金关注和可解释的上涨来源，再把主题映射到能在场外买到的基金，而不是直接从基金列表里随便排序。</li>
            <li>怎么挑选：先按产业链卡点、稀缺层、主题暴露和 1-3 个月资金弹性形成 Serenity 优先级，再映射到能在场外买到的基金。</li>
            <li>为什么挑选：Top5 先由 Serenity 判断决定，不由 Score 机械排序；如果一只基金分数高但不在更关键的产业链位置，它不能越过更高 Serenity 优先级。</li>
            <li>为什么调仓：当新一轮证据显示产业链强弱、资金方向、风险回撤、费用/申赎状态或 Top5 排名发生变化，系统会把它解释为原 baseline 假设需要修正，并输出增配、减少、暂停新增或维持。</li>
            <li>思考公示方式：页面展示证据置信度、等级、目标权重、基准权重、相对比例、费用状态、基金库证据和运行时间线，让用户能看到“为什么是这只、为什么是这个权重、为什么现在动或不动”。</li>
          </ul>
        </article>
        <article class="guide-section">
          <h3>证据置信度</h3>
          <p><code>ConfidenceScore = Data 25 + Timeliness 15 + Source 15 + Return 15 + Risk 20 + Executable 10</code></p>
          <ul>
            <li>证据置信度不是选股主排序，只回答“Serenity 判断有多少数据支持、能不能执行”。</li>
            <li>Data = max(0, 25 - 8 x 缺失字段数)。</li>
            <li>Timeliness = 净值/持仓缺失不超过 2 天得 15，否则 0。</li>
            <li>Source = 官方级来源至少 2 个且无冲突得 15；至少 1 个得 7.5；否则 0。</li>
            <li>Return = 15 x 跑赢次数 / 6，比较窗口为 1 个月、3 个月、10 交易日，对照沪指和标普 500。</li>
            <li>Risk = MDD 小于 40.00% 才计分；回撤修复时间达到 365 天会强制压低风险分。</li>
            <li>Executable = 申购/赎回开放且费率分档完整才得 10，否则 0。</li>
          </ul>
        </article>
        <article class="guide-section">
          <h3>等级与策略口径</h3>
          <ul>
            <li>ConfidenceScore >= 85：Action-Ready，说明 Serenity 判断的证据和执行条件足够强。</li>
            <li>70-84：Watch，Serenity 判断可保留，但证据或执行条件需要继续观察。</li>
            <li>55-69：Manual Review，必须人工复核后处理。</li>
            <li>&lt;55：Block/skip，不执行调仓建议。</li>
            <li>MDD >= 40.00%、保守类资产、来源冲突、关键费率缺失会触发硬降级。</li>
          </ul>
        </article>
        <article class="guide-section">
          <h3>权重配置公式</h3>
          <p><code>SerenityRank_i = 产业链卡点优先级 + 主题暴露 + 场外可执行性</code></p>
          <p><code>ConfidenceModifier_i = 0.85 + 0.15 x ConfidenceScore_i / 100</code></p>
          <p><code>RawWeight_i = SerenityBase_i x ConfidenceModifier_i</code></p>
          <p><code>Capped_i = min(normalize(RawWeight_i), 30.00%)</code></p>
          <p><code>TargetWeight_i = Capped_i / sum(Capped)</code></p>
          <ul>
            <li>仅非 Block 候选参与 Top5；排序优先服从 Serenity 判断，证据置信度只做辅助修正。</li>
            <li>低 Serenity 优先级标的不会仅凭更高 ConfidenceScore 超过高优先级标的。</li>
            <li>目标权重是策略份额，不是支付宝真实账户仓位。</li>
            <li>首轮基准从 0.00% 开始；后续运行相对上一轮 Serenity baseline 比较。</li>
          </ul>
        </article>
        <article class="guide-section">
          <h3>持仓调整逻辑</h3>
          <p>这里不是把 Deviation 翻译成买卖术语，而是说明系统如何从 Serenity 新判断推导到人工操作建议。</p>
          <ul>
            <li><code>Deviation = TargetWeight - BaselineWeight</code>。</li>
            <li>凭什么：先确认数据质量通过、基金申赎和费率可执行、候选没有 Block，再比较新一轮 Serenity 目标权重和上一轮 Serenity baseline。</li>
            <li>为什么：偏离不是账户盈亏，而是 Serenity 对产业链优先级、主题弹性、风险和执行条件的最新判断相对旧 baseline 的变化。</li>
            <li>怎么做：|Deviation| &lt;= 1.00%：维持；Deviation &gt; 1.00% 且 Action-Ready：增配；非 Action-Ready：暂停新增或人工复核；Deviation &lt; -1.00%：减少；Block：阻断或清仓标签。</li>
            <li>做多少：策略调整份额 = TargetWeight - BaselineWeight；若需要换算金额，人工按“计划投入资金 x |Deviation|”在支付宝或官方平台确认，系统不自动下单。</li>
            <li>为什么做这么多：TargetWeight 已由 Serenity 优先级、证据置信度修正、30.00% 单标上限和归一化约束计算完成；Deviation 是把旧 baseline 调到新目标所需的最小策略差额。</li>
            <li>为什么 1.00% 内维持：小于等于 1.00% 的变化通常不足以覆盖确认成本、申赎费、净值时差和短时噪声，除非同时触发风险硬门槛。</li>
          </ul>
        </article>
        <article class="guide-section">
          <h3>重平衡触发</h3>
          <ul>
            <li>单标偏离超过 1.00% 会触发纪律事件。</li>
            <li>Top5 变动率超过 20.00%、新增 1 只、替换 2 只会触发复核。</li>
            <li>关键字段变化超过 1σ 会触发 regime check。</li>
            <li>同日、前一日、前一周、前一月都会生成对比快照。</li>
          </ul>
        </article>
        <article class="guide-section">
          <h3>人工复核与降级</h3>
          <ul>
            <li>连续缺失净值/持仓超过 2 天，进入 Manual Review。</li>
            <li>申购费、赎回费、申购状态、赎回状态或费率分档缺失，暂停新增。</li>
            <li>官方级来源少于 2 个或来源冲突，不能 Action-Ready。</li>
            <li>执行锁开启时，只输出研究排序和纪律标签，不给新增订单。</li>
          </ul>
        </article>
        <article class="guide-section">
          <h3>如何使用</h3>
          <ul>
            <li>先看“当前持仓建议”，确认最新时间和动作颜色。</li>
            <li>再看“持仓建议”表，切换初始持仓权重或上轮对比权重。</li>
            <li>点击“基金库”核对申赎状态和费用分档。</li>
            <li>若出现人工复核，先补证据或记录复核结论，再考虑平台操作。</li>
            <li>所有真实申购、赎回、增配、减配都必须在支付宝或官方平台人工确认。</li>
          </ul>
        </article>
      </div>
    </section>
  </div>
    """


def _action_summary(rows: list[PortalHolding], previous: list[PortalHolding]) -> tuple[str, str, str]:
    if not rows:
        return "无数据", "等待下一轮运行", "暂无建议行，不能生成操作动作。"
    previous_by_code = {row.code: row for row in previous}
    changed = [
        (row, _change(row.target_weight, previous_by_code.get(row.code).target_weight if previous_by_code.get(row.code) else None))
        for row in rows
    ]
    actionable = [item for item in changed if item[1][0] in {"up", "down"} or item[0].action_label not in {"Maintain"}]
    if not actionable:
        return "无需交易", "全部维持", "当前 Top5 策略份额暂无变化。"
    labels = ", ".join(f"{row.code} {change[2]} {change[1]}" for row, change in actionable)
    return "需要人工确认", f"{len(actionable)} 项变化", labels


def _default_alipay_trade_status(subscription_status: str | None, redemption_status: str | None) -> str:
    sub = (subscription_status or "").lower()
    red = (redemption_status or "").lower()
    if sub == "open" and red == "open":
        return "待支付宝交易页确认（基金本身申赎开放）"
    if sub == "limited" or red == "limited":
        return "待支付宝交易页确认（基金本身申赎存在额度或时段限制）"
    return "待支付宝交易页确认（基金本身申购或赎回受限）"


def _default_moomoo_trade_status() -> str:
    return "未验证MooMoo场外基金交易；MooMoo仅作行情/代理数据参考"


def _default_platform_trade_note() -> str:
    return "平台交易可用性只作建议；不支持支付宝或MooMoo交易不能单独排除候选；执行前以支付宝交易确认页或基金公司官方平台为准"


def _fund_library_json(fund_library: dict[str, PortalFundInfo]) -> str:
    data: dict[str, dict[str, object]] = {}
    for code, info in fund_library.items():
        operating_fee = sum(
            value or 0.0 for value in [info.management_fee, info.custody_fee, info.sales_service_fee]
        )
        subscription_schedule = (
            info.subscription_fee_schedule
            or "未提供完整申购费金额分档；不能仅凭单一费率执行。"
        )
        redemption_schedule = (
            info.redemption_fee_schedule
            or "未提供完整赎回费持有期分档；不能仅凭单一费率执行。"
        )
        fee_note = (
            info.fee_schedule_note
            or "费率可能随持有期限、申购金额、销售渠道折扣、A/C份额或基金公告调整；执行前以支付宝交易页和基金公司公告为准。"
        )
        data[code] = {
            "code": info.code,
            "name": info.name,
            "firstTop5Time": _format_time(info.first_top5_time_bj, "Asia/Shanghai"),
            "lastTop5EntryTime": _format_time(info.last_top5_entry_time_bj, "Asia/Shanghai"),
            "currentCandidateDays": (
                f"{info.current_candidate_days} 天" if info.current_candidate_days is not None else "-"
            ),
            "candidateStatus": info.candidate_status or "-",
            "ruleSnapshotTime": _format_time(info.rule_snapshot_time_bj, "Asia/Shanghai"),
            "subscriptionStatus": info.subscription_status or "-",
            "redemptionStatus": info.redemption_status or "-",
            "cutoffTime": info.cutoff_time or "-",
            "confirmLag": info.confirm_lag or "-",
            "redeemLag": info.redeem_lag or "-",
            "alipayTradeStatus": info.alipay_trade_status
            or _default_alipay_trade_status(info.subscription_status, info.redemption_status),
            "moomooTradeStatus": info.moomoo_trade_status or _default_moomoo_trade_status(),
            "platformTradeNote": info.platform_trade_note or _default_platform_trade_note(),
            "subscriptionFee": _fee(info.subscription_fee),
            "redemptionFee": _fee(info.redemption_fee),
            "subscriptionFeeSchedule": subscription_schedule,
            "redemptionFeeSchedule": redemption_schedule,
            "feeScheduleAsOf": info.fee_schedule_as_of or "-",
            "feeScheduleNote": fee_note,
            "managementFee": _fee(info.management_fee),
            "custodyFee": _fee(info.custody_fee),
            "salesServiceFee": _fee(info.sales_service_fee),
            "operatingFee": _fee(operating_fee),
            "minPurchaseAmount": _amount(info.min_purchase_amount),
            "sourceName": info.source_name or "-",
            "sourceType": info.source_type or "-",
            "sourcePriority": info.source_priority if info.source_priority is not None else "-",
            "sourceUrl": info.source_url or "-",
        }
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def render_application_portal(
    current_run: PortalRun | None,
    current_holdings: list[PortalHolding],
    previous_run: PortalRun | None,
    previous_holdings: list[PortalHolding],
    *,
    baseline_time_bj: str | None = None,
    fund_library: dict[str, PortalFundInfo] | None = None,
    run_timeline: list[PortalTimelineEvent] | None = None,
    manual_review_items: list[PortalManualReviewItem] | None = None,
) -> str:
    current_bj = (
        display_run_time_with_backfill_note(current_run.run_time_bj, current_run.created_at)
        if current_run
        else "-"
    )
    current_au = _format_time(current_run.run_time_au, "Australia/Sydney") if current_run else "-"
    current_created = _format_time(current_run.created_at, "Asia/Shanghai") if current_run else "-"
    current_updated_au = _format_compact_time(current_run.created_at, "Australia/Sydney") if current_run else "-"
    previous_bj = _format_time(previous_run.run_time_bj, "Asia/Shanghai") if previous_run else "-"
    previous_au = _format_time(previous_run.run_time_au, "Australia/Sydney") if previous_run else "-"
    previous_created = _format_time(previous_run.created_at, "Asia/Shanghai") if previous_run else "-"
    previous_updated_au = _format_compact_time(previous_run.created_at, "Australia/Sydney") if previous_run else "-"
    baseline_bj = _format_time(baseline_time_bj or (previous_run.run_time_bj if previous_run else None), "Asia/Shanghai")
    action_level, action_count, action_detail = _action_summary(current_holdings, previous_holdings)
    latest_run_time = current_bj
    report_href = _portal_relative_href("data/reports/index.html", "../../data/reports/index.html")
    snapshot_href = _portal_relative_href(
        current_run.html_path if current_run else None,
        report_href,
    )
    previous_by_code = {row.code: row for row in previous_holdings}
    fund_json = _fund_library_json(fund_library or {})
    timeline_events = run_timeline or []
    review_items = manual_review_items or []
    review_count_text = f"{len(review_items)} 项待复核" if review_items else "无打开项"
    fund_count = len(fund_library or {})
    fund_count_text = f"已入库 {fund_count} 只基金" if fund_count else "暂无入库基金"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="120">
  <title>Serenity 每日分析</title>
  <style>
    :root {{
      color-scheme: light;
      --page: #f5f7f4;
      --surface: #ffffff;
      --surface-2: #eef3ef;
      --ink: #132027;
      --muted: #64717b;
      --line: #d9e0da;
      --accent: #0b6f7b;
      --accent-2: #1f7a4d;
      --buy: #c13b3b;
      --sell: #1f7a4d;
      --hold: #1f6ea8;
      --hold-bg: #e8f4ff;
      --hold-border: #b8dcf6;
      --warn: #946200;
      --danger: #a33b3b;
      --shadow: 0 10px 28px rgba(20, 35, 30, 0.08);
      --radius: 8px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      background: var(--page);
      color: var(--ink);
    }}
    a {{ color: inherit; }}
    button, a.action {{
      min-height: 38px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--surface);
      color: var(--ink);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      font: inherit;
      font-weight: 700;
      padding: 9px 12px;
      text-decoration: none;
      transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease, background 160ms ease;
    }}
    button:hover, a.action:hover,
    button:focus-visible, a.action:focus-visible {{
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(11, 111, 123, 0.14);
      outline: none;
    }}
    button:active, a.action:active {{ transform: translateY(1px); }}
    .primary {{ background: var(--accent); border-color: var(--accent); color: #fff; }}
    .floating-refresh {{
      position: fixed;
      top: 14px;
      right: 14px;
      z-index: 20;
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
      box-shadow: var(--shadow);
    }}
    .shell {{ max-width: 1240px; margin: 0 auto; padding: 24px 18px 42px; }}
    .topbar {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 18px;
      align-items: start;
      border-bottom: 1px solid var(--line);
      padding-bottom: 18px;
      padding-right: 92px;
    }}
    h1 {{ margin: 0; font-size: 30px; line-height: 1.15; letter-spacing: 0; }}
    h2 {{ margin: 0 0 12px; font-size: 18px; letter-spacing: 0; }}
    h3 {{ margin: 0 0 8px; font-size: 15px; letter-spacing: 0; }}
    .subtitle {{ color: var(--muted); line-height: 1.55; margin-top: 8px; max-width: 820px; }}
    .gate {{
      min-width: 260px;
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 14px;
      box-shadow: var(--shadow);
    }}
    .gate-title {{ color: var(--muted); font-size: 13px; margin-bottom: 8px; }}
    .gate-value {{ color: var(--accent-2); font-size: 24px; font-weight: 800; line-height: 1.1; }}
    .gate-note {{ color: var(--muted); font-size: 13px; margin-top: 8px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 18px 0; }}
    .metric {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 14px;
      min-height: 98px;
    }}
    .metric span {{ display: block; color: var(--muted); font-size: 13px; }}
    .metric strong {{ display: block; font-size: 22px; margin-top: 8px; line-height: 1.15; }}
    .panel {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 16px;
      box-shadow: var(--shadow);
      min-width: 0;
    }}
    .home-grid {{ display: grid; grid-template-columns: minmax(0, 1fr) 330px; gap: 16px; align-items: start; }}
    .discipline-list {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }}
    .discipline-card {{
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 12px;
      background: #fbfcfb;
      min-width: 0;
      display: grid;
      gap: 10px;
      align-content: start;
    }}
    .discipline-card.up {{ border-color: #f0b3a6; background: #fff7f4; }}
    .discipline-card.down {{ border-color: #a9d9b7; background: #f3faf5; }}
    .discipline-card.flat {{ border-color: var(--hold-border); background: #f6fbff; }}
    .recommendation-head {{
      display: grid;
      grid-template-columns: auto minmax(0, 1fr);
      gap: 8px;
      align-items: start;
      min-height: 42px;
    }}
    .recommendation-rank {{
      color: var(--muted);
      font-weight: 800;
      line-height: 1.35;
    }}
    .discipline-card strong {{ display: block; font-size: 24px; line-height: 1; }}
    .recommendation-meta {{
      border-top: 1px solid var(--line);
      padding-top: 9px;
      display: grid;
      gap: 5px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }}
    .recommendation-meta span {{ display: block; }}
    .legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      color: var(--muted);
      font-size: 13px;
      margin: -4px 0 12px;
    }}
    .legend strong {{ color: var(--ink); }}
    .reference-switch {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      margin: 0 0 12px;
      color: var(--muted);
      font-size: 13px;
    }}
    .reference-switch strong {{ color: var(--ink); }}
    .reference-switch button {{
      min-height: 30px;
      padding: 5px 10px;
      font-size: 13px;
      border-radius: 999px;
    }}
    .reference-switch button.active {{
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
    }}
    .section-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
    }}
    .section-head h2 {{ margin-bottom: 0; }}
    .view-switch {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }}
    .view-switch button {{
      min-height: 30px;
      padding: 5px 10px;
      font-size: 13px;
      border-radius: 999px;
    }}
    .view-switch button.active {{
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
    }}
    .run-timeline-table tr.timeline-row-buy td {{ background: #fff7f4; }}
    .run-timeline-table tr.timeline-row-sell td {{ background: #f3faf5; }}
    .run-timeline-table tr.timeline-row-flat td {{ background: #f6fbff; }}
    .run-timeline-table tr.timeline-row-mixed td {{ background: linear-gradient(90deg, #fff7f4 0, #fff7f4 50%, #f3faf5 50%, #f3faf5 100%); }}
    .timeline-badge, .timeline-count {{
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border-radius: 999px;
      padding: 3px 9px;
      font-size: 12px;
      font-weight: 900;
      white-space: nowrap;
    }}
    .timeline-badge.buy, .timeline-count.buy {{ color: var(--buy); background: #fde9e6; }}
    .timeline-badge.sell, .timeline-count.sell {{ color: var(--sell); background: #e8f5ed; }}
    .timeline-badge.flat {{ color: var(--hold); background: var(--hold-bg); }}
    .timeline-badge.mixed {{
      color: #783b12;
      background: linear-gradient(90deg, #fde9e6 0, #fde9e6 50%, #e8f5ed 50%, #e8f5ed 100%);
      border: 1px solid #ead1c2;
    }}
    .timeline-detail-lines {{
      display: grid;
      gap: 4px;
      min-width: 240px;
      color: var(--ink);
      font-size: 13px;
      line-height: 1.45;
    }}
    .timeline-detail-lines span {{
      display: block;
      overflow-wrap: anywhere;
    }}
    .timeline-visual {{
      position: relative;
      overflow-x: auto;
      padding: 14px 2px 4px;
    }}
    .timeline-axis {{
      position: absolute;
      left: 8px;
      right: 8px;
      top: 34px;
      height: 2px;
      background: var(--line);
    }}
    .timeline-nodes {{
      position: relative;
      display: grid;
      grid-auto-flow: column;
      grid-auto-columns: minmax(168px, 1fr);
      gap: 12px;
      min-width: 720px;
      align-items: start;
    }}
    .timeline-node {{
      display: grid;
      gap: 9px;
      justify-items: center;
      min-width: 0;
    }}
    .timeline-dot {{
      width: 24px;
      height: 24px;
      border-radius: 999px;
      border: 3px solid var(--surface);
      box-shadow: 0 0 0 1px var(--line);
      z-index: 1;
    }}
    .timeline-dot.buy {{ background: var(--buy); }}
    .timeline-dot.sell {{ background: var(--sell); }}
    .timeline-dot.flat {{ background: #7bbce8; }}
    .timeline-dot.mixed {{ background: linear-gradient(90deg, var(--buy) 0 50%, var(--sell) 50% 100%); }}
    .timeline-node-card {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: #fbfcfb;
      padding: 11px;
      min-height: 132px;
      display: grid;
      gap: 6px;
    }}
    .timeline-node.buy .timeline-node-card {{ border-color: #f0b3a6; background: #fff7f4; }}
    .timeline-node.sell .timeline-node-card {{ border-color: #a9d9b7; background: #f3faf5; }}
    .timeline-node.flat .timeline-node-card {{ border-color: var(--hold-border); background: #f6fbff; }}
    .timeline-node.mixed .timeline-node-card {{ border-color: #d8c8ae; background: linear-gradient(90deg, #fff7f4 0, #fff7f4 50%, #f3faf5 50%, #f3faf5 100%); }}
    .timeline-node-card span, .timeline-node-card small {{
      color: var(--muted);
      line-height: 1.35;
      overflow-wrap: anywhere;
    }}
    .timeline-node-card small {{ font-size: 12px; }}
    .timeline-empty {{ color: var(--muted); padding: 12px; }}
    .fund-link {{
      border: 0;
      padding: 0;
      min-height: 0;
      display: inline;
      color: var(--accent);
      background: transparent;
      font-weight: 800;
      text-align: left;
      text-decoration: underline;
      text-underline-offset: 3px;
      box-shadow: none;
    }}
    .fund-link:hover, .fund-link:focus-visible {{ box-shadow: none; color: #064e59; }}
    .timeline {{ display: grid; gap: 10px; }}
    .time-card {{
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 12px;
      background: #fbfcfb;
    }}
    .time-card .label {{ color: var(--muted); font-size: 13px; }}
    .time-card strong {{ display: block; margin-top: 6px; font-size: 16px; }}
    .time-card small {{ display: block; color: var(--muted); margin-top: 6px; line-height: 1.45; }}
    .table-wrap {{ border: 1px solid var(--line); border-radius: var(--radius); overflow: auto; background: var(--surface); max-width: 100%; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 980px; }}
    th, td {{ padding: 11px 12px; border-bottom: 1px solid var(--line); text-align: left; font-size: 14px; vertical-align: top; }}
    th {{ background: var(--surface-2); color: #26323a; }}
    th span, td span {{ display: block; color: var(--muted); margin-top: 4px; line-height: 1.35; font-size: 12px; }}
    tr:last-child td {{ border-bottom: 0; }}
    .compact table {{ min-width: 780px; }}
    .row-up td {{ background: #fffaf8; }}
    .row-down td {{ background: #f7fcf8; }}
    .row-flat td {{ background: #f6fbff; }}
    .badge {{
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border-radius: 999px;
      padding: 3px 9px;
      font-size: 12px;
      font-weight: 800;
      background: #e8f5ed;
      color: var(--accent-2);
      border: 1px solid #c9e3d3;
      white-space: nowrap;
    }}
    .badge.warn {{ background: #fff4d8; border-color: #ead59d; color: var(--warn); }}
    .badge.locked {{ background: #fae9e9; border-color: #ebc6c6; color: var(--danger); }}
    .badge.hold {{ background: var(--hold-bg); border-color: var(--hold-border); color: var(--hold); }}
    .change {{ display: inline-flex; align-items: center; min-height: 24px; border-radius: 999px; padding: 3px 9px; font-weight: 900; }}
    .change.up {{ color: var(--buy); background: #fde9e6; }}
    .change.down {{ color: var(--sell); background: #e8f5ed; }}
    .change.flat {{ color: var(--hold); background: var(--hold-bg); }}
    .action-summary {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin: 16px 0; }}
    .action-box {{
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 14px;
      background: #fbfcfb;
      min-height: 110px;
    }}
    .action-box span {{ color: var(--muted); display: block; font-size: 13px; }}
    .action-box strong {{ display: block; margin-top: 8px; font-size: 19px; }}
    .actions {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; margin-top: 16px; }}
    .action-card {{
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 14px;
      background: #fbfcfb;
      min-height: 122px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 12px;
    }}
    .action-card p {{ margin: 8px 0 0; color: var(--muted); line-height: 1.45; font-size: 14px; }}
    .modal[hidden] {{ display: none; }}
    .modal {{ position: fixed; inset: 0; z-index: 30; display: grid; place-items: center; padding: 18px; }}
    #fund-library-modal {{ z-index: 32; }}
    #fund-modal {{ z-index: 36; }}
    .modal-backdrop {{ position: absolute; inset: 0; background: rgba(19, 32, 39, 0.42); }}
    .modal-panel {{
      position: relative;
      width: min(760px, 100%);
      max-height: min(760px, 88vh);
      overflow: auto;
      background: var(--surface);
      border-radius: var(--radius);
      border: 1px solid var(--line);
      box-shadow: 0 18px 50px rgba(20, 35, 30, 0.18);
      padding: 18px;
    }}
    .review-panel {{ width: min(900px, 100%); }}
    .modal-top {{ display: flex; justify-content: space-between; gap: 12px; align-items: start; border-bottom: 1px solid var(--line); padding-bottom: 12px; margin-bottom: 12px; }}
    .review-toolbar {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }}
    .review-list {{ display: grid; gap: 10px; }}
    .review-empty {{ color: var(--muted); border: 1px dashed var(--line); border-radius: var(--radius); padding: 14px; background: #fbfcfb; }}
    .review-item {{
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: #fbfcfb;
      padding: 12px;
      display: grid;
      gap: 10px;
    }}
    .review-item-head {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      align-items: start;
    }}
    .review-item-head strong, .review-item-head span {{ overflow-wrap: anywhere; }}
    .review-item-head span, .review-reason, .review-item-actions span {{ color: var(--muted); line-height: 1.45; }}
    .review-reason {{ border-left: 3px solid var(--danger); padding-left: 10px; }}
    .review-item label {{ display: grid; gap: 5px; color: var(--muted); font-size: 13px; }}
    .review-item select, .review-item textarea {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--surface);
      color: var(--ink);
      font: inherit;
      padding: 9px 10px;
    }}
    .review-item textarea {{ resize: vertical; min-height: 76px; }}
    .review-item-actions {{ display: flex; align-items: center; flex-wrap: wrap; gap: 10px; }}
    .guide-panel {{ width: min(1060px, 100%); }}
    .guide-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }}
    .guide-section {{
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: #fbfcfb;
      padding: 12px;
    }}
    .guide-section h3 {{ margin: 0 0 8px; font-size: 16px; }}
    .guide-section p {{ margin: 8px 0; color: var(--muted); line-height: 1.55; }}
    .guide-section ul {{ margin: 0; padding-left: 18px; color: var(--muted); line-height: 1.55; }}
    .guide-section li + li {{ margin-top: 5px; }}
    .guide-section code {{
      display: inline-block;
      max-width: 100%;
      overflow-wrap: anywhere;
      white-space: normal;
      background: #eef3ef;
      color: var(--ink);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 2px 5px;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 12px;
    }}
    .fund-library-panel {{ width: min(1080px, 100%); }}
    .fund-library-view-switch {{ margin: 0 0 12px; }}
    .fund-library-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }}
    .fund-library-card {{
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 12px;
      background: #fbfcfb;
      display: grid;
      gap: 10px;
    }}
    .fund-library-head {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      align-items: start;
    }}
    .fund-library-head strong, .fund-library-head span {{ overflow-wrap: anywhere; }}
    .fund-library-head span, .fund-library-meta {{ color: var(--muted); line-height: 1.45; }}
    .fund-library-meta {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      font-size: 13px;
    }}
    .fund-library-meta span {{
      display: block;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--surface);
      padding: 8px;
      overflow-wrap: anywhere;
    }}
    .fund-library-schedule {{
      border-left: 3px solid var(--accent);
      padding-left: 10px;
      color: var(--muted);
      line-height: 1.5;
      overflow-wrap: anywhere;
      white-space: pre-wrap;
    }}
    .fund-library-table-view {{ max-height: 560px; overflow: auto; }}
    .fund-library-table {{ min-width: 3200px; }}
    .fund-library-table th {{
      position: sticky;
      top: 0;
      z-index: 1;
    }}
    .fund-library-table td {{
      min-width: 112px;
      max-width: 260px;
      white-space: normal;
      overflow-wrap: anywhere;
      line-height: 1.45;
      font-size: 12px;
    }}
    .fund-library-table td:nth-child(1) {{ min-width: 86px; }}
    .fund-library-table td:nth-child(2) {{ min-width: 220px; font-weight: 800; color: var(--ink); }}
    .fund-library-table td:nth-child(14),
    .fund-library-table td:nth-child(16),
    .fund-library-table td:nth-child(18),
    .fund-library-table td:nth-child(24),
    .fund-library-table td:nth-child(27) {{ min-width: 260px; }}
    .fund-library-empty {{ color: var(--muted); border: 1px dashed var(--line); border-radius: var(--radius); padding: 14px; background: #fbfcfb; }}
    .fund-fields {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }}
    .fund-field {{ border: 1px solid var(--line); border-radius: var(--radius); padding: 10px; background: #fbfcfb; }}
    .fund-field.wide {{ grid-column: 1 / -1; }}
    .fund-field.warning {{ border-color: #e3c585; background: #fff8e6; }}
    .fund-field span {{ display: block; color: var(--muted); font-size: 12px; }}
    .fund-field strong {{ display: block; margin-top: 5px; overflow-wrap: anywhere; white-space: pre-wrap; line-height: 1.45; }}
    .toast {{
      position: fixed;
      right: 18px;
      bottom: 18px;
      background: #14242a;
      color: #fff;
      border-radius: var(--radius);
      padding: 12px 14px;
      box-shadow: var(--shadow);
      opacity: 0;
      transform: translateY(10px);
      transition: opacity 180ms ease, transform 180ms ease;
      pointer-events: none;
      z-index: 40;
    }}
    .toast.show {{ opacity: 1; transform: translateY(0); }}
    @media (max-width: 1080px) {{
      .discipline-list {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 980px) {{
      .topbar, .home-grid {{ grid-template-columns: 1fr; }}
      .topbar {{ padding-right: 86px; }}
      .gate {{ min-width: 0; }}
      .metrics, .action-summary {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .actions {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 560px) {{
      .shell {{ padding: 18px 12px 32px; }}
      .floating-refresh {{ top: 10px; right: 10px; }}
      h1 {{ font-size: 24px; }}
      .section-head {{ align-items: stretch; flex-direction: column; }}
      .view-switch {{ width: 100%; }}
      .metrics, .action-summary, .discipline-list, .fund-fields, .fund-library-grid, .fund-library-meta, .guide-grid, .review-item-head {{ grid-template-columns: 1fr; }}
      button, a.action {{ width: 100%; }}
      .fund-link {{ width: auto; }}
    }}
  </style>
</head>
<body>
  <button type="button" class="floating-refresh" data-refresh>刷新</button>
  <main class="shell">
    <header class="topbar">
      <div>
        <h1>Serenity 每日分析</h1>
      </div>
      <aside class="gate" aria-label="生产门禁">
        <div class="gate-title">生产门禁</div>
        <div class="gate-value">通过</div>
        <div class="gate-note">完成度 98.57% · 69 通过 / 1 警告 / 0 阻断</div>
      </aside>
    </header>

    <section class="metrics" aria-label="关键状态">
      <div class="metric"><span>当前运行</span><strong>{_escape(latest_run_time)} · {_escape(_zh_status(current_run.quality if current_run else '-'))}</strong></div>
      <div class="metric"><span>当前持仓及时间</span><strong>{_escape(current_bj)}</strong></div>
      <div class="metric"><span>需操作行为</span><strong>{_escape(action_level)}</strong></div>
      <div class="metric"><span>候选池</span><strong>Top5 混合</strong></div>
    </section>

    <section class="panel" style="margin-bottom:16px;">
      <h2>当前持仓建议</h2>
      <div class="legend"><span class="change up">增加/买入</span><span class="change down">减少/卖出</span><span class="change flat">维持</span></div>
      <div class="discipline-list">{_discipline_cards(current_holdings, previous_holdings, latest_time=current_updated_au, comparison_time=previous_updated_au)}</div>
    </section>

    <section class="home-grid">
      <div class="panel">
        <h2>持仓建议</h2>
        <div class="reference-switch" aria-label="基准权重口径">
          <strong>基准权重口径</strong>
          <button type="button" class="active" data-reference-mode="initial">初始持仓权重</button>
          <button type="button" data-reference-mode="previous">上轮对比权重</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>排名</th>
                <th>基金</th>
                <th>等级</th>
                <th>证据置信度</th>
                <th>目标权重<span>{_escape(current_bj)}</span></th>
                <th>基准权重<span data-reference-head-time data-initial-value="{_escape(baseline_bj)}" data-previous-value="{_escape(previous_bj)}">{_escape(baseline_bj)}</span></th>
                <th>相对比例</th>
                <th>动作</th>
                <th>操作口径</th>
              </tr>
            </thead>
            <tbody>{_holding_rows(current_holdings, previous_by_code=previous_by_code, target_time=current_bj, baseline_time=baseline_bj, previous_time=previous_bj)}</tbody>
          </table>
        </div>

        <section class="action-summary" aria-label="需操作的行为">
          <div class="action-box"><span>立即动作</span><strong>{_escape(action_level)}</strong></div>
          <div class="action-box"><span>动作数量</span><strong>{_escape(action_count)}</strong></div>
          <div class="action-box"><span>执行边界</span><strong>人工确认</strong></div>
        </section>
        <div class="panel" style="box-shadow:none;background:#fbfcfb;">
          <h2>需操作的行为</h2>
          <p style="margin:0;color:var(--muted);line-height:1.6;">{_escape(action_detail)}</p>
        </div>
      </div>

      <aside class="panel">
        <h2>时间与口径</h2>
        <div class="timeline">
          <div class="time-card">
            <div class="label">当前持仓及时间</div>
            <strong>{_escape(current_bj)}</strong>
            <small>澳洲：{_escape(current_au)}<br>生成：{_escape(current_created)}</small>
          </div>
          <div class="time-card">
            <div class="label">上轮持仓及时间</div>
            <strong>{_escape(previous_bj)}</strong>
            <small>澳洲：{_escape(previous_au)}<br>生成：{_escape(previous_created)}</small>
          </div>
          <div class="time-card">
            <div class="label">基准权重时间</div>
            <strong>{_escape(baseline_bj)}</strong>
            <small>基准来自 Serenity baseline reference，不是支付宝真实账户持仓。</small>
          </div>
          <div class="time-card">
            <div class="label">口径说明</div>
            <strong>策略份额/权重</strong>
            <small>页面里的“份额”指策略配置份额，即目标权重；支付宝持仓仅作为后续可选 overlay。</small>
          </div>
        </div>
      </aside>
    </section>

    {_run_timeline_panel(timeline_events)}

    <section class="panel" style="margin-top:16px;">
      <h2>操作入口</h2>
      <div class="actions">
        <article class="action-card">
          <div><strong>报告</strong><p>查看最新结果和历史归档。</p></div>
          <a class="action primary" href="{report_href}">查看报告</a>
        </article>
        <article class="action-card">
          <div><strong>当前快照</strong><p>直接打开本轮完整快照。</p></div>
          <a class="action" href="{_escape(snapshot_href)}">查看快照</a>
        </article>
        <article class="action-card">
          <div><strong>基金库</strong><p>{_escape(fund_count_text)}；申赎、费率、状态。</p></div>
          <button type="button" data-open-fund-library>查看基金</button>
        </article>
        <article class="action-card">
          <div><strong>使用说明</strong><p>策略、权重、调仓纪律。</p></div>
          <button type="button" data-open-usage-guide>查看说明</button>
        </article>
        <article class="action-card">
          <div><strong>人工复核</strong><p>{_escape(review_count_text)}；保存到数据库。</p></div>
          <button type="button" data-open-review>处理复核</button>
        </article>
      </div>
    </section>

    <section class="panel" style="margin-top:16px;">
      <h2>执行边界</h2>
      <div class="table-wrap compact">
        <table>
          <thead><tr><th>范围</th><th>规则</th></tr></thead>
          <tbody>
            <tr><td>交易</td><td>无自动交易、无自动下单、无自动基金申购或赎回。</td></tr>
            <tr><td>基准</td><td>Serenity baseline 是纪律审计参考；当前支付宝仓位不是 baseline。</td></tr>
            <tr><td>风险</td><td>最大回撤达到 40.00% 或回撤修复时间达到 365 天会触发硬降级。</td></tr>
            <tr><td>邮件</td><td>Apple Mail 提醒必须在生产门禁通过且显式启用后发送。</td></tr>
            <tr><td>交付</td><td><a href="../package/serenity_daily_analysis_delivery.zip">打开交付包</a></td></tr>
          </tbody>
        </table>
      </div>
    </section>
  </main>

  <div class="modal" id="fund-modal" hidden>
    <div class="modal-backdrop" data-close-fund></div>
    <section class="modal-panel" role="dialog" aria-modal="true" aria-labelledby="fund-modal-title">
      <div class="modal-top">
        <div>
          <h2 id="fund-modal-title">基金信息</h2>
          <div class="subtitle" id="fund-modal-subtitle"></div>
        </div>
        <button type="button" data-close-fund data-close-fund-button>关闭</button>
      </div>
      <div class="fund-fields" id="fund-modal-body"></div>
    </section>
  </div>
  {_fund_library_modal()}
  {_usage_guide_modal()}
  {_manual_review_modal(review_items)}
  <div class="toast" role="status" aria-live="polite" id="toast">完成</div>
  <script>
    const toast = document.getElementById("toast");
    const fundLibrary = {fund_json};
    const showToast = (message) => {{
      toast.textContent = message;
      toast.classList.add("show");
      window.clearTimeout(showToast.timer);
      showToast.timer = window.setTimeout(() => toast.classList.remove("show"), 3200);
    }};
    const pendingRefreshToast = window.sessionStorage.getItem("serenityRefreshToast");
    if (pendingRefreshToast) {{
      window.sessionStorage.removeItem("serenityRefreshToast");
      showToast(pendingRefreshToast);
    }}
    document.querySelectorAll("[data-refresh]").forEach((button) => {{
      button.addEventListener("click", async () => {{
        const original = button.textContent;
        button.disabled = true;
        button.textContent = "更新中";
        showToast("正在同步最新信息");
        if (window.location.protocol === "file:") {{
          showToast("当前为静态入口，已重新载入本地页面");
          window.setTimeout(() => window.location.reload(), 900);
          window.setTimeout(() => {{
            button.disabled = false;
            button.textContent = original;
          }}, 1000);
          return;
        }}
        try {{
          const response = await fetch("/api/refresh", {{ method: "POST" }});
          const data = await response.json();
          if (!response.ok || data.status !== "pass") {{
            throw new Error(data.message || "刷新失败");
          }}
          window.sessionStorage.setItem("serenityRefreshToast", data.message);
          window.location.reload();
        }} catch (error) {{
          const message = error && error.message ? error.message : "当前为静态入口，已重新载入本地页面";
          showToast(message);
          window.setTimeout(() => window.location.reload(), 900);
        }} finally {{
          window.setTimeout(() => {{
            button.disabled = false;
            button.textContent = original;
          }}, 1000);
        }}
      }});
    }});

    const setReferenceMode = (mode) => {{
      document.querySelectorAll("[data-reference-mode]").forEach((button) => {{
        const active = button.dataset.referenceMode === mode;
        button.classList.toggle("active", active);
        button.setAttribute("aria-pressed", active ? "true" : "false");
      }});
      document.querySelectorAll("[data-reference-head-time]").forEach((node) => {{
        node.textContent = node.dataset[`${{mode}}Value`] || "-";
      }});
      document.querySelectorAll("[data-reference-row]").forEach((row) => {{
        const nextClass = row.dataset[`${{mode}}Class`] || "flat";
        row.classList.remove("row-up", "row-down", "row-flat");
        row.classList.add(`row-${{nextClass}}`);
      }});
      document.querySelectorAll("[data-reference-weight], [data-reference-time], [data-relative-action]").forEach((node) => {{
        node.textContent = node.dataset[`${{mode}}Value`] || "-";
      }});
      document.querySelectorAll("[data-relative-ratio]").forEach((node) => {{
        const nextClass = node.dataset[`${{mode}}Class`] || "flat";
        node.textContent = node.dataset[`${{mode}}Value`] || "-";
        node.classList.remove("up", "down", "flat");
        node.classList.add(nextClass);
      }});
    }};
    document.querySelectorAll("[data-reference-mode]").forEach((button) => {{
      button.addEventListener("click", () => {{
        setReferenceMode(button.dataset.referenceMode || "initial");
        showToast(`基准权重口径：${{button.textContent}}`);
      }});
    }});
    setReferenceMode("initial");

    const setTimelineMode = (mode) => {{
      document.querySelectorAll("[data-timeline-mode]").forEach((button) => {{
        const active = button.dataset.timelineMode === mode;
        button.classList.toggle("active", active);
        button.setAttribute("aria-pressed", active ? "true" : "false");
      }});
      document.querySelectorAll("[data-timeline-view]").forEach((view) => {{
        view.hidden = view.dataset.timelineView !== mode;
      }});
    }};
    document.querySelectorAll("[data-timeline-mode]").forEach((button) => {{
      button.addEventListener("click", () => {{
        setTimelineMode(button.dataset.timelineMode || "table");
        showToast(`运行时间线视图：${{button.textContent}}`);
      }});
    }});
    setTimelineMode("table");

    const reviewModal = document.getElementById("review-modal");
    const reviewStorageKey = "serenityManualReview.v1.cache";
    const reviewApiBacked = () => window.location.protocol !== "file:";
    const readReviewCache = () => {{
      try {{
        return JSON.parse(window.localStorage.getItem(reviewStorageKey) || "{{}}");
      }} catch {{
        return {{}};
      }}
    }};
    const writeReviewCache = (log) => {{
      try {{
        window.localStorage.setItem(reviewStorageKey, JSON.stringify(log));
      }} catch {{
        /* 静态入口缓存失败时不阻断页面主流程。 */
      }}
    }};
    const loadReviewLog = async () => {{
      if (!reviewApiBacked()) {{
        return readReviewCache();
      }}
      try {{
        const response = await fetch("/api/manual-review", {{ method: "GET" }});
        const data = await response.json();
        if (!response.ok || data.status !== "pass") {{
          throw new Error(data.message || "读取复核失败");
        }}
        const records = data.records || {{}};
        writeReviewCache(records);
        return records;
      }} catch {{
        return readReviewCache();
      }}
    }};
    const saveReviewRecord = async (record) => {{
      const key = String(record.review_id || "");
      if (!reviewApiBacked()) {{
        const cache = readReviewCache();
        cache[key] = {{ ...record, source: "local" }};
        writeReviewCache(cache);
        return cache[key];
      }}
      const response = await fetch("/api/manual-review", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify(record),
      }});
      const data = await response.json();
      if (!response.ok || data.status !== "pass") {{
        throw new Error(data.message || "保存复核失败");
      }}
      const saved = data.record || {{ ...record, source: "sqlite" }};
      const cache = readReviewCache();
      cache[key] = saved;
      writeReviewCache(cache);
      return saved;
    }};
    const clearReviewRecords = async () => {{
      if (!reviewApiBacked()) {{
        window.localStorage.removeItem(reviewStorageKey);
        return {{ status: "pass", source: "local" }};
      }}
      const response = await fetch("/api/manual-review", {{ method: "DELETE" }});
      const data = await response.json();
      if (!response.ok || data.status !== "pass") {{
        throw new Error(data.message || "清空复核失败");
      }}
      window.localStorage.removeItem(reviewStorageKey);
      return data;
    }};
    const formatReviewSavedAt = () => {{
      const parts = new Intl.DateTimeFormat("en-CA", {{
        timeZone: "Australia/Sydney",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
        timeZoneName: "short",
      }}).formatToParts(new Date());
      const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
      return `${{values.year}}${{values.month}}${{values.day}} - ${{values.hour}}:${{values.minute}} ${{values.timeZoneName || "Australia/Sydney"}}`;
    }};
    const reviewStateText = (record) => {{
      if (!record) return "未保存";
      const savedAt = record.savedAt || record.saved_at || "";
      return record.source === "sqlite" ? `已保存到数据库 ${{savedAt}}` : `已临时保存 ${{savedAt}}`;
    }};
    const applyReviewLog = async () => {{
      const log = await loadReviewLog();
      document.querySelectorAll("[data-review-item]").forEach((item) => {{
        const record = log[item.dataset.reviewId || ""];
        const decision = item.querySelector("[data-review-decision]");
        const note = item.querySelector("[data-review-note]");
        const state = item.querySelector("[data-review-state]");
        if (record) {{
          if (decision) decision.value = record.decision || decision.value;
          if (note) note.value = record.note || "";
          if (state) state.textContent = reviewStateText(record);
        }} else if (state) {{
          state.textContent = "未保存";
        }}
      }});
    }};
    const closeReview = () => {{
      if (reviewModal) reviewModal.hidden = true;
    }};
    document.querySelectorAll("[data-open-review]").forEach((button) => {{
      button.addEventListener("click", () => {{
        void applyReviewLog();
        if (reviewModal) reviewModal.hidden = false;
      }});
    }});
    document.querySelectorAll("[data-close-review]").forEach((button) => {{
      button.addEventListener("click", closeReview);
    }});
    document.querySelectorAll("[data-save-review]").forEach((button) => {{
      button.addEventListener("click", async () => {{
        const item = button.closest("[data-review-item]");
        if (!item) return;
        const decision = item.querySelector("[data-review-decision]");
        const note = item.querySelector("[data-review-note]");
        const state = item.querySelector("[data-review-state]");
        const savedAt = formatReviewSavedAt();
        const record = {{
          review_id: item.dataset.reviewId || "",
          run_id: item.dataset.reviewRunId || "",
          decision: decision ? decision.value : "保持禁止新增",
          note: note ? note.value : "",
          savedAt,
        }};
        try {{
          const saved = await saveReviewRecord(record);
          if (state) state.textContent = reviewStateText(saved);
          showToast(saved.source === "sqlite" ? "人工复核已保存到数据库" : "当前为静态入口，已临时保存到浏览器");
        }} catch (error) {{
          const cache = readReviewCache();
          cache[String(record.review_id || "")] = {{ ...record, source: "local" }};
          writeReviewCache(cache);
          if (state) state.textContent = reviewStateText(cache[String(record.review_id || "")]);
          const message = error && error.message ? error.message : "数据库保存失败";
          showToast(`${{message}}，已临时缓存到浏览器`);
        }}
      }});
    }});
    document.querySelectorAll("[data-copy-review-log]").forEach((button) => {{
      button.addEventListener("click", async () => {{
        const log = await loadReviewLog();
        const lines = Array.from(document.querySelectorAll("[data-review-item]")).map((item) => {{
          const id = item.dataset.reviewId || "";
          const title = item.querySelector(".review-item-head strong")?.textContent?.trim() || id;
          const reason = item.querySelector(".review-reason")?.textContent?.trim() || "-";
          const decision = item.querySelector("[data-review-decision]")?.value || log[id]?.decision || "保持禁止新增";
          const note = item.querySelector("[data-review-note]")?.value || log[id]?.note || "";
          return `#${{id}} ${{title}} | 决策:${{decision}} | 原因:${{reason}} | 备注:${{note || "-"}}`;
        }});
        const text = lines.join("\\n") || "无人工复核项";
        try {{
          await navigator.clipboard.writeText(text);
        }} catch {{
          const holder = document.createElement("textarea");
          holder.value = text;
          holder.setAttribute("readonly", "");
          holder.style.position = "fixed";
          holder.style.opacity = "0";
          document.body.appendChild(holder);
          holder.select();
          document.execCommand("copy");
          holder.remove();
        }}
        showToast("人工复核记录已复制");
      }});
    }});
    document.querySelectorAll("[data-clear-review-log]").forEach((button) => {{
      button.addEventListener("click", async () => {{
        try {{
          const result = await clearReviewRecords();
          document.querySelectorAll("[data-review-item]").forEach((item) => {{
            const note = item.querySelector("[data-review-note]");
            const state = item.querySelector("[data-review-state]");
            const decision = item.querySelector("[data-review-decision]");
            if (note) note.value = "";
            if (decision) decision.value = "保持禁止新增";
            if (state) state.textContent = "未保存";
          }});
          showToast(result.source === "local" ? "临时复核记录已清空" : "数据库复核记录已清空");
        }} catch (error) {{
          const message = error && error.message ? error.message : "清空复核失败";
          showToast(message);
        }}
      }});
    }});
    void applyReviewLog();

    const usageGuideModal = document.getElementById("usage-guide-modal");
    const openUsageGuide = () => {{
      if (usageGuideModal) usageGuideModal.hidden = false;
      showToast("已打开使用说明");
    }};
    const closeUsageGuide = () => {{
      if (usageGuideModal) usageGuideModal.hidden = true;
    }};
    document.querySelectorAll("[data-open-usage-guide]").forEach((button) => {{
      button.addEventListener("click", openUsageGuide);
    }});
    document.querySelectorAll("[data-close-usage-guide]").forEach((button) => {{
      button.addEventListener("click", closeUsageGuide);
    }});

    const modal = document.getElementById("fund-modal");
    const modalTitle = document.getElementById("fund-modal-title");
    const modalSubtitle = document.getElementById("fund-modal-subtitle");
    const modalBody = document.getElementById("fund-modal-body");
    const modalCloseButton = document.querySelector("[data-close-fund-button]");
    const fundLibraryModal = document.getElementById("fund-library-modal");
    const fundLibraryBody = document.getElementById("fund-library-body");
    const fundLibraryTableBody = document.getElementById("fund-library-table-body");
    let fundDetailOpenedFromLibrary = false;
    const fieldLabels = [
      ["首次进入策略 Top5", "firstTop5Time"],
      ["上次进入候选池时间", "lastTop5EntryTime"],
      ["当前进入候选池天数", "currentCandidateDays"],
      ["当前状态", "candidateStatus"],
      ["费用/状态快照时间", "ruleSnapshotTime"],
      ["申购状态", "subscriptionStatus"],
      ["赎回状态", "redemptionStatus"],
      ["交易截止时间", "cutoffTime"],
      ["确认周期", "confirmLag"],
      ["赎回到账", "redeemLag"],
      ["支付宝交易可用性", "alipayTradeStatus"],
      ["MooMoo交易可用性", "moomooTradeStatus"],
      ["平台交易备注", "platformTradeNote"],
      ["申购费（基础/最高）", "subscriptionFee"],
      ["申购费分档规则", "subscriptionFeeSchedule"],
      ["赎回费（基础/最高）", "redemptionFee"],
      ["赎回费分档规则", "redemptionFeeSchedule"],
      ["费率规则时间", "feeScheduleAsOf"],
      ["费率口径说明", "feeScheduleNote"],
      ["管理费（年）", "managementFee"],
      ["托管费（年）", "custodyFee"],
      ["销售服务费", "salesServiceFee"],
      ["合计运营费（年）", "operatingFee"],
      ["最低申购金额", "minPurchaseAmount"],
      ["来源名称", "sourceName"],
      ["来源类型", "sourceType"],
      ["来源优先级", "sourcePriority"],
      ["来源链接", "sourceUrl"]
    ];
    const fundLibrarySummaryLabels = [
      ["当前状态", "candidateStatus"],
      ["入池天数", "currentCandidateDays"],
      ["支付宝交易可用性", "alipayTradeStatus"],
      ["MooMoo交易可用性", "moomooTradeStatus"],
      ["申购状态", "subscriptionStatus"],
      ["赎回状态", "redemptionStatus"],
      ["申购费", "subscriptionFee"],
      ["赎回费", "redemptionFee"],
      ["管理费", "managementFee"],
      ["托管费", "custodyFee"],
      ["销售服务费", "salesServiceFee"],
      ["合计运营费", "operatingFee"]
    ];
    const setFundLibraryMode = (mode) => {{
      document.querySelectorAll("[data-fund-library-mode]").forEach((button) => {{
        const active = button.dataset.fundLibraryMode === mode;
        button.classList.toggle("active", active);
        button.setAttribute("aria-pressed", active ? "true" : "false");
      }});
      document.querySelectorAll("[data-fund-library-view]").forEach((view) => {{
        view.hidden = view.dataset.fundLibraryView !== mode;
      }});
    }};
    const openFundModal = (code, options = {{}}) => {{
      fundDetailOpenedFromLibrary = Boolean(options.fromLibrary);
      const info = fundLibrary[code];
      modalBody.innerHTML = "";
      if (!info) {{
        modalTitle.textContent = "基金信息";
        modalSubtitle.textContent = `${{code}} 暂无基金库详情`;
      }} else {{
        modalTitle.textContent = `${{info.name}}`;
        modalSubtitle.textContent = `${{info.code}} · 点击基金名可查看申购赎回、费率和来源证据`;
        fieldLabels.forEach(([label, key]) => {{
          const field = document.createElement("div");
          field.className = "fund-field";
          if (key.includes("Schedule") || key === "feeScheduleNote" || key === "platformTradeNote" || key === "sourceUrl") {{
            field.classList.add("wide");
          }}
          const labelNode = document.createElement("span");
          labelNode.textContent = label;
          const valueNode = document.createElement("strong");
          valueNode.textContent = String(info[key] ?? "-");
          if (valueNode.textContent.includes("未提供完整")) {{
            field.classList.add("warning");
          }}
          field.appendChild(labelNode);
          field.appendChild(valueNode);
          modalBody.appendChild(field);
        }});
      }}
      if (modalCloseButton) {{
        modalCloseButton.textContent = fundDetailOpenedFromLibrary ? "返回基金库" : "关闭";
      }}
      modal.hidden = false;
      showToast("已打开基金信息");
    }};
    const closeFundModal = () => {{
      modal.hidden = true;
      if (fundDetailOpenedFromLibrary && fundLibraryModal) {{
        fundLibraryModal.hidden = false;
        showToast("已返回基金库");
      }}
      fundDetailOpenedFromLibrary = false;
      if (modalCloseButton) modalCloseButton.textContent = "关闭";
    }};
    const renderFundLibrary = () => {{
      const funds = Object.values(fundLibrary).sort((a, b) => String(a.code).localeCompare(String(b.code)));
      fundLibraryBody.innerHTML = "";
      if (fundLibraryTableBody) fundLibraryTableBody.innerHTML = "";
      if (!funds.length) {{
        const empty = document.createElement("div");
        empty.className = "fund-library-empty";
        empty.textContent = "当前没有已入库基金信息。";
        fundLibraryBody.appendChild(empty);
        if (fundLibraryTableBody) {{
          const row = document.createElement("tr");
          const cell = document.createElement("td");
          cell.colSpan = fieldLabels.length + 3;
          cell.textContent = "当前没有已入库基金信息。";
          row.appendChild(cell);
          fundLibraryTableBody.appendChild(row);
        }}
        return;
      }}
      funds.forEach((info) => {{
        const card = document.createElement("article");
        card.className = "fund-library-card";

        const head = document.createElement("div");
        head.className = "fund-library-head";
        const title = document.createElement("div");
        const name = document.createElement("strong");
        name.textContent = info.name || info.code;
        const subtitle = document.createElement("span");
        subtitle.textContent = `${{info.code}} · ${{info.candidateStatus || "-"}} · 规则时间 ${{info.ruleSnapshotTime || info.feeScheduleAsOf || "-"}}`;
        title.appendChild(name);
        title.appendChild(subtitle);
        const detailButton = document.createElement("button");
        detailButton.type = "button";
        detailButton.textContent = "查看详情";
        detailButton.setAttribute("data-open-fund-detail", info.code || "");
        detailButton.addEventListener("click", () => {{
          openFundModal(info.code, {{ fromLibrary: true }});
        }});
        head.appendChild(title);
        head.appendChild(detailButton);
        card.appendChild(head);

        const meta = document.createElement("div");
        meta.className = "fund-library-meta";
        fundLibrarySummaryLabels.forEach(([label, key]) => {{
          const node = document.createElement("span");
          node.textContent = `${{label}}：${{info[key] ?? "-"}}`;
          meta.appendChild(node);
        }});
        card.appendChild(meta);

        const schedule = document.createElement("div");
        schedule.className = "fund-library-schedule";
        schedule.textContent = `申购费分档：${{info.subscriptionFeeSchedule || "-"}}\\n赎回费分档：${{info.redemptionFeeSchedule || "-"}}\\n支付宝交易：${{info.alipayTradeStatus || "-"}}\\nMooMoo交易：${{info.moomooTradeStatus || "-"}}\\n来源：${{info.sourceName || "-"}}`;
        card.appendChild(schedule);
        fundLibraryBody.appendChild(card);

        if (fundLibraryTableBody) {{
          const row = document.createElement("tr");
          const values = [
            info.code || "-",
            info.name || "-",
            ...fieldLabels.map(([, key]) => info[key] ?? "-")
          ];
          values.forEach((value) => {{
            const cell = document.createElement("td");
            cell.textContent = String(value);
            row.appendChild(cell);
          }});
          const actionCell = document.createElement("td");
          const tableDetailButton = document.createElement("button");
          tableDetailButton.type = "button";
          tableDetailButton.textContent = "详情";
          tableDetailButton.setAttribute("data-open-fund-detail", info.code || "");
          tableDetailButton.addEventListener("click", () => {{
            openFundModal(info.code, {{ fromLibrary: true }});
          }});
          actionCell.appendChild(tableDetailButton);
          row.appendChild(actionCell);
          fundLibraryTableBody.appendChild(row);
        }}
      }});
    }};
    const openFundLibrary = () => {{
      renderFundLibrary();
      setFundLibraryMode("gallery");
      if (fundLibraryModal) fundLibraryModal.hidden = false;
      showToast("已打开基金库");
    }};
    const closeFundLibrary = () => {{
      if (fundLibraryModal) fundLibraryModal.hidden = true;
    }};
    document.querySelectorAll("[data-open-fund-library]").forEach((button) => {{
      button.addEventListener("click", openFundLibrary);
    }});
    document.querySelectorAll("[data-close-fund-library]").forEach((button) => {{
      button.addEventListener("click", closeFundLibrary);
    }});
    document.querySelectorAll("[data-fund-library-mode]").forEach((button) => {{
      button.addEventListener("click", () => setFundLibraryMode(button.dataset.fundLibraryMode || "gallery"));
    }});
    document.querySelectorAll("[data-fund-code]").forEach((button) => {{
      button.addEventListener("click", () => openFundModal(button.dataset.fundCode, {{ fromLibrary: false }}));
    }});
    document.querySelectorAll("[data-close-fund]").forEach((button) => {{
      button.addEventListener("click", closeFundModal);
    }});
    document.addEventListener("keydown", (event) => {{
      if (event.key !== "Escape") return;
      if (!modal.hidden) {{
        closeFundModal();
        return;
      }}
      if (fundLibraryModal && !fundLibraryModal.hidden) {{
        closeFundLibrary();
        return;
      }}
      if (usageGuideModal && !usageGuideModal.hidden) closeUsageGuide();
    }});
  </script>
</body>
</html>
"""


def render_downloads_entry(portal_path: Path) -> str:
    portal_url = portal_path.resolve().as_uri()
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="1; url={_escape(portal_url)}">
  <title>打开 Serenity 每日分析</title>
  <style>
    :root {{
      --page: #f5f7f4;
      --surface: #ffffff;
      --ink: #132027;
      --muted: #64717b;
      --line: #d9e0da;
      --accent: #0b6f7b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      background: var(--page);
      color: var(--ink);
    }}
    main {{ max-width: 760px; margin: 0 auto; padding: 44px 20px; }}
    .panel {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 22px;
      box-shadow: 0 10px 28px rgba(20, 35, 30, 0.08);
    }}
    h1 {{ margin: 0; font-size: 28px; letter-spacing: 0; }}
    p {{ color: var(--muted); line-height: 1.55; }}
    a {{
      min-height: 38px;
      border: 1px solid var(--accent);
      border-radius: 8px;
      background: var(--accent);
      color: #fff;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      padding: 9px 12px;
      text-decoration: none;
    }}
    a:focus-visible {{
      outline: none;
      box-shadow: 0 0 0 3px rgba(11, 111, 123, 0.16);
    }}
  </style>
</head>
<body>
  <main>
    <section class="panel">
      <h1>Serenity 每日分析</h1>
      <p>正在打开本地应用首页。若没有自动跳转，请使用下方按钮。</p>
      <p><a href="{_escape(portal_url)}">打开本地应用</a></p>
    </section>
  </main>
</body>
</html>
"""


def _bundle_identifier(root_dir: Path) -> str:
    suffix = hashlib.sha1(str(root_dir.resolve()).encode("utf-8")).hexdigest()[:10]
    return f"local.serenity.daily-analysis.{suffix}"


def _write_app_bundle(app_path: Path, portal_path: Path, root_dir: Path) -> None:
    contents_dir = app_path / "Contents"
    macos_dir = contents_dir / "MacOS"
    macos_dir.mkdir(parents=True, exist_ok=True)
    bundle_identifier = _bundle_identifier(root_dir)
    (contents_dir / "Info.plist").write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>zh_CN</string>
  <key>CFBundleExecutable</key>
  <string>open-serenity</string>
  <key>CFBundleIconFile</key>
  <string>SerenityIcon</string>
  <key>CFBundleIdentifier</key>
  <string>{bundle_identifier}</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>Serenity 每日分析</string>
  <key>CFBundleDisplayName</key>
  <string>Serenity 每日分析</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>1.0</string>
  <key>CFBundleVersion</key>
  <string>1</string>
  <key>LSMinimumSystemVersion</key>
  <string>10.13</string>
</dict>
</plist>
""",
        encoding="utf-8",
    )
    (contents_dir / "PkgInfo").write_text("APPL????", encoding="ascii")
    _write_app_icon(contents_dir, app_path.parent)
    portal_target = str(portal_path.resolve()).replace('"', '\\"')
    root_target = str(root_dir.resolve()).replace('"', '\\"')
    python_target = sys.executable.replace('"', '\\"')
    executable = macos_dir / "open-serenity"
    executable.write_text(
        f"""#!/bin/sh
ROOT="{root_target}"
PYTHON="{python_target}"
PORT="${{SERENITY_APP_PORT:-8765}}"
URL="http://127.0.0.1:$PORT/"
HEALTH="http://127.0.0.1:$PORT/api/health"
LOG_DIR="$HOME/Library/Logs/SerenityDailyAnalysis"
LOG_FILE="$LOG_DIR/application-server.log"
mkdir -p "$LOG_DIR"
cd "$ROOT" || exit 1
if ! /usr/bin/curl -fsS "$HEALTH" >/dev/null 2>&1; then
  "$PYTHON" -m app.cli application-server --host 127.0.0.1 --port "$PORT" >> "$LOG_FILE" 2>&1 &
  for _ in 1 2 3 4 5; do
    /usr/bin/curl -fsS "$HEALTH" >/dev/null 2>&1 && break
    sleep 0.4
  done
fi
if /usr/bin/curl -fsS "$HEALTH" >/dev/null 2>&1; then
  open "$URL"
else
  open "{portal_target}"
fi
""",
        encoding="utf-8",
    )
    executable.chmod(0o755)


def _install_app_bundle(source_app: Path, destination_app: Path) -> None:
    destination_app.parent.mkdir(parents=True, exist_ok=True)
    if destination_app.exists():
        shutil.rmtree(destination_app)
    shutil.copytree(source_app, destination_app)
    executable = destination_app / "Contents" / "MacOS" / "open-serenity"
    if executable.exists():
        executable.chmod(0o755)
    os.utime(destination_app, None)
    os.utime(destination_app / "Contents", None)
    _register_app_bundle(destination_app)


def _register_app_bundle(app_path: Path) -> bool:
    lsregister = Path("/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister")
    if not lsregister.exists():
        return False
    result = subprocess.run(
        [str(lsregister), "-f", str(app_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _cleanup_legacy_downloads_entries(root_dir: Path) -> list[str]:
    marker = (root_dir / "outputs" / "application" / "index.html").as_posix()
    legacy_root = Path.home() / "Downloads" / "application"
    removed: list[str] = []

    legacy_app = legacy_root / APP_BUNDLE_NAME
    legacy_executable = legacy_app / "Contents" / "MacOS" / "open-serenity"
    if legacy_executable.exists() and marker in legacy_executable.read_text(encoding="utf-8", errors="ignore"):
        shutil.rmtree(legacy_app)
        removed.append(str(legacy_app))

    legacy_html_dir = legacy_root / "serenity-daily-analysis"
    legacy_html = legacy_html_dir / "index.html"
    if legacy_html.exists() and marker in legacy_html.read_text(encoding="utf-8", errors="ignore"):
        shutil.rmtree(legacy_html_dir)
        removed.append(str(legacy_html_dir))

    legacy_flat_html = legacy_root / "Serenity Daily Analysis.html"
    if legacy_flat_html.exists() and marker in legacy_flat_html.read_text(encoding="utf-8", errors="ignore"):
        legacy_flat_html.unlink()
        removed.append(str(legacy_flat_html))

    return removed


def _mix_color(start: tuple[int, int, int], end: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return tuple(round(start[i] + (end[i] - start[i]) * t) for i in range(3))


def _scaled_box(values: tuple[float, float, float, float], scale: float) -> tuple[int, int, int, int]:
    return tuple(round(value * scale) for value in values)


def _render_serenity_icon(size: int = 1024):
    try:
        from PIL import Image, ImageDraw, ImageFilter
    except ImportError as exc:  # pragma: no cover - local macOS build dependency
        raise RuntimeError("Pillow is required to render the Serenity app icon.") from exc

    scale = size / 1024.0
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    corner = round(208 * scale)
    outer = _scaled_box((56, 56, 968, 968), scale)
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        _scaled_box((72, 82, 952, 978), scale),
        radius=corner,
        fill=(24, 44, 45, 70),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(round(22 * scale)))
    canvas.alpha_composite(shadow)

    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(outer, radius=corner, fill=255)

    top = (248, 251, 247)
    mid = (232, 244, 255)
    bottom = (230, 245, 238)
    gradient = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    grad_px = gradient.load()
    for y in range(size):
        vertical = y / max(size - 1, 1)
        for x in range(size):
            diagonal = (x + y) / max((size - 1) * 2, 1)
            base = _mix_color(top, mid, vertical)
            color = _mix_color(base, bottom, diagonal * 0.62)
            grad_px[x, y] = (*color, 255)
    canvas.paste(gradient, (0, 0), mask)

    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for x in range(150, 910, 126):
        sx = round(x * scale)
        draw.line([(sx, round(140 * scale)), (sx, round(880 * scale))], fill=(52, 92, 92, 28), width=max(1, round(2 * scale)))
    for y in range(190, 850, 118):
        sy = round(y * scale)
        draw.line([(round(130 * scale), sy), (round(900 * scale), sy)], fill=(52, 92, 92, 24), width=max(1, round(2 * scale)))
    chart = [
        (174, 676),
        (274, 604),
        (362, 632),
        (474, 498),
        (584, 542),
        (712, 364),
        (846, 308),
    ]
    chart_points = [(round(x * scale), round(y * scale)) for x, y in chart]
    draw.line(chart_points, fill=(11, 111, 123, 52), width=round(8 * scale), joint="curve")
    for x, y in chart_points:
        r = round(9 * scale)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 210), outline=(11, 111, 123, 90), width=max(1, round(2 * scale)))
    clipped = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    clipped.paste(layer, (0, 0), mask)
    canvas.alpha_composite(clipped)

    ribbon_shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ribbon_shadow_draw = ImageDraw.Draw(ribbon_shadow)
    points: list[tuple[int, int]] = []
    for index in range(190):
        t = index / 189
        x = 512 + 186 * math.sin((t - 0.035) * math.tau)
        y = 218 + 588 * t
        points.append((round(x * scale), round(y * scale)))
    shadow_points = [(x + round(12 * scale), y + round(16 * scale)) for x, y in points]
    ribbon_shadow_draw.line(shadow_points, fill=(18, 45, 48, 52), width=round(108 * scale), joint="curve")
    for x, y in (shadow_points[0], shadow_points[-1]):
        r = round(54 * scale)
        ribbon_shadow_draw.ellipse((x - r, y - r, x + r, y + r), fill=(18, 45, 48, 52))
    ribbon_shadow = ribbon_shadow.filter(ImageFilter.GaussianBlur(round(8 * scale)))
    canvas.alpha_composite(ribbon_shadow)

    ribbon_colors = [(193, 59, 59), (11, 111, 123), (31, 110, 168)]
    ribbon_mask = Image.new("L", (size, size), 0)
    ribbon_mask_draw = ImageDraw.Draw(ribbon_mask)
    ribbon_mask_draw.line(points, fill=255, width=round(92 * scale), joint="curve")
    for point in (points[0], points[-1]):
        x, y = point
        r = round(46 * scale)
        ribbon_mask_draw.ellipse((x - r, y - r, x + r, y + r), fill=255)
    ribbon_gradient = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ribbon_px = ribbon_gradient.load()
    for y in range(size):
        vertical = y / max(size - 1, 1)
        for x in range(size):
            diagonal = (x / max(size - 1, 1)) * 0.16
            t = max(0.0, min(1.0, vertical + diagonal - 0.06))
            if t < 0.5:
                color = _mix_color(ribbon_colors[0], ribbon_colors[1], t / 0.5)
            else:
                color = _mix_color(ribbon_colors[1], ribbon_colors[2], (t - 0.5) / 0.5)
            ribbon_px[x, y] = (*color, 255)
    ribbon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ribbon.paste(ribbon_gradient, (0, 0), ribbon_mask)
    ribbon_draw = ImageDraw.Draw(ribbon)
    highlight = [(x - round(18 * scale), y - round(22 * scale)) for x, y in points[18:158]]
    ribbon_draw.line(highlight, fill=(255, 255, 255, 90), width=round(22 * scale), joint="curve")
    canvas.alpha_composite(ribbon)

    bars = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bars_draw = ImageDraw.Draw(bars)
    bar_specs = [
        (650, 742, 104, (193, 59, 59)),
        (698, 704, 142, (211, 152, 55)),
        (746, 656, 190, (11, 111, 123)),
        (794, 616, 230, (31, 122, 77)),
        (842, 676, 170, (31, 110, 168)),
    ]
    for x, bottom_y, height, color in bar_specs:
        width = round(22 * scale)
        x1 = round(x * scale)
        y1 = round((bottom_y - height) * scale)
        y2 = round(bottom_y * scale)
        bars_draw.line([(x1, y2), (x1, y1)], fill=(*color, 230), width=width)
        r = width // 2
        bars_draw.ellipse((x1 - r, y1 - r, x1 + r, y1 + r), fill=(*color, 230))
        bars_draw.ellipse((x1 - r, y2 - r, x1 + r, y2 + r), fill=(*color, 230))
    canvas.alpha_composite(bars)

    border = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border)
    border_draw.rounded_rectangle(outer, radius=corner, outline=(11, 111, 123, 80), width=round(4 * scale))
    inner = _scaled_box((78, 78, 946, 946), scale)
    border_draw.rounded_rectangle(inner, radius=round(184 * scale), outline=(255, 255, 255, 118), width=round(3 * scale))
    canvas.alpha_composite(border)

    return canvas


def _write_app_icon(contents_dir: Path, output_dir: Path) -> None:
    from PIL import Image

    resources_dir = contents_dir / "Resources"
    resources_dir.mkdir(parents=True, exist_ok=True)
    preview_path = output_dir / "serenity-app-icon.png"
    iconset_dir = output_dir / f"{APP_ICON_BASENAME}.iconset"
    if iconset_dir.exists():
        shutil.rmtree(iconset_dir)
    iconset_dir.mkdir(parents=True)

    preview_path.parent.mkdir(parents=True, exist_ok=True)
    if preview_path.exists():
        source = Image.open(preview_path).convert("RGBA").resize((1024, 1024), Image.Resampling.LANCZOS)
    else:
        source = _render_serenity_icon(1024)
    source.save(preview_path)
    icon_sizes = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
    }
    for filename, icon_size in icon_sizes.items():
        source.resize((icon_size, icon_size), Image.Resampling.LANCZOS).save(iconset_dir / filename)

    icns_path = resources_dir / f"{APP_ICON_BASENAME}.icns"
    subprocess.run(
        ["/usr/bin/iconutil", "-c", "icns", "-o", str(icns_path), str(iconset_dir)],
        check=True,
        capture_output=True,
        text=True,
    )


def build_application_portal(settings: Settings) -> dict[str, object]:
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        runs = _latest_runs(conn, limit=12)
        current_run = runs[0] if runs else None
        previous_run = runs[1] if len(runs) > 1 else None
        current_holdings = _holdings_for_run(conn, current_run.run_id) if current_run else []
        previous_holdings = _holdings_for_run(conn, previous_run.run_id) if previous_run else []
        run_timeline = _run_timeline_events(conn, runs)
        manual_review_items = _manual_review_items(conn, current_run.run_id if current_run else None)
        baseline_time_bj = _baseline_reference_time(conn, current_run.run_id if current_run else None)
        fund_library = _fund_library_for_run(
            conn,
            current_run.run_id if current_run else None,
            current_holdings + previous_holdings,
        )

    output_dir = settings.root_dir / "outputs" / "application"
    output_dir.mkdir(parents=True, exist_ok=True)
    portal_path = output_dir / "index.html"
    downloads_entry_path = output_dir / "downloads-entry.html"
    app_bundle_path = output_dir / APP_BUNDLE_NAME
    downloads_app_path = Path.home() / "Downloads" / APP_BUNDLE_NAME
    applications_app_path = Path("/Applications") / APP_BUNDLE_NAME
    portal_path.write_text(
        render_application_portal(
            current_run,
            current_holdings,
            previous_run,
            previous_holdings,
            baseline_time_bj=baseline_time_bj,
            fund_library=fund_library,
            run_timeline=run_timeline,
            manual_review_items=manual_review_items,
        ),
        encoding="utf-8",
    )
    downloads_entry_path.write_text(render_downloads_entry(portal_path), encoding="utf-8")
    _write_app_bundle(app_bundle_path, portal_path, settings.root_dir)
    _install_app_bundle(app_bundle_path, downloads_app_path)
    _install_app_bundle(app_bundle_path, applications_app_path)
    legacy_removed = _cleanup_legacy_downloads_entries(settings.root_dir)
    return {
        "status": "pass",
        "portal_path": str(portal_path),
        "downloads_entry_path": str(downloads_entry_path),
        "app_bundle_path": str(app_bundle_path),
        "downloads_app_path": str(downloads_app_path),
        "applications_app_path": str(applications_app_path),
        "legacy_removed": legacy_removed,
        "current_run_id": current_run.run_id if current_run else None,
        "previous_run_id": previous_run.run_id if previous_run else None,
        "current_rows": len(current_holdings),
        "previous_rows": len(previous_holdings),
        "timeline_rows": len(run_timeline),
        "manual_review_rows": len(manual_review_items),
        "fund_library_rows": len(fund_library),
    }
