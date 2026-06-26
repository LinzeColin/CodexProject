#!/usr/bin/env python3
"""Finalize A209 operator-soak evidence into downstream release-gate input.

This command does not close A209. It gives operators one safe place to refresh
the current heartbeat, regenerate the evidence validator artifact, and see
whether downstream release-gate artifacts may be regenerated.
"""
from __future__ import annotations

import argparse
import copy
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
    REQUIRED_RUNS,
    SoakRequirement,
    build_validation_payload,
    display_path,
    read_parameters,
    write_payload,
)

ROOT = PROJECT_ROOT
SCHEMA_VERSION = "eei-a209-operator-soak-finalization-preflight-v1"
RECOVERY_PACKET_SCHEMA_VERSION = "eei-a209-operator-soak-recovery-authorization-packet-v1"
DEFAULT_OUTPUT = ROOT / "artifacts/tests/a209/t1307_operator_soak_finalization_preflight.json"
DEFAULT_PROMOTION_MANIFEST = ROOT / "artifacts/tests/a209/t1307_operator_soak_24h_promotion.json"
DEFAULT_RECOVERY_PACKET = (
    ROOT / "artifacts/tests/a209/t1307_operator_soak_recovery_authorization_packet.json"
)
DEFAULT_INCIDENT_DIR = ROOT / "artifacts/tests/a209/incidents"
DEFAULT_RECOVERY_AUTHORIZATION_TARGET = (
    "artifacts/operator_inputs/a209/clean-rerun-authorization.json"
)


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


def repository_source_entry(role: str, path: Path) -> dict[str, Any]:
    return {
        "role": role,
        "path": display_path(path),
        "repository_managed": True,
        "sha256": sha256_file(path),
        "preservation_required_before_clean_rerun": True,
        "hash_bound_in_ci": True,
    }


def runtime_source_entry(role: str, path: str | None) -> dict[str, Any]:
    return {
        "role": role,
        "path": path or "UNKNOWN_OPERATOR_RUNTIME_PATH",
        "repository_managed": False,
        "sha256": None,
        "preservation_required_before_clean_rerun": True,
        "hash_bound_in_ci": False,
        "validation_scope": "operator must preserve and attest this external runtime file",
    }


def sanitize_timestamp(value: str) -> str:
    return value.replace(":", "").replace("-", "").replace("+", "Z")


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


def evidence_result(evidence: dict[str, Any], label: str) -> dict[str, Any]:
    for row in evidence.get("results", []):
        if isinstance(row, dict) and row.get("label") == label:
            return row
    return {}


def canonical_failed_evidence_summary(evidence: dict[str, Any]) -> dict[str, Any]:
    result = evidence_result(evidence, "operator_24h")
    return {
        "label": "operator_24h",
        "status": result.get("status"),
        "output_path": result.get("output_path"),
        "checkpoint_path": result.get("checkpoint_path"),
        "windows_completed": result.get("windows_completed"),
        "windows_failed": result.get("windows_failed"),
        "checkpoint_windows": result.get("checkpoint_windows"),
        "failed_checkpoint_windows": result.get("failed_checkpoint_windows"),
        "failed_windows": result.get("failed_windows", []),
        "errors": result.get("errors", []),
    }


def isolated_rerun_failure_summary(heartbeat: dict[str, Any]) -> dict[str, Any]:
    progress = heartbeat.get("progress") if isinstance(heartbeat.get("progress"), dict) else {}
    latest_success = (
        progress.get("latest_successful_window")
        if isinstance(progress.get("latest_successful_window"), dict)
        else {}
    )
    failed_index = None
    if isinstance(latest_success.get("index"), int) and progress.get("windows_failed"):
        failed_index = latest_success["index"] + 1
    elif isinstance(progress.get("windows_completed"), int) and progress.get("windows_failed"):
        failed_index = progress["windows_completed"] + progress.get("windows_failed", 0)
    return {
        "status": heartbeat.get("status"),
        "progress_status": heartbeat.get("progress_status"),
        "target_windows": progress.get("target_windows"),
        "windows_completed": progress.get("windows_completed"),
        "windows_failed": progress.get("windows_failed"),
        "windows_remaining": progress.get("windows_remaining"),
        "completion_percent": progress.get("completion_percent"),
        "latest_successful_window_index": latest_success.get("index"),
        "latest_successful_window_ended_at": latest_success.get("ended_at"),
        "inferred_failed_window_index": failed_index,
        "inferred_failed_window_output_path": infer_failed_window_output_path(
            latest_success.get("output_path"),
            latest_success.get("index"),
            failed_index,
        ),
    }


