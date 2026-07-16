from __future__ import annotations

import queue
import re
import threading
from time import monotonic
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pfi_os.application.jobs import JobLifecycleError, LeaseConflictError, StaleRevisionError
from pfi_os.infrastructure.jobs import SQLiteDurableJobStore
from pfi_os.observability import redact_log_text


RUNTIME_JOB_SUPERVISOR_SCHEMA = "PFIV025RuntimeJobSupervisorV1"
CACHE_REFRESH_JOB_TYPE = "cache.refresh"
CACHE_REFRESH_TOTAL_UNITS = 3
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_TERMINAL = {"succeeded", "failed", "cancelled", "dead_letter"}
_POLICY_HASH_FIELDS = (
    "data_hash",
    "formula_hash",
    "parameter_hash",
    "read_model_hash",
    "streamlit_cache_key",
)


class RuntimeJobSupervisor:
    """Run cache refreshes through the durable SQLite lifecycle.

    The supervisor never persists financial values. Its job payload contains
    only release/dependency hashes and boolean safety assertions. Background
    threads are process-local executors; lifecycle truth remains in SQLite and
    can be recovered by a new supervisor after a process restart.
    """

    def __init__(
        self,
        db_path: Path | str,
        *,
        cache_policy_builder: Callable[[], Mapping[str, Any]],
        backup_dir: Path | str | None = None,
        worker_id: str = "pfi-runtime-cache-worker",
        lease_seconds: int = 5,
        timeout_seconds: float = 30.0,
        auto_start: bool = True,
        store: SQLiteDurableJobStore | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not callable(cache_policy_builder):
            raise TypeError("cache_policy_builder must be callable")
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)):
            raise TypeError("timeout_seconds must be numeric")
        if timeout_seconds <= 0 or timeout_seconds > 300:
            raise ValueError("timeout_seconds must be between 0 and 300")
        if isinstance(lease_seconds, bool) or not isinstance(lease_seconds, int):
            raise TypeError("lease_seconds must be an integer")
        if lease_seconds < 1 or lease_seconds > 3600:
            raise ValueError("lease_seconds must be between 1 and 3600")
        self.store = store or SQLiteDurableJobStore(db_path, backup_dir=backup_dir)
        self._cache_policy_builder = cache_policy_builder
        self._worker_id = worker_id
        self._lease_seconds = lease_seconds
        self._heartbeat_interval_seconds = max(
            0.1,
            min(float(lease_seconds) / 3.0, 1.0),
        )
        self._timeout_seconds = float(timeout_seconds)
        self._auto_start = bool(auto_start)
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._stop = threading.Event()
        self._thread_lock = threading.Lock()
        self._threads: dict[str, threading.Thread] = {}

    def submit_cache_refresh(self, *, request_id: str) -> dict[str, Any]:
        normalized_request_id = str(request_id or "").strip()
        if not _REQUEST_ID_PATTERN.fullmatch(normalized_request_id):
            raise ValueError("request_id must be a stable local request identifier")

        preflight_policy: dict[str, Any]
        preflight_error = ""
        try:
            preflight_policy = self._safe_policy_projection(
                self._call_with_timeout(self._cache_policy_builder)
            )
        except TimeoutError:
            preflight_policy = self._empty_policy_projection()
            preflight_error = "LOCAL_TIMEOUT"
        except Exception:
            preflight_policy = self._empty_policy_projection()
            preflight_error = "CACHE_POLICY_UNAVAILABLE"

        context = {
            "source_hash": preflight_policy["dependency_registry_sha256"],
            "data_hash": preflight_policy["data_hash"],
            "formula_hash": preflight_policy["formula_hash"],
            "parameter_hash": preflight_policy["parameter_hash"],
            "read_model_hash": preflight_policy["read_model_hash"],
            "cache_key": preflight_policy["streamlit_cache_key"],
            "impact_scope": ["cache.frontend", "cache.streamlit", "metrics.read_model"],
            "cache_fallback_used": bool(preflight_error),
            "external_network_calls": 0,
        }
        enqueued = self.store.enqueue(
            job_type=CACHE_REFRESH_JOB_TYPE,
            idempotency_key=normalized_request_id,
            payload={
                "preflight_policy": preflight_policy,
                "preflight_error": preflight_error,
                "offline_only": True,
            },
            max_attempts=3,
            contains_financial_facts=False,
            observability_context=context,
            now=self._clock(),
        )
        job = enqueued["job"]
        if self._auto_start and str(job["status"]) not in _TERMINAL:
            self._schedule(str(job["job_id"]))
        return {
            "schema": RUNTIME_JOB_SUPERVISOR_SCHEMA,
            "created": bool(enqueued["created"]),
            "job": self.get(str(job["job_id"]))["job"],
            "poll_uri": f"/api/jobs/{job['job_id']}",
            "external_network_calls": 0,
        }

    def get(self, job_id: str) -> dict[str, Any]:
        projection = self.store.get_observability(job_id)
        return {
            "schema": RUNTIME_JOB_SUPERVISOR_SCHEMA,
            "job": projection["job"],
            "events": projection["events"],
            "logs": projection["logs"],
            "external_network_calls": 0,
        }

    def list(self, *, status: str = "", limit: int = 50) -> dict[str, Any]:
        jobs = self.store.list_jobs(status=status, limit=limit)
        return {
            "schema": RUNTIME_JOB_SUPERVISOR_SCHEMA,
            "jobs": jobs,
            "job_count": len(jobs),
            "external_network_calls": 0,
        }

    def cancel(self, job_id: str, *, expected_revision: int, reason: str) -> dict[str, Any]:
        job = self.store.cancel(
            job_id,
            expected_revision=expected_revision,
            reason=reason,
        )
        return {
            "schema": RUNTIME_JOB_SUPERVISOR_SCHEMA,
            "job": job,
            "external_network_calls": 0,
        }

    def recover_and_resume(self, *, now: datetime | None = None) -> dict[str, Any]:
        recovery = self.store.recover_expired_leases(
            job_type=CACHE_REFRESH_JOB_TYPE,
            now=now,
        )
        resumable = self.store.list_jobs(limit=500)
        resumable_job_ids: list[str] = []
        scheduled: list[str] = []
        for job in resumable:
            if str(job["job_type"]) != CACHE_REFRESH_JOB_TYPE:
                continue
            if str(job["status"]) not in {"queued", "retrying"}:
                continue
            job_id = str(job["job_id"])
            resumable_job_ids.append(job_id)
            if self._auto_start:
                self._schedule(job_id)
                scheduled.append(job_id)
        return {
            "schema": RUNTIME_JOB_SUPERVISOR_SCHEMA,
            "recovered_count": int(recovery["recovered_count"]),
            "recovered_job_ids": [str(job["job_id"]) for job in recovery["jobs"]],
            "resumable_job_ids": resumable_job_ids,
            "scheduled_job_ids": scheduled,
            "external_network_calls": 0,
        }

    def run_pending_once(self, *, now: datetime | None = None) -> dict[str, Any] | None:
        claim = self.store.claim(
            job_type=CACHE_REFRESH_JOB_TYPE,
            worker_id=self._worker_id,
            lease_seconds=self._lease_seconds,
            now=now or self._clock(),
        )
        if not claim["claimed"]:
            return None
        return self._execute_claim(claim)

    def shutdown(self) -> None:
        self._stop.set()

    def _schedule(self, job_id: str) -> None:
        with self._thread_lock:
            existing = self._threads.get(job_id)
            if existing is not None and existing.is_alive():
                return
            thread = threading.Thread(
                target=self._background_run,
                args=(job_id,),
                name=f"pfi-runtime-job-{job_id[-12:]}",
                daemon=True,
            )
            self._threads[job_id] = thread
            thread.start()

    def _background_run(self, scheduled_job_id: str) -> None:
        reschedule = False
        try:
            if self._stop.is_set():
                return
            result = self.run_pending_once()
            if result is None:
                return
            claimed_id = str(result.get("job_id") or "")
            if claimed_id and claimed_id != scheduled_job_id:
                pending = self.store.get(scheduled_job_id)
                if str(pending["status"]) in {"queued", "retrying"}:
                    reschedule = True
        finally:
            with self._thread_lock:
                current = self._threads.get(scheduled_job_id)
                if current is threading.current_thread():
                    self._threads.pop(scheduled_job_id, None)
            if reschedule and not self._stop.is_set():
                self._schedule(scheduled_job_id)

    def _execute_claim(self, claim: Mapping[str, Any]) -> dict[str, Any]:
        job = dict(claim["job"])
        job_id = str(job["job_id"])
        lease = dict(claim["lease"])
        lease_token = str(lease["token"])
        revision = int(job["revision"])
        lease_revision = [revision]
        try:
            raw_policy = self._call_with_lease_heartbeats(
                self._cache_policy_builder,
                job_id=job_id,
                lease_token=lease_token,
                revision_state=lease_revision,
            )
            revision = lease_revision[0]
            policy = self._safe_policy_projection(raw_policy)
            self._validate_policy(policy)
            if int(job["progress"]["completed_units"]) < 1:
                job = self.store.record_progress(
                    job_id,
                    worker_id=self._worker_id,
                    lease_token=lease_token,
                    expected_revision=revision,
                    completed_units=1,
                    total_units=CACHE_REFRESH_TOTAL_UNITS,
                    step="cache.dependency_snapshot",
                    now=self._clock(),
                )
                revision = int(job["revision"])
                lease_revision[0] = revision
            preflight = claim.get("payload", {}).get("preflight_policy", {})
            if not isinstance(preflight, Mapping):
                raise JobLifecycleError("preflight cache policy is invalid")
            identity_changed = any(
                str(preflight.get(field) or "") != str(policy.get(field) or "")
                for field in _POLICY_HASH_FIELDS
            )
            if int(job["progress"]["completed_units"]) < 2:
                job = self.store.record_progress(
                    job_id,
                    worker_id=self._worker_id,
                    lease_token=lease_token,
                    expected_revision=revision,
                    completed_units=2,
                    total_units=CACHE_REFRESH_TOTAL_UNITS,
                    step=(
                        "cache.identity_changed_narrow_refresh"
                        if identity_changed
                        else "cache.identity_unchanged_no_recompute"
                    ),
                    now=self._clock(),
                )
                revision = int(job["revision"])
                lease_revision[0] = revision
            if int(job["progress"]["completed_units"]) < 3:
                job = self.store.record_progress(
                    job_id,
                    worker_id=self._worker_id,
                    lease_token=lease_token,
                    expected_revision=revision,
                    completed_units=3,
                    total_units=CACHE_REFRESH_TOTAL_UNITS,
                    step="cache.runtime_ready",
                    now=self._clock(),
                )
                revision = int(job["revision"])
                lease_revision[0] = revision
            job = self.store.succeed(
                job_id,
                worker_id=self._worker_id,
                lease_token=lease_token,
                expected_revision=revision,
                result_uri=f"artifact://runtime-cache/{policy['streamlit_cache_key']}",
                now=self._clock(),
            )
            return {"job_id": job_id, "status": str(job["status"]), "job": job}
        except TimeoutError:
            return self._persist_failure(
                job_id,
                lease_token=lease_token,
                revision=lease_revision[0],
                error_code="LOCAL_TIMEOUT",
                message="local cache refresh exceeded its bounded timeout",
            )
        except (LeaseConflictError, StaleRevisionError):
            current = self.store.get(job_id)
            return {"job_id": job_id, "status": str(current["status"]), "job": current}
        except Exception:
            return self._persist_failure(
                job_id,
                lease_token=lease_token,
                revision=lease_revision[0],
                error_code="CACHE_REFRESH_ERROR",
                message="local cache refresh failed validation",
            )

    def _persist_failure(
        self,
        job_id: str,
        *,
        lease_token: str,
        revision: int,
        error_code: str,
        message: str,
    ) -> dict[str, Any]:
        try:
            job = self.store.fail(
                job_id,
                worker_id=self._worker_id,
                lease_token=lease_token,
                expected_revision=revision,
                error_code=error_code,
                error_message=redact_log_text(message),
                retryable=False,
                now=self._clock(),
            )
        except (LeaseConflictError, StaleRevisionError):
            job = self.store.get(job_id)
        return {"job_id": job_id, "status": str(job["status"]), "job": job}

    @staticmethod
    def _callback_queue(
        callback: Callable[[], Mapping[str, Any]],
    ) -> queue.Queue[tuple[bool, object]]:
        results: queue.Queue[tuple[bool, object]] = queue.Queue(maxsize=1)

        def invoke() -> None:
            try:
                results.put((True, callback()))
            except BaseException as exc:  # noqa: BLE001 - transported without persistence
                results.put((False, exc))

        thread = threading.Thread(target=invoke, name="pfi-cache-policy-build", daemon=True)
        thread.start()
        return results

    @staticmethod
    def _unwrap_callback_result(succeeded: bool, value: object) -> Mapping[str, Any]:
        if not succeeded:
            assert isinstance(value, BaseException)
            raise value
        if not isinstance(value, Mapping):
            raise JobLifecycleError("cache policy builder must return an object")
        return value

    def _call_with_timeout(self, callback: Callable[[], Mapping[str, Any]]) -> Mapping[str, Any]:
        results = self._callback_queue(callback)
        try:
            succeeded, value = results.get(timeout=self._timeout_seconds)
        except queue.Empty as exc:
            raise TimeoutError("local cache policy build timed out") from exc
        return self._unwrap_callback_result(succeeded, value)

    def _call_with_lease_heartbeats(
        self,
        callback: Callable[[], Mapping[str, Any]],
        *,
        job_id: str,
        lease_token: str,
        revision_state: list[int],
    ) -> Mapping[str, Any]:
        """Keep a healthy long-running worker leased while local work executes."""

        results = self._callback_queue(callback)
        deadline = monotonic() + self._timeout_seconds
        while True:
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise TimeoutError("local cache policy build timed out")
            try:
                succeeded, value = results.get(
                    timeout=min(self._heartbeat_interval_seconds, remaining)
                )
            except queue.Empty as exc:
                if monotonic() >= deadline:
                    raise TimeoutError("local cache policy build timed out") from exc
                heartbeat = self.store.heartbeat(
                    job_id,
                    worker_id=self._worker_id,
                    lease_token=lease_token,
                    expected_revision=revision_state[0],
                    lease_seconds=self._lease_seconds,
                    now=self._clock(),
                )
                revision_state[0] = int(heartbeat["revision"])
                continue
            return self._unwrap_callback_result(succeeded, value)

    @staticmethod
    def _empty_policy_projection() -> dict[str, Any]:
        return {
            "dependency_registry_sha256": "not_loaded",
            "data_hash": "not_loaded",
            "formula_hash": "not_loaded",
            "parameter_hash": "not_loaded",
            "read_model_hash": "not_loaded",
            "streamlit_cache_key": "not_loaded",
            "dependency_snapshot_valid": False,
            "ordinary_run_network_allowed": False,
            "no_diff_network_allowed": False,
            "external_network_calls": 0,
        }

    @staticmethod
    def _external_network_calls(policy: Mapping[str, Any]) -> int:
        value = policy.get("external_network_calls", 0)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise JobLifecycleError("cache policy external network count is invalid")
        return value

    @classmethod
    def _safe_policy_projection(cls, policy: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(policy, Mapping):
            raise JobLifecycleError("cache policy must be an object")
        return {
            "dependency_registry_sha256": str(
                policy.get("dependency_registry_sha256") or "not_loaded"
            ),
            "data_hash": str(policy.get("data_hash") or "not_loaded"),
            "formula_hash": str(policy.get("formula_hash") or "not_loaded"),
            "parameter_hash": str(policy.get("parameter_hash") or "not_loaded"),
            "read_model_hash": str(policy.get("read_model_hash") or "not_loaded"),
            "streamlit_cache_key": str(policy.get("streamlit_cache_key") or "not_loaded"),
            "dependency_snapshot_valid": bool(policy.get("dependency_snapshot_valid")),
            "ordinary_run_network_allowed": bool(policy.get("ordinary_run_network_allowed")),
            "no_diff_network_allowed": bool(policy.get("no_diff_network_allowed")),
            "external_network_calls": cls._external_network_calls(policy),
        }

    @staticmethod
    def _validate_policy(policy: Mapping[str, Any]) -> None:
        for field in ("dependency_registry_sha256", *_POLICY_HASH_FIELDS):
            if not _HASH_PATTERN.fullmatch(str(policy.get(field) or "")):
                raise JobLifecycleError(f"cache policy {field} is invalid")
        if policy.get("dependency_snapshot_valid") is not True:
            raise JobLifecycleError("cache dependency snapshot is invalid")
        if policy.get("ordinary_run_network_allowed") is not False:
            raise JobLifecycleError("ordinary runtime network access must remain disabled")
        if policy.get("no_diff_network_allowed") is not False:
            raise JobLifecycleError("no-diff runtime network access must remain disabled")
        if int(policy.get("external_network_calls") or 0) != 0:
            raise JobLifecycleError("cache refresh must record zero external network calls")
