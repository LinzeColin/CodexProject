from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

_DEFAULT_MPLCONFIGDIR = Path(__file__).resolve().parents[1] / "data" / "report_artifacts" / "automation_runtime" / "matplotlib"
os.environ.setdefault("MPLCONFIGDIR", str(_DEFAULT_MPLCONFIGDIR))
_DEFAULT_MPLCONFIGDIR.mkdir(parents=True, exist_ok=True)

from src.accounting.alipay_ledger import (
    CURRENT_POSITIONS,
    alipay_execution_state as _alipay_execution_state,
    build_account_summary,
    confirm_current_positions,
    ensure_alipay_files,
    format_update_summary,
    import_alipay_transactions,
    load_current_positions,
    load_pending_orders,
    load_position_candidates,
    record_update,
    summarize_updates,
)
from src.backtesting.engine import run_equal_weight_backtest
from src.advice.engine import build_trading_advice
from src.collectors.financial_data_collector import FinancialDataCollector
from src.collectors.market_data_collector import MarketDataCollector
from src.collectors.news_collector import NewsCollector
from src.collectors.watchlist_collector import WatchlistCollector, WatchlistSnapshotCollector
from src.config import ROOT
from src.data_io import write_csv
from src.data_io import read_csv
from src.factors.engine import compute_price_factors, merge_fundamental_factors
from src.factors.watchlist_engine import build_watchlist_factors
from src.integrations.moomoo_desktop import sync_quotes_from_opend, sync_watchlist_from_desktop
from src.integrations.policy_system_bridge import enrich_events_with_policy_system
from src.integrations.research_bus_bridge import (
    heartbeat_system as research_bus_heartbeat,
    process_pending_research_bus_requests,
    submit_bus_request as submit_research_bus_request,
    submit_chat_input as submit_research_bus_chat_input,
    sync_research_bus as sync_research_bus_bridge,
)
from src.monitoring.automation_health import (
    build_automation_health,
    format_automation_health,
    write_automation_health_log,
)
from src.monitoring.data_trust import write_data_trust_audit
from src.monitoring.evidence_decision import write_evidence_decision_matrix
from src.monitoring.entity_registry import write_entity_registry_audit
from src.monitoring.health import run_health_checks
from src.monitoring.manual_review import write_manual_review_audit
from src.monitoring.reconciliation import write_reconciliation_audit
from src.monitoring.report_layer import write_report_layer_audit
from src.pfi_os.engine import build_thesis_queue, run_pfi_os_validation
from src.reporting.daily_report import generate_daily_report
from src.reporting.industry_report import generate_industry_report
from src.reporting.kline_report import generate_kline_report
from src.reporting.paths import excel_dir, pfi_os_dir
from src.reporting.quality_gate import run_report_quality_gate, week_report_status
from src.reporting.schedule import REPORT_DUE_TIMES
from src.reporting.weekly_report import generate_watchlist_weekly_report
from src.risk.engine import evaluate_risk
from src.strategies.demo_momentum import generate_signals


REPORT_TIMEZONE = ZoneInfo("Australia/Sydney")
USER_TRADABLE_INDEX_SYMBOLS = {"000688", "399986"}


def load_research_context(as_of: str, sync_moomoo: bool = True) -> dict[str, object]:
    _validate_report_date(as_of)
    if sync_moomoo:
        sync_watchlist_from_desktop()
        sync_quotes_from_opend(as_of=as_of, fail_on_error=True)
    watchlist = WatchlistCollector(ROOT / "data" / "sample" / "watchlist_moomoo.csv").fetch()
    snapshot = WatchlistSnapshotCollector(ROOT / "data" / "sample" / "watchlist_snapshot.csv").fetch()
    _assert_actionable_snapshot(snapshot.parsed_data, watchlist.parsed_data, as_of)
    events = NewsCollector(ROOT / "data" / "sample" / "watchlist_events.csv").fetch()
    market = MarketDataCollector(ROOT / "data" / "sample" / "market_prices.csv").fetch()
    fundamentals = FinancialDataCollector(ROOT / "data" / "sample" / "fundamentals.csv").fetch()
    alipay_positions = load_current_positions()
    position_candidates = load_position_candidates(as_of)
    holdings = alipay_positions or position_candidates or _load_sample_holdings()
    pending_orders = load_pending_orders()
    account_summary = build_account_summary(alipay_positions, pending_orders, as_of=as_of)
    alipay_update = summarize_updates(start_date=as_of, end_date=as_of)
    alipay_execution = _alipay_execution_state(alipay_update, as_of)
    account_update_summary = format_update_summary(alipay_update)
    account_summary.update(
        {
            "alipay_update_status": alipay_execution["status"],
            "alipay_update_missing": bool(alipay_update.missing_dates),
            "alipay_missing_dates": alipay_update.missing_dates,
            "alipay_updated_dates": alipay_update.updated_dates,
            "alipay_execution_confirmed": alipay_execution["execution_confirmed"],
            "alipay_execution_blocked": alipay_execution["execution_blocked"],
            "alipay_execution_block_reason": alipay_execution["block_reason"],
            "alipay_latest_update_source_type": alipay_execution["source_type"],
            "alipay_latest_update_source_path": alipay_execution["source_path"],
            "alipay_update_note": account_update_summary,
        }
    )
    factors = build_watchlist_factors(watchlist.parsed_data, snapshot.parsed_data, as_of)
    enriched_events, policy_source = enrich_events_with_policy_system(events.parsed_data, factors, as_of)
    signals = generate_signals(factors)
    positions, risk_logs = evaluate_risk(signals)
    risk_logs = [*risk_logs, account_update_summary]
    advice = build_trading_advice(factors, enriched_events, signals, positions, holdings, pending_orders, account_summary)
    exposure = _summarize_advice_exposure(advice)
    health_logs = [*run_health_checks(snapshot.parsed_data, as_of), account_update_summary]
    sources = [watchlist.source(), snapshot.source(), market.source(), fundamentals.source(), events.source()]
    if policy_source:
        sources.append(policy_source)
    return {
        "market_rows": market.parsed_data,
        "fundamental_rows": fundamentals.parsed_data,
        "watchlist": watchlist.parsed_data,
        "snapshot_rows": snapshot.parsed_data,
        "events": enriched_events,
        "holdings": holdings,
        "pending_orders": pending_orders,
        "account_summary": account_summary,
        "account_update_summary": account_update_summary,
        "factors": factors,
        "signals": signals,
        "advice": advice,
        "positions": positions,
        "risk_logs": risk_logs,
        "exposure": exposure,
        "health_logs": health_logs,
        "sources": sources,
    }


