from __future__ import annotations

import importlib
import json
import tomllib
from datetime import date
from pathlib import Path

from src.accounting.alipay_ledger import alipay_execution_state, summarize_updates
from src.config import ROOT
from src.data_io import read_csv
from src.integrations.moomoo_desktop import (
    MOOMOO_APP_PATH,
    _find_watchlist_db,
    _load_opend_config,
    _port_open,
    _read_watchlist_rows,
)
from src.integrations.policy_system_bridge import EVENT_DIR as POLICY_EVENT_DIR
from src.integrations.policy_system_bridge import STATUS_DIR as POLICY_STATUS_DIR
from src.reporting.paths import pdf_path
from src.reporting.quality_gate import report_name_for_kind, week_report_status


SUPPORTED_QUOTE_EXCHANGES = {"US", "SSE", "SZSE", "SEHK"}


def build_automation_health(
    as_of: str,
    *,
    run_quality: bool = True,
    strict_opend: bool = False,
    min_opend_coverage: float = 0.0,
    preflight: bool = False,
    require_execution_ready: bool = False,
) -> dict[str, object]:
    checks = []
    checks.extend(_runtime_checks())
    checks.append(_automation_prompt_check())
    checks.extend(_moomoo_checks(preflight=preflight))
    week_status_check = _week_status_check(as_of, run_quality=run_quality, preflight=preflight)
    current_day_report_exists = _current_day_report_artifact_exists(as_of)
    due_bad = []
    week_details = week_status_check.get("details") if isinstance(week_status_check.get("details"), dict) else {}
    if isinstance(week_details.get("due_bad"), list):
        due_bad = week_details["due_bad"]
    snapshot_check = _snapshot_check(
        as_of,
        strict_opend=strict_opend,
        min_opend_coverage=min_opend_coverage,
        preflight=preflight,
        require_actionable_snapshot=bool(due_bad) or current_day_report_exists,
    )
    checks.append(snapshot_check)
    alipay_check = _alipay_check(as_of)
    checks.append(alipay_check)
    checks.append(_policy_bridge_check(as_of, preflight=preflight))
    checks.append(week_status_check)
    checks.append(
        _trade_execution_readiness_check(
            snapshot_check,
            alipay_check,
            week_status_check,
            require_execution_ready=require_execution_ready,
        )
    )
    status = _overall_status(checks)
    return {
        "date": as_of,
        "status": status,
        "require_execution_ready": require_execution_ready,
        "checks": checks,
    }


def _runtime_checks() -> list[dict[str, object]]:
    checks = []
    missing = []
    for module in ["certifi", "matplotlib", "reportlab"]:
        try:
            importlib.import_module(module)
        except Exception as exc:  # pragma: no cover - environment dependent
            missing.append(f"{module}: {exc}")
    checks.append(
        {
            "name": "runtime_dependencies",
            "status": "pass" if not missing else "fail",
            "summary": "Python runtime has report dependencies." if not missing else "Python runtime misses report dependencies.",
            "details": {"missing": missing},
        }
    )
    return checks


REPORT_AUTOMATION_IDS = ["ai", "ai-1", "ai-2", "ai-3", "ai-4", "ai-4k"]
REQUIRED_AUTOMATION_PROMPT_TERMS = [
    "Volume依据",
    "fixed 8% style sizing",
    "Translate internal PFIOS labels to Chinese",
    "No internal local paths in PDF body",
    "local request/report paths",
    "Do not backfill or regenerate reports dated before TODAY",
]
FORBIDDEN_AUTOMATION_PROMPT_TERMS = [
    "separate crawler request path",
    "policy system report path",
    "按Volume上限",
    "买入降额",
    "卖出减半",
    "50% Volume",
]


