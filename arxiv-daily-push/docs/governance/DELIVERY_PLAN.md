# DELIVERY_PLAN

Project: `arxiv-daily-push`
Governance spec version: `1.0.0`

## Phase Map

| Phase | Purpose | Exit Gate |
|---|---|---|
| A | Phase 1 repository foundation | CLI skeleton, governance records, and focused tests pass |
| B | Phase 2-4 data contracts, arXiv source, and ranking | schema, adapter, and ranking gates pass |
| C | Phase 5-6 evidence gate and text lesson | Claim Ledger and lesson verification pass |
| D | Phase 7-10 TTS, video, local daily pipeline, and GitHub automation | media, resource, runner, and release gates pass |
| E | Phase 11 weekly/monthly, 30-day trial, and handoff | full operational acceptance passes |

## Task Summary

machine_summary:

- task_count: 11
- acceptance_count: 11

## Delivery Tasks

The machine-readable task source is `delivery_tasks.yaml`.

| Task ID | Phase | Status | Acceptance | Test result | Evidence |
|---|---|---|---|---|---|
| ADP-PHASE1-FOUNDATION-001 | A | completed | ADP-ACC-PHASE1-FOUNDATION | 4 tests OK; validator 0 errors; diff check pass | `docs/phase_records/PHASE_01.md` |
| ADP-PHASE2-DATA-CONTRACTS-001 | B | completed | ADP-ACC-PHASE2-DATA-CONTRACTS | 13 tests OK; schema parse OK; validator 0 errors; sync 0 errors | `docs/phase_records/PHASE_02.md` |
| ADP-PHASE3-ARXIV-ADAPTER-001 | B | completed | ADP-ACC-PHASE3-ARXIV-ADAPTER | 19 tests OK; adapter fixture parse OK; validator 0 errors | `docs/phase_records/PHASE_03.md` |
| ADP-PHASE4-RANKING-001 | B | completed | ADP-ACC-PHASE4-RANKING | 26 tests OK; ranking golden score and gates pass | `docs/phase_records/PHASE_04.md` |
| ADP-PHASE5-EVIDENCE-GATE-001 | C | completed | ADP-ACC-PHASE5-EVIDENCE-GATE | 32 tests OK; Claim Ledger gates pass | `docs/phase_records/PHASE_05.md` |
| ADP-PHASE6-LESSON-001 | C | completed | ADP-ACC-PHASE6-LESSON | 37 tests OK; lesson evidence linkage pass | `docs/phase_records/PHASE_06.md` |
| ADP-PHASE7-TTS-001 | D | completed | ADP-ACC-PHASE7-TTS | 42 tests OK; narration dry-run gate pass | `docs/phase_records/PHASE_07.md` |
| ADP-PHASE8-VIDEO-001 | D | completed | ADP-ACC-PHASE8-VIDEO | 47 tests OK; storyboard dry-run gate pass | `docs/phase_records/PHASE_08.md` |
| ADP-PHASE9-LOCAL-PIPELINE-001 | D | completed | ADP-ACC-PHASE9-LOCAL-PIPELINE | 51 tests OK; local dry-run pipeline pass | `docs/phase_records/PHASE_09.md` |
| ADP-PHASE10-RUNNER-RELEASE-EMAIL-001 | D | completed | ADP-ACC-PHASE10-RUNNER-RELEASE-EMAIL | 55 tests OK; handoff side-effect gate pass; validator 0 errors | `docs/phase_records/PHASE_10.md` |
| ADP-PHASE11-ACCEPTANCE-HANDOFF-001 | E | planned | ADP-ACC-PHASE11-ACCEPTANCE-HANDOFF | not run | pursuing goal baseline |

## Release Gates

| Gate | Required evidence | Status |
|---|---|---|
| Phase 1 unit tests | unittest output | pass |
| Phase 2 contract/state tests | unittest output | pass |
| Phase 2 schema syntax | `json.tool` output | pass |
| Phase 3 arXiv adapter tests | unittest output and fixture parse | pass |
| Phase 4 ranking tests | golden score, evidence gate, metadata conflict gate, duplicate gate | pass |
| Phase 5 Claim Ledger gate tests | P0 locator, unsupported P0, metadata conflict, peer-review claim gate | pass |
| Phase 6 lesson linkage tests | supported claim IDs, unregistered claim rejection, visible claim markers | pass |
| Phase 7 narration/TTS dry-run gate | dry-run narration JSON, blocked real TTS, no audio paths | pass |
| Phase 8 storyboard/video dry-run gate | dry-run storyboard JSON, blocked render/write/download | pass |
| Phase 9 local dry-run pipeline | completed RunRecord, publication gate, Lesson, Narration, Storyboard, email preview | pass |
| Phase 10 runner/release/email handoff | completed RunRecord input, side-effect flags false, recipient preview | pass |
| Project governance | validator output | pass |
| Changed-only sync | validator output | pass |
| Diff hygiene | `git diff --check` | pass |
| Secrets/media guard | file review and `.gitignore` | pass |
