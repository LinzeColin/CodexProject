# Phase 11 Trial Operational Evidence Annotation

Project: `arxiv-daily-push`
Task: `ADP-PHASE11-TRIAL-OPS-EVIDENCE-014`
Acceptance: `ADP-ACC-PHASE11-TRIAL-OPS-EVIDENCE`
Version: `0.11.13`
Generated: `2026-06-22`

## Objective

Provide a fail-closed way to merge weekly/monthly replay, recovery drill, and
other explicit operational evidence refs into the Phase 11 trial evidence
ledger without hand-editing the ledger JSON.

## Implemented

- Added `adp annotate-trial-ops-evidence`.
- Added `adp export-trial-ops-state`.
- Added `adp-trial-ops-evidence-v1` validation for explicit refs.
- Added tests covering final validator unlock when all daily evidence already
  exists, missing-ref blocking, CLI JSON output, and blocked export behavior.
- Updated README, runbook, version files, and governance records.

## Safety Boundary

- The command does not generate weekly reports, monthly reports, recovery drills,
  SMTP sends, Releases, or production acceptance evidence.
- Verified operational flags require non-empty evidence refs.
- Blocked annotations cannot be exported as replacement state.
- The output remains small JSON and does not store media, model weights,
  credentials, Codex auth, GitHub tokens, SMTP secrets, or local cache files.

## Current Status

`pass for trial operational evidence annotation contract`

This phase does not claim that weekly/monthly replay or recovery drill evidence
has actually occurred. It only creates the audited merge path for refs produced
by those future controlled operations.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_ops_target4 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_trial_ops.py arxiv-daily-push/tests/test_trial.py arxiv-daily-push/tests/test_cli.py -q`: 16 focused tests OK.

Full validation results are recorded in the governance run manifest after the
complete local validation suite.

## Remaining Risks

- Real weekly/monthly replay and recovery drill evidence still requires actual
  controlled production operations and durable refs.
- Production acceptance still requires live source pass on the runner, real
  SMTP/Release refs, resource telemetry, weekly/monthly replay, recovery drill,
  and 30 unique daily production evidence entries.

## Rollback

Revert `trial_ops.py`, the new CLI commands, tests, runbook/docs/governance
updates, and restore version `0.11.12`.
