from __future__ import annotations

import csv
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.adapters.alipay_importer import read_positions_csv
from app.adapters.manual_sources import load_candidates, load_fund_rules, load_price_history
from app.config import Settings
from app.core.benchmark_smoke import run_benchmark_smoke
from app.core.moomoo_smoke import run_moomoo_smoke
from app.core.run_visibility import is_future_controlled_backfill
from app.core.path_display import display_path, redact_value_for_markdown
from app.db import connect, init_db


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    severity: str
    message: str
    evidence: dict[str, object]


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def _contains_sample_marker(values: list[str]) -> bool:
    haystack = " ".join(value.lower() for value in values)
    return any(marker in haystack for marker in ["sample", "demo", "manual sample", "示例", "样例"])


def _check_moomoo(settings: Settings) -> CheckResult:
    smoke = run_moomoo_smoke(
        settings,
        auto_start_opend=False,
        keep_auto_started_opend=True,
        opend_wait_seconds=settings.opend_wait_seconds,
    )
    socket_probe = smoke["socket"]
    sdk_probe = smoke["sdk"]
    latest_failure_hint = smoke.get("latest_failure_hint")
    if smoke["production_ready_for_moomoo_data"]:
        status, severity = "pass", "info"
        message = f"{socket_probe['detail']}; {sdk_probe['detail']}"
    else:
        # Live OpenD availability is operationally useful, but benchmark_sources is
        # the authoritative production gate for benchmark readiness.
        status, severity = "warn", "warn"
        message = (
            f"{socket_probe['detail']}; {sdk_probe['detail']}. "
            "Live moomoo_OpenD is unavailable, so runtime should stay degraded for live collection, "
            "but benchmark_sources remains the production gate."
        )
        if latest_failure_hint:
            message = f"{message} Latest moomoo_OpenD log: {latest_failure_hint}"
    return CheckResult(
        name="moomoo_opend",
        status=status,
        severity=severity,
        message=message,
        evidence={
            "socket": socket_probe,
            "sdk": sdk_probe,
            "workbenches": smoke["workbenches"],
            "recommended_actions": smoke["recommended_actions"],
            "latest_failure_hint": latest_failure_hint,
            "opend_lifecycle": smoke.get("opend_lifecycle"),
            "cleanup": smoke.get("cleanup"),
            "auto_start_skipped_for_preflight": True,
            "production_dependency": False,
            "json_path": smoke.get("json_path"),
            "markdown_path": smoke.get("markdown_path"),
        },
    )


def _check_alipay(settings: Settings) -> CheckResult:
    path = settings.imports_dir / "alipay_positions.csv"
    if not path.exists():
        return CheckResult(
            "alipay_positions",
            "pass",
            "info",
            "Alipay positions CSV is optional; Serenity baseline is generated independently",
            {"path": str(path), "optional": True},
        )
    try:
        result = read_positions_csv(path)
    except Exception as exc:
        return CheckResult(
            "alipay_positions",
            "warn",
            "warn",
            f"Optional Alipay positions CSV cannot be imported: {exc}",
            {"path": str(path), "optional": True},
        )
    notes = [str(row.get("source_note", "")) for row in result.rows]
    sample = _contains_sample_marker(notes)
    status = "warn" if sample else "pass"
    severity = "warn" if sample else "info"
    message = (
        "Optional Alipay CSV appears to be sample data; ignored for production baseline"
        if sample
        else "Optional Alipay CSV import is available"
    )
    return CheckResult(
        "alipay_positions",
        status,
        severity,
        message,
        {
            "path": str(path),
            "rows": len(result.rows),
            "warnings": result.warnings,
            "sample_data": sample,
            "optional": True,
            "production_dependency": False,
            "as_of_values": sorted({str(row.get("as_of", "")) for row in result.rows}),
        },
    )


