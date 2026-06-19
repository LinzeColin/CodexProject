from __future__ import annotations

import csv
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import Settings
from app.core.intake_validator import validate_intake


@dataclass(frozen=True)
class ActionQueueRow:
    priority: str
    blocker: str
    asset_code: str
    asset_name: str
    current_weight: str
    required_evidence: str
    target_file: str
    target_field: str
    preferred_source: str
    suggested_evidence_filename: str
    status: str
    reason: str
    validation_command: str
    unlock_command: str


SOURCE_PRIORITY = "moomoo > alipay > official_platform > trade_snapshot > public_aggregation"
VALIDATION_COMMAND = "python -m app.cli validate-intake --scan-path ~/Downloads --scan-path ~/Documents --require-production --json"
UNLOCK_COMMAND = "python -m app.cli production-unlock-check --apply --scan-path ~/Downloads --scan-path ~/Documents --require-production --json"
NO_NEW_ORDER_STATUS = "No-New-Order; read-only evidence intake; production remains locked"


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _display_path(settings: Settings, value: str | Path) -> str:
    raw = str(value)
    if raw in {"", "n/a"}:
        return raw
    path = Path(raw).expanduser()
    try:
        if path.is_absolute():
            return path.relative_to(settings.root_dir).as_posix()
    except ValueError:
        pass
    home = Path.home()
    try:
        if path.is_absolute():
            return f"<home>/{path.relative_to(home).as_posix()}"
    except ValueError:
        pass
    text = raw.replace(settings.root_dir.as_posix(), "<workspace>")
    text = text.replace(str(home), "<home>")
    return text


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    cleaned = cleaned.strip("._-")
    return cleaned[:90] or "asset"


def _to_float(value: object) -> float:
    try:
        return float(str(value or "0").strip())
    except ValueError:
        return 0.0


def _row(
    *,
    priority: str,
    blocker: str,
    asset_code: str = "GLOBAL",
    asset_name: str = "",
    current_weight: str = "",
    required_evidence: str,
    target_file: str,
    target_field: str,
    preferred_source: str,
    suggested_evidence_filename: str,
    status: str = NO_NEW_ORDER_STATUS,
    reason: str,
) -> ActionQueueRow:
    return ActionQueueRow(
        priority=priority,
        blocker=blocker,
        asset_code=asset_code,
        asset_name=asset_name,
        current_weight=current_weight,
        required_evidence=required_evidence,
        target_file=target_file,
        target_field=target_field,
        preferred_source=preferred_source,
        suggested_evidence_filename=suggested_evidence_filename,
        status=status,
        reason=reason,
        validation_command=VALIDATION_COMMAND,
        unlock_command=UNLOCK_COMMAND,
    )


def _holding_rows(settings: Settings, validation: dict[str, object], review_rows: list[dict[str, str]]) -> list[ActionQueueRow]:
    return []


def _fund_rule_rows(fund_rows: list[dict[str, str]]) -> list[ActionQueueRow]:
    result: list[ActionQueueRow] = []
    for item in fund_rows:
        asset_code = item.get("temporary_asset_code") or item.get("production_asset_code_to_confirm") or "UNKNOWN"
        special = str(item.get("special_rule_required", "")).strip().lower() in {"1", "true", "yes"}
        result.append(
            _row(
                priority="P0",
                blocker="fund_rules",
                asset_code=asset_code,
                asset_name=item.get("asset_name", ""),
                required_evidence=(
                    "Product-specific subscription/redemption status, cut-off, confirmation lag, redeem lag, fees, "
                    "minimum purchase, and as_of from current platform or fund-company rule page."
                ),
                target_file="outputs/intake_pack/02_fund_rules_to_fill.csv",
                target_field=item.get("required_rule_fields", "") or "subscription_status; redemption_status; fees; source_url; as_of",
                preferred_source=item.get("source_priority", "") or SOURCE_PRIORITY,
                suggested_evidence_filename=f"outputs/intake_pack/evidence/{_slug(asset_code)}_fund_rules_YYYY-MM-DD.pdf-or-png",
                reason=(
                    "Special/QDII/HK/global fund rule check required; generic 15:00/T+1 assumption is insufficient."
                    if special
                    else "Execution-critical fee and subscription/redemption rules must be current and source-backed."
                ),
            )
        )
    return result


