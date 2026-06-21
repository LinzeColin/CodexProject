"""Dry-run email notification rendering."""

from __future__ import annotations

from dataclasses import dataclass

from .config import DEFAULT_RECIPIENT, DEFAULT_TIMEZONE, PROJECT_NAME


@dataclass(frozen=True)
class EmailNotification:
    subject: str
    recipient: str
    body: str


def render_email(
    status: str,
    run_id: str,
    summary: str,
    recipient: str = DEFAULT_RECIPIENT,
    date: str = "not-scheduled",
    phase: str = "1",
    stage: str = "foundation",
    claim_gate: str = "not_applicable_phase1",
    next_action: str = "continue_phase1_or_phase2_when_gate_passes",
) -> EmailNotification:
    normalized_status = status.upper()
    subject = f"[{PROJECT_NAME}][{normalized_status}][{date}] {summary}"
    body = "\n".join(
        [
            f"project: {PROJECT_NAME}",
            f"run_id: {run_id}",
            f"date: {date}",
            f"timezone: {DEFAULT_TIMEZONE}",
            f"status: {normalized_status}",
            f"phase: {phase}",
            f"stage: {stage}",
            f"claim_gate: {claim_gate}",
            "publication: none_phase1",
            "release_url: none_phase1",
            "report_path: docs/phase_records/PHASE_01.md",
            "queue_health: not_applicable_phase1",
            "degradation: none",
            f"next_action: {next_action}",
            "sha256: pending_when_artifacts_exist",
        ]
    )
    return EmailNotification(subject=subject, recipient=recipient, body=body)

