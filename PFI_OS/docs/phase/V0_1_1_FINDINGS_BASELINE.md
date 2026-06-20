# v0.1.1 Findings Baseline

Schema: `PFIOSV011FindingsBaselineV1`

Status: review baseline, not release-ready closure.

As of: 2026-06-20 Australia/Sydney

## Goal

Create a differential baseline from the v0.2 handoff and iteration packs so the
next run can execute one PFI issue at a time without losing the P0/P1 finding
state.

## Scope

- Source packs: `PFI_OS_CODEX_HANDOFF_v0.2.zip` and
  `PFI_OS_CODEX_ITERATION_PACK_v0.2.zip`.
- Findings included: P0 and P1 only.
- Baseline count: 12 P0 findings and 18 P1 findings.
- Completion model: open and partial findings remain explicit follow-up gates.

## Current Status Counts

| Status | Count |
| --- | ---: |
| Closed | 1 |
| Partial | 18 |
| Open | 11 |

## Issue Routing

The next single issue remains `PFI-001`: reproducible environment, CI,
dependency lock, and secret-scan gates. No later PFI issue should be treated as
closed by this baseline.

## Product Corrections Included

- PFI Web Shell is now the default runtime path.
- Downloads and Applications app launchers bind to the current `PFI_OS`
  worktree and use `StartPFIOS.command`.
- Homepage cache ingestion no longer falls back to retired command-center
  latest cache files.
- Retired value-ledger and command-center metadata are hidden from the active
  homepage read model when stale local SQLite rows exist.

## Policy Overrides

- Future live auto-ordering is rejected for this product line. Replacement:
  human-reviewed `OrderIntent` or `DecisionProposal` only.
- Private data in public Git is rejected. Replacement: `$PFI_OS_DATA_HOME` for
  private data and sanitized fixtures or summaries in Git.

## Safety Boundary

- Research-only.
- Human review required.
- No live trading.
- No autonomous order execution.
- No broker calls.
- No payment, bank, betting, or external account mutation.
- No holdings mutation.
- No private runtime artifacts or secrets committed to public Git.