def _automation_prompt_check(automation_root: Path | None = None) -> dict[str, object]:
    root = automation_root or (Path.home() / ".codex" / "automations")
    issues: list[str] = []
    checked: list[str] = []
    missing: list[str] = []
    for automation_id in REPORT_AUTOMATION_IDS:
        path = root / automation_id / "automation.toml"
        if not path.exists():
            missing.append(automation_id)
            issues.append(f"missing_automation:{automation_id}")
            continue
        checked.append(automation_id)
        try:
            payload = tomllib.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            issues.append(f"invalid_toml:{automation_id}:{exc}")
            continue
        prompt = str(payload.get("prompt") or "")
        for term in REQUIRED_AUTOMATION_PROMPT_TERMS:
            if term not in prompt:
                issues.append(f"missing_prompt_term:{automation_id}:{term}")
        for term in FORBIDDEN_AUTOMATION_PROMPT_TERMS:
            if term in prompt:
                issues.append(f"forbidden_prompt_term:{automation_id}:{term}")
        if payload.get("model") != "gpt-5.5":
            issues.append(f"model_not_5_5:{automation_id}:{payload.get('model')}")
        if payload.get("reasoning_effort") != "xhigh":
            issues.append(f"reasoning_not_xhigh:{automation_id}:{payload.get('reasoning_effort')}")
    status = "pass" if not issues else "fail"
    return {
        "name": "automation_prompt_sync",
        "status": status,
        "summary": "Report automation prompts are synchronized with current report rules." if not issues else (
            f"Report automation prompt sync has {len(issues)} issue(s)."
        ),
        "details": {
            "automation_root": str(root),
            "checked": checked,
            "missing": missing,
            "required_terms": REQUIRED_AUTOMATION_PROMPT_TERMS,
            "forbidden_terms": FORBIDDEN_AUTOMATION_PROMPT_TERMS,
            "issues": issues,
        },
    }


def _moomoo_checks(*, preflight: bool = False) -> list[dict[str, object]]:
    checks = [
        {
            "name": "moomoo_app",
            "status": "pass" if MOOMOO_APP_PATH.exists() else "fail",
            "summary": f"moomoo app path: {MOOMOO_APP_PATH}",
            "details": {"path": str(MOOMOO_APP_PATH)},
        }
    ]
    try:
        config = _load_opend_config()
        host = str(config["opend"]["host"])
        port = int(config["opend"]["port"])
        open_port = _port_open(host, port)
        port_status = "pass" if open_port else "warn" if preflight else "fail"
        checks.append(
            {
                "name": "opend_port",
                "status": port_status,
                "summary": f"OpenD port {'reachable' if open_port else 'not reachable'} at {host}:{port}.",
                "details": {"host": host, "port": port, "preflight": preflight},
            }
        )
    except Exception as exc:
        checks.append(
            {
                "name": "opend_port",
                "status": "fail",
                "summary": "OpenD config or port check failed.",
                "details": {"error": str(exc)},
            }
        )
    try:
        watchlist_db = _find_watchlist_db()
        rows = _read_watchlist_rows(watchlist_db, "全部")
        checks.append(
            {
                "name": "moomoo_watchlist_db",
                "status": "pass" if rows else "fail",
                "summary": f"Read {len(rows)} moomoo watchlist rows.",
                "details": {"watchlist_db": str(watchlist_db), "rows": len(rows)},
            }
        )
    except Exception as exc:
        checks.append(
            {
                "name": "moomoo_watchlist_db",
                "status": "fail",
                "summary": "moomoo watchlist database is not readable.",
                "details": {"error": str(exc)},
            }
        )
    return checks


