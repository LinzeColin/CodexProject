# arXiv Daily Push V4 Baseline Lock

Status: `LOCKED_FOR_S1_S2_EXECUTION`
Task ID: `S1-02-BASELINE-LOCK-TRACEABILITY-001`
Evidence level: `EXTRACTED`

This file locks the Review8 two-stage pursuing-goal package into the project
tree as the current long-running goal baseline. It is an index and integrity
record, not a second editable fact source. Governance facts remain in
`docs/governance/`.

## Source Package

- Source ZIP: `/Users/linzezhang/Downloads/arxiv_daily_push_two_stage_codex_pack_v4_2026-06-22.zip`
- Source ZIP SHA-256: `3c43f6304d54f3d4fe718fb6ef21413f09723b42f0fd0417ec76ef8d42ded6c7`
- Import date: `2026-06-22`
- Imported by: `S1-02-BASELINE-LOCK-TRACEABILITY-001`

## Locked Files

| File | SHA-256 | Role |
|---|---:|---|
| `START_HERE_MASTER_TASK_PACK_TWO_STAGE_V4.md` | `4de90b3ddac0d38880fe185d5f14c997fca797cbd26f80755bb33b5bc6806e1a` | Human-readable task pack entry point |
| `FULL_PURSUING_GOAL_PROMPT_TWO_STAGE_V4.txt` | `b20add8661983e4797da72c3800d86f343fad3a1c13c62f3b08c8b0320634c3c` | Authoritative two-stage execution prompt |
| `baseline/REFERENCE_OWNER_DECISIONS.rtf` | `ed983f72e6233b6c2d707e69d131be9416f894aa46d39e7d962dcf65c738f7e0` | Owner decision baseline from the review package |
| `baseline/MULTISOURCE_LOCAL_PRODUCTION_TASKPACK_V1.md` | `2900f5c810ea4e87ea8a33b953551c4d822475e7063547e9cbc1627100f96bab` | Prior multi-source local production task pack |

The hashes above are checked by governance tests. Any content change must be
intentional, task-bound, and recorded in `development_events.jsonl`.

## Accepted Deltas

Only the following deltas are accepted relative to the imported baseline:

| Delta ID | Evidence level | Decision |
|---|---|---|
| `D-001` | `EXTRACTED` | Execute arXiv first, then promote source and board coverage only after arXiv gates pass. |
| `D-002` | `PROPOSED` | Treat `2026-06-30` as a target date only after owner confirmation; it is not current completion evidence. |
| `D-003` | `EXTRACTED` | Before new-machine migration, keep work low-resource: code, schema, tests, fixtures, governance, and small smoke evidence only. |
| `D-004` | `EXTRACTED` | Add arXiv/source/board promotion gates while preserving the final 30-day plus two live-day acceptance requirement. |

## Stage Contract

- Stage 1: arXiv single-source vertical slice and production acceptance.
- Stage 2: source/board promotion and final full-system acceptance.
- Final target state: `PRODUCTION_ACCEPTED -> DAILY_OPERATION`.
- Current state after S1-02: `NOT_PRODUCTION_ACCEPTED`.

S1-02 binds the baseline and traceability. It does not implement owner controls,
SQLite storage, a new source registry, scheduler installation, backup/restore,
or production acceptance.

## Current Evidence Boundary

GitHub Actions run `27932072771` completed successfully on `main` for the
manual Release plus Gmail SMTP test workflow at commit
`bbdc69bb49758e4ad84f91f45fbe7921b82b1414`.

This is evidence for a controlled manual delivery test only. It is not evidence
for the final 30-day trial, two live days, enabled production schedule, or
full source/board promotion.
