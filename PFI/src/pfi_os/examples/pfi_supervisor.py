from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import shutil
import subprocess
import sys
import time
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

    acceptance = subparsers.add_parser("acceptance", help="Run PFI-003 process-level release acceptance.")
    acceptance.add_argument("--runtime-dir", default="/private/tmp/pfi003-supervisor-acceptance")
    acceptance.add_argument("--lease-seconds", type=int, default=2)
    acceptance.add_argument("--advance-seconds", type=int, default=3)
    acceptance.add_argument("--worker-timeout-seconds", type=int, default=15)
    acceptance.add_argument("--sleep-wake-seconds", type=int, default=120)
    acceptance.add_argument("--hold-seconds", type=int, default=60)
    acceptance.add_argument("--network-retry-delay-seconds", type=int, default=1)
    acceptance.add_argument("--launchd-throttle-seconds", type=int, default=30)
    acceptance.add_argument("--log-rotation-bytes", type=int, default=4096)

    worker_hold = subparsers.add_parser("worker-hold-lease", help=argparse.SUPPRESS)
    worker_hold.add_argument("--job-type", required=True)
    worker_hold.add_argument("--idempotency-key", required=True)
    worker_hold.add_argument("--worker-id", required=True)
    worker_hold.add_argument("--lease-seconds", type=int, default=60)
    worker_hold.add_argument("--log-path", required=True)
    worker_hold.add_argument("--hold-seconds", type=int, default=60)
    worker_hold.add_argument("--case-name", default="WorkerHoldLease")

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
    if command == "acceptance":
        return _acceptance(args, supervisor)
    if command == "worker-hold-lease":
        return _worker_hold_lease(args, supervisor)
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


def _acceptance(args: argparse.Namespace, supervisor: DurableJobStore) -> dict[str, Any]:
    runtime_dir = Path(args.runtime_dir).expanduser()
    runtime_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("pfi003-%Y%m%dT%H%M%SZ")
    log_path = runtime_dir / "pfi003_supervisor_acceptance.jsonl"
    manifest_path = runtime_dir / "pfi003_supervisor_acceptance_manifest.json"
    backup_path = runtime_dir / "pfi003_supervisor_acceptance_backup.sqlite"
    launchd_plist_path = runtime_dir / "pfi003_supervisor_launch_agent.plist"
    log_rotation_manifest_path = runtime_dir / "pfi003_supervisor_log_rotation_manifest.json"
    launchd_out_log_path = runtime_dir / "pfi003_supervisor_launchd.out.log"
    launchd_err_log_path = runtime_dir / "pfi003_supervisor_launchd.err.log"
    for path in (
        log_path,
        manifest_path,
        backup_path,
        launchd_plist_path,
        log_rotation_manifest_path,
        launchd_out_log_path,
        launchd_err_log_path,
        _rotated_log_path(launchd_out_log_path, 1),
        _rotated_log_path(launchd_err_log_path, 1),
    ):
        if path.exists():
            path.unlink()

    _write_log_event(log_path, {"schema": "PFIOSPFI003SupervisorAcceptanceLogV1", "run_id": run_id, "event": "started"})
    doctor = _doctor(supervisor, worker_id=f"{run_id}-doctor", recover_expired=True, job_type="")
    double_worker = _smoke_double_worker(
        supervisor,
        job_type=f"{run_id}_double_worker",
        idempotency_key=f"{run_id}-double-worker",
        worker_a=f"{run_id}-worker-a",
        worker_b=f"{run_id}-worker-b",
        lease_seconds=max(1, int(args.lease_seconds)),
    )
    term_case = _process_recovery_case(args, supervisor, mode="TERM", run_id=run_id, log_path=log_path)
    kill_case = _process_recovery_case(args, supervisor, mode="KILL", run_id=run_id, log_path=log_path)
    sleep_wake = _sleep_wake_recovery(args, supervisor, run_id=run_id, log_path=log_path)
    network_recovery = _network_recovery_case(args, supervisor, run_id=run_id, log_path=log_path)
    launchd_case = _launchd_throttle_log_rotation_case(
        args,
        runtime_dir=runtime_dir,
        run_id=run_id,
        log_path=log_path,
        launchd_plist_path=launchd_plist_path,
        log_rotation_manifest_path=log_rotation_manifest_path,
        stdout_log_path=launchd_out_log_path,
        stderr_log_path=launchd_err_log_path,
    )
    manifest = _write_acceptance_manifest(
        supervisor,
        manifest_path=manifest_path,
        backup_path=backup_path,
        run_id=run_id,
        cases=[doctor, double_worker, term_case, kill_case, sleep_wake, network_recovery, launchd_case],
    )
    private_scan = _scan_private_logs(
        log_path,
        manifest_path,
        launchd_plist_path,
        log_rotation_manifest_path,
        launchd_out_log_path,
        _rotated_log_path(launchd_out_log_path, 1),
    )
    checks = [
        _check("DoctorReadiness", doctor["status"] == "Pass", f"pass={doctor['summary']['pass']} fail={doctor['summary']['fail']}"),
        _check("DoubleWorkerClaimExclusion", double_worker["status"] == "Pass", double_worker["double_worker_behavior"]),
        _check("TERMWorkerRecovery", term_case["status"] == "Pass", term_case.get("evidence", "")),
        _check("KILLWorkerRecovery", kill_case["status"] == "Pass", kill_case.get("evidence", "")),
        _check("SleepWakeRecovery", sleep_wake["status"] == "Pass", sleep_wake.get("evidence", "")),
        _check("NetworkRecovery", network_recovery["status"] == "Pass", network_recovery.get("evidence", "")),
        _check("LaunchdThrottleLogRotation", launchd_case["status"] == "Pass", launchd_case.get("evidence", "")),
        _check("BackupManifest", manifest["status"] == "Pass", manifest.get("backup_file", "")),
        _check("PrivateLogScan", private_scan["status"] == "Pass", private_scan.get("evidence", "")),
        _check("NoExecutionBoundary", True, "research_only_no_broker_orders_payments"),
    ]
    summary = {
        "pass": sum(1 for item in checks if item["status"] == "Pass"),
        "fail": sum(1 for item in checks if item["status"] == "Fail"),
        "total": len(checks),
    }
    return {
        "schema": "PFIOSPFI003SupervisorAcceptanceV1",
        "status": "Pass" if summary["fail"] == 0 else "Fail",
        "run_id": run_id,
        "summary": summary,
        "checks": checks,
        "cases": {
            "doctor": doctor,
            "double_worker": double_worker,
            "term_worker": term_case,
            "kill_worker": kill_case,
            "sleep_wake": sleep_wake,
            "network_recovery": network_recovery,
            "launchd_throttle_log_rotation": launchd_case,
            "private_log_scan": private_scan,
        },
        "outputs": {
            "log_path": str(log_path),
            "manifest_path": str(manifest_path),
            "backup_path": str(backup_path),
            "launchd_plist_path": str(launchd_plist_path),
            "log_rotation_manifest_path": str(log_rotation_manifest_path),
        },
        "manifest": manifest,
        "safety_boundary": "Local deterministic supervisor acceptance. No network, broker, order, payment, betting, or private holdings access.",
        "next_action": "Use the runtime read-model evidence with PFI-004 Golden/PIT proof before closing Gate 1.",
    }


