# arXiv Daily Push Plans

## Current Phase

- Stage: `S1`
- Window: `A`
- Task ID: `S1-07-B1_REPORT_EMAIL_TEXT-001`
- Acceptance ID: `ADP-ACC-S1-07-B1-REPORT-EMAIL-TEXT`
- Gate: V5 Stage 1 B1/arXiv text-delivery baseline is active; scoring, queue,
  and content ledger work is locally verified, and the next task is the B1
  explanatory teaching report plus Chinese email text contract.

The current goal baseline is `docs/pursuing_goal/BASELINE_LOCK.md`. V4,
Phase 12, media, and Release-delivery records remain historical context only
for the current Stage 1 acceptance path.

## Stage 1 Window A Tasks

| Task ID | Status | Acceptance ID | Scope |
|---|---|---|---|
| `S1-01-READONLY-AUDIT-001` | completed | `ADP-ACC-S1-01-READONLY-AUDIT` | Verify V5 package hashes, current implementation gap, and evidence boundary without changing files. |
| `S1-02-V5-BASELINE-GOVERNANCE-CALIBRATION-001` | completed | `ADP-ACC-S1-02-V5-BASELINE-GOVERNANCE-CALIBRATION` | Lock V5 text-delivery baseline, demote conflicting V4/media requirements, and preserve useful S1-03/S1-04/S1-05 foundations. |
| `S1-03-OWNER-CONTROLS-001` | completed | `ADP-ACC-S1-03-OWNER-CONTROLS` | Add `config/owner_controls.yaml` and generated owner-facing views. |
| `S1-04-SQLITE-DATA-MODEL-001` | completed | `ADP-ACC-S1-04-SQLITE-DATA-MODEL` | Add the unified SQLite/WAL/FTS5 document and event model with migrations and rollback. |
| `S1-05-ARXIV-CONNECTOR-CONTRACT-001` | completed | `ADP-ACC-S1-05-ARXIV-CONNECTOR-CONTRACT` | Define source registry, connector contract, and arXiv adapter boundary. |
| `S1-06-SCORING-QUEUE-LEDGER-001` | completed | `ADP-ACC-S1-06-SCORING-QUEUE-LEDGER` | Implement research scoring, 10,000 queue behavior, source-share cap, 365-day window, reason codes, and text-first content ledger. |
| `S1-07-B1_REPORT_EMAIL_TEXT-001` | planned | `ADP-ACC-S1-07-B1-REPORT-EMAIL-TEXT` | Produce B1/arXiv explanatory teaching report, Claim evidence, Chinese email text/HTML preview, and audit artifacts. |
| `S1-08-LOCAL_RUNTIME_RECOVERY-001` | planned | `ADP-ACC-S1-08-LOCAL-RUNTIME-RECOVERY` | Add `tick`, `watchdog`, backup, restore, runtime audit, and scheduler controls without enabling production. |
| `S1-09-MIGRATION_PACKAGE-001` | planned | `ADP-ACC-S1-09-MIGRATION-PACKAGE` | Build the low-resource integration, cloud-runner proof, and migration checklist. |

## Window A Resource Limits

- Online arXiv metadata records: at most 10 for local canaries.
- Raw retained artifacts: at most 100 MB.
- Temporary workspace: at most 2 GB.
- No PDF bulk download.
- No large model or TTS model download.
- No video generation requirement.
- No 30-day replay during low-resource preparation.
- No formal scheduler installation or production enablement.
- No broad non-arXiv source expansion.

## Execution Contract Template

1. Goal.
2. Minimum relevant scope.
3. Files and directories to inspect.
4. Files likely to change.
5. Validation commands.
6. Risks and rollback.
7. Stop conditions.

## Validation Commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push.tests.test_owner_controls arxiv-daily-push.tests.test_stage1_queue arxiv-daily-push.tests.test_cli -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=arxiv-daily-push/src python3 scripts/validate_semantic_extractors.py arxiv-daily-push
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=arxiv-daily-push/src python3 scripts/validate_project_governance.py --project arxiv-daily-push
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=arxiv-daily-push/src python3 scripts/validate_project_governance.py --changed-only --enforce-sync --semantic --base-ref origin/main
git diff --check
```