def generate_daily(args: argparse.Namespace) -> None:
    _assert_report_generation_due(args.session, args.date)
    context = load_research_context(args.date, sync_moomoo=not args.no_sync_moomoo)
    path = generate_daily_report(
        as_of=args.date,
        session=args.session,
        factors=context["factors"],
        events=context["events"],
        advice=context["advice"],
        signals=context["signals"],
        positions=context["positions"],
        exposure=context["exposure"],
        risk_logs=context["risk_logs"],
        health_logs=context["health_logs"],
        sources=context["sources"],
        account_summary=context["account_summary"],
    )
    print(path)
    _run_quality_gate_unless_skipped(args, args.session)


def generate_daily_suite(args: argparse.Namespace) -> None:
    due_sessions = [
        session
        for session in ["pre_open", "midday", "post_close"]
        if _report_generation_is_due(session, args.date, allow_historical=False)
    ]
    for session in ["pre_open", "midday", "post_close"]:
        if session not in due_sessions:
            print(_report_not_due_message(session, args.date, skipped=True))
    if not due_sessions:
        print(f"NO_DUE_REPORTS: {args.date}")
        return
    context = load_research_context(args.date, sync_moomoo=not args.no_sync_moomoo)
    for session in due_sessions:
        path = generate_daily_report(
            as_of=args.date,
            session=session,
            factors=context["factors"],
            events=context["events"],
            advice=context["advice"],
            signals=context["signals"],
            positions=context["positions"],
            exposure=context["exposure"],
            risk_logs=context["risk_logs"],
            health_logs=context["health_logs"],
            sources=context["sources"],
            account_summary=context["account_summary"],
        )
        print(path)
        _run_quality_gate_unless_skipped(args, session)


def generate_industry(args: argparse.Namespace) -> None:
    context = load_research_context(args.date, sync_moomoo=not args.no_sync_moomoo)
    path = generate_industry_report(
        industry=args.industry,
        as_of=args.date,
        factors=context["factors"],
        events=context["events"],
        sources=context["sources"],
        account_summary=context["account_summary"],
    )
    print(path)


def generate_weekly(args: argparse.Namespace) -> None:
    _validate_weekly_session_date(args.date, args.session)
    _assert_report_generation_due(args.session, args.date)
    context = load_research_context(args.date, sync_moomoo=not args.no_sync_moomoo)
    path = generate_watchlist_weekly_report(
        as_of=args.date,
        session=args.session,
        watchlist=context["watchlist"],
        factors=context["factors"],
        events=context["events"],
        advice=context["advice"],
        sources=context["sources"],
        account_update_summary=context["account_update_summary"],
        account_summary=context["account_summary"],
    )
    print(path)
    _run_quality_gate_unless_skipped(args, args.session)


def generate_weekly_suite(args: argparse.Namespace) -> None:
    day = date.fromisoformat(args.date)
    sessions = []
    if day.weekday() == 0:
        sessions.append("monday_pre_open")
    if day.weekday() == 4:
        sessions.append("friday_post_close")
    if not sessions:
        print(f"NO_DUE_REPORTS: {args.date}")
        return
    due_sessions = [session for session in sessions if _report_generation_is_due(session, args.date, allow_historical=False)]
    for session in sessions:
        if session not in due_sessions:
            print(_report_not_due_message(session, args.date, skipped=True))
    if not due_sessions:
        print(f"NO_DUE_REPORTS: {args.date}")
        return
    context = load_research_context(args.date, sync_moomoo=not args.no_sync_moomoo)
    for session in due_sessions:
        path = generate_watchlist_weekly_report(
            as_of=args.date,
            session=session,
            watchlist=context["watchlist"],
            factors=context["factors"],
            events=context["events"],
            advice=context["advice"],
            sources=context["sources"],
            account_update_summary=context["account_update_summary"],
            account_summary=context["account_summary"],
        )
        print(path)
        _run_quality_gate_unless_skipped(args, session, args.date)


