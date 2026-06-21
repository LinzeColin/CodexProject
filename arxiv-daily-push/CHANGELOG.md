# Changelog

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
