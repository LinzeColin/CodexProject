# Phase 11 Production Refs GitHub Metadata Discovery

Date: 2026-06-22
Task: `ADP-PHASE11-PRODUCTION-REFS-GITHUB-DISCOVERY-026`
Status: completed
Version: `0.11.23`

## Scope

Added a fail-closed GitHub Actions metadata discovery path for production refs.
The command is intended to run on the private runner after owner provisioning:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push discover-production-refs \
  --repo LinzeColin/CodexProject \
  --runner-label arxiv-daily-push \
  --generated-at <ISO timestamp> \
  --json
```

## Behavior

- Reads GitHub Actions metadata with `gh api`.
- Uses runner labels/status, SMTP secret names, GitHub variable names, and
  `ADP_RELEASE_TARGET` only.
- Builds a normal `adp-production-refs-v1` report so
  `plan-production-launch --production-refs-report` can consume it.
- Fails closed when `gh` is unavailable, metadata cannot be read, required names
  are missing, the runner label is not online, or refs are not durable.

## Safety

The discovery path does not read GitHub secret values, print `gh` stdout/stderr,
read `~/.codex/auth.json`, dispatch workflows, send SMTP mail, create Releases,
mutate trial evidence, retain media/model/cache artifacts, or claim production
acceptance.

## Local Evidence

- Focused tests: `19 tests OK`.
- Local CLI check: `discover-production-refs` exits `2` because `gh` is not on
  this machine's `PATH`, and the JSON output contains only the redacted error
  `gh command is required for GitHub metadata discovery`.

## Remaining Blockers

Production launch still requires a provisioned private runner, configured SMTP
secrets, configured GitHub variables, explicit launch confirmation, a passing
default-branch trial-start workflow run, real SMTP and Release evidence, and 30
unique daily production evidence entries with replay, recovery, and resource
telemetry proof.
