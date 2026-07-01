# Stage 5 Phase 5.2 Risk and Rollback

## Risks

- `stage5Subpages.js` depends on the existing Stage 4 page catalog as its source data. If the Stage 4 catalog is missing, validation fails rather than creating fallback pages.
- `shell.js` still uses the existing render function names for compatibility, but prefers the v0.2.4 Stage 5 catalog when present.
- `streamlit_app.py` now inlines `stage5Subpages.js`; missing file packaging would fail early during app HTML assembly.

## Rollback

Rollback is limited to the files in `changed_files.txt`.

Do not delete or mutate `MetaDatabase/PFI`.
Do not clean user data, app bundles, or unrelated worktrees.

