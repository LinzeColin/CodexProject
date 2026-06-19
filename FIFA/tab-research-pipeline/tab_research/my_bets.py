from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


BET_DATE_RE = re.compile(r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun) \d{2} [A-Za-z]{3} - \d{2}:\d{2}:\d{2}$")
MONEY_RE = re.compile(r"\$([0-9,.]+)")
PENDING_STATUSES = {"pending"}
LOST_STATUSES = {"lost", "failed"}
REFUNDED_STATUSES = {"void", "refunded", "cancelled", "canceled"}
CASHED_OUT_STATUSES = {"cashed out", "cash out"}
SETTLED_STATUSES = {"won", *LOST_STATUSES, *REFUNDED_STATUSES, *CASHED_OUT_STATUSES}
KNOWN_STATUSES = PENDING_STATUSES | SETTLED_STATUSES
SNAPSHOT_SCHEMA_VERSION = 1


def parse_my_bets_text(text: str) -> List[Dict]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    blocks: List[List[str]] = []
    idx = 0
    while idx < len(lines):
        if BET_DATE_RE.match(lines[idx]):
            start = idx
            idx += 1
            while idx < len(lines) and not BET_DATE_RE.match(lines[idx]) and lines[idx] != "Language:":
                idx += 1
            blocks.append(lines[start:idx])
            continue
        idx += 1
    return [parse_bet_block(block, bet_id + 1) for bet_id, block in enumerate(blocks)]


def parse_bet_block(block: List[str], bet_id: int) -> Dict:
    stake_idx = find_index(block, "Stake")
    odds_idx = find_index(block, "Odds")
    return_idx = find_index(block, "Estimated Return")
    meta_end = stake_idx if stake_idx >= 0 else len(block)
    meta = block[:meta_end]
    selection_lines = meta[4:]
    stake = parse_money(block[stake_idx + 1]) if stake_idx >= 0 and stake_idx + 1 < len(block) else None
    estimated_return = (
        parse_money(block[return_idx + 1]) if return_idx >= 0 and return_idx + 1 < len(block) else None
    )
    return {
        "id": bet_id,
        "placed_at_text": meta[0] if len(meta) > 0 else "",
        "product": meta[1] if len(meta) > 1 else "",
        "bet_type": meta[2] if len(meta) > 2 else "",
        "status": meta[3] if len(meta) > 3 else "",
        "selection": selection_lines[0] if selection_lines else "",
        "market": " / ".join(selection_lines[1:]),
        "stake_aud": stake,
        "odds": parse_float(block[odds_idx + 1]) if odds_idx >= 0 and odds_idx + 1 < len(block) else None,
        "estimated_return_aud": estimated_return,
        "potential_profit_aud": round(estimated_return - stake, 2)
        if estimated_return is not None and stake is not None
        else None,
    }


def summarize_bets(bets: List[Dict], source_url: str = "", scraped_at: Optional[str] = None) -> Dict:
    status_counts: Dict[str, int] = {}
    for bet in bets:
        status = normalize_status(bet.get("status", ""))
        status_counts[status] = status_counts.get(status, 0) + 1
    unknown_statuses = sorted(status for status in status_counts if status not in KNOWN_STATUSES)
    pending = [bet for bet in bets if normalize_status(bet.get("status", "")) in PENDING_STATUSES]
    settled = [bet for bet in bets if normalize_status(bet.get("status", "")) in SETTLED_STATUSES]
    total_stake = sum(float(bet.get("stake_aud") or 0) for bet in bets)
    settled_stake = sum(float(bet.get("stake_aud") or 0) for bet in settled)
    open_stake = sum(float(bet.get("stake_aud") or 0) for bet in pending)
    estimated_return = sum(float(bet.get("estimated_return_aud") or 0) for bet in pending)
    potential_profit = sum(float(bet.get("potential_profit_aud") or 0) for bet in pending)
    realized_pnl = sum(realized_pnl_for_bet(bet) for bet in settled)
    return {
        "scraped_at": scraped_at or datetime.now(timezone.utc).isoformat(),
        "source_url": source_url,
        "bet_count": len(bets),
        "pending_count": len(pending),
        "settled_count": len(settled),
        "unknown_status_count": sum(status_counts[status] for status in unknown_statuses),
        "unknown_statuses": unknown_statuses,
        "status_counts": status_counts,
        "position_statuses_valid": not unknown_statuses,
        "total_stake_aud": round(total_stake, 2),
        "settled_stake_aud": round(settled_stake, 2),
        "open_stake_aud": round(open_stake, 2),
        "estimated_return_if_all_win_aud": round(estimated_return, 2),
        "potential_profit_if_all_win_aud": round(potential_profit, 2),
        "realized_pnl_aud": round(realized_pnl, 2),
        "realized_roi": realized_pnl / settled_stake if settled_stake else 0,
        "note": "Pending bets are excluded from realized ROI until settlement; realized ROI uses settled stake only.",
    }