def _snapshot_check(
    as_of: str,
    *,
    strict_opend: bool,
    min_opend_coverage: float,
    preflight: bool = False,
    require_actionable_snapshot: bool = True,
) -> dict[str, object]:
    watchlist = _read_csv(ROOT / "data" / "sample" / "watchlist_moomoo.csv")
    snapshot = _read_csv(ROOT / "data" / "sample" / "watchlist_snapshot.csv")
    supported = {
        row.get("symbol", "")
        for row in watchlist
        if row.get("asset_class") in {"Stock", "ETF", "Index"} and row.get("exchange") in SUPPORTED_QUOTE_EXCHANGES
    }
    latest: dict[str, dict[str, str]] = {}
    for row in snapshot:
        symbol = row.get("symbol", "")
        if symbol not in supported:
            continue
        current = latest.get(symbol)
        if current is None or row.get("date", "") > current.get("date", ""):
            latest[symbol] = row
    missing = sorted(symbol for symbol in supported if symbol not in latest)
    stale = sorted(symbol for symbol, row in latest.items() if row.get("date") != as_of)
    missing_price = sorted(symbol for symbol, row in latest.items() if not row.get("close"))
    source_counts: dict[str, int] = {}
    for row in latest.values():
        source = row.get("source_name", "未标注")
        source_counts[source] = source_counts.get(source, 0) + 1
    diagnostics = _read_opend_diagnostics(as_of)
    diagnostic_counts: dict[str, int] = {}
    permission_symbols = []
    fallback_symbols = []
    unsupported_symbols = []
    for row in diagnostics:
        category = row.get("opend_error_category", "")
        if category:
            diagnostic_counts[category] = diagnostic_counts.get(category, 0) + 1
        if category == "quote_permission":
            permission_symbols.append(row.get("symbol", ""))
        if row.get("fallback_status") == "used":
            fallback_symbols.append(row.get("symbol", ""))
        if row.get("opend_status") == "unsupported":
            unsupported_symbols.append(row.get("symbol", ""))
    opend_count = source_counts.get("Moomoo OpenD", 0)
    coverage = opend_count / max(1, len(supported))
    fallback_count = max(0, len(latest) - opend_count)
    issues = []
    if missing:
        issues.append("missing_snapshot")
    if stale:
        issues.append("stale_snapshot")
    if missing_price:
        issues.append("missing_price")
    if strict_opend and coverage < 1:
        issues.append("strict_opend_coverage")
    if coverage < min_opend_coverage:
        issues.append("below_min_opend_coverage")
    status = "pass"
    blocking_issues = set(issues)
    if preflight or not require_actionable_snapshot:
        blocking_issues -= {"missing_snapshot", "stale_snapshot", "missing_price"}
    if any(issue in blocking_issues for issue in ["missing_snapshot", "stale_snapshot", "missing_price", "strict_opend_coverage", "below_min_opend_coverage"]):
        status = "fail"
    elif fallback_count or issues:
        status = "warn"
    return {
        "name": "quote_snapshot",
        "status": status,
        "summary": f"Quote snapshot coverage: supported={len(supported)}, rows={len(latest)}, opend={opend_count}, fallback={fallback_count}, opend_coverage={coverage:.3f}.",
        "details": {
            "supported_symbols": sorted(supported),
            "missing": missing,
            "stale": stale,
            "missing_price": missing_price,
            "source_counts": dict(sorted(source_counts.items())),
            "opend_diagnostic_path": str(_opend_diagnostics_path(as_of)),
            "opend_diagnostic_counts": dict(sorted(diagnostic_counts.items())),
            "opend_permission_symbols": sorted(symbol for symbol in permission_symbols if symbol),
            "fallback_symbols": sorted(symbol for symbol in fallback_symbols if symbol),
            "unsupported_symbols": sorted(symbol for symbol in unsupported_symbols if symbol),
            "opend_coverage": round(coverage, 6),
            "strict_opend": strict_opend,
            "min_opend_coverage": min_opend_coverage,
            "preflight": preflight,
            "require_actionable_snapshot": require_actionable_snapshot,
            "issues": issues,
        },
    }


def _alipay_check(as_of: str) -> dict[str, object]:
    summary = summarize_updates(start_date=as_of, end_date=as_of)
    missing_days = summary.missing_dates
    execution = alipay_execution_state(summary, as_of)
    execution_blocked = bool(execution.get("execution_blocked"))
    execution_status = str(execution.get("status") or "")
    if missing_days:
        status = "warn"
        text = f"Alipay update missing for {', '.join(missing_days)}."
    elif execution_status == "missing" or summary.updated_count == 0:
        status = "warn"
        text = f"Alipay update missing or unconfirmed for {as_of}: {execution.get('block_reason')}."
    elif execution_blocked:
        status = "warn"
        text = f"Alipay update exists but execution amounts are blocked: {execution.get('block_reason')}."
    else:
        status = "pass"
        text = "Alipay update exists and is confirmed for report execution calculations."
    return {
        "name": "alipay_update",
        "status": status,
        "summary": text,
        "details": {
            "start_date": summary.start_date,
            "end_date": summary.end_date,
            "updated_dates": summary.updated_dates,
            "missing_dates": summary.missing_dates,
            "updated_count": summary.updated_count,
            "missing_count": summary.missing_count,
            "execution_status": execution.get("status", ""),
            "execution_blocked": execution_blocked,
            "execution_confirmed": execution.get("execution_confirmed", False),
            "block_reason": execution.get("block_reason", ""),
            "source_type": execution.get("source_type", ""),
            "source_path": execution.get("source_path", ""),
        },
    }


