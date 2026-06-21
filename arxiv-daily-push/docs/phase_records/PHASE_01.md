# Phase 1 Repository Foundation

Project: `arXiv Daily Push`  
Task ID: `ADP-PHASE1-FOUNDATION-001`  
Acceptance ID: `ADP-ACC-PHASE1-FOUNDATION`  
Date: 2026-06-21  

## Scope

Create the CodexProject project directory, governance records, CLI skeleton,
configuration examples, schemas, and focused Phase 1 tests.

## Non-Scope

- arXiv ingest.
- ranking and queue logic.
- Claim Ledger extraction.
- TTS or video dependencies.
- GitHub Actions runner setup.
- real email sending.

## Commands

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q
python3 scripts/validate_project_governance.py --project arxiv-daily-push
git diff --check
```

## Acceptance

- `adp version` is implemented.
- `adp doctor` is implemented and fail-closed for missing Phase 1 required commands.
- `adp render-email` renders a dry-run email for `linzezhang35@gmail.com`.
- Governance validator passes for `arxiv-daily-push`.
- No media, model, voice, auth, or secret files are added.

## Current Result

PASS.

Validation evidence:

- `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`: 4 tests OK.
- `python3 scripts/validate_project_governance.py --project arxiv-daily-push`: errors 0, warnings 0.
- `python3 scripts/validate_project_governance.py --changed-only`: errors 0, warnings 0.
- `git diff --check`: exit 0.

Phase 2 is unlocked for the next bounded run; do not start Phase 2 in this
Phase 1 run.
