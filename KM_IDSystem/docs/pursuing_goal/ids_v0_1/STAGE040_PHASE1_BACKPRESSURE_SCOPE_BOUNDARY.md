# STAGE-040 Phase 1 Backpressure Scope Boundary

## Decision Contract

The policy consumes reference-only job and pressure metadata and returns one
of five actions:

| Condition | Action | State effect | Chinese status |
|---|---|---|---|
| All applicable observations valid and healthy | `ADMIT` | no policy state mutation | `可接收` |
| Queue soft pressure | `THROTTLE_ADMISSION` | defer admission; no lifecycle mutation | `限流中` |
| Queue hard capacity | `DENY_NEW_ADMISSION` | create no queue record | `暂不接收新任务` |
| Drive, disk, or API resource unavailable | `PAUSE_RESOURCE_GATE` | queued/retry-wait jobs may reach `PAUSED`; claimed/running jobs only request `PAUSE_REQUESTED` | queued/retry-wait: `已暂停`; claimed/running: `暂停中` |
| Missing, unknown, stale, or unversioned pressure | `REQUIRE_MANUAL_REVIEW` | no new admission | `等待人工复核` |

`UNKNOWN_OR_STALE_PRESSURE` is fail-closed. Priority cannot bypass a safety
gate. Stage 040 does not implement or prove scheduler-level starvation
prevention; STAGE-022 remains the priority-vocabulary owner. Phase 2 provides
only a per-job-type admission guard, while the scheduling algorithm remains
`NOT_IMPLEMENTED_IN_STAGE040` and must be introduced by a separately governed
future owner.

## Legal Lifecycle Effects

The only resource-pause paths are inherited from `ids.job_state.v1`:

- `QUEUED -> PAUSED`
- `RETRY_WAIT -> PAUSED`
- `RUNNING -> PAUSE_REQUESTED -> PAUSED`
- `CLAIMED -> PAUSE_REQUESTED -> PAUSED`

An active job reaches `PAUSED` only through a safe point. `SUCCEEDED`,
`FAILED`, `DEAD_LETTERED`, and `CANCELLED` remain immutable. Throttle,
admission denial, and resource pause consume no retry budget. This contract
does not resume jobs; STAGE-042 owns automatic resume.

## Metadata Input And Evidence

Inputs are stable references for job identity/state/version, priority,
pressure observations, claim/lock status, retry status, checkpoint, input,
output, error, audit, policy version, and observation time. A pressure
observation records a signal code, observed-value reference, unit, timestamp,
source reference, policy version, and validity status. Raw payloads and raw
source bodies are forbidden.

Every decision is keyed by
`idempotency_key + policy_version + pressure_observation_set_digest`.
Replaying the same decision returns the original result. Throttling or pausing
does not rotate the job idempotency key; denied admission creates no job.

## Parameter Gate

Phase 1 assigns no numeric policy value. Phase 2 must separately select,
version, justify, test, and make rollback-ready:

- queue soft-pressure and hard-capacity thresholds;
- disk free-byte threshold and reserve;
- external API budget window;
- high and low watermarks with valid ordering;
- observation TTL;
- per-job-type concurrency;
- admission rate limit.

Each parameter requires a source, rationale, unit, policy version, validation
evidence, and rollback. Implicit library defaults, magic numbers, zero-TTL
observations, inverted watermarks, infinite admission, and undocumented
production assumptions are not allowed.

## Lock And Partial-Output Boundary

STAGE-040 may read claim/lock references as decision inputs but cannot acquire,
renew, release, or fence a lock. STAGE-041 owns lock, lease, and fencing
runtime. Same-source conflict remains a lock input, not a replacement
backpressure threshold.

STAGE-040 defines cleanup eligibility only. STAGE-044 owns execution. Future
cleanup may consider only explicitly allowlisted temporary staging output or
incomplete derivative output. It cannot delete fact sources, manifests,
evidence ledgers, audit logs, or report snapshots.

## Ownership Matrix

| Capability | Owner |
|---|---|
| Backpressure decision policy | `STAGE-040` |
| Queue and worker transport | `STAGE-038` |
| Retry and dead-letter policy | `STAGE-039` |
| Lock, lease, and fencing runtime | `STAGE-041` |
| Automatic resume runtime | `STAGE-042` |
| Crash recovery runtime | `STAGE-043` |
| Cleanup execution runtime | `STAGE-044` |

## Phase 2 Gate And Stop Markers

`Phase 2 must run separately`. Before entry it must revalidate upstream hashes,
select all required parameters, preserve the state/retry/idempotency/ownership
invariants above, and remain production-disabled.

This Phase records:

- `NO_PHASE2`
- `NO_BACKPRESSURE_RUNTIME`
- `NO_QUEUE_RUNTIME`
- `NO_WORKER_RUNTIME`
- `NO_LOCK_RUNTIME`
- `NO_AUTOMATIC_RESUME`
- `NO_CLEANUP_RUNTIME`
- `NO_POSTGRES_CONNECTION`
- `NO_SCHEMA_CHANGE`
- `NO_RUNTIME_OUTPUT`
- `NO_RAW_METADATA_ACCESS`
- `NO_FAKE_IDS_BUSINESS_DATA`
- `NO_GITHUB_UPLOAD`
- `NO_APP_REINSTALL`

The next gate is `IDS-STAGE040-P2-GATE`; `push_allowed=false`.

## Acceptance And Rollback

Phase 1 satisfies only the engineering-contract portion of `ACC-STAGE-040`:
the policy surface, failure/stop/audit/rollback behavior, evidence protection,
and future ownership are explicit and machine-checkable. Stage acceptance
remains in progress until separate Phase 2-4 runs and whole-stage review pass.

Rollback removes only this Phase's Stage040 files and governance transition.
It does not mutate source data, jobs, queues, locks, databases, reports,
earlier Stage evidence, GitHub, app installation, or owner-authored files.