def _policy_bridge_check(as_of: str, *, preflight: bool = False) -> dict[str, object]:
    status_path = POLICY_STATUS_DIR / f"policy_bridge_status_{as_of}.json"
    event_path = POLICY_EVENT_DIR / f"policy_events_{as_of}.csv"
    report_exists = _current_day_report_artifact_exists(as_of)
    if not status_path.exists():
        status = "fail" if report_exists and not preflight else "warn"
        return {
            "name": "policy_bridge",
            "status": status,
            "summary": f"Policy bridge status missing for {as_of}.",
            "details": {
                "status_path": str(status_path),
                "event_path": str(event_path),
                "preflight": preflight,
                "current_day_report_artifact_exists": report_exists,
                "refresh_status": "missing",
                "issues": ["missing_policy_bridge_status"],
            },
        }
    issues: list[str] = []
    try:
        payload = json.loads(status_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "name": "policy_bridge",
            "status": "fail",
            "summary": "Policy bridge status JSON is unreadable.",
            "details": {
                "status_path": str(status_path),
                "event_path": str(event_path),
            "preflight": preflight,
            "current_day_report_artifact_exists": report_exists,
            "error": str(exc),
            "issues": ["invalid_policy_bridge_status_json"],
            },
        }
    refresh = payload.get("refresh") or {}
    refresh_status = str(refresh.get("status") or "unknown") if isinstance(refresh, dict) else "unknown"
    if refresh_status not in {"refreshed", "cached_refreshed"}:
        issues.append("policy_refresh_not_confirmed")
    matched_event_count = int(payload.get("matched_event_count") or 0)
    events = _read_csv(event_path)
    policy_events = [row for row in events if row.get("type") == "government_policy_bridge"]
    source_events = [row for row in policy_events if _has_original_source(row.get("source_url", ""))]
    non_no_match_events = [row for row in policy_events if row.get("policy_match_basis") != "no_high_relevance_policy_match"]
    if matched_event_count and not event_path.exists():
        issues.append("missing_policy_event_log")
    if non_no_match_events and not source_events:
        issues.append("policy_events_without_original_source")
    for row in non_no_match_events:
        if row.get("policy_original_fetch_status") != "verified":
            issues.append("policy_event_without_verified_original_fetch_status")
        if not row.get("policy_request_path"):
            issues.append("policy_event_without_separate_crawler_request")
        if not row.get("policy_operation_impact"):
            issues.append("policy_event_without_operation_impact")
        if refresh_status in {"refreshed", "cached_refreshed"} and not row.get("policy_report_path"):
            issues.append("policy_event_without_policy_report_path")
    if preflight:
        status = "warn" if issues else "pass"
    else:
        status = "fail" if issues else "pass"
    summary = (
        f"Policy bridge refresh={refresh_status}, matched_events={matched_event_count}, "
        f"logged_policy_events={len(policy_events)}, original_source_events={len(source_events)}."
    )
    return {
        "name": "policy_bridge",
        "status": status,
        "summary": summary,
        "details": {
            "status_path": str(status_path),
            "event_path": str(event_path),
            "preflight": preflight,
            "current_day_report_artifact_exists": report_exists,
            "refresh_status": refresh_status,
            "matched_event_count": matched_event_count,
            "logged_policy_events": len(policy_events),
            "original_source_events": len(source_events),
            "issues": issues,
        },
    }


def _has_original_source(value: object) -> bool:
    url = str(value or "")
    if not url or "example.com" in url:
        return False
    return url.startswith("https://") or url.startswith("http://")


def _current_day_report_artifact_exists(as_of: str) -> bool:
    kinds = ["pre_open", "midday", "post_close", "kline"]
    try:
        day = date.fromisoformat(as_of)
    except ValueError:
        day = None
    if day and day.weekday() == 0:
        kinds.append("monday_pre_open")
    if day and day.weekday() == 4:
        kinds.append("friday_post_close")
    for kind in kinds:
        try:
            if pdf_path(report_name_for_kind(kind, as_of) + ".pdf").exists():
                return True
        except ValueError:
            continue
    return False


