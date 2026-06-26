# PHASE LOCAL RUNNER USER CENTER SYNC GATE

## Summary

- task_id: `LOCAL-RUNNER-USER-CENTER-SYNC-GATE`
- acceptance_id: `ADP-ACC-S1P5T05-LOCAL-PRODUCTION-MIGRATION-PREP`
- status: `local_gate_enforced`
- V7.2 contract: `ADP-PRODUCT-CONTRACT-V7.2`
- created_at: `2026-06-26 18:45:19 Australia/Sydney`

The local daily runner now treats GitHub shallow user-center learning snapshot
synchronization as a pass condition. A daily run cannot report `pass` unless
the shallow `用户中心/复习行动与收益.md` page is synchronized from real
S2PJT02/S2PJT03 review/action/asset/ROI reports.

The same synchronization gate also requires every generated, selected, or
queued candidate in the daily input report to carry six-factor ROI score
details. Missing `roi_signals`, missing `roi_component_weights`, or a
`roi_total_score` that cannot be recomputed from the six factors keeps
`user_center_sync_ready=false` and blocks real SMTP.

## Scope

- Add a local runner fail-closed gate for `user_center_sync_ready`.
- Block real SMTP before send when user-center synchronization is missing or
  incomplete.
- Require six-factor ROI score details for generated, selected, and queued
  candidates before user-center synchronization can pass.
- Keep dry-run preview generation possible, but mark the daily report blocked
  when the owner-facing GitHub page is not synchronized.
- Add focused tests for successful sync and missing-sync blocked behavior.

## Non Scope

No scheduler installation, no production SMTP enablement, no public schema
change, no DB migration, no production queue mutation, no CURRENT pointer
change, no V7.1/V7.2 contract-file edit, no Release upload, no daily operation
enablement, and no integrated production acceptance claim.

## Gate Rule

`validate_local_runner_report` now requires passing daily reports to include
`user_center_sync_ready=true`. When sync inputs are missing, stale, or still
contain `待今日运行快照写入`, the local daily report remains blocked and real
SMTP send is not attempted.

Candidate score detail is part of the same gate. The local runner checks
`relevance`, `learning_value`, `economic_conversion_rate`, `roi`,
`interdisciplinary_value`, and `explainability` against their configured
weights and the candidate `roi_total_score`. The gate fails closed instead of
accepting a total-only score.

## Evidence

- `arxiv-daily-push/src/arxiv_daily_push/local_runner.py`
- `arxiv-daily-push/tests/test_local_runner.py`
- `governance/run_manifests/ADP-LOCAL-RUNNER-USER-CENTER-SYNC-GATE-20260626.json`

## Validation

- py_compile local runner and focused tests: PASS
- focused local runner tests: 7 OK
- root no-open-PR rule test: 1 OK

## Boundaries

This is a local readiness gate. It improves fail-closed behavior for human
readability and owner GitHub status, but it does not claim that daily operation
is enabled or that Stage 2 production acceptance has passed.
