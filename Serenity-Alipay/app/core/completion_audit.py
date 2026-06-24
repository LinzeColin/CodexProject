from __future__ import annotations

import csv
import fnmatch
import json
import plistlib
import re
import sqlite3
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from app.adapters.manual_sources import PricePoint
from app.config import Settings
from app.db import connect, init_db
from app.core.history_integrity import run_history_integrity
from app.core.metrics import WINDOWS, calculate_returns
from app.core.path_display import display_path, redact_text_for_markdown
from app.core.packaging import PRIVATE_EVIDENCE_EXCLUDES
from app.core.run_visibility import is_future_controlled_backfill
from app.scheduler import SCHEDULE_SLOTS, due_slot_at


EXPECTED_SLOTS = {
    "R1": "08:30",
    "R2": "09:30",
    "R3": "10:30",
    "R4": "11:30",
    "R5": "12:30",
    "R6": "13:30",
    "R7": "14:30",
    "R8": "15:30",
    "R9": "16:30",
    "R10": "17:30",
}

REQUIRED_TABLES = {
    "run_log",
    "asset_master",
    "source_log",
    "fund_nav_snapshot",
    "market_kline_snapshot",
    "fund_rule_snapshot",
    "position_snapshot",
    "baseline_snapshot",
    "score_snapshot",
    "recommendation_snapshot",
    "asset_pool_entry",
    "comparison_snapshot",
    "audit_log",
    "notification_log",
    "missing_data_log",
    "manual_review_queue",
    "manual_review_decision",
    "conflict_log",
    "decision_record",
    "rebalance_event_log",
    "automation_tick_log",
    "source_evidence_audit_snapshot",
}

FORBIDDEN_EXECUTION_PATTERNS = (
    "place_order",
    "modify_order",
    "cancel_order",
    "unlock_trade",
    "OpenSecTradeContext",
    "buy_order",
    "sell_order",
)


@dataclass(frozen=True)
class AuditItem:
    item_id: str
    area: str
    requirement: str
    status: str
    severity: str
    proof: str
    evidence_path: str
    next_action: str


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def _item(
    items: list[AuditItem],
    item_id: str,
    area: str,
    requirement: str,
    status: str,
    severity: str,
    proof: str,
    evidence_path: Path | str,
    next_action: str = "None",
) -> None:
    items.append(
        AuditItem(
            item_id=item_id,
            area=area,
            requirement=requirement,
            status=status,
            severity=severity,
            proof=proof,
            evidence_path=str(evidence_path),
            next_action=next_action,
        )
    )


