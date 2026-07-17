#!/usr/bin/env python3
"""Execute and privately bind every KMFA v1.5 S03-P3 validation receipt."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import stat
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from KMFA.tools import build_v015_s03_p3_public_repository_safety as builder


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
OUTPUT_PATH = PROJECT_ROOT / builder.PRIVATE_VALIDATION_RECEIPTS_RELATIVE
_ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class RunnerError(RuntimeError):
    """A command, subject, HEAD, or private receipt boundary failed."""


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def parse_command(command: str) -> tuple[dict[str, str], list[str]]:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as error:
        raise RunnerError("validation command quoting is invalid") from error
    environment: dict[str, str] = {}
    index = 0
    while index < len(tokens) and "=" in tokens[index]:
        name, value = tokens[index].split("=", 1)
        if _ENV_NAME_RE.fullmatch(name) is None:
            break
        environment[name] = value
        index += 1
    argv = tokens[index:]
    if not argv:
        raise RunnerError("validation command has no executable")
    return environment, argv


def _execute(command: str) -> subprocess.CompletedProcess[bytes]:
    overrides, argv = parse_command(command)
    environment = os.environ.copy()
    environment.update(overrides)
    return subprocess.run(argv, cwd=REPO_ROOT, env=environment, capture_output=True, check=False)


def _git_head() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    value = result.stdout.strip()
    if result.returncode != 0 or re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise RunnerError("unable to resolve validation HEAD")
    return value


def build_receipts(
    commands: Mapping[str, str],
    *,
    executor: Callable[[str], subprocess.CompletedProcess[bytes]] = _execute,
    subject_resolver: Callable[[], str],
    head_resolver: Callable[[], str] = _git_head,
    clock: Callable[[], datetime] = lambda: datetime.now().astimezone(),
    monotonic_ns: Callable[[], int] = time.monotonic_ns,
    run_id: str | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    subject = subject_resolver()
    if re.fullmatch(r"sha256:[0-9a-f]{64}", subject) is None:
        raise RunnerError("validation subject digest is invalid")
    receipt_run_id = run_id or uuid.uuid4().hex
    if re.fullmatch(r"[0-9a-f]{32}", receipt_run_id) is None:
        raise RunnerError("validation run ID is invalid")
    rows: list[dict[str, Any]] = []
    all_pass = True
    stop_reason: str | None = None
    for sequence, (validation_id, command) in enumerate(commands.items(), start=1):
        if stop_reason is not None:
            rows.append(
                {
                    "schema_version": builder.VALIDATION_RECEIPT_SCHEMA_VERSION,
                    "run_id": receipt_run_id,
                    "validation_id": validation_id,
                    "command": command,
                    "result": "PENDING",
                    "exit_code": None,
                    "execution_sequence": sequence,
                    "phase_base_commit": builder.PHASE_BASE_COMMIT,
                    "skip_reason": stop_reason,
                }
            )
            continue
        head_before = head_resolver()
        subject_before = subject_resolver()
        started = clock()
        start_ns = monotonic_ns()
        try:
            completed = executor(command)
            exit_code = int(completed.returncode)
            stdout = bytes(completed.stdout or b"")
            stderr = bytes(completed.stderr or b"")
        except (OSError, RunnerError, ValueError) as error:
            exit_code = 127
            stdout = b""
            stderr = str(error).encode(errors="replace")
        duration_ms = max(0, (monotonic_ns() - start_ns) // 1_000_000)
        ended = clock()
        head_after = head_resolver()
        subject_after = subject_resolver()
        integrity = head_before == head_after and subject_before == subject_after == subject
        passed = exit_code == 0 and integrity
        effective_exit = exit_code if exit_code else (0 if integrity else 98)
        rows.append(
            {
                "schema_version": builder.VALIDATION_RECEIPT_SCHEMA_VERSION,
                "run_id": receipt_run_id,
                "validation_id": validation_id,
                "command": command,
                "result": "PASS" if passed else "FAIL",
                "exit_code": effective_exit,
                "execution_sequence": sequence,
                "started_at": started.isoformat(),
                "ended_at": ended.isoformat(),
                "duration_ms": duration_ms,
                "phase_base_commit": builder.PHASE_BASE_COMMIT,
                "head_before": head_before,
                "head_after": head_after,
                "validation_subject_sha256": subject,
                "stdout_sha256": _sha256(stdout),
                "stderr_sha256": _sha256(stderr),
            }
        )
        all_pass = all_pass and passed
        if not passed:
            stop_reason = f"STOP_AFTER_{validation_id}"
    return rows, all_pass


def _open_directory_no_follow(path: Path) -> int:
    absolute = Path(os.path.abspath(os.path.normpath(os.fspath(path))))
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open("/", flags)
    try:
        for component in absolute.parts[1:]:
            next_descriptor = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def write_private_receipts(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    target = Path(os.path.abspath(os.path.normpath(os.fspath(path))))
    fixed = Path(os.path.abspath(os.path.normpath(os.fspath(OUTPUT_PATH))))
    if target != fixed:
        raise RunnerError("private validation receipt path is not fixed")
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    parent_fd = _open_directory_no_follow(target.parent)
    temporary = f".{target.name}.{os.getpid()}.{time.monotonic_ns()}.tmp"
    created = False
    try:
        try:
            existing = os.stat(target.name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            existing = None
        if existing is not None and (not stat.S_ISREG(existing.st_mode) or existing.st_nlink != 1):
            raise RunnerError("existing private validation receipt is unsafe")
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=parent_fd,
        )
        created = True
        try:
            os.fchmod(descriptor, 0o600)
            payload = b"".join(
                (json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n").encode()
                for row in rows
            )
            offset = 0
            while offset < len(payload):
                offset += os.write(descriptor, payload[offset:])
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(temporary, target.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        created = False
        final = os.stat(target.name, dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISREG(final.st_mode) or final.st_nlink != 1 or stat.S_IMODE(final.st_mode) != 0o600:
            raise RunnerError("private validation receipt mode/type drift")
        os.fsync(parent_fd)
    finally:
        if created:
            try:
                os.unlink(temporary, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
        os.close(parent_fd)


def main(argv: Sequence[str] | None = None) -> int:
    if list(sys.argv[1:] if argv is None else argv):
        print("FAIL: S03-P3 validation runner accepts no arguments", file=sys.stderr)
        return 2
    try:
        run_id = uuid.uuid4().hex
        pending = [
            {
                "schema_version": builder.VALIDATION_RECEIPT_SCHEMA_VERSION,
                "run_id": run_id,
                "validation_id": validation_id,
                "command": command,
                "result": "PENDING",
                "exit_code": None,
                "execution_sequence": sequence,
                "phase_base_commit": builder.PHASE_BASE_COMMIT,
                "skip_reason": "RUN_STARTED_NOT_FINALIZED",
            }
            for sequence, (validation_id, command) in enumerate(builder.EXPECTED_VALIDATION_RECEIPTS.items(), start=1)
        ]
        write_private_receipts(OUTPUT_PATH, pending)
        rows, passed = build_receipts(
            builder.EXPECTED_VALIDATION_RECEIPTS,
            subject_resolver=builder.validation_subject_sha256,
            run_id=run_id,
        )
        write_private_receipts(OUTPUT_PATH, rows)
        count = sum(row["result"] == "PASS" for row in rows)
        print(f"{'PASS' if passed else 'FAIL'}: S03-P3 validations {count}/{len(rows)}")
        return 0 if passed else 1
    except (RunnerError, builder.BuildError, OSError, ValueError) as error:
        print(f"FAIL: S03-P3 validation runner integrity error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
