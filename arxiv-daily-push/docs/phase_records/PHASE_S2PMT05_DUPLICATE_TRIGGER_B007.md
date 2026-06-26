# PHASE S2PMT05 DUPLICATE TRIGGER B007

## Summary

- Phase: `S2PM`
- Task ID: `S2PMT05-DUPLICATE-TRIGGER-B007`
- Parent task ID: `S2PMT05`
- Inherited finding: `B-007`
- Acceptance ID: `ACC-S2PMT05-STRESS-E2E`
- Model ID: `MOD-ADP-098`
- Formula ID: `FORM-ADP-100`
- Parameter IDs: `PARAM-ADP-812`, `PARAM-ADP-814`
- Status: `completed_local_validation_no_production`
- V7.2 contract: `ADP-PRODUCT-CONTRACT-V7.2`

## Scope

This record remediates inherited P0 finding `B-007` locally by requiring the S2PMT05 duplicate-trigger race evidence to prove:

- Four actor sources are represented: `github_schedule`, `local_launchd`, `manual_retry`, and `restart_catchup`.
- M1-M4 each receive 100 repeated trigger attempts in the fixture.
- The local race fixture records `mail_key`, `lease_owner`, and `fencing_token` receipts for active revisions.
- Exactly one active revision is retained per M1-M4 mail product and cycle.
- Duplicate trigger attempts are blocked with reason code `MAIL_KEY_ALREADY_CLAIMED`.
- Active plus blocked attempts conserve the total attempted revision count.
- Scheduler installation and enablement remain false.
- Negative checks block duplicate active revisions and weak actor-source coverage.

## Non Scope

This task does not install or enable scheduler/launchd, trigger real catch-up, send real SMTP, upload Release assets, execute production restore, change public schema, run DB migration, mutate production queues, change source adapters, change ranking, edit `CURRENT.yaml`, edit V7.1/V7.2 contract files, close inherited P0/P1, enable `DAILY_OPERATION`, or claim integrated production acceptance.

## Evidence

- Code: `arxiv-daily-push/src/arxiv_daily_push/stage2_stress_e2e.py`
- Tests: `arxiv-daily-push/tests/test_stage2_stress_e2e.py`
- Run manifest: `governance/run_manifests/ADP-S2PMT05-DUPLICATE-TRIGGER-B007-20260627.json`
- Report hash: `f2aae1359cd7497e4a1962f2731a8dd99cea0a99a748cf742b394acfbf70cfb7`

## Local Report

- Report status: `pass`
- Duplicate-trigger race status: `pass`
- Cycle ID: `2026-07-04`
- Actor sources: `github_schedule`, `local_launchd`, `manual_retry`, `restart_catchup`
- Mail products covered: `M1`, `M2`, `M3`, `M4`
- Trigger attempts per product: `100`
- Attempted revisions: `400`
- Active revisions: `4`
- Blocked duplicate attempts: `396`
- Duplicate active revisions: `0`
- New checks:
  - `trigger_count_at_least_100=true`
  - `actor_sources_covered=true`
  - `mail_products_covered=true`
  - `one_active_revision_per_product=true`
  - `blocked_duplicate_attempts_conserved=true`
  - `blocked_attempts_have_reason_codes=true`
  - `lease_fencing_receipts_present=true`
  - `no_scheduler_side_effects=true`

## Validation

- `py_compile`: PASS
- Focused S2PMT05 unittest: 18 OK
- Source/board user-center root gate: 14 OK
- Full ADP unittest: 545 OK
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