def _candidate_rows(candidate_rows: list[dict[str, str]]) -> list[ActionQueueRow]:
    result: list[ActionQueueRow] = []
    for item in candidate_rows:
        asset_code = item.get("temporary_asset_code") or item.get("production_asset_code_to_confirm") or "UNKNOWN"
        review_hint = item.get("filter_review_hint", "") or "growth_candidate_review_required"
        result.append(
            _row(
                priority="P1",
                blocker="candidate_universe",
                asset_code=asset_code,
                asset_name=item.get("asset_name", ""),
                required_evidence=(
                    "Two official-grade source-chain references, current NAV/holding freshness <=2 days, no conflict flag, "
                    "and explicit aggressive-growth fit or exclusion decision."
                ),
                target_file="outputs/intake_pack/03_candidates_to_fill.csv",
                target_field="official_source_count; source_type; source_url; missing_nav_days; missing_holding_days; conflict_flag; as_of",
                preferred_source=SOURCE_PRIORITY,
                suggested_evidence_filename=f"outputs/intake_pack/evidence/{_slug(asset_code)}_candidate_sources_YYYY-MM-DD.pdf-or-url-list",
                reason=f"{review_hint}; map only after verification, do not copy helper rows directly.",
            )
        )
    return result


def _generic_gap_rows(settings: Settings, validation: dict[str, object], existing_keys: set[tuple[str, str]]) -> list[ActionQueueRow]:
    target_by_area = {
        "fund_rules": "outputs/intake_pack/02_fund_rules_to_fill.csv",
        "candidate_universe": "outputs/intake_pack/03_candidates_to_fill.csv",
        "benchmark_history": "data/manual/benchmark_price_history.csv",
    }
    rows: list[ActionQueueRow] = []
    for gap in validation.get("gaps", []):
        if not isinstance(gap, dict):
            continue
        area = str(gap.get("area") or "")
        row_id = str(gap.get("row_id") or "UNKNOWN")
        key = (area, row_id)
        if key in existing_keys or area == "alipay_positions":
            continue
        rows.append(
            _row(
                priority="P0" if area == "fund_rules" else ("P1" if area == "candidate_universe" else "P2"),
                blocker=area,
                asset_code=row_id,
                required_evidence=str(gap.get("action") or "Fill the missing production evidence field."),
                target_file=_display_path(settings, target_by_area.get(area, str(gap.get("path") or ""))),
                target_field=str(gap.get("field") or ""),
                preferred_source=SOURCE_PRIORITY,
                suggested_evidence_filename=f"outputs/intake_pack/evidence/{_slug(row_id)}_{_slug(area)}_YYYY-MM-DD.pdf-or-png",
                reason=str(gap.get("message") or "Production intake validation gap."),
            )
        )
    return rows


def _mail_row(preflight: dict[str, object] | None) -> list[ActionQueueRow]:
    blockers = preflight.get("blockers") if isinstance(preflight, dict) else []
    blocker_names = {
        str(blocker.get("name"))
        for blocker in blockers or []
        if isinstance(blocker, dict) and blocker.get("name")
    }
    if "mail_send_config" not in blocker_names:
        return []
    return [
        _row(
            priority="P0",
            blocker="mail_send_config",
            required_evidence="User-approved Apple Mail real-send smoke after data gates clear; do not enable sending before production intake passes.",
            target_file="runtime env / Apple Mail permission",
            target_field="SERENITY_MAIL_SEND_ENABLED; --confirm-real-send SEND",
            preferred_source="macOS Mail app scriptability + explicit user approval.",
            suggested_evidence_filename="outputs/preflight/apple_mail_smoke_latest.json",
            status="deferred_until_data_gates_pass; no real email send from this queue",
            reason="Production alerts cannot claim readiness while SERENITY_MAIL_SEND_ENABLED=false.",
        )
    ]


