# PFI-003 Durable Job Store

Last updated: 2026-06-20 Australia/Sydney

## Scope

This document records the executable PFI-003 runtime supervisor slice.
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
- `scripts/pfiSupervisor.sh --json acceptance` runs a release-oriented local
  acceptance harness with doctor, double-worker claim exclusion, TERM worker
  recovery, KILL worker recovery, sleep/wake time-jump recovery, SQLite backup
  manifest, network recovery, launchd throttle/log-rotation, Web Shell runtime
  read-model, and private-log scan checks.
- TERM/KILL recovery uses a real child worker process that claims a lease, is
  terminated, and is recovered through expired lease handling.
- Sleep/wake recovery uses deterministic time-jump evidence so the check is
  fast, repeatable, and does not require putting the Mac to sleep.
- Acceptance writes a temporary SQLite backup plus a manifest containing
  checksum, byte size, row count, case statuses, and no-network/no-live-exec
  flags.
- Network recovery evidence simulates a source outage, retries through the
  durable job lifecycle, and completes without making a real network call.
- Launchd evidence writes a sanitized local LaunchAgent template with
  `ThrottleInterval`, bounded stdout/stderr paths, and a local log-rotation
  manifest, then exercises rotation against a temporary log file without
  calling `launchctl`.
- Phase C runtime read model now emits `supervisor_runtime` from
  `job_records`, and the Web Shell consumes it in the Data/System workspace so
  PFI-003 job health is visible from the user-facing shell.
- Private-log scan checks acceptance log and manifest for forbidden local path,
  credential, account, and private-holding fragments.
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
- `scripts/pfiSupervisor.sh --json acceptance`

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' /opt/anaconda3/bin/python3.12 -m pytest tests/contract/test_pfi003_durable_jobs.py -q
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' /opt/anaconda3/bin/python3.12 -m pytest tests/contract/test_pfi003_supervisor_cli.py -q
PFI_PYTHON=/opt/anaconda3/bin/python3.12 scripts/pfiSupervisor.sh --db-path /private/tmp/pfi003-supervisor-smoke/pfi.sqlite --json doctor --recover-expired
PFI_PYTHON=/opt/anaconda3/bin/python3.12 scripts/pfiSupervisor.sh --db-path /private/tmp/pfi003-supervisor-smoke/pfi.sqlite --json smoke-double-worker --job-type shell_double_worker --idempotency-key shell-double-worker
PFI_PYTHON=/opt/anaconda3/bin/python3.12 scripts/pfiSupervisor.sh --db-path /private/tmp/pfi003-supervisor-smoke/pfi.sqlite --json smoke-crash-recovery --job-type shell_crash_recovery --idempotency-key shell-crash-recovery --lease-seconds 2 --advance-seconds 3
rm -rf /private/tmp/pfi003-supervisor-acceptance
mkdir -p /private/tmp/pfi003-supervisor-acceptance
PFI_PYTHON=/opt/anaconda3/bin/python3.12 scripts/pfiSupervisor.sh --db-path /private/tmp/pfi003-supervisor-acceptance/pfi.sqlite --json acceptance --runtime-dir /private/tmp/pfi003-supervisor-acceptance --lease-seconds 2 --advance-seconds 3 --worker-timeout-seconds 15 --sleep-wake-seconds 120 --hold-seconds 30
```

Observed: Durable Job Store tests passed `8/8`; supervisor CLI tests passed
`7/7`; shell smoke passed `doctor`, `smoke-double-worker`,
`smoke-crash-recovery`, and `acceptance` against temporary SQLite databases
under `/private/tmp`. The acceptance summary passed `10/10` checks and produced
`pfi003_supervisor_acceptance_manifest.json`,
`pfi003_supervisor_acceptance_backup.sqlite`, and
`pfi003_supervisor_acceptance.jsonl`, plus sanitized launchd/log-rotation
artifacts.

## Remaining PFI-003 Work

- No local implementation gap remains for the PFI-003 release-hardening slice.
- Re-run the PFI-003 acceptance command in CI/release packaging before final
  Gate 7 closure.
