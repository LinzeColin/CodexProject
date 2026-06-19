# Phase A Data Foundation

Status: first contract slice

## Goal

Establish the official local operational store boundary for PFI OS before
moving UI pages or vertical workflows onto it.

## Current Slice

- Adds `pfi_os.application.operational_store`.
- Adds `pfi_os.application.source_registry`.
- Adds `pfi_os.application.homepage_summary`.
- Adds `pfi_os.application.repositories` for entities, evidence search, job
  execution state, review tasks, and holding snapshots.
- Defines six data domains from the PFI data boundary.
- Defines default operational DB path:
  `$PFI_OS_DATA_HOME/private/operational/pfi.sqlite`.
- Creates official SQLite tables for sources, entities, evidence, jobs, tasks,
  source versions, and holding snapshots.
- Requires `source_id`, `as_of`, and `evidence_class` on fact-bearing records.
- Keeps ResearchBus as an internal compatibility layer, not a truth source.
- Every source upsert appends an immutable `source_versions` row for
  point-in-time source replay.
- Source Registry exposes point-in-time rows for a requested `as_of`.
- Web Shell homepage now consumes `PFIOSHomeSummaryV1` when the runtime injects
  it; static fallback remains available for offline shell loading.
- Homepage card source markers now point to `operational_store:*` read models,
  not direct `data/**` JSON artifacts.
- Entity, evidence, job, task queue, and holding snapshot workflows now have
  thin repository adapters over Operational Store official tables.
- Data-home boundary audit now checks that `$PFI_OS_DATA_HOME` and Operational
  SQLite stay outside public Git and that private/runtime/secret path fixtures
  fail closed before migration work adds new data surfaces.
- Homepage ingestion now migrates the command-center latest cache into
  Operational Store source, evidence, job, and task records before building
  `PFIOSHomeSummaryV1`; the Web Shell still consumes only the compact read
  model.
- The legacy Streamlit command-center view now reads a sanitized Operational
  Store command-center read model for display instead of directly building the
  full command-center payload during page render.
- File source ingestion now enforces checksum/provenance metadata, public
  project-relative URIs, private-source-outside-Git boundaries, and rejects
  ephemeral runtime files as fact sources.
- The legacy Streamlit Vectorized Research panel now ingests
  `data/vectorized/VectorizedResearch_latest.json` into Operational Store and
  renders a sanitized vectorized research read model instead of reading the
  latest JSON directly during page render.
- The legacy Streamlit macOS runtime evidence panel now ingests the local-only
  `data/systemAudit/MacOSRuntimeAcceptance_latest.json` into Operational
  Store as `PRIVATE_DERIVED` evidence and renders a sanitized read model
  without raw local paths, PIDs, screenshots, browser paths, or logs.

## Not Done

- Legacy Streamlit UI still has direct JSON/provider reads outside the Web
  Shell, command-center, vectorized research, and macOS runtime evidence
  vertical slices.
- Existing legacy holdings sync and ResearchBus code is not migrated yet.
- DuckDB/Parquet query surfaces remain in the existing `DataStore`.
- Full source ingestion and vertical workflow migration are not complete.

## Next Phase A Iterations

1. Replace remaining legacy Streamlit direct reads one vertical slice at a
   time.
