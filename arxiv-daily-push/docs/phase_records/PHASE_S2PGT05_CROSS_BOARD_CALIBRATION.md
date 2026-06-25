# PHASE S2PGT05 Cross-Board Calibration

## Scope

S2PGT05 defines a private backend percentile-calibration, source-balance, waiting-credit, deterministic ordering, and explainable queue evidence layer after S2PGT04. The report builder validates upstream delta resonance evidence, B1-B6 board coverage, D1-D4 source-domain coverage, selected/queued/deferred queue decisions, readable reasons, selected-source share caps, waiting-credit bounds, stable queue hashing, and no-production/no-schema/no-email-frontstage side-effect gates.

This is not the production ranking algorithm, not a real queue mutation, not a public schema migration, and not an Email V1 runtime or frontstage change. It does not send SMTP, install schedulers, upload Releases, change V7.2 contract files, or claim `INTEGRATED_PRODUCTION_ACCEPTED`.

## Implementation

- Added `S2PGT05` constants, builder, validator, runner, and report persistence in `stage2_sources.py`.
- Added `stage2-cross-board-calibration` CLI in `cli.py`.
- Added focused tests for deterministic pass, source-balance/readable reasons, blocking invalid candidate input and side effects, persistence, and CLI JSON output.
- Added model/formula/parameter governance entries for `MOD-ADP-074`, `FORM-ADP-076`, and `PARAM-ADP-545` through `PARAM-ADP-559`.

## Gates

- `upstream_delta_resonance_gate`: S2PGT04 delta resonance evidence passes.
- `percentile_calibration_gate`: B1-B6 boards are observed and each candidate has a bounded board-percentile score.
- `source_balance_gate`: D1-D4 source domains are observed and selected source share stays at or below 50%.
- `waiting_credit_gate`: waiting days and waiting credit remain bounded.
- `queue_reason_gate`: selected, queued, and deferred decisions each have readable reason codes.
- `deterministic_order_gate`: calibrated ranks are stable and contiguous.
- `no_side_effect_gate`: public schema, production queue, ranking algorithm, SMTP, scheduler, Release, production, V7.2 contract, and Email V1 frontstage side effects remain false.

## Validation

- `PYTHONPATH=arxiv-daily-push/src python3 -m py_compile arxiv-daily-push/src/arxiv_daily_push/stage2_sources.py arxiv-daily-push/src/arxiv_daily_push/cli.py arxiv-daily-push/tests/test_stage2_sources.py` PASS.
- `PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_stage2_sources.py -q` PASS, 87 tests OK.
- py_compile PASS; focused Stage2 source tests 87 OK; full arxiv-daily-push unittest 316 OK; semantic extractor 76 formulas / 542 parameters checked; V7.2 validator PASS; ADP project governance 0 errors / 0 warnings; changed-only governance semantic 0 errors / 0 warnings; lean check-render drift 0 reference_issue_count 0; JSON/YAML/JSONL/CSV parse OK; forbidden path scan clean; no __pycache__/.pyc; git diff --check PASS.

## Acceptance

`ACC-S2PGT05-CALIBRATION` is accepted only as private cross-board calibration and explainable queue evidence. It proves deterministic board-percentile calibration, source balance, waiting credit, selected/queued/deferred reasons, and no side effects without granting public schema migration, production ranking changes, production queue mutation, source-domain production inclusion, SMTP, scheduler, Release, or `INTEGRATED_PRODUCTION_ACCEPTED`.
