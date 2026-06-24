from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from app.adapters.alipay_importer import read_positions_csv
from app.adapters.manual_sources import load_candidates, load_fund_rules, load_price_history
from app.config import Settings
from app.core.metrics import WINDOWS, calculate_returns
from app.core.path_display import display_path


SAMPLE_MARKERS = ("sample", "demo", "manual sample", "示例", "样例", "placeholder", "replace_")
CRITICAL_RULE_FIELDS = (
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
)
PRODUCTION_SOURCE_TYPES = {"moomoo", "alipay", "official"}
MIN_BENCHMARK_TRADING_ROWS = 11
EVIDENCE_REF_PATTERN = re.compile(r"(?:evidence|evidence_path|source_path|source_url)=([^;,\n]+)", re.IGNORECASE)


@dataclass(frozen=True)
class IntakeGap:
    area: str
    severity: str
    path: str
    row_id: str
    field: str
    message: str
    action: str


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def _today(settings: Settings) -> date:
    return datetime.now(ZoneInfo(settings.timezone_primary)).date()


def _has_sample_marker(*values: object) -> bool:
    haystack = " ".join(str(value).lower() for value in values if value is not None)
    return any(marker in haystack for marker in SAMPLE_MARKERS)


def _source_ref_status(settings: Settings, raw: object, *, forbidden_path: Path | None = None) -> tuple[bool, str]:
    value = str(raw or "").strip()
    if not value:
        return False, "source reference is empty"
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return True, "valid http(s) URL"
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return False, f"unsupported URL scheme: {parsed.scheme}"
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = settings.root_dir / path
    if forbidden_path is not None:
        try:
            if path.resolve() == forbidden_path.resolve():
                return False, "source reference points to the production CSV itself"
        except FileNotFoundError:
            pass
    if path.exists() and path.is_file():
        return True, "existing local evidence file"
    return False, f"not a valid http(s) URL or existing local file: {value}"


def _source_note_ref_status(settings: Settings, raw: object) -> tuple[bool, str]:
    text = str(raw or "").strip()
    if not text:
        return False, "source_note is empty"
    match = EVIDENCE_REF_PATTERN.search(text)
    if match:
        return _source_ref_status(settings, match.group(1).strip())
    return _source_ref_status(settings, text)


def _gap(
    gaps: list[IntakeGap],
    area: str,
    severity: str,
    path: Path,
    row_id: str,
    field: str,
    message: str,
    action: str,
) -> None:
    gaps.append(IntakeGap(area, severity, str(path), row_id, field, message, action))


def _validate_alipay(settings: Settings, gaps: list[IntakeGap]) -> dict[str, object]:
    path = settings.imports_dir / "alipay_positions.csv"
    if not path.exists():
        return {"path": str(path), "rows": 0, "status": "optional_missing", "production_dependency": False}
    try:
        result = read_positions_csv(path)
    except Exception as exc:
        _gap(gaps, "alipay_positions", "warn", path, "file", "schema", str(exc), "Fix only if you want optional real-holding overlay")
        return {"path": str(path), "rows": 0, "status": "optional_invalid", "production_dependency": False}

    today = _today(settings)
    as_of_values: set[str] = set()
    for row in result.rows:
        row_id = str(row["asset_code"])
        as_of = str(row.get("as_of") or "")
        as_of_values.add(as_of)
        if _has_sample_marker(row.get("source_note")):
            _gap(gaps, "alipay_positions", "warn", path, row_id, "source_note", "optional source_note contains sample/demo marker", "Replace only if you want optional real-holding overlay")
        else:
            source_ref_ok, source_ref_reason = _source_note_ref_status(settings, row.get("source_note"))
            if not source_ref_ok:
                _gap(
                    gaps,
                    "alipay_positions",
                    "warn",
                    path,
                    row_id,
                    "source_note",
                    f"optional source_note lacks verifiable evidence reference: {source_ref_reason}",
                    "Add evidence only if you want optional real-holding overlay",
                )
        try:
            as_of_date = date.fromisoformat(as_of)
        except ValueError:
            _gap(gaps, "alipay_positions", "warn", path, row_id, "as_of", f"Optional invalid as_of date: {as_of}", "Use YYYY-MM-DD if keeping optional holdings")
            continue
        stale_days = (today - as_of_date).days
        if stale_days > 2:
            _gap(gaps, "alipay_positions", "warn", path, row_id, "as_of", f"Optional position snapshot is stale by {stale_days} days", "Refresh only if using real-holding overlay")
        if stale_days < 0:
            _gap(gaps, "alipay_positions", "warn", path, row_id, "as_of", f"Optional position snapshot is in the future: {as_of}", "Correct only if using real-holding overlay")
    for warning in result.warnings:
        _gap(gaps, "alipay_positions", "warn", path, "file", "current_weight", warning, "Confirm weights only if using optional real-holding overlay")
    return {
        "path": str(path),
        "rows": len(result.rows),
        "as_of_values": sorted(as_of_values),
        "status": "optional_checked",
        "production_dependency": False,
    }