def generate_kline(args: argparse.Namespace) -> None:
    _assert_report_generation_due("kline", args.date)
    context = load_research_context(args.date, sync_moomoo=not args.no_sync_moomoo)
    path = generate_kline_report(
        as_of=args.date,
        factors=context["factors"],
        events=context["events"],
        advice=context["advice"],
        sources=context["sources"],
        account_summary=context["account_summary"],
    )
    print(path)
    _run_quality_gate_unless_skipped(args, "kline")


def validate_advice(args: argparse.Namespace) -> None:
    context = load_research_context(args.date, sync_moomoo=not args.no_sync_moomoo)
    symbols = [item["symbol"] for item in context["signals"] if item.get("internal_signal") == "buy"]
    result = run_equal_weight_backtest(context["market_rows"], symbols)
    out_dir = excel_dir(args.date)
    metrics_path = out_dir / f"backtest_{args.strategy}_{args.date}_metrics.csv"
    curve_path = out_dir / f"backtest_{args.strategy}_{args.date}_equity_curve.csv"
    write_csv(metrics_path, [result["metrics"]])
    write_csv(curve_path, result["equity_curve"])
    print(metrics_path)
    print(curve_path)


def pfi_os_refresh(args: argparse.Namespace) -> None:
    context = load_research_context(args.date, sync_moomoo=not args.no_sync_moomoo)
    _run_pfi_os_for_context(args.date, context, args.monte_carlo_runs, args.pipeline_reruns)


def generate_due_reports(args: argparse.Namespace) -> None:
    payload = week_report_status(as_of=args.date, through_date=args.date, run_quality=True)
    due_rows = _due_report_rows(payload, args.date)
    if not due_rows:
        print(f"NO_DUE_REPORTS: {args.date}")
        return
    context = load_research_context(args.date, sync_moomoo=not args.no_sync_moomoo)
    _run_pfi_os_for_context(args.date, context, 100000, 2)
    for row in due_rows:
        report_kind = str(row["report_kind"])
        _assert_report_generation_due(report_kind, args.date, allow_historical=False)
        if report_kind in {"pre_open", "midday", "post_close"}:
            path = generate_daily_report(
                as_of=args.date,
                session=report_kind,
                factors=context["factors"],
                events=context["events"],
                advice=context["advice"],
                signals=context["signals"],
                positions=context["positions"],
                exposure=context["exposure"],
                risk_logs=context["risk_logs"],
                health_logs=context["health_logs"],
                sources=context["sources"],
                account_summary=context["account_summary"],
            )
        elif report_kind == "kline":
            path = generate_kline_report(
                as_of=args.date,
                factors=context["factors"],
                events=context["events"],
                advice=context["advice"],
                sources=context["sources"],
                account_summary=context["account_summary"],
            )
        elif report_kind in {"monday_pre_open", "friday_post_close"}:
            _validate_weekly_session_date(args.date, report_kind)
            path = generate_watchlist_weekly_report(
                as_of=args.date,
                session=report_kind,
                watchlist=context["watchlist"],
                factors=context["factors"],
                events=context["events"],
                advice=context["advice"],
                sources=context["sources"],
                account_update_summary=context["account_update_summary"],
                account_summary=context["account_summary"],
            )
        else:
            raise ValueError(f"Unsupported due report kind: {report_kind}")
        print(path)
        issues = run_report_quality_gate(as_of=args.date, report_kind=report_kind)
        if issues:
            for issue in issues:
                print(f"QUALITY_GATE_FAIL: {issue}")
            raise SystemExit(1)
        print(f"QUALITY_GATE_PASS: {report_kind} {args.date}")


def _run_pfi_os_for_context(
    as_of: str,
    context: dict[str, object],
    monte_carlo_runs: int,
    pipeline_reruns: int,
) -> None:
    queue = build_thesis_queue(
        as_of,
        context["factors"],
        context["advice"],
        context["events"],
    )
    result = run_pfi_os_validation(
        as_of,
        queue,
        context["market_rows"],
        monte_carlo_runs=monte_carlo_runs,
        pipeline_reruns=pipeline_reruns,
    )
    summary = result["summary"]
    print(f"PFIOS queue: {len(result['queue'])}")
    print(f"PFIOS results: {summary['status_counts']}")
    print(pfi_os_dir(as_of))


def sync_moomoo(args: argparse.Namespace) -> None:
    path = sync_watchlist_from_desktop(group_name=args.group_name, open_if_needed=not args.no_open)
    print(path)
    if args.quotes:
        snapshot_path = sync_quotes_from_opend(as_of=args.date, open_if_needed=not args.no_open, fail_on_error=args.require_opend)
        if snapshot_path:
            print(snapshot_path)


def sync_quotes(args: argparse.Namespace) -> None:
    path = sync_quotes_from_opend(as_of=args.date, open_if_needed=not args.no_open, fail_on_error=args.require_opend)
    if path:
        print(path)


def alipay_record_update(args: argparse.Namespace) -> None:
    row = record_update(
        update_date=args.date,
        source_type=args.source_type,
        source_path=args.source_path or "",
        status=args.status,
        notes=args.notes or "",
        positions_count=args.positions_count,
        trades_count=args.trades_count,
        pending_count=args.pending_count,
    )
    print(f"Recorded Alipay update for {row['date']} at {row['updated_at']} ({row['status']}).")


