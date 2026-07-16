#!/usr/bin/env python3
"""Verified production entry for natural KMFA attendance automations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from KMFA.tools.dingtalk_attendance.production_release import ProductionReleaseError, verify_release


AUTOMATION_IDS = {"morning": "kmfa", "evening": "kmfa-3"}
PROMPT_PATHS = {
    "morning": Path("KMFA/kmfa-dingtalk-attendance-skill/automation/morning_prompt.md"),
    "evening": Path("KMFA/kmfa-dingtalk-attendance-skill/automation/evening_prompt.md"),
}
PRIVATE_DIAGNOSTIC_PATH = Path(
    "KMFA/metadata/dingtalk_attendance/private_runtime/production_release/latest_repository_diagnostic.json"
)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.rstrip("\n").encode("utf-8")).hexdigest()


def verify_live_prompt(*, release_root: Path, run_slot: str, automation_id: str, home: Path | None = None) -> dict[str, Any]:
    expected_id = AUTOMATION_IDS[run_slot]
    if automation_id != expected_id:
        raise ProductionReleaseError("automation id does not match the release run slot")
    prompt_path = release_root / PROMPT_PATHS[run_slot]
    expected_prompt = prompt_path.read_text(encoding="utf-8").rstrip("\n")
    config_path = (home or Path.home()) / ".codex/automations" / automation_id / "automation.toml"
    try:
        live_prompt = str(tomllib.loads(config_path.read_text(encoding="utf-8"))["prompt"]).rstrip("\n")
    except (OSError, KeyError, tomllib.TOMLDecodeError) as exc:
        raise ProductionReleaseError("live automation prompt cannot be read") from exc
    if live_prompt != expected_prompt:
        raise ProductionReleaseError("live automation prompt does not match the immutable release")
    return {
        "status": "PASS",
        "automation_id": automation_id,
        "prompt_sha256": _sha256_text(live_prompt),
    }


def _git_value(repo: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args], cwd=repo, text=True, capture_output=True, timeout=5, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return "UNAVAILABLE"
    return result.stdout.strip() if result.returncode == 0 else "UNAVAILABLE"


def record_repository_diagnostics(repo: Path, *, output_path: Path | None = None) -> dict[str, Any]:
    status = _git_value(repo, "status", "--porcelain", "-z")
    dirty_paths: list[str] = []
    if status != "UNAVAILABLE":
        for entry in status.split("\0"):
            if not entry:
                continue
            dirty_paths.append(entry[3:] if len(entry) > 3 else entry)
    diagnostic = {
        "recorded_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "repository_diagnostics_only": True,
        "branch": _git_value(repo, "branch", "--show-current"),
        "head": _git_value(repo, "rev-parse", "HEAD"),
        "origin_main": _git_value(repo, "rev-parse", "origin/main"),
        "dirty_paths": dirty_paths,
        "blocks_attendance": False,
    }
    path = output_path or repo / PRIVATE_DIAGNOSTIC_PATH
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            json.dump(diagnostic, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            temporary = Path(handle.name)
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except OSError:
        diagnostic["diagnostic_write_status"] = "UNAVAILABLE_NON_BLOCKING"
    return diagnostic


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run KMFA attendance from a verified immutable release.")
    parser.add_argument("--run-slot", choices=("morning", "evening"), required=True)
    parser.add_argument("--trigger-source", choices=("automation", "manual"), default="manual")
    parser.add_argument("--automation-id", choices=("kmfa", "kmfa-3"), required=True)
    parser.add_argument("--resume-final-only", action="store_true")
    parser.add_argument("--allow-dws-commands", action="store_true")
    args = parser.parse_args(argv)
    release_root = Path(__file__).resolve().parents[3]
    try:
        release = verify_release(release_root)
        prompt = verify_live_prompt(
            release_root=release_root,
            run_slot=args.run_slot,
            automation_id=args.automation_id,
        )
    except (OSError, ProductionReleaseError) as exc:
        print(
            json.dumps(
                {
                    "status": "PRODUCTION_RELEASE_GATE_FAILED",
                    "error_code": exc.__class__.__name__,
                    "detail": str(exc),
                    "notification_status": "NOT_SENT",
                },
                ensure_ascii=False,
            )
        )
        return 8
    repo = Path.cwd()
    record_repository_diagnostics(repo)
    os.environ["KMFA_ATTENDANCE_PRODUCTION_FINGERPRINT"] = release["attendance_runtime_fingerprint"]
    os.environ["KMFA_ATTENDANCE_PRODUCTION_SOURCE_COMMIT"] = release["source_commit"]
    os.environ["KMFA_ATTENDANCE_PRODUCTION_RELEASE_ROOT"] = str(release_root)
    os.environ["KMFA_ATTENDANCE_PRODUCTION_PROMPT_SHA256"] = prompt["prompt_sha256"]
    os.environ["KMFA_ATTENDANCE_DIAGNOSTIC_REPO_ROOT"] = str(repo)
    os.environ["KMFA_ATTENDANCE_LOCAL_KMFA_ROOT"] = str(repo / "KMFA")
    forwarded = [
        "--run-slot",
        args.run_slot,
        "--trigger-source",
        args.trigger_source,
        "--automation-id",
        args.automation_id,
    ]
    if args.resume_final_only:
        forwarded.append("--resume-final-only")
    if args.allow_dws_commands:
        forwarded.append("--allow-dws-commands")
    from KMFA.tools.dingtalk_attendance.automatic_closure import main as closure_main

    return closure_main(forwarded)


if __name__ == "__main__":
    raise SystemExit(main())
