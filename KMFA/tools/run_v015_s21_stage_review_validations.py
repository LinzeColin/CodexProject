#!/usr/bin/env python3
"""运行一次且只运行一组 S21 整体复审正式验收。"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s21_stage_review as builder
from KMFA.tools import check_v015_s21_stage_review as checker
from KMFA.tools import v015_roadmap_governance_sync as roadmap_sync


REPO_ROOT = builder.REPO_ROOT


class ValidationError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise ValidationError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _write_receipts(receipts: list[dict[str, Any]]) -> None:
    builder.VALIDATION_RESULTS_PATH.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in receipts
        ),
        encoding="utf-8",
    )


def run() -> list[dict[str, Any]]:
    if _git("status", "--porcelain", "--untracked-files=no"):
        raise ValidationError("validation requires a clean tracked implementation commit")
    subject = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
    if (
        subject.get("stage_acceptance_status") != "PENDING"
        or subject.get("decision") != "REMAIN_IN_S21_STAGE_REVIEW_FINAL_VALIDATION"
        or subject.get("s22_entry_allowed") is not False
        or subject.get("s22_p1_entry_allowed") is not False
        or subject.get("s22_p1_started") is not False
        or subject.get("github_upload_performed") is not False
        or subject.get("app_reinstall_performed") is not False
    ):
        raise ValidationError(
            "validation subject must be pending S21 review with S22 and release actions closed"
        )

    validation_head = _git("rev-parse", "HEAD")
    validation_run_id = uuid.uuid4().hex
    validation_environment = dict(os.environ)
    validation_environment.update(
        {
            "KMFA_PRESERVE_TRACKED_SCREENSHOTS": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": ".",
            "PATH": f"{Path(sys.executable).parent}:{os.environ.get('PATH', '')}",
        }
    )
    receipts: list[dict[str, Any]] = []
    for name, command in checker.EXPECTED_VALIDATIONS:
        started_at = _now()
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            shell=True,
            executable="/bin/zsh",
            env=validation_environment,
            capture_output=True,
            text=True,
            check=False,
        )
        combined = result.stdout + result.stderr
        receipt = {
            "schema_version": "kmfa.v015.s21_stage_review.validation_receipt.v1",
            "validation_run_id": validation_run_id,
            "validation_head": validation_head,
            "name": name,
            "command": command,
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "exit_code": result.returncode,
            "output_sha256": "sha256:"
            + hashlib.sha256(combined.encode("utf-8")).hexdigest(),
            "started_at": started_at,
            "ended_at": _now(),
        }
        receipts.append(receipt)
        print(f"{receipt['status']}: {name}", flush=True)
        if result.returncode:
            raise ValidationError(f"{name} failed\n{combined[-6000:]}")

    passed_outputs = builder.expected_outputs(
        "PASSED", validation_run_id, validation_head
    )
    try:
        _write_receipts(receipts)
        builder.write_outputs(passed_outputs)
        roadmap_sync.run(
            check=False, validation_state="S21_STAGE_REVIEW_PASSED"
        )
        builder.check_outputs(passed_outputs)
        roadmap_sync.run(check=True, validation_state="S21_STAGE_REVIEW_PASSED")
    except Exception as error:
        builder.VALIDATION_RESULTS_PATH.unlink(missing_ok=True)
        builder.write_outputs(builder.expected_outputs("PENDING", None, None))
        roadmap_sync.run(
            check=False,
            validation_state="S21_STAGE_REVIEW_PENDING_FINAL_VALIDATION",
        )
        raise ValidationError(f"final acceptance materialization failed: {error}") from error
    return receipts


def main() -> int:
    try:
        receipts = run()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, ValidationError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(
        "PASS: S21 整体复审验收回执 "
        f"run={receipts[0]['validation_run_id']} count={len(receipts)} "
        f"head={receipts[0]['validation_head']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