def alipay_update_status(args: argparse.Namespace) -> None:
    end_date = args.end_date or args.date
    summary = summarize_updates(
        start_date=args.start_date,
        end_date=end_date,
        weekdays_only=not args.include_weekends,
    )
    print(format_update_summary(summary))


def alipay_init(args: argparse.Namespace) -> None:
    ensure_alipay_files()
    print(CURRENT_POSITIONS.parent)


def alipay_import_transactions(args: argparse.Namespace) -> None:
    summary = import_alipay_transactions(args.path)
    print("Imported Alipay transaction CSV")
    for key in [
        "source_start_time",
        "source_end_time",
        "total_rows",
        "investment_rows",
        "fund_trade_rows",
        "confirmed_trade_rows",
        "pending_rows",
        "raw_output_path",
        "trade_ledger_path",
        "pending_orders_path",
    ]:
        print(f"{key}: {summary[key]}")


def alipay_confirm_positions(args: argparse.Namespace) -> None:
    summary = confirm_current_positions(
        args.date,
        source_path=args.source_path,
        notes=args.notes,
        allow_unverified=args.allow_unverified,
    )
    print("Confirmed Alipay current positions")
    for key in [
        "date",
        "confirmed_positions",
        "unverified_rows",
        "allow_unverified",
        "current_positions_path",
        "update_log_path",
    ]:
        print(f"{key}: {summary[key]}")


def report_quality_check(args: argparse.Namespace) -> None:
    issues = run_report_quality_gate(
        as_of=args.date,
        report_kind=args.report_kind,
        strict_week_folder=not args.no_week_folder_check,
    )
    if issues:
        for issue in issues:
            print(f"QUALITY_GATE_FAIL: {issue}")
        raise SystemExit(1)
    print(f"QUALITY_GATE_PASS: {args.report_kind} {args.date}")


def report_week_status(args: argparse.Namespace) -> None:
    payload = week_report_status(
        as_of=args.date,
        through_date=args.through_date,
        run_quality=not args.no_quality_check,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"WEEK_REPORT_STATUS: {payload['week_folder']}")
    print(f"expected_total={payload['expected_total']} counts={payload['status_counts']}")
    for issue in payload["folder_issues"]:
        print(f"WEEK_FOLDER_ISSUE: {issue}")
    for row in payload["reports"]:
        status = row["status"]
        print(f"{status}: {row['report_date']} {row['label']} {row['pdf_name']}")
        for issue in row["issues"]:
            print(f"  ISSUE: {issue}")
        if row["next_action"] != "none":
            print(f"  NEXT: {row['next_action']}")
        if row["repair_command"]:
            print(f"  REPAIR: {row['repair_command']}")
        if row["blocker_note"]:
            print(f"  BLOCKER_NOTE: {row['blocker_note']}")


def automation_health(args: argparse.Namespace) -> None:
    payload = build_automation_health(
        args.date,
        run_quality=not args.no_quality_check,
        strict_opend=args.strict_opend,
        min_opend_coverage=args.min_opend_coverage,
        preflight=args.preflight,
        require_execution_ready=args.require_execution_ready,
    )
    log_path = write_automation_health_log(payload)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_automation_health(payload))
        print(log_path)
    if payload["status"] == "fail":
        raise SystemExit(1)


def data_trust_audit(args: argparse.Namespace) -> None:
    payload = write_data_trust_audit(args.date)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"DATA_TRUST_AUDIT: {payload['audit_status']} {payload['as_of']}")
    print(f"records: {payload['record_count']}")
    print(f"status_counts: {payload['status_counts']}")
    for key, path in payload["outputs"].items():
        print(f"{key}: {path}")


def reconciliation_audit(args: argparse.Namespace) -> None:
    payload = write_reconciliation_audit(args.date)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"RECONCILIATION_AUDIT: {payload['audit_status']} {payload['as_of']}")
    print(f"checks: {payload['check_count']}")
    print(f"status_counts: {payload['status_counts']}")
    for key, path in payload["outputs"].items():
        print(f"{key}: {path}")


def manual_review_audit(args: argparse.Namespace) -> None:
    payload = write_manual_review_audit(args.date)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"MANUAL_REVIEW_QUEUE: {payload['audit_status']} {payload['as_of']}")
    print(f"items: {payload['item_count']}")
    print(f"priority_counts: {payload['priority_counts']}")
    for key, path in payload["outputs"].items():
        print(f"{key}: {path}")


def entity_registry_audit(args: argparse.Namespace) -> None:
    payload = write_entity_registry_audit(args.date)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"ENTITY_REGISTRY: {payload['audit_status']} {payload['as_of']}")
    print(f"entities: {payload['entity_count']}")
    print(f"aliases: {payload['alias_count']}")
    print(f"entity_type_counts: {payload['entity_type_counts']}")
    for key, path in payload["outputs"].items():
        print(f"{key}: {path}")


def evidence_decision_audit(args: argparse.Namespace) -> None:
    payload = write_evidence_decision_matrix(args.date)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"EVIDENCE_DECISION_MATRIX: {payload['audit_status']} {payload['as_of']}")
    print(f"rows: {payload['row_count']}")
    print(f"evidence_counts: {payload['evidence_counts']}")
    print(f"decision_counts: {payload['decision_counts']}")
    for key, path in payload["outputs"].items():
        print(f"{key}: {path}")


