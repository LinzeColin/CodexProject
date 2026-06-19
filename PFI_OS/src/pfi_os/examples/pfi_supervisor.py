from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from pfi_os.application import (
    DurableJobStore,
    OperationalStore,
    build_pfi003_runtime_supervisor_contract,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="PFI-003 local runtime supervisor and durable job CLI.")
    parser.add_argument("--db-path", default="", help="Optional OperationalStore SQLite path for tests or isolated runs.")
    parser.add_argument("--json", action="store_true", help="Print full JSON payload.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("contract", help="Print the PFI-003 runtime supervisor contract.")

    status_parser = subparsers.add_parser("status", help="Print Web/API/Worker/JobStore readiness.")
    status_parser.add_argument("--worker-id", default="", help="Optional worker id for worker readiness.")

    doctor_parser = subparsers.add_parser("doctor", help="Run supervisor readiness and recovery checks.")
    doctor_parser.add_argument("--worker-id", default="doctor-worker", help="Worker id used for readiness checks.")
    doctor_parser.add_argument("--recover-expired", action="store_true", help="Recover expired leases before reporting.")
    doctor_parser.add_argument("--job-type", default="", help="Optional job type filter for expired lease recovery.")

    enqueue_parser = subparsers.add_parser("enqueue", help="Enqueue an idempotent durable job.")
    enqueue_parser.add_argument("--job-type", required=True)
    enqueue_parser.add_argument("--idempotency-key", required=True)
    enqueue_parser.add_argument("--payload-json", default="{}", help="JSON object payload.")
    enqueue_parser.add_argument("--max-attempts", type=int, default=3)
    enqueue_parser.add_argument("--as-of", default="")

    claim_parser = subparsers.add_parser("claim", help="Atomically claim a queued job.")
    claim_parser.add_argument("--job-type", required=True)
    claim_parser.add_argument("--worker-id", required=True)
    claim_parser.add_argument("--lease-seconds", type=int, default=60)

    heartbeat_parser = subparsers.add_parser("heartbeat", help="Refresh a running job lease heartbeat.")
    heartbeat_parser.add_argument("--job-id", required=True)
    heartbeat_parser.add_argument("--worker-id", required=True)
    heartbeat_parser.add_argument("--progress", type=float, default=None)
    heartbeat_parser.add_argument("--phase", default="")
    heartbeat_parser.add_argument("--lease-seconds", type=int, default=None)

    complete_parser = subparsers.add_parser("complete", help="Complete a running job.")
    complete_parser.add_argument("--job-id", required=True)
    complete_parser.add_argument("--worker-id", required=True)
    complete_parser.add_argument("--artifact-uri", default="")

    fail_parser = subparsers.add_parser("fail", help="Fail a running job and retry or dead-letter it.")
    fail_parser.add_argument("--job-id", required=True)
    fail_parser.add_argument("--worker-id", required=True)
    fail_parser.add_argument("--error-message", required=True)

    cancel_parser = subparsers.add_parser("cancel", help="Cancel a job.")
    cancel_parser.add_argument("--job-id", required=True)
    cancel_parser.add_argument("--reason", required=True)

    resume_parser = subparsers.add_parser("resume", help="Resume a cancelled or dead-letter job.")
    resume_parser.add_argument("--job-id", required=True)
    resume_parser.add_argument("--reason", required=True)

    recover_parser = subparsers.add_parser("recover", help="Recover expired leases.")
    recover_parser.add_argument("--job-type", default="")

    smoke_double = subparsers.add_parser("smoke-double-worker", help="Prove only one worker can claim one queued job.")
    smoke_double.add_argument("--job-type", default="pfi003_double_worker_smoke")
    smoke_double.add_argument("--idempotency-key", default="pfi003-double-worker")
    smoke_double.add_argument("--worker-a", default="worker-a")
    smoke_double.add_argument("--worker-b", default="worker-b")
    smoke_double.add_argument("--lease-seconds", type=int, default=60)

    smoke_crash = subparsers.add_parser("smoke-crash-recovery", help="Prove expired lease recovery after a simulated worker crash.")
    smoke_crash.add_argument("--job-type", default="pfi003_crash_recovery_smoke")
    smoke_crash.add_argument("--idempotency-key", default="pfi003-crash-recovery")
    smoke_crash.add_argument("--worker-id", default="worker-crash")
    smoke_crash.add_argument("--lease-seconds", type=int, default=5)
    smoke_crash.add_argument("--advance-seconds", type=int, default=6)

    args = parser.parse_args()
    supervisor = DurableJobStore(_store(args.db_path))
    payload = _dispatch(args, supervisor)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    else:
        print(_summary(payload))


def _dispatch(args: argparse.Namespace, supervisor: DurableJobStore) -> dict[str, Any]:
    command = args.command
    if command == "contract":
        return build_pfi003_runtime_supervisor_contract()
    if command == "status":
        return supervisor.readiness(worker_id=args.worker_id)
    if command == "doctor":
        return _doctor(supervisor, worker_id=args.worker_id, recover_expired=args.recover_expired, job_type=args.job_type)
    if command == "enqueue":
        return supervisor.enqueue(
            job_type=args.job_type,
            idempotency_key=args.idempotency_key,
            payload=_payload(args.payload_json),
            max_attempts=args.max_attempts,
            as_of=args.as_of,
        )
    if command == "claim":
        return supervisor.claim(job_type=args.job_type, worker_id=args.worker_id, lease_seconds=args.lease_seconds)
    if command == "heartbeat":
        return supervisor.heartbeat(
            args.job_id,
            worker_id=args.worker_id,
            progress=args.progress,
            phase=args.phase or None,
            lease_seconds=args.lease_seconds,
        )
    if command == "complete":
        return supervisor.complete(args.job_id, worker_id=args.worker_id, artifact_uri=args.artifact_uri)
    if command == "fail":
        return supervisor.fail_or_retry(args.job_id, worker_id=args.worker_id, error_message=args.error_message)
    if command == "cancel":
        return supervisor.cancel(args.job_id, reason=args.reason)
    if command == "resume":
        return supervisor.resume(args.job_id, reason=args.reason)
    if command == "recover":
        return supervisor.recover_expired_leases(job_type=args.job_type)
    if command == "smoke-double-worker":
        return _smoke_double_worker(
            supervisor,
            job_type=args.job_type,
            idempotency_key=args.idempotency_key,
            worker_a=args.worker_a,
            worker_b=args.worker_b,
            lease_seconds=args.lease_seconds,
        )
    if command == "smoke-crash-recovery":
        return _smoke_crash_recovery(
            supervisor,
            job_type=args.job_type,
            idempotency_key=args.idempotency_key,
            worker_id=args.worker_id,
            lease_seconds=args.lease_seconds,
            advance_seconds=args.advance_seconds,
        )
    raise ValueError(f"Unknown command: {command}")


def _doctor(supervisor: DurableJobStore, *, worker_id: str, recover_expired: bool, job_type: str) -> dict[str, Any]:
    recovered = supervisor.recover_expired_leases(job_type=job_type) if recover_expired else {"recovered_count": 0, "recovered": []}
    readiness = supervisor.readiness(worker_id=worker_id)
    checks = [
        _check("WebReady", readiness["web"]["ready"], readiness["web"]["surface"]),
        _check("APIReady", readiness["api"]["ready"], readiness["api"]["surface"]),
        _check("WorkerReady", readiness["worker"]["ready"], readiness["worker"].get("worker_id", "")),
        _check("JobStoreReady", readiness["job_store"]["ready"], readiness["job_store"]["db_path"]),
        _check("NoExecutionBoundary", readiness["safety_boundary"]["no_order_execution"], "no_order_execution=true"),
        _check("NoBrokerBoundary", readiness["safety_boundary"]["no_broker_calls"], "no_broker_calls=true"),
    ]
    if recover_expired:
        checks.append(_check("ExpiredLeaseRecovery", True, f"recovered={recovered['recovered_count']}"))
    summary = {
        "pass": sum(1 for item in checks if item["status"] == "Pass"),
        "fail": sum(1 for item in checks if item["status"] == "Fail"),
        "total": len(checks),
    }
    return {
        "schema": "PFIOSPFI003SupervisorDoctorV1",
        "status": "Pass" if summary["fail"] == 0 else "Fail",
        "readiness": readiness,
        "recovery": recovered,
        "checks": checks,
        "summary": summary,
        "safety_boundary": readiness["safety_boundary"],
        "next_action": "Use pfiSupervisor smoke-double-worker and smoke-crash-recovery before release Gate 1.",
    }


def _smoke_double_worker(
    supervisor: DurableJobStore,
    *,
    job_type: str,
    idempotency_key: str,
    worker_a: str,
    worker_b: str,
    lease_seconds: int,
) -> dict[str, Any]:
    supervisor.enqueue(job_type=job_type, idempotency_key=idempotency_key)
    first = supervisor.claim(job_type=job_type, worker_id=worker_a, lease_seconds=lease_seconds)
    second = supervisor.claim(job_type=job_type, worker_id=worker_b, lease_seconds=lease_seconds)
    passed = bool(first.get("claimed")) and not bool(second.get("claimed")) and first.get("job_id")
    return {
        "schema": "PFIOSPFI003DoubleWorkerSmokeV1",
        "status": "Pass" if passed else "Fail",
        "job_id": first.get("job_id", ""),
        "first_claim": first,
        "second_claim": second,
        "double_worker_behavior": "only_one_worker_receives_active_lease",
        "safety_boundary": build_pfi003_runtime_supervisor_contract()["safety_boundary"],
    }


def _smoke_crash_recovery(
    supervisor: DurableJobStore,
    *,
    job_type: str,
    idempotency_key: str,
    worker_id: str,
    lease_seconds: int,
    advance_seconds: int,
) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    supervisor.enqueue(job_type=job_type, idempotency_key=idempotency_key, now=started)
    claimed = supervisor.claim(job_type=job_type, worker_id=worker_id, lease_seconds=lease_seconds, now=started)
    recovered_at = started + timedelta(seconds=max(int(advance_seconds), int(lease_seconds) + 1))
    recovered = supervisor.recover_expired_leases(now=recovered_at, job_type=job_type)
    passed = bool(claimed.get("claimed")) and int(recovered.get("recovered_count", 0)) >= 1
    return {
        "schema": "PFIOSPFI003CrashRecoverySmokeV1",
        "status": "Pass" if passed else "Fail",
        "job_id": claimed.get("job_id", ""),
        "claimed": claimed,
        "recovered": recovered,
        "simulated_signal": "worker process stopped before heartbeat; lease expiry recovered job",
        "safety_boundary": build_pfi003_runtime_supervisor_contract()["safety_boundary"],
    }


def _store(db_path: str) -> OperationalStore:
    return OperationalStore(Path(db_path).expanduser()) if str(db_path or "").strip() else OperationalStore()


def _payload(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value or "{}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"--payload-json must be a JSON object: {exc}") from exc
    if not isinstance(parsed, dict):
        raise SystemExit("--payload-json must be a JSON object")
    return parsed


def _check(name: str, passed: bool, evidence: str) -> dict[str, str]:
    return {"name": name, "status": "Pass" if passed else "Fail", "evidence": str(evidence)}


def _summary(payload: dict[str, Any]) -> str:
    schema = payload.get("schema", "")
    status = payload.get("status", payload.get("job_id", "ok"))
    if "summary" in payload:
        summary = payload["summary"]
        return f"PFI_SUPERVISOR: schema={schema} status={status} pass={summary.get('pass')} fail={summary.get('fail')}"
    if "job_id" in payload:
        return f"PFI_SUPERVISOR: schema={schema} status={payload.get('status')} job_id={payload.get('job_id')} phase={payload.get('phase')}"
    return f"PFI_SUPERVISOR: schema={schema} status={status}"


if __name__ == "__main__":
    main()
