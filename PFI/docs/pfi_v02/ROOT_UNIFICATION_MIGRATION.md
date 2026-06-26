# PFI Root Unification Migration

Date: 2026-06-27 Australia/Sydney

## Decision

`CodexProject/PFI` is the only active GitHub and local product root.

## Changes

- Migrated QBVS from the misleading product-root-like path into
  `PFI/modules/qbvs_lab`.
- Migrated the former local app shell into `PFI`:
  `src/pfi_os`, `scripts`, `macos`, `assets`, `web`, `shared`, and `systems`.
- Replaced installed app target from `PFI_OS.app` to `PFI.app`.
- Removed the old `PFI_OS` root from the active repository tree.
- Kept old app/root documentation under `PFI/docs/pfi_os_legacy` for audit
  history only.
- Excluded old virtual environment, cache, and generated runtime output from
  the new active product root.
- Installed fresh `PFI.app` entries in `/Applications`, `~/Downloads`, and
  `~/Desktop`, all bound to `CodexProject/PFI` via `PFI_PROJECT_ROOT`.
- Stopped the stale `CodexProject/PFI_OS` Streamlit process that was still
  serving port 8501 after the old root was removed.
- Migrated local runtime data from `~/.pfi_os` to `~/.pfi` after creating a
  config backup.

## Backup

- Git backup branch: `backup/pfi-root-unification-pre-20260627T081546`
- Local backup archive:
  `/Users/linzezhang/Downloads/PFI_ROOT_UNIFICATION_BACKUP_20260627T081546.tar.gz`
- Local data-home backup:
  `/Users/linzezhang/Downloads/PFI_HOME_CONFIG_BACKUP_20260627T222831.tar.gz`

## Canonical Paths

| Purpose | Path |
| --- | --- |
| Product root | `PFI/` |
| V0.2 contracts | `PFI/src/pfi_v02` |
| Migrated app shell | `PFI/src/pfi_os` |
| App installer | `PFI/scripts/installPFIEntryApps.sh` |
| macOS app template | `PFI/macos/PFI.app` |
| Installed app | `/Applications/PFI.app`, `~/Downloads/PFI.app`, `~/Desktop/PFI.app` |
| Local data home | `~/.pfi` or explicit `$PFI_DATA_HOME` |
| QBVS strategy lab | `PFI/modules/qbvs_lab` |
| QBVS package | `PFI/modules/qbvs_lab/qbvs` |
| Archived legacy docs | `PFI/docs/pfi_os_legacy` |

## Boundaries

- No trading password.
- No automatic real-money orders.
- No broker-order submission.
- No payment submission.
- No Alpha product page inside PFI.

## Validation Evidence

- Stage 1/2 contracts: 45 tests passed.
- QBVS lifecycle contract: 1 test passed.
- macOS app lite acceptance: 29 pass, 0 fail.
- Manual browser navigation evidence:
  `PFI/data/systemAudit/PFIManualNavigationAcceptance_latest.json`.
- Confirmed app entry dry-run:
  `/Applications/PFI.app/Contents/MacOS/PFI` resolves
  `CodexProject/PFI/StartPFI.command`.
