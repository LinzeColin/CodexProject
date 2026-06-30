# PFI v0.2.4 Stage 2 Build and Hash Display Spec

## Purpose

Phase 2 must make app and localhost entry identity visible and machine-readable.
Phase 2.1 only defines where these values must appear. Phase 2.2 implements
them.

## Required Fields

| Field | Meaning |
| --- | --- |
| `repairLabel` | Visible product label, expected to include `PFI v0.2.3 Repair`. |
| `buildId` | Current repair build id. |
| `bundleHash` | Hash derived from the shipped Web Shell assets. |
| `uiContractVersion` | Current UI contract version. |
| `webIndexSha256` | SHA256 for `PFI/web/index.html`. |
| `shellJsSha256` | SHA256 for `PFI/web/app/shell.js`. |

## Display and Read Locations

| Surface | Location | Phase |
| --- | --- | --- |
| `PFI/web/index.html` | Body dataset and visible status strip. | 2.2 |
| `PFI/web/app/version.js` | `window.PFI_STAGE1_VERSION` and read function. | 2.2 |
| `PFI/web/app/entry_audit.js` | New entry audit read model for app/local/browser validation. | 2.2 |
| Browser evidence | DOM extraction for app, localhost, clean-cache, and new-profile paths. | 2.3 |

## Non-Goals

- Do not hardcode financial metrics.
- Do not use localStorage/sessionStorage/IndexedDB as production proof.
- Do not treat README or docs text as entry validation.