def report_layer_audit(args: argparse.Namespace) -> None:
    payload = write_report_layer_audit(args.date)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"REPORT_LAYER_AUDIT: {payload['audit_status']} {payload['as_of']}")
    print(f"conclusion_ceiling: {payload['conclusion_ceiling']}")
    print(f"rows: {payload['row_count']}")
    print(f"quality_gate_issues: {len(payload['quality_gate_issues'])}")
    for key, path in payload["outputs"].items():
        print(f"{key}: {path}")


def research_bus_sync(args: argparse.Namespace) -> None:
    payload = sync_research_bus_bridge(
        args.db or None,
        report_limit=args.report_limit,
        result_limit=args.result_limit,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"RESEARCH_BUS_SYNC: {payload['synced_at']}")
    print(f"db_path: {payload['db_path']}")
    print(f"published_reports: {payload['published_reports']}")
    print(f"pfi_os_result_count: {payload['pfi_os_result_count']}")
    print(f"pfi_os_results_path: {payload['pfi_os_results_path']}")
    print(f"validation_task_count: {payload['validation_task_count']}")
    print(f"validation_tasks_path: {payload['validation_tasks_path']}")
    print(f"independent_validation_run_count: {payload['independent_validation_run_count']}")
    print(f"independent_validation_runs_path: {payload['independent_validation_runs_path']}")
    print(f"consumer_behavior_state_count: {payload['consumer_behavior_state_count']}")
    print(f"consumer_behavior_state_path: {payload['consumer_behavior_state_path']}")
    print(f"holdings_master_count: {payload['holdings_master_count']}")
    print(f"holdings_master_path: {payload['holdings_master_path']}")
    print(f"holding_symbol_mapping_count: {payload['holding_symbol_mapping_count']}")
    print(f"holding_symbol_mappings_path: {payload['holding_symbol_mappings_path']}")
    print(f"portfolio_transaction_count: {payload['portfolio_transaction_count']}")
    print(f"portfolio_transactions_path: {payload['portfolio_transactions_path']}")
    print(f"holding_update_candidate_count: {payload['holding_update_candidate_count']}")
    print(f"holding_update_candidates_path: {payload['holding_update_candidates_path']}")


def research_bus_submit(args: argparse.Namespace) -> None:
    if args.text:
        payload = submit_research_bus_chat_input(
            args.text,
            source_system=args.source_system,
            author=args.author,
            channel=args.channel,
            attachments=_research_bus_attachments(args.attachment_path, args.attachment_json),
            db_path=args.db or None,
        )
    else:
        payload = submit_research_bus_request(
            args.request_type,
            json.loads(args.payload_json),
            source_system=args.source_system,
            target_system=args.target_system,
            priority=args.priority,
            db_path=args.db or None,
        )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    for key, value in payload.items():
        print(f"{key}: {value}")


def _research_bus_attachments(paths: list[str], attachment_json_values: list[str]) -> list[dict[str, object]]:
    attachments: list[dict[str, object]] = []
    for path in paths:
        clean_path = str(path or "").strip()
        if clean_path:
            expanded = Path(clean_path).expanduser()
            attachments.append({"path": str(expanded), "name": expanded.name, "source": "cli"})
    for raw in attachment_json_values:
        if not str(raw or "").strip():
            continue
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            attachments.append(parsed)
        elif isinstance(parsed, list):
            attachments.extend(item for item in parsed if isinstance(item, dict))
        else:
            raise ValueError("--attachment-json must be a JSON object or array of objects.")
    return attachments


def research_bus_process(args: argparse.Namespace) -> None:
    payload = process_pending_research_bus_requests(
        args.db or None,
        system_name=args.system_name,
        limit=args.limit,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"processed: {payload['processed']}")
    print(f"failed: {payload['failed']}")


def research_bus_heartbeat_cmd(args: argparse.Namespace) -> None:
    research_bus_heartbeat(
        args.system_name,
        db_path=args.db or None,
        status=args.status,
        capabilities=args.capability,
        payload=json.loads(args.payload_json),
    )
    print(f"HEARTBEAT: {args.system_name} {args.status}")


def _due_report_rows(payload: dict[str, object], report_date: str) -> list[dict[str, object]]:
    rows = []
    for row in payload.get("reports", []):
        if not isinstance(row, dict):
            continue
        if row.get("report_date") != report_date:
            continue
        if row.get("status") in {"missing", "quality_fail"}:
            rows.append(row)
    return rows


def _report_generation_is_due(
    report_kind: str,
    as_of: str,
    now: datetime | None = None,
    allow_historical: bool = True,
) -> bool:
    _validate_report_date(as_of)
    report_day = date.fromisoformat(as_of)
    now_dt = _report_now(now)
    if report_day > now_dt.date():
        return False
    if report_day < now_dt.date():
        return allow_historical
    due_time = REPORT_DUE_TIMES[report_kind]
    return now_dt.time() >= due_time


def _assert_report_generation_due(
    report_kind: str,
    as_of: str,
    now: datetime | None = None,
    allow_historical: bool = True,
) -> None:
    if _report_generation_is_due(report_kind, as_of, now, allow_historical=allow_historical):
        return
    raise SystemExit(_report_not_due_message(report_kind, as_of))


