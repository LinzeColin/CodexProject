# STAGE-040 Phase 3 - Backpressure Scenario Validation

## Contract Identity

- Stage: `STAGE-040 · 反压策略`
- Task: `IDS-V0_1-STAGE040-P3`
- Acceptance: `ACC-STAGE-040`
- Policy: `ids.backpressure_policy.v0_1.stage040.p2`
- Mode: `ISOLATED_NON_PRODUCTION_BACKPRESSURE_SCENARIOS`
- Scenario contract:
  `backpressure_policy/stage040_backpressure_scenarios.json`
- Checker: `KM_IDSystem/scripts/check_backpressure_scenarios.py`
- Next separate gate: `IDS-STAGE040-P4-GATE`

The approved taskpack and roadmap were reverified before implementation. The
unique Stage040 taskpack member remains
`IDS_v0_1_Final_Chinese_Revised/stages/STAGE-040_反压策略.md` with SHA-256
`f0ef128467300d7541796f8d51caca673f838cac2552eba2e415a94a07af614d`.
The scenario contract requires the committed Phase 2 commit and exact hashes
for the Phase 2 contract, checker, evidence, and reviewed Stage038/039 scenario
sources.

## Scenario Evidence

| Scenario | Controlled result | Physical or production action |
|---|---|---|
| duplicate click | one in-memory decision; replay keeps the same decision and checkpoint | no job or persistent write |
| worker exception boundary | actual isolated worker exception is replayed from reviewed Stage038/039 evidence; terminal failure remains immutable | no process termination; crash recovery stays with `STAGE-043` |
| external drive offline | a queued control candidate requests `QUEUED -> PAUSED` | no physical drive removal |
| disk pressure | actual project-filesystem free-space observation matches the formula; an exact low-disk boundary requests pause | no disk allocation |
| external API budget | a running control candidate requests `RUNNING -> PAUSE_REQUESTED -> PAUSED` | no external API call |
| same-source concurrency | `ARCHIVE`, `PARSE`, `INDEX`, and `REPORT` over one tracked input are throttled without job creation | no production lock runtime |
| reviewed lock conflict | one isolated control invocation and three conflicts share one lock key | production lock/lease/fencing stays with `STAGE-041` |
| protected cleanup | fact source, manifest, evidence ledger, report snapshot, and audit log return `PROTECTED_ARTIFACT` | no cleanup or delete |

The worker exception is an actual isolated exception, not a process crash. The
actual project-filesystem free-space observation is read-only. Drive, low-disk
boundary, and API-budget conditions are bounded control metadata, not physical
failure claims. The checker never removes a drive, allocates disk, calls an
external API, kills a process, invokes cleanup, or exposes a delete function.

The same-source lock proof re-executes the reviewed Stage039 Phase 3 checker,
which itself binds the Stage038 isolated lock registry. Stage040 consumes that
proof but does not take ownership of production locks, leases, or fencing. The
protected cleanup evaluator verifies exact Git-tracked refs and always returns
a denial without a delete attempt.

## Scope Proof

- no read, list, hash, open, copy, mutation, or expansion of `IDS_MetaData`;
- no real IDS business source or job and no fake IDS business data;
- no Stage040 queue or worker runtime, process termination, physical drive
  removal, disk allocation, external API call, cleanup/delete, persistence, or
  database connection;
- no Stage041 production lock/lease/fencing, Stage042 automatic resume,
  Stage043 crash recovery, or Stage044 cleanup execution;
- no Phase 4, whole-stage review, batch gate, GitHub upload, PR, merge, issue,
  or app reinstall;
- `push_allowed=false`.

## Verification State

- TDD RED: `11/11` tests failed because the Phase 3 contract, checker,
  evidence, and governance transition did not yet exist.
- GREEN: `18/18` contract checks true, `8/8` scenarios passed, focused P3
  `11/11`, Stage040 `36/36`, Stage005 `148/148`, Stage037 `39/39`, Stage038
  review `5/5`, and Stage039 review `6/6`.
- Stage031-039 aggregate `254/254`, Stage026-030 compatibility `75/75`, and full
  IDS v0.1 discovery `699/699` passed.
- Stage004 legacy scan returned `valid=true`. Direct Stage005 failed closed only
  on the four preserved owner dirty paths; scoped Stage005 returned `valid=true`.
- Events: `190` JSONL records, `0` duplicate IDs, exactly one Phase 3 event.
- Owner render: `drift_count=0`, `reference_issue_count=0`; changed-only
  governance: `errors=0`, `warnings=0`; Git diff checks passed.
- Self-review repaired one Important evidence gap by exposing
  `stage038_isolated_worker_exception_replayed=true` and
  `reviewed_control_lock_proof_replayed=true` in the machine report, rather than
  leaving those truths only in governance text.
- Phase 4 did not run.

## Rollback

Revert only the Phase 3 contract, checker, evidence, tests, and governance
transition. Preserve Phase 1-2, Stage037-039, raw metadata, databases, runtime
paths, owner-authored dirty files, GitHub state, and app entries.
