from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List


SENSITIVE_MARKERS = [
    "sessionId",
    "session_id",
    "sid=",
    "socket",
    "logged_in",
    "logged-in",
    "customer",
    "customerNumber",
    "account",
    "accountNumber",
    "balance",
    "Active Session",
    "My Bets",
    "Bet Slip",
    "Pending Bets",
    "My Offers",
    "/accounts/",
    "REDACTED_ACTIVE_SESSION",
    "REDACTED_BS_LABEL",
    "REDACTED_PENDING_BETS",
    "REDACTED_MY_OFFERS",
    "REDACTED_MB_LABEL",
]
PRIVATE_OUTPUT_FIELD_MARKERS = [
    "placed_at_text",
    "open_stake_aud",
    "estimated_return_aud",
    "estimated_return_if_all_win_aud",
    "potential_profit_if_all_win_aud",
    "tab_my_bets_positions",
    "private_detail_path",
    "positions_ready",
    "private_detail_available",
    "private_match_stakes",
    "match_stakes",
    "open_exposure_aud",
    "remaining_budget_aud",
    "target_new_exposure_aud",
    "/work/private/",
]
SENSITIVE_SUFFIXES = {".json", ".txt", ".html", ".htm", ".md"}
PUBLIC_ARTIFACT_TEXT_SUFFIXES = {".json", ".txt", ".html", ".htm", ".md", ".csv"}
PUBLIC_ARTIFACT_SQLITE_SUFFIXES = {".sqlite", ".sqlite3", ".db"}
PUBLIC_ARTIFACT_BINARY_SUFFIXES = {".pdf"}
PUBLIC_ARTIFACT_SUFFIXES = PUBLIC_ARTIFACT_TEXT_SUFFIXES | PUBLIC_ARTIFACT_SQLITE_SUFFIXES | PUBLIC_ARTIFACT_BINARY_SUFFIXES
PUBLIC_PATH_PATTERNS = [
    re.compile(r"/Users/[^/\s\"'<>]+", re.IGNORECASE),
    re.compile(r"/var/folders/", re.IGNORECASE),
    re.compile(r"/private/var/folders/", re.IGNORECASE),
    re.compile(r"/tmp/", re.IGNORECASE),
    re.compile(r"/private/tmp/", re.IGNORECASE),
    re.compile(r"Downloads/FIFA Report", re.IGNORECASE),
    re.compile(r"/work/private/", re.IGNORECASE),
    re.compile(r"file://", re.IGNORECASE),
]


def audit_safety(
    workspace_dir: Path,
    output_dir: Path,
    private_dir: Path | None = None,
    allow_private_positions: bool = False,
) -> Dict:
    sensitive_artifacts = scan_sensitive_artifacts(workspace_dir, output_dir)
    public_position_files = sorted(public_output_path(output_dir, path) for path in output_dir.rglob("tab_my_bets_positions_*.json"))
    private_position_files = (
        sorted(path.name for path in private_dir.glob("tab_my_bets_positions_*.json"))
        if private_dir
        else []
    )
    private_permission_issues = scan_private_permission_issues(private_dir) if private_dir else []
    blocking_reasons: List[str] = []
    if sensitive_artifacts:
        blocking_reasons.append(
            f"{len(sensitive_artifacts)} scraped artifacts still contain sensitive UI state markers."
        )
    if public_position_files:
        blocking_reasons.append(
            f"{len(public_position_files)} private My Bets snapshots are in public outputs; move them to private storage."
        )
    if private_position_files and not allow_private_positions:
        blocking_reasons.append(
            f"{len(private_position_files)} private My Bets position snapshots exist; automation requires explicit private-output mode."
        )
    if private_permission_issues:
        blocking_reasons.append(
            f"{len(private_permission_issues)} private files or directories are readable by group/other."
        )
    return {
        "automation_safety_ready": not blocking_reasons,
        "allow_private_positions": allow_private_positions,
        "sensitive_artifact_count": len(sensitive_artifacts),
        "sensitive_artifacts": sensitive_artifacts,
        "public_position_file_count": len(public_position_files),
        "public_position_files": public_position_files,
        "private_position_file_count": len(private_position_files),
        "private_position_files_redacted": bool(private_position_files),
        "private_permission_issue_count": len(private_permission_issues),
        "private_permission_issues": private_permission_issues,
        "blocking_reasons": blocking_reasons,
    }