def _report_not_due_message(report_kind: str, as_of: str, skipped: bool = False) -> str:
    due = REPORT_DUE_TIMES[report_kind].strftime("%H:%M")
    status = "REPORT_NOT_DUE_SKIPPED" if skipped else "REPORT_NOT_DUE"
    return f"{status}: {report_kind} {as_of} due_at={due} timezone=Australia/Sydney"


def _report_now(now: datetime | None = None) -> datetime:
    if now is None:
        return datetime.now(REPORT_TIMEZONE)
    if now.tzinfo is None:
        return now
    return now.astimezone(REPORT_TIMEZONE)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Research Terminal - report-first trading advice system")
    sub = parser.add_subparsers(required=True)

    daily = sub.add_parser("generate-report")
    daily.add_argument("--date", required=True)
    daily.add_argument("--session", choices=["pre_open", "midday", "post_close"], default="pre_open")
    _add_sync_controls(daily)
    _add_quality_controls(daily)
    daily.set_defaults(func=generate_daily)

    daily_alias = sub.add_parser("generate-daily")
    daily_alias.add_argument("--date", required=True)
    daily_alias.add_argument("--session", choices=["pre_open", "midday", "post_close"], default="pre_open")
    _add_sync_controls(daily_alias)
    _add_quality_controls(daily_alias)
    daily_alias.set_defaults(func=generate_daily)

    daily_suite = sub.add_parser("generate-daily-suite")
    daily_suite.add_argument("--date", required=True)
    _add_sync_controls(daily_suite)
    _add_quality_controls(daily_suite)
    daily_suite.set_defaults(func=generate_daily_suite)

    industry = sub.add_parser("generate-industry")
    industry.add_argument("--industry", required=True)
    industry.add_argument("--date", required=True)
    _add_sync_controls(industry)
    industry.set_defaults(func=generate_industry)

    weekly = sub.add_parser("generate-weekly")
    weekly.add_argument("--date", required=True)
    weekly.add_argument("--session", choices=["monday_pre_open", "friday_post_close"], default="monday_pre_open")
    _add_sync_controls(weekly)
    _add_quality_controls(weekly)
    weekly.set_defaults(func=generate_weekly)

    weekly_suite = sub.add_parser("generate-weekly-suite")
    weekly_suite.add_argument("--date", required=True)
    _add_sync_controls(weekly_suite)
    _add_quality_controls(weekly_suite)
    weekly_suite.set_defaults(func=generate_weekly_suite)

    kline = sub.add_parser("generate-kline")
    kline.add_argument("--date", required=True)
    _add_sync_controls(kline)
    _add_quality_controls(kline)
    kline.set_defaults(func=generate_kline)

    due = sub.add_parser("generate-due-reports")
    due.add_argument("--date", required=True)
    _add_sync_controls(due)
    due.set_defaults(func=generate_due_reports)

    validate = sub.add_parser("validate-advice")
    validate.add_argument("--strategy", default="demo_momentum")
    validate.add_argument("--date", required=True)
    _add_sync_controls(validate)
    validate.set_defaults(func=validate_advice)

    backtest_alias = sub.add_parser("run-backtest")
    backtest_alias.add_argument("--strategy", default="demo_momentum")
    backtest_alias.add_argument("--date", required=True)
    _add_sync_controls(backtest_alias)
    backtest_alias.set_defaults(func=validate_advice)

    pfi_os = sub.add_parser("pfi_os-refresh")
    pfi_os.add_argument("--date", required=True)
    pfi_os.add_argument("--monte-carlo-runs", type=int, default=100000)
    pfi_os.add_argument("--pipeline-reruns", type=int, default=2)
    _add_sync_controls(pfi_os)
    pfi_os.set_defaults(func=pfi_os_refresh)

    quality = sub.add_parser("report-quality-check")
    quality.add_argument("--date", required=True)
    quality.add_argument(
        "--report-kind",
        required=True,
        choices=["pre_open", "midday", "post_close", "kline", "monday_pre_open", "friday_post_close"],
    )
    quality.add_argument("--no-week-folder-check", action="store_true")
    quality.set_defaults(func=report_quality_check)

    week_status = sub.add_parser("report-week-status")
    week_status.add_argument("--date", required=True)
    week_status.add_argument("--through-date", default=None)
    week_status.add_argument("--no-quality-check", action="store_true")
    week_status.add_argument("--json", action="store_true")
    week_status.set_defaults(func=report_week_status)

    health = sub.add_parser("automation-health")
    health.add_argument("--date", required=True)
    health.add_argument("--no-quality-check", action="store_true")
    health.add_argument("--json", action="store_true")
    health.add_argument("--strict-opend", action="store_true")
    health.add_argument("--min-opend-coverage", type=float, default=0.0)
    health.add_argument(
        "--preflight",
        action="store_true",
        help="生成报告前使用：旧行情快照只预警，生成后仍应使用严格 health。",
    )
    health.add_argument(
        "--require-execution-ready",
        action="store_true",
        help="要求真实交易执行金额可用；支付宝未确认、当前报告缺失或行情不可操作时失败。",
    )
    health.set_defaults(func=automation_health)

    data_trust = sub.add_parser("data-trust-audit")
    data_trust.add_argument("--date", required=True)
    data_trust.add_argument("--json", action="store_true")
    data_trust.set_defaults(func=data_trust_audit)

    reconciliation = sub.add_parser("reconciliation-audit")
    reconciliation.add_argument("--date", required=True)
    reconciliation.add_argument("--json", action="store_true")
    reconciliation.set_defaults(func=reconciliation_audit)

    manual_review = sub.add_parser("manual-review-audit")
    manual_review.add_argument("--date", required=True)
    manual_review.add_argument("--json", action="store_true")
    manual_review.set_defaults(func=manual_review_audit)

    entity_registry = sub.add_parser("entity-registry-audit")
    entity_registry.add_argument("--date", required=True)
    entity_registry.add_argument("--json", action="store_true")
    entity_registry.set_defaults(func=entity_registry_audit)

    evidence_decision = sub.add_parser("evidence-decision-audit")
    evidence_decision.add_argument("--date", required=True)
    evidence_decision.add_argument("--json", action="store_true")
    evidence_decision.set_defaults(func=evidence_decision_audit)

    report_layer = sub.add_parser("report-layer-audit")
    report_layer.add_argument("--date", required=True)
    report_layer.add_argument("--json", action="store_true")
    report_layer.set_defaults(func=report_layer_audit)

    research_bus = sub.add_parser("research-bus-sync")
    research_bus.add_argument("--db", default="")
    research_bus.add_argument("--report-limit", type=int, default=500)
    research_bus.add_argument("--result-limit", type=int, default=500)
    research_bus.add_argument("--json", action="store_true")
    research_bus.set_defaults(func=research_bus_sync)

    research_bus_submit_parser = sub.add_parser("research-bus-submit")
    research_bus_submit_parser.add_argument("--text", default="")
    research_bus_submit_parser.add_argument("--request-type", default="chat_general_note")
    research_bus_submit_parser.add_argument("--payload-json", default="{}")
    research_bus_submit_parser.add_argument("--source-system", default="AI-Research-System")
    research_bus_submit_parser.add_argument("--target-system", default="ResearchBus")
    research_bus_submit_parser.add_argument("--author", default="")
    research_bus_submit_parser.add_argument("--channel", default="chat")
    research_bus_submit_parser.add_argument("--attachment-path", action="append", default=[])
    research_bus_submit_parser.add_argument("--attachment-json", action="append", default=[])
    research_bus_submit_parser.add_argument("--priority", type=int, default=5)
    research_bus_submit_parser.add_argument("--db", default="")
    research_bus_submit_parser.add_argument("--json", action="store_true")
    research_bus_submit_parser.set_defaults(func=research_bus_submit)

    research_bus_process_parser = sub.add_parser("research-bus-process")
    research_bus_process_parser.add_argument("--db", default="")
    research_bus_process_parser.add_argument("--system-name", default="AI-Research-System")
    research_bus_process_parser.add_argument("--limit", type=int, default=25)
    research_bus_process_parser.add_argument("--json", action="store_true")
    research_bus_process_parser.set_defaults(func=research_bus_process)

    research_bus_heartbeat_parser = sub.add_parser("research-bus-heartbeat")
    research_bus_heartbeat_parser.add_argument("--db", default="")
    research_bus_heartbeat_parser.add_argument("--system-name", default="AI-Research-System")
    research_bus_heartbeat_parser.add_argument("--status", default="Ready")
    research_bus_heartbeat_parser.add_argument("--capability", action="append", default=[])
    research_bus_heartbeat_parser.add_argument("--payload-json", default="{}")
    research_bus_heartbeat_parser.set_defaults(func=research_bus_heartbeat_cmd)

    moomoo = sub.add_parser("sync-moomoo")
    moomoo.add_argument("--group-name", default="全部")
    moomoo.add_argument("--date", required=True)
    moomoo.add_argument("--quotes", action="store_true")
    moomoo.add_argument("--no-open", action="store_true")
    moomoo.add_argument("--require-opend", action="store_true")
    moomoo.set_defaults(func=sync_moomoo)

    quotes = sub.add_parser("sync-quotes")
    quotes.add_argument("--date", required=True)
    quotes.add_argument("--no-open", action="store_true")
    quotes.add_argument("--require-opend", action="store_true")
    quotes.set_defaults(func=sync_quotes)

    alipay_init_parser = sub.add_parser("alipay-init")
    alipay_init_parser.set_defaults(func=alipay_init)

    alipay_record = sub.add_parser("alipay-record-update")
    alipay_record.add_argument("--date", required=True)
    alipay_record.add_argument("--source-type", required=True, choices=["video", "screenshot", "csv", "xlsx", "pdf", "manual", "none"])
    alipay_record.add_argument("--source-path", default="")
    alipay_record.add_argument(
        "--status",
        default="received",
        choices=["received", "parsed", "confirmed", "no_trade", "needs_confirmation"],
    )
    alipay_record.add_argument("--positions-count", type=int, default=0)
    alipay_record.add_argument("--trades-count", type=int, default=0)
    alipay_record.add_argument("--pending-count", type=int, default=0)
    alipay_record.add_argument("--notes", default="")
    alipay_record.set_defaults(func=alipay_record_update)

    alipay_status = sub.add_parser("alipay-update-status")
    alipay_status.add_argument("--date", default=None)
    alipay_status.add_argument("--start-date", default=None)
    alipay_status.add_argument("--end-date", default=None)
    alipay_status.add_argument("--include-weekends", action="store_true")
    alipay_status.set_defaults(func=alipay_update_status)

    alipay_import = sub.add_parser("alipay-import-transactions")
    alipay_import.add_argument("--path", required=True)
    alipay_import.set_defaults(func=alipay_import_transactions)

    alipay_confirm = sub.add_parser("alipay-confirm-positions")
    alipay_confirm.add_argument("--date", required=True)
    alipay_confirm.add_argument("--source-path", default="")
    alipay_confirm.add_argument("--notes", default="")
    alipay_confirm.add_argument(
        "--allow-unverified",
        action="store_true",
        help="允许人工确认低清晰度或沿用旧日持仓行；默认会阻止这些低置信行进入可执行口径。",
    )
    alipay_confirm.set_defaults(func=alipay_confirm_positions)
    return parser


