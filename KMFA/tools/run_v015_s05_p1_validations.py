#!/usr/bin/env python3
"""Run one exact validation receipt set for KMFA v1.5 S05-P1."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s05_p1_amount_precision as builder
from KMFA.tools import check_v015_s05_p1_amount_precision as checker


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


def run() -> list[dict[str, Any]]:
    if _git("status", "--porcelain"):
        raise ValidationError("validation requires a clean implementation commit")
    manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("phase_acceptance_status") != "PENDING_FINAL_VALIDATION":
        raise ValidationError("validation subject must be the pending S05-P1 implementation state")
    validation_head = _git("rev-parse", "HEAD")
    validation_run_id = uuid.uuid4().hex
    receipts: list[dict[str, Any]] = []
    for name, command in checker.EXPECTED_VALIDATIONS:
        started_at = _now()
        result = subprocess.run(command, cwd=REPO_ROOT, shell=True, executable="/bin/zsh", capture_output=True, text=True, check=False)
        ended_at = _now()
        combined = result.stdout + result.stderr
        receipt = {
            "schema_version": "kmfa.v015.s05p1.validation_receipt.v1",
            "validation_run_id": validation_run_id,
            "validation_head": validation_head,
            "name": name,
            "command": command,
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "exit_code": result.returncode,
            "output_sha256": "sha256:" + hashlib.sha256(combined.encode("utf-8")).hexdigest(),
            "started_at": started_at,
            "ended_at": ended_at,
        }
        receipts.append(receipt)
        print(f"{receipt['status']}: {name}")
        if result.returncode:
            raise ValidationError(f"{name} failed\n{combined[-4000:]}")
    builder.write_outputs(final_validation=True, receipts=receipts)
    return receipts


def main() -> int:
    try:
        receipts = run()
    except (OSError, ValueError, json.JSONDecodeError, ValidationError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(
        "PASS: S05-P1 validation receipts "
        f"run={receipts[0]['validation_run_id']} count={len(receipts)} "
        f"head={receipts[0]['validation_head']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
