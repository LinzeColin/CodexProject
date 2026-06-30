# Risk And Rollback

## Risk

- `PFI/web/app/routes.js` now owns a v0.2.4 route API while preserving the existing v0.2.3 `PFI_V023_STAGE3_NAV` compatibility payload.
- `PFI/web/app/shell.js` now consults `PFI_V024_STAGE3_ROUTES.resolveRouteAlias()` before fallback parsing. If the route API is absent, the existing local fallback still resolves legacy aliases and owned routes.
- Browser route behavior is declared and wired, but real browser back/forward screenshot validation remains Phase 3.3.
- The local branch is ahead 1 and behind 7 relative to `origin/main`; remote delta does not touch `PFI/`. Before any GitHub main upload, sync with `origin/main`.

## Rollback

Revert the Phase 3.2 commit or restore:

- `PFI/web/app/routes.js` to the Phase 3.1 route compatibility state.
- `PFI/web/app/shell.js` to local route parsing without `PFI_V024_STAGE3_ROUTES`.
- `PFI/src/pfi_v02/stage_v024_stage3_navigation.py` to the Phase 3.1-only contract.

Rollback does not touch user financial data, app bundles, launcher C/Info.plist, or `MetaDatabase/PFI`.