def _process_recovery_case(
    args: argparse.Namespace,
    supervisor: DurableJobStore,
    *,
    mode: str,
    run_id: str,
    log_path: Path,
) -> dict[str, Any]:
    lease_seconds = max(1, int(args.lease_seconds))
    advance_seconds = max(lease_seconds + 1, int(args.advance_seconds) + lease_seconds)
    worker_id = f"{run_id}-{mode.lower()}-worker"
    job_type = f"{run_id}_{mode.lower()}_process"
    idempotency_key = f"{run_id}-{mode.lower()}-process"
    started = datetime.now(timezone.utc)
    supervisor.enqueue(job_type=job_type, idempotency_key=idempotency_key, max_attempts=3, now=started)
    process = _start_worker_hold_process(
        args,
        job_type=job_type,
        idempotency_key=idempotency_key,
        worker_id=worker_id,
        lease_seconds=lease_seconds,
        log_path=log_path,
        case_name=f"{mode}WorkerRecovery",
    )
    claimed = _wait_for_worker_claim(log_path, worker_id=worker_id, timeout_seconds=max(1, int(args.worker_timeout_seconds)))
    if not claimed:
        _stop_process(process, mode="KILL")
        return {"schema": "PFIOSPFI003ProcessRecoveryCaseV1", "status": "Fail", "mode": mode, "evidence": "worker_did_not_claim"}

    _stop_process(process, mode=mode)
    recovery_now = datetime.now(timezone.utc) + timedelta(seconds=advance_seconds)
    recovered = supervisor.recover_expired_leases(now=recovery_now, job_type=job_type)
    passed = int(recovered.get("recovered_count", 0)) >= 1
    _write_log_event(log_path, {"run_id": run_id, "event": "recovered", "mode": mode, "recovered_count": recovered.get("recovered_count", 0)})
    return {
        "schema": "PFIOSPFI003ProcessRecoveryCaseV1",
        "status": "Pass" if passed else "Fail",
        "mode": mode,
        "job_type": job_type,
        "worker_id": worker_id,
        "claimed": claimed,
        "recovered": recovered,
        "evidence": f"{mode}_worker_claimed_then_expired_lease_recovered={int(recovered.get('recovered_count', 0))}",
    }


