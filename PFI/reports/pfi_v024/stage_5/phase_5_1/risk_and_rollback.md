# Stage 5 Phase 5.1 Risk and Rollback

## Risks

- `PFI/web/index.html` now loads `./app/pages/home.js`; if packaged app embedding misses the file, the shell still keeps v0.2.3 fallback behavior.
- `PFI/web/app/shell.js` now passes `#pfi-read-model-status` into the v0.2.4 home model before initial render; malformed JSON falls back to empty state through existing parser guards.
- Homepage wording changes remove the old mechanical layer but do not complete Phase 5.2 subpage differentiation or Phase 5.3 full interaction-state work.

## Rollback

Rollback is scoped to the files listed in `changed_files.txt`.

Do not delete or mutate `MetaDatabase/PFI`.
Do not clean user data, app bundles, or unrelated worktrees.

