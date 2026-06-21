# Phase 11 Release Delivery Boundary

Project: `arxiv-daily-push`
Task: `ADP-PHASE11-RELEASE-DELIVERY-008`
Acceptance: `ADP-ACC-PHASE11-RELEASE-DELIVERY`
Version: `0.11.7`
Generated: `2026-06-21`

## Objective

Add a fail-closed GitHub Release delivery boundary so the system can produce
private Release delivery evidence by default and create a real Release only
when explicitly allowed.

## Implemented

- Added `src/arxiv_daily_push/release_delivery.py`.
- Added `adp publish-release`.
- Added `schemas/release_delivery.schema.json`.
- Added tests for dry-run delivery, missing target blocking, forbidden
  secret-like assets, mocked `gh release create`, no clobber upload, and CLI
  dry-run JSON.
- Updated the production trial runbook with dry-run and explicit
  `--allow-upload` commands.

## Safety Boundary

- Dry-run is the default and makes no `gh` call.
- Real Release creation requires `--allow-upload`.
- Real Release creation requires `ADP_RELEASE_TARGET` or `--target`.
- Real Release creation requires the `gh` command.
- Release creation uses `gh release create` and never adds `--clobber`.
- Assets must exist, be files, be non-empty, stay within the configured size
  gate, and avoid secret-like names and model-weight suffixes.
- Reports include tag, target, asset names, asset sizes, asset SHA256 values,
  and a redacted command preview.
- Release notes text, secret values, `gh` stdout, and `gh` stderr are not
  logged.

## Current Status

`pass for code gate`

This phase does not claim real private GitHub Release delivery. Production
acceptance still requires archived private Release evidence generated on the
provisioned runner during the 30-day trial.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_release_target PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_release_delivery.py arxiv-daily-push/tests/test_cli.py -q`: 9 focused tests OK.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_release_cli PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push publish-release --tag adp-release-probe-20260621 --title 'arXiv Daily Push release probe' --notes 'Release delivery boundary probe' --asset <temporary-json-asset> --generated-at 2026-06-21T05:00:00+10:00 --json`: dry-run evidence emitted.

Full validation results are recorded in the governance run manifest after the
complete local validation suite.

## Remaining Risks

- `gh` authentication and repository Release permissions are not verified in
  this local environment.
- `ADP_RELEASE_TARGET` is not provisioned for the production runner here.
- Real private Release delivery against `LinzeColin/CodexProject` is not
  verified.
- Production acceptance still requires runner provisioning, CA trust repair,
  SMTP configuration, scheduler, weekly/monthly replay, recovery drill, and
  30-day evidence.

## Rollback

Revert `release_delivery.py`, the `publish-release` CLI command,
`release_delivery.schema.json`, related tests, runbook updates, and restore
version `0.11.6`.
