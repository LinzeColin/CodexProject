# Sprint 2O Minimal Data Core Seed Plan

## Decision

Sprint 2O can start.

## Host

Run on the new computer only.

## Input

Use only:

`/Users/linzezhang/Downloads/WDA_MetaData/stage2_outputs/sprint2m_b_subject_coverage_import_validation/`

## Output

Write local database files only under:

`/Users/linzezhang/Downloads/WDA_MetaData/data_core/sprint2o_minimal_seed/`

## Sprint 2O Boundaries

- ingest exactly the bounded 2M-B pack
- expected messages: `500`
- expected conversations: `5`
- expected contacts: `23`
- expected media rows: `0`
- no exporter tools
- no external hard drive
- no full export
- no media path handling
- no RAG/Web/Matrix

## Required Validation

Sprint 2O must report:

- source checksums match
- input row counts match
- database table counts match input counts
- all message conversation references resolve
- sender references resolve or use approved fallbacks
- media refs are empty
- no raw data committed to Git

If any validation fails, Sprint 2O should stop and produce a repo-safe failure
report without retry loops or data expansion.

