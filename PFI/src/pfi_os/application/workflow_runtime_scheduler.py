from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pfi_os.application.operational_store import (
    DataDomain,
    JobRecord,
    OperationalStore,
    SourceRecord,
)
from pfi_os.application.workflow_runtime_read_model import (
    FAST_PATH_TARGET_SECONDS,
    WORKFLOW_RUNTIME_READ_MODEL_SCHEMA,
    build_workflow_runtime_read_model,
    record_workflow_runtime_read_model,
)


WORKFLOW_RUNTIME_SCHEDULER_SCHEMA = "PFIOSPhaseCWorkflowRuntimeSchedulerV1"
WORKFLOW_RUNTIME_SCHEDULER_RUN_SCHEMA = "PFIOSPhaseCWorkflowRuntimeSchedulerRunV1"
WORKFLOW_RUNTIME_SCHEDULER_SOURCE_ID = "src-phase-c-workflow-runtime-scheduler"
WORKFLOW_RUNTIME_REFRESH_JOB_TYPE = "phase_c_workflow_runtime_refresh"
WORKFLOW_RUNTIME_SCHEDULER_EVIDENCE_CLASS = "workflow_runtime_scheduler"
WORKFLOW_RUNTIME_CACHE_ARTIFACT_URI = "operational_store:workflow_runtime_read_model:latest"

WorkflowRuntimeBuilder = Callable[[OperationalStore, datetime | None, int], dict[str, Any]]


def build_phase_c_workflow_runtime_scheduler_contract() -> dict[str, Any]:
    retry_policy = _retry_policy()
    return {
        "schema": WORKFLOW_RUNTIME_SCHEDULER_SCHEMA,
        "phase": "Phase C",
        "job_type": WORKFLOW_RUNTIME_REFRESH_JOB_TYPE,
        "read_model_schema": WORKFLOW_RUNTIME_READ_MODEL_SCHEMA,
        "target_seconds": FAST_PATH_TARGET_SECONDS,
        "retry_policy": retry_policy,
        "idempotency": {
            "job_id_fields": ["scheduler_source_id", "as_of", "job_type", "read_model_schema"],
            "duplicate_schedule_behavior": "return_existing_job",
        },
        "writes": {
            "source_records": True,
            "job_records": True,
            "workflow_runtime_evidence": True,
            "review_task": True,
            "new_tables": False,
        },
        "external_dependencies": {
            "provider_fetch_required": False,
            "broker_required": False,
            "llm_required": False,
            "network_required": False,
        },
        "safety_boundary": _safety_boundary(),
    }


