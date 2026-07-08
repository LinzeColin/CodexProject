#!/usr/bin/env python3
"""Minimal Memory Atlas control CLI introduced stage by stage."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHATGPT_SYNC = ROOT / "scripts" / "sync_chatgpt_memory_data.py"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas control CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync = subparsers.add_parser("sync", help="Run source sync.")
    sync.add_argument("--source", required=True)
    sync.add_argument("--dry-run", action="store_true")
    sync.add_argument("--official-export", type=Path)
    return parser.parse_args(argv)


def chatgpt_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "source_id": "chatgpt",
        "dry_run": True,
        "browser_connector": "readonly_contract",
        "fallback": "official_export",
        "writes_files": False,
        "input_required_for_apply": True,
        "no_browser_mutation": True,
    }


def run_sync(args: argparse.Namespace) -> int:
    if args.source != "chatgpt":
        print(json.dumps({
            "status": "NOT_IMPLEMENTED",
            "source_id": args.source,
            "reason": "S04 P1 only implements ChatGPT sync; S04 P2 covers Codex and future-agent adapters.",
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    if args.dry_run and not args.official_export:
        print(json.dumps(chatgpt_contract(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    command = [sys.executable, str(CHATGPT_SYNC), "--database-dir", str(ROOT)]
    if args.official_export:
        command.extend(["--official-export", str(args.official_export)])
    if args.dry_run:
        command.append("--dry-run")
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "sync":
        return run_sync(args)
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