def _read_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _read_plist(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        with path.open("rb") as handle:
            data = plistlib.load(handle)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _latest_strategy_run(conn: sqlite3.Connection) -> sqlite3.Row | None:
    rows = conn.execute(
        """
        SELECT run_id, schedule_slot, run_time_bj, run_time_au, status, data_quality_status,
               report_path, offline_html_path, notification_status, created_at
        FROM run_log
        WHERE schedule_slot LIKE 'R%'
          AND report_path IS NOT NULL
        ORDER BY run_time_bj DESC, created_at DESC, rowid DESC
        LIMIT 12
        """
    ).fetchall()
    if not rows:
        return None
    visible_rows = [
        row
        for row in rows
        if not is_future_controlled_backfill(row["run_time_bj"], row["created_at"])
    ]
    return visible_rows[0] if visible_rows else rows[0]


def _count(conn: sqlite3.Connection, query: str, params: tuple[object, ...] = ()) -> int:
    row = conn.execute(query, params).fetchone()
    return int(row[0] if row else 0)


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {str(row["name"] if isinstance(row, sqlite3.Row) else row[0]) for row in rows}


def _scan_forbidden_execution(root: Path) -> list[str]:
    hits: list[str] = []
    for path in (root / "app").rglob("*.py"):
        if path.name == "completion_audit.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in FORBIDDEN_EXECUTION_PATTERNS:
            if re.search(rf"\b{re.escape(pattern)}\b", text):
                hits.append(f"{path}:{pattern}")
    return hits


def _zip_test(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, "zip missing"
    try:
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad:
                return False, f"first bad member: {bad}"
            return True, f"{len(archive.namelist())} members"
    except zipfile.BadZipFile as exc:
        return False, str(exc)


def _zip_private_evidence_members(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        with zipfile.ZipFile(path) as archive:
            return sorted(
                name
                for name in archive.namelist()
                if any(fnmatch.fnmatch(name, pattern) for pattern in PRIVATE_EVIDENCE_EXCLUDES)
            )
    except zipfile.BadZipFile:
        return []


def _local_path_sensitive_hits(settings: Settings, paths: list[Path]) -> list[str]:
    markers = [
        settings.root_dir.as_posix(),
        "/Users/",
        "linzezhang",
        "Documents/Codex",
        "file://",
        "/private/var/",
    ]
    hits: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        text = path.read_bytes().decode("latin-1", errors="ignore")
        for marker in markers:
            if marker and marker in text:
                hits.append(f"{path.name}:{marker}")
    return hits[:50]


def _formal_report_sensitive_hits(settings: Settings) -> list[str]:
    paths = [
        settings.root_dir / "outputs" / "preflight" / "PRODUCTION_READINESS_REPORT.md",
        settings.root_dir / "outputs" / "preflight" / "PRODUCTION_READINESS_REPORT.pdf",
    ]
    return _local_path_sensitive_hits(settings, paths)


def _auxiliary_markdown_sensitive_hits(settings: Settings) -> list[str]:
    paths = [
        settings.root_dir / "outputs" / "preflight" / "preflight_latest.md",
        settings.root_dir / "outputs" / "preflight" / "intake_validation_latest.md",
        settings.root_dir / "outputs" / "preflight" / "apple_mail_smoke_latest.md",
        settings.root_dir / "outputs" / "preflight" / "PRODUCTION_UNBLOCK_EVIDENCE_MATRIX.md",
        settings.root_dir / "outputs" / "preflight" / "moomoo_smoke_latest.md",
        settings.root_dir / "outputs" / "preflight" / "holdings_discovery_latest.md",
        settings.root_dir / "outputs" / "preflight" / "production_action_queue_latest.md",
        settings.root_dir / "outputs" / "preflight" / "production_unlock_check_latest.md",
        settings.root_dir / "outputs" / "preflight" / "mail_unlock_check_latest.md",
        settings.root_dir / "outputs" / "preflight" / "source_evidence_audit_latest.md",
    ]
    markers = [
        settings.root_dir.as_posix(),
        "/Users/",
        "Documents/Codex",
        "file://",
        "/private/var/",
    ]
    hits: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in markers:
            if marker and marker in text:
                hits.append(f"{path.name}:{marker}")
    return hits[:50]


def _intake_pack_user_facing_sensitive_hits(settings: Settings) -> list[str]:
    intake_dir = settings.root_dir / "outputs" / "intake_pack"
    paths = [
        intake_dir / "README_PRODUCTION_DATA_INTAKE.md",
        intake_dir / "FIELD_GUIDE.md",
        intake_dir / "EVIDENCE_INTAKE_GUIDE.md",
        intake_dir / "01_alipay_positions_to_fill.csv",
        intake_dir / "02_fund_rules_to_fill.csv",
        intake_dir / "03_candidates_to_fill.csv",
        intake_dir / "04_gap_actions.csv",
        intake_dir / "05_discovered_candidate_files.csv",
        intake_dir / "06_alipay_positions_review_prefill.csv",
        intake_dir / "07_special_fund_rule_checklist.csv",
        intake_dir / "08_fund_rules_from_review_checklist.csv",
        intake_dir / "09_candidate_source_review_prefill.csv",
        intake_dir / "promotion_latest.md",
    ]
    return _local_path_sensitive_hits(settings, paths)


def _production_unlock_workflow_consistency(settings: Settings) -> tuple[bool, str, Path, str]:
    json_path = settings.root_dir / "outputs" / "preflight" / "production_unlock_check_latest.json"
    markdown_path = settings.root_dir / "outputs" / "preflight" / "production_unlock_check_latest.md"
    data = _read_json(json_path)
    if data is None:
        return False, "production unlock check JSON missing or invalid", json_path, "Run `python -m app.cli production-unlock-check --json`."
    if not markdown_path.exists():
        return False, "production unlock check Markdown missing", markdown_path, "Run `python -m app.cli production-unlock-check --json`."

    stage_names = [
        str(stage.get("name"))
        for stage in data.get("stages") or []
        if isinstance(stage, dict) and stage.get("name")
    ]
    required_stages = {"source_evidence_audit_pack", "promote_intake_pack_dry_run", "preflight", "completion_audit"}
    missing_stages = sorted(required_stages - set(stage_names))
    if missing_stages:
        return (
            False,
            f"production unlock workflow missing stages={missing_stages}",
            json_path,
            "Regenerate production unlock check after restoring the full fail-closed stage chain.",
        )

    markdown_text = markdown_path.read_text(encoding="utf-8", errors="ignore")
    boundary_phrases = [
        "This command does not send mail.",
        "This command does not place trades.",
        "`--apply` only promotes the intake pack",
        "Production remains locked unless preflight and completion audit both pass.",
    ]
    missing_boundary = [phrase for phrase in boundary_phrases if phrase not in markdown_text]
    if missing_boundary:
        return (
            False,
            f"production unlock Markdown missing boundary phrases={missing_boundary}",
            markdown_path,
            "Regenerate production unlock check Markdown with explicit safety boundary language.",
        )

    sensitive_markers = [settings.root_dir.as_posix(), "/Users/", "Documents/Codex", "file://"]
    sensitive_hits = [marker for marker in sensitive_markers if marker and marker in markdown_text]
    if sensitive_hits:
        return (
            False,
            f"production unlock Markdown contains sensitive path markers={sensitive_hits}",
            markdown_path,
            "Regenerate production unlock check after path redaction.",
        )

    workflow_status = data.get("status")
    if workflow_status not in {"pass", "blocked"}:
        return (
            False,
            f"production unlock workflow status invalid: {workflow_status}",
            json_path,
            "Regenerate production unlock check with a pass/blocked status.",
        )

    return (
        True,
        f"status={workflow_status}, stages={stage_names}, production_ready={data.get('production_ready')}, stop_reason={data.get('stop_reason')}",
        markdown_path,
        "None",
    )


def _production_action_queue_consistency(settings: Settings) -> tuple[bool, str, Path, str]:
    json_path = settings.root_dir / "outputs" / "preflight" / "production_action_queue_latest.json"
    markdown_path = settings.root_dir / "outputs" / "preflight" / "production_action_queue_latest.md"
    csv_path = settings.root_dir / "outputs" / "preflight" / "production_action_queue_latest.csv"
    data = _read_json(json_path)
    if data is None:
        return False, "production action queue JSON missing or invalid", json_path, "Run `python -m app.cli production-action-queue --json`."
    if not markdown_path.exists() or not csv_path.exists():
        return False, "production action queue Markdown or CSV missing", markdown_path, "Run `python -m app.cli production-action-queue --json`."
    row_count = int(data.get("row_count") or 0)
    if row_count <= 0:
        return False, f"production action queue has no rows: {row_count}", json_path, "Regenerate action queue from current intake validation gaps."
    text = markdown_path.read_text(encoding="utf-8", errors="ignore")
    csv_text = csv_path.read_text(encoding="utf-8", errors="ignore")
    required_phrases = ["No-New-Order", "does not place trades", "does not send email", "does not unlock production"]
    missing = [phrase for phrase in required_phrases if phrase not in text]
    if missing:
        return False, f"production action queue missing fail-closed boundary phrases={missing}", markdown_path, "Regenerate action queue with explicit safety boundaries."
    sensitive_markers = [settings.root_dir.as_posix(), "/Users/", "Documents/Codex", "file://"]
    sensitive_hits = [marker for marker in sensitive_markers if marker and (marker in text or marker in csv_text)]
    if sensitive_hits:
        return False, f"production action queue contains sensitive path markers={sensitive_hits}", markdown_path, "Regenerate action queue after path redaction."
    if data.get("production_ready") is not False or data.get("no_new_order") is not True:
        return False, f"action queue safety flags invalid: production_ready={data.get('production_ready')}, no_new_order={data.get('no_new_order')}", json_path, "Regenerate action queue without unlocking production."
    return True, f"rows={row_count}, blockers={data.get('blocker_counts')}, priority_counts={data.get('priority_counts')}", markdown_path, "None"


def _risk_gate_regression_consistency(settings: Settings) -> tuple[bool, str, Path, str]:
    json_path = settings.root_dir / "outputs" / "tests" / "risk_gate_regression_latest.json"
    data = _read_json(json_path)
    if data is None:
        return (
            False,
            "risk gate regression artifact missing or invalid",
            json_path,
            "Run `python -m app.cli risk-gate-regression --require-pass --json`.",
        )
    cases = data.get("cases") or []
    passed_case_ids = {
        str(case.get("case_id"))
        for case in cases
        if isinstance(case, dict) and case.get("status") == "pass" and case.get("case_id")
    }
    required_case_ids = {"max_drawdown_block", "recovery_time_block"}
    missing = sorted(required_case_ids - passed_case_ids)
    if data.get("status") == "pass" and not missing:
        return (
            True,
            f"regression_status=pass, passed_cases={sorted(passed_case_ids)}",
            json_path,
            "None",
        )
    return (
        False,
        f"regression_status={data.get('status')}, missing_or_failed_cases={missing}",
        json_path,
        "Fix risk gate scoring and rerun `python -m app.cli risk-gate-regression --require-pass --json`.",
    )


def _readiness_report_package_consistency(settings: Settings) -> tuple[bool, str, Path, str]:
    report_path = settings.root_dir / "outputs" / "preflight" / "PRODUCTION_READINESS_REPORT.md"
    package_path = settings.root_dir / "outputs" / "package" / "package_latest.json"
    package_data = _read_json(package_path)
    if not report_path.exists():
        return False, "readiness report markdown missing", report_path, "Regenerate PRODUCTION_READINESS_REPORT.md and PDF."
    if not package_data:
        return False, "package_latest.json missing or invalid", package_path, "Run `python -m app.cli package-delivery --json`."

    member_count = package_data.get("member_count")
    private_members = package_data.get("included_private_like_members")
    if not isinstance(member_count, int):
        return False, f"package member_count invalid: {member_count}", package_path, "Rebuild package metadata."
    if not isinstance(private_members, list):
        return False, f"private evidence member list invalid: {private_members}", package_path, "Rebuild package metadata."

    text = report_path.read_text(encoding="utf-8", errors="ignore")
    member_phrases = [
        f"latest final ZIP has {member_count} members",
        f"最新最终 ZIP 包含 {member_count} 个文件",
    ]
    privacy_phrases = (
        ["no private-evidence members", "不包含私有证据文件"]
        if not private_members
        else ["private-evidence members", "包含私有证据文件"]
    )
    missing = []
    if not any(phrase in text for phrase in member_phrases):
        missing.append(member_phrases[0])
    if not any(phrase in text for phrase in privacy_phrases):
        missing.append(privacy_phrases[0])
    if missing:
        return (
            False,
            f"readiness report package summary is stale or incomplete; missing={missing}",
            report_path,
            "Update the readiness report from package_latest.json and regenerate PDF.",
        )
    return True, f"report matches package member_count={member_count}, private_members={len(private_members)}", report_path, "None"


def _benchmark_points(path: Path) -> dict[str, list[tuple[datetime, float]]]:
    points: dict[str, list[tuple[datetime, float]]] = {}
    if not path.exists():
        return points
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            code = str(row.get("asset_code") or "")
            raw_date = str(row.get("date") or "")
            raw_close = str(row.get("close") or "")
            if not code or not raw_date or not raw_close:
                continue
            try:
                day = datetime.fromisoformat(raw_date)
                close = float(raw_close)
            except ValueError:
                continue
            points.setdefault(code, []).append((day, close))
    for rows in points.values():
        rows.sort(key=lambda item: item[0])
    return points


def _readiness_report_benchmark_consistency(settings: Settings) -> tuple[bool, str, Path, str]:
    report_path = settings.root_dir / "outputs" / "preflight" / "PRODUCTION_READINESS_REPORT.md"
    history_path = settings.manual_dir / "benchmark_price_history.csv"
    if not history_path.exists():
        history_path = settings.manual_dir / "price_history.csv"
    if not report_path.exists():
        return False, "readiness report markdown missing", report_path, "Regenerate PRODUCTION_READINESS_REPORT.md and PDF."
    points_by_code = _benchmark_points(history_path)
    missing_codes = [code for code in ("000001.SH", "SPX") if code not in points_by_code]
    if missing_codes:
        return False, f"benchmark history missing codes={missing_codes}", history_path, "Regenerate benchmark history."

    report_text = report_path.read_text(encoding="utf-8", errors="ignore")
    labels = {"000001.SH": ("Shanghai Composite", "沪指"), "SPX": ("S&P 500", "标普500")}
    missing_required: list[str] = []
    return_snapshot_drifts: list[str] = []
    proof_parts: list[str] = []
    for code, (label, zh_label) in labels.items():
        points = points_by_code[code]
        first_day = points[0][0].date().isoformat()
        latest_day = points[-1][0].date().isoformat()
        row_phrase = f"{label} canonical code `{code}`: {len(points)} rows from {first_day} to {latest_day}."
        row_phrase_zh = f"{zh_label} 标准代码 `{code}`：{len(points)} 行，日期 {first_day} 至 {latest_day}。"
        returns = calculate_returns([PricePoint(code, day.date(), close) for day, close in points])
        missing_windows = [window for window in WINDOWS if returns.get(window) is None]
        return_phrase = (
            f"{label}: 1m `{returns['1m'] * 100:.2f}%`, "
            f"3m `{returns['3m'] * 100:.2f}%`, "
            f"12m `{returns['12m'] * 100:.2f}%`, "
            f"10d `{returns['10d'] * 100:.2f}%`."
            if not missing_windows
            else ""
        )
        return_phrase_zh = (
            f"{zh_label}：1个月 `{returns['1m'] * 100:.2f}%`，"
            f"3个月 `{returns['3m'] * 100:.2f}%`，"
            f"1年 `{returns['12m'] * 100:.2f}%`，"
            f"最近10交易日 `{returns['10d'] * 100:.2f}%`。"
            if not missing_windows
            else ""
        )
        proof_parts.append(f"{code}: rows={len(points)}, latest={latest_day}")
        if row_phrase not in report_text and row_phrase_zh not in report_text:
            missing_required.append(row_phrase)
        if missing_windows:
            missing_required.append(f"{label} missing return windows: {', '.join(missing_windows)}")
        if return_phrase and return_phrase not in report_text and return_phrase_zh not in report_text:
            return_snapshot_drifts.append(return_phrase)
    if missing_required:
        return (
            False,
            f"readiness report benchmark summary is stale or incomplete; missing={missing_required[:4]}",
            report_path,
            "Update benchmark evidence section from data/manual/benchmark_price_history.csv and regenerate PDF.",
        )
    if return_snapshot_drifts:
        proof_parts.append(f"return_snapshot_drift_tolerated={len(return_snapshot_drifts)}")
    return True, "; ".join(proof_parts), report_path, "None"


def _readiness_report_preflight_consistency(settings: Settings, preflight: dict[str, object] | None) -> tuple[bool, str, Path, str]:
    report_path = settings.root_dir / "outputs" / "preflight" / "PRODUCTION_READINESS_REPORT.md"
    preflight_path = settings.root_dir / "outputs" / "preflight" / "preflight_latest.json"
    if not report_path.exists():
        return False, "readiness report markdown missing", report_path, "Regenerate PRODUCTION_READINESS_REPORT.md and PDF."
    if preflight is None:
        return False, "preflight_latest.json missing or invalid", preflight_path, "Run `python -m app.cli preflight --json`."

    text = report_path.read_text(encoding="utf-8", errors="ignore")
    lower_text = text.lower()
    production_ready = bool(preflight.get("production_ready"))
    if production_ready:
        stale_markers = [
            marker
            for marker in ["not production-ready", "Production remains blocked", "Current production blockers"]
            if marker.lower() in lower_text
        ]
        if stale_markers:
            return (
                False,
                f"preflight is production-ready but report still contains blocked markers={stale_markers}",
                report_path,
                "Update the readiness report to production-ready status and regenerate PDF.",
            )
        if "production-ready" not in lower_text and "production ready" not in lower_text and "生产就绪" not in text:
            return (
                False,
                "preflight is production-ready but report lacks production-ready status language",
                report_path,
                "Update the readiness report to state production-ready status and regenerate PDF.",
            )
        return True, "report production-ready language matches preflight production_ready=True", report_path, "None"

    blockers = preflight.get("blockers") or []
    blocker_names = [str(blocker.get("name")) for blocker in blockers if isinstance(blocker, dict)]
    required_phrase_groups = [
        ("not production-ready", "尚未生产就绪"),
        ("Production remains blocked", "生产仍然阻断"),
    ]
    blocker_phrase_map = {
        "candidate_universe": ("Candidate universe", "候选池证据"),
        "fund_rules": ("Fund rules", "基金规则"),
        "mail_send_config": ("Alert delivery config", "告警投递配置"),
    }
    required_phrase_groups.extend(blocker_phrase_map[name] for name in blocker_names if name in blocker_phrase_map)
    missing = [
        group[0]
        for group in required_phrase_groups
        if not any(phrase.lower() in lower_text for phrase in group)
    ]
    if missing:
        return (
            False,
            f"preflight is blocked but report is stale or incomplete; missing={missing}",
            report_path,
            "Update blocked-status and blocker sections from preflight_latest.json and regenerate PDF.",
        )
    return True, f"report blocked status matches preflight blockers={blocker_names}", report_path, "None"


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def _audit_static_and_files(settings: Settings, items: list[AuditItem]) -> None:
    _item(
        items,
        "schedule_exact",
        "Schedule",
        "Beijing schedule must contain 10 hourly runs from 08:30 through 17:30.",
        "pass" if SCHEDULE_SLOTS == EXPECTED_SLOTS else "block",
        "critical" if SCHEDULE_SLOTS != EXPECTED_SLOTS else "info",
        f"configured_slots={SCHEDULE_SLOTS}",
        settings.root_dir / "app" / "scheduler.py",
        "Restore the exact Beijing 08:30-17:30 hourly slot matrix." if SCHEDULE_SLOTS != EXPECTED_SLOTS else "None",
    )
    saturday = datetime(2026, 6, 13, 8, 30, tzinfo=ZoneInfo("Asia/Shanghai"))
    saturday_default = due_slot_at(saturday, 3)
    saturday_override = due_slot_at(saturday, 3, require_business_day=False)
    business_day_gate_ready = saturday_default is None and saturday_override == "R1"
    _item(
        items,
        "business_day_schedule_gate",
        "Schedule",
        "Recurring automation must skip Beijing weekends by default while preserving manual override support for controlled backfills.",
        "pass" if business_day_gate_ready else "block",
        "critical" if not business_day_gate_ready else "info",
        f"saturday_default={saturday_default or 'none'}, saturday_override={saturday_override or 'none'}",
        settings.root_dir / "app" / "scheduler.py",
        "Restore business-day gating in scheduler due-slot resolution." if not business_day_gate_ready else "None",
    )
    risk_ok = settings.max_drawdown_block == 0.40 and settings.recovery_time_block_days == 365
    _item(
        items,
        "risk_thresholds",
        "Risk",
        "Max drawdown block must be 40%; recovery-to-origin repair time must be under 1 year.",
        "pass" if risk_ok else "block",
        "critical" if not risk_ok else "info",
        f"max_drawdown_block={settings.max_drawdown_block:.2%}, recovery_time_block_days={settings.recovery_time_block_days}",
        settings.root_dir / "app" / "config.py",
        "Set Settings.max_drawdown_block=0.40 and recovery_time_block_days=365." if not risk_ok else "None",
    )
    forbidden_hits = _scan_forbidden_execution(settings.root_dir)
    _item(
        items,
        "no_trade_execution_code",
        "Safety",
        "System must not contain automatic real buy/sell/order execution paths.",
        "pass" if not forbidden_hits else "block",
        "critical" if forbidden_hits else "info",
        "no forbidden trade execution patterns found in app/" if not forbidden_hits else "; ".join(forbidden_hits[:20]),
        settings.root_dir / "app",
        "Remove or hard-disable real order execution code." if forbidden_hits else "None",
    )
    repo_root = Path(__file__).resolve().parents[2]
    cli_path = repo_root / "app" / "cli.py"
    benchmark_path = repo_root / "app" / "core" / "benchmark_smoke.py"
    cli_text = cli_path.read_text(encoding="utf-8", errors="ignore") if cli_path.exists() else ""
    benchmark_text = benchmark_path.read_text(encoding="utf-8", errors="ignore") if benchmark_path.exists() else ""
    static_defaults = [
        marker
        for marker in ('default="2026-03-01"', 'default="2026-06-12"')
        if marker in cli_text
    ]
    dynamic_window_ready = (
        not static_defaults
        and "default_benchmark_window" in benchmark_text
        and "dynamic_latest_weekday" in benchmark_text
        and "DEFAULT_LOOKBACK_DAYS = 396" in benchmark_text
    )
    _item(
        items,
        "benchmark_dynamic_window",
        "Benchmark",
        "Benchmark smoke default window must be dynamic so recurring automation does not keep using stale hard-coded dates.",
        "pass" if dynamic_window_ready else "block",
        "critical" if not dynamic_window_ready else "info",
        (
            "default window is latest Beijing weekday plus 396-day lookback"
            if dynamic_window_ready
            else f"static_defaults={static_defaults}, has_dynamic_function={'default_benchmark_window' in benchmark_text}, has_dynamic_source={'dynamic_latest_weekday' in benchmark_text}"
        ),
        benchmark_path,
        "Remove static CLI date defaults and restore dynamic benchmark window resolution." if not dynamic_window_ready else "None",
    )
    output_checks = {
        "formal_pdf": settings.root_dir / "outputs" / "preflight" / "PRODUCTION_READINESS_REPORT.pdf",
        "task_pack": settings.root_dir / "outputs" / "task_pack" / "13_CODEX_PROMPT.md",
        "launchd_plist": settings.root_dir / "outputs" / "implementation" / "com.serenity.daily-analysis.plist",
        "codex_automation_notes": settings.root_dir / "outputs" / "implementation" / "CODEX_AUTOMATION_PROPOSALS.md",
        "application_portal": settings.root_dir / "outputs" / "application" / "index.html",
        "intake_pack": settings.root_dir / "outputs" / "intake_pack" / "README_PRODUCTION_DATA_INTAKE.md",
        "intake_evidence_guide": settings.root_dir / "outputs" / "intake_pack" / "EVIDENCE_INTAKE_GUIDE.md",
        "validation_summary": settings.root_dir / "outputs" / "tests" / "VALIDATION_SUMMARY.md",
    }
    for item_id, path in output_checks.items():
        exists = path.exists() and path.stat().st_size > 0
        _item(
            items,
            item_id,
            "Deliverables",
            f"Required deliverable `{path.name}` must exist and be non-empty.",
            "pass" if exists else "block",
            "critical" if not exists else "info",
            f"exists={exists}, size={path.stat().st_size if path.exists() else 0}",
            path,
            f"Regenerate {path}." if not exists else "None",
        )
    portal_path = settings.root_dir / "outputs" / "application" / "index.html"
    portal_text = portal_path.read_text(encoding="utf-8", errors="ignore") if portal_path.exists() else ""
    portal_ready = (
        portal_path.exists()
        and "data/reports/index.html" in portal_text
        and ("No automatic trading" in portal_text or "无自动交易" in portal_text)
        and ("Delivery Package" in portal_text or "交付包" in portal_text)
    )
    _item(
        items,
        "web_application_entry",
        "Web",
        "A stable local web application portal must exist and link to the continuously updated offline report index.",
        "pass" if portal_ready else "block",
        "info" if portal_ready else "critical",
        (
            "portal links report index, readiness report, package, and no-trading boundary"
            if portal_ready
            else f"exists={portal_path.exists()}, has_report_index={'data/reports/index.html' in portal_text}, has_boundary={('No automatic trading' in portal_text or '无自动交易' in portal_text)}"
        ),
        portal_path,
        "Create or refresh `outputs/application/index.html`." if not portal_ready else "None",
    )
    def _app_bundle_ready(app_path: Path) -> tuple[bool, str]:
        info_path = app_path / "Contents" / "Info.plist"
        pkginfo_path = app_path / "Contents" / "PkgInfo"
        executable_path = app_path / "Contents" / "MacOS" / "open-serenity"
        icon_path = app_path / "Contents" / "Resources" / "SerenityIcon.icns"
        info_text = info_path.read_text(encoding="utf-8", errors="ignore") if info_path.exists() else ""
        pkginfo_text = pkginfo_path.read_text(encoding="ascii", errors="ignore") if pkginfo_path.exists() else ""
        executable_text = executable_path.read_text(encoding="utf-8", errors="ignore") if executable_path.exists() else ""
        icon_size = icon_path.stat().st_size if icon_path.exists() else 0
        ready = (
            app_path.is_dir()
            and info_path.exists()
            and pkginfo_text == "APPL????"
            and executable_path.exists()
            and icon_path.exists()
            and icon_size > 1024
            and "CFBundleIconFile" in info_text
            and "SerenityIcon" in info_text
            and "local.serenity.daily-analysis." in info_text
            and "Serenity 每日分析" in info_text
            and settings.root_dir.as_posix() in executable_text
            and "application-server" in executable_text
            and "/api/health" in executable_text
        )
        proof = (
            f"exists={app_path.is_dir()}, info={info_path.exists()}, pkginfo={pkginfo_text == 'APPL????'}, executable={executable_path.exists()}, "
            f"icon={icon_path.exists()}, icon_size={icon_size}, bundle_id_scoped={'local.serenity.daily-analysis.' in info_text}, "
            f"chinese_name={'Serenity 每日分析' in info_text}, points_to_workspace={settings.root_dir.as_posix() in executable_text}, "
            f"starts_server={'application-server' in executable_text}, has_health_check={'/api/health' in executable_text}, "
            f"icon_plist={'CFBundleIconFile' in info_text and 'SerenityIcon' in info_text}"
        )
        return ready, proof

    downloads_entry_path = Path.home() / "Downloads" / "Serenity 每日分析.app"
    downloads_entry_ready, downloads_entry_proof = _app_bundle_ready(downloads_entry_path)
    _item(
        items,
        "downloads_application_entry",
        "Web",
        "Downloads root must provide a `.app` entry point to the Serenity Daily Analysis portal, not `~/Downloads/application`.",
        "pass" if downloads_entry_ready else "block",
        "info" if downloads_entry_ready else "critical",
        (
            f"Downloads root app bundle opens the current workspace application portal; {downloads_entry_proof}"
            if downloads_entry_ready
            else downloads_entry_proof
        ),
        downloads_entry_path,
        "Run `python -m app.cli application-portal --json` to install `~/Downloads/Serenity 每日分析.app`." if not downloads_entry_ready else "None",
    )
    applications_entry_path = Path("/Applications") / "Serenity 每日分析.app"
    applications_entry_ready, applications_entry_proof = _app_bundle_ready(applications_entry_path)
    _item(
        items,
        "applications_app_entry",
        "Web",
        "/Applications must provide a `.app` entry point to the Serenity Daily Analysis portal.",
        "pass" if applications_entry_ready else "block",
        "info" if applications_entry_ready else "critical",
        (
            f"/Applications app bundle opens the current workspace application portal; {applications_entry_proof}"
            if applications_entry_ready
            else applications_entry_proof
        ),
        applications_entry_path,
        "Run `python -m app.cli application-portal --json` to install `/Applications/Serenity 每日分析.app`." if not applications_entry_ready else "None",
    )
    legacy_downloads_root = Path.home() / "Downloads" / "application"
    legacy_paths = [
        legacy_downloads_root / "Serenity 每日分析.app",
        legacy_downloads_root / "serenity-daily-analysis",
        legacy_downloads_root / "Serenity Daily Analysis.html",
    ]
    legacy_present = [str(path) for path in legacy_paths if path.exists()]
    legacy_clean = not legacy_present
    _item(
        items,
        "legacy_downloads_application_entry_removed",
        "Web",
        "`~/Downloads/application` must not remain the active Serenity app entry location.",
        "pass" if legacy_clean else "block",
        "info" if legacy_clean else "critical",
        "legacy Serenity entries removed from ~/Downloads/application" if legacy_clean else "; ".join(legacy_present),
        legacy_downloads_root,
        "Run `python -m app.cli application-portal --json` to remove legacy Serenity entries that point to this workspace." if not legacy_clean else "None",
    )
    automation_root = Path.home() / ".codex" / "automations"
    automation_specs = {
        "serenity-daily-analysis-beijing-hour-slots": {
            "rrule": "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=8,10,13,16,17,19;BYMINUTE=0",
            "status": "PAUSED",
        },
        "serenity-daily-analysis-beijing-half-hour-slots": {
            "rrule": "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=10,11,12,13,14,15,16,17,18,19;BYMINUTE=30",
            "status": "PAUSED",
        },
    }
    automation_proofs: list[str] = []
    automation_missing: list[str] = []
    for automation_id, spec in automation_specs.items():
        automation_path = automation_root / automation_id / "automation.toml"
        text = automation_path.read_text(encoding="utf-8", errors="ignore") if automation_path.exists() else ""
        ready = (
            automation_path.exists()
            and f'status = "{spec["status"]}"' in text
            and 'status = "ACTIVE"' not in text
            and 'model = "gpt-5.4"' in text
            and 'reasoning_effort = "high"' in text
            and f'rrule = "{spec["rrule"]}"' in text
            and settings.root_dir.as_posix() in text
            and ("must remain paused" in text or "DISABLED" in text)
        )
        if ready:
            automation_proofs.append(f"{automation_id}={spec['status']}")
        else:
            automation_missing.append(automation_id)
    codex_automation_ready = not automation_missing
    _item(
        items,
        "codex_app_automation_active",
        "Automation",
        "Codex app cron automations must stay paused so recurring production ticks do not create sidebar chats; launchd owns silent local execution.",
        "pass" if codex_automation_ready else "block",
        "info" if codex_automation_ready else "critical",
        "; ".join(automation_proofs) if codex_automation_ready else f"missing_or_invalid={automation_missing}",
        settings.root_dir / "outputs" / "implementation" / "CODEX_AUTOMATION_READY.md",
        "Pause Serenity Codex app cron automations and use launchd for sidebar-free automatic execution." if not codex_automation_ready else "None",
    )
    launchd_plist_path = settings.root_dir / "outputs" / "implementation" / "com.serenity.daily-analysis.plist"
    launchd_plist = _read_plist(launchd_plist_path)
    launchd_args = launchd_plist.get("ProgramArguments") if isinstance(launchd_plist, dict) else None
    launchd_env = launchd_plist.get("EnvironmentVariables") if isinstance(launchd_plist, dict) else None
    start_interval = launchd_plist.get("StartInterval") if isinstance(launchd_plist, dict) else None
    expected_args = [
        "/opt/anaconda3/bin/python",
        "-m",
        "app.cli",
        "automation-tick",
        "--no-dry-run",
        "--send-mail",
        "--local",
        "--json",
    ]
    launchd_schedule_ready = (
        isinstance(launchd_args, list)
        and [str(arg) for arg in launchd_args] == expected_args
        and str(launchd_plist.get("WorkingDirectory")) == settings.root_dir.as_posix()
        and isinstance(start_interval, int)
        and start_interval <= 180
    )
    _item(
        items,
        "launchd_schedule_contract",
        "Automation",
        "launchd template must poll frequently enough to catch Beijing slots and run the preflight-gated production automation command.",
        "pass" if launchd_schedule_ready else "block",
        "info" if launchd_schedule_ready else "critical",
        (
            f"StartInterval={start_interval}, command=automation-tick, env={launchd_env}"
            if launchd_schedule_ready
            else f"plist_valid={launchd_plist is not None}, args={launchd_args}, working_dir={launchd_plist.get('WorkingDirectory') if isinstance(launchd_plist, dict) else None}, StartInterval={start_interval}, env={launchd_env}"
        ),
        launchd_plist_path,
        "Restore the launchd template command, working directory, and StartInterval<=180." if not launchd_schedule_ready else "None",
    )
    launchd_status_path = settings.root_dir / "outputs" / "implementation" / "LAUNCHD_STATUS.json"
    launchd_status = _read_json(launchd_status_path)
    launchd_runtime_ready = False
    if launchd_status:
        latest_tick = launchd_status.get("latest_tick")
        latest_tick_dry_run = latest_tick.get("dry_run") if isinstance(latest_tick, dict) else None
        launchd_runtime_ready = (
            launchd_status.get("install_state") == "loaded"
            and launchd_status.get("plist_lint") == "OK"
            and launchd_status.get("stderr_bytes") == 0
            and isinstance(latest_tick, dict)
            and latest_tick.get("action") in {"non_business_day", "no_due_slot", "skipped_duplicate", "ran"}
            and isinstance(latest_tick_dry_run, (bool, int))
            and int(latest_tick_dry_run) in {0, 1}
            and launchd_status.get("automatic_trading") is False
        )
    launchd_status_label = "pass" if launchd_runtime_ready else ("warn" if not launchd_status_path.exists() else "block")
    _item(
        items,
        "launchd_runtime_status",
        "Automation",
        "Installed launchd runtime status snapshot must show a loaded job, successful tick evidence, and disabled automatic trading.",
        launchd_status_label,
        "info" if launchd_status_label == "pass" else ("warn" if launchd_status_label == "warn" else "critical"),
        (
            "install_state=loaded, latest_tick_action="
            f"{launchd_status['latest_tick']['action']}, dry_run={launchd_status['latest_tick']['dry_run']}, "
            f"stderr_bytes={launchd_status['stderr_bytes']}, mail_send_enabled={launchd_status['mail_send_enabled']}"
            if launchd_runtime_ready
            else (
                "launchd runtime status snapshot missing"
                if not launchd_status_path.exists()
                else f"launchd_status={launchd_status}"
            )
        ),
        launchd_status_path,
        "Install/kick launchd and regenerate LAUNCHD_STATUS.json." if launchd_status_label != "pass" else "None",
    )
    mail_smoke_path = settings.root_dir / "outputs" / "preflight" / "apple_mail_smoke_latest.json"
    mail_smoke = _read_json(mail_smoke_path)
    mail_smoke_ready = (
        isinstance(mail_smoke, dict)
        and bool(mail_smoke.get("draft_ready"))
        and isinstance(mail_smoke.get("apple_mail"), dict)
        and bool(mail_smoke["apple_mail"].get("app_scriptable"))
        and "production_send_ready" in mail_smoke
        and mail_smoke.get("send_requested") is False
    )
    _item(
        items,
        "apple_mail_smoke_artifact",
        "Notification",
        "Controlled Apple Mail smoke must prove draft generation, Mail scriptability, and current production-send config without sending by default.",
        "pass" if mail_smoke_ready else "block",
        "info" if mail_smoke_ready else "critical",
        (
            f"draft_ready={mail_smoke['draft_ready']}, app_scriptable={mail_smoke['apple_mail']['app_scriptable']}, "
            f"production_send_ready={mail_smoke['production_send_ready']}, send_status={mail_smoke['send_status']}"
            if mail_smoke_ready
            else (
                "apple_mail_smoke_latest.json missing or invalid"
                if not mail_smoke_path.exists()
                else f"mail_smoke={mail_smoke}"
            )
        ),
        mail_smoke_path,
        "Run `python -m app.cli mail-smoke --json`." if not mail_smoke_ready else "None",
    )
    mail_unlock_path = settings.root_dir / "outputs" / "preflight" / "mail_unlock_check_latest.json"
    mail_unlock_md = settings.root_dir / "outputs" / "preflight" / "mail_unlock_check_latest.md"
    mail_unlock = _read_json(mail_unlock_path)
    mail_unlock_text = mail_unlock_md.read_text(encoding="utf-8", errors="ignore") if mail_unlock_md.exists() else ""
    mail_unlock_ready = (
        isinstance(mail_unlock, dict)
        and bool(mail_unlock.get("workflow_ready"))
        and mail_unlock.get("mail_sent") is False
        and mail_unlock.get("launchd_modified") is False
        and mail_unlock.get("trades_placed") is False
        and "mail-unlock-check" in cli_text
        and "This command does not send mail." in mail_unlock_text
        and "--send --confirm-real-send SEND" in mail_unlock_text
    )
    _item(
        items,
        "mail_unlock_workflow",
        "Notification",
        "Real Apple Mail production-send workflow must have a controlled checklist and explicit real-send smoke command without sending by default.",
        "pass" if mail_unlock_ready else "warn",
        "info" if mail_unlock_ready else "warn",
        (
            f"workflow_ready={mail_unlock['workflow_ready']}, production_send_ready_now={mail_unlock['production_send_ready_now']}, "
            f"mail_sent={mail_unlock['mail_sent']}, launchd_modified={mail_unlock['launchd_modified']}"
            if mail_unlock_ready
            else (
                "mail_unlock_check_latest artifacts missing or incomplete"
                if not mail_unlock_path.exists() or not mail_unlock_md.exists()
                else f"mail_unlock={mail_unlock}"
            )
        ),
        mail_unlock_md,
        "Run `python -m app.cli mail-unlock-check --json`." if not mail_unlock_ready else "None",
    )
    execution_md = settings.root_dir / "outputs" / "preflight" / "ALIPAY_FUND_EXECUTION_WINDOW_EVIDENCE.md"
    execution_json = settings.root_dir / "outputs" / "preflight" / "alipay_fund_execution_window_evidence.json"
    execution_text = execution_md.read_text(encoding="utf-8") if execution_md.exists() else ""
    execution_data = _read_json(execution_json)
    execution_ready = (
        execution_md.exists()
        and execution_json.exists()
        and execution_data is not None
        and "15:00" in execution_text
        and "T+1" in execution_text
        and "QDII" in execution_text
    )
    _item(
        items,
        "alipay_execution_window_evidence",
        "Execution Rules",
        "Alipay/off-platform fund execution window must be source-backed, including 15:00 cutoff, T+1 confirmation, and product-specific exceptions.",
        "pass" if execution_ready else "block",
        "critical" if not execution_ready else "info",
        f"md_exists={execution_md.exists()}, json_exists={execution_json.exists()}, has_15_cutoff={'15:00' in execution_text}, has_t_plus_1={'T+1' in execution_text}, has_exceptions={'QDII' in execution_text}",
        execution_md,
        "Regenerate Alipay/off-platform execution-window evidence." if not execution_ready else "None",
    )
    intake_validator_path = settings.root_dir / "app" / "core" / "intake_validator.py"
    intake_validator_text = intake_validator_path.read_text(encoding="utf-8") if intake_validator_path.exists() else ""
    source_evidence_gate_ready = all(
        marker in intake_validator_text
        for marker in [
            "Fund rule source evidence is not verifiable",
            "Candidate source evidence is not verifiable",
        ]
    )
    _item(
        items,
        "source_evidence_reference_gate",
        "Evidence",
        "Production intake validation must block unverifiable fund-rule and candidate source URLs or local evidence paths.",
        "pass" if source_evidence_gate_ready else "block",
        "critical" if not source_evidence_gate_ready else "info",
        "validator blocks unverifiable fund-rule url_or_path and candidate source_url references" if source_evidence_gate_ready else "source evidence reference gate markers missing",
        intake_validator_path,
        "Restore source evidence reference validation in intake_validator." if not source_evidence_gate_ready else "None",
    )
    evidence_audit_md = settings.root_dir / "outputs" / "preflight" / "source_evidence_audit_latest.md"
    evidence_audit_csv = settings.root_dir / "outputs" / "preflight" / "source_evidence_audit_latest.csv"
    evidence_audit_json = settings.root_dir / "outputs" / "preflight" / "source_evidence_audit_latest.json"
    evidence_audit_data = _read_json(evidence_audit_json)
    evidence_audit_rows = _line_count(evidence_audit_csv)
    evidence_audit_ready = (
        evidence_audit_md.exists()
        and evidence_audit_csv.exists()
        and evidence_audit_data is not None
        and evidence_audit_rows > 0
        and "invalid_count" in evidence_audit_data
        and "status_counts" in evidence_audit_data
    )
    _item(
        items,
        "source_evidence_audit_manifest",
        "Evidence",
        "Source evidence references must be exportable as an audit manifest with URL/local-file status and local-file hashes.",
        "pass" if evidence_audit_ready else "warn",
        "info" if evidence_audit_ready else "warn",
        (
            f"md_exists={evidence_audit_md.exists()}, csv_exists={evidence_audit_csv.exists()}, "
            f"json_exists={evidence_audit_json.exists()}, rows={evidence_audit_rows}, "
            f"status={evidence_audit_data.get('status') if evidence_audit_data else None}, "
            f"invalid_count={evidence_audit_data.get('invalid_count') if evidence_audit_data else None}, "
            f"local_hashed_count={evidence_audit_data.get('local_hashed_count') if evidence_audit_data else None}"
        ),
        evidence_audit_md,
        "Run `python -m app.cli source-evidence-audit --json`." if not evidence_audit_ready else "None",
    )
    unblock_md = settings.root_dir / "outputs" / "preflight" / "PRODUCTION_UNBLOCK_EVIDENCE_MATRIX.md"
    unblock_csv = settings.root_dir / "outputs" / "preflight" / "production_unblock_evidence_matrix.csv"
    unblock_json = settings.root_dir / "outputs" / "preflight" / "production_unblock_evidence_matrix.json"
    unblock_text = unblock_md.read_text(encoding="utf-8") if unblock_md.exists() else ""
    unblock_data = _read_json(unblock_json)
    unblock_rows = _line_count(unblock_csv)
    unblock_base_ready = (
        unblock_md.exists()
        and unblock_csv.exists()
        and unblock_data is not None
    )
    unblock_production_ready = bool(unblock_data.get("production_ready")) if unblock_data else False
    if unblock_base_ready and unblock_production_ready:
        unblock_ready = "warning/open quality items" in unblock_text or "Production preflight currently passes" in unblock_text
    else:
        unblock_ready = (
            unblock_base_ready
            and unblock_rows > 0
            and "Production remains locked" in unblock_text
            and "fund_rules" in unblock_text
            and "candidate_universe" in unblock_text
        )
    _item(
        items,
        "production_unblock_matrix",
        "Production Gate",
        "Remaining production blockers or warning-level evidence items must be mapped to field-level requirements and exact refresh/unlock commands.",
        "pass" if unblock_ready else "warn",
        "info" if unblock_ready else "warn",
        (
            f"md_exists={unblock_md.exists()}, csv_exists={unblock_csv.exists()}, json_exists={unblock_json.exists()}, "
            f"rows={unblock_rows}, production_ready={unblock_production_ready}, "
            f"has_locked_language={'Production remains locked' in unblock_text}"
        ),
        unblock_md,
        "Run `python -m app.cli production-unblock-matrix --scan-path ~/Downloads --scan-path ~/Documents --json`." if not unblock_ready else "None",
    )
    unlock_ready, unlock_proof, unlock_path, unlock_next_action = _production_unlock_workflow_consistency(settings)
    _item(
        items,
        "production_unlock_workflow",
        "Production Gate",
        "A fail-closed production unlock workflow must verify pack evidence, dry-run promotion, preflight, and completion audit without sending mail or placing trades.",
        "pass" if unlock_ready else "block",
        "info" if unlock_ready else "critical",
        unlock_proof,
        unlock_path,
        unlock_next_action,
    )
    action_queue_ready, action_queue_proof, action_queue_path, action_queue_next_action = _production_action_queue_consistency(settings)
    _item(
        items,
        "production_action_queue",
        "Production Gate",
        "Remaining production blockers must have a prioritized No-New-Order action queue with target files, fields, evidence requirements, and unlock commands.",
        "pass" if action_queue_ready else "block",
        "info" if action_queue_ready else "critical",
        action_queue_proof,
        action_queue_path,
        action_queue_next_action,
    )
    data_request_path = settings.root_dir / "outputs" / "preflight" / "PRODUCTION_DATA_REQUEST.md"
    data_request_text = data_request_path.read_text(encoding="utf-8", errors="ignore") if data_request_path.exists() else ""
    data_request_hits = _local_path_sensitive_hits(settings, [data_request_path])
    data_request_ready = (
        data_request_path.exists()
        and "02_fund_rules_to_fill.csv" in data_request_text
        and "03_candidates_to_fill.csv" in data_request_text
        and "baseline" in data_request_text.lower()
        and "normalize-intake-bundle" in data_request_text
        and "production-unlock-check" in data_request_text
        and not data_request_hits
    )
    _item(
        items,
        "production_data_request_contract",
        "Production Gate",
        "Production blockers must have a concise input contract for baseline generation, fund rules, candidate sources, evidence rules, and unlock commands.",
        "pass" if data_request_ready else "warn",
        "info" if data_request_ready else "warn",
        (
            "input contract ready"
            if data_request_ready
            else f"exists={data_request_path.exists()}, sensitive_hits={data_request_hits}, has_unlock_commands={'production-unlock-check' in data_request_text}"
        ),
        data_request_path,
        "Create or refresh `outputs/preflight/PRODUCTION_DATA_REQUEST.md`." if not data_request_ready else "None",
    )
    normalizer_path = settings.root_dir / "app" / "core" / "alipay_position_normalizer.py"
    cli_path = settings.root_dir / "app" / "cli.py"
    cli_text = cli_path.read_text(encoding="utf-8", errors="ignore") if cli_path.exists() else ""
    normalizer_ready = normalizer_path.exists() and "normalize-alipay-positions" in cli_text and "write_pack" in normalizer_path.read_text(encoding="utf-8", errors="ignore")
    _item(
        items,
        "alipay_position_normalizer",
        "Data Quality",
        "Current Alipay holdings/OCR CSVs must have a safe normalizer into intake-pack format without touching production files by default.",
        "pass" if normalizer_ready else "warn",
        "info" if normalizer_ready else "warn",
        "CLI `normalize-alipay-positions` is available with candidate-output default and explicit `--write-pack` option" if normalizer_ready else "normalizer CLI or module missing",
        normalizer_path,
        "Restore `app/core/alipay_position_normalizer.py` and CLI command." if not normalizer_ready else "None",
    )
    fund_rule_normalizer_path = settings.root_dir / "app" / "core" / "fund_rule_normalizer.py"
    fund_rule_normalizer_ready = (
        fund_rule_normalizer_path.exists()
        and "normalize-fund-rules" in cli_text
        and "02_fund_rules_normalized_candidate.csv" in fund_rule_normalizer_path.read_text(encoding="utf-8", errors="ignore")
    )
    _item(
        items,
        "fund_rule_normalizer",
        "Data Quality",
        "Current Alipay/fund-company rule OCR CSVs must have a safe normalizer into intake-pack fund-rule format without touching production files by default.",
        "pass" if fund_rule_normalizer_ready else "warn",
        "info" if fund_rule_normalizer_ready else "warn",
        "CLI `normalize-fund-rules` is available with candidate-output default and explicit `--write-pack` option" if fund_rule_normalizer_ready else "fund-rule normalizer CLI or module missing",
        fund_rule_normalizer_path,
        "Restore `app/core/fund_rule_normalizer.py` and CLI command." if not fund_rule_normalizer_ready else "None",
    )
    candidate_normalizer_path = settings.root_dir / "app" / "core" / "candidate_normalizer.py"
    candidate_normalizer_ready = (
        candidate_normalizer_path.exists()
        and "normalize-candidates" in cli_text
        and "03_candidates_normalized_candidate.csv" in candidate_normalizer_path.read_text(encoding="utf-8", errors="ignore")
    )
    _item(
        items,
        "candidate_normalizer",
        "Data Quality",
        "Current candidate/source-chain OCR CSVs must have a safe normalizer into intake-pack candidate-universe format without touching production files by default.",
        "pass" if candidate_normalizer_ready else "warn",
        "info" if candidate_normalizer_ready else "warn",
        "CLI `normalize-candidates` is available with candidate-output default and explicit `--write-pack` option" if candidate_normalizer_ready else "candidate normalizer CLI or module missing",
        candidate_normalizer_path,
        "Restore `app/core/candidate_normalizer.py` and CLI command." if not candidate_normalizer_ready else "None",
    )
    intake_bundle_normalizer_path = settings.root_dir / "app" / "core" / "intake_bundle_normalizer.py"
    intake_bundle_text = intake_bundle_normalizer_path.read_text(encoding="utf-8", errors="ignore") if intake_bundle_normalizer_path.exists() else ""
    intake_bundle_normalizer_ready = (
        intake_bundle_normalizer_path.exists()
        and "normalize-intake-bundle" in cli_text
        and "production_files_touched" in intake_bundle_text
        and "promote_intake_pack" in intake_bundle_text
        and "build_source_evidence_audit" in intake_bundle_text
    )
    _item(
        items,
        "intake_bundle_normalizer",
        "Data Quality",
        "Holdings, fund-rule, and candidate normalizers must be available as a single staged intake-pack workflow that audits evidence and dry-runs promotion without touching production files.",
        "pass" if intake_bundle_normalizer_ready else "warn",
        "info" if intake_bundle_normalizer_ready else "warn",
        "CLI `normalize-intake-bundle` is available with staged pack write, source-evidence audit, promotion dry-run, and no production copy" if intake_bundle_normalizer_ready else "intake bundle normalizer CLI or module missing",
        intake_bundle_normalizer_path,
        "Restore `app/core/intake_bundle_normalizer.py` and CLI command." if not intake_bundle_normalizer_ready else "None",
    )
    zip_path = settings.root_dir / "outputs" / "package" / "serenity_daily_analysis_delivery.zip"
    zip_ok, zip_proof = _zip_test(zip_path)
    _item(
        items,
        "final_zip_integrity",
        "Deliverables",
        "Final ZIP package must exist and pass archive integrity verification.",
        "pass" if zip_ok else "block",
        "critical" if not zip_ok else "info",
        zip_proof,
        zip_path,
        "Rebuild and retest the delivery ZIP." if not zip_ok else "None",
    )
    private_members = _zip_private_evidence_members(zip_path)
    _item(
        items,
        "final_zip_private_evidence_exclusion",
        "Deliverables",
        "Final ZIP must exclude private evidence directories unless explicitly requested.",
        "pass" if not private_members else "warn",
        "info" if not private_members else "warn",
        "no private evidence members found" if not private_members else f"private-like members={private_members[:20]}",
        zip_path,
        "Rebuild with `python -m app.cli package-delivery --json`." if private_members else "None",
    )
    package_consistent, package_proof, package_evidence_path, package_next_action = _readiness_report_package_consistency(settings)
    _item(
        items,
        "readiness_report_package_consistency",
        "Deliverables",
        "Formal readiness report must match the latest package manifest member count and private-evidence status.",
        "pass" if package_consistent else "block",
        "info" if package_consistent else "critical",
        package_proof,
        package_evidence_path,
        package_next_action,
    )
    benchmark_consistent, benchmark_proof, benchmark_evidence_path, benchmark_next_action = _readiness_report_benchmark_consistency(settings)
    _item(
        items,
        "readiness_report_benchmark_consistency",
        "Deliverables",
        "Formal readiness report must include benchmark row counts, dates, and return-window evidence; intraday return drift is tolerated for timestamped snapshot reports.",
        "pass" if benchmark_consistent else "block",
        "info" if benchmark_consistent else "critical",
        benchmark_proof,
        benchmark_evidence_path,
        benchmark_next_action,
    )


def _audit_preflight(settings: Settings, items: list[AuditItem], preflight: dict[str, object] | None) -> None:
    path = settings.root_dir / "outputs" / "preflight" / "preflight_latest.json"
    if preflight is None:
        _item(items, "production_preflight", "Production Gate", "Production preflight result must exist.", "block", "critical", "preflight_latest.json missing or invalid", path, "Run `python -m app.cli preflight --json`.")
        return
    production_ready = bool(preflight.get("production_ready"))
    shadow_ready = bool(preflight.get("shadow_ready"))
    blockers = preflight.get("blockers") or []
    blocker_names = [str(blocker.get("name")) for blocker in blockers if isinstance(blocker, dict)]
    _item(
        items,
        "production_preflight",
        "Production Gate",
        "Production execution must only unlock when baseline candidate universe, fund rules, benchmark sources, scheduler, Mail, and MooMoo gates pass; Alipay holdings are optional overlay data.",
        "pass" if production_ready else "block",
        "critical" if not production_ready else "info",
        f"production_ready={production_ready}; blockers={blocker_names}",
        path,
        "Clear the listed production blockers." if not production_ready else "None",
    )
    report_consistent, report_proof, report_evidence_path, report_next_action = _readiness_report_preflight_consistency(settings, preflight)
    _item(
        items,
        "readiness_report_preflight_consistency",
        "Deliverables",
        "Formal readiness report production-ready/blocked status must match the latest production preflight result.",
        "pass" if report_consistent else "block",
        "info" if report_consistent else "critical",
        report_proof,
        report_evidence_path,
        report_next_action,
    )
    _item(
        items,
        "shadow_ready_gate",
        "Production Gate",
        "When production data is incomplete, system must remain runnable in shadow mode only.",
        "pass" if production_ready or (shadow_ready and not production_ready) else "block",
        "info" if production_ready else ("warn" if shadow_ready else "critical"),
        f"shadow_ready={shadow_ready}, production_ready={production_ready}",
        path,
        "Keep automation dry-run forced until production_ready=true." if shadow_ready and not production_ready else "None",
    )
    checks = preflight.get("checks") or []
    check_map = {str(check.get("name")): check for check in checks if isinstance(check, dict)}
    mail_config = check_map.get("mail_send_config")
    _item(
        items,
        "mail_send_config_gate",
        "Notification",
        "Production alert delivery must have real Apple Mail sending enabled before rebalance or urgent risk alerts can claim readiness.",
        "pass" if mail_config and mail_config.get("status") == "pass" else "block",
        "critical" if not mail_config or mail_config.get("status") != "pass" else "info",
        str(mail_config.get("evidence") if mail_config else "missing mail_send_config preflight check"),
        path,
        "Run the production path with `--send-mail` only after data gates are cleared and a real-send smoke is approved." if not mail_config or mail_config.get("status") != "pass" else "None",
    )
    moomoo = check_map.get("moomoo_opend")
    _item(
        items,
        "moomoo_opend_gate",
        "Data Source",
        "MooMoo/moomoo_OpenD socket and SDK must be available; moomoo_OpenD lifecycle must respect user-opened process ownership.",
        "pass" if moomoo and moomoo.get("status") == "pass" else "block",
        "critical" if not moomoo or moomoo.get("status") != "pass" else "info",
        str(moomoo.get("message") if moomoo else "missing moomoo preflight check"),
        path,
        "Open or auto-start OpenD and rerun moomoo smoke." if not moomoo or moomoo.get("status") != "pass" else "None",
    )
    benchmark = check_map.get("benchmark_sources")
    _item(
        items,
        "benchmark_gate",
        "Benchmark",
        "Shanghai Composite and S&P 500 must have 1m, 3m, 12m, and recent 10 trading day comparison data.",
        "pass" if benchmark and benchmark.get("status") == "pass" else "block",
        "critical" if not benchmark or benchmark.get("status") != "pass" else "info",
        str(benchmark.get("evidence") if benchmark else "missing benchmark check"),
        path,
        "Provide exact benchmark history and rerun benchmark smoke." if not benchmark or benchmark.get("status") != "pass" else "None",
    )


def _audit_intake(settings: Settings, items: list[AuditItem], intake: dict[str, object] | None, promotion: dict[str, object] | None) -> None:
    intake_sensitive_hits = _intake_pack_user_facing_sensitive_hits(settings)
    _item(
        items,
        "intake_pack_user_facing_path_redaction",
        "Safety",
        "Production intake-pack user-facing Markdown/CSV helpers must not expose absolute local paths or user-home identifiers.",
        "pass" if not intake_sensitive_hits else "block",
        "info" if not intake_sensitive_hits else "critical",
        "no intake-pack user-facing local path markers found" if not intake_sensitive_hits else f"sensitive path markers={intake_sensitive_hits}",
        settings.root_dir / "outputs" / "intake_pack",
        "Regenerate production intake pack with redacted display paths." if intake_sensitive_hits else "None",
    )
    intake_path = settings.root_dir / "outputs" / "preflight" / "intake_validation_latest.json"
    if intake is None:
        _item(items, "intake_validation", "Data Quality", "Production intake validation must exist.", "block", "critical", "intake validation missing", intake_path, "Run `python -m app.cli validate-intake --json`.")
    else:
        block_count = int(intake.get("block_count") or 0)
        warn_count = int(intake.get("warn_count") or 0)
        gaps = intake.get("gaps") or []
        gap_areas = sorted({str(gap.get("area")) for gap in gaps if isinstance(gap, dict) and gap.get("severity") == "block"})
        _item(
            items,
            "intake_validation",
            "Data Quality",
            "NAV/holding freshness, fees, redemption status, official source count, conflicts, and aggregated fallback must be validated and timestamped.",
            "pass" if block_count == 0 else "block",
            "critical" if block_count else ("warn" if warn_count else "info"),
            f"block_count={block_count}, warn_count={warn_count}, block_areas={gap_areas}",
            intake_path,
            "Fill the production intake pack and promote it." if block_count else "None",
        )
    promotion_path = settings.root_dir / "outputs" / "intake_pack" / "promotion_latest.json"
    if promotion is None:
        status, severity, proof = "warn", "warn", "promotion report missing"
    else:
        placeholder_blocked = bool(promotion.get("placeholder_blocked"))
        applied = bool(promotion.get("applied"))
        status = "pass" if applied or placeholder_blocked else "warn"
        severity = "info" if applied or placeholder_blocked else "warn"
        proof = f"applied={applied}, placeholder_blocked={placeholder_blocked}, production_ready={promotion.get('production_ready')}"
    _item(
        items,
        "intake_promotion_safety",
        "Data Quality",
        "Filled intake pack must be blocked when placeholders remain and backed up before production copy.",
        status,
        severity,
        proof,
        promotion_path,
        "Run `python -m app.cli promote-intake-pack --json` or fill placeholders." if promotion is None else "None",
    )
    holdings_path = settings.root_dir / "outputs" / "preflight" / "holdings_discovery_latest.json"
    holdings = _read_json(holdings_path)
    if holdings is None:
        _item(
            items,
            "holdings_review_matrix",
            "Data Quality",
            "Discovered local holding candidates must be triaged into a review matrix before manual promotion.",
            "warn",
            "warn",
            "holdings discovery output missing",
            holdings_path,
            "Run `python -m app.cli discover-holdings --scan-path <path> --json`.",
        )
        return
    review_summary = holdings.get("review_summary") if isinstance(holdings.get("review_summary"), dict) else {}
    review_matrix = holdings.get("review_matrix_csv")
    review_rows = int(review_summary.get("rows") or 0) if isinstance(review_summary, dict) else 0
    matrix_exists = bool(review_matrix) and Path(str(review_matrix)).exists()
    status = "pass" if matrix_exists and review_rows > 0 else "warn"
    _item(
        items,
        "holdings_review_matrix",
        "Data Quality",
        "Discovered local holding candidates must be triaged into a review matrix before manual promotion.",
        status,
        "info" if status == "pass" else "warn",
        (
            f"review_rows={review_rows}, matrix_exists={matrix_exists}, "
            f"row_production_candidate_count={review_summary.get('row_production_candidate_count') if isinstance(review_summary, dict) else None}, "
            f"stale_or_missing_date_count={review_summary.get('stale_or_missing_date_count') if isinstance(review_summary, dict) else None}, "
            f"special_rule_count={review_summary.get('special_fund_rule_check_required_count') if isinstance(review_summary, dict) else None}"
        ),
        holdings_path,
        "Refresh holdings discovery and review matrix." if status != "pass" else "None",
    )
    holdings_md_path = settings.root_dir / "outputs" / "preflight" / "holdings_discovery_latest.md"
    holdings_sensitive_hits = _local_path_sensitive_hits(settings, [holdings_md_path])
    _item(
        items,
        "holdings_discovery_markdown_redaction",
        "Safety",
        "Holdings discovery Markdown must not expose absolute local paths or user-home identifiers.",
        "pass" if not holdings_sensitive_hits else "block",
        "info" if not holdings_sensitive_hits else "critical",
        "no absolute local path markers found" if not holdings_sensitive_hits else f"sensitive path markers={holdings_sensitive_hits}",
        holdings_md_path,
        "Regenerate holdings discovery with redacted Markdown paths." if holdings_sensitive_hits else "None",
    )
    review_prefill = settings.root_dir / "outputs" / "intake_pack" / "06_alipay_positions_review_prefill.csv"
    special_checklist = settings.root_dir / "outputs" / "intake_pack" / "07_special_fund_rule_checklist.csv"
    prefill_rows = _line_count(review_prefill)
    special_rows = _line_count(special_checklist)
    helper_ready = review_prefill.exists() and special_checklist.exists() and prefill_rows > 0 and special_rows > 0
    _item(
        items,
        "intake_review_prefill",
        "Data Quality",
        "Production intake pack should include review-matrix assisted holding prefill and special-fund checklist files.",
        "pass" if helper_ready else "warn",
        "info" if helper_ready else "warn",
        f"review_prefill_rows={prefill_rows}, special_checklist_rows={special_rows}, helper_ready={helper_ready}",
        settings.root_dir / "outputs" / "intake_pack",
        "Regenerate `production-intake-pack` after holdings discovery." if not helper_ready else "None",
    )
    fund_rule_helper = settings.root_dir / "outputs" / "intake_pack" / "08_fund_rules_from_review_checklist.csv"
    fund_rule_helper_rows = _line_count(fund_rule_helper)
    fund_rule_helper_ready = fund_rule_helper.exists() and fund_rule_helper_rows > 0
    _item(
        items,
        "intake_fund_rule_review_helper",
        "Data Quality",
        "Production intake pack should include per-holding fund-rule source queries and required execution fields.",
        "pass" if fund_rule_helper_ready else "warn",
        "info" if fund_rule_helper_ready else "warn",
        f"fund_rule_helper_rows={fund_rule_helper_rows}, helper_ready={fund_rule_helper_ready}",
        fund_rule_helper,
        "Regenerate `production-intake-pack` after holdings discovery." if not fund_rule_helper_ready else "None",
    )
    candidate_helper = settings.root_dir / "outputs" / "intake_pack" / "09_candidate_source_review_prefill.csv"
    candidate_helper_rows = _line_count(candidate_helper)
    candidate_helper_ready = candidate_helper.exists() and candidate_helper_rows > 0
    _item(
        items,
        "intake_candidate_source_helper",
        "Data Quality",
        "Production intake pack should include per-holding candidate source-chain queries for filling candidate universe evidence.",
        "pass" if candidate_helper_ready else "warn",
        "info" if candidate_helper_ready else "warn",
        f"candidate_helper_rows={candidate_helper_rows}, helper_ready={candidate_helper_ready}",
        candidate_helper,
        "Regenerate `production-intake-pack` after holdings discovery." if not candidate_helper_ready else "None",
    )

def _audit_database(settings: Settings, items: list[AuditItem]) -> None:
    db_path = settings.db_path
    if not db_path.exists():
        _item(items, "sqlite_schema", "Archive", "SQLite audit database must exist.", "block", "critical", "database missing", db_path, "Run `python -m app.cli init-db` and a shadow run.")
        return
    init_db(db_path)
    with connect(db_path) as conn:
        missing_tables = sorted(REQUIRED_TABLES - _table_names(conn))
        _item(
            items,
            "sqlite_schema",
            "Archive",
            "SQLite DB must include run/source/score/recommendation/comparison/notification/missing/manual-review/decision audit tables.",
            "pass" if not missing_tables else "block",
            "critical" if missing_tables else "info",
            f"missing_tables={missing_tables}",
            db_path,
            "Run DB migration/init and rerun tests." if missing_tables else "None",
        )
        baseline_path = settings.root_dir / "outputs" / "audit" / "history_integrity_baseline.json"
        if baseline_path.exists():
            history_result = run_history_integrity(settings, baseline_path=baseline_path)
            violations = int(history_result.get("violation_count") or 0)
            _item(
                items,
                "history_integrity_append_only",
                "Archive",
                "Previously observed historical rows and artifacts must remain append-only: no edits, deletes, overwrites, or rerendered past facts.",
                "pass" if history_result.get("status") == "pass" else "block",
                "info" if history_result.get("status") == "pass" else "critical",
                f"baseline={baseline_path}, violations={violations}, latest_manifest={history_result.get('json_path')}",
                history_result.get("json_path") or baseline_path,
                "Restore historical rows/files from backup or create a new forward-only correction record; do not rewrite the baseline." if violations else "None",
            )
        else:
            _item(
                items,
                "history_integrity_append_only",
                "Archive",
                "Previously observed historical rows and artifacts must remain append-only: no edits, deletes, overwrites, or rerendered past facts.",
                "warn",
                "warn",
                "history integrity baseline missing",
                baseline_path,
                "Run `python -m app.cli history-integrity --write-baseline --require-pass --json` after current artifacts are verified.",
            )
        latest = _latest_strategy_run(conn)
        if latest is None:
            _item(items, "latest_strategy_report", "Reporting", "At least one user-visible R-slot report run must exist.", "block", "critical", "no user-visible R-slot strategy run found; future controlled backfills are excluded", db_path, "Run a real Beijing slot or a past-slot backfill, then regenerate reports.")
            return
        run_id = latest["run_id"]
        report_ok = bool(latest["report_path"]) and Path(str(latest["report_path"])).exists()
        html_ok = bool(latest["offline_html_path"]) and Path(str(latest["offline_html_path"])).exists()
        _item(
            items,
            "latest_strategy_report",
            "Reporting",
            "Latest strategy run must have Markdown and offline HTML reports.",
            "pass" if report_ok and html_ok else "block",
            "critical" if not (report_ok and html_ok) else "info",
            f"run_id={run_id}, status={latest['status']}, data_quality_status={latest['data_quality_status']}, markdown={report_ok}, html={html_ok}",
            latest["report_path"] or db_path,
            "Regenerate report and offline HTML." if not (report_ok and html_ok) else "None",
        )
        verification = _latest_strategy_run(conn)
        verification_run_id = verification["run_id"] if verification else None
        verification_run_time = datetime.fromisoformat(str(verification["run_time_bj"])) if verification else None
        latest_tick = conn.execute(
            """
            SELECT action, dry_run FROM automation_tick_log
            WHERE run_id=?
            ORDER BY rowid DESC
            LIMIT 1
            """,
            (verification_run_id,),
        ).fetchone() if verification_run_id else None
        latest_sent = _count(
            conn,
            """
            SELECT count(*) FROM notification_log
            WHERE run_id=?
              AND channel='macos_mail_and_local'
              AND send_status LIKE 'sent%'
              AND error_message IS NULL
            """,
            (verification_run_id,),
        ) if verification_run_id else 0
        verification_kind = (
            "future_controlled_backfill"
            if verification
            and is_future_controlled_backfill(str(verification["run_time_bj"]), str(verification["created_at"]))
            else "live_or_past_run"
        )
        production_backfill_ready = (
            verification is not None
            and str(verification["status"]) == "success"
            and str(verification["data_quality_status"]) == "pass"
            and verification_run_time is not None
            and verification_run_time.weekday() < 5
            and latest_tick is not None
            and latest_tick["action"] in {"ran", "manual_refresh_ran"}
            and int(latest_tick["dry_run"] or 0) == 0
            and latest_sent > 0
        )
        _item(
            items,
            "production_slot_backfill_verified",
            "Automation",
            "Latest production verification must be a non-dry-run Beijing business-day slot with data-quality pass and sent Mail/local notification evidence.",
            "pass" if production_backfill_ready else "block",
            "info" if production_backfill_ready else "critical",
            (
                f"run_id={verification_run_id}, run_time_bj={verification['run_time_bj'] if verification else None}, "
                f"verification_kind={verification_kind}, tick_action={latest_tick['action'] if latest_tick else None}, "
                f"dry_run={latest_tick['dry_run'] if latest_tick else None}, sent_notifications={latest_sent}"
            ),
            db_path,
            "Run a Beijing business-day `automation-tick --no-dry-run --send-mail --local` verification." if not production_backfill_ready else "None",
        )
        offline_index_path = settings.reports_dir / "index.html"
        offline_index_text = offline_index_path.read_text(encoding="utf-8", errors="ignore") if offline_index_path.exists() else ""
        latest_html_name = Path(str(latest["offline_html_path"])).name if latest["offline_html_path"] else ""
        index_latest_ready = offline_index_path.exists() and bool(latest_html_name) and latest_html_name in offline_index_text
        _item(
            items,
            "offline_web_index_updates_latest",
            "Web",
            "Offline web report index must update to include the latest production verification run.",
            "pass" if index_latest_ready else "block",
            "info" if index_latest_ready else "critical",
            (
                f"index={offline_index_path}, latest_html={latest_html_name}, linked={latest_html_name in offline_index_text}"
                if offline_index_path.exists()
                else "offline report index missing"
            ),
            offline_index_path,
            "Regenerate the latest report so `_write_offline_index` refreshes `data/reports/index.html`." if not index_latest_ready else "None",
        )
        source_rows = _count(conn, "SELECT count(*) FROM source_log WHERE run_id=?", (run_id,))
        _item(
            items,
            "source_traceability",
            "Evidence",
            "Every run must persist source traceability records.",
            "pass" if source_rows > 0 else "block",
            "critical" if source_rows == 0 else "info",
            f"run_id={run_id}, source_log_rows={source_rows}",
            db_path,
            "Persist source_log rows for the latest strategy run." if source_rows == 0 else "None",
        )
        top5_rows = _count(conn, "SELECT count(*) FROM recommendation_snapshot WHERE run_id=? AND rank BETWEEN 1 AND 5 AND target_weight IS NOT NULL", (run_id,))
        _item(
            items,
            "top5_weights",
            "Recommendation",
            "All-market mixed Top5 candidate pool and target weights must be produced.",
            "pass" if top5_rows >= 5 else "block",
            "critical" if top5_rows < 5 else "info",
            f"run_id={run_id}, top5_weight_rows={top5_rows}",
            db_path,
            "Run a strategy slot after candidate data is available." if top5_rows < 5 else "None",
        )
        grade_count = _count(conn, "SELECT count(DISTINCT grade) FROM score_snapshot WHERE run_id=?", (run_id,))
        _item(
            items,
            "score_grade_mapping",
            "Scoring",
            "Scoring must map candidates to Action-Ready, Watch, Manual Review, or Block bands.",
            "pass" if grade_count >= 3 else "warn",
            "warn" if grade_count < 3 else "info",
            f"run_id={run_id}, distinct_grade_count={grade_count}",
            db_path,
            "Keep test coverage for all grade bands." if grade_count < 3 else "None",
        )
        conservative_blocks = _count(conn, "SELECT count(*) FROM asset_master WHERE is_excluded=1 AND lower(asset_type) LIKE '%bond%'")
        _item(
            items,
            "conservative_exclusion",
            "Filtering",
            "Bond/money/Yuebao/conservative assets must be excluded from aggressive candidate pool.",
            "pass" if conservative_blocks > 0 else "warn",
            "warn" if conservative_blocks == 0 else "info",
            f"excluded_bond_like_assets={conservative_blocks}",
            db_path,
            "Add regression fixtures for conservative exclusions." if conservative_blocks == 0 else "None",
        )
        hard_gate_rows = _count(
            conn,
            """
            SELECT count(*) FROM manual_review_queue
            WHERE run_id=? AND (reason LIKE '%max_drawdown%' OR reason LIKE '%recovery_time_days%')
            """,
            (run_id,),
        )
        risk_regression_ok, risk_regression_proof, risk_regression_path, risk_regression_next_action = (
            _risk_gate_regression_consistency(settings)
        )
        hard_gate_ready = hard_gate_rows > 0 or risk_regression_ok
        _item(
            items,
            "hard_risk_gate_evidence",
            "Risk",
            "MDD >=40% and recovery >=365 days must create Block/Manual Review evidence.",
            "pass" if hard_gate_ready else "warn",
            "info" if hard_gate_ready else "warn",
            f"run_id={run_id}, hard_gate_review_rows={hard_gate_rows}, {risk_regression_proof}",
            db_path if hard_gate_rows > 0 else risk_regression_path,
            "None" if hard_gate_ready else risk_regression_next_action,
        )
        comparison_types = {
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT compare_type FROM comparison_snapshot WHERE run_id=?",
                (run_id,),
            ).fetchall()
        }
        required_comparisons = {"same_day_previous", "previous_day", "previous_week", "previous_month"}
        missing_comparisons = sorted(required_comparisons - comparison_types)
        _item(
            items,
            "same_day_and_period_comparisons",
            "Comparison",
            "Reports must compare same-day slots and previous day/week/month snapshots.",
            "pass" if not missing_comparisons else "block",
            "critical" if missing_comparisons else "info",
            f"run_id={run_id}, comparison_types={sorted(comparison_types)}",
            db_path,
            f"Generate missing comparison types: {missing_comparisons}." if missing_comparisons else "None",
        )
        discipline_rows = _count(conn, "SELECT count(*) FROM decision_record WHERE run_id=? AND decision_type='discipline_action'", (run_id,))
        rebalance_rows = _count(conn, "SELECT count(*) FROM rebalance_event_log WHERE run_id=?", (run_id,))
        _item(
            items,
            "discipline_actions",
            "Discipline",
            "Serenity baseline reference vs target weights must produce Maintain/Reduce/Increase/Pause/Clear discipline labels; rebalance events are required only when thresholds fire.",
            "pass" if discipline_rows >= 5 else "block",
            "critical" if discipline_rows < 5 else "info",
            f"run_id={run_id}, decision_rows={discipline_rows}, rebalance_events={rebalance_rows}",
            db_path,
            "Run discipline stage and persist decision evidence." if discipline_rows < 5 else "None",
        )
        notification_rows = _count(conn, "SELECT count(*) FROM notification_log WHERE run_id=?", (run_id,))
        _item(
            items,
            "notification_drafts",
            "Notification",
            "Triggering rebalance/risk/watch conditions must create Mail-ready and local-notification artifacts.",
            "pass" if notification_rows > 0 else "block",
            "critical" if notification_rows == 0 else "info",
            f"run_id={run_id}, notification_rows={notification_rows}",
            db_path,
            "Run `python -m app.cli notify --dry-run` for the latest strategy run." if notification_rows == 0 else "None",
        )
        latest_notification = conn.execute(
            "SELECT body_path FROM notification_log WHERE run_id=? ORDER BY rowid DESC LIMIT 1",
            (run_id,),
        ).fetchone()
        report_text = Path(str(latest["report_path"])).read_text(encoding="utf-8", errors="ignore") if report_ok else ""
        notification_path = Path(str(latest_notification["body_path"])) if latest_notification and latest_notification["body_path"] else None
        notification_text = (
            notification_path.read_text(encoding="utf-8", errors="ignore")
            if notification_path and notification_path.exists()
            else ""
        )
        latest_quality = str(latest["data_quality_status"])
        report_locked_en = all(
            marker in report_text
            for marker in ["Execution lock: ON", "Current prohibited action: No-New-Order", "Suggested amount: 0.00", "Suggested units: 0"]
        )
        report_locked_zh = (
            "执行锁：ON" in report_text
            and "No-New-Order" in report_text
            and "建议金额：0.00" in report_text
            and "建议份额：0" in report_text
        )
        report_locked = report_locked_en or report_locked_zh
        notification_locked = (
            ("执行锁：ON" in notification_text or "Execution lock: ON" in notification_text)
            and "No-New-Order" in notification_text
            and ("建议金额：0.00" in notification_text or "Suggested amount: 0.00" in notification_text)
            and ("建议份额：0" in notification_text or "Suggested units: 0" in notification_text)
        )
        execution_lock_ok = latest_quality == "pass" or (report_locked and notification_locked)
        _item(
            items,
            "execution_lock_zero_order",
            "Safety",
            "When latest strategy run is not data-quality pass, reports and notifications must force No-New-Order with suggested amount 0.00 and suggested units 0.",
            "pass" if execution_lock_ok else "block",
            "critical" if not execution_lock_ok else "info",
            (
                f"data_quality_status={latest_quality}, report_locked={report_locked}, notification_locked={notification_locked}"
            ),
            latest["report_path"] or db_path,
            "Regenerate latest report/notification with execution-lock zero-order language." if not execution_lock_ok else "None",
        )
        moomoo_rows = _count(conn, "SELECT count(*) FROM market_kline_snapshot WHERE run_id IN (SELECT run_id FROM run_log WHERE schedule_slot='MOOMOO_COLLECT')")
        _item(
            items,
            "moomoo_kline_archive",
            "Data Source",
            "Read-only MooMoo K-line collection must persist K-line rows and source evidence.",
            "pass" if moomoo_rows > 0 else "warn",
            "warn" if moomoo_rows == 0 else "info",
            f"moomoo_kline_rows={moomoo_rows}",
            db_path,
            "Run `python -m app.cli collect-moomoo ... --require-success`." if moomoo_rows == 0 else "None",
        )
        source_evidence_rows = _count(conn, "SELECT count(*) FROM source_evidence_audit_snapshot")
        source_evidence_audit_runs = _count(conn, "SELECT count(DISTINCT audit_run_id) FROM source_evidence_audit_snapshot")
        _item(
            items,
            "source_evidence_sqlite_archive",
            "Evidence",
            "Source evidence audit rows must be persisted in SQLite for future comparison and review.",
            "pass" if source_evidence_rows > 0 else "warn",
            "info" if source_evidence_rows > 0 else "warn",
            f"source_evidence_rows={source_evidence_rows}, audit_runs={source_evidence_audit_runs}",
            db_path,
            "Run `python -m app.cli source-evidence-audit --json`." if source_evidence_rows == 0 else "None",
        )


def _audit_reports(settings: Settings, items: list[AuditItem]) -> None:
    validation = settings.root_dir / "outputs" / "tests" / "VALIDATION_SUMMARY.md"
    text = validation.read_text(encoding="utf-8") if validation.exists() else ""
    match = re.search(r"\b(\d+) passed\b", text)
    tests_ok = match is not None
    _item(
        items,
        "test_evidence",
        "Testing",
        "Validation summary must record current test pass evidence.",
        "pass" if tests_ok else "block",
        "critical" if not tests_ok else "info",
        f"found `{match.group(0)}`" if match else "`N passed` not found",
        validation,
        "Rerun pytest and update validation summary." if not tests_ok else "None",
    )
    readiness = settings.root_dir / "outputs" / "preflight" / "PRODUCTION_READINESS_REPORT.md"
    readiness_text = readiness.read_text(encoding="utf-8") if readiness.exists() else ""
    boundary_text = readiness_text.lower()
    no_guarantee_en = "future outperformance" in boundary_text and "guarantee" in boundary_text
    no_guarantee_zh = "不承诺" in readiness_text and "未来" in readiness_text and ("跑赢" in readiness_text or "收益" in readiness_text)
    no_guarantee = no_guarantee_en or no_guarantee_zh
    _item(
        items,
        "benchmark_language_boundary",
        "Safety",
        "System may target benchmark outperformance but must not guarantee future outperformance.",
        "pass" if no_guarantee else "block",
        "critical" if not no_guarantee else "info",
        "readiness report includes no-guarantee language" if no_guarantee else "missing no-guarantee language",
        readiness,
        "Add benchmark no-guarantee language to formal report." if not no_guarantee else "None",
    )
    sensitive_hits = _formal_report_sensitive_hits(settings)
    _item(
        items,
        "formal_report_path_redaction",
        "Safety",
        "Formal user-facing readiness report must not expose absolute local paths or user-home identifiers.",
        "pass" if not sensitive_hits else "block",
        "info" if not sensitive_hits else "critical",
        "no absolute local path markers found" if not sensitive_hits else f"sensitive path markers={sensitive_hits}",
        readiness,
        "Remove absolute local paths/user-home identifiers from the formal readiness report and regenerate PDF." if sensitive_hits else "None",
    )
    auxiliary_hits = _auxiliary_markdown_sensitive_hits(settings)
    _item(
        items,
        "auxiliary_markdown_path_redaction",
        "Safety",
        "Auxiliary user-facing Markdown reports must not expose absolute local paths or user-home directories.",
        "pass" if not auxiliary_hits else "block",
        "info" if not auxiliary_hits else "critical",
        "no auxiliary Markdown local path markers found" if not auxiliary_hits else f"sensitive path markers={auxiliary_hits}",
        settings.root_dir / "outputs" / "preflight",
        "Redact auxiliary Markdown path display and regenerate affected reports." if auxiliary_hits else "None",
    )


def run_completion_audit(settings: Settings, write_output: bool = True) -> dict[str, object]:
    settings.ensure_dirs()
    items: list[AuditItem] = []
    preflight = _read_json(settings.root_dir / "outputs" / "preflight" / "preflight_latest.json")
    intake = _read_json(settings.root_dir / "outputs" / "preflight" / "intake_validation_latest.json")
    promotion = _read_json(settings.root_dir / "outputs" / "intake_pack" / "promotion_latest.json")

    _audit_static_and_files(settings, items)
    _audit_preflight(settings, items, preflight)
    _audit_intake(settings, items, intake, promotion)
    _audit_database(settings, items)
    _audit_reports(settings, items)

    block_count = sum(1 for item in items if item.status == "block")
    warn_count = sum(1 for item in items if item.status == "warn")
    pass_count = sum(1 for item in items if item.status == "pass")
    total_count = len(items)
    completion_percent = round((pass_count / total_count * 100.0) if total_count else 0.0, 2)
    result: dict[str, object] = {
        "generated_at": _now(settings),
        "overall_status": "complete" if block_count == 0 else "blocked",
        "completion_percent": completion_percent,
        "pass_count": pass_count,
        "warn_count": warn_count,
        "block_count": block_count,
        "total_count": total_count,
        "items": [asdict(item) for item in items],
    }
    if write_output:
        output_dir = settings.root_dir / "outputs" / "completion_audit"
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "completion_audit_latest.json"
        md_path = output_dir / "completion_audit_latest.md"
        csv_path = output_dir / "completion_audit_latest.csv"
        json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(asdict(items[0]).keys()) if items else [])
            if items:
                writer.writeheader()
                for item in items:
                    writer.writerow(asdict(item))
        lines = [
            "# Serenity Completion Audit",
            "",
            f"- Generated at: {result['generated_at']}",
            f"- Overall status: {result['overall_status']}",
            f"- Completion: {completion_percent:.2f}%",
            f"- Pass/Warn/Block: {pass_count}/{warn_count}/{block_count}",
            "",
            "## Blocking Items",
            "",
        ]
        blockers = [item for item in items if item.status == "block"]
        if blockers:
            for item in blockers:
                lines.append(f"- **{item.item_id}** ({item.area}): {item.requirement}")
                lines.append(f"  - Proof: {redact_text_for_markdown(settings.root_dir, item.proof)}")
                lines.append(f"  - Evidence: `{display_path(settings.root_dir, item.evidence_path)}`")
                lines.append(f"  - Next action: {item.next_action}")
        else:
            lines.append("- None")
        lines.extend(["", "## Full Matrix", ""])
        lines.append("| ID | Area | Status | Severity | Proof | Evidence |")
        lines.append("|---|---|---|---|---|---|")
        for item in items:
            proof = redact_text_for_markdown(settings.root_dir, item.proof).replace("|", "/")
            evidence = display_path(settings.root_dir, item.evidence_path)
            lines.append(f"| {item.item_id} | {item.area} | {item.status} | {item.severity} | {proof} | `{evidence}` |")
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        result["json_path"] = str(json_path)
        result["markdown_path"] = str(md_path)
        result["csv_path"] = str(csv_path)
    return result
