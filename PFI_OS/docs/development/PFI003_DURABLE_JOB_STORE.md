# PFI-003 Durable Job Store

Last updated: 2026-06-20 Australia/Sydney

## Scope

This document records the first executable PFI-003 runtime supervisor slice.
It adds a durable job lifecycle contract on top of the existing
`job_records` table without introducing a new database table or a destructive
schema migration.

## Implemented

- Deterministic job id from `job_type` and `idempotency_key`.
- Duplicate enqueue returns the existing job.
- Atomic claim uses SQLite `BEGIN IMMEDIATE`.
- A running job carries `lease_owner`, `lease_expires_at`, `heartbeat_at`, and
  `claim_count` in `metadata_json`.
- Only the active lease owner can heartbeat, complete, or fail a job.
- Double-worker behavior is fail-closed: only one worker receives the active
  lease; the second worker sees idle/no claim.
- Bounded `fail_or_retry` moves jobs through `retrying` and then
  `dead_letter`.
- Expired lease recovery requeues retryable jobs and dead-letters exhausted
  jobs.
- Cancel and resume are explicit state transitions.
- Readiness reports Web/API/Worker separately.
- `scripts/pfiSupervisor.sh` exposes contract, status, doctor, enqueue, claim,
  heartbeat, complete, fail, cancel, resume, recover, double-worker smoke, and
  crash-recovery smoke commands.
- Double-worker smoke proves only one worker receives the active lease.
- Crash-recovery smoke simulates a worker that stops before heartbeat and then
  recovers the expired lease.
- Safety boundary remains research-only: no broker calls, no order execution,
  no payments, no betting, no private-data commit path.

## Current API

- `build_pfi003_runtime_supervisor_contract()`
- `durable_job_id(job_type=..., idempotency_key=...)`
- `DurableJobStore.enqueue(...)`
- `DurableJobStore.claim(...)`
- `DurableJobStore.heartbeat(...)`
- `DurableJobStore.complete(...)`
- `DurableJobStore.fail_or_retry(...)`
- `DurableJobStore.cancel(...)`
- `DurableJobStore.resume(...)`
- `DurableJobStore.recover_expired_leases(...)`
- `DurableJobStore.readiness(...)`
- `scripts/pfiSupervisor.sh --json doctor --recover-expired`
- `scripts/pfiSupervisor.sh --json smoke-double-worker`
- `scripts/pfiSupervisor.sh --json smoke-crash-recovery`

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' /opt/anaconda3/bin/python3.12 -m pytest tests/contract/test_pfi003_durable_jobs.py -q
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' /opt/anaconda3/bin/python3.12 -m pytest tests/contract/test_pfi003_supervisor_cli.py -q
PFI_PYTHON=/opt/anaconda3/bin/python3.12 scripts/pfiSupervisor.sh --db-path /private/tmp/pfi003-supervisor-smoke/pfi.sqlite --json doctor --recover-expired
PFI_PYTHON=/opt/anaconda3/bin/python3.12 scripts/pfiSupervisor.sh --db-path /private/tmp/pfi003-supervisor-smoke/pfi.sqlite --json smoke-double-worker --job-type shell_double_worker --idempotency-key shell-double-worker
PFI_PYTHON=/opt/anaconda3/bin/python3.12 scripts/pfiSupervisor.sh --db-path /private/tmp/pfi003-supervisor-smoke/pfi.sqlite --json smoke-crash-recovery --job-type shell_crash_recovery --idempotency-key shell-crash-recovery --lease-seconds 2 --advance-seconds 3
```

Observed: Durable Job Store tests passed `8/8`; supervisor CLI tests passed
`6/6`; shell smoke passed `doctor`, `smoke-double-worker`, and
`smoke-crash-recovery` against `/private/tmp/pfi003-supervisor-smoke/pfi.sqlite`.

## Remaining PFI-003 Work

- Add sleep/wake, TERM/KILL, network recovery, backup/restore manifest, and
  private-log scan evidence.
- Integrate durable lifecycle events into the Web Shell/runtime read model.
- Add launchd throttle/log-rotation proof for release Gate 1.