def _check_candidates(settings: Settings) -> CheckResult:
    path = settings.manual_dir / "candidates.csv"
    if not path.exists():
        return CheckResult("candidate_universe", "block", "critical", "Candidate universe missing", {"path": str(path)})
    candidates = load_candidates(path)
    sample = _contains_sample_marker(
        [candidate.source_name for candidate in candidates]
        + [candidate.source_url for candidate in candidates]
        + [candidate.asset_name for candidate in candidates]
    )
    if sample or all(candidate.source_url.startswith("data/") for candidate in candidates):
        return CheckResult(
            "candidate_universe",
            "block",
            "critical",
            "Candidate universe appears local/manual sample; usable for shadow run, not production conviction",
            {"path": str(path), "rows": len(candidates), "sample_like": True},
        )
    return CheckResult(
        "candidate_universe",
        "pass",
        "info",
        "Candidate universe has non-sample source references",
        {"path": str(path), "rows": len(candidates), "sample_like": False},
    )


def _check_candidate_nav_history(settings: Settings) -> CheckResult:
    candidates_path = settings.manual_dir / "candidates.csv"
    history_path = settings.manual_dir / "price_history.csv"
    if not candidates_path.exists() or not history_path.exists():
        return CheckResult(
            "candidate_nav_history",
            "block",
            "critical",
            "Candidate NAV history or candidate universe is missing",
            {"candidates_path": str(candidates_path), "history_path": str(history_path)},
        )
    candidates = [candidate for candidate in load_candidates(candidates_path) if not candidate.is_excluded]
    history = load_price_history(history_path)
    insufficient: list[dict[str, object]] = []
    for candidate in candidates:
        points = history.get(candidate.asset_code, [])
        span_days = (points[-1].date - points[0].date).days if len(points) >= 2 else 0
        if span_days < settings.min_candidate_nav_history_span_days:
            insufficient.append(
                {
                    "asset_code": candidate.asset_code,
                    "asset_name": candidate.asset_name,
                    "rows": len(points),
                    "span_days": span_days,
                }
            )
    if insufficient:
        return CheckResult(
            "candidate_nav_history",
            "block",
            "critical",
            (
                f"Candidate NAV history must cover {settings.min_candidate_nav_history_months} months; "
                f"{len(insufficient)} candidates are short"
            ),
            {
                "path": str(history_path),
                "min_months": settings.min_candidate_nav_history_months,
                "min_span_days": settings.min_candidate_nav_history_span_days,
                "insufficient": insufficient[:20],
            },
        )
    return CheckResult(
        "candidate_nav_history",
        "pass",
        "info",
        f"Candidate NAV history covers at least {settings.min_candidate_nav_history_months} months",
        {
            "path": str(history_path),
            "rows": sum(len(points) for points in history.values()),
            "min_span_days": settings.min_candidate_nav_history_span_days,
        },
    )


def _check_fund_rules(settings: Settings) -> CheckResult:
    path = settings.manual_dir / "fund_rules.csv"
    if not path.exists():
        return CheckResult("fund_rules", "block", "critical", "Fund rule snapshot missing", {"path": str(path)})
    rules = load_fund_rules(path)
    missing: list[str] = []
    sample_like = False
    for code, rule in rules.items():
        if rule.url_or_path.startswith("data/") or "manual" in rule.source_name.lower():
            sample_like = True
        for field in [
            "subscription_status",
            "redemption_status",
            "cutoff_time",
            "confirm_lag",
            "redeem_lag",
            "subscription_fee",
            "redemption_fee",
            "subscription_fee_schedule",
            "redemption_fee_schedule",
            "management_fee",
            "custody_fee",
        ]:
            value = getattr(rule, field)
            if value in (None, ""):
                missing.append(f"{code}.{field}")
    if missing:
        return CheckResult(
            "fund_rules",
            "block",
            "critical",
            "Fund rules have missing execution-critical fields",
            {"path": str(path), "rows": len(rules), "missing": missing[:30], "sample_like": sample_like},
        )
    if sample_like:
        return CheckResult(
            "fund_rules",
            "block",
            "critical",
            "Fund rules are sample/manual-local snapshots; replace with Alipay/fund official evidence before production",
            {"path": str(path), "rows": len(rules), "sample_like": sample_like},
        )
    return CheckResult("fund_rules", "pass", "info", "Fund rules ready", {"path": str(path), "rows": len(rules)})


