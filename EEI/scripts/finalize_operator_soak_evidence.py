#!/usr/bin/env python3
"""Finalize A209 operator-soak evidence into downstream release-gate input.

This command does not close A209. It gives operators one safe place to refresh
the current heartbeat, regenerate the evidence validator artifact, and see
whether downstream release-gate artifacts may be regenerated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.record_operator_soak_heartbeat import (  # noqa: E402
    DEFAULT_OUTPUT as DEFAULT_HEARTBEAT,
)
from scripts.record_operator_soak_heartbeat import (  # noqa: E402
    build_heartbeat_payload,
    validate_heartbeat_payload,
)
from scripts.validate_operator_soak_evidence import (  # noqa: E402
    DEFAULT_OUTPUT as DEFAULT_EVIDENCE,
)
from scripts.validate_operator_soak_evidence import (  # noqa: E402
    build_validation_payload,
    display_path,
    read_parameters,
    write_payload,
)

ROOT = PROJECT_ROOT
SCHEMA_VERSION = "eei-a209-operator-soak-finalization-preflight-v1"
DEFAULT_OUTPUT = ROOT / "artifacts/tests/a209/t1307_operator_soak_finalization_preflight.json"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{display_path(path)} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def summarize_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    results = {}
    for row in evidence.get("results", []):
        if isinstance(row, dict):
            results[str(row.get("label"))] = {
                "status": row.get("status"),
                "windows_completed": row.get("windows_completed"),
                "checkpoint_windows": row.get("checkpoint_windows"),
                "completed_duration_seconds": row.get("completed_duration_seconds"),
                "errors": row.get("errors", []),
                "missing": row.get("missing", []),
            }
    return {
        "status": evidence.get("status"),
        "release_gate_closed_by_validator": evidence.get(
            "release_gate_closed_by_validator"
        ),
        "a209_task_status_required": evidence.get("a209_task_status_required"),
        "results": results,
    }


def summarize_heartbeat(heartbeat: dict[str, Any]) -> dict[str, Any]:
    progress = heartbeat.get("progress") if isinstance(heartbeat.get("progress"), dict) else {}
    contract = (
        heartbeat.get("background_resolution_contract")
        if isinstance(heartbeat.get("background_resolution_contract"), dict)
        else {}
    )
    return {
        "status": heartbeat.get("status"),
        "progress_status": heartbeat.get("progress_status"),
        "release_gate_closed_by_background_heartbeat": heartbeat.get(
            "release_gate_closed_by_background_heartbeat"
        ),
        "operator_process_status": contract.get("operator_process_status"),
        "operator_pid": contract.get("operator_pid"),
        "watchdog_process_status": contract.get("watchdog_process_status"),
        "watchdog_pid": contract.get("watchdog_pid"),
        "target_windows": progress.get("target_windows"),
        "windows_completed": progress.get("windows_completed"),
        "windows_failed": progress.get("windows_failed"),
        "windows_remaining": progress.get("windows_remaining"),
        "completion_percent": progress.get("completion_percent"),
    }


def finalization_status(
    *,
    heartbeat_summary: dict[str, Any],
    evidence_summary: dict[str, Any],
    heartbeat_errors: list[str],
) -> str:
    if heartbeat_errors or evidence_summary["status"] == "FAIL":
        return "A209_FINALIZATION_OPERATOR_INTERVENTION_REQUIRED"
    if (
        heartbeat_summary.get("progress_status") == "RUNNING_PARTIAL"
        and heartbeat_summary.get("windows_failed") == 0
        and heartbeat_summary.get("operator_process_status") == "RUNNING"
    ):
        return "A209_FINALIZATION_BLOCKED_RUNNING_PARTIAL"
    if evidence_summary["status"] == "FAILED_OPERATOR_EVIDENCE":
        return "A209_FINALIZATION_OPERATOR_INTERVENTION_REQUIRED"
    if evidence_summary["status"] == "EVIDENCE_READY_FOR_RELEASE_MANAGER_REVIEW":
        if (
            heartbeat_summary.get("windows_completed") == 288
            and heartbeat_summary.get("windows_failed") == 0
        ):
            return "A209_FINALIZATION_READY_FOR_RELEASE_GATE_REGEN"
        return "A209_FINALIZATION_EVIDENCE_READY_HEARTBEAT_STALE"
    if heartbeat_summary.get("progress_status") == "COMPLETE_SUMMARY_PENDING":
        return "A209_FINALIZATION_BLOCKED_SUMMARY_PENDING"
    return "A209_FINALIZATION_BLOCKED_MISSING_OR_PARTIAL"


def build_preflight(
    *,
    heartbeat_path: Path = DEFAULT_HEARTBEAT,
    evidence_path: Path = DEFAULT_EVIDENCE,
    generated_at: str | None = None,
) -> dict[str, Any]:
    heartbeat = read_json(heartbeat_path)
    evidence = read_json(evidence_path)
    heartbeat_errors = validate_heartbeat_payload(heartbeat)
    heartbeat_summary = summarize_heartbeat(heartbeat)
    evidence_summary = summarize_evidence(evidence)
    status = finalization_status(
        heartbeat_summary=heartbeat_summary,
        evidence_summary=evidence_summary,
        heartbeat_errors=heartbeat_errors,
    )
    downstream_refresh_allowed = status == "A209_FINALIZATION_READY_FOR_RELEASE_GATE_REGEN"
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": "t1307-a209-operator-soak-finalization-preflight",
        "generated_at": generated_at or utc_now(),
        "system_name": "EEI",
        "system_en_name": "Enterprise Ecosystem Intelligence",
        "task_id": "T1307",
        "acceptance_ids": ["A209"],
        "status": status,
        "a209_evidence_ready_for_release_manager": downstream_refresh_allowed,
        "downstream_release_gate_refresh_allowed": downstream_refresh_allowed,
        "release_gate_closed_by_finalizer": False,
        "a209_task_status_required": "IN_PROGRESS",
        "source_files": {
            "heartbeat": display_path(heartbeat_path),
            "heartbeat_sha256": sha256_file(heartbeat_path),
            "evidence_validation": display_path(evidence_path),
            "evidence_validation_sha256": sha256_file(evidence_path),
        },
        "source_statuses": {
            "heartbeat": heartbeat_summary,
            "evidence_validation": evidence_summary,
            "heartbeat_validation_errors": heartbeat_errors,
        },
        "operator_next_actions": operator_next_actions(status),
        "downstream_refresh_commands": [
            "make generate-production-api-release-preflight",
            "make generate-release-manager-activation-artifact",
            "make generate-mvp-release-gate-preflight",
            "make generate-clean-room-release generate-release-artifacts",
            "make verify",
        ],
        "non_claims": [
            "This finalizer does not close A209 by itself.",
            "This finalizer does not replace validate_operator_soak_evidence.py.",
            "This finalizer does not publish production graph or score artifacts.",
            "This finalizer does not replace A202, A210, A026 or A027 evidence.",
        ],
        "rollback": [
            "Regenerate heartbeat and evidence-validation artifacts from source logs.",
            "Do not delete the live 24h checkpoint or log during rollback.",
            "If status requires operator intervention, inspect failed windows before resume.",
        ],
    }


def operator_next_actions(status: str) -> list[str]:
    if status == "A209_FINALIZATION_READY_FOR_RELEASE_GATE_REGEN":
        return [
            "Regenerate A203, release-manager and MVP release-gate artifacts.",
            "Run make verify and root governance before committing release-gate refresh.",
        ]
    if status == "A209_FINALIZATION_EVIDENCE_READY_HEARTBEAT_STALE":
        return [
            "Refresh the A209 heartbeat so it reports 288/288 windows and zero failures.",
            "Rerun this finalizer before downstream gate regeneration.",
        ]
    if status == "A209_FINALIZATION_BLOCKED_RUNNING_PARTIAL":
        return [
            "Keep the detached 24h soak and watchdog running.",
            "Refresh heartbeat again after more windows complete.",
        ]
    if status == "A209_FINALIZATION_BLOCKED_SUMMARY_PENDING":
        return [
            "Wait for or regenerate the final 24h summary JSON from checkpoints.",
            "Run validate_operator_soak_evidence.py generate after summary exists.",
        ]
    if status == "A209_FINALIZATION_OPERATOR_INTERVENTION_REQUIRED":
        return [
            "Inspect heartbeat_validation_errors and evidence result errors.",
            "Do not auto-resume if any failed window is present.",
        ]
    return [
        "Start or resume the detached operator soak using the documented A209 command.",
        "Generate heartbeat and evidence-validation artifacts after progress changes.",
    ]


def validate_preflight(
    payload: dict[str, Any],
    *,
    heartbeat_path: Path = DEFAULT_HEARTBEAT,
    evidence_path: Path = DEFAULT_EVIDENCE,
) -> None:
    expected = build_preflight(
        heartbeat_path=heartbeat_path,
        evidence_path=evidence_path,
        generated_at=payload.get("generated_at"),
    )
    checked_fields = (
        "schema_version",
        "artifact_id",
        "system_name",
        "task_id",
        "acceptance_ids",
        "status",
        "a209_evidence_ready_for_release_manager",
        "downstream_release_gate_refresh_allowed",
        "release_gate_closed_by_finalizer",
        "a209_task_status_required",
        "source_files",
        "source_statuses",
        "operator_next_actions",
        "downstream_refresh_commands",
        "non_claims",
    )
    for key in checked_fields:
        if payload.get(key) != expected.get(key):
            raise ValueError(f"A209 finalization preflight drift: {key}")
    if payload.get("release_gate_closed_by_finalizer") is not False:
        raise ValueError("A209 finalizer must not close the release gate")
    if payload.get("downstream_release_gate_refresh_allowed") is True:
        if payload.get("status") != "A209_FINALIZATION_READY_FOR_RELEASE_GATE_REGEN":
            raise ValueError("downstream refresh requires ready finalization status")


def refresh_upstream_artifacts() -> None:
    heartbeat = build_heartbeat_payload()
    heartbeat_errors = validate_heartbeat_payload(heartbeat)
    if heartbeat_errors:
        raise ValueError(f"heartbeat cannot be refreshed: {heartbeat_errors}")
    write_json(DEFAULT_HEARTBEAT, heartbeat)
    write_payload(DEFAULT_EVIDENCE, build_validation_payload(parameters=read_parameters()))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("generate", "validate"))
    parser.add_argument("--heartbeat", type=Path, default=DEFAULT_HEARTBEAT)
    parser.add_argument("--evidence-validation", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--refresh-upstream",
        action="store_true",
        help="Refresh heartbeat and evidence-validation artifacts before generating.",
    )
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "generate":
        if args.refresh_upstream:
            refresh_upstream_artifacts()
        payload = build_preflight(
            heartbeat_path=args.heartbeat,
            evidence_path=args.evidence_validation,
        )
        validate_preflight(
            payload,
            heartbeat_path=args.heartbeat,
            evidence_path=args.evidence_validation,
        )
        write_json(args.output, payload)
        if not args.quiet:
            print(json.dumps({"generated": True, "artifact": display_path(args.output)}))
    else:
        validate_preflight(
            read_json(args.output),
            heartbeat_path=args.heartbeat,
            evidence_path=args.evidence_validation,
        )
        if not args.quiet:
            print(json.dumps({"valid": True, "artifact": display_path(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
