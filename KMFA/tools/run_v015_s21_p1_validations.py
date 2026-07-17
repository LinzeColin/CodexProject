#!/usr/bin/env python3
"""Run and bind the single formal KMFA v1.5 S21-P1 validation set."""

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

from KMFA.tools import build_v015_s21_p1_report_model as builder
from KMFA.tools import check_v015_s21_p1_report_model as checker


REPO_ROOT = builder.REPO_ROOT
BUNDLED_PYTHON = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"


class ValidationError(RuntimeError):
    """Formal S21-P1 validation cannot continue."""


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        raise ValidationError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _require_clean_subject() -> None:
    if not BUNDLED_PYTHON.is_file() or not Path(sys.executable).samefile(BUNDLED_PYTHON):
        raise ValidationError(f"run formal validation with bundled Python: {BUNDLED_PYTHON}")
    for args in (("diff", "--quiet"), ("diff", "--cached", "--quiet")):
        if subprocess.run(["git", *args], cwd=REPO_ROOT, check=False).returncode:
            raise ValidationError("validation requires a clean tracked S21-P1 implementation commit")
    untracked = [line for line in _git("-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard").splitlines() if line and not checker._preserved(line)]
    if untracked:
        raise ValidationError("unexpected untracked file before validation: " + ", ".join(untracked))


def run() -> list[dict[str, Any]]:
    _require_clean_subject()
    subject = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
    zero_keys = (
        "history_overwrite_count", "data_check_board_backend_content_count", "technical_log_content_count",
        "technical_grade_abbreviation_count", "raw_root_access_count", "raw_write_count",
        "external_network_request_count", "html_report_generation_count", "pdf_report_generation_count",
        "spreadsheet_report_generation_count", "approval_or_publication_count", "s21_p2_execution_count", "s21_p3_execution_count",
    )
    if (
        subject.get("phase_acceptance_status") != "PENDING_FINAL_VALIDATION"
        or subject.get("phase_task_accepted_count") != 0
        or subject.get("s20_stage_review_acceptance_status") != "PASSED"
        or subject.get("s21_p1_started") is not True or subject.get("s21_p1_completed") is not False
        or subject.get("s21_p2_entry_allowed") is not False or subject.get("s21_p2_started") is not False
        or any(subject.get(key) != 0 for key in zero_keys)
        or subject.get("github_upload_performed") is not False
        or subject.get("app_reinstall_performed") is not False
        or subject.get("formal_business_report") is not False
    ):
        raise ValidationError("validation subject must be pending S21-P1 with downstream and release work closed")
    validation_head = _git("rev-parse", "HEAD")
    validation_run_id = uuid.uuid4().hex
    receipts: list[dict[str, Any]] = []
    environment = dict(os.environ)
    environment["PATH"] = f"{BUNDLED_PYTHON.parent}:{environment.get('PATH', '')}"
    for name, command in checker.EXPECTED_VALIDATIONS:
        started_at = _now()
        result = subprocess.run(command, cwd=REPO_ROOT, shell=True, executable="/bin/zsh", env=environment, capture_output=True, text=True, check=False)
        combined = result.stdout + result.stderr
        receipt = {
            "schema_version": "kmfa.v015.s21p1.validation_receipt.v1", "validation_run_id": validation_run_id,
            "validation_head": validation_head, "name": name, "command": command,
            "status": "PASS" if result.returncode == 0 else "FAIL", "exit_code": result.returncode,
            "output_sha256": "sha256:" + hashlib.sha256(combined.encode()).hexdigest(),
            "started_at": started_at, "ended_at": _now(),
        }
        receipts.append(receipt)
        print(f"{receipt['status']}: {name}", flush=True)
        if result.returncode:
            raise ValidationError(f"{name} failed\n{combined[-6000:]}")
    temporary = builder.VALIDATION_RESULTS_PATH.with_suffix(".jsonl.tmp")
    temporary.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in receipts), encoding="utf-8")
    temporary.replace(builder.VALIDATION_RESULTS_PATH)
    if builder.build().get("phase_acceptance_status") != "PASSED":
        raise ValidationError("final evidence did not bind validation receipts")
    return receipts


def main() -> int:
    try:
        rows = run()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, builder.BuildError, ValidationError) as error:
        print(f"FAIL: {error}"); return 1
    print(f"PASS: S21-P1 validation receipts run={rows[0]['validation_run_id']} count={len(rows)} head={rows[0]['validation_head']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
