# PFI v0.2.4 Stage 1 Phase 1.3 Risk and Rollback

## Scope

This phase records Stage 1 validation evidence only. It does not change
`PFI/web/app/shell.js`, `PFI/web/app/version.js`, business UI, app bundle,
launcher, or data logic.

## Risks

- Stage 1 may be mistaken for complete after Phase 1.3. It is only candidate
  complete until whole-stage review runs and any findings are fixed.
- GitHub main remains behind the local PFI Stage 1 commits by design; upload is
  deferred until whole-stage review and fixes are complete.
- The shell environment does not provide `node` on default PATH, so Phase 1.3
  runs the exact `node --check` command with PATH including the Codex bundled
  Node binary.

## Rollback

Revert the Phase 1.3 commit. Phase 1.1 and Phase 1.2 remain separate local
commits unless explicitly reverted.