def infer_failed_window_output_path(
    latest_output_path: str | None,
    latest_index: Any,
    failed_index: int | None,
) -> str:
    if (
        latest_output_path
        and isinstance(latest_index, int)
        and isinstance(failed_index, int)
    ):
        suffix = f"-{latest_index}.json"
        if latest_output_path.endswith(suffix):
            return f"{latest_output_path.removesuffix(suffix)}-{failed_index}.json"
    return "UNKNOWN_OPERATOR_RUNTIME_PATH: inspect checkpoint/log failed window output_path"


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


def build_recovery_authorization_packet(
    *,
    heartbeat_path: Path = DEFAULT_HEARTBEAT,
    evidence_path: Path = DEFAULT_EVIDENCE,
    finalization_path: Path = DEFAULT_OUTPUT,
    generated_at: str | None = None,
) -> dict[str, Any]:
    heartbeat = read_json(heartbeat_path)
    evidence = read_json(evidence_path)
    finalization = read_json(finalization_path)
    heartbeat_summary = summarize_heartbeat(heartbeat)
    evidence_summary = summarize_evidence(evidence)
    finalization_status_value = finalization.get("status")
    recovery_required = (
        heartbeat.get("progress_status") == "FAILED_WINDOW"
        or evidence.get("status") in {"FAIL", "FAILED_OPERATOR_EVIDENCE"}
        or finalization_status_value == "A209_FINALIZATION_OPERATOR_INTERVENTION_REQUIRED"
    )
    artifacts = heartbeat.get("artifacts") if isinstance(heartbeat.get("artifacts"), dict) else {}
    progress = heartbeat.get("progress") if isinstance(heartbeat.get("progress"), dict) else {}
    latest_success = (
        progress.get("latest_successful_window")
        if isinstance(progress.get("latest_successful_window"), dict)
        else {}
    )
    canonical = canonical_failed_evidence_summary(evidence)
    clean_dir = "/private/tmp/eei-a209-clean-rerun-YYYYMMDD-HHMM"
    clean_output = f"{clean_dir}/operator_soak_24h.json"
    clean_checkpoint = f"{clean_dir}/operator_soak_24h.checkpoints.jsonl"
    return {
        "schema_version": RECOVERY_PACKET_SCHEMA_VERSION,
        "artifact_id": "t1307-a209-operator-soak-recovery-authorization-packet",
        "generated_at": generated_at or utc_now(),
        "system_name": "EEI",
        "system_en_name": "Enterprise Ecosystem Intelligence",
        "task_id": "T1307",
        "acceptance_ids": ["A209"],
        "status": "A209_RECOVERY_OPERATOR_AUTHORIZATION_REQUIRED"
        if recovery_required
        else "A209_RECOVERY_NOT_REQUIRED",
        "a209_task_status_required": "IN_PROGRESS",
        "release_gate_closed_by_recovery_packet": False,
        "clean_rerun_authorized_by_packet": False,
        "source_files": {
            "heartbeat": display_path(heartbeat_path),
            "heartbeat_sha256": sha256_file(heartbeat_path),
            "evidence_validation": display_path(evidence_path),
            "evidence_validation_sha256": sha256_file(evidence_path),
            "finalization_preflight": display_path(finalization_path),
            "finalization_preflight_sha256": sha256_file(finalization_path),
        },
        "current_gate_state": {
            "heartbeat": heartbeat_summary,
            "evidence_validation": evidence_summary,
            "finalization_status": finalization_status_value,
            "downstream_release_gate_refresh_allowed": finalization.get(
                "downstream_release_gate_refresh_allowed"
            ),
            "release_gate_closed_by_finalizer": finalization.get(
                "release_gate_closed_by_finalizer"
            ),
        },
        "failed_evidence_summary": {
            "canonical_failed_operator_evidence": canonical,
            "latest_isolated_rerun_failure": isolated_rerun_failure_summary(heartbeat),
        },
        "failed_evidence_preservation": {
            "required_before_clean_rerun": recovery_required,
            "operator_attestation_required": True,
            "authorization_target": DEFAULT_RECOVERY_AUTHORIZATION_TARGET,
            "repository_sources": [
                repository_source_entry("background_heartbeat", heartbeat_path),
                repository_source_entry("evidence_validation", evidence_path),
                repository_source_entry("finalization_preflight", finalization_path),
            ],
            "runtime_sources_to_preserve": [
                runtime_source_entry(
                    "canonical_failed_24h_summary",
                    canonical.get("output_path"),
                ),
                runtime_source_entry(
                    "canonical_failed_24h_checkpoint",
                    canonical.get("checkpoint_path"),
                ),
                runtime_source_entry(
                    "isolated_rerun_summary",
                    artifacts.get("operator_output_path"),
                ),
                runtime_source_entry(
                    "isolated_rerun_checkpoint",
                    artifacts.get("operator_checkpoint_path"),
                ),
                runtime_source_entry("isolated_rerun_log", artifacts.get("operator_log_path")),
                runtime_source_entry("isolated_rerun_pid", artifacts.get("operator_pid_path")),
                runtime_source_entry(
                    "latest_successful_window_output",
                    latest_success.get("output_path"),
                ),
                runtime_source_entry(
                    "inferred_failed_window_output",
                    isolated_rerun_failure_summary(heartbeat).get(
                        "inferred_failed_window_output_path"
                    ),
                ),
            ],
        },
        "operator_authorization_contract": {
            "authorization_required_before_start": True,
            "authorization_file": DEFAULT_RECOVERY_AUTHORIZATION_TARGET,
            "required_schema_version": "eei-a209-clean-rerun-authorization-v1",
            "required_fields": [
                "schema_version",
                "authorized_by",
                "authorized_at",
                "reason",
                "failed_evidence_preserved",
                "preserved_evidence_manifest_sha256",
                "allow_clean_rerun",
                "allowed_output_dir",
                "acknowledge_previous_failed_window",
            ],
            "required_boolean_values": {
                "failed_evidence_preserved": True,
                "allow_clean_rerun": True,
                "acknowledge_previous_failed_window": True,
            },
        },
        "clean_rerun_contract": {
            "may_start_without_authorization": False,
            "recommended_output_dir_template": f"{clean_dir}/",
            "operator_command_template": (
                "node scripts/run_operator_soak.mjs --mode operator_24h "
                "--duration-hours 24 --window-seconds 300 "
                f"--output {clean_output} "
                f"--checkpoint {clean_checkpoint} --fail-on-budget --quiet"
            ),
            "watchdog_command_template": (
                "python scripts/watch_operator_soak.py --detach --execute --auto-resume "
                "--cycles 300 --interval-seconds 300 "
                f"--write-output {clean_dir}/watchdog.json"
            ),
            "post_rerun_validation_commands": [
                "python scripts/finalize_operator_soak_evidence.py promote-rerun "
                f"--source-output {clean_output} --source-checkpoint {clean_checkpoint}",
                "make generate-operator-soak-background-heartbeat "
                "generate-operator-soak-evidence-artifact "
                "generate-operator-soak-finalization-preflight",
                "make validate-operator-soak-background-heartbeat "
                "validate-operator-soak-evidence "
                "validate-operator-soak-finalization-preflight",
            ],
        },
        "operator_next_actions": [
            "Preserve every listed repository and runtime evidence file before any clean rerun.",
            "Write a signed clean-rerun authorization file only after preservation is complete.",
            "Start a clean 24h rerun in a new output directory only after authorization.",
            "Promote a rerun only after 288/288 windows pass, zero failures, "
            "and validator release-ready status.",
        ],
        "non_claims": [
            "This recovery packet does not start, stop, resume, or restart A209.",
            "This recovery packet does not close A209 or any release gate.",
            "This recovery packet does not promote failed or partial runtime evidence.",
            "This recovery packet does not replace the final 24h evidence validator.",
        ],
        "rollback": [
            "Regenerate this packet from heartbeat, evidence-validation and "
            "finalization artifacts.",
            "Do not delete failed runtime evidence during rollback.",
            "If a clean rerun was started without authorization, discard it as "
            "non-release evidence.",
        ],
    }


