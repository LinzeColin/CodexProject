# PFI v0.2.4 Stage 1 Phase 1.2 Risk and Rollback

## Scope

This phase adds the minimum shell integrity API and version read interface. It
does not rebuild UI, change app bundle entry points, or alter financial metric
logic.

## Risks

- `PFI/web/app/version.js` is added but not wired into `index.html` in this
  phase, because Stage 1 allowed files do not include `index.html`. Entry
  consistency is reserved for Stage 2.
- The shell boundary wraps initialization and route events, but Phase 1.3 still
  must run validation closeout before Stage 1 can be reviewed as complete.
- Local branch remains ahead of `origin/main`; GitHub upload is intentionally
  deferred until the full Stage 1 review and fixes are complete.

## Rollback

Revert the Phase 1.2 commit. Phase 1.1 snapshot evidence remains available at
`PFI/reports/pfi_v024/stage_1/phase_1_1/shell.js.snapshot`.
