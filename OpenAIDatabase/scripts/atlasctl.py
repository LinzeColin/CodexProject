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
CODEX_SYNC = ROOT / "scripts" / "sync_codex_memory_data.py"
FUTURE_AGENT_SYNC = ROOT / "scripts" / "sync_future_agent_data.py"
BUILD_ATLAS = ROOT / "scripts" / "build_memory_atlas_data.py"
GITHUB_BACKUP = ROOT / "scripts" / "github_backup.py"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas control CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync = subparsers.add_parser("sync", help="Run source sync.")
    sync.add_argument("--source", required=True)
    sync.add_argument("--dry-run", action="store_true")
    sync.add_argument("--official-export", type=Path)
    sync.add_argument("--codex-home", type=Path)
    sync.add_argument("--agent-id", default="future-agent")
    sync.add_argument("--input", type=Path)

    build_atlas = subparsers.add_parser("build-atlas", help="Build derived Memory Atlas visualization data.")
    build_atlas.add_argument("--dry-run", action="store_true")

    push = subparsers.add_parser("push", help="Prepare local GitHub backup scope.")
    mode = push.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    push.add_argument("--database-dir", type=Path, default=ROOT)
    push.add_argument("--message", default="Memory Atlas GitHub backup snapshot")
    return parser.parse_args(argv)


def chatgpt_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "source_id": "chatgpt",
        "dry_run": True,
        "browser_connector": "readonly_contract",
        "fallback": "official_export",
        "writes_files": False,
        "raw_root": "data/public_raw/chatgpt",
        "derived_summary": "data/derived/chatgpt/chatgpt_sync_summary.json",
        "run_log_dir": "data/run_logs/sync_runs",
        "input_required_for_apply": True,
        "no_browser_mutation": True,
    }


def codex_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "source_id": "codex",
        "dry_run": True,
        "sync_mode": "codex_local_sync",
        "writes_files": False,
        "raw_root": "data/public_raw/codex",
        "derived_summary": "data/derived/codex/codex_activity_snapshot.json",
        "run_log_dir": "data/run_logs/sync_runs",
        "append_only": True,
    }


def future_agent_contract(agent_id: str) -> dict[str, object]:
    return {
        "status": "PASS",
        "source_id": "future-agent",
        "agent_id": agent_id,
        "dry_run": True,
        "adapter_mode": "minimal_adapter",
        "writes_files": False,
        "raw_root": f"data/public_raw/agents/{agent_id}",
        "derived_summary": f"data/derived/agents/{agent_id}/agent_sync_summary.json",
        "run_log_dir": "data/run_logs/sync_runs",
        "input_required_for_apply": True,
        "append_only": True,
    }


def run_sync(args: argparse.Namespace) -> int:
    if args.source == "chatgpt" and args.dry_run and not args.official_export:
        print(json.dumps(chatgpt_contract(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.source == "codex" and args.dry_run and not args.codex_home:
        print(json.dumps(codex_contract(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.source == "future-agent" and args.dry_run and not args.input:
        print(json.dumps(future_agent_contract(args.agent_id), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.source == "chatgpt":
        command = [sys.executable, str(CHATGPT_SYNC), "--database-dir", str(ROOT)]
        if args.official_export:
            command.extend(["--official-export", str(args.official_export)])
        if args.dry_run:
            command.append("--dry-run")
    elif args.source == "codex":
        command = [sys.executable, str(CODEX_SYNC), "--database-dir", str(ROOT)]
        if args.codex_home:
            command.extend(["--codex-home", str(args.codex_home)])
        if args.dry_run:
            command.append("--dry-run")
    elif args.source == "future-agent":
        command = [sys.executable, str(FUTURE_AGENT_SYNC), "--database-dir", str(ROOT), "--agent-id", args.agent_id]
        if args.input:
            command.extend(["--input", str(args.input)])
        if args.dry_run:
            command.append("--dry-run")
    else:
        print(json.dumps({
            "status": "NOT_IMPLEMENTED",
            "source_id": args.source,
            "reason": "Unknown sync source. Supported sources: chatgpt, codex, future-agent.",
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode


def run_build_atlas(args: argparse.Namespace) -> int:
    output = "data/derived/visualization/memory_atlas.json"
    if args.dry_run:
        print(json.dumps({
            "status": "PASS",
            "command": "build-atlas",
            "dry_run": True,
            "writes_files": False,
            "output": output,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    command = [sys.executable, str(BUILD_ATLAS), "--database-dir", str(ROOT), "--output", output]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode


def run_push(args: argparse.Namespace) -> int:
    command = [sys.executable, str(GITHUB_BACKUP), "--database-dir", str(args.database_dir)]
    if args.dry_run:
        command.append("--dry-run")
    if args.apply:
        command.extend(["--apply", "--message", args.message])
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
    if args.command == "build-atlas":
        return run_build_atlas(args)
    if args.command == "push":
        return run_push(args)
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
