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
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from app.adapters.manual_sources import Candidate, PricePoint, load_candidates, load_price_history
from app.config import Settings
from app.core.run_visibility import display_run_time_with_backfill_note, is_future_controlled_backfill
from app.core.time_display import format_display_time, parse_datetime
from app.db import connect, init_db


APP_BUNDLE_NAME = "Serenity 每日分析.app"
APP_ICON_BASENAME = "SerenityIcon"
RELATIVE_ACTION_THRESHOLD = 0.01
TRADING_DAYS_PER_YEAR = 252


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
class PortalActionSummary:
    level: str
    count: str
    boundary: str
    detail: str
    tone: str


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
    analysis_rank: int | None = None
    analysis_grade: str | None = None
    analysis_score: float | None = None


@dataclass(frozen=True)
class PortalPoolMetric:
    rank: int
    pool_label: str
    pool_class: str
    code: str
    name: str
    grade: str
    score: float
    target_weight: float
    action_label: str
    trigger_reason: str
    review_text: str
    entry_time_bj: str | None
    metric_data_date: str | None
    since_entry_return: float | None
    return_1m: float | None
    return_3m: float | None
    return_6m: float | None
    benchmark_label: str
    alpha: float | None
    beta: float | None
    gamma: float | None
    theta: float | None
    vega: float | None
    sharpe: float | None
    sortino: float | None
    calmar: float | None
    treynor: float | None


@dataclass(frozen=True)
class PortalExpansionCandidate:
    sequence: int
    code: str
    name: str
    fund_type: str
    theme_score: int
    matched_keywords: tuple[str, ...]
    nav_status: str
    rule_status: str
    current_status: str
    note: str
    source_url: str | None = None


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


def _ratio(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}"


def _benchmark_display_label(value: str | None) -> str:
    text = str(value or "-").strip()
    return text.removeprefix("主题基准：") or "-"


def _pct_pair_from_annualized(value: float | None) -> tuple[str, str]:
    if value is None:
        return "-", "-"
    daily = value / TRADING_DAYS_PER_YEAR
    weekly = daily * 5
    return _pct(daily), _pct(weekly)


def _pct_pair_from_daily(value: float | None) -> tuple[str, str]:
    if value is None:
        return "-", "-"
    return _pct(value), _pct(value * 5)


def _ratio_pair_same(value: float | None) -> tuple[str, str]:
    text = _ratio(value)
    return text, text


def _metric_pair_line(label: str, left_label: str, left: str, right_label: str, right: str) -> str:
    return (
        '<span class="metric-pair-line">'
        f"<strong>{_escape(label)}</strong>"
        f"<em>{_escape(left_label)} {left}</em>"
        f"<em>{_escape(right_label)} {right}</em>"
        "</span>"
    )


def _greek_metric_cell(row: PortalPoolMetric) -> str:
    alpha_daily, alpha_weekly = _pct_pair_from_annualized(row.alpha)
    theta_daily, theta_weekly = _pct_pair_from_daily(row.theta)
    gamma_daily, gamma_weekly = _ratio(row.gamma), _ratio(row.gamma * 5 if row.gamma is not None else None)
    beta_daily, beta_weekly = _ratio_pair_same(row.beta)
    vega_daily, vega_weekly = _ratio_pair_same(row.vega)
    return (
        '<div class="metric-pair-stack">'
        + _metric_pair_line("Alpha", "日均", alpha_daily, "周均", alpha_weekly)
        + _metric_pair_line("Beta", "日频", beta_daily, "周频", beta_weekly)
        + _metric_pair_line("Gamma", "日均", gamma_daily, "周均", gamma_weekly)
        + _metric_pair_line("Theta", "日均", theta_daily, "周均", theta_weekly)
        + _metric_pair_line("Vega", "日频", vega_daily, "周频", vega_weekly)
        + "</div>"
    )


def _risk_metric_cell(row: PortalPoolMetric) -> str:
    sharpe_daily, sharpe_weekly = _ratio_pair_same(row.sharpe)
    sortino_daily, sortino_weekly = _ratio_pair_same(row.sortino)
    calmar_daily, calmar_weekly = _ratio_pair_same(row.calmar)
    treynor_daily, treynor_weekly = _pct_pair_from_annualized(row.treynor)
    return (
        '<div class="metric-pair-stack">'
        + _metric_pair_line("Sharpe", "日频", sharpe_daily, "周频", sharpe_weekly)
        + _metric_pair_line("Sortino", "日频", sortino_daily, "周频", sortino_weekly)
        + _metric_pair_line("Calmar", "日频", calmar_daily, "周频", calmar_weekly)
        + _metric_pair_line("Treynor", "日均", treynor_daily, "周均", treynor_weekly)
        + "</div>"
    )


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
        ORDER BY run_time_bj DESC, created_at DESC, rowid DESC
        LIMIT ?
        """,
        (fetch_limit,),
    ).fetchall()
    visible_rows = [
        row for row in rows if not is_future_controlled_backfill(row["run_time_bj"], row["created_at"])
    ]
    rows = _dedupe_runs_by_display_time(visible_rows or rows)[:limit]
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


def _recommendations_for_run(conn, run_id: str, min_rank: int = 1, max_rank: int = 5) -> list[PortalHolding]:
    rows = conn.execute(
        """
        SELECT r.rank, a.asset_code, a.asset_name, s.grade, s.total_score,
               r.target_weight, r.current_weight, r.action_label, r.trigger_reason
        FROM recommendation_snapshot r
        JOIN asset_master a ON a.asset_id=r.asset_id
        JOIN score_snapshot s ON s.run_id=r.run_id AND s.asset_id=r.asset_id
        WHERE r.run_id=?
          AND r.rank BETWEEN ? AND ?
        ORDER BY r.rank ASC
        """,
        (run_id, min_rank, max_rank),
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


def _holdings_for_run(conn, run_id: str) -> list[PortalHolding]:
    return _recommendations_for_run(conn, run_id, 1, 5)


def _audit_context_for_run(conn, run_id: str | None, event_type: str) -> dict[str, object]:
    if not run_id:
        return {}
    row = conn.execute(
        """
        SELECT context_json
        FROM audit_log
        WHERE run_id=? AND event_type=?
        ORDER BY id DESC
        LIMIT 1
        """,
        (run_id, event_type),
    ).fetchone()
    if not row or not row["context_json"]:
        return {}
    try:
        payload = json.loads(row["context_json"])
    except (TypeError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _expansion_candidates_for_run(conn, run_id: str | None) -> list[PortalExpansionCandidate]:
    expansion = _audit_context_for_run(conn, run_id, "candidate_universe_expansion")
    raw_additions = expansion.get("additions")
    if not isinstance(raw_additions, list):
        return []

    price_history = expansion.get("price_history_expansion")
    nav_backfilled_codes = set()
    if isinstance(price_history, dict):
        nav_backfilled_codes = {str(code) for code in price_history.get("nav_backfilled_codes") or []}

    rule_context = _audit_context_for_run(conn, run_id, "fund_rule_autofill")
    rule_rows = rule_context.get("rows") if isinstance(rule_context, dict) else []
    rule_by_code: dict[str, dict[str, object]] = {}
    if isinstance(rule_rows, list):
        for row in rule_rows:
            if isinstance(row, dict) and row.get("asset_code"):
                rule_by_code[str(row["asset_code"])] = row

    ranked_rows = conn.execute(
        """
        SELECT a.asset_code, r.rank
        FROM recommendation_snapshot r
        JOIN asset_master a ON a.asset_id=r.asset_id
        WHERE r.run_id=?
        """,
        (run_id,),
    ).fetchall() if run_id else []
    ranked_by_code = {str(row["asset_code"]): int(row["rank"] or 0) for row in ranked_rows}

    candidates: list[PortalExpansionCandidate] = []
    for index, item in enumerate(raw_additions, start=1):
        if not isinstance(item, dict):
            continue
        code = str(item.get("code") or "").strip()
        name = str(item.get("name") or "").strip()
        if not code or not name:
            continue
        matched_keywords = tuple(str(value) for value in item.get("matched_keywords") or [] if value)
        rule_row = rule_by_code.get(code, {})
        rule_status = str(rule_row.get("message") or rule_row.get("status") or "规则待补齐")
        rank = ranked_by_code.get(code)
        if rank:
            current_status = f"已进入当前排序 #{rank}"
            note = "已进入持仓池/观察池排序，按 Serenity 当前权重规则处理。"
        else:
            current_status = "扩容观察"
            note = "已被全市场扩容发现并补齐公开数据；尚未超过当前 Top5/观察池，后续刷新继续参与排序。"
        candidates.append(
            PortalExpansionCandidate(
                sequence=index,
                code=code,
                name=name,
                fund_type=str(item.get("fund_type") or "-"),
                theme_score=int(item.get("theme_score") or 0),
                matched_keywords=matched_keywords,
                nav_status="24个月净值已补齐" if code in nav_backfilled_codes else "净值历史待补齐/沿用",
                rule_status=rule_status,
                current_status=current_status,
                note=note,
                source_url=str(rule_row.get("source_url") or "") or None,
            )
        )
    return candidates


def _manual_review_decision_rows(conn) -> list:
    return conn.execute(
        """
        SELECT COALESCE(q.asset_id, '') AS asset_id,
               COALESCE(a.asset_code, '') AS asset_code,
               COALESCE(q.reason, '') AS reason,
               COALESCE(d.outcome, '') AS outcome,
               COALESCE(d.refresh_status, '') AS refresh_status,
               d.updated_at
        FROM manual_review_decision d
        LEFT JOIN manual_review_queue q ON q.id=d.review_id
        LEFT JOIN asset_master a ON a.asset_id=q.asset_id
        WHERE COALESCE(q.reason, '') <> ''
        ORDER BY d.updated_at DESC
        """
    ).fetchall()


def _decision_is_successful(decision) -> bool:
    refresh_status = str(decision["refresh_status"] or "")
    return not refresh_status or refresh_status == "pass"


def _decision_suppresses_created_at(decision, created_at: str | None) -> bool:
    if not _decision_is_successful(decision):
        return False
    outcome = str(decision["outcome"] or "")
    if outcome == "exclude_current_observation":
        decided_at = parse_datetime(str(decision["updated_at"] or ""))
        queue_created_at = parse_datetime(str(created_at or ""))
        if not decided_at or not queue_created_at:
            return True
        return queue_created_at <= decided_at + timedelta(days=14)
    return outcome in {"observe_pool", "promote_top5_candidate_pool"}


def _manual_review_row_is_resolved(row, decisions: list) -> bool:
    asset_id = str(row["asset_id"] or "")
    reason = str(row["reason"] or "")
    return any(
        str(decision["asset_id"] or "") == asset_id
        and str(decision["reason"] or "") == reason
        and _decision_suppresses_created_at(decision, str(row["created_at"] or ""))
        for decision in decisions
    )


def _resolved_review_code_reason_keys(conn) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    now = datetime.now().astimezone()
    for decision in _manual_review_decision_rows(conn):
        if not _decision_is_successful(decision):
            continue
        code = str(decision["asset_code"] or "")
        reason = str(decision["reason"] or "")
        if not code or not reason:
            continue
        outcome = str(decision["outcome"] or "")
        if outcome == "exclude_current_observation":
            decided_at = parse_datetime(str(decision["updated_at"] or ""))
            if decided_at and now > decided_at.astimezone(now.tzinfo) + timedelta(days=14):
                continue
        elif outcome not in {"observe_pool", "promote_top5_candidate_pool"}:
            continue
        keys.add((code, reason))
    return keys


def _manual_review_items(conn, run_id: str | None, limit: int = 12) -> list[PortalManualReviewItem]:
    def fetch_rows(where_sql: str, params_sql: list[object], query_limit: int):
        return conn.execute(
            f"""
            SELECT m.id, m.run_id, m.asset_id, COALESCE(a.asset_code, '-') AS asset_code,
                   COALESCE(a.asset_name, '未指定标的') AS asset_name,
                   m.reason, m.action_blocked, m.status, m.created_at,
                   r.rank AS analysis_rank, s.grade AS analysis_grade, s.total_score AS analysis_score
            FROM manual_review_queue m
            LEFT JOIN asset_master a ON a.asset_id=m.asset_id
            LEFT JOIN recommendation_snapshot r ON r.run_id=m.run_id AND r.asset_id=m.asset_id
            LEFT JOIN score_snapshot s ON s.run_id=m.run_id AND s.asset_id=m.asset_id
            WHERE {where_sql}
            ORDER BY {order}
            LIMIT ?
            """,
            tuple(params_sql + [query_limit]),
        ).fetchall()

    def unresolved(rows):
        decisions = _manual_review_decision_rows(conn)
        return [row for row in rows if not _manual_review_row_is_resolved(row, decisions)]

    params: list[object] = []
    where = "m.status='open'"
    order = "COALESCE(r.rank, 999), m.created_at DESC, m.id DESC"
    if run_id:
        where = "m.run_id=? AND m.status='open'"
        params.append(run_id)
    query_limit = max(limit * 5, limit)
    rows = fetch_rows(where, params, query_limit)
    filtered_rows = unresolved(rows)
    if rows and not filtered_rows:
        rows = []
    elif filtered_rows:
        rows = filtered_rows[:limit]
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
            analysis_rank=int(row["analysis_rank"]) if row["analysis_rank"] is not None else None,
            analysis_grade=row["analysis_grade"],
            analysis_score=float(row["analysis_score"]) if row["analysis_score"] is not None else None,
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
        WHERE r.rank BETWEEN 1 AND 10
          AND a.asset_code IN ({placeholders})
        """,
        tuple(asset_codes),
    ).fetchall()
    entry_rows = conn.execute(
        f"""
        SELECT a.asset_code, e.pool_kind, e.first_run_time_bj
        FROM asset_pool_entry e
        JOIN asset_master a ON a.asset_id=e.asset_id
        WHERE e.pool_kind IN ('candidate_pool', 'holding_pool')
          AND a.asset_code IN ({placeholders})
        """,
        tuple(asset_codes),
    ).fetchall()
    immutable_entries: dict[str, dict[str, str]] = {}
    for row in entry_rows:
        immutable_entries.setdefault(str(row["asset_code"]), {})[str(row["pool_kind"])] = str(row["first_run_time_bj"])
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
            "first_top5_time_bj": immutable_entries.get(code, {}).get("holding_pool") or first_seen,
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


