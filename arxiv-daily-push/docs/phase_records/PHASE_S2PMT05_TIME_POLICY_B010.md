# PHASE S2PMT05 TIME POLICY B010

## Summary

- Phase: `S2PM`
- Task ID: `S2PMT05-TIME-POLICY-B010`
- Parent task ID: `S2PMT05`
- Inherited finding: `B-010`
- Acceptance ID: `ACC-S2PMT05-STRESS-E2E`
- Model ID: `MOD-ADP-098`
- Formula ID: `FORM-ADP-100`
- Parameter IDs: `PARAM-ADP-915`, `PARAM-ADP-916`, `PARAM-ADP-917`, `PARAM-ADP-918`, `PARAM-ADP-919`
- Status: `completed_local_validation_no_production`
- V7.2 contract: `ADP-PRODUCT-CONTRACT-V7.2`

## Scope

This record remediates inherited P1 finding `B-010` locally by requiring S2PMT05 time-policy evidence to cover:

- A structured Australia/Sydney local schedule: `05:00`, timezone, 3600-second misfire grace, catch-up enabled, and at most one catch-up run per cycle.
- Required local time cases: `NORMAL_0500`, `DST_BACKWARD_FOLD_0`, `DST_BACKWARD_FOLD_1`, `DST_FORWARD_AFTER_GAP`, `MISFIRE_WITHIN_GRACE`, `SLEEP_MISSED_8H`, `FUTURE_HEARTBEAT_GT_TOLERANCE`, `NTP_BACKWARD_WITHIN_TOLERANCE`, `NTP_FORWARD_GT_TOLERANCE`.
- Local business-date `cycle_id` plus UTC instant watermarks.
- DST backward folds recording different UTC offsets while staying one local business date.
- DST forward gap handling by running after the gap with a UTC watermark.
- Future heartbeat over tolerance blocking for owner review.
- NTP backward within tolerance preserving monotonic lease handling and UTC audit.
- NTP forward over tolerance blocking with a clock/timezone failure.
- Misfire inside grace running once with a receipt.
- 8h machine-sleep missed-run recovery catching up one missed cycle only.
- No duplicate M4 watermark across the matrix.

## Non Scope

This task does not install or enable scheduler/launchd, trigger a real catch-up run, send real SMTP, upload Release assets, change public schema, run DB migration, mutate production queues, change source adapters, change ranking, edit `CURRENT.yaml`, edit V7.1/V7.2 contract files, close inherited P0/P1, enable `DAILY_OPERATION`, or claim integrated production acceptance.

## Evidence

- Code: `arxiv-daily-push/src/arxiv_daily_push/stage2_stress_e2e.py`
- Tests: `arxiv-daily-push/tests/test_stage2_stress_e2e.py`
- Run manifest: `governance/run_manifests/ADP-S2PMT05-TIME-POLICY-B010-20260627.json`
- Report hash: `55d54b1bc90fe6d04447da6d3abc4afb4be95269d5a78625ebf81c991042a120`

## Local Report

- Report status: `pass`
- Time policy status: `pass`
- Required time policy cases present: `true`
- Structured schedule policy present: `true`
- Uses UTC cycle watermark: `true`
- Cycle IDs are date scoped: `true`
- DST fold records offset: `true`
- DST gap runs after gap: `true`
- Future heartbeat blocks: `true`
- NTP backward within tolerance allows: `true`
- NTP forward over tolerance blocks: `true`
- Misfire within grace runs once: `true`
- Sleep 8h catch-up bounded: `true`
- Catch-up is bounded: `true`
- No duplicate M4 watermark: `true`
- Scheduler side effects disabled: `true`

## Validation

- `py_compile`: PASS
- Focused S2PMT05 unittest: 16 OK
- Source/board user-center root gate: 14 OK
- Full ADP unittest: 543 OK
- V7.2 validator: PASS
- ADP project governance: 0 errors / 0 warnings
- Changed-only governance semantic: 0 errors / 0 warnings
- Governance sync validator: 0 errors / 0 warnings
- Lean check-render: drift_count 0 / reference_issue_count 0
- YAML/JSON/JSONL/CSV parse: OK
- `git diff --check`: PASS
- Production-side-effect forbidden scan: OK
- Full semantic extractor: NOT COMPLETED after local interrupt at >90 seconds during full-table AST parsing; changed-only semantic governance passed and remains the blocking semantic gate for this run

## Boundaries

Inherited P0/P1 blockers remain open. `S2PMT07`, S2PL final replay/live-run gates, final bundle, independent review, and production acceptance remain blocked until their own evidence gates pass.
