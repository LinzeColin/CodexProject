# WDA Stage 2 Sprint 2B-A Candidate Bundle

Generated: 2026-07-03T08:13:49+10:00

Purpose: prepare a small local isolated candidate DB bundle for Sprint 2B-B schema-only read-only probing on the new computer.

Source contract:
- Source class: authoritative old-computer APFS sparseimage export.
- Source root label in CSV: `APFS_RAW_COPY_ROOT`.
- Local bundle target: `/Users/linzezhang/Downloads/WDA_MetaData/raw_ferry/sprint2b_candidate_db_bundle_20260703`.
- The bundle is APFS-derived local data and is not a git artifact.

Bundle result:
- Selected files: 169
- Main DB candidates: 91
- WAL companions: 39
- SHM companions: 39
- Copied size: 959938032 bytes (915.47 MiB)
- Exclusion rows documented: 160
- Local files pruned during strict validation: 38

Decision state:
- Message readability is not proven.
- No message/contact rows were selected.
- No schema was opened in Sprint 2B-A.
- Raw Gate remains Conditional Investigation.

Sprint 2B-B can run without the external drive by using only `/Users/linzezhang/Downloads/WDA_MetaData/raw_ferry/sprint2b_candidate_db_bundle_20260703`.