def audit_output_safety(output_dir: Path) -> Dict:
    sensitive_artifacts = scan_public_output_artifacts(output_dir)
    blocking_reasons: List[str] = []
    if sensitive_artifacts:
        blocking_reasons.append(
            f"{len(sensitive_artifacts)} staged output artifacts contain sensitive UI state markers."
        )
    return {
        "automation_safety_ready": not blocking_reasons,
        "sensitive_artifact_count": len(sensitive_artifacts),
        "sensitive_artifacts": sensitive_artifacts,
        "blocking_reasons": blocking_reasons,
    }


def audit_public_artifact_safety(paths: Iterable[Path]) -> Dict:
    issues: List[Dict] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists() or not path.is_file():
            issues.append({"path": path.name, "markers": ["missing_public_artifact"]})
            continue
        try:
            text = public_artifact_text(path)
        except Exception as exc:
            issues.append({"path": path.name, "markers": [f"{type(exc).__name__}: {exc}"]})
            continue
        hits = public_artifact_hits(text)
        if hits:
            issues.append({"path": path.name, "markers": hits})
    blocking_reasons = []
    if issues:
        blocking_reasons.append(f"{len(issues)} current public artifact(s) failed safety scan.")
    return {
        "public_artifact_safety_ready": not issues,
        "public_artifact_issue_count": len(issues),
        "public_artifact_issues": issues,
        "blocking_reasons": blocking_reasons,
    }


def public_artifact_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in PUBLIC_ARTIFACT_TEXT_SUFFIXES:
        return path.read_text(errors="ignore")
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except Exception as exc:
            raise RuntimeError("pypdf is required to scan public PDF artifacts") from exc
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix in PUBLIC_ARTIFACT_SQLITE_SUFFIXES:
        return public_sqlite_text(path)
    return path.read_bytes()[:200_000].decode("utf-8", errors="ignore")


def public_sqlite_text(path: Path) -> str:
    uri = f"file:{Path(path).resolve()}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    try:
        conn.row_factory = sqlite3.Row
        parts = []
        tables = [
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
            if not str(row[0]).startswith("sqlite_")
        ]
        for table in tables:
            columns = conn.execute(f"PRAGMA table_info({table})").fetchall()
            text_columns = [row[1] for row in columns if "TEXT" in str(row[2]).upper()]
            if not text_columns:
                continue
            quoted = ", ".join(f'"{column}"' for column in text_columns)
            for row in conn.execute(f'SELECT {quoted} FROM "{table}"').fetchall():
                for column in text_columns:
                    value = row[column]
                    if value:
                        parts.append(str(value))
        return "\n".join(parts)
    finally:
        conn.close()


def public_artifact_hits(text: str) -> List[str]:
    hits = []
    lower_text = text.lower()
    for marker in PRIVATE_OUTPUT_FIELD_MARKERS + SENSITIVE_MARKERS:
        if marker in {"sid=", "account", "balance", "customer", "socket"}:
            hit = marker.lower() in lower_text and marker_hit(marker, text)
        else:
            hit = marker.lower() in lower_text
        if hit:
            hits.append(safe_marker_name(marker))
    for pattern in PUBLIC_PATH_PATTERNS:
        if pattern.search(text):
            hits.append(safe_marker_name(pattern.pattern))
    return sorted(set(hits))


def scan_sensitive_artifacts(
    workspace_dir: Path,
    output_dir: Path | None = None,
    markers: Iterable[str] = SENSITIVE_MARKERS,
) -> List[Dict]:
    results = scan_workspace_sensitive_artifacts(workspace_dir, markers)
    if output_dir:
        for issue in scan_public_output_artifacts(output_dir):
            results.append(issue)
    return results


