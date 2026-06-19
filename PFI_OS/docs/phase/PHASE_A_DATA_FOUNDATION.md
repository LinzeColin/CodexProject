# Phase A Data Foundation

Status: first contract slice

## Goal

Establish the official local operational store boundary for PFI OS before
moving UI pages or vertical workflows onto it.

## Current Slice

- Adds `pfi_os.application.operational_store`.
- Adds `pfi_os.application.source_registry`.
- Adds `pfi_os.application.homepage_summary`.
- Defines six data domains from the PFI data boundary.
- Defines default operational DB path:
  `$PFI_OS_DATA_HOME/private/operational/pfi.sqlite`.
- Creates official SQLite tables for sources, entities, evidence, jobs, tasks,
  and holding snapshots.
- Requires `source_id`, `as_of`, and `evidence_class` on fact-bearing records.
- Keeps ResearchBus as an internal compatibility layer, not a truth source.
- Web Shell homepage now consumes `PFIOSHomeSummaryV1` when the runtime injects
  it; static fallback remains available for offline shell loading.
- Homepage card source markers now point to `operational_store:*` read models,
  not direct `data/**` JSON artifacts.

## Not Done

- Legacy Streamlit UI still has direct JSON/provider reads outside the new
  Web Shell vertical slice.
- Existing holdings and ResearchBus code is not migrated yet.
- DuckDB/Parquet query surfaces remain in the existing `DataStore`.
- Full source ingestion, point-in-time query APIs, and vertical workflow
  migration are not complete.

## Next Phase A Iterations

1. Add repository adapters for holdings and task queues.
2. Add point-in-time source query APIs and immutable source versioning.
3. Migrate one real cached homepage slice into Operational Store records.
4. Add private-path and Git fixture scans for the new data-home layout.
5. Replace legacy Streamlit direct reads one vertical slice at a time.
