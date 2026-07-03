# Data Core Seed Summary

## Local Output

`/Users/linzezhang/Downloads/WDA_MetaData/v0_1/data_core_seed/`

Required local outputs were generated:

- `wda_v0_1_seed.sqlite`
- `ingest_manifest.json`
- `ingest_validation_report.json`
- `query_examples.sql`
- `row_count_summary.csv`
- `subject_coverage_summary.csv`

## Seed Boundary

The database contains only the Sprint 2M-B bounded first-batch Raw Import Pack.
It does not include full history, full contacts, media files, embeddings, web
state, matrix state, or ChatGPT Pack artifacts.

## Decision

v0.1-A passes. The next sprint can build a local analysis layer over this seed
without enabling RAG/Web/Matrix or expanding raw data.
