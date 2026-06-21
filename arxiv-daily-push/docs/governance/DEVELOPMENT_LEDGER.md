# DEVELOPMENT_LEDGER

Project: `arxiv-daily-push`
Active product version: `0.1.0`
Governance spec version: `1.0.0`

The append-only machine record is `development_events.jsonl`.

## Current State

- Product version: 0.1.0
- Current phase: A
- Current gate: ADP-PHASE1-FOUNDATION-PASS
- Confirmed iteration count: 1
- Reconstructed event count: 0
- Current task: ADP-PHASE2-DATA-CONTRACTS-001
- Blockers: Later phases need Node/npm/gh/ffmpeg/docker, more disk, runner readiness, and real mail transport validation.

## Phase Matrix

| Phase | Name | Status | Exit criteria | Evidence |
|---|---|---|---|---|
| A | Phase 1 repository foundation | completed | CLI skeleton, governance records, and tests pass | `docs/phase_records/PHASE_01.md` |
| B | Data contracts and arXiv source/ranking | planned | generic schemas and arXiv adapter gates pass | planned Phase 2-4 |
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
- Result commit: PENDING
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

## Unknown Historical Periods

None for this new project baseline.
