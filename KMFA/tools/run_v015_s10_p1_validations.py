#!/usr/bin/env python3
"""Run and receipt one exact validation set for KMFA v1.5 S10-P1."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s10_p1_general_import as builder
from KMFA.tools import check_v015_s10_p1_general_import as checker


REPO_ROOT = Path(__file__).resolve().parents[2]


class ValidationError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        raise ValidationError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _require_clean_subject() -> None:
    for args in (("diff", "--quiet"), ("diff", "--cached", "--quiet")):
        if subprocess.run(["git", *args], cwd=REPO_ROOT, check=False).returncode:
            raise ValidationError("validation requires a clean tracked S10-P1 implementation commit")
    untracked = [
        line
        for line in _git("-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard").splitlines()
        if line and not checker._preserved(line)
    ]
    if untracked:
        raise ValidationError("unexpected untracked file before validation: " + ", ".join(untracked))


def run() -> list[dict[str, Any]]:
    _require_clean_subject()
    subject = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
    if (
        subject.get("phase_acceptance_status") != "PENDING_FINAL_VALIDATION"
        or subject.get("phase_task_accepted_count") != 0
        or subject.get("s10_p2_entry_allowed") is not False
        or subject.get("s10_p2_started") is not False
        or subject.get("github_upload_performed") is not False
        or subject.get("app_reinstall_performed") is not False
    ):
        raise ValidationError("validation subject must be pending S10-P1 with later and release work closed")

    validation_head = _git("rev-parse", "HEAD")
    validation_run_id = uuid.uuid4().hex
    receipts: list[dict[str, Any]] = []
    for name, command in checker.EXPECTED_VALIDATIONS:
        started_at = _now()
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            shell=True,
            executable="/bin/zsh",
            capture_output=True,
            text=True,
            check=False,
        )
        combined = result.stdout + result.stderr
        receipt = {
            "schema_version": "kmfa.v015.s10p1.validation_receipt.v1",
            "validation_run_id": validation_run_id,
            "validation_head": validation_head,
            "name": name,
            "command": command,
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "exit_code": result.returncode,
            "output_sha256": "sha256:" + hashlib.sha256(combined.encode()).hexdigest(),
            "started_at": started_at,
            "ended_at": _now(),
        }
        receipts.append(receipt)
        print(f"{receipt['status']}: {name}")
        if result.returncode:
            raise ValidationError(f"{name} failed\n{combined[-6000:]}")

    builder.VALIDATION_RESULTS_PATH.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in receipts),
        encoding="utf-8",
    )
    builder.write_outputs()
    return receipts


def main() -> int:
    try:
        rows = run()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, ValidationError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(
        "PASS: S10-P1 validation receipts "
        f"run={rows[0]['validation_run_id']} count={len(rows)} head={rows[0]['validation_head']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
