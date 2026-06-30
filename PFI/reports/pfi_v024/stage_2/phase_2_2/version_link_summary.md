# PFI v0.2.4 Stage 2 Phase 2.2 Version Link Summary

## Implemented

- Visible repair label: `PFI v0.2.3 Repair`.
- Build id: `pfi-v024-stage2-phase22`.
- Bundle version: `20260630.2`.
- UI contract version: `PFI-V024-STAGE2-ENTRY-CONSISTENCY`.
- Web bundle hash: `e8928ed7f3067ae3e732aacda74427a61b69fbcfe855b2254118e7dafe38f8e4`.

## Entry Surfaces

| Surface | Phase 2.2 result |
| --- | --- |
| `PFI/web/index.html` | Body dataset and visible status strip expose repair/build/hash/contract identity. |
| `PFI/web/styles/tokens.css` | Keeps the visible entry identity strip stable in the top-bar layout and is included in the bundle hash. |
| `PFI/web/app/version.js` | Exposes `window.PFI_STAGE2_ENTRY_VERSION` and `window.PFI_READ_STAGE2_ENTRY_VERSION`. |
| `PFI/web/app/shell.js` | Reads runtime metadata and writes it into body dataset and the visible status strip. |
| `PFI/web/app/entry_audit.js` | Exposes `window.PFI_STAGE2_ENTRY_AUDIT` and `window.PFI_READ_STAGE2_ENTRY_AUDIT`. |
| `PFI/src/pfi_os/app/streamlit_app.py` | Injects Stage 2 runtime metadata and inlines version/audit scripts. |
| `PFI/StartPFI.command` | Opens `pfi-v024-stage2-phase22` query contract. |
| `PFI/scripts/startPFI.sh` | Opens `pfi-v024-stage2-phase22` query contract. |

## Explicitly Not Done

- No app bundle reinstall.
- No app/localhost/browser screenshot evidence.
- No clean-cache or new-profile validation.
- No Stage 2 whole-stage review.
- No GitHub main upload.
