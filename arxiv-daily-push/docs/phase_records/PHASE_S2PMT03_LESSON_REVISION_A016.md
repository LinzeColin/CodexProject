# PHASE S2PMT03 Lesson Revision A016

Task: `S2PMT03-LESSON-REVISION-A016`

Parent task: `S2PMT03`

Acceptance: `ACC-S2PMT03-CONCURRENCY-OUTBOX`

## Scope

This run adds local remediation evidence for inherited V7.1 audit finding `A-016`.

The Lesson contract now distinguishes:

- `lesson_key`: stable logical key for unchanged source, supported `claim_id` set, and language.
- `lesson_revision_id`: immutable revision identifier derived from claim statements, evidence locator hashes, source metadata/content reference hashes, language, lesson model version, prompt contract version, and revision contract version.
- `lesson_id`: compatibility field equal to `lesson_revision_id`, so downstream narration/video references continue to use a revision-sensitive identifier.

Regression tests prove that changing claim content or evidence locator data changes `lesson_revision_id` while `lesson_key` remains stable when source, claim IDs, and language do not change.

## Non-Scope

This run does not close inherited V7.1 P0/P1 findings, provide independent S2PMT07 signoff, enable real SMTP, install scheduler, upload Release assets, run production restore, execute DB migration, mutate production queues, change source adapters or ranking, edit CURRENT or V7.1/V7.2 contract files, claim `INTEGRATED_PRODUCTION_ACCEPTED`, or enable `DAILY_OPERATION`.

## Validation

- py_compile: PASS
- focused lesson/narration/video/contracts tests: 28 OK
- JSON schema/fixture parse: OK
- full ADP unittest: 472 OK
- V7.2 validator: PASS
- project governance: 0 errors / 0 warnings
- changed-only governance semantic: 0 errors / 0 warnings
- lean check-render: drift_count 0, reference_issue_count 0
- JSONL/CSV/YAML/manifest parse: OK
- `git diff --check`: PASS
- full semantic extractor: NOT COMPLETED after local interrupt at >150 seconds during full-table AST parsing

## Remaining Blockers

- inherited V7.1 P0 findings: 8
- inherited V7.1 P1 findings: 37
- independent A-016 closure review: missing
- S2PLT04: incomplete
- S2PMT07 final independent production gate: blocked

## Evidence

- `arxiv-daily-push/src/arxiv_daily_push/lesson.py`
- `arxiv-daily-push/schemas/lesson.schema.json`
- `arxiv-daily-push/tests/test_lesson.py`
- `governance/run_manifests/ADP-S2PMT03-LESSON-REVISION-A016-20260626.json`
