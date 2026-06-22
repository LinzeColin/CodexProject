# arXiv Daily Push Plans

## Current Phase

- Stage: `S1`
- Window: `A`
- Task ID: `S1-02-BASELINE-LOCK-TRACEABILITY-001`
- Acceptance ID: `ADP-ACC-S1-02-BASELINE-LOCK`
- Gate: V4 baseline locked, version drift removed, manual delivery evidence bound, and traceability updated.

The current goal baseline is `docs/pursuing_goal/BASELINE_LOCK.md`. The older
`docs/pursuing_goal/06_PURSUING_GOAL_READY_PROMPT.md` remains historical context
only.

## Stage 1 Window A Tasks

| Task ID | Status | Acceptance ID | Scope |
|---|---|---|---|
| `S1-01-READONLY-AUDIT-001` | completed | `ADP-ACC-S1-01-READONLY-AUDIT` | Verify Review8 package hashes, current implementation gap, and GitHub evidence without changing files. |
| `S1-02-BASELINE-LOCK-TRACEABILITY-001` | in_progress | `ADP-ACC-S1-02-BASELINE-LOCK` | Lock the V4 baseline into governance and connect requirements, tasks, tests, and evidence. |
| `S1-03-OWNER-CONTROLS-001` | planned | `ADP-ACC-S1-03-OWNER-CONTROLS` | Add `config/owner_controls.yaml` and generated owner-facing views. |
| `S1-04-SQLITE-DATA-MODEL-001` | planned | `ADP-ACC-S1-04-SQLITE-DATA-MODEL` | Add the unified SQLite/WAL/FTS5 document and event model with migrations and rollback. |
| `S1-05-ARXIV-CONNECTOR-CONTRACT-001` | planned | `ADP-ACC-S1-05-ARXIV-CONNECTOR-CONTRACT` | Define source registry, connector contract, and arXiv adapter boundary. |
| `S1-06-SCORING-QUEUE-LEDGER-001` | planned | `ADP-ACC-S1-06-SCORING-QUEUE-LEDGER` | Implement research scoring, 10,000 queue behavior, and content ledger. |
| `S1-07-B1_REPORT_EMAIL_MEDIA-001` | planned | `ADP-ACC-S1-07-B1-REPORT-EMAIL-MEDIA` | Produce B1 report, Claim evidence, email preview, and media interface. |
| `S1-08-LOCAL_RUNTIME_RECOVERY-001` | planned | `ADP-ACC-S1-08-LOCAL-RUNTIME-RECOVERY` | Add `tick`, `watchdog`, backup, restore, runtime audit, and scheduler controls. |
| `S1-09-MIGRATION_PACKAGE-001` | planned | `ADP-ACC-S1-09-MIGRATION-PACKAGE` | Build the low-resource integration and new-machine migration checklist. |

## Window A Resource Limits

- Online arXiv metadata records: at most 10.
- Raw retained artifacts: at most 100 MB.
- Temporary workspace: at most 2 GB.
- Media smoke: at most 30 seconds at 480p.
- No PDF bulk download.
- No large model or TTS model download.
- No 30-day replay.
- No formal scheduler installation.
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
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=arxiv-daily-push/src python3 scripts/validate_semantic_extractors.py arxiv-daily-push
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=arxiv-daily-push/src python3 scripts/validate_project_governance.py --project arxiv-daily-push
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=arxiv-daily-push/src python3 scripts/validate_project_governance.py --changed-only --enforce-sync --semantic --base-ref origin/main
git diff --check
```

