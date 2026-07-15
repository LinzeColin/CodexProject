# STAGE-039 Phase 3 - Retry And Dead-Letter Scenario Validation

## Contract Identity

- Stage: `STAGE-039 · 重试与死信策略`
- Task: `IDS-V0_1-STAGE039-P3`
- Acceptance: `ACC-STAGE-039`
- Policy: `ids.retry_policy.v0_1.stage039.p2`
- Mode: `ISOLATED_NON_PRODUCTION_RETRY_DEAD_LETTER_SCENARIOS`
- Scenario contract:
  `retry_dead_letter/stage039_retry_dead_letter_scenarios.json`
- Checker: `KM_IDSystem/scripts/check_retry_dead_letter_scenarios.py`
- Next separate gate: `IDS-STAGE039-P4-GATE`

The approved taskpack, roadmap, and instruction bindings were reverified before
implementation. The exact Stage039 taskpack member remains
`IDS_v0_1_Final_Chinese_Revised/stages/STAGE-039_重试与死信策略.md` with
SHA-256
`504caf72a6aeab67a650b4b096e728f03269f6ca8798f6e8a5c51210c8ddd7d9`.
The checker also requires exact hashes for the committed Phase 2 contract,
checker, evidence, and reviewed Stage038 scenario boundary.

## Scenario Evidence

| Scenario | Expected controlled result | Physical or production action |
|---|---|---|
| duplicate retry reservation and admission | replay preserves one reservation and one budget increment | none |
| worker exception crash boundary | actual isolated worker exception is observed; process crash recovery is deferred to `STAGE-043` | no process termination |
| external drive offline | pending retry pauses without consuming retry budget | no drive removal |
| low disk | actual free-space observation feeds the controlled low-disk gate; pending retry pauses | no disk allocation |
| external API budget | pending retry pauses without consuming retry budget | no API call |
| same-source cross-operation lock | one `ARCHIVE` execution; `PARSE`, `INDEX`, and `REPORT` receive resource conflicts | no production lock runtime |
| retry exhaustion | retry count reaches exactly `2`, then becomes `DEAD_LETTERED` | in-memory control metadata only |
| terminal replay | terminal state stays immutable | no terminal reopen |
| manual rerun | owner-authorized, new-lineage candidate is idempotent | no job creation, queue write, or database write |
| protected cleanup | fact source, manifest, evidence ledger, report snapshot, and audit log are denied | no delete attempt or delete API |

Stage038 supplies the real isolated worker exception and the real local
free-space observation. A worker exception is not evidence of process
termination or process-crash recovery. External-drive and API-budget cases are
control-gate inputs only. The checker never kills a process, removes a drive,
allocates disk, calls an external API, invokes cleanup, or deletes a file.

The protected cleanup evaluator verifies that each exact `repo:` reference is
Git-tracked, then returns `PROTECTED_ARTIFACT`. It does not expose a deletion
path. The manual-rerun evaluator produces only an in-memory candidate with a
new job ID and idempotency key linked to the terminal parent; it cannot create
or persist a job.

## Scope Proof

- no read, list, hash, open, copy, mutation, or expansion of `IDS_MetaData`;
- no real IDS business source or job and no fake IDS business data;
- no process termination, physical drive removal, disk allocation, external
  API call, cleanup runtime, persistent queue write, or database connection;
- no Stage040 measured backpressure/fairness, Stage041 production lock/lease/
  fencing, Stage042 automatic resume, Stage043 crash recovery, or Stage044
  cleanup ownership;
- no Phase 4, whole-stage review, GitHub upload, PR, merge, issue, or app
  reinstall.

## Verification State

- TDD red: `11/11` tests initially failed because the Phase 3 contract,
  checker, evidence, and governance transition did not yet exist.
- Phase 3 checker: `14/14` contract checks true, `10/10` scenarios passed,
  `scenario_validation_valid=true`, next gate `IDS-STAGE039-P4-GATE`.
- Stage039: `31/31` tests passed.
- Stage005: `146/146` governance regression tests passed. The direct validator
  fails closed only on the four preserved owner-authored dirty paths; its
  source, event, phase-state, boundary, and project-path checks are otherwise
  clean.
- Stage031-039 aggregate: `238/238` tests passed.
- Stage026-030 compatibility: `75/75` tests passed (`63` for Stage026-029 and
  `12` for Stage030).
- Full IDS v0.1 discovery: `644/644` tests passed.
- Owner render: `drift_count=0`, `reference_issue_count=0`.
- Events: `185` JSONL records, `0` duplicate IDs, exactly `1` Phase 3 event.
- Python in-memory compilation: `4/4` changed Python files passed without
  writing runtime output.
- `git diff --cached --check` passed.
- Changed-only semantic governance: `errors=0`, `warnings=0`.
- Pre-commit self-review repaired one Important ambiguity: a manual-rerun
  candidate now exposes `proposed_initial_state=CREATED` instead of a
  misleading `job_state=CREATED`, while `candidate_only=true`,
  `persisted=false`, and `job_created=false` remain machine-checked.
- `push_allowed=false`.
- Phase 4 did not run.

## Rollback

Revert only the Phase 3 contract, checker, evidence, tests, and Phase 3
governance transition. Preserve Phase 1-2, Stage037/038, source and evidence
files, raw metadata, databases, runtime paths, owner-authored dirty files,
GitHub state, and app entries.
