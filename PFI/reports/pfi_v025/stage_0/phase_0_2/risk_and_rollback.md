# PFI v0.2.5 Stage 0 Phase 0.2 Risk and Rollback

## Current candidate state

- Contract: `PFI-V025-STAGE0-PHASE02-ACTIVE-REQUIREMENTS`.
- Acceptance: `ACC-PFI-V025-S0-P02-ACTIVE-CONTRACT`.
- Current result: Phase 0.2 candidate validation passed; atomic commit and post-commit attestation remain pending, with no Stage, release, install, upload, or production acceptance claim.
- Exact scope: the 20 paths in `changed_files.txt`; every 21st path is a stop condition.

## Open conflicts

- Owner views, release identity, App identity, runtime listeners, stale route markers, and target/current route gaps remain `blocked` and keep their named Roadmap resolution tasks.
- Governance scope is `approved_pending_validation` and continues to block the Phase candidate until exact-path, selective governance, atomic-commit, and post-commit attestation gates pass.
- The legacy parameter consistency test baseline (`3 passed / 5 failed`) belongs to `PFI-V025-CONFLICT-OWNER-VIEWS / S0-P3-T1`; this run does not alter owner files, the test, or its renderer.
- The direct PyYAML comparison cannot run in the available Python environments. No package is installed; equivalent old/new structure and value assertions use the repository fallback YAML parser.

## Guarded temporary paths

- Protected metadata baseline: `/private/tmp/pfi-v025-s0p02-guard-82869ffdb37e/before.json`.
- Historical regression temp roots match `/private/tmp/pfi-v025-s0p02.*` and are removed with preserved test exit status.
- Recorded governance preflight, candidate review, CI shadow, and final attestation may use only their plan-declared `/private/tmp/pfi-v025-s0p02-*` roots and must clean registered worktrees.

## Stop conditions

- Source digest, contract identity, PHASE_BASE, exact path ledger, projection parity, schema, semantic route, privacy, append-only event, or protected metadata mismatch.
- Any data/DB/App/runtime/installer/browser/real-financial side effect or materialization.
- Any missing governance companion, non-zero focused gate, review finding, remote drift that violates ancestry/PFI quietness, or evidence that refers to a future result.
- Any attempt to enter Phase 0.3 in this run.

## Rollback

Before commit, remove only the exact 20-path candidate diff and restore `PHASE_BASE`; preserve external inputs and protected roots. After commit, never rewrite or delete historical event/evidence lines: create one append-only-safe compensating commit that records the failed acceptance, restores the prior active contract view, and retains the original candidate commit and evidence references. No automatic push, App rollback, or remote rewrite is authorized.

## Candidate validation results

- Isolated historical Phase 0.2 regression: `3 passed`.
- Task Pack active/evidence schemas, full semantic/type gate, current route/shell snapshot, and cross-document projection parity: pass.
- Recorded sparse-aware selective shadow: project governance and governance sync each reported `errors: 0 / warnings: 0`; the temporary registered worktree was removed.
- These are pre-commit candidate facts only. Atomic commit review, commit creation, CI-shadow proof, protected-baseline recheck, current-remote recheck, and external final attestation remain pending.
