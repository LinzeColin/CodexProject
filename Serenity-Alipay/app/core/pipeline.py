from __future__ import annotations

import json
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.adapters import moomoo_adapter
from app.adapters.alipay_importer import read_positions_csv
from app.adapters.mail_notifier import send_with_apple_mail, write_mail_ready_draft
from app.adapters.manual_sources import Candidate, load_candidates, load_fund_rules, load_price_history
from app.config import Settings
from app.core.candidate_universe_expander import expand_candidate_universe
from app.core.comparison import persist_comparisons
from app.core.discipline import (
    deviation_events,
    persist_rebalance_events,
    single_position_overexpansion_events,
)
from app.core.fund_rule_autofill import autofill_fund_rules
from app.core.fund_nav_history_collector import collect_fund_nav_history
from app.core.indicator_discipline import calculate_indicator_days, evaluate_exclusion_rule
from app.core.metrics import calculate_metrics
from app.core.mail_policy import should_send_mail_for_run, suppressed_no_material_change_message
from app.core.reporting import (
    render_markdown_report,
    render_notification,
    render_notification_html,
    render_offline_html,
    render_offline_index,
    write_text,
)
from app.core.run_visibility import display_run_time_with_backfill_note
from app.core.scoring import ScoreResult, score_candidate
from app.core.time_display import format_display_time
from app.db import connect, init_db, insert_row, record_asset_pool_entries, upsert_asset
from app.scheduler import SlotTimes, slot_times