def _check_mail(settings: Settings) -> CheckResult:
    osascript = shutil.which("osascript")
    if not osascript:
        status = "block" if settings.mail_send_enabled else "warn"
        return CheckResult(
            "apple_mail",
            status,
            "critical" if status == "block" else "warn",
            "osascript not found; Mail automation unavailable",
            {"mail_send_enabled": settings.mail_send_enabled},
        )
    result = subprocess.run(
        [osascript, "-e", 'id of application "Mail"'],
        capture_output=True,
        text=True,
        check=False,
    )
    app_available = result.returncode == 0
    status = "pass" if app_available else ("block" if settings.mail_send_enabled else "warn")
    return CheckResult(
        "apple_mail",
        status,
        "info" if app_available else ("critical" if status == "block" else "warn"),
        "Apple Mail is script-addressable" if app_available else "Apple Mail is not script-addressable",
        {
            "mail_send_enabled": settings.mail_send_enabled,
            "osascript": osascript,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        },
    )


def _check_mail_send_config(settings: Settings) -> CheckResult:
    if not settings.recipient_email:
        return CheckResult(
            "mail_send_config",
            "block",
            "critical",
            "Production alert recipient email is missing",
            {
                "mail_send_enabled": settings.mail_send_enabled,
                "recipient_email": settings.recipient_email,
                "activation_hint": "--send-mail",
            },
        )
    if not settings.mail_send_enabled:
        return CheckResult(
            "mail_send_config",
            "block",
            "critical",
            "Real Apple Mail sending is not enabled for this runtime; production rebalance alerts would remain draft-only",
            {
                "mail_send_enabled": settings.mail_send_enabled,
                "recipient_email": settings.recipient_email,
                "activation_hint": "--send-mail",
            },
        )
    return CheckResult(
        "mail_send_config",
        "pass",
        "info",
        "Real Apple Mail sending is enabled for this runtime",
        {
            "mail_send_enabled": settings.mail_send_enabled,
            "recipient_email": settings.recipient_email,
            "activation_hint": "--send-mail",
        },
    )


def _check_scheduler(settings: Settings) -> CheckResult:
    plist = settings.root_dir / "outputs" / "implementation" / "com.serenity.daily-analysis.plist"
    manifest = settings.root_dir / "outputs" / "implementation" / "automation_manifest.json"
    missing = [str(path) for path in [plist, manifest] if not path.exists()]
    return CheckResult(
        "scheduler_artifacts",
        "block" if missing else "pass",
        "critical" if missing else "info",
        "Scheduler artifacts missing" if missing else "Scheduler artifacts present",
        {"missing": missing, "plist": str(plist), "manifest": str(manifest)},
    )


def _check_latest_run(settings: Settings) -> CheckResult:
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        rows = conn.execute(
            """
            SELECT run_id, status, data_quality_status, report_path, run_time_bj, created_at
            FROM run_log
            WHERE report_path IS NOT NULL
              AND schedule_slot LIKE 'R%'
            ORDER BY run_time_bj DESC, created_at DESC, rowid DESC
            LIMIT 12
            """
        ).fetchall()
        visible_rows = [
            item for item in rows if not is_future_controlled_backfill(item["run_time_bj"], item["created_at"])
        ]
        row = (visible_rows or rows or [None])[0]
    if not row:
        return CheckResult("latest_shadow_run", "warn", "warn", "No shadow run report found", {})
    status = "pass" if row["status"] == "success" and row["data_quality_status"] == "pass" else "warn"
    return CheckResult(
        "latest_shadow_run",
        status,
        "info" if status == "pass" else "warn",
        f"Latest run is {row['status']}/{row['data_quality_status']}",
        dict(row),
    )


def _check_benchmarks(settings: Settings) -> CheckResult:
    smoke = run_benchmark_smoke(settings, auto_start_opend=False, cleanup_auto_started=False)
    if smoke["production_ready"]:
        status, severity = "pass", "info"
        message = "Benchmark sources are production-ready"
    else:
        status, severity = "block", "critical"
        blocked = [
            name
            for name, ready in dict(smoke["production_ready_by_benchmark"]).items()
            if not ready
        ]
        message = "Benchmark sources are not production-ready: " + ", ".join(sorted(blocked))
    return CheckResult(
        "benchmark_sources",
        status,
        severity,
        message,
        {
            "production_ready_by_benchmark": smoke["production_ready_by_benchmark"],
            "proxy_available": smoke["proxy_available"],
            "auto_start_skipped_for_preflight": True,
            "json_path": smoke.get("json_path"),
            "markdown_path": smoke.get("markdown_path"),
        },
    )