def _validate_fund_rules(settings: Settings, gaps: list[IntakeGap]) -> dict[str, object]:
    path = settings.manual_dir / "fund_rules.csv"
    if not path.exists():
        _gap(gaps, "fund_rules", "block", path, "file", "path", "Fund rules CSV is missing", "Create it from app/templates/fund_rules_template.csv")
        return {"path": str(path), "rows": 0, "status": "block"}
    rules = load_fund_rules(path)
    for code, rule in rules.items():
        weak_source = _has_sample_marker(rule.source_name, rule.url_or_path) or rule.url_or_path.startswith("data/")
        if weak_source:
            _gap(gaps, "fund_rules", "block", path, code, "source", "Fund rule source is sample/manual-local", "Replace with Alipay path or fund-company official evidence")
        else:
            source_ref_ok, source_ref_reason = _source_ref_status(settings, rule.url_or_path, forbidden_path=path)
            if not source_ref_ok:
                _gap(
                    gaps,
                    "fund_rules",
                    "block",
                    path,
                    code,
                    "url_or_path",
                    f"Fund rule source evidence is not verifiable: {source_ref_reason}",
                    "Use a valid http(s) URL or an existing local evidence file path",
                )
        if rule.source_type not in PRODUCTION_SOURCE_TYPES:
            _gap(gaps, "fund_rules", "block", path, code, "source_type", f"Source type is not production-grade: {rule.source_type}", "Use moomoo, alipay, or official")
        if rule.source_priority > 3:
            _gap(gaps, "fund_rules", "block", path, code, "source_priority", f"Source priority {rule.source_priority} is below production threshold", "Use source priority 1-3")
        if rule.fallback_aggregated:
            _gap(gaps, "fund_rules", "block", path, code, "fallback_aggregated", "Aggregated fallback cannot unlock execution rules", "Replace with official or Alipay evidence")
        for field in CRITICAL_RULE_FIELDS:
            value = getattr(rule, field)
            if value in (None, ""):
                _gap(gaps, "fund_rules", "block", path, code, field, f"Missing execution-critical field: {field}", "Fill from Alipay/fund official rule page")
    return {"path": str(path), "rows": len(rules), "status": "checked"}


def _validate_candidates(settings: Settings, gaps: list[IntakeGap]) -> dict[str, object]:
    path = settings.manual_dir / "candidates.csv"
    if not path.exists():
        _gap(gaps, "candidate_universe", "block", path, "file", "path", "Candidate universe CSV is missing", "Create it from app/templates/candidates_template.csv")
        return {"path": str(path), "rows": 0, "status": "block"}
    candidates = load_candidates(path)
    for candidate in candidates:
        if candidate.is_excluded:
            continue
        moomoo_local_evidence = (
            candidate.source_type == "moomoo"
            and candidate.source_url.startswith("data/moomoo/")
        )
        weak_source = _has_sample_marker(candidate.asset_name, candidate.source_name, candidate.source_url) or (
            candidate.source_url.startswith("data/") and not moomoo_local_evidence
        )
        if weak_source:
            _gap(gaps, "candidate_universe", "block", path, candidate.asset_code, "source", "Candidate source is sample/manual-local", "Replace with moomoo, Alipay, fund-company, or official source")
        else:
            source_ref_ok, source_ref_reason = _source_ref_status(settings, candidate.source_url, forbidden_path=path)
            if not source_ref_ok:
                _gap(
                    gaps,
                    "candidate_universe",
                    "block",
                    path,
                    candidate.asset_code,
                    "source_url",
                    f"Candidate source evidence is not verifiable: {source_ref_reason}",
                    "Use a valid http(s) URL or an existing local evidence file path",
                )
        if candidate.source_type not in PRODUCTION_SOURCE_TYPES:
            _gap(gaps, "candidate_universe", "block", path, candidate.asset_code, "source_type", f"Source type is not production-grade: {candidate.source_type}", "Use moomoo, alipay, or official")
        if candidate.official_source_count < settings.min_official_sources_action_ready:
            _gap(gaps, "candidate_universe", "block", path, candidate.asset_code, "official_source_count", f"Official source count {candidate.official_source_count} < {settings.min_official_sources_action_ready}", "Add at least two official-grade sources")
        if candidate.fallback_aggregated:
            _gap(gaps, "candidate_universe", "block", path, candidate.asset_code, "fallback_aggregated", "Aggregated fallback cannot unlock production candidate", "Replace with production-grade sources")
        if candidate.conflict_flag:
            _gap(gaps, "candidate_universe", "block", path, candidate.asset_code, "conflict_flag", "Candidate has source conflict flag", "Resolve conflict before production")
        if max(candidate.missing_nav_days, candidate.missing_holding_days) > 2:
            _gap(gaps, "candidate_universe", "block", path, candidate.asset_code, "missing_days", "NAV/holding missing >2 days", "Refresh NAV and holding evidence")
    return {"path": str(path), "rows": len(candidates), "status": "checked"}


