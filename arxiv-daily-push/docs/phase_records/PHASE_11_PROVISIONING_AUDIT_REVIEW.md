# Phase 11 Provisioning Audit Review

Date: 2026-06-22
Task: `ADP-PHASE11-PROVISIONING-AUDIT-REVIEW-029`
Status: completed
Version: `0.11.26`

## Scope

Added a no-side-effect review gate for downloaded `adp-production-
provisioning-audit` artifacts. The gate lets a later production operator bind
a passing production refs report to durable GitHub Actions workflow run and
artifact refs before any private-runner trial-start dispatch.

## Behavior

- Adds `review-provisioning-audit`.
- Requires a valid passing `adp-production-refs-v1` report.
- Requires `production_refs_ready=true`.
- Requires durable `workflow_run_ref` and `artifact_ref`.
- Carries forward runner, SMTP secret-name, Release target, and workflow
  variable readiness refs from the production refs report.
- Fails closed when the report is blocked, malformed, missing durable refs, or
  records unsafe side effects.

## Safety

The review command does not read secret values, read Codex auth, dispatch
workflows, send SMTP mail, upload Releases, mutate trial evidence, retain
media/model/cache artifacts, or claim Phase 11 production acceptance.

## Local Evidence

- Focused tests: `23 tests OK`.
- CLI fixture review returns exit `0` with `provisioning_audit_ready=true`.
- CLI blocked sample returns exit `2` when workflow or artifact refs are
  missing.

## Remaining Blockers

Production trial start still requires the owner to run the provisioning audit,
download the actual artifact, provide durable refs, provision the private
runner, GitHub secrets, workflow variables, Release target, and explicit launch
confirmation, run the default-branch trial-start workflow, and collect 30 unique
daily production entries with real SMTP, Release, replay, recovery, and resource
telemetry evidence.