def _week_status_check(as_of: str, *, run_quality: bool, preflight: bool = False) -> dict[str, object]:
    payload = week_report_status(as_of=as_of, through_date=as_of, run_quality=run_quality)
    due_bad = [
        row
        for row in payload["reports"]
        if row["report_date"] == as_of and row["status"] in {"missing", "quality_fail"}
    ]
    folder_issues = payload.get("folder_issues", [])
    if not due_bad and not folder_issues:
        status = "pass"
    elif preflight:
        status = "warn"
    else:
        status = "fail"
    return {
        "name": "week_report_status",
        "status": status,
        "summary": f"Week status counts: {payload['status_counts']}.",
        "details": {
            "week_folder": payload["week_folder"],
            "status_counts": payload["status_counts"],
            "folder_issues": folder_issues,
            "preflight": preflight,
            "due_bad": [
                {
                    "report_date": row["report_date"],
                    "report_kind": row["report_kind"],
                    "status": row["status"],
                    "pdf_name": row["pdf_name"],
                    "issues": row["issues"],
                }
                for row in due_bad
            ],
        },
    }


def _trade_execution_readiness_check(
    snapshot_check: dict[str, object],
    alipay_check: dict[str, object],
    week_status_check: dict[str, object],
    *,
    require_execution_ready: bool = False,
) -> dict[str, object]:
    snapshot_details = snapshot_check.get("details") if isinstance(snapshot_check.get("details"), dict) else {}
    alipay_details = alipay_check.get("details") if isinstance(alipay_check.get("details"), dict) else {}
    week_details = week_status_check.get("details") if isinstance(week_status_check.get("details"), dict) else {}

    blockers: list[str] = []
    warnings: list[str] = []

    if alipay_details.get("execution_blocked"):
        blockers.append("alipay_execution_blocked")
    if alipay_details.get("missing_count"):
        blockers.append("alipay_update_missing")
    if week_details.get("due_bad"):
        blockers.append("current_due_report_missing_or_quality_failed")
    if snapshot_check.get("status") == "fail":
        blockers.append("quote_snapshot_not_actionable")
    elif snapshot_details.get("opend_coverage", 0.0) < 1:
        warnings.append("quote_snapshot_uses_fallback_sources")

    execution_ready = not blockers
    if execution_ready:
        status = "pass" if not warnings else "warn"
        summary = "Report is generated; trade execution amounts are ready." if not warnings else (
            "Report is generated and execution is not blocked, but quote snapshot still uses fallback sources."
        )
    else:
        status = "fail" if require_execution_ready else "warn"
        summary = "Report may be usable for research, but trade execution amounts are not ready."

    return {
        "name": "trade_execution_readiness",
        "status": status,
        "summary": summary,
        "details": {
            "execution_ready": execution_ready,
            "require_execution_ready": require_execution_ready,
            "blockers": blockers,
            "warnings": warnings,
            "alipay_execution_status": alipay_details.get("execution_status", ""),
            "alipay_block_reason": alipay_details.get("block_reason", ""),
            "quote_opend_coverage": snapshot_details.get("opend_coverage", 0.0),
            "quote_source_counts": snapshot_details.get("source_counts", {}),
            "due_bad": week_details.get("due_bad", []),
        },
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    return read_csv(path) if path.exists() else []


def _opend_diagnostics_path(as_of: str) -> Path:
    return ROOT / "data" / "sample" / f"opend_quote_diagnostics_{as_of}.csv"


def _read_opend_diagnostics(as_of: str) -> list[dict[str, str]]:
    return _read_csv(_opend_diagnostics_path(as_of))


def _overall_status(checks: list[dict[str, object]]) -> str:
    statuses = {str(check["status"]) for check in checks}
    if "fail" in statuses:
        return "fail"
    if "warn" in statuses:
        return "warn"
    return "pass"


def format_automation_health(payload: dict[str, object]) -> str:
    lines = [f"AUTOMATION_HEALTH: {payload['date']} status={payload['status']}"]
    for check in payload["checks"]:
        lines.append(f"{str(check['status']).upper()}: {check['name']} - {check['summary']}")
    return "\n".join(lines)


def write_automation_health_log(payload: dict[str, object]) -> Path:
    suffix = "_execution_ready_required" if payload.get("require_execution_ready") else ""
    path = ROOT / "data" / "report_artifacts" / "automation_logs" / f"automation_health_{payload['date']}{suffix}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
