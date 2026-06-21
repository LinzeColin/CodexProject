# Phase 11 Release Permissions Hardening

## Scope

Hardened the two GitHub Actions entry points that must eventually create real
GitHub Release evidence:

- `.github/workflows/arxiv-daily-push-trial-start.yml`
- `.github/workflows/arxiv-daily-push-scheduled.yml`

## Result

Both workflows now declare `contents: write` alongside `actions: read`, and the
workflow contract validators require that permission before marking the workflow
contract ready.

This does not enable Release uploads by itself. Real Release creation remains
blocked unless the existing explicit gates are set:

- `ADP_ALLOW_RELEASE_UPLOAD=true`
- valid `ADP_RELEASE_TARGET`
- safe asset checks
- available `gh`
- Release delivery validator pass

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_release_perms_focus PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_trial_start_workflow.py arxiv-daily-push/tests/test_production_scheduler.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_release_perms_cli PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push plan-trial-start-workflow --path . --generated-at 2026-06-22T18:00:00+10:00 --json
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_release_perms_cli2 PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push plan-production-scheduler --path . --generated-at 2026-06-22T18:00:00+10:00 --json
```

## Evidence

- Focused scheduler/workflow tests: 6 tests OK.
- Trial start workflow JSON plan parses and validates.
- Production scheduler JSON plan parses and validates.

## Remaining Blockers

Production launch is still blocked until durable runner, SMTP secret, Release
target, workflow variable refs, and explicit launch confirmation exist.

Production acceptance still requires a passing default-branch trial-start run,
30 unique daily production evidence entries, weekly/monthly replay evidence,
recovery drill evidence, resource telemetry, real SMTP evidence, and private
Release evidence.
