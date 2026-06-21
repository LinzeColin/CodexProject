# DEVELOPMENT_LEDGER

Project: `arxiv-daily-push`
Active product version: `0.3.0`
Governance spec version: `1.0.0`

The append-only machine record is `development_events.jsonl`.

## Current State

- Product version: 0.3.0
- Current phase: B
- Current gate: ADP-PHASE3-ARXIV-ADAPTER-PASS
- Confirmed iteration count: 3
- Reconstructed event count: 0
- Current task: ADP-PHASE4-RANKING-001
- Blockers: Later phases still need arXiv network ingest/ranking/evidence implementation, real mail transport validation, and later media/runner resource readiness.

## Phase Matrix

| Phase | Name | Status | Exit criteria | Evidence |
|---|---|---|---|---|
| A | Phase 1 repository foundation | completed | CLI skeleton, governance records, and tests pass | `docs/phase_records/PHASE_01.md` |
| B | Data contracts and arXiv source/ranking | in_progress | generic schemas and arXiv adapter/ranking gates pass | `docs/phase_records/PHASE_02.md`; `docs/phase_records/PHASE_03.md`; planned Phase 4 |
| C | Evidence and text lesson | planned | Claim Ledger and lesson verification pass | planned Phase 5-6 |
| D | TTS/video/local pipeline/GitHub automation | planned | media gates and daily pipeline pass | planned Phase 7-10 |
| E | Weekly/monthly trial and handoff | planned | 30-day acceptance passes | planned Phase 11 |

## Iteration Records

### `ITER-20260621-001`

- Date: 2026-06-21
- Fact level: EXTRACTED for created Phase 1 files and PROPOSED for future phases
- Version before: none
- Version after: 0.1.0
- Base commit: 18c3773dd5cb9d618993a5685eed7fb668349ac3
- Result commit: 4090ec69fea8fd5329eeee03a8ab842a5347b909
- Task IDs: ADP-PHASE1-FOUNDATION-001
- Goal: Start arXiv Daily Push inside CodexProject using the prepared pursuing goal baseline.
- Assumptions: Phase 1 remains foundation-only and does not implement ingest, ranking, evidence, TTS, video, runner, or SMTP transport.
- Files read: root AGENTS, governance standard, projects registry, codex-dex, project-governance skill, Phase 0 and pursuing goal preparation outputs.
- Files changed: arxiv-daily-push project files, root README, governance/projects.yaml.
- Model changes: Added MOD-ADP-001 active foundation gate and planned MOD-ADP-002/MOD-ADP-003.
- Parameter changes: Added PARAM-ADP-001 through PARAM-ADP-019.
- Commands run: `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`; `python3 scripts/validate_project_governance.py --project arxiv-daily-push`; `python3 scripts/validate_project_governance.py --changed-only`; `git diff --check`.
- Test results: 4 unit tests OK; project governance errors 0 warnings 0; changed-only governance errors 0 warnings 0; diff check exit 0.
- Successes: Project skeleton and governance records created.
- Failures: none recorded at file creation time.
- Decisions: Use public CodexProject path `arxiv-daily-push` and preserve future multi-source boundaries.
- Remaining risks: Later phases need environment setup and additional implementation.
- Rollback: Remove `arxiv-daily-push/` and restore `README.md` plus `governance/projects.yaml`.
- Next step: Start Phase 2 data contracts after the next run contract.

### `ITER-20260621-002`

- Date: 2026-06-21
- Fact level: EXTRACTED for Phase 2 contracts, schemas, state machine, tests, and governance updates.
- Version before: 0.1.0
- Version after: 0.2.0
- Base commit: 4090ec69fea8fd5329eeee03a8ab842a5347b909
- Result commit: PENDING
- Task IDs: ADP-PHASE2-DATA-CONTRACTS-001
- Goal: Implement generic SourceItem, EvidenceClaim, Lesson, Storyboard, Publication, and RunRecord contracts without network or media side effects.
- Assumptions: Phase 2 remains offline-only and does not implement arXiv ingest, ranking, evidence extraction, lesson generation, media generation, runner automation, or SMTP transport.
- Files changed: contract/state code, schema files, tests, README, CHANGELOG, VERSION, and governance records.
- Model changes: Added MOD-ADP-004 active generic contract and RunRecord state gate.
- Parameter changes: Added PARAM-ADP-020 through PARAM-ADP-028.
- Commands run: `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`; `python3 -m json.tool arxiv-daily-push/schemas/*.schema.json`.
- Test results: 13 unit tests OK; all schema JSON files parse OK.
- Successes: Generic source boundary accepts arXiv and a future GitHub source; P0 locator requirement and skipped state transitions fail closed.
- Failures: Initial `RunRecord.stages` empty-array validation failed and was fixed in `state_machine.py`.
- Decisions: Keep runtime validation dependency-free; use schemas as external contract and stdlib validators for local gates.
- Remaining risks: Phase 4 ranking and real arXiv adapter are not implemented.
- Rollback: Revert Phase 2 commit and restore version/governance records to 0.1.0.
- Next step: Start Phase 4 arXiv adapter/ranking only after final Phase 2 validation passes.

### `ITER-20260621-003`

- Date: 2026-06-21
- Fact level: EXTRACTED for arXiv adapter code, local fixture, CLI commands, tests, and governance updates.
- Version before: 0.2.0
- Version after: 0.3.0
- Base commit: e5f15384887e8e4878a228673dfb487345d1a5c1
- Result commit: PENDING
- Task IDs: ADP-PHASE3-ARXIV-ADAPTER-001
- Goal: Implement the first concrete arXiv SourceAdapter without bulk ingest or media side effects.
- Assumptions: Phase 3 validates URL construction and Atom parsing locally; live scheduled ingestion remains future work.
- Files changed: arXiv adapter code, CLI commands, fixture, tests, source config, version files, and governance records.
- Model changes: Added MOD-ADP-005 active arXiv Atom source adapter.
- Parameter changes: Added PARAM-ADP-029 through PARAM-ADP-034.
- Commands run: `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`.
- Test results: 19 unit tests OK.
- Successes: arXiv Atom fixture maps into generic SourceItem and validates against Phase 2 contract.
- Failures: Initial CLI indentation error was caught by tests and fixed before governance validation.
- Decisions: Keep Phase 3 tests offline and cap Phase 3 query construction at 50 results per call.
- Remaining risks: Live arXiv API availability, rate limits, and daily freshness are not yet covered by scheduler/runner gates.
- Rollback: Revert Phase 3 adapter code, tests, fixture, and governance updates.
- Next step: Start Phase 4 queue/ranking once final Phase 3 validation passes.

## Unknown Historical Periods

None for this new project baseline.
