# Changelog

## 0.11.20 - 2026-06-22

- Added `adp plan-production-refs` and `adp-production-refs-v1` to collect external runner, SMTP secret-name, Release target, and workflow variable readiness refs without reading or logging secret values.
- Added fail-closed checks for required SMTP secret names, required workflow variable names, durable readiness refs, explicit ready flags, and suspicious secret-value input fields.
- Updated `adp plan-production-launch` so a passing production refs report can fill the external runner/SMTP/Release/workflow refs while keeping launch and 30-day production acceptance blocked until real external evidence exists.

## 0.11.19 - 2026-06-22

- Added `adp plan-production-launch` and `adp-production-launch-readiness-v1` to fail closed before default-branch trial start workflow dispatch.
- Added launch readiness validation for PR merged/non-draft state, expected head SHA binding, trial start workflow contract, private runner ref, SMTP secrets ref, Release target ref, workflow variable ref, and explicit launch confirmation.
- Added launch readiness schema and tests covering pass, current draft/unmerged PR blocking, head SHA mismatch blocking, and CLI JSON output.

## 0.11.18 - 2026-06-22

- Added `.github/workflows/arxiv-daily-push-trial-start.yml` to collect default-branch trial start evidence on the private runner.
- Added `adp plan-trial-start-workflow` and `adp-trial-start-workflow-v1` to validate manual dispatch, preflight-first ordering, live source and delivery probe ordering, artifact uploads, durable refs, and explicit SMTP/Release variable gates.
- Added workflow plan schema and tests covering manual-only behavior, required artifacts, side-effect gating, secret-name-only mapping, and CLI JSON output.

## 0.11.17 - 2026-06-22

- Added `adp plan-trial-start` and `adp-trial-start-v1` to build a fail-closed readiness report before starting the real 30-day production trial.
- Added start gating across passing production preflight, bootstrap workflow, scheduler contract, live arXiv source batch, real sent SMTP probe, real created Release probe, explicit confirmation, and durable GitHub/runner/state/start refs.
- Added trial start schema and tests covering pass, missing confirmation, missing durable refs, SMTP dry-run blocking, blocked preflight, and CLI JSON output.

## 0.11.16 - 2026-06-22

- Added `adp build-trial-resource-evidence` and `adp-trial-resource-v1` to verify 30-day resource telemetry from daily trial resource refs and passing production preflight reports.
- Tightened production preflight resource refs so passing preflight reports use timestamped `production-preflight://` refs instead of a static `current` ref.
- Added resource schema and tests covering pass, missing matching preflight blocking, blocked preflight blocking, missing durable resource ref blocking, and CLI JSON output.

## 0.11.15 - 2026-06-22

- Added `adp build-trial-recovery-evidence` and `adp-trial-recovery-v1` to build fail-closed recovery drill evidence from a failed/degraded scheduled daily-run and a recovered production-ready rerun.
- Added recovery validation requiring real sent failure/recovery notifications, production-ready recovery refs, matching daily dates when available, and durable failure/recovery evidence refs.
- Added recovery schema and tests covering pass, dry-run failure notification blocking, missing recovery ref blocking, non-production-ready recovery blocking, and CLI JSON output.

## 0.11.14 - 2026-06-22

- Added `adp build-trial-replay-evidence` and `adp-trial-replay-v1` to build fail-closed weekly/monthly replay evidence from the accumulated trial ledger.
- Added replay validation requiring production-ready daily refs, no duplicate dates/source/publication IDs, 7 consecutive days for weekly replay, 30 consecutive days for monthly replay, and a durable replay evidence ref.
- Added replay schema and tests covering weekly/monthly pass, monthly coverage blocking, missing durable ref blocking, duplicate-date blocking, and CLI JSON output.

## 0.11.13 - 2026-06-22

- Added `adp annotate-trial-ops-evidence` for fail-closed annotation of explicit weekly/monthly replay, recovery drill, scheduler, Release, SMTP, and resource evidence refs.
- Added `adp export-trial-ops-state` so a passing ops annotation can carry forward the updated `trial_evidence` JSON without hand-editing state.
- Added tests that block verified operational flags without refs and prove weekly/monthly plus recovery evidence can unlock the final trial validator when all daily evidence already exists.

## 0.11.12 - 2026-06-22

- Added `adp export-trial-ledger-state` to export the accumulated `trial_evidence` JSON from a passing ledger update report.
- Updated the scheduled workflow to restore the prior `adp-trial-evidence-ledger` artifact with `gh run download` and upload the new state after successful daily ledger append.
- Added tests and scheduler validation for cross-run trial ledger state persistence while keeping 30-day production acceptance blocked until the validator passes.

