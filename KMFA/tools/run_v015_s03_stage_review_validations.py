#!/usr/bin/env python3
"""Run and bind every KMFA v1.5 S03 Stage-review validation command."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from KMFA.tools import build_v015_s03_stage_review as builder


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = builder.PROJECT_ROOT / builder.OUTPUT_ROOT_RELATIVE / builder.VALIDATION_RESULTS_RELATIVE
_ENV_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


class RunnerError(RuntimeError):
    """Raised when a command, HEAD, subject or output boundary drifts."""


def _digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _git(args: Sequence[str]) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RunnerError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _parse(command: str) -> tuple[dict[str, str], list[str]]:
    tokens = shlex.split(command, posix=True)
    environment: dict[str, str] = {}
    index = 0
    while index < len(tokens) and "=" in tokens[index]:
        name, value = tokens[index].split("=", 1)
        if _ENV_RE.fullmatch(name) is None:
            break
        environment[name] = value
        index += 1
    argv = tokens[index:]
    if not argv:
        raise RunnerError("validation command has no executable")
    return environment, argv


def _execute(command: str) -> subprocess.CompletedProcess[bytes]:
    overrides, argv = _parse(command)
    environment = os.environ.copy()
    environment.update(overrides)
    return subprocess.run(argv, cwd=REPO_ROOT, env=environment, capture_output=True, check=False)


def build_receipts(commands: Mapping[str, str]) -> tuple[list[dict[str, Any]], bool]:
    if _git(["status", "--porcelain"]):
        raise RunnerError("validation runner requires a clean implementation commit")
    head = _git(["rev-parse", "HEAD"])
    if re.fullmatch(r"[0-9a-f]{40}", head) is None:
        raise RunnerError("validation HEAD is invalid")
    subject = builder.validation_subject_sha256(head)
    run_id = uuid.uuid4().hex
    rows: list[dict[str, Any]] = []
    all_pass = True
    for sequence, (validation_id, command) in enumerate(commands.items(), 1):
        head_before = _git(["rev-parse", "HEAD"])
        subject_before = builder.validation_subject_sha256(head_before)
        started = datetime.now().astimezone()
        start_ns = time.monotonic_ns()
        try:
            completed = _execute(command)
            exit_code = int(completed.returncode)
            stdout = bytes(completed.stdout or b"")
            stderr = bytes(completed.stderr or b"")
        except (OSError, ValueError, RunnerError) as error:
            exit_code = 127
            stdout = b""
            stderr = str(error).encode(errors="replace")
        ended = datetime.now().astimezone()
        duration_ms = max(0, (time.monotonic_ns() - start_ns) // 1_000_000)
        head_after = _git(["rev-parse", "HEAD"])
        subject_after = builder.validation_subject_sha256(head_after)
        clean = not _git(["status", "--porcelain"])
        passed = exit_code == 0 and clean and head_before == head_after == head and subject_before == subject_after == subject
        row = {
            "schema_version": "kmfa.v015.s03_stage_review.validation_receipt.v1",
            "run_id": run_id,
            "validation_id": validation_id,
            "command": command,
            "result": "PASS" if passed else "FAIL",
            "exit_code": exit_code if exit_code else (0 if passed else 98),
            "execution_sequence": sequence,
            "review_base_commit": builder.REVIEW_BASE_COMMIT,
            "head_before": head_before,
            "head_after": head_after,
            "validation_subject_sha256": subject,
            "started_at": started.isoformat(),
            "ended_at": ended.isoformat(),
            "duration_ms": duration_ms,
            "stdout_sha256": _digest(stdout),
            "stderr_sha256": _digest(stderr),
        }
        rows.append(row)
        print(f"{validation_id}: {'PASS' if passed else 'FAIL'} ({duration_ms} ms)", flush=True)
        if not passed:
            sys.stderr.write(stdout.decode(errors="replace")[-4000:])
            sys.stderr.write(stderr.decode(errors="replace")[-4000:])
            all_pass = False
            break
    return rows, all_pass and len(rows) == len(commands)


def _write(rows: Sequence[Mapping[str, Any]]) -> None:
    fixed = OUTPUT_PATH.resolve()
    if fixed.parent != (builder.PROJECT_ROOT / builder.OUTPUT_ROOT_RELATIVE / "machine").resolve():
        raise RunnerError("validation output path drift")
    fixed.parent.mkdir(parents=True, exist_ok=True)
    temporary = fixed.with_name(f".{fixed.name}.{os.getpid()}.{time.monotonic_ns()}.tmp")
    payload = b"".join((json.dumps(dict(row), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode() for row in rows)
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, fixed)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def main(argv: Sequence[str] | None = None) -> int:
    if list(sys.argv[1:] if argv is None else argv):
        print("FAIL: S03 Stage-review validation runner accepts no arguments", file=sys.stderr)
        return 2
    try:
        rows, passed = build_receipts(builder.EXPECTED_VALIDATIONS)
        if not passed:
            raise RunnerError("validation stopped after first failure; public pending receipts were preserved")
        _write(rows)
    except (builder.BuildError, RunnerError, OSError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: wrote {len(rows)}/{len(builder.EXPECTED_VALIDATIONS)} exact S03 Stage-review receipts to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
