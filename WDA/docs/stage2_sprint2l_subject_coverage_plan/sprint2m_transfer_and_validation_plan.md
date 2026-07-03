# Sprint 2M Transfer And Validation Plan

## New-Computer Validation

Sprint 2M-B should run on the new computer after Sprint 2M-A creates a bounded
transfer bundle on the old computer.

## Transfer Boundary

Transfer only:

- bounded raw JSONL exports for selected subjects
- manifest/checksum files
- repo-safe selection, shape, row count, and safety reports

Do not transfer:

- key material
- wxkey config
- decrypted DBs
- DB/WAL/SHM files
- broad logs
- `tool_work/`
- `sensitive_local_state/`
- full contact exports
- all-history exports
- media files

## Validation Steps

1. Verify transfer bundle path and SHA-256.
2. Verify payload checksums.
3. Inventory included files.
4. Confirm excluded sensitive material is absent.
5. Parse bounded subject JSONL exports.
6. Validate per-subject and total row counts.
7. Convert to WDA Raw Import Contract.
8. Generate local full-sensitive Raw Import Pack under WDA_MetaData.
9. Generate repo-safe docs with counts, schemas, mappings, and errors only.
10. Preserve Raw Gate wording: bounded subject coverage result, not full Go.

## Expected Validation Metrics

- Subject targets attempted: up to `5`
- Conversations exported: up to `5`
- Messages exported: up to `500`
- `include_media_paths=false`
- conversion errors: `0` expected
- missing required fields: none expected