def finalization_status(
    *,
    heartbeat_summary: dict[str, Any],
    evidence_summary: dict[str, Any],
    heartbeat_errors: list[str],
) -> str:
    if heartbeat_errors:
        return "A209_FINALIZATION_OPERATOR_INTERVENTION_REQUIRED"
    if is_running_zero_failure_rerun(heartbeat_summary):
        return "A209_FINALIZATION_BLOCKED_RUNNING_PARTIAL"
    if evidence_summary["status"] in {"FAIL", "FAILED_OPERATOR_EVIDENCE"}:
        return "A209_FINALIZATION_OPERATOR_INTERVENTION_REQUIRED"
    if evidence_summary["status"] == "EVIDENCE_READY_FOR_RELEASE_MANAGER_REVIEW":
        if (
            heartbeat_summary.get("windows_completed") == 288
            and heartbeat_summary.get("windows_failed") == 0
        ):
            return "A209_FINALIZATION_READY_FOR_RELEASE_GATE_REGEN"
        return "A209_FINALIZATION_EVIDENCE_READY_HEARTBEAT_STALE"
    if heartbeat_summary.get("progress_status") == "RUNNING_PARTIAL":
        return "A209_FINALIZATION_BLOCKED_RUNNING_PARTIAL"
    if heartbeat_summary.get("progress_status") == "COMPLETE_SUMMARY_PENDING":
        return "A209_FINALIZATION_BLOCKED_SUMMARY_PENDING"
    return "A209_FINALIZATION_BLOCKED_MISSING_OR_PARTIAL"