def _scan_candidates(paths: list[Path]) -> list[dict[str, str]]:
    matches: list[dict[str, str]] = []
    patterns = ["alipay", "支付宝", "fund", "基金", "holding", "持仓"]
    for root in paths:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".csv", ".xlsx", ".xls", ".json"}:
                continue
            name = path.name.lower()
            if any(pattern.lower() in name for pattern in patterns):
                matches.append({"path": str(path), "name": path.name})
                if len(matches) >= 50:
                    return matches
    return matches


def _compact_evidence(settings: Settings, evidence: dict[str, object]) -> str:
    keys = [
        "missing",
        "sample_data",
        "sample_like",
        "production_ready_by_benchmark",
        "proxy_available",
        "rows",
        "path",
        "min_months",
        "min_span_days",
        "insufficient",
        "json_path",
        "markdown_path",
        "mail_send_enabled",
        "recipient_email",
        "env_var",
    ]
    compact = {key: evidence[key] for key in keys if key in evidence}
    if not compact:
        return ""
    return json.dumps(redact_value_for_markdown(settings.root_dir, compact), ensure_ascii=False, sort_keys=True)


def run_preflight(settings: Settings, scan_paths: list[Path] | None = None) -> dict[str, object]:
    settings.ensure_dirs()
    checks = [
        _check_moomoo(settings),
        _check_alipay(settings),
        _check_candidates(settings),
        _check_candidate_nav_history(settings),
        _check_fund_rules(settings),
        _check_benchmarks(settings),
        _check_mail(settings),
        _check_mail_send_config(settings),
        _check_scheduler(settings),
        _check_latest_run(settings),
    ]
    blockers = [check for check in checks if check.status == "block"]
    warnings = [check for check in checks if check.status == "warn"]
    production_ready = not blockers
    shadow_ready = not any(check.name in {"scheduler_artifacts"} and check.status == "block" for check in checks)
    scanned = _scan_candidates(scan_paths or [])
    result = {
        "generated_at": _now(settings),
        "production_ready": production_ready,
        "shadow_ready": shadow_ready,
        "status": "pass" if production_ready else "blocked",
        "blockers": [asdict(check) for check in blockers],
        "warnings": [asdict(check) for check in warnings],
        "checks": [asdict(check) for check in checks],
        "candidate_files_found": scanned,
    }
    output_dir = settings.root_dir / "outputs" / "preflight"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "preflight_latest.json"
    md_path = output_dir / "preflight_latest.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    md_lines = [
        "# Serenity Production Preflight",
        "",
        f"- Generated at: {result['generated_at']}",
        f"- Production ready: {production_ready}",
        f"- Shadow ready: {shadow_ready}",
        "",
        "## Blockers",
        "",
    ]
    if blockers:
        for check in blockers:
            md_lines.append(f"- **{check.name}**: {check.message}")
            evidence = _compact_evidence(settings, check.evidence)
            if evidence:
                md_lines.append(f"  - Evidence: `{evidence}`")
    else:
        md_lines.append("- None")
    md_lines.extend(["", "## Warnings", ""])
    if warnings:
        for check in warnings:
            md_lines.append(f"- **{check.name}**: {check.message}")
            evidence = _compact_evidence(settings, check.evidence)
            if evidence:
                md_lines.append(f"  - Evidence: `{evidence}`")
    else:
        md_lines.append("- None")
    md_lines.extend(["", "## Candidate Files Found", ""])
    if scanned:
        for item in scanned:
            md_lines.append(f"- {display_path(settings.root_dir, item['path'])}")
    else:
        md_lines.append("- None")
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    result["json_path"] = str(json_path)
    result["markdown_path"] = str(md_path)
    return result