## 0.11.11 - 2026-06-21

- Added `adp update-trial-ledger` and `adp-trial-ledger-v1` to append production-ready scheduled daily-run evidence into the Phase 11 trial evidence package.
- Updated the scheduled workflow to upload an `adp-trial-ledger-update` artifact after daily-run evidence while preserving fail-closed behavior for duplicate days, dry-run side effects, and missing production refs.
- Added trial ledger schema and tests covering blocked non-production evidence, duplicate daily evidence, global evidence flag upgrades, CLI JSON output, and scheduled workflow wiring.

## 0.11.10 - 2026-06-21

- Added `adp build-daily-input` and `adp-daily-input-builder-v1` to convert live arXiv source batches into ranked daily pipeline inputs using only Atom summary claims.
- Updated scheduled daily-run workflow wiring to build and upload `adp-scheduled-source-batch` and `adp-scheduled-daily-input` artifacts when no override input path is configured.
- Added daily input schema and tests covering summary-derived P0 claims, missing-summary blocking, recent-selection blocking, CLI JSON output, and scheduled execution compatibility.

## 0.11.9 - 2026-06-21

- Added `adp run-scheduled-production` and `adp-scheduled-execution-v1` as the controlled execution driver for scheduled health-check, daily-run, and watchdog modes.
- Updated the scheduled GitHub workflow to upload `adp-scheduled-execution` evidence after preflight while still failing closed when preflight, daily input, SMTP, or Release evidence is missing.
- Added scheduled execution schema and tests covering dry-run notification evidence, scheduled-run gating, degraded dry-run side effects, and mocked production-ready SMTP/Release evidence.

## 0.11.8 - 2026-06-21

- Added `.github/workflows/arxiv-daily-push-scheduled.yml` with `Australia/Sydney` 04:45 health-check, 05:00 daily-run, and 05:10 watchdog schedule slots.
- Added `adp plan-production-scheduler` and `adp-production-scheduler-v1` to validate the scheduled workflow gate without enabling production side effects.
- Added scheduler schema and tests covering timezone schedules, production variable gates, preflight-first ordering, and no SMTP/Release side effects.

## 0.11.7 - 2026-06-21

- Added `adp publish-release` for dry-run GitHub Release evidence and explicit Release creation.
- Added `adp-release-delivery-v1` with target gating, safe asset checks, no clobber upload, and no notes/stdout/stderr logging.
- Added Release delivery schema and tests covering dry-run, missing-target blocking, forbidden secret-like assets, mocked `gh release create`, and CLI JSON output.

## 0.11.6 - 2026-06-21

- Added `adp send-notification` for dry-run notification evidence and explicit SMTP delivery.
- Added `adp-smtp-delivery-v1` with fail-closed environment-key checks, TLS-required delivery, body hashing, and no secret/body logging.
- Added SMTP delivery schema and tests covering dry-run, missing-env blocking, and mocked real send.

## 0.11.5 - 2026-06-21

- Added `adp fetch-arxiv-latest` for small-window live arXiv Atom source ingestion.
- Added incremental duplicate filtering by prior `source_id` and a SourceBatch schema.
- Added fail-closed network/API/Atom parsing behavior with tests and current local SSL-blocker evidence.

## 0.11.4 - 2026-06-21

- Added a manual GitHub Actions production trial bootstrap workflow that runs production preflight before any trial work.
- Added `adp plan-trial-bootstrap` to validate the workflow/runbook contract without enabling cron, Release upload, or SMTP sending.
- Added a production trial runbook and trial bootstrap schema/tests.

## 0.11.3 - 2026-06-21

- Added `adp preflight-production` as a fail-closed gate before any scheduled production run.
- Preflight now checks production commands, required secret environment key presence without logging values, disk, memory, Git artifact hygiene, and local cache/staging directories.
- Added production preflight schema and tests covering blocked and passing reports.

## 0.11.2 - 2026-06-21

- Added a Phase 11 trial evidence validator for 30-day production evidence packages.
- Added `adp evaluate-trial` for validating daily run uniqueness, traceability, scheduler, Release, SMTP, resource, weekly/monthly replay, and recovery evidence.
- Hardened production acceptance so manual operational flags cannot pass unless they come from a validated trial evidence report.

## 0.11.1 - 2026-06-21

