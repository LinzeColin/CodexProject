# STAGE-040 Phase 1 Entry Contract

## Identity

- Stage: `STAGE-040 · 反压策略`
- Task: `IDS-V0_1-STAGE040-P1`
- Acceptance: `ACC-STAGE-040`
- Local code: `D07-S004`
- Domain: `D07 · 任务编排与机器控制`
- Entrance: `IDS 系统运营入口`
- Contract: `ids.backpressure_policy.v0_1.p1`
- State: `PHASE1_ENGINEERING_CONTRACT_RUNTIME_DISABLED`
- Next gate: `IDS-STAGE040-P2-GATE`

## Goal

Define an executable and testable engineering contract that limits new task
admission or requests a legal safe pause when queue pressure, disk capacity,
external API budget, or external-drive availability cannot support work. This
Phase defines decision metadata only. It neither starts nor controls a worker.

## Source Binding

The unique task-pack member
`IDS_v0_1_Final_Chinese_Revised/stages/STAGE-040_反压策略.md` was read from the
named v0.1 archive. Its member SHA256 is
`f0ef128467300d7541796f8d51caca673f838cac2552eba2e415a94a07af614d`.
The archive, Roadmap, and instruction hashes are recorded in the machine
contract. No IDS business source or raw metadata content was read.

## Entry Preconditions

- STAGE-039 is `completed_reviewed_local` and `ACC-STAGE-039` passed locally.
- STAGE-037 `ids.job_state.v1` remains authoritative for legal state changes.
- STAGE-038 owns queue and worker transport.
- STAGE-039 owns retry and dead-letter policy.
- The metadata root remains path-only and untouched.
- The four owner-authored dirty files remain outside this task and commit.

## Phase 1 Deliverables

1. This entry contract.
2. `STAGE040_PHASE1_BACKPRESSURE_SCOPE_BOUNDARY.md`.
3. `backpressure_policy/stage040_backpressure_policy_contract.json`.
4. `scripts/check_backpressure_policy.py`.
5. `tests/test_stage040_backpressure_policy.py`.
6. Minimal governance routing and owner-facing rendered records.

## Stop Boundary

`Phase 2 must run separately`. It must select and evidence every numeric
threshold before exercising an isolated decision slice. This run stops at:

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

`push_allowed=false`. The next task is only `IDS-V0_1-STAGE040-P2` in a
separate run.

## Rollback

Revert only STAGE-040 Phase 1 artifacts and its governance transition. Do not
touch earlier Stages, the raw metadata root, databases, runtime outputs,
reports, the four owner-authored dirty files, GitHub state, or app entries.