def _add_sync_controls(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--no-sync-moomoo",
        action="store_true",
        help="跳过默认的 moomoo 自选清单和行情刷新，使用本地已有快照。",
    )


def _add_quality_controls(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--skip-quality-check",
        action="store_true",
        help="跳过报告生成后的质量闸门。仅用于本地调试，不用于正式报告或 automation。",
    )


def _run_quality_gate_unless_skipped(args: argparse.Namespace, report_kind: str, as_of: str | None = None) -> None:
    report_date = as_of or args.date
    if getattr(args, "skip_quality_check", False):
        print(f"QUALITY_GATE_SKIPPED: {report_kind} {report_date}")
        return
    issues = run_report_quality_gate(as_of=report_date, report_kind=report_kind)
    if issues:
        for issue in issues:
            print(f"QUALITY_GATE_FAIL: {issue}")
        raise SystemExit(1)
    print(f"QUALITY_GATE_PASS: {report_kind} {report_date}")


def _validate_report_date(value: str) -> None:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid report date {value!r}; expected YYYY-MM-DD.") from exc


def _validate_weekly_session_date(value: str, session: str) -> None:
    day = date.fromisoformat(value)
    expected_weekday = {"monday_pre_open": 0, "friday_post_close": 4}[session]
    if day.weekday() != expected_weekday:
        expected = "Monday" if expected_weekday == 0 else "Friday"
        raise ValueError(f"{session} must use a {expected} report date; got {value}.")


