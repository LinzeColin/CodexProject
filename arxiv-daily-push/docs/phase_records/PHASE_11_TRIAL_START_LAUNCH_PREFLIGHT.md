# Phase 11 Trial Start Launch Preflight

Date: 2026-06-22
Task: `ADP-PHASE11-TRIAL-START-LAUNCH-PREFLIGHT-027`
Status: completed
Version: `0.11.24`

## Scope

Updated the default-branch trial-start workflow so it runs production refs
discovery and launch readiness before any live source ingest, SMTP probe,
Release probe, or trial-start gate work.

## Behavior

- Runs `discover-production-refs` after production preflight passes.
- Uploads `adp-trial-start-production-refs`.
- Stops before source, SMTP, Release, or start-gate work when refs discovery is
  blocked.
- Builds default-branch launch metadata for the checked-out commit.
- Runs `plan-production-launch --production-refs-report ... --confirm-launch`.
- Uploads `adp-trial-start-launch-readiness`.
- Stops before source, SMTP, Release, or start-gate work when launch readiness is
  blocked.

## Safety

This change does not dispatch the workflow, read GitHub secret values, read
Codex auth, send SMTP mail, create Releases, mutate trial evidence, retain
media/model/cache artifacts, or claim Phase 11 production acceptance.

## Local Evidence

- Focused tests: `13 tests OK`.
- `plan-trial-start-workflow` returned `status=pass` with
  `production_refs_before_source_and_delivery` and
  `launch_readiness_before_source_and_delivery` checks passing.

## Remaining Blockers

Production trial start still requires the owner-provisioned private runner,
configured GitHub SMTP secrets and variables, Release target, controlled
side-effect variables, a passing default-branch workflow run, real SMTP and
Release evidence, and 30 unique daily production entries with replay, recovery,
and resource telemetry proof.
