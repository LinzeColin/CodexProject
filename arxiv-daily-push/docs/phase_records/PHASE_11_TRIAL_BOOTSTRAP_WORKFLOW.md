# PHASE_11_TRIAL_BOOTSTRAP_WORKFLOW

Project: `arxiv-daily-push`
Phase: `E`
Task: `ADP-PHASE11-TRIAL-BOOTSTRAP-005`
Status: `PASS_FOR_BOOTSTRAP_GATE`
Version: `0.11.4`

## Scope

Added a manual GitHub Actions bootstrap entrypoint for the real production trial
path.

The bootstrap gate includes:

- workflow_dispatch-only GitHub Actions workflow;
- explicit `confirm_production_trial=true` guard;
- private self-hosted runner label input;
- production preflight execution before project tests or trial work;
- upload of the `adp-production-preflight` JSON artifact;
- runbook for runner, SMTP, Release target, and 30-day evidence steps;
- CLI validator `adp plan-trial-bootstrap`.

## Non-Scope

- No cron schedule.
- No Release upload.
- No SMTP send.
- No media rendering or model download.
- No claim that the 30-day trial has started or passed.

## Current Environment Status

`bootstrap_ready`

The repository now has a manual preflight-first entrypoint. Actual production
trial start is still blocked until a private runner and external prerequisites
are provisioned and the production preflight passes on that runner.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_bootstrap_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`: 74 tests OK.
- `for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done`: all schema JSON files parse.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_bootstrap_cli PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push plan-trial-bootstrap --path . --generated-at 2026-06-22T00:30:00+10:00 --json`: exit 0; bootstrap plan pass.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_bootstrap_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q`: 35 tests OK.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_bootstrap_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push`: errors 0 warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_bootstrap_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync`: errors 0 warnings 0.
- `PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_bootstrap_dashboard python3 scripts/generate_governance_dashboard.py --write`: PASS.
- `git diff --check`: exit 0.

## Result

The system now has a GitHub-visible manual bootstrap path for starting the real
trial safely. Full production/30-day acceptance remains blocked until external
runner, SMTP, Release, resource, scheduled execution, and 30-day evidence exists.