def is_running_zero_failure_rerun(heartbeat_summary: dict[str, Any]) -> bool:
    windows_completed = heartbeat_summary.get("windows_completed")
    return (
        heartbeat_summary.get("progress_status") == "RUNNING_PARTIAL"
        and heartbeat_summary.get("operator_process_status") == "RUNNING"
        and isinstance(windows_completed, int)
        and 0 < windows_completed < 288
        and heartbeat_summary.get("windows_failed") == 0
    )


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


def validate_recovery_authorization_packet(
    payload: dict[str, Any],
    *,
    heartbeat_path: Path = DEFAULT_HEARTBEAT,
    evidence_path: Path = DEFAULT_EVIDENCE,
    finalization_path: Path = DEFAULT_OUTPUT,
) -> None:
    expected = build_recovery_authorization_packet(
        heartbeat_path=heartbeat_path,
        evidence_path=evidence_path,
        finalization_path=finalization_path,
        generated_at=payload.get("generated_at"),
    )
    checked_fields = (
        "schema_version",
        "artifact_id",
        "system_name",
        "task_id",
        "acceptance_ids",
        "status",
        "a209_task_status_required",
        "release_gate_closed_by_recovery_packet",
        "clean_rerun_authorized_by_packet",
        "source_files",
        "current_gate_state",
        "failed_evidence_summary",
        "failed_evidence_preservation",
        "operator_authorization_contract",
        "clean_rerun_contract",
        "operator_next_actions",
        "non_claims",
    )
    for key in checked_fields:
        if payload.get(key) != expected.get(key):
            raise ValueError(f"A209 recovery authorization packet drift: {key}")
    if payload.get("release_gate_closed_by_recovery_packet") is not False:
        raise ValueError("A209 recovery packet must not close release gates")
    if payload.get("clean_rerun_authorized_by_packet") is not False:
        raise ValueError("A209 recovery packet must not authorize a clean rerun by itself")
    if payload.get("status") == "A209_RECOVERY_OPERATOR_AUTHORIZATION_REQUIRED":
        preservation = payload.get("failed_evidence_preservation")
        if not isinstance(preservation, dict):
            raise ValueError("A209 recovery packet missing preservation contract")
        if preservation.get("required_before_clean_rerun") is not True:
            raise ValueError("A209 recovery packet must require preservation before rerun")
        authorization = payload.get("operator_authorization_contract")
        if not isinstance(authorization, dict):
            raise ValueError("A209 recovery packet missing authorization contract")
        if authorization.get("authorization_required_before_start") is not True:
            raise ValueError("A209 recovery packet must require operator authorization")


