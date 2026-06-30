# PFI v0.2.4 Stage 1 Phase 1.1 Risk and Rollback

## Scope

This phase captures the current `PFI/web/app/shell.js` state and records syntax
and structural diagnostics. It does not repair `shell.js`.

## Risks

- Phase 1.1 may be mistaken for Stage 1 completion. It is not; Phase 1.2 and
  Phase 1.3 remain required.
- The exact `node --check` command is unavailable in the current Codex shell
  because `node` is not on PATH; the Codex bundled Node binary is used for the
  actual syntax check and this environment gap is recorded.
- The committed snapshot is large because it intentionally preserves the
  current shell file before Phase 1.2 repair.

## Rollback

Revert the Phase 1.1 commit. No user data, app bundle, launcher, business UI
behavior, or data logic is changed by this phase.
