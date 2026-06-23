# arXiv Daily Push

`arXiv 日报推送 / arXiv Daily Push` is a private, evidence-first daily teaching
pipeline. V5 Stage 1 for the B1/arXiv single-source vertical slice is recorded
as `ARXIV_PRODUCTION_ACCEPTED` from PR #82 evidence. Current V6 task pointer:
`S1P5T04`.

The user-facing product must be an explanatory Chinese learning email, not a
shallow news digest. Stage 1 delivery is text-first: high-density Chinese
teaching report, email preview/delivery contract, and Markdown/HTML/JSON audit
artifacts. Video, TTS, MP4 rendering, GitHub Release video links, and media
attachments are historical/legacy capabilities only and are not Stage 1 V5
acceptance requirements.

Stage 1 acceptance is not the same as enabling scheduled sends. Scheduled
production remains fail-closed until GitHub repository variables/secrets are
explicitly verified or enabled. Current operation must not rely on the user's
Mac as a background production runner.

Baseline clarification: 30-day-grade Stage 1/2 evidence means 30 independent
unique-date artifacts and replay/coverage checks generated from real data where
available. It must not be interpreted as waiting 30 wall-clock days when the
same evidence can be produced and verified faster.

## Current Scope

Implemented foundations now:

- package and CLI foundation: `adp version`, `adp doctor`, `adp render-email`,
  `adp send-notification`, `adp validate-record`;
- arXiv adapter and source controls: `adp arxiv-url`, `adp parse-arxiv-atom`,
  `adp fetch-arxiv-latest`, `adp source-registry`;
- deterministic ranking, evidence gate, Chinese lesson JSON, publication gate,
  dry-run pipeline, handoff, and acceptance validators from earlier phases;
- owner controls: `config/owner_controls.yaml` plus generated owner views under
  `docs/owner/`;
- Stage 1 SQLite/WAL/FTS5 document and event storage model;
- Stage 1 source registry contract with only `SRC-ARXIV / arxiv.atom.v1` active;
- Stage 1 scoring, deterministic queue, and content ledger contract via
  `adp stage1-queue`;
- Stage 1 B1 report/email preview, 30 historical preview evidence, local
  runtime recovery, migration package, and post-migration bootstrap gates via
  `adp build-b1-report-email`, `adp historical-b1-previews`,
  `adp runtime-audit`, `adp migration`, and `adp post-migration-bootstrap`.

Retained but inactive for V5 Stage 1 acceptance:

- historical TTS/storyboard/video commands;
- historical GitHub Release media delivery paths;
- Phase 12 all-arXiv/ROI/manual-delivery experiments.

These are not current acceptance gates for `ARXIV_PRODUCTION_ACCEPTED` unless a
later owner decision explicitly restores them.

Completed Stage 1 acceptance evidence:

- 30 independent historical B1 report/email previews.
- Two controlled Gmail SMTP refs on GitHub/cloud runner from run
  `28002478689`, both sent to `linzezhang35@gmail.com`.
- PR #82 live all-arXiv cloud dry-run artifact `7818287996`: 20/20 primary
  archive buckets, 49 real candidates, 30 selected samples, and
  `ARXIV_PRODUCTION_ACCEPTED`.

Not enabled yet:

- scheduled production repo variables/secrets;
- automatic daily send on default branch;
- deferred email frontstage template redesign.

## Goal Baseline

The current long-running baseline is locked at:

```text
docs/pursuing_goal/BASELINE_LOCK.md
docs/pursuing_goal/START_HERE_MASTER_TASK_PACK_TWO_STAGE_TEXT_DELIVERY_V5.md
docs/pursuing_goal/FULL_PURSUING_GOAL_PROMPT_TWO_STAGE_TEXT_DELIVERY_V5.txt
docs/pursuing_goal/ARXIV_DAILY_PUSH_TWO_STAGE_ROADMAP_V6.md
```

V4 and Phase 1-12 files remain historical context only. For the current goal,
Stage 1 covers only board one, B1/arXiv. Stage 2 may later promote the other
boards and sources.

V6 task-numbering rule: every completion report must state the current Task ID.
The current Task is `S1P5T04` - controlled live B1 email evidence and Stage 1
acceptance. Stage 1 arXiv is accepted; scheduled production remains a separate
fail-closed enablement step.

Current V5-to-V6 Stage 1 task continuity:

- `S1-01-READONLY-AUDIT-001`: read-only package and repository audit.
- `S1-02-V5-BASELINE-GOVERNANCE-CALIBRATION-001`: V5 baseline lock and
  governance calibration.
- `S1-03-OWNER-CONTROLS-001`: owner controls and generated owner-readable
  views.
- `S1-04-SQLITE-DATA-MODEL-001`: unified local document/event store.
- `S1-05-ARXIV-CONNECTOR-CONTRACT-001`: arXiv source registry contract.
- `S1-06-SCORING-QUEUE-LEDGER-001`: research scoring, 10,000 queue behavior,
  and content ledger.
- `S1-07-B1_REPORT_EMAIL_TEXT-001`: B1 teaching report, claims, and email text
  preview.
- `S1-08-LOCAL_RUNTIME_RECOVERY-001`: tick, watchdog, backup, restore, runtime
  audit, and scheduler controls.
- `S1-09-MIGRATION_PACKAGE-001`: low-resource integration and migration package.
- `S1-10-POST_MIGRATION_BOOTSTRAP-001`: migration-bound target machine or
  GitHub-hosted runner bootstrap.
- `S1-11-HISTORICAL_B1_PREVIEWS-001`: completed 30 independent historical B1
  report/email previews.
- `S1-12-CONTROLLED_B1_LIVE_EMAIL_DAYS-001`: completed through the PR #82
  accelerated real-arXiv acceptance artifact and existing controlled SMTP refs.

## Local Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=arxiv-daily-push/src python3 scripts/validate_project_governance.py --project arxiv-daily-push
git diff --check
```

## Resource Policy

Do not commit media, model weights, voice samples, credentials, Codex auth,
GitHub tokens, SMTP secrets, render cache, or dependency directories. Stage 1
Window A remains low-resource until migration readiness is explicitly proven:
no PDF bulk downloads, no large model/TTS downloads, no full 30-day replay, no
real SMTP send, no Release upload, no production scheduler enablement, and no
broad non-arXiv source expansion.
