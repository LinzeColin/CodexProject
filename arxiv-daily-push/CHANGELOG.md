# Changelog

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