def _point_index_on_or_before(points: list[PricePoint], target_date: date) -> int | None:
    candidates = [idx for idx, point in enumerate(points) if point.date <= target_date]
    return max(candidates) if candidates else None


def _return_from_index(points: list[PricePoint], start_index: int | None) -> float | None:
    if start_index is None or not points or start_index >= len(points):
        return None
    if start_index >= len(points) - 1:
        return None
    start = points[start_index].close
    end = points[-1].close
    if start == 0:
        return None
    return end / start - 1.0


def _return_since_date(points: list[PricePoint], start_date: date | None) -> float | None:
    if start_date is None:
        return None
    return _return_from_index(points, _point_index_on_or_before(points, start_date))


def _return_over_days(points: list[PricePoint], days: int) -> float | None:
    if not points:
        return None
    return _return_since_date(points, points[-1].date - timedelta(days=days))


def _daily_returns_by_date(points: list[PricePoint]) -> dict[date, float]:
    returns: dict[date, float] = {}
    for previous, current in zip(points, points[1:]):
        if previous.close:
            returns[current.date] = current.close / previous.close - 1.0
    return returns


def _composite_benchmark_returns(benchmark_history: dict[str, list[PricePoint]]) -> dict[date, float]:
    daily_maps = [
        _daily_returns_by_date(points)
        for code, points in benchmark_history.items()
        if code in {"000001.SH", "SPX"} and len(points) >= 2
    ]
    if not daily_maps:
        return {}
    dates = sorted({day for daily_map in daily_maps for day in daily_map})
    composite: dict[date, float] = {}
    for day in dates:
        values = [daily_map[day] for daily_map in daily_maps if day in daily_map]
        if values:
            composite[day] = sum(values) / len(values)
    return composite


def _benchmark_returns_by_code(benchmark_history: dict[str, list[PricePoint]]) -> dict[str, dict[date, float]]:
    return {
        code: _daily_returns_by_date(points)
        for code, points in benchmark_history.items()
        if len(points) >= 2
    }


def _candidate_theme_text(row: PortalHolding, candidate: Candidate | None) -> str:
    fields = [
        row.code,
        row.name,
        candidate.market if candidate else "",
        candidate.theme if candidate else "",
        candidate.asset_type if candidate else "",
    ]
    return " ".join(str(field or "") for field in fields).lower()


