# Risk And Rollback

## Risk

- `PFI/web/index.html` now loads `PFI/web/app/navigation.js` before `routes.js`; missing Streamlit inlining would make the app iframe try to fetch a relative external script. This is mitigated by updating `_pfi_web_shell_html()`.
- `PFI/web/app/shell.js` now prefers `window.PFI_V024_STAGE3_NAVIGATION`; if the new contract is unavailable, it falls back to the existing v0.2.3 route contract and then an internal alias fallback.
- The local branch is behind `origin/main` by 7 non-PFI commits at evidence time. Before any GitHub main upload, rebase or otherwise sync with `origin/main`.

## Rollback

Revert the Phase 3.1 commit or remove the following scoped changes:

- Remove `PFI/web/app/navigation.js` and its `<script>` tag.
- Restore `PFI/web/index.html` `data-pfi-stage` and `data-pfi-phase` fields if returning to Stage 2 evidence state.
- Restore `_pfi_web_shell_html()` to inline only version, entry audit, routes, pages, and shell scripts.
- Restore `PFI/web/app/shell.js` to read only `window.PFI_V023_STAGE3_NAV`.

Rollback does not touch user financial data, app bundles, launcher C/Info.plist, or `MetaDatabase/PFI`.
