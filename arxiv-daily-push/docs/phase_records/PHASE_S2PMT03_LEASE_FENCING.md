# PHASE S2PMT03 LEASE FENCING

## Status

- status: `completed_local_validation`
- phase: `S2PM`
- task_id: `S2PMT03`
- acceptance_id: `ACC-S2PMT03-LEASE-FENCING-OUTBOX`
- model_id: `MOD-ADP-096`
- formula_id: `FORM-ADP-098`
- parameter_ids: `PARAM-ADP-778` through `PARAM-ADP-788`
- completed_at: `2026-06-26T13:20:00+10:00`

## Scope

S2PMT03 adds local-only lease fencing, state concurrency, transactional outbox, SMTP accept crash-window, and M4 cycle watermark evidence. It proves row_version compare-and-swap, lease expiry, fencing-token rejection of stale writers, state-history consistency, idempotent mail identity by content revision, and cycle-scoped M4 readiness/degradation.

## Non Scope

This phase does not send SMTP, install a scheduler, upload Release assets, run production restore, migrate DB or public schema, mutate production queues, change ranking, change source adapters, fetch live sources, change `CURRENT`, edit V7.1/V7.2 contract files, close inherited P0/P1 blockers, claim exactly-once delivery, or claim `INTEGRATED_PRODUCTION_ACCEPTED`.

## Evidence

- `arxiv-daily-push/src/arxiv_daily_push/stage2_lease_fencing.py`
- `arxiv-daily-push/src/arxiv_daily_push/state_machine.py`
- `arxiv-daily-push/src/arxiv_daily_push/smtp_delivery.py`
- `arxiv-daily-push/tests/test_stage2_lease_fencing.py`
- `arxiv-daily-push/tests/test_state_machine.py`
- `arxiv-daily-push/tests/test_smtp_delivery.py`
- `governance/run_manifests/ADP-S2PMT03-LEASE-FENCING-20260626.json`

## Validation

- `py_compile`: PASS
- focused S2PMT03/state/SMTP tests: 14 OK
- Full ADP unittest: 419 OK
- V7.2 validator: PASS
- ADP project governance: 0 errors / 0 warnings
- Changed-only governance semantic: 0 errors / 0 warnings
- Lean check-render: drift_count 0 reference_issue_count 0
- JSONL/YAML/CSV/manifest parse: OK
- git diff --check: PASS

## Remaining Risks

- S2PMT03 proves local concurrency and outbox semantics only; it is not production SMTP/outbox enablement.
- At-least-once plus idempotent Message-ID is the stated delivery model; exactly-once remains forbidden.
- Inherited V7.1 P0/P1 blockers remain production blockers until independent review accepts remediation evidence and S2PMT07 passes.