def scan_public_output_artifacts(output_dir: Path) -> List[Dict]:
    output_dir = Path(output_dir)
    results: List[Dict] = []
    if not output_dir.exists():
        return results
    for path in sorted(path for path in output_dir.rglob("*") if path.is_file() and path.suffix.lower() in PUBLIC_ARTIFACT_SUFFIXES):
        rel_parts = relative_parts(output_dir, path)
        if "__pycache__" in rel_parts:
            continue
        try:
            text = public_artifact_text(path)
        except Exception as exc:
            results.append({"path": public_output_path(output_dir, path), "markers": [f"{type(exc).__name__}: {exc}"]})
            continue
        hits = sorted(safe_marker_name(marker) for marker in public_artifact_hits(text))
        if hits:
            results.append({"path": public_output_path(output_dir, path), "markers": hits})
    return results


def public_output_path(output_dir: Path, path: Path) -> str:
    try:
        return str(Path(path).relative_to(output_dir))
    except ValueError:
        return Path(path).name


def scan_workspace_sensitive_artifacts(
    workspace_dir: Path,
    markers: Iterable[str] = SENSITIVE_MARKERS,
) -> List[Dict]:
    marker_list = list(markers)
    results = []
    candidates = sensitive_scan_candidates(workspace_dir)
    for path in sorted(path for path in candidates if path.is_file() and path.suffix.lower() in SENSITIVE_SUFFIXES):
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        hits = sorted(safe_marker_name(marker) for marker in marker_list if marker_hit(marker, text))
        if hits:
            results.append({"path": public_workspace_path(path), "markers": hits})
    return results


def public_workspace_path(path: Path) -> str:
    parts = list(path.parts)
    if "tab-research-pipeline" in parts:
        idx = parts.index("tab-research-pipeline")
        return str(Path(*parts[idx:]))
    return path.name


def safe_marker_name(marker: str) -> str:
    names = {
        "/work/private/": "private_path_marker",
        "/accounts/": "account_url_marker",
        "sid=": "sid_param_marker",
        "account": "acct_marker",
        "accountNumber": "acct_number_marker",
        "customer": "cust_marker",
        "customerNumber": "cust_number_marker",
        "balance": "bal_marker",
        r"/Users/[^/\s\"'<>]+": "local_user_path_marker",
        r"/var/folders/": "var_folders_path_marker",
        r"/private/var/folders/": "private_var_folders_path_marker",
        r"/tmp/": "tmp_path_marker",
        r"/private/tmp/": "private_tmp_path_marker",
        r"Downloads/FIFA Report": "downloads_report_path_marker",
        r"file://": "file_uri_marker",
    }
    return names.get(marker, marker)


def sensitive_scan_candidates(workspace_dir: Path) -> List[Path]:
    candidates = list(workspace_dir.glob("scraped_*"))
    candidates.extend(workspace_dir.glob("scraped_tab_js/*"))
    candidates.extend(workspace_dir.glob("work/tmp*/**/*"))
    candidates.extend(workspace_dir.glob("work/*tmp*/**/*"))
    return [
        path
        for path in candidates
        if "private" not in relative_parts(workspace_dir, path) and "__pycache__" not in relative_parts(workspace_dir, path)
    ]


def relative_parts(base: Path, path: Path) -> tuple[str, ...]:
    try:
        return tuple(Path(path).relative_to(base).parts)
    except ValueError:
        return tuple(Path(path).parts)


def scan_private_permission_issues(private_dir: Path) -> List[Dict]:
    issues: List[Dict] = []
    if not private_dir.exists():
        return issues
    for path in [private_dir, *sorted(private_dir.glob("**/*"))]:
        try:
            mode = path.stat().st_mode & 0o777
        except OSError:
            continue
        if mode & 0o077:
            issues.append({"path": private_path_ref(private_dir, path), "mode": oct(mode)})
    return issues