def refresh_upstream_artifacts() -> None:
    heartbeat = build_heartbeat_payload()
    heartbeat_errors = validate_heartbeat_payload(heartbeat)
    if heartbeat_errors:
        raise ValueError(f"heartbeat cannot be refreshed: {heartbeat_errors}")
    write_json(DEFAULT_HEARTBEAT, heartbeat)
    write_payload(DEFAULT_EVIDENCE, build_validation_payload(parameters=read_parameters()))


def promotable_required_runs(
    *,
    source_output: Path,
    source_checkpoint: Path,
    short_output: Path = REQUIRED_RUNS[0].output_path,
    short_checkpoint: Path = REQUIRED_RUNS[0].checkpoint_path,
) -> tuple[SoakRequirement, SoakRequirement]:
    short = SoakRequirement(
        label="operator_4h",
        mode="operator_4h",
        output_path=short_output,
        checkpoint_path=short_checkpoint,
        parameter_key="soak.short_duration_hours",
        coverage_key="covers_4h_target",
    )
    long = SoakRequirement(
        label="operator_24h",
        mode="operator_24h",
        output_path=source_output,
        checkpoint_path=source_checkpoint,
        parameter_key="soak.long_duration_hours",
        coverage_key="covers_24h_target",
    )
    return (short, long)


def build_promotable_source_validation_payload(
    *,
    source_output: Path,
    source_checkpoint: Path,
    short_output: Path = REQUIRED_RUNS[0].output_path,
    short_checkpoint: Path = REQUIRED_RUNS[0].checkpoint_path,
    parameters: dict[str, float] | None = None,
) -> dict[str, Any]:
    return build_validation_payload(
        parameters=parameters or read_parameters(),
        required_runs=promotable_required_runs(
            source_output=source_output,
            source_checkpoint=source_checkpoint,
            short_output=short_output,
            short_checkpoint=short_checkpoint,
        ),
    )


def archive_existing_artifact(
    path: Path,
    *,
    incident_dir: Path,
    promoted_at: str,
) -> dict[str, Any] | None:
    if not path.exists():
        return None
    incident_dir.mkdir(parents=True, exist_ok=True)
    archive_path = incident_dir / f"{sanitize_timestamp(promoted_at)}_{path.name}"
    archive_path.write_bytes(path.read_bytes())
    return {
        "original_path": display_path(path),
        "archive_path": display_path(archive_path),
        "sha256": sha256_file(archive_path),
    }


