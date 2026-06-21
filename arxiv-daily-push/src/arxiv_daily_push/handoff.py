"""Phase 10 runner, release, and email dry-run handoff."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .config import DEFAULT_RECIPIENT, DEFAULT_TIMEZONE


class HandoffError(ValueError):
    """Raised when a handoff would enable external side effects."""


def build_handoff(run_payload: Mapping[str, Any], *, generated_at: str) -> dict[str, Any]:
    record = run_payload.get("run_record")
    if not isinstance(record, Mapping) or record.get("current_state") != "completed":
        raise HandoffError("Phase 10 handoff requires a completed dry-run RunRecord")
    run_id = str(record["run_id"])
    return {
        "handoff_id": f"handoff:{run_id}",
        "run_id": run_id,
        "generated_at": generated_at,
        "runner_gate": {
            "scheduler_enabled": False,
            "github_actions_runner_enabled": False,
            "unattended_execution_allowed": False,
            "timezone": record.get("timezone", DEFAULT_TIMEZONE),
            "target_local_time": "05:00",
        },
        "release_gate": {
            "release_upload_allowed": False,
            "release_url": "",
            "artifacts_preview": _artifact_preview(run_payload),
        },
        "email_transport_gate": {
            "recipient": DEFAULT_RECIPIENT,
            "real_smtp_send_enabled": False,
            "smtp_secret_required": True,
            "preview_subject": str((run_payload.get("email_preview") or {}).get("subject") or ""),
        },
        "blocking_reasons": [
            "scheduler remains disabled in Phase 10",
            "release upload remains disabled in Phase 10",
            "real SMTP send remains disabled in Phase 10",
        ],
    }


def validate_handoff(handoff: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for gate_name, flag_name in (
        ("runner_gate", "scheduler_enabled"),
        ("runner_gate", "github_actions_runner_enabled"),
        ("runner_gate", "unattended_execution_allowed"),
        ("release_gate", "release_upload_allowed"),
        ("email_transport_gate", "real_smtp_send_enabled"),
    ):
        gate = handoff.get(gate_name)
        if not isinstance(gate, Mapping):
            errors.append(f"{gate_name} must be an object")
        elif gate.get(flag_name) is not False:
            errors.append(f"{gate_name}.{flag_name} must be false in Phase 10")
    if not handoff.get("blocking_reasons"):
        errors.append("handoff.blocking_reasons must document disabled external side effects")
    return errors


def _artifact_preview(run_payload: Mapping[str, Any]) -> list[dict[str, str]]:
    previews: list[dict[str, str]] = []
    for key in ("lesson", "narration", "storyboard"):
        if key in run_payload:
            previews.append({"artifact_type": key, "path": f"dry-run://{key}", "status": "preview_only"})
    return previews