def _benchmark_upgrade_rows(settings: Settings) -> list[ActionQueueRow]:
    history_path = settings.manual_dir / "benchmark_price_history.csv"
    rows = _read_csv(history_path)
    if not rows:
        return []
    benchmark_names = {"000001.SH": "Shanghai Composite", "SPX": "S&P 500"}
    result: list[ActionQueueRow] = []
    for code, name in benchmark_names.items():
        benchmark_rows = [row for row in rows if row.get("asset_code") == code]
        if not benchmark_rows:
            continue
        if all(row.get("source_type") == "public_aggregation" for row in benchmark_rows):
            result.append(
                _row(
                    priority="P2",
                    blocker="benchmark_source_priority",
                    asset_code=code,
                    asset_name=name,
                    required_evidence=f"Upgrade {name} history from public aggregation fallback to MooMoo or official index/exchange evidence when available.",
                    target_file="data/manual/benchmark_price_history.csv",
                    target_field="source_name; source_type; source_priority; url_or_path; evidence_level; as_of",
                    preferred_source="MooMoo/OpenD > official exchange/index provider > public aggregation fallback.",
                    suggested_evidence_filename=f"outputs/intake_pack/evidence/{_slug(code)}_benchmark_sources_YYYY-MM-DD.pdf-or-url-list",
                    status="optional_quality_upgrade; current production gate may still pass with warning-only fallback",
                    reason=f"{name} still uses public aggregation fallback; benchmark source priority should be upgraded when exact official/MooMoo history is available.",
                )
            )
    return result


def _dedupe(rows: list[ActionQueueRow]) -> list[ActionQueueRow]:
    seen: set[tuple[str, str, str, str]] = set()
    result: list[ActionQueueRow] = []
    for row in rows:
        key = (row.blocker, row.asset_code, row.target_file, row.target_field)
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def _sort(rows: list[ActionQueueRow]) -> list[ActionQueueRow]:
    priority_rank = {"P0": 0, "P1": 1, "P2": 2}
    blocker_rank = {
        "fund_rules": 0,
        "candidate_universe": 1,
        "mail_send_config": 2,
        "benchmark_source_priority": 3,
    }
    return sorted(
        rows,
        key=lambda row: (
            priority_rank.get(row.priority, 9),
            blocker_rank.get(row.blocker, 9),
            -_to_float(row.current_weight),
            row.asset_name,
            row.asset_code,
        ),
    )


