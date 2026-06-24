from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.adapters import moomoo_adapter
from app.config import load_settings
from app.core.automation_tick import automation_tick
from app.core.alipay_position_normalizer import normalize_alipay_positions
from app.core.application_server import serve_application
from app.core.application_portal import build_application_portal
from app.core.benchmark_smoke import run_benchmark_smoke
from app.core.candidate_normalizer import normalize_candidates
from app.core.completion_audit import run_completion_audit
from app.core.fund_nav_history_collector import collect_fund_nav_history
from app.core.fund_rule_normalizer import normalize_fund_rules
from app.core.holdings_discovery import discover_holdings
from app.core.history_integrity import run_history_integrity
from app.core.intake_bundle_normalizer import normalize_intake_bundle
from app.core.intake_validator import validate_intake
from app.core.intake_promoter import promote_intake_pack
from app.core.mail_smoke import run_mail_smoke
from app.core.mail_unlock_check import build_mail_unlock_check
from app.core.moomoo_collect import KLINE_TYPES, collect_moomoo_data
from app.core.moomoo_smoke import run_moomoo_smoke
from app.core.notification import notify_run
from app.core.packaging import build_delivery_package
from app.core.pipeline import import_alipay_csv, run_slot
from app.core.platform_trade_checker import run_platform_trade_check
from app.core.preflight import run_preflight
from app.core.production_intake_pack import build_production_intake_pack
from app.core.production_action_queue import build_production_action_queue
from app.core.production_unblock_matrix import build_production_unblock_matrix
from app.core.production_unlock import run_production_unlock_check
from app.core.risk_gate_regression import run_risk_gate_regression
from app.core.scheduler_runner import scheduler_tick
from app.core.source_evidence_audit import build_source_evidence_audit
from app.db import connect, init_db
from app.scheduler import SCHEDULE_SLOTS, slot_times


