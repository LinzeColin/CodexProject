# STAGE-039 Phase 2 - Isolated Retry And Dead-Letter Slice

## Contract Identity

- Stage: `STAGE-039 · 重试与死信策略`
- Task: `IDS-V0_1-STAGE039-P2`
- Acceptance: `ACC-STAGE-039`
- Policy: `ids.retry_policy.v0_1.stage039.p2`
- Mode: `ISOLATED_NON_PRODUCTION_RETRY_DEAD_LETTER_METADATA_SLICE`
- Machine contract:
  `retry_dead_letter/stage039_retry_dead_letter_runtime_contract.json`
- Checker: `KM_IDSystem/scripts/check_retry_dead_letter_runtime.py`
- Next separate gate: `IDS-STAGE039-P3-GATE`

The approved taskpack member remains
`IDS_v0_1_Final_Chinese_Revised/stages/STAGE-039_重试与死信策略.md`
with SHA-256
`504caf72a6aeab67a650b4b096e728f03269f6ca8798f6e8a5c51210c8ddd7d9`.
All Stage037, Stage038, and Phase 1 upstream bindings are exact-hash checked
before the slice can execute.

## Parameter Selection

| Parameter | Value | Reason | Fact level |
|---|---:|---|---|
| `max_retries` | `2` | Caps one logical job at three attempts and bounds duplicate load. | `PROPOSED` |
| `backoff_schedule_seconds` | `[5, 30]` | Separates a short transient retry from a sustained transient retry without a busy loop. | `PROPOSED` |
| `jitter_policy` | `DETERMINISTIC_BOUNDED_HASH_JITTER_V1` | Keeps tests and idempotent decisions deterministic while spreading eligibility times. | `PROPOSED` |
| retryable allowlist | `TRANSIENT_DEPENDENCY_UNAVAILABLE`, `TRANSIENT_OPERATION_TIMEOUT` | Exact safe-code matching only; unknown codes default to no automatic retry. | `PROPOSED` |

These values are a conservative local engineering safety boundary for the
isolated slice. They are not production-calibrated and are not derived from
IDS business records. Production activation remains prohibited; calibration
against approved operational evidence is required before any later production
use. Rollback is `NO_AUTOMATIC_RETRY`.

The policy is registered as `MOD-008`, `FORM-008`, and `PARAM-050..055` in
the project governance facts and legacy registries. Its status is `planned`,
so the existing `7` active models, `7` active formulas, and `49` active
parameters remain unchanged. The owner-rendered `模型参数文件.md` exposes the
six new proposal-level values without
misrepresenting them as production-active.

The delay formula is:

```text
lower = max(1, ceil(base_delay / 2))
delay = lower + (
  sha256(policy_version | job_id | retry_ordinal)
  mod (base_delay - lower + 1)
)
```

For each retry ordinal, the result is deterministic, at least one second,
not greater than the configured ceiling, and cannot extend beyond the two
configured retries.

## Controlled Evidence

The only job input is the Git-tracked control reference
`repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE1_RETRY_DEAD_LETTER_SCOPE_BOUNDARY.md`.
Stage038 performs one isolated in-memory transport-prerequisite admission with
its reviewed `max_retries=0` envelope. Stage039 preserves that queue-entry ref
but derives a different control `job_id` from the Stage038 job ID, policy
version, and acceptance ID. The isolated Stage039 in-memory policy snapshot is
therefore initialized with `max_retries=2`; no persistent job is created and no
existing job identity or immutable retry budget is mutated.
Stage037 then evaluates candidate-only CAS transitions for:

1. `QUEUED -> CLAIMED -> RUNNING`;
2. retryable failure `RUNNING -> RETRY_WAIT`, without budget consumption;
   replaying the same failure transition request returns the original result;
3. due admission `RETRY_WAIT -> QUEUED`, atomically incrementing
   `retry_count` exactly once;
