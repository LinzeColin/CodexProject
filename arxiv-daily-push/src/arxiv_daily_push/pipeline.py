"""Phase 9 local daily dry-run pipeline orchestration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .config import DEFAULT_TIMEZONE
from .evidence_gate import gate_publication
from .lesson import generate_lesson
from .narration import generate_narration_plan
from .notifications import render_email
from .state_machine import initial_run_record, transition_run_record, validate_run_record
from .video import generate_storyboard


class PipelineError(ValueError):
    """Raised when the dry-run pipeline cannot complete safely."""


def run_daily_dry_run(
    source_item: Mapping[str, Any],
    claims: Sequence[Mapping[str, Any]],
    *,
    run_id: str,
    publication_id: str,
    date: str,
    generated_at: str,
    timezone: str = DEFAULT_TIMEZONE,
) -> dict[str, Any]:
    record = initial_run_record(run_id, date, timezone)
    record["phase"] = "9"
    record = _transition(record, "health_checked", generated_at)

    record["source_items"] = [dict(source_item)]
    record["stages"].append({"name": "source_collected", "status": "passed"})
    record = _transition(record, "source_collected", generated_at)

    publication_gate = gate_publication(
        source_item,
        claims,
        run_id=run_id,
        publication_id=publication_id,
        publication_type="daily",
        created_at=generated_at,
    )
    if not publication_gate["publish_allowed"]:
        raise PipelineError("; ".join(publication_gate["blocking_reasons"]))
    record["evidence_claims"] = publication_gate["ledger"]["claims"]
    record["stages"].append({"name": "evidence_bound", "status": "passed"})
    record = _transition(record, "evidence_bound", generated_at)

    lesson = generate_lesson(source_item, claims, generated_at=generated_at)
    record["lessons"] = [lesson]
    record["stages"].append({"name": "lesson_ready", "status": "passed"})
    record = _transition(record, "lesson_ready", generated_at)

    narration = generate_narration_plan(lesson, generated_at=generated_at)
    storyboard = generate_storyboard(narration, generated_at=generated_at)
    record["storyboards"] = [storyboard]
    record["stages"].append({"name": "storyboard_ready", "status": "passed"})
    record = _transition(record, "storyboard_ready", generated_at)

    record["publications"] = [publication_gate["publication"]]
    record["stages"].append({"name": "publication_ready", "status": "passed"})
    record = _transition(record, "publication_ready", generated_at)

    email = render_email(
        "success",
        run_id,
        "daily dry-run pipeline completed",
        date=date,
        phase="9",
        stage="daily_dry_run",
        claim_gate="pass",
        next_action="review_dry_run_outputs_then_continue_phase10",
    )
    record["stages"].append({"name": "notified", "status": "passed"})
    record = _transition(record, "notified", generated_at)
    record = _transition(record, "completed", generated_at)
    errors = validate_run_record(record)
    if errors:
        raise PipelineError("; ".join(errors))
    return {
        "status": "succeeded",
        "run_record": record,
        "publication_gate": publication_gate,
        "lesson": lesson,
        "narration": narration,
        "storyboard": storyboard,
        "email_preview": {"recipient": email.recipient, "subject": email.subject, "body": email.body},
    }


def _transition(record: Mapping[str, Any], next_state: str, at: str) -> dict[str, Any]:
    return transition_run_record(record, next_state, reason=f"phase9:{next_state}", at=at)
