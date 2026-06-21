# Phase 11 Provisioning Audit Workflow

Date: 2026-06-22
Task: `ADP-PHASE11-PROVISIONING-AUDIT-WORKFLOW-028`
Status: completed
Version: `0.11.25`

## Scope

Added a manual GitHub-hosted provisioning audit workflow that can run before
the private self-hosted trial-start workflow. The workflow produces a no-secret
production refs readiness artifact without occupying the private runner.

## Behavior

- Runs on `ubuntu-latest`.
- Uses `discover-production-refs` to inspect GitHub Actions metadata.
- Verifies the requested runner label, required SMTP secret names, required
  workflow variables, and `ADP_RELEASE_TARGET`.
- Uses `secrets.ADP_GITHUB_METADATA_TOKEN` when configured and falls back to
  `github.token`.
- Uploads `adp-production-provisioning-audit`.
- Fails closed when metadata access, runner label, secret names, variables, or
  durable readiness refs are missing.

## Safety

The workflow does not read secret values, read Codex auth, start the private
self-hosted runner job, dispatch trial-start, send SMTP mail, create Releases,
mutate trial evidence, retain media/model/cache artifacts, or claim Phase 11
production acceptance.

## Local Evidence

- Focused tests: `20 tests OK`.
- Local `discover-production-refs` exits `2` because `gh` is not available on
  this machine, with JSON output parseable and error text redacted.

## Remaining Blockers

Production trial start still requires owner-provisioned GitHub metadata access,
the private runner online with the configured label, required SMTP secrets and
workflow variables, a passing provisioning audit artifact, a passing
default-branch trial-start workflow run, real SMTP and Release evidence, and 30
unique daily production entries with replay, recovery, and resource telemetry
proof.
