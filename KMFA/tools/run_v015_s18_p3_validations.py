#!/usr/bin/env python3
"""执行并记录 KMFA v1.5 S18-P3 唯一一组正式验收。"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s18_p3_relation_reporting as builder
from KMFA.tools import check_v015_s18_p3_relation_reporting as checker


REPO_ROOT = builder.REPO_ROOT
BUNDLED_PYTHON = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"


class ValidationError(RuntimeError):
    """S18-P3 正式验收无法继续。"""


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        raise ValidationError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _require_bundled_runtime() -> None:
    if not BUNDLED_PYTHON.is_file() or not Path(sys.executable).samefile(BUNDLED_PYTHON):
        raise ValidationError(f"run formal validation with bundled Python: {BUNDLED_PYTHON}")


def _require_clean_subject() -> None:
    for args in (("diff", "--quiet"), ("diff", "--cached", "--quiet")):
        if subprocess.run(["git", *args], cwd=REPO_ROOT, check=False).returncode:
            raise ValidationError("validation requires a clean tracked S18-P3 implementation commit")
    untracked = [
        line
        for line in _git("-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard").splitlines()
        if line and not checker._preserved(line)
    ]
    if untracked:
        raise ValidationError("unexpected untracked file before validation: " + ", ".join(untracked))


def run() -> list[dict[str, Any]]:
    _require_bundled_runtime()
    _require_clean_subject()
    subject = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
    if (
        subject.get("phase_acceptance_status") != "PENDING_FINAL_VALIDATION"
        or subject.get("phase_task_accepted_count") != 0
        or subject.get("s18_p2_acceptance_status") != "PASSED"
        or subject.get("s18_p3_started") is not True
        or subject.get("s18_p3_completed") is not False
        or subject.get("s18_stage_review_entry_allowed") is not False
        or subject.get("s18_stage_review_started") is not False
        or any(subject.get(key) != 0 for key in (
            "raw_root_access_count", "live_source_read_count", "external_network_request_count", "real_identity_count", "credential_count",
            "real_business_action_count", "source_data_write_count", "fact_layer_write_count", "full_sensitive_detail_count",
            "exposed_sensitive_field_count", "notification_send_count", "external_message_count", "payment_execution_count", "bank_operation_count",
        ))
        or subject.get("github_upload_performed") is not False
        or subject.get("app_reinstall_performed") is not False
        or subject.get("formal_business_report") is not False
    ):
        raise ValidationError("validation subject must be pending S18-P3 with review and release work closed")

    validation_head = _git("rev-parse", "HEAD")
    validation_run_id = uuid.uuid4().hex
    receipts: list[dict[str, Any]] = []
    for name, command in checker.EXPECTED_VALIDATIONS:
        started_at = _now()
        result = subprocess.run(command, cwd=REPO_ROOT, shell=True, executable="/bin/zsh", capture_output=True, text=True, check=False)
        combined = result.stdout + result.stderr
        receipt = {
            "schema_version": "kmfa.v015.s18p3.validation_receipt.v1",
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

    temporary = builder.VALIDATION_RESULTS_PATH.with_suffix(".jsonl.tmp")
    temporary.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in receipts), encoding="utf-8")
    temporary.replace(builder.VALIDATION_RESULTS_PATH)
    output = builder.build()
    if output.get("phase_acceptance_status") != "PASSED":
        raise ValidationError("final evidence did not bind the validation receipts")
    return receipts


def main() -> int:
    try:
        rows = run()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, builder.BuildError, ValidationError) as error:
        print(f"FAIL: {error}")
        return 1
    print(f"PASS: S18-P3 validation receipts run={rows[0]['validation_run_id']} count={len(rows)} head={rows[0]['validation_head']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