def _write_csv(path: Path, rows: list[ActionQueueRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(ActionQueueRow.__dataclass_fields__)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def _write_md(path: Path, *, result: dict[str, object], rows: list[ActionQueueRow]) -> None:
    has_blocking_rows = any(row.priority in {"P0", "P1"} for row in rows)
    lines = [
        "# Serenity Production Action Queue",
        "",
        f"- Generated: {result['generated_at']}",
        f"- Status: {result['status']}",
        f"- Production ready: {result['production_ready']}",
        f"- Row count: {result['row_count']}",
        f"- Priority counts: {result['priority_counts']}",
        f"- Blocker counts: {result['blocker_counts']}",
        "",
        "## Boundary",
        "",
        "- No-New-Order is enforced.",
        "- This queue does not place trades.",
        "- This queue does not send email.",
        "- This queue does not unlock production; it only lists the evidence required before promotion and preflight can pass.",
        "",
        "## Recommended Order",
        "",
    ]
    if has_blocking_rows:
        lines.extend(
            [
                "1. Generate the Serenity baseline from production candidate and fund-rule evidence.",
                "2. Fill P0/P1 fund rules from MooMoo, Alipay, or fund-company official pages into `outputs/intake_pack/02_fund_rules_to_fill.csv`.",
                "3. Fill P1 candidate source-chain evidence into `outputs/intake_pack/03_candidates_to_fill.csv`.",
                "4. Run dry validation, then fail-closed production unlock only after all placeholders and evidence gaps are cleared.",
            ]
        )
    else:
        lines.extend(
            [
                "1. Keep the Serenity baseline candidate and fund-rule evidence fresh.",
                "2. Upgrade P2 benchmark evidence from public aggregation fallback to MooMoo or official index/exchange evidence when available.",
                "3. Rerun validation and completion audit after any evidence refresh.",
            ]
        )
    lines.extend(
        [
        "",
        "```bash",
        "python -m app.cli source-evidence-audit --pack-dir outputs/intake_pack --require-pass --json",
        "python -m app.cli promote-intake-pack --json",
        "python -m app.cli promote-intake-pack --apply --json",
        VALIDATION_COMMAND,
        UNLOCK_COMMAND,
        "```",
        "",
        "## P0 Queue",
        "",
        "| Priority | Blocker | Asset | Weight | Target field | Evidence |",
        "|---|---|---|---|---|---|",
        ]
    )
    p0_rows = [row for row in rows if row.priority == "P0"]
    if not p0_rows:
        lines.append("| - | - | - | - | - | - |")
    for row in p0_rows[:35]:
        asset = f"{row.asset_code} {row.asset_name}".strip().replace("|", "/")
        evidence = row.required_evidence.replace("|", "/")
        lines.append(f"| {row.priority} | {row.blocker} | {asset} | {row.current_weight} | {row.target_field} | {evidence} |")
    if len(p0_rows) > 35:
        lines.append(f"| ... | ... | ... | ... | ... | {len(p0_rows) - 35} more P0 rows in CSV |")
    lines.extend(["", "## Files", ""])
    for label, file_path in (result.get("files") or {}).items():
        lines.append(f"- `{label}`: `{file_path}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_production_action_queue(
    settings: Settings,
    *,
    scan_paths: list[Path] | None = None,
    write_output: bool = True,
) -> dict[str, object]:
    settings.ensure_dirs()
    validation = validate_intake(settings, scan_paths=scan_paths or [], write_output=True)
    preflight = _read_json(settings.root_dir / "outputs" / "preflight" / "preflight_latest.json")

    rows: list[ActionQueueRow] = []
    existing_keys = {(row.blocker, row.asset_code) for row in rows}
    rows.extend(_generic_gap_rows(settings, validation, existing_keys))
    rows.extend(_mail_row(preflight))
    rows.extend(_benchmark_upgrade_rows(settings))
    rows = _sort(_dedupe(rows))
    blocking_rows = [row for row in rows if row.priority in {"P0", "P1"}]

    generated_at = _now(settings)
    output_dir = settings.root_dir / "outputs" / "preflight"
    files = {
        "markdown": "outputs/preflight/production_action_queue_latest.md",
        "csv": "outputs/preflight/production_action_queue_latest.csv",
        "json": "outputs/preflight/production_action_queue_latest.json",
    }
    result: dict[str, object] = {
        "generated_at": generated_at,
        "status": "blocked" if blocking_rows or not validation.get("production_ready") else ("watch" if rows else "pass"),
        "production_ready": False,
        "no_new_order": True,
        "row_count": len(rows),
        "priority_counts": dict(Counter(row.priority for row in rows)),
        "blocker_counts": dict(Counter(row.blocker for row in rows)),
        "validation_status": validation.get("status"),
        "validation_block_count": validation.get("block_count"),
        "validation_warn_count": validation.get("warn_count"),
        "files": files,
    }
    if write_output:
        csv_path = output_dir / "production_action_queue_latest.csv"
        md_path = output_dir / "production_action_queue_latest.md"
        json_path = output_dir / "production_action_queue_latest.json"
        _write_csv(csv_path, rows)
        _write_md(md_path, result=result, rows=rows)
        json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
