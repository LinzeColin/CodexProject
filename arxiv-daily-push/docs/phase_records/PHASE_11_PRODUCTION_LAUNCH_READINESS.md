# Phase 11 Production Launch Readiness

Project: `arxiv-daily-push`
Task: `ADP-PHASE11-PRODUCTION-LAUNCH-READINESS-020`
Acceptance: `ADP-ACC-PHASE11-PRODUCTION-LAUNCH-READINESS`
Version: `0.11.19`
Status: `completed`

## Scope

- Added `adp-production-launch-readiness-v1` in
  `src/arxiv_daily_push/production_launch.py`.
- Added `adp plan-production-launch`.
- Added `schemas/production_launch.schema.json`.
- Added tests for passing launch readiness, current draft/unmerged PR blocking,
  head SHA mismatch blocking, durable ref checks, no-secret/no-auth safety, and
  CLI JSON output.
- Updated the production trial runbook, README, changelog, version files, and
  governance records.

## Acceptance Evidence

- A passing launch readiness report requires:
  - explicit `--confirm-launch`;
  - current PR metadata with `state`, `merged`, `draft`, `base`, and `head_sha`;
  - PR non-draft status;
  - PR merged into `main`;
  - observed PR `head_sha` matching `--expected-head-sha`;
  - a passing `adp-trial-start-workflow-v1` workflow contract;
  - durable refs for default branch, private runner, SMTP secrets readiness,
    Release target readiness, GitHub workflow variables readiness, and the
    default-branch trial start workflow.
- The gate performs no side effects, logs no secret values, does not read Codex
  auth, and does not claim production acceptance.

## Validation

- Focused command:
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_production_launch_target PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_production_launch.py arxiv-daily-push/tests/test_trial_start_workflow.py arxiv-daily-push/tests/test_cli.py -q`
- Focused result: `12 tests OK`.

Full project and governance validation is recorded in
`governance/run_manifests/ADP-PHASE11-PRODUCTION-LAUNCH-READINESS-20260622.json`.

## Current Boundary

This phase proves the launch readiness contract and a deterministic way to
document the current GitHub blockers. It does not merge the PR, dispatch
workflows, send SMTP, create Releases, fetch arXiv, mutate the trial ledger,
generate media, retain local cache/model artifacts, or claim 30-day operational
acceptance.

## Current Observed GitHub State

As of this implementation run, PR #14 is open, draft, unmerged, and has head
commit `fc5a10065073f08772ea6e482f4d251e2c331003`. The new gate intentionally
blocks launch while that remains true.

## Remaining Risks

- Real launch still requires marking the PR ready, merging it into `main`,
  provisioning the private runner, setting GitHub SMTP secrets and Release/
  workflow variables, and archiving durable readiness refs.
- Production acceptance remains blocked until a default-branch trial start
  workflow run passes, live source passes on the runner, real SMTP and Release
  refs exist, resource telemetry is archived, weekly/monthly replay and recovery
  drill evidence pass, and 30 unique daily production evidence entries are
  validated.

## Rollback

Revert production launch readiness gate, CLI command, schema, tests,
runbook/docs/governance updates, and restore version `0.11.18`.
