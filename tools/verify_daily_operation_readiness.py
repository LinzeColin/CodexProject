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
        "daily_operation_ready": daily_operation_ready,
        "gate_status": gate.get("status"),
        "blocking_reasons": blocking_reasons,
        "validation_errors": validation_errors,
        "next_required_step": gate.get("next_required_step"),
        "next_executable_task": gate.get("next_executable_task"),
        "authorization_artifact": gate.get("persistent_authorization_artifact_ref", AUTHORIZATION_ARTIFACT_REF),
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
