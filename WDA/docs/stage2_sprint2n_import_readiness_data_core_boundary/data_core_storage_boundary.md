# Data Core Storage Boundary

Sprint 2O database files must be local-only and outside Git.

## Approved Local Storage Root

`/Users/linzezhang/Downloads/WDA_MetaData/data_core/sprint2o_minimal_seed/`

## Proposed Local Files

| File | Purpose | Git policy |
|---|---|---|
| `wda_data_core_sprint2o.sqlite` | minimal local Data Core seed database | do not commit |
| `wda_data_core_sprint2o.sqlite-shm` | SQLite sidecar if produced | do not commit |
| `wda_data_core_sprint2o.sqlite-wal` | SQLite sidecar if produced | do not commit |
| `import_readiness_manifest.json` | local execution manifest with source checksums | do not commit |
| `import_validation_report.csv` | local validation details | do not commit if it includes raw refs |

## Repo-Safe Policy

Git may contain only summarized docs: schema names, row counts, checksum hashes,
validation pass/fail states, and decisions. Git must not contain raw messages,
raw contacts, transfer bundles, generated databases, SQLite sidecars, or Raw
Import Pack files.

