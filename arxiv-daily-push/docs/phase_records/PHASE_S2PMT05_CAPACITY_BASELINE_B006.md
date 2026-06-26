# PHASE S2PMT05 CAPACITY BASELINE B006

## Summary

- Phase: `S2PM`
- Task ID: `S2PMT05-CAPACITY-BASELINE-B006`
- Parent task ID: `S2PMT05`
- Inherited finding: `B-006`
- Acceptance ID: `ACC-S2PMT05-STRESS-E2E`
- Model ID: `MOD-ADP-098`
- Formula ID: `FORM-ADP-100`
- Parameter IDs: `PARAM-ADP-814`, `PARAM-ADP-910`, `PARAM-ADP-911`, `PARAM-ADP-912`
- Status: `completed_local_validation_no_production`
- V7.2 contract: `ADP-PRODUCT-CONTRACT-V7.2`

## Scope

This record remediates inherited P1 finding `B-006` locally by requiring S2PMT05 capacity-baseline evidence to cover:

- Formal load, stress, spike, and soak rows.
- Required `1x`, `2x`, and `5x` capacity multipliers.
- Throughput, p95 latency, queue age, memory, disk, and error-rate metrics.
- Queue age bounded at `1800` seconds and recoverable.
- Error rate at or below `0.001`.
- Accelerated local 24h soak coverage.
- Spike shedding limited to rebuildable noncritical work while preserving durable evidence.

## Non Scope

This task does not execute a live production load test, execute a real 24h wall-clock production soak, install or enable scheduler/launchd, send real SMTP, upload Release assets, execute production restore, change public schema, run DB migration, mutate production queues, change source adapters, change ranking, edit `CURRENT.yaml`, edit V7.1/V7.2 contract files, close inherited P0/P1, enable `DAILY_OPERATION`, or claim integrated production acceptance.

## Evidence

- Code: `arxiv-daily-push/src/arxiv_daily_push/stage2_stress_e2e.py`
- Tests: `arxiv-daily-push/tests/test_stage2_stress_e2e.py`
- Run manifest: `governance/run_manifests/ADP-S2PMT05-CAPACITY-BASELINE-B006-20260627.json`
- Report hash: `4d6b2a4f4771c2d8fb08ecc23335da3d987330a4385f90b9a773928ed000935a`

## Local Report

- Report status: `pass`
- Capacity baseline status: `pass`
- Required multipliers: `1`, `2`, `5`
- Max queue age seconds: `1800`
- Max error rate: `0.001`
- Real 24h wall-clock run: `false`
- Accelerated local soak hours: `24`
- New checks:
  - `load_stress_spike_soak_rows_present=true`
  - `required_multipliers_present=true`
  - `throughput_latency_queue_metrics_present=true`
  - `queue_age_bounded_and_recoverable=true`
  - `memory_disk_metrics_present=true`
  - `error_rate_within_budget=true`
  - `soak_duration_covered=true`
  - `spike_sheds_rebuildable_only=true`

## Validation

- `py_compile`: PASS
- Focused S2PMT05 unittest: 14 OK
- Source/board user-center root gate: 14 OK
- Full ADP unittest: 541 OK
- V7.2 validator: PASS
- ADP project governance: 0 errors / 0 warnings
- Changed-only governance semantic: 0 errors / 0 warnings
- Governance sync validator: 0 errors / 0 warnings
- Lean check-render: drift_count 0 / reference_issue_count 0
- YAML/JSON/JSONL/CSV parse: OK
- `git diff --check`: PASS
- Production-side-effect forbidden scan: OK

## Boundaries

Inherited P0/P1 blockers remain open. `S2PMT07`, S2PL final replay/live-run gates, final bundle, independent review, and production acceptance remain blocked until their own evidence gates pass.