def build_snapshot(text: str, source_url: str = "", scraped_at: Optional[str] = None) -> Dict:
    bets = parse_my_bets_text(text)
    summary = summarize_bets(bets, source_url=source_url, scraped_at=scraped_at)
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "private_snapshot": True,
        "summary": summary,
        "bets": bets,
    }


def snapshot_filename(report_date: str) -> str:
    normalized = normalize_report_date(report_date)
    return f"tab_my_bets_positions_{normalized}.json"


def normalize_report_date(report_date: str) -> str:
    value = str(report_date or "").strip()
    if not re.fullmatch(r"\d{8}", value):
        raise ValueError("report_date must use DDMMYYYY format")
    return value


def validate_snapshot(snapshot: Dict) -> List[str]:
    issues: List[str] = []
    if not isinstance(snapshot, dict):
        return ["snapshot is not a JSON object"]
    summary = snapshot.get("summary")
    bets = snapshot.get("bets")
    if not isinstance(summary, dict):
        issues.append("summary is missing")
        summary = {}
    if not isinstance(bets, list):
        issues.append("bets list is missing")
        bets = []
    if int(summary.get("bet_count") or 0) != len(bets):
        issues.append("summary bet_count does not match bets length")
    if summary.get("position_statuses_valid") is not True:
        issues.append("position statuses are not fully recognized")
    if int(summary.get("unknown_status_count") or 0) > 0:
        issues.append("snapshot contains unknown bet statuses")
    return issues


def assert_private_snapshot_dir(private_dir: Path) -> Path:
    resolved = Path(private_dir).expanduser().resolve()
    parts = normalized_private_guard_parts(resolved)
    if "private" not in parts:
        raise ValueError("My Bets snapshot directory must be under a private path")
    private_index = parts.index("private")
    if "outputs" in parts and parts.index("outputs") < private_index:
        raise ValueError("My Bets snapshot directory must not be under public outputs")
    return resolved


def normalized_private_guard_parts(path: Path) -> List[str]:
    parts = [part.lower() for part in Path(path).parts if part and part != Path(path).anchor]
    if len(parts) >= 2 and parts[0] == "private" and parts[1] in {"tmp", "var"}:
        parts = parts[2:]
    return parts


def write_private_snapshot(
    text: str,
    private_dir: Path,
    report_date: str,
    source_url: str = "",
    scraped_at: Optional[str] = None,
) -> Dict:
    import json
    import os

    private_dir = assert_private_snapshot_dir(private_dir)
    private_dir.mkdir(parents=True, exist_ok=True)
    try:
        private_dir.chmod(0o700)
    except OSError:
        pass
    snapshot = build_snapshot(text, source_url=source_url, scraped_at=scraped_at)
    snapshot["report_date"] = normalize_report_date(report_date)
    snapshot["validation_issues"] = validate_snapshot(snapshot)
    path = private_dir / snapshot_filename(report_date)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        tmp.chmod(0o600)
    except OSError:
        pass
    os.replace(tmp, path)
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return {
        "path": path,
        "snapshot": snapshot,
        "ready": not snapshot["validation_issues"],
    }


def load_snapshot(path: Path) -> Dict:
    import json

    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def realized_pnl_for_bet(bet: Dict) -> float:
    status = normalize_status(bet.get("status", ""))
    stake = float(bet.get("stake_aud") or 0)
    estimated_return = float(bet.get("estimated_return_aud") or 0)
    if status == "won":
        return estimated_return - stake
    if status in LOST_STATUSES:
        return -stake
    if status in REFUNDED_STATUSES:
        return 0.0
    if status in CASHED_OUT_STATUSES:
        return estimated_return - stake
    return 0.0


def normalize_status(status: str) -> str:
    return re.sub(r"\s+", " ", str(status or "").strip().lower())


def find_index(block: List[str], value: str) -> int:
    try:
        return block.index(value)
    except ValueError:
        return -1


def parse_money(value: str) -> Optional[float]:
    match = MONEY_RE.search(value or "")
    return float(match.group(1).replace(",", "")) if match else None


def parse_float(value: str) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
