# Legacy Migration Record

Version: PFI-001

This file is the explicit allowlist for legacy terminology during the migration
from `PFI_OS` / `PFIOS` to `PFI OS`.

## Legacy Terms

- `PFI_OS`
- `PFI OS`
- `PFI_`
- `PFIOS`
- `pfi_os`
- `PFI_`
- `Token ROI`
- `token_roi`
- `tokenRoi`
- `EVAToken`

After PFI-003, these terms should appear only in this archive file or Git
history, except for temporary migration scripts that have a documented removal
date.

## Migration Order

1. PFI-001: product contracts and contract tests.
2. PFI-002: remove Token ROI and non-core active entrances without deleting user
   runtime data.
3. PFI-003: rename directory, namespace, scripts, env vars, app identity, and
   artifact prefixes to PFI OS.
4. PFI-004: create the new Web Shell and preserve rollback to legacy Streamlit
   only during migration.

## Explicit PFI-001 Non-Actions

- No runtime business logic changed.
- No Streamlit UI changed.
- No Token ROI code deleted.
- No data migration performed.
- No package or directory rename performed.
- No private data read or transformed.

## Disposition Summary

- Token ROI: delete from active product surfaces in PFI-002.
- Cashflow and consumption: remove from MVP user entrances.
- ResearchBus: internal compatibility layer only.
- Strategy backtesting: preserve and upgrade.
- Market-feel training: preserve and rebuild as Strategy Lab training mode.
- Holdings and portfolio risk: rebuild around formal private operational data.