def _price_history_columns(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return set(reader.fieldnames or [])


def _validate_candidate_nav_history(settings: Settings, gaps: list[IntakeGap]) -> dict[str, object]:
    path = settings.manual_dir / "price_history.csv"
    candidates_path = settings.manual_dir / "candidates.csv"
    if not candidates_path.exists():
        return {"path": str(path), "rows": 0, "status": "skipped_candidate_universe_missing"}
    if not path.exists():
        _gap(
            gaps,
            "candidate_nav_history",
            "block",
            path,
            "file",
            "path",
            "Candidate NAV history CSV is missing",
            "Run collect-fund-nav-history --apply to provide 24-month NAV history",
        )
        return {"path": str(path), "rows": 0, "status": "block"}

    history = load_price_history(path)
    candidates = [candidate for candidate in load_candidates(settings.manual_dir / "candidates.csv") if not candidate.is_excluded]
    columns = _price_history_columns(path)
    required_meta = {"source_name", "source_type", "source_priority", "url_or_path", "evidence_level", "as_of"}
    missing_meta = sorted(required_meta - columns)
    for candidate in candidates:
        points = history.get(candidate.asset_code, [])
        if not points:
            _gap(
                gaps,
                "candidate_nav_history",
                "block",
                path,
                candidate.asset_code,
                "asset_code",
                "Candidate has no NAV history",
                "Fetch or stage 24-month NAV history before allowing the fund into screening scope",
            )
            continue
        span_days = (points[-1].date - points[0].date).days if len(points) >= 2 else 0
        if span_days < settings.min_candidate_nav_history_span_days:
            _gap(
                gaps,
                "candidate_nav_history",
                "block",
                path,
                candidate.asset_code,
                "date_span",
                (
                    f"Candidate NAV history spans only {span_days} days; "
                    f"requires {settings.min_candidate_nav_history_months} months / "
                    f"{settings.min_candidate_nav_history_span_days} days"
                ),
                "Fetch complete 24-month NAV history before screening or action-ready recommendation",
            )
        if missing_meta:
            _gap(
                gaps,
                "candidate_nav_history",
                "block",
                path,
                candidate.asset_code,
                "source_metadata",
                f"Missing NAV source metadata columns: {', '.join(missing_meta)}",
                "Use collect-fund-nav-history or add verifiable source metadata columns",
            )
    if not missing_meta:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        for candidate in candidates:
            candidate_rows = [row for row in rows if row.get("asset_code") == candidate.asset_code]
            if candidate_rows and all(row.get("source_type") == "public_aggregation" for row in candidate_rows):
                _gap(
                    gaps,
                    "candidate_nav_history",
                    "warn",
                    path,
                    candidate.asset_code,
                    "source_type",
                    "Candidate NAV history uses public aggregation fallback",
                    "Prefer moomoo, Alipay, or fund-company official NAV source when available",
                )
    return {"path": str(path), "rows": sum(len(points) for points in history.values()), "status": "checked"}


def _validate_benchmarks(settings: Settings, gaps: list[IntakeGap]) -> dict[str, object]:
    path = settings.manual_dir / "benchmark_price_history.csv"
    if not path.exists():
        path = settings.manual_dir / "price_history.csv"
    if not path.exists():
        _gap(gaps, "benchmark_history", "block", path, "file", "path", "Price history CSV is missing", "Provide exact benchmark history with source metadata")
        return {"path": str(path), "rows": 0, "status": "block"}
    history = load_price_history(path)
    columns = _price_history_columns(path)
    required_meta = {"source_name", "source_type", "source_priority", "url_or_path", "evidence_level", "as_of"}
    missing_meta = sorted(required_meta - columns)
    for code, name in [("000001.SH", "Shanghai Composite"), ("SPX", "S&P 500")]:
        points = history.get(code, [])
        if not points:
            _gap(gaps, "benchmark_history", "block", path, code, "asset_code", f"{name} benchmark history missing", "Add exact benchmark history")
            continue
        if len(points) < 11:
            _gap(gaps, "benchmark_history", "block", path, code, "rows", f"{name} has only {len(points)} rows", "Provide enough rows for recent 10 trading day comparison")
        elif (points[-1].date - points[0].date).days < 365:
            span_days = (points[-1].date - points[0].date).days
            _gap(gaps, "benchmark_history", "block", path, code, "date_span", f"{name} history spans only {span_days} days", "Provide enough exact benchmark history for 1m, 3m, 12m, and recent 10 trading day comparison")
        else:
            returns = calculate_returns(points)
            missing_windows = [window for window in WINDOWS if returns.get(window) is None]
            if missing_windows:
                _gap(
                    gaps,
                    "benchmark_history",
                    "block",
                    path,
                    code,
                    "return_windows",
                    f"{name} benchmark return windows missing: {', '.join(missing_windows)}",
                    "Provide exact benchmark history that can calculate 1m, 3m, 12m, and recent 10 trading day returns",
                )
        if points[0].close == 100.0 and _has_sample_marker(path.name, "manual"):
            _gap(gaps, "benchmark_history", "block", path, code, "close", f"{name} looks sample-indexed from 100.0", "Replace with real close values from exact benchmark source")
        if missing_meta:
            _gap(gaps, "benchmark_history", "block", path, code, "source_metadata", f"Missing source metadata columns: {', '.join(missing_meta)}", "Use app/templates/benchmark_price_history_template.csv shape or add metadata columns")
        if not missing_meta:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                benchmark_rows = [
                    row for row in csv.DictReader(handle)
                    if row.get("asset_code") == code
                ]
            if benchmark_rows and all(row.get("source_type") == "public_aggregation" for row in benchmark_rows):
                _gap(gaps, "benchmark_history", "warn", path, code, "source_type", f"{name} uses public aggregation fallback", "Prefer moomoo or official source when available")
    return {"path": str(path), "rows": sum(len(points) for points in history.values()), "status": "checked"}


def _scan_candidates(paths: list[Path]) -> list[dict[str, str]]:
    patterns = ("alipay", "支付宝", "fund", "基金", "holding", "持仓")
    matches: list[dict[str, str]] = []
    for root in paths:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".csv", ".xlsx", ".xls", ".json"}:
                continue
            name = path.name.lower()
            if any(pattern.lower() in name for pattern in patterns):
                matches.append({"path": str(path), "name": path.name, "suffix": path.suffix.lower()})
                if len(matches) >= 100:
                    return matches
    return matches


