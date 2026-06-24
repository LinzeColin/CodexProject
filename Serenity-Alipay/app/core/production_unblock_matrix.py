from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import Settings
from app.core.intake_validator import validate_intake
from app.core.path_display import display_path


@dataclass(frozen=True)
class UnblockRow:
    area: str
    severity: str
    row_id: str
    field: str
    production_file: str
    intake_pack_file: str
    helper_files: str
    current_failure: str
    required_fix: str
    accepted_sources: str
    source_priority_rule: str
    freshness_requirement: str
    validation_command: str
    promotion_command: str
    preflight_command: str
    unlock_effect: str


AREA_RULES: dict[str, dict[str, str]] = {
    "alipay_positions": {
        "production_file": "data/imports/alipay_positions.csv",
        "intake_pack_file": "outputs/intake_pack/01_alipay_positions_to_fill.csv",
        "helper_files": "outputs/intake_pack/06_alipay_positions_review_prefill.csv",
        "accepted_sources": "Current Alipay export, Alipay current holding page, or manually transcribed current holding with `evidence=/path/or/https-url` in source_note",
        "source_priority_rule": "Alipay/current platform evidence is optional overlay evidence for personal-position review; sample/demo rows are ignored by baseline production gates",
        "freshness_requirement": "as_of must be valid YYYY-MM-DD and no more than 2 Beijing-calendar days stale",
        "unlock_effect": "Unlocks optional personal-position comparison only; baseline ranking and baseline-relative discipline do not depend on this file",
    },
    "fund_rules": {
        "production_file": "data/manual/fund_rules.csv",
        "intake_pack_file": "outputs/intake_pack/02_fund_rules_to_fill.csv",
        "helper_files": "outputs/intake_pack/07_special_fund_rule_checklist.csv; outputs/intake_pack/08_fund_rules_from_review_checklist.csv",
        "accepted_sources": "MooMoo, Alipay fund rule/detail page, fund-company official page, prospectus, official announcement, or an existing local evidence file",
        "source_priority_rule": "source_type must be moomoo/alipay/official, source_priority <= 3, fallback_aggregated=false, url_or_path must be verifiable",
        "freshness_requirement": "Execution-critical fields must reflect the current product rule page; QDII/HK/global/special funds need product-specific confirmation",
        "unlock_effect": "Unlocks executable subscription/redemption/fee constraint checks",
    },
    "candidate_universe": {
        "production_file": "data/manual/candidates.csv",
        "intake_pack_file": "outputs/intake_pack/03_candidates_to_fill.csv",
        "helper_files": "outputs/intake_pack/09_candidate_source_review_prefill.csv",
        "accepted_sources": "MooMoo, Alipay, fund-company official source, official reports, exchange/official platform evidence, or an existing local evidence file",
        "source_priority_rule": "official_source_count >= 2, source_type must be moomoo/alipay/official, fallback_aggregated=false, conflict_flag=false, source_url must be verifiable",
        "freshness_requirement": "missing_nav_days <= 2 and missing_holding_days <= 2",
        "unlock_effect": "Unlocks production-grade all-market mixed Top5 candidate scoring",
    },
    "benchmark_history": {
        "production_file": "data/manual/benchmark_price_history.csv",
        "intake_pack_file": "n/a",
        "helper_files": "outputs/preflight/benchmark_smoke_latest.md",
        "accepted_sources": "MooMoo, official index/exchange provider, or exact public aggregation fallback with metadata",
        "source_priority_rule": "MooMoo/official preferred; public_aggregation is warning-only and cannot override higher-priority conflict",
        "freshness_requirement": "Must cover 1m, 3m, 12m, and recent 10 trading-day windows",
        "unlock_effect": "Maintains Shanghai Composite and S&P 500 benchmark comparison windows",
    },
}


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def _rel(settings: Settings, path: str) -> str:
    try:
        return str((settings.root_dir / path).relative_to(settings.root_dir))
    except ValueError:
        return path


def _rule_for(area: str) -> dict[str, str]:
    return AREA_RULES.get(
        area,
        {
            "production_file": "unknown",
            "intake_pack_file": "unknown",
            "helper_files": "unknown",
            "accepted_sources": "See gap action",
            "source_priority_rule": "See gap action",
            "freshness_requirement": "See gap action",
            "unlock_effect": "Clears corresponding intake validation gap",
        },
    )


def _rows(settings: Settings, gaps: list[dict[str, object]]) -> list[UnblockRow]:
    rows: list[UnblockRow] = []
    for gap in gaps:
        area = str(gap.get("area", ""))
        rule = _rule_for(area)
        rows.append(
            UnblockRow(
                area=area,
                severity=str(gap.get("severity", "")),
                row_id=str(gap.get("row_id", "")),
                field=str(gap.get("field", "")),
                production_file=_rel(settings, rule["production_file"]),
                intake_pack_file=_rel(settings, rule["intake_pack_file"]),
                helper_files=rule["helper_files"],
                current_failure=str(gap.get("message", "")),
                required_fix=str(gap.get("action", "")),
                accepted_sources=rule["accepted_sources"],
                source_priority_rule=rule["source_priority_rule"],
                freshness_requirement=rule["freshness_requirement"],
                validation_command="python -m app.cli validate-intake --scan-path ~/Downloads --scan-path ~/Documents --require-production --json",
                promotion_command="python -m app.cli promote-intake-pack --json && python -m app.cli promote-intake-pack --apply --json",
                preflight_command="python -m app.cli preflight --scan-path ~/Downloads --scan-path ~/Documents --require-production --json",
                unlock_effect=rule["unlock_effect"],
            )
        )
    return rows


