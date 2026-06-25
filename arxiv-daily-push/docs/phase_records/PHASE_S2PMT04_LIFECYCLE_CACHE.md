# PHASE S2PMT04 LIFECYCLE CACHE

## Summary

- phase: `S2PM`
- task_id: `S2PMT04`
- acceptance_id: `ACC-S2PMT04-LIFECYCLE`
- model_id: `MOD-ADP-097`
- formula_id: `FORM-ADP-099`
- parameter_ids: `PARAM-ADP-789` through `PARAM-ADP-801`
- status: local validation passed
- V7.2 contract: `ADP-PRODUCT-CONTRACT-V7.2`

S2PMT04 adds local-only automatic lifecycle and cache-cleanup evidence. It proves a disabled dry-run launchd wake path, the required STOPPED/STARTING/RECOVERING/LEADER/RUNNING/DRAINING/CHECKPOINTING/CLEANING lifecycle, startup reconciliation for temp/inflight/outbox/stale locks, durable shutdown receipts, whitelist/symlink/durable-evidence cache safety, parseable launchd plist generation, and no production side effects.

## Scope

- Add private S2PMT04 lifecycle/cache evidence helpers.
- Keep existing local launchd package generation disabled and not installed.
- Generate launchd plist XML through `plistlib` rather than handwritten XML.
- Add focused tests for lifecycle transitions, reconciliation, shutdown receipt, cache cleanup safety, launchd plist parsing, and report validation.
- Register S2PMT04 model/formula/parameters in governance.

## Non Scope

No real SMTP, scheduler install, launchd bootstrap, Release upload, production restore, public schema change, DB migration, production queue mutation, source adapter change, ranking change, workflow enforcement change, V7.1/V7.2 contract-file edit, Stage 2 production acceptance, integrated production acceptance, or daily-operation enablement.

## Evidence

- `arxiv-daily-push/src/arxiv_daily_push/stage2_lifecycle_cache.py`
- `arxiv-daily-push/src/arxiv_daily_push/local_runner.py`
- `arxiv-daily-push/tests/test_stage2_lifecycle_cache.py`
- `arxiv-daily-push/tests/test_local_runner.py`
- `governance/run_manifests/ADP-S2PMT04-LIFECYCLE-CACHE-20260626.json`

## Local Report

- report_status: `pass`
- report_hash: `620b934d7fafddd46c8ac4c0aaad6f7cf2cafcabe43379438ab40dfff0ced806`
- launchd_plist_sha256: `3dea47c478d7a09d03fdf554a0d4773b6d59f877c804412fe3caee597eff792c`
- cache_delete_candidate_count: `2`
- cache_delete_bytes_dry_run: `2176`
- durable_evidence_delete_allowed: `false`
- scheduler_installed: `false`
- real_smtp_sent: `false`
- production_side_effects_enabled: `false`

## Validation

- py_compile: PASS
- focused S2PMT04/local-runner tests: 12 OK
- full arxiv-daily-push unittest: 425 OK
- V7.2 validator: PASS
- ADP project governance: 0 errors / 0 warnings
- changed-only governance semantic: 0 errors / 0 warnings
- lean check-render: drift_count 0 reference_issue_count 0
- JSONL/YAML/CSV/manifest parse: OK
- git diff --check: PASS

## Boundaries

S2PMT04 is local lifecycle/cache hardening evidence only. It does not enable scheduler operation. It does not close inherited V7.1 P0/P1 blockers, does not authorize production restore or real SMTP production, and does not claim `INTEGRATED_PRODUCTION_ACCEPTED`.

## Next

Continue to `S2PMT05` pressure, fault, time, and E2E validation under the same V7.2 no-production boundaries.
