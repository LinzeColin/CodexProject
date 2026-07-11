# Changelog

## IDS v0.1 STAGE-038 Phase 1 - 2026-07-11

- Recorded the source-limited Worker queue boundary under `ACC-STAGE-038`: inherited STAGE-037/022/030 constraints and STAGE-039..044 ownership are fixed, while exact ordering, idempotency, dependency, queue-entry, and claim contracts remain unassigned.
- Recorded the absent external taskpack truthfully with no fabricated SHA-256, set `phase2_entry_authorized=false`, and routed the next run only to a P1 source-reverification gate.
- Kept queue/worker runtime, claim persistence, PostgreSQL/schema actions, raw metadata access, fake IDS data, runtime outputs, GitHub upload, app reinstall, stage review, and batch gates out of this phase.

## IDS v0.1 STAGE-037 Review - 2026-07-11

- Reviewed and repaired the STAGE-037 unified job-state engineering contract under `ACC-STAGE-037` without running a queue, worker, retry scheduler, database, cleanup action, or real IDS job.
- Added fail-closed direct and paused retry eligibility, cancellation stop reasons, `ids.job_control_envelope.v1`, distinct “暂停中” projection, structured review governance, and Git-index-bound delivery/review sources.
- Kept raw metadata content, fake IDS data, runtime outputs, GitHub upload, app reinstall, batch gates, and STAGE-038 execution out of this review.

## IDS v0.1 STAGE-036 Review - 2026-07-11

- Reviewed and repaired the STAGE-036 database-quality engineering contract under `ACC-STAGE-036` without changing product version, diagnostic models, formulas, or active parameter values.
- Added hash-pinned migration section selection, ownership-safe public-schema rollback, bounded real-data authorization queries, dependency/snapshot provenance checks, and fail-closed governance regressions.
- Kept PostgreSQL access, raw metadata access, fake IDS data, runtime outputs, GitHub upload, app reinstall, batch gates, and STAGE-037 execution out of this review.

## 1.0.0 - 2026-06-24

- Added Other8 S3PCT01 lifecycle contract coverage for dependency fail-fast entrypoints, owned launcher PID cleanup, and temporary SQLite persistence recovery.
- Added `stop_local_services.sh` and LF enforcement for OpMe shell scripts.
- Kept diagnostic formulas, LLM routing values, provider calls, and production readiness unchanged.

## 1.0.0 - 2026-06-20

- Established CodexProject governance baseline for KM_IDSystem without changing backend/frontend behavior.
- Recorded offline rule models, risk scoring formulas, LLM routing/fallback strategy, parameters, version matrix, and traceability.
- Marked engineering calibration, prompt/provider governance, and signoff evidence as UNKNOWN under `TASK-OPME-B-001`.