def schedule_workflow_runtime_refresh(
    store: OperationalStore,
    *,
    as_of: str = "",
    now: datetime | None = None,
    source_id: str = WORKFLOW_RUNTIME_SCHEDULER_SOURCE_ID,
    target_seconds: int = FAST_PATH_TARGET_SECONDS,
) -> dict[str, Any]:
    operational_store = store
    operational_store.initialize()
    resolved_as_of = as_of or (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")
    _ensure_scheduler_source(operational_store, source_id=source_id, as_of=resolved_as_of)
    job_id = _scheduler_job_id(source_id=source_id, as_of=resolved_as_of)
    existing = _job_row(operational_store, job_id)
    if existing:
        return _schedule_report(existing, target_seconds=target_seconds, queued=False)

    metadata = {
        "schema": WORKFLOW_RUNTIME_SCHEDULER_RUN_SCHEMA,
        "contract_schema": WORKFLOW_RUNTIME_SCHEDULER_SCHEMA,
        "target_seconds": int(target_seconds),
        "retry_policy": _retry_policy(),
        "idempotency_key": _idempotency_key(source_id=source_id, as_of=resolved_as_of),
        "safety_boundary": _safety_boundary(),
    }
    operational_store.upsert_job(
        JobRecord(
            job_id=job_id,
            source_id=source_id,
            as_of=resolved_as_of,
            job_type=WORKFLOW_RUNTIME_REFRESH_JOB_TYPE,
            status="queued",
            phase="queued",
            progress=0.0,
            retry_count=0,
            artifact_uri=WORKFLOW_RUNTIME_CACHE_ARTIFACT_URI,
            metadata=metadata,
        )
    )
    return _schedule_report(_job_row(operational_store, job_id), target_seconds=target_seconds, queued=True)


def execute_workflow_runtime_refresh_job(
    store: OperationalStore,
    job_id: str,
    *,
    now: datetime | None = None,
    target_seconds: int = FAST_PATH_TARGET_SECONDS,
    builder: WorkflowRuntimeBuilder | None = None,
) -> dict[str, Any]:
    operational_store = store
    operational_store.initialize()
    current = _job_row(operational_store, job_id)
    if not current:
        raise KeyError(job_id)
    if str(current.get("job_type", "")) != WORKFLOW_RUNTIME_REFRESH_JOB_TYPE:
        raise ValueError(f"job {job_id} is not a Phase C workflow runtime refresh job")
    if str(current.get("status", "")).lower() == "completed":
        return _completed_report(current, target_seconds=target_seconds, already_completed=True)
    if str(current.get("status", "")).lower() in {"failed", "blocked"} and int(
        current.get("retry_count", 0) or 0
    ) >= int(_retry_policy()["max_attempts"]):
        return _failed_report(current, target_seconds=target_seconds)

    started = time.perf_counter()
    metadata = _metadata_dict(current)
    attempt_number = int(current.get("retry_count", 0) or 0) + 1
    _upsert_scheduler_job(
        operational_store,
        current,
        status="running",
        phase="cache_refresh_started",
        progress=0.2,
        retry_count=int(current.get("retry_count", 0) or 0),
        error_message="",
        metadata={**metadata, "attempt_number": attempt_number, "started_at": _iso_now(now)},
    )

    try:
        payload = _build_runtime_payload(operational_store, now=now, target_seconds=target_seconds, builder=builder)
        ids = record_workflow_runtime_read_model(
            operational_store,
            payload,
            as_of=str(payload.get("generated_at", "")),
            artifact_uri=WORKFLOW_RUNTIME_CACHE_ARTIFACT_URI,
        )
        elapsed_seconds = round(max(0.0, time.perf_counter() - started), 4)
        within_target = elapsed_seconds <= int(target_seconds) and int(
            payload.get("fast_path", {}).get("estimated_seconds", 0) or 0
        ) <= int(target_seconds)
        completed_metadata = {
            **metadata,
            "attempt_number": attempt_number,
            "runtime_ids": ids,
            "runtime_schema": payload.get("schema", ""),
            "fast_path": payload.get("fast_path", {}),
            "elapsed_seconds": elapsed_seconds,
            "within_target_seconds": within_target,
            "completed_at": _iso_now(now),
        }
        _upsert_scheduler_job(
            operational_store,
            current,
            status="completed",
            phase="cache_refreshed",
            progress=1.0,
            retry_count=int(current.get("retry_count", 0) or 0),
            error_message="",
            metadata=completed_metadata,
        )
        return {
            "schema": WORKFLOW_RUNTIME_SCHEDULER_RUN_SCHEMA,
            "status": "completed",
            "job_id": job_id,
            "source_id": str(current.get("source_id", "")),
            "as_of": str(current.get("as_of", "")),
            "attempt_number": attempt_number,
            "target_seconds": int(target_seconds),
            "elapsed_seconds": elapsed_seconds,
            "within_target_seconds": within_target,
            "runtime_ids": ids,
            "fast_path": payload.get("fast_path", {}),
            "retry_policy": _retry_policy(),
            "safety_boundary": _safety_boundary(),
        }
    except Exception as error:
        return _record_retry_or_failure(
            operational_store,
            current,
            error_message=str(error),
            attempt_number=attempt_number,
            target_seconds=target_seconds,
            now=now,
        )


def refresh_workflow_runtime_cache(
    store: OperationalStore,
    *,
    as_of: str = "",
    now: datetime | None = None,
    target_seconds: int = FAST_PATH_TARGET_SECONDS,
    builder: WorkflowRuntimeBuilder | None = None,
) -> dict[str, Any]:
    scheduled = schedule_workflow_runtime_refresh(store, as_of=as_of, now=now, target_seconds=target_seconds)
    return execute_workflow_runtime_refresh_job(
        store,
        str(scheduled["job_id"]),
        now=now,
        target_seconds=target_seconds,
        builder=builder,
    )


def _ensure_scheduler_source(store: OperationalStore, *, source_id: str, as_of: str) -> None:
    store.upsert_source(
        SourceRecord(
            source_id=source_id,
            domain=DataDomain.PRIVATE_DERIVED,
            source_type="phase_c_workflow_runtime_scheduler",
            uri="operational_store:workflow_runtime_scheduler",
            as_of=as_of,
            evidence_class=WORKFLOW_RUNTIME_SCHEDULER_EVIDENCE_CLASS,
            title="Phase C workflow runtime scheduler",
            checksum=_stable_id(WORKFLOW_RUNTIME_SCHEDULER_SCHEMA, source_id, as_of),
            metadata={
                "schema": WORKFLOW_RUNTIME_SCHEDULER_SCHEMA,
                "target_seconds": FAST_PATH_TARGET_SECONDS,
                "safety_boundary": _safety_boundary(),
            },
        )
    )


def _build_runtime_payload(
    store: OperationalStore,
    *,
    now: datetime | None,
    target_seconds: int,
    builder: WorkflowRuntimeBuilder | None,
) -> dict[str, Any]:
    payload = (
        builder(store, now, int(target_seconds))
        if builder
        else build_workflow_runtime_read_model(
            store,
            now=now,
            fast_path_target_seconds=target_seconds,
        )
    )
    if payload.get("schema") != WORKFLOW_RUNTIME_READ_MODEL_SCHEMA:
        raise ValueError(f"workflow runtime payload schema must be {WORKFLOW_RUNTIME_READ_MODEL_SCHEMA}")
    return payload


def _record_retry_or_failure(
    store: OperationalStore,
    current: dict[str, Any],
    *,
    error_message: str,
    attempt_number: int,
    target_seconds: int,
    now: datetime | None,
) -> dict[str, Any]:
    retry_policy = _retry_policy()
    max_attempts = int(retry_policy["max_attempts"])
    retry_count = attempt_number
    retryable = retry_count < max_attempts
    next_retry_after_seconds = retry_policy["backoff_seconds"][retry_count - 1] if retryable else None
    status = "queued" if retryable else "failed"
    phase = "retry_scheduled" if retryable else "fail_closed"
    metadata = {
        **_metadata_dict(current),
        "attempt_number": attempt_number,
        "retryable": retryable,
        "attempts_remaining": max(max_attempts - retry_count, 0),
        "next_retry_after_seconds": next_retry_after_seconds,
        "last_error": error_message,
        "failed_at": _iso_now(now),
        "fail_closed_review_required": True,
    }
    _upsert_scheduler_job(
        store,
        current,
        status=status,
        phase=phase,
        progress=0.0,
        retry_count=retry_count,
        error_message=error_message,
        metadata=metadata,
    )
    return {
        "schema": WORKFLOW_RUNTIME_SCHEDULER_RUN_SCHEMA,
        "status": status,
        "phase": phase,
        "job_id": str(current.get("job_id", "")),
        "source_id": str(current.get("source_id", "")),
        "as_of": str(current.get("as_of", "")),
        "attempt_number": attempt_number,
        "target_seconds": int(target_seconds),
        "retry_count": retry_count,
        "next_retry_after_seconds": next_retry_after_seconds,
        "error_message": error_message,
        "retry_policy": retry_policy,
        "safety_boundary": _safety_boundary(),
    }


def _upsert_scheduler_job(
    store: OperationalStore,
    current: dict[str, Any],
    *,
    status: str,
    phase: str,
    progress: float,
    retry_count: int,
    error_message: str,
    metadata: dict[str, Any],
) -> None:
    store.upsert_job(
        JobRecord(
            job_id=str(current.get("job_id", "")),
            source_id=str(current.get("source_id", "")),
            as_of=str(current.get("as_of", "")),
            job_type=WORKFLOW_RUNTIME_REFRESH_JOB_TYPE,
            status=status,
            phase=phase,
            progress=progress,
            retry_count=retry_count,
            error_message=error_message,
            artifact_uri=str(current.get("artifact_uri", "")) or WORKFLOW_RUNTIME_CACHE_ARTIFACT_URI,
            metadata=metadata,
        )
    )


def _schedule_report(row: dict[str, Any], *, target_seconds: int, queued: bool) -> dict[str, Any]:
    metadata = _metadata_dict(row)
    return {
        "schema": WORKFLOW_RUNTIME_SCHEDULER_RUN_SCHEMA,
        "status": str(row.get("status", "")),
        "phase": str(row.get("phase", "")),
        "job_id": str(row.get("job_id", "")),
        "source_id": str(row.get("source_id", "")),
        "as_of": str(row.get("as_of", "")),
        "queued": queued,
        "target_seconds": int(target_seconds),
        "retry_policy": metadata.get("retry_policy", _retry_policy()),
        "idempotency_key": metadata.get("idempotency_key", ""),
        "safety_boundary": metadata.get("safety_boundary", _safety_boundary()),
    }


def _completed_report(row: dict[str, Any], *, target_seconds: int, already_completed: bool) -> dict[str, Any]:
    metadata = _metadata_dict(row)
    return {
        "schema": WORKFLOW_RUNTIME_SCHEDULER_RUN_SCHEMA,
        "status": "completed",
        "phase": str(row.get("phase", "")),
        "job_id": str(row.get("job_id", "")),
        "source_id": str(row.get("source_id", "")),
        "as_of": str(row.get("as_of", "")),
        "already_completed": already_completed,
        "target_seconds": int(target_seconds),
        "elapsed_seconds": metadata.get("elapsed_seconds", 0),
        "within_target_seconds": metadata.get("within_target_seconds", False),
        "runtime_ids": metadata.get("runtime_ids", {}),
        "fast_path": metadata.get("fast_path", {}),
        "retry_policy": metadata.get("retry_policy", _retry_policy()),
        "safety_boundary": metadata.get("safety_boundary", _safety_boundary()),
    }


def _failed_report(row: dict[str, Any], *, target_seconds: int) -> dict[str, Any]:
    metadata = _metadata_dict(row)
    return {
        "schema": WORKFLOW_RUNTIME_SCHEDULER_RUN_SCHEMA,
        "status": str(row.get("status", "")),
        "phase": str(row.get("phase", "")),
        "job_id": str(row.get("job_id", "")),
        "source_id": str(row.get("source_id", "")),
        "as_of": str(row.get("as_of", "")),
        "attempt_number": int(row.get("retry_count", 0) or 0),
        "target_seconds": int(target_seconds),
        "retry_count": int(row.get("retry_count", 0) or 0),
        "next_retry_after_seconds": None,
        "error_message": str(row.get("error_message", "")),
        "retry_policy": metadata.get("retry_policy", _retry_policy()),
        "safety_boundary": metadata.get("safety_boundary", _safety_boundary()),
    }


def _job_row(store: OperationalStore, job_id: str) -> dict[str, Any]:
    for row in store.table_rows("job_records"):
        if str(row.get("job_id", "")) == str(job_id):
            return row
    return {}


def _metadata_dict(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("metadata_json", "{}")
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _scheduler_job_id(*, source_id: str, as_of: str) -> str:
    digest = _stable_id(
        source_id,
        as_of,
        WORKFLOW_RUNTIME_REFRESH_JOB_TYPE,
        WORKFLOW_RUNTIME_READ_MODEL_SCHEMA,
    )
    return f"job-phase-c-runtime-refresh-{digest}"


def _idempotency_key(*, source_id: str, as_of: str) -> str:
    return _stable_id(
        "idempotency",
        source_id,
        as_of,
        WORKFLOW_RUNTIME_REFRESH_JOB_TYPE,
        WORKFLOW_RUNTIME_READ_MODEL_SCHEMA,
    )


def _stable_id(*parts: Any) -> str:
    payload = json.dumps(_json_safe(parts), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _retry_policy() -> dict[str, Any]:
    return {
        "max_attempts": 3,
        "backoff_seconds": [1, 5, 15],
        "fail_closed": True,
        "retryable_statuses": ["queued", "running", "error"],
    }


def _safety_boundary() -> dict[str, bool]:
    return {
        "research_only": True,
        "no_live_trading": True,
        "no_broker_calls": True,
        "no_order_execution": True,
        "no_holding_mutation": True,
        "human_review_required": True,
    }


def _iso_now(value: datetime | None) -> str:
    return (value or datetime.now(timezone.utc)).isoformat(timespec="seconds")