4. idempotent replay of the same admission request, without another increment;
5. exhaustion `RUNNING -> RETRY_WAIT -> DEAD_LETTERED`.

The checker does not sleep. It supplies an explicit observed epoch to the
deterministic scheduler and evaluates the recorded eligibility epoch. The
controlled failure retains input refs, emits no output refs, records a safe
error ref, and records a checkpoint digest of the tracked control document.
No source body is copied into retry or dead-letter metadata.

## Classification And Owner Status

| Condition | Action | Final or pending state | Chinese status |
|---|---|---|---|
| exact retryable allowlist match with budget | `SCHEDULE_RETRY` | `RETRY_WAIT` | `等待重试` |
| due eligibility and resource gates pass | `ADMIT_RETRY` | `QUEUED` | `等待处理` |
| approved resource pause reason | `PAUSE_RESOURCE_GATE` | `PAUSED` | `已暂停` |
| exact permanent allowlist match | `FAIL_TERMINAL` | `FAILED` | `处理失败` |
| unknown/missing code or policy | `REQUIRE_MANUAL_REVIEW` | `FAILED` or no transition | `处理失败` |
| exhausted budget | `DEAD_LETTER` | `DEAD_LETTERED` | `需要人工处理` |

Message substrings never classify a failure. Terminal states remain immutable.
Manual rerun still requires a new linked-job identity under the Phase 1
contract; this Phase does not create a rerun candidate or terminal rerun job.

## Scope Proof

- in-memory control metadata only;
- one Stage038 isolated admission; no Stage038 production worker activation;
- Stage037 candidate transitions only; no database or registry persistence;
- no PostgreSQL connection, schema change, queue file, runtime output, or API;
- no read, list, hash, open, copy, mutation, or expansion of `IDS_MetaData`;
- no real IDS business job and no fake IDS business data;
- no measured backpressure/fairness, production lock/lease/fencing, automatic
  resume, worker-crash recovery, or cleanup execution;
- no GitHub upload, PR, merge, issue, or app reinstall.

Stage040 owns measured backpressure, Stage041 owns production lock/lease/
fencing, Stage042 owns automatic resume/lifecycle, Stage043 owns crash
recovery, and Stage044 owns cleanup execution.

## Verification State

- TDD red: `10` tests failed because the Phase 2 checker and contract did not
  yet exist; this was the expected implementation-start failure.
- Phase 2 checker: `16/16` contract checks true, `contract_valid=true`,
  `slice_valid=true`, final state `DEAD_LETTERED`, and final
  `retry_count=2`.
- Stage039: `20/20` tests passed.
- Stage005: `146/146` governance regression tests passed.
- Stage031-039 aggregate: `227/227` tests passed after this phase's controlled
  files were bound to the Git index; the pre-index review failures were the
  expected historical delivery-binding gate and cleared after scoped staging.
- Stage026-030 compatibility: `75/75` tests passed.
- Full IDS v0.1 discovery: `633/633` tests passed.
- Owner render: `drift_count=0`, `reference_issue_count=0`.
- Events: `184` JSONL records, `0` duplicate IDs, exactly `1` Phase 2 event.
- Python in-memory compilation: `4/4` changed Python files passed without
  writing `__pycache__`.
- `git diff --cached --check` passed.
- Changed-only semantic governance: `errors=0`, `warnings=0`.
- Pre-commit Phase 2 self-review repaired two Important findings: Stage038 and
  Stage039 no longer reuse a logical job identity across different immutable
  `max_retries` values, and first failure-transition results are now written to
  the same in-memory idempotency ledger used for replay.
- `push_allowed=false`.
- Phase 3 did not run.

## Rollback

Disable automatic retry, then revert only the Phase 2 contract, checker,
evidence, tests, and Phase 2 governance transition. Preserve Phase 1,
Stage037/038, source/evidence files, raw metadata, databases, runtime paths,
the four owner-authored dirty files, GitHub state, and app entries.
