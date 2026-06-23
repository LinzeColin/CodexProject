# PHASE S1P5T05 - Local Production And Migration Prep

Task: `ADP-S1P5T05-LOCAL-PRODUCTION-AND-MIGRATION-PREP`
Acceptance: `ADP-ACC-S1P5T05-LOCAL-PRODUCTION-MIGRATION-PREP`
Date: 2026-06-24

## Result

Status: `completed`

Stage 1 arXiv remains accepted. This task prepares the owner-approved final
runner strategy: local Mac + Codex/local runner before 2026-06-30, then the new
Mac after migration. GitHub remains code, PR/CI, evidence, status, and backup
only.

## Implemented

- `local-runner preflight` checks local commands, state directory, disk, memory,
  and SMTP secret-name presence without reading or logging secret values.
- `local-runner daily` runs the Stage 1 all-arXiv daily path with local queue,
  local content ledger, per-run reports, and plain/HTML email preview evidence.
- `ADP_LOCAL_DAILY_RUN_ENABLED` allows the local daily-run path without enabling
  GitHub cloud scheduled production.
- `local-runner launchd-package` generates a disabled launchd package and owner
  scripts; it does not install or enable the scheduler.
- `LOCAL_CODEX_RUNNER_RUNBOOK.md` documents smoke test, evidence files, local
  SMTP env setup, launchd package generation, and the 2026-06-30 migration.

## Safety

- `secret_values_logged=false`
- `github_cloud_schedule_enabled=false`
- `production_schedule_enabled=false`
- `real_smtp_sent=false`
- `release_upload_enabled=false`
- `video_generated=false`
- `launchd_installed=false`

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_s1p5t05_focus_now PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_local_runner.py arxiv-daily-push/tests/test_scheduled_execution.py arxiv-daily-push/tests/test_stage1_migration.py -q
```

Result: `15 tests OK`

Additional verification:

- `python3 -m unittest discover -s arxiv-daily-push/tests -q`: `207 tests OK`
- `scripts/validate_semantic_extractors.py arxiv-daily-push`: `48` formulas and
  `342` parameters checked
- `scripts/validate_project_governance.py --changed-only --enforce-sync
  --semantic --base-ref origin/main`: errors `0`, warnings `0`
- `python3 -m unittest discover -s tests/governance -p 'test_*.py' -q`:
  `192 tests OK`
- `git diff --check`: pass
- cache check: no `__pycache__` or `.pyc` files under `arxiv-daily-push`,
  `tests`, or `scripts`

## Next

Current next task: `S2P1T01` - bioRxiv and medRxiv source promotion.
