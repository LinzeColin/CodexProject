# S2PCT04 Top-Journal Profile And Relation Shadow Evidence

Task: `S2PCT04` / legacy `S2P2T04`
Acceptance: `ACC-S2PCT04-JOURNAL-PROFILE`
Phase: `S2PC`
Status: completed shadow evidence, no formal production inclusion

## Evidence

- Built a metadata-only profile model over the completed Nature, Science, and The Lancet SourceBatches.
- Profile taxonomy differentiates `research`, `review`, `editorial`, `news`, `correction`, and `retraction`.
- Publication relation edges cover `original_publication`, `discusses`, `corrects`, and `retracts`.
- Correction events force old conclusions into `requires_revision`; retraction events force old conclusions into `invalidated`.
- Focused tests cover taxonomy classification, relation edges, forced correction/retraction target validation, persisted report/ledger evidence, and CLI JSON output.
- CLI fixture canary on 2026-06-24 returned `status=pass`, `validation_errors=[]`, `forced_event_update_count=2`, and all production flags false.
- Semantic extractor validated 59 formulas and 382 active parameters after S2PCT04 registry updates.
- Project governance validator and changed-only semantic sync both returned `errors=0`, `warnings=0`.
- Lean render check returned `drift_count=0` and `reference_issue_count=0`; root governance unittest ran 238 tests OK.
- V7.1 task-pack validator returned PASS with task_count 98 and finding_count 53; S2PCT05 remains planned, not production accepted.

## Boundaries

This task does not claim `D2_SOURCE_DOMAIN_ACCEPTED`, `STAGE2_PRODUCTION_ACCEPTED`, or `INTEGRATED_PRODUCTION_ACCEPTED`.

No SMTP send, Release upload, GitHub production schedule, video, PDF/full-text download, paid API use, or paywall bypass is enabled.

## Rollback

Revert S2PCT04 additions in `stage2_sources.py`, `cli.py`, the top-journal publication event fixtures/tests, governance registry rows, this phase record, and the run manifest.
