# PFI v0.2.4 Stage 0 Phase 0.3 Risk and Rollback

## Scope

This phase only adds Stage 0 contract verification and evidence records. It does
not modify business UI, app bundle, launcher, runtime service, or financial data
logic.

## Risks

- Stage 0 may be mistaken for fully complete before whole-stage review.
- Local `node` may be unavailable on PATH even though the bundled Codex Node can
  verify `PFI/web/app/shell.js`.
- Evidence may become stale if a later phase changes the Stage 0 contract.

## Rollback

Revert the Phase 0.3 commit or remove the Phase 0.3 test/evidence additions and
restore the top-level status files to Phase 0.2. No user data or runtime data is
created, modified, or deleted by this phase.
