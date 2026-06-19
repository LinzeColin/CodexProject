from __future__ import annotations

from pathlib import Path
import json
from datetime import datetime
from typing import Dict, Iterable, List
from zoneinfo import ZoneInfo

from .my_bets import load_snapshot, validate_snapshot


RISKY_AUTOBET_PATTERNS = [
    "page.click(",
    ".click(",
    "mouse.click(",
    "placeBet",
    "place_bet",
    "submitBet",
    "submit_bet",
    "addSelection",
    "add_to_bet",
    "betSlipService",
    "dispatchEvent(",
    "MouseEvent(",
    "fetch(",
    "XMLHttpRequest",
]
ALLOWED_READ_ONLY_CLICK_SNIPPETS = {
    "refresh_tab_readonly.mjs": [
        "readOnlyHeaderLocator.click(",
        "header.dispatchEvent(new MouseEvent(type,",
        "new MouseEvent(type, { bubbles: true, cancelable: true, view: window })",
    ],
}
REPORT_TZ = ZoneInfo("Australia/Sydney")


def audit_automation_preflight(
    code_dir: Path,
    output_dir: Path,
    private_dir: Path,
    safety: Dict,
    portfolio: Dict,
    raw_refresh: Dict | None,
    report_date: str,
    downloads_pdf: Path | None,
    output_pdf: Path,
    bankroll_plan: Path,
    private_output_mode: bool,
    raw_refresh_enabled: bool,
    raw_refresh_succeeded: bool,
    user_automation_authorized: bool,
    automation_authorization: Dict | None = None,
) -> Dict:
    checks = []
    checks.append(
        check_bool(
            "portfolio_gate",
            bool(portfolio.get("portfolio_automation_ready")),
            f"{portfolio.get('ready_required_board_count', 0)}/{portfolio.get('required_board_count', 0)} required boards ready",
        )
    )
    checks.append(
        check_bool(
            "safety_gate",
            bool(safety.get("automation_safety_ready")),
            "; ".join(safety.get("blocking_reasons", [])) or "safety gate clear",
        )
    )
    checks.append(
        check_bool(
            "raw_refresh_enabled",
            raw_refresh_enabled,
            "raw refresh runs before report generation" if raw_refresh_enabled else "raw refresh is disabled",
        )
    )
    checks.append(
        check_bool(
            "raw_refresh_execution",
            raw_refresh_succeeded,
            "raw refresh completed in this run" if raw_refresh_succeeded else "raw refresh did not complete in this run",
        )
    )
    checks.append(
        check_bool(
            "raw_refresh_gate",
            bool(raw_refresh and raw_refresh.get("raw_refresh_ready")),
            "; ".join((raw_refresh or {}).get("blocking_reasons", [])) if raw_refresh else "raw refresh gate is missing",
        )
    )
    if downloads_pdf is not None:
        checks.append(check_file("downloads_pdf", downloads_pdf, min_bytes=10_000))
    checks.append(check_file("output_pdf_copy", output_pdf, min_bytes=10_000))
    checks.append(check_file("bankroll_plan", bankroll_plan, min_bytes=100))

    public_position_files = sorted(path.name for path in output_dir.glob("tab_my_bets_positions_*.json"))
    private_position_paths = sorted(private_dir.glob(f"tab_my_bets_positions_{report_date}.json"))
    private_position_files = [path.name for path in private_position_paths]
    private_position_issues: List[str] = []
    if private_position_paths:
        private_position_issues = validate_private_position_snapshot(load_snapshot(private_position_paths[-1]), report_date)
    capture_diagnostic = load_capture_diagnostic(private_dir, report_date)
    checks.append(
        check_bool(
            "no_private_positions_in_public_outputs",
            not public_position_files,
            ", ".join(public_position_files) if public_position_files else "public outputs clean",
        )
    )
    checks.append(
        check_bool(
            "private_positions_available",
            bool(private_position_files) and private_output_mode and not private_position_issues,
            private_position_message(private_position_files, private_position_issues, capture_diagnostic),
            details=private_position_details(private_position_issues, capture_diagnostic),
        )
    )

    risky_hits = scan_risky_autobet_code(code_dir)
    checks.append(
        check_bool(
            "no_auto_betting_code_path",
            not risky_hits,
            "no risky execution patterns found" if not risky_hits else f"{len(risky_hits)} risky patterns found",
            details=risky_hits,
        )
    )

    technical_ready = all(check["passed"] for check in checks)
    blocking = [check["message"] for check in checks if not check["passed"]]
    authorization_blocking = (automation_authorization or {}).get("blocking_reasons") or ["user has not authorized recurring automation"]
    return {
        "technical_preflight_ready": technical_ready,
        "automation_entry_ready": technical_ready and user_automation_authorized,
        "private_output_mode": private_output_mode,
        "raw_refresh_enabled": raw_refresh_enabled,
        "raw_refresh_succeeded": raw_refresh_succeeded,
        "user_automation_authorized": user_automation_authorized,
        "automation_authorization": automation_authorization or {},
        "checks": checks,
        "blocking_reasons": blocking + ([] if user_automation_authorized else authorization_blocking),
    }


