# Phase 11 Production Refs Template

## Scope

Added a no-secret production refs input template for the owner provisioning step
that remains blocking Phase 11 trial start.

## Added

- `adp print-production-refs-template`
- `config/examples/production_refs.input.example.json`
- Template tests proving required secret and variable names are present while
  secret values are absent.
- A fail-closed path from the generated template into `adp plan-production-refs`.

## Safety Boundaries

The template contains only readiness booleans, GitHub secret names, GitHub
variable names, runner label, optional Release target placeholder, and empty
durable evidence ref fields. It does not contain SMTP host values, SMTP port
values, usernames, passwords, API keys, tokens, credential blobs, Codex auth, or
Release media.

The command does not inspect GitHub secret values, read `~/.codex/auth.json`,
dispatch GitHub Actions workflows, send SMTP mail, create Releases, mutate trial
evidence, generate media, retain model/cache artifacts, or claim production
acceptance.

## Validation Intent

The generated template defaults all `ready` flags to `false`, so feeding it
directly to `adp plan-production-refs` must remain blocked until the owner fills
real durable readiness refs and flips readiness flags after external
provisioning.

## Result

Local focused tests pass for template generation, no-secret structure, CLI JSON
output, example JSON parsing, and expected blocked validation. This makes the
next owner provisioning step less error-prone, but it does not unblock
production launch or Phase 11 production acceptance by itself.

## Rollback

Remove the template function, CLI command, example input JSON, tests, runbook
section, governance registry rows, phase record, run manifest, and version bump
to restore version `0.11.21`.
