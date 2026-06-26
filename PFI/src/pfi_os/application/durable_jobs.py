from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from pfi_os.application.operational_store import DataDomain, JobRecord, OperationalStore, SourceRecord


PFI003_DURABLE_JOB_STORE_SCHEMA = "PFIOSPFI003DurableJobStoreV1"
PFI003_RUNTIME_SUPERVISOR_SCHEMA = "PFIOSPFI003RuntimeSupervisorContractV1"
PFI003_DURABLE_JOB_SOURCE_ID = "src-pfi003-durable-job-store"
PFI003_DURABLE_JOB_SOURCE_TYPE = "pfi003_durable_job_store"
PFI003_DURABLE_JOB_EVIDENCE_CLASS = "runtime_supervisor_job_lifecycle"

ACTIVE_JOB_STATUSES = {"queued", "retrying", "resumed", "running"}
CLAIMABLE_JOB_STATUSES = {"queued", "retrying", "resumed"}
TERMINAL_JOB_STATUSES = {"completed", "cancelled", "dead_letter"}


def build_pfi003_runtime_supervisor_contract() -> dict[str, Any]:
    return {
        "schema": PFI003_RUNTIME_SUPERVISOR_SCHEMA,
        "issue": "PFI-003",
        "job_store_schema": PFI003_DURABLE_JOB_STORE_SCHEMA,
        "storage": {
            "table": "job_records",
            "schema_migration": "non_destructive_metadata_contract",
            "new_tables": False,
        },
        "states": ["queued", "running", "completed", "retrying", "cancelled", "resumed", "dead_letter"],
        "idempotency": {
            "key_fields": ["job_type", "idempotency_key"],
            "duplicate_enqueue_behavior": "return_existing_job",
        },
        "claiming": {
            "atomic_claim": True,
            "sqlite_lock": "BEGIN IMMEDIATE",
            "lease_required": True,
            "heartbeat_required": True,
            "double_worker_behavior": "only_one_worker_receives_active_lease",
        },
        "recovery": {
            "expired_lease_requeue": True,
            "bounded_retry": True,
            "dead_letter_after_max_attempts": True,
            "cancel": True,
            "resume": True,
        },
        "readiness": {
            "web": "separate",
            "api": "separate",
            "worker": "separate",
        },
        "safety_boundary": {
            "research_only": True,
            "no_live_trading": True,
            "no_broker_calls": True,
            "no_order_execution": True,
            "no_payment_or_betting": True,
            "human_review_required": True,
            "private_data_commit_path": False,
        },
    }


