# STAGE-040 Phase 2 Backpressure Decision Slice

## Identity

- Task: `IDS-V0_1-STAGE040-P2`
- Acceptance: `ACC-STAGE-040`
- Policy: `ids.backpressure_policy.v0_1.stage040.p2`
- Mode: `ISOLATED_NON_PRODUCTION_BACKPRESSURE_DECISION_SLICE`
- State: `PHASE2_ISOLATED_DECISION_SLICE_ENABLED_PRODUCTION_DISABLED`
- Next gate: `IDS-STAGE040-P3-GATE`

## Source And Upstream Reverification

The approved Stage040 member remains unique and its SHA256 remains
`f0ef128467300d7541796f8d51caca673f838cac2552eba2e415a94a07af614d`.
The Phase 1 contract/checker/boundary, Stage037 state model, Stage038 queue
baseline, and Stage039 retry contract were rehashed before implementation.
All exact refs and hashes are recorded in the Phase 2 machine contract.

No content under `/Users/linzezhang/Downloads/IDS_MetaData` was listed, opened,
hashed, copied, moved, changed, dumped, scanned, or used.

## Selected Policy Parameters

All values below are `PROPOSED` local engineering safety boundaries for the
isolated control slice. They are not production calibrated and remain linked
to `TASK-OPME-B-001`.

| Parameter | Value | Unit | Selection basis |
|---|---:|---|---|
| queue soft/high watermark | 2 | tracked control refs | begin throttling before hard capacity |
| queue hard capacity | 4 | tracked control refs | equals the exact four-ref control corpus and stays below Stage038 max 16 |
| queue low watermark | 1 | tracked control ref | release hysteresis only after pressure falls below soft/high watermark |
| disk usable-free threshold | 1,073,741,824 | bytes | finite 1 GiB isolated guard, not a production storage forecast |
| disk reserve | 536,870,912 | bytes | preserve a separate 512 MiB reserve in the isolated calculation |
| API budget window | 60 | seconds | bounded observation window; no API call or credential is used |
| observation TTL | 30 | seconds | shorter than the API window so stale state fails closed |
| per-job-type concurrency | 1 | active control jobs | avoid same-type overlap before Stage041 lock runtime exists |
| admission rate limit | 4 | admissions per window | at most one hard-cap control set per 60-second window |

Formula invariants:

- `queue_low_watermark < queue_soft_pressure_threshold < queue_hard_capacity_threshold <= 16`;
- `usable_free_bytes = max(0, disk_free_bytes - disk_reserve_bytes)`;
- disk pressure triggers when `usable_free_bytes < disk_free_bytes_threshold`;
- API pressure triggers when `required_units > remaining_units`;
- observation age must be `0..observation_ttl_seconds`;
- throttle/deny/pause consumes no retry budget and never rotates the job
  idempotency key.

## Controlled Evidence

The checker evaluates four real Git-tracked governance/control documents. It
does not copy their bodies into a job or output. It also performs one actual
`shutil.disk_usage` observation on the project volume, then evaluates the
result against the proposed policy without allocating or deleting disk space.

The runnable slice proves:

1. queue depth `2` over two tracked refs returns `THROTTLE_ADMISSION`;
2. queue depth `4` over all four refs returns `DENY_NEW_ADMISSION` and creates
   no queue record or job;
3. an API-required control observation with zero remaining units returns a
   legal `RUNNING -> PAUSE_REQUESTED -> PAUSED` candidate without an API call;
4. identical job/policy/observation input replays the original in-memory
   decision and checkpoint;
5. actual project free-space observation is classified by the exact formula;
6. input/output/error/checkpoint/audit refs remain bounded metadata and no
   runtime output is written.

Machine state is mapped to restrained Chinese status: `可接收`, `限流中`,
`暂不接收新任务`, `暂停中`, `已暂停`, or `等待人工复核`.

## Failure And Stop Behavior

- Missing, malformed, future, stale, unversioned, or untracked observations
  return a JSON-serializable `REQUIRE_MANUAL_REVIEW` decision and admit
  nothing. Non-JSON control metadata is represented only by a fixed invalid
  digest marker; it is never echoed into the decision.
- Invalid jobs are evaluated through an empty safe view. Invalid `input_refs`
  therefore produce `input_refs=[]` and cannot leak unapproved payloads or
  untracked values into error output.
- `SUCCEEDED`, `FAILED`, `DEAD_LETTERED`, and `CANCELLED` remain immutable.
- Active work can request `PAUSE_REQUESTED`; it is not directly forced to
  `PAUSED` and is not automatically resumed.
- The decision ledger is memory-only. Process restart does not recover it and
  STAGE-043 remains the crash-recovery owner.
- Same-source lock acquisition, renewal, release, and fencing remain STAGE-041
  work. This Phase evaluates concurrency metadata only.
- Partial-output deletion remains STAGE-044 work. This Phase exposes no delete
  path.

## Validation Boundary

`Phase 3 must run separately`. Phase 3 owns adversarial scenario evidence,
including duplicate click, worker exception/crash boundary, drive removal
control, low disk, same-file concurrency, lock enforcement, and protected
cleanup denial.

Stop markers:

- `NO_PHASE3`
- `NO_QUEUE_RUNTIME`
- `NO_WORKER_RUNTIME`
- `NO_RETRY_SCHEDULER`
- `NO_LOCK_RUNTIME`
- `NO_AUTOMATIC_RESUME`
- `NO_CLEANUP_RUNTIME`
- `NO_POSTGRES_CONNECTION`
- `NO_PERSISTENT_QUEUE_WRITE`
- `NO_RUNTIME_OUTPUT`
- `NO_EXTERNAL_API_CALL`
- `NO_RAW_METADATA_ACCESS`
- `NO_FAKE_IDS_BUSINESS_DATA`
- `NO_GITHUB_UPLOAD`
- `NO_APP_REINSTALL`

`push_allowed=false`. The only next task is `IDS-V0_1-STAGE040-P3`.

## Rollback

On invalid contract, policy, observation, or upstream binding, deny new
admission, require manual review, and revert only Phase 2 artifacts and the
Phase 2 governance transition. Preserve Phase 1, earlier stages, raw sources,
manifests, evidence ledgers, audit logs, report snapshots, owner-authored dirty
files, GitHub state, and app entries.
