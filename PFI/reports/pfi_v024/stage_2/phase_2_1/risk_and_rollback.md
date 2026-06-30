# PFI v0.2.4 Stage 2 Phase 2.1 Risk and Rollback

## Scope

This phase only maps the app/local/static entry chain and records old UI
signatures. It does not implement the version chain, reinstall apps, or run
browser/app validation.

## Risks

- Entry mapping could become stale if app bundles are reinstalled before Phase 2.2.
- The old v0.2.3 Stage 1 signatures are recorded but intentionally not fixed in this phase.
- Evidence could be mistaken for app/browser validation; it is not.

## Controls

- Contract tests assert Phase 2.2 and Phase 2.3 remain incomplete.
- Evidence explicitly records no app bundle, launcher, data logic, or business UI changes.
- App launcher dry-run output records current app-root bindings without launching UI.

## Rollback

Revert the Phase 2.1 commit. No installed app, launcher, data, or UI runtime
files are modified by this phase.
