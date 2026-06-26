# PHASE S2PMT05 SMTP CRASH WINDOW B008

## Summary

- Phase: `S2PM`
- Task ID: `S2PMT05-SMTP-CRASH-WINDOW-B008`
- Parent task ID: `S2PMT05`
- Inherited finding: `B-008`
- Acceptance ID: `ACC-S2PMT05-STRESS-E2E`
- Model ID: `MOD-ADP-098`
- Formula ID: `FORM-ADP-100`
- Parameter IDs: `PARAM-ADP-814`
- Status: `completed_local_validation_no_production`
- V7.2 contract: `ADP-PRODUCT-CONTRACT-V7.2`

## Scope

This record remediates inherited P0 finding `B-008` locally by requiring the S2PMT05 SMTP crash-window evidence to prove:

- The outbox message is claimed before SMTP acceptance is modeled.
- `ACCEPTED_PENDING_COMMIT` is explicitly reproduced.
- `mail_key` and `message_id` are present and stable for the same content revision.
- Changed content revision produces a different `message_id`.
- Resend after crash is blocked without a durable provider accept reference.
- The blocked path is not retry-safe and does not send SMTP.
- A durable `smtp-accept://...` provider reference finalizes local state as `SENT` without another SMTP send.
- Real SMTP remains disabled in the fixture.
- Negative checks block missing provider references and unstable message identity.

## Non Scope

This task does not send real SMTP, install or enable scheduler/launchd, trigger real catch-up, upload Release assets, execute production restore, change public schema, run DB migration, mutate production queues, change source adapters, change ranking, edit `CURRENT.yaml`, edit V7.1/V7.2 contract files, close inherited P0/P1, enable `DAILY_OPERATION`, or claim integrated production acceptance.

## Evidence

- Code: `arxiv-daily-push/src/arxiv_daily_push/stage2_stress_e2e.py`
- Tests: `arxiv-daily-push/tests/test_stage2_stress_e2e.py`
- Run manifest: `governance/run_manifests/ADP-S2PMT05-SMTP-CRASH-WINDOW-B008-20260627.json`
- Report hash: `b8c8d10da64d1e9005f90ab48f17529b26d6b95f89c8d282a1d83a640195445a`

## Local Report

- Report status: `pass`
- SMTP crash-window status: `pass`
- Mail key: `2026-07-04|M1|owner@example.test`
- Message ID: `adp-1d5790d40c46c746586f375c@arxiv-daily-push.local`
- Accepted-without-commit status: `blocked`
- Accepted-with-provider-ref status: `pass`
- New checks:
  - `outbox_claimed_before_smtp=true`
  - `accepted_pending_commit_reproduced=true`
  - `idempotent_message_identity_stable=true`
  - `resend_without_provider_ref_blocked=true`
  - `provider_accept_ref_required_before_resolution=true`
  - `provider_accept_ref_finalizes_without_resend=true`
  - `no_real_smtp_side_effect=true`

## Validation

- `py_compile`: PASS
- Focused S2PMT05 unittest: 19 OK
- Source/board user-center root gate: 14 OK
- Full ADP unittest: 546 OK
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