ACTION_POOL_SIZE = 5


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _run_id(slot: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"sda_{stamp}_{slot.lower()}_{uuid4().hex[:8]}"


def _source_id(run_id: str, asset_code: str, suffix: str) -> str:
    return f"{run_id}_{asset_code}_{suffix}".replace("/", "_")


def _action_pool_rows(recommendations: list[dict[str, object]], limit: int = ACTION_POOL_SIZE) -> list[dict[str, object]]:
    return [
        row
        for row in recommendations
        if int(row.get("rank") or 0) > 0 and int(row.get("rank") or 0) <= limit
    ]


def _action_pool_requires_manual_review(recommendations: list[dict[str, object]]) -> bool:
    return any(bool(row.get("manual_review_required")) for row in _action_pool_rows(recommendations))


def _asset_row(candidate: Candidate) -> dict[str, object]:
    return {
        "asset_id": candidate.asset_id,
        "asset_code": candidate.asset_code,
        "asset_name": candidate.asset_name,
        "asset_type": candidate.asset_type,
        "market": candidate.market,
        "fund_company": candidate.fund_company,
        "risk_level": candidate.risk_level,
        "is_excluded": int(candidate.is_excluded),
        "exclusion_reason": candidate.exclusion_reason,
    }


def import_alipay_csv(settings: Settings, csv_path: Path) -> dict[str, object]:
    init_db(settings.db_path)
    result = read_positions_csv(csv_path)
    run_id = f"alipay_import_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid4().hex[:8]}"
    created_at = _now_iso()
    with connect(settings.db_path) as conn:
        insert_row(
            conn,
            "run_log",
            {
                "run_id": run_id,
                "run_time_bj": created_at,
                "run_time_au": created_at,
                "schedule_slot": "IMPORT",
                "model_profile": settings.model_profile,
                "status": "success",
                "data_quality_status": "imported",
                "notification_status": "not_applicable",
                "notes": f"Imported {len(result.rows)} Alipay rows from {csv_path}",
                "report_path": None,
                "offline_html_path": None,
                "created_at": created_at,
            },
        )
        source_id = f"{run_id}_alipay_csv"
        insert_row(
            conn,
            "source_log",
            {
                "source_id": source_id,
                "run_id": run_id,
                "asset_id": None,
                "source_name": "Alipay CSV import",
                "source_type": "alipay_import",
                "source_priority": 2,
                "url_or_path": str(csv_path),
                "observed_at": created_at,
                "fetched_at": created_at,
                "evidence_level": "Strong",
                "field_list": "current_amount,current_weight,cost_basis,unrealized_pnl",
                "fallback_aggregated": 0,
                "conflict_group": None,
            },
        )
        for row in result.rows:
            asset_id = str(row["asset_code"])
            conn.execute(
                """
                INSERT INTO asset_master (
                    asset_id, asset_code, asset_name, asset_type, market,
                    fund_company, risk_level, is_excluded, exclusion_reason
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(asset_code) DO NOTHING
                """,
                (
                    asset_id,
                    row["asset_code"],
                    row["asset_name"],
                    "off_platform_fund",
                    None,
                    None,
                    None,
                    0,
                    None,
                ),
            )
            insert_row(
                conn,
                "position_snapshot",
                {
                    "run_id": run_id,
                    "asset_id": asset_id,
                    "platform": row["platform"],
                    "current_amount": row["current_amount"],
                    "current_weight": row["current_weight"],
                    "cost_basis": row["cost_basis"],
                    "unrealized_pnl": row["unrealized_pnl"],
                    "imported_by": "csv",
                    "source_id": source_id,
                },
            )
    return {"run_id": run_id, "rows": len(result.rows), "warnings": result.warnings}


def _latest_positions(conn) -> dict[str, float]:
    latest_import = conn.execute(
        "SELECT run_id FROM run_log WHERE schedule_slot='IMPORT' ORDER BY created_at DESC, rowid DESC LIMIT 1"
    ).fetchone()
    if not latest_import:
        return {}
    rows = conn.execute(
        "SELECT asset_id, current_weight FROM position_snapshot WHERE run_id=?",
        (latest_import["run_id"],),
    ).fetchall()
    return {row["asset_id"]: float(row["current_weight"] or 0.0) for row in rows}


def _latest_baseline_reference(conn) -> tuple[dict[str, float], str | None]:
    latest_baseline = conn.execute(
        """
        SELECT b.run_id
        FROM baseline_snapshot b
        JOIN run_log r ON r.run_id=b.run_id
        WHERE b.baseline_kind='serenity_baseline'
        ORDER BY r.run_time_bj DESC, r.created_at DESC, b.rowid DESC
        LIMIT 1
        """
    ).fetchone()
    if not latest_baseline:
        return {}, None
    rows = conn.execute(
        """
        SELECT asset_id, baseline_weight
        FROM baseline_snapshot
        WHERE run_id=? AND baseline_kind='serenity_baseline'
        """,
        (latest_baseline["run_id"],),
    ).fetchall()
    return {row["asset_id"]: float(row["baseline_weight"] or 0.0) for row in rows}, latest_baseline["run_id"]


def _serenity_priority(row: dict[str, object]) -> int:
    return int(row.get("candidate_index", 1_000_000))


def _confidence_multiplier(score: ScoreResult) -> float:
    confidence = max(0.0, min(1.0, score.total_score / 100.0))
    return 0.85 + (0.15 * confidence)


def _ranked_recommendation_rows(scored_rows: list[dict[str, object]], limit: int = 5) -> list[dict[str, object]]:
    eligible = [row for row in scored_rows if row["score"].grade != "Block"]
    return sorted(
        eligible,
        key=lambda row: (
            int(row["score"].manual_review_required),
            _serenity_priority(row),
            -row["score"].total_score,
            row["candidate"].asset_code,
        ),
    )[:limit]


def _target_weights(scored_rows: list[dict[str, object]]) -> dict[str, float]:
    top = _ranked_recommendation_rows(scored_rows)
    raw: dict[str, float] = {}
    for index, row in enumerate(top):
        # Serenity priority is primary. Score only applies a bounded confidence modifier.
        serenity_base = 0.82 ** index
        raw[row["candidate"].asset_id] = serenity_base * _confidence_multiplier(row["score"])
    raw_total = sum(raw.values())
    if not top or raw_total <= 0:
        return {}
    raw = {asset_id: weight / raw_total for asset_id, weight in raw.items()}
    capped = {asset_id: min(weight, 0.30) for asset_id, weight in raw.items()}
    cap_total = sum(capped.values())
    return {asset_id: weight / cap_total for asset_id, weight in capped.items()} if cap_total else {}


def _action_with_deviation(
    score: ScoreResult, current_weight: float, target_weight: float, settings: Settings
) -> tuple[str, str]:
    deviation = target_weight - current_weight
    if score.grade == "Block":
        return score.action_label, score.trigger_reason
    if score.manual_review_required:
        return "Manual Review", score.trigger_reason
    if abs(deviation) <= settings.deviation_threshold:
        return "Maintain", score.trigger_reason
    if deviation > 0:
        action = "Increase" if score.grade == "Action-Ready" else "Pause New"
        return action, f"target/current deviation {deviation:.2%} exceeds {settings.deviation_threshold:.2%}"
    return "Reduce", f"target/current deviation {deviation:.2%} exceeds {settings.deviation_threshold:.2%}"


def _write_offline_index(conn, settings: Settings) -> Path:
    rows = conn.execute(
        """
        SELECT run_id, schedule_slot, run_time_bj, run_time_au, created_at,
               status, data_quality_status, report_path, offline_html_path
        FROM run_log
        WHERE report_path IS NOT NULL AND offline_html_path IS NOT NULL
        ORDER BY run_time_bj DESC, created_at DESC, rowid DESC
        LIMIT 100
        """
    ).fetchall()
    index_rows = []
    for row in rows[:50]:
        report_path = Path(row["report_path"])
        html_path = Path(row["offline_html_path"])
        index_rows.append(
            {
                "run_id": row["run_id"],
                "slot": row["schedule_slot"],
                "run_time_bj": display_run_time_with_backfill_note(
                    row["run_time_bj"],
                    row["created_at"],
                    zone=settings.timezone_primary,
                ),
                "run_time_au": format_display_time(row["run_time_au"], settings.timezone_secondary),
                "status": row["status"],
                "quality": row["data_quality_status"],
                "md_file": report_path.name,
                "html_file": html_path.name,
            }
        )
    index_path = settings.reports_dir / "index.html"
    write_text(index_path, render_offline_index(index_rows))
    return index_path


def run_slot(
    settings: Settings,
    slot: str,
    dry_run: bool = True,
    send_mail: bool = False,
    run_date: date | None = None,
    run_datetime_bj: datetime | None = None,
) -> dict[str, object]:
    init_db(settings.db_path)
    if run_datetime_bj:
        primary_zone = ZoneInfo(settings.timezone_primary)
        secondary_zone = ZoneInfo(settings.timezone_secondary)
        beijing_dt = run_datetime_bj.astimezone(primary_zone) if run_datetime_bj.tzinfo else run_datetime_bj.replace(tzinfo=primary_zone)
        times = SlotTimes(slot=slot.upper(), beijing=beijing_dt, secondary=beijing_dt.astimezone(secondary_zone))
    else:
        times = slot_times(slot, run_date, primary_tz=settings.timezone_primary, secondary_tz=settings.timezone_secondary)
    run_id = _run_id(slot)
    created_at = _now_iso()
    run_time_bj = times.beijing.isoformat(timespec="seconds")
    run_time_au = times.secondary.isoformat(timespec="seconds")

    if dry_run or not settings.candidate_universe_nav_backfill_enabled:
        fund_nav_history_collection: dict[str, object] = {
            "generated_at": created_at,
            "status": "skipped",
            "message": "dry_run or runtime NAV refresh disabled",
            "applied": False,
            "apply_mode": "none",
        }
    else:
        try:
            fund_nav_history_collection = collect_fund_nav_history(
                settings,
                timeout_seconds=settings.candidate_universe_fetch_timeout_seconds,
                workers=4,
                write_output=True,
                apply=True,
                allow_partial_apply=True,
                incremental=True,
            )
        except Exception as exc:
            fund_nav_history_collection = {
                "generated_at": created_at,
                "status": "warn",
                "message": f"runtime NAV refresh failed: {exc}",
                "applied": False,
                "apply_mode": "none",
            }

    base_candidates_path = settings.manual_dir / "candidates.csv"
    candidate_universe_expansion = expand_candidate_universe(
        settings,
        base_candidates_path=base_candidates_path,
    )
    candidates_path = Path(str(candidate_universe_expansion.get("expanded_candidates_path") or base_candidates_path))
    rules_path = settings.manual_dir / "fund_rules.csv"
    prices_path = Path(str(candidate_universe_expansion.get("expanded_price_history_path") or settings.manual_dir / "price_history.csv"))
    benchmark_prices_path = settings.manual_dir / "benchmark_price_history.csv"
    candidates = load_candidates(candidates_path)
    fund_rules = load_fund_rules(rules_path)
    price_history = load_price_history(prices_path)
    benchmark_history = load_price_history(benchmark_prices_path) if benchmark_prices_path.exists() else price_history
    fund_rules, fund_rule_autofill = autofill_fund_rules(settings, candidates, fund_rules)
    shanghai_returns = calculate_metrics(benchmark_history.get("000001.SH", [])).returns
    sp500_returns = calculate_metrics(benchmark_history.get("SPX", [])).returns
    moomoo = moomoo_adapter.healthcheck(
        settings=settings,
        auto_start_opend=settings.opend_auto_start_enabled and not dry_run,
        keep_auto_started_opend=settings.opend_keep_auto_started,
        opend_wait_seconds=settings.opend_wait_seconds,
    )

    scored_rows: list[dict[str, object]] = []
    with connect(settings.db_path) as conn:
        insert_row(
            conn,
            "run_log",
            {
                "run_id": run_id,
                "run_time_bj": run_time_bj,
                "run_time_au": run_time_au,
                "schedule_slot": slot.upper(),
                "model_profile": settings.model_profile,
                "status": "started",
                "data_quality_status": "pending",
                "notification_status": "pending",
                "notes": f"dry_run={dry_run}; offline_webpage=true",
                "report_path": None,
                "offline_html_path": None,
                "created_at": created_at,
            },
        )
        insert_row(
            conn,
            "audit_log",
            {
                "run_id": run_id,
                "event_type": "moomoo_healthcheck",
                "severity": "info" if moomoo.available else "warn",
                "message": moomoo.detail,
                "context_json": json.dumps(
                    {
                        "status": moomoo.status,
                        "sdk_available": moomoo.sdk_available,
                        "opend_lifecycle": moomoo.opend_lifecycle,
                        "cleanup": moomoo.cleanup,
                    },
                    ensure_ascii=False,
                    default=str,
                ),
                "created_at": created_at,
            },
        )
        insert_row(
            conn,
            "audit_log",
            {
                "run_id": run_id,
                "event_type": "fund_nav_history_collection",
                "severity": (
                    "info"
                    if fund_nav_history_collection.get("status") in {"pass", "skipped"}
                    else "warn"
                ),
                "message": (
                    f"applied={fund_nav_history_collection.get('applied')}; "
                    f"mode={fund_nav_history_collection.get('apply_mode')}; "
                    f"assets={len(fund_nav_history_collection.get('applied_asset_codes') or [])}"
                ),
                "context_json": json.dumps(fund_nav_history_collection, ensure_ascii=False, default=str),
                "created_at": created_at,
            },
        )
        insert_row(
            conn,
            "audit_log",
            {
                "run_id": run_id,
                "event_type": "candidate_universe_expansion",
                "severity": "info" if candidate_universe_expansion.get("status") == "pass" else "warn",
                "message": str(candidate_universe_expansion.get("message") or ""),
                "context_json": json.dumps(candidate_universe_expansion, ensure_ascii=False, default=str),
                "created_at": created_at,
            },
        )
        insert_row(
            conn,
            "audit_log",
            {
                "run_id": run_id,
                "event_type": "fund_rule_autofill",
                "severity": "info" if fund_rule_autofill.get("status") == "pass" else "warn",
                "message": (
                    f"filled={fund_rule_autofill.get('filled_count', 0)}; "
                    f"attempted={fund_rule_autofill.get('attempted_count', 0)}"
                ),
                "context_json": json.dumps(fund_rule_autofill, ensure_ascii=False, default=str),
                "created_at": created_at,
            },
        )
        baseline_reference, baseline_reference_run_id = _latest_baseline_reference(conn)
        if baseline_reference_run_id:
            reference_weights = baseline_reference
            reference_mode = "previous_serenity_baseline"
        else:
            reference_weights = {}
            reference_mode = "zero_start_first_baseline"
        insert_row(
            conn,
            "audit_log",
            {
                "run_id": run_id,
                "event_type": "baseline_reference",
                "severity": "info",
                "message": (
                    f"Discipline comparison uses {reference_mode}; "
                    "Alipay current holdings are optional reference data, not a production prerequisite."
                ),
                "context_json": json.dumps(
                    {"reference_mode": reference_mode, "reference_run_id": baseline_reference_run_id},
                    ensure_ascii=False,
                ),
                "created_at": created_at,
            },
        )
        conn.commit()

        for candidate_index, candidate in enumerate(candidates):
            upsert_asset(conn, _asset_row(candidate))
            candidate_source_id = _source_id(run_id, candidate.asset_code, "candidate")
            insert_row(
                conn,
                "source_log",
                {
                    "source_id": candidate_source_id,
                    "run_id": run_id,
                    "asset_id": candidate.asset_id,
                    "source_name": candidate.source_name or "manual candidate universe",
                    "source_type": candidate.source_type or "manual",
                    "source_priority": 3 if candidate.source_type == "official" else 5,
                    "url_or_path": candidate.source_url or str(candidates_path),
                    "observed_at": candidate.as_of,
                    "fetched_at": created_at,
                    "evidence_level": candidate.evidence_level,
                    "field_list": "candidate,source_count,evidence_level,missing_days",
                    "fallback_aggregated": int(candidate.fallback_aggregated),
                    "conflict_group": "candidate_conflict" if candidate.conflict_flag else None,
                },
            )

            rule = fund_rules.get(candidate.asset_code)
            rule_source_id = None
            if rule:
                rule_source_id = _source_id(run_id, candidate.asset_code, "rule")
                insert_row(
                    conn,
                    "source_log",
                    {
                        "source_id": rule_source_id,
                        "run_id": run_id,
                        "asset_id": candidate.asset_id,
                        "source_name": rule.source_name,
                        "source_type": rule.source_type,
                        "source_priority": rule.source_priority,
                        "url_or_path": rule.url_or_path,
                        "observed_at": rule.as_of,
                        "fetched_at": created_at,
                        "evidence_level": rule.evidence_level,
                        "field_list": "subscription_status,redemption_status,fees,cutoff,confirm_lag,platform_trade_advisory",
                        "fallback_aggregated": int(rule.fallback_aggregated),
                        "conflict_group": None,
                    },
                )
                insert_row(
                    conn,
                    "fund_rule_snapshot",
                    {
                        "run_id": run_id,
                        "asset_id": candidate.asset_id,
                        "subscription_status": rule.subscription_status,
                        "redemption_status": rule.redemption_status,
                        "cutoff_time": rule.cutoff_time,
                        "confirm_lag": rule.confirm_lag,
                        "redeem_lag": rule.redeem_lag,
                        "subscription_fee": rule.subscription_fee,
                        "redemption_fee": rule.redemption_fee,
                        "management_fee": rule.management_fee,
                        "custody_fee": rule.custody_fee,
                        "sales_service_fee": rule.sales_service_fee,
                        "min_purchase_amount": rule.min_purchase_amount,
                        "subscription_fee_schedule": rule.subscription_fee_schedule,
                        "redemption_fee_schedule": rule.redemption_fee_schedule,
                        "fee_schedule_as_of": rule.fee_schedule_as_of,
                        "fee_schedule_note": rule.fee_schedule_note,
                        "alipay_trade_status": rule.alipay_trade_status,
                        "moomoo_trade_status": rule.moomoo_trade_status,
                        "platform_trade_note": rule.platform_trade_note,
                        "source_id": rule_source_id,
                    },
                )

            points = price_history.get(candidate.asset_code, [])
            for point in points:
                insert_row(
                    conn,
                    "market_kline_snapshot",
                    {
                        "run_id": run_id,
                        "asset_id": candidate.asset_id,
                        "bar_interval": "1d",
                        "start_time": point.date.isoformat(),
                        "end_time": point.date.isoformat(),
                        "open": point.close,
                        "high": point.close,
                        "low": point.close,
                        "close": point.close,
                        "volume": None,
                        "turnover": None,
                        "source_id": candidate_source_id,
                    },
                )
            metrics = calculate_metrics(points)
            if points:
                latest = points[-1]
                previous = points[-2] if len(points) > 1 else latest
                daily_return = (latest.close / previous.close - 1.0) if previous.close else None
                insert_row(
                    conn,
                    "fund_nav_snapshot",
                    {
                        "run_id": run_id,
                        "asset_id": candidate.asset_id,
                        "nav_date": latest.date.isoformat(),
                        "nav": latest.close,
                        "accumulated_nav": latest.close,
                        "daily_return": daily_return,
                        "nav_source_id": candidate_source_id,
                        "freshness_status": "fresh" if candidate.missing_nav_days <= 2 else "stale",
                    },
                )
            indicator_days = calculate_indicator_days(candidate, points, benchmark_history)
            for indicator in indicator_days:
                insert_row(
                    conn,
                    "asset_indicator_snapshot",
                    {
                        "run_id": run_id,
                        "asset_id": candidate.asset_id,
                        "metric_date": indicator.metric_date.isoformat(),
                        "alpha": indicator.alpha,
                        "beta": indicator.beta,
                        "gamma": indicator.gamma,
                        "theta": indicator.theta,
                        "vega": indicator.vega,
                        "sharpe": indicator.sharpe,
                        "sortino": indicator.sortino,
                        "calmar": indicator.calmar,
                        "treynor": indicator.treynor,
                        "negative_indicator_count": indicator.negative_indicator_count,
                        "total_indicator_count": indicator.total_indicator_count,
                        "benchmark_code": indicator.benchmark_code,
                        "benchmark_label": indicator.benchmark_label,
                        "created_at": created_at,
                    },
                )
            exclusion_decision = evaluate_exclusion_rule(indicator_days)
            score = score_candidate(candidate, rule, metrics, shanghai_returns, sp500_returns, settings)
            if exclusion_decision.should_exclude:
                score = replace(
                    score,
                    total_score=min(score.total_score, 54.0),
                    grade="Block",
                    hard_block_reason=exclusion_decision.reason,
                    action_label="Clear",
                    trigger_reason=exclusion_decision.reason or "indicator exclusion discipline",
                    manual_review_required=True,
                )
                insert_row(
                    conn,
                    "asset_exclusion_event",
                    {
                        "run_id": run_id,
                        "asset_id": candidate.asset_id,
                        "rule_window_days": exclusion_decision.rule_window_days or 0,
                        "negative_count": exclusion_decision.negative_count,
                        "threshold_count": exclusion_decision.threshold_count,
                        "total_count": exclusion_decision.total_count,
                        "action": "Block/Clear",
                        "reason": exclusion_decision.reason or "indicator exclusion discipline",
                        "created_at": created_at,
                    },
                )
            scored_rows.append(
                {
                    "candidate_index": candidate_index,
                    "candidate": candidate,
                    "rule": rule,
                    "metrics": metrics,
                    "score": score,
                }
            )
            insert_row(
                conn,
                "score_snapshot",
                {
                    "run_id": run_id,
                    "asset_id": candidate.asset_id,
                    "total_score": score.total_score,
                    "data_score": score.data_score,
                    "timeliness_score": score.timeliness_score,
                    "source_score": score.source_score,
                    "return_score": score.return_score,
                    "risk_score": score.risk_score,
                    "executable_score": score.executable_score,
                    "evidence_coverage": score.evidence_coverage,
                    "grade": score.grade,
                    "hard_block_reason": score.hard_block_reason,
                },
            )
            for field in score.missing_fields:
                insert_row(
                    conn,
                    "missing_data_log",
                    {
                        "run_id": run_id,
                        "asset_id": candidate.asset_id,
                        "field_name": field,
                        "severity": "warn",
                        "reason": "required field missing for Action-Ready scoring",
                        "created_at": created_at,
                    },
                )
            if score.manual_review_required:
                insert_row(
                    conn,
                    "manual_review_queue",
                    {
                        "run_id": run_id,
                        "asset_id": candidate.asset_id,
                        "reason": score.trigger_reason,
                        "action_blocked": "No-New-Order",
                        "status": "open",
                        "created_at": created_at,
                    },
                )
            if candidate.conflict_flag:
                insert_row(
                    conn,
                    "conflict_log",
                    {
                        "run_id": run_id,
                        "asset_id": candidate.asset_id,
                        "field_name": "source_chain",
                        "conflict_note": "manual candidate file marks source conflict",
                        "created_at": created_at,
                    },
                )
            conn.commit()

        target_weights = _target_weights(scored_rows)
        ranked = _ranked_recommendation_rows(scored_rows, limit=10)
        recommendations: list[dict[str, object]] = []
        for rank, row in enumerate(ranked, start=1):
            candidate = row["candidate"]
            score = row["score"]
            target = target_weights.get(candidate.asset_id, 0.0)
            current = reference_weights.get(candidate.asset_id, 0.0)
            deviation = target - current
            action, trigger_reason = _action_with_deviation(score, current, target, settings)
            recommendation = {
                "rank": rank,
                "asset_id": candidate.asset_id,
                "asset_code": candidate.asset_code,
                "asset_name": candidate.asset_name,
                "grade": score.grade,
                "score": score.total_score,
                "target_weight": target,
                "current_weight": current,
                "deviation": deviation,
                "action_label": action,
                "trigger_reason": trigger_reason,
                "manual_review_required": score.manual_review_required,
            }
            recommendations.append(recommendation)
            insert_row(
                conn,
                "recommendation_snapshot",
                {
                    "run_id": run_id,
                    "asset_id": candidate.asset_id,
                    "rank": rank,
                    "target_weight": target,
                    "current_weight": current,
                    "deviation": deviation,
                    "action_label": action,
                    "trigger_reason": trigger_reason,
                    "next_check_by": "next configured Beijing slot",
                    "manual_review_required": int(score.manual_review_required),
                },
            )
            record_asset_pool_entries(
                conn,
                run_id=run_id,
                asset_id=candidate.asset_id,
                rank=rank,
                run_time_bj=run_time_bj,
                run_time_au=run_time_au,
                run_created_at=created_at,
                created_at=created_at,
            )
            insert_row(
                conn,
                "decision_record",
                {
                    "run_id": run_id,
                    "asset_id": candidate.asset_id,
                    "decision_type": "discipline_action",
                    "decision": action,
                    "rationale": trigger_reason,
                    "created_at": created_at,
                },
            )
            insert_row(
                conn,
                "baseline_snapshot",
                {
                    "run_id": run_id,
                    "asset_id": candidate.asset_id,
                    "baseline_weight": target,
                    "baseline_kind": "serenity_baseline",
                    "reference_run_id": baseline_reference_run_id,
                    "created_at": created_at,
                },
            )
        conn.commit()

        comparison_summaries, comparison_events = persist_comparisons(conn, run_id, created_at, settings)
        rebalance_events = (
            deviation_events(recommendations, settings)
            + comparison_events
        )
        if baseline_reference_run_id:
            rebalance_events += single_position_overexpansion_events(conn, run_id, settings)
        persist_rebalance_events(conn, run_id, created_at, rebalance_events)
        conn.commit()

        action_pool = _action_pool_rows(recommendations)
        data_quality_status = "degraded" if not moomoo.available else "pass"
        if _action_pool_requires_manual_review(recommendations):
            data_quality_status = "manual_review"
        severity = "Info"
        if rebalance_events:
            severity = "Alert"
        if any(row["action_label"] in {"Clear", "Block"} for row in action_pool):
            severity = "Urgent"
        if data_quality_status in {"degraded", "manual_review"} and severity == "Info":
            severity = "Warn"
        execution_locked = data_quality_status != "pass"
        notification_recommendations = action_pool

        notification_title, notification_body = render_notification(
            run_id,
            severity,
            notification_recommendations,
            run_time_bj,
            run_time_au,
            data_quality_status=data_quality_status,
            execution_locked=execution_locked,
        )
        notification_event_reason = (
            rebalance_events[0].trigger_reason
            if rebalance_events
            else (
                notification_recommendations[0]["trigger_reason"]
                if notification_recommendations
                else ""
            )
        )
        notification_html = render_notification_html(
            notification_title,
            run_id,
            severity,
            notification_recommendations,
            run_time_bj,
            run_time_au,
            data_quality_status=data_quality_status,
            event_reason=notification_event_reason,
            manual_review_items=[
                f"{row['asset_name']}：{row['trigger_reason']}"
                for row in recommendations
                if row.get("manual_review_required")
            ],
            execution_locked=execution_locked,
        )
        report_md = render_markdown_report(
            run_id=run_id,
            slot=slot.upper(),
            run_time_bj=run_time_bj,
            run_time_au=run_time_au,
            status="degraded" if not moomoo.available else "success",
            data_quality_status=data_quality_status,
            moomoo_status=moomoo.status,
            recommendations=recommendations,
            benchmark_returns={"Shanghai Composite": shanghai_returns, "S&P 500": sp500_returns},
            notification_title=notification_title,
            comparison_summaries=[
                {
                    "compare_type": item.compare_type,
                    "base_run_id": item.base_run_id,
                    "old_top5": list(item.old_top5),
                    "new_top5": list(item.new_top5),
                    "top5_change_rate": item.top5_change_rate,
                    "new_count": item.new_count,
                    "replacement_count": item.replacement_count,
                    "max_key_field_sigma": item.max_key_field_sigma,
                }
                for item in comparison_summaries
            ],
            rebalance_events=[event.trigger_reason for event in rebalance_events],
            execution_locked=execution_locked,
        )
        report_path = settings.reports_dir / f"{run_id}_report.md"
        html_path = settings.reports_dir / f"{run_id}_report.html"
        notification_path = settings.notifications_dir / f"{run_id}_{severity.lower()}.md"
        write_text(report_path, report_md)
        write_text(html_path, render_offline_html(f"Serenity 每日分析正式报告 {run_id}", report_md))
        write_mail_ready_draft(
            notification_path,
            notification_title,
            notification_body,
            settings.recipient_email,
            html_body=notification_html,
        )

        send_status = "drafted"
        send_error = None
        if send_mail and not dry_run:
            should_send_mail = should_send_mail_for_run(
                severity,
                notification_recommendations,
                data_quality_status=data_quality_status,
                execution_locked=execution_locked,
            )
            if not should_send_mail:
                send_status = "suppressed_no_material_change"
                send_error = suppressed_no_material_change_message()
            elif settings.mail_send_enabled:
                mail_result = send_with_apple_mail(
                    notification_title,
                    notification_body,
                    settings.recipient_email,
                    html_body=notification_html,
                )
                send_status = mail_result["status"]
                send_error = mail_result["error"] or None
            else:
                send_status = "blocked_by_config"
                send_error = "SERENITY_MAIL_SEND_ENABLED is false"

        insert_row(
            conn,
            "notification_log",
            {
                "notification_id": f"{run_id}_{severity.lower()}",
                "run_id": run_id,
                "channel": "macos_mail",
                "severity": severity,
                "title": notification_title,
                "body_path": str(notification_path),
                "send_status": send_status,
                "sent_at": created_at if send_status == "sent" else None,
                "error_message": send_error,
            },
        )
        conn.execute(
            """
            UPDATE run_log
            SET status=?, data_quality_status=?, notification_status=?,
                report_path=?, offline_html_path=?
            WHERE run_id=?
            """,
            (
                "degraded" if not moomoo.available else "success",
                data_quality_status,
                send_status,
                str(report_path),
                str(html_path),
                run_id,
            ),
        )
        conn.commit()
        offline_index_path = _write_offline_index(conn, settings)

    moomoo_cleanup = None
    if moomoo.cleanup_required and moomoo.opend_lifecycle_handle is not None:
        from app.core.moomoo_lifecycle import cleanup_started_processes

        moomoo_cleanup = cleanup_started_processes(moomoo.opend_lifecycle_handle)
        with connect(settings.db_path) as conn:
            insert_row(
                conn,
                "audit_log",
                {
                    "run_id": run_id,
                    "event_type": "moomoo_opend_cleanup",
                    "severity": "info",
                    "message": str(moomoo_cleanup.get("cleanup_result")),
                    "context_json": json.dumps(moomoo_cleanup, ensure_ascii=False, default=str),
                    "created_at": _now_iso(),
                },
            )

    return {
        "run_id": run_id,
        "status": "degraded" if not moomoo.available else "success",
        "data_quality_status": data_quality_status,
        "report_path": str(report_path),
        "offline_html_path": str(html_path),
        "offline_index_path": str(offline_index_path),
        "notification_path": str(notification_path),
        "moomoo_status": moomoo.status,
        "moomoo_cleanup": moomoo_cleanup,
        "rebalance_events": [event.trigger_reason for event in rebalance_events],
        "top5": [row["asset_code"] for row in _action_pool_rows(recommendations)],
    }