def _print_result(result: dict[str, object], as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    for key, value in result.items():
        print(f"{key}: {value}")


def _runtime_settings(settings, *, dry_run: bool, send_mail: bool):
    return settings.with_runtime_mail_intent(dry_run=dry_run, send_mail=send_mail)


def cmd_doctor(args: argparse.Namespace) -> int:
    settings = load_settings()
    moomoo = moomoo_adapter.healthcheck()
    result = {
        "status": "ok",
        "python": sys.version.split()[0],
        "db_path": str(settings.db_path),
        "db_exists": settings.db_path.exists(),
        "schedule_slots": len(SCHEDULE_SLOTS),
        "timezone_primary": settings.timezone_primary,
        "timezone_secondary": settings.timezone_secondary,
        "moomoo_status": moomoo.status,
        "moomoo_detail": moomoo.detail,
        "moomoo_sdk_available": moomoo.sdk_available,
        "mail_send_enabled": settings.mail_send_enabled,
        "secret_storage_enabled": settings.secret_storage_enabled,
        "dry_run_default": settings.dry_run_default,
    }
    _print_result(result, args.json)
    return 0


def cmd_init_db(args: argparse.Namespace) -> int:
    settings = load_settings()
    init_db(settings.db_path)
    _print_result({"status": "ok", "db_path": str(settings.db_path)}, args.json)
    return 0


def cmd_import_alipay(args: argparse.Namespace) -> int:
    settings = load_settings()
    result = import_alipay_csv(settings, Path(args.csv))
    _print_result(result, args.json)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    settings = load_settings()
    dry_run = bool(args.dry_run or (settings.dry_run_default and not args.no_dry_run))
    runtime_settings = _runtime_settings(settings, dry_run=dry_run, send_mail=args.send_mail)
    if args.at:
        raise SystemExit("--at is reserved for the scheduler-ready interface; use --slot for MVP Phases 0-2")
    result = run_slot(runtime_settings, args.slot, dry_run=dry_run, send_mail=args.send_mail)
    _print_result(result, args.json)
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    settings = load_settings()
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        if args.run_id:
            run_id = args.run_id
        else:
            latest = conn.execute(
                """
                SELECT run_id FROM run_log
                WHERE report_path IS NOT NULL
                  AND schedule_slot LIKE 'R%'
                ORDER BY created_at DESC, rowid DESC LIMIT 1
                """
            ).fetchone()
            run_id = latest["run_id"] if latest else None
        if not run_id:
            raise SystemExit("No run found. Run `python -m app.cli run --slot R7 --dry-run` first.")
        row = conn.execute("SELECT report_path, offline_html_path FROM run_log WHERE run_id=?", (run_id,)).fetchone()
        if not row:
            raise SystemExit(f"Run not found: {run_id}")
    result = {
        "run_id": run_id,
        "report_path": row["report_path"],
        "offline_html_path": row["offline_html_path"],
        "offline_index_path": str(settings.reports_dir / "index.html"),
    }
    _print_result(result, args.json)
    return 0


def cmd_notify(args: argparse.Namespace) -> int:
    settings = load_settings()
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        if args.run_id:
            run_id = args.run_id
        else:
            latest = conn.execute(
                """
                SELECT run_id FROM run_log
                WHERE report_path IS NOT NULL
                  AND schedule_slot LIKE 'R%'
                ORDER BY created_at DESC, rowid DESC LIMIT 1
                """
            ).fetchone()
            run_id = latest["run_id"] if latest else None
    if not run_id:
        raise SystemExit("No report run found. Run one slot first.")
    dry_run = bool(args.dry_run or (settings.dry_run_default and not args.no_dry_run))
    runtime_settings = _runtime_settings(settings, dry_run=dry_run, send_mail=args.send_mail)
    result = notify_run(runtime_settings, run_id, dry_run=dry_run, send_mail=args.send_mail, local=args.local)
    _print_result(result, args.json)
    return 0


def cmd_scheduler_tick(args: argparse.Namespace) -> int:
    settings = load_settings()
    dry_run = bool(args.dry_run or (settings.dry_run_default and not args.no_dry_run))
    result = scheduler_tick(
        settings,
        now=args.now,
        dry_run=dry_run,
        force_slot=args.force_slot,
        allow_duplicate=args.allow_duplicate,
        tolerance_minutes=args.tolerance_minutes,
    )
    _print_result(result, args.json)
    return 0


def cmd_automation_tick(args: argparse.Namespace) -> int:
    settings = load_settings()
    dry_run = bool(args.dry_run or (settings.dry_run_default and not args.no_dry_run))
    scan_paths = [Path(path).expanduser() for path in args.scan_path]
    result = automation_tick(
        settings,
        now=args.now,
        dry_run=dry_run,
        force_slot=args.force_slot,
        allow_duplicate=args.allow_duplicate,
        tolerance_minutes=args.tolerance_minutes,
        scan_paths=scan_paths,
        send_mail=args.send_mail,
        local=args.local,
    )
    _print_result(result, args.json)
    if args.require_production and result.get("preflight") and not result["preflight"]["production_ready"]:
        return 2
    return 0


def cmd_preflight(args: argparse.Namespace) -> int:
    settings = load_settings()
    scan_paths = [Path(path).expanduser() for path in args.scan_path]
    runtime_settings = _runtime_settings(settings, dry_run=False, send_mail=args.send_mail)
    result = run_preflight(runtime_settings, scan_paths=scan_paths)
    _print_result(result, args.json)
    if args.require_production and not result["production_ready"]:
        return 2
    return 0


def cmd_completion_audit(args: argparse.Namespace) -> int:
    settings = load_settings()
    result = run_completion_audit(settings)
    _print_result(result, args.json)
    if args.require_complete and result["overall_status"] != "complete":
        return 2
    return 0


def cmd_history_integrity(args: argparse.Namespace) -> int:
    settings = load_settings()
    result = run_history_integrity(
        settings,
        baseline_path=Path(args.baseline).expanduser() if args.baseline else None,
        write_baseline=args.write_baseline,
        overwrite_baseline=args.overwrite_baseline,
    )
    _print_result(result, args.json)
    if args.require_pass and result["status"] != "pass":
        return 2
    return 0 if result["status"] == "pass" else 2


def cmd_risk_gate_regression(args: argparse.Namespace) -> int:
    settings = load_settings()
    result = run_risk_gate_regression(settings)
    _print_result(result, args.json)
    if args.require_pass and result["status"] != "pass":
        return 2
    return 0


def cmd_package_delivery(args: argparse.Namespace) -> int:
    settings = load_settings()
    result = build_delivery_package(
        settings,
        include_private_evidence=args.include_private_evidence,
        output_path=Path(args.output) if args.output else None,
    )
    _print_result(result, args.json)
    return 0 if result["status"] == "pass" else 2


def cmd_application_portal(args: argparse.Namespace) -> int:
    settings = load_settings()
    result = build_application_portal(settings)
    _print_result(result, args.json)
    return 0 if result["status"] == "pass" else 2


def cmd_application_server(args: argparse.Namespace) -> int:
    settings = load_settings()
    serve_application(
        settings,
        host=args.host,
        port=args.port,
        ttl_seconds=args.ttl_seconds,
        enable_autoscheduler=not args.disable_autoscheduler,
        autoscheduler_interval_seconds=args.autoscheduler_interval_seconds,
        autoscheduler_initial_delay_seconds=args.autoscheduler_initial_delay_seconds,
    )
    return 0


def cmd_mail_smoke(args: argparse.Namespace) -> int:
    settings = load_settings()
    runtime_settings = _runtime_settings(settings, dry_run=False, send_mail=args.send)
    result = run_mail_smoke(
        runtime_settings,
        send=args.send,
        confirm_real_send=args.confirm_real_send or "",
        title=args.title,
        body=args.body,
    )
    _print_result(result, args.json)
    if args.require_send_ready and not result["production_send_ready"]:
        return 2
    if args.send and result["send_status"] != "sent":
        return 2
    return 0 if result["status"] == "pass" else 2


def cmd_mail_unlock_check(args: argparse.Namespace) -> int:
    settings = load_settings()
    result = build_mail_unlock_check(settings)
    _print_result(result, args.json)
    if args.require_workflow_ready and not result["workflow_ready"]:
        return 2
    return 0 if result["status"] == "pass" else 2


def cmd_moomoo_smoke(args: argparse.Namespace) -> int:
    settings = load_settings()
    result = run_moomoo_smoke(
        settings,
        host=args.host,
        port=args.port,
        timeout=args.timeout,
        include_user_codex=not args.no_user_codex_scan,
        auto_start_opend=args.auto_start_opend,
        keep_auto_started_opend=args.keep_auto_started_opend,
        opend_wait_seconds=args.opend_wait_seconds,
    )
    _print_result(result, args.json)
    if args.require_ready and not result["production_ready_for_moomoo_data"]:
        return 2
    return 0


def cmd_collect_moomoo(args: argparse.Namespace) -> int:
    settings = load_settings()
    result = collect_moomoo_data(
        settings,
        args.symbol,
        start=args.start,
        end=args.end,
        ktype=args.ktype,
        host=args.host,
        port=args.port,
        include_snapshot=not args.no_snapshot,
        include_kline=not args.no_kline,
        auto_start_opend=args.auto_start_opend,
        cleanup_auto_started=args.cleanup_auto_started_opend,
        opend_wait_seconds=args.opend_wait_seconds,
    )
    _print_result(result, args.json)
    if args.require_success and result["status"] != "success":
        return 2
    return 0


def cmd_benchmark_smoke(args: argparse.Namespace) -> int:
    settings = load_settings()
    result = run_benchmark_smoke(
        settings,
        start=args.start,
        end=args.end,
        host=args.host,
        port=args.port,
        auto_start_opend=args.auto_start_opend,
        cleanup_auto_started=args.cleanup_auto_started_opend,
        opend_wait_seconds=args.opend_wait_seconds,
    )
    _print_result(result, args.json)
    if args.require_production and not result["production_ready"]:
        return 2
    return 0


def cmd_validate_intake(args: argparse.Namespace) -> int:
    settings = load_settings()
    scan_paths = [Path(path).expanduser() for path in args.scan_path]
    result = validate_intake(settings, scan_paths=scan_paths)
    _print_result(result, args.json)
    if args.require_production and not result["production_ready"]:
        return 2
    return 0


def cmd_normalize_alipay_positions(args: argparse.Namespace) -> int:
    settings = load_settings()
    result = normalize_alipay_positions(
        settings,
        csv_path=Path(args.csv),
        evidence=args.evidence,
        as_of=args.as_of,
        output_path=Path(args.output).expanduser() if args.output else None,
        write_pack=args.write_pack,
    )
    _print_result(result, args.json)
    if args.require_pass and result["status"] != "pass":
        return 2
    return 0


def cmd_normalize_fund_rules(args: argparse.Namespace) -> int:
    settings = load_settings()
    result = normalize_fund_rules(
        settings,
        csv_path=Path(args.csv),
        evidence=args.evidence,
        as_of=args.as_of,
        output_path=Path(args.output).expanduser() if args.output else None,
        write_pack=args.write_pack,
    )
    _print_result(result, args.json)
    if args.require_pass and result["status"] != "pass":
        return 2
    return 0


def cmd_normalize_candidates(args: argparse.Namespace) -> int:
    settings = load_settings()
    result = normalize_candidates(
        settings,
        csv_path=Path(args.csv),
        evidence=args.evidence,
        as_of=args.as_of,
        output_path=Path(args.output).expanduser() if args.output else None,
        write_pack=args.write_pack,
    )
    _print_result(result, args.json)
    if args.require_pass and result["status"] != "pass":
        return 2
    return 0


def cmd_normalize_intake_bundle(args: argparse.Namespace) -> int:
    settings = load_settings()
    result = normalize_intake_bundle(
        settings,
        alipay_csv=Path(args.alipay_csv).expanduser() if args.alipay_csv else None,
        fund_rules_csv=Path(args.fund_rules_csv).expanduser() if args.fund_rules_csv else None,
        candidates_csv=Path(args.candidates_csv).expanduser() if args.candidates_csv else None,
        alipay_evidence=args.alipay_evidence,
        fund_rules_evidence=args.fund_rules_evidence,
        candidates_evidence=args.candidates_evidence,
        as_of=args.as_of,
        write_pack=args.write_pack,
        audit_pack=not args.no_audit_pack,
        promote_dry_run=not args.no_promote_dry_run,
    )
    _print_result(result, args.json)
    if args.require_pass and result["status"] != "pass":
        return 2
    return 0


def cmd_production_intake_pack(args: argparse.Namespace) -> int:
    settings = load_settings()
    scan_paths = [Path(path).expanduser() for path in args.scan_path]
    result = build_production_intake_pack(settings, scan_paths=scan_paths)
    _print_result(result, args.json)
    if args.require_production and not result["production_ready"]:
        return 2
    return 0


def cmd_production_unblock_matrix(args: argparse.Namespace) -> int:
    settings = load_settings()
    scan_paths = [Path(path).expanduser() for path in args.scan_path]
    result = build_production_unblock_matrix(settings, scan_paths=scan_paths)
    _print_result(result, args.json)
    if args.require_production and not result["production_ready"]:
        return 2
    return 0


def cmd_production_action_queue(args: argparse.Namespace) -> int:
    settings = load_settings()
    scan_paths = [Path(path).expanduser() for path in args.scan_path]
    result = build_production_action_queue(settings, scan_paths=scan_paths)
    _print_result(result, args.json)
    if args.require_production and not result["production_ready"]:
        return 2
    return 0


def cmd_source_evidence_audit(args: argparse.Namespace) -> int:
    settings = load_settings()
    result = build_source_evidence_audit(
        settings,
        pack_dir=Path(args.pack_dir).expanduser() if args.pack_dir else None,
    )
    _print_result(result, args.json)
    if args.require_pass and result["status"] != "pass":
        return 2
    return 0


def cmd_platform_trade_check(args: argparse.Namespace) -> int:
    settings = load_settings()
    result = run_platform_trade_check(
        settings,
        asset_codes=args.asset_code,
        limit=args.limit,
        timeout_seconds=args.timeout_seconds,
        write_db=not args.no_sqlite,
    )
    _print_result(result, args.json)
    if args.require_pass and result["status"] != "pass":
        return 2
    return 0


def cmd_collect_fund_nav_history(args: argparse.Namespace) -> int:
    settings = load_settings()
    result = collect_fund_nav_history(
        settings,
        asset_codes=args.asset_code,
        start_date=args.start,
        end_date=args.end,
        timeout_seconds=args.timeout_seconds,
        workers=args.workers,
        apply=args.apply,
    )
    _print_result(result, args.json)
    if args.require_pass and result["status"] != "pass":
        return 2
    return 0


def cmd_promote_intake_pack(args: argparse.Namespace) -> int:
    settings = load_settings()
    scan_paths = [Path(path).expanduser() for path in args.scan_path]
    result = promote_intake_pack(
        settings,
        pack_dir=Path(args.pack_dir).expanduser() if args.pack_dir else None,
        apply=args.apply,
        scan_paths=scan_paths,
    )
    _print_result(result, args.json)
    if args.require_production and not result["production_ready"]:
        return 2
    if args.apply and not result["applied"]:
        return 2
    return 0


def cmd_production_unlock_check(args: argparse.Namespace) -> int:
    settings = load_settings()
    scan_paths = [Path(path).expanduser() for path in args.scan_path]
    result = run_production_unlock_check(
        settings,
        pack_dir=Path(args.pack_dir).expanduser() if args.pack_dir else None,
        apply=args.apply,
        scan_paths=scan_paths,
        package=args.package,
        full_diagnostics=args.full_diagnostics,
    )
    _print_result(result, args.json)
    if args.require_production and not result["production_ready"]:
        return 2
    if args.apply and not result["apply_performed"]:
        return 2
    return 0 if result["status"] == "pass" else 2


def cmd_discover_holdings(args: argparse.Namespace) -> int:
    settings = load_settings()
    scan_paths = [Path(path).expanduser() for path in args.scan_path]
    result = discover_holdings(settings, scan_paths=scan_paths)
    _print_result(result, args.json)
    if args.require_production_candidate and not result["production_ready_candidate_found"]:
        return 2
    return 0


def cmd_slots(args: argparse.Namespace) -> int:
    rows = []
    for slot in SCHEDULE_SLOTS:
        times = slot_times(slot)
        rows.append(
            {
                "slot": slot,
                "beijing": times.beijing.isoformat(timespec="seconds"),
                "australia_sydney": times.secondary.isoformat(timespec="seconds"),
            }
        )
    _print_result({"slots": rows}, args.json)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description="Serenity Daily Analysis MVP")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="Check local readiness")
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(func=cmd_doctor)

    init = sub.add_parser("init-db", help="Create or migrate SQLite schema")
    init.add_argument("--json", action="store_true")
    init.set_defaults(func=cmd_init_db)

    imp = sub.add_parser("import-alipay", help="Import Alipay holding CSV")
    imp.add_argument("--csv", required=True)
    imp.add_argument("--json", action="store_true")
    imp.set_defaults(func=cmd_import_alipay)

    run = sub.add_parser("run", help="Run one Beijing schedule slot")
    run.add_argument("--slot", required=True)
    run.add_argument("--at")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--no-dry-run", action="store_true")
    run.add_argument("--send-mail", action="store_true", help="Enable real Apple Mail send intent when not dry-run")
    run.add_argument("--json", action="store_true")
    run.set_defaults(func=cmd_run)

    report = sub.add_parser("report", help="Print report paths for a run")
    report.add_argument("--run-id")
    report.add_argument("--json", action="store_true")
    report.set_defaults(func=cmd_report)

    notify = sub.add_parser("notify", help="Render or send notification for a run")
    notify.add_argument("--run-id")
    notify.add_argument("--dry-run", action="store_true")
    notify.add_argument("--no-dry-run", action="store_true")
    notify.add_argument("--send-mail", action="store_true")
    notify.add_argument("--local", action="store_true", help="Send local macOS notification when not dry-run")
    notify.add_argument("--json", action="store_true")
    notify.set_defaults(func=cmd_notify)

    tick = sub.add_parser("scheduler-tick", help="Codex Automation/launchd dispatcher tick")
    tick.add_argument("--now", help="Override current time, e.g. 2026-06-12T14:30:00+08:00")
    tick.add_argument("--force-slot", choices=list(SCHEDULE_SLOTS))
    tick.add_argument("--tolerance-minutes", type=int, default=3)
    tick.add_argument("--allow-duplicate", action="store_true")
    tick.add_argument("--dry-run", action="store_true")
    tick.add_argument("--no-dry-run", action="store_true")
    tick.add_argument("--json", action="store_true")
    tick.set_defaults(func=cmd_scheduler_tick)

    auto_tick = sub.add_parser("automation-tick", help="Preflight-gated scheduler tick for Codex Automation or launchd")
    auto_tick.add_argument("--now", help="Override current time, e.g. 2026-06-12T14:30:00+08:00")
    auto_tick.add_argument("--force-slot", choices=list(SCHEDULE_SLOTS))
    auto_tick.add_argument("--tolerance-minutes", type=int, default=3)
    auto_tick.add_argument("--allow-duplicate", action="store_true")
    auto_tick.add_argument("--dry-run", action="store_true")
    auto_tick.add_argument("--no-dry-run", action="store_true")
    auto_tick.add_argument("--send-mail", action="store_true", help="Enable real Apple Mail send intent when production-ready and not dry-run")
    auto_tick.add_argument("--local", action="store_true", help="Send local macOS notification only when production-ready and not dry-run")
    auto_tick.add_argument("--scan-path", action="append", default=[], help="Optional filename-only scan for likely Alipay/fund files")
    auto_tick.add_argument("--require-production", action="store_true", help="Exit non-zero when due-slot preflight is not production-ready")
    auto_tick.add_argument("--json", action="store_true")
    auto_tick.set_defaults(func=cmd_automation_tick)

    preflight = sub.add_parser("preflight", help="Run production readiness checks")
    preflight.add_argument("--json", action="store_true")
    preflight.add_argument("--scan-path", action="append", default=[], help="Optional filename-only scan for likely Alipay/fund files")
    preflight.add_argument("--send-mail", action="store_true", help="Evaluate readiness for a runtime that intends real Apple Mail delivery")
    preflight.add_argument("--require-production", action="store_true", help="Exit non-zero when production blockers remain")
    preflight.set_defaults(func=cmd_preflight)

    completion_audit = sub.add_parser("completion-audit", help="Audit original delivery requirements against current evidence")
    completion_audit.add_argument("--require-complete", action="store_true", help="Exit non-zero when any completion blocker remains")
    completion_audit.add_argument("--json", action="store_true")
    completion_audit.set_defaults(func=cmd_completion_audit)

    history_integrity = sub.add_parser("history-integrity", help="Audit append-only historical rows and artifact hashes")
    history_integrity.add_argument("--baseline", help="History integrity baseline JSON; defaults to outputs/audit/history_integrity_baseline.json")
    history_integrity.add_argument("--write-baseline", action="store_true", help="Write the current manifest as baseline when no baseline exists")
    history_integrity.add_argument("--overwrite-baseline", action="store_true", help="Allow replacing an existing baseline only after explicit manual approval")
    history_integrity.add_argument("--require-pass", action="store_true", help="Exit non-zero when historical rows/files changed or baseline write is refused")
    history_integrity.add_argument("--json", action="store_true")
    history_integrity.set_defaults(func=cmd_history_integrity)

    risk_gate = sub.add_parser("risk-gate-regression", help="Generate deterministic MDD/recovery hard-risk-gate evidence")
    risk_gate.add_argument("--require-pass", action="store_true", help="Exit non-zero unless all hard-risk-gate regression cases pass")
    risk_gate.add_argument("--json", action="store_true")
    risk_gate.set_defaults(func=cmd_risk_gate_regression)

    package_delivery = sub.add_parser("package-delivery", help="Build final ZIP package while excluding private evidence by default")
    package_delivery.add_argument("--include-private-evidence", action="store_true", help="Include evidence/ and outputs/intake_pack/evidence/ in the ZIP")
    package_delivery.add_argument("--output", help="Optional ZIP output path")
    package_delivery.add_argument("--json", action="store_true")
    package_delivery.set_defaults(func=cmd_package_delivery)

    application_portal = sub.add_parser("application-portal", help="Render the Chinese local application portal from latest SQLite evidence")
    application_portal.add_argument("--json", action="store_true")
    application_portal.set_defaults(func=cmd_application_portal)

    application_server = sub.add_parser("application-server", help="Run the local Serenity application server with refresh API")
    application_server.add_argument("--host", default="127.0.0.1")
    application_server.add_argument("--port", type=int, default=8765)
    application_server.add_argument(
        "--ttl-seconds",
        type=int,
        default=None,
        help="Auto-stop the local server after this many seconds. Defaults to SERENITY_APPLICATION_SERVER_TTL_SECONDS or disabled; use 0 to disable.",
    )
    application_server.add_argument(
        "--disable-autoscheduler",
        action="store_true",
        help="Disable the in-process Serenity autoscheduler.",
    )
    application_server.add_argument(
        "--autoscheduler-interval-seconds",
        type=int,
        default=None,
        help="Seconds between automatic automation-tick checks. Defaults to SERENITY_APP_AUTOSCHEDULER_INTERVAL_SECONDS or 60.",
    )
    application_server.add_argument(
        "--autoscheduler-initial-delay-seconds",
        type=int,
        default=None,
        help="Delay before the first automatic automation-tick check. Defaults to SERENITY_APP_AUTOSCHEDULER_INITIAL_DELAY_SECONDS or 3.",
    )
    application_server.set_defaults(func=cmd_application_server)

    mail_smoke = sub.add_parser("mail-smoke", help="Controlled Apple Mail draft/send readiness smoke")
    mail_smoke.add_argument("--send", action="store_true", help="Attempt real Apple Mail send when confirmation allows it")
    mail_smoke.add_argument("--confirm-real-send", help="Must be exactly SEND when --send is used")
    mail_smoke.add_argument("--require-send-ready", action="store_true", help="Exit non-zero unless production mail send config is ready")
    mail_smoke.add_argument("--title", help="Optional smoke email subject")
    mail_smoke.add_argument("--body", help="Optional smoke email body")
    mail_smoke.add_argument("--json", action="store_true")
    mail_smoke.set_defaults(func=cmd_mail_smoke)

    mail_unlock = sub.add_parser("mail-unlock-check", help="Generate controlled Apple Mail production-send checklist and launchd review copy")
    mail_unlock.add_argument("--require-workflow-ready", action="store_true", help="Exit non-zero unless draft, Apple Mail, recipient, and launchd review copy are ready")
    mail_unlock.add_argument("--json", action="store_true")
    mail_unlock.set_defaults(func=cmd_mail_unlock_check)

    moomoo_smoke = sub.add_parser("moomoo-smoke", help="Diagnose moomoo_OpenD socket, SDK, and local workbench readiness")
    moomoo_smoke.add_argument("--json", action="store_true")
    moomoo_smoke.add_argument("--host", default="127.0.0.1")
    moomoo_smoke.add_argument("--port", type=int, default=11111)
    moomoo_smoke.add_argument("--timeout", type=float, default=0.5)
    moomoo_smoke.add_argument("--no-user-codex-scan", action="store_true", help="Only inspect this workspace for a workbench")
    moomoo_smoke.add_argument("--auto-start-opend", action="store_true", help="Start OpenD from a discovered workbench if the socket is closed")
    moomoo_smoke.add_argument("--keep-auto-started-opend", action="store_true", help="Do not close OpenD if this command had to start it")
    moomoo_smoke.add_argument("--cleanup-auto-started-opend", action="store_false", dest="keep_auto_started_opend", help=argparse.SUPPRESS)
    moomoo_smoke.add_argument("--opend-wait-seconds", type=float, default=20.0)
    moomoo_smoke.add_argument("--require-ready", action="store_true", help="Exit non-zero when socket or SDK is not ready")
    moomoo_smoke.set_defaults(keep_auto_started_opend=False)
    moomoo_smoke.set_defaults(func=cmd_moomoo_smoke)

    collect_moomoo = sub.add_parser("collect-moomoo", help="Collect read-only moomoo snapshot and historical K-line data")
    collect_moomoo.add_argument("--symbol", action="append", required=True, help="Moomoo symbol, e.g. US.AAPL; repeat for multiple")
    collect_moomoo.add_argument("--start", required=True, help="History start date YYYY-MM-DD")
    collect_moomoo.add_argument("--end", required=True, help="History end date YYYY-MM-DD")
    collect_moomoo.add_argument("--ktype", choices=sorted(KLINE_TYPES), default="K_DAY")
    collect_moomoo.add_argument("--host", default="127.0.0.1")
    collect_moomoo.add_argument("--port", type=int, default=11111)
    collect_moomoo.add_argument("--no-snapshot", action="store_true")
    collect_moomoo.add_argument("--no-kline", action="store_true")
    collect_moomoo.add_argument("--auto-start-opend", action="store_true", help="Start OpenD when the socket is closed; enabled by default")
    collect_moomoo.add_argument("--cleanup-auto-started-opend", action="store_true", help="Close only OpenD processes started by this command; enabled by default")
    collect_moomoo.add_argument("--no-auto-start-opend", action="store_false", dest="auto_start_opend", help=argparse.SUPPRESS)
    collect_moomoo.add_argument("--keep-auto-started-opend", action="store_false", dest="cleanup_auto_started_opend", help=argparse.SUPPRESS)
    collect_moomoo.add_argument("--opend-wait-seconds", type=float, default=20.0)
    collect_moomoo.add_argument("--require-success", action="store_true", help="Exit non-zero if any symbol/scope fails")
    collect_moomoo.add_argument("--json", action="store_true")
    collect_moomoo.set_defaults(auto_start_opend=True, cleanup_auto_started_opend=True)
    collect_moomoo.set_defaults(func=cmd_collect_moomoo)

    benchmark = sub.add_parser("benchmark-smoke", help="Validate benchmark source readiness for Shanghai Composite and S&P 500")
    benchmark.add_argument("--start", help="History start date YYYY-MM-DD; defaults to a dynamic 396-day lookback from the latest Beijing weekday")
    benchmark.add_argument("--end", help="History end date YYYY-MM-DD; defaults to the latest Beijing weekday")
    benchmark.add_argument("--host", default="127.0.0.1")
    benchmark.add_argument("--port", type=int, default=11111)
    benchmark.add_argument("--auto-start-opend", action="store_true", help="Start OpenD when the socket is closed; enabled by default")
    benchmark.add_argument("--cleanup-auto-started-opend", action="store_true", help="Close only OpenD processes started by this command; enabled by default")
    benchmark.add_argument("--no-auto-start-opend", action="store_false", dest="auto_start_opend", help=argparse.SUPPRESS)
    benchmark.add_argument("--keep-auto-started-opend", action="store_false", dest="cleanup_auto_started_opend", help=argparse.SUPPRESS)
    benchmark.add_argument("--opend-wait-seconds", type=float, default=20.0)
    benchmark.add_argument("--require-production", action="store_true", help="Exit non-zero unless both exact benchmark sources are ready")
    benchmark.add_argument("--json", action="store_true")
    benchmark.set_defaults(auto_start_opend=True, cleanup_auto_started_opend=True)
    benchmark.set_defaults(func=cmd_benchmark_smoke)

    validate = sub.add_parser("validate-intake", help="Validate production intake files and write gap reports")
    validate.add_argument("--scan-path", action="append", default=[], help="Optional scan path for likely holding/fund files")
    validate.add_argument("--require-production", action="store_true", help="Exit non-zero unless intake files are production-ready")
    validate.add_argument("--json", action="store_true")
    validate.set_defaults(func=cmd_validate_intake)

    normalize_alipay = sub.add_parser("normalize-alipay-positions", help="Normalize a current Alipay holdings/OCR CSV into canonical intake-pack format")
    normalize_alipay.add_argument("--csv", required=True, help="Source CSV exported/transcribed from current Alipay holdings")
    normalize_alipay.add_argument("--evidence", help="Optional evidence file or URL; defaults to copying the source CSV into outputs/intake_pack/evidence/")
    normalize_alipay.add_argument("--as-of", help="Fallback YYYY-MM-DD date when the source CSV has no date column")
    normalize_alipay.add_argument("--output", help="Optional output CSV path; defaults to outputs/intake_pack/01_alipay_positions_normalized_candidate.csv")
    normalize_alipay.add_argument("--write-pack", action="store_true", help="Write directly to outputs/intake_pack/01_alipay_positions_to_fill.csv")
    normalize_alipay.add_argument("--require-pass", action="store_true", help="Exit non-zero when required columns or values are missing")
    normalize_alipay.add_argument("--json", action="store_true")
    normalize_alipay.set_defaults(func=cmd_normalize_alipay_positions)

    normalize_rules = sub.add_parser("normalize-fund-rules", help="Normalize Alipay/fund-company rule OCR CSV into canonical intake-pack fund rules")
    normalize_rules.add_argument("--csv", required=True, help="Source CSV exported/transcribed from current fund rule/detail pages")
    normalize_rules.add_argument("--evidence", help="Optional evidence file or URL; defaults to copying the source CSV into outputs/intake_pack/evidence/")
    normalize_rules.add_argument("--as-of", help="Fallback YYYY-MM-DD date when the source CSV has no date column")
    normalize_rules.add_argument("--output", help="Optional output CSV path; defaults to outputs/intake_pack/02_fund_rules_normalized_candidate.csv")
    normalize_rules.add_argument("--write-pack", action="store_true", help="Write directly to outputs/intake_pack/02_fund_rules_to_fill.csv")
    normalize_rules.add_argument("--require-pass", action="store_true", help="Exit non-zero when required fields are missing")
    normalize_rules.add_argument("--json", action="store_true")
    normalize_rules.set_defaults(func=cmd_normalize_fund_rules)

    normalize_candidates_parser = sub.add_parser("normalize-candidates", help="Normalize candidate universe/source-chain CSV into canonical intake-pack candidates")
    normalize_candidates_parser.add_argument("--csv", required=True, help="Source CSV exported/transcribed from MooMoo, Alipay, fund-company, or official candidate evidence")
    normalize_candidates_parser.add_argument("--evidence", help="Optional evidence file or URL; defaults to copying the source CSV into outputs/intake_pack/evidence/")
    normalize_candidates_parser.add_argument("--as-of", help="Fallback YYYY-MM-DD date when the source CSV has no date column")
    normalize_candidates_parser.add_argument("--output", help="Optional output CSV path; defaults to outputs/intake_pack/03_candidates_normalized_candidate.csv")
    normalize_candidates_parser.add_argument("--write-pack", action="store_true", help="Write directly to outputs/intake_pack/03_candidates_to_fill.csv")
    normalize_candidates_parser.add_argument("--require-pass", action="store_true", help="Exit non-zero when required fields are missing")
    normalize_candidates_parser.add_argument("--json", action="store_true")
    normalize_candidates_parser.set_defaults(func=cmd_normalize_candidates)

    normalize_bundle = sub.add_parser("normalize-intake-bundle", help="Normalize holdings, fund rules, and candidates into a staged intake pack")
    normalize_bundle.add_argument("--alipay-csv", help="Current Alipay holdings CSV/OCR source")
    normalize_bundle.add_argument("--fund-rules-csv", help="Current Alipay/fund-company rule CSV/OCR source")
    normalize_bundle.add_argument("--candidates-csv", help="Current MooMoo/Alipay/official-source candidate CSV/OCR source")
    normalize_bundle.add_argument("--alipay-evidence", help="Optional evidence file or URL for Alipay holdings")
    normalize_bundle.add_argument("--fund-rules-evidence", help="Optional evidence file or URL for fund rules")
    normalize_bundle.add_argument("--candidates-evidence", help="Optional evidence file or URL for candidate universe")
    normalize_bundle.add_argument("--as-of", help="Fallback YYYY-MM-DD date when a source CSV has no date column")
    normalize_bundle.add_argument("--write-pack", action="store_true", help="Write normalized rows directly to outputs/intake_pack/01/02/03_to_fill.csv")
    normalize_bundle.add_argument("--no-audit-pack", action="store_true", help="Skip source-evidence-audit stage after --write-pack")
    normalize_bundle.add_argument("--no-promote-dry-run", action="store_true", help="Skip promote-intake-pack dry-run stage after --write-pack")
    normalize_bundle.add_argument("--require-pass", action="store_true", help="Exit non-zero unless all requested stages pass")
    normalize_bundle.add_argument("--json", action="store_true")
    normalize_bundle.set_defaults(func=cmd_normalize_intake_bundle)

    intake_pack = sub.add_parser("production-intake-pack", help="Create fill-ready files for production data intake")
    intake_pack.add_argument("--scan-path", action="append", default=[], help="Optional scan path for likely holding/fund files")
    intake_pack.add_argument("--require-production", action="store_true", help="Exit non-zero unless current intake is production-ready")
    intake_pack.add_argument("--json", action="store_true")
    intake_pack.set_defaults(func=cmd_production_intake_pack)

    unblock_matrix = sub.add_parser("production-unblock-matrix", help="Create field-level evidence matrix for remaining production blockers")
    unblock_matrix.add_argument("--scan-path", action="append", default=[], help="Optional scan path for likely holding/fund files")
    unblock_matrix.add_argument("--require-production", action="store_true", help="Exit non-zero unless current intake is production-ready")
    unblock_matrix.add_argument("--json", action="store_true")
    unblock_matrix.set_defaults(func=cmd_production_unblock_matrix)

    action_queue = sub.add_parser("production-action-queue", help="Create a prioritized No-New-Order queue for remaining production evidence work")
    action_queue.add_argument("--scan-path", action="append", default=[], help="Optional scan path for likely holding/fund files")
    action_queue.add_argument("--require-production", action="store_true", help="Exit non-zero unless current production gates are ready")
    action_queue.add_argument("--json", action="store_true")
    action_queue.set_defaults(func=cmd_production_action_queue)

    evidence_audit = sub.add_parser("source-evidence-audit", help="Audit source evidence references and hash local evidence files")
    evidence_audit.add_argument("--pack-dir", help="Audit an intake pack directory instead of production data files")
    evidence_audit.add_argument("--require-pass", action="store_true", help="Exit non-zero when any evidence reference is invalid")
    evidence_audit.add_argument("--json", action="store_true")
    evidence_audit.set_defaults(func=cmd_source_evidence_audit)

    platform_trade = sub.add_parser(
        "platform-trade-check",
        help="Fetch Alipay/official fund pages and archive advisory-only buy/sell availability evidence",
    )
    platform_trade.add_argument("--asset-code", action="append", help="Fund code to check; repeat for multiple")
    platform_trade.add_argument("--limit", type=int, help="Limit checked rows for controlled production smoke")
    platform_trade.add_argument("--timeout-seconds", type=float, default=8.0)
    platform_trade.add_argument("--no-sqlite", action="store_true", help="Write files only; do not append SQLite evidence rows")
    platform_trade.add_argument("--require-pass", action="store_true", help="Exit non-zero when any row needs manual review")
    platform_trade.add_argument("--json", action="store_true")
    platform_trade.set_defaults(func=cmd_platform_trade_check)

    fund_nav_history = sub.add_parser(
        "collect-fund-nav-history",
        help="Fetch 24-month candidate fund NAV history and optionally apply it to data/manual/price_history.csv",
    )
    fund_nav_history.add_argument("--asset-code", action="append", help="Fund code to fetch; repeat for multiple")
    fund_nav_history.add_argument("--start", help="Start date YYYY-MM-DD; default is >24-month lookback")
    fund_nav_history.add_argument("--end", help="End date YYYY-MM-DD; default is current Beijing date")
    fund_nav_history.add_argument("--timeout-seconds", type=float, default=12.0)
    fund_nav_history.add_argument("--workers", type=int, default=8, help="Concurrent page workers per fund")
    fund_nav_history.add_argument("--apply", action="store_true", help="Replace data/manual/price_history.csv after writing a backup")
    fund_nav_history.add_argument("--require-pass", action="store_true", help="Exit non-zero unless all candidates have 24-month NAV history")
    fund_nav_history.add_argument("--json", action="store_true")
    fund_nav_history.set_defaults(func=cmd_collect_fund_nav_history)

    promote_pack = sub.add_parser("promote-intake-pack", help="Validate and optionally promote filled intake pack CSVs into production inputs")
    promote_pack.add_argument("--pack-dir", help="Defaults to outputs/intake_pack")
    promote_pack.add_argument("--apply", action="store_true", help="Copy filled CSVs into data/imports and data/manual only after production validation passes")
    promote_pack.add_argument("--scan-path", action="append", default=[], help="Optional scan path for likely holding/fund files")
    promote_pack.add_argument("--require-production", action="store_true", help="Exit non-zero unless promoted/validated data is production-ready")
    promote_pack.add_argument("--json", action="store_true")
    promote_pack.set_defaults(func=cmd_promote_intake_pack)

    unlock_check = sub.add_parser("production-unlock-check", help="Run fail-closed evidence, promotion, preflight, completion, and optional package gates")
    unlock_check.add_argument("--pack-dir", help="Defaults to outputs/intake_pack")
    unlock_check.add_argument("--apply", action="store_true", help="Promote the filled intake pack only after dry-run and evidence checks pass")
    unlock_check.add_argument("--scan-path", action="append", default=[], help="Optional scan path for likely holding/fund files")
    unlock_check.add_argument("--package", action="store_true", help="Rebuild final ZIP after checks")
    unlock_check.add_argument(
        "--full-diagnostics",
        action="store_true",
        help="Continue read-only preflight and completion audit after pack blockers; never applies files by itself",
    )
    unlock_check.add_argument("--require-production", action="store_true", help="Exit non-zero unless preflight and completion audit are production-ready")
    unlock_check.add_argument("--json", action="store_true")
    unlock_check.set_defaults(func=cmd_production_unlock_check)

    holdings = sub.add_parser("discover-holdings", help="Discover local holding files and create review-only Alipay candidate CSV")
    holdings.add_argument("--scan-path", action="append", required=True, help="Path to scan for holding files")
    holdings.add_argument("--require-production-candidate", action="store_true", help="Exit non-zero unless a fresh production-grade holding file is found")
    holdings.add_argument("--json", action="store_true")
    holdings.set_defaults(func=cmd_discover_holdings)

    slots = sub.add_parser("slots", help="Show configured Beijing slots with Australia/Sydney display")
    slots.add_argument("--json", action="store_true")
    slots.set_defaults(func=cmd_slots)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