def private_path_ref(private_dir: Path, path: Path) -> str:
    try:
        rel = path.relative_to(private_dir)
    except ValueError:
        return "<private>"
    value = str(rel) if str(rel) != "." else "."
    return f"<private>/{value}"


def ensure_private_tree_permissions(private_dir: Path) -> None:
    private_dir = Path(private_dir)
    private_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    for path in [private_dir, *sorted(private_dir.glob("**/*"))]:
        try:
            os_mode = 0o700 if path.is_dir() else 0o600
            path.chmod(os_mode)
        except OSError:
            continue


def marker_hit(marker: str, text: str) -> bool:
    if marker == "sid=":
        return bool(re.search(r"(?i)(^|[?&;])sid=", text))
    if marker == "account":
        scrubbed = re.sub(r"(?i)login/account/betting UI markers", "login betting UI markers", text)
        scrubbed = re.sub(r"(?i)(?<![A-Za-z0-9_])account-update-pending(?![A-Za-z0-9_])", "funding-update-pending", scrubbed)
        return bool(re.search(r"(?i)(?<![A-Za-z0-9_])account(?![A-Za-z0-9_])", scrubbed))
    if marker == "balance":
        scrubbed = public_safe_balance_text(text)
        return bool(re.search(r"(?i)(?<![A-Za-z0-9_])balance(?![A-Za-z0-9_])", scrubbed))
    if marker in {"balance", "account", "customer", "socket"}:
        return bool(re.search(rf"(?i)(?<![A-Za-z0-9_]){re.escape(marker)}(?![A-Za-z0-9_])", text))
    return marker.lower() in text.lower()


def public_safe_balance_text(text: str) -> str:
    scrubbed = text
    safe_values = r"(account-update-pending|funding-update-pending|private-ready|pending|not-ready|unavailable)"
    scrubbed = re.sub(rf"(?i)(?<![A-Za-z0-9_])balance\s*=\s*{safe_values}(?![A-Za-z0-9_])", "funding_status=public-safe-placeholder", scrubbed)
    scrubbed = re.sub(rf"(?i)\"balance\"\s*:\s*\"?{safe_values}\"?", '"funding_status":"public-safe-placeholder"', scrubbed)
    scrubbed = re.sub(r"(?i)(?<![A-Za-z0-9_])public_visible_balance(?![A-Za-z0-9_])", "public_visible_funding", scrubbed)
    scrubbed = re.sub(r"(?i)(?<![A-Za-z0-9_])balance_display(?![A-Za-z0-9_])", "funding_display", scrubbed)
    return scrubbed


def redact_sensitive_text(text: str) -> str:
    replacements = {
        "sessionId": "REDACTED_SID",
        "session_id": "REDACTED_SID_PARAM",
        "logged-in": "REDACTED_AUTH_STATE",
        "customer": "REDACTED_CUST",
        "account": "REDACTED_ACCT",
        "balance": "REDACTED_BAL",
        "Active Session": "REDACTED_ACTIVE_SESSION",
        "My Bets": "REDACTED_MB_LABEL",
        "Bet Slip": "REDACTED_BS_LABEL",
        "Pending Bets": "REDACTED_PENDING_BETS",
        "My Offers": "REDACTED_MY_OFFERS",
        "push": "REDACTED_MSG",
    }
    redacted = text
    redacted = re.sub(r"(?i)(session[_-]?id|sid|socket[_-]?id|customer(number)?|account(number)?|balance)=([^&\\s\"']+)", r"\1=REDACTED", redacted)
    redacted = re.sub(r"(?i)\"(session[_-]?id|sid|socket[_-]?id|customer(number)?|account(number)?|balance)\"\s*:\s*\"?[^\"]+\"?", r'"\1":"REDACTED"', redacted)
    for source, target in replacements.items():
        redacted = redacted.replace(source, target)
        redacted = redacted.replace(source.upper(), target)
        redacted = redacted.replace(source.title(), target)
    return redacted