def check_file(name: str, path: Path, min_bytes: int) -> Dict:
    path = Path(path)
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    return {
        "name": name,
        "passed": exists and size >= min_bytes,
        "message": f"{path.name} size={size}",
        "details": {
            "file_name": path.name,
            "exists": exists,
            "size_bytes": size,
            "min_bytes": min_bytes,
        },
    }


def check_bool(name: str, passed: bool, message: str, details: List[Dict] | None = None) -> Dict:
    result = {"name": name, "passed": bool(passed), "message": message}
    if details is not None:
        result["details"] = details
    return result


def validate_private_position_snapshot(snapshot: Dict, report_date: str) -> List[str]:
    issues = validate_snapshot(snapshot)
    if not isinstance(snapshot, dict):
        return issues
    if str(snapshot.get("report_date") or "") != str(report_date):
        issues.append("snapshot report_date does not match current report date")
    summary = snapshot.get("summary") if isinstance(snapshot.get("summary"), dict) else {}
    scraped_at = str(summary.get("scraped_at") or "")
    if not scraped_at:
        issues.append("snapshot scraped_at is missing")
        return issues
    try:
        parsed = datetime.fromisoformat(scraped_at.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            issues.append("snapshot scraped_at is timezone-naive")
            return issues
        if parsed.astimezone(REPORT_TZ).strftime("%d%m%Y") != str(report_date):
            issues.append("snapshot scraped_at is not on current report date")
    except ValueError:
        issues.append("snapshot scraped_at is not valid ISO timestamp")
    return issues


def private_position_message(
    private_position_files: List[str],
    private_position_issues: List[str],
    capture_diagnostic: Dict | None = None,
) -> str:
    if not private_position_files:
        message = "current-day private position snapshot missing"
        diagnostic_message = capture_diagnostic_message(capture_diagnostic)
        return f"{message}; {diagnostic_message}" if diagnostic_message else message
    if private_position_issues:
        return "current-day private position snapshot invalid: " + "; ".join(private_position_issues)
    return "current-day private position snapshot present and valid"


def private_position_details(private_position_issues: List[str], capture_diagnostic: Dict | None) -> List[Dict] | None:
    details: List[Dict] = []
    details.extend({"issue": issue} for issue in private_position_issues)
    diagnostic = public_capture_diagnostic(capture_diagnostic)
    if diagnostic:
        details.append({"capture_diagnostic": diagnostic})
    return details or None


def capture_diagnostic_filename(report_date: str) -> str:
    return f"tab_my_bets_capture_diagnostics_{report_date}.json"


def load_capture_diagnostic(private_dir: Path, report_date: str) -> Dict | None:
    path = Path(private_dir) / capture_diagnostic_filename(report_date)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def capture_diagnostic_message(capture_diagnostic: Dict | None) -> str:
    diagnostic = public_capture_diagnostic(capture_diagnostic)
    if not diagnostic:
        return ""
    auth_status = diagnostic.get("auth_status") or "unknown"
    reason = diagnostic.get("reason") or "no reason supplied"
    auth_mode = diagnostic.get("auth_mode") or "unknown auth mode"
    return f"latest My Bets capture diagnostic: {auth_status} via {auth_mode} ({reason})"


def public_capture_diagnostic(capture_diagnostic: Dict | None) -> Dict | None:
    if not isinstance(capture_diagnostic, dict):
        return None
    return {
        "report_date": capture_diagnostic.get("report_date", ""),
        "ready": bool(capture_diagnostic.get("ready")),
        "auth_status": capture_diagnostic.get("auth_status", ""),
        "auth_mode": capture_diagnostic.get("auth_mode", ""),
        "reason": capture_diagnostic.get("reason", ""),
        "text_length": capture_diagnostic.get("text_length", 0),
    }


def scan_risky_autobet_code(code_dir: Path, patterns: Iterable[str] = RISKY_AUTOBET_PATTERNS) -> List[Dict]:
    hits = []
    pattern_list = list(patterns)
    for path in sorted(Path(code_dir).glob("**/*")):
        if path.suffix not in {".py", ".js", ".mjs", ".cjs"}:
            continue
        if "__pycache__" in path.parts:
            continue
        if path.name == "preflight.py" or "tests" in path.parts:
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            for pattern in pattern_list:
                if pattern in line and not is_allowed_read_only_click(path, line, pattern):
                    hits.append({"path": str(path), "line": line_number, "pattern": pattern})
    return hits


def is_allowed_read_only_click(path: Path, line: str, pattern: str) -> bool:
    if pattern not in {"page.click(", ".click(", "mouse.click(", "dispatchEvent(", "MouseEvent("}:
        return False
    return any(snippet in line for snippet in ALLOWED_READ_ONLY_CLICK_SNIPPETS.get(path.name, []))
