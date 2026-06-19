# Phase A Data Foundation

Status: first contract slice

## Goal

Establish the official local operational store boundary for PFI OS before
moving UI pages or vertical workflows onto it.

## Current Slice

- Adds `pfi_os.application.operational_store`.
- Defines six data domains from the PFI data boundary.
- Defines default operational DB path:
  `$PFI_OS_DATA_HOME/private/operational/pfi.sqlite`.
- Creates official SQLite tables for sources, entities, evidence, jobs, tasks,
  and holding snapshots.
- Requires `source_id`, `as_of`, and `evidence_class` on fact-bearing records.
- Keeps ResearchBus as an internal compatibility layer, not a truth source.

## Not Done

- UI still has legacy direct JSON/provider reads.
- Existing holdings and ResearchBus code is not migrated yet.
- DuckDB/Parquet query surfaces remain in the existing `DataStore`.
- Source registry ingestion and point-in-time query APIs are not complete.

## Next Phase A Iterations

1. Add Source Registry service on top of `source_records`.
2. Add repository adapters for holdings and task queues.
3. Add UI/application read contracts that consume Operational Store summaries.
4. Migrate one cached homepage slice off direct JSON reads.
5. Add private-path and Git fixture scans for the new data-home layout.