def _write_gaps_csv(path: Path, gaps: list[IntakeGap]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["area", "severity", "path", "row_id", "field", "message", "action"])
        writer.writeheader()
        for gap in gaps:
            writer.writerow(asdict(gap))


def validate_intake(settings: Settings, scan_paths: list[Path] | None = None, write_output: bool = True) -> dict[str, object]:
    settings.ensure_dirs()
    gaps: list[IntakeGap] = []
    sections = {
        "alipay_positions": _validate_alipay(settings, gaps),
        "fund_rules": _validate_fund_rules(settings, gaps),
        "candidate_universe": _validate_candidates(settings, gaps),
        "candidate_nav_history": _validate_candidate_nav_history(settings, gaps),
        "benchmark_history": _validate_benchmarks(settings, gaps),
    }
    scanned = _scan_candidates(scan_paths or [])
    block_count = sum(1 for gap in gaps if gap.severity == "block")
    warn_count = sum(1 for gap in gaps if gap.severity == "warn")
    result: dict[str, object] = {
        "generated_at": _now(settings),
        "production_ready": block_count == 0,
        "status": "pass" if block_count == 0 else "blocked",
        "block_count": block_count,
        "warn_count": warn_count,
        "sections": sections,
        "gaps": [asdict(gap) for gap in gaps],
        "candidate_files_found": scanned,
    }
    if write_output:
        output_dir = settings.root_dir / "outputs" / "preflight"
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "intake_validation_latest.json"
        md_path = output_dir / "intake_validation_latest.md"
        csv_path = output_dir / "intake_gap_latest.csv"
        json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        _write_gaps_csv(csv_path, gaps)
        lines = [
            "# Intake Validation",
            "",
            f"- Generated at: {result['generated_at']}",
            f"- Production ready: {result['production_ready']}",
            f"- Block gaps: {block_count}",
            f"- Warn gaps: {warn_count}",
            "",
            "## Gaps",
            "",
        ]
        if gaps:
            for gap in gaps:
                lines.append(f"- **{gap.area} / {gap.row_id} / {gap.field}** [{gap.severity}]: {gap.message}")
                lines.append(f"  - Action: {gap.action}")
        else:
            lines.append("- None")
        lines.extend(["", "## Candidate Files Found", ""])
        if scanned:
            for item in scanned:
                lines.append(f"- {display_path(settings.root_dir, item['path'])}")
        else:
            lines.append("- None")
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        result["json_path"] = str(json_path)
        result["markdown_path"] = str(md_path)
        result["csv_path"] = str(csv_path)
    return result
