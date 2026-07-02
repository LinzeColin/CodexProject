#!/usr/bin/env python3
"""Verify the ADP final-command prerequisite state from the repository root.

The S2PMT07 final-command contract requires this root entrypoint.  It is
fail-closed for P0/P1 zero proof and S2PLT04 completion, but it must not require
``FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json`` before the final
command has actually been executed.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


DAILY_OPERATION_GATE_REF = "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization_gate.json"
DAILY_OPERATION_AUTHORIZATION_REF = (
    "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json"
)


def _load_json_artifact(root: Path, relative_path: str) -> dict[str, Any]:
    path = root / relative_path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        payload = {}
    return payload if isinstance(payload, dict) else {}


def _load_cli_report(root: Path) -> tuple[int, dict[str, Any], str]:
    project_root = root / "arxiv-daily-push"
    env = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": str(project_root / "src"),
    }
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "arxiv_daily_push.cli",
            "validate-final-acceptance-bundle",
            "--repo-root",
            ".",
            "--json",
        ],
        cwd=root,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload = {}
    stderr_tail = "\n".join(completed.stderr.strip().splitlines()[-20:])
    return completed.returncode, payload, stderr_tail


def _integrated_acceptance_state(root: Path) -> dict[str, bool]:
    payload = _load_json_artifact(root, "FINAL_ACCEPTANCE_BUNDLE/integrated_production_acceptance.json")
    accepted = (
        payload.get("status")
        == "pass_integrated_production_accepted_evidence_written_no_runtime_enablement"
        and payload.get("production_acceptance_claimed") is True
        and payload.get("integrated_production_accepted") is True
        and payload.get("stage2_integrated_production_accepted") is True
    )
    runtime_enabled = any(
        payload.get(flag) is True
        for flag in (
            "daily_operation_enabled",
            "real_smtp_send_enabled",
            "scheduler_install_enabled",
            "release_packaging_enabled",
            "production_restore_enabled",
        )
    )
    return {
        "production_acceptance_claimed": accepted,
        "integrated_production_accepted": accepted,
        "stage2_integrated_production_accepted": accepted,
        "daily_operation_enabled": payload.get("daily_operation_enabled") is True,
        "runtime_enabled": runtime_enabled,
    }


def _daily_operation_authorization_state(root: Path) -> dict[str, Any]:
    payload = _load_json_artifact(root, DAILY_OPERATION_GATE_REF)
    if not payload:
        return {
            "daily_operation_authorization_ready": False,
            "daily_operation_gate_status": "missing",
            "daily_operation_blocking_reasons": [
                "daily_operation_persistent_enablement_authorization_gate_missing"
            ],
            "daily_operation_next_required_step": "RUN_DAILY_OPERATION_PERSISTENT_ENABLEMENT_AUTHORIZATION_GATE",
            "daily_operation_next_executable_task": "S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION",
            "daily_operation_persistent_authorization_artifact": DAILY_OPERATION_AUTHORIZATION_REF,
            "daily_operation_gate_artifact": DAILY_OPERATION_GATE_REF,
        }

    blocking_reasons = list(payload.get("blocking_reasons", []))
    ready = (
        payload.get("persistent_daily_operation_authorized") is True
        and payload.get("daily_operation_enablement_allowed_by_this_artifact") is True
        and not blocking_reasons
        and payload.get("real_smtp_send_enabled") is not True
        and payload.get("scheduler_install_enabled") is not True
        and payload.get("release_packaging_enabled") is not True
        and payload.get("production_restore_enabled") is not True
    )
    if not ready and not blocking_reasons:
        failed_checks = [
            str(check)
            for check in payload.get("failed_checks", [])
            if isinstance(check, str) and check
        ]
        blocking_reasons = failed_checks or ["daily_operation_authorization_not_ready"]

    return {
        "daily_operation_authorization_ready": ready,
        "daily_operation_gate_status": payload.get("status"),
        "daily_operation_blocking_reasons": blocking_reasons,
        "daily_operation_next_required_step": payload.get("next_required_step"),
        "daily_operation_next_executable_task": payload.get("next_executable_task"),
        "daily_operation_persistent_authorization_artifact": payload.get(
            "persistent_authorization_artifact_ref",
            DAILY_OPERATION_AUTHORIZATION_REF,
        ),
        "daily_operation_gate_artifact": payload.get("gate_artifact_ref", DAILY_OPERATION_GATE_REF),
    }


def build_verification_report(root: Path, required_zero: list[str]) -> dict[str, Any]:
    required_zero_set = {item.upper() for item in required_zero}
    unsupported = sorted(required_zero_set.difference({"P0", "P1"}))
    exit_code, payload, stderr_tail = _load_cli_report(root)
    zero_state = payload.get("p0_p1_zero_proof_artifact_validation", {})
    zero_checks = {
        "P0": zero_state.get("p0_zero_proven_by_payload") is True,
        "P1": zero_state.get("p1_zero_proven_by_payload") is True,
    }
    missing_zero = sorted(item for item in required_zero_set if not zero_checks.get(item, False))
    validation_errors = list(payload.get("readiness_validation_errors", []))
    blocking_reasons = list(payload.get("blocking_reasons", []))
    bundle_status = payload.get("status", "blocked")
    next_required_step = payload.get("next_required_step")
    next_executable_task = payload.get("next_executable_task")
    s2plt04_validation = payload.get("s2plt04_completion_report_validation", {})
    bundle_complete = (
        not unsupported
        and not missing_zero
        and exit_code == 0
        and bundle_status == "pass"
        and not validation_errors
    )
    final_command_prerequisite_ready = (
        not unsupported
        and not missing_zero
        and not validation_errors
        and bundle_status == "blocked"
        and next_required_step == "FINAL_COMMAND_EXECUTION"
        and next_executable_task == "FINAL_COMMAND_EXECUTION"
        and s2plt04_validation.get("status") == "pass"
        and s2plt04_validation.get("s2plt04_completed_by_report") is True
    )
    acceptance = _integrated_acceptance_state(root)
    daily_operation = _daily_operation_authorization_state(root)
    passed = (bundle_complete or final_command_prerequisite_ready) and not acceptance["runtime_enabled"]
    return {
        "status": "PASS" if passed else "FAIL",
        "scope": "adp_final_command_prerequisite_root_verification_no_production_side_effects",
        "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
        "task_id": "S2PMT07",
        "required_zero": sorted(required_zero_set),
        "unsupported_required_zero": unsupported,
        "zero_checks": zero_checks,
        "missing_required_zero": missing_zero,
        "bundle_validator_exit_code": exit_code,
        "bundle_status": bundle_status,
        "bundle_complete": bundle_complete,
        "final_command_prerequisite_ready": final_command_prerequisite_ready,
        "next_required_step": next_required_step,
        "next_executable_task": next_executable_task,
        "s2plt04_completion_report_status": s2plt04_validation.get("status"),
        "blocking_reasons": blocking_reasons,
        **daily_operation,
        "readiness_validation_errors": validation_errors,
        "missing_items": list(payload.get("missing_items", [])),
        "stderr_tail": stderr_tail,
        "production_acceptance_claimed": acceptance["production_acceptance_claimed"],
        "integrated_production_accepted": acceptance["integrated_production_accepted"],
        "stage2_integrated_production_accepted": acceptance["stage2_integrated_production_accepted"],
        "daily_operation_enabled": acceptance["daily_operation_enabled"],
        "runtime_enablement_detected": acceptance["runtime_enabled"],
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="CodexProject repository root.")
    parser.add_argument(
        "--require-zero",
        nargs="+",
        default=[],
        help="Required zero severities. Supported values: P0 P1.",
    )
    args = parser.parse_args(argv)
    report = build_verification_report(Path(args.root).resolve(), args.require_zero)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
