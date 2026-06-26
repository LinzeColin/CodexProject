"""RunRecord state machine for Phase 2."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .contracts import (
    validate_evidence_claim,
    validate_lesson,
    validate_publication,
    validate_source_item,
    validate_storyboard,
)


RUN_STATES = (
    "created",
    "health_checked",
    "source_collected",
    "evidence_bound",
    "lesson_ready",
    "storyboard_ready",
    "publication_ready",
    "notified",
    "completed",
    "blocked",
    "failed",
)
RUN_STATUSES = {"created", "running", "blocked", "failed", "degraded", "succeeded"}
STAGE_STATUSES = {"not_started", "running", "passed", "blocked", "failed", "skipped"}
TERMINAL_STATES = {"completed", "blocked", "failed"}
ALLOWED_TRANSITIONS = {
    "created": {"health_checked", "blocked", "failed"},
    "health_checked": {"source_collected", "blocked", "failed"},
    "source_collected": {"evidence_bound", "blocked", "failed"},
    "evidence_bound": {"lesson_ready", "blocked", "failed"},
    "lesson_ready": {"storyboard_ready", "publication_ready", "blocked", "failed"},
    "storyboard_ready": {"publication_ready", "blocked", "failed"},
    "publication_ready": {"notified", "completed", "blocked", "failed"},
    "notified": {"completed", "blocked", "failed"},
    "completed": set(),
    "blocked": set(),
    "failed": set(),
}


def validate_transition(current_state: str, next_state: str) -> list[str]:
    if current_state not in RUN_STATES:
        return [f"Unknown current_state: {current_state}"]
    if next_state not in RUN_STATES:
        return [f"Unknown next_state: {next_state}"]
    if next_state not in ALLOWED_TRANSITIONS[current_state]:
        return [f"Transition {current_state} -> {next_state} is not allowed"]
    return []


def initial_run_record(run_id: str, date: str, timezone: str) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "date": date,
        "timezone": timezone,
        "phase": "2",
        "status": "created",
        "current_state": "created",
        "stages": [],
        "state_history": [{"from_state": "", "to_state": "created", "reason": "initial", "at": _initial_history_at(date, timezone)}],
        "source_items": [],
        "evidence_claims": [],
        "lessons": [],
        "storyboards": [],
        "publications": [],
    }


def validate_run_record(record: Mapping[str, Any]) -> list[str]:
    if not isinstance(record, Mapping):
        return ["RunRecord must be an object"]
    errors: list[str] = []
    for field in ("run_id", "date", "timezone", "phase", "status", "current_state", "stages"):
        if record.get(field) in (None, ""):
            errors.append(f"RunRecord.{field} is required")
    if record.get("status") not in RUN_STATUSES:
        errors.append(f"RunRecord.status must be one of {sorted(RUN_STATUSES)}")
    current_state = record.get("current_state")
    if current_state not in RUN_STATES:
        errors.append(f"RunRecord.current_state must be one of {list(RUN_STATES)}")
    if current_state in TERMINAL_STATES and record.get("status") == "running":
        errors.append("RunRecord.status cannot be running when current_state is terminal")
    _validate_stages(record.get("stages"), errors)
    _validate_state_history(record.get("state_history", []), errors)
    history = record.get("state_history", [])
    if isinstance(history, list) and history:
        last = history[-1]
        if isinstance(last, Mapping) and str(last.get("to_state") or "") != current_state:
            errors.append("RunRecord.current_state must match state_history last to_state")
    for item in record.get("source_items", []) or []:
        errors.extend(validate_source_item(item))
    for claim in record.get("evidence_claims", []) or []:
        errors.extend(validate_evidence_claim(claim))
    for lesson in record.get("lessons", []) or []:
        errors.extend(validate_lesson(lesson))
    for storyboard in record.get("storyboards", []) or []:
        errors.extend(validate_storyboard(storyboard))
    for publication in record.get("publications", []) or []:
        errors.extend(validate_publication(publication))
    return errors


def transition_run_record(record: Mapping[str, Any], next_state: str, *, reason: str, at: str) -> dict[str, Any]:
    current_state = str(record.get("current_state") or "")
    errors = validate_transition(current_state, next_state)
    if errors:
        raise ValueError("; ".join(errors))
    updated = copy.deepcopy(dict(record))
    updated["current_state"] = next_state
    if next_state in {"blocked", "failed"}:
        updated["status"] = next_state
    elif next_state == "completed":
        updated["status"] = "succeeded"
    else:
        updated["status"] = "running"
    history = list(updated.get("state_history") or [])
    history.append({"from_state": current_state, "to_state": next_state, "reason": reason, "at": at})
    updated["state_history"] = history
    return updated


def _validate_stages(stages: Any, errors: list[str]) -> None:
    if not isinstance(stages, list):
        errors.append("RunRecord.stages must be an array")
        return
    names: set[str] = set()
    for index, stage in enumerate(stages):
        if not isinstance(stage, Mapping):
            errors.append(f"RunRecord.stages[{index}] must be an object")
            continue
        name = stage.get("name")
        status = stage.get("status")
        if not name:
            errors.append(f"RunRecord.stages[{index}].name is required")
        elif name in names:
            errors.append(f"RunRecord.stages[{index}].name duplicates {name}")
        else:
            names.add(str(name))
        if status not in STAGE_STATUSES:
            errors.append(f"RunRecord.stages[{index}].status must be one of {sorted(STAGE_STATUSES)}")


def _validate_state_history(history: Any, errors: list[str]) -> None:
    if not isinstance(history, list):
        errors.append("RunRecord.state_history must be an array")
        return
    previous = ""
    previous_at: datetime | None = None
    for index, item in enumerate(history):
        if not isinstance(item, Mapping):
            errors.append(f"RunRecord.state_history[{index}] must be an object")
            continue
        from_state = str(item.get("from_state") or "")
        to_state = str(item.get("to_state") or "")
        reason = str(item.get("reason") or "")
        at_value = str(item.get("at") or "")
        at = _parse_history_at(at_value)
        if not reason:
            errors.append(f"RunRecord.state_history[{index}].reason is required")
        if not at_value:
            errors.append(f"RunRecord.state_history[{index}].at is required")
        elif at is None:
            errors.append(f"RunRecord.state_history[{index}].at must be an ISO timestamp")
        elif previous_at is not None and at < previous_at:
            errors.append(f"RunRecord.state_history[{index}].at must be non-decreasing")
        if index == 0:
            if from_state or to_state != "created":
                errors.append("RunRecord.state_history[0] must initialize to created")
        elif from_state != previous:
            errors.append(f"RunRecord.state_history[{index}].from_state must match previous to_state")
        elif previous and validate_transition(previous, to_state):
            errors.append(f"RunRecord.state_history[{index}] transition {previous} -> {to_state} is not allowed")
        previous = to_state
        if at is not None:
            previous_at = at


def _parse_history_at(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _initial_history_at(date: str, timezone_name: str) -> str:
    try:
        parsed = datetime.fromisoformat(date)
    except ValueError:
        return f"{date}T00:00:00"
    if parsed.tzinfo is not None:
        return parsed.isoformat()
    try:
        zone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        zone = timezone.utc
    return parsed.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=zone).isoformat()