def _write_csv(path: Path, rows: list[UnblockRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys()) if rows else [field.name for field in UnblockRow.__dataclass_fields__.values()]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def _write_md(
    path: Path,
    *,
    generated_at: str,
    validation: dict[str, object],
    rows: list[UnblockRow],
    files: dict[str, str],
) -> None:
    by_area = Counter(row.area for row in rows)
    by_severity = Counter(row.severity for row in rows)
    lines = [
        "# Serenity Production Unblock Evidence Matrix",
        "",
        f"- Generated: {generated_at}",
        f"- Production ready: {validation.get('production_ready')}",
        f"- Block count: {validation.get('block_count')}",
        f"- Warn count: {validation.get('warn_count')}",
        f"- Gap count by area: {dict(by_area)}",
        f"- Gap count by severity: {dict(by_severity)}",
        "",
        "## Purpose",
        "",
        (
            "Production preflight currently passes. This matrix records warning/open quality items for evidence refresh. "
            "It is read-only and does not promote or execute any trading action."
            if validation.get("production_ready")
            else "This matrix turns the remaining production blockers into field-level evidence requirements. It is read-only and does not promote or execute any trading action."
        ),
        "",
        "## Files",
        "",
    ]
    for label, file_path in files.items():
        lines.append(f"- `{label}`: `{display_path(path.parents[2], file_path)}`")
    lines.extend(
        [
            "",
            "## Unlock Ladder",
            "",
            "```bash",
            "python -m app.cli production-intake-pack --scan-path ~/Downloads --scan-path ~/Documents --json",
            "python -m app.cli production-unblock-matrix --scan-path ~/Downloads --scan-path ~/Documents --json",
            "python -m app.cli promote-intake-pack --json",
            "python -m app.cli promote-intake-pack --apply --json",
            "python -m app.cli validate-intake --scan-path ~/Downloads --scan-path ~/Documents --require-production --json",
            "python -m app.cli preflight --scan-path ~/Downloads --scan-path ~/Documents --require-production --json",
            "```",
            "",
            (
                "Production preflight currently passes; rerun the last two commands after any evidence refresh to confirm `production_ready=true` remains true."
                if validation.get("production_ready")
                else "Production remains locked until the last two commands return exit code 0 and `production_ready=true`."
            ),
            "",
            "## Area Requirements",
            "",
        ]
    )
    grouped: dict[str, list[UnblockRow]] = defaultdict(list)
    for row in rows:
        grouped[row.area].append(row)
    for area, area_rows in grouped.items():
        rule = _rule_for(area)
        lines.extend(
            [
                f"### {area}",
                "",
                f"- Production file: `{rule['production_file']}`",
                f"- Intake file: `{rule['intake_pack_file']}`",
                f"- Helper files: `{rule['helper_files']}`",
                f"- Accepted sources: {rule['accepted_sources']}",
                f"- Source rule: {rule['source_priority_rule']}",
                f"- Freshness rule: {rule['freshness_requirement']}",
                f"- Unlock effect: {rule['unlock_effect']}",
                "",
                "| Row | Field | Severity | Current failure | Required fix |",
                "|---|---|---|---|---|",
            ]
        )
        for row in area_rows[:30]:
            failure = row.current_failure.replace("|", "/")
            fix = row.required_fix.replace("|", "/")
            lines.append(f"| {row.row_id} | {row.field} | {row.severity} | {failure} | {fix} |")
        if len(area_rows) > 30:
            lines.append(f"| ... | ... | ... | {len(area_rows) - 30} more rows in CSV | ... |")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_production_unblock_matrix(
    settings: Settings,
    *,
    scan_paths: list[Path] | None = None,
    write_output: bool = True,
) -> dict[str, object]:
    settings.ensure_dirs()
    validation = validate_intake(settings, scan_paths=scan_paths or [], write_output=True)
    gaps = [dict(gap) for gap in validation.get("gaps", [])]
    rows = _rows(settings, gaps)
    generated_at = _now(settings)
    output_dir = settings.root_dir / "outputs" / "preflight"
    files = {
        "markdown": str(output_dir / "PRODUCTION_UNBLOCK_EVIDENCE_MATRIX.md"),
        "csv": str(output_dir / "production_unblock_evidence_matrix.csv"),
        "json": str(output_dir / "production_unblock_evidence_matrix.json"),
    }
    result: dict[str, object] = {
        "generated_at": generated_at,
        "production_ready": bool(validation.get("production_ready")),
        "block_count": int(validation.get("block_count") or 0),
        "warn_count": int(validation.get("warn_count") or 0),
        "row_count": len(rows),
        "area_counts": dict(Counter(row.area for row in rows)),
        "severity_counts": dict(Counter(row.severity for row in rows)),
        "files": files,
    }
    if write_output:
        _write_csv(Path(files["csv"]), rows)
        _write_md(Path(files["markdown"]), generated_at=generated_at, validation=validation, rows=rows, files=files)
        Path(files["json"]).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
