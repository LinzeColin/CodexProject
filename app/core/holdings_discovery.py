from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import Settings
from app.core.path_display import display_path


HOLDINGS_BOOK_FIELDS = {
    "source_system",
    "source_file",
    "symbol",
    "name",
    "market",
    "asset_type",
    "quantity",
    "cost_basis",
    "position_value",
    "unrealized_pnl",
    "weight",
    "updated_at",
    "quality_status",
}


@dataclass(frozen=True)
class DiscoveredHoldingFile:
    path: str
    kind: str
    rows: int
    production_eligible: bool
    reason: str


def _today(settings: Settings) -> date:
    return datetime.now(ZoneInfo(settings.timezone_primary)).date()


def _candidate_paths(paths: list[Path]) -> list[Path]:
    patterns = ("holding", "持仓", "alipay", "支付宝")
    found: list[Path] = []
    for root in paths:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".csv", ".json"}:
                continue
            if any(pattern.lower() in path.name.lower() for pattern in patterns):
                found.append(path)
                if len(found) >= 200:
                    return found
    return found


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                return list(reader.fieldnames or []), list(reader)
        except Exception as exc:
            last_error = exc
    raise ValueError(f"Cannot read CSV {path}: {last_error}")


def _iso_date(value: str) -> date | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        try:
            return date.fromisoformat(raw[:10])
        except ValueError:
            return None


def _holding_code(row: dict[str, str]) -> str:
    symbol = (row.get("symbol") or "").strip()
    if symbol:
        return symbol
    name = (row.get("name") or "").strip()
    safe = "".join(ch if ch.isalnum() else "_" for ch in name)[:80]
    return f"ALIPAY_NAME_{safe}"


def _write_candidate_alipay_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "asset_code",
        "asset_name",
        "platform",
        "current_amount",
        "current_weight",
        "cost_basis",
        "unrealized_pnl",
        "as_of",
        "source_note",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            as_of = (_iso_date(row.get("updated_at", "")) or date.today()).isoformat()
            writer.writerow(
                {
                    "asset_code": _holding_code(row),
                    "asset_name": (row.get("name") or "").strip(),
                    "platform": "Alipay",
                    "current_amount": row.get("position_value") or "0",
                    "current_weight": row.get("weight") or "0",
                    "cost_basis": row.get("cost_basis") or "0",
                    "unrealized_pnl": row.get("unrealized_pnl") or "0",
                    "as_of": as_of,
                    "source_note": (
                        "candidate_from_quantlab_holdings_book; "
                        f"quality={row.get('quality_status', '')}; "
                        "manual_review_required"
                    ),
                }
            )


def _is_special_fund(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in ["qdii", "港", "全球", "海外", "纳斯达克", "标普", "恒生"])


def _review_action(row: dict[str, str], today: date) -> tuple[bool, str, int | None, bool]:
    as_of = _iso_date(row.get("updated_at", ""))
    stale_days = (today - as_of).days if as_of else None
    quality = (row.get("quality_status") or "").strip()
    name = (row.get("name") or "").strip()
    special = _is_special_fund(name)
    blockers: list[str] = []
    if stale_days is None:
        blockers.append("missing_updated_at")
    elif stale_days > 2:
        blockers.append(f"stale_{stale_days}_days")
    elif stale_days < 0:
        blockers.append("future_updated_at")
    if quality != "video_visible":
        blockers.append(f"quality_{quality or 'missing'}")
    if special:
        blockers.append("special_fund_rule_check_required")
    eligible = not blockers
    action = "production_candidate_after_manual_confirm" if eligible else "manual_review_required: " + "; ".join(blockers)
    return eligible, action, stale_days, special


def _write_review_matrix(path: Path, rows: list[dict[str, str]], today: date) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "asset_code",
        "asset_name",
        "current_amount",
        "current_weight",
        "unrealized_pnl",
        "as_of",
        "quality_status",
        "stale_days",
        "special_fund_rule_check_required",
        "row_production_candidate",
        "review_action",
        "source_file",
    ]
    quality_counts: dict[str, int] = {}
    special_count = 0
    stale_count = 0
    production_candidate_count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            quality = (row.get("quality_status") or "").strip()
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
            eligible, action, stale_days, special = _review_action(row, today)
            if special:
                special_count += 1
            if stale_days is None or stale_days > 2:
                stale_count += 1
            if eligible:
                production_candidate_count += 1
            writer.writerow(
                {
                    "asset_code": _holding_code(row),
                    "asset_name": (row.get("name") or "").strip(),
                    "current_amount": row.get("position_value") or "0",
                    "current_weight": row.get("weight") or "0",
                    "unrealized_pnl": row.get("unrealized_pnl") or "0",
                    "as_of": (_iso_date(row.get("updated_at", "")) or date.min).isoformat(),
                    "quality_status": quality,
                    "stale_days": "" if stale_days is None else stale_days,
                    "special_fund_rule_check_required": int(special),
                    "row_production_candidate": int(eligible),
                    "review_action": action,
                    "source_file": row.get("source_file") or "",
                }
            )
    return {
        "rows": len(rows),
        "quality_counts": quality_counts,
        "special_fund_rule_check_required_count": special_count,
        "stale_or_missing_date_count": stale_count,
        "row_production_candidate_count": production_candidate_count,
        "review_matrix_csv": str(path),
    }