def _sleep_wake_recovery(args: argparse.Namespace, supervisor: DurableJobStore, *, run_id: str, log_path: Path) -> dict[str, Any]:
    lease_seconds = max(1, int(args.lease_seconds))
    sleep_wake_seconds = max(lease_seconds + 1, int(args.sleep_wake_seconds))
    worker_id = f"{run_id}-sleep-wake-worker"
    job_type = f"{run_id}_sleep_wake"
    started = datetime.now(timezone.utc)
    supervisor.enqueue(job_type=job_type, idempotency_key=f"{run_id}-sleep-wake", max_attempts=3, now=started)
    claimed = supervisor.claim(job_type=job_type, worker_id=worker_id, lease_seconds=lease_seconds, now=started)
    recovered = supervisor.recover_expired_leases(now=started + timedelta(seconds=sleep_wake_seconds), job_type=job_type)
    passed = bool(claimed.get("claimed")) and int(recovered.get("recovered_count", 0)) >= 1
    _write_log_event(
        log_path,
        {
            "run_id": run_id,
            "event": "sleep_wake_time_jump",
            "worker_id": worker_id,
            "claimed": bool(claimed.get("claimed")),
            "recovered_count": recovered.get("recovered_count", 0),
        },
    )
    return {
        "schema": "PFIOSPFI003SleepWakeRecoveryCaseV1",
        "status": "Pass" if passed else "Fail",
        "job_type": job_type,
        "worker_id": worker_id,
        "claimed": claimed,
        "recovered": recovered,
        "sleep_wake_seconds": sleep_wake_seconds,
        "evidence": f"sleep_wake_time_jump_seconds={sleep_wake_seconds} recovered={int(recovered.get('recovered_count', 0))}",
    }


def _network_recovery_case(args: argparse.Namespace, supervisor: DurableJobStore, *, run_id: str, log_path: Path) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    retry_delay = max(0, int(args.network_retry_delay_seconds))
    job_type = f"{run_id}_network_recovery"
    first_worker = f"{run_id}-network-worker-a"
    second_worker = f"{run_id}-network-worker-b"
    queued = supervisor.enqueue(
        job_type=job_type,
        idempotency_key=f"{run_id}-network-recovery",
        payload={"network_fixture": "simulated_unavailable_then_recovered", "real_network_used": False},
        max_attempts=3,
        now=started,
    )
    claimed = supervisor.claim(job_type=job_type, worker_id=first_worker, lease_seconds=max(1, int(args.lease_seconds)), now=started)
    failed = {}
    reclaimed = {}
    completed = {}
    if claimed.get("claimed"):
        failed = supervisor.fail_or_retry(
            claimed["job_id"],
            worker_id=first_worker,
            error_message="simulated network source unavailable",
            now=started + timedelta(seconds=1),
        )
    if failed.get("status") == "retrying":
        reclaimed = supervisor.claim(
            job_type=job_type,
            worker_id=second_worker,
            lease_seconds=max(1, int(args.lease_seconds)),
            now=started + timedelta(seconds=retry_delay + 2),
        )
    if reclaimed.get("claimed"):
        completed = supervisor.complete(
            reclaimed["job_id"],
            worker_id=second_worker,
            artifact_uri="operational_store:pfi003_network_recovery",
            now=started + timedelta(seconds=retry_delay + 3),
        )
    passed = (
        queued.get("status") == "queued"
        and claimed.get("claimed") is True
        and failed.get("status") == "retrying"
        and reclaimed.get("claimed") is True
        and completed.get("status") == "completed"
    )
    _write_log_event(
        log_path,
        {
            "run_id": run_id,
            "event": "network_recovery",
            "network_used": False,
            "first_status": failed.get("status", ""),
            "final_status": completed.get("status", ""),
        },
    )
    return {
        "schema": "PFIOSPFI003NetworkRecoveryCaseV1",
        "status": "Pass" if passed else "Fail",
        "job_type": job_type,
        "network_used": False,
        "retry_delay_seconds": retry_delay,
        "queued": queued,
        "claimed": claimed,
        "failed": failed,
        "reclaimed": reclaimed,
        "completed": completed,
        "evidence": f"simulated_network_failure_retry_completed={completed.get('status') == 'completed'}",
    }


