# Phase 11 Production Refs Readiness Bundle

## Scope

Add a no-secret readiness bundle gate for external production refs needed before
the default-branch trial start workflow can be launched.

## Added

- `adp plan-production-refs`
- `adp-production-refs-v1`
- `schemas/production_refs.schema.json`
- Regression tests for passing no-secret refs, secret-like payload blocking,
  missing SMTP secret-name blocking, CLI JSON output, and launch readiness
  consumption through `--production-refs-report`.

## Safety Boundaries

The refs bundle accepts only readiness metadata: runner label, required GitHub
secret names, required GitHub variable names, Release target name, ready flags,
and durable evidence refs. It must not include SMTP host values, SMTP port
values, usernames, passwords, API keys, tokens, credential blobs, or Codex auth.

The command does not inspect GitHub secret values, read `~/.codex/auth.json`,
dispatch GitHub Actions workflows, send SMTP mail, create Releases, mutate trial
evidence, generate media, retain model/cache artifacts, or claim production
acceptance.

## Validation Intent

`production_refs_ready=true` requires:

- `runner.ready=true`, a runner label, and a durable runner evidence ref.
- All required SMTP secret names:
  `ADP_SMTP_HOST`, `ADP_SMTP_PORT`, `ADP_SMTP_USERNAME`,
  `ADP_SMTP_PASSWORD`.
- `release_target.ready=true`, `var_name=ADP_RELEASE_TARGET`, a non-empty
  target, and a durable Release target evidence ref.
- All required workflow variable names:
  `ADP_RELEASE_TARGET`, `ADP_ALLOW_SMTP_SEND`, `ADP_ALLOW_RELEASE_UPLOAD`.
- Durable refs for `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and
  `workflow_vars_ref`.
- No secret-like input keys or values.

## Result

Local target tests pass for the new production refs gate and launch-readiness
integration. This does not unblock Phase 11 production acceptance by itself:
the owner still must provision real durable external refs, explicitly confirm
launch, run the default-branch trial start workflow, and collect 30 unique daily
production evidence entries plus replay, recovery, resource, SMTP, and Release
evidence.

## Rollback

Revert the production refs module, CLI command and launch integration, schema,
tests, runbook section, governance registry rows, and version bump to restore
version `0.11.19`.