def _select_theme_benchmark(
    row: PortalHolding,
    candidate: Candidate | None,
    benchmark_returns: dict[str, dict[date, float]],
) -> tuple[str, dict[date, float]]:
    text = _candidate_theme_text(row, candidate)
    theme_rows: list[tuple[str, str]]
    if any(marker in text for marker in ("恒生", "港股", "hk", "互联网科技")):
        theme_rows = [
            ("HSIII", "恒生互联网科技业"),
            ("HSTECH", "恒生科技"),
            ("HSTECH_PROXY", "恒生科技ETF代理"),
        ]
    elif any(marker in text for marker in ("纳斯达克", "nasdaq", "美股", "us")):
        theme_rows = [
            ("NDX", "纳指100"),
        ]
    elif any(marker in text for marker in ("创业板", "chinext")):
        theme_rows = [
            ("399006.SZ", "创业板指"),
        ]
    elif any(marker in text for marker in ("人工智能", "ai", "算力", "光模块")):
        theme_rows = [
            ("CSI_AI", "中证人工智能"),
            ("930713.CSI", "中证人工智能"),
        ]
    elif any(marker in text for marker in ("半导体", "芯片", "semiconductor")):
        preferred_rows = (
            [("CNI_CHIP", "国证芯片")] if row.code == "008887" or "国证" in text else []
        )
        theme_rows = preferred_rows + [
            ("H30184.CSI", "中证全指半导体"),
            ("931865.CSI", "中证半导"),
            ("CNI_CHIP", "国证芯片"),
        ]
    else:
        theme_rows = []

    for code, label in theme_rows:
        returns = benchmark_returns.get(code)
        if returns:
            return f"主题基准：{label}", returns
    return "主题基准：待补齐", {}


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _sample_std(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    avg = sum(values) / len(values)
    variance = sum((value - avg) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def _covariance(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    left_avg = sum(left) / len(left)
    right_avg = sum(right) / len(right)
    return sum((l - left_avg) * (r - right_avg) for l, r in zip(left, right)) / (len(left) - 1)


def _annualized_mean_return(daily_returns: list[float]) -> float | None:
    avg = _mean(daily_returns)
    return None if avg is None else avg * TRADING_DAYS_PER_YEAR


def _beta(asset_returns: list[float], benchmark_returns: list[float]) -> float | None:
    variance = _sample_std(benchmark_returns)
    if variance is None or variance == 0:
        return None
    cov = _covariance(asset_returns, benchmark_returns)
    return None if cov is None else cov / (variance**2)


def _sharpe(asset_returns: list[float]) -> float | None:
    avg = _mean(asset_returns)
    std = _sample_std(asset_returns)
    if avg is None or std is None or std == 0:
        return None
    return avg / std * math.sqrt(TRADING_DAYS_PER_YEAR)


def _sortino(asset_returns: list[float]) -> float | None:
    avg = _mean(asset_returns)
    downside = [value for value in asset_returns if value < 0]
    downside_std = _sample_std(downside)
    if avg is None or downside_std is None or downside_std == 0:
        return None
    return avg / downside_std * math.sqrt(TRADING_DAYS_PER_YEAR)


def _entry_times_for_pool_rows(conn, rows: list[PortalHolding]) -> dict[tuple[str, str], str]:
    if not rows:
        return {}
    codes = sorted({row.code for row in rows})
    placeholders = ",".join("?" for _ in codes)
    entry_rows = conn.execute(
        f"""
        SELECT a.asset_code, e.pool_kind, e.first_run_time_bj
        FROM asset_pool_entry e
        JOIN asset_master a ON a.asset_id=e.asset_id
        WHERE a.asset_code IN ({placeholders})
          AND e.pool_kind IN ('holding_pool', 'observation_pool')
        """,
        tuple(codes),
    ).fetchall()
    return {
        (str(row["asset_code"]), str(row["pool_kind"])): str(row["first_run_time_bj"])
        for row in entry_rows
    }


def _latest_indicator_rows(conn, run_id: str | None, rows: list[PortalHolding]) -> dict[str, object]:
    if not run_id or not rows:
        return {}
    codes = sorted({row.code for row in rows})
    placeholders = ",".join("?" for _ in codes)
    indicator_rows = conn.execute(
        f"""
        SELECT a.asset_code, i.*
        FROM asset_indicator_snapshot i
        JOIN asset_master a ON a.asset_id=i.asset_id
        JOIN (
          SELECT asset_id, MAX(metric_date) AS metric_date
          FROM asset_indicator_snapshot
          WHERE run_id=?
          GROUP BY asset_id
        ) latest ON latest.asset_id=i.asset_id AND latest.metric_date=i.metric_date
        WHERE i.run_id=?
          AND a.asset_code IN ({placeholders})
        """,
        tuple([run_id, run_id] + codes),
    ).fetchall()
    return {str(row["asset_code"]): row for row in indicator_rows}


def _pool_performance_metric(
    row: PortalHolding,
    *,
    entry_time_bj: str | None,
    price_history: dict[str, list[PricePoint]],
    benchmark_returns_by_code: dict[str, dict[date, float]],
    candidate: Candidate | None,
    resolved_review_keys: set[tuple[str, str]],
    indicator_row=None,
) -> PortalPoolMetric:
    points = price_history.get(row.code, [])
    entry_date = _beijing_date(entry_time_bj)
    asset_daily_map = _daily_returns_by_date(points)
    benchmark_label, benchmark_returns = _select_theme_benchmark(row, candidate, benchmark_returns_by_code)
    aligned = [
        (day, asset_daily_map[day], benchmark_returns[day])
        for day in sorted(asset_daily_map)
        if day in benchmark_returns
    ]
    asset_returns = [item[1] for item in aligned]
    benchmark_values = [item[2] for item in aligned]
    beta = _beta(asset_returns, benchmark_values) if len(aligned) >= 20 else None
    asset_annualized = _annualized_mean_return(asset_returns) if len(aligned) >= 20 else None
    benchmark_annualized = _annualized_mean_return(benchmark_values) if len(aligned) >= 20 else None
    alpha = (
        asset_annualized - beta * benchmark_annualized
        if asset_annualized is not None and beta is not None and benchmark_annualized is not None
        else None
    )
    recent_aligned = aligned[-20:]
    theta = _mean([asset - benchmark for _, asset, benchmark in recent_aligned]) if len(recent_aligned) >= 5 else None
    gamma = None
    vega = None
    calmar = None
    treynor = None
    sharpe = _sharpe(asset_returns) if len(asset_returns) >= 20 else None
    sortino = _sortino(asset_returns) if len(asset_returns) >= 20 else None
    metric_data_date = points[-1].date.strftime("%Y%m%d") if points else None
    if indicator_row is not None:
        benchmark_label = f"主题基准：{indicator_row['benchmark_label'] or indicator_row['benchmark_code'] or '-'}"
        alpha = indicator_row["alpha"]
        beta = indicator_row["beta"]
        gamma = indicator_row["gamma"]
        theta = indicator_row["theta"]
        vega = indicator_row["vega"]
        sharpe = indicator_row["sharpe"]
        sortino = indicator_row["sortino"]
        calmar = indicator_row["calmar"]
        treynor = indicator_row["treynor"]
        metric_raw_date = str(indicator_row["metric_date"] or "")
        metric_data_date = metric_raw_date.replace("-", "") if metric_raw_date else metric_data_date
    is_holding = row.rank <= 5
    needs_review = row.grade == "Manual Review" or row.action_label == "Manual Review"
    review_text = (
        "已复核/观察中"
        if needs_review and (row.code, row.trigger_reason) in resolved_review_keys
        else ("需人工复核" if needs_review else _zh_action(row.action_label))
    )
    return PortalPoolMetric(
        rank=row.rank,
        pool_label="持仓池" if is_holding else "观察池",
        pool_class="holding" if is_holding else "observe",
        code=row.code,
        name=row.name,
        grade=row.grade,
        score=row.score,
        target_weight=row.target_weight if is_holding else 0.0,
        action_label=row.action_label,
        trigger_reason=row.trigger_reason,
        review_text=review_text,
        entry_time_bj=entry_time_bj,
        metric_data_date=metric_data_date,
        since_entry_return=_return_since_date(points, entry_date),
        return_1m=_return_over_days(points, 31),
        return_3m=_return_over_days(points, 93),
        return_6m=_return_over_days(points, 183),
        benchmark_label=benchmark_label,
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        theta=theta,
        vega=vega,
        sharpe=sharpe,
        sortino=sortino,
        calmar=calmar,
        treynor=treynor,
    )


def _pool_performance_metrics(
    settings: Settings,
    conn,
    rows: list[PortalHolding],
    current_run: PortalRun | None,
    resolved_review_keys: set[tuple[str, str]] | None = None,
) -> list[PortalPoolMetric]:
    sorted_rows = sorted(rows, key=lambda item: item.rank)
    if not sorted_rows:
        return []
    price_path = settings.manual_dir / "price_history.csv"
    benchmark_path = settings.manual_dir / "benchmark_price_history.csv"
    if not price_path.exists():
        return []
    try:
        price_history = load_price_history(price_path)
        benchmark_history = load_price_history(benchmark_path) if benchmark_path.exists() else {}
        candidate_path = settings.manual_dir / "candidates.csv"
        candidates = load_candidates(candidate_path) if candidate_path.exists() else []
    except (OSError, ValueError):
        return []
    benchmark_returns_by_code = _benchmark_returns_by_code(benchmark_history)
    candidates_by_code = {candidate.asset_code: candidate for candidate in candidates}
    entry_times = _entry_times_for_pool_rows(conn, sorted_rows)
    indicator_rows = _latest_indicator_rows(conn, current_run.run_id if current_run else None, sorted_rows)
    resolved_review_keys = resolved_review_keys or set()
    metrics: list[PortalPoolMetric] = []
    for row in sorted_rows:
        pool_kind = "holding_pool" if row.rank <= 5 else "observation_pool"
        metrics.append(
            _pool_performance_metric(
                row,
                entry_time_bj=entry_times.get((row.code, pool_kind)),
                price_history=price_history,
                benchmark_returns_by_code=benchmark_returns_by_code,
                candidate=candidates_by_code.get(row.code),
                resolved_review_keys=resolved_review_keys,
                indicator_row=indicator_rows.get(row.code),
            )
        )
    return metrics


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
    ratio_text = f"{ratio * 100:+.2f}%"
    if ratio > RELATIVE_ACTION_THRESHOLD:
        return "up", ratio_text, "增加/买入"
    if ratio < -RELATIVE_ACTION_THRESHOLD:
        return "down", ratio_text, "减少/卖出"
    return "flat", ratio_text, "维持"


def _fund_button(row: PortalHolding) -> str:
    return (
        f'<button type="button" class="fund-link" data-fund-code="{_escape(row.code)}">'
        f"{_escape(row.name)}</button>"
    )


def _fund_table_cell(code: str, name: str) -> str:
    return (
        '<div class="fund-cell">'
        f'<strong class="fund-code">{_escape(code)}</strong>'
        f'<button type="button" class="fund-link" data-fund-code="{_escape(code)}">'
        f"{_escape(name)}</button>"
        "</div>"
    )


def _holding_rows(
    rows: list[PortalHolding],
    *,
    previous_by_code: dict[str, PortalHolding],
    target_time: str,
    baseline_time: str,
    previous_time: str,
    initial_times_by_code: dict[str, str] | None = None,
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
        initial_time = (initial_times_by_code or {}).get(row.code) or baseline_time
        cells.append(
            f'<tr class="row-{initial_class}" data-reference-row data-initial-class="{initial_class}" data-previous-class="{previous_class}">'
            f"<td>{row.rank}</td>"
            f"<td>{_fund_table_cell(row.code, row.name)}</td>"
            f"<td><span class=\"badge\">{_escape(_zh_grade(row.grade))}</span></td>"
            f"<td>{_score(row.score)}</td>"
            f"<td><strong>{_pct(row.target_weight)}</strong><span>目标时间：{_escape(target_time)}</span></td>"
            "<td>"
            f'<strong data-reference-weight data-initial-value="{_escape(initial_value)}" data-previous-value="{_escape(previous_value)}">{_escape(initial_value)}</strong>'
            f'<span data-reference-time data-initial-value="初始持仓权重时间：{_escape(initial_time)}" data-previous-value="上轮对比权重时间：{_escape(previous_time)}">初始持仓权重时间：{_escape(initial_time)}</span>'
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


def _pool_rows(
    holding_pool: list[PortalHolding],
    observation_pool: list[PortalHolding],
    resolved_review_keys: set[tuple[str, str]] | None = None,
) -> str:
    resolved_review_keys = resolved_review_keys or set()
    rows = sorted([*holding_pool, *observation_pool], key=lambda item: item.rank)
    if not rows:
        return '<tr><td colspan="8">暂无持仓池或观察池排序数据；下一次真实刷新后会生成最新排序。</td></tr>'
    cells: list[str] = []
    for row in rows:
        is_holding = row.rank <= 5
        pool_label = "持仓池" if is_holding else "观察池"
        pool_class = "holding" if is_holding else "observe"
        weight_text = _pct(row.target_weight) if is_holding else "0.00% · 观察"
        needs_review = row.grade == "Manual Review" or row.action_label == "Manual Review"
        review_text = "已复核/观察中" if needs_review and (row.code, row.trigger_reason) in resolved_review_keys else (
            "需人工复核" if needs_review else _zh_action(row.action_label)
        )
        cells.append(
            f'<tr class="pool-row {pool_class}">'
            f"<td><strong>#{row.rank}</strong></td>"
            f'<td><span class="pool-badge {pool_class}">{pool_label}</span></td>'
            f"<td>{_fund_table_cell(row.code, row.name)}</td>"
            f"<td><span class=\"badge\">{_escape(_zh_grade(row.grade))}</span></td>"
            f"<td>{_score(row.score)}</td>"
            f"<td>{_escape(weight_text)}</td>"
            f"<td>{_escape(review_text)}</td>"
            f"<td>{_escape(row.trigger_reason)}</td>"
            "</tr>"
        )
    return "\n".join(cells)


def _pool_metric_rows(metrics: list[PortalPoolMetric]) -> str:
    if not metrics:
        return '<tr><td colspan="17">暂无可展示的持仓池/观察池表现指标；下一次全局数据刷新后会重新计算。</td></tr>'
    cells: list[str] = []
    for row in metrics:
        weight_text = _pct(row.target_weight) if row.pool_class == "holding" else "0.00% · 观察"
        cells.append(
            f'<tr class="pool-row {row.pool_class}">'
            f"<td><strong>#{row.rank}</strong></td>"
            f'<td><span class="pool-badge {row.pool_class}">{_escape(row.pool_label)}</span></td>'
            f"<td>{_fund_table_cell(row.code, row.name)}</td>"
            f"<td><span class=\"badge\">{_escape(_zh_grade(row.grade))}</span></td>"
            f"<td>{_score(row.score)}</td>"
            f"<td>{_escape(weight_text)}</td>"
            f"<td>{_escape(row.review_text)}</td>"
            f"<td>{_escape(row.trigger_reason)}</td>"
            f"<td>{_escape(_format_time(row.entry_time_bj, 'Asia/Shanghai'))}</td>"
            f"<td>{_escape(row.metric_data_date or '-')}</td>"
            f"<td>{_pct(row.since_entry_return)}</td>"
            f"<td>{_pct(row.return_1m)}</td>"
            f"<td>{_pct(row.return_3m)}</td>"
            f"<td>{_pct(row.return_6m)}</td>"
            f"<td>{_escape(_benchmark_display_label(row.benchmark_label))}</td>"
            f"<td>{_greek_metric_cell(row)}</td>"
            f"<td>{_risk_metric_cell(row)}</td>"
            "</tr>"
        )
    return "\n".join(cells)


def _expansion_candidate_rows(candidates: list[PortalExpansionCandidate]) -> str:
    if not candidates:
        return '<tr><td colspan="8">最新运行未记录新增扩容候选；当前候选池以持仓池和观察池排序为准。</td></tr>'
    cells: list[str] = []
    for row in candidates:
        keywords = "、".join(row.matched_keywords) if row.matched_keywords else "-"
        source = (
            f'<a href="{_escape(row.source_url)}" target="_blank" rel="noreferrer">费率来源</a>'
            if row.source_url
            else "-"
        )
        cells.append(
            '<tr class="expansion-row">'
            f"<td><strong>E{row.sequence}</strong></td>"
            f"<td>{_fund_table_cell(row.code, row.name)}</td>"
            f"<td>{_escape(row.fund_type)}</td>"
            f"<td>{_escape(str(row.theme_score))}</td>"
            f"<td>{_escape(keywords)}</td>"
            f"<td>{_escape(row.nav_status)}<br>{_escape(row.rule_status)}</td>"
            f'<td><span class="pool-badge expand">{_escape(row.current_status)}</span><br><small>{_escape(row.note)}</small></td>'
            f"<td>{source}</td>"
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
        cards = '<div class="review-empty">当前没有待处理复核项；已处理记录保留在 SQLite 数据库和历史运行中。</div>'
    else:
        cards = "\n".join(
            f"""
            <article class="review-item" data-review-item data-review-id="{item.review_id}" data-review-run-id="{_escape(item.run_id)}">
              <div class="review-item-head">
                <div>
                  <strong>{_escape(item.code)} · {_escape(item.name)}</strong>
                  <span>{_escape(item.created_at)} · {_escape(item.status)} · {_escape(item.run_id)}</span>
                  <span>基金分析排序：{_escape('#' + str(item.analysis_rank) if item.analysis_rank is not None else '未进入当前分析排序')} · 等级：{_escape(_zh_grade(item.analysis_grade or '-'))} · 证据置信度：{_escape(_score(item.analysis_score))}</span>
                </div>
                <span class="badge locked">{_escape(item.action_blocked)}</span>
              </div>
              <div class="review-reason">
                <strong>为什么需要人工复核</strong>
                <span>{_escape(item.reason)}</span>
              </div>
              <label>
                <span>复核结果</span>
                <select data-review-decision>
                  <option value="observe_pool">放入观察池继续观察</option>
                  <option value="exclude_current_observation">剔除这一轮观察池</option>
                  <option value="promote_top5_candidate_pool">进入 Top 5 候选操作池</option>
                </select>
              </label>
              <label>
                <span>备注</span>
                <textarea data-review-note rows="3" placeholder="记录你核对的来源、平台交易页、费率、状态或操作理由"></textarea>
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
          <div class="subtitle">复核记录实时保存到本机 SQLite 数据库；不做浏览器端保存。</div>
        </div>
        <button type="button" data-close-review>关闭</button>
      </div>
      <div class="review-result-guide" aria-label="复核结果含义">
        <article>
          <strong>放入观察池继续观察</strong>
          <p>保存后立即新增一次真实 Serenity run；对象继续观察，后续满足 Serenity 标准和条件后更新进持仓建议，不满足则继续观察，直到不再满足观察池标准后移出。</p>
        </article>
        <article>
          <strong>剔除这一轮观察池</strong>
          <p>保存后立即新增一次真实 Serenity run；对象本轮移除，当前问题解决后，或 14 天后再次满足 Serenity 标准和条件时，才允许重新进入观察池。</p>
        </article>
        <article>
          <strong>进入 Top 5 候选操作池</strong>
          <p>保存后立即运行一次 Serenity 全流程，并同步更新首页持仓建议、报告、数据库和全局展示数据。</p>
        </article>
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
        <button type="button" class="active" data-fund-library-mode="table">表格</button>
        <button type="button" data-fund-library-mode="gallery">卡片</button>
      </div>
      <div class="fund-library-grid" id="fund-library-body" data-fund-library-view="gallery" hidden></div>
      <div class="table-wrap fund-library-table-view" data-fund-library-view="table">
        <table class="fund-library-table">
          <thead>
            <tr>
              <th>代码</th>
              <th>基金名称</th>
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
          <div class="subtitle">用来解释 Serenity 为什么挑选、为什么调仓、怎么计算权重；Score 只表示证据置信度。</div>
        </div>
        <button type="button" data-close-usage-guide>关闭</button>
      </div>
      <div class="guide-layout">
        <nav class="guide-nav" aria-label="使用说明目录">
          <button type="button" class="active" data-guide-target="guide-overview">阅读顺序</button>
          <button type="button" data-guide-target="guide-selection">Skill 选股逻辑</button>
          <button type="button" data-guide-target="guide-admission">准入规则</button>
          <button type="button" data-guide-target="guide-exit">剔除规则</button>
          <button type="button" data-guide-target="guide-indicators">指标说明</button>
          <button type="button" data-guide-target="guide-confidence">证据置信度</button>
          <button type="button" data-guide-target="guide-sources">数据源</button>
          <button type="button" data-guide-target="guide-weight">权重配置</button>
          <button type="button" data-guide-target="guide-discipline">调仓纪律</button>
          <button type="button" data-guide-target="guide-review">复核与边界</button>
        </nav>
        <div class="guide-content">
          <section class="guide-hero" id="guide-overview" data-guide-section>
            <div>
              <span class="guide-kicker">默认阅读顺序</span>
              <h3>先看结论，再追溯原因。</h3>
              <p>首页只保留关键动作；这块说明专门回答“为什么是这只基金、为什么是这个权重、为什么现在动或不动”。</p>
            </div>
            <div class="guide-summary">
              <span><strong>持有期</strong>1个月-1年</span>
              <span><strong>排序口径</strong>Serenity 优先</span>
              <span><strong>候选来源</strong>全市场自动扩容</span>
              <span><strong>Score 角色</strong>置信度/说服力</span>
              <span><strong>执行边界</strong>人工确认</span>
            </div>
          </section>

          <section class="guide-section" id="guide-selection" data-guide-section>
            <div class="guide-section-title">
              <span class="guide-kicker">第一层</span>
              <h3>Skill 选股逻辑</h3>
            </div>
            <p class="guide-lead">Serenity 不是先拿一张规则表机械筛选，而是先形成“未来 1个月-1年最值得承担高波动的高成长方向”判断，再检查这个判断能否落到可执行的场外基金上。</p>
            <div class="guide-steps">
              <p><strong>如何挑选</strong>先看高成长主题是否仍有景气度、资金关注和可解释的上涨来源，再把主题映射到能在场外买到的基金。</p>
              <p><strong>怎么挑选</strong>按产业链卡点、稀缺层、主题暴露、资金弹性和执行可得性形成 Serenity 优先级。</p>
              <p><strong>为什么挑选</strong>Top5 先由 Serenity 判断决定，不由 Score 机械排序；低 Serenity 优先级标的不会仅凭更高 ConfidenceScore 超过高优先级标的。</p>
              <p><strong>为什么调仓</strong>当产业链强弱、资金方向、风险回撤、费用/申赎状态或 Top5 排名改变，系统会视为旧 baseline 需要修正。</p>
            </div>
            <div class="guide-callout">页面公开证据置信度、等级、目标权重、基准权重、相对比例、费用状态、基金库证据和运行时间线，方便追溯每一次建议。</div>
          </section>

          <section class="guide-section" id="guide-admission" data-guide-section>
            <div class="guide-section-title">
              <span class="guide-kicker">准入</span>
              <h3>进入候选池的规则</h3>
            </div>
            <p class="guide-lead">准入不是 Score 排名赛，而是 Serenity 先判断哪些高成长方向值得研究，再用数据闸门决定能否进入持仓池或观察池。</p>
            <div class="guide-steps">
              <p><strong>全市场扩容</strong>每次正式运行前扫描公开全市场基金列表，优先补充 AI、半导体、科技、QDII、创业板、科创、互联网、通信、机器人、软件、云计算、数字经济、信息技术等高成长主题。</p>
              <p><strong>硬排除</strong>债券、货币、现金、余额宝、固收、短债、同业存单等保守类对象在扩容阶段直接排除；不因支付宝或 MooMoo 暂不支持交易而单独排除，只作为交易路径建议。</p>
              <p><strong>历史要求</strong>所有进入筛选范围和候选池的基金必须有至少 24 个月净值历史；不足 24 个月不能进入可执行持仓建议。</p>
              <p><strong>风险要求</strong>MDD 达到或超过 40.00% 直接 Block/清仓标签；回撤修复时间达到或超过 365 天时强制降级复核。</p>
              <p><strong>证据要求</strong>申购状态、赎回状态、申购费、赎回费、管理费、托管费和费率分档必须可追溯；官方级来源少于 2 个或来源冲突时只能观察或复核。</p>
              <p><strong>排序要求</strong>通过硬闸门后，Top5 持仓池按 Serenity 优先级排序；Score 只修正置信度和权重，不允许单独压过 Serenity 的主题判断。</p>
            </div>
          </section>

          <section class="guide-section" id="guide-exit" data-guide-section>
            <div class="guide-section-title">
              <span class="guide-kicker">剔除</span>
              <h3>入池后的纪律规则</h3>
            </div>
            <p class="guide-lead">剔除规则只约束已经进入持仓池或观察池的对象，不作为 Serenity 初始准入规则；只统计希腊字母指标和风险指标。</p>
            <div class="guide-steps">
              <p><strong>跟踪对象</strong>每个交易日计算 Alpha、Beta、Gamma、Theta、Vega、Sharpe、Sortino、Calmar、Treynor；当天可计算指标数量记为 x。</p>
              <p><strong>5 日剔除</strong>连续 5 个交易日中，负项数量达到 ceil(80.00% * 5 * x) 时剔除或给出降权/清仓标签。</p>
              <p><strong>10 日剔除</strong>连续 10 个交易日中，负项数量达到 ceil(60.00% * 10 * x) 时剔除或给出降权/清仓标签。</p>
              <p><strong>硬风险剔除</strong>MDD 达到 40.00%、7 日回撤恶化超过 5.00%、或单标过度放大连续 2 次，会触发风险纪律，优先输出减少、暂停新增、Block 或清仓标签。</p>
              <p><strong>数据异常剔除</strong>连续缺失净值/持仓超过 2 天、费率/赎回状态缺失、官方级来源少于 2 个或来源冲突时，不硬下买入结论，进入 Manual Review 或观察池。</p>
              <p><strong>重新进入</strong>被剔除对象解决当前问题后，或 14 天后重新满足 Serenity 标准和证据条件，才允许重新进入观察池；进入 Top5 仍由 Serenity 优先判断。</p>
            </div>
          </section>

          <section class="guide-section" id="guide-indicators" data-guide-section>
            <div class="guide-section-title">
              <span class="guide-kicker">指标</span>
              <h3>希腊字母与风险指标</h3>
            </div>
            <p class="guide-lead">这些指标用于入池后纪律审计和剔除判断，不取代 Serenity 的准入判断；所有指标每日写入本机 SQLite。</p>
            <div class="guide-steps">
              <p><strong>Alpha</strong>公式：年化基金收益 - Beta x 年化基准收益；意义：剔除基准暴露后是否有正超额收益。</p>
              <p><strong>Beta</strong>公式：Cov(基金日收益, 基准日收益) / Var(基准日收益)；意义：基金对主题/市场基准的方向敏感度。</p>
              <p><strong>Gamma</strong>公式：本期 Beta - 上期 Beta；意义：基准敏感度是否继续放大或快速衰减。</p>
              <p><strong>Theta</strong>公式：近 20 个净值点平均日超额收益；意义：本系统把它定义为时间衰减/趋势退化代理，不是期权定价 Theta。</p>
              <p><strong>Vega</strong>公式：基金波动率 / 基准波动率 - 1；意义：相对基准的波动暴露是否过度放大。</p>
              <p><strong>Sharpe</strong>公式：平均日收益 / 日收益标准差 x sqrt(252)；意义：单位总波动获得的年化收益。</p>
              <p><strong>Sortino</strong>公式：平均日收益 / 下行日收益标准差 x sqrt(252)；意义：只惩罚下行波动后的收益质量。</p>
              <p><strong>Calmar</strong>公式：年化收益 / 最大回撤；意义：承担回撤后是否仍有足够收益补偿。</p>
              <p><strong>Treynor</strong>公式：(年化基金收益 - 年化基准收益) / Beta；意义：单位系统性风险获得的超额收益。</p>
            </div>
          </section>

          <section class="guide-section" id="guide-confidence" data-guide-section>
            <div class="guide-section-title">
              <span class="guide-kicker">第二层</span>
              <h3>证据置信度</h3>
            </div>
            <p class="guide-lead">Score 不替代 Serenity 判断，只回答“这次判断有多少数据支持、是否足够可执行”。</p>
            <div class="guide-formula">ConfidenceScore = Data 25 + Timeliness 15 + Source 15 + Return 15 + Risk 20 + Executable 10</div>
            <div class="guide-steps">
              <p><strong>Data</strong>普通关键字段缺失按项扣分；return_windows 缺失按关键缺失处理，最高扣 20 分并触发复核。</p>
              <p><strong>Timeliness</strong>净值/持仓缺失不超过 2 天得分，否则进入时间完整性降级。</p>
              <p><strong>Source</strong>官方级来源至少 2 个且无冲突才完整得分；来源冲突优先解释冲突。</p>
              <p><strong>Return</strong>Return = 15 x 跑赢次数 / 8；比较 1个月、3个月、1年、10交易日，对照沪指和标普500。</p>
              <p><strong>Risk</strong>MDD 小于 40.00% 才可继续；回撤修复时间达到 365 天会强制压低风险分。</p>
              <p><strong>Executable</strong>申购/赎回开放且费率分档完整才完整得分。</p>
            </div>
          </section>

          <section class="guide-section" id="guide-sources" data-guide-section>
            <div class="guide-section-title">
              <span class="guide-kicker">数据层</span>
              <h3>数据源与可审计文件</h3>
            </div>
            <p class="guide-lead">首页结论来自本地 SQLite 历史归档和 GitHub 可审计 CSV。SQLite 负责保护历史事实，不作为公开外链；GitHub 链接指向可复核的数据源文件。</p>
            <div class="guide-steps">
              <p><strong>候选基金主数据</strong><a href="https://github.com/LinzeColin/CodexProject/blob/main/Serenity-Alipay/data/manual/candidates.csv" target="_blank" rel="noreferrer">data/manual/candidates.csv</a>：基金代码、基金名称、市场、主题、来源等级、是否排除。</p>
              <p><strong>基金净值历史</strong><a href="https://github.com/LinzeColin/CodexProject/blob/main/Serenity-Alipay/data/manual/price_history.csv" target="_blank" rel="noreferrer">data/manual/price_history.csv</a>：候选基金至少 24 个月净值历史，用于收益、回撤、Sharpe、Sortino 等指标。</p>
              <p><strong>基金申赎与费用</strong><a href="https://github.com/LinzeColin/CodexProject/blob/main/Serenity-Alipay/data/manual/fund_rules.csv" target="_blank" rel="noreferrer">data/manual/fund_rules.csv</a>：申购、赎回、确认周期、申购费、赎回费、管理费、托管费和费用分档。</p>
              <p><strong>基准与专项基准</strong><a href="https://github.com/LinzeColin/CodexProject/blob/main/Serenity-Alipay/data/manual/benchmark_price_history.csv" target="_blank" rel="noreferrer">data/manual/benchmark_price_history.csv</a>：沪指、标普500、纳指100、创业板指、国证芯片、中证半导、中证人工智能和港股科技主题代理基准。</p>
            </div>
            <div class="guide-callout">数据源优先级仍按 MooMoo/OpenD、支付宝、官方平台、交易快照、公开财经聚合排序；当前专项基准若来自 Yahoo 或东方财富，会在 CSV 的 source_name、source_type、url_or_path、as_of 中保留来源证据。</div>
          </section>

          <section class="guide-section" id="guide-weight" data-guide-section>
            <div class="guide-section-title">
              <span class="guide-kicker">第三层</span>
              <h3>权重配置</h3>
            </div>
            <div class="guide-formula">SerenityRank_i = 产业链卡点优先级 + 主题暴露 + 场外可执行性</div>
            <div class="guide-formula">ConfidenceModifier_i = 0.85 + 0.15 x ConfidenceScore_i / 100</div>
            <div class="guide-formula">RawWeight_i = SerenityBase_i x ConfidenceModifier_i</div>
            <div class="guide-formula">Capped_i = min(normalize(RawWeight_i), 30.00%)</div>
            <div class="guide-formula">TargetWeight_i = Capped_i / sum(Capped)</div>
            <div class="guide-steps">
              <p><strong>排序</strong>仅非 Block 候选进入 Top5；排序优先服从 Serenity，ConfidenceScore 只做辅助修正。</p>
              <p><strong>权重</strong>目标权重是策略份额，不是支付宝真实账户仓位。</p>
              <p><strong>基准</strong>首轮基准从 0.00% 开始；后续运行相对上一轮 Serenity baseline 比较。</p>
            </div>
          </section>

          <section class="guide-section" id="guide-discipline" data-guide-section>
            <div class="guide-section-title">
              <span class="guide-kicker">第四层</span>
              <h3>持仓调整逻辑</h3>
            </div>
            <p class="guide-lead">这里不是把 Deviation 翻译成买卖术语，而是说明系统如何从 Serenity 新判断推导到人工操作建议。</p>
            <div class="guide-formula">Deviation = TargetWeight - BaselineWeight</div>
            <div class="guide-steps">
              <p><strong>凭什么</strong>先确认数据质量通过、基金申赎和费率可执行、候选没有 Block，再比较新一轮 Serenity 目标权重和上一轮 Serenity baseline。</p>
              <p><strong>为什么</strong>偏离不是账户盈亏，而是 Serenity 对产业链优先级、主题弹性、风险和执行条件的最新判断相对旧 baseline 的变化。</p>
              <p><strong>怎么做</strong>|Deviation| &lt;= 1.00%：维持；Deviation &gt; 1.00% 且 Action-Ready：增配；非 Action-Ready：暂停新增或人工复核；Deviation &lt; -1.00%：减少；Block：阻断或清仓标签。</p>
              <p><strong>做多少</strong>策略调整份额 = TargetWeight - BaselineWeight；若需要换算金额，人工按“计划投入资金 x |Deviation|”在支付宝或官方平台确认。</p>
              <p><strong>为什么做这么多</strong>TargetWeight 已由 Serenity 优先级、证据置信度修正、30.00% 单标上限和归一化约束计算完成；Deviation 是把旧 baseline 调到新目标所需的最小策略差额。</p>
              <p><strong>为什么 1.00% 内维持</strong>小于等于 1.00% 的变化通常不足以覆盖确认成本、申赎费、净值时差和短时噪声，除非同时触发风险硬门槛。</p>
            </div>
          </section>

          <section class="guide-section" id="guide-review" data-guide-section>
            <div class="guide-section-title">
              <span class="guide-kicker">第五层</span>
              <h3>重平衡、复核与边界</h3>
            </div>
            <div class="guide-steps">
              <p><strong>重平衡</strong>单标偏离超过 1.00%、Top5 变动率超过 20.00%、新增 1 只、替换 2 只或关键字段变化超过 1σ，会触发纪律事件。</p>
              <p><strong>人工复核</strong>连续缺失净值/持仓超过 2 天、费率分档缺失、官方级来源少于 2 个或来源冲突，会进入 Manual Review。</p>
              <p><strong>为什么需要复核</strong>每个复核对象都会显示进入复核的具体原因，例如费率/申赎状态缺失、来源冲突、净值或持仓时间滞后、数据质量不足或执行条件不明确。</p>
              <p><strong>放入观察池继续观察</strong>保存复核后立即新增一次真实 Serenity run；对象继续保留在观察池，后续满足 Serenity 标准和条件后更新进持仓建议，不满足则继续观察，直到不再满足观察池标准后移出。</p>
              <p><strong>剔除这一轮观察池</strong>保存复核后立即新增一次真实 Serenity run；对象从本轮观察池移除，当前问题解决后，或 14 天后再次满足 Serenity 标准和条件时，才允许重新进入观察池。</p>
              <p><strong>进入 Top 5 候选操作池</strong>保存复核后立即运行一次 Serenity 全流程，同步刷新首页持仓建议、报告、数据库和全局展示数据。</p>
              <p><strong>保存处置</strong>保存复核必须写入本机 SQLite 数据库；页面不会把复核保存在浏览器端。</p>
              <p><strong>执行边界</strong>无自动交易；执行锁开启时，只输出研究排序和纪律标签；所有真实申购、赎回、增配、减配都必须在支付宝或官方平台人工确认。</p>
              <p><strong>使用顺序</strong>先看“当前持仓建议”，再看“持仓建议”表里的基准权重口径；需要追溯费用和申赎状态时进入“基金库”。</p>
            </div>
          </section>
        </div>
      </div>
    </section>
  </div>
    """


def _relative_action_summary(
    rows: list[PortalHolding],
    reference_weights: dict[str, float | None],
) -> PortalActionSummary:
    if not rows:
        return PortalActionSummary(
            level="无数据",
            count="等待下一轮",
            boundary="不输出操作",
            detail="暂无持仓建议行，不能生成操作动作。",
            tone="flat",
        )
    changes: list[tuple[PortalHolding, str, str, str]] = []
    for row in rows:
        change_class, ratio, action = _relative_ratio(row.target_weight, reference_weights.get(row.code))
        if change_class in {"up", "down"}:
            changes.append((row, change_class, ratio, action))
    if not changes:
        return PortalActionSummary(
            level="保持当前持仓",
            count="0 项变化",
            boundary="无需新增操作",
            detail="持仓建议表当前基准口径下全部为维持；无需新增申购、赎回、增配或减配。",
            tone="flat",
        )

    buy_count = sum(1 for _, change_class, _, _ in changes if change_class == "up")
    sell_count = sum(1 for _, change_class, _, _ in changes if change_class == "down")
    if buy_count and sell_count:
        level = "需人工确认再平衡"
        tone = "mixed"
    elif buy_count:
        level = "需人工确认增配"
        tone = "up"
    else:
        level = "需人工确认减配"
        tone = "down"
    detail = "\n".join(f"{row.name}：{action} {ratio}" for row, _, ratio, action in changes)
    return PortalActionSummary(
        level=level,
        count=f"增加/买入 {buy_count} 项；减少/卖出 {sell_count} 项",
        boundary="支付宝/官方平台人工确认",
        detail=detail,
        tone=tone,
    )


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
            "sourceUrl": info.source_url or "-",
        }
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def render_application_portal(
    current_run: PortalRun | None,
    current_holdings: list[PortalHolding],
    previous_run: PortalRun | None,
    previous_holdings: list[PortalHolding],
    *,
    observation_pool: list[PortalHolding] | None = None,
    baseline_time_bj: str | None = None,
    fund_library: dict[str, PortalFundInfo] | None = None,
    run_timeline: list[PortalTimelineEvent] | None = None,
    manual_review_items: list[PortalManualReviewItem] | None = None,
    resolved_review_keys: set[tuple[str, str]] | None = None,
    pool_metrics: list[PortalPoolMetric] | None = None,
    expansion_candidates: list[PortalExpansionCandidate] | None = None,
    initial_reference_times_by_code: dict[str, str] | None = None,
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
    previous_by_code = {row.code: row for row in previous_holdings}
    initial_action_summary = _relative_action_summary(
        current_holdings,
        {row.code: row.current_weight for row in current_holdings},
    )
    previous_action_summary = _relative_action_summary(
        current_holdings,
        {code: row.target_weight for code, row in previous_by_code.items()},
    )
    latest_run_time = current_bj
    report_href = _portal_relative_href("data/reports/index.html", "../../data/reports/index.html")
    snapshot_href = _portal_relative_href(
        current_run.html_path if current_run else None,
        report_href,
    )
    fund_json = _fund_library_json(fund_library or {})
    timeline_events = run_timeline or []
    review_items = manual_review_items or []
    resolved_review_keys = resolved_review_keys or set()
    observation_rows = observation_pool or []
    pool_metric_rows = pool_metrics or []
    expansion_rows = expansion_candidates or []
    if not pool_metric_rows:
        fallback_pool_rows = sorted([*current_holdings, *observation_rows], key=lambda item: item.rank)
        for row in fallback_pool_rows:
            is_holding = row.rank <= 5
            needs_review = row.grade == "Manual Review" or row.action_label == "Manual Review"
            review_text = (
                "已复核/观察中"
                if needs_review and (row.code, row.trigger_reason) in resolved_review_keys
                else ("需人工复核" if needs_review else _zh_action(row.action_label))
            )
            pool_metric_rows.append(
                PortalPoolMetric(
                    rank=row.rank,
                    pool_label="持仓池" if is_holding else "观察池",
                    pool_class="holding" if is_holding else "observe",
                    code=row.code,
                    name=row.name,
                    grade=row.grade,
                    score=row.score,
                    target_weight=row.target_weight if is_holding else 0.0,
                    action_label=row.action_label,
                    trigger_reason=row.trigger_reason,
                    review_text=review_text,
                    entry_time_bj=None,
                    metric_data_date=None,
                    since_entry_return=None,
                    return_1m=None,
                    return_3m=None,
                    return_6m=None,
                    benchmark_label="基准缺失",
                    alpha=None,
                    beta=None,
                    gamma=None,
                    theta=None,
                    vega=None,
                    sharpe=None,
                    sortino=None,
                    calmar=None,
                    treynor=None,
                )
            )
    initial_reference_times = {
        code: _format_time(value, "Asia/Shanghai")
        for code, value in (initial_reference_times_by_code or {}).items()
        if value
    }
    if not initial_reference_times:
        initial_reference_times = {
            metric.code: _format_time(metric.entry_time_bj, "Asia/Shanghai")
            for metric in pool_metric_rows
            if metric.pool_class == "holding" and metric.entry_time_bj
        }
    initial_head_time = "按各基金首次入池时间" if initial_reference_times else baseline_bj
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
    .home-grid {{ display: grid; grid-template-columns: minmax(0, 1fr); gap: 16px; align-items: start; }}
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
    .fund-cell {{
      display: grid;
      gap: 4px;
      min-width: 220px;
      align-items: start;
    }}
    .fund-code {{
      display: block;
      color: var(--ink);
      font-weight: 900;
      line-height: 1.25;
    }}
    .fund-cell .fund-link {{
      display: block;
      width: fit-content;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }}
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
    .pool-ranking-panel {{ margin-bottom: 16px; }}
    .pool-ranking-note {{ margin: 6px 0 12px; color: var(--muted); line-height: 1.5; font-size: 13px; }}
    .pool-table {{ min-width: 1040px; }}
    .pool-metric-panel {{ margin-bottom: 16px; }}
    .pool-metric-table {{ min-width: 1760px; }}
    .pool-metric-table th, .pool-metric-table td {{ font-size: 12px; }}
    .metric-pair-stack {{ display: grid; gap: 6px; min-width: 250px; }}
    .metric-pair-line {{ display: grid; grid-template-columns: 58px minmax(82px, 1fr) minmax(82px, 1fr); gap: 6px; align-items: center; line-height: 1.35; }}
    .metric-pair-line strong {{ color: var(--ink); }}
    .metric-pair-line em {{ font-style: normal; color: var(--muted); white-space: nowrap; }}
    .pool-metric-table th:nth-child(1),
    .pool-metric-table td:nth-child(1) {{
      position: sticky;
      left: 0;
      z-index: 2;
      min-width: 92px;
      background: inherit;
    }}
    .pool-metric-table th:nth-child(2),
    .pool-metric-table td:nth-child(2) {{
      position: sticky;
      left: 92px;
      z-index: 2;
      min-width: 92px;
      background: inherit;
    }}
    .pool-metric-table th:nth-child(3),
    .pool-metric-table td:nth-child(3) {{
      position: sticky;
      left: 184px;
      z-index: 2;
      min-width: 280px;
      background: inherit;
      box-shadow: 1px 0 0 var(--line);
    }}
    .pool-metric-table thead th:nth-child(1),
    .pool-metric-table thead th:nth-child(2),
    .pool-metric-table thead th:nth-child(3) {{ z-index: 3; background: var(--surface-2); }}
    .pool-row.holding td {{ background: #f8fbff; }}
    .pool-row.observe td {{ background: #fbfcfb; }}
    .pool-metric-table .pool-row.holding td:nth-child(1),
    .pool-metric-table .pool-row.holding td:nth-child(2),
    .pool-metric-table .pool-row.holding td:nth-child(3) {{ background: #f8fbff; }}
    .pool-metric-table .pool-row.observe td:nth-child(1),
    .pool-metric-table .pool-row.observe td:nth-child(2),
    .pool-metric-table .pool-row.observe td:nth-child(3) {{ background: #fbfcfb; }}
    .pool-badge {{
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border-radius: 999px;
      padding: 3px 9px;
      font-size: 12px;
      font-weight: 900;
      border: 1px solid var(--line);
      white-space: nowrap;
    }}
    .pool-badge.holding {{ color: var(--hold); background: var(--hold-bg); border-color: var(--hold-border); }}
    .pool-badge.observe {{ color: #6b4b11; background: #fff4d8; border-color: #ead59d; }}
    .pool-badge.expand {{ color: #075f6a; background: #e7f7f9; border-color: #b7e4e8; }}
    .expansion-candidate-panel {{ margin-bottom: 16px; }}
    .expansion-table {{ min-width: 1180px; }}
    .expansion-table th, .expansion-table td {{ font-size: 13px; }}
    .expansion-table th:nth-child(1),
    .expansion-table td:nth-child(1) {{
      position: sticky;
      left: 0;
      z-index: 2;
      min-width: 78px;
      background: inherit;
    }}
    .expansion-table th:nth-child(2),
    .expansion-table td:nth-child(2) {{
      position: sticky;
      left: 78px;
      z-index: 2;
      min-width: 300px;
      background: inherit;
      box-shadow: 1px 0 0 var(--line);
    }}
    .expansion-table thead th:nth-child(1),
    .expansion-table thead th:nth-child(2) {{ z-index: 3; background: var(--surface-2); }}
    .expansion-row td {{ background: #fbfeff; }}
    .expansion-row td:nth-child(1),
    .expansion-row td:nth-child(2) {{ background: #fbfeff; }}
    .expansion-row small {{ display: block; margin-top: 6px; color: var(--muted); line-height: 1.4; }}
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
    .change.mixed {{
      color: #783b12;
      background: linear-gradient(90deg, #fde9e6 0, #fde9e6 50%, #e8f5ed 50%, #e8f5ed 100%);
      border: 1px solid #ead1c2;
    }}
    .action-decision {{
      margin-top: 16px;
      border-top: 1px solid var(--line);
      padding-top: 14px;
      display: grid;
      gap: 12px;
    }}
    .action-decision-head {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .action-decision-head h2 {{ margin: 0; }}
    .action-decision-head small {{
      display: block;
      color: var(--muted);
      margin-top: 5px;
      line-height: 1.45;
    }}
    .action-decision-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }}
    .action-box {{
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 14px;
      background: #fbfcfb;
      min-height: 88px;
    }}
    .action-box span {{ color: var(--muted); display: block; font-size: 13px; }}
    .action-box strong {{ display: block; margin-top: 8px; font-size: 17px; line-height: 1.3; }}
    .action-detail {{
      margin: 0;
      border-left: 3px solid var(--accent);
      padding: 8px 0 8px 12px;
      color: var(--muted);
      line-height: 1.6;
      white-space: pre-line;
      overflow-wrap: anywhere;
    }}
    .actions {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; margin-top: 16px; }}
    .top-actions {{ margin: 16px 0; }}
    .top-actions .actions {{ margin-top: 0; }}
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
    .review-result-guide {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 12px;
    }}
    .review-result-guide article {{
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: #f8faf9;
      padding: 11px;
      display: grid;
      gap: 6px;
    }}
    .review-result-guide strong {{ font-size: 13px; }}
    .review-result-guide p {{ margin: 0; color: var(--muted); line-height: 1.45; font-size: 12px; }}
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
    .review-reason {{ border-left: 3px solid var(--danger); padding-left: 10px; display: grid; gap: 3px; }}
    .review-reason strong {{ color: var(--ink); font-size: 13px; }}
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
    .guide-panel {{ width: min(1080px, 100%); }}
    .guide-layout {{
      display: grid;
      grid-template-columns: 184px minmax(0, 1fr);
      gap: 14px;
      align-items: start;
    }}
    .guide-nav {{
      position: sticky;
      top: 0;
      display: grid;
      gap: 6px;
      align-self: start;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: #fbfcfb;
      padding: 8px;
    }}
    .guide-nav button {{
      width: 100%;
      justify-content: flex-start;
      background: transparent;
      border-color: transparent;
      color: var(--muted);
      text-align: left;
      padding: 8px 10px;
    }}
    .guide-nav button.active {{
      background: #eaf3f9;
      border-color: #bed7e7;
      color: var(--ink);
    }}
    .guide-content {{ display: grid; gap: 12px; }}
    .guide-hero {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(260px, 340px);
      gap: 12px;
      align-items: start;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: #f8faf8;
      padding: 14px;
    }}
    .guide-hero h3, .guide-section h3 {{ margin: 0; font-size: 17px; line-height: 1.35; }}
    .guide-hero p, .guide-lead {{
      margin: 8px 0 0;
      color: var(--muted);
      line-height: 1.6;
    }}
    .guide-summary {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }}
    .guide-summary span {{
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--surface);
      padding: 9px;
      color: var(--muted);
      line-height: 1.35;
      min-height: 58px;
    }}
    .guide-summary strong {{ display: block; color: var(--ink); margin-bottom: 4px; }}
    .guide-section {{
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--surface);
      padding: 14px;
      scroll-margin-top: 16px;
    }}
    .guide-section-title {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: center;
      border-bottom: 1px solid var(--line);
      padding-bottom: 10px;
      margin-bottom: 10px;
    }}
    .guide-kicker {{
      display: inline-flex;
      width: fit-content;
      border-radius: 999px;
      background: #eaf3f9;
      color: #24546b;
      font-size: 12px;
      font-weight: 800;
      padding: 4px 8px;
      white-space: nowrap;
    }}
    .guide-steps {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      margin-top: 10px;
    }}
    .guide-steps p {{
      margin: 0;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: #fbfcfb;
      padding: 10px;
      color: var(--muted);
      line-height: 1.55;
      overflow-wrap: anywhere;
    }}
    .guide-steps strong {{
      display: block;
      color: var(--ink);
      margin-bottom: 5px;
    }}
    .guide-callout {{
      margin-top: 10px;
      border-left: 3px solid var(--accent);
      background: #eef3ef;
      color: var(--ink);
      border: 1px solid var(--line);
      border-left-color: var(--accent);
      border-radius: var(--radius);
      padding: 10px 12px;
      line-height: 1.55;
    }}
    .guide-formula {{
      margin-top: 8px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: #eef3ef;
      color: var(--ink);
      padding: 9px 10px;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 12px;
      line-height: 1.45;
      overflow-wrap: anywhere;
      white-space: normal;
    }}
    .fund-library-panel {{ width: min(1180px, 100%); }}
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
    .fund-library-schedule strong {{ display: block; color: var(--ink); margin-bottom: 4px; }}
    .fund-library-schedule span {{ display: block; margin-top: 6px; white-space: pre-line; }}
    .fund-library-table-view {{
      max-height: min(640px, 72vh);
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--surface);
    }}
    .fund-library-table {{
      min-width: 2460px;
      border-collapse: separate;
      border-spacing: 0;
    }}
    .fund-library-table th {{
      position: sticky;
      top: 0;
      z-index: 3;
      background: #eef3ef;
      box-shadow: 0 1px 0 var(--line);
    }}
    .fund-library-table td {{
      min-width: 112px;
      max-width: 260px;
      white-space: normal;
      overflow-wrap: anywhere;
      line-height: 1.45;
      font-size: 12px;
      background: var(--surface);
    }}
    .fund-library-table tbody tr:nth-child(even) td {{ background: #fbfcfb; }}
    .fund-library-table th:nth-child(1),
    .fund-library-table td:nth-child(1) {{
      position: sticky;
      left: 0;
      z-index: 2;
      min-width: 92px;
      max-width: 92px;
    }}
    .fund-library-table th:nth-child(2),
    .fund-library-table td:nth-child(2) {{
      position: sticky;
      left: 92px;
      z-index: 2;
      min-width: 260px;
      max-width: 260px;
      font-weight: 800;
      color: var(--ink);
      box-shadow: 8px 0 14px -14px rgba(19, 32, 39, 0.48);
    }}
    .fund-library-table th:nth-child(1),
    .fund-library-table th:nth-child(2) {{
      z-index: 5;
    }}
    .fund-library-table td.fee-schedule-cell {{
      min-width: 300px;
      max-width: 340px;
      white-space: pre-line;
      line-height: 1.55;
    }}
    .fund-library-table td.fee-note-cell {{ min-width: 260px; max-width: 320px; }}
    .fund-field strong.multi-line-value {{ white-space: pre-line; line-height: 1.55; }}
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
      .metrics, .action-decision-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .actions {{ grid-template-columns: 1fr; }}
      .guide-layout {{ grid-template-columns: 1fr; }}
      .guide-nav {{ position: static; grid-template-columns: repeat(3, minmax(0, 1fr)); }}
      .guide-nav button {{ justify-content: center; text-align: center; }}
    }}
    @media (max-width: 560px) {{
      .shell {{ padding: 18px 12px 32px; }}
      .floating-refresh {{ top: 10px; right: 10px; }}
      h1 {{ font-size: 24px; }}
      .section-head {{ align-items: stretch; flex-direction: column; }}
      .view-switch {{ width: 100%; }}
      .metrics, .action-decision-grid, .discipline-list, .fund-fields, .fund-library-grid, .fund-library-meta, .guide-hero, .guide-summary, .guide-steps, .review-item-head, .review-result-guide {{ grid-template-columns: 1fr; }}
      .guide-nav {{ grid-template-columns: 1fr; }}
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
      <div class="metric"><span>需操作行为</span><strong data-action-level data-initial-value="{_escape(initial_action_summary.level)}" data-previous-value="{_escape(previous_action_summary.level)}">{_escape(initial_action_summary.level)}</strong></div>
      <div class="metric"><span>候选池</span><strong>Top5 持仓 / Top6-10 观察</strong></div>
    </section>

    <section class="panel top-actions" aria-label="操作入口">
      <div class="section-head">
        <h2>操作入口</h2>
      </div>
      <div class="actions">
        <article class="action-card">
          <div><strong>基金库</strong><p>{_escape(fund_count_text)}；申赎、费率、状态。</p></div>
          <button type="button" data-open-fund-library>查看基金</button>
        </article>
        <article class="action-card">
          <div><strong>使用说明</strong><p>选股、权重、调仓原因。</p></div>
          <button type="button" data-open-usage-guide>打开说明</button>
        </article>
        <article class="action-card">
          <div><strong>人工复核</strong><p>{_escape(review_count_text)}；保存到数据库。</p></div>
          <button type="button" data-open-review>处理复核</button>
        </article>
        <article class="action-card">
          <div><strong>报告</strong><p>查看最新结果和历史归档。</p></div>
          <a class="action primary" href="{report_href}">查看报告</a>
        </article>
        <article class="action-card">
          <div><strong>当前快照</strong><p>直接打开本轮完整快照。</p></div>
          <a class="action" href="{_escape(snapshot_href)}">查看快照</a>
        </article>
      </div>
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
                <th>基准权重<span data-reference-head-time data-initial-value="{_escape(initial_head_time)}" data-previous-value="{_escape(previous_bj)}">{_escape(initial_head_time)}</span></th>
                <th>相对比例</th>
                <th>动作</th>
                <th>操作口径</th>
              </tr>
            </thead>
            <tbody>{_holding_rows(current_holdings, previous_by_code=previous_by_code, target_time=current_bj, baseline_time=baseline_bj, previous_time=previous_bj, initial_times_by_code=initial_reference_times)}</tbody>
          </table>
        </div>

        <section class="action-decision" aria-label="需操作的行为">
          <div class="action-decision-head">
            <div>
              <h2>需操作的行为</h2>
              <small>跟随上方“基准权重口径”切换；与持仓建议表的相对比例动作保持一致。</small>
            </div>
            <strong class="change {initial_action_summary.tone}" data-action-level data-action-class data-initial-value="{_escape(initial_action_summary.level)}" data-previous-value="{_escape(previous_action_summary.level)}" data-initial-class="{_escape(initial_action_summary.tone)}" data-previous-class="{_escape(previous_action_summary.tone)}">{_escape(initial_action_summary.level)}</strong>
          </div>
          <div class="action-decision-grid">
            <div class="action-box"><span>基准口径</span><strong data-action-reference data-initial-value="初始持仓权重" data-previous-value="上轮对比权重">初始持仓权重</strong></div>
            <div class="action-box"><span>变化数量</span><strong data-action-count data-initial-value="{_escape(initial_action_summary.count)}" data-previous-value="{_escape(previous_action_summary.count)}">{_escape(initial_action_summary.count)}</strong></div>
            <div class="action-box"><span>执行边界</span><strong data-action-boundary data-initial-value="{_escape(initial_action_summary.boundary)}" data-previous-value="{_escape(previous_action_summary.boundary)}">{_escape(initial_action_summary.boundary)}</strong></div>
          </div>
          <p class="action-detail" data-action-detail data-initial-value="{_escape(initial_action_summary.detail)}" data-previous-value="{_escape(previous_action_summary.detail)}">{_escape(initial_action_summary.detail)}</p>
        </section>
      </div>

    </section>

    <section class="panel pool-metric-panel" aria-label="持仓池与观察池表现指标">
      <h2>持仓池表现指标</h2>
      <p class="pool-ranking-note">同一 Serenity 基金分析排序：#1-#5 为持仓池，#6-#10 为观察池；观察池只进入跟踪和人工复核队列，不作为当前目标配置权重。表内同时展示等级、证据置信度、策略份额、动作/复核、排序原因和希腊字母/风险指标。每次全局数据刷新后按最新净值历史重新计算并写入数据库；入池后涨跌幅使用不可覆盖的首次入池时间，若入池后暂无新净值则显示为空值。Alpha/Treynor 的日均和周均由年化值折算；Theta 使用近20个净值点日均超额并折算周均，不是期权定价 Theta。</p>
      <div class="table-wrap">
        <table class="pool-metric-table">
          <thead>
            <tr>
              <th>基金分析排序</th>
              <th>池</th>
              <th>基金</th>
              <th>等级</th>
              <th>证据置信度</th>
              <th>策略份额</th>
              <th>动作/复核</th>
              <th>排序原因</th>
              <th>入池时间</th>
              <th>指标数据日</th>
              <th>入池后涨跌幅</th>
              <th>近1个月</th>
              <th>近3个月</th>
              <th>近6个月</th>
              <th>Alpha/Beta基准</th>
              <th>希腊字母（日/周）</th>
              <th>风险调整（日/周）</th>
            </tr>
          </thead>
          <tbody>{_pool_metric_rows(pool_metric_rows)}</tbody>
        </table>
      </div>
    </section>

    <section class="panel expansion-candidate-panel" aria-label="扩容观察候选">
      <h2>扩容观察候选</h2>
      <p class="pool-ranking-note">每次刷新会先从全市场公开基金列表自动扩容高成长方向，再补 24 个月净值和申赎/费率规则。这里显示“新增发现但尚未必然进入 Top5”的候选，属于观察与后续排序对象，不等同于当前买入建议。</p>
      <div class="table-wrap">
        <table class="expansion-table">
          <thead>
            <tr>
              <th>新增序号</th>
              <th>基金</th>
              <th>类型</th>
              <th>主题分</th>
              <th>命中主题</th>
              <th>数据补齐</th>
              <th>当前处置</th>
              <th>来源</th>
            </tr>
          </thead>
          <tbody>{_expansion_candidate_rows(expansion_rows)}</tbody>
        </table>
      </div>
    </section>

    {_run_timeline_panel(timeline_events)}
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
    const localServiceOrigins = Array.from({{ length: 31 }}, (_, index) => `http://127.0.0.1:${{8765 + index}}`);
    let activeServiceOrigin = window.location.protocol === "http:" ? window.location.origin : localServiceOrigins[0];
    const localServiceRequiredMessage = "本地服务未启动。请重新打开 Serenity 每日分析.app，或稍等几秒后再试。";
    const candidateServiceOrigins = () => {{
      const origins = [];
      if (window.location.protocol === "http:" || window.location.protocol === "https:") origins.push(window.location.origin);
      origins.push(activeServiceOrigin, ...localServiceOrigins);
      return [...new Set(origins.filter(Boolean))];
    }};
    const fetchApiJson = async (path, options = {{}}) => {{
      let lastError = null;
      for (const origin of candidateServiceOrigins()) {{
        try {{
          const response = await fetch(`${{origin}}${{path}}`, options);
          const raw = await response.text();
          let data = {{}};
          try {{
            data = raw ? JSON.parse(raw) : {{}};
          }} catch {{
            lastError = new Error(localServiceRequiredMessage);
            continue;
          }}
          if (!Object.prototype.hasOwnProperty.call(data, "status")) {{
            lastError = new Error(localServiceRequiredMessage);
            continue;
          }}
          activeServiceOrigin = origin;
          return {{ response, data, origin }};
        }} catch (error) {{
          lastError = error;
        }}
      }}
      throw lastError || new Error(localServiceRequiredMessage);
    }};
    const reloadAfterServerUpdate = (origin = activeServiceOrigin) => {{
      window.setTimeout(() => {{
        const targetOrigin = origin || activeServiceOrigin || localServiceOrigins[0];
        if (window.location.protocol === "file:" || window.location.origin !== targetOrigin) {{
          window.location.href = `${{targetOrigin}}/`;
        }} else {{
          window.location.reload();
        }}
      }}, 500);
    }};
    document.querySelectorAll("[data-refresh]").forEach((button) => {{
      button.addEventListener("click", async () => {{
        const original = button.textContent;
        button.disabled = true;
        button.textContent = "更新中";
        showToast("正在运行 Serenity 全流程并同步最新信息");
        try {{
          const {{ response, data, origin }} = await fetchApiJson("/api/refresh", {{ method: "POST" }});
          if (!response.ok || data.status !== "pass") {{
            throw new Error(data.message || "刷新失败");
          }}
          window.sessionStorage.setItem("serenityRefreshToast", data.message);
          reloadAfterServerUpdate(origin);
        }} catch (error) {{
          const message = error && error.message && error.message !== "Failed to fetch" ? error.message : localServiceRequiredMessage;
          showToast(message);
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
      document.querySelectorAll("[data-action-level], [data-action-reference], [data-action-count], [data-action-boundary], [data-action-detail]").forEach((node) => {{
        node.textContent = node.dataset[`${{mode}}Value`] || "-";
      }});
      document.querySelectorAll("[data-action-class]").forEach((node) => {{
        const nextClass = node.dataset[`${{mode}}Class`] || "flat";
        node.classList.remove("up", "down", "flat", "mixed");
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
    const reviewDatabaseRequiredMessage = "本地服务未启动。请重新打开 Serenity 每日分析.app；复核必须实时写入数据库。";
    const reviewOutcomeLabels = {{
      observe_pool: "放入观察池继续观察",
      exclude_current_observation: "剔除这一轮观察池",
      promote_top5_candidate_pool: "进入 Top 5 候选操作池",
    }};
    const reviewOutcomeKeysByLabel = Object.fromEntries(
      Object.entries(reviewOutcomeLabels).map(([key, label]) => [label, key])
    );
    const reviewApiBacked = () => true;
    const normalizeReviewOutcome = (value) => {{
      if (reviewOutcomeLabels[value]) return value;
      if (reviewOutcomeKeysByLabel[value]) return reviewOutcomeKeysByLabel[value];
      return "observe_pool";
    }};
    const loadReviewLog = async () => {{
      const {{ response, data }} = await fetchApiJson("/api/manual-review", {{ method: "GET" }});
      if (!response.ok || data.status !== "pass") {{
        throw new Error(data.message || "读取复核失败");
      }}
      return data.records || {{}};
    }};
    const saveReviewRecord = async (record) => {{
      const {{ response, data }} = await fetchApiJson("/api/manual-review", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify(record),
      }});
      if (!response.ok || data.status !== "pass") {{
        throw new Error(data.message || "保存复核失败");
      }}
      return data.record || {{ ...record, source: "sqlite" }};
    }};
    const clearReviewRecords = async () => {{
      const {{ response, data }} = await fetchApiJson("/api/manual-review", {{ method: "DELETE" }});
      if (!response.ok || data.status !== "pass") {{
        throw new Error(data.message || "清空复核失败");
      }}
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
      const label = record.outcomeLabel || record.decision || "";
      if (record.refreshStatus === "running") {{
        return `已写入数据库 ${{savedAt}} · 正在重新运行 Serenity 全流程`;
      }}
      return `已保存到数据库 ${{savedAt}}${{label ? ` · ${{label}}` : ""}}`;
    }};
    const waitForReviewRefresh = async (reviewId, state, button, originalText) => {{
      for (let attempt = 0; attempt < 30; attempt += 1) {{
        await new Promise((resolve) => window.setTimeout(resolve, 2000));
        let log = {{}};
        try {{
          log = await loadReviewLog();
        }} catch {{
          continue;
        }}
        const record = log[reviewId];
        if (!record || record.refreshStatus === "running") {{
          if (state) state.textContent = "已写入数据库，正在重新运行 Serenity 全流程";
          continue;
        }}
        if (state) state.textContent = reviewStateText(record);
        if (record.refreshStatus === "error") {{
          if (button) {{
            button.disabled = false;
            button.textContent = originalText || "保存复核";
          }}
          showToast(record.refreshMessage || "已保存到数据库，但同步刷新失败");
          return;
        }}
        window.sessionStorage.setItem(
          "serenityRefreshToast",
          record.refreshMessage || "人工复核已保存到数据库，并已重新运行 Serenity 全流程"
        );
        reloadAfterServerUpdate();
        return;
      }}
      if (button) {{
        button.disabled = false;
        button.textContent = originalText || "保存复核";
      }}
      showToast("已写入数据库，后台刷新仍在运行；稍后请点击刷新查看最新结果");
    }};
    const applyReviewLog = async () => {{
      let log = {{}};
      try {{
        log = await loadReviewLog();
      }} catch (error) {{
        const message = error && error.message && error.message !== "Failed to fetch" ? error.message : reviewDatabaseRequiredMessage;
        showToast(message);
      }}
      document.querySelectorAll("[data-review-item]").forEach((item) => {{
        const record = log[item.dataset.reviewId || ""];
        const decision = item.querySelector("[data-review-decision]");
        const note = item.querySelector("[data-review-note]");
        const state = item.querySelector("[data-review-state]");
        if (record) {{
          if (decision) decision.value = normalizeReviewOutcome(record.outcome || record.decision || decision.value);
          if (note) note.value = record.note || "";
          if (state) state.textContent = reviewStateText(record);
        }} else if (state) {{
          state.textContent = reviewApiBacked() ? "未保存" : "数据库入口不可用";
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
        const originalText = button.textContent;
        const decision = item.querySelector("[data-review-decision]");
        const note = item.querySelector("[data-review-note]");
        const state = item.querySelector("[data-review-state]");
        const savedAt = formatReviewSavedAt();
        const outcome = normalizeReviewOutcome(decision ? decision.value : "observe_pool");
        button.disabled = true;
        button.textContent = "保存中";
        if (state) state.textContent = "正在写入数据库...";
        showToast("正在保存复核到数据库");
        const record = {{
          review_id: item.dataset.reviewId || "",
          run_id: item.dataset.reviewRunId || "",
          outcome,
          decision: reviewOutcomeLabels[outcome],
          note: note ? note.value : "",
          savedAt,
        }};
        try {{
          const saved = await saveReviewRecord(record);
          if (state) state.textContent = reviewStateText(saved);
          if (saved.refreshStatus === "running") {{
            button.textContent = "刷新中";
            showToast("已写入数据库，正在重新运行 Serenity 全流程");
            void waitForReviewRefresh(String(saved.review_id || record.review_id), state, button, originalText);
            return;
          }}
          if (saved.refreshTriggered) {{
            if (saved.refreshStatus === "error") {{
              button.disabled = false;
              button.textContent = originalText;
              showToast(saved.refreshMessage || "已保存到数据库，但同步刷新失败");
            }} else {{
              window.sessionStorage.setItem(
                "serenityRefreshToast",
                saved.refreshMessage || "人工复核已保存到数据库，并已重新运行 Serenity 全流程"
              );
              reloadAfterServerUpdate();
            }}
          }} else {{
            button.disabled = false;
            button.textContent = originalText;
            showToast(`人工复核已保存到数据库：${{saved.outcomeLabel || saved.decision || "已保存"}}`);
          }}
        }} catch (error) {{
          const message = error && error.message && error.message !== "Failed to fetch" ? error.message : reviewDatabaseRequiredMessage;
          if (state) state.textContent = "保存失败，未写入数据库";
          button.disabled = false;
          button.textContent = originalText;
          showToast(message);
        }}
      }});
    }});
    document.querySelectorAll("[data-copy-review-log]").forEach((button) => {{
      button.addEventListener("click", async () => {{
        let log = {{}};
        try {{
          log = await loadReviewLog();
        }} catch (error) {{
          const message = error && error.message && error.message !== "Failed to fetch" ? error.message : reviewDatabaseRequiredMessage;
          showToast(message);
        }}
        const lines = Array.from(document.querySelectorAll("[data-review-item]")).map((item) => {{
          const id = item.dataset.reviewId || "";
          const title = item.querySelector(".review-item-head strong")?.textContent?.trim() || id;
          const reason = item.querySelector(".review-reason")?.textContent?.trim() || "-";
          const outcome = normalizeReviewOutcome(item.querySelector("[data-review-decision]")?.value || log[id]?.outcome || log[id]?.decision);
          const decision = reviewOutcomeLabels[outcome];
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
            if (decision) decision.value = "observe_pool";
            if (state) state.textContent = "未保存";
          }});
          showToast("数据库复核记录已清空");
        }} catch (error) {{
          const message = error && error.message && error.message !== "Failed to fetch" ? error.message : reviewDatabaseRequiredMessage;
          showToast(message);
        }}
      }});
    }});
    void applyReviewLog();

    const usageGuideModal = document.getElementById("usage-guide-modal");
    const guideNavButtons = Array.from(document.querySelectorAll("[data-guide-target]"));
    const setActiveGuideTarget = (targetId) => {{
      guideNavButtons.forEach((button) => {{
        button.classList.toggle("active", button.dataset.guideTarget === targetId);
      }});
    }};
    const openUsageGuide = () => {{
      if (usageGuideModal) usageGuideModal.hidden = false;
      setActiveGuideTarget("guide-overview");
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
    guideNavButtons.forEach((button) => {{
      button.addEventListener("click", () => {{
        const targetId = button.dataset.guideTarget;
        const target = targetId ? document.getElementById(targetId) : null;
        if (!target) return;
        setActiveGuideTarget(targetId);
        target.scrollIntoView({{ block: "start", behavior: "smooth" }});
      }});
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
    const formatFeeSchedule = (value) => {{
      const raw = String(value ?? "-").trim();
      if (!raw || raw === "-") return "-";
      return raw
        .split(/[；;]/)
        .map((part) => part.trim())
        .filter(Boolean)
        .join("\\n");
    }};
    const formatFundValue = (key, value) => {{
      if (key.includes("Schedule")) return formatFeeSchedule(value);
      return String(value ?? "-");
    }};
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
      ["来源链接", "sourceUrl"]
    ];
    const fundLibraryTableColumns = [
      ["代码", "code"],
      ["基金名称", "name"],
      ["上次进入候选池时间", "lastTop5EntryTime"],
      ["当前进入候选池天数", "currentCandidateDays"],
      ["当前状态", "candidateStatus"],
      ["费用/状态快照时间", "ruleSnapshotTime"],
      ["申购状态", "subscriptionStatus"],
      ["赎回状态", "redemptionStatus"],
      ["交易截止时间", "cutoffTime"],
      ["确认周期", "confirmLag"],
      ["赎回到账", "redeemLag"],
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
    ];
    const fundLibrarySummaryLabels = [
      ["当前状态", "candidateStatus"],
      ["费用快照", "ruleSnapshotTime"],
      ["入池天数", "currentCandidateDays"],
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
          valueNode.textContent = formatFundValue(key, info[key]);
          if (key.includes("Schedule")) {{
            valueNode.classList.add("multi-line-value");
          }}
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
          cell.colSpan = fundLibraryTableColumns.length + 1;
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
        schedule.innerHTML = "";
        [
          ["申购费分档", formatFeeSchedule(info.subscriptionFeeSchedule)],
          ["赎回费分档", formatFeeSchedule(info.redemptionFeeSchedule)],
          ["费率说明", info.feeScheduleNote || "-"],
        ].forEach(([label, value]) => {{
          const labelNode = document.createElement("strong");
          labelNode.textContent = label;
          const valueNode = document.createElement("span");
          valueNode.textContent = String(value || "-");
          schedule.appendChild(labelNode);
          schedule.appendChild(valueNode);
        }});
        card.appendChild(schedule);
        fundLibraryBody.appendChild(card);

        if (fundLibraryTableBody) {{
          const row = document.createElement("tr");
          fundLibraryTableColumns.forEach(([, key]) => {{
            const cell = document.createElement("td");
            cell.textContent = formatFundValue(key, info[key]);
            if (key.includes("Schedule")) {{
              cell.classList.add("fee-schedule-cell");
            }}
            if (key === "feeScheduleNote") {{
              cell.classList.add("fee-note-cell");
            }}
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
      setFundLibraryMode("table");
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
      button.addEventListener("click", () => setFundLibraryMode(button.dataset.fundLibraryMode || "table"));
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
    ports = ",".join(str(port) for port in range(8765, 8796))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>正在启动 Serenity 每日分析</title>
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
    .status {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--accent);
      font-weight: 700;
      margin: 12px 0;
    }}
    .spinner {{
      width: 16px;
      height: 16px;
      border: 2px solid rgba(11, 111, 123, 0.18);
      border-top-color: var(--accent);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
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
      <div class="status"><span class="spinner" aria-hidden="true"></span><span id="status">正在启动本地服务...</span></div>
      <p>通常几秒内会自动打开首页；服务启动后会跳转到可实时刷新和写入数据库的入口。</p>
      <p><a id="retry" href="#">立即重试</a></p>
    </section>
  </main>
  <script>
    const ports = [{ports}];
    const staticPortalUrl = "{_escape(portal_url)}";
    const statusNode = document.getElementById("status");
    const retry = document.getElementById("retry");
    let attempt = 0;
    const checkOrigin = async (origin) => {{
      const controller = new AbortController();
      const timer = window.setTimeout(() => controller.abort(), 450);
      try {{
        const response = await fetch(`${{origin}}/api/health`, {{
          cache: "no-store",
          signal: controller.signal,
        }});
        if (!response.ok) return false;
        const data = await response.json();
        return data && data.status === "ok";
      }} catch {{
        return false;
      }} finally {{
        window.clearTimeout(timer);
      }}
    }};
    const firstHealthyOrigin = () => new Promise((resolve) => {{
      let remaining = ports.length;
      for (const port of ports) {{
        const origin = `http://127.0.0.1:${{port}}`;
        checkOrigin(origin).then((healthy) => {{
          if (healthy) {{
            resolve(origin);
            return;
          }}
          remaining -= 1;
          if (remaining <= 0) resolve(null);
        }});
      }}
    }});
    const findService = async () => {{
      attempt += 1;
      statusNode.textContent = `正在启动本地服务... 第 ${{attempt}} 次检查`;
      const origin = await firstHealthyOrigin();
      if (origin) {{
        statusNode.textContent = "服务已启动，正在打开首页...";
        window.location.replace(`${{origin}}/`);
        return;
      }}
      if (attempt >= 60) {{
        statusNode.textContent = "服务仍在启动；请稍等或重新打开 Serenity 每日分析.app。";
      }}
      window.setTimeout(findService, 650);
    }};
    retry.addEventListener("click", (event) => {{
      event.preventDefault();
      void findService();
    }});
    void findService();
  </script>
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
    bootstrap_target = str((portal_path.parent / "downloads-entry.html").resolve()).replace('"', '\\"')
    root_target = str(root_dir.resolve()).replace('"', '\\"')
    python_target = sys.executable.replace('"', '\\"')
    executable = macos_dir / "open-serenity"
    executable.write_text(
        f"""#!/bin/sh
ROOT="{root_target}"
PYTHON="{python_target}"
BOOTSTRAP="{bootstrap_target}"
PORT="${{SERENITY_APP_PORT:-8765}}"
URL="http://127.0.0.1:$PORT/"
HEALTH="http://127.0.0.1:$PORT/api/health"
LOG_DIR="$HOME/Library/Logs/SerenityDailyAnalysis"
LOG_FILE="$LOG_DIR/application-server.log"
SERVER_PID=""
mkdir -p "$LOG_DIR"
cd "$ROOT" || exit 1
open "$BOOTSTRAP" >/dev/null 2>&1 || true
is_serenity_health() {{
  /usr/bin/curl --connect-timeout 0.2 --max-time 0.5 -fsS "$1" 2>/dev/null | /usr/bin/grep -q '"status": "ok"'
}}
if ! is_serenity_health "$HEALTH"; then
  for CANDIDATE in "$PORT" $(seq 8765 8795); do
    CANDIDATE_HEALTH="http://127.0.0.1:$CANDIDATE/api/health"
    if is_serenity_health "$CANDIDATE_HEALTH"; then
      PORT="$CANDIDATE"
      break
    fi
    if ! /usr/bin/nc -z 127.0.0.1 "$CANDIDATE" >/dev/null 2>&1; then
      PORT="$CANDIDATE"
      break
    fi
  done
  URL="http://127.0.0.1:$PORT/"
  HEALTH="http://127.0.0.1:$PORT/api/health"
fi
if ! is_serenity_health "$HEALTH"; then
  "$PYTHON" -m app.cli application-server --host 127.0.0.1 --port "$PORT" --disable-autoscheduler >> "$LOG_FILE" 2>&1 </dev/null &
  SERVER_PID="$!"
  for _ in $(seq 1 60); do
    is_serenity_health "$HEALTH" && break
    sleep 0.5
  done
fi
if is_serenity_health "$HEALTH"; then
  open "$URL" >/dev/null 2>&1 || true
else
  /usr/bin/osascript -e 'display notification "本地服务启动失败，请查看 ~/Library/Logs/SerenityDailyAnalysis/application-server.log" with title "Serenity 每日分析"' >/dev/null 2>&1 || true
fi
if [ -n "$SERVER_PID" ]; then
  wait "$SERVER_PID"
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


def build_application_portal(settings: Settings, *, install_apps: bool = True) -> dict[str, object]:
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        runs = _latest_runs(conn, limit=12)
        current_run = runs[0] if runs else None
        previous_run = runs[1] if len(runs) > 1 else None
        current_pool = _recommendations_for_run(conn, current_run.run_id, 1, 10) if current_run else []
        current_holdings = [row for row in current_pool if row.rank <= 5]
        observation_pool = [row for row in current_pool if 6 <= row.rank <= 10]
        previous_holdings = _holdings_for_run(conn, previous_run.run_id) if previous_run else []
        run_timeline = _run_timeline_events(conn, runs)
        manual_review_items = _manual_review_items(conn, current_run.run_id if current_run else None)
        resolved_review_keys = _resolved_review_code_reason_keys(conn)
        baseline_time_bj = _baseline_reference_time(conn, current_run.run_id if current_run else None)
        expansion_candidates = _expansion_candidates_for_run(conn, current_run.run_id if current_run else None)
        expansion_holdings = [
            PortalHolding(
                rank=10_000 + item.sequence,
                code=item.code,
                name=item.name,
                grade="Watch",
                score=0.0,
                target_weight=0.0,
                current_weight=0.0,
                action_label="Maintain",
                trigger_reason="全市场扩容观察候选",
            )
            for item in expansion_candidates
        ]
        fund_library = _fund_library_for_run(
            conn,
            current_run.run_id if current_run else None,
            current_holdings + observation_pool + previous_holdings + expansion_holdings,
        )
        pool_metrics = _pool_performance_metrics(
            settings,
            conn,
            current_holdings + observation_pool,
            current_run,
            resolved_review_keys,
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
            observation_pool=observation_pool,
            baseline_time_bj=baseline_time_bj,
            fund_library=fund_library,
            run_timeline=run_timeline,
            manual_review_items=manual_review_items,
            resolved_review_keys=resolved_review_keys,
            pool_metrics=pool_metrics,
            expansion_candidates=expansion_candidates,
        ),
        encoding="utf-8",
    )
    downloads_entry_path.write_text(render_downloads_entry(portal_path), encoding="utf-8")
    legacy_removed: list[str] = []
    if install_apps:
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
        "pool_metric_rows": len(pool_metrics),
        "expansion_candidate_rows": len(expansion_candidates),
    }