def _assert_actionable_snapshot(
    snapshot_rows: list[dict[str, str]],
    watchlist_rows: list[dict[str, str]],
    as_of: str,
) -> None:
    if not snapshot_rows:
        raise RuntimeError("No quote snapshot is available; report generation is blocked.")
    supported_symbols = {
        row["symbol"]
        for row in watchlist_rows
        if _requires_actionable_quote(row)
    }
    latest_by_symbol: dict[str, dict[str, str]] = {}
    for row in snapshot_rows:
        symbol = row.get("symbol", "")
        if symbol not in supported_symbols:
            continue
        current = latest_by_symbol.get(symbol)
        if current is None or row.get("date", "") > current.get("date", ""):
            latest_by_symbol[symbol] = row
    missing_rows = sorted(symbol for symbol in supported_symbols if symbol not in latest_by_symbol)
    stale_rows = sorted(symbol for symbol, row in latest_by_symbol.items() if row.get("date") != as_of)
    missing_price = sorted(symbol for symbol, row in latest_by_symbol.items() if not row.get("close"))
    if missing_rows or stale_rows or missing_price:
        details = []
        if missing_rows:
            details.append("缺少行情：" + ", ".join(missing_rows))
        if stale_rows:
            details.append("行情日期不是报告日期：" + ", ".join(stale_rows))
        if missing_price:
            details.append("缺少最新价格：" + ", ".join(missing_price))
        raise RuntimeError("Quote snapshot is not actionable; report generation is blocked. " + "；".join(details))


def _requires_actionable_quote(row: dict[str, str]) -> bool:
    asset_class = row.get("asset_class")
    exchange = row.get("exchange")
    symbol = str(row.get("symbol") or "")
    if exchange not in {"US", "SSE", "SZSE", "SEHK"}:
        return False
    if asset_class in {"Stock", "ETF"}:
        return True
    return asset_class == "Index" and symbol in USER_TRADABLE_INDEX_SYMBOLS


def _load_holdings() -> list[dict[str, str]]:
    return load_current_positions() or load_position_candidates() or _load_sample_holdings()


def _load_sample_holdings() -> list[dict[str, str]]:
    path = ROOT / "data" / "sample" / "holdings.csv"
    return read_csv(path) if path.exists() else []


def _summarize_advice_exposure(advice: list[dict[str, object]]) -> dict[str, object]:
    industry: dict[str, float] = {}
    total = 0.0
    for row in advice:
        action = str(row.get("Position", ""))
        if "承接" not in action and "低仓位" not in action:
            continue
        weight = float(row.get("Volume") or 0)
        total += weight
        key = str(row.get("industry") or "未分类")
        industry[key] = industry.get(key, 0.0) + weight
    return {
        "total_weight": round(total, 6),
        "industry_exposure": {key: round(value, 6) for key, value in sorted(industry.items())},
        "cash_weight": round(max(0.0, 1 - total), 6),
    }


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
