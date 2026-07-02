#!/usr/bin/env python3
"""Fail-closed root verifier for ADP S3 DAILY_OPERATION readiness.

This tool is intentionally stricter than ``verify_acceptance_bundle.py``:
the final bundle can be complete while S3 DAILY_OPERATION remains blocked.
It never writes authorization artifacts and never enables runtime.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AUTHORIZATION_ARTIFACT_REF = "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json"
GATE_ARTIFACT_REF = "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization_gate.json"
REQUIRED_CWD = "CodexProject repository root"
ROOT_VALIDATION_FAILURE = "codexproject_repo_root_invalid"
REQUIRED_ROOT_PATHS = (
    "arxiv-daily-push/src",
    "arxiv-daily-push/docs/pursuing_goal/CURRENT.yaml",
    GATE_ARTIFACT_REF,
)


def _validate_repo_root(root: Path) -> tuple[bool, list[str], list[str]]:
    missing_paths = [path for path in REQUIRED_ROOT_PATHS if not (root / path).exists()]
    errors = [ROOT_VALIDATION_FAILURE] if missing_paths else []
    return not errors, missing_paths, errors


def _build_invalid_root_report(root: Path, generated: str, missing_paths: list[str], errors: list[str]) -> dict[str, Any]:
    authorization_artifact = root / AUTHORIZATION_ARTIFACT_REF
    return {
        "status": "FAIL",
        "scope": "adp_s3_daily_operation_readiness_fail_closed_no_runtime_enablement",
        "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
        "task_id": "S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION",
        "generated_at": generated,
        "repo_root": str(root),
        "required_cwd": REQUIRED_CWD,
        "repo_root_valid": False,
        "root_validation_errors": errors,
        "required_paths_missing": missing_paths,
        "daily_operation_ready": False,
        "gate_status": None,
        "blocking_reasons": errors,
        "validation_errors": errors,
        "next_required_step": "RUN_FROM_CODEXPROJECT_REPOSITORY_ROOT",
        "next_executable_task": None,
        "authorization_artifact": AUTHORIZATION_ARTIFACT_REF,
        "authorization_artifact_exists": authorization_artifact.is_file(),
        "gate_artifact": GATE_ARTIFACT_REF,
        "persistent_daily_operation_authorized": False,
        "daily_operation_enablement_allowed_by_this_artifact": False,
        "runtime_enablement_detected": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
    }


def _load_stage2_gate(root: Path):
    src = root / "arxiv-daily-push" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from arxiv_daily_push.stage2_final_gate import (  # noqa: PLC0415
        build_daily_operation_persistent_enablement_authorization_state,
        validate_daily_operation_persistent_enablement_authorization_state,
    )

    return (
        build_daily_operation_persistent_enablement_authorization_state,
        validate_daily_operation_persistent_enablement_authorization_state,
    )


def build_readiness_report(root: Path, generated_at: str | None = None) -> dict[str, Any]:
    generated = generated_at or datetime.now(timezone.utc).isoformat()
    authorization_artifact = root / AUTHORIZATION_ARTIFACT_REF
    repo_root_valid, missing_paths, root_errors = _validate_repo_root(root)
    if not repo_root_valid:
        return _build_invalid_root_report(root, generated, missing_paths, root_errors)
    build_state, validate_state = _load_stage2_gate(root)
    gate = build_state(
        generated_at=generated,
        repo_root=root,
        persistent_authorization_artifact_ref=AUTHORIZATION_ARTIFACT_REF,
    )
    validation_errors = validate_state(gate)
    runtime_flags = {
        "daily_operation_enabled": gate.get("daily_operation_enabled") is True,
        "real_smtp_send_enabled": gate.get("real_smtp_send_enabled") is True,
        "scheduler_install_enabled": gate.get("scheduler_install_enabled") is True,
        "release_packaging_enabled": gate.get("release_packaging_enabled") is True,
        "production_restore_enabled": gate.get("production_restore_enabled") is True,
    }
    runtime_enablement_detected = any(runtime_flags.values())
    daily_operation_ready = (
        not validation_errors
        and gate.get("status") == "pass_persistent_daily_operation_authorization_recorded_no_runtime_enablement"
        and gate.get("persistent_daily_operation_authorized") is True
        and gate.get("daily_operation_enablement_allowed_by_this_artifact") is True
        and not runtime_enablement_detected
    )
    blocking_reasons = list(gate.get("blocking_reasons") or [])
    if not daily_operation_ready and not blocking_reasons:
        blocking_reasons = validation_errors or ["daily_operation_readiness_not_satisfied"]

    return {
        "status": "PASS" if daily_operation_ready else "FAIL",
        "scope": "adp_s3_daily_operation_readiness_fail_closed_no_runtime_enablement",
        "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
        "task_id": "S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION",
        "generated_at": generated,
        "repo_root": str(root),
        "required_cwd": REQUIRED_CWD,
        "repo_root_valid": True,
        "root_validation_errors": [],
        "required_paths_missing": [],
        "daily_operation_ready": daily_operation_ready,
        "gate_status": gate.get("status"),
        "blocking_reasons": blocking_reasons,
        "validation_errors": validation_errors,
        "next_required_step": gate.get("next_required_step"),
        "next_executable_task": gate.get("next_executable_task"),
        "authorization_artifact": gate.get("persistent_authorization_artifact_ref", AUTHORIZATION_ARTIFACT_REF),
        "authorization_artifact_exists": authorization_artifact.is_file(),
        "gate_artifact": gate.get("gate_artifact_ref", GATE_ARTIFACT_REF),
        "persistent_daily_operation_authorized": gate.get("persistent_daily_operation_authorized") is True,
        "daily_operation_enablement_allowed_by_this_artifact": (
            gate.get("daily_operation_enablement_allowed_by_this_artifact") is True
        ),
        "runtime_enablement_detected": runtime_enablement_detected,
        **runtime_flags,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="CodexProject repository root.")
    parser.add_argument("--generated-at", default=None, help="Optional timestamp for deterministic reports.")
    args = parser.parse_args(argv)
    report = build_readiness_report(Path(args.root).resolve(), generated_at=args.generated_at)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