def rewrite_promoted_runner_paths(
    *,
    source_payload: dict[str, Any],
    source_output: Path,
    source_checkpoint: Path,
    destination_output: Path,
    destination_checkpoint: Path,
    promoted_at: str,
    archived_previous: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = copy.deepcopy(source_payload)
    runner = payload.get("runner")
    if not isinstance(runner, dict):
        raise ValueError("source output runner must be an object")
    runner["output_path"] = display_path(destination_output)
    runner["checkpoint_path"] = display_path(destination_checkpoint)
    payload["promotion"] = {
        "schema_version": "eei-a209-operator-soak-rerun-promotion-v1",
        "promoted_at": promoted_at,
        "promoted_by": "scripts/finalize_operator_soak_evidence.py promote-rerun",
        "source_output_path": display_path(source_output),
        "source_output_sha256": sha256_file(source_output),
        "source_checkpoint_path": display_path(source_checkpoint),
        "source_checkpoint_sha256": sha256_file(source_checkpoint),
        "destination_output_path": display_path(destination_output),
        "destination_checkpoint_path": display_path(destination_checkpoint),
        "archived_previous_artifacts": archived_previous,
        "release_gate_closed_by_promotion": False,
        "reason": (
            "Promote an isolated 24h rerun after the existing 4h evidence and "
            "the isolated 24h source both validate as release-manager review ready."
        ),
    }
    return payload


def promote_rerun_source(
    *,
    source_output: Path,
    source_checkpoint: Path,
    destination_output: Path = REQUIRED_RUNS[1].output_path,
    destination_checkpoint: Path = REQUIRED_RUNS[1].checkpoint_path,
    short_output: Path = REQUIRED_RUNS[0].output_path,
    short_checkpoint: Path = REQUIRED_RUNS[0].checkpoint_path,
    evidence_output: Path = DEFAULT_EVIDENCE,
    promotion_manifest: Path = DEFAULT_PROMOTION_MANIFEST,
    incident_dir: Path = DEFAULT_INCIDENT_DIR,
    parameters: dict[str, float] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    if source_output.resolve() == destination_output.resolve():
        raise ValueError("source_output must differ from destination_output")
    if source_checkpoint.resolve() == destination_checkpoint.resolve():
        raise ValueError("source_checkpoint must differ from destination_checkpoint")

    effective_parameters = parameters or read_parameters()
    source_validation = build_promotable_source_validation_payload(
        source_output=source_output,
        source_checkpoint=source_checkpoint,
        short_output=short_output,
        short_checkpoint=short_checkpoint,
        parameters=effective_parameters,
    )
    if source_validation["status"] != "EVIDENCE_READY_FOR_RELEASE_MANAGER_REVIEW":
        raise ValueError(f"source rerun is not promotable: {source_validation['status']}")

    promoted_at = generated_at or utc_now()
    archived_previous = [
        archive
        for archive in (
            archive_existing_artifact(
                destination_output,
                incident_dir=incident_dir,
                promoted_at=promoted_at,
            ),
            archive_existing_artifact(
                destination_checkpoint,
                incident_dir=incident_dir,
                promoted_at=promoted_at,
            ),
        )
        if archive is not None
    ]
    source_payload = read_json(source_output)
    promoted_payload = rewrite_promoted_runner_paths(
        source_payload=source_payload,
        source_output=source_output,
        source_checkpoint=source_checkpoint,
        destination_output=destination_output,
        destination_checkpoint=destination_checkpoint,
        promoted_at=promoted_at,
        archived_previous=archived_previous,
    )
    write_json(destination_output, promoted_payload)
    destination_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    destination_checkpoint.write_text(
        source_checkpoint.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    promoted_validation = build_validation_payload(
        parameters=effective_parameters,
        required_runs=promotable_required_runs(
            source_output=destination_output,
            source_checkpoint=destination_checkpoint,
            short_output=short_output,
            short_checkpoint=short_checkpoint,
        ),
    )
    if promoted_validation["status"] != "EVIDENCE_READY_FOR_RELEASE_MANAGER_REVIEW":
        raise ValueError(
            "promoted canonical evidence did not validate: "
            f"{promoted_validation['status']}"
        )
    write_payload(evidence_output, promoted_validation)

    manifest = {
        "schema_version": "eei-a209-operator-soak-rerun-promotion-manifest-v1",
        "artifact_id": "t1307-a209-operator-soak-24h-promotion",
        "generated_at": promoted_at,
        "system_name": "EEI",
        "task_id": "T1307",
        "acceptance_ids": ["A209"],
        "status": "PROMOTED_CANONICAL_24H_EVIDENCE_READY_FOR_FINALIZER",
        "release_gate_closed_by_promotion": False,
        "source_validation_status": source_validation["status"],
        "promoted_validation_status": promoted_validation["status"],
        "source_files": {
            "source_output": display_path(source_output),
            "source_output_sha256": sha256_file(source_output),
            "source_checkpoint": display_path(source_checkpoint),
            "source_checkpoint_sha256": sha256_file(source_checkpoint),
            "destination_output": display_path(destination_output),
            "destination_output_sha256": sha256_file(destination_output),
            "destination_checkpoint": display_path(destination_checkpoint),
            "destination_checkpoint_sha256": sha256_file(destination_checkpoint),
            "evidence_validation": display_path(evidence_output),
            "evidence_validation_sha256": sha256_file(evidence_output),
        },
        "archived_previous_artifacts": archived_previous,
        "next_commands": [
            "python scripts/finalize_operator_soak_evidence.py generate",
            "make generate-production-api-release-preflight",
            "make generate-release-manager-activation-artifact",
            "make generate-mvp-release-gate-preflight",
            "make verify",
        ],
        "non_claims": [
            "This promotion does not close A209 by itself.",
            "This promotion does not replace finalizer validation.",
            "This promotion does not replace A202, A210, A026 or A027 evidence.",
        ],
    }
    write_json(promotion_manifest, manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "generate",
            "validate",
            "generate-recovery-packet",
            "validate-recovery-packet",
            "promote-rerun",
        ),
    )
    parser.add_argument("--heartbeat", type=Path, default=DEFAULT_HEARTBEAT)
    parser.add_argument("--evidence-validation", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--finalization-preflight", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--recovery-output", type=Path, default=DEFAULT_RECOVERY_PACKET)
    parser.add_argument("--source-output", type=Path)
    parser.add_argument("--source-checkpoint", type=Path)
    parser.add_argument("--destination-output", type=Path, default=REQUIRED_RUNS[1].output_path)
    parser.add_argument(
        "--destination-checkpoint",
        type=Path,
        default=REQUIRED_RUNS[1].checkpoint_path,
    )
    parser.add_argument("--promotion-manifest", type=Path, default=DEFAULT_PROMOTION_MANIFEST)
    parser.add_argument("--incident-dir", type=Path, default=DEFAULT_INCIDENT_DIR)
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
    elif args.command == "validate":
        validate_preflight(
            read_json(args.output),
            heartbeat_path=args.heartbeat,
            evidence_path=args.evidence_validation,
        )
        if not args.quiet:
            print(json.dumps({"valid": True, "artifact": display_path(args.output)}))
    elif args.command == "generate-recovery-packet":
        payload = build_recovery_authorization_packet(
            heartbeat_path=args.heartbeat,
            evidence_path=args.evidence_validation,
            finalization_path=args.finalization_preflight,
        )
        validate_recovery_authorization_packet(
            payload,
            heartbeat_path=args.heartbeat,
            evidence_path=args.evidence_validation,
            finalization_path=args.finalization_preflight,
        )
        write_json(args.recovery_output, payload)
        if not args.quiet:
            print(
                json.dumps(
                    {
                        "generated": True,
                        "artifact": display_path(args.recovery_output),
                        "status": payload["status"],
                    }
                )
            )
    elif args.command == "validate-recovery-packet":
        validate_recovery_authorization_packet(
            read_json(args.recovery_output),
            heartbeat_path=args.heartbeat,
            evidence_path=args.evidence_validation,
            finalization_path=args.finalization_preflight,
        )
        if not args.quiet:
            print(json.dumps({"valid": True, "artifact": display_path(args.recovery_output)}))
    else:
        if args.source_output is None or args.source_checkpoint is None:
            raise SystemExit("promote-rerun requires --source-output and --source-checkpoint")
        manifest = promote_rerun_source(
            source_output=args.source_output,
            source_checkpoint=args.source_checkpoint,
            destination_output=args.destination_output,
            destination_checkpoint=args.destination_checkpoint,
            evidence_output=args.evidence_validation,
            promotion_manifest=args.promotion_manifest,
            incident_dir=args.incident_dir,
        )
        if not args.quiet:
            print(
                json.dumps(
                    {
                        "promoted": True,
                        "artifact": display_path(args.promotion_manifest),
                        "status": manifest["status"],
                    }
                )
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
