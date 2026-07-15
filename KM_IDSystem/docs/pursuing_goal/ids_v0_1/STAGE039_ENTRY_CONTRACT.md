# IDS v0.1 STAGE-039 Entry Contract

## Identity And Source

- Stage: `STAGE-039 · 重试与死信策略`
- Task: `IDS-V0_1-STAGE039-P1`
- Acceptance: `ACC-STAGE-039`
- Version: `v0.1`
- Local code: `D07-S003`
- Domain: `D07 · 任务编排与机器控制`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 1 · 范围、输入输出与边界确认`
- Pursuing goal: `让失败任务可重试、可终止、可归类、可进入人工复核。`
- `retry_policy_contract_id=ids.retry_dead_letter.v0_1.p1`
- `contract_state=PHASE1_ENGINEERING_CONTRACT_RUNTIME_DISABLED`

The exact approved source was read directly from the named archive without
extracting it or enumerating unrelated Downloads content:

- `source_archive_path=/Users/linzezhang/Downloads/IDS_Taskpack_v0_1_only_中文修订版.zip`
- `source_archive_sha256=55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3`
- `source_member=IDS_v0_1_Final_Chinese_Revised/stages/STAGE-039_重试与死信策略.md`
- `source_member_match_count=1`
- `source_member_integrity=OK`
- `source_member_sha256=504caf72a6aeab67a650b4b096e728f03269f6ca8798f6e8a5c51210c8ddd7d9`
- `roadmap_sha256=a193fd2c44c51d634bf7887a1a6baf7e5199d9a8535e4211e35e97588e2e21a6`
- `instructions_sha256=ce456e06136d5ecc56cd7c9dc926abb5894817dda87bf7667588bf85211794f8`
- `source_verification_status=SOURCE_VERIFIED`

## Authoritative Preconditions

- STAGE-037 `ids.job_state.v1` remains lifecycle authority. `FAILED`,
  `DEAD_LETTERED`, `SUCCEEDED`, and `CANCELLED` remain immutable terminal
  states; STAGE-039 must not add an outgoing terminal transition.
- STAGE-038 is `completed_reviewed_local`. Its isolated queue baseline has no
  automatic retry/dead-letter runtime and leaves policy ownership here.
- `max_retries` means retry attempts after the initial attempt;
  `total_attempt_limit = 1 + max_retries`.
- Retry reservation does not consume the budget. Only an atomic eligible
  admission back to `QUEUED` increments `retry_count`.
- `BATCH031_040_UPLOAD_LOCK.yaml` remains active with `push_allowed=false`.
- `/Users/linzezhang/Downloads/IDS_MetaData` is path-only governance context.
  `NO_RAW_METADATA_ACCESS` applies to the directory and every child.

The tracked upstream bindings and exact hashes are recorded in
`retry_dead_letter/stage039_retry_dead_letter_policy_contract.json`. Phase 2
must stop if any tracked dependency hash changes without a reviewed rebind.

## Phase 1 Decision Contract

One failure is classified into exactly one of these fail-closed classes:

| Failure class | Decision | Lifecycle target | Owner handling |
|---|---|---|---|
| `TRANSIENT_RETRYABLE` | `SCHEDULE_RETRY` | `RUNNING -> RETRY_WAIT` | wait for explicit eligibility |
| `PERMANENT_NON_RETRYABLE` | `FAIL_TERMINAL` | `RUNNING -> FAILED` | inspect; optional new linked job |
| `RESOURCE_CONDITION_PAUSE` | `PAUSE_RESOURCE_GATE` | legal path to `PAUSED` | restore resource and revalidate |
| `RETRY_EXHAUSTED` | `DEAD_LETTER` | `RETRY_WAIT -> DEAD_LETTERED` | mandatory manual triage |
| `POLICY_OR_AUTHORIZATION_BLOCK` | `REQUIRE_MANUAL_REVIEW` | fail closed | resolve policy or authorization |
| `INDETERMINATE_UNSAFE` | `REQUIRE_MANUAL_REVIEW` | fail closed | no automatic continuation |

`RUNNING -> DEAD_LETTERED` remains forbidden. An exhausted retry first has a
durable `RETRY_WAIT` decision with `retry_pending=false`; its only progress
path is the audited `RETRY_WAIT -> DEAD_LETTERED` transition.

## Identity, Idempotency, And Manual Rerun

- `job_id` is stable across attempts for one logical job.
- `attempt_id` is unique for each execution attempt.
- `idempotency_key` remains stable for one logical job, so duplicate clicks or
  duplicate scheduler delivery cannot create a second logical job.
- `transition_request_id` is unique per transition request; idempotent replay
  returns the original result and cannot consume retry budget twice.
- Terminal jobs are never reopened. An owner-approved manual rerun creates a
  new linked job with `parent_job_id`, `rerun_request_id`, `new_job_id`, and
  `new_idempotency_key`. The rerun identity is idempotent over
  `parent_job_id + owner-approved rerun_request_id`; replaying that request
  returns the same linked job. This closes the STAGE-038 same-operation replay
  gap without weakening terminal immutability.

## Retry Eligibility And Parameters

A retry is eligible only when all contract gates are true: current state is
`RETRY_WAIT`, disposition is `eligible`, `retry_pending=true`,
`retry_count < max_retries`, `next_eligible_at` has been reached with evidence,
a versioned policy exists, resource gates pass, the previous claim is inactive,
the previous lock is released or fenced, checkpoint compatibility or safe
restart is proven, compare-and-set succeeds, and append-only audit is ready.

Phase 1 does not invent numeric policy values. Before any Phase 2 runtime,
`max_retries`, `backoff_schedule_seconds`, `jitter_policy`, and the
`retryable_safe_error_codes` allowlist must be explicit, versioned, validated,
and evidence-backed. Missing or unversioned policy means
`NO_AUTOMATIC_RETRY`; the job fails closed for manual review.

## Resource Pause, Dead Letter, And Evidence

`external_drive_offline`, `disk_space_insufficient`, and
`external_api_budget_insufficient` pause only affected work and consume no
retry budget. Automatic resume is forbidden; STAGE-042 owns runtime resume.

A dead-letter record stores bounded metadata refs, not raw content. It retains
job/attempt identity, retry counters, safe error, checkpoint, input/output refs,
policy version, and audit ref. It cannot copy raw payloads, expose secrets,
automatically replay, or delete `FACT_SOURCE`, `MANIFEST`, `EVIDENCE_LEDGER`,
`AUDIT_LOG`, or `REPORT_SNAPSHOT` evidence.

## Ownership Boundary

- STAGE-039 Phase 2 may implement isolated failure classification, retry
  eligibility/decision, scheduler, dead-letter decision, and manual-triage
  metadata over approved control refs.
- STAGE-038 retains queue/worker ownership.
- STAGE-040 owns measured backpressure and fairness.
- STAGE-041 owns lock/lease/fencing runtime.
- STAGE-042 owns automatic lifecycle and resource resume.
- STAGE-043 owns worker-crash recovery.
- STAGE-044 owns cleanup execution.

## Current Run Non-Goals

Mandatory markers:
`NO_PHASE2`, `NO_RETRY_RUNTIME`, `NO_DEAD_LETTER_RUNTIME`,
`NO_QUEUE_RUNTIME`, `NO_WORKER_RUNTIME`, `NO_POSTGRES_CONNECTION`,
`NO_SCHEMA_CHANGE`, `NO_RUNTIME_OUTPUT`, `NO_RAW_METADATA_ACCESS`,
`NO_FAKE_IDS_BUSINESS_DATA`, `NO_GITHUB_UPLOAD`, `NO_APP_REINSTALL`.

This run creates no retry schedule, dead-letter entry, queue record, worker,
job, database row, report, log, checkpoint, cleanup action, API call, PR, issue,
merge, upload, or app entry. `Phase 2 must run separately`.

## Truth Record And Next Gate

- `taskpack_source_read_performed=true`
- `ids_business_source_read_performed=false`
- `raw_metadata_content_accessed=false`
- `retry_scheduler_performed=false`
- `dead_letter_runtime_performed=false`
- `queue_runtime_performed=false`
- `worker_runtime_performed=false`
- `database_connection_performed=false`
- `schema_change_performed=false`
- `runtime_output_written=false`
- `real_ids_business_job_created=false`
- `fake_ids_business_data_used=false`
- `external_api_call_performed=false`
- `github_upload_allowed=false`
- `app_reinstall_allowed=false`

Phase 1 authorizes only the next separate task `IDS-V0_1-STAGE039-P2` at
`IDS-STAGE039-P2-GATE`. It does not authorize production activation.

## Rollback

Revert only the STAGE-039 Phase 1 contract, checker, tests, governance/event
transition, handoff/changelog, and rendered owner views. Preserve STAGE-038 and
earlier evidence, the four owner-authored dirty paths, raw metadata, databases,
runtime content, reports, GitHub state, and app entries.