class DurableJobStore:
    def __init__(self, store: OperationalStore | None = None, *, source_id: str = PFI003_DURABLE_JOB_SOURCE_ID):
        self.store = store or OperationalStore()
        self.source_id = source_id
        self.store.initialize()

    def enqueue(
        self,
        *,
        job_type: str,
        idempotency_key: str,
        payload: dict[str, Any] | None = None,
        as_of: str = "",
        max_attempts: int = 3,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        _require(job_type, "job_type")
        _require(idempotency_key, "idempotency_key")
        resolved_now = _as_utc(now)
        resolved_as_of = as_of or _iso(resolved_now)
        self._ensure_source(as_of=resolved_as_of, now=resolved_now)
        job_id = durable_job_id(job_type=job_type, idempotency_key=idempotency_key)
        existing = self.get(job_id)
        if existing:
            return _job_report(existing, queued=False, claimed=False)

        metadata = {
            "schema": PFI003_DURABLE_JOB_STORE_SCHEMA,
            "contract_schema": PFI003_RUNTIME_SUPERVISOR_SCHEMA,
            "idempotency_key": idempotency_key,
            "payload": _json_safe(payload or {}),
            "max_attempts": max(1, int(max_attempts)),
            "lease_owner": "",
            "lease_expires_at": "",
            "heartbeat_at": "",
            "claim_count": 0,
            "resume_count": 0,
            "cancel_requested": False,
            "dead_letter_reason": "",
            "safety_boundary": build_pfi003_runtime_supervisor_contract()["safety_boundary"],
            "event_log": [_event("queued", "enqueue", resolved_now, worker_id="")],
        }
        self.store.upsert_job(
            JobRecord(
                job_id=job_id,
                source_id=self.source_id,
                as_of=resolved_as_of,
                job_type=job_type,
                status="queued",
                phase="queued",
                progress=0.0,
                retry_count=0,
                metadata=metadata,
            )
        )
        return _job_report(self.get(job_id), queued=True, claimed=False)

    def claim(
        self,
        *,
        job_type: str,
        worker_id: str,
        lease_seconds: int = 60,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        _require(job_type, "job_type")
        _require(worker_id, "worker_id")
        resolved_now = _as_utc(now)
        lease_until = resolved_now + timedelta(seconds=max(1, int(lease_seconds)))
        with self._connect_immediate() as conn:
            self._recover_expired_leases(conn, now=resolved_now, job_type=job_type)
            row = conn.execute(
                """
                SELECT * FROM job_records
                WHERE job_type = ?
                  AND status IN ('queued', 'retrying', 'resumed')
                ORDER BY created_at, job_id
                LIMIT 1
                """,
                (job_type,),
            ).fetchone()
            if row is None:
                return {
                    "schema": PFI003_DURABLE_JOB_STORE_SCHEMA,
                    "claimed": False,
                    "status": "idle",
                    "job_type": job_type,
                    "worker_id": worker_id,
                    "safety_boundary": build_pfi003_runtime_supervisor_contract()["safety_boundary"],
                }
            current = _row_dict(row)
            metadata = _metadata(current)
            metadata.update(
                {
                    "lease_owner": worker_id,
                    "lease_expires_at": _iso(lease_until),
                    "heartbeat_at": _iso(resolved_now),
                    "claim_count": int(metadata.get("claim_count", 0) or 0) + 1,
                    "last_claimed_at": _iso(resolved_now),
                }
            )
            _append_event(metadata, _event("running", "claim", resolved_now, worker_id=worker_id))
            updated = _write_job(
                conn,
                current,
                status="running",
                phase="claimed",
                progress=max(float(current.get("progress", 0.0) or 0.0), 0.05),
                retry_count=int(current.get("retry_count", 0) or 0),
                error_message="",
                artifact_uri=str(current.get("artifact_uri", "")),
                metadata=metadata,
                now=resolved_now,
            )
            return _job_report(updated, queued=False, claimed=True)

    def heartbeat(
        self,
        job_id: str,
        *,
        worker_id: str,
        progress: float | None = None,
        phase: str | None = None,
        lease_seconds: int | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        _require(worker_id, "worker_id")
        resolved_now = _as_utc(now)
        with self._connect_immediate() as conn:
            current = self._locked_job(conn, job_id)
            metadata = _metadata(current)
            _require_lease_owner(metadata, worker_id, job_id)
            metadata["heartbeat_at"] = _iso(resolved_now)
            if lease_seconds is not None:
                metadata["lease_expires_at"] = _iso(resolved_now + timedelta(seconds=max(1, int(lease_seconds))))
            _append_event(metadata, _event("running", "heartbeat", resolved_now, worker_id=worker_id))
            updated = _write_job(
                conn,
                current,
                status="running",
                phase=phase or str(current.get("phase", "running")),
                progress=_clamp_progress(progress if progress is not None else float(current.get("progress", 0.0) or 0.0)),
                retry_count=int(current.get("retry_count", 0) or 0),
                error_message=str(current.get("error_message", "")),
                artifact_uri=str(current.get("artifact_uri", "")),
                metadata=metadata,
                now=resolved_now,
            )
            return _job_report(updated, queued=False, claimed=True)

    def complete(
        self,
        job_id: str,
        *,
        worker_id: str,
        artifact_uri: str = "",
        now: datetime | None = None,
    ) -> dict[str, Any]:
        _require(worker_id, "worker_id")
        resolved_now = _as_utc(now)
        with self._connect_immediate() as conn:
            current = self._locked_job(conn, job_id)
            metadata = _metadata(current)
            _require_lease_owner(metadata, worker_id, job_id)
            metadata.update(
                {
                    "lease_owner": "",
                    "lease_expires_at": "",
                    "heartbeat_at": _iso(resolved_now),
                    "completed_at": _iso(resolved_now),
                }
            )
            _append_event(metadata, _event("completed", "complete", resolved_now, worker_id=worker_id))
            updated = _write_job(
                conn,
                current,
                status="completed",
                phase="completed",
                progress=1.0,
                retry_count=int(current.get("retry_count", 0) or 0),
                error_message="",
                artifact_uri=artifact_uri or str(current.get("artifact_uri", "")),
                metadata=metadata,
                now=resolved_now,
            )
            return _job_report(updated, queued=False, claimed=False)

    def fail_or_retry(
        self,
        job_id: str,
        *,
        worker_id: str,
        error_message: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        _require(worker_id, "worker_id")
        _require(error_message, "error_message")
        resolved_now = _as_utc(now)
        with self._connect_immediate() as conn:
            current = self._locked_job(conn, job_id)
            metadata = _metadata(current)
            _require_lease_owner(metadata, worker_id, job_id)
            attempts = int(current.get("retry_count", 0) or 0) + 1
            max_attempts = _max_attempts(metadata)
            retryable = attempts < max_attempts
            status = "retrying" if retryable else "dead_letter"
            phase = "retry_scheduled" if retryable else "dead_letter"
            metadata.update(
                {
                    "lease_owner": "",
                    "lease_expires_at": "",
                    "heartbeat_at": _iso(resolved_now),
                    "last_error": error_message,
                    "last_failed_at": _iso(resolved_now),
                    "attempts_remaining": max(max_attempts - attempts, 0),
                }
            )
            if not retryable:
                metadata["dead_letter_reason"] = error_message
                metadata["dead_lettered_at"] = _iso(resolved_now)
            _append_event(metadata, _event(status, "fail_or_retry", resolved_now, worker_id=worker_id, detail=error_message))
            updated = _write_job(
                conn,
                current,
                status=status,
                phase=phase,
                progress=0.0,
                retry_count=attempts,
                error_message=error_message,
                artifact_uri=str(current.get("artifact_uri", "")),
                metadata=metadata,
                now=resolved_now,
            )
            return _job_report(updated, queued=retryable, claimed=False)

    def cancel(self, job_id: str, *, reason: str, now: datetime | None = None) -> dict[str, Any]:
        _require(reason, "reason")
        resolved_now = _as_utc(now)
        with self._connect_immediate() as conn:
            current = self._locked_job(conn, job_id)
            metadata = _metadata(current)
            metadata.update(
                {
                    "lease_owner": "",
                    "lease_expires_at": "",
                    "cancel_requested": True,
                    "cancel_reason": reason,
                    "cancelled_at": _iso(resolved_now),
                }
            )
            _append_event(metadata, _event("cancelled", "cancel", resolved_now, worker_id="", detail=reason))
            updated = _write_job(
                conn,
                current,
                status="cancelled",
                phase="cancelled",
                progress=float(current.get("progress", 0.0) or 0.0),
                retry_count=int(current.get("retry_count", 0) or 0),
                error_message=str(current.get("error_message", "")),
                artifact_uri=str(current.get("artifact_uri", "")),
                metadata=metadata,
                now=resolved_now,
            )
            return _job_report(updated, queued=False, claimed=False)

    def resume(self, job_id: str, *, reason: str, now: datetime | None = None) -> dict[str, Any]:
        _require(reason, "reason")
        resolved_now = _as_utc(now)
        with self._connect_immediate() as conn:
            current = self._locked_job(conn, job_id)
            metadata = _metadata(current)
            was_dead = str(current.get("status", "")).lower() in {"dead_letter", "failed"}
            metadata.update(
                {
                    "lease_owner": "",
                    "lease_expires_at": "",
                    "cancel_requested": False,
                    "resume_reason": reason,
                    "resumed_at": _iso(resolved_now),
                    "resume_count": int(metadata.get("resume_count", 0) or 0) + 1,
                }
            )
            _append_event(metadata, _event("queued", "resume", resolved_now, worker_id="", detail=reason))
            updated = _write_job(
                conn,
                current,
                status="queued",
                phase="resumed",
                progress=0.0,
                retry_count=0 if was_dead else int(current.get("retry_count", 0) or 0),
                error_message="",
                artifact_uri=str(current.get("artifact_uri", "")),
                metadata=metadata,
                now=resolved_now,
            )
            return _job_report(updated, queued=True, claimed=False)

    def recover_expired_leases(self, *, now: datetime | None = None, job_type: str = "") -> dict[str, Any]:
        resolved_now = _as_utc(now)
        with self._connect_immediate() as conn:
            recovered = self._recover_expired_leases(conn, now=resolved_now, job_type=job_type)
        return {
            "schema": PFI003_DURABLE_JOB_STORE_SCHEMA,
            "recovered": recovered,
            "recovered_count": len(recovered),
            "now": _iso(resolved_now),
        }

    def readiness(self, *, worker_id: str = "") -> dict[str, Any]:
        self.store.initialize()
        rows = self.store.table_rows("job_records")
        active = [row for row in rows if str(row.get("status", "")).lower() in ACTIVE_JOB_STATUSES]
        return {
            "schema": PFI003_RUNTIME_SUPERVISOR_SCHEMA,
            "web": {"ready": True, "surface": "PFI Web Shell"},
            "api": {"ready": True, "surface": "local OperationalStore API"},
            "worker": {"ready": bool(worker_id), "worker_id": worker_id, "active_jobs": len(active)},
            "job_store": {"ready": True, "db_path": str(self.store.db_path), "active_jobs": len(active)},
            "safety_boundary": build_pfi003_runtime_supervisor_contract()["safety_boundary"],
        }

    def get(self, job_id: str) -> dict[str, Any]:
        if not str(job_id or "").strip():
            return {}
        for row in self.store.table_rows("job_records"):
            if str(row.get("job_id", "")) == str(job_id):
                return row
        return {}

    def _ensure_source(self, *, as_of: str, now: datetime) -> None:
        self.store.upsert_source(
            SourceRecord(
                source_id=self.source_id,
                domain=DataDomain.PRIVATE_DERIVED,
                source_type=PFI003_DURABLE_JOB_SOURCE_TYPE,
                uri="operational_store:job_records",
                as_of=as_of,
                evidence_class=PFI003_DURABLE_JOB_EVIDENCE_CLASS,
                observed_at=_iso(now),
                title="PFI-003 durable job store",
                checksum=_stable_digest(PFI003_DURABLE_JOB_STORE_SCHEMA, self.source_id, as_of),
                metadata={
                    "schema": PFI003_DURABLE_JOB_STORE_SCHEMA,
                    "contract_schema": PFI003_RUNTIME_SUPERVISOR_SCHEMA,
                    "safety_boundary": build_pfi003_runtime_supervisor_contract()["safety_boundary"],
                },
            )
        )

    def _connect_immediate(self) -> sqlite3.Connection:
        self.store.initialize()
        conn = sqlite3.connect(self.store.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("BEGIN IMMEDIATE")
        return _ImmediateConnection(conn)

    @staticmethod
    def _locked_job(conn: sqlite3.Connection, job_id: str) -> dict[str, Any]:
        _require(job_id, "job_id")
        row = conn.execute("SELECT * FROM job_records WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(job_id)
        return _row_dict(row)

    @staticmethod
    def _recover_expired_leases(conn: sqlite3.Connection, *, now: datetime, job_type: str = "") -> list[dict[str, Any]]:
        query = "SELECT * FROM job_records WHERE status = 'running'"
        params: tuple[Any, ...] = ()
        if job_type:
            query += " AND job_type = ?"
            params = (job_type,)
        rows = [_row_dict(row) for row in conn.execute(query, params).fetchall()]
        recovered: list[dict[str, Any]] = []
        for row in rows:
            metadata = _metadata(row)
            expires_at = _parse_dt(str(metadata.get("lease_expires_at", "")))
            if expires_at is None or expires_at > now:
                continue
            attempts = int(row.get("retry_count", 0) or 0) + 1
            max_attempts = _max_attempts(metadata)
            retryable = attempts < max_attempts
            status = "retrying" if retryable else "dead_letter"
            phase = "lease_expired_requeued" if retryable else "dead_letter"
            detail = f"lease expired at {metadata.get('lease_expires_at', '')}"
            metadata.update(
                {
                    "lease_owner": "",
                    "lease_expires_at": "",
                    "last_error": detail,
                    "last_failed_at": _iso(now),
                    "attempts_remaining": max(max_attempts - attempts, 0),
                }
            )
            if not retryable:
                metadata["dead_letter_reason"] = detail
                metadata["dead_lettered_at"] = _iso(now)
            _append_event(metadata, _event(status, "recover_expired_lease", now, worker_id="", detail=detail))
            updated = _write_job(
                conn,
                row,
                status=status,
                phase=phase,
                progress=0.0,
                retry_count=attempts,
                error_message=detail,
                artifact_uri=str(row.get("artifact_uri", "")),
                metadata=metadata,
                now=now,
            )
            recovered.append(_job_report(updated, queued=retryable, claimed=False))
        return recovered


class _ImmediateConnection:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def __enter__(self) -> sqlite3.Connection:
        return self.conn

    def __exit__(self, exc_type, exc, traceback) -> None:
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()


def durable_job_id(*, job_type: str, idempotency_key: str) -> str:
    return f"durableJob_{_stable_digest(job_type, idempotency_key)}"


def _write_job(
    conn: sqlite3.Connection,
    current: dict[str, Any],
    *,
    status: str,
    phase: str,
    progress: float,
    retry_count: int,
    error_message: str,
    artifact_uri: str,
    metadata: dict[str, Any],
    now: datetime,
) -> dict[str, Any]:
    metadata_json = json.dumps(_json_safe(metadata), ensure_ascii=False, sort_keys=True)
    conn.execute(
        """
        UPDATE job_records
        SET status = ?,
            phase = ?,
            progress = ?,
            retry_count = ?,
            error_message = ?,
            artifact_uri = ?,
            metadata_json = ?,
            updated_at = ?
        WHERE job_id = ?
        """,
        (
            status,
            phase,
            _clamp_progress(progress),
            int(retry_count),
            error_message,
            artifact_uri,
            metadata_json,
            _iso(now),
            str(current.get("job_id", "")),
        ),
    )
    updated = {**current}
    updated.update(
        {
            "status": status,
            "phase": phase,
            "progress": _clamp_progress(progress),
            "retry_count": int(retry_count),
            "error_message": error_message,
            "artifact_uri": artifact_uri,
            "metadata_json": metadata_json,
            "updated_at": _iso(now),
        }
    )
    return updated


def _job_report(row: dict[str, Any], *, queued: bool, claimed: bool) -> dict[str, Any]:
    metadata = _metadata(row)
    return {
        "schema": PFI003_DURABLE_JOB_STORE_SCHEMA,
        "job_id": str(row.get("job_id", "")),
        "job_type": str(row.get("job_type", "")),
        "source_id": str(row.get("source_id", "")),
        "as_of": str(row.get("as_of", "")),
        "status": str(row.get("status", "")),
        "phase": str(row.get("phase", "")),
        "progress": float(row.get("progress", 0.0) or 0.0),
        "retry_count": int(row.get("retry_count", 0) or 0),
        "error_message": str(row.get("error_message", "")),
        "artifact_uri": str(row.get("artifact_uri", "")),
        "queued": queued,
        "claimed": claimed,
        "idempotency_key": str(metadata.get("idempotency_key", "")),
        "lease_owner": str(metadata.get("lease_owner", "")),
        "lease_expires_at": str(metadata.get("lease_expires_at", "")),
        "heartbeat_at": str(metadata.get("heartbeat_at", "")),
        "claim_count": int(metadata.get("claim_count", 0) or 0),
        "max_attempts": _max_attempts(metadata),
        "dead_letter_reason": str(metadata.get("dead_letter_reason", "")),
        "safety_boundary": metadata.get("safety_boundary", build_pfi003_runtime_supervisor_contract()["safety_boundary"]),
    }


def _metadata(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("metadata_json", "{}")
    if isinstance(value, dict):
        return dict(value)
    try:
        parsed = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _row_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def _event(status: str, action: str, now: datetime, *, worker_id: str, detail: str = "") -> dict[str, Any]:
    return {
        "at": _iso(now),
        "status": status,
        "action": action,
        "worker_id": worker_id,
        "detail": detail,
    }


def _append_event(metadata: dict[str, Any], event: dict[str, Any]) -> None:
    events = metadata.get("event_log", [])
    if not isinstance(events, list):
        events = []
    events.append(event)
    metadata["event_log"] = events[-20:]


def _require_lease_owner(metadata: dict[str, Any], worker_id: str, job_id: str) -> None:
    if str(metadata.get("lease_owner", "")) != worker_id:
        raise PermissionError(f"worker {worker_id} does not own lease for job {job_id}")


def _max_attempts(metadata: dict[str, Any]) -> int:
    try:
        return max(1, int(metadata.get("max_attempts", 3) or 3))
    except (TypeError, ValueError):
        return 3


def _clamp_progress(value: float) -> float:
    return min(max(float(value), 0.0), 1.0)


def _as_utc(value: datetime | None) -> datetime:
    resolved = value or datetime.now(timezone.utc)
    if resolved.tzinfo is None:
        return resolved.replace(tzinfo=timezone.utc)
    return resolved.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return _as_utc(value).isoformat(timespec="seconds")


def _parse_dt(value: str) -> datetime | None:
    clean = str(value or "").strip()
    if not clean:
        return None
    try:
        parsed = datetime.fromisoformat(clean.replace("Z", "+00:00"))
    except ValueError:
        return None
    return _as_utc(parsed)


def _stable_digest(*parts: Any) -> str:
    raw = json.dumps(_json_safe(parts), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


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


def _require(value: str, field_name: str) -> None:
    if not str(value or "").strip():
        raise ValueError(f"{field_name} is required")