def discover_holdings(settings: Settings, scan_paths: list[Path], write_output: bool = True) -> dict[str, object]:
    settings.ensure_dirs()
    paths = _candidate_paths(scan_paths)
    discovered: list[DiscoveredHoldingFile] = []
    converted_csv_path: Path | None = None
    review_matrix_path: Path | None = None
    review_summary: dict[str, object] | None = None
    best_rows: list[dict[str, str]] = []
    today = _today(settings)

    for path in paths:
        if path.suffix.lower() != ".csv":
            discovered.append(DiscoveredHoldingFile(str(path), "candidate_file", 0, False, "non-csv or unsupported candidate"))
            continue
        try:
            fields, rows = _read_csv(path)
        except Exception as exc:
            discovered.append(DiscoveredHoldingFile(str(path), "unreadable_csv", 0, False, str(exc)))
            continue
        fieldset = set(fields)
        if HOLDINGS_BOOK_FIELDS.issubset(fieldset):
            dates = [_iso_date(row.get("updated_at", "")) for row in rows]
            dates = [item for item in dates if item is not None]
            newest = max(dates) if dates else None
            stale_days = (today - newest).days if newest else None
            qualities = sorted({row.get("quality_status", "") for row in rows})
            eligible = bool(rows) and stale_days is not None and stale_days <= 2 and all(q == "video_visible" for q in qualities)
            reason = (
                "production candidate"
                if eligible
                else f"manual_review_required: newest={newest}, stale_days={stale_days}, quality={qualities}"
            )
            discovered.append(DiscoveredHoldingFile(str(path), "quantlab_holdings_book", len(rows), eligible, reason))
            if len(rows) > len(best_rows):
                best_rows = rows
        elif any("交易" in field or "收/支" in field for field in fields):
            discovered.append(DiscoveredHoldingFile(str(path), "alipay_transaction_statement", len(rows), False, "transaction statement is not current holdings"))
        else:
            discovered.append(DiscoveredHoldingFile(str(path), "csv_candidate", len(rows), False, "schema does not match holdings intake"))

    if best_rows and write_output:
        converted_csv_path = settings.root_dir / "outputs" / "preflight" / "alipay_positions_candidate_from_quantlab.csv"
        _write_candidate_alipay_csv(converted_csv_path, best_rows)
        review_matrix_path = settings.root_dir / "outputs" / "preflight" / "alipay_holdings_review_matrix.csv"
        review_summary = _write_review_matrix(review_matrix_path, best_rows, today)

    result: dict[str, object] = {
        "generated_at": datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds"),
        "production_ready_candidate_found": any(item.production_eligible for item in discovered),
        "files": [item.__dict__ for item in discovered],
        "converted_candidate_csv": str(converted_csv_path) if converted_csv_path else None,
        "review_matrix_csv": str(review_matrix_path) if review_matrix_path else None,
        "review_summary": review_summary,
    }
    if write_output:
        output_dir = settings.root_dir / "outputs" / "preflight"
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "holdings_discovery_latest.json"
        md_path = output_dir / "holdings_discovery_latest.md"
        json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        lines = [
            "# Holdings Discovery",
            "",
            f"- Generated at: {result['generated_at']}",
            f"- Production-ready candidate found: {result['production_ready_candidate_found']}",
            f"- Converted candidate CSV: {display_path(settings.root_dir, str(result['converted_candidate_csv']) if result['converted_candidate_csv'] else None)}",
            f"- Review matrix CSV: {display_path(settings.root_dir, str(result['review_matrix_csv']) if result['review_matrix_csv'] else None)}",
            "- Path display: workspace-relative for project files; external local paths are filename-only for privacy.",
            "",
            "## Files",
            "",
        ]
        for item in discovered:
            lines.append(f"- **{item.kind}** rows={item.rows} eligible={item.production_eligible}: `{display_path(settings.root_dir, item.path)}`")
            lines.append(f"  - {item.reason}")
        if not discovered:
            lines.append("- None")
        if review_summary:
            lines.extend(
                [
                    "",
                    "## Review Summary",
                    "",
                    f"- Rows: {review_summary['rows']}",
                    f"- Row production candidates after row-level checks: {review_summary['row_production_candidate_count']}",
                    f"- Stale or missing-date rows: {review_summary['stale_or_missing_date_count']}",
                    f"- Special fund rule check required rows: {review_summary['special_fund_rule_check_required_count']}",
                    f"- Quality counts: `{json.dumps(review_summary['quality_counts'], ensure_ascii=False, sort_keys=True)}`",
                    "",
                    "Rows in the review matrix remain manual-review candidates. They do not unlock production unless the current Alipay page/export confirms fresh holdings and fund-specific rules.",
                ]
            )
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        result["json_path"] = str(json_path)
        result["markdown_path"] = str(md_path)
    return result
