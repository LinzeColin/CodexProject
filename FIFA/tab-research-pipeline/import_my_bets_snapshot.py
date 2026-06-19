from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from tab_research.artifacts import sanitize_public_manifest
from tab_research.my_bets import write_private_snapshot
from tab_research.paths import resolve_private_dir, resolve_workspace_root


ROOT = resolve_workspace_root(Path(__file__))
DEFAULT_PRIVATE_DIR = resolve_private_dir(Path(__file__))
REPORT_TZ = ZoneInfo("Australia/Sydney")


def default_report_date() -> str:
    return datetime.now(REPORT_TZ).strftime("%d%m%Y")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import read-only TAB My Bets text into a private DDMMYYYY position snapshot."
    )
    parser.add_argument("--source", type=Path, help="Private raw My Bets text file.")
    parser.add_argument("--report-date", default=default_report_date(), help="Report date in DDMMYYYY format.")
    parser.add_argument("--private-dir", type=Path, default=DEFAULT_PRIVATE_DIR, help="Private output directory.")
    parser.add_argument("--source-url", default="", help="Optional private source URL metadata.")
    parser.add_argument("--scraped-at", default="", help="Optional ISO timestamp for the source text.")
    parser.add_argument("--stdin", action="store_true", help="Read raw My Bets text from stdin.")
    parser.add_argument("--dry-run", action="store_true", help="Parse and validate without writing a snapshot file.")
    return parser.parse_args(argv)


def read_source_text(args: argparse.Namespace) -> str:
    if args.stdin:
        return sys.stdin.read()
    if not args.source:
        raise SystemExit("Provide --source or --stdin.")
    return args.source.read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    text = read_source_text(args)
    if args.dry_run:
        from tab_research.my_bets import build_snapshot, validate_snapshot

        snapshot = build_snapshot(text, source_url=args.source_url, scraped_at=args.scraped_at or None)
        snapshot["report_date"] = args.report_date
        issues = validate_snapshot(snapshot)
        print(
            json.dumps(
                sanitize_public_manifest(
                    {
                        "ready": not issues,
                        "report_date": args.report_date,
                        "bet_count": (snapshot.get("summary") or {}).get("bet_count", 0),
                        "pending_count": (snapshot.get("summary") or {}).get("pending_count", 0),
                        "settled_count": (snapshot.get("summary") or {}).get("settled_count", 0),
                        "open_stake_aud": (snapshot.get("summary") or {}).get("open_stake_aud", 0),
                        "realized_pnl_aud": (snapshot.get("summary") or {}).get("realized_pnl_aud", 0),
                        "validation_issues": issues,
                    }
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0 if not issues else 2

    result = write_private_snapshot(
        text,
        args.private_dir,
        args.report_date,
        source_url=args.source_url,
        scraped_at=args.scraped_at or None,
    )
    snapshot = result["snapshot"]
    output = {
        "ready": bool(result["ready"]),
        "report_date": args.report_date,
        "private_snapshot_file": result["path"].name,
        "bet_count": (snapshot.get("summary") or {}).get("bet_count", 0),
        "pending_count": (snapshot.get("summary") or {}).get("pending_count", 0),
        "settled_count": (snapshot.get("summary") or {}).get("settled_count", 0),
        "open_stake_aud": (snapshot.get("summary") or {}).get("open_stake_aud", 0),
        "realized_pnl_aud": (snapshot.get("summary") or {}).get("realized_pnl_aud", 0),
        "validation_issues": snapshot.get("validation_issues", []),
    }
    print(json.dumps(sanitize_public_manifest(output), indent=2, ensure_ascii=False))
    return 0 if result["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