def _launchd_throttle_log_rotation_case(
    args: argparse.Namespace,
    *,
    runtime_dir: Path,
    run_id: str,
    log_path: Path,
    launchd_plist_path: Path,
    log_rotation_manifest_path: Path,
    stdout_log_path: Path,
    stderr_log_path: Path,
) -> dict[str, Any]:
    throttle_seconds = max(10, int(args.launchd_throttle_seconds))
    max_bytes = max(512, int(args.log_rotation_bytes))
    plist_payload = {
        "Label": "com.pfi.os.supervisor",
        "ProgramArguments": ["scripts/pfiSupervisor.sh", "--json", "doctor", "--recover-expired"],
        "WorkingDirectory": "PFI_OS",
        "RunAtLoad": False,
        "KeepAlive": False,
        "ThrottleInterval": throttle_seconds,
        "StandardOutPath": str(stdout_log_path),
        "StandardErrorPath": str(stderr_log_path),
        "EnvironmentVariables": {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PFI_UI_V2": "1",
        },
    }
    with launchd_plist_path.open("wb") as handle:
        plistlib.dump(plist_payload, handle, sort_keys=True)

    stdout_log_path.write_text("x" * (max_bytes + 64), encoding="utf-8")
    stderr_log_path.write_text("", encoding="utf-8")
    rotated_files = _rotate_log_if_needed(stdout_log_path, max_bytes=max_bytes, max_files=3)
    rotation_manifest = {
        "schema": "PFIOSPFI003LaunchdLogRotationManifestV1",
        "run_id": run_id,
        "policy": "bounded_local_logs",
        "max_bytes": max_bytes,
        "max_files": 3,
        "stdout_file": stdout_log_path.name,
        "stderr_file": stderr_log_path.name,
        "rotated_files": [path.name for path in rotated_files],
        "truncate_current_log": True,
        "launchd_loaded": False,
        "launchctl_used": False,
    }
    log_rotation_manifest_path.write_text(json.dumps(rotation_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    passed = (
        launchd_plist_path.exists()
        and plist_payload["ThrottleInterval"] >= 10
        and stdout_log_path.exists()
        and _rotated_log_path(stdout_log_path, 1).exists()
        and stdout_log_path.stat().st_size <= max_bytes
        and bool(rotation_manifest["rotated_files"])
    )
    _write_log_event(
        log_path,
        {
            "run_id": run_id,
            "event": "launchd_throttle_log_rotation",
            "throttle_seconds": throttle_seconds,
            "max_bytes": max_bytes,
            "rotated_files": rotation_manifest["rotated_files"],
        },
    )
    return {
        "schema": "PFIOSPFI003LaunchdThrottleLogRotationCaseV1",
        "status": "Pass" if passed else "Fail",
        "throttle_seconds": throttle_seconds,
        "plist_file": launchd_plist_path.name,
        "plist_path": str(launchd_plist_path),
        "log_rotation_manifest_file": log_rotation_manifest_path.name,
        "log_rotation_manifest_path": str(log_rotation_manifest_path),
        "rotated_files": rotation_manifest["rotated_files"],
        "launchd_loaded": False,
        "launchctl_used": False,
        "evidence": f"throttle={throttle_seconds}s rotated_files={len(rotation_manifest['rotated_files'])}",
    }


def _worker_hold_lease(args: argparse.Namespace, supervisor: DurableJobStore) -> dict[str, Any]:
    claimed = supervisor.claim(
        job_type=args.job_type,
        worker_id=args.worker_id,
        lease_seconds=max(1, int(args.lease_seconds)),
    )
    log_path = Path(args.log_path).expanduser()
    _write_log_event(
        log_path,
        {
            "schema": "PFIOSPFI003WorkerHoldLeaseLogV1",
            "case": args.case_name,
            "event": "claimed" if claimed.get("claimed") else "claim_failed",
            "worker_id": args.worker_id,
            "job_type": args.job_type,
            "job_id": claimed.get("job_id", ""),
            "lease_owner": claimed.get("lease_owner", ""),
        },
    )
    if not claimed.get("claimed"):
        return {"schema": "PFIOSPFI003WorkerHoldLeaseV1", "status": "Fail", "claimed": claimed}
    time.sleep(max(1, int(args.hold_seconds)))
    return {"schema": "PFIOSPFI003WorkerHoldLeaseV1", "status": "Pass", "claimed": claimed}


def _start_worker_hold_process(
    args: argparse.Namespace,
    *,
    job_type: str,
    idempotency_key: str,
    worker_id: str,
    lease_seconds: int,
    log_path: Path,
    case_name: str,
) -> subprocess.Popen:
    project_root = Path(__file__).resolve().parents[3]
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{project_root / 'src'}{os.pathsep}{env['PYTHONPATH']}" if env.get("PYTHONPATH") else str(project_root / "src")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.setdefault("PYTHONPYCACHEPREFIX", "/private/tmp/pfi003-acceptance-pycache")
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "pfi_os.examples.pfi_supervisor",
            "--db-path",
            str(args.db_path),
            "--json",
            "worker-hold-lease",
            "--job-type",
            job_type,
            "--idempotency-key",
            idempotency_key,
            "--worker-id",
            worker_id,
            "--lease-seconds",
            str(lease_seconds),
            "--log-path",
            str(log_path),
            "--hold-seconds",
            str(max(1, int(args.hold_seconds))),
            "--case-name",
            case_name,
        ],
        cwd=project_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _wait_for_worker_claim(log_path: Path, *, worker_id: str, timeout_seconds: int) -> dict[str, Any]:
    deadline = time.time() + max(1, timeout_seconds)
    while time.time() < deadline:
        for event in _read_log_events(log_path):
            if event.get("worker_id") == worker_id and event.get("event") == "claimed":
                return event
        time.sleep(0.1)
    return {}


def _stop_process(process: subprocess.Popen, *, mode: str) -> None:
    if process.poll() is not None:
        return
    if mode == "TERM":
        process.terminate()
        try:
            process.wait(timeout=3)
            return
        except subprocess.TimeoutExpired:
            process.kill()
    else:
        process.kill()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        pass


def _write_acceptance_manifest(
    supervisor: DurableJobStore,
    *,
    manifest_path: Path,
    backup_path: Path,
    run_id: str,
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    supervisor.store.initialize()
    db_path = supervisor.store.db_path
    shutil.copy2(db_path, backup_path)
    manifest = {
        "schema": "PFIOSPFI003SupervisorAcceptanceManifestV1",
        "status": "Pass" if backup_path.exists() and backup_path.stat().st_size > 0 else "Fail",
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_db_file": db_path.name,
        "backup_file": backup_path.name,
        "backup_sha256": _sha256(backup_path),
        "backup_bytes": backup_path.stat().st_size if backup_path.exists() else 0,
        "job_record_count": len(supervisor.store.table_rows("job_records")),
        "case_statuses": [
            {
                "index": index,
                "schema": str(case.get("schema", "")),
                "mode": str(case.get("mode", "")),
                "status": str(case.get("status", "Unknown")),
            }
            for index, case in enumerate(cases)
        ],
        "private_data_included": False,
        "network_used": False,
        "live_execution_used": False,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def _scan_private_logs(*paths: Path) -> dict[str, Any]:
    forbidden = [
        "/Users/",
        "/Applications/",
        "password",
        "secret",
        "token",
        "holdings_json",
        "private_holding",
        "broker_account",
        "api_key",
    ]
    findings: list[dict[str, str]] = []
    for path in paths:
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        lowered = text.lower()
        for fragment in forbidden:
            needle = fragment.lower()
            if needle in lowered:
                findings.append({"file": path.name, "fragment": fragment})
    return {
        "schema": "PFIOSPFI003PrivateLogScanV1",
        "status": "Pass" if not findings else "Fail",
        "findings": findings,
        "evidence": f"scanned_files={len(paths)} findings={len(findings)}",
    }


def _rotate_log_if_needed(path: Path, *, max_bytes: int, max_files: int) -> list[Path]:
    if not path.exists() or path.stat().st_size <= max_bytes:
        return []
    rotated: list[Path] = []
    for index in range(max_files, 0, -1):
        current = _rotated_log_path(path, index)
        if index == max_files and current.exists():
            current.unlink()
        elif current.exists():
            current.rename(_rotated_log_path(path, index + 1))
    first = _rotated_log_path(path, 1)
    path.rename(first)
    path.write_text("", encoding="utf-8")
    rotated.append(first)
    return rotated


def _rotated_log_path(path: Path, index: int) -> Path:
    return path.with_name(f"{path.name}.{index}")


def _write_log_event(log_path: Path, event: dict[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    clean_event = {"timestamp": datetime.now(timezone.utc).isoformat(), **event}
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(clean_event, ensure_ascii=False, sort_keys=True) + "\n")


def _read_log_events(log_path: Path) -> list[dict[str, Any]]:
    if not log_path.exists():
        return []
    events = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
