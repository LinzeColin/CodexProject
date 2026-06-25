# S2PJT02 Review Schedule Local Evidence

Task: `S2PJT02`
Acceptance: `ACC-S2PJT02-REVIEW`
Phase: `S2PJ`
Status: completed local review schedule evidence, no scheduler or production side effects

## Evidence

- Adds a local-only `stage2-review-schedule` CLI report path.
- Validates default review intervals `1/3/7/14/30/90` days and feedback-adjustment readiness.
- Recomputes due buckets from `service_date`: due today, due in the next 7 days, overdue, and completed.
- Validates each review record has a stable `content_id`, valid `anchor_date`, valid `due_date`, and `due_date = anchor_date + review_stage_days`.
- Builds deterministic due queues and a stable `due_queue_hash`.
- Writes `stage2_s2pjt02_review_schedule_report.json` under the explicit local state directory when not run with `--no-write`.
- Focused tests cover pass, blocked, persistence, and CLI JSON behavior.

## Boundaries

This task does not install or enable a scheduler and does not claim owner-experience final acceptance, `STAGE2_PRODUCTION_ACCEPTED`, or `INTEGRATED_PRODUCTION_ACCEPTED`.

No SMTP send, scheduler enablement, Release upload, public schema migration, DB migration, production queue mutation, ranking change, source adapter change, Email V1 runtime/frontstage change, V7.1 CURRENT switch, or V7.2 contract-file edit is enabled.

## Rollback

Revert S2PJT02 code, CLI, tests, governance registrations, this phase record, and the run manifest. No runtime production state is changed.