- Hardened Phase 11 production acceptance: every production pass requirement now needs both a true flag and a non-empty evidence reference.
- Added regression coverage that blocks boolean-only operational evidence from marking production acceptance as passed.

## 0.11.0 - 2026-06-21

- Added Phase 11 acceptance and handoff readiness package generation.
- Added `adp build-acceptance` for converting Phase 10 handoff JSON into a truthful acceptance package.
- Acceptance output blocks production acceptance unless explicit 30-day, scheduler, Release, SMTP, and resource evidence is provided.
- Added acceptance tests covering default blocked status, unsupported claim prevention, invalid handoff rejection, future evidence pass, and CLI output.

## 0.10.0 - 2026-06-21

- Added Phase 10 runner/release/email dry-run handoff.
- Added `adp build-handoff` for converting a completed dry-run pipeline payload into a handoff preview.
- Added fail-closed validation that keeps scheduler, GitHub Actions runner, Release upload, unattended execution, and real SMTP sending disabled.
- Added handoff tests covering completed RunRecord requirements, disabled external side effects, validation errors, and CLI output.

## 0.9.0 - 2026-06-21

- Added Phase 9 local daily dry-run pipeline orchestration.
- Added `adp run-daily-dry-run` for local source/claim JSON pipeline execution.
- Added RunRecord state transitions through completed, publication gate, Lesson, Narration, Storyboard, and email preview output.
- Added pipeline fixture and tests covering successful completion, evidence blocking, email preview, and CLI output.

## 0.8.0 - 2026-06-21

- Added Phase 8 storyboard/video dry-run generation from narration JSON.
- Added `adp generate-storyboard` for local storyboard rendering.
- Added video media gate with rendering, media writes, and asset downloads blocked in Phase 8.
- Added video fixture and tests covering dry-run storyboard generation, real render blocking, media path rejection, claim subset validation, and CLI output.

## 0.7.0 - 2026-06-21

- Added Phase 7 dry-run narration/TTS plan generation from Lesson JSON.
- Added `adp generate-narration` for local narration plan rendering.
- Added TTS resource gate with real synthesis, audio writes, and model downloads blocked in Phase 7.
- Added narration schema, fixture, and tests covering dry-run boundaries, real TTS blocking, audio path rejection, CLI output, and runtime parameters.

## 0.6.0 - 2026-06-21

- Added Phase 6 deterministic Chinese Lesson JSON generation from supported Claim Ledger evidence.
- Added `adp generate-lesson` for local lesson rendering from source/claim JSON fixtures.
- Added lesson validation that blocks unsupported or unknown claim references and requires visible claim markers in section bodies.
- Added lesson fixture and tests covering supported-claim linkage, unverified claim exclusion, blocked ledger handling, validation failures, and CLI output.

## 0.5.0 - 2026-06-21

- Added Phase 5 Claim Ledger construction and publication hard-block gate.
- Added `adp gate-publication` for local source/claim JSON gate checks.
- Added fail-closed checks for missing P0 locators, unsupported P0 claims, metadata conflicts, and unsupported arXiv peer-review claims.
- Added Claim Ledger fixture and evidence gate tests.

## 0.4.0 - 2026-06-21

- Added Phase 4 deterministic 100-point ranking and queue audit.
- Added fail-closed gates for missing P0 evidence, unsupported P0 evidence, metadata conflicts, and recent duplicate selections.
- Added `adp rank-candidates` for local candidate ranking from JSON fixtures.
- Added ranking golden tests and a small queue fixture.

## 0.3.0 - 2026-06-21

- Added Phase 3 arXiv Atom source adapter.
- Added offline Atom fixture parsing into generic `SourceItem` records.
- Added arXiv query URL rendering without network fetch.
- Added source adapter tests using local fixtures only.

## 0.2.0 - 2026-06-21

- Added Phase 2 generic contracts for `SourceItem`, `EvidenceClaim`, `Lesson`, `Storyboard`, `Publication`, and `RunRecord`.
- Added dependency-free runtime validators and a deterministic `RunRecord` state machine.
- Added `adp validate-record` for local `RunRecord` validation.
- Kept Phase 2 offline-only: no network ingest, ranking, TTS, video, runner automation, or real SMTP sending.

## 0.1.0 - 2026-06-21

- Created Phase 1 repository foundation for `arXiv Daily Push`.
- Added CLI skeleton with `version`, `doctor`, and `render-email`.
- Added dry-run notification contract for `linzezhang35@gmail.com`.
- Added local resource and storage pressure guardrails.
- Added CodexProject governance records for Phase 1.
